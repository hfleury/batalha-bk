from pydantic import BaseModel, Field
import uuid
import time
from typing import Any


class PlayerBoard(BaseModel):
    board: dict[str, list[str]] = Field(default_factory=dict)


class GameSession(BaseModel):
    game_id: uuid.UUID
    start_datetime: int = Field(default_factory=lambda: int(time.time()))
    end_datetime: int = 0
    players: dict[uuid.UUID, PlayerBoard]

    def to_serializable_dict(self) -> dict[str, Any]:
        return {
            "game_id": str(self.game_id),
            "start_datetime": self.start_datetime,
            "end_datetime": self.end_datetime,
            "players": {
                str(player_id): board.model_dump()
                for player_id, board in self.players.items()
            },
        }
