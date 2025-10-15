import uuid

from pydantic import BaseModel


class PlayerInfoRequest(BaseModel):
    game_id: uuid.UUID
    player_id: str
