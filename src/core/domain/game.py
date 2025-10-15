import time
import uuid
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class GameStatus(str, Enum):
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"


class PlayerBoard(BaseModel):
    board: dict[str, list[str]] = Field(default_factory=dict)


class GameSession(BaseModel):
    game_id: uuid.UUID
    start_datetime: int = Field(default_factory=lambda: int(time.time()))
    end_datetime: int = 0
    players: dict[uuid.UUID, PlayerBoard]
    current_turn: uuid.UUID
    status: GameStatus = GameStatus.WAITING

    def to_serializable_dict(self) -> dict[str, Any]:
        return {
            "game_id": str(self.game_id),
            "start_datetime": self.start_datetime,
            "end_datetime": self.end_datetime,
            "players": {
                str(player_id): board.model_dump()
                for player_id, board in self.players.items()
            },
            "current_turn": str(self.current_turn),
            "status": self.status.value,
        }
