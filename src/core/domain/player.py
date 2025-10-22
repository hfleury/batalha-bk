"""Domain model for a player."""

import uuid
from pydantic import BaseModel
from typing import Self


class Player(BaseModel):
    """Represents a player in the game.

    Attributes:
        id: The unique identifier for the player.
        username: The player's chosen username.
        email: The player's email address.
    """

    def __init__(
        self,
        id: uuid.UUID | None = None,
        username: str | None = None,
        email: str | None = None,
        password: str | None = None,
    ):
        self.id = id
        self.username = username
        self.email = email
        self.password = password

    id: uuid.UUID | None = None
    username: str | None = None
    email: str | None = None
    password: str | None = None

    @classmethod
    def empty(cls) -> Self:
        return cls()
