from pydantic import BaseModel


class StartGameRequest(BaseModel):
    game_id: str
    players: dict[str, dict[str, list[str]]]
