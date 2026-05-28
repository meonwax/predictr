"""Tests for the dev-only test-user seed."""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dev_seed import (
    DEV_BETS,
    DEV_PASSWORD,
    DEV_SHOUTS,
    DEV_USERS,
    run_dev_seed,
)
from app.models import Bet, Shout, User
from app.security import verify_password

pytestmark = pytest.mark.usefixtures("clean_user_tables")


def test_run_dev_seed_creates_every_user(db_session: Session) -> None:
    report = run_dev_seed(db_session)
    assert report.skipped is False
    assert report.users_created == len(DEV_USERS)
    assert report.users_existing == 0

    emails = {row.email for row in db_session.scalars(select(User)).all()}
    assert emails == {spec.email for spec in DEV_USERS}


def test_admin_user_gets_admin_role(db_session: Session) -> None:
    run_dev_seed(db_session)
    admin = db_session.scalar(select(User).where(User.email == "admin@predictr.local"))
    assert admin is not None
    assert admin.role == User.ROLE_ADMIN


def test_every_user_can_authenticate_with_shared_password(db_session: Session) -> None:
    run_dev_seed(db_session)
    for spec in DEV_USERS:
        user = db_session.scalar(select(User).where(User.email == spec.email))
        assert user is not None, spec.email
        assert verify_password(DEV_PASSWORD, user.password) is True


def test_run_dev_seed_is_idempotent(db_session: Session) -> None:
    first = run_dev_seed(db_session)
    second = run_dev_seed(db_session)
    assert first.users_created == len(DEV_USERS)
    assert second.users_created == 0
    assert second.users_existing == len(DEV_USERS)
    assert second.shouts_created == 0
    assert second.bets_created == 0

    users_count = db_session.scalar(select(User.id).limit(1))
    assert users_count is not None
    total_users = len(db_session.scalars(select(User)).all())
    assert total_users == len(DEV_USERS)


def test_seed_creates_one_shout_per_DEV_SHOUTS_entry(db_session: Session) -> None:
    report = run_dev_seed(db_session)
    assert report.shouts_created == len(DEV_SHOUTS)

    rows = db_session.scalars(select(Shout)).all()
    assert len(rows) == len(DEV_SHOUTS)
    messages = {row.message for row in rows}
    assert messages == {message for _, message in DEV_SHOUTS}


def test_shouts_are_ordered_so_first_DEV_SHOUTS_entry_is_oldest(db_session: Session) -> None:
    """Earliest-in-list should be earliest-in-time, so the home dashboard
    surfaces the most recent message at the top of the recent-shouts panel."""
    run_dev_seed(db_session)
    rows = db_session.scalars(select(Shout).order_by(Shout.date)).all()
    actual_messages = [row.message for row in rows]
    expected_messages = [message for _, message in DEV_SHOUTS]
    assert actual_messages == expected_messages


def test_seed_creates_expected_number_of_bets(db_session: Session) -> None:
    report = run_dev_seed(db_session)
    expected = sum(len(by_game) for by_game in DEV_BETS.values())
    assert report.bets_created == expected

    bets = db_session.scalars(select(Bet)).all()
    assert len(bets) == expected


def test_bet_values_match_DEV_BETS(db_session: Session) -> None:
    run_dev_seed(db_session)
    user_ids = {
        spec.email: db_session.scalar(select(User.id).where(User.email == spec.email))
        for spec in DEV_USERS
    }
    for email, by_game in DEV_BETS.items():
        for game_id, (home, away) in by_game.items():
            bet = db_session.scalar(
                select(Bet).where(
                    Bet.user_id == user_ids[email],
                    Bet.game_id == game_id,
                )
            )
            assert bet is not None, (email, game_id)
            assert bet.score_home == home
            assert bet.score_away == away


def test_if_empty_skips_when_users_already_exist(db_session: Session) -> None:
    run_dev_seed(db_session)
    report = run_dev_seed(db_session, if_empty=True)
    assert report.skipped is True
    assert report.users_created == 0


def test_if_empty_runs_when_users_table_is_empty(db_session: Session) -> None:
    report = run_dev_seed(db_session, if_empty=True)
    assert report.skipped is False
    assert report.users_created == len(DEV_USERS)


def test_reset_wipes_existing_users_before_seeding(db_session: Session) -> None:
    """An operator who mutated dev users should be able to recover quickly."""
    run_dev_seed(db_session)
    admin = db_session.scalar(select(User).where(User.email == "admin@predictr.local"))
    assert admin is not None
    admin.name = "Definitely Not Admin"
    db_session.commit()

    report = run_dev_seed(db_session, reset=True)
    assert report.users_created == len(DEV_USERS)
    refreshed = db_session.scalar(select(User).where(User.email == "admin@predictr.local"))
    assert refreshed is not None
    assert refreshed.name == "Admin"


def test_seed_repairs_demoted_admin_on_rerun(db_session: Session) -> None:
    """Re-running without --reset should still un-do role drift on the admin row."""
    run_dev_seed(db_session)
    admin = db_session.scalar(select(User).where(User.email == "admin@predictr.local"))
    assert admin is not None
    admin.role = User.ROLE_USER
    db_session.commit()

    run_dev_seed(db_session)
    refreshed = db_session.scalar(select(User).where(User.email == "admin@predictr.local"))
    assert refreshed is not None
    assert refreshed.role == User.ROLE_ADMIN
