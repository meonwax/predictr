"""Integration tests for ``GET /bets/{game_id}/others``."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.models import Game

GAME_OPENER_ID = 1


def _register(client: TestClient, *, name: str, email: str) -> None:
    r = client.post(
        "/register",
        data={"name": name, "email": email, "password": "hunter222"},
        follow_redirects=False,
    )
    assert r.status_code == 303, r.text


def _login(client: TestClient, email: str) -> None:
    r = client.post(
        "/login", data={"email": email, "password": "hunter222"}, follow_redirects=False
    )
    assert r.status_code == 303, r.text


def _logout(client: TestClient) -> None:
    client.post("/logout")


@pytest.fixture()
def db(seeded_engine) -> Iterator[Session]:
    Session_ = sessionmaker(bind=seeded_engine, expire_on_commit=False, future=True)
    with Session_() as s:
        yield s


@pytest.fixture(autouse=True)
def _restore_opener(seeded_engine) -> Iterator[None]:
    """Reset the opener game's kickoff + result after each test."""
    yield
    Session_ = sessionmaker(bind=seeded_engine, expire_on_commit=False, future=True)
    with Session_() as s:
        g = s.get(Game, GAME_OPENER_ID)
        if g is not None:
            g.kickoff_time = datetime(2026, 6, 11, 19, 0, tzinfo=UTC)
            g.score_home = None
            g.score_away = None
            s.commit()


def _move_kickoff_to_past(db: Session) -> None:
    g = db.get(Game, GAME_OPENER_ID)
    assert g is not None
    g.kickoff_time = datetime.now(UTC) - timedelta(hours=1)
    db.commit()


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


def test_others_requires_login(auth_client: TestClient) -> None:
    r = auth_client.get(f"/bets/{GAME_OPENER_ID}/others")
    assert r.status_code == 401


def test_others_unknown_game_404(auth_client: TestClient) -> None:
    _register(auth_client, name="Alice", email="a@example.com")
    _login(auth_client, "a@example.com")
    r = auth_client.get("/bets/99999/others")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Locked vs unlocked
# ---------------------------------------------------------------------------


def test_locked_before_kickoff_shows_placeholder(
    auth_client: TestClient,
) -> None:
    _register(auth_client, name="Alice", email="a@example.com")
    _login(auth_client, "a@example.com")
    r = auth_client.get(f"/bets/{GAME_OPENER_ID}/others")
    assert r.status_code == 200
    assert "after kickoff" in r.text.lower()
    # Should not be a full document - this is a fragment for swap-into.
    assert "<!doctype html>" not in r.text.lower()


def test_unlocked_lists_other_bets(
    auth_client: TestClient,
    db: Session,
) -> None:
    # Two players each place a bet, then kickoff is moved to the past so
    # the requester (Alice) can peek at Bob's bet.
    _register(auth_client, name="Bob", email="b@example.com")
    _login(auth_client, "b@example.com")
    auth_client.post(
        f"/bets/{GAME_OPENER_ID}",
        data={"score_home": "2", "score_away": "1"},
        headers={"HX-Request": "true"},
    )
    _logout(auth_client)

    _register(auth_client, name="Alice", email="a@example.com")
    _login(auth_client, "a@example.com")
    _move_kickoff_to_past(db)

    r = auth_client.get(f"/bets/{GAME_OPENER_ID}/others")
    assert r.status_code == 200
    assert "Bob" in r.text
    assert "2" in r.text and "1" in r.text


def test_excludes_own_bet(
    auth_client: TestClient,
    db: Session,
) -> None:
    _register(auth_client, name="Alice", email="a@example.com")
    _login(auth_client, "a@example.com")
    auth_client.post(
        f"/bets/{GAME_OPENER_ID}",
        data={"score_home": "9", "score_away": "9"},
        headers={"HX-Request": "true"},
    )
    _move_kickoff_to_past(db)

    r = auth_client.get(f"/bets/{GAME_OPENER_ID}/others")
    assert r.status_code == 200
    # The user's own bet (9:9) should NOT appear in the "others" table.
    assert "Alice" not in r.text or "Nobody else" in r.text


def test_empty_state_when_no_other_bets(
    auth_client: TestClient,
    db: Session,
) -> None:
    _register(auth_client, name="Alice", email="a@example.com")
    _login(auth_client, "a@example.com")
    _move_kickoff_to_past(db)
    r = auth_client.get(f"/bets/{GAME_OPENER_ID}/others")
    assert r.status_code == 200
    assert "Nobody else" in r.text


def test_shows_official_result_when_set(
    auth_client: TestClient,
    db: Session,
) -> None:
    _register(auth_client, name="Bob", email="b@example.com")
    _login(auth_client, "b@example.com")
    auth_client.post(
        f"/bets/{GAME_OPENER_ID}",
        data={"score_home": "2", "score_away": "1"},
        headers={"HX-Request": "true"},
    )
    _logout(auth_client)

    _register(auth_client, name="Alice", email="a@example.com")
    _login(auth_client, "a@example.com")
    _move_kickoff_to_past(db)
    # Stamp the official 2:1 result.
    g = db.get(Game, GAME_OPENER_ID)
    assert g is not None
    g.score_home = 2
    g.score_away = 1
    db.commit()

    r = auth_client.get(f"/bets/{GAME_OPENER_ID}/others")
    assert r.status_code == 200
    # The exact-result CSS class should be applied (Bootstrap table colour).
    assert "table-success" in r.text


# ---------------------------------------------------------------------------
# Trigger button is present on the page
# ---------------------------------------------------------------------------


def test_bets_page_has_others_buttons(auth_client: TestClient) -> None:
    _register(auth_client, name="Alice", email="a@example.com")
    _login(auth_client, "a@example.com")
    page = auth_client.get("/bets").text
    assert f'hx-get="/bets/{GAME_OPENER_ID}/others"' in page
    assert 'data-bs-target="#peek-modal"' in page
