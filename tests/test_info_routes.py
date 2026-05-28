"""End-to-end tests for the public ``/info`` page."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from app.models import Config


def _register_and_login(client: TestClient) -> None:
    r = client.post(
        "/register",
        data={"name": "Alice", "email": "a@example.com", "password": "hunter222"},
        follow_redirects=False,
    )
    assert r.status_code == 303, r.text
    r = client.post(
        "/login", data={"email": "a@example.com", "password": "hunter222"}, follow_redirects=False
    )
    assert r.status_code == 303, r.text


@pytest.fixture()
def empty_config(seeded_engine) -> Iterator[None]:
    """Snapshot, clear, restore the config singleton - used by fallback tests."""
    Session_ = sessionmaker(bind=seeded_engine, expire_on_commit=False, future=True)
    with Session_() as s:
        rows = s.query(Config).all()
        snapshot = [
            {
                "id": r.id,
                "title": r.title,
                "owner": r.owner,
                "admin_email": r.admin_email,
                "show_important_message": r.show_important_message,
                "points_result": r.points_result,
                "points_tendency": r.points_tendency,
                "points_tendency_spread": r.points_tendency_spread,
                "rules_en": r.rules_en,
                "rules_de": r.rules_de,
            }
            for r in rows
        ]
    with seeded_engine.begin() as conn:
        conn.execute(text("DELETE FROM config"))
    try:
        yield
    finally:
        with seeded_engine.begin() as conn:
            conn.execute(text("DELETE FROM config"))
            for row in snapshot:
                conn.execute(
                    text(
                        "INSERT INTO config (id, title, owner, admin_email, "
                        "show_important_message, points_result, points_tendency, "
                        "points_tendency_spread, rules_en, rules_de) VALUES "
                        "(:id, :title, :owner, :admin_email, "
                        ":show_important_message, :points_result, :points_tendency, "
                        ":points_tendency_spread, :rules_en, :rules_de)"
                    ),
                    row,
                )


# ---------------------------------------------------------------------------
# Public access
# ---------------------------------------------------------------------------


def test_info_is_public(auth_client: TestClient) -> None:
    """No login required."""
    r = auth_client.get("/info")
    assert r.status_code == 200
    assert "<!DOCTYPE html>" in r.text


def test_info_renders_rules_html(auth_client: TestClient) -> None:
    """The Markdown content is converted to HTML and embedded raw."""
    r = auth_client.get("/info")
    page = r.text
    assert "<h2>" in page  # at least one rendered section heading
    assert "About this game" in page  # page chrome
    # Point values from the seeded config (5/3/2) surface in the rules table.
    assert "<strong>5</strong>" in page


def test_info_anon_shows_signup_cta(auth_client: TestClient) -> None:
    """Anonymous visitors get a 'create account / sign in' nudge below the rules."""
    r = auth_client.get("/info")
    assert "Create account" in r.text
    assert 'href="/register"' in r.text


def test_info_logged_in_hides_signup_cta(auth_client: TestClient) -> None:
    _register_and_login(auth_client)
    r = auth_client.get("/info")
    # Signed-in users shouldn't see the "Create account" call-to-action.
    assert "Create account" not in r.text or 'href="/register"' not in r.text


def test_info_link_in_navbar(auth_client: TestClient) -> None:
    """The /info link should be present on at least the games page."""
    page = auth_client.get("/games").text
    assert 'href="/info"' in page


def test_info_falls_back_when_config_table_empty(
    auth_client: TestClient,
    empty_config: None,
) -> None:
    r = auth_client.get("/info")
    assert r.status_code == 200
    assert "<h2>" in r.text
    assert "About this game" in r.text


def test_info_renders_pipe_tables(auth_client: TestClient) -> None:
    """The scoring breakdown ships as a Markdown table; it must render as <table>."""
    page = auth_client.get("/info").text
    assert "<table>" in page
    assert "<th>Outcome</th>" in page


# ---------------------------------------------------------------------------
# Language selection (preferred_language on User)
# ---------------------------------------------------------------------------


def test_info_anonymous_serves_english(auth_client: TestClient) -> None:
    page = auth_client.get("/info").text
    assert "Welcome to" in page
    assert "Willkommen" not in page


def test_info_serves_german_to_de_user(auth_client: TestClient) -> None:
    """A user with preferred_language='de' sees the German rules.

    Registration always creates users with ``preferred_language='en'``;
    switching is done from the /settings page.
    """
    auth_client.post(
        "/register",
        data={"name": "Hans", "email": "hans@example.com", "password": "hunter222"},
        follow_redirects=False,
    )
    auth_client.post(
        "/login",
        data={"email": "hans@example.com", "password": "hunter222"},
        follow_redirects=False,
    )
    # Flip the preference via the public settings endpoint.
    r = auth_client.post(
        "/settings/profile",
        data={"name": "Hans", "preferred_language": "de"},
        follow_redirects=False,
    )
    assert r.status_code in (303, 200)

    page = auth_client.get("/info").text
    assert "Willkommen" in page
    assert "Welcome to" not in page
    # Point values still surface in the German variant.
    assert "<strong>5</strong>" in page


def test_info_serves_english_to_en_user(auth_client: TestClient) -> None:
    auth_client.post(
        "/register",
        data={"name": "Alice", "email": "alice@example.com", "password": "hunter222"},
        follow_redirects=False,
    )
    auth_client.post(
        "/login",
        data={"email": "alice@example.com", "password": "hunter222"},
        follow_redirects=False,
    )
    page = auth_client.get("/info").text
    assert "Welcome to" in page
    assert "Willkommen" not in page
