"""Data validation schemas for game-related actions like starting or shooting."""

import uuid
import re
from typing import List

from pydantic import BaseModel, field_validator, Field
from .validators import ensure_uuid


class StartGameRequest(BaseModel):
    """Schema for a request to start a new game."""

    game_id: str
    players: dict[str, dict[str, list[str]]]


class ShootRequest(BaseModel):
    """Schema for a player's request to shoot at a target."""

    game_id: uuid.UUID
    player_id: uuid.UUID
    target: str

    _validate_uuids = field_validator("game_id", "player_id", mode="before")(
        ensure_uuid
    )


class FindGameRequest(BaseModel):
    """Schema for a player's request to find a game session."""

    player_id: uuid.UUID
    _validate_uuids = field_validator("player_id", mode="before")(ensure_uuid)


"""Data validation schemas for player-related actions."""

BOARD_SIZE = 15
LETTERS = [chr(i) for i in range(ord("A"), ord("O") + 1)]

# TODO validate if all ships are coming.
# TODO get the player_id from the connection manager
# TODO get the game_id from the connection manager


def is_valid_coordinate(coord: str) -> bool:
    """Check if the coordinate is valid (e.g., 'A1', 'B2', etc.)."""
    match = re.fullmatch(r"([A-O])([1-9])|1[0-5]", coord)
    return bool(match)


class ShipPlacement(BaseModel):
    """Schema for validating a player's ship placement request.

    Attributes:
        player_id: The ID of the player placing the ships.
        ships: A list of ships, where each ship is a list of its coordinates.
    """

    player_id: int = Field()
    ships: List[List[str]] = Field(
        ..., description="List of ships with their coordinates"
    )

    @classmethod
    @field_validator("ships")
    def validate_ship_coordinates(cls, ships: List[List[str]]) -> List[List[str]]:
        """Validate all ships' coordinates."""
        for ship in ships:
            if not all(is_valid_coordinate(coord) for coord in ship):
                raise ValueError(
                    "Invalid ship coordinates. Must be in the format 'A1', 'B2', etc."
                )
        return ships
