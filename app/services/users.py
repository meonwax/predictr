"""User-related business logic.

Lives between the route layer (which only knows about HTTP) and the model
layer (which only knows about persistence). Routes call these functions;
they raise domain exceptions that the route maps to a response.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.config import Settings
from app.i18n import EN, SUPPORTED_LANGUAGES, gettext, resolve_language
from app.models import PasswordResetToken, User
from app.security import (
    hash_password,
    make_password_reset_token,
    verify_password,
)
from app.services.mail import MailBackend, MailMessage
from app.timezones import is_supported as _is_supported_tz

LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Domain exceptions
# ---------------------------------------------------------------------------


class EmailAlreadyRegistered(Exception):
    """Raised by :func:`register_user` when the email is already in the DB."""


class InvalidResetToken(Exception):
    """Raised by reset-confirm when the token cannot be honoured.

    The :attr:`reason` attribute distinguishes the two cases the route
    layer cares about: ``"unknown"`` (the token does not exist - either
    bogus or already consumed) and ``"expired"`` (the row exists but its
    ``expiry`` has passed). Both still translate to a 400 for HTTP
    callers, but the user-facing error page picks a different message
    per reason without ever surfacing the English ``str(exc)`` text into
    a translated UI.
    """

    reason: str

    def __init__(self, reason: str) -> None:
        if reason not in ("unknown", "expired"):
            raise ValueError(f"Unknown InvalidResetToken reason: {reason!r}")
        self.reason = reason
        super().__init__(f"Reset token is {reason}.")


class WrongCurrentPassword(Exception):
    """Raised by :func:`change_password` when the supplied old password doesn't verify."""


# ---------------------------------------------------------------------------
# Lookups
# ---------------------------------------------------------------------------


def _normalise_email(email: str) -> str:
    return email.strip().lower()


def find_user_by_email(db: Session, email: str) -> User | None:
    """Case-insensitive email lookup, mirroring ``findOneByEmailIgnoringCase``."""
    stmt = select(User).where(func.lower(User.email) == _normalise_email(email))
    return db.execute(stmt).scalar_one_or_none()


def authenticate(db: Session, email: str, password: str) -> User | None:
    """Return the user iff *(email, password)* matches an existing row."""
    user = find_user_by_email(db, email)
    if user is None:
        return None
    if not verify_password(password, user.password):
        return None
    return user


def touch_last_login(db: Session, user: User) -> None:
    """Stamp ``last_login_date`` to now() and commit."""
    user.last_login_date = datetime.now(UTC)
    db.commit()


# ---------------------------------------------------------------------------
# Profile updates (settings page)
# ---------------------------------------------------------------------------


def update_profile(
    db: Session,
    user: User,
    *,
    name: str,
    preferred_language: str,
    preferred_timezone: str | None = None,
) -> User:
    """Apply a name + preferred-language [+ timezone] change.

    ``preferred_timezone`` is optional for backwards compatibility - the
    /settings form has always sent name and language, and adding the
    timezone field gradually keeps any existing callers from breaking.
    Pass ``None`` to leave the field untouched; pass the empty string to
    clear it back to "inherit the site default".

    Raises ``ValueError`` on bad input.
    """
    name = name.strip()
    if len(name) < 2:
        raise ValueError("Display name must be at least 2 characters long.")
    if preferred_language not in SUPPORTED_LANGUAGES:
        raise ValueError(
            f"Unsupported language {preferred_language!r}. Choose one of {SUPPORTED_LANGUAGES}."
        )

    user.name = name
    user.preferred_language = preferred_language
    if preferred_timezone is not None:
        tz = preferred_timezone.strip()
        if tz == "":
            user.preferred_timezone = None
        else:
            if not _is_supported_tz(tz):
                raise ValueError(
                    f"Unsupported timezone {tz!r}. "
                    "Choose one of the entries in app.timezones.SUPPORTED_TIMEZONES."
                )
            user.preferred_timezone = tz
    user.last_modified_date = datetime.now(UTC)
    db.commit()
    return user


def change_password(
    db: Session,
    user: User,
    *,
    old_password: str,
    new_password: str,
) -> User:
    """Verify *old_password* and replace the stored hash with *new_password*.

    Raises :class:`WrongCurrentPassword` if the supplied current password
    doesn't match. The caller (route layer) handles new-password length
    validation before calling - we don't repeat that here because the
    business rule (minimum length) is shared with registration and reset.
    """
    if not verify_password(old_password, user.password):
        raise WrongCurrentPassword
    user.password = hash_password(new_password)
    user.last_modified_date = datetime.now(UTC)
    db.commit()
    LOGGER.info("Password changed via settings for user id=%d", user.id)
    return user


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class RegistrationData:
    """Inputs to :func:`register_user`.

    *preferred_language* defaults to ``None`` because the site-wide default
    (from :class:`app.config.Settings.default_language`) should be applied
    here at the service layer rather than baked into a class attribute. A
    ``None`` value is stored as-is, so the user's preference effectively
    *tracks* the site default until they explicitly change it.
    """

    name: str
    email: str
    password: str
    preferred_language: str | None = None


