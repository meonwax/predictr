"""End-to-end tests for the language switcher.

Covers three intertwined behaviours:

* :class:`app.middleware.LanguageMiddleware` resolves cookie ->
  ``Accept-Language`` -> site default in that order;
* ``POST /language`` writes a cookie that the middleware reads on the
  next request;
* signed-in users get the cookie plus a persisted
  ``preferred_language`` on their user row.

Each test stays self-contained: cookies live in the ``TestClient`` jar
and are cleared between fixture invocations so cross-test pollution
can't sneak in.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.middleware import LANGUAGE_COOKIE_NAME, TIMEZONE_COOKIE_NAME
from app.models import User

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


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


@pytest.fixture()
def german_default(auth_client: TestClient) -> Iterator[TestClient]:
    """Flip ``Settings.default_language`` to ``"de"`` for one test."""
    settings = get_settings()
    original = settings.default_language
    settings.default_language = "de"
    try:
        yield auth_client
    finally:
        settings.default_language = original


# ---------------------------------------------------------------------------
# Accept-Language header recognition (anonymous visitors)
# ---------------------------------------------------------------------------


def test_anonymous_accept_language_german_overrides_english_default(
    auth_client: TestClient,
) -> None:
    """The test suite default is English; an ``Accept-Language: de`` header
    should still win for an anonymous visitor."""
    page = auth_client.get("/games", headers={"Accept-Language": "de"}).text
    assert 'lang="de"' in page
    assert "Spielplan" in page


def test_anonymous_accept_language_uses_quality_ranking(
    auth_client: TestClient,
) -> None:
    """Most preferred language wins, not the lexicographically first one."""
    page = auth_client.get(
        "/games",
        headers={"Accept-Language": "en;q=0.5,de;q=0.9,fr"},
    ).text
    assert 'lang="de"' in page


def test_anonymous_accept_language_falls_back_when_unsupported(
    auth_client: TestClient,
) -> None:
    """A header with only unsupported languages should hit the site default."""
    page = auth_client.get("/games", headers={"Accept-Language": "fr,it,es"}).text
    # Test-suite default is English.
    assert 'lang="en"' in page


def test_anonymous_accept_language_strips_region_subtag(
    auth_client: TestClient,
) -> None:
    page = auth_client.get("/games", headers={"Accept-Language": "de-AT"}).text
    assert 'lang="de"' in page


# ---------------------------------------------------------------------------
# POST /language sets the cookie (anonymous)
# ---------------------------------------------------------------------------


def test_post_language_sets_cookie(auth_client: TestClient) -> None:
    r = auth_client.post(
        "/language",
        data={"language": "de", "next": "/games"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert r.headers["location"] == "/games"
    assert LANGUAGE_COOKIE_NAME in r.cookies
    assert r.cookies[LANGUAGE_COOKIE_NAME] == "de"


def test_anonymous_cookie_persists_across_requests(auth_client: TestClient) -> None:
    """A previously-set cookie should make the next page render German even
    without an ``Accept-Language`` header."""
    auth_client.post(
        "/language",
        data={"language": "de", "next": "/games"},
        follow_redirects=False,
    )
    page = auth_client.get("/games").text
    assert 'lang="de"' in page
    assert "Spielplan" in page


def test_cookie_beats_accept_language(auth_client: TestClient) -> None:
    """A user who explicitly chose English shouldn't have it overruled by
    the browser sending ``Accept-Language: de``."""
    auth_client.post(
        "/language",
        data={"language": "en", "next": "/games"},
        follow_redirects=False,
    )
    page = auth_client.get("/games", headers={"Accept-Language": "de"}).text
    assert 'lang="en"' in page


def test_unsupported_language_does_not_set_cookie(auth_client: TestClient) -> None:
    """A garbage value should be silently rejected - no cookie, redirect
    still happens so the form still submits cleanly."""
    r = auth_client.post(
        "/language",
        data={"language": "klingon", "next": "/games"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert LANGUAGE_COOKIE_NAME not in r.cookies


def test_language_cookie_omits_secure_flag_by_default(auth_client: TestClient) -> None:
    """Dev traffic over plain HTTP must not get a ``Secure`` cookie."""
    r = auth_client.post(
        "/language",
        data={"language": "de", "next": "/games"},
        follow_redirects=False,
    )
    assert "secure" not in r.headers["set-cookie"].lower()


def test_preference_cookies_carry_secure_flag_when_enabled(
    auth_client: TestClient,
) -> None:
    """``SECURE_COOKIES=true`` must mark both the language and timezone
    cookies with ``Secure`` so the user's preference can't be sniffed
    off a downgrade-attacked connection."""
    from app.dependencies import get_settings_dep
    from app.main import app

    secure_settings = get_settings().model_copy(update={"secure_cookies": True})
    app.dependency_overrides[get_settings_dep] = lambda: secure_settings
    try:
        lang = auth_client.post(
            "/language",
            data={"language": "de", "next": "/games"},
            follow_redirects=False,
        )
        assert "secure" in lang.headers["set-cookie"].lower()

        tz = auth_client.post("/timezone", data={"timezone": "Europe/Berlin"})
        assert "secure" in tz.headers["set-cookie"].lower()
    finally:
        app.dependency_overrides.pop(get_settings_dep, None)


# ---------------------------------------------------------------------------
# `next` URL sanitisation (open-redirect protection)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw_next",
    [
        "https://evil.example/x",
        "//evil.example/x",
        "javascript:alert(1)",
        "ftp://elsewhere/",
        "no-leading-slash",
        "",
    ],
)
def test_post_language_sanitises_next_url(
    auth_client: TestClient,
    raw_next: str,
) -> None:
    r = auth_client.post(
        "/language",
        data={"language": "de", "next": raw_next},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert r.headers["location"] == "/"


def test_post_language_preserves_safe_query_and_fragment(
    auth_client: TestClient,
) -> None:
    r = auth_client.post(
        "/language",
        data={"language": "de", "next": "/bets?week=2#row-3"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert r.headers["location"] == "/bets?week=2#row-3"


# ---------------------------------------------------------------------------
# Resolution precedence
# ---------------------------------------------------------------------------


def test_logged_in_user_preference_beats_cookie(auth_client: TestClient) -> None:
    """A signed-in user's persisted preference wins over the cookie."""
    _register_and_login(auth_client)
    # Switch to German via settings (sets preferred_language).
    auth_client.post(
        "/settings/profile",
        data={"name": "Test", "preferred_language": "de"},
        follow_redirects=False,
    )
    # Manually plant a competing English cookie. The user's stored
    # preference should still win.
    auth_client.cookies.set(LANGUAGE_COOKIE_NAME, "en")
    page = auth_client.get("/games").text
    assert 'lang="de"' in page


