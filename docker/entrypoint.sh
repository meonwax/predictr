#!/bin/sh
# Container entrypoint:
#   1. Run alembic migrations (unless RUN_MIGRATIONS=0).
#   2. If AUTO_SEED=1, load the public WC 2026 seed via --if-empty (safe
#      to repeat: it no-ops on an already-seeded database).
#   3. Exec the requested command (uvicorn by default).
set -eu

if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
    echo "[entrypoint] running alembic upgrade head..."
    alembic upgrade head
else
    echo "[entrypoint] RUN_MIGRATIONS=0 - skipping alembic upgrade"
fi

if [ "${AUTO_SEED:-0}" = "1" ]; then
    seed_file="${AUTO_SEED_FILE:-seeds/wc2026.sql}"
    echo "[entrypoint] AUTO_SEED=1 - running 'python -m app.seed --if-empty ${seed_file}'"
    python -m app.seed --if-empty "${seed_file}"
fi

# AUTO_DEV_SEED is intentionally gated behind a *separate* env var (no default
# alias to AUTO_SEED) because it inserts well-known test accounts with a
# shared throwaway password and must never run in production.
if [ "${AUTO_DEV_SEED:-0}" = "1" ]; then
    echo "[entrypoint] AUTO_DEV_SEED=1 - running 'python -m app.dev_seed --if-empty'"
    python -m app.dev_seed --if-empty
fi

exec "$@"
