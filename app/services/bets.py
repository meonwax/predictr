"""Business logic for the ``/bets`` page.

Three public entry points:

* :func:`list_games_with_bets` - fetch every game alongside the current
  user's bet (if any) and the points earned (after the official result is
  in). Sorted by kickoff time, then game id.
* :func:`upsert_bet` - insert or update one bet, with kickoff-time and
  range validation.
* :func:`delete_bet` - remove a bet (deadline still applies).

The cut-off is strict: once ``game.kickoff_time`` is in the past, the bet
is frozen. This is the one piece of game UX that materially affects
fairness, so the deadline check is enforced at the service layer (not in
the route handler) to keep it impossible to bypass.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import NamedTuple

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Bet, Game, Group, User
from app.services.scoring import calculate_bet_points

LOGGER = logging.getLogger(__name__)

# Score validation bounds. Two-digit scores per side cover every realistic
# football result; anything outside 0..99 is effectively a typo.
MIN_SCORE: int = 0
MAX_SCORE: int = 99


# ---------------------------------------------------------------------------
# Domain exceptions
# ---------------------------------------------------------------------------


class GameNotFound(KeyError):
    """Raised when the game id passed to the service doesn't exist."""


class BetDeadlinePassed(Exception):
    """Raised when an upsert/delete is attempted after kickoff."""


class InvalidScore(ValueError):
    """Raised when a supplied score is outside the accepted range.

    Carries machine-readable ``field`` (``"score_home"`` / ``"score_away"``)
    and ``kind`` (``"not_int"`` / ``"range"``) attributes so the route layer
    can translate the message without parsing strings. The base ``args``
    still carry the English message for log compatibility.
    """

    def __init__(self, message: str, *, field: str | None = None, kind: str | None = None) -> None:
        super().__init__(message)
        self.field = field
        self.kind = kind


# ---------------------------------------------------------------------------
# Read model
# ---------------------------------------------------------------------------


class GameWithBet(NamedTuple):
    """Read-model entry for the bets page.

    * ``game``       - full Game row, with venue + group eagerly loaded.
    * ``bet``        - the current user's bet, or ``None``.
    * ``points``     - points earned (>=0). Always 0 until both bet and
                       official result are present.
    * ``can_bet``    - whether the current user can still edit this bet
                       (kickoff is still in the future).
    """

    game: Game
    bet: Bet | None
    points: int
    can_bet: bool


def list_games_with_bets(
    db: Session,
    user: User,
    *,
    now: datetime | None = None,
) -> list[GameWithBet]:
    """Return one :class:`GameWithBet` per game, sorted by kickoff time + id.

    *now* is overridable so tests can pin "current time" without monkey-
    patching :mod:`datetime`. Production callers should leave it ``None``.
    """
    now = now or datetime.now(UTC)

    games = db.scalars(
        select(Game)
        .options(joinedload(Game.venue), joinedload(Game.group))
        .order_by(Game.kickoff_time, Game.id)
    ).all()

    # One SELECT for all the user's bets, indexed by game_id.
    bets_by_game = {
        b.game_id: b for b in db.scalars(select(Bet).where(Bet.user_id == user.id)).all()
    }

    result: list[GameWithBet] = []
    for game in games:
        bet = bets_by_game.get(game.id)
        # Only surface points once kickoff has actually happened. Otherwise
        # an admin entering an early/erroneous result would leak information
        # players could use to adjust still-editable bets.
        points = (
            calculate_bet_points(
                bet.score_home if bet else None,
                bet.score_away if bet else None,
                game.score_home,
                game.score_away,
            )
            if bet is not None and game.kickoff_time <= now
            else 0
        )
        result.append(
            GameWithBet(
                game=game,
                bet=bet,
                points=points,
                can_bet=game.kickoff_time > now,
            )
        )
    return result


def list_games_with_bets_grouped(
    db: Session,
    user: User,
    *,
    now: datetime | None = None,
) -> list[tuple[Group, list[GameWithBet]]]:
    """Same as :func:`list_games_with_bets` but bundled into the ``(group, entries)``
    sections that the bets template renders, in tournament priority order.

    Useful because Jinja's groupby + lookup gymnastics around ORM
    relationships gets noisy; doing it in Python keeps the template clean.
    """
    flat = list_games_with_bets(db, user, now=now)
    by_group: dict[str, list[GameWithBet]] = {}
    for entry in flat:
        by_group.setdefault(entry.game.group_id, []).append(entry)

    groups = db.scalars(select(Group).order_by(Group.priority)).all()
    sections: list[tuple[Group, list[GameWithBet]]] = []
    for group in groups:
        entries = sorted(
            by_group.get(group.id, []),
            key=lambda e: (e.game.kickoff_time, e.game.id),
        )
        sections.append((group, entries))
    return sections


# ---------------------------------------------------------------------------
# Mutations
# ---------------------------------------------------------------------------


def _load_game(db: Session, game_id: int) -> Game:
    game = db.get(Game, game_id)
    if game is None:
        raise GameNotFound(game_id)
    return game


def _validate_score(name: str, value: int) -> None:
    if not isinstance(value, int):  # type: ignore[unreachable]
        raise InvalidScore(f"{name} must be an integer.", field=name, kind="not_int")
    if value < MIN_SCORE or value > MAX_SCORE:
        raise InvalidScore(
            f"{name} must be between {MIN_SCORE} and {MAX_SCORE}.",
            field=name,
            kind="range",
        )


