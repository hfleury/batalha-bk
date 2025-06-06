import logging
import uuid
import json
from typing import Any

from src.core.player.player_connection import PlayerConnection
from src.core.domain.player import Player

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and player state."""

    def __init__(self, max_players: int = 2) -> None:
        self.connected_players: dict[uuid.UUID, PlayerConnection] = {}
        self.max_players = max_players

    def get_new_player_id(self) -> uuid.UUID:
        """Generate a new unique player ID using UUID4."""
        return uuid.uuid4()

    def add_player(self, player_conn: PlayerConnection) -> None:
        """Add a player connection to the active player list."""
        self.connected_players[player_conn.player.id] = player_conn
        logger.info(f"Player {player_conn.player.id} connected.")

    def remove_player(self, player_id: uuid.UUID) -> None:
        """Remove a player from the connection list by ID."""
        if player_id in self.connected_players:
            del self.connected_players[player_id]
            logger.info(
                f"Player {player_id} removed. Remaining: {len(self.connected_players)}"
            )

    def get_player(self, player: Player) -> PlayerConnection | None:
        """Retrieve the PlayerConnection associated with a Player."""
        return self.connected_players.get(player.id)

    async def broadcast(
        self, message: str, excluded_player_id: uuid.UUID | None = None
    ) -> None:
        """
        Broadcast a message to all connected players, optionally excluding one.

        Removes disconnected players automatically.
        """
        to_remove: list[uuid.UUID] = []
        for player_id, player_conn in self.connected_players.items():
            if player_id == excluded_player_id:
                continue
            try:
                await player_conn.send_message(message)
            except Exception as e:
                logger.error(f"Failed to send to Player {player_id}: {e}")
                to_remove.append(player_id)

        for pid in to_remove:
            await self._remove_and_close(pid)

    async def _remove_and_close(self, player_id: uuid.UUID) -> None:
        """Gracefully remove and close a player's connection."""
        player = self.connected_players.get(player_id)
        if player:
            try:
                await player.close_connection()
            except Exception as e:
                logger.error(f"Error closing connection for Player {player_id}: {e}")
            self.remove_player(player_id)

    def default_encoder(self, obj):
        if isinstance(obj, uuid.UUID):
            return str(obj)
        raise TypeError(
            f"Object of type {obj.__class__.__name__} is not JSON serializable"
        )

    async def send_to_player(
        self, player_id: uuid.UUID, message: str | dict[str, Any]
    ) -> None:
        """Send a message to a specific player via WebSocket.
        If the player is disconnected, their connection is cleaned up.

        Args:
            player_id (uuid.UUID): The unique identifier of the player
            message (str): The message to be send
        """
        if isinstance(message, dict):
            message = json.dumps(message, default=self.default_encoder)
        player_conn = self.connected_players.get(player_id)
        if player_conn:
            try:
                await player_conn.send_message(message=message)
            except Exception as e:
                logger.error(
                    f"Failed to send message to Player: {player_id} error: {e}"
                )
                await self._remove_and_close(player_id)
