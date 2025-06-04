from pydantic import BaseModel


class ShipPlacementRequest(BaseModel):
    game_id: str
    player_id: str
    ships: dict[str, list[str]]


class StandardResponse(BaseModel):
    status: str
    message: str
