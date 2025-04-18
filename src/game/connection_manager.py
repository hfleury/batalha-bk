from typing import Dict

from src.player.models import Player


class ConnectionManager:
    """
    Manages the WebSocket connections for connected players.
    Handle adding, removing, and retrieving players as
    broadcast messages.
    """

    def __init__(self):
        """
        Initialize the ConnectionManager(Constructor)
        """
        self.connected_players: Dict[int, Player] = {}
        self.next_player_id: int = 1

    def get_available_player_id(self) -> int:
        """
        Gets the first available player ID (1 or 2) - since it is a test

        Returns:
            The available player ID (int)
        """

        if 1 not in self.connected_players:
            return 1
        elif 2 not in self.connected_players:
            return 2
        else:
            id_to_return = self.next_player_id
            self.next_player_id += 1
            return id_to_return

    def add_player(self, player: Player):
        """
        Adds a player to the connection ConnectionManager

        Args:
            player: The Player object to add.
        """
        self.connected_players[player.player_id] = player

    def remove_player(self, player_id: int):
        """
        Remove the player from the connection

        Args:
            player_id: the Player ID (int) to be removed.
        """
        if player_id in self.connected_players:
            del self.connected_players[player_id]

    def get_player(self, player_id: int) -> Player | None:
        """
        Retrieve a player by their ID

        Args:
            player_id: The ID of the player to retrieve
        """
        return self.connected_players.get(player_id)

    async def broadcast(self, message: str, excluded_player_id: int | None = None):
        """
        Sends a message to all connected player, optionally excluding one

        Args:
            message: The message to be send (string)
            excluded_player_id: The Id of the player to exclude.
        """
        for player_id, player in self.connected_players.items():
            if player_id != excluded_player_id:
                try:
                    await player.send_message(message)
                except RuntimeError:
                    print(
                        f"Error sending message to Player {player_id} during broadcast. Removing player"
                    )
                    self.remove_player(player_id)
                    await player.close_connection()


connection_manager = ConnectionManager()
