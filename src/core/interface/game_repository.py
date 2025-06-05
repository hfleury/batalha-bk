from abc import ABC, abstractmethod
import uuid
from typing import Any
from src.core.domain.player import Player
from src.core.domain.ship import Ship


class GameRepository(ABC):
    """The interface for the game repository

    Args:
        ABC (_type_): Helper class that provides a standard way to create an ABC using
        inheritance.
    """

    @abstractmethod
    async def save_player_board(
        self, game_id: str, player: Player, ships: list[Ship]
    ) -> None:
        pass

    @abstractmethod
    async def get_player_board(
        self, game_id: uuid.UUID, player_id: uuid.UUID
    ) -> dict[str, list[str]]:
        pass

    @abstractmethod
    async def get_opponent_id(
        self, game_id: uuid.UUID, player: Player
    ) -> uuid.UUID | None:
        pass

    @abstractmethod
    async def get_player_hits(
        self, game_id: uuid.UUID, player: uuid.UUID
    ) -> dict[str, list[str]]:
        pass

    @abstractmethod
    async def save_hit(
        self, game_id: uuid.UUID, player: uuid.UUID, ship_id: str, position: str
    ) -> None:
        pass

    @abstractmethod
    async def push_to_queue(self, queue_name: str, player: uuid.UUID) -> None:
        pass

    @abstractmethod
    async def pop_from_queue(self, queue_name: str) -> str | None:
        pass

    @abstractmethod
    async def save_game_session(self, game_key: str, game_data: Any) -> None:
        pass

    @abstractmethod
    async def save_game_to_redis(
        self,
        game_id: uuid.UUID,
        players_data: dict[str, dict[str, dict[str, list[str]]]],
    ) -> None:
        pass
