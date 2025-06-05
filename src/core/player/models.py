import uuid
from fastapi import WebSocket
from src.core.interface.connection_protocol import ConnectionProtocol


class WebSocketConnection(ConnectionProtocol):
    """
    Represents a player in the Websocket connection.
    """

    def __init__(self, player_id: uuid.UUID, websocket: WebSocket):
        """
        Initialize a Player Object

        Args:
            player_id: The unique ID of the player
            websocket: The WebSocket connection object
        """
        self.player_id = player_id
        self.websocket = websocket

    async def send_message(self, message: str) -> None:
        """
        Sends a text message to the player's WebSocket connection

        Args:
            message: The message to be send
        """
        try:
            await self.websocket.send_text(message)
        except RuntimeError as e:
            print(f"Error sending message to Player {self.player_id}: {e}")
            raise

    async def close_connection(self) -> None:
        """
        Closes the Player's WebSocket connection.
        """
        await self.websocket.close()

    def __repr__(self) -> str:
        return f"WebSocketConnection(player_id={self.player_id})"
