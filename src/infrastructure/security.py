"""JWT token creation and decoding."""
from datetime import datetime, timedelta, timezone
from typing import Optional, Any
from jose import jwt, JWTError  # type: ignore
from src.config import settings

# JWT config
SECRET_KEY = settings.jwt.secret_key
ALGORITHM = settings.jwt.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.jwt.access_token_expire_minutes


def create_access_token(
    data: dict[Any, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """Creates a new JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[dict[Any, Any]]:
    """Decodes a JWT access token and returns its payload."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
