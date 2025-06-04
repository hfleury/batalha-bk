from dataclasses import dataclass


@dataclass
class Ship:
    name: str
    position: list[str]

    def is_sunk(self, hits: list[str]) -> bool:
        return all(pos in hits for pos in self.position)
