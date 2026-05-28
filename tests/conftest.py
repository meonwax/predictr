"""Shared pytest fixtures.

A single Postgres 16 testcontainer is started once per pytest session and
re-used across every test module that needs it. The container requires a
running Docker daemon on the host.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

# Force English as the test-suite default language *before* any app module
# instantiates the cached Settings object. Production defaults to German
# (the real audience), but every existing assertion in this suite was
# written against English UI text, so flipping the suite default keeps
# the diff focused on tests that actually exercise translation behaviour.
os.environ.setdefault("DEFAULT_LANGUAGE", "en")
# Same idea for the display timezone: production defaults to
# ``Europe/Berlin`` (the primary audience). Pin the test suite to UTC so
# assertions on rendered kickoff times stay stable regardless of DST and
# don't need to know about local-to-UTC math.
os.environ.setdefault("DEFAULT_TIMEZONE", "UTC")
# Pin DEBUG to false so the test environment mirrors production: Starlette's
# ServerErrorMiddleware bypasses user-registered ``Exception`` handlers when
# ``app.debug`` is true (it would render a traceback page instead), and our
# 500-page handler in app.main is registered behind ``if not settings.debug``.
# Forcing it here keeps the suite asserting against the branded 500 page
# without leaking the developer's local ``DEBUG=true`` in ``.env``.
os.environ["DEBUG"] = "false"
# Pin a quiet log level for the suite. ``app.main._configure_logging`` calls
# ``logging.basicConfig`` from this value, so without this pin every test
# would emit hundreds of INFO lines (bet upserts, mail backend banners, ...)
# into pytest's captured stderr. Individual tests that exercise log output
# can override locally via ``caplog`` or by monkeypatching the root level.
os.environ.setdefault("LOG_LEVEL", "WARNING")

import pytest
from alembic import command
from alembic.config import Config as AlembicConfig
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from testcontainers.postgres import PostgresContainer

from app.config import get_settings
from app.dependencies import get_db, get_mail_backend_dep
from app.main import app
from app.seed import load_seed_file
from app.services.mail import InMemoryMailBackend

# Defensive: if any module instantiated Settings before conftest ran, drop
# the cache so the env-var override above takes effect. Cheap.
get_settings.cache_clear()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SEED_FILE = PROJECT_ROOT / "seeds" / "wc2026.sql"
ALEMBIC_INI = PROJECT_ROOT / "alembic.ini"


@pytest.fixture(autouse=True, scope="session")
def _lower_bcrypt_cost() -> Iterator[None]:
    """Run bcrypt with the minimum cost factor during the test session.

    Production uses cost 12 (~200ms / hash on this hardware); tests don't
    care about that hardness and would otherwise burn a couple of seconds
    on hashing in every auth-route test. Cost 4 is ~1ms / hash.
    """
    import app.security as sec

    original = sec._BCRYPT_ROUNDS
    sec._BCRYPT_ROUNDS = 4
    try:
        yield
    finally:
        sec._BCRYPT_ROUNDS = original


@pytest.fixture(scope="session")
def postgres_container() -> Iterator[PostgresContainer]:
    """Start a disposable Postgres 16 container for the test session.

    Requires a running Docker daemon on the host. The container is pinned
    to UTC so timestamp assertions are stable. The container handle is
    exposed (in addition to the URL) so tests that need to ``exec`` into
    it - e.g. the backup-sidecar round-trip test that runs ``pg_dump`` /
    ``pg_restore`` inside the container to avoid host/server version
    mismatch - have a stable handle.
    """
    container = (
        PostgresContainer("postgres:16-alpine", driver="psycopg")
        .with_env("TZ", "UTC")
        .with_env("PGTZ", "UTC")
    )
    with container as pg:
        yield pg


@pytest.fixture(scope="session")
def postgres_url(postgres_container: PostgresContainer) -> str:
    """Connection URL of the session-scoped Postgres testcontainer."""
    return postgres_container.get_connection_url()


@pytest.fixture(scope="session")
def seeded_engine(postgres_url: str) -> Iterator[Engine]:
    """Run Alembic, load the WC 2026 seed, return a session-scoped engine."""
    cfg = AlembicConfig(str(ALEMBIC_INI))
    cfg.set_main_option("sqlalchemy.url", postgres_url)
    command.upgrade(cfg, "head")

    engine = create_engine(postgres_url, future=True)
    load_seed_file(SEED_FILE, engine=engine)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture()
def db_session(seeded_engine: Engine) -> Iterator[Session]:
    """A fresh SQLAlchemy session bound to the shared seeded engine."""
    Session_ = sessionmaker(bind=seeded_engine, expire_on_commit=False, future=True)
    with Session_() as session:
        yield session


# ---------------------------------------------------------------------------
# Auth-test plumbing
# ---------------------------------------------------------------------------


@pytest.fixture()
def clean_user_tables(seeded_engine: Engine) -> Iterator[None]:
    """Wipe per-user tables before and after each test.

    The seeded reference data (groups/teams/venues/games) is left untouched
    so we don't pay the seed cost again. Use ``TRUNCATE ... CASCADE`` so any
    table that grows to depend on ``users`` later (bets, answers, shouts)
    keeps working without updates here.
    """
    with seeded_engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE password_reset_token, users RESTART IDENTITY CASCADE"))
    yield
    with seeded_engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE password_reset_token, users RESTART IDENTITY CASCADE"))


@pytest.fixture()
def mail_inbox() -> InMemoryMailBackend:
    """An in-memory mail backend that the test can inspect."""
    return InMemoryMailBackend()


@pytest.fixture()
def auth_client(
    seeded_engine: Engine,
    mail_inbox: InMemoryMailBackend,
    clean_user_tables: None,
) -> Iterator[TestClient]:
    """A TestClient with ``get_db`` + mail backend wired to the test fixtures."""
    Session_ = sessionmaker(bind=seeded_engine, expire_on_commit=False, future=True)

    def _override_get_db() -> Iterator[Session]:
        with Session_() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_mail_backend_dep] = lambda: mail_inbox
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_mail_backend_dep, None)
