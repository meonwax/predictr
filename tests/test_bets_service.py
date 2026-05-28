"""Unit tests for :mod:`app.services.bets`.

These tests reuse the seeded testcontainer (so we have real Game rows
with kickoff times), but each test gets its own freshly-created user
via the :func:`clean_user_tables` fixture so bet state can't leak
between tests.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.orm import Session, sessionmaker

from app.models import Bet, Game, User
from app.services.bets import (
    BetDeadlinePassed,
    delete_bet,
    get_cell_view,
    list_games_with_bets,
    list_games_with_bets_grouped,
    upsert_bet,
)
from app.services.games import GameNotFound, InvalidScore
from app.services.users import RegistrationData, register_user

# Game id 1 in the WC 2026 seed: Mexico v South Africa, 2026-06-11 19:00 UTC.
GAME_OPENER_ID = 1
GAME_OPENER_KICKOFF = datetime(2026, 6, 11, 19, 0, tzinfo=UTC)


@pytest.fixture()
def fresh_db(clean_user_tables: None, seeded_engine) -> Iterator[Session]:
    """A Session bound to the seeded engine, after wiping user tables."""
    Session_ = sessionmaker(bind=seeded_engine, expire_on_commit=False, future=True)
    with Session_() as session:
        yield session


def _make_user(db: Session, *, name: str, email: str) -> User:
    return register_user(
        db,
        RegistrationData(name=name, email=email, password="hunter222"),
    )


@pytest.fixture()
def user(fresh_db: Session) -> User:
    return _make_user(fresh_db, name="Better Bertha", email="bertha@example.com")


# ---------------------------------------------------------------------------
# upsert_bet
# ---------------------------------------------------------------------------


def test_upsert_creates_new_bet(fresh_db: Session, user: User) -> None:
    """First bet on a game inserts a row."""
    before_kickoff = GAME_OPENER_KICKOFF - timedelta(days=1)
    bet = upsert_bet(
        fresh_db,
        user,
        game_id=GAME_OPENER_ID,
        score_home=2,
        score_away=1,
        now=before_kickoff,
    )
    assert bet.id is not None
    assert bet.score_home == 2
    assert bet.score_away == 1
    assert bet.user_id == user.id
    assert bet.game_id == GAME_OPENER_ID


def test_upsert_updates_existing_bet(fresh_db: Session, user: User) -> None:
    """Second upsert reuses the same row (UNIQUE constraint on user+game)."""
    before = GAME_OPENER_KICKOFF - timedelta(days=1)
    first = upsert_bet(
        fresh_db, user, game_id=GAME_OPENER_ID, score_home=2, score_away=1, now=before
    )
    second = upsert_bet(
        fresh_db, user, game_id=GAME_OPENER_ID, score_home=3, score_away=0, now=before
    )
    assert first.id == second.id
    assert second.score_home == 3
    assert second.score_away == 0

    # Belt-and-braces: only one bet row per user/game.
    bets_for_user = fresh_db.query(Bet).filter_by(user_id=user.id).all()
    assert len(bets_for_user) == 1


def test_upsert_rejects_after_kickoff(fresh_db: Session, user: User) -> None:
    after = GAME_OPENER_KICKOFF + timedelta(seconds=1)
    with pytest.raises(BetDeadlinePassed):
        upsert_bet(fresh_db, user, game_id=GAME_OPENER_ID, score_home=1, score_away=0, now=after)


def test_upsert_rejects_at_exact_kickoff(fresh_db: Session, user: User) -> None:
    """Kickoff itself is closed (strictly-less-than rule)."""
    with pytest.raises(BetDeadlinePassed):
        upsert_bet(
            fresh_db,
            user,
            game_id=GAME_OPENER_ID,
            score_home=1,
            score_away=0,
            now=GAME_OPENER_KICKOFF,
        )


def test_upsert_rejects_unknown_game(fresh_db: Session, user: User) -> None:
    with pytest.raises(GameNotFound):
        upsert_bet(
            fresh_db,
            user,
            game_id=99999,
            score_home=1,
            score_away=0,
            now=GAME_OPENER_KICKOFF - timedelta(days=1),
        )


@pytest.mark.parametrize(
    "home, away",
    [
        (-1, 0),
        (0, -1),
        (100, 0),
        (0, 100),
    ],
)
def test_upsert_rejects_out_of_range_scores(
    fresh_db: Session, user: User, home: int, away: int
) -> None:
    with pytest.raises(InvalidScore):
        upsert_bet(
            fresh_db,
            user,
            game_id=GAME_OPENER_ID,
            score_home=home,
            score_away=away,
            now=GAME_OPENER_KICKOFF - timedelta(days=1),
        )


def test_upsert_accepts_zero_zero(fresh_db: Session, user: User) -> None:
    """0-0 is a valid bet (one of the most common ones)."""
    bet = upsert_bet(
        fresh_db,
        user,
        game_id=GAME_OPENER_ID,
        score_home=0,
        score_away=0,
        now=GAME_OPENER_KICKOFF - timedelta(days=1),
    )
    assert bet.score_home == 0
    assert bet.score_away == 0


# ---------------------------------------------------------------------------
# delete_bet
# ---------------------------------------------------------------------------


def test_delete_removes_existing_bet(fresh_db: Session, user: User) -> None:
    before = GAME_OPENER_KICKOFF - timedelta(days=1)
    upsert_bet(fresh_db, user, game_id=GAME_OPENER_ID, score_home=1, score_away=2, now=before)
    delete_bet(fresh_db, user, GAME_OPENER_ID, now=before)
    assert fresh_db.query(Bet).filter_by(user_id=user.id).count() == 0


def test_delete_missing_bet_is_noop(fresh_db: Session, user: User) -> None:
    """Deleting a bet that doesn't exist is a no-op (and doesn't raise)."""
    before = GAME_OPENER_KICKOFF - timedelta(days=1)
    delete_bet(fresh_db, user, GAME_OPENER_ID, now=before)


def test_delete_rejects_after_kickoff(fresh_db: Session, user: User) -> None:
    before = GAME_OPENER_KICKOFF - timedelta(days=1)
    upsert_bet(fresh_db, user, game_id=GAME_OPENER_ID, score_home=1, score_away=2, now=before)
    after = GAME_OPENER_KICKOFF + timedelta(minutes=1)
    with pytest.raises(BetDeadlinePassed):
        delete_bet(fresh_db, user, GAME_OPENER_ID, now=after)
    # The bet must survive a rejected delete.
    assert fresh_db.query(Bet).filter_by(user_id=user.id).count() == 1


def test_delete_unknown_game_raises(fresh_db: Session, user: User) -> None:
    with pytest.raises(GameNotFound):
        delete_bet(fresh_db, user, 99999, now=GAME_OPENER_KICKOFF - timedelta(days=1))


# ---------------------------------------------------------------------------
# list_games_with_bets / list_games_with_bets_grouped
# ---------------------------------------------------------------------------


def test_list_returns_one_entry_per_game(fresh_db: Session, user: User) -> None:
    entries = list_games_with_bets(
        fresh_db,
        user,
        now=GAME_OPENER_KICKOFF - timedelta(days=10),
    )
    total_games = fresh_db.query(Game).count()
    assert len(entries) == total_games
    # No bets placed yet -> every entry has bet=None and points=0.
    assert all(e.bet is None for e in entries)
    assert all(e.points == 0 for e in entries)


def test_list_marks_can_bet_based_on_kickoff(fresh_db: Session, user: User) -> None:
    """Games before *now* are locked; games after are still editable."""
    midpoint = datetime(2026, 6, 25, 12, 0, tzinfo=UTC)
    entries = list_games_with_bets(fresh_db, user, now=midpoint)
    locked = [e for e in entries if not e.can_bet]
    open_ = [e for e in entries if e.can_bet]
    assert locked, "expected at least one locked game by 25 June"
    assert open_, "expected at least one open game by 25 June"
    # Every locked entry's kickoff is in the past (relative to *midpoint*).
    assert all(e.game.kickoff_time <= midpoint for e in locked)
    assert all(e.game.kickoff_time > midpoint for e in open_)


def test_list_attaches_users_bet(fresh_db: Session, user: User) -> None:
    before = GAME_OPENER_KICKOFF - timedelta(days=1)
    upsert_bet(fresh_db, user, game_id=GAME_OPENER_ID, score_home=2, score_away=1, now=before)
    entries = {e.game.id: e for e in list_games_with_bets(fresh_db, user, now=before)}
    opener = entries[GAME_OPENER_ID]
    assert opener.bet is not None
    assert (opener.bet.score_home, opener.bet.score_away) == (2, 1)


def test_list_does_not_leak_other_users_bets(fresh_db: Session, user: User) -> None:
    other = _make_user(fresh_db, name="Other", email="other@example.com")
    before = GAME_OPENER_KICKOFF - timedelta(days=1)
    upsert_bet(fresh_db, other, game_id=GAME_OPENER_ID, score_home=2, score_away=1, now=before)
    entries = {e.game.id: e for e in list_games_with_bets(fresh_db, user, now=before)}
    assert entries[GAME_OPENER_ID].bet is None


def test_list_computes_points_when_result_in(fresh_db: Session, user: User) -> None:
    before = GAME_OPENER_KICKOFF - timedelta(days=1)
    after = GAME_OPENER_KICKOFF + timedelta(hours=2)
    upsert_bet(fresh_db, user, game_id=GAME_OPENER_ID, score_home=2, score_away=1, now=before)
    # Stash the official result, mimicking what /admin will eventually do.
    # The seeded engine is shared across the test session, so restore the
    # game row to NULL on teardown to avoid cross-test pollution.
    game = fresh_db.get(Game, GAME_OPENER_ID)
    assert game is not None
    game.score_home = 2
    game.score_away = 1
    fresh_db.commit()
    try:
        # Use a "now" after kickoff so the service surfaces the points.
        entries = {e.game.id: e for e in list_games_with_bets(fresh_db, user, now=after)}
        # Exact result -> DEFAULT_CONFIG.points_result == 5.
        assert entries[GAME_OPENER_ID].points == 5
    finally:
        game.score_home = None
        game.score_away = None
        fresh_db.commit()


def test_list_suppresses_points_before_kickoff(
    fresh_db: Session,
    user: User,
) -> None:
    """A result entered before kickoff must not leak points to the user yet."""
    before = GAME_OPENER_KICKOFF - timedelta(days=1)
    upsert_bet(fresh_db, user, game_id=GAME_OPENER_ID, score_home=2, score_away=1, now=before)
    game = fresh_db.get(Game, GAME_OPENER_ID)
    assert game is not None
    # Admin enters the "result" early (e.g. by mistake while testing).
    game.score_home = 2
    game.score_away = 1
    fresh_db.commit()
    try:
        entries = {e.game.id: e for e in list_games_with_bets(fresh_db, user, now=before)}
        assert entries[GAME_OPENER_ID].points == 0
        # Cell is still editable, of course.
        assert entries[GAME_OPENER_ID].can_bet is True
    finally:
        game.score_home = None
        game.score_away = None
        fresh_db.commit()


def test_grouped_orders_groups_by_priority(fresh_db: Session, user: User) -> None:
    sections = list_games_with_bets_grouped(
        fresh_db,
        user,
        now=GAME_OPENER_KICKOFF - timedelta(days=1),
    )
    # Every section has a non-empty list of entries, except possibly the
    # knockout pseudo-groups (which DO have games in WC 2026 - the bracket
    # is already drawn in the seed file).
    assert sections, "expected non-empty group sections"
    priorities = [grp.priority for grp, _ in sections]
    assert priorities == sorted(priorities)


# ---------------------------------------------------------------------------
# get_cell_view (used by the HTMX route)
# ---------------------------------------------------------------------------


def test_get_cell_view_round_trip(fresh_db: Session, user: User) -> None:
    before = GAME_OPENER_KICKOFF - timedelta(days=1)
    upsert_bet(fresh_db, user, game_id=GAME_OPENER_ID, score_home=3, score_away=2, now=before)
    cell = get_cell_view(fresh_db, user, GAME_OPENER_ID, now=before)
    assert cell.game.id == GAME_OPENER_ID
    assert cell.bet is not None
    assert (cell.bet.score_home, cell.bet.score_away) == (3, 2)
    assert cell.can_bet is True
    assert cell.points == 0  # no official result yet


def test_get_cell_view_unknown_game(fresh_db: Session, user: User) -> None:
    with pytest.raises(GameNotFound):
        get_cell_view(fresh_db, user, 99999)
