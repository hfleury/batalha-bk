"""Validates game state and actions."""

from typing import Optional
from src.domain.game import GameSession, GameStatus
from src.api.v1.schemas.place_ships import StandardResponse
from src.application.builders.response import ResponseBuilder


class GameValidator:
    """Validates game state and actions."""

    @staticmethod
    def validate_shoot(game: GameSession, player_id: str) -> Optional[StandardResponse]:
        """Validate shoot action."""
        if not game:
            return ResponseBuilder.error("Game not found", "shoot_result")

        if game.status != GameStatus.IN_PROGRESS:
            return ResponseBuilder.error("Game is not active", "shoot_result")

        if player_id != game.current_turn:
            return ResponseBuilder.error("It's not your turn", "shoot_result")

        return None

    @staticmethod
    def validate_turn_pass(
        game: GameSession,
        player_id: str
    ) -> Optional[StandardResponse]:
        """Validate turn pass action."""
        if not game:
            return ResponseBuilder.error("Game not found", "error_confirm_pass_turn")

        if game.status != GameStatus.IN_PROGRESS:
            return ResponseBuilder.error(
                "Game is not active", "error_confirm_pass_turn"
            )

        if player_id != game.current_turn:
            return ResponseBuilder.error(
                "It's not your turn to pass",
                "error_confirm_pass_turn"
            )

        return None
