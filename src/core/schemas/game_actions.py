"""Data validation schemas for game-related actions like starting or shooting."""

import uuid
from typing import Any

from pydantic import BaseModel, field_validator


class StartGameRequest(BaseModel):
    """Schema for a request to start a new game."""

    game_id: str
    players: dict[str, dict[str, list[str]]]


class ShootRequest(BaseModel):
    """Schema for a player's request to shoot at a target."""

    game_id: uuid.UUID
    player_id: uuid.UUID
    target: str

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


class FindGameRequest(BaseModel):
    """Schema for a player's request to find a game session."""

    player_id: uuid.UUID

    @field_validator("player_id", mode="before")
    @classmethod
    def ensure_uuid(cls, v: Any) -> uuid.UUID:
        """Validate that a given value can be converted to a UUID."""
        if isinstance(v, uuid.UUID):
            return v
        try:
            return uuid.UUID(str(v))
        except ValueError as exc:
            raise ValueError("Invalid UUID format") from exc
