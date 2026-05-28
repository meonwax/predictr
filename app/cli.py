"""Operational CLI commands.

A small ``argparse`` front-end for tasks that don't fit a web UI (yet)
and shouldn't require firing up a Python REPL. Right now this covers
*promoting* and *demoting* admins, which is the bootstrap step needed
before anyone can use the ``/admin`` web UI.

Usage:

    python -m app.cli promote-admin <email>
    python -m app.cli demote-admin <email>
    python -m app.cli list-admins

The commands run against the database configured by :mod:`app.config`
(i.e. the same one the FastAPI app talks to).
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from sqlalchemy.orm import Session, sessionmaker

from app.db import get_engine
from app.models import User
from app.services.users import find_user_by_email

# ---------------------------------------------------------------------------
# Command handlers - pure functions over a Session, easy to unit-test
# ---------------------------------------------------------------------------


class UserNotFound(LookupError):
    """Raised when no user matches the email the CLI was invoked with."""


def promote_admin(db: Session, email: str) -> User:
    """Grant ``ROLE_ADMIN`` to the user with the given *email*.

    Idempotent: a user that's already an admin is left untouched.
    """
    user = find_user_by_email(db, email)
    if user is None:
        raise UserNotFound(email)
    if user.role != User.ROLE_ADMIN:
        user.role = User.ROLE_ADMIN
        db.commit()
    return user


def demote_admin(db: Session, email: str) -> User:
    """Revoke admin role; downgrade to ``ROLE_USER``.

    Idempotent and symmetric to :func:`promote_admin`.
    """
    user = find_user_by_email(db, email)
    if user is None:
        raise UserNotFound(email)
    if user.role != User.ROLE_USER:
        user.role = User.ROLE_USER
        db.commit()
    return user


def list_admins(db: Session) -> list[User]:
    """All current admins, in insertion order (i.e. by ``id``)."""
    return db.query(User).filter(User.role == User.ROLE_ADMIN).order_by(User.id).all()


# ---------------------------------------------------------------------------
# argparse plumbing
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m app.cli",
        description="Predictr operational CLI.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_promote = sub.add_parser(
        "promote-admin",
        help="Grant ROLE_ADMIN to an existing user.",
    )
    p_promote.add_argument("email")

    p_demote = sub.add_parser(
        "demote-admin",
        help="Revoke admin role (downgrade to ROLE_USER).",
    )
    p_demote.add_argument("email")

    sub.add_parser("list-admins", help="Print all admin email addresses.")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Dispatch a single command. Returns a Unix-style exit code."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    engine = get_engine()
    Session_ = sessionmaker(bind=engine, expire_on_commit=False, future=True)

    with Session_() as db:
        try:
            if args.cmd == "promote-admin":
                user = promote_admin(db, args.email)
                print(f"Promoted {user.email} to admin (id={user.id}).")
                return 0
            if args.cmd == "demote-admin":
                user = demote_admin(db, args.email)
                print(f"Demoted {user.email} (id={user.id}).")
                return 0
            if args.cmd == "list-admins":
                admins = list_admins(db)
                if not admins:
                    print("No admin users.")
                    return 0
                for a in admins:
                    print(f"{a.id}\t{a.email}\t{a.name}")
                return 0
        except UserNotFound as exc:
            print(f"No such user: {exc.args[0]}", file=sys.stderr)
            return 1

    parser.error(f"Unknown command: {args.cmd}")  # unreachable; argparse exits
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
