"""Domain model for a player."""

import uuid
from typing import Optional, Self
from pydantic import BaseModel, Field


class Player(BaseModel):
    """Represents a player in the game.

    Attributes:
        id: The unique identifier for the player.
        username: The player's chosen username.
        email: The player's email address.
    """

    id: Optional[uuid.UUID] = None
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = Field(default=None, exclude=True)

    @property
    def id_str(self) -> str:
        """Returns the player's ID as a string. """
        return str(self.id)

    @classmethod
    def empty(cls) -> Self:
        """Creates an empty Player instance."""
        return cls()

    model_config = {
        "extra": "forbid",  # strict mode
    }
