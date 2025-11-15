"""Encapsulates game logic and state management."""

import uuid
from src.domain.game import GameStatus
from src.application.repositories.game_repository import GameRepository


class GameEngine:
    """Encapsulates game logic and state management."""

    def __init__(self, repository: GameRepository):
        self.repository = repository

    async def check_all_ships_sunk(self, game_id: str, opponent_id: str) -> bool:
        """Check if all opponent ships are sunk."""
        game_id_uuid = uuid.UUID(game_id)
        opponent_id_uuid = uuid.UUID(opponent_id)

        opponent_board = await self.repository.get_player_board(
            game_id_uuid,
            opponent_id_uuid
        )
        if not opponent_board:
            return False

        hits = await self.repository.get_player_hits(
            game_id_uuid,
            opponent_id_uuid
        )

        for ship_id, ship_positions in opponent_board.items():
            ship_hits = set(hits.get(ship_id, []))
            if ship_hits != set(ship_positions):
                return False
        return True

    async def end_game(self, game_id: str) -> None:
        """End the game and cleanup."""
        game = await self.repository.load_game_session(uuid.UUID(game_id))
        if game:
            game.status = GameStatus.FINISHED
            for player_id in game.players:
                await self.repository.clear_player_active_game(player_id)
