"""Dev-only seed: create test users + sample shouts + sample bets.

Why a Python module instead of a SQL file: bcrypt hashes depend on the
process that produced them (cost factor, library version), so checking
pre-computed hashes into a `.sql` is fragile. Going through the service
layer also exercises the same validation paths that real registrations
hit, which catches regressions for free.

Usage::

    uv run python -m app.dev_seed             # always run; safe to re-invoke
    uv run python -m app.dev_seed --if-empty  # no-op if any user exists
    uv run python -m app.dev_seed --reset     # wipe per-user tables first

**Never run this in production.** Every account uses the same throwaway
password and the admin email is fixed; both are documented and intended
to be discoverable. The container entrypoint requires an explicit
``AUTO_DEV_SEED=1`` env var so the dev seed cannot run accidentally.
"""

from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.db import get_engine
from app.models import Bet, Game, Shout, User
from app.security import hash_password
from app.services.users import find_user_by_email

LOGGER = logging.getLogger(__name__)

#: Shared throwaway password for every account in this seed. Documented
#: openly because the seed is dev-only.
DEV_PASSWORD: str = "hunter22"


@dataclass(frozen=True, slots=True)
class _DevUser:
    """Lightweight spec for one user the dev seed should create."""

    email: str
    name: str
    role: str = User.ROLE_USER
    preferred_language: str | None = None


# Stable list of accounts the seed always creates. Two languages so the
# i18n surface is exercised without flipping preferences manually.
DEV_USERS: tuple[_DevUser, ...] = (
    _DevUser("admin@predictr.local", "Admin", role=User.ROLE_ADMIN, preferred_language="en"),
    _DevUser("alice@predictr.local", "Alice", preferred_language="en"),
    _DevUser("bob@predictr.local", "Bob", preferred_language="de"),
    _DevUser("carla@predictr.local", "Carla", preferred_language="en"),
    _DevUser("dave@predictr.local", "Dave", preferred_language="de"),
)

# Sample chatter for the shoutbox / home dashboard. Tuples of
# (user_email, message). Messages are deduplicated by exact content per
# user, so re-running the seed never produces "Hello!" * 5.
DEV_SHOUTS: tuple[tuple[str, str], ...] = (
    ("admin@predictr.local", "Welcome to the Predictr dev instance!"),
    ("alice@predictr.local", "Anyone else betting Brazil to win the whole thing?"),
    ("bob@predictr.local", "Deutschland holt sich den Titel, kein Zweifel."),
    ("carla@predictr.local", "Curacao in the group stage is going to be the surprise."),
    ("dave@predictr.local", "Frankreich gegen Norwegen, das wird spannend."),
)

# Sample bets keyed by user_email -> {game_id: (score_home, score_away)}.
# Limited to the first matchday so the data exercises the bets page
# without spoiling group-stage outcomes for whoever's developing.
DEV_BETS: dict[str, dict[int, tuple[int, int]]] = {
    "admin@predictr.local": {1: (2, 0), 2: (1, 1)},
    "alice@predictr.local": {1: (1, 0), 2: (2, 1), 3: (1, 2)},
    "bob@predictr.local": {1: (3, 1), 2: (0, 1), 4: (1, 1)},
    "carla@predictr.local": {1: (2, 1), 3: (0, 0), 4: (2, 0)},
    "dave@predictr.local": {2: (1, 2), 3: (1, 1), 4: (3, 0)},
}


# ---------------------------------------------------------------------------
# Building blocks (each idempotent)
# ---------------------------------------------------------------------------


