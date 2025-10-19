# src/api/v1/auth_router.py
from fastapi import APIRouter, HTTPException, status, Request
from src.core.schemas.auth_schema import LoginRequest, TokenResponse
from src.core.secutiry import verify_password, create_access_token
from src.infra.psql.player_repo_impl import PostgresPlayerRegistrationRepository

router = APIRouter(prefix="/api/v1", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login_for_access_token(
    request_data: LoginRequest, request: Request
) -> TokenResponse:
    """
    Authenticate user and return JWT token.
    Expects JSON body with username and password.
    """
    # Get DB pool from app state
    pool = request.app.state.db_pool
    repo = PostgresPlayerRegistrationRepository(pool)

    # Fetch player by username
    player = await repo.get_player_by_username(request_data.username)
    if not player:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    if not verify_password(request_data.password, player["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create JWT token
    access_token = create_access_token(
        data={"sub": str(player["id"]), "username": player["username"]}
    )
    return TokenResponse(access_token=access_token)
