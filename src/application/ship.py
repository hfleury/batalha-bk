"""Utility function for parsing ship data from raw formats."""
import logging
from typing import Any, List

from src.api.v1.schemas.place_ships import ShipDetails

logger = logging.getLogger(__name__)


def parse_ships(raw_ships: List[dict[str, Any]]) -> List[ShipDetails]:
    """Parses a dictionary of raw ship data into a list of Ship domain objects.

    Args:
        raw_ships: A dictionary where keys are ship names and values are lists
            of their coordinate positions.

    Raises:
        ValueError: If a ship is provided with an empty list of positions.

    Returns:
        A list of Ship objects.
    """
    ships: List[ShipDetails] = []
    logger.debug(f"Raw ships: {raw_ships}")
    for raw_ship in raw_ships:
        ship_name = raw_ship.get("type")
        positions = raw_ship.get("positions")

        if not ship_name or not positions:
            raise ValueError("Invalid ship data format")

        ships.append(ShipDetails(type=ship_name, positions=positions))

    return ships
