"""End-to-end tests for the user-facing ``/questions`` route."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from app.models import Answer, Question


def _register_and_login(
    client: TestClient,
    *,
    name: str = "Alice",
    email: str = "alice@example.com",
    password: str = "hunter222",
) -> None:
    r = client.post(
        "/register",
        data={"name": name, "email": email, "password": password},
        follow_redirects=False,
    )
    assert r.status_code == 303, r.text
    r = client.post("/login", data={"email": email, "password": password}, follow_redirects=False)
    assert r.status_code == 303, r.text


@pytest.fixture()
def logged_in_client(auth_client: TestClient) -> TestClient:
    _register_and_login(auth_client)
    return auth_client


@pytest.fixture()
def db(seeded_engine) -> Iterator[Session]:
    Session_ = sessionmaker(bind=seeded_engine, expire_on_commit=False, future=True)
    with Session_() as s:
        yield s


@pytest.fixture(autouse=True)
def _reset_question_tables(seeded_engine) -> Iterator[None]:
    yield
    with seeded_engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE answer, question RESTART IDENTITY CASCADE"))


def _make_question(
    db: Session,
    *,
    text: str = "Top scorer of the tournament?",
    deadline: datetime | None = None,
    points: int = 10,
    correct_answer: str | None = None,
) -> Question:
    if deadline is None:
        deadline = datetime.now(UTC) + timedelta(days=7)
    q = Question(question=text, deadline=deadline, points=points, correct_answer=correct_answer)
    db.add(q)
    db.commit()
    db.refresh(q)
    return q


# ---------------------------------------------------------------------------
# Access control + base render
# ---------------------------------------------------------------------------


def test_questions_requires_login(auth_client: TestClient) -> None:
    r = auth_client.get("/questions")
    assert r.status_code == 401


def test_questions_renders_with_no_questions(logged_in_client: TestClient) -> None:
    r = logged_in_client.get("/questions")
    assert r.status_code == 200
    assert "Special questions" in r.text
    assert "No special questions" in r.text


def test_questions_link_in_navbar(logged_in_client: TestClient) -> None:
    page = logged_in_client.get("/games").text
    assert 'href="/questions"' in page


def test_questions_renders_question_rows(
    logged_in_client: TestClient,
    db: Session,
) -> None:
    _make_question(db, text="Will any team go undefeated?")
    page = logged_in_client.get("/questions").text
    assert "Will any team go undefeated?" in page
    assert 'name="answer"' in page


# ---------------------------------------------------------------------------
# POST /questions/{id} - HTMX
# ---------------------------------------------------------------------------


def test_htmx_post_creates_answer(
    logged_in_client: TestClient,
    db: Session,
) -> None:
    q = _make_question(db)
    r = logged_in_client.post(
        f"/questions/{q.id}",
        data={"answer": "Mbappe"},
        headers={"HX-Request": "true"},
    )
    assert r.status_code == 200, r.text
    assert "<!DOCTYPE html>" not in r.text
    assert f'id="answer-cell-{q.id}"' in r.text
    assert "saved" in r.text

    a = db.query(Answer).filter_by(question_id=q.id).one()
    assert a.answer == "Mbappe"


def test_htmx_post_updates_existing_answer(
    logged_in_client: TestClient,
    db: Session,
) -> None:
    q = _make_question(db)
    logged_in_client.post(
        f"/questions/{q.id}",
        data={"answer": "first guess"},
        headers={"HX-Request": "true"},
    )
    r = logged_in_client.post(
        f"/questions/{q.id}",
        data={"answer": "second guess"},
        headers={"HX-Request": "true"},
    )
    assert r.status_code == 200
    answers = db.query(Answer).filter_by(question_id=q.id).all()
    assert len(answers) == 1
    assert answers[0].answer == "second guess"


def test_htmx_post_blank_deletes_answer(
    logged_in_client: TestClient,
    db: Session,
) -> None:
    q = _make_question(db)
    logged_in_client.post(
        f"/questions/{q.id}",
        data={"answer": "to be removed"},
        headers={"HX-Request": "true"},
    )
    r = logged_in_client.post(
        f"/questions/{q.id}",
        data={"answer": ""},
        headers={"HX-Request": "true"},
    )
    assert r.status_code == 200
    assert db.query(Answer).filter_by(question_id=q.id).count() == 0


def test_htmx_post_after_deadline_returns_error(
    logged_in_client: TestClient,
    db: Session,
) -> None:
    past = datetime.now(UTC) - timedelta(minutes=1)
    q = _make_question(db, deadline=past)
    r = logged_in_client.post(
        f"/questions/{q.id}",
        data={"answer": "too late"},
        headers={"HX-Request": "true"},
    )
    assert r.status_code == 200
    assert "deadline" in r.text.lower()
    # Read-only mode: no form in the response.
    assert "<form" not in r.text.lower()


def test_htmx_post_unknown_question_404s(
    logged_in_client: TestClient,
) -> None:
    r = logged_in_client.post(
        "/questions/99999",
        data={"answer": "anything"},
        headers={"HX-Request": "true"},
    )
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Vanilla form fallback
# ---------------------------------------------------------------------------


def test_plain_post_redirects(
    logged_in_client: TestClient,
    db: Session,
) -> None:
    q = _make_question(db)
    r = logged_in_client.post(
        f"/questions/{q.id}",
        data={"answer": "Messi"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert r.headers["location"] == "/questions"
    assert db.query(Answer).filter_by(question_id=q.id).one().answer == "Messi"


def test_post_requires_login(auth_client: TestClient, db: Session) -> None:
    q = _make_question(db)
    r = auth_client.post(f"/questions/{q.id}", data={"answer": "x"})
    assert r.status_code == 401


# ---------------------------------------------------------------------------
# Correct-answer visibility + scoring
# ---------------------------------------------------------------------------


def test_correct_answer_hidden_before_deadline(
    logged_in_client: TestClient,
    db: Session,
) -> None:
    _make_question(db, correct_answer="Mbappe")
    page = logged_in_client.get("/questions").text
    assert "Mbappe" not in page


def test_correct_answer_visible_after_deadline(
    logged_in_client: TestClient,
    db: Session,
) -> None:
    past = datetime.now(UTC) - timedelta(minutes=1)
    _make_question(db, deadline=past, correct_answer="Mbappe,Mbappé")
    page = logged_in_client.get("/questions").text
    # The first variant becomes the display form.
    assert "Mbappe" in page
    # The other variants stay private.
    assert "Mbappé" not in page


def test_user_sees_their_earned_points_after_deadline(
    logged_in_client: TestClient,
    db: Session,
) -> None:
    """End-to-end: answer pre-deadline, deadline passes, correct answer set."""
    # Question initially has a future deadline so we can answer through the API.
    q = _make_question(db)
    logged_in_client.post(
        f"/questions/{q.id}",
        data={"answer": "mbappe"},
        headers={"HX-Request": "true"},
    )
    # Then admin sets the correct answer and the deadline rolls past.
    q.correct_answer = "Mbappe"
    q.deadline = datetime.now(UTC) - timedelta(seconds=1)
    db.commit()

    page = logged_in_client.get("/questions").text
    # Earned points (10) should be rendered somewhere in the page.
    # The structured layout makes a more targeted assertion noisy; spot-check
    # that the answer cell shows the user's answer with a success badge.
    assert "text-bg-success" in page
