"""End-to-end tests for /admin and /admin/games."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from app.models import Game, User

GAME_OPENER_ID = 1
GAME_R32_FIRST_ID = 73
GAME_R16_FIRST_ID = 89


def _register_and_login(
    client: TestClient,
    *,
    name: str = "Admin",
    email: str = "admin@example.com",
    password: str = "hunter222",
) -> None:
    r = client.post(
        "/register",
        data={"name": name, "email": email, "password": password},
        follow_redirects=False,
    )
    assert r.status_code == 303, r.text
    r = client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=False,
    )
    assert r.status_code == 303, r.text


def _promote(db: Session, email: str) -> None:
    user = db.query(User).filter(User.email == email).one()
    user.role = User.ROLE_ADMIN
    db.commit()


@pytest.fixture()
def db(seeded_engine) -> Iterator[Session]:
    Session_ = sessionmaker(bind=seeded_engine, expire_on_commit=False, future=True)
    with Session_() as s:
        yield s


@pytest.fixture()
def admin_client(auth_client: TestClient, db: Session) -> TestClient:
    """A TestClient logged in as an admin user."""
    _register_and_login(auth_client)
    _promote(db, "admin@example.com")
    # Session cookie already issued; the next request's RequiredAdmin will
    # re-query the user row, see ROLE_ADMIN, and let it through.
    return auth_client


@pytest.fixture()
def non_admin_client(auth_client: TestClient) -> TestClient:
    _register_and_login(
        auth_client,
        name="Pat",
        email="pat@example.com",
        password="hunter222",
    )
    return auth_client


# Reset game result state after every test so cross-test pollution can't
# happen on the session-scoped seeded engine.
@pytest.fixture(autouse=True)
def _reset_game_scores(seeded_engine) -> Iterator[None]:
    yield
    with seeded_engine.begin() as conn:
        conn.execute(text("UPDATE game SET score_home = NULL, score_away = NULL, notes = NULL"))


@pytest.fixture(autouse=True)
def _reset_knockout_teams(seeded_engine) -> Iterator[None]:
    yield
    with seeded_engine.begin() as conn:
        conn.execute(
            text(
                "UPDATE game SET team_home_id = NULL, team_away_id = NULL "
                "WHERE group_id IN ('r32','r16','qf','sf','3rd','fin')"
            )
        )


# ---------------------------------------------------------------------------
# Access control
# ---------------------------------------------------------------------------


def test_admin_index_requires_login(auth_client: TestClient) -> None:
    r = auth_client.get("/admin")
    assert r.status_code == 401


def test_admin_index_rejects_non_admin(non_admin_client: TestClient) -> None:
    r = non_admin_client.get("/admin")
    assert r.status_code == 403


def test_admin_games_requires_admin(non_admin_client: TestClient) -> None:
    r = non_admin_client.get("/admin/games")
    assert r.status_code == 403


def test_admin_post_requires_admin(non_admin_client: TestClient) -> None:
    r = non_admin_client.post(
        f"/admin/games/{GAME_OPENER_ID}",
        data={"score_home": "2", "score_away": "1"},
    )
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# GET /admin
# ---------------------------------------------------------------------------


def test_admin_index_renders_dashboard(admin_client: TestClient) -> None:
    r = admin_client.get("/admin")
    assert r.status_code == 200
    assert "Admin dashboard" in r.text
    # Quick link to /admin/games is on the dashboard.
    assert 'href="/admin/games"' in r.text


def test_admin_link_shown_for_admin(admin_client: TestClient) -> None:
    page = admin_client.get("/games").text
    assert 'href="/admin"' in page


def test_admin_link_hidden_for_non_admin(non_admin_client: TestClient) -> None:
    page = non_admin_client.get("/games").text
    assert 'href="/admin"' not in page


# ---------------------------------------------------------------------------
# GET /admin/games
# ---------------------------------------------------------------------------


def test_admin_games_lists_all_fixtures(admin_client: TestClient) -> None:
    r = admin_client.get("/admin/games")
    assert r.status_code == 200
    assert f'id="admin-game-{GAME_OPENER_ID}"' in r.text
    # Inputs are present for the opener.
    assert 'name="score_home"' in r.text
    assert 'name="score_away"' in r.text
    assert 'name="notes"' in r.text


# ---------------------------------------------------------------------------
# POST /admin/games/{id} - HTMX
# ---------------------------------------------------------------------------


def test_htmx_post_sets_result(admin_client: TestClient, db: Session) -> None:
    r = admin_client.post(
        f"/admin/games/{GAME_OPENER_ID}",
        data={"score_home": "2", "score_away": "1", "notes": "AET"},
        headers={"HX-Request": "true"},
    )
    assert r.status_code == 200, r.text
    assert "<!DOCTYPE html>" not in r.text
    assert f'id="admin-game-{GAME_OPENER_ID}"' in r.text
    assert "saved" in r.text

    db.expire_all()
    game = db.get(Game, GAME_OPENER_ID)
    assert game is not None
    assert (game.score_home, game.score_away, game.notes) == (2, 1, "AET")


def test_htmx_post_clears_result_with_blank_scores(
    admin_client: TestClient,
    db: Session,
) -> None:
    admin_client.post(
        f"/admin/games/{GAME_OPENER_ID}",
        data={"score_home": "1", "score_away": "0", "notes": "OT"},
        headers={"HX-Request": "true"},
    )
    r = admin_client.post(
        f"/admin/games/{GAME_OPENER_ID}",
        data={"score_home": "", "score_away": "", "notes": ""},
        headers={"HX-Request": "true"},
    )
    assert r.status_code == 200
    db.expire_all()
    game = db.get(Game, GAME_OPENER_ID)
    assert game is not None
    assert game.score_home is None
    assert game.score_away is None
    assert game.notes is None


def test_htmx_post_mixed_returns_error(admin_client: TestClient) -> None:
    r = admin_client.post(
        f"/admin/games/{GAME_OPENER_ID}",
        data={"score_home": "2", "score_away": "", "notes": ""},
        headers={"HX-Request": "true"},
    )
    assert r.status_code == 200
    assert "fill in both scores" in r.text.lower()


def test_htmx_post_non_numeric_returns_error(admin_client: TestClient) -> None:
    r = admin_client.post(
        f"/admin/games/{GAME_OPENER_ID}",
        data={"score_home": "foo", "score_away": "1", "notes": ""},
        headers={"HX-Request": "true"},
    )
    assert r.status_code == 200
    assert "whole number" in r.text.lower()


def test_htmx_post_out_of_range_returns_error(admin_client: TestClient) -> None:
    r = admin_client.post(
        f"/admin/games/{GAME_OPENER_ID}",
        data={"score_home": "150", "score_away": "1", "notes": ""},
        headers={"HX-Request": "true"},
    )
    assert r.status_code == 200
    assert "between" in r.text.lower()


def test_htmx_post_notes_too_long_returns_error(admin_client: TestClient) -> None:
    r = admin_client.post(
        f"/admin/games/{GAME_OPENER_ID}",
        data={"score_home": "1", "score_away": "0", "notes": "x" * 200},
        headers={"HX-Request": "true"},
    )
    assert r.status_code == 200
    assert "notes" in r.text.lower()


def test_htmx_post_unknown_game_404s(admin_client: TestClient) -> None:
    r = admin_client.post(
        "/admin/games/99999",
        data={"score_home": "1", "score_away": "0", "notes": ""},
        headers={"HX-Request": "true"},
    )
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# POST /admin/games/{id} - vanilla form fallback
# ---------------------------------------------------------------------------


def test_plain_post_redirects(admin_client: TestClient, db: Session) -> None:
    r = admin_client.post(
        f"/admin/games/{GAME_OPENER_ID}",
        data={"score_home": "3", "score_away": "2", "notes": ""},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert r.headers["location"] == "/admin/games"
    db.expire_all()
    game = db.get(Game, GAME_OPENER_ID)
    assert game is not None
    assert (game.score_home, game.score_away) == (3, 2)


# ---------------------------------------------------------------------------
# End-to-end: scoring loop closes
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# /admin/games - knockout team picker (placeholder resolution)
# ---------------------------------------------------------------------------


def test_admin_games_shows_placeholder_label_for_knockout(
    admin_client: TestClient,
) -> None:
    page = admin_client.get("/admin/games").text
    # The Round-of-32 picker for game 73 has slots "2A" (home) and
    # "2B" (away) before any team is set.
    assert "2A" in page
    assert "2B" in page
    # Group-stage games don't render the team-picker submit button.
    assert 'aria-label="Save teams for game 1"' not in page
    # But knockout rows do.
    assert 'aria-label="Save teams for game 73"' in page


def test_admin_games_picker_lists_all_48_teams(admin_client: TestClient) -> None:
    page = admin_client.get("/admin/games").text
    for code in ("mex", "ger", "bra", "fra", "esp", "eng", "arg", "jpn"):
        assert f'value="{code}"' in page


def test_post_teams_requires_admin(non_admin_client: TestClient) -> None:
    r = non_admin_client.post(
        f"/admin/games/{GAME_R32_FIRST_ID}/teams",
        data={"team_home_id": "mex", "team_away_id": "can"},
    )
    assert r.status_code == 403


def test_post_teams_requires_login(auth_client: TestClient) -> None:
    r = auth_client.post(
        f"/admin/games/{GAME_R32_FIRST_ID}/teams",
        data={"team_home_id": "mex", "team_away_id": "can"},
    )
    assert r.status_code == 401


def test_htmx_post_teams_resolves_placeholder(
    admin_client: TestClient,
    db: Session,
) -> None:
    r = admin_client.post(
        f"/admin/games/{GAME_R32_FIRST_ID}/teams",
        data={"team_home_id": "mex", "team_away_id": "can"},
        headers={"HX-Request": "true"},
    )
    assert r.status_code == 200, r.text
    assert "<!DOCTYPE html>" not in r.text
    assert f'id="admin-game-{GAME_R32_FIRST_ID}"' in r.text
    assert "saved" in r.text

    db.expire_all()
    game = db.get(Game, GAME_R32_FIRST_ID)
    assert game is not None
    assert game.team_home_id == "mex"
    assert game.team_away_id == "can"


def test_htmx_post_teams_clears_back_to_placeholder(
    admin_client: TestClient,
    db: Session,
) -> None:
    admin_client.post(
        f"/admin/games/{GAME_R32_FIRST_ID}/teams",
        data={"team_home_id": "mex", "team_away_id": "can"},
        headers={"HX-Request": "true"},
    )
    r = admin_client.post(
        f"/admin/games/{GAME_R32_FIRST_ID}/teams",
        data={"team_home_id": "", "team_away_id": ""},
        headers={"HX-Request": "true"},
    )
    assert r.status_code == 200
    db.expire_all()
    game = db.get(Game, GAME_R32_FIRST_ID)
    assert game is not None
    assert game.team_home_id is None
    assert game.team_away_id is None


def test_htmx_post_teams_same_team_returns_error(
    admin_client: TestClient,
) -> None:
    r = admin_client.post(
        f"/admin/games/{GAME_R32_FIRST_ID}/teams",
        data={"team_home_id": "mex", "team_away_id": "mex"},
        headers={"HX-Request": "true"},
    )
    assert r.status_code == 200
    assert "must differ" in r.text.lower()


def test_htmx_post_teams_unknown_team_returns_error(
    admin_client: TestClient,
) -> None:
    r = admin_client.post(
        f"/admin/games/{GAME_R32_FIRST_ID}/teams",
        data={"team_home_id": "zzz", "team_away_id": "can"},
        headers={"HX-Request": "true"},
    )
    assert r.status_code == 200
    assert "unknown team" in r.text.lower()


def test_htmx_post_teams_group_stage_returns_error(
    admin_client: TestClient,
) -> None:
    r = admin_client.post(
        f"/admin/games/{GAME_OPENER_ID}/teams",
        data={"team_home_id": "mex", "team_away_id": "rsa"},
        headers={"HX-Request": "true"},
    )
    assert r.status_code == 200
    assert "group-stage" in r.text.lower() or "group stage" in r.text.lower()


def test_htmx_post_teams_unknown_game_404s(admin_client: TestClient) -> None:
    r = admin_client.post(
        "/admin/games/99999/teams",
        data={"team_home_id": "mex", "team_away_id": "can"},
        headers={"HX-Request": "true"},
    )
    assert r.status_code == 404


def test_plain_post_teams_redirects(admin_client: TestClient, db: Session) -> None:
    r = admin_client.post(
        f"/admin/games/{GAME_R32_FIRST_ID}/teams",
        data={"team_home_id": "mex", "team_away_id": "can"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert r.headers["location"] == "/admin/games"
    db.expire_all()
    game = db.get(Game, GAME_R32_FIRST_ID)
    assert game is not None
    assert (game.team_home_id, game.team_away_id) == ("mex", "can")


def test_games_page_shows_placeholder_for_anonymous(
    auth_client: TestClient,
) -> None:
    """Anonymous visitors browsing /games see the bracket slot labels for
    knockout fixtures with no team set yet."""
    page = auth_client.get("/games").text
    # Round of 32, match 73: 2A v 2B.
    assert "2A" in page
    assert "2B" in page


def test_resolved_team_displaces_placeholder_on_games_page(
    admin_client: TestClient,
) -> None:
    """Once teams are set, the placeholder ("2A") gives way to the team name."""
    admin_client.post(
        f"/admin/games/{GAME_R32_FIRST_ID}/teams",
        data={"team_home_id": "mex", "team_away_id": "can"},
        headers={"HX-Request": "true"},
    )
    page = admin_client.get("/games").text
    assert "Mexico" in page
    assert "Canada" in page


def test_admin_result_makes_bet_score_show_up(
    auth_client: TestClient,
    db: Session,
) -> None:
    """An admin entering a result should flip a user's prior bet to scored."""
    # Step 1: register a regular user, place a bet on the opener.
    auth_client.post(
        "/register",
        data={
            "name": "Carol",
            "email": "carol@example.com",
            "password": "hunter222",
        },
    )
    auth_client.post(
        "/login",
        data={
            "email": "carol@example.com",
            "password": "hunter222",
        },
    )
    auth_client.post(
        f"/bets/{GAME_OPENER_ID}",
        data={"score_home": "2", "score_away": "1"},
        headers={"HX-Request": "true"},
    )
    auth_client.post("/logout")

    # Step 2: register + promote an admin, then enter the official result.
    auth_client.post(
        "/register",
        data={
            "name": "Admin",
            "email": "admin@example.com",
            "password": "hunter222",
        },
    )
    _promote(db, "admin@example.com")
    auth_client.post(
        "/login",
        data={
            "email": "admin@example.com",
            "password": "hunter222",
        },
    )
    auth_client.post(
        f"/admin/games/{GAME_OPENER_ID}",
        data={"score_home": "2", "score_away": "1", "notes": ""},
        headers={"HX-Request": "true"},
    )
    auth_client.post("/logout")

    # Step 3: Carol logs back in and visits /bets. Move the opener kickoff
    # into the past so the cell renders the locked, scored view.
    game = db.get(Game, GAME_OPENER_ID)
    assert game is not None
    original_kickoff = game.kickoff_time
    from datetime import datetime, timedelta

    game.kickoff_time = datetime.now(UTC) - timedelta(hours=2)
    db.commit()
    try:
        auth_client.post(
            "/login",
            data={
                "email": "carol@example.com",
                "password": "hunter222",
            },
        )
        page = auth_client.get("/bets").text
        # Locked view shows the bet inside a coloured success badge.
        assert "text-bg-success" in page
        # The "Pts" column shows 5 (exact match -> DEFAULT_CONFIG.points_result).
        # We don't grep for "5" alone (too noisy) but make sure the
        # editable form is gone for the opener.
        import re

        cell = re.search(
            rf'id="bet-cell-{GAME_OPENER_ID}".*?</td>',
            page,
            re.DOTALL,
        )
        assert cell, "opener cell missing"
        assert "<form" not in cell.group(0).lower()
    finally:
        game.kickoff_time = original_kickoff
        db.commit()
