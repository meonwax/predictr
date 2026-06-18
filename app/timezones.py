"""Timezone handling for predictr.

Stores per-user timezone preferences as IANA names (``Europe/Berlin``,
``America/New_York``, ...) and exposes a tiny resolution API that mirrors
the one in :mod:`app.i18n`. Every persisted timestamp in the database is
UTC; this module is exclusively about *display*. The :func:`get_zone`
helper turns a stored name into a :class:`zoneinfo.ZoneInfo` for the
templating filters; :func:`resolve_timezone` does the precedence-chain
work for ``preferred_timezone`` -> cookie -> site default.

Why a curated allow-list instead of accepting any IANA zone?

* The tzdata database has ~600 entries, most of them historical
  duplicates (e.g. ``Asia/Kuala_Lumpur`` is just ``Asia/Singapore``
  these days). A curated list makes the settings dropdown manageable
  and stops "cute" choices (``Etc/GMT+14``) from confusing users.
* The list still covers every continent and every reasonable host
  location for the actual prediction-game audience.
* Custom entries can be added with a single line; nothing about the
  rest of the stack depends on the list being short.
"""

from __future__ import annotations

import logging
from typing import Final
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

LOGGER = logging.getLogger(__name__)


#: Site default fallback. Mirrors :data:`app.config.Settings.default_timezone`
#: when settings haven't been instantiated yet (e.g. in unit tests).
DEFAULT_TIMEZONE: Final[str] = "Europe/Berlin"


#: Curated list of timezones offered in the settings dropdown. Ordered
#: roughly by region (Europe -> Americas -> Africa/Middle East -> Asia ->
#: Pacific) and within each region by longitude. Add new entries to the
#: tuple to expose them in the UI; resolution accepts any name that
#: ``zoneinfo`` can load, not just the ones in this list, so a user
#: with a hand-edited preference is fine.
SUPPORTED_TIMEZONES: Final[tuple[str, ...]] = (
    # Reference
    "UTC",
    # Europe
    "Europe/London",
    "Europe/Lisbon",
    "Europe/Madrid",
    "Europe/Paris",
    "Europe/Amsterdam",
    "Europe/Brussels",
    "Europe/Berlin",
    "Europe/Zurich",
    "Europe/Vienna",
    "Europe/Rome",
    "Europe/Stockholm",
    "Europe/Helsinki",
    "Europe/Athens",
    "Europe/Istanbul",
    "Europe/Moscow",
    # Americas
    "America/Halifax",
    "America/New_York",
    "America/Chicago",
    "America/Denver",
    "America/Los_Angeles",
    "America/Anchorage",
    "America/Mexico_City",
    "America/Bogota",
    "America/Sao_Paulo",
    "America/Buenos_Aires",
    "America/Santiago",
    # Africa / Middle East
    "Africa/Cairo",
    "Africa/Lagos",
    "Africa/Johannesburg",
    "Asia/Jerusalem",
    "Asia/Dubai",
    # Asia / Pacific
    "Asia/Kolkata",
    "Asia/Bangkok",
    "Asia/Singapore",
    "Asia/Hong_Kong",
    "Asia/Shanghai",
    "Asia/Seoul",
    "Asia/Tokyo",
    "Australia/Perth",
    "Australia/Sydney",
    "Pacific/Auckland",
    "Pacific/Honolulu",
)


# Pre-build a frozenset for fast membership tests in the settings form.
_SUPPORTED_SET: Final[frozenset[str]] = frozenset(SUPPORTED_TIMEZONES)


def is_supported(name: str | None) -> bool:
    """Return ``True`` if *name* appears in the curated picker list."""
    return name is not None and name in _SUPPORTED_SET


def canonical_supported(name: str | None) -> str | None:
    """Return the :data:`SUPPORTED_TIMEZONES` entry matching *name*, else ``None``.

    Unlike :func:`is_supported`, which returns a bool, this yields the value
    *from* the curated tuple, so callers persist or set cookies using a known
    constant rather than the caller-supplied string.
    """
    if name is None:
        return None
    for candidate in SUPPORTED_TIMEZONES:
        if candidate == name:
            return candidate
    return None


def get_zone(name: str | None, *, default: str = DEFAULT_TIMEZONE) -> ZoneInfo:
    """Return a :class:`ZoneInfo` for *name*, falling back to *default*.

    The fallback chain itself never raises: if *default* is also a bad
    name (operator misconfiguration) we land on plain UTC. That keeps
    template rendering robust against typos in settings.
    """
    for candidate in (name, default, "UTC"):
        if not candidate:
            continue
        try:
            return ZoneInfo(candidate)
        except ZoneInfoNotFoundError:
            LOGGER.warning("Unknown timezone %r, falling back", candidate)
            continue
    # ``UTC`` is part of stdlib and never missing; this is defensive only.
    return ZoneInfo("UTC")


def resolve_timezone(user_timezone: str | None, *, default: str = DEFAULT_TIMEZONE) -> str:
    """Pick the timezone name we'll use for *user_timezone*.

    Returns *default* for ``None``, blank input, or any name that
    ``zoneinfo`` refuses to load. Unlike :func:`get_zone`, this function
    returns the *name* (a string), which is what the middleware stashes
    on ``request.state.timezone`` and the settings form persists.
    """
    name = (user_timezone or "").strip()
    if not name:
        return default
    try:
        ZoneInfo(name)
    except ZoneInfoNotFoundError:
        return default
    return name


__all__ = [
    "DEFAULT_TIMEZONE",
    "SUPPORTED_TIMEZONES",
    "get_zone",
    "is_supported",
    "canonical_supported",
    "resolve_timezone",
]
