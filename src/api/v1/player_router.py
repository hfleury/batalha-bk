"""
Defines the player registration route for the Batalha Naval API.

This router handles player registration via HTTP POST.
Players are persisted in PostgreSQL using a clean dependency flow:
    Router → PlayerRegistrationService → PostgresPlayerRegistrationRepository → asyncpg

All routes are under the /api/v1 namespace.
"""

import asyncpg
import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from .http_routes import v1_router
from src.core.services.player import PlayerRegistrationService
from src.infra.psql.player_repo_impl import PostgresPlayerRegistrationRepository
from src.core.player.repositories import PlayerRegistrationRepository
from src.core.schemas.plalyer_schemas import (
    PlayerRegisterRequest,
    PlayerRegisterResponse,
)

logger = logging.getLogger(__name__)


# Optional: Add startup/shutdown logic if needed later
@asynccontextmanager
async def lifespan(router: APIRouter) -> AsyncGenerator[None, None]:
    # You can add per-router setup/teardown here if needed
    yield


# --- Dependency Injection ---
def get_player_registration_service(request: Request) -> PlayerRegistrationService:
    """
    Dependency factory that provides a PlayerRegistrationService instance.

    Retrieves the database connection pool from app state and injects it into the
    repository.

    Args:
        request: FastAPI request object (used to access app state)

    Returns:
        Configured PlayerRegistrationService
    """
    try:
        pool = request.app.state.db_pool
        if not pool:
            raise RuntimeError("Database pool not available in app state")
    except AttributeError:
        raise RuntimeError("Database pool not initialized")

    # Create concrete repository and service
    repo: PlayerRegistrationRepository = PostgresPlayerRegistrationRepository(pool)
    return PlayerRegistrationService(repo)


# --- Routes ---
@v1_router.post(
    "/players/register",
    response_model=PlayerRegisterResponse,
    status_code=201,
    summary="Register a New Player",
    description="""
    Registers a new player with a username and email.
    Returns the generated player ID.
    Username must be unique and alphanumeric.
    Email must be valid and unique.
    """,
    responses={
        201: {
            "description": "Player successfully registered.",
            "content": {
                "application/json": {
                    "example": {
                        "player_id": "a1b2c3d4-5678-90ef-1234-567890abcdef",
                        "username": "capitao_nemo",
                        "email": "nemo@submarine.org",
                    }
                }
            },
        },
        400: {
            "description": "Validation or business rule error"
            "(e.g., duplicate username)"
        },
        500: {"description": "Internal server error"},
    },
)
async def register_player(
    request_body: PlayerRegisterRequest,
    service: PlayerRegistrationService = Depends(get_player_registration_service),
) -> PlayerRegisterResponse:
    """
    Handle player registration request.

    Args:
        request_body: Validated input data (username, email)
        service: Injected service for business logic

    Returns:
        PlayerRegisterResponse with assigned player ID
    """
    try:
        player_id = await service.register_new_player(
            username=request_body.username,
            email=request_body.email,
            password=request_body.password,
            confirm_password=request_body.confirm_password,
        )
        return PlayerRegisterResponse(
            player_id=str(player_id),
            username=request_body.username,
            email=request_body.email,
        )

    except ValueError as ve:
        # Business logic errors (e.g., invalid username, already exists)
        raise HTTPException(status_code=400, detail=str(ve))

    except asyncpg.UniqueViolationError as ue:
        # Shouldn't happen due to service-layer check, but safe fallback
        if "username" in str(ue).lower():
            raise HTTPException(
                status_code=400,
                detail=f"Username '{request_body.username}' is already taken.",
            )
        elif "email" in str(ue).lower():
            raise HTTPException(
                status_code=400,
                detail=f"Email '{request_body.email}' is already registered.",
            )
        else:
            raise HTTPException(status_code=400, detail="Player already exists.")

    except Exception as e:
        # Unexpected errors
        logger = logging.getLogger("uvicorn")
        logger.error(f"Unexpected error during player registration: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An internal error occurred. Please try again later.",
        )


# Optional: Health check specific to this router
@v1_router.get("/players/health", include_in_schema=False)
async def health_check() -> dict[str, str]:
    """Simple health check for player service."""
    return {"status": "ok", "module": "player_registration"}
