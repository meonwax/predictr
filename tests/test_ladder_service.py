"""Unit tests for :mod:`app.services.ladder`.

These exercise the read model directly. We seed bets and (optionally)
questions/answers via the service+model layers and then assert against
the resulting :class:`LadderEntry` list.

The seeded engine is shared across the test session, so any mutation
of seeded game scores must be undone in fixture teardown. The
``_reset_game_scores`` autouse fixture (introduced by the admin tests)
already does that; we mirror it here for the questions/answers tables
which the ladder also consumes.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from app.models import Answer, Game, Question, User
from app.services.bets import upsert_bet
from app.services.ladder import compute_ladder
from app.services.users import RegistrationData, register_user

GAME_OPENER_ID = 1
GAME_2_ID = 2
GAME_OPENER_KICKOFF = datetime(2026, 6, 11, 19, 0, tzinfo=UTC)


@pytest.fixture()
def fresh_db(clean_user_tables: None, seeded_engine) -> Iterator[Session]:
    Session_ = sessionmaker(bind=seeded_engine, expire_on_commit=False, future=True)
    with Session_() as session:
        yield session


@pytest.fixture(autouse=True)
def _reset_game_and_question_tables(seeded_engine) -> Iterator[None]:
    """Undo any mutation of game scores or questions/answers between tests."""
    yield
    with seeded_engine.begin() as conn:
        conn.execute(text("UPDATE game SET score_home = NULL, score_away = NULL, notes = NULL"))
        # The wc2026 seed doesn't include questions, but tests insert some.
        conn.execute(text("TRUNCATE TABLE answer, question RESTART IDENTITY CASCADE"))


def _make_user(db: Session, *, name: str, email: str) -> User:
    return register_user(
        db,
        RegistrationData(name=name, email=email, password="hunter222"),
    )


def _record_result(
    db: Session,
    game_id: int,
    home: int,
    away: int,
) -> None:
    """Directly stamp an official result on a seeded game row."""
    game = db.get(Game, game_id)
    assert game is not None
    game.score_home = home
    game.score_away = away
    db.commit()


# ---------------------------------------------------------------------------
# Empty / trivial states
# ---------------------------------------------------------------------------


def test_ladder_with_no_users_is_empty(fresh_db: Session) -> None:
    assert compute_ladder(fresh_db) == []


def test_ladder_omits_excluded_users(fresh_db: Session) -> None:
    """A user flagged ``excluded_from_ladder`` never appears, even with points."""
    alice = _make_user(fresh_db, name="Alice", email="alice@example.com")
    ghost = _make_user(fresh_db, name="Ghost", email="ghost@example.com")

    before = GAME_OPENER_KICKOFF - timedelta(days=1)
    # The excluded user even has a perfect bet - they still must not show up.
    upsert_bet(fresh_db, ghost, game_id=GAME_OPENER_ID, score_home=2, score_away=1, now=before)
    _record_result(fresh_db, GAME_OPENER_ID, 2, 1)

    ghost.excluded_from_ladder = True
    fresh_db.commit()

    after = GAME_OPENER_KICKOFF + timedelta(hours=2)
    ladder = compute_ladder(fresh_db, now=after)
    assert [e.user.id for e in ladder] == [alice.id]


def test_ladder_with_no_bets_lists_users_at_zero(fresh_db: Session) -> None:
    a = _make_user(fresh_db, name="Alice", email="alice@example.com")
    b = _make_user(fresh_db, name="Bob", email="bob@example.com")

    ladder = compute_ladder(fresh_db)
    assert len(ladder) == 2
    assert all(e.total_points == 0 for e in ladder)
    # Tied at 0 -> both share rank 1 (competition ranking) and Alice
    # appears before Bob (alphabetical tiebreak).
    assert ladder[0].rank == 1 and ladder[0].user.id == a.id
    assert ladder[1].rank == 1 and ladder[1].user.id == b.id


# ---------------------------------------------------------------------------
# Scoring from bets
# ---------------------------------------------------------------------------


def test_ladder_awards_points_for_scored_bet(fresh_db: Session) -> None:
    """A bet on a played game with the exact result earns 5 pts."""
    alice = _make_user(fresh_db, name="Alice", email="alice@example.com")
    before = GAME_OPENER_KICKOFF - timedelta(days=1)
    upsert_bet(fresh_db, alice, game_id=GAME_OPENER_ID, score_home=2, score_away=1, now=before)
    _record_result(fresh_db, GAME_OPENER_ID, 2, 1)

    after = GAME_OPENER_KICKOFF + timedelta(hours=2)
    ladder = compute_ladder(fresh_db, now=after)
    assert len(ladder) == 1
    me = ladder[0]
    assert me.total_points == 5
    assert me.bet_points == 5
    assert me.breakdown.exact == 1
    assert me.breakdown.scored == 1


def test_ladder_classifies_bet_outcomes(fresh_db: Session) -> None:
    """Same bet but different official results -> different breakdown buckets."""
    alice = _make_user(fresh_db, name="Alice", email="alice@example.com")
    before = GAME_OPENER_KICKOFF - timedelta(days=1)
    upsert_bet(fresh_db, alice, game_id=GAME_OPENER_ID, score_home=2, score_away=1, now=before)
    upsert_bet(fresh_db, alice, game_id=GAME_2_ID, score_home=1, score_away=0, now=before)
    # Game 1: exact match (5 pts), Game 2: same winner only (2 pts).
    _record_result(fresh_db, GAME_OPENER_ID, 2, 1)
    _record_result(fresh_db, GAME_2_ID, 3, 1)

    after = GAME_OPENER_KICKOFF + timedelta(days=2)
    ladder = compute_ladder(fresh_db, now=after)
    me = ladder[0]
    assert me.breakdown.exact == 1
    assert me.breakdown.tendency == 1
    assert me.total_points == 5 + 2


def test_ladder_does_not_count_pre_kickoff_results(fresh_db: Session) -> None:
    """Result entered before kickoff is invisible until kickoff has happened."""
    alice = _make_user(fresh_db, name="Alice", email="alice@example.com")
    before = GAME_OPENER_KICKOFF - timedelta(days=1)
    upsert_bet(fresh_db, alice, game_id=GAME_OPENER_ID, score_home=2, score_away=1, now=before)
    _record_result(fresh_db, GAME_OPENER_ID, 2, 1)

    ladder = compute_ladder(fresh_db, now=before)  # still before kickoff
    me = ladder[0]
    assert me.total_points == 0
    assert me.breakdown.exact == 0
    assert me.breakdown.upcoming == 1


def test_ladder_marks_bet_as_pending_after_kickoff_without_result(
    fresh_db: Session,
) -> None:
    alice = _make_user(fresh_db, name="Alice", email="alice@example.com")
    before = GAME_OPENER_KICKOFF - timedelta(days=1)
    upsert_bet(fresh_db, alice, game_id=GAME_OPENER_ID, score_home=2, score_away=1, now=before)

    after = GAME_OPENER_KICKOFF + timedelta(hours=2)
    ladder = compute_ladder(fresh_db, now=after)
    me = ladder[0]
    assert me.total_points == 0
    assert me.breakdown.pending == 1
    assert me.breakdown.scored == 0


def test_ladder_counts_miss(fresh_db: Session) -> None:
    """Bet that gets 0 pts is still counted toward 'scored', under 'miss'."""
    alice = _make_user(fresh_db, name="Alice", email="alice@example.com")
    before = GAME_OPENER_KICKOFF - timedelta(days=1)
    upsert_bet(fresh_db, alice, game_id=GAME_OPENER_ID, score_home=3, score_away=0, now=before)
    # Actual: 0-3 -> opposite winner, 0 pts.
    _record_result(fresh_db, GAME_OPENER_ID, 0, 3)

    after = GAME_OPENER_KICKOFF + timedelta(hours=2)
    ladder = compute_ladder(fresh_db, now=after)
    me = ladder[0]
    assert me.total_points == 0
    assert me.breakdown.miss == 1
    assert me.breakdown.scored == 1


# ---------------------------------------------------------------------------
# Scoring from special questions
# ---------------------------------------------------------------------------


def _make_question(
    db: Session,
    *,
    question: str = "Top scorer?",
    correct_answer: str | None = "Mbappe",
    points: int = 10,
    deadline: datetime,
) -> Question:
    q = Question(
        question=question,
        deadline=deadline,
        points=points,
        correct_answer=correct_answer,
    )
    db.add(q)
    db.commit()
    db.refresh(q)
    return q


def test_ladder_awards_points_for_correct_answer(fresh_db: Session) -> None:
    alice = _make_user(fresh_db, name="Alice", email="alice@example.com")
    past = datetime.now(UTC) - timedelta(hours=1)
    q = _make_question(fresh_db, deadline=past)
    fresh_db.add(Answer(user_id=alice.id, question_id=q.id, answer="mbappe"))
    fresh_db.commit()

    ladder = compute_ladder(fresh_db)
    me = ladder[0]
    assert me.answer_points == 10
    assert me.answers_correct == 1
    assert me.answers_total == 1


def test_ladder_skips_question_before_deadline(fresh_db: Session) -> None:
    """Answers are hidden until the question's deadline has passed."""
    alice = _make_user(fresh_db, name="Alice", email="alice@example.com")
    future = datetime.now(UTC) + timedelta(days=10)
    q = _make_question(fresh_db, deadline=future)
    fresh_db.add(Answer(user_id=alice.id, question_id=q.id, answer="mbappe"))
    fresh_db.commit()

    ladder = compute_ladder(fresh_db)
    me = ladder[0]
    assert me.answer_points == 0
    assert me.answers_total == 0


