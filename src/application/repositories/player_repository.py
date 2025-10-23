"""Defines the abstract repository for player registration."""
from abc import ABC, abstractmethod
from uuid import UUID
from src.domain.player import Player


class PlayerRegistrationRepository(ABC):
    """Abstract base class for player registration data operations."""
    @abstractmethod
    async def register_player(
        self,
        username: str,
        email: str,
        password: str,
    ) -> UUID:
        """Create a new player and return their UUID."""

    @abstractmethod
    async def get_player_by_id(self, player_id: UUID) -> Player:
        """Retrieve a player by ID."""

    @abstractmethod
    async def get_player_by_username(self, username: str) -> Player:
        """Check if username exists."""
