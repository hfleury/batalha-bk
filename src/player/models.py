from fastapi import WebSocket


class Player:
    """
    Represents a player in the Websocket connection.
    """

    def __init__(self, player_id: int, websocket: WebSocket):
        """
        Initialize a Player Object

        Args:
            player_id: The unique ID of the player
            websocket: The WebSocket connection object
        """
        self.player_id = player_id
        self.websocket = websocket

    async def send_message(self, message: str):
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

    async def close_connection(self):
        """
        Closes the Player's WebSocket connection.
        """
        await self.websocket.close()

    def __repr__(self):
        return f"Player(id={self.player_id})"
