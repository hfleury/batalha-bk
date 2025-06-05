from pydantic import BaseModel
from typing import Any


class SerializableModel(BaseModel):
    def to_json(self) -> str:
        return self.model_dump_json()

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()


class ShipPlacementRequest(BaseModel):
    game_id: str
    player_id: str
    ships: dict[str, list[str]]


class StandardResponse(SerializableModel):
    status: str
    message: str
    action: str
    data: Any
