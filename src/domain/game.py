"""Domain models for the game state and related entities."""

import time
import uuid
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class GameStatus(str, Enum):
    """Enumeration for the status of a game session."""

    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"
    PLACE_SHIP = "place_ship"


class PlayerBoard(BaseModel):
    """Represents a player's board, containing their ship placements."""

    board: dict[str, list[str]] = Field(default_factory=dict)


class GameSession(BaseModel):
    """Represents the state of a single game session.

    Attributes:
        game_id: The unique identifier for the game.
        start_datetime: The Unix timestamp when the game started.
        end_datetime: The Unix timestamp when the game finished.
        players: A dictionary mapping player UUIDs to their respective boards.
        current_turn: The UUID of the player whose turn it is.
        status: The current status of the game.
    """

    game_id: uuid.UUID
    start_datetime: int = Field(default_factory=lambda: int(time.time()))
    end_datetime: int = 0
    players: dict[uuid.UUID, PlayerBoard]
    current_turn: uuid.UUID | None = None
    status: GameStatus = GameStatus.WAITING

    def to_serializable_dict(self) -> dict[str, Any]:
        """Converts the GameSession object to a JSON-serializable dictionary.

        Returns:
            A dictionary representation of the game session with UUIDs as strings.
        """
        return {
            "game_id": str(self.game_id),
            "start_datetime": self.start_datetime,
            "end_datetime": self.end_datetime,
            "players": {
                str(player_id): board.model_dump()
                for player_id, board in self.players.items()
            },
            "current_turn": str(self.current_turn) if self.current_turn is not None else None,
            "status": self.status.value,
        }

    @classmethod
    def from_serialized_dict(cls, data: dict[str, Any]) -> "GameSession":
        """Reconstructs GameSession from a dict produced by to_serializable_dict."""
        return cls(
            game_id=uuid.UUID(data["game_id"]),
            start_datetime=data["start_datetime"],
            end_datetime=data["end_datetime"],
            players={
                uuid.UUID(pid): PlayerBoard(**board_data)
                for pid, board_data in data["players"].items()
            },
            current_turn=uuid.UUID(data["current_turn"]) if data.get("current_turn") else None,
            status=GameStatus(data["status"]),
        )


class GameInfo(BaseModel):
    """Lightweight representation of game metadata stored in Redis."""

    game_id: str
    player1_id: str
    player2_id: str
    status: str
    created_at: str

    class Config:
        """Make the class immutable
        """
        frozen = True
