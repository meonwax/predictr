"""SQLAlchemy 2.0 ORM models for predictr.

Column names are ``snake_case`` and table names are singular (``user``,
``bet``, ``answer``, ...) so the ``seeds/wc2026.sql`` script and the
Alembic migration can describe the same schema with no per-side
translation. The full schema lives in
``migrations/versions/0001_initial.py``; this module is the runtime ORM
view of it.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Common declarative base for every model."""


# ---------------------------------------------------------------------------
# Reference data (loaded from seed files)
# ---------------------------------------------------------------------------


class Group(Base):
    """A tournament group ('a'..'l') or a knockout pseudo-group ('r32', 'qf', ...)."""

    __tablename__ = "groups"  # 'group' is reserved in SQL

    # Widened to 4 chars (was CHAR(1)) so the WC 2026 knockout pseudo-groups
    # like 'r32', 'qf', 'fin' fit.
    id: Mapped[str] = mapped_column(String(4), primary_key=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False)

    teams: Mapped[list[Team]] = relationship(back_populates="group")
    games: Mapped[list[Game]] = relationship(back_populates="group", order_by="Game.kickoff_time")


class Team(Base):
    __tablename__ = "team"

    id: Mapped[str] = mapped_column(String(3), primary_key=True)
    group_id: Mapped[str] = mapped_column(String(4), ForeignKey("groups.id"), nullable=False)

    group: Mapped[Group] = relationship(back_populates="teams")


class Venue(Base):
    __tablename__ = "venue"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    stadium: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(64), nullable=False)


class Game(Base):
    __tablename__ = "game"

    # Note: explicit IDs come from the seed file (matches the FIFA match numbers),
    # so the column is *not* autoincrement.
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    kickoff_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    group_id: Mapped[str] = mapped_column(String(4), ForeignKey("groups.id"), nullable=False)
    venue_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("venue.id"), nullable=False)
    # Nullable for knockout fixtures until the bracket is resolved.
    team_home_id: Mapped[str | None] = mapped_column(
        String(3), ForeignKey("team.id"), nullable=True
    )
    team_away_id: Mapped[str | None] = mapped_column(
        String(3), ForeignKey("team.id"), nullable=True
    )
    score_home: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score_away: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Short human-readable label shown in the UI while a knockout slot's
    # team is still unknown - e.g. "1A" (winner of group A), "2C" (runner-up
    # of group C), "W74" (winner of match 74). Null for group-stage games,
    # where ``team_home_id`` / ``team_away_id`` are always populated by the
    # seed.
    placeholder_home: Mapped[str | None] = mapped_column(String(32), nullable=True)
    placeholder_away: Mapped[str | None] = mapped_column(String(32), nullable=True)

    group: Mapped[Group] = relationship(back_populates="games")
    venue: Mapped[Venue] = relationship()
    team_home: Mapped[Team | None] = relationship(foreign_keys=[team_home_id])
    team_away: Mapped[Team | None] = relationship(foreign_keys=[team_away_id])
    bets: Mapped[list[Bet]] = relationship(back_populates="game")


# ---------------------------------------------------------------------------
# Per-user data
# ---------------------------------------------------------------------------


class Avatar(Base):
    __tablename__ = "avatar"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(64), nullable=False)


class User(Base):
    __tablename__ = "users"  # 'user' is reserved in SQL

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    created_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_modified_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_login_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    avatar_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("avatar.id"), nullable=True
    )
    preferred_language: Mapped[str | None] = mapped_column(String(8), nullable=True)
    # IANA timezone name (``Europe/Berlin``, ``America/New_York``, ...) used
    # to localise date/time *display*. All stored timestamps remain UTC;
    # nullable so newly-registered users inherit ``Settings.default_timezone``
    # the same way they inherit ``Settings.default_language``.
    preferred_timezone: Mapped[str | None] = mapped_column(String(64), nullable=True)

    avatar: Mapped[Avatar | None] = relationship()
    bets: Mapped[list[Bet]] = relationship(back_populates="user")
    answers: Mapped[list[Answer]] = relationship(back_populates="user")
    shouts: Mapped[list[Shout]] = relationship(back_populates="user")

    # Role constants stored on ``users.role``. The literal values are
    # compared as raw strings (in the seed file and the admin
    # promote/demote CLI), so the ``ROLE_*`` prefix is intentional and
    # must not be changed without a migration.
    ROLE_ADMIN = "ROLE_ADMIN"
    ROLE_USER = "ROLE_USER"


class Bet(Base):
    __tablename__ = "bet"
    __table_args__ = (UniqueConstraint("user_id", "game_id", name="uk_bet_user_game"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    game_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("game.id"), nullable=False)
    score_home: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score_away: Mapped[int | None] = mapped_column(Integer, nullable=True)

    user: Mapped[User] = relationship(back_populates="bets")
    game: Mapped[Game] = relationship(back_populates="bets")


class Question(Base):
    __tablename__ = "question"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    question: Mapped[str] = mapped_column(String(500), nullable=False)
    deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    points: Mapped[int] = mapped_column(Integer, nullable=False)
    correct_answer: Mapped[str | None] = mapped_column(String(500), nullable=True)

    answers: Mapped[list[Answer]] = relationship(back_populates="question")


class Answer(Base):
    __tablename__ = "answer"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    question_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("question.id"), nullable=False)
    answer: Mapped[str | None] = mapped_column(String(500), nullable=True)

    user: Mapped[User] = relationship(back_populates="answers")
    question: Mapped[Question] = relationship(back_populates="answers")


class Shout(Base):
    __tablename__ = "shout"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    message: Mapped[str] = mapped_column(String(1000), nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)

    user: Mapped[User] = relationship(back_populates="shouts")


class Config(Base):
    """Site-wide configuration row (single-row table in practice)."""

    __tablename__ = "config"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    owner: Mapped[str] = mapped_column(String(120), nullable=False)
    admin_email: Mapped[str] = mapped_column(String(255), nullable=False)
    show_important_message: Mapped[bool] = mapped_column(Boolean, nullable=False)
    points_result: Mapped[int] = mapped_column(Integer, nullable=False)
    points_tendency: Mapped[int] = mapped_column(Integer, nullable=False)
    points_tendency_spread: Mapped[int] = mapped_column(Integer, nullable=False)
    rules_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    rules_de: Mapped[str | None] = mapped_column(Text, nullable=True)


class PasswordResetToken(Base):
    __tablename__ = "password_reset_token"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    # 'value' is reserved in some SQL dialects, so the column is named 'val'.
    val: Mapped[str] = mapped_column("val", String(64), unique=True, nullable=False)
    expiry: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)

    user: Mapped[User] = relationship()


__all__ = [
    "Base",
    "Group",
    "Team",
    "Venue",
    "Game",
    "Avatar",
    "User",
    "Bet",
    "Question",
    "Answer",
    "Shout",
    "Config",
    "PasswordResetToken",
]
