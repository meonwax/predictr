"""Tests for the project's visual identity assets.

Two distinct things are exercised here:

* The **favicon** at ``app/static/img/favicon.png`` (small PNG, browser tab).
* The **WC 2026 emblem** at ``app/static/img/wc2026/emblem.svg`` (auth-page
  decoration + anonymous home hero). The emblem's CC BY-SA 4.0 credit
  lives in the project README rather than on a rendered page.
"""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

STATIC_ROOT = Path(__file__).resolve().parent.parent / "app" / "static"

FAVICON_PATH = "/static/img/favicon.png"
FAVICON_FS = STATIC_ROOT / "img" / "favicon.png"

EMBLEM_PATH = "/static/img/wc2026/emblem.svg"
EMBLEM_FS = STATIC_ROOT / "img" / "wc2026" / "emblem.svg"


# ---------------------------------------------------------------------------
# Both static assets must exist on disk (precondition for the tests below).
# ---------------------------------------------------------------------------


def test_favicon_png_is_present_on_disk() -> None:
    assert FAVICON_FS.is_file(), (
        f"Missing favicon at {FAVICON_FS}. It is a committed static asset; "
        f"did the file get removed from the repo?"
    )


def test_emblem_svg_is_present_on_disk() -> None:
    assert EMBLEM_FS.is_file(), (
        f"Missing emblem at {EMBLEM_FS}. It is a committed static asset; "
        f"did the file get removed from the repo?"
    )


def test_favicon_is_served_as_static_file(auth_client: TestClient) -> None:
    r = auth_client.get(FAVICON_PATH)
    assert r.status_code == 200
    assert "png" in r.headers.get("content-type", "").lower()
    # PNG signature: 0x89 'P' 'N' 'G' 0x0D 0x0A 0x1A 0x0A
    assert r.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_emblem_is_served_as_static_file(auth_client: TestClient) -> None:
    r = auth_client.get(EMBLEM_PATH)
    assert r.status_code == 200
    assert "svg" in r.headers.get("content-type", "").lower()
    assert b"<svg" in r.content[:500]


# ---------------------------------------------------------------------------
# Favicon: present on every rendered page via base.html.
# ---------------------------------------------------------------------------


def test_favicon_link_is_in_base_template_anonymous(auth_client: TestClient) -> None:
    page = auth_client.get("/").text
    assert 'rel="icon"' in page
    assert 'type="image/png"' in page
    assert FAVICON_PATH in page


def test_favicon_link_persists_when_logged_in(auth_client: TestClient) -> None:
    auth_client.post(
        "/register",
        data={"name": "Alice", "email": "a@example.com", "password": "hunter222"},
        follow_redirects=False,
    )
    auth_client.post(
        "/login",
        data={"email": "a@example.com", "password": "hunter222"},
        follow_redirects=False,
    )
    assert 'rel="icon"' in auth_client.get("/").text


# ---------------------------------------------------------------------------
# Emblem placement on every auth page.
# ---------------------------------------------------------------------------


def test_login_page_shows_emblem(auth_client: TestClient) -> None:
    page = auth_client.get("/login").text
    assert EMBLEM_PATH in page
    assert 'alt="FIFA World Cup 2026 emblem"' in page


def test_register_page_shows_emblem(auth_client: TestClient) -> None:
    page = auth_client.get("/register").text
    assert EMBLEM_PATH in page


def test_lostpwd_page_shows_emblem(auth_client: TestClient) -> None:
    page = auth_client.get("/lostpwd").text
    assert EMBLEM_PATH in page


def test_reset_password_page_shows_emblem(auth_client: TestClient) -> None:
    """Even the error-path render (expired/invalid token) shows the emblem."""
    page = auth_client.get("/password/reset/not-a-real-token").text
    assert EMBLEM_PATH in page


# ---------------------------------------------------------------------------
# Emblem placement on the home dashboard.
# ---------------------------------------------------------------------------


def test_home_anonymous_hero_shows_emblem(auth_client: TestClient) -> None:
    """Anonymous landing page shows the emblem in the hero block."""
    page = auth_client.get("/").text
    assert EMBLEM_PATH in page


def test_home_authenticated_hero_omits_the_emblem_image(auth_client: TestClient) -> None:
    """Logged-in users get the personalised greeting, no big logo.

    The favicon link in <head> no longer references the emblem (the
    favicon is a separate small PNG), so the emblem should not appear
    on the authenticated home page at all.
    """
    r1 = auth_client.post(
        "/register",
        data={"name": "Bob", "email": "b@example.com", "password": "hunter222"},
        follow_redirects=False,
    )
    assert r1.status_code == 303, r1.text
    r2 = auth_client.post(
        "/login",
        data={"email": "b@example.com", "password": "hunter222"},
        follow_redirects=False,
    )
    assert r2.status_code == 303, r2.text
    page = auth_client.get("/").text
    assert "Welcome, Bob!" in page, "expected the authenticated hero greeting"
    assert EMBLEM_PATH not in page, "emblem should not render on the authenticated home"
