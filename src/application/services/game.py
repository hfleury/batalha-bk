"""Provides the core business logic for the game service."""

import logging
import time
import uuid
import random
from typing import Any, List

from pydantic import ValidationError

from src.domain.game import GameSession, GameStatus, PlayerBoard
from src.domain.player import Player
from src.application.repositories.game_repository import GameRepository
from src.infrastructure.manager.connection_manager import ConnectionManager
from src.api.v1.schemas.game_actions import (
    FindGameRequest,
    ShootRequest,
    StartGameRequest,
)
from src.api.v1.schemas.place_ships import (
    ShipPlacementRequest,
    StandardResponse,
    ShipDetails
)
from src.api.v1.schemas.player_info import PlayerInfoRequest
from src.application.ship import parse_ships

logger = logging.getLogger(__name__)


class GameService:
    """Orchestrates game logic, handling player actions and game state.

    This service acts as a facade for all game-related operations, coordinating
    between the data repository and the connection manager to manage game flow.

    Attributes:
        repository: An instance of a GameRepository for data persistence.
        conn_manager: An instance of a ConnectionManager for handling player
        connections.
    """

    def __init__(
        self, repository: GameRepository, conn_manager: ConnectionManager
    ) -> None:
        """Initializes the GameService."""
        self.repository = repository
        self.conn_manager = conn_manager

    async def handle_action(
        self, action: str, payload: dict[Any, Any], player: Player
    ) -> StandardResponse:
        """Routes incoming player actions to the appropriate handler method.

        This method acts as a dispatcher, validating the payload for a given
        action and calling the corresponding service method.

        Args:
            action: The action requested by the player (e.g., 'place_ships').
            payload: The data associated with the action.
            player: The player who initiated the action.

        Returns:
            A StandardResponse object with the result of the action.
        """
        if action == "place_ships":
            # Construct ShipPlacementRequest from payload and player
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

        elif action == "start_game":
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

        elif action == "get_game_info":
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

        elif action == "shoot":
            try:
                req_shoot = ShootRequest(
                    game_id=payload["game_id"],
                    player_id=payload["player_id"],
                    target=payload["target"],
                )
            except (KeyError, ValidationError) as e:
                logger.error(f"{action} validation error: {e}")
                return StandardResponse(
                    status="error",
                    message=f"Invalid request payload: {e}",
                    action="resp_shoot",
                    data="",
                )
            return await self.shoot(req_shoot)

        elif action == "find_game_session":
            try:
                req_find_game_session = FindGameRequest(
                    player_id=uuid.UUID(payload["player_id"]),
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

        else:
            return StandardResponse(
                status="error",
                message=f"Unknown action: {action}",
                action=f"error_{action}",
                data="",
            )

    async def place_ships(
        self, request: ShipPlacementRequest, player: Player
    ) -> StandardResponse:
        """Handles the logic for a player to place their ships on the board.

        Args:
            request: The validated request containing ship placement data.
            player: The player placing the ships.

        Returns:
            A StandardResponse indicating the outcome of the operation.
        """
        game_id: str = request.game_id
        await self.repository.save_player_board(game_id, player, request.ships)
        logger.debug("AFTER SAVE PLAYER BOARD")
        game_info = await self.repository.get_game_info(game_key=game_id)
        ready = await self.are_both_player_ready(
            game_id,
            game_info.player1_id,
            game_info.player2_id
        )

        if ready:
            first_turn = str(
                random.choice(
                    [game_info.player1_id, game_info.player2_id]
                )
            )

            battle_msg = StandardResponse(
                status="battle_start",
                message="Both players have placed the ships",
                action="place_ship_response",
                data={
                    "firstTurn": first_turn,
                },
            )

            await self.conn_manager.send_to_player(
                uuid.UUID(game_info.player1_id),
                battle_msg.to_dict()
            )
            await self.conn_manager.send_to_player(
                uuid.UUID(game_info.player2_id),
                battle_msg.to_dict()
            )

            return StandardResponse(
                status="OK",
                message="Ships placed. Battle starting!",
                action="place_ship_response",
                data="",
            )

        return StandardResponse(
                status="shipsPlaced",
                message=f"Ships placed for player {player.id}",
                action="place_ship_response",
                data=""
            )

    async def start_game(self, request: StartGameRequest) -> StandardResponse:
        """Initializes a game by setting up the boards for all players.

        Note: This is likely a legacy or administrative action. Game creation
        is typically handled by `find_game_session`.

        Args:
            request: The validated request containing game and player ship data.

        Returns:
            A StandardResponse indicating the outcome of the operation.
        """
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
        """Retrieves the board information for a specific player in a game.

        Args:
            request: The validated request containing the game and player IDs.

        Returns:
            A StandardResponse containing the player's board data.
        """
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
        """Handles a player's attempt to shoot at an opponent's board.

        Args:
            request: The validated request containing game, player, and target info.

        Returns:
            A StandardResponse indicating whether the shot was a hit or miss.
        """
        game = await self.repository.load_game_session(request.game_id)

        if game:
            if game.status != GameStatus.IN_PROGRESS:
                return StandardResponse(
                    status="error",
                    message="Game is not active",
                    action="resp_shoot",
                    data="",
                )

            # Check if it's the shooter's turn
            if request.player_id != game.current_turn:
                return StandardResponse(
                    status="error",
                    message="It's not your turn",
                    action="resp_shoot",
                    data="",
                )

            shooter = Player(id=request.player_id)
            opponent_id: uuid.UUID | None = await self.repository.get_opponent_id(
                request.game_id, shooter
            )
            if opponent_id is None:
                logger.info(f"No opponent found for game_id: {request.game_id}")
                return StandardResponse(
                    status="error",
                    message="No opponent found",
                    action="resp_shoot",
                    data="",
                )

            opponent_board = await self.repository.get_player_board(
                request.game_id, opponent_id
            )

            if not opponent_board:
                return StandardResponse(
                    status="error",
                    message=f"Opponent{opponent_id} board not found"
                    " of game:{request.game_id}",
                    action="resp_shoot",
                    data="",
                )

            for ship_id, positions in opponent_board.items():
                if request.target in positions:
                    await self.repository.save_hit(
                        request.game_id, opponent_id, ship_id, request.target
                    )
                    hits = await self.repository.get_player_hits(
                        request.game_id, opponent_id
                    )
                    is_sunk = set(hits.get(ship_id, [])) == set(positions)

                    return StandardResponse(
                        status="OK",
                        message=f"the shoot of the player{request.player_id}"
                        " hit the target:{request.target}",
                        action="resp_shoot",
                        data={
                            "status": "hit",
                            "target": request.target,
                            "ship_id": ship_id,
                            "sunk": is_sunk,
                        },
                    )

                game.current_turn = self._get_next_player(game, request.player_id)
                await self.repository.save_game_session(game)

            return StandardResponse(
                status="OK",
                message=f"the shoot of the player{request.player_id}"
                " on target:{request.target}",
                action="resp_shoot",
                data={"status": "miss", "target": request.target},
            )
        return StandardResponse(
            status="error",
            message="Game not found",
            action="resp_shoot",
            data="",
        )

    async def find_game_session(self, player: FindGameRequest) -> StandardResponse:
        """Handles a player's request to find and join a game.

        If an opponent is waiting in the queue, a new game is created and
        both players are notified. Otherwise, the current player is added
        to the queue.

        Args:
            player: The validated request containing the player's ID.

        Returns:
            A StandardResponse indicating if a game was created or if the player is
            waiting.
        """
        queue_key = "game:queue"

        opponent_player_id = await self.repository.get_opponent_from_queue(
            queue_key, player.player_id
        )
        logger.debug(f"The opponent_player_id {opponent_player_id}")

        if opponent_player_id:
            await self.repository.pop_from_queue(queue_key, opponent_player_id)
            logger.info(f"ESTA AQUIIII {opponent_player_id}")
            game_id = uuid.uuid4()
            now = int(time.time())

            game_data = GameSession(
                game_id=game_id,
                start_datetime=now,
                end_datetime=0,
                players={
                    opponent_player_id: PlayerBoard(),
                    player.player_id: PlayerBoard(),
                },
                status=GameStatus.IN_PROGRESS,
            )
            logger.debug(f"AFTER CREATE GAMESESSION {game_data}")
            try:
                await self.repository.save_game_to_redis(game_data)
            except Exception as e:
                logger.error(f"Game Not saved ERROR: {e}")

            # Create player-specific game data (hide opponent info)
            def create_player_game_data(
                game_session: GameSession,
                player_id: uuid.UUID
            ) -> dict[str, Any]:
                """Create game data payload specific
                to a player (hides opponent info).
                """
                return {
                    "game_id": str(game_session.game_id),
                    "start_datetime": game_session.start_datetime,
                    "end_datetime": game_session.end_datetime,
                    "players": (str(player_id)),
                    "current_turn": str(game_session.current_turn),
                    "status": game_session.status.value,
                    "first_turn": str(game_session.current_turn),
                }

            # Create separate payloads for each player
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

            # Send player-specific payloads
            # await self.conn_manager.send_to_player(
            #    player.player_id,
            #    current_player_payload
            # )
            await self.conn_manager.send_to_player(opponent_player_id, opponent_payload)

            # Return response for the current player (the one who made the request)
            return current_player_payload

        # No player waiting, put current player in queue
        await self.repository.push_to_queue(
            queue_key,
            player.player_id,
        )
        return StandardResponse(
            status="waiting",
            message="Waiting for another player",
            action="res_find_game_session",
            data=str(player.player_id),
        )

    def _get_next_player(self, game: GameSession, current_id: uuid.UUID) -> uuid.UUID:
        """Determines the next player's turn in a game.

        Args:
            game: The current game session.
            current_id: The UUID of the player who just finished their turn.

        Returns:
            The UUID of the next player.
        """
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
        """Check if both players are ready to start a game

        Args:
            game_id (str): the game id to check against
            player1_id (str): One of the players id
            player2_id (str): the other players id

        Returns:
            bool: if both players has placed the ships they are ready to start a game
        """
        player1_ready = await self.repository.exist_player_on_game(game_id, player1_id)
        logger.debug(f"player1_ready {player1_ready}")
        player2_ready = await self.repository.exist_player_on_game(game_id, player2_id)
        logger.debug(f"player2_ready {player2_ready}")
        if player1_ready and player2_ready:
            return True
        return False
