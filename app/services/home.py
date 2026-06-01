"""Read-only helpers for the home dashboard.

The home page is a small aggregation of *other* services' data: live and
upcoming matches from the games schedule, open special questions from
the question service, and recent shouts from the shoutbox. The queries
themselves are small enough (and specific enough to the home layout) to
keep here rather than threading them through the per-feature services
which already expose richer, page-specific reads.

Every function takes an optional ``now`` so tests can pin the wall clock
without monkey-patching :mod:`datetime`. Production callers leave it as
``None`` and get the current UTC time.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Final

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models import Bet, Game, User
from app.services.questions import QuestionForUser, list_questions_for_user

# A match runs ~90 minutes of regular time, up to 30 minutes of extra
# time, plus penalties and post-match interviews. Three hours covers the
# longest realistic match window. Anything past that without a recorded
# score is almost certainly a forgotten admin entry, not a live game.
LIVE_WINDOW: Final[timedelta] = timedelta(hours=3)

# Default upper bound for the upcoming-matches strip - the WC 2026
# group stage runs every day with several kickoffs, so eight matches
# is enough to cover ~2 days even at peak density without flooding the
# panel.
DEFAULT_UPCOMING_LIMIT: Final[int] = 8

# Default size for the open-questions panel. Mirrors the size used on
# the bets/ladder pages for consistency.
DEFAULT_OPEN_QUESTIONS_LIMIT: Final[int] = 5

# How far ahead the home page looks when deciding whether to nudge a
# user about unbet matches. 24 hours is short enough to feel urgent
# (the kickoff is "imminent") but long enough to cover the typical
# tournament-day cadence so the warning surfaces well before the
# bet deadline closes on each match.
IMMINENT_BET_WINDOW: Final[timedelta] = timedelta(hours=24)


def _now(now: datetime | None) -> datetime:
    """Normalise *now* to an aware UTC datetime."""
    if now is None:
        return datetime.now(UTC)
    if now.tzinfo is None:
        return now.replace(tzinfo=UTC)
    return now


# ---------------------------------------------------------------------------
# Matches
# ---------------------------------------------------------------------------


def live_games(
    db: Session,
    *,
    now: datetime | None = None,
    window: timedelta = LIVE_WINDOW,
) -> list[Game]:
    """Return matches currently in progress (kickoff passed, no score yet).

    The window cap stops abandoned/unscored matches from haunting the
    panel forever - if a match kicked off more than :data:`LIVE_WINDOW`
    ago and the admin still hasn't recorded a score, we hide it on the
    home page (it's still visible on ``/games`` and ``/admin/games``).
    """
    now = _now(now)
    earliest = now - window
    stmt = (
        select(Game)
        .options(joinedload(Game.venue), joinedload(Game.group))
        .where(
            and_(
                Game.kickoff_time <= now,
                Game.kickoff_time >= earliest,
                or_(Game.score_home.is_(None), Game.score_away.is_(None)),
            )
        )
        .order_by(Game.kickoff_time, Game.id)
    )
    return list(db.scalars(stmt).all())


def upcoming_games(
    db: Session,
    *,
    now: datetime | None = None,
    limit: int = DEFAULT_UPCOMING_LIMIT,
) -> list[Game]:
    """Return the next *limit* matches whose kickoff is still in the future.

    A ``limit`` of ``0`` or negative disables the cap so callers can
    request the whole forward schedule.
    """
    now = _now(now)
    stmt = (
        select(Game)
        .options(joinedload(Game.venue), joinedload(Game.group))
        .where(Game.kickoff_time > now)
        .order_by(Game.kickoff_time, Game.id)
    )
    if limit and limit > 0:
        stmt = stmt.limit(limit)
    return list(db.scalars(stmt).all())


# ---------------------------------------------------------------------------
# Questions
# ---------------------------------------------------------------------------


def open_questions_for_user(
    db: Session,
    user: User,
    *,
    now: datetime | None = None,
    limit: int = DEFAULT_OPEN_QUESTIONS_LIMIT,
) -> list[QuestionForUser]:
    """Return the soonest *limit* open questions, paired with *user*'s answers.

    "Open" = the deadline is still in the future. We delegate to
    :func:`app.services.questions.list_questions_for_user` so points,
    correct-answer gating, and answer pairing stay in exactly one
    place; here we just filter to the open subset and apply the
    home-panel cap.
    """
    entries = [e for e in list_questions_for_user(db, user, now=now) if e.can_answer]
    if limit and limit > 0:
        return entries[:limit]
    return entries


def has_unanswered_open_questions(
    entries: list[QuestionForUser],
) -> bool:
    """True iff *entries* contains at least one open question without an answer.

    Drives the home-page "do not forget to answer" reminder banner.
    """
    return any(e.answer is None for e in entries)


# ---------------------------------------------------------------------------
# Bets (imminent kickoff nudge)
# ---------------------------------------------------------------------------


def has_unbet_imminent_games(
    db: Session,
    user: User,
    *,
    now: datetime | None = None,
    window: timedelta = IMMINENT_BET_WINDOW,
) -> bool:
    """True iff *user* has at least one unbet match kicking off within *window*.

    "Imminent" is anchored at *now* and runs forward for *window* (default
    :data:`IMMINENT_BET_WINDOW`). Matches whose kickoff has already passed
    are intentionally excluded - the bet deadline is gone, the user has no
    action left to take. Matches further out than *window* are also
    excluded so the nudge stays urgent and doesn't degrade into permanent
    early-tournament noise (a freshly-registered user with no bets and a
    100-match schedule would otherwise see the warning forever).

    Implemented as a single ``NOT EXISTS`` query so it stays cheap on the
    home dashboard hot path even with hundreds of fixtures.
    """
    now = _now(now)
    cutoff = now + window
    user_bet_exists = select(Bet.id).where(Bet.game_id == Game.id, Bet.user_id == user.id).exists()
    stmt = (
        select(Game.id)
        .where(
            Game.kickoff_time > now,
            Game.kickoff_time <= cutoff,
            ~user_bet_exists,
        )
        .limit(1)
    )
    return db.scalar(stmt) is not None


__all__ = [
    "LIVE_WINDOW",
    "DEFAULT_UPCOMING_LIMIT",
    "DEFAULT_OPEN_QUESTIONS_LIMIT",
    "IMMINENT_BET_WINDOW",
    "live_games",
    "upcoming_games",
    "open_questions_for_user",
    "has_unanswered_open_questions",
    "has_unbet_imminent_games",
]
