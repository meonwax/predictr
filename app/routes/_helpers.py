"""Shared utilities for the HTTP route modules.

The four interactive route modules (``bets``, ``admin``, ``questions``,
``shouts``) share a small set of helpers:

* HTMX detection via the ``HX-Request`` header.
* Parsing of the optional integer score form fields.
* Translation of service-layer exceptions into the i18n key + args pairs
  that the templates render.

Keeping these in a neutral module avoids cross-imports between routes
(admin would otherwise have to import from the user-facing ``questions``
route, or vice versa) and gives us a single place to evolve the HTMX or
scoring contract.
"""

from __future__ import annotations

from fastapi import Request

from app.services.games import MAX_SCORE, MIN_SCORE, InvalidScore
from app.services.questions import (
    MAX_ANSWER_LEN,
    MAX_CORRECT_ANSWER_LEN,
    MAX_POINTS,
    MAX_QUESTION_LEN,
    MIN_POINTS,
    MIN_QUESTION_LEN,
    InvalidQuestionData,
)


def is_htmx(request: Request) -> bool:
    """Return True when *request* was issued by HTMX (``HX-Request: true``)."""
    return request.headers.get("HX-Request", "").lower() == "true"


def parse_score(raw: str) -> int | None:
    """Parse a score form value into an int, or return ``None`` for blank.

    Raises :class:`ValueError` when *raw* is non-blank but not a clean
    integer. ``raw`` is treated defensively: ``None`` is accepted and
    handled like the empty string so a stray ``Form()`` default does not
    blow up the route.
    """
    s = (raw or "").strip()
    if s == "":
        return None
    return int(s)


def map_invalid_score(exc: InvalidScore) -> tuple[str, dict[str, object]]:
    """Translate an :class:`InvalidScore` into an i18n key + args pair.

    The route never trusts the exception's message - it only inspects the
    structured ``field`` / ``kind`` attributes so the same error wording
    surfaces consistently in both languages.
    """
    field_key = "error.score.home" if exc.field == "score_home" else "error.score.away"
    if exc.kind == "range":
        return "error.score.range", {
            "field_key": field_key,
            "min": MIN_SCORE,
            "max": MAX_SCORE,
        }
    return "error.score.not_int", {"field_key": field_key}


_QUESTION_ERROR_KEYS: dict[str, tuple[str, dict[str, object]]] = {
    "text_too_short": ("error.question.text_too_short", {"min": MIN_QUESTION_LEN}),
    "text_too_long": ("error.question.text_too_long", {"max": MAX_QUESTION_LEN}),
    "points_not_int": ("error.question.points_not_int", {}),
    "points_required": ("error.question.points_required", {}),
    "points_range": (
        "error.question.points_range",
        {"min": MIN_POINTS, "max": MAX_POINTS},
    ),
    "correct_too_long": (
        "error.question.correct_too_long",
        {"max": MAX_CORRECT_ANSWER_LEN},
    ),
    "answer_empty": ("error.question.answer_empty", {}),
    "answer_too_long": ("error.question.answer_too_long", {"max": MAX_ANSWER_LEN}),
    "deadline_required": ("error.question.deadline_required", {}),
    "deadline_invalid": ("error.question.deadline_invalid", {}),
}


def map_invalid_question(exc: InvalidQuestionData) -> tuple[str, dict[str, object]]:
    """Translate an :class:`InvalidQuestionData` into an i18n key + args pair.

    Falls back to ``error.question.answer_empty`` if the exception's
    ``kind`` is missing or unknown so the user still sees a sensible
    message instead of a blank field.
    """
    key, args = _QUESTION_ERROR_KEYS.get(
        exc.kind or "",
        ("error.question.answer_empty", {}),
    )
    return key, dict(args)
