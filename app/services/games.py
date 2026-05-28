"""Shared primitives for game-centric services.

Both :mod:`app.services.bets` (player predictions) and
:mod:`app.services.admin` (official results) need to look a game up by id
and validate a 0-99 score. Hosting those primitives here keeps the two
services from forming a soft dependency on each other and gives the
:class:`GameNotFound` and :class:`InvalidScore` exceptions a single
canonical identity, so a caller that touches both services can write one
``except`` clause instead of two for the same logical condition.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Game

# Two-digit scores per side cover every realistic football result;
# anything outside 0..99 is effectively a typo. The bound applies to
# both predicted bets and official results, so it lives here.
MIN_SCORE: int = 0
MAX_SCORE: int = 99


class GameNotFound(KeyError):
    """Raised when the supplied game_id doesn't exist."""


class InvalidScore(ValueError):
    """Raised when a supplied score is outside the accepted range.

    Carries machine-readable ``field`` (``"score_home"`` / ``"score_away"``)
    and ``kind`` (``"not_int"`` / ``"range"``) attributes so the route
    layer can translate the message without parsing strings. The base
    ``args`` still carry the English message for log compatibility.
    """

    def __init__(self, message: str, *, field: str | None = None, kind: str | None = None) -> None:
        super().__init__(message)
        self.field = field
        self.kind = kind


def load_game(db: Session, game_id: int) -> Game:
    """Return the :class:`Game` with *game_id* or raise :class:`GameNotFound`."""
    game = db.get(Game, game_id)
    if game is None:
        raise GameNotFound(game_id)
    return game


def validate_score(name: str, value: int) -> None:
    """Validate that *value* is in ``MIN_SCORE..MAX_SCORE`` for field *name*.

    Raises :class:`InvalidScore` with ``kind="range"`` when out of bounds.
    The function trusts its type annotation; non-int values are caught
    upstream by the route's form-parser, which raises ``ValueError`` and
    surfaces a separate i18n key.
    """
    if value < MIN_SCORE or value > MAX_SCORE:
        raise InvalidScore(
            f"{name} must be between {MIN_SCORE} and {MAX_SCORE}.",
            field=name,
            kind="range",
        )


__all__ = [
    "MIN_SCORE",
    "MAX_SCORE",
    "GameNotFound",
    "InvalidScore",
    "load_game",
    "validate_score",
]
