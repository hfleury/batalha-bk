"""Create players table

Revision ID: 064d04062820
Revises:
Create Date: 2025-10-21 11:41:09.064039

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "064d04062820"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
               -- Enable pgcrypto for gen_random_uuid()
                CREATE EXTENSION IF NOT EXISTS "pgcrypto";

                -- Create players table
                CREATE TABLE IF NOT EXISTS players (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    username VARCHAR(32) UNIQUE NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                    deleted_at TIMESTAMPTZ DEFAULT NULL
                );

                -- Indexes (optional, but helpful)
                CREATE INDEX IF NOT EXISTS idx_players_username ON players(username);
                CREATE INDEX IF NOT EXISTS idx_players_email ON players(email);
               """
    )


def downgrade() -> None:
    op.execute("DROP TABLE players;")