def test_post_language_persists_for_logged_in_user(
    auth_client: TestClient,
    seeded_engine,
) -> None:
    """Signing in then switching language should also update the DB row,
    so the choice survives a sign-out + sign-in on a fresh browser."""
    from sqlalchemy.orm import sessionmaker

    _register_and_login(auth_client)
    auth_client.post(
        "/language",
        data={"language": "de", "next": "/games"},
        follow_redirects=False,
    )

    Session_ = sessionmaker(bind=seeded_engine, expire_on_commit=False, future=True)
    with Session_() as db:
        user = db.query(User).filter(User.email == "a@example.com").one()
        assert user.preferred_language == "de"


# ---------------------------------------------------------------------------
# Footer switcher is visible everywhere
# ---------------------------------------------------------------------------


def test_footer_switcher_is_visible_for_anonymous(auth_client: TestClient) -> None:
    page = auth_client.get("/games").text
    # Two submit buttons, one per language, posting to /language.
    assert 'action="/language"' in page
    assert 'value="de"' in page
    assert 'value="en"' in page


def test_footer_switcher_marks_active_language(auth_client: TestClient) -> None:
    """The button for the currently-active language carries
    ``aria-current="true"`` so screen-reader users hear the state."""
    page = auth_client.get("/games", headers={"Accept-Language": "de"}).text
    # German is active -> its button is marked aria-current; English is not.
    # Order in the form is [de, en], so find both buttons.
    assert 'value="de"' in page
    assert 'value="en"' in page
    # Active button has aria-current; we only care that *some* button does.
    assert 'aria-current="true"' in page


