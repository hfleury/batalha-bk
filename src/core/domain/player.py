import uuid
from dataclasses import dataclass, field


@dataclass
class Player:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    username: str = field(default="")
    email: str = field(default="")
