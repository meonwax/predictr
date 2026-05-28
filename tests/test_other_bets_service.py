"""Unit tests for :func:`app.services.bets.list_other_bets_for_game`."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from app.models import Game, User
from app.services.bets import (
    list_other_bets_for_game,
    upsert_bet,
)
from app.services.games import GameNotFound
from app.services.users import RegistrationData, register_user

# Game id 1 in the WC 2026 seed.
GAME_OPENER_ID = 1
GAME_OPENER_KICKOFF = datetime(2026, 6, 11, 19, 0, tzinfo=UTC)


@pytest.fixture()
def fresh_db(clean_user_tables: None, seeded_engine) -> Iterator[Session]:
    Session_ = sessionmaker(bind=seeded_engine, expire_on_commit=False, future=True)
    with Session_() as session:
        yield session


@pytest.fixture(autouse=True)
def _reset_game_score(seeded_engine) -> Iterator[None]:
    """Some tests stamp an official result onto the opener; reset after."""
    yield
    with seeded_engine.begin() as conn:
        conn.execute(
            text("UPDATE game SET score_home = NULL, score_away = NULL WHERE id = :gid"),
            {"gid": GAME_OPENER_ID},
        )


def _make_user(db: Session, *, name: str, email: str) -> User:
    return register_user(
        db,
        RegistrationData(name=name, email=email, password="hunter222"),
    )


def _before(seconds: int = 60) -> datetime:
    return GAME_OPENER_KICKOFF - timedelta(seconds=seconds)


def _after(seconds: int = 60) -> datetime:
    return GAME_OPENER_KICKOFF + timedelta(seconds=seconds)


# ---------------------------------------------------------------------------
# Visibility gate
# ---------------------------------------------------------------------------


def test_locked_before_kickoff(fresh_db: Session) -> None:
    """Before kickoff the view is locked and `others` is empty."""
    alice = _make_user(fresh_db, name="Alice", email="a@example.com")
    bob = _make_user(fresh_db, name="Bob", email="b@example.com")
    upsert_bet(fresh_db, bob, game_id=GAME_OPENER_ID, score_home=2, score_away=1, now=_before())

    view = list_other_bets_for_game(
        fresh_db,
        alice,
        GAME_OPENER_ID,
        now=_before(),
    )
    assert view.can_view is False
    assert view.others == []
    assert view.game.id == GAME_OPENER_ID


def test_unlocks_after_kickoff(fresh_db: Session) -> None:
    alice = _make_user(fresh_db, name="Alice", email="a@example.com")
    bob = _make_user(fresh_db, name="Bob", email="b@example.com")
    upsert_bet(fresh_db, bob, game_id=GAME_OPENER_ID, score_home=2, score_away=1, now=_before())

    view = list_other_bets_for_game(
        fresh_db,
        alice,
        GAME_OPENER_ID,
        now=_after(),
    )
    assert view.can_view is True
    assert [o.user.name for o in view.others] == ["Bob"]


def test_unknown_game_raises(fresh_db: Session) -> None:
    alice = _make_user(fresh_db, name="Alice", email="a@example.com")
    with pytest.raises(GameNotFound):
        list_other_bets_for_game(fresh_db, alice, 99999)


# ---------------------------------------------------------------------------
# Own-user exclusion
# ---------------------------------------------------------------------------


def test_excludes_requesting_user(fresh_db: Session) -> None:
    """The user calling the function should never see their own row."""
    alice = _make_user(fresh_db, name="Alice", email="a@example.com")
    bob = _make_user(fresh_db, name="Bob", email="b@example.com")
    upsert_bet(fresh_db, alice, game_id=GAME_OPENER_ID, score_home=3, score_away=3, now=_before())
    upsert_bet(fresh_db, bob, game_id=GAME_OPENER_ID, score_home=2, score_away=1, now=_before())

    view = list_other_bets_for_game(
        fresh_db,
        alice,
        GAME_OPENER_ID,
        now=_after(),
    )
    assert [o.user.name for o in view.others] == ["Bob"]


def test_empty_when_nobody_else_bet(fresh_db: Session) -> None:
    alice = _make_user(fresh_db, name="Alice", email="a@example.com")
    upsert_bet(fresh_db, alice, game_id=GAME_OPENER_ID, score_home=1, score_away=0, now=_before())
    view = list_other_bets_for_game(
        fresh_db,
        alice,
        GAME_OPENER_ID,
        now=_after(),
    )
    assert view.can_view is True
    assert view.others == []


# ---------------------------------------------------------------------------
# Scoring + ordering
# ---------------------------------------------------------------------------


def test_points_zero_when_no_result_yet(fresh_db: Session) -> None:
    alice = _make_user(fresh_db, name="Alice", email="a@example.com")
    bob = _make_user(fresh_db, name="Bob", email="b@example.com")
    upsert_bet(fresh_db, bob, game_id=GAME_OPENER_ID, score_home=2, score_away=1, now=_before())

    view = list_other_bets_for_game(
        fresh_db,
        alice,
        GAME_OPENER_ID,
        now=_after(),
    )
    assert all(o.points == 0 for o in view.others)


def test_sorts_by_points_desc_then_name_asc(fresh_db: Session) -> None:
    """Best bet first, then alphabetical for ties."""
    alice = _make_user(fresh_db, name="Alice", email="a@example.com")
    bob = _make_user(fresh_db, name="Bob", email="b@example.com")
    cara = _make_user(fresh_db, name="Cara", email="c@example.com")
    dora = _make_user(fresh_db, name="Dora", email="d@example.com")

    # Bob: exact, Cara: spread (home win by 1), Dora: tendency only, no-one else.
    upsert_bet(fresh_db, bob, game_id=GAME_OPENER_ID, score_home=2, score_away=1, now=_before())
    upsert_bet(fresh_db, cara, game_id=GAME_OPENER_ID, score_home=3, score_away=2, now=_before())
    upsert_bet(fresh_db, dora, game_id=GAME_OPENER_ID, score_home=4, score_away=0, now=_before())

    # Stamp the official result: 2:1.
    game = fresh_db.get(Game, GAME_OPENER_ID)
    assert game is not None
    game.score_home = 2
    game.score_away = 1
    fresh_db.commit()

    view = list_other_bets_for_game(
        fresh_db,
        alice,
        GAME_OPENER_ID,
        now=_after(),
    )
    # Expected order:
    #   Bob   exact          -> 5
    #   Cara  spread (+1)    -> 3
    #   Dora  tendency only  -> 2
    assert [(o.user.name, o.points) for o in view.others] == [
        ("Bob", 5),
        ("Cara", 3),
        ("Dora", 2),
    ]


def test_name_tiebreak_when_equal_points(fresh_db: Session) -> None:
    alice = _make_user(fresh_db, name="Alice", email="a@example.com")
    zara = _make_user(fresh_db, name="Zara", email="z@example.com")
    bobby = _make_user(fresh_db, name="bobby", email="b@example.com")  # lower-case
    upsert_bet(fresh_db, zara, game_id=GAME_OPENER_ID, score_home=2, score_away=1, now=_before())
    upsert_bet(fresh_db, bobby, game_id=GAME_OPENER_ID, score_home=2, score_away=1, now=_before())

    # No official result yet -> both have 0 points -> name asc tie-break.
    view = list_other_bets_for_game(
        fresh_db,
        alice,
        GAME_OPENER_ID,
        now=_after(),
    )
    assert [o.user.name for o in view.others] == ["bobby", "Zara"]
