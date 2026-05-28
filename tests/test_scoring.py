"""
Tests for the scoring engine.

These lock down every branch of the four public scoring helpers in
``app.services.scoring``:

* :func:`calculate_bet_points`
* :func:`calculate_answer_points`
* :func:`bet_css_class`
* :func:`answer_css_class`

If a test in this file ever fails, the live game's results would change
silently - please understand the implication before touching it.
"""

from __future__ import annotations

import pytest

from app.services.scoring import (
    DEFAULT_CONFIG,
    ScoringConfig,
    answer_css_class,
    bet_css_class,
    calculate_answer_points,
    calculate_bet_points,
)

# ---------------------------------------------------------------------------
# calculate_bet_points
# ---------------------------------------------------------------------------


class TestBetExactResult:
    """Branch 1 of the priority cascade: exact result match."""

    def test_simple_home_win(self) -> None:
        assert calculate_bet_points(2, 1, 2, 1) == DEFAULT_CONFIG.points_result

    def test_simple_away_win(self) -> None:
        assert calculate_bet_points(0, 3, 0, 3) == DEFAULT_CONFIG.points_result

    def test_zero_zero_draw(self) -> None:
        assert calculate_bet_points(0, 0, 0, 0) == DEFAULT_CONFIG.points_result

    def test_high_scoring_match(self) -> None:
        assert calculate_bet_points(7, 1, 7, 1) == DEFAULT_CONFIG.points_result

    def test_custom_config_value_is_returned(self) -> None:
        cfg = ScoringConfig(points_result=42, points_tendency_spread=7, points_tendency=1)
        assert calculate_bet_points(3, 2, 3, 2, cfg) == 42


class TestBetSameSpread:
    """
    Branch 2: same goal difference, different exact score.

    Includes the subtle case of two different draws (0-0 bet vs 1-1
    actual), which also count as "same spread" (both spreads are 0) and
    therefore award ``points_tendency_spread`` rather than 0.
    """

    def test_home_win_same_spread(self) -> None:
        # Bet 2-1, actual 3-2 -> both +1 spread.
        assert calculate_bet_points(2, 1, 3, 2) == DEFAULT_CONFIG.points_tendency_spread

    def test_away_win_same_spread(self) -> None:
        # Bet 0-2, actual 1-3 -> both -2 spread.
        assert calculate_bet_points(0, 2, 1, 3) == DEFAULT_CONFIG.points_tendency_spread

    def test_wrong_draw_score_still_counts_as_spread(self) -> None:
        # Both are draws, so both spreads are 0 -> "same spread" wins.
        assert calculate_bet_points(1, 1, 2, 2) == DEFAULT_CONFIG.points_tendency_spread

    def test_zero_zero_bet_vs_one_one_actual(self) -> None:
        # Sister case: both draws, spread 0 == 0.
        assert calculate_bet_points(0, 0, 1, 1) == DEFAULT_CONFIG.points_tendency_spread

    def test_large_spread_match(self) -> None:
        # Bet 5-1, actual 6-2 -> both +4 spread.
        assert calculate_bet_points(5, 1, 6, 2) == DEFAULT_CONFIG.points_tendency_spread


class TestBetTendencyOnly:
    """Branch 3: same winner (positive product of spreads), different spread."""

    def test_home_win_different_spread(self) -> None:
        # Bet 1-0 (+1), actual 3-0 (+3) -> same sign, different magnitude.
        assert calculate_bet_points(1, 0, 3, 0) == DEFAULT_CONFIG.points_tendency

    def test_away_win_different_spread(self) -> None:
        # Bet 0-1 (-1), actual 0-4 (-4).
        assert calculate_bet_points(0, 1, 0, 4) == DEFAULT_CONFIG.points_tendency

    def test_home_win_predicted_bigger_than_actual(self) -> None:
        # Bet 4-0 (+4), actual 1-0 (+1).
        assert calculate_bet_points(4, 0, 1, 0) == DEFAULT_CONFIG.points_tendency

    def test_away_win_predicted_bigger_than_actual(self) -> None:
        assert calculate_bet_points(0, 5, 1, 2) == DEFAULT_CONFIG.points_tendency


class TestBetNoPoints:
    """Branch 4: wrong tendency / no match -> 0."""

    def test_wrong_tendency_predicted_home_got_away(self) -> None:
        assert calculate_bet_points(2, 0, 0, 2) == 0

    def test_wrong_tendency_predicted_away_got_home(self) -> None:
        assert calculate_bet_points(0, 3, 4, 1) == 0

    def test_predicted_home_win_actual_was_draw(self) -> None:
        # +1 * 0 == 0, NOT > 0 -> no tendency points.
        assert calculate_bet_points(1, 0, 1, 1) == 0

    def test_predicted_away_win_actual_was_draw(self) -> None:
        assert calculate_bet_points(0, 1, 2, 2) == 0

    def test_predicted_draw_actual_was_home_win(self) -> None:
        # Bet spread 0, result spread > 0 -> spreads differ, product is 0 -> no tendency.
        assert calculate_bet_points(1, 1, 2, 0) == 0

    def test_predicted_draw_actual_was_away_win(self) -> None:
        assert calculate_bet_points(2, 2, 0, 3) == 0


