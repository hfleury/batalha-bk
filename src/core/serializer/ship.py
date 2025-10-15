"""Utility function for parsing ship data from raw formats."""

from src.core.domain.ship import Ship


def parse_ships(raw_ships: dict[str, list[str]]) -> list[Ship]:
    """Parses a dictionary of raw ship data into a list of Ship domain objects.

    Args:
        raw_ships: A dictionary where keys are ship names and values are lists
            of their coordinate positions.

    Raises:
        ValueError: If a ship is provided with an empty list of positions.

    Returns:
        A list of Ship objects.
    """
    ships: list[Ship] = []

    for ship_name, positions in raw_ships.items():
        if not positions:
            raise ValueError(f"Invalid positions for ship {ship_name}")
        ships.append(Ship(name=ship_name, position=positions))

    return ships
