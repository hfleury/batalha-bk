"""Domain model for a ship."""

from dataclasses import dataclass


@dataclass
class Ship:
    """Represents a ship in the game.

    Attributes:
        name: The type or name of the ship (e.g., 'battleship').
        position: A list of strings representing the coordinates occupied by the ship.
    """

    name: str
    position: list[str]

    def is_sunk(self, hits: list[str]) -> bool:
        """Checks if the ship has been sunk.

        Args:
            hits: A list of coordinates that have been hit.

        Returns:
            True if all of the ship's positions are in the hits list, False otherwise.
        """
        return all(pos in hits for pos in self.position)
