import abc
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Type
from dataclasses import dataclass

# Standard ship types expected by the system
STANDARD_SHIPS = ["Carrier", "Battleship", "Cruiser", "Submarine", "Destroyer"]


class ShootStrategy(ABC):
    """Abstract base class for shooting strategies."""

    @property
    @abstractmethod
    def fuel_cost(self) -> int:
        """The fuel cost to use this strategy."""
        pass

    @abstractmethod
    def calculate_hits(self, target: str, board_size: int = 15) -> List[str]:
        """Calculates the list of coordinates affected by the shot.
        
        Args:
            target: The primary target coordinate (e.g., "A1").
            board_size: The size of the board (assumed square).

        Returns:
            A list of coordinate strings affected by the shot.
        """
        pass


class SingleShotStrategy(ShootStrategy):
    """Standard single-shot strategy."""

    @property
    def fuel_cost(self) -> int:
        return 0

    def calculate_hits(self, target: str, board_size: int = 15) -> List[str]:
        return [target]


class AreaShotStrategy(ShootStrategy):
    """Hits the target and adjacent cells (cross pattern)."""

    @property
    def fuel_cost(self) -> int:
        return 10

    def calculate_hits(self, target: str, board_size: int = 15) -> List[str]:
        # Basic parsing of coordinate A1 -> (row, col)
        # Assuming A=0, B=1... and numerics are 1-based index
        # This duplicates logic in game_actions.py slightly but is needed for domain logic
        # Ideally, coordinate logic should be centralized.
        # For now, implementing basic offset.
        
        row_char = target[0]
        try:
            col = int(target[1:])
        except ValueError:
            return [target] # Fallback

        row_idx = ord(row_char) - ord('A')
        col_idx = col - 1

        hits = []
        offsets = [(0, 0), (0, 1), (0, -1), (1, 0), (-1, 0)]

        for r_off, c_off in offsets:
            new_r = row_idx + r_off
            new_c = col_idx + c_off
            
            if 0 <= new_r < board_size and 0 <= new_c < board_size:
                # Convert back to string
                new_row_char = chr(new_r + ord('A'))
                hits.append(f"{new_row_char}{new_c + 1}")
        
        return hits


class HeavyShotStrategy(ShootStrategy):
    """Hits a 2x2 area bottom-right from target."""

    @property
    def fuel_cost(self) -> int:
        return 15

    def calculate_hits(self, target: str, board_size: int = 15) -> List[str]:
        row_char = target[0]
        try:
            col = int(target[1:])
        except ValueError:
            return [target]

        row_idx = ord(row_char) - ord('A')
        col_idx = col - 1

        hits = []
        # Target, Right, Down, Down-Right
        offsets = [(0, 0), (0, 1), (1, 0), (1, 1)]

        for r_off, c_off in offsets:
            new_r = row_idx + r_off
            new_c = col_idx + c_off
            
            if 0 <= new_r < board_size and 0 <= new_c < board_size:
                new_row_char = chr(new_r + ord('A'))
                hits.append(f"{new_row_char}{new_c + 1}")
        
        return hits


class Faction(ABC):
    """Abstract base class for a game faction."""

    @property
    @abstractmethod
    def name(self) -> str:
        """The name of the faction."""
        pass

    @property
    @abstractmethod
    def fuel_name(self) -> str:
        """The name of the resource used for special shots."""
        pass
    
    @property
    @abstractmethod
    def fuel_regeneration_rate(self) -> int:
        """Amount of fuel regenerated per turn."""
        pass

    @abstractmethod
    def get_ship_name(self, standard_type: str) -> str:
        """Returns the faction-specific name for a ship type."""
        pass

    @abstractmethod
    def get_shoot_strategy(self, ship_type: str) -> ShootStrategy:
        """Returns the shooting strategy for a specific ship type."""
        pass

    def regenerate_fuel(self, current_fuel: int, max_fuel: int = 100) -> int:
        """Calculates new fuel amount after regeneration."""
        return min(current_fuel + self.fuel_regeneration_rate, max_fuel)


class MarineFaction(Faction):
    """Marine faction: Disciplined, average fuel regen."""

    @property
    def name(self) -> str:
        return "Marines"

    @property
    def fuel_name(self) -> str:
        return "Ammo"

    @property
    def fuel_regeneration_rate(self) -> int:
        return 5

    def get_ship_name(self, standard_type: str) -> str:
        names = {
            "Carrier": "Aircraft Carrier",
            "Battleship": "Dreadnought",
            "Cruiser": "Battlecruiser",
            "Submarine": "U-Boat",
            "Destroyer": "Frigate",
        }
        return names.get(standard_type, standard_type)

    def get_shoot_strategy(self, ship_type: str) -> ShootStrategy:
        if ship_type == "Battleship":
            return AreaShotStrategy() # Special attack
        return SingleShotStrategy()


class PirateFaction(Faction):
    """Pirate faction: Aggressive, high outcome variance."""

    @property
    def name(self) -> str:
        return "Pirates"

    @property
    def fuel_name(self) -> str:
        return "Grog"

    @property
    def fuel_regeneration_rate(self) -> int:
        return 7 # Higher regen

    def get_ship_name(self, standard_type: str) -> str:
        names = {
            "Carrier": "Floating Fortress",
            "Battleship": "Man-o-War",
            "Cruiser": "Galleon",
            "Submarine": "Iron Turtle",
            "Destroyer": "Corsair",
        }
        return names.get(standard_type, standard_type)

    def get_shoot_strategy(self, ship_type: str) -> ShootStrategy:
        if ship_type == "Cruiser":
             return HeavyShotStrategy() # 2x2 blast
        return SingleShotStrategy()


class WinderFaction(Faction):
    """Winder faction: Technological/Scientific."""

    @property
    def name(self) -> str:
        return "Winders"

    @property
    def fuel_name(self) -> str:
        return "Aether"

    @property
    def fuel_regeneration_rate(self) -> int:
         return 3 # Slower regen but maybe stronger abilities (future)

    def get_ship_name(self, standard_type: str) -> str:
        names = {
            "Carrier": "Sky Fortress",
            "Battleship": "Tesla Coil",
            "Cruiser": "Storm Caller",
            "Submarine": "Abyss Walker",
            "Destroyer": "Wind Rider",
        }
        return names.get(standard_type, standard_type)

    def get_shoot_strategy(self, ship_type: str) -> ShootStrategy:
        if ship_type == "Submarine":
            return AreaShotStrategy() # Torpedo spread
        return SingleShotStrategy()


def get_faction(faction_name: str) -> Faction:
    """Factory method to get a faction instance by name."""
    factions = {
        "Marines": MarineFaction(),
        "Pirates": PirateFaction(),
        "Winders": WinderFaction(),
    }
    return factions.get(faction_name, MarineFaction()) # Default to Marines
