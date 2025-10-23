"""Defines the abstract interface for game data persistence."""

import uuid
from abc import ABC, abstractmethod

from src.domain.game import GameSession
from src.domain.player import Player
from src.domain.ship import Ship


class GameRepository(ABC):
    """Abstract base class defining the contract for game data storage."""

    @abstractmethod
    async def save_player_board(
        self, game_id: str, player: Player, ships: list[Ship]
    ) -> None:
        """Saves a player's board (ship placements) to the repository."""
        pass

    @abstractmethod
    async def get_player_board(
        self, game_id: uuid.UUID, player_id: uuid.UUID
    ) -> dict[str, list[str]]:
        """Retrieves a player's board from the repository."""
        pass

    @abstractmethod
    async def get_opponent_id(
        self, game_id: uuid.UUID, player: Player
    ) -> uuid.UUID | None:
        """Finds the opponent's ID for a given game and player."""
        pass

    @abstractmethod
    async def get_player_hits(
        self, game_id: uuid.UUID, player: uuid.UUID
    ) -> dict[str, list[str]]:
        """Retrieves the recorded hits against a player's board."""
        pass

    @abstractmethod
    async def save_hit(
        self, game_id: uuid.UUID, player: uuid.UUID, ship_id: str, position: str
    ) -> None:
        """Records a hit on a specific position of a player's board."""
        pass

    @abstractmethod
    async def push_to_queue(self, queue_name: str, player: uuid.UUID) -> None:
        """Adds a player to a matchmaking queue."""
        pass

    @abstractmethod
    async def pop_from_queue(self, queue_name: str, player: uuid.UUID) -> None:
        """Removes a player from a matchmaking queue."""
        pass

    @abstractmethod
    async def save_game_session(self, game: GameSession) -> None:
        """Saves the entire game session state."""
        pass

    @abstractmethod
    async def save_game_to_redis(
        self,
        game: GameSession,
    ) -> None:
        """Saves the game state to Redis.

        Note: This might be a legacy or specific implementation detail.
        Consider consolidating with save_game_session.
        """
        pass

    @abstractmethod
    async def load_game_session(self, game_id: uuid.UUID) -> GameSession | None:
        """Loads a game session state from the repository."""
        pass

    @abstractmethod
    async def get_opponent_from_queue(
        self, queue_name: str, player_id: uuid.UUID
    ) -> uuid.UUID | None:
        """Retrieves an opponent for a player from the matchmaking queue."""
        pass
