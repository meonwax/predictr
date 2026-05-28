"""Smoke tests for the FastAPI app shell.

These never touch the database - they only verify that the ASGI app can be
constructed and that the healthcheck endpoint behaves.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_healthz_returns_ok() -> None:
    client = TestClient(app)
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_app_title_and_version_are_set() -> None:
    """Version is sourced from ``pyproject.toml`` via ``importlib.metadata``
    and re-exported as ``app.__version__``; the FastAPI ``app.version``
    attribute must round-trip whatever the package metadata reports."""
    from app import __version__

    assert app.title == "Predictr"
    assert app.version == __version__
    # Sanity check on the format - we always ship a PEP 440 release-ish
    # string, never the ``0.0.0+unknown`` placeholder.
    assert not app.version.endswith("+unknown")
