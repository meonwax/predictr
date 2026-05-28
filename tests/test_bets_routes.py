"""End-to-end tests for the ``/bets`` page and POST endpoint.

These tests exercise the FastAPI routes with a real Postgres testcontainer
and a real session cookie, but stub time-sensitive behaviour (kickoff vs.
"now") by manipulating ``Game.kickoff_time`` directly through a side-channel
SQLAlchemy session.

The HTMX path is verified by sending the ``HX-Request: true`` header and
asserting on the fragment response. The plain-form fallback is verified by
omitting that header and checking for the 303 redirect.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.models import Bet, Game

# Seeded WC 2026 fixture: Mexico vs South Africa, 2026-06-11 19:00 UTC.
GAME_OPENER_ID = 1


def _register_and_login(client: TestClient) -> None:
    r = client.post(
        "/register",
        data={"name": "Better Bertha", "email": "bertha@example.com", "password": "hunter222"},
        follow_redirects=False,
    )
    assert r.status_code == 303, r.text
    r = client.post(
        "/login",
        data={"email": "bertha@example.com", "password": "hunter222"},
        follow_redirects=False,
    )
    assert r.status_code == 303, r.text


@pytest.fixture()
def logged_in_client(auth_client: TestClient) -> TestClient:
    _register_and_login(auth_client)
    return auth_client


@pytest.fixture()
def db(seeded_engine) -> Iterator[Session]:
    Session_ = sessionmaker(bind=seeded_engine, expire_on_commit=False, future=True)
    with Session_() as s:
        yield s


# Some tests need to "move" a game's kickoff into the past to verify the
# deadline logic. The session-scoped seed is read-write, so we restore the
# original timestamp on teardown to keep test isolation.
@pytest.fixture()
def move_opener_kickoff_to_past(db: Session) -> Iterator[None]:
    game = db.get(Game, GAME_OPENER_ID)
    assert game is not None
    original = game.kickoff_time
    game.kickoff_time = datetime.now(UTC) - timedelta(hours=1)
    db.commit()
    yield
    # Reload because the route-side session may have refreshed the row.
    game = db.get(Game, GAME_OPENER_ID)
    assert game is not None
    game.kickoff_time = original
    db.commit()


# ---------------------------------------------------------------------------
# GET /bets - access control + structure
# ---------------------------------------------------------------------------


def test_bets_page_requires_authentication(auth_client: TestClient) -> None:
    r = auth_client.get("/bets")
    assert r.status_code == 401


def test_bets_page_renders_for_logged_in_user(logged_in_client: TestClient) -> None:
    r = logged_in_client.get("/bets")
    assert r.status_code == 200
    assert "My bets" in r.text
    # The opener fixture should be rendered with its HTMX-targetable cell.
    assert f'id="bet-cell-{GAME_OPENER_ID}"' in r.text
    # The form posts to /bets/{id}.
    assert f"/bets/{GAME_OPENER_ID}" in r.text
    # Active nav link.
    assert 'href="/bets"' in r.text


def test_bets_page_shows_existing_bet(logged_in_client: TestClient, db: Session) -> None:
    """The page pre-fills the inputs from the user's persisted bet."""
    import re

    r = logged_in_client.post(
        f"/bets/{GAME_OPENER_ID}",
        data={"score_home": "2", "score_away": "1"},
        headers={"HX-Request": "true"},
    )
    assert r.status_code == 200, r.text

    page = logged_in_client.get("/bets").text
    # Match inputs in any attribute order/whitespace: the cell is targetable
    # by id and contains both score values.
    cell_match = re.search(
        rf'id="bet-cell-{GAME_OPENER_ID}".*?</td>',
        page,
        re.DOTALL,
    )
    assert cell_match, "opener bet cell missing from page"
    cell_html = cell_match.group(0)
    assert re.search(r'name="score_home"[^>]*value="2"', cell_html), cell_html
    assert re.search(r'name="score_away"[^>]*value="1"', cell_html), cell_html


# ---------------------------------------------------------------------------
# POST /bets/{game_id} - HTMX path
# ---------------------------------------------------------------------------


def test_htmx_post_creates_bet(logged_in_client: TestClient, db: Session) -> None:
    r = logged_in_client.post(
        f"/bets/{GAME_OPENER_ID}",
        data={"score_home": "3", "score_away": "0"},
        headers={"HX-Request": "true"},
    )
    assert r.status_code == 200, r.text
    # Response is the cell fragment, not the full page.
    assert "<!DOCTYPE html>" not in r.text
    assert f'id="bet-cell-{GAME_OPENER_ID}"' in r.text
    assert "saved" in r.text  # success indicator

    # And the bet is actually persisted.
    bet = db.query(Bet).filter_by(game_id=GAME_OPENER_ID).one()
    assert (bet.score_home, bet.score_away) == (3, 0)


