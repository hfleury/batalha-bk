import logging
from fastapi import APIRouter, HTTPException, status, Request, Depends

from src.core.schemas.auth_schema import LoginRequest, TokenResponse
from src.core.security import create_access_token
from src.core.services.player import PlayerRegistrationService
from src.infra.psql.player_repo_impl import PostgresPlayerRegistrationRepository
from src.core.config import settings


router = APIRouter(prefix="/api/v1", tags=["Authentication"])
logger = logging.getLogger(__name__)


def get_player_service(request: Request) -> PlayerRegistrationService:
    """Dependency: provides PlayerRegistrationService with live DB connection."""
    pool = request.app.state.db_pool
    repo = PostgresPlayerRegistrationRepository(pool)
    return PlayerRegistrationService(repo)


@router.post("/auth/login", response_model=TokenResponse)
async def login_for_access_token(
    request_data: LoginRequest,
    request: Request,
    service: PlayerRegistrationService = Depends(get_player_service),
) -> TokenResponse:
    """
    Authenticate user and return JWT token.
    Uses service layer for all business logic.
    """
    player = await service.get_player_by_username(request_data.username)
    if not player:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not service.verify_password(request_data.password, player.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={
            "sub": str(player.id),
            "username": player.username,
            "iss": settings.jwt.iss,
        }
    )
    return TokenResponse(access_token=access_token)
