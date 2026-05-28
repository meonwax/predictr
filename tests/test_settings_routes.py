"""End-to-end tests for the ``/settings`` page and its POST endpoints.

Each test gets a freshly-registered + logged-in user via the
:func:`logged_in_client` fixture; raw DB assertions go through the
session bound to the same testcontainer.
"""

from __future__ import annotations

import io
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy.orm import Session, sessionmaker

from app.models import User


def _register_and_login(
    client: TestClient,
    *,
    name: str = "Alice",
    email: str = "alice@example.com",
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


@pytest.fixture()
def logged_in_client(auth_client: TestClient) -> TestClient:
    _register_and_login(auth_client)
    return auth_client


@pytest.fixture()
def db(seeded_engine) -> Iterator[Session]:
    """Plain SQLAlchemy session - used to read back DB state after requests."""
    Session_ = sessionmaker(bind=seeded_engine, expire_on_commit=False, future=True)
    with Session_() as s:
        yield s


def _png_bytes(size: tuple[int, int] = (200, 100), colour=(0, 0, 255)) -> bytes:
    img = Image.new("RGB", size, colour)
    out = io.BytesIO()
    img.save(out, format="PNG", optimize=True)
    return out.getvalue()


def _jpeg_bytes(size: tuple[int, int] = (200, 200)) -> bytes:
    img = Image.new("RGB", size, (255, 0, 0))
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=90)
    return out.getvalue()


# ---------------------------------------------------------------------------
# Access control
# ---------------------------------------------------------------------------


def test_settings_page_requires_authentication(auth_client: TestClient) -> None:
    """Anonymous request to /settings is rejected with 401."""
    r = auth_client.get("/settings")
    assert r.status_code == 401


def test_settings_profile_post_requires_authentication(auth_client: TestClient) -> None:
    r = auth_client.post(
        "/settings/profile",
        data={"name": "Hacker", "preferred_language": "en"},
    )
    assert r.status_code == 401


# ---------------------------------------------------------------------------
# GET /settings renders all three cards
# ---------------------------------------------------------------------------


def test_settings_page_renders_when_logged_in(logged_in_client: TestClient) -> None:
    r = logged_in_client.get("/settings")
    assert r.status_code == 200
    body = r.text
    for needle in (
        "Account settings",
        'action="/settings/profile"',
        'action="/settings/password"',
        'action="/settings/avatar"',
        'name="preferred_language"',
        'value="Alice"',  # current display name pre-filled
        "alice@example.com",  # signed-in caption
    ):
        assert needle in body, f"missing {needle!r}"


def test_settings_page_shows_saved_banner(logged_in_client: TestClient) -> None:
    r = logged_in_client.get("/settings?saved=profile")
    assert "Profile updated." in r.text


def test_settings_page_shows_error_banner(logged_in_client: TestClient) -> None:
    r = logged_in_client.get("/settings?error=password_wrong_current")
    assert "current password is incorrect" in r.text


# ---------------------------------------------------------------------------
# /settings/profile
# ---------------------------------------------------------------------------


