import re
from typing import List

from pydantic import BaseModel, Field, field_validator

BOARD_SIZE = 15
LETTERS = [chr(i) for i in range(ord("A"), ord("O") + 1)]

#TODO validate if all ships are coming.
#TODO get the player_id from the connection manager
#TODO get the game_id from the connection manager

def is_valid_coordinate(coord: str) -> bool:
    """Check if the coordinate is valid (e.g., 'A1', 'B2', etc.)."""
    match = re.fullmatch(r"([A-O])([1-9])|1[0-5]", coord)
    return bool(match)


class ShipPlacement(BaseModel):
    player_id: int = Field()
    ships: List[List[str]] = Field(
        ..., description="List of ships with their coordinates"
    )

    @field_validator("ships", each_item=True)
    def validate_ship_coordinates(cls, ship: List[str]) -> List[str]:
        """Validate each ship's coordinates."""
        if not all(is_valid_coordinate(coord) for coord in ship):
            raise ValueError(
                "Invalid ship coordinates. Must be in the format 'A1', 'B2', etc."
            )
        return ship