def test_ladder_skips_question_without_correct_answer(fresh_db: Session) -> None:
    """Admin hasn't decided yet -> no scoring even after deadline."""
    alice = _make_user(fresh_db, name="Alice", email="alice@example.com")
    past = datetime.now(UTC) - timedelta(hours=1)
    q = _make_question(fresh_db, deadline=past, correct_answer=None)
    fresh_db.add(Answer(user_id=alice.id, question_id=q.id, answer="anything"))
    fresh_db.commit()

    ladder = compute_ladder(fresh_db)
    assert ladder[0].answer_points == 0
    assert ladder[0].answers_total == 0


def test_ladder_combines_bet_and_answer_points(fresh_db: Session) -> None:
    alice = _make_user(fresh_db, name="Alice", email="alice@example.com")
    # Bet: exact result, 5 pts
    before = GAME_OPENER_KICKOFF - timedelta(days=1)
    upsert_bet(fresh_db, alice, game_id=GAME_OPENER_ID, score_home=2, score_away=1, now=before)
    _record_result(fresh_db, GAME_OPENER_ID, 2, 1)
    # Question: 10 pts
    past = datetime.now(UTC) - timedelta(hours=1)
    q = _make_question(fresh_db, deadline=past, points=10)
    fresh_db.add(Answer(user_id=alice.id, question_id=q.id, answer="Mbappe"))
    fresh_db.commit()

    after = GAME_OPENER_KICKOFF + timedelta(hours=2)
    ladder = compute_ladder(fresh_db, now=after)
    assert ladder[0].total_points == 15
    assert ladder[0].bet_points == 5
    assert ladder[0].answer_points == 10


