"""Low-level security primitives used by the auth flows.

Two responsibilities:

1. **Password hashing** via `bcrypt`. Hashed strings include the cost factor
   so future bumps don't break existing hashes.
2. **Signed, expiring tokens** via `itsdangerous`. We use one signer instance
   per *purpose* (session cookie, password-reset link) so a token minted for
   one purpose cannot be replayed against another even if both share the same
   underlying secret.

Both APIs are intentionally tiny and synchronous: they're called from
request handlers a few times per request at most, well below the threshold
where we'd benefit from running them off the event loop.
"""

from __future__ import annotations

import secrets
from typing import Final

import bcrypt
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.config import Settings

# Salt strings used to namespace tokens by purpose. itsdangerous mixes them
# into the HMAC, so a token signed with one salt cannot be verified with
# another. Keep the names stable - changing them invalidates outstanding
# tokens (which is fine: users just have to log in / request a new reset).
SALT_SESSION: Final[str] = "predictr.session.v1"
SALT_PASSWORD_RESET: Final[str] = "predictr.password_reset.v1"

# Cost factor (work) used for new bcrypt hashes. 12 is the de-facto default
# in 2026; tune if hash time becomes noticeable in profiling.
_BCRYPT_ROUNDS: Final[int] = 12


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------


def hash_password(plain: str) -> str:
    """Hash *plain* with bcrypt + a fresh random salt; returns the encoded hash."""
    if not plain:
        raise ValueError("Refusing to hash an empty password.")
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)).decode(
        "ascii"
    )


def verify_password(plain: str, hashed: str) -> bool:
    """Return True iff *plain* matches *hashed*.

    Never raises on bad input; returns False instead. This makes the function
    safe to call against attacker-controlled values (e.g. a corrupted DB row
    or an out-of-band hash format we no longer recognise).
    """
    if not plain or not hashed:
        return False
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("ascii"))
    except (ValueError, TypeError):
        return False


# ---------------------------------------------------------------------------
# Signed, expiring tokens
# ---------------------------------------------------------------------------


def _serializer(secret: str, salt: str) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(secret_key=secret, salt=salt)


def make_session_token(user_id: int, *, settings: Settings) -> str:
    """Mint a signed token carrying *user_id* for the session cookie."""
    return _serializer(settings.session_secret, SALT_SESSION).dumps(user_id)


def read_session_token(token: str, *, settings: Settings) -> int | None:
    """Decode a session token. Returns the user id, or ``None`` if invalid/expired.

    Tokens older than ``settings.session_max_age_days`` are rejected even if
    the signature still matches.
    """
    max_age = settings.session_max_age_days * 24 * 3600
    try:
        value = _serializer(settings.session_secret, SALT_SESSION).loads(token, max_age=max_age)
    except (SignatureExpired, BadSignature):
        return None
    if not isinstance(value, int):
        return None
    return value


def make_password_reset_token(*, settings: Settings) -> str:
    """Generate a fresh opaque token to store in the DB and email to the user.

    We store the *plain* token in the DB (it's already random, single-use, and
    short-lived) so the link in the email is the same string we look up.
    Compared to itsdangerous-signed tokens this lets us trivially invalidate
    a reset on demand (e.g. by deleting the row).
    """
    del settings  # currently unused; kept for symmetry / future hardening
    return secrets.token_urlsafe(32)


__all__ = [
    "SALT_SESSION",
    "SALT_PASSWORD_RESET",
    "hash_password",
    "verify_password",
    "make_session_token",
    "read_session_token",
    "make_password_reset_token",
]
