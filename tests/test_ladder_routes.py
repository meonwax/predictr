"""End-to-end tests for the ``/ladder`` route."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from app.models import Game

GAME_OPENER_ID = 1


def _register_and_login(
    client: TestClient,
    *,
    name: str,
    email: str,
    password: str = "hunter222",
) -> None:
    r = client.post(
        "/register",
        data={"name": name, "email": email, "password": password},
        follow_redirects=False,
    )
    assert r.status_code == 303
    r = client.post("/login", data={"email": email, "password": password}, follow_redirects=False)
    assert r.status_code == 303


@pytest.fixture()
def db(seeded_engine) -> Iterator[Session]:
    Session_ = sessionmaker(bind=seeded_engine, expire_on_commit=False, future=True)
    with Session_() as s:
        yield s


@pytest.fixture(autouse=True)
def _reset_game_scores(seeded_engine) -> Iterator[None]:
    yield
    with seeded_engine.begin() as conn:
        conn.execute(text("UPDATE game SET score_home = NULL, score_away = NULL, notes = NULL"))


# ---------------------------------------------------------------------------
# Access control + basic render
# ---------------------------------------------------------------------------


def test_ladder_requires_login(auth_client: TestClient) -> None:
    r = auth_client.get("/ladder")
    assert r.status_code == 401


def test_ladder_renders_for_logged_in_user(auth_client: TestClient) -> None:
    _register_and_login(auth_client, name="Alice", email="alice@example.com")
    r = auth_client.get("/ladder")
    assert r.status_code == 200
    assert "Ladder" in r.text
    assert "Alice" in r.text
    # "you" badge appears next to the current user.
    assert ">you<" in r.text


def test_ladder_link_in_navbar(auth_client: TestClient) -> None:
    _register_and_login(auth_client, name="Alice", email="alice@example.com")
    page = auth_client.get("/games").text
    assert 'href="/ladder"' in page


def test_ladder_anon_navbar_has_no_ladder_link(auth_client: TestClient) -> None:
    """The Ladder link is only shown to logged-in users."""
    page = auth_client.get("/games").text
    assert 'href="/ladder"' not in page


# ---------------------------------------------------------------------------
# End-to-end ordering with real bets + admin-entered results
# ---------------------------------------------------------------------------


def _extract_user_row(html: str, user_name: str) -> str:
    """Return the ``<tr>...</tr>`` HTML containing *user_name*.

    A regex-based ``<tr>.*?</tr>`` match is too greedy here because Jinja's
    output isn't line-broken and we'd accidentally grab the entire table.
    Splitting on ``</tr>`` gives us non-overlapping row chunks; the first
    chunk that mentions the user is the row we want.
    """
    for chunk in html.split("</tr>"):
        # Skip header chunks: they all contain <th scope="col"> and never <td>.
        if user_name in chunk and "<td" in chunk:
            return chunk + "</tr>"
    raise AssertionError(f"No row mentioning {user_name!r} found in page")


def test_ladder_orders_by_points_after_results_in(
    auth_client: TestClient,
    db: Session,
) -> None:
    """High-scoring user appears above low-scoring user once results land."""
    # Alice places an exact-match bet.
    _register_and_login(auth_client, name="Alice", email="alice@example.com")
    auth_client.post(
        f"/bets/{GAME_OPENER_ID}",
        data={"score_home": "2", "score_away": "1"},
        headers={"HX-Request": "true"},
    )
    auth_client.post("/logout")

    # Bob places a bet that will earn 0 points (wrong winner).
    _register_and_login(auth_client, name="Bob", email="bob@example.com")
    auth_client.post(
        f"/bets/{GAME_OPENER_ID}",
        data={"score_home": "0", "score_away": "5"},
        headers={"HX-Request": "true"},
    )
    auth_client.post("/logout")

    # Stamp the result and pull the kickoff into the past so the ladder
    # actually counts the bet.
    from datetime import datetime, timedelta

    game = db.get(Game, GAME_OPENER_ID)
    assert game is not None
    original = game.kickoff_time
    game.kickoff_time = datetime.now(UTC) - timedelta(hours=2)
    game.score_home = 2
    game.score_away = 1
    db.commit()
    try:
        # Anyone logged in can see the ladder. Re-use the test client as Alice.
        auth_client.post(
            "/login",
            data={
                "email": "alice@example.com",
                "password": "hunter222",
            },
        )
        page = auth_client.get("/ladder").text
        # Alice should appear before Bob in the rendered table.
        alice_pos = page.find("Alice")
        bob_pos = page.find("Bob")
        assert alice_pos != -1 and bob_pos != -1
        assert alice_pos < bob_pos
        # 5 points should show somewhere in the rendered numbers for Alice.
        # Locate her row and look for the points cell.
        row = _extract_user_row(page, "Alice")
        assert ">5<" in row
    finally:
        game.kickoff_time = original
        game.score_home = None
        game.score_away = None
        db.commit()


def test_ladder_does_not_count_pre_kickoff_result(
    auth_client: TestClient,
    db: Session,
) -> None:
    """An admin-entered result before kickoff must not change the ladder."""
    _register_and_login(auth_client, name="Alice", email="alice@example.com")
    auth_client.post(
        f"/bets/{GAME_OPENER_ID}",
        data={"score_home": "2", "score_away": "1"},
        headers={"HX-Request": "true"},
    )
    # Result entered while kickoff is still in the future.
    game = db.get(Game, GAME_OPENER_ID)
    assert game is not None
    game.score_home = 2
    game.score_away = 1
    db.commit()

    page = auth_client.get("/ladder").text
    row = _extract_user_row(page, "Alice")
    # Points cell renders 0, not 5: no leak.
    assert ">5<" not in row
    # And the row should include a "0" indicator somewhere.
    assert ">0<" in row
