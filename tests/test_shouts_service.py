"""Unit tests for :mod:`app.services.shouts`."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from app.models import User
from app.services.shouts import (
    MAX_MESSAGE_LEN,
    InvalidShout,
    create_shout,
    list_shouts,
)
from app.services.users import RegistrationData, register_user


@pytest.fixture()
def fresh_db(clean_user_tables: None, seeded_engine) -> Iterator[Session]:
    Session_ = sessionmaker(bind=seeded_engine, expire_on_commit=False, future=True)
    with Session_() as session:
        yield session


@pytest.fixture(autouse=True)
def _reset_shouts(seeded_engine) -> Iterator[None]:
    yield
    with seeded_engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE shout RESTART IDENTITY CASCADE"))


def _make_user(db: Session, *, name: str, email: str) -> User:
    return register_user(
        db,
        RegistrationData(name=name, email=email, password="hunter222"),
    )


# ---------------------------------------------------------------------------
# create_shout
# ---------------------------------------------------------------------------


def test_create_basic(fresh_db: Session) -> None:
    alice = _make_user(fresh_db, name="Alice", email="a@example.com")
    shout = create_shout(fresh_db, alice, message="hello world")
    assert shout.id is not None
    assert shout.message == "hello world"
    assert shout.user_id == alice.id
    assert shout.date.tzinfo is not None  # tz-aware UTC


def test_create_trims_whitespace(fresh_db: Session) -> None:
    alice = _make_user(fresh_db, name="Alice", email="a@example.com")
    shout = create_shout(fresh_db, alice, message="  hi  there  ")
    assert shout.message == "hi there"


def test_create_collapses_internal_whitespace(fresh_db: Session) -> None:
    """Tabs and newlines fold into single spaces so the list stays compact."""
    alice = _make_user(fresh_db, name="Alice", email="a@example.com")
    shout = create_shout(fresh_db, alice, message="line1\n\nline2\t\tend")
    assert shout.message == "line1 line2 end"


@pytest.mark.parametrize("blank", ["", "   ", "\n\t", " \r\n "])
def test_create_rejects_empty(fresh_db: Session, blank: str) -> None:
    alice = _make_user(fresh_db, name="Alice", email="a@example.com")
    with pytest.raises(InvalidShout):
        create_shout(fresh_db, alice, message=blank)


def test_create_rejects_too_long(fresh_db: Session) -> None:
    alice = _make_user(fresh_db, name="Alice", email="a@example.com")
    with pytest.raises(InvalidShout) as exc:
        create_shout(fresh_db, alice, message="x" * (MAX_MESSAGE_LEN + 1))
    assert str(MAX_MESSAGE_LEN) in str(exc.value)


def test_max_length_boundary_accepted(fresh_db: Session) -> None:
    alice = _make_user(fresh_db, name="Alice", email="a@example.com")
    msg = "x" * MAX_MESSAGE_LEN
    shout = create_shout(fresh_db, alice, message=msg)
    assert len(shout.message) == MAX_MESSAGE_LEN


def test_create_accepts_now_override(fresh_db: Session) -> None:
    alice = _make_user(fresh_db, name="Alice", email="a@example.com")
    fixed = datetime(2026, 7, 19, 21, 0, tzinfo=UTC)
    shout = create_shout(fresh_db, alice, message="final whistle!", now=fixed)
    assert shout.date == fixed


# ---------------------------------------------------------------------------
# list_shouts
# ---------------------------------------------------------------------------


def test_list_empty(fresh_db: Session) -> None:
    assert list_shouts(fresh_db) == []


def test_list_returns_newest_first(fresh_db: Session) -> None:
    alice = _make_user(fresh_db, name="Alice", email="a@example.com")
    bob = _make_user(fresh_db, name="Bob", email="b@example.com")
    base = datetime(2026, 6, 11, 19, 0, tzinfo=UTC)
    create_shout(fresh_db, alice, message="oldest", now=base)
    create_shout(fresh_db, bob, message="middle", now=base + timedelta(minutes=5))
    create_shout(fresh_db, alice, message="newest", now=base + timedelta(minutes=10))
    shouts = list_shouts(fresh_db)
    assert [s.message for s in shouts] == ["newest", "middle", "oldest"]


def test_list_limit_caps_result(fresh_db: Session) -> None:
    alice = _make_user(fresh_db, name="Alice", email="a@example.com")
    base = datetime(2026, 6, 11, 19, 0, tzinfo=UTC)
    for i in range(5):
        create_shout(fresh_db, alice, message=f"m{i}", now=base + timedelta(minutes=i))
    shouts = list_shouts(fresh_db, limit=2)
    assert len(shouts) == 2
    # Newest two:
    assert [s.message for s in shouts] == ["m4", "m3"]


def test_list_limit_zero_returns_all(fresh_db: Session) -> None:
    alice = _make_user(fresh_db, name="Alice", email="a@example.com")
    base = datetime(2026, 6, 11, 19, 0, tzinfo=UTC)
    for i in range(3):
        create_shout(fresh_db, alice, message=f"m{i}", now=base + timedelta(minutes=i))
    assert len(list_shouts(fresh_db, limit=0)) == 3


def test_list_eager_loads_user(fresh_db: Session) -> None:
    """Accessing ``shout.user`` after the session closes must not raise."""
    alice = _make_user(fresh_db, name="Alice", email="a@example.com")
    create_shout(fresh_db, alice, message="hi")
    shouts = list_shouts(fresh_db)
    # Close the session and try to read the user - would error if lazy.
    fresh_db.close()
    assert shouts[0].user.name == "Alice"
