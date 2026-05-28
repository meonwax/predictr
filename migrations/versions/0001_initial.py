"""initial schema

Creates the 12 tables that make up the Predictr domain model:
avatar, config, groups, question, venue, team, users, answer, game,
password_reset_token, shout, bet.

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-22

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "avatar",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("data", sa.LargeBinary(), nullable=False),
        sa.Column("mime_type", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "config",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("owner", sa.String(length=120), nullable=False),
        sa.Column("admin_email", sa.String(length=255), nullable=False),
        sa.Column("show_important_message", sa.Boolean(), nullable=False),
        sa.Column("points_result", sa.Integer(), nullable=False),
        sa.Column("points_tendency", sa.Integer(), nullable=False),
        sa.Column("points_tendency_spread", sa.Integer(), nullable=False),
        sa.Column("rules_en", sa.Text(), nullable=True),
        sa.Column("rules_de", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "groups",
        sa.Column("id", sa.String(length=4), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "question",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("question", sa.String(length=500), nullable=False),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("correct_answer", sa.String(length=500), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "venue",
        sa.Column("id", sa.BigInteger(), autoincrement=False, nullable=False),
        sa.Column("stadium", sa.String(length=255), nullable=False),
        sa.Column("city", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "team",
        sa.Column("id", sa.String(length=3), nullable=False),
        sa.Column("group_id", sa.String(length=4), nullable=False),
        sa.ForeignKeyConstraint(
            ["group_id"],
            ["groups.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("created_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_modified_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_login_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("avatar_id", sa.BigInteger(), nullable=True),
        sa.Column("preferred_language", sa.String(length=8), nullable=True),
        sa.Column("preferred_timezone", sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(
            ["avatar_id"],
            ["avatar.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_table(
        "answer",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("question_id", sa.BigInteger(), nullable=False),
        sa.Column("answer", sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(
            ["question_id"],
            ["question.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "game",
        sa.Column("id", sa.BigInteger(), autoincrement=False, nullable=False),
        sa.Column("kickoff_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("group_id", sa.String(length=4), nullable=False),
        sa.Column("venue_id", sa.BigInteger(), nullable=False),
        sa.Column("team_home_id", sa.String(length=3), nullable=True),
        sa.Column("team_away_id", sa.String(length=3), nullable=True),
        sa.Column("score_home", sa.Integer(), nullable=True),
        sa.Column("score_away", sa.Integer(), nullable=True),
        sa.Column("notes", sa.String(length=255), nullable=True),
        sa.Column("placeholder_home", sa.String(length=32), nullable=True),
        sa.Column("placeholder_away", sa.String(length=32), nullable=True),
        sa.ForeignKeyConstraint(
            ["group_id"],
            ["groups.id"],
        ),
        sa.ForeignKeyConstraint(
            ["team_away_id"],
            ["team.id"],
        ),
        sa.ForeignKeyConstraint(
            ["team_home_id"],
            ["team.id"],
        ),
        sa.ForeignKeyConstraint(
            ["venue_id"],
            ["venue.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "password_reset_token",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("val", sa.String(length=64), nullable=False),
        sa.Column("expiry", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("val"),
    )
    op.create_table(
        "shout",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("message", sa.String(length=1000), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "bet",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("game_id", sa.BigInteger(), nullable=False),
        sa.Column("score_home", sa.Integer(), nullable=True),
        sa.Column("score_away", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["game_id"],
            ["game.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "game_id", name="uk_bet_user_game"),
    )


def downgrade() -> None:
    op.drop_table("bet")
    op.drop_table("shout")
    op.drop_table("password_reset_token")
    op.drop_table("game")
    op.drop_table("answer")
    op.drop_table("users")
    op.drop_table("team")
    op.drop_table("venue")
    op.drop_table("question")
    op.drop_table("groups")
    op.drop_table("config")
    op.drop_table("avatar")
