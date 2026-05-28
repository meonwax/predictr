"""Tests for the daily Postgres backup sidecar.

Three layers of coverage, each cheaper than the next is expensive:

1. ``test_backup_script_syntax_check`` - ``sh -n docker/backup.sh``.
   Catches accidental shell syntax breakage with zero external deps.

2. ``test_backup_script_creates_dump_file_with_stub_pg_dump`` - drives
   the actual script with a PATH-injected stub binary that impersonates
   ``pg_dump``. Asserts the script writes to ``BACKUP_DIR`` with the
   expected ``predictr-<UTC>.pgdump`` filename pattern and invokes the
   binary with the expected flags. No Postgres needed.

3. ``test_backup_round_trip_against_real_postgres`` - runs real
   ``pg_dump`` and ``pg_restore`` *inside* the testcontainer (so the
   client version matches the server version), restores into a fresh
   throwaway database, and verifies the row counts of a representative
   seeded table survive the round-trip.
"""

from __future__ import annotations

import os
import re
import subprocess
import time
from pathlib import Path

from sqlalchemy import Engine, create_engine, text
from testcontainers.postgres import PostgresContainer

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKUP_SCRIPT = PROJECT_ROOT / "docker" / "backup.sh"


# ---------------------------------------------------------------------------
# Layer 1: shell syntax
# ---------------------------------------------------------------------------


