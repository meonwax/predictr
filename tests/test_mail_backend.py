"""Tests for the mail backend factory + in-memory implementation."""

from __future__ import annotations

from app.config import Settings
from app.services.mail import (
    InMemoryMailBackend,
    MailMessage,
    SmtpMailBackend,
    build_mail_backend,
)


def _msg(to: str = "user@example.com") -> MailMessage:
    return MailMessage(
        to=to,
        subject="hello",
        body="world",
        sender="noreply@predictr.local",
    )


def test_in_memory_backend_records_messages() -> None:
    backend = InMemoryMailBackend()
    backend.send(_msg("a@example.com"))
    backend.send(_msg("b@example.com"))

    assert len(backend.sent) == 2
    assert backend.sent[0].to == "a@example.com"
    assert backend.sent[1].to == "b@example.com"


def test_in_memory_backend_clear() -> None:
    backend = InMemoryMailBackend()
    backend.send(_msg())
    backend.clear()
    assert backend.sent == []


def test_build_mail_backend_returns_in_memory_when_no_host() -> None:
    backend = build_mail_backend(Settings(mail_host=""))
    assert isinstance(backend, InMemoryMailBackend)


def test_build_mail_backend_returns_smtp_when_host_configured() -> None:
    backend = build_mail_backend(
        Settings(
            mail_host="smtp.example.com",
            mail_port=587,
            mail_username="user",
            mail_password="pass",
            mail_use_tls=True,
        )
    )
    assert isinstance(backend, SmtpMailBackend)