class TestBetNullScores:
    """Any missing score returns 0 - covers "no bet placed yet" and
    "official result not entered yet" with a single guard."""

    @pytest.mark.parametrize(
        "scores",
        [
            (None, 1, 2, 1),
            (1, None, 2, 1),
            (1, 1, None, 1),
            (1, 1, 2, None),
            (None, None, 2, 1),
            (1, 1, None, None),
            (None, None, None, None),
        ],
    )
    def test_any_none_returns_zero(self, scores: tuple[int | None, ...]) -> None:
        bh, ba, rh, ra = scores
        assert calculate_bet_points(bh, ba, rh, ra) == 0


class TestBetPriorityOrder:
    """
    The cascade must always award the most valuable matching category.

    The classic config has `points_result > points_tendency_spread > points_tendency`,
    but the priority must hold for any monotone-decreasing config too.
    """

    @pytest.mark.parametrize(
        "config",
        [
            DEFAULT_CONFIG,
            ScoringConfig(points_result=10, points_tendency_spread=5, points_tendency=1),
            ScoringConfig(points_result=100, points_tendency_spread=50, points_tendency=10),
        ],
    )
    def test_exact_match_always_wins_over_spread(self, config: ScoringConfig) -> None:
        # 2-1 vs 2-1 is BOTH exact result and same spread; must award result, not spread.
        assert calculate_bet_points(2, 1, 2, 1, config) == config.points_result

    @pytest.mark.parametrize(
        "config",
        [
            DEFAULT_CONFIG,
            ScoringConfig(points_result=10, points_tendency_spread=5, points_tendency=1),
        ],
    )
    def test_spread_wins_over_tendency(self, config: ScoringConfig) -> None:
        # 2-1 vs 3-2 is BOTH same spread (+1) and same tendency (home); must award spread.
        assert calculate_bet_points(2, 1, 3, 2, config) == config.points_tendency_spread


class TestBetCustomConfig:
    """A non-default config flows all the way through."""

    def test_zero_point_config_yields_zero_for_correct_bet(self) -> None:
        cfg = ScoringConfig(points_result=0, points_tendency_spread=0, points_tendency=0)
        # Even an exact result earns 0 if the config says so.
        assert calculate_bet_points(2, 1, 2, 1, cfg) == 0

    def test_negative_points_are_returned_as_is(self) -> None:
        # The function is opinionated about category selection, not about the
        # value range - handing back a negative value is fine, and useful
        # for property-based tests that flip the sign.
        cfg = ScoringConfig(points_result=-1, points_tendency_spread=-2, points_tendency=-3)
        assert calculate_bet_points(2, 1, 2, 1, cfg) == -1
        assert calculate_bet_points(2, 1, 3, 2, cfg) == -2
        assert calculate_bet_points(2, 1, 4, 2, cfg) == -3


# ---------------------------------------------------------------------------
# calculate_answer_points
# ---------------------------------------------------------------------------


class TestAnswerExactMatch:
    def test_simple_match(self) -> None:
        assert calculate_answer_points("Germany", "Germany", 7) == 7

    def test_case_insensitive(self) -> None:
        assert calculate_answer_points("germany", "Germany", 7) == 7
        assert calculate_answer_points("GERMANY", "germany", 7) == 7

    def test_leading_and_trailing_whitespace_in_user_answer(self) -> None:
        assert calculate_answer_points("  Germany  ", "Germany", 7) == 7

    def test_leading_and_trailing_whitespace_in_variant(self) -> None:
        assert calculate_answer_points("Germany", "   Germany   ", 7) == 7


class TestAnswerContainsSemantics:
    """Answer matching uses *contains* semantics, not equality - so the
    user can write the variant inside a longer sentence and still match."""

    def test_user_answer_is_a_superstring_of_variant(self) -> None:
        assert calculate_answer_points("I think Germany wins", "Germany", 7) == 7

    def test_user_answer_contains_variant_in_the_middle(self) -> None:
        assert calculate_answer_points("Go Germany go!", "germany", 7) == 7

    def test_variant_is_not_substring_of_user_answer(self) -> None:
        # The relationship is "user CONTAINS variant", not the other way around.
        # "Germ" as the user answer does NOT contain "Germany".
        assert calculate_answer_points("Germ", "Germany", 7) == 0


class TestAnswerCommaSeparated:
    def test_first_variant_matches(self) -> None:
        assert calculate_answer_points("Germany", "Germany,Deutschland,GER", 7) == 7

    def test_middle_variant_matches(self) -> None:
        assert calculate_answer_points("Deutschland", "Germany,Deutschland,GER", 7) == 7

    def test_last_variant_matches(self) -> None:
        assert calculate_answer_points("GER", "Germany,Deutschland,GER", 7) == 7

    def test_none_of_the_variants_match(self) -> None:
        assert calculate_answer_points("France", "Germany,Deutschland,GER", 7) == 0

    def test_variants_are_individually_trimmed(self) -> None:
        # Whitespace around variant text must not stop a match.
        assert calculate_answer_points("Germany", " Germany ,  Deutschland", 7) == 7

    def test_each_variant_is_independently_case_insensitive(self) -> None:
        assert calculate_answer_points("deutschland", "Germany,Deutschland,GER", 7) == 7


