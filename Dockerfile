# syntax=docker/dockerfile:1.7

# ---------------------------------------------------------------------------
# Builder: install the locked dependency set into a project-local venv using uv.
# ---------------------------------------------------------------------------
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# Install dependencies first (without the project itself) so the layer can be
# cached across source-only changes.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    uv sync --frozen --no-install-project --no-dev

# Copy the project sources and install the project itself.
COPY pyproject.toml uv.lock README.md LICENSE ./
COPY app ./app
COPY migrations ./migrations
COPY alembic.ini ./
COPY seeds ./seeds
COPY scripts ./scripts

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Fetch (and SHA-256-verify) the third-party JS/CSS we ship with the app.
# These live in app/static/vendor/ at runtime; the script is a no-op if the
# files are already present with the expected hashes (cache-friendly).
RUN uv run python scripts/fetch_vendor_assets.py --quiet

# ---------------------------------------------------------------------------
# Runtime: slim Python image with only the project + venv, runs as non-root.
# ---------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/app/.venv/bin:$PATH

RUN groupadd --gid 1000 predictr \
 && useradd --uid 1000 --gid predictr --no-create-home --home-dir /app --shell /usr/sbin/nologin predictr

WORKDIR /app

COPY --from=builder --chown=predictr:predictr /app /app
COPY --chown=predictr:predictr docker/entrypoint.sh /app/docker/entrypoint.sh
RUN chmod +x /app/docker/entrypoint.sh

USER predictr

EXPOSE 8000

# --forwarded-allow-ips="*" lets uvicorn honour the X-Forwarded-Proto /
# X-Forwarded-For headers from the reverse proxy. uvicorn enables
# --proxy-headers by default but only trusts them from 127.0.0.1; inside the
# container the host's Caddy arrives via the Docker bridge gateway, so without
# this the forwarded scheme is dropped, every request looks like plain HTTP,
# and url_for() emits http:// asset URLs that browsers flag as mixed content
# on the HTTPS page. Trusting "*" is safe because the app port is published on
# loopback only (APP_BIND defaults to 127.0.0.1:8000), so the host's Caddy is
# the sole client that can reach it.
ENTRYPOINT ["/app/docker/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--forwarded-allow-ips", "*"]
