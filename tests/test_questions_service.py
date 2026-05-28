"""Unit tests for :mod:`app.services.questions`."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from app.models import Answer, Question, User
from app.services.questions import (
    DeadlinePassed,
    InvalidQuestionData,
    QuestionNotFound,
    create_question,
    delete_answer,
    delete_question,
    get_question_view_for_user,
    list_all_questions,
    list_questions_for_user,
    update_question,
    upsert_answer,
)
from app.services.users import RegistrationData, register_user


@pytest.fixture()
def fresh_db(clean_user_tables: None, seeded_engine) -> Iterator[Session]:
    Session_ = sessionmaker(bind=seeded_engine, expire_on_commit=False, future=True)
    with Session_() as session:
        yield session


@pytest.fixture(autouse=True)
def _reset_question_tables(seeded_engine) -> Iterator[None]:
    """Wipe questions/answers after each test (seed file has none)."""
    yield
    with seeded_engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE answer, question RESTART IDENTITY CASCADE"))


def _make_user(db: Session, *, name: str, email: str) -> User:
    return register_user(
        db,
        RegistrationData(name=name, email=email, password="hunter222"),
    )


def _future(days: int = 7) -> datetime:
    return datetime.now(UTC) + timedelta(days=days)


def _past(hours: int = 1) -> datetime:
    return datetime.now(UTC) - timedelta(hours=hours)


# ---------------------------------------------------------------------------
# create_question
# ---------------------------------------------------------------------------


def test_create_question_basic(fresh_db: Session) -> None:
    q = create_question(
        fresh_db,
        text="Who scores the most goals?",
        deadline=_future(),
        points=10,
    )
    assert q.id is not None
    assert q.question == "Who scores the most goals?"
    assert q.points == 10
    assert q.correct_answer is None
    assert q.deadline.tzinfo is not None  # always tz-aware UTC


def test_create_question_stores_correct_answer(fresh_db: Session) -> None:
    q = create_question(
        fresh_db,
        text="Top scorer?",
        deadline=_future(),
        points=10,
        correct_answer="Mbappe,Mbappé,Kylian Mbappe",
    )
    assert q.correct_answer == "Mbappe,Mbappé,Kylian Mbappe"


def test_create_question_normalises_blank_correct_answer(fresh_db: Session) -> None:
    q = create_question(
        fresh_db,
        text="Top scorer?",
        deadline=_future(),
        points=10,
        correct_answer="   ",
    )
    assert q.correct_answer is None


@pytest.mark.parametrize("text_input", ["", "  ", "  hi  "])
def test_create_question_rejects_short_text(fresh_db: Session, text_input: str) -> None:
    with pytest.raises(InvalidQuestionData):
        create_question(fresh_db, text=text_input, deadline=_future(), points=10)


@pytest.mark.parametrize("pts", [0, -1, 1000])
def test_create_question_rejects_bad_points(fresh_db: Session, pts: int) -> None:
    with pytest.raises(InvalidQuestionData):
        create_question(fresh_db, text="A valid question?", deadline=_future(), points=pts)


def test_create_question_converts_naive_deadline_to_utc(fresh_db: Session) -> None:
    naive = datetime.now() + timedelta(days=1)
    q = create_question(fresh_db, text="A valid question?", deadline=naive, points=5)
    assert q.deadline.tzinfo is UTC


# ---------------------------------------------------------------------------
# update_question
# ---------------------------------------------------------------------------


def test_update_question_replaces_fields(fresh_db: Session) -> None:
    q = create_question(fresh_db, text="Initial question?", deadline=_future(), points=5)
    updated = update_question(
        fresh_db,
        q.id,
        text="Updated question?",
        deadline=_future(days=14),
        points=20,
        correct_answer="answer-a, answer-b",
    )
    assert updated.id == q.id
    assert updated.question == "Updated question?"
    assert updated.points == 20
    assert updated.correct_answer == "answer-a, answer-b"


def test_update_question_unknown_id(fresh_db: Session) -> None:
    with pytest.raises(QuestionNotFound):
        update_question(fresh_db, 99999, text="A valid question?", deadline=_future(), points=5)


def test_update_question_validates(fresh_db: Session) -> None:
    q = create_question(fresh_db, text="A valid question?", deadline=_future(), points=5)
    with pytest.raises(InvalidQuestionData):
        update_question(fresh_db, q.id, text="A valid question?", deadline=_future(), points=5000)


# ---------------------------------------------------------------------------
# delete_question
# ---------------------------------------------------------------------------


def test_delete_question_removes_row_and_answers(fresh_db: Session) -> None:
    alice = _make_user(fresh_db, name="Alice", email="a@example.com")
    q = create_question(fresh_db, text="A valid question?", deadline=_future(), points=5)
    upsert_answer(fresh_db, alice, question_id=q.id, answer_text="A")
    delete_question(fresh_db, q.id)
    assert fresh_db.get(Question, q.id) is None
    assert fresh_db.query(Answer).filter_by(question_id=q.id).count() == 0


def test_delete_question_idempotent_when_missing(fresh_db: Session) -> None:
    """No exception for an already-gone id."""
    delete_question(fresh_db, 99999)


# ---------------------------------------------------------------------------
# upsert_answer / delete_answer
# ---------------------------------------------------------------------------


def test_upsert_answer_inserts(fresh_db: Session) -> None:
    alice = _make_user(fresh_db, name="Alice", email="a@example.com")
    q = create_question(fresh_db, text="A valid question?", deadline=_future(), points=5)
    ans = upsert_answer(fresh_db, alice, question_id=q.id, answer_text="My guess")
    assert ans.id is not None
    assert ans.answer == "My guess"
    assert ans.user_id == alice.id
    assert ans.question_id == q.id


def test_upsert_answer_updates_existing(fresh_db: Session) -> None:
    alice = _make_user(fresh_db, name="Alice", email="a@example.com")
    q = create_question(fresh_db, text="A valid question?", deadline=_future(), points=5)
    first = upsert_answer(fresh_db, alice, question_id=q.id, answer_text="A")
    second = upsert_answer(fresh_db, alice, question_id=q.id, answer_text="B")
    assert first.id == second.id
    assert second.answer == "B"
    assert fresh_db.query(Answer).filter_by(user_id=alice.id).count() == 1


def test_upsert_answer_trims_whitespace(fresh_db: Session) -> None:
    alice = _make_user(fresh_db, name="Alice", email="a@example.com")
    q = create_question(fresh_db, text="A valid question?", deadline=_future(), points=5)
    ans = upsert_answer(fresh_db, alice, question_id=q.id, answer_text="  hello  ")
    assert ans.answer == "hello"


def test_upsert_answer_rejects_empty(fresh_db: Session) -> None:
    alice = _make_user(fresh_db, name="Alice", email="a@example.com")
    q = create_question(fresh_db, text="A valid question?", deadline=_future(), points=5)
    with pytest.raises(InvalidQuestionData):
        upsert_answer(fresh_db, alice, question_id=q.id, answer_text="   ")


def test_upsert_answer_rejects_after_deadline(fresh_db: Session) -> None:
    alice = _make_user(fresh_db, name="Alice", email="a@example.com")
    q = create_question(fresh_db, text="A valid question?", deadline=_past(), points=5)
    with pytest.raises(DeadlinePassed):
        upsert_answer(fresh_db, alice, question_id=q.id, answer_text="A")


def test_upsert_answer_unknown_question(fresh_db: Session) -> None:
    alice = _make_user(fresh_db, name="Alice", email="a@example.com")
    with pytest.raises(QuestionNotFound):
        upsert_answer(fresh_db, alice, question_id=99999, answer_text="A")


def test_delete_answer_removes_it(fresh_db: Session) -> None:
    alice = _make_user(fresh_db, name="Alice", email="a@example.com")
    q = create_question(fresh_db, text="A valid question?", deadline=_future(), points=5)
    upsert_answer(fresh_db, alice, question_id=q.id, answer_text="A")
    delete_answer(fresh_db, alice, q.id)
    assert fresh_db.query(Answer).filter_by(user_id=alice.id).count() == 0


def test_delete_answer_missing_is_noop(fresh_db: Session) -> None:
    alice = _make_user(fresh_db, name="Alice", email="a@example.com")
    q = create_question(fresh_db, text="A valid question?", deadline=_future(), points=5)
    delete_answer(fresh_db, alice, q.id)


def test_delete_answer_rejects_after_deadline(fresh_db: Session) -> None:
    alice = _make_user(fresh_db, name="Alice", email="a@example.com")
    q = create_question(fresh_db, text="A valid question?", deadline=_past(), points=5)
    with pytest.raises(DeadlinePassed):
        delete_answer(fresh_db, alice, q.id)


# ---------------------------------------------------------------------------
# Reads
# ---------------------------------------------------------------------------


def test_list_for_user_returns_one_entry_per_question(fresh_db: Session) -> None:
    """One entry per question, sorted by deadline ascending (soonest first)."""
    alice = _make_user(fresh_db, name="Alice", email="a@example.com")
    q_late = create_question(fresh_db, text="Question late?", deadline=_future(days=14), points=5)
    q_early = create_question(fresh_db, text="Question early?", deadline=_future(days=2), points=10)
    entries = list_questions_for_user(fresh_db, alice)
    assert [e.question.id for e in entries] == [q_early.id, q_late.id]
    assert all(e.can_answer for e in entries)
    assert all(e.answer is None for e in entries)
    assert all(e.points_earned == 0 for e in entries)


def test_list_for_user_hides_correct_answer_before_deadline(
    fresh_db: Session,
) -> None:
    alice = _make_user(fresh_db, name="Alice", email="a@example.com")
    create_question(
        fresh_db,
        text="A valid question?",
        deadline=_future(),
        points=5,
        correct_answer="answer",
    )
    entries = list_questions_for_user(fresh_db, alice)
    assert entries[0].correct_answer_display is None


def test_list_for_user_reveals_correct_answer_after_deadline(
    fresh_db: Session,
) -> None:
    alice = _make_user(fresh_db, name="Alice", email="a@example.com")
    create_question(
        fresh_db,
        text="A valid question?",
        deadline=_past(),
        points=5,
        correct_answer="Mbappe,Mbappé",  # first variant becomes the display form
    )
    entries = list_questions_for_user(fresh_db, alice)
    assert entries[0].correct_answer_display == "Mbappe"


def test_list_for_user_scores_correct_answer(fresh_db: Session) -> None:
    alice = _make_user(fresh_db, name="Alice", email="a@example.com")
    # Use a future deadline for the upsert, then move it into the past.
    q = create_question(
        fresh_db, text="Top scorer?", deadline=_future(), points=10, correct_answer="Mbappe"
    )
    upsert_answer(fresh_db, alice, question_id=q.id, answer_text="mbappe")
    q.deadline = _past()
    fresh_db.commit()
    entries = list_questions_for_user(fresh_db, alice)
    assert entries[0].points_earned == 10


def test_list_for_user_does_not_leak_other_users_answers(
    fresh_db: Session,
) -> None:
    alice = _make_user(fresh_db, name="Alice", email="a@example.com")
    bob = _make_user(fresh_db, name="Bob", email="b@example.com")
    q = create_question(fresh_db, text="A valid question?", deadline=_future(), points=5)
    upsert_answer(fresh_db, bob, question_id=q.id, answer_text="Bob's guess")
    entries = list_questions_for_user(fresh_db, alice)
    assert entries[0].answer is None


def test_get_question_view_for_user_round_trip(fresh_db: Session) -> None:
    alice = _make_user(fresh_db, name="Alice", email="a@example.com")
    q = create_question(fresh_db, text="A valid question?", deadline=_future(), points=5)
    upsert_answer(fresh_db, alice, question_id=q.id, answer_text="A")
    view = get_question_view_for_user(fresh_db, alice, q.id)
    assert view.question.id == q.id
    assert view.answer is not None
    assert view.answer.answer == "A"
    assert view.can_answer is True


def test_list_all_questions_includes_answer_counts(fresh_db: Session) -> None:
    alice = _make_user(fresh_db, name="Alice", email="a@example.com")
    bob = _make_user(fresh_db, name="Bob", email="b@example.com")
    q1 = create_question(fresh_db, text="Question one?", deadline=_future(), points=5)
    q2 = create_question(fresh_db, text="Question two?", deadline=_future(days=2), points=5)
    upsert_answer(fresh_db, alice, question_id=q1.id, answer_text="A")
    upsert_answer(fresh_db, bob, question_id=q1.id, answer_text="B")
    rows = list_all_questions(fresh_db)
    by_id = {r.question.id: r for r in rows}
    assert by_id[q1.id].answer_count == 2
    assert by_id[q2.id].answer_count == 0
