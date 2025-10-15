"""Data validation schemas for game-related actions like starting or shooting."""

import uuid

from pydantic import BaseModel, field_validator
from src.core.schemas.validators import ensure_uuid


class StartGameRequest(BaseModel):
    """Schema for a request to start a new game."""

    game_id: str
    players: dict[str, dict[str, list[str]]]


class ShootRequest(BaseModel):
    """Schema for a player's request to shoot at a target."""

    game_id: uuid.UUID
    player_id: uuid.UUID
    target: str

    _validate_uuids = field_validator("game_id", "player_id", mode="before")(
        ensure_uuid
    )


class FindGameRequest(BaseModel):
    """Schema for a player's request to find a game session."""

    player_id: uuid.UUID
    _validate_uuids = field_validator("player_id", mode="before")(ensure_uuid)
