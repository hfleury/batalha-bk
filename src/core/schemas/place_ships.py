from pydantic import BaseModel
from typing import Any


class ShipPlacementRequest(BaseModel):
    game_id: str
    player_id: str
    ships: dict[str, list[str]]


class StandardResponse(BaseModel):
    status: str
    message: str
    action: str
    data: Any
