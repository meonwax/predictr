"""Unit tests for :mod:`app.cli`.

The handler functions are pure ``(Session, ...) -> ...`` and easy to call
directly against the seeded testcontainer. The argparse dispatcher
(:func:`app.cli.main`) is only smoke-tested for argument parsing - wiring
it to a real Engine in tests would require monkey-patching ``get_engine``,
which adds noise for negligible coverage gain.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy.orm import Session, sessionmaker

from app.cli import UserNotFound, demote_admin, list_admins, promote_admin
from app.models import User
from app.services.users import RegistrationData, register_user


@pytest.fixture()
def fresh_db(clean_user_tables: None, seeded_engine) -> Iterator[Session]:
    Session_ = sessionmaker(bind=seeded_engine, expire_on_commit=False, future=True)
    with Session_() as session:
        yield session


@pytest.fixture()
def regular_user(fresh_db: Session) -> User:
    return register_user(
        fresh_db,
        RegistrationData(name="Pat", email="pat@example.com", password="hunter222"),
    )


# ---------------------------------------------------------------------------
# promote_admin
# ---------------------------------------------------------------------------


def test_promote_admin_grants_role(fresh_db: Session, regular_user: User) -> None:
    assert regular_user.role == User.ROLE_USER
    promoted = promote_admin(fresh_db, "pat@example.com")
    assert promoted.id == regular_user.id
    assert promoted.role == User.ROLE_ADMIN
    fresh_db.refresh(regular_user)
    assert regular_user.role == User.ROLE_ADMIN


def test_promote_admin_is_idempotent(fresh_db: Session, regular_user: User) -> None:
    promote_admin(fresh_db, "pat@example.com")
    again = promote_admin(fresh_db, "pat@example.com")
    assert again.role == User.ROLE_ADMIN


def test_promote_admin_is_case_insensitive(fresh_db: Session, regular_user: User) -> None:
    """The email lookup uses :func:`find_user_by_email`, which lowercases."""
    promoted = promote_admin(fresh_db, "PAT@example.COM")
    assert promoted.role == User.ROLE_ADMIN


def test_promote_admin_unknown_email_raises(fresh_db: Session) -> None:
    with pytest.raises(UserNotFound):
        promote_admin(fresh_db, "ghost@example.com")


# ---------------------------------------------------------------------------
# demote_admin
# ---------------------------------------------------------------------------


def test_demote_admin_strips_role(fresh_db: Session, regular_user: User) -> None:
    promote_admin(fresh_db, "pat@example.com")
    demoted = demote_admin(fresh_db, "pat@example.com")
    assert demoted.role == User.ROLE_USER


def test_demote_admin_is_idempotent(fresh_db: Session, regular_user: User) -> None:
    demoted = demote_admin(fresh_db, "pat@example.com")
    assert demoted.role == User.ROLE_USER  # was already ROLE_USER


def test_demote_admin_unknown_email_raises(fresh_db: Session) -> None:
    with pytest.raises(UserNotFound):
        demote_admin(fresh_db, "ghost@example.com")


# ---------------------------------------------------------------------------
# list_admins
# ---------------------------------------------------------------------------


def test_list_admins_returns_empty_when_none(fresh_db: Session) -> None:
    assert list_admins(fresh_db) == []


def test_list_admins_returns_promoted_users(fresh_db: Session) -> None:
    register_user(
        fresh_db,
        RegistrationData(name="Alice", email="alice@example.com", password="hunter222"),
    )
    register_user(
        fresh_db,
        RegistrationData(name="Bob", email="bob@example.com", password="hunter222"),
    )
    promote_admin(fresh_db, "alice@example.com")
    promote_admin(fresh_db, "bob@example.com")
    admins = list_admins(fresh_db)
    emails = [a.email for a in admins]
    assert emails == ["alice@example.com", "bob@example.com"]


# ---------------------------------------------------------------------------
# argparse dispatcher
# ---------------------------------------------------------------------------


def test_parser_promote_admin() -> None:
    """The 'promote-admin' subcommand parses an email argument."""
    from app.cli import _build_parser

    args = _build_parser().parse_args(["promote-admin", "pat@example.com"])
    assert args.cmd == "promote-admin"
    assert args.email == "pat@example.com"


def test_parser_missing_email_fails() -> None:
    """Subcommand without the required positional arg -> argparse exits."""
    from app.cli import _build_parser

    with pytest.raises(SystemExit):
        _build_parser().parse_args(["promote-admin"])


def test_parser_unknown_command_fails() -> None:
    from app.cli import _build_parser

    with pytest.raises(SystemExit):
        _build_parser().parse_args(["delete-everything"])
