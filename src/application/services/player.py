"""Player registration service containing business logic."""
import uuid
import logging
import re
from passlib.context import CryptContext  # type: ignore
from src.application.repositories.player_repository import PlayerRegistrationRepository
from src.domain.player import Player


logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# Define allowed format once
VALID_USERNAME = re.compile(r"^[a-zA-Z0-9_]{3,32}$")


class PlayerRegistrationService:
    """Handles the business logic for player registration."""

    def __init__(self, repo: PlayerRegistrationRepository):
        """Initializes the service with a player repository."""
        self.repo = repo

    def verify_password(self, plain_password: str, hashed_password: str | None) -> bool:
        """Verifies a plain password against a hashed one."""
        logger.debug(f"Verifying password for '{plain_password}' against hash")
        logger.debug(f"Hashed password from DB: {hashed_password}")
        return pwd_context.verify(plain_password, hashed_password)

    def _hash_password(self, password: str) -> str:
        """Hashes a password using bcrypt."""
        max_bcrypt_input = 72
        if len(password.encode("utf-8")) > max_bcrypt_input:
            print(f"Password truncate to {max_bcrypt_input} bytes")
            truncate = password.encode("utf-8")[:max_bcrypt_input].decode(
                "utf-8", errors="ignore"
            )
            return pwd_context.hash(truncate)

        return pwd_context.hash(password)

    async def register_new_player(
        self,
        username: str,
        email: str,
        password: str,
        confirm_password: str,
    ) -> uuid.UUID:
        """Registers a new player after validating input."""
        # Optional: validate input format here
        if not VALID_USERNAME.match(username):
            raise ValueError("Username must be alphanumeric")

        # Check if user already exists
        existing: Player = await self.repo.get_player_by_username(username)
        logger.debug(existing)
        if existing and existing.username is not None:
            logger.debug("ENTGROU AWQUIQN DOASJKLODNM AS P{ORRRAAAAAA   }")
            raise ValueError(f"Username '{username}' is already taken")

        if password != confirm_password:
            raise ValueError("Passwords do not match")

        hashed_password = self._hash_password(password)

        return await self.repo.register_player(username, email, hashed_password)

    async def get_player_by_username(self, username: str) -> Player:
        """
        Retrieve a player by username.

        Returns:
            Player object (dict or domain model), or None if not found.
        """
        return await self.repo.get_player_by_username(username)
