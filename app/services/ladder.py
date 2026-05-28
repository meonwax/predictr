"""Ladder / leaderboard read model.

Single entry point: :func:`compute_ladder`. Sums each user's points across:

* All bets on games that have **kicked off and have a recorded result**.
* All answers on questions whose **deadline has passed and have a correct
  answer** recorded.

Both gates mirror the visibility rules used on ``/bets`` so a user's
ladder position never reflects information they can't already see on
their own bets page.

Scoring is computed in Python (via :mod:`app.services.scoring`) rather
than in SQL so the rules stay defined in exactly one place. For the
expected user counts (single-digit to low-hundreds) this is trivially
fast - two queries + one O(N.M) loop.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Answer, Bet, User
from app.services.scoring import (
    DEFAULT_CONFIG,
    ScoringConfig,
    calculate_answer_points,
    calculate_bet_points,
)


@dataclass(slots=True)
class BetBreakdown:
    """Per-user counters used to colour the ladder's "breakdown" column."""

    exact: int = 0  # bet matched the result exactly (5 pts each)
    spread: int = 0  # correct goal difference (3 pts each)
    tendency: int = 0  # correct winner only (2 pts each)
    miss: int = 0  # bet was placed but earned 0 points
    pending: int = 0  # bet placed, kickoff passed, no result yet
    upcoming: int = 0  # bet placed on a still-future game

    @property
    def scored(self) -> int:
        return self.exact + self.spread + self.tendency + self.miss


@dataclass(slots=True)
class LadderEntry:
    rank: int
    user: User
    bet_points: int = 0
    answer_points: int = 0
    breakdown: BetBreakdown = field(default_factory=BetBreakdown)
    answers_correct: int = 0
    answers_total: int = 0

    @property
    def total_points(self) -> int:
        return self.bet_points + self.answer_points


def compute_ladder(
    db: Session,
    *,
    now: datetime | None = None,
    config: ScoringConfig = DEFAULT_CONFIG,
) -> list[LadderEntry]:
    """Build a sorted ladder of every registered user.

    Sort order:

    1. ``total_points`` descending
    2. ``breakdown.exact`` descending (more 5-pointers wins ties)
    3. ``user.name`` ascending (stable alphabetical tiebreak)

    Users with no bets and no answers still appear in the ladder - they
    just rank last. That lets people confirm they signed up correctly
    even before placing their first bet.
    """
    now = now or datetime.now(UTC)

    users = db.scalars(select(User).order_by(User.id)).all()
    by_user: dict[int, LadderEntry] = {u.id: LadderEntry(rank=0, user=u) for u in users}

    # ---- Bets contribution ------------------------------------------------
    #
    # Eager-load the game so we can read kickoff_time + scores without an
    # N+1 explosion. Sorting in Python afterwards is cheap.
    bet_rows = db.scalars(select(Bet).options(joinedload(Bet.game))).all()
    for bet in bet_rows:
        entry = by_user.get(bet.user_id)
        if entry is None:
            # Defensive: orphaned bet (e.g. user was deleted but the FK
            # isn't ON DELETE CASCADE). Skip silently.
            continue
        game = bet.game
        if game.kickoff_time > now:
            entry.breakdown.upcoming += 1
            continue
        if game.score_home is None or game.score_away is None:
            entry.breakdown.pending += 1
            continue
        pts = calculate_bet_points(
            bet.score_home,
            bet.score_away,
            game.score_home,
            game.score_away,
            config,
        )
        entry.bet_points += pts
        if pts == config.points_result:
            entry.breakdown.exact += 1
        elif pts == config.points_tendency_spread:
            entry.breakdown.spread += 1
        elif pts == config.points_tendency:
            entry.breakdown.tendency += 1
        else:
            entry.breakdown.miss += 1

    # ---- Answers contribution --------------------------------------------
    answer_rows = db.scalars(select(Answer).options(joinedload(Answer.question))).all()
    for answer in answer_rows:
        entry = by_user.get(answer.user_id)
        if entry is None:
            continue
        question = answer.question
        if question.deadline > now:
            continue
        if question.correct_answer is None:
            continue
        entry.answers_total += 1
        pts = calculate_answer_points(
            answer.answer,
            question.correct_answer,
            question.points,
        )
        if pts > 0:
            entry.answers_correct += 1
            entry.answer_points += pts

    # ---- Sort + assign ranks --------------------------------------------
    ranked = sorted(
        by_user.values(),
        key=lambda e: (
            -e.total_points,
            -e.breakdown.exact,
            (e.user.name or "").lower(),
        ),
    )

    # Assign 1-based ranks; users tied on total_points share the same rank
    # ("competition ranking" - 1, 2, 2, 4 - rather than dense ranking).
    previous_key: tuple[int, int] | None = None
    rank_for_prev = 0
    for i, entry in enumerate(ranked, start=1):
        key = (entry.total_points, entry.breakdown.exact)
        if previous_key is not None and key == previous_key:
            entry.rank = rank_for_prev
        else:
            entry.rank = i
            rank_for_prev = i
            previous_key = key

    return ranked


__all__ = [
    "BetBreakdown",
    "LadderEntry",
    "compute_ladder",
]
