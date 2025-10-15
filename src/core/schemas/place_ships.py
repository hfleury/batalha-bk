"""Data validation and serialization models for game actions."""

from typing import Any

from pydantic import BaseModel, Field


class SerializableModel(BaseModel):
    """A base model providing JSON and dictionary serialization methods."""

    def to_json(self) -> str:
        """Serializes the model to a JSON string."""
        return self.model_dump_json()

    def to_dict(self) -> dict[str, Any]:
        """Serializes the model to a dictionary."""
        return self.model_dump()


class ShipPlacementRequest(BaseModel):
    """Schema for validating a player's ship placement request.

    Attributes:
        game_id: The unique identifier for the game.
        player_id: The unique identifier for the player.
        ships: A dictionary mapping ship names to their list of coordinates.
    """

    game_id: str = Field(..., description="The ID of the game")
    player_id: str = Field(..., description="The ID of the player placing ships")
    ships: dict[str, list[str]] = Field(
        ..., description="Dictionary mapping ship names to coordinates"
    )


class StandardResponse(SerializableModel):
    """Standard response model for WebSocket communications.

    Attributes:
        status: The status of the response (e.g., 'OK', 'error').
        message: A human-readable message describing the outcome.
        action: The action this response corresponds to (e.g., 'resp_place_ships').
        data: The payload of the response, can be any type.
    """

    status: str
    message: str
    action: str
    data: Any
