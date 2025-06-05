from pydantic import BaseModel
import uuid


class PlayerInfoRequest(BaseModel):
    game_id: uuid.UUID
    player_id: str
