import uuid
from src.core.player.repositories import PlayerRegistrationRepository
import re
from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# Define allowed format once
VALID_USERNAME = re.compile(r"^[a-zA-Z0-9_]{3,32}$")


class PlayerRegistrationService:
    def __init__(self, repo: PlayerRegistrationRepository):
        self.repo = repo

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def _hash_password(self, password: str) -> str:
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
        # Optional: validate input format here
        if not VALID_USERNAME.match(username):
            raise ValueError("Username must be alphanumeric")

        # Check if user already exists
        existing = await self.repo.get_player_by_username(username)
        if existing:
            raise ValueError(f"Username '{username}' is already taken")

        if password != confirm_password:
            raise ValueError("Passwords do not match")

        hashed_password = self._hash_password(password)

        return await self.repo.register_player(username, email, hashed_password)
