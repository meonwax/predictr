"""End-to-end tests for the branded 401 / 403 / 404 / 500 pages.

The actual exception handlers live in :mod:`app.main`. These tests drive
them through the real :class:`fastapi.testclient.TestClient` so we exercise
the whole stack: language middleware -> router lookup / dependency chain
-> exception handler -> Jinja2 template -> HTTP response.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.dependencies import get_current_user, get_db
from app.main import app

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _register_and_login(client: TestClient, *, email: str = "u@example.com") -> None:
    """Register a new ROLE_USER and sign them in on *client*."""
    r = client.post(
        "/register",
        data={"name": "Alice", "email": email, "password": "hunter222"},
        follow_redirects=False,
    )
    assert r.status_code == 303, r.text
    r = client.post(
        "/login",
        data={"email": email, "password": "hunter222"},
        follow_redirects=False,
    )
    assert r.status_code == 303, r.text


# ---------------------------------------------------------------------------
# 404 - unknown route
# ---------------------------------------------------------------------------


def test_404_renders_branded_html_page(auth_client: TestClient) -> None:
    """An unknown URL returns the branded 404 page with status 404."""
    r = auth_client.get("/this-route-does-not-exist")
    assert r.status_code == 404
    page = r.text
    assert "<!DOCTYPE html>" in page
    assert "Page not found" in page
    # The shared layout renders the big status code above the heading.
    assert "404" in page
    # The footer/navbar of the base layout are present, so the page is
    # rendered inside the full app chrome instead of being a stub.
    assert "navbar" in page


def test_404_returns_json_when_client_only_accepts_json(
    auth_client: TestClient,
) -> None:
    """API-shaped clients keep the FastAPI ``{"detail": ...}`` body."""
    r = auth_client.get(
        "/this-route-does-not-exist",
        headers={"Accept": "application/json"},
    )
    assert r.status_code == 404
    assert r.headers["content-type"].startswith("application/json")
    assert r.json() == {"detail": "Not Found"}


def test_404_localises_to_german_when_cookie_set(auth_client: TestClient) -> None:
    """The DE catalogue is picked up via the anonymous language cookie."""
    auth_client.cookies.set("predictr_lang", "de")
    try:
        r = auth_client.get("/no-such-page")
    finally:
        auth_client.cookies.delete("predictr_lang")
    assert r.status_code == 404
    assert "Seite nicht gefunden" in r.text
    assert "Page not found" not in r.text


# ---------------------------------------------------------------------------
# 401 - unauthenticated visit to a protected page
# ---------------------------------------------------------------------------


def test_401_renders_branded_html_page(auth_client: TestClient) -> None:
    """Anonymous GET /bets surfaces the 401 page, not a JSON detail."""
    r = auth_client.get("/bets")
    assert r.status_code == 401
    page = r.text
    assert "<!DOCTYPE html>" in page
    assert "Please sign in" in page
    assert "401" in page
    assert 'href="/login"' in page


def test_401_returns_json_when_client_only_accepts_json(
    auth_client: TestClient,
) -> None:
    r = auth_client.get("/bets", headers={"Accept": "application/json"})
    assert r.status_code == 401
    assert r.headers["content-type"].startswith("application/json")
    body = r.json()
    assert body["detail"] == "Authentication required."


# ---------------------------------------------------------------------------
# 403 - logged in but lacking the role
# ---------------------------------------------------------------------------


def test_403_renders_branded_html_page(auth_client: TestClient) -> None:
    """A ROLE_USER visiting /admin gets the 403 page."""
    _register_and_login(auth_client)
    r = auth_client.get("/admin")
    assert r.status_code == 403
    page = r.text
    assert "<!DOCTYPE html>" in page
    assert "Forbidden" in page
    assert "403" in page
    # The base navbar should reflect the signed-in state so the user can
    # still navigate elsewhere - the 403 means *this* page is off-limits,
    # not "log out and start over".
    assert "Alice" in page


def test_403_returns_json_when_client_only_accepts_json(
    auth_client: TestClient,
) -> None:
    _register_and_login(auth_client, email="json@example.com")
    r = auth_client.get("/admin", headers={"Accept": "application/json"})
    assert r.status_code == 403
    assert r.headers["content-type"].startswith("application/json")
    assert r.json()["detail"] == "Admin role required."


# ---------------------------------------------------------------------------
# 500 - unhandled exception
# ---------------------------------------------------------------------------


@pytest.fixture()
def boom_client(
    seeded_engine: Engine,
) -> Iterator[TestClient]:
    """A TestClient where the ``get_current_user`` dep always blows up.

    Used to drive the catch-all 500 handler. ``raise_server_exceptions``
    has to be ``False`` so the exception is converted into a real HTTP
    response by the registered ``Exception`` handler instead of being
    re-raised inside the test. The DB override mirrors ``auth_client``
    so the surrounding plumbing (sessions, middleware) is identical.
    """
    Session_ = sessionmaker(bind=seeded_engine, expire_on_commit=False, future=True)

    def _override_get_db() -> Iterator[Session]:
        with Session_() as session:
            yield session

    def _boom() -> None:
        raise RuntimeError("synthetic boom for the 500 test")

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _boom
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            yield client
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)


def test_500_renders_branded_html_page(boom_client: TestClient) -> None:
    """An unhandled exception surfaces the branded 500 page."""
    r = boom_client.get("/")
    assert r.status_code == 500
    page = r.text
    assert "<!DOCTYPE html>" in page
    assert "Something went wrong" in page
    assert "500" in page


def test_500_returns_json_when_client_only_accepts_json(
    boom_client: TestClient,
) -> None:
    r = boom_client.get("/", headers={"Accept": "application/json"})
    assert r.status_code == 500
    assert r.headers["content-type"].startswith("application/json")
    assert r.json() == {"detail": "Internal Server Error"}


# ---------------------------------------------------------------------------
# Other status codes still get FastAPI's default JSON detail
# ---------------------------------------------------------------------------


def test_400_keeps_default_json_detail(auth_client: TestClient) -> None:
    """Status codes outside {401,403,404} keep their default JSON body.

    400 is a representative example; we trigger it by raising it manually
    via FastAPI's ``HTTPException`` from a temporary route registered on
    the live app instance for the duration of the test.
    """

    @app.get("/_test_400", include_in_schema=False)
    def _raise_400() -> None:
        raise HTTPException(status_code=400, detail="bad request")

    try:
        r = auth_client.get("/_test_400")
        assert r.status_code == 400
        assert r.headers["content-type"].startswith("application/json")
        assert r.json() == {"detail": "bad request"}
    finally:
        # Surgically remove the test-only route so it doesn't bleed into
        # other tests sharing the same FastAPI app instance.
        app.router.routes = [r for r in app.router.routes if getattr(r, "path", "") != "/_test_400"]
