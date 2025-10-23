"""Data validation schema for player information requests."""

import uuid

from pydantic import BaseModel, field_validator
from src.api.v1.schemas.validators import ensure_uuid


class PlayerInfoRequest(BaseModel):
    """Schema for a request to get information about a player in a game.

    Attributes:
        game_id: The unique identifier for the game.
        player_id: The unique identifier for the player.
    """

    game_id: uuid.UUID
    player_id: uuid.UUID

    _validate_uuids = field_validator("game_id", "player_id", mode="before")(
        ensure_uuid
    )
