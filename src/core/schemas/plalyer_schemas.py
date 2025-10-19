"""
Pydantic models for player registration API endpoints.

These schemas define the request and response payloads
for the /api/v1/players/register endpoint.

Note:
    This is separate from src/core/player/schemas.py,
    which contains game-related models like ShipPlacement.
"""

from pydantic import BaseModel, Field
from typing import Annotated


class PlayerRegisterRequest(BaseModel):
    """
    Request payload for registering a new player.
    """

    username: Annotated[
        str,
        Field(
            ...,
            min_length=3,
            max_length=32,
            pattern="^[a-zA-Z0-9_]+$",
            description="Alphanumeric username between 3 and 32 characters",
        ),
    ]
    email: Annotated[
        str,
        Field(..., description="Valid email address", pattern=r"^[^@]+@[^@]+\.[^@]+$"),
    ]
    password: str = Field(
        ...,
        min_length=6,
        description="Password must be at least 6 characteres",
    )
    confirm_password: str = Field(
        ...,
        min_length=6,
        description="Password must be at least 6 characteres",
    )


class PlayerRegisterResponse(BaseModel):
    """
    Response payload after successful player registration.
    """

    player_id: str = Field(..., description="Unique UUID of the registered player")
    username: str = Field(..., description="Player's chosen username")
    email: str = Field(..., description="Player's registered email")
