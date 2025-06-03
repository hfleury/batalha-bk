from typing import Dict, Protocol, Optional, runtime_checkable
import logging


logger = logging.getLogger(__name__)


@runtime_checkable
class ConnectionProtocol(Protocol):
    """
    Protocol for connection interfaces.
    Defines the methods that a connection interface should implement.
    """

    async def send_message(self, message: str) -> None:
        """
        Send a message to the player.

        Args:
            message: The message to be sent (string).
        """
        pass

    async def close_connection(self) -> None:
        """
        Close the connection to the player.
        """
        pass


class Player:
    def __init__(self, player_id: int, connection: ConnectionProtocol) -> None:
        """
        Initialize a Player instance.

        Args:
            player_id: The ID of the player.
            connection: The connection interface for the player.
        """
        self.player_id = player_id
        self.connection: ConnectionProtocol = connection

    async def send_message(self, message: str) -> None:
        """Send a new message

        Args:
            message (str): A string to be send
        """
        await self.connection.close_connection()

    async def close_connection(self) -> None:
        """Close the connection"""
        await self.connection.close_connection()


class ConnectionManager:
    """
    Manages the WebSocket connections for connected players.
    Handle adding, removing, and retrieving players as
    broadcast messages.
    """

    def __init__(self, max_players: int = 2) -> None:
        """
        Initialize the ConnectionManager(Constructor)
        """
        self.connected_players: Dict[int, Player] = {}
        self.next_player_id: int = 1
        self.max_players = max_players

    def get_available_player_id(self) -> int:
        """
        Returns first available player ID within max players limit,
        or increments beyond.
        TODO need it?
        """
        for i in range(1, self.max_players + 1):
            if i not in self.connected_players:
                return i

        # If all default slots taken, increment IDs
        id_to_return = self.next_player_id + self.max_players
        self.next_player_id += 1
        return id_to_return

    def add_player(self, player_conn: Player) -> None:
        """
        Adds a player to the connection ConnectionManager

        Args:
            player: The Player object to add.
        """
        self.connected_players[player_conn.player_id] = player_conn

    def remove_player(self, player_id: int) -> None:
        """
        Remove the player from the connection

        Args:
            player_id: the Player ID (int) to be removed.
        """
        if player_id in self.connected_players:
            del self.connected_players[player_id]
            logger.info(
                f"Player {player_id} was removed."
                " Total Connections: {len(self.connected_players)}"
            )

    def get_player(self, player_id: int) -> Player | None:
        """
        Retrieve a player by their ID

        Args:
            player_id: The ID of the player to retrieve
        """
        return self.connected_players.get(player_id)

    async def broadcast(
        self, message: str, excluded_player_id: Optional[int] | None = None
    ) -> None:
        """
        Sends a message to all connected player, optionally excluding one

        Args:
            message: The message to be send (string)
            excluded_player_id: The Id of the player to exclude.
        """
        to_remove: list[int] = []
        for player_id, player_conn in self.connected_players.items():
            if player_id == excluded_player_id:
                continue

            try:
                await player_conn.send_message(message)
            except Exception as e:
                logger.error(
                    f"Error sending message to Player {player_id}: {e}."
                    " Removing player from connection"
                )
                to_remove.append(player_id)

        for pid in to_remove:
            await self._remove_and_close(pid)

    async def _remove_and_close(self, player_id: int) -> None:
        player = self.connected_players.get(player_id)
        if player:
            try:
                await player.close_connection()
            except Exception as e:
                logger.error(f"Error closing connection for Player {player_id}: {e}")
            self.remove_player(player_id)


connection_manager = ConnectionManager()