class TestAnswerNullsAndEmpties:
    def test_null_user_answer(self) -> None:
        assert calculate_answer_points(None, "Germany", 7) == 0

    def test_null_correct_answer(self) -> None:
        assert calculate_answer_points("Germany", None, 7) == 0

    def test_both_null(self) -> None:
        assert calculate_answer_points(None, None, 7) == 0

    def test_empty_user_answer(self) -> None:
        # An empty user answer can never CONTAIN a non-empty variant.
        assert calculate_answer_points("", "Germany", 7) == 0

    def test_empty_correct_answer_yields_zero(self) -> None:
        # `"".split(",") == [""]`, and `"" in "France"` is True in Python,
        # so an empty ``correct_answer`` matches every non-empty user
        # answer. Documenting current behaviour so anyone who changes it
        # has to think twice - admins should never save an empty correct
        # answer in practice.
        assert calculate_answer_points("France", "", 7) == 7

    def test_empty_variant_in_list_matches_anything(self) -> None:
        # Same surprising-but-consistent behaviour: an empty variant in
        # a comma-separated list (``"Germany,,France"``) collapses to an
        # empty string which trivially "contains" everything.
        assert calculate_answer_points("anything", "Germany,,France", 7) == 7


class TestAnswerCustomPoints:
    def test_zero_question_points_yields_zero_even_on_match(self) -> None:
        assert calculate_answer_points("Germany", "Germany", 0) == 0

    def test_negative_points_are_returned_as_is(self) -> None:
        assert calculate_answer_points("Germany", "Germany", -3) == -3


# ---------------------------------------------------------------------------
# CSS class helpers
# ---------------------------------------------------------------------------


class TestBetCssClass:
    def test_exact_result_returns_success_bold(self) -> None:
        assert bet_css_class(DEFAULT_CONFIG.points_result) == "success bold"

    def test_spread_returns_info(self) -> None:
        assert bet_css_class(DEFAULT_CONFIG.points_tendency_spread) == "info"

    def test_tendency_returns_warning(self) -> None:
        assert bet_css_class(DEFAULT_CONFIG.points_tendency) == "warning"

    def test_zero_returns_none(self) -> None:
        assert bet_css_class(0) is None

    def test_unknown_value_returns_none(self) -> None:
        assert bet_css_class(99) is None

    def test_respects_custom_config(self) -> None:
        cfg = ScoringConfig(points_result=10, points_tendency_spread=5, points_tendency=1)
        assert bet_css_class(10, cfg) == "success bold"
        assert bet_css_class(5, cfg) == "info"
        assert bet_css_class(1, cfg) == "warning"
        assert bet_css_class(2, cfg) is None


class TestAnswerCssClass:
    def test_full_points_returns_success_bold(self) -> None:
        assert answer_css_class(7, 7) == "success bold"

    def test_no_points_returns_none(self) -> None:
        assert answer_css_class(0, 7) is None

    def test_partial_points_returns_none(self) -> None:
        # Answers score either full points or zero - no partial credit.
        assert answer_css_class(3, 7) is None

    def test_zero_question_points_still_returns_none(self) -> None:
        # Guards against the "everybody got 0 = success" anti-bug.
        assert answer_css_class(0, 0) is None


# ---------------------------------------------------------------------------
# End-to-end realistic scenario
# ---------------------------------------------------------------------------


def test_realistic_round_of_bets_totals_correctly() -> None:
    """
    A small scenario mirroring how the LadderService composes points.

    Bets (user -> game): exact, spread, tendency, no points, half-null.
    Default config: 5 / 3 / 2.
    Expected total: 5 + 3 + 2 + 0 + 0 = 10.
    """
    bets = [
        (2, 1, 2, 1),  # exact     -> 5
        (3, 2, 4, 3),  # spread    -> 3
        (1, 0, 4, 2),  # tendency  -> 2
        (0, 2, 3, 0),  # wrong     -> 0
        (1, None, 2, 1),  # half-null -> 0
    ]
    total = sum(calculate_bet_points(*b) for b in bets)
    assert total == 10


def test_realistic_round_of_answers_totals_correctly() -> None:
    """
    Mirrors a typical "special questions" round.

    Default question points = 7 each, so two correct + one wrong = 14.
    """
    answers = [
        ("Germany", "Germany,Deutschland,GER", 7),  # 7
        ("kane", "Harry Kane,Kane", 7),  # 7
        ("Eriksen", "Mbappé,Messi", 7),  # 0
    ]
    total = sum(calculate_answer_points(*a) for a in answers)
    assert total == 14
