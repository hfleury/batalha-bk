"""create casual table

Revision ID: b1abb72538c9
Revises: 064d04062820
Create Date: 2025-10-21 11:59:45.836916

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "b1abb72538c9"
down_revision: Union[str, Sequence[str], None] = "064d04062820"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        -- Create casual table
        CREATE TABLE IF NOT EXISTS casual_games (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            player1_id UUID REFERENCES players(id),
            player2_id UUID REFERENCES players(id),
            winner_id UUID REFERENCES players(id),
            played_at TIMESTAMPTZ,
        );

        CREATE INDEX IF NOT EXISTS
            idx_casual_games_player1_id ON casual_games(player1_id);
        CREATE INDEX IF NOT EXISTS
            idx_casual_games_player2_id ON casual_games(player2_id);
        CREATE INDEX IF NOT EXISTS
            idx_casual_games_winner_id ON casual_games(winner_id);
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE casual_games;")
