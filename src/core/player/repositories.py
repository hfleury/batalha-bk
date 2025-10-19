from abc import ABC, abstractmethod
from uuid import UUID


class PlayerRegistrationRepository(ABC):
    @abstractmethod
    async def register_player(
        self,
        username: str,
        email: str,
        hashed_password: str,
    ) -> UUID:
        """Create a new player and return their UUID."""

    @abstractmethod
    async def get_player_by_id(self, player_id: UUID) -> dict | None:
        """Retrieve a player by ID."""

    @abstractmethod
    async def get_player_by_username(self, username: str) -> dict | None:
        """Check if username exists."""
