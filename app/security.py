"""Low-level security primitives used by the auth flows.

Three responsibilities:

1. **Password hashing** via `bcrypt`. Hashed strings include the cost factor
   so future bumps don't break existing hashes.
2. **Signed, expiring session tokens** via `itsdangerous`. The salt namespaces
   the session signer so that, if we ever add a second signed-token kind
   sharing the same secret, a session token can't be replayed there.
3. **Opaque password-reset tokens** generated with `secrets.token_urlsafe`
   and stored verbatim in the ``password_reset_token`` table. Keeping them
   DB-backed (rather than signed) lets us invalidate one by deleting its
   row; the token itself is unforgeable purely because it is high-entropy.

All three APIs are intentionally tiny and synchronous: they're called from
request handlers a few times per request at most, well below the threshold
where we'd benefit from running them off the event loop.
"""

from __future__ import annotations

import secrets
from typing import Final

import bcrypt
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.config import Settings

# itsdangerous mixes this into the HMAC, so a session token cannot be
# replayed against any future signer that shares the same secret. Keep the
# string stable - changing it invalidates outstanding sessions (users just
# have to log in again).
SALT_SESSION: Final[str] = "predictr.session.v1"

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
# Session tokens (signed, expiring)
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


# ---------------------------------------------------------------------------
# Password-reset tokens (opaque, DB-backed)
# ---------------------------------------------------------------------------


def make_password_reset_token() -> str:
    """Generate a fresh opaque token to store in the DB and email to the user.

    The token is high-entropy random; we store the plain value in the
    ``password_reset_token`` table so the link in the email is the same
    string we look up. Revocation is just a ``DELETE`` on the row.
    """
    return secrets.token_urlsafe(32)


__all__ = [
    "SALT_SESSION",
    "hash_password",
    "verify_password",
    "make_session_token",
    "read_session_token",
    "make_password_reset_token",
]
