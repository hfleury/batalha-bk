"""Domain model for a player."""

import uuid
from dataclasses import dataclass, field


@dataclass
class Player:
    """Represents a player in the game.

    Attributes:
        id: The unique identifier for the player.
        username: The player's chosen username.
        email: The player's email address.
    """

    id: uuid.UUID = field(default_factory=uuid.uuid4)
    username: str = field(default="")
    email: str = field(default="")