def upsert_bet(
    db: Session,
    user: User,
    *,
    game_id: int,
    score_home: int,
    score_away: int,
    now: datetime | None = None,
) -> Bet:
    """Insert or update *user*'s bet on *game_id*.

    Raises:
        :class:`GameNotFound`   if the game id doesn't exist
        :class:`BetDeadlinePassed` if kickoff has already happened
        :class:`InvalidScore`   if either score is out of range
    """
    now = now or datetime.now(UTC)

    game = _load_game(db, game_id)
    if game.kickoff_time <= now:
        raise BetDeadlinePassed(game_id)

    _validate_score("score_home", score_home)
    _validate_score("score_away", score_away)

    bet = db.scalars(
        select(Bet).where(Bet.user_id == user.id, Bet.game_id == game_id)
    ).one_or_none()
    if bet is None:
        bet = Bet(user_id=user.id, game_id=game_id)
        db.add(bet)
    bet.score_home = score_home
    bet.score_away = score_away
    db.commit()
    db.refresh(bet)
    LOGGER.info(
        "Bet upsert: user=%d game=%d -> %d:%d",
        user.id,
        game_id,
        score_home,
        score_away,
    )
    return bet


def delete_bet(
    db: Session,
    user: User,
    game_id: int,
    *,
    now: datetime | None = None,
) -> None:
    """Remove *user*'s bet on *game_id*.

    No-op when the user hasn't placed a bet. Raises
    :class:`BetDeadlinePassed` if the game already kicked off, so a
    template that's gone stale can't sneak through a delete.
    Raises :class:`GameNotFound` if the game id is unknown.
    """
    now = now or datetime.now(UTC)

    game = _load_game(db, game_id)
    if game.kickoff_time <= now:
        raise BetDeadlinePassed(game_id)

    bet = db.scalars(
        select(Bet).where(Bet.user_id == user.id, Bet.game_id == game_id)
    ).one_or_none()
    if bet is None:
        return
    db.delete(bet)
    db.commit()
    LOGGER.info("Bet deleted: user=%d game=%d", user.id, game_id)


# ---------------------------------------------------------------------------
# Single-cell lookup (used by the HTMX swap on save)
# ---------------------------------------------------------------------------


def get_cell_view(
    db: Session,
    user: User,
    game_id: int,
    *,
    now: datetime | None = None,
) -> GameWithBet:
    """Return one :class:`GameWithBet` for a freshly-saved cell.

    Used by the route after an upsert/delete so the HTMX response can
    re-render exactly the same shape the page-level handler produces.
    """
    now = now or datetime.now(UTC)
    # Eager-load so the template has venue/group available without lazy hits.
    game = db.scalars(
        select(Game)
        .options(joinedload(Game.venue), joinedload(Game.group))
        .where(Game.id == game_id)
    ).one_or_none()
    if game is None:
        raise GameNotFound(game_id)

    bet = db.scalars(
        select(Bet).where(Bet.user_id == user.id, Bet.game_id == game_id)
    ).one_or_none()
    points = (
        calculate_bet_points(
            bet.score_home if bet else None,
            bet.score_away if bet else None,
            game.score_home,
            game.score_away,
        )
        if bet is not None and game.kickoff_time <= now
        else 0
    )
    return GameWithBet(
        game=game,
        bet=bet,
        points=points,
        can_bet=game.kickoff_time > now,
    )


# ---------------------------------------------------------------------------
# "Other players' bets" - read-only peek behind the kickoff curtain
# ---------------------------------------------------------------------------


class OtherBet(NamedTuple):
    """One opponent's bet for a game, post-kickoff."""

    user: User
    score_home: int | None
    score_away: int | None
    points: int


class OtherBetsView(NamedTuple):
    """Payload backing the /bets/{id}/others modal.

    ``can_view`` is ``False`` until kickoff. The route layer renders a
    "wait until kickoff" placeholder in that case and we intentionally
    return 200 in both cases so the HTMX swap behaves identically.
    """

    game: Game
    can_view: bool
    others: list[OtherBet]


def list_other_bets_for_game(
    db: Session,
    requesting_user: User,
    game_id: int,
    *,
    now: datetime | None = None,
) -> OtherBetsView:
    """Bets placed by everybody else on *game_id*.

    Order: by points descending (best first), then user name ascending. The
    requesting user is always excluded so the modal never repeats
    information they already see in their own row.

    Raises:
        :class:`GameNotFound`  unknown ``game_id``
    """
    now = now or datetime.now(UTC)
    game = db.get(Game, game_id)
    if game is None:
        raise GameNotFound(game_id)
    if game.kickoff_time > now:
        return OtherBetsView(game=game, can_view=False, others=[])

    bets = db.scalars(
        select(Bet)
        .options(joinedload(Bet.user))
        .where(Bet.game_id == game_id, Bet.user_id != requesting_user.id)
    ).all()

    has_result = game.score_home is not None and game.score_away is not None
    others = [
        OtherBet(
            user=bet.user,
            score_home=bet.score_home,
            score_away=bet.score_away,
            points=(
                calculate_bet_points(
                    bet.score_home,
                    bet.score_away,
                    game.score_home,
                    game.score_away,
                )
                if has_result
                else 0
            ),
        )
        for bet in bets
    ]
    others.sort(key=lambda o: (-o.points, o.user.name.lower()))
    return OtherBetsView(game=game, can_view=True, others=others)


__all__ = [
    "MIN_SCORE",
    "MAX_SCORE",
    "GameWithBet",
    "GameNotFound",
    "BetDeadlinePassed",
    "InvalidScore",
    "OtherBet",
    "OtherBetsView",
    "list_games_with_bets",
    "list_games_with_bets_grouped",
    "upsert_bet",
    "delete_bet",
    "get_cell_view",
    "list_other_bets_for_game",
]
