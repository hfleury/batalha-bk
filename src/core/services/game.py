from typing import Any
from src.core.interface.game_repository import GameRepository
from src.core.domain.player import Player
from src.core.domain.ship import Ship
from src.core.serializer.ship import parse_ships
from src.core.schemas.place_ships import StandardResponse, ShipPlacementRequest
from src.core.schemas.start_game import StartGameRequest
from pydantic import ValidationError
import uuid


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
            except KeyError as e:
                return StandardResponse(
                    status="error", message=f"Missing field in payload: {e}"
                )
            except ValidationError as e:
                return StandardResponse(status="error", message=str(e))

            return await self.place_ships(req_place_ship, player)

        elif action == "start_game":
            req_start_game = StartGameRequest(
                game_id=payload["game_id"],
                players=payload["players"],
            )
            return await self.start_game(req_start_game)

        elif action == "get_game_info":
            return await self.get_game_info(payload)

        elif action == "shoot":
            return await self.shoot(payload)

        else:
            return StandardResponse(status="error", message=f"Unknown action: {action}")

    async def place_ships(
        self, request: ShipPlacementRequest, player: Player
    ) -> dict[str, str]:
        try:
            ships: list[Ship] = parse_ships(request.ships)
        except ValueError as e:
            return {"status": "error", "message": str(e)}

        await self.repository.save_player_board(request.game_id, player, ships)

        return {"status": "OK", "message": f"Ships placed for player {player.id}"}

    async def start_game(self, request: StartGameRequest) -> StandardResponse:
        game_id = request.game_id
        players_data = request.players

        for player_id_str, raw_ships_raw in players_data.items():
            # player_id_str is guaranteed str by Pydantic, but convert to int carefully
            try:
                player_id_int = uuid.UUID(player_id_str)
            except ValueError:
                return StandardResponse(
                    status="error",
                    message=f"Invalid player ID: {player_id_str}",
                )

            if not raw_ships_raw:
                return StandardResponse(
                    status="error",
                    message=f"Invalid ships data for player {player_id_str}",
                )

            try:
                ships: list[Ship] = parse_ships(raw_ships_raw)
            except ValueError as e:
                return StandardResponse(status="error", message=str(e))

            player = Player(id=player_id_int)
            await self.repository.save_player_board(game_id, player, ships)

        return StandardResponse(status="OK", message=f"Game {game_id} started")

    async def get_game_info(self, payload: dict) -> dict:
        game_id = payload.get("game_id")
        player_id = payload.get("player_id")

        if not game_id or player_id is None:
            return {"status": "error", "message": "Missing game_id or player_id"}

        return await self.repository.get_player_board(game_id, player_id)

    async def shoot(self, payload: dict) -> dict:
        game_id = payload.get("game_id")
        shooter_id = payload.get("player_id")
        target = payload.get("target")

        if not game_id or shooter_id is None or not target:
            return {
                "status": "error",
                "message": "Missing game_id, player_id, or target",
            }

        opponent_id = self.repository.get_opponent_id(game_id, shooter_id)
        opponent_board = await self.repository.get_player_board(game_id, opponent_id)

        if not opponent_board:
            return {"status": "error", "message": "Opponent board not found"}

        for ship_id, positions in opponent_board.items():
            if target in positions:
                await self.repository.save_hit(game_id, opponent_id, ship_id, target)
                hits = await self.repository.get_player_hits(game_id, opponent_id)
                is_sunk = set(hits.get(ship_id, [])) == set(positions)

                return {
                    "status": "hit",
                    "target": target,
                    "ship_id": ship_id,
                    "sunk": is_sunk,
                }

        return {"status": "miss", "target": target}