def test_htmx_post_updates_existing_bet(logged_in_client: TestClient, db: Session) -> None:
    logged_in_client.post(
        f"/bets/{GAME_OPENER_ID}",
        data={"score_home": "1", "score_away": "1"},
        headers={"HX-Request": "true"},
    )
    r = logged_in_client.post(
        f"/bets/{GAME_OPENER_ID}",
        data={"score_home": "2", "score_away": "0"},
        headers={"HX-Request": "true"},
    )
    assert r.status_code == 200
    bets = db.query(Bet).filter_by(game_id=GAME_OPENER_ID).all()
    assert len(bets) == 1
    assert (bets[0].score_home, bets[0].score_away) == (2, 0)


def test_htmx_post_with_blank_fields_deletes_bet(logged_in_client: TestClient, db: Session) -> None:
    logged_in_client.post(
        f"/bets/{GAME_OPENER_ID}",
        data={"score_home": "1", "score_away": "1"},
        headers={"HX-Request": "true"},
    )
    r = logged_in_client.post(
        f"/bets/{GAME_OPENER_ID}",
        data={"score_home": "", "score_away": ""},
        headers={"HX-Request": "true"},
    )
    assert r.status_code == 200
    assert db.query(Bet).filter_by(game_id=GAME_OPENER_ID).count() == 0


def test_htmx_post_with_one_blank_returns_error(
    logged_in_client: TestClient,
) -> None:
    r = logged_in_client.post(
        f"/bets/{GAME_OPENER_ID}",
        data={"score_home": "2", "score_away": ""},
        headers={"HX-Request": "true"},
    )
    assert r.status_code == 200
    # The fragment is still returned, but with an error message.
    assert "fill in both scores" in r.text.lower()


def test_htmx_post_rejects_non_integer(
    logged_in_client: TestClient,
) -> None:
    r = logged_in_client.post(
        f"/bets/{GAME_OPENER_ID}",
        data={"score_home": "two", "score_away": "1"},
        headers={"HX-Request": "true"},
    )
    assert r.status_code == 200
    assert "whole number" in r.text.lower()


def test_htmx_post_rejects_out_of_range(
    logged_in_client: TestClient,
) -> None:
    r = logged_in_client.post(
        f"/bets/{GAME_OPENER_ID}",
        data={"score_home": "150", "score_away": "1"},
        headers={"HX-Request": "true"},
    )
    assert r.status_code == 200
    assert "between" in r.text.lower()


def test_htmx_post_after_kickoff_returns_error(
    logged_in_client: TestClient,
    move_opener_kickoff_to_past: None,
) -> None:
    r = logged_in_client.post(
        f"/bets/{GAME_OPENER_ID}",
        data={"score_home": "2", "score_away": "1"},
        headers={"HX-Request": "true"},
    )
    assert r.status_code == 200
    # Cell re-renders in read-only mode; no <form> in the response body for
    # locked games.
    assert "<form" not in r.text.lower()
    assert "kickoff" in r.text.lower()


def test_htmx_post_unknown_game_404s(logged_in_client: TestClient) -> None:
    r = logged_in_client.post(
        "/bets/99999",
        data={"score_home": "1", "score_away": "0"},
        headers={"HX-Request": "true"},
    )
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# POST /bets/{game_id} - plain-form fallback (no HX-Request)
# ---------------------------------------------------------------------------


def test_plain_post_redirects_to_bets(logged_in_client: TestClient, db: Session) -> None:
    r = logged_in_client.post(
        f"/bets/{GAME_OPENER_ID}",
        data={"score_home": "4", "score_away": "2"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert r.headers["location"] == "/bets"
    bet = db.query(Bet).filter_by(game_id=GAME_OPENER_ID).one()
    assert (bet.score_home, bet.score_away) == (4, 2)


def test_post_requires_authentication(auth_client: TestClient) -> None:
    r = auth_client.post(
        f"/bets/{GAME_OPENER_ID}",
        data={"score_home": "1", "score_away": "0"},
    )
    assert r.status_code == 401


# ---------------------------------------------------------------------------
# Cross-user isolation
# ---------------------------------------------------------------------------


def test_other_users_bet_invisible(
    auth_client: TestClient,
    db: Session,
) -> None:
    """A bet placed by user A is not exposed to user B's GET /bets."""
    # Register + log in user A, place a bet.
    auth_client.post(
        "/register",
        data={
            "name": "Alice",
            "email": "alice@example.com",
            "password": "hunter222",
        },
    )
    auth_client.post(
        "/login",
        data={
            "email": "alice@example.com",
            "password": "hunter222",
        },
    )
    auth_client.post(
        f"/bets/{GAME_OPENER_ID}",
        data={"score_home": "9", "score_away": "9"},
        headers={"HX-Request": "true"},
    )
    auth_client.post("/logout")

    # Now register + log in user B.
    auth_client.post(
        "/register",
        data={
            "name": "Bob",
            "email": "bob@example.com",
            "password": "hunter222",
        },
    )
    auth_client.post(
        "/login",
        data={
            "email": "bob@example.com",
            "password": "hunter222",
        },
    )
    page = auth_client.get("/bets").text
    # Bob's cell for the same game should NOT contain Alice's 9:9.
    # The pattern below would only appear inside Bob's own (empty) form,
    # which uses value="".
    assert 'value="9"' not in page
