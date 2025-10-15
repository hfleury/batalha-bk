"""Binds a player domain object to a connection protocol."""

from src.core.domain.player import Player
from src.core.interface.connection_protocol import ConnectionProtocol


class PlayerConnection:
    """Represents an active player's connection.

    This class links a `Player` domain object with a concrete implementation
    of the `ConnectionProtocol`, allowing for sending messages and managing
    the connection state for a specific player.

    Attributes:
        player: The domain object representing the player.
        connection: The protocol object for handling the connection.
    """

    def __init__(self, player: Player, connection: ConnectionProtocol) -> None:
        """Initializes the PlayerConnection.

        Args:
            player: The player domain object.
            connection: The connection protocol implementation.
        """
        self.player = player
        self.connection = connection

    async def send_message(self, message: str) -> None:
        """Sends a message to the player via the underlying connection."""
        await self.connection.send_message(message)

    async def close_connection(self) -> None:
        """Closes the underlying connection for the player."""
        await self.connection.close_connection()
