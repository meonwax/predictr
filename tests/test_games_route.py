"""Integration tests for the read-only ``/games`` route."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlalchemy.orm import sessionmaker

from app.dependencies import get_db
from app.main import app


@pytest.fixture(scope="module")
def client(seeded_engine: Engine) -> Iterator[TestClient]:
    """A FastAPI TestClient with ``get_db`` overridden to use the seeded engine.

    Module-scoped so the override is set up once and torn down at the end,
    matching the lifetime of the seeded postgres testcontainer.
    """
    Session_ = sessionmaker(bind=seeded_engine, expire_on_commit=False, future=True)

    def _override_get_db() -> Iterator:
        with Session_() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.pop(get_db, None)


# --- Plumbing checks ---------------------------------------------------------


def test_root_renders_the_home_dashboard(client: TestClient) -> None:
    """``/`` no longer redirects - it now serves the home dashboard.

    The plumbing-level assertion lives in ``tests/test_home_routes.py``;
    here we just confirm the redirect was removed and a 200 HTML
    response is served at the bare root.
    """
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")


def test_healthz_still_ok(client: TestClient) -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# --- Games page content -----------------------------------------------------


def test_games_page_returns_html_200(client: TestClient) -> None:
    response = client.get("/games")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")


def test_games_page_lists_all_18_groups(client: TestClient) -> None:
    """Every group (A..L plus the six knockout pseudo-groups) renders as its own section."""
    body = client.get("/games").text
    # Each section has id="group-<gid>" in its <section> tag.
    for gid in [
        "a",
        "b",
        "c",
        "d",
        "e",
        "f",
        "g",
        "h",
        "i",
        "j",
        "k",
        "l",
        "r32",
        "r16",
        "qf",
        "sf",
        "3rd",
        "fin",
    ]:
        assert f'id="group-{gid}"' in body, f"missing section for group {gid!r}"


def test_games_page_renders_opening_match(client: TestClient) -> None:
    """Match 1 - Mexico v South Africa at Estadio Azteca on 11 Jun 2026."""
    body = client.get("/games").text
    assert "Mexico" in body
    assert "South Africa" in body
    assert "Estadio Azteca" in body
    assert "Thu, 11 Jun 2026 19:00 UTC" in body


def test_games_page_renders_final_with_placeholder_slots(client: TestClient) -> None:
    """The final (match 104) has no resolved teams yet - render the bracket-slot
    placeholders ("W101" / "W102") instead of a literal "TBD"."""
    body = client.get("/games").text
    assert "MetLife Stadium" in body
    assert "Final" in body
    # The final's slots are "winner of semi-final 101" / "winner of 102".
    assert "W101" in body
    assert "W102" in body


def test_games_page_renders_phase_labels(client: TestClient) -> None:
    body = client.get("/games").text
    for label in (
        "Group A",
        "Group L",
        "Round of 32",
        "Round of 16",
        "Quarter-finals",
        "Semi-finals",
        "Third-place play-off",
        "Final",
    ):
        assert label in body, f"missing phase label {label!r}"


def test_games_page_renders_flag_images_for_known_teams(client: TestClient) -> None:
    """Mexico -> mx.svg, USA -> us.svg, England -> gb-eng.svg, Scotland -> gb-sct.svg."""
    body = client.get("/games").text
    for iso in ("mx", "us", "gb-eng", "gb-sct"):
        assert f"img/flags/{iso}.svg" in body, f"missing flag link for {iso!r}"


def test_games_page_shows_no_resolved_scores_yet(client: TestClient) -> None:
    """All 104 games are pre-tournament: the 'vs' placeholder should appear in each row."""
    body = client.get("/games").text
    # 12 group-stage groups have 6 matches each = 72; plus 32 knockout rows.
    assert body.count(">vs<") == 104


def test_games_page_links_to_static_bootstrap_css(client: TestClient) -> None:
    body = client.get("/games").text
    assert "/static/vendor/bootstrap-5.3.3/css/bootstrap.min.css" in body
    assert "/static/vendor/htmx-2.0.3/htmx.min.js" in body


# --- Static asset wiring -----------------------------------------------------


def test_static_bootstrap_css_is_served(client: TestClient) -> None:
    r = client.get("/static/vendor/bootstrap-5.3.3/css/bootstrap.min.css")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/css")


def test_static_mexico_flag_is_served(client: TestClient) -> None:
    r = client.get("/static/img/flags/mx.svg")
    assert r.status_code == 200
    assert r.headers["content-type"] in {"image/svg+xml", "application/octet-stream"}


def test_missing_static_asset_returns_404(client: TestClient) -> None:
    r = client.get("/static/img/flags/zz.svg")
    assert r.status_code == 404
