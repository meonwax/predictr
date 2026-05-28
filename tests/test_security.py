"""Unit tests for the pure crypto primitives in :mod:`app.security`."""

from __future__ import annotations

import time

import pytest

from app.config import Settings
from app.security import (
    hash_password,
    make_password_reset_token,
    make_session_token,
    read_session_token,
    verify_password,
)


@pytest.fixture()
def settings() -> Settings:
    return Settings(
        session_secret="test-secret-do-not-use-in-prod",
        session_max_age_days=7,
        password_reset_ttl_hours=24,
    )


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------


def test_hash_password_round_trip() -> None:
    hashed = hash_password("hunter22")
    assert hashed != "hunter22", "hash must not echo the plaintext"
    assert verify_password("hunter22", hashed) is True


def test_hash_password_rejects_empty() -> None:
    with pytest.raises(ValueError):
        hash_password("")


def test_verify_password_rejects_wrong_password() -> None:
    hashed = hash_password("correct-horse-battery-staple")
    assert verify_password("Tr0ub4dor&3", hashed) is False


def test_verify_password_handles_garbage_input() -> None:
    """Never raise on malformed/empty input - return False instead."""
    assert verify_password("", "anything") is False
    assert verify_password("anything", "") is False
    assert verify_password("anything", "not-a-bcrypt-hash") is False


def test_hash_password_produces_distinct_hashes_for_same_input() -> None:
    """Random salt => two hashes of the same password differ but both verify."""
    h1 = hash_password("same")
    h2 = hash_password("same")
    assert h1 != h2
    assert verify_password("same", h1)
    assert verify_password("same", h2)


# ---------------------------------------------------------------------------
# Session tokens
# ---------------------------------------------------------------------------


def test_session_token_round_trip(settings: Settings) -> None:
    token = make_session_token(42, settings=settings)
    assert read_session_token(token, settings=settings) == 42


def test_session_token_with_tampered_payload_rejected(settings: Settings) -> None:
    token = make_session_token(42, settings=settings)
    tampered = token[:-2] + ("AA" if not token.endswith("AA") else "BB")
    assert read_session_token(tampered, settings=settings) is None


def test_session_token_signed_with_different_secret_rejected() -> None:
    issuer = Settings(session_secret="issuer-secret")
    reader = Settings(session_secret="other-secret")
    token = make_session_token(7, settings=issuer)
    assert read_session_token(token, settings=reader) is None


def test_session_token_expired_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    s = Settings(session_secret="t", session_max_age_days=7)

    token = make_session_token(99, settings=s)
    assert read_session_token(token, settings=s) == 99

    later = time.time() + 8 * 24 * 3600
    monkeypatch.setattr(time, "time", lambda: later)
    assert read_session_token(token, settings=s) is None


def test_session_token_with_garbage_value_returns_none(settings: Settings) -> None:
    assert read_session_token("not.a.valid.token", settings=settings) is None
    assert read_session_token("", settings=settings) is None


# ---------------------------------------------------------------------------
# Password reset tokens
# ---------------------------------------------------------------------------


def test_password_reset_tokens_are_unique(settings: Settings) -> None:
    seen = {make_password_reset_token(settings=settings) for _ in range(50)}
    assert len(seen) == 50, "every reset token must be unique"


def test_password_reset_tokens_are_urlsafe(settings: Settings) -> None:
    token = make_password_reset_token(settings=settings)
    assert token == token.strip()
    assert all(c.isalnum() or c in "-_" for c in token)
    assert len(token) >= 32