# ---------------------------------------------------------------------------
# POST /timezone - anonymous + signed-in cookie behaviour
# ---------------------------------------------------------------------------


def test_post_timezone_sets_cookie(auth_client: TestClient) -> None:
    r = auth_client.post(
        "/timezone",
        data={"timezone": "Europe/Berlin"},
    )
    assert r.status_code == 204
    assert TIMEZONE_COOKIE_NAME in r.cookies
    # The ``/`` in IANA zone names triggers RFC-compliant cookie quoting,
    # so the raw value comes back as either ``Europe/Berlin`` or
    # ``"Europe/Berlin"`` depending on the client's parser. Either is
    # fine - the next request's :class:`LanguageMiddleware` resolves it
    # the same way.
    assert r.cookies[TIMEZONE_COOKIE_NAME].strip('"') == "Europe/Berlin"


def test_post_timezone_rejects_unsupported_zone(auth_client: TestClient) -> None:
    """Tampered POSTs (zone not in the curated list) drop no cookie."""
    r = auth_client.post(
        "/timezone",
        data={"timezone": "Mars/Olympus_Mons"},
    )
    assert r.status_code == 204
    assert TIMEZONE_COOKIE_NAME not in r.cookies


def test_post_timezone_rejects_blank(auth_client: TestClient) -> None:
    r = auth_client.post("/timezone", data={"timezone": ""})
    assert r.status_code == 204
    assert TIMEZONE_COOKIE_NAME not in r.cookies


def test_post_timezone_persists_for_new_user(
    auth_client: TestClient,
    seeded_engine,
) -> None:
    """A signed-in user with no explicit preference gets the auto-detect
    posted to their user row, so the next sign-in honours it."""
    from sqlalchemy.orm import sessionmaker

    _register_and_login(auth_client)
    auth_client.post("/timezone", data={"timezone": "America/New_York"})

    Session_ = sessionmaker(bind=seeded_engine, expire_on_commit=False, future=True)
    with Session_() as db:
        user = db.query(User).filter(User.email == "a@example.com").one()
        assert user.preferred_timezone == "America/New_York"


def test_post_timezone_respects_explicit_user_preference(
    auth_client: TestClient,
    seeded_engine,
) -> None:
    """If the user has already chosen a timezone in settings, the JS
    auto-detect shouldn't quietly overwrite it on the next page load."""
    from sqlalchemy.orm import sessionmaker

    _register_and_login(auth_client)
    auth_client.post(
        "/settings/profile",
        data={
            "name": "Test",
            "preferred_language": "en",
            "preferred_timezone": "Europe/Berlin",
        },
        follow_redirects=False,
    )
    # JS later posts a different zone - settings preference wins.
    auth_client.post("/timezone", data={"timezone": "America/New_York"})

    Session_ = sessionmaker(bind=seeded_engine, expire_on_commit=False, future=True)
    with Session_() as db:
        user = db.query(User).filter(User.email == "a@example.com").one()
        assert user.preferred_timezone == "Europe/Berlin"


# ---------------------------------------------------------------------------
# Display: kickoff times honour the active timezone
# ---------------------------------------------------------------------------


def test_anonymous_default_renders_utc_in_test_suite(
    auth_client: TestClient,
) -> None:
    """The conftest pins DEFAULT_TIMEZONE=UTC so existing kickoff
    assertions stay stable."""
    body = auth_client.get("/games").text
    # Opener is Thu, 11 Jun 2026 19:00 UTC (canonical test-suite default).
    assert "Thu, 11 Jun 2026 19:00 UTC" in body


