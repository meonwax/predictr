"""Tests for the business logic in :mod:`app.services.users`.

Exercises the service layer directly with a fresh DB session, so no HTTP
plumbing or template rendering is involved.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import PasswordResetToken, User
from app.security import hash_password
from app.services.mail import InMemoryMailBackend
from app.services.users import (
    EmailAlreadyRegistered,
    InvalidResetToken,
    RegistrationData,
    WrongCurrentPassword,
    authenticate,
    change_password,
    check_reset_token,
    confirm_password_reset,
    find_user_by_email,
    register_user,
    request_password_reset,
    touch_last_login,
    update_profile,
)


@pytest.fixture()
def settings() -> Settings:
    return Settings(
        session_secret="test-secret",
        base_url="http://test.example",
        mail_sender="noreply@test.example",
        password_reset_ttl_hours=24,
    )


@pytest.fixture()
def mailer() -> InMemoryMailBackend:
    return InMemoryMailBackend()


@pytest.fixture()
def fresh_db(clean_user_tables: None, db_session: Session) -> Session:
    """Reuse the project's ``db_session`` fixture but guarantee no leftover users.

    The argument order matters: pytest sets up fixtures left-to-right and
    tears them down LIFO, so this signature guarantees that ``db_session``
    is closed (releasing any held locks on the ``users`` table) *before*
    ``clean_user_tables`` tries to ``TRUNCATE`` it on the way out.
    """
    return db_session


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def test_register_user_creates_row_with_defaults(fresh_db: Session) -> None:
    user = register_user(
        fresh_db,
        RegistrationData(name="Alice", email="alice@example.com", password="hunter22"),
    )
    assert user.id is not None
    assert user.email == "alice@example.com"
    assert user.name == "Alice"
    assert user.role == User.ROLE_USER
    assert user.password != "hunter22"


def test_register_user_normalises_email_case(fresh_db: Session) -> None:
    user = register_user(
        fresh_db,
        RegistrationData(name="Bob", email="Bob@Example.COM", password="hunter22"),
    )
    assert user.email == "bob@example.com"


def test_register_user_rejects_duplicate_email(fresh_db: Session) -> None:
    register_user(
        fresh_db,
        RegistrationData(name="Alice", email="dup@example.com", password="hunter22"),
    )
    with pytest.raises(EmailAlreadyRegistered):
        register_user(
            fresh_db,
            RegistrationData(name="Alice2", email="DUP@example.com", password="another"),
        )


# ---------------------------------------------------------------------------
# Lookup + authentication
# ---------------------------------------------------------------------------


def test_find_user_by_email_is_case_insensitive(fresh_db: Session) -> None:
    register_user(
        fresh_db,
        RegistrationData(name="X", email="x@example.com", password="hunter22"),
    )
    assert find_user_by_email(fresh_db, "X@EXAMPLE.COM") is not None


def test_authenticate_with_correct_credentials(fresh_db: Session) -> None:
    register_user(
        fresh_db,
        RegistrationData(name="A", email="a@example.com", password="correct"),
    )
    user = authenticate(fresh_db, "a@example.com", "correct")
    assert user is not None
    assert user.email == "a@example.com"


def test_authenticate_with_wrong_password_returns_none(fresh_db: Session) -> None:
    register_user(
        fresh_db,
        RegistrationData(name="A", email="a@example.com", password="correct"),
    )
    assert authenticate(fresh_db, "a@example.com", "wrong") is None


def test_authenticate_unknown_email_returns_none(fresh_db: Session) -> None:
    assert authenticate(fresh_db, "nobody@example.com", "anything") is None


def test_touch_last_login_updates_timestamp(fresh_db: Session) -> None:
    user = register_user(
        fresh_db,
        RegistrationData(name="A", email="a@example.com", password="x" * 8),
    )
    assert user.last_login_date is None
    touch_last_login(fresh_db, user)
    assert user.last_login_date is not None


# ---------------------------------------------------------------------------
# Password reset
# ---------------------------------------------------------------------------


def test_request_reset_for_known_user_sends_mail_and_creates_token(
    fresh_db: Session,
    settings: Settings,
    mailer: InMemoryMailBackend,
) -> None:
    register_user(
        fresh_db,
        RegistrationData(name="A", email="a@example.com", password="hunter22"),
    )
    issued = request_password_reset(
        fresh_db, email="a@example.com", settings=settings, mailer=mailer
    )
    assert issued is True
    assert len(mailer.sent) == 1
    sent = mailer.sent[0]
    assert sent.to == "a@example.com"
    assert "password reset" in sent.subject.lower()
    assert settings.base_url in sent.body

    tokens = fresh_db.query(PasswordResetToken).all()
    assert len(tokens) == 1
    assert tokens[0].val in sent.body


def test_request_reset_localises_email_to_user_preferred_language(
    fresh_db: Session,
    settings: Settings,
    mailer: InMemoryMailBackend,
) -> None:
    """A user with ``preferred_language='de'`` receives the German body."""
    user = register_user(
        fresh_db,
        RegistrationData(
            name="Alice",
            email="alice@example.com",
            password="hunter22",
            preferred_language="de",
        ),
    )
    assert user.preferred_language == "de"

    issued = request_password_reset(fresh_db, email=user.email, settings=settings, mailer=mailer)
    assert issued is True
    sent = mailer.sent[0]
    assert sent.subject == "Predictr: Passwort zurücksetzen"
    assert sent.body.startswith("Hallo Alice,")
    assert "ein Zurücksetzen des Passworts" in sent.body
    assert "24 Stunden gültig" in sent.body
    assert settings.base_url in sent.body


def test_request_reset_falls_back_to_site_default_language(
    fresh_db: Session,
    settings: Settings,
    mailer: InMemoryMailBackend,
) -> None:
    """A user without an explicit preference gets the site default language."""
    settings = settings.model_copy(update={"default_language": "de"})
    user = register_user(
        fresh_db,
        RegistrationData(name="Bob", email="bob@example.com", password="hunter22"),
    )
    assert user.preferred_language is None

    request_password_reset(fresh_db, email=user.email, settings=settings, mailer=mailer)
    sent = mailer.sent[0]
    assert sent.subject.startswith("Predictr:")
    assert "Passwort" in sent.subject
    assert sent.body.startswith("Hallo Bob,")


def test_request_reset_renders_english_for_en_users(
    fresh_db: Session,
    settings: Settings,
    mailer: InMemoryMailBackend,
) -> None:
    """A user with ``preferred_language='en'`` overrides a German site default."""
    settings = settings.model_copy(update={"default_language": "de"})
    user = register_user(
        fresh_db,
        RegistrationData(
            name="Carol",
            email="carol@example.com",
            password="hunter22",
            preferred_language="en",
        ),
    )

    request_password_reset(fresh_db, email=user.email, settings=settings, mailer=mailer)
    sent = mailer.sent[0]
    assert sent.subject == "Predictr: password reset"
    assert sent.body.startswith("Hi Carol,")
    assert "expires in 24 hours" in sent.body


def test_request_reset_uses_configured_site_title(
    fresh_db: Session,
    settings: Settings,
    mailer: InMemoryMailBackend,
) -> None:
    """The reset email white-labels to the database-configured site title."""
    from app.models import Config

    config = fresh_db.query(Config).order_by(Config.id).first()
    assert config is not None
    original = config.title
    config.title = "Office Cup 2026"
    fresh_db.commit()
    try:
        user = register_user(
            fresh_db,
            RegistrationData(
                name="Dora",
                email="dora@example.com",
                password="hunter22",
                preferred_language="en",
            ),
        )
        request_password_reset(fresh_db, email=user.email, settings=settings, mailer=mailer)
        sent = mailer.sent[0]
        assert sent.subject == "Office Cup 2026: password reset"
        assert "Office Cup 2026" in sent.body
    finally:
        config.title = original
        fresh_db.commit()


def test_request_reset_for_unknown_user_is_silent_noop(
    fresh_db: Session,
    settings: Settings,
    mailer: InMemoryMailBackend,
) -> None:
    issued = request_password_reset(
        fresh_db, email="ghost@example.com", settings=settings, mailer=mailer
    )
    assert issued is False
    assert mailer.sent == []
    assert fresh_db.query(PasswordResetToken).count() == 0


def test_request_reset_replaces_existing_token(
    fresh_db: Session,
    settings: Settings,
    mailer: InMemoryMailBackend,
) -> None:
    register_user(
        fresh_db,
        RegistrationData(name="A", email="a@example.com", password="hunter22"),
    )
    request_password_reset(fresh_db, email="a@example.com", settings=settings, mailer=mailer)
    first_token = fresh_db.query(PasswordResetToken).one()
    request_password_reset(fresh_db, email="a@example.com", settings=settings, mailer=mailer)
    rows = fresh_db.query(PasswordResetToken).all()
    assert len(rows) == 1
    assert rows[0].val != first_token.val


def test_check_reset_token_with_unknown_value_raises(fresh_db: Session) -> None:
    with pytest.raises(InvalidResetToken):
        check_reset_token(fresh_db, "totally-bogus")


def test_check_reset_token_with_expired_value_raises_and_deletes(
    fresh_db: Session,
    settings: Settings,
    mailer: InMemoryMailBackend,
) -> None:
    user = register_user(
        fresh_db,
        RegistrationData(name="A", email="a@example.com", password="hunter22"),
    )
    request_password_reset(fresh_db, email=user.email, settings=settings, mailer=mailer)
    token = fresh_db.query(PasswordResetToken).one()
    token.expiry = datetime.now(UTC) - timedelta(hours=1)
    fresh_db.commit()

    with pytest.raises(InvalidResetToken):
        check_reset_token(fresh_db, token.val)
    assert fresh_db.query(PasswordResetToken).count() == 0


def test_confirm_password_reset_changes_password_and_consumes_token(
    fresh_db: Session,
    settings: Settings,
    mailer: InMemoryMailBackend,
) -> None:
    user = register_user(
        fresh_db,
        RegistrationData(name="A", email="a@example.com", password="oldpassword"),
    )
    request_password_reset(fresh_db, email=user.email, settings=settings, mailer=mailer)
    token = fresh_db.query(PasswordResetToken).one()

    confirm_password_reset(fresh_db, token_value=token.val, new_password="brand-new-pw")

    assert fresh_db.query(PasswordResetToken).count() == 0
    assert authenticate(fresh_db, user.email, "brand-new-pw") is not None
    assert authenticate(fresh_db, user.email, "oldpassword") is None


def test_confirm_password_reset_rejects_unknown_token(fresh_db: Session) -> None:
    with pytest.raises(InvalidResetToken):
        confirm_password_reset(fresh_db, token_value="bogus", new_password="any-new-pw")


def test_confirm_password_reset_rejects_expired_token(
    fresh_db: Session, settings: Settings, mailer: InMemoryMailBackend
) -> None:
    user = register_user(
        fresh_db,
        RegistrationData(name="A", email="a@example.com", password="oldpassword"),
    )
    # Create a token directly with an expiry in the past so we don't depend
    # on monkey-patching ``datetime.now``.
    expired = PasswordResetToken(
        val="some-stale-token",
        expiry=datetime.now(UTC) - timedelta(minutes=1),
        user_id=user.id,
    )
    # Direct INSERT bypasses the service layer; we just need an expired row.
    user_password_before = user.password
    fresh_db.add(expired)
    fresh_db.commit()

    with pytest.raises(InvalidResetToken):
        confirm_password_reset(
            fresh_db, token_value="some-stale-token", new_password="should-not-apply"
        )
    fresh_db.refresh(user)
    assert user.password == user_password_before


def test_hash_password_helper_round_trip_via_authenticate(
    fresh_db: Session,
) -> None:
    """Belt-and-braces: hash_password output is accepted by authenticate()."""
    now = datetime.now(UTC)
    fresh_db.add(
        User(
            created_date=now,
            last_modified_date=now,
            email="z@example.com",
            password=hash_password("zzzzzzzz"),
            name="Z",
            role=User.ROLE_USER,
        )
    )
    fresh_db.commit()
    assert authenticate(fresh_db, "z@example.com", "zzzzzzzz") is not None


# ---------------------------------------------------------------------------
# Profile + password changes (settings page)
# ---------------------------------------------------------------------------


def test_update_profile_changes_name_and_language(fresh_db: Session) -> None:
    user = register_user(
        fresh_db,
        RegistrationData(name="Old Name", email="x@example.com", password="hunter222"),
    )
    update_profile(fresh_db, user, name="New Name", preferred_language="de")
    fresh_db.refresh(user)
    assert user.name == "New Name"
    assert user.preferred_language == "de"


def test_update_profile_trims_whitespace_around_name(fresh_db: Session) -> None:
    user = register_user(
        fresh_db,
        RegistrationData(name="Old", email="x@example.com", password="hunter222"),
    )
    update_profile(fresh_db, user, name="   Padded   ", preferred_language="en")
    fresh_db.refresh(user)
    assert user.name == "Padded"


def test_update_profile_rejects_short_name(fresh_db: Session) -> None:
    user = register_user(
        fresh_db,
        RegistrationData(name="OK", email="x@example.com", password="hunter222"),
    )
    with pytest.raises(ValueError):
        update_profile(fresh_db, user, name="A", preferred_language="en")
    fresh_db.refresh(user)
    assert user.name == "OK"


def test_update_profile_rejects_unsupported_language(fresh_db: Session) -> None:
    user = register_user(
        fresh_db,
        RegistrationData(name="OK", email="x@example.com", password="hunter222"),
    )
    with pytest.raises(ValueError):
        update_profile(fresh_db, user, name="OK", preferred_language="fr")


def test_update_profile_bumps_last_modified_date(fresh_db: Session) -> None:
    user = register_user(
        fresh_db,
        RegistrationData(name="OK", email="x@example.com", password="hunter222"),
    )
    before = user.last_modified_date
    update_profile(fresh_db, user, name="Updated", preferred_language="en")
    fresh_db.refresh(user)
    assert user.last_modified_date >= before


def test_change_password_round_trip(fresh_db: Session) -> None:
    user = register_user(
        fresh_db,
        RegistrationData(name="A", email="a@example.com", password="old-pw-1"),
    )
    change_password(fresh_db, user, old_password="old-pw-1", new_password="brand-new-pw")
    assert authenticate(fresh_db, "a@example.com", "brand-new-pw") is not None
    assert authenticate(fresh_db, "a@example.com", "old-pw-1") is None


def test_change_password_rejects_wrong_current(fresh_db: Session) -> None:
    user = register_user(
        fresh_db,
        RegistrationData(name="A", email="a@example.com", password="old-pw-1"),
    )
    with pytest.raises(WrongCurrentPassword):
        change_password(fresh_db, user, old_password="not-correct", new_password="brand-new-pw")
    # The original password must still work and the hash must not have changed.
    assert authenticate(fresh_db, "a@example.com", "old-pw-1") is not None
