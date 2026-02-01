"""Provides the core business logic for the game service."""

import logging
import time
import uuid
import random
from typing import Any, List
from dataclasses import dataclass

from pydantic import ValidationError

from src.domain.game import GameSession, PlayerBoard, GameStatus
from src.domain.player import Player
from src.application.repositories.game_repository import GameRepository
from src.infrastructure.manager.connection_manager import ConnectionManager
from src.api.v1.schemas.game_actions import (
    FindGameRequest,
    ShootRequest,
    StartGameRequest,
    PassTurn,
)
from src.api.v1.schemas.place_ships import (
    ShipPlacementRequest,
    StandardResponse,
    ShipDetails
)
from src.api.v1.schemas.player_info import PlayerInfoRequest
from src.application.ship import parse_ships
from src.application.builders.response import ResponseBuilder
from src.domain.game_validator import GameValidator
from src.application.services.notification_service import (
    NotificationService,
    NotificationData,
)
from src.domain.factions import get_faction

logger = logging.getLogger(__name__)


@dataclass
class ProcessHitData:
    """Data class for arguments passed to _process_hit."""
    game: GameSession
    request: ShootRequest
    opponent_id: uuid.UUID
    ship_id: str
    positions: list


class GameService:
    """Orchestrates game logic, handling player actions and game state."""

    def __init__(
        self,
        repository: GameRepository,
        conn_manager: ConnectionManager
    ) -> None:
        """Initializes the GameService."""
        self.repository = repository
        self.conn_manager = conn_manager
        self.notification_service = NotificationService(conn_manager)
        self.validator = GameValidator()

        self._action_handlers = {
            "place_ships": self._handle_place_ships,
            "start_game": self._handle_start_game,
            "get_game_info": self._handle_get_game_info,
            "shoot": self._handle_shoot,
            "find_game_session": self._handle_find_game_session,
            "pass_turn": self._handle_pass_turn,
        }

    async def handle_action(
        self, action: str, payload: dict[Any, Any], player: Player
    ) -> StandardResponse:
        """Routes incoming player actions to the appropriate handler method."""
        handler = self._action_handlers.get(action)
        if handler:
            return await handler(action, payload, player)

        return ResponseBuilder.error(f"Unknown action: {action}", f"error_{action}")

    async def _handle_place_ships(
        self, action: str, payload: dict[Any, Any], player: Player
    ) -> StandardResponse:
        try:
            req_place_ship = ShipPlacementRequest(
                game_id=payload["game_id"],
                player_id=str(player.id),
                ships=parse_ships(payload["ships"]),
            )
        except (KeyError, ValidationError) as e:
            logger.error(f"{action} validation error: {e}")
            return StandardResponse(
                status="error",
                message=f"Invalid request payload: {e}",
                action="resp_place_ships",
                data="",
            )

        return await self.place_ships(req_place_ship, player)

    async def _handle_start_game(
        self, action: str, payload: dict[Any, Any], _player: Player
    ) -> StandardResponse:
        try:
            req_start_game = StartGameRequest(
                game_id=payload["game_id"],
                players=payload["players"],
            )
        except (KeyError, ValidationError) as e:
            logger.error(f"{action} validation error: {e}")
            return StandardResponse(
                status="error",
                message=f"Invalid request payload: {e}",
                action="resp_start_game",
                data="",
            )
        return await self.start_game(req_start_game)

    async def _handle_get_game_info(
        self, action: str, payload: dict[Any, Any], _player: Player
    ) -> StandardResponse:
        try:
            req_player_info = PlayerInfoRequest(
                game_id=payload["game_id"],
                player_id=payload["player_id"],
            )
        except (KeyError, ValidationError) as e:
            logger.error(f"{action} validation error: {e}")
            return StandardResponse(
                status="error",
                message=f"Invalid request payload: {e}",
                action="resp_get_game_info",
                data="",
            )
        return await self.get_game_info(req_player_info)

    async def _handle_shoot(
        self, action: str, payload: dict[Any, Any], _player: Player
    ) -> StandardResponse:
        logger.debug(f"ACTION SHOOT {payload}")
        try:
            req_shoot = ShootRequest(
                game_id=payload["game_id"],
                player_id=payload["player_id"],
                target=payload["target"],
                ship_type=payload["ship_type"],
            )
        except (KeyError, ValidationError) as e:
            logger.error(f"{action} validation error: {e}")
            return StandardResponse(
                status="error",
                message=f"Invalid request payload: {e}",
                action="shoot_result",
                data="",
            )
        return await self.shoot(req_shoot)

    async def _handle_find_game_session(
        self, action: str, payload: dict[Any, Any], _player: Player
    ) -> StandardResponse:
        try:
            req_find_game_session = FindGameRequest(
                player_id=uuid.UUID(payload["player_id"]),
                faction=payload.get("faction", "Marines")
            )
        except (KeyError, ValidationError) as e:
            logger.error(f"{action} validation error: {e}")
            return StandardResponse(
                status="error",
                message=f"Invalid request payload: {e}",
                action="error_find_game_session",
                data="",
            )
        return await self.find_game_session(req_find_game_session)

    async def _handle_pass_turn(
        self, action: str, payload: dict[Any, Any], _player: Player
    ) -> StandardResponse:
        logger.debug("ENTROU NO PASS TURN")
        try:
            logger.debug("INSIDE TRY OF PASS TURN")
            req_pass_turn = PassTurn(
                player_id=uuid.UUID(payload["player_id"]),
                game_id=uuid.UUID(payload["game_id"])
            )
        except (KeyError, ValidationError) as e:
            logger.error(f"{action} validation error: {e}")
            return StandardResponse(
                status="error",
                message=f"Invalid request payload: {e}",
                action="error_confirm_pass_turn",
                data="",
            )
        return await self.pass_turn(req_pass_turn)

    async def place_ships(
        self, request: ShipPlacementRequest, player: Player
    ) -> StandardResponse:
        """Handles the logic for a player to place their ships on the board."""
        game_id: str = request.game_id
        game_id_uuid: uuid.UUID = uuid.UUID(game_id)
        try:
            await self.repository.save_player_board(game_id, player, request.ships)
        except Exception as ex:
            logger.debug(f"EXCEPTION ON PLACE SHIPS SAVING PLAYER BOARD {ex}")

        logger.debug("AFTER SAVE PLAYER BOARD")
        game_session = await self.repository.load_game_session(game_id=game_id_uuid)
        logger.debug(f"LOAD GAME SESSION {game_session}")

        if not game_session:
            return StandardResponse(
                status="error",
                message="Game session not found",
                action="place_ship_response",
                data="",
            )

        # Extract player IDs from the session's players dict
        player_ids = list(game_session.players.keys())
        if len(player_ids) != 2:
            return StandardResponse(
                status="error",
                message="Invalid number of players in game",
                action="place_ship_response",
                data="",
            )
        player1_id, player2_id = player_ids[0], player_ids[1]
        logger.debug(f"PLAYERS {player1_id} AND THE {player2_id}")
        ready = await self.are_both_player_ready(
            game_id,
            str(player1_id),
            str(player2_id)
        )

        if ready:
            logger.debug(f"INSIDE READY TRUE {ready}")
            first_turn = random.choice(
                    [player1_id, player2_id]
            )

            game_session.current_turn = first_turn
            game_session.status = GameStatus.IN_PROGRESS
            await self.repository.save_game_to_redis(game_session)

            battle_msg = StandardResponse(
                status="battle_start",
                message="Both players have placed the ships",
                action="place_ship_response",
                data={
                    "game_id": str(game_session.game_id),
                    "player_id": str(player.id),
                    "firstTurn": str(first_turn),
                },
            )
            logger.debug(
                f"BATTLE MSG SENT TO THE FRONT END"
                f"{battle_msg} and {battle_msg.to_dict()}"
            )
            try:
                await self.conn_manager.send_to_player(
                    player1_id,
                    battle_msg.to_dict()
                )
                await self.conn_manager.send_to_player(
                    player2_id,
                    battle_msg.to_dict()
                )
            except Exception as ep:
                logger.debug(f"ERROR SENDING MESSAGE TO PLAYERS {ep}")

            logger.debug(f"BATLLE MSG {battle_msg}")
            return StandardResponse(
                status="battle_start",
                message="Ships placed. Battle starting!",
                action="place_ship_response",
                data={
                    "game_id": str(game_session.game_id),
                    "player_id": str(player.id),
                    "firstTurn": str(first_turn),
                },
            )

        return StandardResponse(
                status="shipsPlaced",
                message=f"Ships placed for player {player.id}",
                action="place_ship_response",
                data={
                    "game_id": str(game_session.game_id),
                    "player_id": str(player.id),
                }
            )

    async def start_game(self, request: StartGameRequest) -> StandardResponse:
        """Initializes a game by setting up the boards for all players."""
        game_id = request.game_id
        players_data = request.players

        for player_id_str, raw_ships_dict in players_data.items():
            try:
                player_id_int = uuid.UUID(player_id_str)
            except ValueError as e:
                logger.error(f"Valuer error on start_game validation error: {e}")
                return StandardResponse(
                    status="error",
                    message=f"Invalid player ID: {player_id_str}",
                    action="resp_start_game",
                    data="",
                )

            if not raw_ships_dict:
                return StandardResponse(
                    status="error",
                    message=f"Invalid ships data for player {player_id_str}",
                    action="resp_start_game",
                    data="",
                )
            try:
                # Assuming raw_ships_dict is like {"Carrier": ["A1", "A2", ...], ...}
                raw_ship_list: List[dict[str, Any]] = [
                    {"type": ship_type, "positions": positions}
                    for ship_type, positions in raw_ships_dict.items()
                ]
            except Exception as e:
                logger.error(f"Error structuring ship data: {e}")
                return StandardResponse(
                    status="error",
                    message="Internal error structuring ship data.",
                    action="resp_start_game",
                    data=""
                )

            try:
                ships: List[ShipDetails] = parse_ships(raw_ship_list)
            except ValueError as e:
                return StandardResponse(
                    status="error", message=str(e), action="resp_start_game", data=""
                )

            player = Player(id=player_id_int)
            await self.repository.save_player_board(game_id, player, ships)

        return StandardResponse(
            status="OK",
            message=f"Game {game_id} started",
            action="resp_start_game",
            data="",
        )

    async def get_game_info(self, request: PlayerInfoRequest) -> StandardResponse:
        """Retrieves the board information for a specific player in a game."""
        if not request.game_id or not request.player_id:
            return StandardResponse(
                status="error",
                message="Missing game_id or player_id",
                action="resp_get_game_info",
                data="",
            )

        player = Player(id=request.player_id)
        if player.id is None:
            return StandardResponse(
                status="error",
                message="Player not found",
                action="resp_get_game_info",
                data="",
            )
        rtn_player_info = StandardResponse(
            status="OK",
            message=f"player: {request.player_id} info for game: {request.game_id}",
            action="resp_get_game_info",
            data=await self.repository.get_player_board(request.game_id, player.id),
        )
        return rtn_player_info

    async def shoot(self, request: ShootRequest) -> StandardResponse:
        """Handles a player's attempt to shoot at an opponent's board."""
        logger.debug(f"INSIDE THE SHOOT FUNCTION {request}")

        game = await self.repository.load_game_session(request.game_id)

        if game is None:
            return ResponseBuilder.error("Game not found", "resp_shoot")

        validation_error = self.validator.validate_shoot(game, str(request.player_id))
        if validation_error:
            return validation_error

        # Get Player Board for Faction and Fuel
        player_board = game.players.get(request.player_id)
        if not player_board:
             return ResponseBuilder.error("Player not in game", "shoot_result")
        
        faction_name = player_board.faction or "Marines"
        current_fuel = player_board.fuel
        faction = get_faction(faction_name)
        
        # Verify ship ownership/existence (simple check if key exists in board)
        # logic: player's ships are also in game.players[player_id].board
        # But we need to ensure the specific ship type is available/alive if we want to be strict.
        # The plan didn't specify strict dead-ship check, but let's assume if it exists it's fine for now.

        strategy = faction.get_shoot_strategy(request.ship_type)
        
        if current_fuel < strategy.fuel_cost:
            return ResponseBuilder.error(
                f"Not enough fuel. Need {strategy.fuel_cost}, have {current_fuel}", 
                "shoot_result"
            )

        # Deduct Fuel
        player_board.fuel -= strategy.fuel_cost

        # Get opponent info
        opponent_id = await self.repository.get_opponent_id(
            request.game_id,
            Player(id=request.player_id)
        )
        if opponent_id is None:
            logger.info(f"No opponent found for game_id: {request.game_id}")
            return ResponseBuilder.error("No opponent found", "shoot_result")

        opponent_board_ships = await self.repository.get_player_board(
            request.game_id,
            opponent_id
        )
        if not opponent_board_ships:
            return ResponseBuilder.error(
                f"Opponent {opponent_id} board not found "
                f"for game {request.game_id}",
                "shoot_result"
            )

        # Calculate affected coordinates
        target_cells = strategy.calculate_hits(request.target)
        hit_details = []
        
        game_over = False
        winner = None

        for cell in target_cells:
            # Check for Hit
            hit_ship_id = None
            hit_positions = []
            
            for ship_id, positions in opponent_board_ships.items():
                if cell in positions:
                    hit_ship_id = ship_id
                    hit_positions = positions
                    break
            
            # Prepare new request object for internal processing if needed, 
            # or just call internal methods with the specific cell.
            # We can reuse the request object but modify target.
            
            single_shot_request = ShootRequest(
                game_id=request.game_id,
                player_id=request.player_id,
                target=cell,
                ship_type=request.ship_type
            )

            if hit_ship_id:
                 # It's a Hit
                 hit_data = ProcessHitData(
                    game=game,
                    request=single_shot_request,
                    opponent_id=opponent_id,
                    ship_id=hit_ship_id,
                    positions=hit_positions
                )
                 # Note: _process_hit saves game info and sends notification.
                 # We need to be careful about Game being modified in loop (fuel matches).
                 # _process_hit saves hits to repository.
                 # It also checks game over.
                 
                 resp = await self._process_hit(hit_data)
                 hit_details.append({
                     "cell": cell, 
                     "result": "hit", 
                     "ship_id": hit_ship_id,
                     "sunk": resp.data.get("sunk", False)
                 })
                 
                 if resp.data.get("game_over"):
                     game_over = True
                     winner = str(request.player_id)
                     break # Stop processing if game over
            else:
                # It's a Miss
                # _process_miss saves game and notifies
                await self._process_miss(game, single_shot_request, opponent_id)
                hit_details.append({"cell": cell, "result": "miss"})

        if game_over:
             return ResponseBuilder.success(
                f"Player {request.player_id} wins!",
                "shoot_result",
                {
                    "result": "game_over",
                    "hits": hit_details,
                    "game_over": True,
                    "winner": winner
                }
            )

        return ResponseBuilder.success(
            f"Shot processed. Fuel remaining: {player_board.fuel}",
            "shoot_result",
            {
                "result": "multi_shot",
                "hits": hit_details,
                "fuel_remaining": player_board.fuel,
                "player_turn": str(game.current_turn),
            }
        )

    async def _process_hit(
        self,
        hit_data: ProcessHitData
    ) -> StandardResponse:
        """Process a hit on opponent's ship."""
        await self.repository.save_hit(
            hit_data.request.game_id,
            hit_data.opponent_id,
            hit_data.ship_id,
            hit_data.request.target
        )
        hits = await self.repository.get_player_hits(
            hit_data.request.game_id,
            hit_data.opponent_id
        )
        is_sunk = set(hits.get(hit_data.ship_id, [])) == set(hit_data.positions)

        # Check if all ships are sunk
        if await self._check_all_ships_sunk(hit_data.game, hit_data.opponent_id):
            return await self._process_game_over(hit_data.game, hit_data.request)

        # Regular hit - continue game
        await self.repository.save_game_to_redis(hit_data.game)
        logger.debug("BEFORE SEND HIT")

        notification_data = NotificationData(
            opponent_id=str(hit_data.opponent_id),
            target=hit_data.request.target,
            request_player_id=str(hit_data.request.player_id),
            current_turn=str(hit_data.game.current_turn),
            ship_id=hit_data.ship_id,
            is_sunk=is_sunk
        )
        await self.notification_service.notify_opponent_hit(notification_data)

        return ResponseBuilder.success(
            f"the shoot of the player {hit_data.request.player_id} "
            f"hit the target: {hit_data.request.target}",
            "shoot_result",
            {
                "result": "hit",
                "cell": hit_data.request.target,
                "ship_id": hit_data.ship_id,
                "sunk": is_sunk,
                "player_turn": str(hit_data.game.current_turn),
            }
        )

    async def _process_miss(
        self,
        game: GameSession,
        request: ShootRequest,
        opponent_id: uuid.UUID
    ) -> StandardResponse:
        """Process a miss."""
        await self.repository.save_game_to_redis(game)
        logger.debug("MISS THE SHOOT")

        notification_data = NotificationData(
            opponent_id=str(opponent_id),
            target=request.target,
            request_player_id=str(request.player_id),
            current_turn=str(game.current_turn)
        )
        await self.notification_service.notify_opponent_miss(notification_data)

        return ResponseBuilder.success(
            f"the shoot of the player {request.player_id} "
            f"on target: {request.target}",
            "shoot_result",
            {
                "result": "miss",
                "cell": request.target,
                "player_turn": str(game.current_turn),
            }
        )

    async def _check_all_ships_sunk(
        self,
        game: GameSession,
        opponent_id: uuid.UUID
    ) -> bool:
        """Check if all opponent ships are sunk."""
        opponent_board = await self.repository.get_player_board(
            game.game_id,
            opponent_id
        )
        if not opponent_board:
            return False

        hits = await self.repository.get_player_hits(game.game_id, opponent_id)

        for ship_id, ship_positions in opponent_board.items():
            ship_hits = set(hits.get(ship_id, []))
            if ship_hits != set(ship_positions):
                return False
        return True

    async def _process_game_over(
        self,
        game: GameSession,
        request: ShootRequest
    ) -> StandardResponse:
        """Process game over scenario."""
        game.status = GameStatus.FINISHED
        game.end_datetime = int(time.time())
        await self.repository.save_game_to_redis(game)
        await self.end_game(game.game_id)

        await self.notification_service.notify_victory(game, str(request.player_id))

        return ResponseBuilder.success(
            f"Player {request.player_id} wins! All opponent ships destroyed!",
            "shoot_result",
            {
                "result": "hit",
                "cell": request.target,
                "ship_id": request.target,
                "sunk": True,
                "game_over": True,
                "winner": str(request.player_id)
            }
        )

    async def find_game_session(self, player: FindGameRequest) -> StandardResponse:
        """Find or create a game session for the player."""
        queue_key = "game:queue"

        if await self.repository.is_player_in_active_game(player.player_id):
            game_id_str = await self.repository.get_active_game(player.player_id)
            if game_id_str:
                game = await self.repository.load_game_session(uuid.UUID(game_id_str))
                if game and game.status != "finished":
                    opponent_id = await self.repository.get_opponent_id(
                        uuid.UUID(game_id_str),
                        Player(id=player.player_id)
                    )

                    # If opponent exists and is connected, resume the game
                    if opponent_id and self.conn_manager.is_player_connected(
                        opponent_id
                    ):
                        logger.info(
                            f"Resuming game {game_id_str} for player {player.player_id}"
                        )

                        # Associate player with game in connection manager
                        self.conn_manager.add_player_to_game(
                            player.player_id, uuid.UUID(game_id_str)
                        )

                        return StandardResponse(
                            status="resume_game",
                            message="Reconnected to existing game",
                            action="res_find_game_session",
                            data={
                                "game_id": game_id_str,
                                "status": game.status.value,
                                "current_turn": (
                                    str(
                                        game.current_turn
                                    ) if game.current_turn else None
                                ),
                                "resume": True
                            },
                        )
                    else:
                        # Opponent is not connected - game is dead
                        logger.info(
                            f"Opponent {opponent_id} is offline. "
                            f"Clearing dead game for {player.player_id}"
                        )
                        await self.repository.clear_player_active_game(player.player_id)
                        # Fall through to treat as new player

        if await self.repository.is_player_in_queue(queue_key, player.player_id):
            return StandardResponse(
                status="waiting",
                message="Already waiting for another player",
                action="res_find_game_session",
                data={
                    "player_id": str(player.player_id)},
            )

        opponent_player_id = await self.repository.get_opponent_from_queue(
            queue_key, player.player_id
        )
        logger.debug(f"The opponent_player_id {opponent_player_id}")

        if opponent_player_id:
            await self.repository.pop_from_queue(queue_key, opponent_player_id)
            logger.info(
                f"Pairing player {player.player_id} with opponent {opponent_player_id}"
            )

            if opponent_player_id == player.player_id:
                logger.warning(
                    "Opponent is same as current player - returning to queue"
                )
                await self.repository.push_to_queue(queue_key, player.player_id)
                return StandardResponse(
                    status="error",
                    message="Invalid opponent found",
                    action="res_find_game_session",
                    data="",
                )

            game_id = uuid.uuid4()
            now = int(time.time())
            game_data = GameSession(
                game_id=game_id,
                start_datetime=now,
                end_datetime=0,
                players={
                    opponent_player_id: PlayerBoard(faction="Marines", fuel=100), # Default for opponent from queue (should fetch actual)
                    player.player_id: PlayerBoard(faction=player.faction, fuel=100),
                },
                status=GameStatus.PLACE_SHIP,
            )
            logger.debug(f"AFTER CREATE GAMESESSION {game_data}")

            try:
                await self.repository.save_game_to_redis(game_data)
                await self.repository.set_player_active_game(
                    player.player_id, game_id
                )
                await self.repository.set_player_active_game(
                    opponent_player_id,
                    game_id
                )

                self.conn_manager.add_player_to_game(player.player_id, game_id)

            except Exception as e:
                logger.error(f"Game not saved ERROR: {e}")
                await self.repository.push_to_queue(queue_key, player.player_id)
                await self.repository.push_to_queue(queue_key, opponent_player_id)
                return StandardResponse(
                    status="error",
                    message="Failed to create game",
                    action="res_find_game_session",
                    data="",
                )

            def create_player_game_data(
                game_session: GameSession, player_id: uuid.UUID
            ) -> dict[str, Any]:
                return {
                    "game_id": str(game_session.game_id),
                    "start_datetime": game_session.start_datetime,
                    "end_datetime": game_session.end_datetime,
                    "players": str(player_id),
                    "status": game_session.status.value,
                }

            current_player_payload = StandardResponse(
                status="ready",
                message="Game has started",
                action="res_find_game_session",
                data=create_player_game_data(game_data, player.player_id),
            )

            opponent_payload = StandardResponse(
                status="ready",
                message="Game has started",
                action="res_find_game_session",
                data=create_player_game_data(game_data, opponent_player_id),
            ).to_dict()

            # When opponent receives this, they should also call add_player_to_game
            await self.conn_manager.send_to_player(opponent_player_id, opponent_payload)
            return current_player_payload

        # No opponent - add to queue
        await self.repository.push_to_queue(queue_key, player.player_id)
        return StandardResponse(
            status="waiting",
            message="Waiting for another player",
            action="res_find_game_session",
            data={
                "player_id": str(player.player_id)
            },
        )

    def _get_next_player(self, game: GameSession, current_id: uuid.UUID) -> uuid.UUID:
        """Determines the next player's turn in a game."""
        for pid in game.players:
            if pid != current_id:
                return pid
        return current_id

    async def are_both_player_ready(
        self,
        game_id: str,
        player1_id: str,
        player2_id: str
    ) -> bool:
        """Check if both players are ready to start a game."""
        player1_ready = await self.repository.exist_player_on_game(game_id, player1_id)
        logger.debug(f"player1_ready {player1_ready}")
        player2_ready = await self.repository.exist_player_on_game(game_id, player2_id)
        logger.debug(f"player2_ready {player2_ready}")
        if player1_ready and player2_ready:
            return True
        return False

    async def end_game(self, game_id: uuid.UUID) -> None:
        """Clean up game resources when game ends."""
        game = await self.repository.load_game_session(game_id)
        if game:
            # Clear active game for all players
            for player_id in game.players:
                await self.repository.clear_player_active_game(player_id)

            # Optionally delete game session (or let TTL expire)
            # await self.redis_client.delete(f"game:{game_id}")

    async def pass_turn(self, pass_turn: PassTurn) -> StandardResponse:
        """Handles a player's request to pass their turn to the opponent."""
        logger.debug("INSIDE THE FUNCTION PASS TURN")
        logger.debug(f"INSIDE PASS_TURN FUNCTION {pass_turn}")

        # Load the current game
        game = await self.repository.load_game_session(pass_turn.game_id)
        if not game:
            return StandardResponse(
                status="error",
                message="Game not found",
                action="error_confirm_pass_turn",
                data="",
            )

        # Check if game is still active
        if game.status != "in_progress":
            return StandardResponse(
                status="error",
                message="Game is not active",
                action="error_confirm_pass_turn",
                data="",
            )

        # Verify that the requesting player
        # is the one whose turn it currently is
        if pass_turn.player_id != game.current_turn:
            return StandardResponse(
                status="error",
                message="It's not your turn to pass",
                action="error_confirm_pass_turn",
                data="",
            )

        # Get the opponent
        opponent_id = await self.repository.get_opponent_id(
            pass_turn.game_id,
            Player(id=pass_turn.player_id)
        )
        if not opponent_id:
            return StandardResponse(
                status="error",
                message="No opponent found",
                action="error_confirm_pass_turn",
                data="",
            )

        # Switch turn to opponent
        game.current_turn = opponent_id

        # Regenerate Fuel for the player starting their turn (opponent_id)
        opponent_board = game.players.get(opponent_id)
        current_fuel = 0
        if opponent_board:
            faction_name = opponent_board.faction or "Marines"
            faction = get_faction(faction_name)
            opponent_board.fuel = faction.regenerate_fuel(opponent_board.fuel)
            current_fuel = opponent_board.fuel
            logger.info(f"Regenerated fuel for {opponent_id}: {opponent_board.fuel}")

        await self.repository.save_game_to_redis(game)

        # Notify opponent that it's their turn
        turn_notification = StandardResponse(
            status="ok",
            message=(
                "Opponent has passed their turn. It's now your turn!"
            ),
            action="confirm_pass_turn",
            data={
                "currentTurn": str(opponent_id),
                "fuel": current_fuel,
                "previous_turn": str(pass_turn.player_id),
                "game_id": str(pass_turn.game_id)
            }
        )

        # Send notification to opponent
        if self.conn_manager.is_player_connected(opponent_id):
            await self.conn_manager.send_to_player(
                opponent_id,
                turn_notification.to_dict()
            )
            logger.info(f"Turn passed notification sent to opponent {opponent_id}")

        # Return confirmation to the player who passed their turn
        return StandardResponse(
            status="ok",
            message="Turn passed successfully",
            action="confirm_pass_turn",
            data={
                "currentTurn": str(opponent_id),
                "game_id": str(pass_turn.game_id)
            },
        )
