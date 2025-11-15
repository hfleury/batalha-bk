"""Handles all game notifications."""

import uuid
from dataclasses import dataclass
from typing import Optional
from src.infrastructure.manager.connection_manager import ConnectionManager
from src.api.v1.schemas.place_ships import StandardResponse
from src.domain.game import GameSession


@dataclass
class NotificationData:
    """Data class for notification parameters."""
    opponent_id: str
    target: str
    request_player_id: str
    current_turn: str
    ship_id: Optional[str] = None
    is_sunk: Optional[bool] = None


class NotificationService:
    """Handles all game notifications."""

    def __init__(self, conn_manager: ConnectionManager):
        self.conn_manager = conn_manager

    async def notify_opponent_hit(self, data: NotificationData) -> None:
        """Notify opponent about a hit."""
        notification = StandardResponse(
            status="hit",
            message=f"Opponent shot hit your ship at {data.target}!",
            action="enemy_shoot",
            data={
                "result": "hit",
                "cell": data.target,
                "ship_id": data.ship_id,
                "sunk": data.is_sunk,
                "opponent_turn": str(data.request_player_id),
                "your_turn_next": str(data.current_turn) == str(data.opponent_id)
            }
        )

        opponent_uuid = uuid.UUID(data.opponent_id)
        if self.conn_manager.is_player_connected(opponent_uuid):
            await self.conn_manager.send_to_player(
                opponent_uuid,
                notification.to_dict()
            )

    async def notify_opponent_miss(self, data: NotificationData) -> None:
        """Notify opponent about a miss."""
        notification = StandardResponse(
            status="miss",
            message=f"Opponent shot missed at {data.target}",
            action="enemy_shoot",
            data={
                "result": "miss",
                "cell": data.target,
                "opponent_turn": str(data.request_player_id),
                "your_turn_next": str(data.current_turn) == str(data.opponent_id)
            }
        )

        opponent_uuid = uuid.UUID(data.opponent_id)
        if self.conn_manager.is_player_connected(opponent_uuid):
            await self.conn_manager.send_to_player(
                opponent_uuid,
                notification.to_dict()
            )

    async def notify_victory(self, game: GameSession, winner_id: str) -> None:
        """Notify all players about victory."""
        victory_msg = StandardResponse(
            status="game_over",
            message=f"Player {winner_id} wins! All opponent ships destroyed!",
            action="game_ended",
            data={
                "winner": str(winner_id),
                "game_id": str(game.game_id)
            }
        )

        for player_id in game.players:
            if self.conn_manager.is_player_connected(player_id):
                await self.conn_manager.send_to_player(player_id, victory_msg.to_dict())