def test_backup_script_syntax_check() -> None:
    """``sh -n`` parses the script without executing it."""
    result = subprocess.run(
        ["sh", "-n", str(BACKUP_SCRIPT)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


# ---------------------------------------------------------------------------
# Layer 2: end-to-end script behaviour with a stub binary
# ---------------------------------------------------------------------------


_STUB_PG_DUMP_SCRIPT = """#!/bin/sh
# Test stub for pg_dump. Records argv to $ARGV_LOG and, when invoked with
# `-f <path>`, writes a sentinel string to that path so the test can
# verify the script's "did we get a file?" assertion.
printf '%s\\n' "$*" >> "$ARGV_LOG"
while [ $# -gt 0 ]; do
    if [ "$1" = "-f" ]; then
        echo 'FAKE_PGDUMP_CONTENT' > "$2"
        exit 0
    fi
    shift
done
exit 1
"""


def test_backup_script_creates_dump_file_with_stub_pg_dump(tmp_path: Path) -> None:
    """Stub out pg_dump and confirm the script writes a correctly-named file."""
    backup_dir = tmp_path / "backups"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    argv_log = tmp_path / "argv.log"

    stub = bin_dir / "pg_dump"
    stub.write_text(_STUB_PG_DUMP_SCRIPT)
    stub.chmod(0o755)

    env = {
        **os.environ,
        "PATH": f"{bin_dir}:{os.environ.get('PATH', '')}",
        "ARGV_LOG": str(argv_log),
        "BACKUP_DIR": str(backup_dir),
        "BACKUP_ON_STARTUP": "1",
        # Park the post-startup sleep far into the future; we terminate
        # the process well before the timer fires.
        "SCHEDULE_HOUR_UTC": "23",
        # Keep the binary stub happy - the real values would point at a
        # live DB; the stub ignores them entirely.
        "PGHOST": "stub",
        "PGUSER": "stub",
        "PGPASSWORD": "stub",
        "PGDATABASE": "stub",
    }

    process = subprocess.Popen(  # noqa: S603 - controlled inputs
        ["sh", str(BACKUP_SCRIPT)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        deadline = time.time() + 10
        dump_files: list[Path] = []
        while time.time() < deadline:
            dump_files = list(backup_dir.glob("predictr-*.pgdump"))
            if dump_files:
                break
            time.sleep(0.1)
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)

    assert len(dump_files) == 1, f"expected exactly one dump file, got {dump_files!r}"
    dump = dump_files[0]

    # Filename: predictr-YYYY-MM-DDTHH-MM-SSZ.pgdump (UTC, : replaced with -).
    assert re.match(
        r"^predictr-\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}Z\.pgdump$",
        dump.name,
    ), dump.name
    assert dump.read_text() == "FAKE_PGDUMP_CONTENT\n"

    argv = argv_log.read_text().strip()
    assert "-Fc" in argv, argv
    assert "-f " in argv, argv


def test_backup_script_rejects_invalid_schedule_hour(tmp_path: Path) -> None:
    """SCHEDULE_HOUR_UTC out of range or non-numeric exits 2 with a clear log."""
    env = {
        **os.environ,
        "BACKUP_DIR": str(tmp_path),
        "SCHEDULE_HOUR_UTC": "25",
        "PGHOST": "stub",
        "PGUSER": "stub",
        "PGPASSWORD": "stub",
        "PGDATABASE": "stub",
    }
    result = subprocess.run(  # noqa: S603 - controlled inputs
        ["sh", str(BACKUP_SCRIPT)],
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=5,
    )
    assert result.returncode == 2, result.stdout
    assert "FATAL" in result.stdout
    assert "SCHEDULE_HOUR_UTC" in result.stdout


# ---------------------------------------------------------------------------
# Layer 3: real pg_dump + pg_restore round-trip against the testcontainer
# ---------------------------------------------------------------------------


def test_backup_round_trip_against_real_postgres(
    postgres_container: PostgresContainer,
    seeded_engine: Engine,
) -> None:
    """Dump the seeded DB, restore into a throwaway DB, verify row counts.

    The dump and restore both run *inside* the testcontainer (via
    ``container.exec``), so the client binary version always matches
    the server version. Host pg_dump version drift is therefore not a
    concern for this test.
    """
    # The testcontainer's superuser / database are NOT necessarily named
    # `predictr` (testcontainers-python defaults both to `test`); read the
    # real values off the container so the assertions match what
    # ``seeded_engine`` was wired to.
    pg_user = postgres_container.username
    pg_source_db = postgres_container.dbname
    target_db = f"{pg_source_db}_backup_test"

    # CREATE DATABASE can't run inside a transaction, so use a dedicated
    # autocommit engine for the admin DDL.
    admin_engine = create_engine(
        seeded_engine.url,
        isolation_level="AUTOCOMMIT",
        future=True,
    )
    with admin_engine.connect() as conn:
        conn.execute(text(f"DROP DATABASE IF EXISTS {target_db}"))
        conn.execute(text(f"CREATE DATABASE {target_db}"))

    try:
        # Snapshot a couple of row counts from the seeded DB so we can
        # assert the restored DB matches exactly.
        with seeded_engine.connect() as conn:
            original_teams = conn.execute(text("SELECT COUNT(*) FROM team")).scalar_one()
            original_games = conn.execute(text("SELECT COUNT(*) FROM game")).scalar_one()
        assert original_teams > 0
        assert original_games > 0

        dump_path = "/tmp/predictr_backup_test.pgdump"
        result = postgres_container.exec(
            ["pg_dump", "-U", pg_user, "-d", pg_source_db, "-Fc", "-f", dump_path]
        )
        assert result.exit_code == 0, f"pg_dump failed: {result.output!r}"

        result = postgres_container.exec(["pg_restore", "-U", pg_user, "-d", target_db, dump_path])
        # pg_restore can emit warnings on stdout while still succeeding -
        # only the exit code is authoritative.
        assert result.exit_code == 0, f"pg_restore failed: {result.output!r}"

        # Build the target URL by overriding only the ``database`` component
        # of the source URL - a naive str.replace("/test", "/...") would
        # also mangle the user/password segment when those collide.
        target_url = seeded_engine.url.set(database=target_db)
        target_engine = create_engine(target_url, future=True)
        try:
            with target_engine.connect() as conn:
                restored_teams = conn.execute(text("SELECT COUNT(*) FROM team")).scalar_one()
                restored_games = conn.execute(text("SELECT COUNT(*) FROM game")).scalar_one()
            assert restored_teams == original_teams
            assert restored_games == original_games
        finally:
            target_engine.dispose()
    finally:
        with admin_engine.connect() as conn:
            conn.execute(text(f"DROP DATABASE IF EXISTS {target_db}"))
        admin_engine.dispose()
