"""Read-side service for the public ``/info`` page.

The ``rules_en`` / ``rules_de`` Markdown columns can reference the
configured point values (e.g. *"You get {{ points_result }} points for an
exact result"*), so rules text always stays in sync with the scoring
config without operators having to remember to edit two places.

Rendering is a two-step pipeline:

1. A tiny Jinja2 ``Template`` substitutes ``{{ points_result }}`` etc.
2. :mod:`markdown` converts the interpolated Markdown to HTML, which the
   page template emits with ``| safe``.

Both steps happen inside :func:`get_site_info` so the route handler
stays a one-liner.

If the ``config`` table is empty we fall back to
:data:`DEFAULT_SITE_INFO`. Operators are expected to override the row
via the SQL seed; an in-app editor is intentionally out of scope.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import markdown as md
from jinja2 import Template
from jinja2.exceptions import TemplateError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.i18n import SUPPORTED_LANGUAGES as I18N_SUPPORTED_LANGUAGES
from app.i18n import resolve_language
from app.models import Config, User

LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Defaults - used when the singleton config row is missing.
# ---------------------------------------------------------------------------

DEFAULT_TITLE: str = "Predictr"
DEFAULT_OWNER: str = "Predictr"
DEFAULT_ADMIN_EMAIL: str = "admin@example.com"
DEFAULT_POINTS_RESULT: int = 5
DEFAULT_POINTS_TENDENCY_SPREAD: int = 3
DEFAULT_POINTS_TENDENCY: int = 2

#: Languages with bundled default rules text. Kept in sync with
#: :data:`app.i18n.SUPPORTED_LANGUAGES`.
SUPPORTED_LANGUAGES: tuple[str, ...] = I18N_SUPPORTED_LANGUAGES


DEFAULT_RULES_MARKDOWN: str = """\
## Welcome to **{{ title }}**

This is the office prediction game for the 2026 FIFA World Cup - the first
edition with **48 teams** spread over **12 groups**, **104 matches**, and the
shiny new **Round of 32** knockout stage. The tournament kicks off on
**11 June 2026** and ends with the final on **19 July 2026** at MetLife
Stadium, New Jersey.

## How to play

1. Sign up with your name, email, and a password.
2. Predict the **final score** of every match before kickoff. After kickoff
   the bet is locked - no edits allowed.
3. Answer the **special questions** before each one's individual deadline
   (top scorer of the tournament, dark-horse semi-finalist, etc.).
4. Watch the **ladder** to see how you're doing against the rest of the
   office.

## Scoring

For every match your bet is compared against the official result:

| Outcome                                       | Points                          |
| --------------------------------------------- | ------------------------------- |
| **Exact score**                               | **{{ points_result }}**         |
| Correct goal difference (non-draw, e.g. 2:1 vs 3:2) | {{ points_tendency_spread }} |
| Correct winner only (or correct draw)         | {{ points_tendency }}           |
| Wrong tendency                                | 0                               |

For special questions you get the **full point value of the question** if
your answer matches the correct one (case-insensitive, comma-separated
variants count as "the same answer"). Otherwise zero - there is no partial
credit.

## Tie-breaking on the ladder

If two players end up with the same total, the one with more **exact
results** ranks higher. If they're still tied, alphabetical order decides.

## Questions or trouble?

Drop a line to <a href="mailto:{{ admin_email }}">{{ admin_email }}</a>.
"""


DEFAULT_RULES_MARKDOWN_DE: str = """\
## Willkommen bei **{{ title }}**

Das ist das Tippspiel für die FIFA Fussball-Weltmeisterschaft 2026 - die
erste Ausgabe mit **48 Mannschaften** in **12 Gruppen**, **104 Spielen**
und der neuen **Runde der letzten 32**. Das Turnier startet am
**11. Juni 2026** und endet mit dem Finale am **19. Juli 2026** im
MetLife Stadium in New Jersey.

## Spielablauf

1. Mit Name, E-Mail und Passwort registrieren.
2. Vor jedem Anpfiff das **Endergebnis** tippen. Nach dem Anpfiff ist
   der Tipp gesperrt - keine Änderungen mehr möglich.
3. Die **Sonderfragen** jeweils vor ihrem eigenen Stichtag beantworten
   (Torschützenkönig, Geheim-Halbfinalist, …).
4. In der **Rangliste** mitverfolgen, wie es im Vergleich zu den anderen
   läuft.

## Punktevergabe

Pro Spiel wird der Tipp mit dem offiziellen Ergebnis verglichen:

| Ergebnis                                       | Punkte                       |
| ---------------------------------------------- | ---------------------------- |
| **Exakter Endstand**                           | **{{ points_result }}**      |
| Richtige Tordifferenz (z. B. 2:1 vs. 3:2)      | {{ points_tendency_spread }} |
| Nur richtiger Sieger (oder richtiges Remis)    | {{ points_tendency }}        |
| Falsche Tendenz                                | 0                            |

Bei Sonderfragen gibt es die **volle Punktzahl der Frage**, wenn die
Antwort zur korrekten passt (Groß-/Kleinschreibung egal, komma-getrennte
Varianten zählen als "dieselbe Antwort"). Sonst null Punkte - Teilpunkte
gibt es nicht.

## Gleichstand in der Rangliste

Bei Punktegleichstand liegt die Spielerin oder der Spieler mit **mehr
exakten Ergebnissen** vorn. Bleibt es trotzdem gleich, entscheidet die
alphabetische Reihenfolge.

## Fragen oder Probleme?

