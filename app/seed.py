"""Load a SQL seed file into the configured Postgres database.

Usage:

    python -m app.seed seeds/wc2026.sql
    python -m app.seed --if-empty seeds/wc2026.sql      # safe re-run

The runner is intentionally simple: it splits the file into statements at
top-level semicolons, strips ``--``-style line comments (correctly handling
SQL-escaped apostrophes such as ``Levi''s``), and executes the result inside
a single transaction against the engine built from ``app.config.Settings``
(i.e. the same database the app itself talks to).

The ``--if-empty`` flag makes the runner idempotent for the WC 2026 public
seed: it checks whether any of the seed's target tables (``groups``,
``team``, ``venue``, ``game``) already contain rows, and skips the load if
so. This is the mode used by the container entrypoint when ``AUTO_SEED=1``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sqlalchemy import Engine, text

from app.db import get_engine

# Tables touched by the public WC 2026 seed. Used by --if-empty to decide
# whether a re-run would be a no-op.
_SEED_TARGET_TABLES: tuple[str, ...] = ("groups", "team", "venue", "game")


def _strip_line_comments(sql: str) -> str:
    """Remove ``-- ...`` comments while preserving them inside string literals."""
    out: list[str] = []
    i = 0
    in_string = False
    while i < len(sql):
        ch = sql[i]
        if in_string:
            out.append(ch)
            if ch == "'":
                # Doubled '' is an escaped apostrophe, not end-of-string.
                if i + 1 < len(sql) and sql[i + 1] == "'":
                    out.append(sql[i + 1])
                    i += 2
                    continue
                in_string = False
            i += 1
            continue

        if ch == "'":
            in_string = True
            out.append(ch)
            i += 1
            continue

        if ch == "-" and i + 1 < len(sql) and sql[i + 1] == "-":
            # Skip to the next newline (preserve the newline itself).
            nl = sql.find("\n", i)
            if nl == -1:
                break
            i = nl
            continue

        out.append(ch)
        i += 1
    return "".join(out)


def _split_statements(sql: str) -> list[str]:
    """Split the SQL text into top-level statements (semicolon-terminated)."""
    cleaned = _strip_line_comments(sql)
    statements: list[str] = []
    current: list[str] = []
    in_string = False
    i = 0
    n = len(cleaned)
    while i < n:
        ch = cleaned[i]
        if in_string:
            current.append(ch)
            if ch == "'":
                # `''` is an escaped apostrophe - copy both and stay in the string.
                if i + 1 < n and cleaned[i + 1] == "'":
                    current.append(cleaned[i + 1])
                    i += 2
                    continue
                in_string = False
            i += 1
            continue

        if ch == "'":
            in_string = True
            current.append(ch)
            i += 1
            continue

        if ch == ";":
            stmt = "".join(current).strip()
            if stmt:
                statements.append(stmt)
            current = []
            i += 1
            continue

        current.append(ch)
        i += 1

    tail = "".join(current).strip()
    if tail:
        statements.append(tail)
    return statements


def is_target_seeded(engine: Engine) -> bool:
    """Return True if any of the seed's target tables already has rows.

    Used by :func:`load_seed_file` to decide whether to skip when called
    with ``if_empty=True``. Reads each table with a cheap ``COUNT(*)`` and
    short-circuits on the first non-empty one.
    """
    with engine.connect() as conn:
        for table in _SEED_TARGET_TABLES:
            count = conn.scalar(text(f"SELECT COUNT(*) FROM {table}"))
            if count is not None and count > 0:
                return True
    return False


def load_seed_file(
    path: Path,
    engine: Engine | None = None,
    *,
    if_empty: bool = False,
) -> int:
    """Execute every statement in *path* in a single transaction.

    Returns the number of statements run, or ``0`` if *if_empty* was set and
    the target tables already contained data (in that case the database is
    left untouched).
    """
    bind = engine if engine is not None else get_engine()
    if if_empty and is_target_seeded(bind):
        return 0
    sql = path.read_text(encoding="utf-8")
    statements = _split_statements(sql)
    with bind.begin() as conn:
        for stmt in statements:
            conn.execute(text(stmt))
    return len(statements)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.seed",
        description="Load a SQL seed file into the Predictr database.",
    )
    parser.add_argument("seed_file", type=Path, help="Path to a .sql seed file.")
    parser.add_argument(
        "--if-empty",
        action="store_true",
        help=(
            "Skip the load (no error) if any of the seed's target tables "
            "already contains rows. Use this for boot-time auto-seeding."
        ),
    )
    args = parser.parse_args(argv)

    if not args.seed_file.is_file():
        print(f"error: seed file not found: {args.seed_file}", file=sys.stderr)
        return 2

    count = load_seed_file(args.seed_file, if_empty=args.if_empty)
    if count == 0 and args.if_empty:
        print(f"Skipping {args.seed_file}: target tables already contain data.")
    else:
        print(f"Loaded {count} statement(s) from {args.seed_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