def register_user(db: Session, data: RegistrationData) -> User:
    """Create a new user row. Raises :class:`EmailAlreadyRegistered` on conflict.

    Note: deliberately commits inside this function so the caller doesn't
    have to remember to. Other domain mutations on the user row follow the
    same pattern.
    """
    if find_user_by_email(db, data.email) is not None:
        raise EmailAlreadyRegistered(data.email)

    now = datetime.now(UTC)
    user = User(
        created_date=now,
        last_modified_date=now,
        email=_normalise_email(data.email),
        password=hash_password(data.password),
        name=data.name.strip(),
        role=User.ROLE_USER,
        preferred_language=data.preferred_language,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    LOGGER.info("Registered new user: %s (id=%d)", user.email, user.id)
    return user


# ---------------------------------------------------------------------------
# Password reset flow
# ---------------------------------------------------------------------------


def _build_reset_url(settings: Settings, token: str) -> str:
    base = settings.base_url.rstrip("/")
    return f"{base}/password/reset/{token}"


def request_password_reset(
    db: Session,
    *,
    email: str,
    settings: Settings,
    mailer: MailBackend,
) -> bool:
    """Create a password-reset token for *email* and email the link.

    Returns ``True`` if a token was actually issued (i.e. the email matched a
    user). Callers should *not* surface this to the client - the public route
    must answer identically regardless to avoid leaking which addresses are
    registered.
    """
    user = find_user_by_email(db, email)
    if user is None:
        LOGGER.info("Password reset requested for unknown email %r - ignored.", email)
        return False

    db.execute(delete(PasswordResetToken).where(PasswordResetToken.user_id == user.id))

    token_value = make_password_reset_token(settings=settings)
    expiry = datetime.now(UTC) + timedelta(hours=settings.password_reset_ttl_hours)
    db.add(
        PasswordResetToken(
            val=token_value,
            expiry=expiry,
            user_id=user.id,
        )
    )
    db.commit()

    reset_url = _build_reset_url(settings, token_value)
    language = resolve_language(user.preferred_language, default=settings.default_language)
    brand = EN["brand.name"]
    placeholders: dict[str, object] = {
        "name": user.name,
        "url": reset_url,
        "ttl_hours": settings.password_reset_ttl_hours,
        "brand": brand,
    }
    mailer.send(
        MailMessage(
            to=user.email,
            sender=settings.mail_sender,
            subject=gettext("mail.reset.subject", language, **placeholders),
            body=gettext("mail.reset.body", language, **placeholders),
        )
    )
    return True


def _load_valid_reset_token(db: Session, token_value: str) -> PasswordResetToken:
    """Return the (non-expired) reset row, or raise :class:`InvalidResetToken`."""
    stmt = select(PasswordResetToken).where(PasswordResetToken.val == token_value)
    token = db.execute(stmt).scalar_one_or_none()
    if token is None:
        raise InvalidResetToken("unknown")
    if token.expiry < datetime.now(UTC):
        db.delete(token)
        db.commit()
        raise InvalidResetToken("expired")
    return token


def check_reset_token(db: Session, token_value: str) -> User:
    """Return the user the token belongs to, without consuming it."""
    return _load_valid_reset_token(db, token_value).user


def confirm_password_reset(
    db: Session,
    *,
    token_value: str,
    new_password: str,
) -> User:
    """Validate the token, set the user's password, delete the token. Atomic."""
    token = _load_valid_reset_token(db, token_value)
    user = token.user
    user.password = hash_password(new_password)
    user.last_modified_date = datetime.now(UTC)
    db.delete(token)
    db.commit()
    LOGGER.info("Password reset for user %s (id=%d)", user.email, user.id)
    return user


__all__ = [
    "RegistrationData",
    "EmailAlreadyRegistered",
    "InvalidResetToken",
    "WrongCurrentPassword",
    "SUPPORTED_LANGUAGES",
    "find_user_by_email",
    "authenticate",
    "touch_last_login",
    "register_user",
    "update_profile",
    "change_password",
    "request_password_reset",
    "check_reset_token",
    "confirm_password_reset",
]