Eine kurze Mail an <a href="mailto:{{ admin_email }}">{{ admin_email }}</a>
genügt.
"""


# ---------------------------------------------------------------------------
# Read model
# ---------------------------------------------------------------------------


@dataclass(slots=True, frozen=True)
class SiteInfo:
    """Read model passed to the ``/info`` template.

    ``rules_html`` is already pre-rendered (Jinja -> Markdown -> HTML) so the
    template can dump it with ``{{ site_info.rules_html | safe }}`` and not
    worry about double-escaping.
    """

    title: str
    owner: str
    admin_email: str
    rules_html: str
    points_result: int
    points_tendency_spread: int
    points_tendency: int


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def render_rules_markdown(
    raw: str,
    *,
    title: str,
    owner: str,
    admin_email: str,
    points_result: int,
    points_tendency_spread: int,
    points_tendency: int,
) -> str:
    """Render the rules Markdown to HTML, with point-value interpolation.

    The two-step pipeline:

    1. Jinja2 substitutes ``{{ points_result }}``, ``{{ admin_email }}`` etc.
       Any other Jinja constructs are *not* expected - the rules text is
       supposed to be plain Markdown with a sprinkle of variable references.
    2. :mod:`markdown` converts the interpolated Markdown to HTML, with
       ``tables`` and ``fenced_code`` enabled so authors can write GitHub-
       flavoured tables (the default scoring table relies on this).

    A broken template never crashes the request: we log a warning and fall
    back to the raw text so admins can still see what they wrote.
    """
    try:
        rendered = Template(raw).render(
            title=title,
            owner=owner,
            admin_email=admin_email,
            points_result=points_result,
            points_tendency_spread=points_tendency_spread,
            points_tendency=points_tendency,
        )
    except TemplateError as exc:
        LOGGER.warning("Failed to interpolate rules template: %s", exc)
        rendered = raw
    return md.markdown(
        rendered,
        extensions=["tables", "fenced_code", "sane_lists"],
        output_format="html",
    )


# ---------------------------------------------------------------------------
# Reads
# ---------------------------------------------------------------------------


def _resolve_language(user: User | None) -> str:
    """Pick the language code we'll serve for *user*.

    Anonymous visitors and users without a stored preference fall back to
    ``Settings.default_language`` (German for our deployment). Unknown codes
    also fall through to the default rather than producing a 500.
    """
    default = get_settings().default_language
    if user is None:
        return resolve_language(None, default=default)
    return resolve_language(user.preferred_language, default=default)


def _pick_rules_source(
    config: Config | None,
    language: str,
) -> str:
    """Return the Markdown text to render for *language*.

    Precedence (per language):
      1. The matching column on the config row, if non-blank.
      2. The English column (cross-language fallback) if non-blank.
      3. The packaged default for the language.
    """
    if config is None:
        return DEFAULT_RULES_MARKDOWN_DE if language == "de" else DEFAULT_RULES_MARKDOWN

    preferred = (config.rules_de if language == "de" else config.rules_en) or ""
    if preferred.strip():
        return preferred
    fallback_col = config.rules_en or ""
    if fallback_col.strip():
        return fallback_col
    return DEFAULT_RULES_MARKDOWN_DE if language == "de" else DEFAULT_RULES_MARKDOWN


def get_site_info(db: Session, user: User | None = None) -> SiteInfo:
    """Return the singleton site info, falling back to defaults if absent.

    The ``config`` table is *almost* a singleton: it has an
    auto-incrementing primary key but is expected to hold exactly one
    row. We read by ``id ASC LIMIT 1`` so multiple rows wouldn't crash,
    and so a fresh database with no config row still produces a sensible
    page.

    When *user* is supplied and has ``preferred_language == 'de'``, the
    German rules variant is preferred (with graceful fallback to the
    English column or the packaged default if German is blank).
    """
    config = db.scalars(select(Config).order_by(Config.id).limit(1)).first()
    language = _resolve_language(user)

    if config is None:
        rules_html = render_rules_markdown(
            _pick_rules_source(None, language),
            title=DEFAULT_TITLE,
            owner=DEFAULT_OWNER,
            admin_email=DEFAULT_ADMIN_EMAIL,
            points_result=DEFAULT_POINTS_RESULT,
            points_tendency_spread=DEFAULT_POINTS_TENDENCY_SPREAD,
            points_tendency=DEFAULT_POINTS_TENDENCY,
        )
        return SiteInfo(
            title=DEFAULT_TITLE,
            owner=DEFAULT_OWNER,
            admin_email=DEFAULT_ADMIN_EMAIL,
            rules_html=rules_html,
            points_result=DEFAULT_POINTS_RESULT,
            points_tendency_spread=DEFAULT_POINTS_TENDENCY_SPREAD,
            points_tendency=DEFAULT_POINTS_TENDENCY,
        )

    rules_html = render_rules_markdown(
        _pick_rules_source(config, language),
        title=config.title,
        owner=config.owner,
        admin_email=config.admin_email,
        points_result=config.points_result,
        points_tendency_spread=config.points_tendency_spread,
        points_tendency=config.points_tendency,
    )
    return SiteInfo(
        title=config.title,
        owner=config.owner,
        admin_email=config.admin_email,
        rules_html=rules_html,
        points_result=config.points_result,
        points_tendency_spread=config.points_tendency_spread,
        points_tendency=config.points_tendency,
    )


__all__ = [
    "DEFAULT_RULES_MARKDOWN",
    "DEFAULT_RULES_MARKDOWN_DE",
    "DEFAULT_TITLE",
    "DEFAULT_OWNER",
    "DEFAULT_ADMIN_EMAIL",
    "SUPPORTED_LANGUAGES",
    "DEFAULT_POINTS_RESULT",
    "DEFAULT_POINTS_TENDENCY_SPREAD",
    "DEFAULT_POINTS_TENDENCY",
    "SiteInfo",
    "get_site_info",
    "render_rules_markdown",
]
