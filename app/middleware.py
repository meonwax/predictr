"""Cross-cutting ASGI middleware.

Currently a single middleware lives here: :class:`LanguageMiddleware`
(slight misnomer - it now also handles timezone). It resolves both the
active UI language *and* the display timezone for every incoming request
and stashes them on ``request.state``. Templates read those values via
:func:`app.templating._language_from_context` and
:func:`app.templating._timezone_from_context` so an anonymous visitor's
choices - cookies or browser hints - are honoured even before they
reach a per-user preference.

Resolution order (highest priority first), applied to both fields:

1. The explicit cookie set by ``POST /language`` (language only) or
   ``POST /timezone`` (timezone only).
2. *Language only*: the first supported code in the request's
   ``Accept-Language`` header.
3. The site default from :class:`app.config.Settings`.

A logged-in user with a non-null preference wins over all of the above;
that comparison happens in :mod:`app.templating` because the user
resolution needs DB access (and we want to keep middleware cheap).
"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from app.config import get_settings
from app.i18n import (
    DEFAULT_LANGUAGE,
    SUPPORTED_LANGUAGES,
    parse_accept_language,
    resolve_language,
)
from app.timezones import DEFAULT_TIMEZONE, resolve_timezone

#: Name of the cookie used by ``POST /language`` to remember an anonymous
#: visitor's choice. A simple, namespaced name makes it harmless if it ever
#: leaks; the cookie value is checked against ``SUPPORTED_LANGUAGES`` before
#: being trusted.
LANGUAGE_COOKIE_NAME: str = "predictr_lang"

#: Cookie used by ``POST /timezone`` to remember an anonymous visitor's
#: timezone (also written by a small client-side helper that detects the
#: browser's ``Intl.DateTimeFormat().resolvedOptions().timeZone``).
TIMEZONE_COOKIE_NAME: str = "predictr_tz"


def _site_default_language() -> str:
    try:
        return get_settings().default_language
    except Exception:
        return DEFAULT_LANGUAGE


def _site_default_timezone() -> str:
    try:
        return get_settings().default_timezone
    except Exception:
        return DEFAULT_TIMEZONE


def resolve_request_language(request: Request) -> str:
    """Resolve the language code for *request* using cookie -> header -> default.

    Pure function (no DB access). Exposed for tests and reusable from
    routes that need to know the language before the template is
    rendered (e.g. ``POST /language`` itself, which echoes the picked
    code back into a redirect).
    """
    site_default = _site_default_language()

    cookie_value = request.cookies.get(LANGUAGE_COOKIE_NAME)
    if cookie_value:
        cookie_lang = resolve_language(cookie_value, default="")
        if cookie_lang in SUPPORTED_LANGUAGES:
            return cookie_lang

    header = request.headers.get("accept-language")
    for code in parse_accept_language(header):
        if code in SUPPORTED_LANGUAGES:
            return code

    return resolve_language(site_default, default=DEFAULT_LANGUAGE)


def resolve_request_timezone(request: Request) -> str:
    """Resolve the IANA timezone name for *request* using cookie -> default.

    There is no ``Accept-Language``-style timezone header in HTTP, so
    the only browser-side hint is the cookie set by the small JS helper
    that reads ``Intl.DateTimeFormat().resolvedOptions().timeZone``. If
    the cookie names a zone we can load, we use it; otherwise we fall
    back to the site default.
    """
    site_default = _site_default_timezone()

    cookie_value = request.cookies.get(TIMEZONE_COOKIE_NAME)
    if cookie_value:
        return resolve_timezone(cookie_value, default=site_default)

    return resolve_timezone(site_default, default=DEFAULT_TIMEZONE)


class LanguageMiddleware(BaseHTTPMiddleware):
    """Populate ``request.state`` with language + timezone for every request."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        request.state.language = resolve_request_language(request)
        request.state.timezone = resolve_request_timezone(request)
        return await call_next(request)


__all__ = [
    "LANGUAGE_COOKIE_NAME",
    "TIMEZONE_COOKIE_NAME",
    "LanguageMiddleware",
    "resolve_request_language",
    "resolve_request_timezone",
]
