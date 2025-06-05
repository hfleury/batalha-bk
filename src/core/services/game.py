from typing import Any
from src.core.interface.game_repository import GameRepository
from src.core.domain.player import Player
from src.core.domain.ship import Ship
from src.core.serializer.ship import parse_ships
from src.core.schemas.place_ships import StandardResponse, ShipPlacementRequest
from src.core.schemas.game_actions import StartGameRequest, ShootRequest
from src.core.schemas.player_info import PlayerInfoRequest
from pydantic import ValidationError
import uuid
import logging

# TODO have here just the GameService logic, move the handler to another place
# TODO Add logger where it is need.

logger = logging.getLogger(__name__)


class GameService:
    def __init__(self, repository: GameRepository) -> None:
        self.repository = repository

    async def handle_action(
        self, action: str, payload: dict[Any, Any], player: Player
    ) -> StandardResponse:
        if action == "place_ships":
            # Construct ShipPlacementRequest from payload and player
            try:
                req_place_ship = ShipPlacementRequest(
                    game_id=payload["game_id"],
                    player_id=str(player.id),
                    ships=payload["players"][str(player.id)],
                )
            except (KeyError, ValidationError) as e:
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
                return StandardResponse(
                    status="error",
                    message=f"Invalid request payload: {e}",
                    action="resp_shoot",
                    data="",
                )
            return await self.shoot(req_shoot)

        else:
            return StandardResponse(
                status="error",
                message=f"Unknown action: {action}",
                action=f"resp_{action}",
                data="",
            )

    async def place_ships(
        self, request: ShipPlacementRequest, player: Player
    ) -> StandardResponse:
        try:
            ships: list[Ship] = parse_ships(request.ships)
        except ValueError as e:
            return StandardResponse(
                status="error", message=str(e), action="resp_place_ships", data=""
            )

        await self.repository.save_player_board(request.game_id, player, ships)

        return StandardResponse(
            status="OK",
            message=f"Ships placed for player {player.id}",
            action="resp_place_ships",
            data="",
        )

    async def start_game(self, request: StartGameRequest) -> StandardResponse:
        # TODO add the saved data to the return
        game_id = request.game_id
        players_data = request.players

        for player_id_str, raw_ships_raw in players_data.items():
            try:
                player_id_int = uuid.UUID(player_id_str)
            except ValueError:
                return StandardResponse(
                    status="error",
                    message=f"Invalid player ID: {player_id_str}",
                    action="resp_start_game",
                    data="",
                )

            if not raw_ships_raw:
                return StandardResponse(
                    status="error",
                    message=f"Invalid ships data for player {player_id_str}",
                    action="resp_start_game",
                    data="",
                )

            try:
                ships: list[Ship] = parse_ships(raw_ships_raw)
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
        # TODO ask betoso if we should change the name of the action
        # to get_game_player_id_info

        player_info = Player(
            id=uuid.UUID(request.player_id),
        )

        if not request.game_id or request.player_id == "":
            return StandardResponse(
                status="error",
                message="Missing game_id or player_id",
                action="resp_get_game_info",
                data="",
            )
        rtn_player_info = StandardResponse(
            status="OK",
            message=f"player: {request.player_id} info for game: {request.game_id}",
            action="resp_get_game_info",
            data=await self.repository.get_player_board(
                request.game_id, player_info.id
            ),
        )
        return rtn_player_info

    async def shoot(self, request: ShootRequest) -> StandardResponse:
        shooter = Player(id=request.player_id)

        opponent_id = await self.repository.get_opponent_id(request.game_id, shooter)
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

        return StandardResponse(
            status="OK",
            message=f"the shoot of the player{request.player_id}"
            " on target:{request.target}",
            action="resp_shoot",
            data={"status": "miss", "target": request.target},
        )
