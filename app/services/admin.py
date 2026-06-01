"""Administrative business logic.

Right now this is *only* about entering official game results - the one
admin action without which the scoring loop never closes. Special-questions
admin and team-resolution for knockout TBDs live in later chunks.

All mutations commit inside the function (same pattern as
:mod:`app.services.users` and :mod:`app.services.bets`).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models import Bet, Game, Group, Team, User
from app.services.games import load_game, validate_score
from app.team_data import GROUP_STAGE_IDS, KNOCKOUT_GROUP_IDS

LOGGER = logging.getLogger(__name__)

# The DB `notes` column is `VARCHAR(255)`, but 255 chars in a tiny result
# annotation is silly. 64 comfortably fits the longest realistic note
# ("after extra time" / "after penalties") while keeping the admin form
# tidy and the table layout predictable.
MAX_NOTES_LEN: int = 64


# ---------------------------------------------------------------------------
# Domain exceptions
# ---------------------------------------------------------------------------


class NotesTooLong(ValueError):
    """Raised when the optional notes value exceeds :data:`MAX_NOTES_LEN`."""


class InvalidTeamAssignment(ValueError):
    """Raised when an admin tries to set knockout teams to invalid values.

    Carries a ``kind`` attribute so routes can map the error to a
    catalogue key without parsing the message:

    * ``"unknown_team"``  - supplied team code doesn't exist in ``team``
    * ``"same_team"``     - home and away resolved to the same team code
    * ``"not_knockout"``  - game belongs to a group stage; its teams come
      straight from the seed and aren't admin-editable
    """

    def __init__(self, message: str, *, kind: str) -> None:
        super().__init__(message)
        self.kind = kind


# ---------------------------------------------------------------------------
# Dashboard read-model
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class DashboardStats:
    """Quick-glance numbers rendered on the admin landing page."""

    user_count: int
    admin_count: int
    bet_count: int
    games_total: int
    games_finished: int
    games_pending_result: int
    games_upcoming: int


def get_dashboard_stats(db: Session, *, now: datetime | None = None) -> DashboardStats:
    """Compute the headline numbers shown on ``GET /admin``.

    *now* is overridable so tests can pin "current time" without
    monkey-patching :mod:`datetime`.
    """
    now = now or datetime.now(UTC)

    user_count = db.scalar(select(func.count()).select_from(User)) or 0
    admin_count = (
        db.scalar(select(func.count()).select_from(User).where(User.role == User.ROLE_ADMIN)) or 0
    )
    bet_count = db.scalar(select(func.count()).select_from(Bet)) or 0

    games_total = db.scalar(select(func.count()).select_from(Game)) or 0
    games_finished = (
        db.scalar(
            select(func.count())
            .select_from(Game)
            .where(
                Game.score_home.is_not(None),
                Game.score_away.is_not(None),
            )
        )
        or 0
    )
    games_pending_result = (
        db.scalar(
            select(func.count())
            .select_from(Game)
            .where(
                Game.kickoff_time <= now,
                (Game.score_home.is_(None)) | (Game.score_away.is_(None)),
            )
        )
        or 0
    )
    games_upcoming = games_total - games_finished - games_pending_result

    return DashboardStats(
        user_count=user_count,
        admin_count=admin_count,
        bet_count=bet_count,
        games_total=games_total,
        games_finished=games_finished,
        games_pending_result=games_pending_result,
        games_upcoming=games_upcoming,
    )


# ---------------------------------------------------------------------------
# Games list (for /admin/games)
# ---------------------------------------------------------------------------


def list_teams_grouped(db: Session) -> list[tuple[str, list[Team]]]:
    """Return group-stage teams as ``[(group_id, [team, ...]), ...]``.

    Ordered by group priority then team id so the admin team-picker
    dropdown shows groups A->L with teams in their seed order. Knockout
    pseudo-groups are filtered out (they hold no teams).
    """
    groups = list(
        db.scalars(
            select(Group)
            .options(selectinload(Group.teams))
            .where(Group.id.in_(tuple(GROUP_STAGE_IDS)))
            .order_by(Group.priority)
        ).all()
    )
    return [(g.id, sorted(g.teams, key=lambda t: t.id)) for g in groups]


def list_games_for_admin(
    db: Session,
    *,
    now: datetime | None = None,
) -> list[Game]:
    """Return every game with venue + group eagerly loaded.

    Ordered by kickoff time ascending so the most pressing rows
    (already-kicked-off-no-result) appear near the top.
    """
    # *now* is currently unused but accepted to keep the signature symmetric
    # with the bets service; admins likely want the same chronological
    # ordering regardless of clock skew.
    del now
    return list(
        db.scalars(
            select(Game)
            .options(joinedload(Game.venue), joinedload(Game.group))
            .order_by(Game.kickoff_time, Game.id)
        ).all()
    )


# ---------------------------------------------------------------------------
# Mutations
# ---------------------------------------------------------------------------


def _normalise_notes(notes: str | None) -> str | None:
    """Trim whitespace; treat blank/empty as None; enforce hard length cap."""
    if notes is None:
        return None
    cleaned = notes.strip()
    if not cleaned:
        return None
    if len(cleaned) > MAX_NOTES_LEN:
        raise NotesTooLong(
            f"Notes must be at most {MAX_NOTES_LEN} characters (got {len(cleaned)})."
        )
    return cleaned


def set_game_result(
    db: Session,
    *,
    game_id: int,
    score_home: int,
    score_away: int,
    notes: str | None = None,
) -> Game:
    """Record the official result for *game_id*.

    Setting a result on a future game is intentionally allowed - the UI
    discourages it (admin column shows the kickoff time) but the model
    doesn't forbid it; some admins prefer to enter results immediately
    after the final whistle rather than worrying about clock skew.

    Raises:
        :class:`GameNotFound`   game id doesn't exist
        :class:`InvalidScore`   home or away score out of range
        :class:`NotesTooLong`   notes longer than :data:`MAX_NOTES_LEN`
    """
    validate_score("score_home", score_home)
    validate_score("score_away", score_away)
    cleaned_notes = _normalise_notes(notes)

    game = load_game(db, game_id)
    game.score_home = score_home
    game.score_away = score_away
    game.notes = cleaned_notes
    db.commit()
    db.refresh(game)
    LOGGER.info(
        "Admin set result: game=%d -> %d:%d (notes=%r)",
        game_id,
        score_home,
        score_away,
        cleaned_notes,
    )
    return game


def _normalise_team_code(raw: str | None) -> str | None:
    if raw is None:
        return None
    cleaned = raw.strip().lower()
    return cleaned or None


def set_game_teams(
    db: Session,
    *,
    game_id: int,
    team_home_id: str | None,
    team_away_id: str | None,
) -> Game:
    """Resolve the knockout placeholders for *game_id*.

    The two arguments are FIFA 3-letter codes (case-insensitive) or
    ``None`` to clear a slot back to "TBD". Group-stage games refuse the
    operation: their teams come from the seed and don't change during the
    tournament. Existing bets on the fixture are intentionally preserved
    - the user bet on a game ID, not on a particular pair of teams, and
    re-shuffling the bracket shouldn't wipe everyone's predictions.

    Raises:
        :class:`GameNotFound`         game id doesn't exist
        :class:`InvalidTeamAssignment` invalid combination (see ``kind``)
    """
    home = _normalise_team_code(team_home_id)
    away = _normalise_team_code(team_away_id)

    game = load_game(db, game_id)
    group_id = game.group_id
    if group_id is not None and len(group_id) == 1 and group_id.isalpha():
        raise InvalidTeamAssignment(
            "Cannot edit teams for a group-stage fixture.",
            kind="not_knockout",
        )

    for code in (home, away):
        if code is not None and db.get(Team, code) is None:
            raise InvalidTeamAssignment(
                f"Unknown team code: {code!r}.",
                kind="unknown_team",
            )

    if home is not None and away is not None and home == away:
        raise InvalidTeamAssignment(
            "Home and away teams must differ.",
            kind="same_team",
        )

    game.team_home_id = home
    game.team_away_id = away
    db.commit()
    db.refresh(game)
    LOGGER.info(
        "Admin set teams: game=%d -> home=%r away=%r",
        game_id,
        home,
        away,
    )
    return game


def clear_game_result(db: Session, *, game_id: int) -> Game:
    """Remove the recorded result (and notes) from *game_id*.

    No-op when the game has no result. Raises :class:`GameNotFound` if
    the game id is unknown.
    """
    game = load_game(db, game_id)
    if game.score_home is None and game.score_away is None and game.notes is None:
        return game
    game.score_home = None
    game.score_away = None
    game.notes = None
    db.commit()
    db.refresh(game)
    LOGGER.info("Admin cleared result: game=%d", game_id)
    return game


def _validate_team_codes(
    db: Session,
    home: str | None,
    away: str | None,
) -> None:
    """Shared validation: both codes (if non-null) must exist and differ."""
    for code in (home, away):
        if code is not None and db.get(Team, code) is None:
            raise InvalidTeamAssignment(
                f"Unknown team code: {code!r}.",
                kind="unknown_team",
            )
    if home is not None and away is not None and home == away:
        raise InvalidTeamAssignment(
            "Home and away teams must differ.",
            kind="same_team",
        )


def save_admin_game(
    db: Session,
    *,
    game_id: int,
    score_home: int | None,
    score_away: int | None,
    notes: str | None,
    team_home_id: str | None = None,
    team_away_id: str | None = None,
    apply_teams: bool = False,
) -> Game:
    """Apply every editable admin field for *game_id* in one transaction.

    Used by the consolidated ``POST /admin/games/{id}`` handler so a row
    save persists score+notes+team-resolution atomically.

    Score fields:

    * Both ``None`` -> clear the recorded result (and notes) for this game.
    * Both set      -> store the result. ``notes`` is normalised by
      :func:`_normalise_notes`; ``"   "`` collapses to ``None``.
    * Mixed         -> rejected by the route before reaching this function.

    Team fields are looked at only when *apply_teams* is true (the route
    flips this on for knockout fixtures whose form actually carries the
    selects). Validation matches :func:`set_game_teams` exactly: codes are
    case-/whitespace-normalised, non-null codes must exist in ``team``,
    and home/away may not collapse to the same team. Group-stage games
    refuse the operation outright.

    Raises:
        :class:`GameNotFound`         game id doesn't exist
        :class:`InvalidScore`         home or away score out of range
        :class:`NotesTooLong`         notes longer than :data:`MAX_NOTES_LEN`
        :class:`InvalidTeamAssignment` invalid team combination (see ``kind``)
    """
    game = load_game(db, game_id)

    # Validate everything before mutating, so a teams error doesn't leave
    # a half-applied score behind.
    if score_home is not None and score_away is not None:
        validate_score("score_home", score_home)
        validate_score("score_away", score_away)
        cleaned_notes = _normalise_notes(notes)
    elif score_home is None and score_away is None:
        cleaned_notes = None
    else:
        # The route is expected to reject the mixed (one-set / one-blank)
        # case before we get here. Defensive raise so direct callers still
        # see a clear error.
        raise ValueError(
            "save_admin_game requires score_home and score_away to be both set or both None."
        )

    home_code: str | None = None
    away_code: str | None = None
    if apply_teams:
        if game.group_id not in KNOCKOUT_GROUP_IDS:
            raise InvalidTeamAssignment(
                "Cannot edit teams for a group-stage fixture.",
                kind="not_knockout",
            )
        home_code = _normalise_team_code(team_home_id)
        away_code = _normalise_team_code(team_away_id)
        _validate_team_codes(db, home_code, away_code)

    # Apply.
    if score_home is None and score_away is None:
        game.score_home = None
        game.score_away = None
        game.notes = None
    else:
        game.score_home = score_home
        game.score_away = score_away
        game.notes = cleaned_notes

    if apply_teams:
        game.team_home_id = home_code
        game.team_away_id = away_code

    db.commit()
    db.refresh(game)
    LOGGER.info(
        "Admin saved game: game=%d score=%r:%r notes=%r teams=%r:%r",
        game_id,
        game.score_home,
        game.score_away,
        game.notes,
        game.team_home_id if apply_teams else "<unchanged>",
        game.team_away_id if apply_teams else "<unchanged>",
    )
    return game


__all__ = [
    "MAX_NOTES_LEN",
    "DashboardStats",
    "InvalidTeamAssignment",
    "NotesTooLong",
    "get_dashboard_stats",
    "list_games_for_admin",
    "list_teams_grouped",
    "save_admin_game",
    "set_game_result",
    "set_game_teams",
    "clear_game_result",
    "KNOCKOUT_GROUP_IDS",
]
