from src.core.domain.ship import Ship


def parse_ships(raw_ships: dict[str, list[str]]) -> list[Ship]:
    ships: list[Ship] = []

    for ship_name, positions in raw_ships.items():
        if not positions:
            raise ValueError(f"Invalid positions for ship {ship_name}")
        ships.append(Ship(name=ship_name, position=positions))

    return ships
