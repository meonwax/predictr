"""Integration tests for ``GET /questions/{question_id}/others``."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from app.models import Question


def _register(client: TestClient, *, name: str, email: str) -> None:
    r = client.post(
        "/register",
        data={"name": name, "email": email, "password": "hunter222"},
        follow_redirects=False,
    )
    assert r.status_code == 303


def _login(client: TestClient, email: str) -> None:
    r = client.post(
        "/login", data={"email": email, "password": "hunter222"}, follow_redirects=False
    )
    assert r.status_code == 303


def _logout(client: TestClient) -> None:
    client.post("/logout")


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


def _move_deadline_to_past(db: Session, q: Question) -> None:
    q.deadline = datetime.now(UTC) - timedelta(hours=1)
    db.commit()


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


def test_others_requires_login(auth_client: TestClient, db: Session) -> None:
    q = _make_question(db)
    r = auth_client.get(f"/questions/{q.id}/others")
    assert r.status_code == 401


def test_others_unknown_question_404(auth_client: TestClient) -> None:
    _register(auth_client, name="Alice", email="a@example.com")
    _login(auth_client, "a@example.com")
    r = auth_client.get("/questions/99999/others")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Locked vs unlocked
# ---------------------------------------------------------------------------


def test_locked_before_deadline(
    auth_client: TestClient,
    db: Session,
) -> None:
    q = _make_question(db)
    _register(auth_client, name="Alice", email="a@example.com")
    _login(auth_client, "a@example.com")
    r = auth_client.get(f"/questions/{q.id}/others")
    assert r.status_code == 200
    assert "after the deadline" in r.text.lower()
    assert "<!doctype html>" not in r.text.lower()


def test_unlocked_lists_other_answers(
    auth_client: TestClient,
    db: Session,
) -> None:
    q = _make_question(db)
    _register(auth_client, name="Bob", email="b@example.com")
    _login(auth_client, "b@example.com")
    auth_client.post(
        f"/questions/{q.id}", data={"answer": "Mbappe"}, headers={"HX-Request": "true"}
    )
    _logout(auth_client)

    _register(auth_client, name="Alice", email="a@example.com")
    _login(auth_client, "a@example.com")
    _move_deadline_to_past(db, q)

    r = auth_client.get(f"/questions/{q.id}/others")
    assert r.status_code == 200
    assert "Bob" in r.text
    assert "Mbappe" in r.text


def test_excludes_own_answer(
    auth_client: TestClient,
    db: Session,
) -> None:
    q = _make_question(db)
    _register(auth_client, name="Alice", email="a@example.com")
    _login(auth_client, "a@example.com")
    auth_client.post(
        f"/questions/{q.id}", data={"answer": "alice-secret-guess"}, headers={"HX-Request": "true"}
    )
    _move_deadline_to_past(db, q)

    r = auth_client.get(f"/questions/{q.id}/others")
    assert r.status_code == 200
    assert "alice-secret-guess" not in r.text


def test_empty_state(
    auth_client: TestClient,
    db: Session,
) -> None:
    q = _make_question(db)
    _register(auth_client, name="Alice", email="a@example.com")
    _login(auth_client, "a@example.com")
    _move_deadline_to_past(db, q)

    r = auth_client.get(f"/questions/{q.id}/others")
    assert r.status_code == 200
    assert "Nobody else" in r.text


def test_colours_correct_answers_after_admin_sets_them(
    auth_client: TestClient,
    db: Session,
) -> None:
    q = _make_question(db)
    _register(auth_client, name="Bob", email="b@example.com")
    _login(auth_client, "b@example.com")
    auth_client.post(
        f"/questions/{q.id}", data={"answer": "Mbappe"}, headers={"HX-Request": "true"}
    )
    _logout(auth_client)

    _register(auth_client, name="Alice", email="a@example.com")
    _login(auth_client, "a@example.com")
    q.correct_answer = "Mbappe"
    _move_deadline_to_past(db, q)

    r = auth_client.get(f"/questions/{q.id}/others")
    assert r.status_code == 200
    assert "table-success" in r.text


# ---------------------------------------------------------------------------
# Trigger button on the page
# ---------------------------------------------------------------------------


def test_questions_page_has_others_buttons(
    auth_client: TestClient,
    db: Session,
) -> None:
    q = _make_question(db)
    _register(auth_client, name="Alice", email="a@example.com")
    _login(auth_client, "a@example.com")
    page = auth_client.get("/questions").text
    assert f'hx-get="/questions/{q.id}/others"' in page
    assert 'data-bs-target="#peek-modal"' in page


def test_base_template_includes_modal(
    auth_client: TestClient,
) -> None:
    """Every authenticated page should render the shared peek modal."""
    _register(auth_client, name="Alice", email="a@example.com")
    _login(auth_client, "a@example.com")
    page = auth_client.get("/games").text
    assert 'id="peek-modal"' in page
    assert 'id="peek-modal-body"' in page
