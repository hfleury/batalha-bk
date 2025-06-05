from pydantic import BaseModel, field_validator
from typing import Any
import uuid


class StartGameRequest(BaseModel):
    game_id: str
    players: dict[str, dict[str, list[str]]]


class ShootRequest(BaseModel):
    game_id: uuid.UUID
    player_id: uuid.UUID
    target: str

    @field_validator("game_id", "player_id", mode="before")
    def ensure_uuid(cls, v: Any) -> uuid.UUID:
        if isinstance(v, uuid.UUID):
            return v
        try:
            return uuid.UUID(str(v))
        except ValueError:
            raise ValueError("Invalid UUID format")


class FindGameRequest(BaseModel):
    player_id: uuid.UUID