def test_update_profile_changes_db_row(logged_in_client: TestClient, db: Session) -> None:
    r = logged_in_client.post(
        "/settings/profile",
        data={"name": "Alicia", "preferred_language": "de"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert r.headers["location"] == "/settings?saved=profile"
    user = db.query(User).filter_by(email="alice@example.com").one()
    assert user.name == "Alicia"
    assert user.preferred_language == "de"


def test_update_profile_rejects_short_name(logged_in_client: TestClient) -> None:
    r = logged_in_client.post(
        "/settings/profile",
        data={"name": "A", "preferred_language": "en"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert r.headers["location"] == "/settings?error=profile"


def test_update_profile_rejects_unsupported_language(
    logged_in_client: TestClient,
) -> None:
    r = logged_in_client.post(
        "/settings/profile",
        data={"name": "Alice", "preferred_language": "fr"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert r.headers["location"] == "/settings?error=profile"


def test_update_profile_navbar_uses_new_name(logged_in_client: TestClient) -> None:
    logged_in_client.post(
        "/settings/profile",
        data={"name": "Alicia", "preferred_language": "en"},
    )
    body = logged_in_client.get("/games").text
    assert "Alicia" in body


# ---------------------------------------------------------------------------
# /settings/password
# ---------------------------------------------------------------------------


def test_change_password_success(logged_in_client: TestClient, auth_client: TestClient) -> None:
    r = logged_in_client.post(
        "/settings/password",
        data={
            "old_password": "hunter222",
            "new_password": "brand-new-pw",
            "new_password_confirm": "brand-new-pw",
        },
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert r.headers["location"] == "/settings?saved=password"

    # Drop cookie and try the new password against /login.
    logged_in_client.cookies.clear()
    bad = logged_in_client.post(
        "/login", data={"email": "alice@example.com", "password": "hunter222"}
    )
    assert bad.status_code == 401
    good = logged_in_client.post(
        "/login",
        data={"email": "alice@example.com", "password": "brand-new-pw"},
        follow_redirects=False,
    )
    assert good.status_code == 303


def test_change_password_wrong_current(logged_in_client: TestClient) -> None:
    r = logged_in_client.post(
        "/settings/password",
        data={
            "old_password": "definitely-wrong",
            "new_password": "brand-new-pw",
            "new_password_confirm": "brand-new-pw",
        },
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert r.headers["location"] == "/settings?error=password_wrong_current"


def test_change_password_mismatch(logged_in_client: TestClient) -> None:
    r = logged_in_client.post(
        "/settings/password",
        data={
            "old_password": "hunter222",
            "new_password": "brand-new-pw",
            "new_password_confirm": "something-else",
        },
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert r.headers["location"] == "/settings?error=password_mismatch"


def test_change_password_too_short(logged_in_client: TestClient) -> None:
    r = logged_in_client.post(
        "/settings/password",
        data={
            "old_password": "hunter222",
            "new_password": "short",
            "new_password_confirm": "short",
        },
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert r.headers["location"] == "/settings?error=password_too_short"


# ---------------------------------------------------------------------------
# /settings/avatar - upload / serve / delete
# ---------------------------------------------------------------------------


def test_upload_avatar_persists_row_and_links_user(
    logged_in_client: TestClient, db: Session
) -> None:
    png = _png_bytes()
    r = logged_in_client.post(
        "/settings/avatar",
        files={"file": ("me.png", png, "image/png")},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert r.headers["location"] == "/settings?saved=avatar"
    user = db.query(User).filter_by(email="alice@example.com").one()
    assert user.avatar_id is not None
    assert user.avatar.mime_type == "image/png"
    assert len(user.avatar.data) > 0


def test_serve_avatar_returns_image_bytes(logged_in_client: TestClient, db: Session) -> None:
    logged_in_client.post(
        "/settings/avatar",
        files={"file": ("me.jpg", _jpeg_bytes(), "image/jpeg")},
    )
    user_id = db.query(User).filter_by(email="alice@example.com").one().id
    r = logged_in_client.get(f"/avatars/{user_id}")
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/jpeg"
    # Image bytes round-trip as decodable JPEG.
    img = Image.open(io.BytesIO(r.content))
    img.load()
    assert img.format == "JPEG"
    assert img.size == (128, 128)


def test_serve_avatar_for_unknown_user_is_404(auth_client: TestClient) -> None:
    r = auth_client.get("/avatars/999999")
    assert r.status_code == 404


def test_serve_avatar_for_user_without_avatar_is_404(
    logged_in_client: TestClient, db: Session
) -> None:
    user_id = db.query(User).filter_by(email="alice@example.com").one().id
    r = logged_in_client.get(f"/avatars/{user_id}")
    assert r.status_code == 404


def test_upload_avatar_normalises_image_jpg_mime(logged_in_client: TestClient, db: Session) -> None:
    r = logged_in_client.post(
        "/settings/avatar",
        files={"file": ("me.jpg", _jpeg_bytes(), "image/jpg")},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert r.headers["location"] == "/settings?saved=avatar"
    user = db.query(User).filter_by(email="alice@example.com").one()
    assert user.avatar.mime_type == "image/jpeg"


def test_upload_avatar_rejects_gif(logged_in_client: TestClient, db: Session) -> None:
    fake_gif = b"GIF89a\x01\x00\x01\x00\x00\x00\x00,"
    r = logged_in_client.post(
        "/settings/avatar",
        files={"file": ("evil.gif", fake_gif, "image/gif")},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert r.headers["location"] == "/settings?error=avatar_bad_type"
    user = db.query(User).filter_by(email="alice@example.com").one()
    assert user.avatar_id is None


def test_upload_avatar_rejects_oversized(logged_in_client: TestClient) -> None:
    # We don't need a *valid* image - the size check runs before the image
    # is even decoded. A 250-KiB buffer of zero bytes is plenty.
    oversized = b"\x00" * (250 * 1024)
    assert len(oversized) > 200 * 1024
    r = logged_in_client.post(
        "/settings/avatar",
        files={"file": ("big.png", oversized, "image/png")},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert r.headers["location"] == "/settings?error=avatar_too_large"


def test_upload_avatar_rejects_corrupt_image(logged_in_client: TestClient) -> None:
    r = logged_in_client.post(
        "/settings/avatar",
        files={"file": ("nope.png", b"not actually a png", "image/png")},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert r.headers["location"] == "/settings?error=avatar_corrupt"


def test_delete_avatar_removes_row(logged_in_client: TestClient, db: Session) -> None:
    logged_in_client.post(
        "/settings/avatar",
        files={"file": ("me.png", _png_bytes(), "image/png")},
    )
    r = logged_in_client.post("/settings/avatar/delete", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/settings?saved=avatar_deleted"
    user = db.query(User).filter_by(email="alice@example.com").one()
    assert user.avatar_id is None


def test_delete_avatar_when_none_is_noop(logged_in_client: TestClient) -> None:
    r = logged_in_client.post("/settings/avatar/delete", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/settings?saved=avatar_deleted"


def test_navbar_shows_uploaded_avatar(logged_in_client: TestClient, db: Session) -> None:
    logged_in_client.post(
        "/settings/avatar",
        files={"file": ("me.png", _png_bytes(), "image/png")},
    )
    user_id = db.query(User).filter_by(email="alice@example.com").one().id
    page = logged_in_client.get("/games")
    assert f'src="/avatars/{user_id}"' in page.text


def test_navbar_shows_placeholder_icon_when_no_avatar(
    logged_in_client: TestClient,
) -> None:
    page = logged_in_client.get("/games")
    assert "bi-person-circle" in page.text
    assert "/avatars/" not in page.text  # no image src yet


def test_upload_avatar_replaces_existing(logged_in_client: TestClient, db: Session) -> None:
    logged_in_client.post(
        "/settings/avatar",
        files={"file": ("a.png", _png_bytes(colour=(255, 0, 0)), "image/png")},
    )
    first_avatar_id = db.query(User).filter_by(email="alice@example.com").one().avatar_id
    logged_in_client.post(
        "/settings/avatar",
        files={"file": ("b.jpg", _jpeg_bytes(), "image/jpeg")},
    )
    user = db.query(User).filter_by(email="alice@example.com").one()
    # Uploading a second avatar updates the existing row instead of
    # inserting a new one, so user.avatar_id is stable across uploads.
    assert user.avatar_id == first_avatar_id
    db.refresh(user.avatar)
    assert user.avatar.mime_type == "image/jpeg"
