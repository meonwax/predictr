"""Centralised Jinja2 setup.

A single :data:`templates` object lives here so every route imports the
*same* environment - that way template globals (helpers, filters, the
``url_for`` shortcut for static assets) are configured exactly once.

Routes that render a template are responsible for putting ``current_user``
in their context (typically by declaring ``Depends(get_current_user)``);
the base layout reads ``{% if current_user %}`` to switch the navbar
between signed-in and anonymous states. Jinja's default ``Undefined``
treats a missing ``current_user`` as falsy, so a route that doesn't pass
it just shows the anonymous navbar - which is the correct default for
the auth pages themselves (login, register, lost-password).

i18n
----

Translations are exposed as a Jinja global ``_(key, **kwargs)`` plus a
filter ``language`` for resolving the active language code from a user
object. Both helpers read ``current_user`` from the rendering context;
when there's no logged-in user (or their ``preferred_language`` is
``None``) we fall back to the language stashed on ``request.state`` by
:class:`app.middleware.LanguageMiddleware`. That layer encapsulates the
cookie -> ``Accept-Language`` -> site-default precedence chain, so
templates don't need to know about it.

The date filter (``kickoff``) is also language-aware: it formats the
weekday and month abbreviations through the same catalogue rather than
relying on the host's ``LC_TIME`` locale. The same filter also picks up
the active *timezone* from ``current_user.preferred_timezone`` ->
``request.state.timezone`` -> :data:`app.config.Settings.default_timezone`,
converts the UTC timestamp accordingly, and renders the local zone
abbreviation (``CEST`` for Berlin in summer, ``EDT`` for New York in
summer, ``UTC`` for the eponymous zone).
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from fastapi.templating import Jinja2Templates
from jinja2 import pass_context
from jinja2.runtime import Context

from app.config import get_settings
from app.i18n import DEFAULT_LANGUAGE, gettext, resolve_language
from app.services.scoring import bet_css_class
from app.team_data import group_label, team_iso, team_name
from app.timezones import DEFAULT_TIMEZONE, get_zone, resolve_timezone

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def _language_from_context(ctx: Context) -> str:
    """Look up the active language for *ctx*.

    Resolution order:

    1. ``current_user.preferred_language`` if a user is signed in and has
       explicitly chosen a language (i.e. it's non-null and supported).
    2. ``request.state.language`` populated by
       :class:`app.middleware.LanguageMiddleware` (cookie or
       ``Accept-Language`` for anonymous visitors).
    3. The site default from :class:`app.config.Settings`.

    Steps 2 and 3 are reused as the fallback for users with a null
    ``preferred_language``, so newly-registered users follow the same
    cookie/header chain anonymous visitors do.
    """
    user = ctx.get("current_user")
    user_lang = getattr(user, "preferred_language", None) if user is not None else None
    if user_lang:
        return resolve_language(user_lang, default=get_settings().default_language)

    request = ctx.get("request")
    request_lang = getattr(getattr(request, "state", None), "language", None)
    if request_lang:
        return resolve_language(request_lang, default=get_settings().default_language)

    return resolve_language(None, default=get_settings().default_language)


def _timezone_from_context(ctx: Context) -> ZoneInfo:
    """Look up the display timezone for *ctx*, returning a :class:`ZoneInfo`.

    Mirrors :func:`_language_from_context`:

    1. ``current_user.preferred_timezone`` if set and loadable.
    2. ``request.state.timezone`` populated by the language middleware
       (cookie for anonymous visitors).
    3. :data:`app.config.Settings.default_timezone`.

    Always returns a usable zone - unknown names fall back through the
    chain instead of raising, so template rendering can't blow up on a
    bad preference.
    """
    site_default = get_settings().default_timezone

    user = ctx.get("current_user")
    user_tz = getattr(user, "preferred_timezone", None) if user is not None else None
    if user_tz:
        return get_zone(user_tz, default=site_default)

    request = ctx.get("request")
    request_tz = getattr(getattr(request, "state", None), "timezone", None)
    if request_tz:
        return get_zone(request_tz, default=site_default)

    return get_zone(site_default, default=DEFAULT_TIMEZONE)


@pass_context
def _t(ctx: Context, key: str, /, **kwargs: Any) -> str:
    """Jinja global ``_``: translate *key* using the request-scoped language.

    Any keyword argument whose name ends in ``_key`` is recursively
    translated before substitution - so a route can hand the template a
    structured ``{"field_key": "error.score.home", "min": 0, "max": 99}``
    payload and the cell template renders ``"Heimtor muss zwischen 0 und
    99 liegen."`` in one shot, without the route having to know the
    current language.
    """
    language = _language_from_context(ctx)
    resolved: dict[str, Any] = {}
    for name, value in kwargs.items():
        if name.endswith("_key") and isinstance(value, str):
            resolved[name[:-4]] = gettext(value, language)
        else:
            resolved[name] = value
    return gettext(key, language, **resolved)


def _tz_label(local: datetime) -> str:
    """Return a short, display-friendly label for *local*'s timezone.

    Prefers the canonical abbreviation from :py:meth:`datetime.tzname`
    (``CEST`` / ``CET`` / ``EDT`` / ``UTC`` ...). For zones whose
    abbreviation is just a signed offset like ``+05`` we expand to the
    classic ``UTC+05:00`` notation, which is what most users expect to
    see in a UI.
    """
    abbrev = local.tzname() or "UTC"
    if not abbrev or abbrev[0] in "+-":
        offset = local.utcoffset()
        if offset is None:
            return "UTC"
        total = int(offset.total_seconds())
        sign = "+" if total >= 0 else "-"
        total = abs(total)
        return f"UTC{sign}{total // 3600:02d}:{(total % 3600) // 60:02d}"
    return abbrev


@pass_context
def _format_kickoff(ctx: Context, dt: datetime | None) -> str:
    """Render a kickoff time for display, in the user's language + timezone.

    Format: ``<weekday>, DD <month> YYYY HH:MM <tz>`` (e.g.
    ``Mi, 11 Jun 2026 21:00 CEST`` for a German user in Berlin in June,
    ``Thu, 11 Jun 2026 15:00 EDT`` for an English user in New York).
    Weekday and month abbreviations come from the i18n catalogue so we
    don't depend on the host's ``LC_TIME``; the timezone label comes
    from ``tzname()`` on the *converted* datetime so DST is handled
    correctly (CEST vs CET).
    """
    if dt is None:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    zone = _timezone_from_context(ctx)
    local = dt.astimezone(zone)
    language = _language_from_context(ctx)
    day = gettext(f"date.day.{local.weekday()}", language)
    month = gettext(f"date.month.{local.month}", language)
    return (
        f"{day}, {local.day:02d} {month} {local.year} "
        f"{local.hour:02d}:{local.minute:02d} {_tz_label(local)}"
    )


@pass_context
def _format_short_date(ctx: Context, dt: datetime | None) -> str:
    """Render a date-only label in the user's locale.

    The conversion to the user's timezone happens *before* formatting,
    so a UTC ``2026-06-11 23:30`` displays on the local calendar day,
    even when the wall-clock time slips across midnight (Berlin viewer
    sees ``12 Jun 2026``; New York viewer sees ``11 Jun 2026``).

    Language drives the punctuation:

    * English: ``DD <month> YYYY`` (e.g. ``12 Jun 2026``). Two-digit
      day is the common compact form used in tabular contexts.
    * German:  ``D. <month> YYYY`` (e.g. ``22. Mai 2026``). The
      trailing dot on the day is the German ordinal marker; standard
      orthography also drops the leading zero on single-digit days
      (``1. Mai 2026``, not ``01. Mai 2026``).
    """
    if dt is None:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    zone = _timezone_from_context(ctx)
    local = dt.astimezone(zone)
    language = _language_from_context(ctx)
    month = gettext(f"date.month.{local.month}", language)
    if language == "de":
        return f"{local.day}. {month} {local.year}"
    return f"{local.day:02d} {month} {local.year}"


@pass_context
def _group_label(ctx: Context, group_id: str | None) -> str:
    """Context-aware group/knockout label lookup.

    Mirrors :func:`_team_name`: the language is resolved from the
    rendering context so callers can write ``{{ id | group_label }}``
    without threading the language through every partial. Unknown ids
    fall through to their uppercase form.
    """
    return group_label(group_id, language=_language_from_context(ctx))


def _datetime_local(dt: datetime | None) -> str:
    """Format a datetime as ``YYYY-MM-DDTHH:MM`` (UTC), the format expected by
    ``<input type="datetime-local">``. Empty string for ``None``.
    """
    if dt is None:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M")


@pass_context
def _language_filter(ctx: Context, user: object | None) -> str:
    """Return the language code that ``_()`` would use for *user*.

    Useful in templates that want to switch HTML markup based on the
    language (e.g. ``<html lang="{{ current_user | language }}">``).
    Mirrors :func:`_language_from_context`: an explicit preference on
    *user* wins, otherwise we fall through to the request-scoped
    language (cookie / ``Accept-Language``) and finally the site
    default.
    """
    lang = getattr(user, "preferred_language", None) if user is not None else None
    if lang:
        return resolve_language(lang, default=get_settings().default_language)
    return _language_from_context(ctx)


@pass_context
def _timezone_filter(ctx: Context, user: object | None) -> str:
    """Return the IANA timezone name that the date filters would use.

    Counterpart to ``language``: useful for the settings form
    ("currently saved as: Europe/Berlin") and the footer label, which
    wants the human-friendly name not the abbreviation.
    """
    tz = getattr(user, "preferred_timezone", None) if user is not None else None
    if tz:
        return resolve_timezone(tz, default=get_settings().default_timezone)
    zone = _timezone_from_context(ctx)
    return str(zone)


@pass_context
def _team_name(ctx: Context, fifa_code: str | None) -> str:
    """Context-aware team-name lookup.

    Picks the language from the rendering context (logged-in user's
    preference, falling back to the request-scoped language and finally
    the site default) so callers can write ``{{ team_name(code) }}``
    without threading the language through every partial.
    """
    return team_name(fifa_code, language=_language_from_context(ctx))


@pass_context
def _tz_label_now(ctx: Context, dt: datetime | None = None) -> str:
    """Return the abbreviation (``CEST``, ``UTC``) of the active timezone.

    If *dt* is given, the label is computed *at that instant* - useful
    when callers want a stable label for a specific match (so a single
    game's caption doesn't drift across the spring-forward/fall-back
    boundary). Without an argument, "now" is used, which is what the
    footer wants.
    """
    zone = _timezone_from_context(ctx)
    if dt is None:
        dt = datetime.now(UTC)
    elif dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return _tz_label(dt.astimezone(zone))


# Filters: usable as `{{ value | filter_name }}` in templates.
templates.env.filters["kickoff"] = _format_kickoff
templates.env.filters["short_date"] = _format_short_date
templates.env.filters["group_label"] = _group_label
templates.env.filters["datetime_local"] = _datetime_local
templates.env.filters["language"] = _language_filter
templates.env.filters["timezone"] = _timezone_filter

# Globals: usable as `{{ team_iso(code) }}` from anywhere in a template.
templates.env.globals.update(
    {
        "team_iso": team_iso,
        "team_name": _team_name,
        "group_label": _group_label,
        "bet_css_class": bet_css_class,
        "_": _t,
        "tz_label": _tz_label_now,
        "DEFAULT_LANGUAGE": DEFAULT_LANGUAGE,
    }
)
