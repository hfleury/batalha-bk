import asyncpg  # type: ignore
from uuid import UUID
from src.core.player.repositories import PlayerRegistrationRepository
from src.core.domain.player import Player


class PostgresPlayerRegistrationRepository(PlayerRegistrationRepository):
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def register_player(
        self,
        username: str,
        email: str,
        password: str,
    ) -> UUID:
        async with self.pool.acquire() as conn:  # type: ignore
            try:
                row = await conn.fetchrow(  # type: ignore
                    """
                    INSERT INTO players (username, email, password)
                    VALUES ($1, $2, $3)
                    RETURNING id
                    """,
                    username,
                    email,
                    password,
                )
                if row:
                    return row["id"]
                # This case should ideally not be hit if RETURNING id is used on a
                # successful insert.
                # But as a fallback, we can raise an error.
                raise ValueError("Failed to register player, no ID returned.")
            except asyncpg.UniqueViolationError as e:
                if "username" in str(e).lower():
                    raise ValueError(f"Username '{username}' is already taken.")
                elif "email" in str(e).lower():
                    raise ValueError(f"Email '{email}' is already registered.")
                else:
                    # Re-raise with a more generic message if the specific column is
                    # not identified
                    raise ValueError(
                        "A player with the given details already exists."
                    ) from e

    async def get_player_by_id(self, player_id: UUID) -> Player:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, username, email FROM players WHERE id = $1", player_id
            )
            if row:
                return Player(
                    id=row["id"], username=row["username"], email=row["email"]
                )
            return Player()

    async def get_player_by_username(self, username: str) -> Player:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, username, email, password
                FROM players
                WHERE username = $1
                """,
                username,
            )
            if row:
                return Player(
                    id=row["id"],
                    username=row["username"],
                    email=row["email"],
                    password=row["password"],
                )
        return None
