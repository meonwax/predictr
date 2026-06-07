"""add users.excluded_from_ladder

Adds a boolean flag that hides a user from the ladder/scoreboard while
leaving the rest of their gameplay untouched. Defaults to false so every
existing account keeps competing; operators flip it directly in the
database for non-competing accounts.

Revision ID: 0002_user_excluded_from_ladder
Revises: 0001_initial
Create Date: 2026-06-07

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_user_excluded_from_ladder"
down_revision: str | Sequence[str] | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "excluded_from_ladder",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "excluded_from_ladder")
