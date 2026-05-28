"""End-to-end tests for the ``/shouts`` page and POST endpoint."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from app.models import Shout


def _register_and_login(
    client: TestClient,
    *,
    name: str = "Alice",
    email: str = "alice@example.com",
) -> None:
    r = client.post(
        "/register",
        data={"name": name, "email": email, "password": "hunter222"},
        follow_redirects=False,
    )
    assert r.status_code == 303, r.text
    r = client.post(
        "/login", data={"email": email, "password": "hunter222"}, follow_redirects=False
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


@pytest.fixture(autouse=True)
def _reset_shouts(seeded_engine) -> Iterator[None]:
    yield
    with seeded_engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE shout RESTART IDENTITY CASCADE"))


# ---------------------------------------------------------------------------
# Access control + page render
# ---------------------------------------------------------------------------


def test_shouts_requires_login(auth_client: TestClient) -> None:
    r = auth_client.get("/shouts")
    assert r.status_code == 401


def test_post_requires_login(auth_client: TestClient) -> None:
    r = auth_client.post("/shouts", data={"message": "hi"})
    assert r.status_code == 401


def test_shouts_page_renders(logged_in_client: TestClient) -> None:
    r = logged_in_client.get("/shouts")
    assert r.status_code == 200
    assert "Shoutbox" in r.text
    assert 'id="shoutbox-panel"' in r.text
    assert 'name="message"' in r.text


def test_shouts_empty_state(logged_in_client: TestClient) -> None:
    r = logged_in_client.get("/shouts")
    assert "No shouts yet" in r.text


def test_navbar_has_shoutbox_link(logged_in_client: TestClient) -> None:
    page = logged_in_client.get("/games").text
    assert 'href="/shouts"' in page


# ---------------------------------------------------------------------------
# HTMX POST: success
# ---------------------------------------------------------------------------


def test_htmx_post_creates_shout_and_returns_panel(
    logged_in_client: TestClient,
    db: Session,
) -> None:
    r = logged_in_client.post(
        "/shouts",
        data={"message": "hello world"},
        headers={"HX-Request": "true"},
    )
    assert r.status_code == 200
    assert "<!DOCTYPE html>" not in r.text
    assert 'id="shoutbox-panel"' in r.text
    assert "hello world" in r.text
    # The input was cleared on success.
    assert 'value=""' in r.text or 'value="" maxlength' in r.text
    # The shout is persisted.
    assert db.query(Shout).count() == 1


def test_htmx_post_shows_existing_shouts_newest_first(
    logged_in_client: TestClient,
) -> None:
    """Newer messages appear before older ones in the rendered panel.

    We isolate the rendered ``<ul>`` (the list of shouts) so unrelated
    occurrences of the words "older" / "newer" anywhere else in the
    panel (eg. timestamp humanisation) can't skew the ordering check.
    """
    logged_in_client.post("/shouts", data={"message": "OLDER_MSG"}, headers={"HX-Request": "true"})
    r = logged_in_client.post(
        "/shouts", data={"message": "NEWER_MSG"}, headers={"HX-Request": "true"}
    )
    import re

    m = re.search(r'<ul class="list-group[^"]*">(.*?)</ul>', r.text, re.DOTALL)
    assert m is not None, "shout list <ul> not found in response"
    list_html = m.group(1)
    newer_at = list_html.index("NEWER_MSG")
    older_at = list_html.index("OLDER_MSG")
    assert newer_at < older_at, f"expected NEWER_MSG@{newer_at} before OLDER_MSG@{older_at}"


# ---------------------------------------------------------------------------
# HTMX POST: validation errors
# ---------------------------------------------------------------------------


def test_htmx_post_empty_returns_error_panel(
    logged_in_client: TestClient,
    db: Session,
) -> None:
    r = logged_in_client.post(
        "/shouts",
        data={"message": "   "},
        headers={"HX-Request": "true"},
    )
    assert r.status_code == 200
    assert "empty" in r.text.lower()
    assert "alert-danger" in r.text
    assert db.query(Shout).count() == 0


def test_htmx_post_too_long_returns_error(
    logged_in_client: TestClient,
    db: Session,
) -> None:
    r = logged_in_client.post(
        "/shouts",
        data={"message": "x" * 5000},
        headers={"HX-Request": "true"},
    )
    assert r.status_code == 200
    assert "alert-danger" in r.text
    assert db.query(Shout).count() == 0


def test_htmx_post_error_preserves_draft(
    logged_in_client: TestClient,
) -> None:
    """A failed submit re-renders the user's draft so they can fix and retry."""
    msg = "x" * 1000  # too long, will fail
    r = logged_in_client.post(
        "/shouts",
        data={"message": msg},
        headers={"HX-Request": "true"},
    )
    # The draft should round-trip into the input value.
    assert msg in r.text


# ---------------------------------------------------------------------------
# Vanilla form fallback
# ---------------------------------------------------------------------------


def test_plain_post_redirects(
    logged_in_client: TestClient,
    db: Session,
) -> None:
    r = logged_in_client.post(
        "/shouts",
        data={"message": "hello via 303"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert r.headers["location"] == "/shouts"
    assert db.query(Shout).count() == 1


def test_plain_post_invalid_still_redirects(
    logged_in_client: TestClient,
    db: Session,
) -> None:
    """Without HTMX, validation errors silently redirect (no flash storage yet)."""
    r = logged_in_client.post(
        "/shouts",
        data={"message": ""},
        follow_redirects=False,
    )
    # Either 303 (our route's choice) or 422; the important invariant is no row.
    assert r.status_code in (303, 422)
    assert db.query(Shout).count() == 0


# ---------------------------------------------------------------------------
# Cross-user
# ---------------------------------------------------------------------------


def test_shouts_show_all_users(auth_client: TestClient, db: Session) -> None:
    _register_and_login(auth_client, name="Alice", email="alice@example.com")
    auth_client.post("/shouts", data={"message": "from Alice"}, headers={"HX-Request": "true"})
    auth_client.post("/logout")
    _register_and_login(auth_client, name="Bob", email="bob@example.com")
    auth_client.post("/shouts", data={"message": "from Bob"}, headers={"HX-Request": "true"})

    page = auth_client.get("/shouts").text
    assert "Alice" in page
    assert "Bob" in page
    assert "from Alice" in page
    assert "from Bob" in page
