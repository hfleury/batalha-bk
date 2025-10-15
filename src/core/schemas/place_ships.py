from typing import Any

from pydantic import BaseModel, Field


class SerializableModel(BaseModel):
    def to_json(self) -> str:
        return self.model_dump_json()

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()


class ShipPlacementRequest(BaseModel):
    game_id: str = Field(..., description="The ID of the game")
    player_id: str = Field(..., description="The ID of the player placing ships")
    ships: dict[str, list[str]] = Field(
        ..., description="Dictionary mapping ship names to coordinates"
    )


class StandardResponse(SerializableModel):
    status: str
    message: str
    action: str
    data: Any
