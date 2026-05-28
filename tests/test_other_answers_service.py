"""Unit tests for :func:`app.services.questions.list_other_answers_for_question`."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from app.models import User
from app.services.questions import (
    QuestionNotFound,
    create_question,
    list_other_answers_for_question,
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
# Visibility gate
# ---------------------------------------------------------------------------


def test_locked_before_deadline(fresh_db: Session) -> None:
    alice = _make_user(fresh_db, name="Alice", email="a@example.com")
    bob = _make_user(fresh_db, name="Bob", email="b@example.com")
    q = create_question(fresh_db, text="Top scorer?", deadline=_future(), points=10)
    upsert_answer(fresh_db, bob, question_id=q.id, answer_text="Messi")

    view = list_other_answers_for_question(fresh_db, alice, q.id)
    assert view.can_view is False
    assert view.others == []
    assert view.question.id == q.id


def test_unlocks_after_deadline(fresh_db: Session) -> None:
    alice = _make_user(fresh_db, name="Alice", email="a@example.com")
    bob = _make_user(fresh_db, name="Bob", email="b@example.com")
    q = create_question(fresh_db, text="Top scorer?", deadline=_future(), points=10)
    upsert_answer(fresh_db, bob, question_id=q.id, answer_text="Messi")

    q.deadline = _past()
    fresh_db.commit()

    view = list_other_answers_for_question(fresh_db, alice, q.id)
    assert view.can_view is True
    assert [o.user.name for o in view.others] == ["Bob"]


def test_unknown_question_raises(fresh_db: Session) -> None:
    alice = _make_user(fresh_db, name="Alice", email="a@example.com")
    with pytest.raises(QuestionNotFound):
        list_other_answers_for_question(fresh_db, alice, 99999)


# ---------------------------------------------------------------------------
# Own-user exclusion + empty list
# ---------------------------------------------------------------------------


def test_excludes_requesting_user(fresh_db: Session) -> None:
    alice = _make_user(fresh_db, name="Alice", email="a@example.com")
    bob = _make_user(fresh_db, name="Bob", email="b@example.com")
    q = create_question(fresh_db, text="A valid question?", deadline=_future(), points=10)
    upsert_answer(fresh_db, alice, question_id=q.id, answer_text="alice-guess")
    upsert_answer(fresh_db, bob, question_id=q.id, answer_text="bob-guess")
    q.deadline = _past()
    fresh_db.commit()

    view = list_other_answers_for_question(fresh_db, alice, q.id)
    assert [o.user.name for o in view.others] == ["Bob"]


def test_empty_when_nobody_else_answered(fresh_db: Session) -> None:
    alice = _make_user(fresh_db, name="Alice", email="a@example.com")
    q = create_question(fresh_db, text="A valid question?", deadline=_future(), points=10)
    upsert_answer(fresh_db, alice, question_id=q.id, answer_text="alice-guess")
    q.deadline = _past()
    fresh_db.commit()

    view = list_other_answers_for_question(fresh_db, alice, q.id)
    assert view.can_view is True
    assert view.others == []


# ---------------------------------------------------------------------------
# Scoring + ordering
# ---------------------------------------------------------------------------


def test_points_zero_when_no_correct_answer_yet(fresh_db: Session) -> None:
    alice = _make_user(fresh_db, name="Alice", email="a@example.com")
    bob = _make_user(fresh_db, name="Bob", email="b@example.com")
    q = create_question(fresh_db, text="A valid question?", deadline=_future(), points=10)
    upsert_answer(fresh_db, bob, question_id=q.id, answer_text="anything")
    q.deadline = _past()
    fresh_db.commit()

    view = list_other_answers_for_question(fresh_db, alice, q.id)
    assert [(o.user.name, o.points) for o in view.others] == [("Bob", 0)]


def test_sorts_by_points_desc_then_name_asc(fresh_db: Session) -> None:
    """Correct answers first, then alphabetical for ties."""
    alice = _make_user(fresh_db, name="Alice", email="a@example.com")
    bob = _make_user(fresh_db, name="Bob", email="b@example.com")
    cara = _make_user(fresh_db, name="Cara", email="c@example.com")
    dora = _make_user(fresh_db, name="Dora", email="d@example.com")
    q = create_question(fresh_db, text="A valid question?", deadline=_future(), points=10)
    # Cara + Dora answer correctly, Bob wrong.
    upsert_answer(fresh_db, bob, question_id=q.id, answer_text="wrong")
    upsert_answer(fresh_db, cara, question_id=q.id, answer_text="Mbappe")
    upsert_answer(fresh_db, dora, question_id=q.id, answer_text="mbappe")
    q.correct_answer = "Mbappe,Mbappé"
    q.deadline = _past()
    fresh_db.commit()

    view = list_other_answers_for_question(fresh_db, alice, q.id)
    assert [(o.user.name, o.points) for o in view.others] == [
        ("Cara", 10),
        ("Dora", 10),
        ("Bob", 0),
    ]


def test_name_tiebreak_is_case_insensitive(fresh_db: Session) -> None:
    alice = _make_user(fresh_db, name="Alice", email="a@example.com")
    zara = _make_user(fresh_db, name="Zara", email="z@example.com")
    bobby = _make_user(fresh_db, name="bobby", email="b@example.com")
    q = create_question(fresh_db, text="A valid question?", deadline=_future(), points=10)
    upsert_answer(fresh_db, zara, question_id=q.id, answer_text="x")
    upsert_answer(fresh_db, bobby, question_id=q.id, answer_text="x")
    q.deadline = _past()
    fresh_db.commit()

    view = list_other_answers_for_question(fresh_db, alice, q.id)
    assert [o.user.name for o in view.others] == ["bobby", "Zara"]
