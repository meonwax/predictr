"""The database-configured site title drives the shared page chrome.

The ``config.title`` row is rendered into the ``<title>`` tag, the navbar
brand, and the footer on every page. These tests temporarily override the
seeded title (which happens to equal the brand name) with a distinctive
value so we can prove the value really comes from the database and not a
hardcoded ``brand.name`` string.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

CUSTOM_TITLE = "Office Cup 2026"


@pytest.fixture()
def custom_title(seeded_engine: Engine) -> Iterator[None]:
    """Set a distinctive config title for the test, then restore the seed."""
    with seeded_engine.begin() as conn:
        original = conn.execute(text("SELECT title FROM config ORDER BY id LIMIT 1")).scalar_one()
        conn.execute(text("UPDATE config SET title = :title"), {"title": CUSTOM_TITLE})
    try:
        yield
    finally:
        with seeded_engine.begin() as conn:
            conn.execute(text("UPDATE config SET title = :title"), {"title": original})


def test_site_title_in_head_navbar_and_footer(
    auth_client: TestClient,
    custom_title: None,
) -> None:
    """A custom DB title surfaces in the head <title>, navbar, and footer."""
    page = auth_client.get("/games").text
    # Head <title>: "<page> | <site title>".
    assert f"| {CUSTOM_TITLE}</title>" in page
    # Head <title>, navbar brand, and footer all render the configured title.
    assert page.count(CUSTOM_TITLE) >= 3


def test_site_title_falls_back_to_brand_on_unknown_path(auth_client: TestClient) -> None:
    """A 404 page has no route dependency, so it falls back to the brand name."""
    r = auth_client.get("/no-such-page")
    assert r.status_code == 404
    assert "Predictr" in r.text
