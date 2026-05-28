"""End-to-end tests for /admin/questions CRUD endpoints."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from app.models import Answer, Question, User


def _register_and_login(
    client: TestClient,
    *,
    name: str,
    email: str,
    password: str = "hunter222",
) -> None:
    r = client.post(
        "/register",
        data={"name": name, "email": email, "password": password},
        follow_redirects=False,
    )
    assert r.status_code == 303
    r = client.post("/login", data={"email": email, "password": password}, follow_redirects=False)
    assert r.status_code == 303


def _promote(db: Session, email: str) -> None:
    user = db.query(User).filter(User.email == email).one()
    user.role = User.ROLE_ADMIN
    db.commit()


@pytest.fixture()
def db(seeded_engine) -> Iterator[Session]:
    Session_ = sessionmaker(bind=seeded_engine, expire_on_commit=False, future=True)
    with Session_() as s:
        yield s


@pytest.fixture()
def admin_client(auth_client: TestClient, db: Session) -> TestClient:
    _register_and_login(auth_client, name="Admin", email="admin@example.com")
    _promote(db, "admin@example.com")
    return auth_client


@pytest.fixture()
def non_admin_client(auth_client: TestClient) -> TestClient:
    _register_and_login(auth_client, name="Pat", email="pat@example.com")
    return auth_client


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


def _dt_local(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M")


# ---------------------------------------------------------------------------
# Access control
# ---------------------------------------------------------------------------


def test_admin_questions_requires_login(auth_client: TestClient) -> None:
    r = auth_client.get("/admin/questions")
    assert r.status_code == 401


def test_admin_questions_rejects_non_admin(non_admin_client: TestClient) -> None:
    r = non_admin_client.get("/admin/questions")
    assert r.status_code == 403


def test_admin_create_requires_admin(non_admin_client: TestClient) -> None:
    r = non_admin_client.post(
        "/admin/questions/new",
        data={
            "question": "Anything?",
            "deadline": _dt_local(datetime.now(UTC) + timedelta(days=1)),
            "points": "5",
        },
    )
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# GET /admin/questions
# ---------------------------------------------------------------------------


def test_admin_questions_page_renders(admin_client: TestClient) -> None:
    r = admin_client.get("/admin/questions")
    assert r.status_code == 200
    assert "Special questions" in r.text
    # New-question form is on the page.
    assert 'action="/admin/questions/new"' in r.text


def test_admin_questions_lists_existing(
    admin_client: TestClient,
    db: Session,
) -> None:
    _make_question(db, text="A specific seed question?")
    page = admin_client.get("/admin/questions").text
    assert "A specific seed question?" in page
    assert 'id="admin-question-1"' in page


# ---------------------------------------------------------------------------
# POST /admin/questions/new
# ---------------------------------------------------------------------------


def test_admin_create_question(admin_client: TestClient, db: Session) -> None:
    deadline = datetime.now(UTC) + timedelta(days=5)
    r = admin_client.post(
        "/admin/questions/new",
        data={
            "question": "How many own goals in the group stage?",
            "deadline": _dt_local(deadline),
            "points": "15",
            "correct_answer": "",
        },
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert r.headers["location"] == "/admin/questions?saved=created"
    q = db.query(Question).one()
    assert q.question == "How many own goals in the group stage?"
    assert q.points == 15
    assert q.correct_answer is None
    # Deadline survives the round-trip and is stored as tz-aware UTC.
    assert q.deadline.tzinfo is not None


def test_admin_create_rejects_short_text(
    admin_client: TestClient,
    db: Session,
) -> None:
    deadline = datetime.now(UTC) + timedelta(days=5)
    r = admin_client.post(
        "/admin/questions/new",
        data={
            "question": "x",
            "deadline": _dt_local(deadline),
            "points": "5",
        },
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert "/admin/questions?error=" in r.headers["location"]
    assert db.query(Question).count() == 0


def test_admin_create_rejects_invalid_deadline(
    admin_client: TestClient,
    db: Session,
) -> None:
    r = admin_client.post(
        "/admin/questions/new",
        data={
            "question": "Is the deadline a real date?",
            "deadline": "not-a-date",
            "points": "5",
        },
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert "error=" in r.headers["location"]
    assert db.query(Question).count() == 0


# ---------------------------------------------------------------------------
# POST /admin/questions/{id} - HTMX update
# ---------------------------------------------------------------------------


def test_htmx_update_question(admin_client: TestClient, db: Session) -> None:
    q = _make_question(db, text="Original?")
    new_deadline = datetime.now(UTC) + timedelta(days=21)
    r = admin_client.post(
        f"/admin/questions/{q.id}",
        data={
            "question": "Updated text?",
            "deadline": _dt_local(new_deadline),
            "points": "25",
            "correct_answer": "answer-a, answer-b",
        },
        headers={"HX-Request": "true"},
    )
    assert r.status_code == 200
    assert "<!DOCTYPE html>" not in r.text
    assert f'id="admin-question-{q.id}"' in r.text
    assert "saved" in r.text

    db.expire_all()
    q2 = db.get(Question, q.id)
    assert q2 is not None
    assert q2.question == "Updated text?"
    assert q2.points == 25
    assert q2.correct_answer == "answer-a, answer-b"


def test_htmx_update_validation_returns_error(
    admin_client: TestClient,
    db: Session,
) -> None:
    q = _make_question(db)
    r = admin_client.post(
        f"/admin/questions/{q.id}",
        data={
            "question": "Valid question?",
            "deadline": _dt_local(datetime.now(UTC) + timedelta(days=2)),
            "points": "5000",  # too high
            "correct_answer": "",
        },
        headers={"HX-Request": "true"},
    )
    assert r.status_code == 200
    assert "between" in r.text.lower()


def test_update_unknown_question_404s(admin_client: TestClient) -> None:
    r = admin_client.post(
        "/admin/questions/99999",
        data={
            "question": "Hello?",
            "deadline": _dt_local(datetime.now(UTC) + timedelta(days=1)),
            "points": "5",
            "correct_answer": "",
        },
        headers={"HX-Request": "true"},
    )
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# POST /admin/questions/{id}/delete
# ---------------------------------------------------------------------------


def test_delete_question_removes_row(
    admin_client: TestClient,
    db: Session,
) -> None:
    q = _make_question(db)
    qid = q.id
    r = admin_client.post(
        f"/admin/questions/{qid}/delete",
        headers={"HX-Request": "true"},
    )
    assert r.status_code == 200
    assert r.text == "" or r.text.strip() == ""
    db.expire_all()
    assert db.get(Question, qid) is None


def test_delete_question_cascades_to_answers(
    auth_client: TestClient,
    db: Session,
) -> None:
    """Deleting a question also removes any user answers on it."""
    # Create an answer first.
    _register_and_login(auth_client, name="Alice", email="alice@example.com")
    q = _make_question(db)
    auth_client.post(f"/questions/{q.id}", data={"answer": "guess"}, headers={"HX-Request": "true"})
    assert db.query(Answer).filter_by(question_id=q.id).count() == 1
    auth_client.post("/logout")

    # Now log in as admin and delete the question.
    _register_and_login(auth_client, name="Admin", email="admin@example.com")
    _promote(db, "admin@example.com")
    r = auth_client.post(f"/admin/questions/{q.id}/delete", headers={"HX-Request": "true"})
    assert r.status_code == 200
    assert db.query(Answer).filter_by(question_id=q.id).count() == 0


def test_delete_unknown_question_is_idempotent(
    admin_client: TestClient,
) -> None:
    r = admin_client.post(
        "/admin/questions/99999/delete",
        headers={"HX-Request": "true"},
    )
    # Returns 200 (no-op) rather than 404 - the row is gone either way.
    assert r.status_code == 200


def test_plain_delete_redirects(admin_client: TestClient, db: Session) -> None:
    q = _make_question(db)
    qid = q.id
    r = admin_client.post(
        f"/admin/questions/{qid}/delete",
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert r.headers["location"] == "/admin/questions?saved=deleted"
    db.expire_all()
    assert db.get(Question, qid) is None
