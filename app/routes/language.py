"""HTTP routes for switching the active UI language and timezone.

The footer language switcher posts to ``POST /language``; a small
piece of JavaScript posts to ``POST /timezone`` with the browser's
detected zone shortly after the first page load. Both endpoints work
for anonymous and signed-in visitors:

* Anonymous users get a long-lived cookie (``predictr_lang`` /
  ``predictr_tz``). The next request goes through
  :class:`app.middleware.LanguageMiddleware`, which reads the cookies
  and stashes the choice on ``request.state`` so templates pick them
  up automatically.
* Signed-in users get the same cookies plus we persist the choice on
  their user row. This keeps the choice sticky across devices once
  they sign in elsewhere - the cookie alone would only cover the
  current browser.

The ``next`` form field on ``POST /language`` carries the URL we
redirect to after the switch (typically the page the user was already
on). We sanitise it to a relative path to prevent open-redirect attacks.
``POST /timezone`` is invoked from JavaScript and returns 204, so it
doesn't need a redirect target.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated
from urllib.parse import urlsplit

from fastapi import APIRouter, Form, Response, status
from fastapi.responses import RedirectResponse

from app.dependencies import CurrentUser, DbSession, SettingsDep
from app.i18n import SUPPORTED_LANGUAGES
from app.middleware import LANGUAGE_COOKIE_NAME, TIMEZONE_COOKIE_NAME
from app.timezones import is_supported as _is_supported_tz

router = APIRouter(tags=["language"])

#: Cookie lifetime in seconds. 365 days is short enough that long-stale
#: choices eventually defer to the site default, and long enough that the
#: switch survives normal browsing.
_COOKIE_MAX_AGE: int = 365 * 24 * 60 * 60


def _safe_next(raw: str) -> str:
    """Return a safe in-app redirect target.

    Accepts only paths starting with ``/`` and not ``//`` (which would be
    a protocol-relative URL allowing the attacker to redirect to a
    different host). Anything else collapses to ``"/"``.
    """
    if not raw:
        return "/"
    parsed = urlsplit(raw)
    if parsed.scheme or parsed.netloc:
        return "/"
    if not parsed.path.startswith("/"):
        return "/"
    if parsed.path.startswith("//"):
        return "/"
    path = parsed.path
    if parsed.query:
        path = f"{path}?{parsed.query}"
    if parsed.fragment:
        path = f"{path}#{parsed.fragment}"
    return path


@router.post("/language", include_in_schema=False)
def set_language(
    db: DbSession,
    user: CurrentUser,
    settings: SettingsDep,
    language: Annotated[str, Form()] = "",
    next: Annotated[str, Form()] = "/",
) -> RedirectResponse:
    """Switch the UI language for the current visitor.

    Only takes effect when *language* is an explicitly supported code
    (``"de"`` or ``"en"``). Unknown / blank / tampered values are
    silently ignored - the redirect still happens so the form submit
    feels seamless, but no cookie is written and the user's stored
    preference is left untouched. For signed-in users we also persist
    the choice on the user row so the next sign-in on a different
    browser inherits it.
    """
    target = _safe_next(next)
    response = RedirectResponse(url=target, status_code=status.HTTP_303_SEE_OTHER)

    requested = (language or "").strip().lower()
    if requested not in SUPPORTED_LANGUAGES:
        return response

    response.set_cookie(
        key=LANGUAGE_COOKIE_NAME,
        value=requested,
        max_age=_COOKIE_MAX_AGE,
        path="/",
        samesite="lax",
        httponly=False,
        secure=settings.secure_cookies,
    )
    if user is not None and user.preferred_language != requested:
        user.preferred_language = requested
        user.last_modified_date = datetime.now(UTC)
        db.commit()
    return response


@router.post("/timezone", include_in_schema=False)
def set_timezone(
    db: DbSession,
    user: CurrentUser,
    settings: SettingsDep,
    timezone_name: Annotated[str, Form(alias="timezone")] = "",
) -> Response:
    """Update the visitor's timezone from a small JS auto-detect snippet.

    Returns ``204 No Content`` so the calling fetch() doesn't have to
    parse a body. Like ``/language``, unknown / unsupported zones are
    silently ignored (no cookie, no DB write) so a tampered POST can't
    drop a garbage cookie on the visitor.
    """
    response = Response(status_code=status.HTTP_204_NO_CONTENT)

    requested = (timezone_name or "").strip()
    if not _is_supported_tz(requested):
        return response

    response.set_cookie(
        key=TIMEZONE_COOKIE_NAME,
        value=requested,
        max_age=_COOKIE_MAX_AGE,
        path="/",
        samesite="lax",
        httponly=False,
        secure=settings.secure_cookies,
    )
    if (
        user is not None
        and user.preferred_timezone != requested
        and user.preferred_timezone is None
    ):
        # Don't overwrite an explicit user preference with a browser
        # auto-detect - once the user has chosen a timezone in
        # settings, we respect that across browsers.
        user.preferred_timezone = requested
        user.last_modified_date = datetime.now(UTC)
        db.commit()
    return response


__all__ = ["router"]
