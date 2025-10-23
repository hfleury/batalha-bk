"""Pydantic schemas for authentication."""
from pydantic import BaseModel


class LoginRequest(BaseModel):
    """Schema for user login requests."""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Schema for the JWT token response."""
    access_token: str
    token_type: str = "bearer"
