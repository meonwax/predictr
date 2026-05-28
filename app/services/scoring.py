"""
Scoring engine.

The rules are deliberately implemented as plain functions of primitive
values so they can be exercised without spinning up a database, an HTTP
client, or even a SQLAlchemy session. The service layer that talks to the
ORM is intentionally a *thin* wrapper around these functions - keep it
that way.

Scoring rules
-------------

Per game bet, in priority order:

1. **Exact result** - `points_result`
2. **Correct goal difference** (same spread as the actual result, but
   different exact score) - `points_tendency_spread`. This also covers
   correctly-predicted draws with the wrong score: bet 1-1, actual 2-2.
3. **Correct tendency only** (same winner, different spread) -
   `points_tendency`. Implemented as `bet_spread * result_spread > 0`,
   which is true only when both spreads have the same non-zero sign.
4. Otherwise: **0 points**.

Per special-question answer:

* `correct_answer` may be a comma-separated list of acceptable variants
  (e.g. `"Germany,Deutschland,GER"`).
* A user answer matches when, after lowercasing and stripping, the user
  answer *contains* any of those variants. This `contains` semantics
  is intentional: it lets users write "Germany wins" and still match.
* Match -> `question.points`. No match -> 0.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ScoringConfig:
    """
    Configurable point values for the three winning bet categories.

    Mirrors the `points_result`, `points_tendency_spread`, and
    `points_tendency` columns of the `config` table.
    """

    points_result: int
    points_tendency_spread: int
    points_tendency: int


DEFAULT_CONFIG = ScoringConfig(
    points_result=5,
    points_tendency_spread=3,
    points_tendency=2,
)
"""Default scoring config: 5 / 3 / 2 points (matches the ``config`` table seed)."""


def calculate_bet_points(
    bet_score_home: int | None,
    bet_score_away: int | None,
    result_score_home: int | None,
    result_score_away: int | None,
    config: ScoringConfig = DEFAULT_CONFIG,
) -> int:
    """
    Compute points awarded for one game bet.

    Returns 0 if any of the four scores is `None` (i.e. either the user did
    not bet or the official result has not been entered yet).
    """
    if any(
        s is None for s in (bet_score_home, bet_score_away, result_score_home, result_score_away)
    ):
        return 0

    # Narrowed for the type checker.
    bh, ba = bet_score_home, bet_score_away
    rh, ra = result_score_home, result_score_away
    assert bh is not None and ba is not None and rh is not None and ra is not None

    if bh == rh and ba == ra:
        return config.points_result

    bet_spread = bh - ba
    result_spread = rh - ra

    if bet_spread == result_spread:
        # Same goal difference, different exact score.
        # Also covers correctly-predicted draws: spread 0 == 0.
        return config.points_tendency_spread

    if bet_spread * result_spread > 0:
        # Same non-zero sign -> same winner, different spread.
        # A draw bet vs. a non-draw result (or vice versa) falls through
        # to 0 because the product is 0, not strictly positive.
        return config.points_tendency

    return 0


def calculate_answer_points(
    user_answer: str | None,
    correct_answer: str | None,
    question_points: int,
) -> int:
    """
    Compute points awarded for one special-question answer.

    `correct_answer` may be a comma-separated list of accepted variants;
    each variant is compared case-insensitively against the (trimmed,
    lowercased) `user_answer` using *contains* semantics, so a user
    answer like ``"I think Germany wins"`` still matches the variant
    ``"Germany"``.
    """
    if user_answer is None or correct_answer is None:
        return 0

    haystack = user_answer.lower().strip()
    for variant in correct_answer.split(","):
        if variant.strip().lower() in haystack:
            return question_points
    return 0


def bet_css_class(points: int, config: ScoringConfig = DEFAULT_CONFIG) -> str | None:
    """
    Classify a bet's points into a Bootstrap-style CSS class.

    Used by the bets / ladder templates to colour each cell according to
    how the bet scored: exact result is the strong "success" green, same
    goal difference is "info" blue, correct tendency only is "warning"
    yellow, no points returns ``None`` (no extra class).
    """
    if points == config.points_result:
        return "success bold"
    if points == config.points_tendency_spread:
        return "info"
    if points == config.points_tendency:
        return "warning"
    return None


def answer_css_class(points: int, question_points: int) -> str | None:
    """
    Classify an answer's points into a Bootstrap-style CSS class.

    Returns ``"success bold"`` when the user earned the full
    ``question.points`` value (an answer scores either full points or
    zero - there is no partial credit), otherwise ``None``.
    """
    if points == question_points and question_points > 0:
        return "success bold"
    return None
