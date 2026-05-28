"""Business logic for the ``/shouts`` page (the public shoutbox).

The model is intentionally tiny: every authenticated user can post a
short text message, and the page lists the most recent N entries in
reverse-chronological order. The two public entry points mirror that:

* :func:`list_shouts` - newest-first reads, eager-loading the author so
  the template can show name + avatar without an N+1 query.
* :func:`create_shout` - validated insert with the current timestamp.

There is no edit / delete intentionally - shouts are write-once so the
banter on the wall stays an honest record of what people said in the
moment.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Shout, User

LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

MIN_MESSAGE_LEN: int = 1
MAX_MESSAGE_LEN: int = 280  # Twitter-ish. The DB column allows 1000.
DEFAULT_LIMIT: int = 100


class InvalidShout(ValueError):
    """Raised when a shout fails validation (empty or too long).

    Carries a ``kind`` attribute (``"empty"`` / ``"too_long"``) so the
    route layer can pick the right translation key without parsing the
    English message.
    """

    def __init__(self, message: str, *, kind: str | None = None) -> None:
        super().__init__(message)
        self.kind = kind


# ---------------------------------------------------------------------------
# Reads
# ---------------------------------------------------------------------------


def list_shouts(db: Session, *, limit: int = DEFAULT_LIMIT) -> list[Shout]:
    """Return the most recent shouts, newest first.

    The author is eager-loaded so :func:`app.templating.avatar` can render
    each row without firing an extra query. ``limit`` caps the page size;
    callers that want everything pass ``limit=0`` (no cap).
    """
    stmt = (
        select(Shout).options(joinedload(Shout.user)).order_by(Shout.date.desc(), Shout.id.desc())
    )
    if limit and limit > 0:
        stmt = stmt.limit(limit)
    return list(db.scalars(stmt).all())


# ---------------------------------------------------------------------------
# Mutations
# ---------------------------------------------------------------------------


def create_shout(
    db: Session,
    user: User,
    *,
    message: str,
    now: datetime | None = None,
) -> Shout:
    """Persist a new shout from *user*.

    Whitespace is trimmed, internal newlines/tabs are collapsed to single
    spaces so the list rendering stays compact. Multiple spaces collapse
    too - copy-paste-from-IDE behaves predictably.

    Raises:
        :class:`InvalidShout`  empty after trim, or longer than
                               :data:`MAX_MESSAGE_LEN`.
    """
    cleaned = " ".join((message or "").split())
    if len(cleaned) < MIN_MESSAGE_LEN:
        raise InvalidShout("Message must not be empty.", kind="empty")
    if len(cleaned) > MAX_MESSAGE_LEN:
        raise InvalidShout(
            f"Message must be at most {MAX_MESSAGE_LEN} characters.",
            kind="too_long",
        )

    shout = Shout(
        date=now or datetime.now(UTC),
        message=cleaned,
        user_id=user.id,
    )
    db.add(shout)
    db.commit()
    db.refresh(shout)
    LOGGER.info("Shout created: id=%d user=%d (%d chars)", shout.id, user.id, len(cleaned))
    return shout


__all__ = [
    "MIN_MESSAGE_LEN",
    "MAX_MESSAGE_LEN",
    "DEFAULT_LIMIT",
    "InvalidShout",
    "list_shouts",
    "create_shout",
]
