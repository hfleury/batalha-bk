"""Manages active WebSocket connections for players."""

import json
import logging
import uuid
from typing import Any

from src.domain.player import Player
from src.infrastructure.connection.player_connection import PlayerConnection

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and player state."""

    def __init__(self, max_players: int = 2) -> None:
        self.connected_players: dict[uuid.UUID, PlayerConnection] = {}
        self.player_game_map: dict[uuid.UUID, uuid.UUID] = {}  # player_id → game_id
        self.max_players = max_players

    def add_player(self, player_conn: PlayerConnection) -> None:
        """Add a player connection to the active player list."""
        if player_conn.player.id is not None:
            self.connected_players[player_conn.player.id] = player_conn
        logger.info(f"Player {player_conn.player.id} connected.")

    def remove_player(self, player_id: uuid.UUID | None) -> None:
        """Remove a player from the connection list by ID."""
        if player_id in self.connected_players and player_id is not None:
            del self.connected_players[player_id]
            if player_id in self.player_game_map:
                del self.player_game_map[player_id]
            logger.info(
                f"Player {player_id} removed. Remaining: {len(self.connected_players)}"
            )

    def get_player(self, player: Player) -> PlayerConnection | None:
        """Retrieve the PlayerConnection associated with a Player."""
        if player.id is not None:
            return self.connected_players.get(player.id)
        return None

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

    def default_encoder(self, obj: uuid.UUID) -> str:
        """JSON encoder for UUID objects, converting them to strings.

        Args:
            obj: The object to encode. Expected to be a UUID.

        Returns:
            The string representation of the UUID.
        """
        return str(obj)

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

    def add_player_to_game(self, player_id: uuid.UUID, game_id: uuid.UUID) -> None:
        """Associate a connected player with a specific game."""
        self.player_game_map[player_id] = game_id
        logger.debug(f"Player {player_id} associated with game {game_id}")

    def is_player_connected(self, player_id: uuid.UUID) -> bool:
        """Check if a player is currently connected via WebSocket."""
        return player_id in self.connected_players

    def get_player_game(self, player_id: uuid.UUID) -> uuid.UUID | None:
        """Get the game ID that a connected player is currently in."""
        return self.player_game_map.get(player_id)
