"""End-to-end tests for the i18n surface across HTTP routes.

These verify that:

* the application reacts to ``Settings.default_language`` for anonymous
  users (production default is German, the test suite forces English);
* a logged-in user's ``preferred_language`` overrides the site default
  on every page they touch;
* the ``<html lang>`` attribute reflects the active language so screen
  readers, search engines, and ``hreflang``-aware caches behave;
* error messages emitted from POST handlers honour the language at
  render time, not at exception-raise time.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings


@pytest.fixture()
def german_default(auth_client: TestClient) -> Iterator[TestClient]:
    """Flip ``Settings.default_language`` to ``"de"`` for one test.

    The session-wide default is English (set in :mod:`conftest`); this
    fixture lets a single test exercise the real production default
    without polluting other tests.
    """
    settings = get_settings()
    original = settings.default_language
    settings.default_language = "de"
    try:
        yield auth_client
    finally:
        settings.default_language = original


def _register_and_login(client: TestClient, email: str = "a@example.com") -> None:
    client.post(
        "/register",
        data={"name": "Test", "email": email, "password": "hunter222"},
        follow_redirects=False,
    )
    client.post(
        "/login",
        data={"email": email, "password": "hunter222"},
        follow_redirects=False,
    )


def _set_language(client: TestClient, language: str) -> None:
    r = client.post(
        "/settings/profile",
        data={"name": "Test", "preferred_language": language},
        follow_redirects=False,
    )
    assert r.status_code == 303


# ---------------------------------------------------------------------------
# Anonymous visitors follow Settings.default_language
# ---------------------------------------------------------------------------


def test_anonymous_default_is_english_in_test_suite(auth_client: TestClient) -> None:
    """The conftest forces English; anonymous visitors must see English."""
    page = auth_client.get("/games").text
    assert "Tournament schedule" in page
    assert 'lang="en"' in page
    assert "Spielplan" not in page


def test_anonymous_default_can_be_overridden_to_german(german_default: TestClient) -> None:
    page = german_default.get("/games").text
    assert "Spielplan" in page
    assert 'lang="de"' in page
    assert "Tournament schedule" not in page


# ---------------------------------------------------------------------------
# Logged-in users follow preferred_language
# ---------------------------------------------------------------------------


def test_logged_in_user_inherits_site_default(auth_client: TestClient) -> None:
    """A freshly-registered user has ``preferred_language=None``; rendering
    therefore falls back to the site default (English in this suite)."""
    _register_and_login(auth_client)
    page = auth_client.get("/games").text
    assert "Tournament schedule" in page
    assert 'lang="en"' in page


def test_user_can_switch_to_german_via_settings(auth_client: TestClient) -> None:
    _register_and_login(auth_client)
    _set_language(auth_client, "de")
    page = auth_client.get("/games").text
    assert "Spielplan" in page
    assert 'lang="de"' in page
    # Navbar reflects the language too.
    assert "Spiele" in page
    assert "Anmelden" not in page  # already signed in
    assert "Abmelden" in page


def test_user_can_switch_back_to_english(auth_client: TestClient) -> None:
    _register_and_login(auth_client)
    _set_language(auth_client, "de")
    _set_language(auth_client, "en")
    page = auth_client.get("/games").text
    assert 'lang="en"' in page
    assert "Tournament schedule" in page


# ---------------------------------------------------------------------------
# Auth / register / lostpwd pages honour the site default
# ---------------------------------------------------------------------------


def test_register_page_localises_for_german_default(german_default: TestClient) -> None:
    page = german_default.get("/register").text
    assert "Konto anlegen" in page
    assert "Create your account" not in page


def test_login_page_localises_for_german_default(german_default: TestClient) -> None:
    page = german_default.get("/login").text
    assert "Anmelden" in page
    assert "Sign in" not in page


def test_lostpwd_page_localises_for_german_default(german_default: TestClient) -> None:
    page = german_default.get("/lostpwd").text
    assert "Passwort zurücksetzen" in page
    assert "Reset your password" not in page


# ---------------------------------------------------------------------------
# Form-validation errors are translated, not literal English
# ---------------------------------------------------------------------------


def test_login_invalid_credentials_translates_for_german_default(
    german_default: TestClient,
) -> None:
    r = german_default.post(
        "/login",
        data={"email": "no@one.example", "password": "wrong"},
        follow_redirects=False,
    )
    assert r.status_code == 401
    assert "E-Mail oder Passwort sind falsch." in r.text


def test_register_short_name_translates_for_german_default(
    german_default: TestClient,
) -> None:
    r = german_default.post(
        "/register",
        data={"name": "A", "email": "x@example.com", "password": "hunter222"},
        follow_redirects=False,
    )
    assert r.status_code == 400
    assert "mindestens 2 Zeichen" in r.text


def test_bet_validation_error_uses_user_language(auth_client: TestClient) -> None:
    """The same POST returns a German error after the user switches."""
    _register_and_login(auth_client)
    _set_language(auth_client, "de")
    r = auth_client.post(
        "/bets/1",
        data={"score_home": "2", "score_away": ""},
        headers={"HX-Request": "true"},
    )
    assert r.status_code == 200
    # German wording from `error.score.partial`
    assert "beide Tore eintragen" in r.text


def test_shout_too_short_translates_per_user(auth_client: TestClient) -> None:
    _register_and_login(auth_client)
    _set_language(auth_client, "de")
    r = auth_client.post(
        "/shouts",
        data={"message": "   "},
        headers={"HX-Request": "true"},
    )
    assert r.status_code == 200
    assert "Nachricht darf nicht leer sein" in r.text


# ---------------------------------------------------------------------------
# Date filter renders localised weekday / month abbreviations
# ---------------------------------------------------------------------------


def test_german_user_sees_german_weekdays_on_games(auth_client: TestClient) -> None:
    _register_and_login(auth_client)
    _set_language(auth_client, "de")
    page = auth_client.get("/games").text
    # The opener (Mexico v. ?) kicks off Thu 11 Jun 2026 - German "Do" / "Jun".
    # We just check that *some* German abbreviation appears so the test is
    # robust against schedule tweaks.
    german_days = ("Mo,", "Di,", "Mi,", "Do,", "Fr,", "Sa,", "So,")
    assert any(d in page for d in german_days), "expected at least one German weekday abbreviation"


def test_english_user_sees_english_weekdays_on_games(auth_client: TestClient) -> None:
    _register_and_login(auth_client)
    page = auth_client.get("/games").text
    english_days = ("Mon,", "Tue,", "Wed,", "Thu,", "Fri,", "Sat,", "Sun,")
    assert any(d in page for d in english_days), (
        "expected at least one English weekday abbreviation"
    )