def _ensure_user(db: Session, spec: _DevUser) -> User:
    """Create *spec* if absent, return the live row otherwise.

    Idempotent: re-running the seed never duplicates accounts. If the
    user exists, we only patch their role / language so an operator who
    promoted ``admin@predictr.local`` to ``ROLE_USER`` mid-test cannot
    accidentally permanently demote the seed admin on the next run.
    """
    existing = find_user_by_email(db, spec.email)
    now = datetime.now(UTC)
    if existing is not None:
        changed = False
        if existing.role != spec.role:
            existing.role = spec.role
            changed = True
        if existing.preferred_language != spec.preferred_language:
            existing.preferred_language = spec.preferred_language
            changed = True
        if changed:
            existing.last_modified_date = now
            db.commit()
            LOGGER.info("Refreshed dev user role/language for %s", spec.email)
        return existing

    user = User(
        created_date=now,
        last_modified_date=now,
        email=spec.email.strip().lower(),
        password=hash_password(DEV_PASSWORD),
        name=spec.name,
        role=spec.role,
        preferred_language=spec.preferred_language,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    LOGGER.info("Created dev user %s (role=%s)", spec.email, spec.role)
    return user


def _ensure_shout(db: Session, user: User, message: str, *, age: timedelta) -> Shout | None:
    """Insert *message* for *user* unless an identical row already exists.

    *age* is subtracted from "now" so the seeded shouts appear in a
    natural reverse-chronological order rather than as five rows with
    the same millisecond timestamp.
    """
    existing = db.scalars(
        select(Shout).where(Shout.user_id == user.id, Shout.message == message)
    ).first()
    if existing is not None:
        return None

    shout = Shout(
        date=datetime.now(UTC) - age,
        message=message,
        user_id=user.id,
    )
    db.add(shout)
    db.commit()
    db.refresh(shout)
    LOGGER.info("Created dev shout id=%d by user=%d", shout.id, user.id)
    return shout


def _ensure_bet(db: Session, user: User, game_id: int, scores: tuple[int, int]) -> Bet | None:
    """Upsert a single bet for *user* on *game_id*.

    Bets on already-kicked-off games are silently skipped: the dev seed
    must not pretend to predict the past. Returns ``None`` when nothing
    was created or updated.
    """
    game = db.get(Game, game_id)
    if game is None:
        LOGGER.warning("Dev seed skipping bet on unknown game id=%d", game_id)
        return None
    if game.kickoff_time <= datetime.now(UTC):
        LOGGER.info("Dev seed skipping bet on game %d - kickoff already passed.", game_id)
        return None

    score_home, score_away = scores
    existing = db.scalars(select(Bet).where(Bet.user_id == user.id, Bet.game_id == game_id)).first()
    if existing is not None:
        if existing.score_home == score_home and existing.score_away == score_away:
            return None
        existing.score_home = score_home
        existing.score_away = score_away
        db.commit()
        LOGGER.info(
            "Updated dev bet user=%d game=%d -> %d:%d",
            user.id,
            game_id,
            score_home,
            score_away,
        )
        return existing

    bet = Bet(
        user_id=user.id,
        game_id=game_id,
        score_home=score_home,
        score_away=score_away,
    )
    db.add(bet)
    db.commit()
    db.refresh(bet)
    LOGGER.info(
        "Created dev bet id=%d user=%d game=%d -> %d:%d",
        bet.id,
        user.id,
        game_id,
        score_home,
        score_away,
    )
    return bet


# ---------------------------------------------------------------------------
# Top-level driver
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class DevSeedReport:
    """Summary of what :func:`run_dev_seed` did during a single invocation."""

    users_created: int
    users_existing: int
    shouts_created: int
    bets_created: int
    skipped: bool = False


def _any_users(db: Session) -> bool:
    return db.scalar(select(User.id).limit(1)) is not None


def _reset_user_tables(db: Session) -> None:
    """Wipe per-user tables, leaving tournament reference data intact.

    The session's identity map is purged afterwards so any objects the
    caller already loaded (e.g. a previous run's User rows) don't
    resurrect themselves when we re-insert primary keys.
    """
    db.execute(
        text(
            "TRUNCATE TABLE password_reset_token, answer, bet, shout, users "
            "RESTART IDENTITY CASCADE"
        )
    )
    db.commit()
    db.expunge_all()


def run_dev_seed(
    db: Session,
    *,
    if_empty: bool = False,
    reset: bool = False,
) -> DevSeedReport:
    """Apply the dev seed against *db*.

    * ``reset`` wipes per-user tables before seeding. Tournament data
      (groups / teams / venues / games / config / questions) is left
      alone.
    * ``if_empty`` skips the whole seed if any user already exists. Use
      this in CI or container boot to avoid stomping a manually-edited
      DB.
    """
    if reset:
        _reset_user_tables(db)

    if if_empty and _any_users(db):
        return DevSeedReport(0, 0, 0, 0, skipped=True)

    users_created = 0
    users_existing = 0
    user_by_email: dict[str, User] = {}
    for spec in DEV_USERS:
        before = find_user_by_email(db, spec.email)
        user = _ensure_user(db, spec)
        user_by_email[spec.email] = user
        if before is None:
            users_created += 1
        else:
            users_existing += 1

    shouts_created = 0
    # Earliest shout in the list gets the largest "age" so the list ends
    # up in chronological order when sorted by Shout.date desc.
    for index, (email, message) in enumerate(reversed(DEV_SHOUTS)):
        user = user_by_email[email]
        age = timedelta(minutes=5 * (index + 1))
        if _ensure_shout(db, user, message, age=age) is not None:
            shouts_created += 1

    bets_created = 0
    for email, by_game in DEV_BETS.items():
        user = user_by_email[email]
        for game_id, scores in by_game.items():
            if _ensure_bet(db, user, game_id, scores) is not None:
                bets_created += 1

    return DevSeedReport(
        users_created=users_created,
        users_existing=users_existing,
        shouts_created=shouts_created,
        bets_created=bets_created,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.dev_seed",
        description=(
            "Insert a set of dev-only test users (plus sample shouts and "
            "bets) into the configured database. Never run in production."
        ),
    )
    parser.add_argument(
        "--if-empty",
        action="store_true",
        help="Skip seeding (silently) if any user already exists.",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Wipe per-user tables before seeding. Mutually exclusive with --if-empty.",
    )
    args = parser.parse_args(argv)

    if args.reset and args.if_empty:
        print("error: --reset and --if-empty are mutually exclusive.", file=sys.stderr)
        return 2

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    engine = get_engine()
    from sqlalchemy.orm import sessionmaker

    Session_ = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    with Session_() as session:
        report = run_dev_seed(session, if_empty=args.if_empty, reset=args.reset)

    if report.skipped:
        print("Dev seed skipped: users already exist (use --reset to overwrite).")
        return 0

    print(
        f"Dev seed done. users created={report.users_created} "
        f"existing={report.users_existing} shouts={report.shouts_created} "
        f"bets={report.bets_created}."
    )
    print(f"Login with any of {[u.email for u in DEV_USERS]} / password {DEV_PASSWORD!r}.")
    return 0


__all__ = [
    "DEV_PASSWORD",
    "DEV_USERS",
    "DEV_SHOUTS",
    "DEV_BETS",
    "DevSeedReport",
    "run_dev_seed",
    "main",
]


if __name__ == "__main__":
    raise SystemExit(main())
