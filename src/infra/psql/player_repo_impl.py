import asyncpg
from uuid import UUID
from src.core.player.repositories import PlayerRegistrationRepository


class PostgresPlayerRegistrationRepository(PlayerRegistrationRepository):
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def register_player(
        self,
        username: str,
        email: str,
        hashed_password: str,
    ) -> UUID:
        async with self.pool.acquire() as conn:
            try:
                row = await conn.fetchrow(
                    """
                    INSERT INTO players (username, email, password)
                    VALUES ($1, $2, $3)
                    RETURNING id
                    """,
                    username,
                    email,
                    hashed_password,
                )
                return row["id"]
            except asyncpg.UniqueViolationError as e:
                if "username" in str(e).lower():
                    raise ValueError(f"Username '{username}' is already taken.")
                elif "email" in str(e).lower():
                    raise ValueError(f"Email '{email}' is already registered.")
                else:
                    raise ValueError("Player already exists.")

    async def get_player_by_id(self, player_id: UUID) -> dict | None:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, username, email, created_at FROM players WHERE id = $1",
                player_id,
            )
            return dict(row) if row else None

    async def get_player_by_username(self, username: str) -> dict | None:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, username, email, created_at
                FROM players
                WHERE username = $1
                """,
                username,
            )
            return dict(row) if row else None
