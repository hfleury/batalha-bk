import logging
from typing import Dict, Optional

from src.core.player.player_connection import Player

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self, max_players: int = 2) -> None:
        self.connected_players: Dict[int, Player] = {}
        self.next_player_id: int = 1
        self.max_players = max_players

    def get_available_player_id(self) -> int:
        for i in range(1, self.max_players + 1):
            if i not in self.connected_players:
                return i
        id_to_return = self.next_player_id + self.max_players
        self.next_player_id += 1
        return id_to_return

    def add_player(self, player_conn: Player) -> None:
        self.connected_players[player_conn.player_id] = player_conn

    def remove_player(self, player_id: int) -> None:
        if player_id in self.connected_players:
            del self.connected_players[player_id]
            logger.info(
                f"Player {player_id} removed. Remaining: {len(self.connected_players)}"
            )

    def get_player(self, player_id: int) -> Optional[Player]:
        return self.connected_players.get(player_id)

    async def broadcast(
        self, message: str, excluded_player_id: Optional[int] = None
    ) -> None:
        to_remove: list[int] = []
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

    async def _remove_and_close(self, player_id: int) -> None:
        player = self.connected_players.get(player_id)
        if player:
            try:
                await player.close_connection()
            except Exception as e:
                logger.error(f"Error closing connection for Player {player_id}: {e}")
            self.remove_player(player_id)
