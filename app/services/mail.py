"""Outbound email backends.

Two implementations are provided:

* :class:`SmtpMailBackend` - talks to a real SMTP server via the stdlib
  :mod:`smtplib`. Works for MailHog in dev (plain SMTP on port 1025, no auth,
  no TLS) and for production relays (TLS + auth).
* :class:`InMemoryMailBackend` - records the messages it was asked to send in
  a list, and logs them at INFO level. Used both as the implicit fallback
  when ``MAIL_HOST`` is empty (so devs without a relay can still register
  users) and as the test backend.

The factory :func:`get_mail_backend` picks one based on the current settings.
For tests, override the FastAPI dependency
:func:`app.dependencies.get_mail_backend_dep` directly.
"""

from __future__ import annotations

import logging
import smtplib
from dataclasses import dataclass, field
from email.message import EmailMessage
from functools import lru_cache
from typing import Protocol, runtime_checkable

from app.config import Settings, get_settings

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class MailMessage:
    to: str
    subject: str
    body: str
    sender: str


@runtime_checkable
class MailBackend(Protocol):
    """A minimal mail-sending interface.

    Implementations should never raise on transient/configuration errors -
    log them and return. Outbound email is rarely critical-path enough to
    warrant aborting a user-facing request.
    """

    def send(self, message: MailMessage) -> None: ...


class SmtpMailBackend:
    """SMTP backend that opens a fresh connection per message.

    We don't pool connections because the volume is tiny (registration,
    password resets - a handful per day at most). If it ever matters,
    swap in a long-lived ``smtplib.SMTP`` instance behind a lock.
    """

    def __init__(
        self,
        *,
        host: str,
        port: int,
        username: str = "",
        password: str = "",
        use_tls: bool = False,
    ) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._use_tls = use_tls

    def send(self, message: MailMessage) -> None:
        email = EmailMessage()
        email["From"] = message.sender
        email["To"] = message.to
        email["Subject"] = message.subject
        email.set_content(message.body)

        try:
            with smtplib.SMTP(self._host, self._port, timeout=10) as client:
                if self._use_tls:
                    client.starttls()
                if self._username:
                    client.login(self._username, self._password)
                client.send_message(email)
        except (OSError, smtplib.SMTPException) as exc:
            LOGGER.error(
                "Failed to send mail to %s (%s): %s",
                message.to,
                message.subject,
                exc,
            )
            return
        LOGGER.info("Mail %r sent to %s", message.subject, message.to)


@dataclass(slots=True)
class InMemoryMailBackend:
    """Records sent messages instead of dispatching them.

    Used both as the implicit fallback when no SMTP host is configured and
    as the test backend (override the FastAPI dependency and assert against
    ``backend.sent``).
    """

    sent: list[MailMessage] = field(default_factory=list)

    def send(self, message: MailMessage) -> None:
        self.sent.append(message)
        LOGGER.info(
            "[in-memory mail] to=%s subject=%r (%d chars body)",
            message.to,
            message.subject,
            len(message.body),
        )

    def clear(self) -> None:
        self.sent.clear()


def build_mail_backend(settings: Settings) -> MailBackend:
    """Pick an implementation based on *settings*.

    No SMTP host configured => in-memory backend (dev + tests).
    """
    if not settings.mail_host:
        LOGGER.info(
            "MAIL_HOST is empty - using in-memory mail backend (messages will not be delivered)."
        )
        return InMemoryMailBackend()
    return SmtpMailBackend(
        host=settings.mail_host,
        port=settings.mail_port,
        username=settings.mail_username,
        password=settings.mail_password,
        use_tls=settings.mail_use_tls,
    )


@lru_cache(maxsize=1)
def get_mail_backend() -> MailBackend:
    """Cached process-wide backend. Use the FastAPI dep wrapper in handlers."""
    return build_mail_backend(get_settings())


__all__ = [
    "MailMessage",
    "MailBackend",
    "SmtpMailBackend",
    "InMemoryMailBackend",
    "build_mail_backend",
    "get_mail_backend",
]
