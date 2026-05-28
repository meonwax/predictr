# Predictr

A football prediction game.
Data for the FIFA World Cup 2026 included.

## Stack

* **Backend**: Python 3.12 + FastAPI + SQLAlchemy 2 + Alembic
* **Frontend**: Server-rendered Jinja2 + Bootstrap 5 (vanilla CSS/JS) + HTMX 2
* **Database**: PostgreSQL 16 (dev and prod)
* **Packaging**: [`uv`](https://docs.astral.sh/uv/)
* **Deployment**: Docker Compose, host-level Caddy in front

## First-time setup

You need Python 3.12+ and [`uv`](https://docs.astral.sh/uv/) on your machine.

```sh
# Install the locked Python dependency set (incl. dev tooling)
uv sync --extra dev

# Fetch + SHA-256-verify the bundled third-party JS/CSS (Bootstrap, Bootstrap
# Icons, HTMX) into app/static/vendor/. Idempotent; re-runs are no-ops when
# the files already match the pinned hashes.
uv run python scripts/fetch_vendor_assets.py
```

The vendor assets live under `app/static/vendor/` and are deliberately
**not** committed - see the script's docstring for the version-bump dance.

## Development

The fastest path is the Docker Compose dev stack. It transparently merges
`docker-compose.yml` (the prod-ready base) with `docker-compose.override.yml`
(dev overrides: ephemeral tmpfs Postgres, MailHog, auto-seed enabled).

```sh
docker compose up --build
```

Then open <http://localhost:8000/>.

Services exposed in dev:

| Service       | URL                          |
| ------------- | ---------------------------- |
| App           | <http://localhost:8000/>     |
| MailHog UI    | <http://localhost:8025/>     |
| Adminer       | <http://localhost:8081/>     |
| Postgres      | `localhost:5432` (predictr/predictr/predictr) |

For the Adminer login screen the "Server" field is pre-filled with `postgres`
(the compose service name); enter the standard dev credentials
`predictr` / `predictr` / `predictr` (user / password / database).

Bring it down (and wipe the ephemeral DB):

```sh
docker compose down
```

### Running the app outside Docker

```sh
# Start a local Postgres however you like (or reuse the compose one with
# `docker compose up -d postgres`), then point DATABASE_URL at it:
export DATABASE_URL='postgresql+psycopg://predictr:predictr@localhost:5432/predictr'

# Apply migrations
uv run alembic upgrade head

# Load the World Cup 2026 seed (idempotent with --if-empty)
uv run python -m app.seed --if-empty seeds/wc2026.sql

# Optional: load a handful of dev-only test users + sample data
uv run python -m app.dev_seed

# Run the dev server
uv run uvicorn app.main:app --reload
```

#### Dev-only test users

`python -m app.dev_seed` populates the database with five well-known accounts
plus a few sample shouts and bets so the home dashboard, shoutbox, ladder, and
bets pages are not empty during local development:

| Email | Role | Language |
|---|---|---|
| `admin@predictr.local` | admin | en |
| `alice@predictr.local` | user  | en |
| `bob@predictr.local`   | user  | de |
| `carla@predictr.local` | user  | en |
| `dave@predictr.local`  | user  | de |

All five share the password `hunter22`. The seed is idempotent (re-running it
never duplicates rows) and supports two switches:

* `--if-empty` skips the whole run if any user already exists. Used by the
  container entrypoint when `AUTO_DEV_SEED=1`.
* `--reset` truncates the per-user tables before seeding. Use this to recover
  from local edits.

The dev seed is **never run in production** - the container entrypoint only
honours `AUTO_DEV_SEED=1`, which must be opted into explicitly via the env file,
and the dev compose override is the only place that sets it.

### Tests

```sh
uv run pytest
```

The integration tests boot a throwaway PostgreSQL via
[`testcontainers`](https://testcontainers-python.readthedocs.io/), so you
need a working Docker daemon. They will also fail if the vendor assets are
missing - run `uv run python scripts/fetch_vendor_assets.py` once after
cloning.

### Linting / typing

```sh
uv run ruff check .
uv run ruff format --check .
uv run mypy app
```

## Production

The production deployment target is a VPS with Docker Compose + a host-level
Caddy in front for TLS and the public hostname. The compose stack listens on
loopback (port `8000`) and Caddy proxies to it.

### Bootstrap the host

1. Install Docker Engine + the compose plugin.
2. Clone this repo and create a `.env` next to `docker-compose.yml`. See
   `.env.example` for the variables; at minimum set:
   * `POSTGRES_PASSWORD` - strong, unique
   * `SESSION_SECRET` - long random string (e.g. `openssl rand -hex 48`)
   * `MAIL_*` - your real SMTP relay
   * `LOG_LEVEL` (optional) - defaults to `INFO`; flip to `DEBUG`
     temporarily when diagnosing a live issue, then revert
3. Build and start:

   ```sh
   docker compose -f docker-compose.yml up -d --build
   ```

   (Note the explicit `-f docker-compose.yml` - that opts out of the dev
   override file.)

4. Migrations are applied automatically on container start. Seed data is
   **not** auto-loaded in prod; do it once manually:

   ```sh
   docker compose -f docker-compose.yml exec app \
     python -m app.seed --if-empty seeds/wc2026.sql
   ```

5. Point your Caddy to `http://127.0.0.1:8000` and you're done.

### Bootstrap an admin

The `/admin` UI is role-gated. Register the first admin through the normal
sign-up form, then promote them with the operational CLI:

```sh
docker compose -f docker-compose.yml exec app \
  python -m app.cli promote-admin you@example.com
```

Other CLI commands:

```sh
# List current admins
python -m app.cli list-admins

# Revoke admin role
python -m app.cli demote-admin you@example.com
```

### Upgrades

```sh
git pull
docker compose -f docker-compose.yml up -d --build
```

Migrations run as part of the entrypoint; the persistent `postgres_data`
volume keeps user data across restarts.

### Database backups

The base compose file ships a `postgres-backup` sidecar that runs `pg_dump`
once a day and writes one compressed dump file per run to the host
directory bound at `${BACKUP_DIR:-./backups}`.

Schedule and configuration (all via `.env`):

* `BACKUP_HOUR_UTC` (default `4`): UTC hour to run the backup at. The
  default `04:00 UTC` equals `06:00 CEST` during the WC 2026 tournament
  window (June/July, all CEST).
* `BACKUP_DIR` (default `./backups`): host directory where the dump
  files land. Point your existing host-level backup tool (Borg, restic,
  rsync, VPS snapshots) at this directory and you have an off-site copy
  for free.
* `BACKUP_ON_STARTUP` (default `0`): set to `1` to run one immediate
  backup when the container starts. Useful for sanity-checking right
  after a deploy.

Dump format: `pg_dump -Fc` (Postgres custom format, compressed). File
names look like `predictr-2026-06-15T04-00-00Z.pgdump` (always UTC,
`:` replaced with `-` so the file name is portable to any filesystem).

**No retention** is applied automatically: predictr only runs during the
World Cup so the dump count is naturally bounded (~40-50 files). If you
ever want to prune older files, add a `find "$BACKUP_DIR" -name
'predictr-*.pgdump' -mtime +N -delete` line in `docker/backup.sh` next
to the `run_backup` call.

The sidecar is not started in development (the dev compose override
pins it behind a `never` profile so the dev tmpfs DB isn't backed up
every morning).

**Restore** a dump into a running stack:

```sh
# Drop+recreate the existing schema before restoring so you don't end
# up with a half-imported state.
docker compose -f docker-compose.yml exec -T postgres \
  pg_restore -U predictr -d predictr --clean --if-exists \
  < ./backups/predictr-2026-06-15T04-00-00Z.pgdump
```

For a clean rebuild (e.g. moving to a new host), tear the stack down,
recreate the volume, bring it back up with `RUN_MIGRATIONS=0` (the dump
already contains the schema), and run the same `pg_restore` against the
fresh database.

### Database web UI (Adminer)

The base compose file ships an `adminer` service bound to `127.0.0.1:8081`
(override with `ADMINER_BIND`). It is **not** exposed publicly by Docker;
the host-level Caddy must put it behind HTTP Basic Auth before proxying.

Generate a bcrypt hash for the operator password:

```sh
caddy hash-password --plaintext 'your-strong-password'
```

Add a dedicated subdomain (or subpath) to the Caddyfile, for example:

```caddyfile
db.predictr.example.com {
    basic_auth {
        # Pair of "username  bcrypt-hash" lines. Repeat for more operators.
        admin   $2a$14$EXAMPLE_REPLACE_ME_WITH_caddy_hash-password_OUTPUT
    }
    reverse_proxy 127.0.0.1:8081
}
```

Reload Caddy (`sudo systemctl reload caddy`). The Adminer login form then
prompts for the Postgres credentials separately - the Caddy basic auth
guards access to the web UI itself, not the database password.

If you'd rather not expose Adminer at all in production, comment the
`adminer:` block out of `docker-compose.yml` (or remove it). Nothing else
in the stack depends on it.

## Project layout

```
app/                 # FastAPI application
  routes/            # HTTP route handlers
  static/            # CSS + flag SVGs + (fetched) vendor JS/CSS
  templates/         # Jinja2 templates
  cli.py             # `python -m app.cli` (promote/demote admins, ...)
  config.py          # Pydantic Settings
  db.py              # SQLAlchemy engine + session helpers
  models.py          # ORM models
  seed.py            # `python -m app.seed` SQL loader
  dev_seed.py        # `python -m app.dev_seed` test users (dev only)
docker/              # entrypoint.sh
migrations/          # Alembic
plan/                # design notes
scripts/             # ops scripts (vendor fetch, ...)
seeds/wc2026.sql     # World Cup 2026 fixtures, teams, venues, groups
tests/               # pytest suite (testcontainers + FastAPI TestClient)
```

## Credits

The tournament emblem shown on the home page and the auth pages is
["2026 FIFA World Cup emblem"](https://commons.wikimedia.org/wiki/File:2026_FIFA_World_Cup_emblem.svg)
by Wikidasher, used under the
[Creative Commons Attribution-ShareAlike 4.0 International](https://creativecommons.org/licenses/by-sa/4.0/)
licence. The SVG was downloaded once from Wikimedia Commons and committed
verbatim at `app/static/img/wc2026/emblem.svg`.

Note that the underlying FIFA emblem is a registered trademark; Predictr
displays the Wikimedia version under nominative-fair-use as a
non-commercial fan project. If the project ever monetises, the image must
be removed or replaced.