# ---------------------------------------------------------------------------
# Ordering & ranks
# ---------------------------------------------------------------------------


def test_ladder_sorts_by_points_desc(fresh_db: Session) -> None:
    high = _make_user(fresh_db, name="High", email="h@example.com")
    low = _make_user(fresh_db, name="Low", email="l@example.com")
    before = GAME_OPENER_KICKOFF - timedelta(days=1)
    upsert_bet(fresh_db, high, game_id=GAME_OPENER_ID, score_home=2, score_away=1, now=before)
    upsert_bet(fresh_db, low, game_id=GAME_OPENER_ID, score_home=4, score_away=2, now=before)
    _record_result(fresh_db, GAME_OPENER_ID, 2, 1)  # exact for High, miss for Low (2-1 winner)

    after = GAME_OPENER_KICKOFF + timedelta(hours=2)
    ladder = compute_ladder(fresh_db, now=after)
    # Low actually scored 2 pts (correct winner), High scored 5 pts (exact).
    assert [e.user.name for e in ladder] == ["High", "Low"]
    assert ladder[0].rank == 1
    assert ladder[1].rank == 2


def test_ladder_competition_ranking_for_ties(fresh_db: Session) -> None:
    """Three players tied at 5 pts share rank 1; the next is rank 4."""
    a = _make_user(fresh_db, name="Alice", email="a@example.com")
    b = _make_user(fresh_db, name="Bob", email="b@example.com")
    c = _make_user(fresh_db, name="Carol", email="c@example.com")
    d = _make_user(fresh_db, name="Dave", email="d@example.com")
    before = GAME_OPENER_KICKOFF - timedelta(days=1)
    for u in (a, b, c):
        upsert_bet(fresh_db, u, game_id=GAME_OPENER_ID, score_home=2, score_away=1, now=before)
    upsert_bet(fresh_db, d, game_id=GAME_OPENER_ID, score_home=0, score_away=0, now=before)  # miss
    _record_result(fresh_db, GAME_OPENER_ID, 2, 1)

    after = GAME_OPENER_KICKOFF + timedelta(hours=2)
    ladder = compute_ladder(fresh_db, now=after)
    by_name = {e.user.name: e for e in ladder}
    assert by_name["Alice"].rank == 1
    assert by_name["Bob"].rank == 1
    assert by_name["Carol"].rank == 1
    assert by_name["Dave"].rank == 4


def test_ladder_exact_count_breaks_ties(fresh_db: Session) -> None:
    """Same total points, more exact-results sorts higher."""
    a = _make_user(fresh_db, name="Alice", email="a@example.com")
    b = _make_user(fresh_db, name="Bob", email="b@example.com")
    before = GAME_OPENER_KICKOFF - timedelta(days=1)
    # Alice: one exact (5 pts)
    upsert_bet(fresh_db, a, game_id=GAME_OPENER_ID, score_home=2, score_away=1, now=before)
    # Bob: one spread + one tendency = 3 + 2 = 5 pts. Same total, 0 exacts.
    upsert_bet(
        fresh_db, b, game_id=GAME_OPENER_ID, score_home=3, score_away=2, now=before
    )  # spread 1, actual 1 -> 3
    upsert_bet(
        fresh_db, b, game_id=GAME_2_ID, score_home=4, score_away=1, now=before
    )  # winner home, tendency -> 2
    _record_result(fresh_db, GAME_OPENER_ID, 2, 1)
    _record_result(fresh_db, GAME_2_ID, 2, 1)

    after = GAME_OPENER_KICKOFF + timedelta(days=2)
    ladder = compute_ladder(fresh_db, now=after)
    assert [e.user.name for e in ladder[:2]] == ["Alice", "Bob"]
    assert ladder[0].total_points == 5
    assert ladder[1].total_points == 5
    # Alice ranks 1 (exact=1), Bob ranks 2 (exact=0).
    assert ladder[0].rank == 1
    assert ladder[1].rank == 2
