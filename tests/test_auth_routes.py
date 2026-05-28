"""End-to-end tests for the auth routes via :class:`fastapi.testclient.TestClient`.

These tests use the ``auth_client`` fixture from ``conftest.py``, which wires
the FastAPI app to the seeded testcontainer Postgres and to an in-memory
mail backend.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from app.models import PasswordResetToken, User
from app.services.mail import InMemoryMailBackend


def _register(
    client: TestClient,
    *,
    name: str = "Alice",
    email: str = "alice@example.com",
    password: str = "hunter222",
) -> None:
    response = client.post(
        "/register",
        data={"name": name, "email": email, "password": password},
        follow_redirects=False,
    )
    assert response.status_code == 303, response.text


def _login(
    client: TestClient,
    *,
    email: str = "alice@example.com",
    password: str = "hunter222",
    remember_me: bool = False,
) -> None:
    data: dict[str, str] = {"email": email, "password": password}
    if remember_me:
        data["remember_me"] = "true"
    response = client.post("/login", data=data, follow_redirects=False)
    assert response.status_code == 303, response.text


# ---------------------------------------------------------------------------
# GET pages render
# ---------------------------------------------------------------------------


def test_get_login_renders_form(auth_client: TestClient) -> None:
    response = auth_client.get("/login")
    assert response.status_code == 200
    assert "Sign in" in response.text
    assert 'action="/login"' in response.text


def test_get_register_renders_form(auth_client: TestClient) -> None:
    response = auth_client.get("/register")
    assert response.status_code == 200
    assert "Create your account" in response.text
    assert 'action="/register"' in response.text


def test_get_lostpwd_renders_form(auth_client: TestClient) -> None:
    response = auth_client.get("/lostpwd")
    assert response.status_code == 200
    assert "Reset your password" in response.text


def test_navbar_shows_sign_in_when_anonymous(auth_client: TestClient) -> None:
    response = auth_client.get("/games")
    assert "Sign in" in response.text
    assert "Create account" in response.text
    assert "Sign out" not in response.text


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def test_register_creates_user_and_redirects(auth_client: TestClient) -> None:
    response = auth_client.post(
        "/register",
        data={
            "name": "Alice",
            "email": "Alice@Example.com",
            "password": "hunter222",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/login?registered=1"


def test_register_rejects_duplicate_email(auth_client: TestClient) -> None:
    _register(auth_client)
    response = auth_client.post(
        "/register",
        data={
            "name": "Other",
            "email": "ALICE@example.com",
            "password": "different-pw",
        },
    )
    assert response.status_code == 400
    assert "already registered" in response.text


def test_register_rejects_short_password(auth_client: TestClient) -> None:
    response = auth_client.post(
        "/register",
        data={"name": "Alice", "email": "a@example.com", "password": "short"},
    )
    assert response.status_code == 400
    assert "at least 8 characters" in response.text


def test_register_rejects_invalid_email(auth_client: TestClient) -> None:
    response = auth_client.post(
        "/register",
        data={"name": "Alice", "email": "not-an-email", "password": "hunter222"},
    )
    assert response.status_code == 400
    assert "valid email" in response.text.lower()


def test_register_rejects_short_name(auth_client: TestClient) -> None:
    response = auth_client.post(
        "/register",
        data={"name": "A", "email": "a@example.com", "password": "hunter222"},
    )
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# Login / Logout
# ---------------------------------------------------------------------------


def test_login_with_bad_credentials_returns_401(auth_client: TestClient) -> None:
    response = auth_client.post(
        "/login",
        data={"email": "nobody@example.com", "password": "anything"},
    )
    assert response.status_code == 401
    assert "Invalid email or password" in response.text


def test_login_with_good_credentials_sets_session_cookie(
    auth_client: TestClient,
) -> None:
    _register(auth_client)
    response = auth_client.post(
        "/login",
        data={"email": "alice@example.com", "password": "hunter222"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/"
    assert "predictr_session" in response.cookies


def test_login_redirects_to_next_param(auth_client: TestClient) -> None:
    _register(auth_client)
    response = auth_client.post(
        "/login",
        data={
            "email": "alice@example.com",
            "password": "hunter222",
            "next": "/games",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/games"


def test_remember_me_sets_max_age_on_cookie(auth_client: TestClient) -> None:
    _register(auth_client)
    response = auth_client.post(
        "/login",
        data={
            "email": "alice@example.com",
            "password": "hunter222",
            "remember_me": "true",
        },
        follow_redirects=False,
    )
    set_cookie = response.headers["set-cookie"]
    assert "Max-Age=" in set_cookie
    assert "HttpOnly" in set_cookie
    assert "SameSite=lax" in set_cookie.lower() or "samesite=lax" in set_cookie.lower()


def test_login_without_remember_me_is_session_cookie(auth_client: TestClient) -> None:
    _register(auth_client)
    response = auth_client.post(
        "/login",
        data={"email": "alice@example.com", "password": "hunter222"},
        follow_redirects=False,
    )
    set_cookie = response.headers["set-cookie"]
    assert "Max-Age=" not in set_cookie


def test_navbar_shows_user_name_when_signed_in(auth_client: TestClient) -> None:
    _register(auth_client, name="Alice")
    _login(auth_client)
    response = auth_client.get("/games")
    assert response.status_code == 200
    assert "Alice" in response.text
    assert "Sign out" in response.text
    assert "Create account" not in response.text


def test_get_login_when_already_signed_in_redirects(auth_client: TestClient) -> None:
    _register(auth_client)
    _login(auth_client)
    response = auth_client.get("/login", follow_redirects=False)
    assert response.status_code == 303


def test_logout_clears_cookie(auth_client: TestClient) -> None:
    _register(auth_client)
    _login(auth_client)
    response = auth_client.post("/logout", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"
    # After logout, the navbar shows "Sign in" again.
    page = auth_client.get("/games")
    assert "Sign in" in page.text


def test_session_cookie_with_tampered_payload_is_ignored(
    auth_client: TestClient,
) -> None:
    _register(auth_client)
    _login(auth_client)
    auth_client.cookies.set("predictr_session", "garbage.token.value")
    page = auth_client.get("/games")
    assert "Sign out" not in page.text
    assert "Sign in" in page.text


# ---------------------------------------------------------------------------
# Lost-password flow
# ---------------------------------------------------------------------------


def test_lostpwd_for_known_email_sends_link(
    auth_client: TestClient, mail_inbox: InMemoryMailBackend
) -> None:
    _register(auth_client, email="alice@example.com")
    response = auth_client.post(
        "/lostpwd", data={"email": "alice@example.com"}, follow_redirects=False
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/lostpwd?sent=1"
    assert len(mail_inbox.sent) == 1
    msg = mail_inbox.sent[0]
    assert msg.to == "alice@example.com"
    assert "/password/reset/" in msg.body


def test_lostpwd_for_unknown_email_still_returns_303(
    auth_client: TestClient, mail_inbox: InMemoryMailBackend
) -> None:
    """We must not leak which addresses are registered."""
    response = auth_client.post(
        "/lostpwd", data={"email": "ghost@example.com"}, follow_redirects=False
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/lostpwd?sent=1"
    assert mail_inbox.sent == []


def test_lostpwd_rejects_invalid_email(auth_client: TestClient) -> None:
    response = auth_client.post("/lostpwd", data={"email": "not-an-email"}, follow_redirects=False)
    assert response.status_code == 400
    assert "valid email" in response.text.lower()


# ---------------------------------------------------------------------------
# Reset-password (tokenised link)
# ---------------------------------------------------------------------------


def _extract_token(mail_inbox: InMemoryMailBackend) -> str:
    body = mail_inbox.sent[-1].body
    prefix = "/password/reset/"
    start = body.find(prefix) + len(prefix)
    end = start
    while end < len(body) and body[end] not in " \n\r\t":
        end += 1
    return body[start:end]


def test_full_lost_password_flow(
    auth_client: TestClient,
    mail_inbox: InMemoryMailBackend,
) -> None:
    _register(auth_client, email="alice@example.com", password="old-password-1")
    auth_client.post("/lostpwd", data={"email": "alice@example.com"})
    token = _extract_token(mail_inbox)

    form = auth_client.get(f"/password/reset/{token}")
    assert form.status_code == 200
    assert "Choose a new password" in form.text

    submit = auth_client.post(
        f"/password/reset/{token}",
        data={"password": "new-password-2", "password_confirm": "new-password-2"},
        follow_redirects=False,
    )
    assert submit.status_code == 303
    assert "reset=1" in submit.headers["location"]

    _login(auth_client, email="alice@example.com", password="new-password-2")
    bad = auth_client.post(
        "/login",
        data={"email": "alice@example.com", "password": "old-password-1"},
    )
    assert bad.status_code == 401


def test_reset_form_with_unknown_token_renders_400(auth_client: TestClient) -> None:
    response = auth_client.get("/password/reset/totally-bogus")
    assert response.status_code == 400
    assert "no longer valid" in response.text


def test_reset_submit_with_mismatched_passwords(
    auth_client: TestClient, mail_inbox: InMemoryMailBackend
) -> None:
    _register(auth_client, email="a@example.com")
    auth_client.post("/lostpwd", data={"email": "a@example.com"})
    token = _extract_token(mail_inbox)

    response = auth_client.post(
        f"/password/reset/{token}",
        data={"password": "new-password-2", "password_confirm": "different"},
    )
    assert response.status_code == 400
    # Apostrophes are HTML-escaped by Jinja autoescape, so we match the
    # surrounding phrase rather than the literal string.
    assert "two passwords" in response.text and "match" in response.text


def test_reset_submit_rejects_short_password(
    auth_client: TestClient, mail_inbox: InMemoryMailBackend
) -> None:
    _register(auth_client, email="a@example.com")
    auth_client.post("/lostpwd", data={"email": "a@example.com"})
    token = _extract_token(mail_inbox)
    response = auth_client.post(
        f"/password/reset/{token}",
        data={"password": "shorty", "password_confirm": "shorty"},
    )
    assert response.status_code == 400


def test_reset_token_is_single_use(
    auth_client: TestClient, mail_inbox: InMemoryMailBackend
) -> None:
    _register(auth_client, email="a@example.com")
    auth_client.post("/lostpwd", data={"email": "a@example.com"})
    token = _extract_token(mail_inbox)
    auth_client.post(
        f"/password/reset/{token}",
        data={"password": "new-pw-1234", "password_confirm": "new-pw-1234"},
    )
    # Second use should be rejected.
    second = auth_client.get(f"/password/reset/{token}")
    assert second.status_code == 400


def test_reset_submit_with_expired_token_returns_400(
    auth_client: TestClient,
    mail_inbox: InMemoryMailBackend,
    seeded_engine,
) -> None:
    _register(auth_client, email="a@example.com")
    auth_client.post("/lostpwd", data={"email": "a@example.com"})
    token = _extract_token(mail_inbox)

    # Backdate the token directly in the DB.
    Session_ = sessionmaker(bind=seeded_engine, expire_on_commit=False, future=True)
    with Session_() as s:
        row = s.query(PasswordResetToken).filter_by(val=token).one()
        row.expiry = datetime.now(UTC) - timedelta(hours=1)
        s.commit()

    response = auth_client.post(
        f"/password/reset/{token}",
        data={"password": "new-password-2", "password_confirm": "new-password-2"},
    )
    assert response.status_code == 400
    # The handler must render the localised reset_password template, not
    # leak the English ``str(InvalidResetToken)`` via a bare HTTPException.
    assert "has expired" in response.text
    assert "Reset token is" not in response.text


def test_reset_submit_with_unknown_token_renders_400(auth_client: TestClient) -> None:
    """A bogus token in the POST must render the same localised page as the GET."""
    response = auth_client.post(
        "/password/reset/totally-bogus",
        data={"password": "new-password-2", "password_confirm": "new-password-2"},
    )
    assert response.status_code == 400
    assert "no longer valid" in response.text
    assert "Reset token is" not in response.text


def test_role_admin_required_default_user_is_role_user(
    auth_client: TestClient, seeded_engine
) -> None:
    """A freshly-registered user has ROLE_USER, never ROLE_ADMIN."""
    _register(auth_client, email="a@example.com")
    Session_ = sessionmaker(bind=seeded_engine, expire_on_commit=False, future=True)
    with Session_() as s:
        user = s.query(User).filter_by(email="a@example.com").one()
        assert user.role == User.ROLE_USER


def test_user_normalised_email_stored_lowercase(auth_client: TestClient, seeded_engine) -> None:
    auth_client.post(
        "/register",
        data={
            "name": "Bob",
            "email": "Bob.Capital@Example.COM",
            "password": "hunter222",
        },
    )
    with seeded_engine.begin() as conn:
        rows = list(
            conn.execute(
                text("SELECT email FROM users WHERE email = :e"),
                {"e": "bob.capital@example.com"},
            )
        )
    assert len(rows) == 1