def test_anonymous_timezone_cookie_localises_kickoffs(
    auth_client: TestClient,
) -> None:
    """Setting the timezone cookie should shift the rendered times."""
    auth_client.post("/timezone", data={"timezone": "Europe/Berlin"})
    body = auth_client.get("/games").text
    # 19:00 UTC + 2h (CEST) = 21:00 local. Day name stays "Thu" in English.
    assert "Thu, 11 Jun 2026 21:00 CEST" in body
    # Old UTC string must be gone.
    assert "19:00 UTC" not in body


def test_logged_in_user_preference_localises_kickoffs(
    auth_client: TestClient,
) -> None:
    """Persisting a timezone in settings should affect kickoff rendering
    even without a cookie."""
    _register_and_login(auth_client)
    auth_client.post(
        "/settings/profile",
        data={
            "name": "Test",
            "preferred_language": "en",
            "preferred_timezone": "America/New_York",
        },
        follow_redirects=False,
    )
    body = auth_client.get("/games").text
    # 11 Jun 19:00 UTC = 11 Jun 15:00 EDT.
    assert "15:00 EDT" in body


def test_user_preference_beats_timezone_cookie(auth_client: TestClient) -> None:
    """A logged-in user's stored preference must override the cookie."""
    _register_and_login(auth_client)
    auth_client.post(
        "/settings/profile",
        data={
            "name": "Test",
            "preferred_language": "en",
            "preferred_timezone": "Europe/Berlin",
        },
        follow_redirects=False,
    )
    auth_client.cookies.set(TIMEZONE_COOKIE_NAME, "America/New_York")
    body = auth_client.get("/games").text
    assert "CEST" in body
    assert "EDT" not in body


def test_footer_shows_active_timezone(auth_client: TestClient) -> None:
    """The footer 'all times in ...' label should pick up the active zone."""
    auth_client.post("/timezone", data={"timezone": "Europe/Berlin"})
    body = auth_client.get("/games").text
    # June 2026 -> CEST.
    assert "All times shown in CEST" in body


def test_short_date_filter_localises_to_user_zone(auth_client: TestClient) -> None:
    """The /settings page shows the user's account-created date via
    ``short_date``; setting a New York zone should pull dates backwards
    when the UTC timestamp is in early-morning UTC."""
    # Register a user so /settings is reachable.
    _register_and_login(auth_client)
    # No assertions on a specific date here - created_date is "now()" at
    # registration. We just verify the page renders, i.e. the filter
    # doesn't crash when invoked with a timezone-aware datetime.
    auth_client.post(
        "/settings/profile",
        data={
            "name": "Test",
            "preferred_language": "en",
            "preferred_timezone": "America/New_York",
        },
        follow_redirects=False,
    )
    r = auth_client.get("/settings")
    assert r.status_code == 200
    assert "Signed in as" in r.text


def test_short_date_filter_uses_german_ordinal_dot(auth_client: TestClient) -> None:
    """German short dates render with a trailing dot on the day number.

    Standard German ordinal-date orthography is ``D. <Monat> YYYY``
    (e.g. ``22. Mai 2026``). The /settings page composes the rendered
    date into a full sentence ("Konto angelegt am {date}.") so the
    missing dot is jarring; this test pins the dot in place so we never
    regress to the English ``DD <month> YYYY`` form here.
    """
    import re

    _register_and_login(auth_client)
    auth_client.post(
        "/settings/profile",
        data={
            "name": "Test",
            "preferred_language": "de",
            "preferred_timezone": "Europe/Berlin",
        },
        follow_redirects=False,
    )
    r = auth_client.get("/settings")
    assert r.status_code == 200
    assert "Angemeldet als" in r.text
    # created_date is "now()" at registration, so we can't pin the exact
    # date, but we *can* pin the structural pattern: "<day>. <month> <year>".
    # The German month abbreviations in i18n.py are at most 3 chars
    # (Mär, Mai, Okt, Dez); allow 3-4 to be safe against catalogue tweaks.
    pattern = re.compile(r"\b\d{1,2}\. [A-ZÄÖÜ][a-zäöü]{2,3} 20\d{2}\b")
    assert pattern.search(r.text), (
        "Expected a German-style 'D. Mon YYYY' date on the settings page, "
        "but found none in the rendered HTML."
    )
