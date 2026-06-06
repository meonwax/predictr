"""FastAPI dependency providers.

These are the small adapters between FastAPI's ``Depends`` machinery and the
plain Python services in :mod:`app.services`. Keeping them centralised lets
us override every cross-cutting concern from tests (DB session, current
user, mail backend, settings) without touching the route layer.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_session_factory
from app.models import User
from app.security import read_session_token
from app.services.mail import MailBackend, get_mail_backend
from app.services.site_info import get_site_title

# ---------------------------------------------------------------------------
# DB session
# ---------------------------------------------------------------------------


def get_db() -> Iterator[Session]:
    """Yield a request-scoped SQLAlchemy session and close it on teardown.

    Note that this does *not* commit. Read-only handlers can rely on the
    implicit close; writing handlers (or, more commonly, the service layer
    they call) commit explicitly so any failure rolls back deterministically.
    """
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


DbSession = Annotated[Session, Depends(get_db)]


# ---------------------------------------------------------------------------
# Settings + mail backend
# ---------------------------------------------------------------------------


def get_settings_dep() -> Settings:
    """FastAPI wrapper around :func:`app.config.get_settings`."""
    return get_settings()


SettingsDep = Annotated[Settings, Depends(get_settings_dep)]


def get_mail_backend_dep() -> MailBackend:
    """FastAPI wrapper around :func:`app.services.mail.get_mail_backend`.

    Tests override this dep to inject :class:`InMemoryMailBackend` and assert
    against the captured messages.
    """
    return get_mail_backend()


MailerDep = Annotated[MailBackend, Depends(get_mail_backend_dep)]


# ---------------------------------------------------------------------------
# Current user
# ---------------------------------------------------------------------------


def get_current_user(
    request: Request,
    db: DbSession,
    settings: SettingsDep,
) -> User | None:
    """Return the logged-in user, or ``None`` if there's no valid session cookie.

    Reads the signed session cookie, verifies it, and looks the user up. The
    decoded user is cached on ``request.state`` so subsequent ``Depends`` calls
    in the same request don't re-query the DB.
    """
    cached = getattr(request.state, "user", None)
    if cached is not None or getattr(request.state, "user_resolved", False):
        return cached

    request.state.user_resolved = True

    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        request.state.user = None
        return None

    user_id = read_session_token(token, settings=settings)
    if user_id is None:
        request.state.user = None
        return None

    user = db.get(User, user_id)
    request.state.user = user
    return user


CurrentUser = Annotated[User | None, Depends(get_current_user)]


def require_user(user: CurrentUser) -> User:
    """Dependency that 401s if no user is logged in."""
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )
    return user


RequiredUser = Annotated[User, Depends(require_user)]


def require_admin(user: CurrentUser) -> User:
    """Dependency that 403s if the user isn't logged in *or* isn't ROLE_ADMIN."""
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )
    if user.role != User.ROLE_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required.",
        )
    return user


RequiredAdmin = Annotated[User, Depends(require_admin)]


# ---------------------------------------------------------------------------
# Site title (shared chrome)
# ---------------------------------------------------------------------------


def provide_site_title(request: Request, db: DbSession) -> None:
    """Resolve the configured site title and stash it on ``request.state``.

    Wired as a router-level dependency on every page-rendering router so the
    shared chrome (``<title>``, navbar brand, footer) can read the
    database-configured title without each handler threading it through its
    template context. The Jinja ``site_title()`` global reads
    ``request.state.site_title`` and falls back to the brand name when it is
    absent (e.g. on a 404 where no route dependency ran).
    """
    request.state.site_title = get_site_title(db)
