"""Domain model for a player."""

import uuid
from pydantic import BaseModel


class Player(BaseModel):
    """Represents a player in the game.

    Attributes:
        id: The unique identifier for the player.
        username: The player's chosen username.
        email: The player's email address.
    """

    id: uuid.UUID
    username: str
    email: str
    password: str | None = None
