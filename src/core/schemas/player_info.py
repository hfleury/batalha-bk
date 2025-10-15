"""Data validation schema for player information requests."""

import uuid
from typing import Any

from pydantic import BaseModel, field_validator


class PlayerInfoRequest(BaseModel):
    """Schema for a request to get information about a player in a game.

    Attributes:
        game_id: The unique identifier for the game.
        player_id: The unique identifier for the player.
    """

    game_id: uuid.UUID
    player_id: uuid.UUID

    @field_validator("game_id", "player_id", mode="before")
    @classmethod
    def ensure_uuid(cls, v: Any) -> uuid.UUID:
        """Validate that a given value can be converted to a UUID."""
        if isinstance(v, uuid.UUID):
            return v
        try:
            return uuid.UUID(str(v))
        except ValueError as exc:
            raise ValueError("Invalid UUID format") from exc
