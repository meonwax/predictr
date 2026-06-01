"""Integration tests for the ``/`` home dashboard.

Exercises both visitor states (anonymous + authenticated) and confirms
each panel renders the right empty / non-empty state. Live and upcoming
matches are driven by mutating the seeded ``game.kickoff_time`` /
``score`` columns inside the test, then reset by an autouse fixture so
cross-test pollution can't leak. Shouts and answers are written via the
service layer to keep the wiring honest.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from app.middleware import LANGUAGE_COOKIE_NAME
from app.models import Question

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _register_and_login(
    client: TestClient,
    *,
    name: str = "Alice",
    email: str = "alice@example.com",
    password: str = "hunter222",
) -> None:
    client.post(
        "/register",
        data={"name": name, "email": email, "password": password},
        follow_redirects=False,
    )
    client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=False,
    )


@pytest.fixture()
def db(seeded_engine) -> Iterator[Session]:
    Session_ = sessionmaker(bind=seeded_engine, expire_on_commit=False, future=True)
    with Session_() as s:
        yield s


@pytest.fixture()
def logged_in_client(auth_client: TestClient) -> TestClient:
    _register_and_login(auth_client)
    return auth_client


@pytest.fixture(autouse=True)
def _reset_game_state(seeded_engine) -> Iterator[None]:
    """Restore game scores + kickoff times after every home test.

    The home page is sensitive to where ``now`` falls in the schedule,
    so several tests temporarily move a game's kickoff into the past
    or the immediate future. This fixture undoes those mutations so
    other home tests (and other test files using the same session-
    scoped engine) start from a clean state.
    """
    with seeded_engine.begin() as conn:
        rows = conn.execute(text("SELECT id, kickoff_time FROM game ORDER BY id")).all()
        backup = {row.id: row.kickoff_time for row in rows}
    yield
    with seeded_engine.begin() as conn:
        conn.execute(text("UPDATE game SET score_home = NULL, score_away = NULL, notes = NULL"))
        for game_id, kickoff in backup.items():
            conn.execute(
                text("UPDATE game SET kickoff_time = :k WHERE id = :id"),
                {"k": kickoff, "id": game_id},
            )


@pytest.fixture(autouse=True)
def _wipe_questions_and_shouts(seeded_engine) -> Iterator[None]:
    """Home tests own the questions + shouts tables for the run."""
    with seeded_engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE shout, answer, question RESTART IDENTITY CASCADE"))
    yield
    with seeded_engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE shout, answer, question RESTART IDENTITY CASCADE"))


def _force_game_live(seeded_engine, game_id: int) -> None:
    """Move *game_id*'s kickoff to 30 minutes ago, leave score NULL."""
    past = datetime.now(UTC) - timedelta(minutes=30)
    with seeded_engine.begin() as conn:
        conn.execute(
            text(
                "UPDATE game SET kickoff_time = :k, score_home = NULL, "
                "score_away = NULL WHERE id = :id"
            ),
            {"k": past, "id": game_id},
        )


def _add_question(
    db: Session,
    *,
    text_: str,
    deadline_offset: timedelta,
    points: int = 5,
) -> Question:
    """Insert an admin-style question with deadline relative to now."""
    q = Question(
        question=text_,
        correct_answer="something",
        points=points,
        deadline=datetime.now(UTC) + deadline_offset,
    )
    db.add(q)
    db.commit()
    db.refresh(q)
    return q


# ---------------------------------------------------------------------------
# Anonymous visitor
# ---------------------------------------------------------------------------


def test_root_returns_200_for_anonymous_visitor(auth_client: TestClient) -> None:
    r = auth_client.get("/")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/html")


def test_anonymous_visitor_sees_hero_and_ctas(auth_client: TestClient) -> None:
    page = auth_client.get("/").text
    assert "Welcome to" in page
    # Sign-in + register CTAs targeting the right URLs.
    assert 'href="/register"' in page
    assert 'href="/login"' in page
    assert 'href="/info"' in page


def test_anonymous_visitor_does_not_see_user_only_panels(
    auth_client: TestClient,
) -> None:
    """Open-questions and shouts panels are only shown to logged-in users."""
    page = auth_client.get("/").text
    assert "Open questions" not in page
    assert "Recent shouts" not in page


# ---------------------------------------------------------------------------
# Authenticated visitor: greeting + empty panels
# ---------------------------------------------------------------------------


def test_logged_in_user_sees_personalised_greeting(
    logged_in_client: TestClient,
) -> None:
    page = logged_in_client.get("/").text
    assert "Welcome, Alice!" in page


def test_logged_in_user_sees_all_panels_in_empty_state(
    logged_in_client: TestClient,
) -> None:
    """With no live games / questions / shouts every panel shows its empty state."""
    page = logged_in_client.get("/").text
    assert "No live matches right now." in page
    assert "No open questions right now." in page
    assert "No shouts yet." in page


def test_logged_in_user_sees_upcoming_matches_strip(
    logged_in_client: TestClient,
) -> None:
    """The WC 2026 seed always has at least one upcoming match in this test
    suite (kickoff_time values are in 2026 + the test clock floats forward),
    so the panel should render its non-empty body."""
    page = logged_in_client.get("/").text
    assert "Upcoming matches" in page
    # Not the empty-state copy.
    assert "No more matches scheduled." not in page


# ---------------------------------------------------------------------------
# Live matches panel
# ---------------------------------------------------------------------------


def test_live_panel_lights_up_when_a_game_kicks_off(
    logged_in_client: TestClient,
    seeded_engine,
) -> None:
    _force_game_live(seeded_engine, game_id=1)
    page = logged_in_client.get("/").text
    assert "Live now" in page
    # The "live" indicator badge wording from the i18n catalogue.
    assert "live" in page.lower()
    # Empty-state copy must NOT appear when a live game is present.
    assert "No live matches right now." not in page


# ---------------------------------------------------------------------------
# Open questions panel
# ---------------------------------------------------------------------------


def test_questions_panel_shows_open_questions(
    logged_in_client: TestClient,
    db: Session,
) -> None:
    _add_question(
        db,
        text_="Who scores the most goals?",
        deadline_offset=timedelta(days=3),
    )
    _add_question(
        db,
        text_="Who reaches the final?",
        deadline_offset=timedelta(days=10),
    )
    page = logged_in_client.get("/").text
    assert "Who scores the most goals?" in page
    assert "Who reaches the final?" in page
    # Unanswered nudge banner appears when at least one question is open + unanswered.
    assert "open questions waiting" in page


def test_questions_panel_hides_questions_past_deadline(
    logged_in_client: TestClient,
    db: Session,
) -> None:
    _add_question(
        db,
        text_="Past question that should not appear",
        deadline_offset=timedelta(days=-1),
    )
    page = logged_in_client.get("/").text
    assert "Past question that should not appear" not in page
    assert "No open questions right now." in page


# ---------------------------------------------------------------------------
# Imminent-bet nudge
# ---------------------------------------------------------------------------


def _move_game_to(seeded_engine, *, game_id: int, kickoff: datetime) -> None:
    with seeded_engine.begin() as conn:
        conn.execute(
            text("UPDATE game SET kickoff_time = :k WHERE id = :id"),
            {"k": kickoff, "id": game_id},
        )


# The English copy contains an apostrophe which Jinja escapes as &#39;.
# Match on a substring without it so the assertions don't depend on the
# exact HTML-escape representation.
_UNBET_NUDGE_SNIPPET = "upcoming matches you"


def test_unbet_nudge_hidden_when_no_imminent_games(
    logged_in_client: TestClient,
    seeded_engine,
) -> None:
    """If every fixture is more than 24h away, the imminent-bet nudge stays hidden."""
    with seeded_engine.begin() as conn:
        conn.execute(
            text("UPDATE game SET kickoff_time = :k"),
            {"k": datetime.now(UTC) + timedelta(days=14)},
        )
    page = logged_in_client.get("/").text
    assert _UNBET_NUDGE_SNIPPET not in page


def test_unbet_nudge_shown_when_imminent_game_has_no_bet(
    logged_in_client: TestClient,
    seeded_engine,
) -> None:
    """A match kicking off in the next 24h with no bet from the user
    triggers the yellow nudge."""
    # Push every game beyond the imminent window first, then bring just
    # one back inside it, so we control the nudge precisely.
    with seeded_engine.begin() as conn:
        conn.execute(
            text("UPDATE game SET kickoff_time = :k"),
            {"k": datetime.now(UTC) + timedelta(days=14)},
        )
    _move_game_to(seeded_engine, game_id=1, kickoff=datetime.now(UTC) + timedelta(hours=12))
    page = logged_in_client.get("/").text
    assert _UNBET_NUDGE_SNIPPET in page
    # Same yellow-nudge layout as the unanswered-questions reminder.
    assert "btn btn-sm btn-warning" in page
    assert 'href="/bets"' in page


def test_unbet_nudge_hidden_after_user_bets_on_imminent_game(
    logged_in_client: TestClient,
    seeded_engine,
) -> None:
    """Once every imminent match has a bet, the nudge disappears."""
    with seeded_engine.begin() as conn:
        conn.execute(
            text("UPDATE game SET kickoff_time = :k"),
            {"k": datetime.now(UTC) + timedelta(days=14)},
        )
    _move_game_to(seeded_engine, game_id=1, kickoff=datetime.now(UTC) + timedelta(hours=12))

    r = logged_in_client.post(
        "/bets/1",
        data={"score_home": "2", "score_away": "1"},
        headers={"HX-Request": "true"},
    )
    assert r.status_code == 200, r.text

    page = logged_in_client.get("/").text
    assert _UNBET_NUDGE_SNIPPET not in page


def test_unbet_nudge_ignores_kicked_off_games(
    logged_in_client: TestClient,
    seeded_engine,
) -> None:
    """A match whose kickoff has already passed is not actionable any more
    and must not surface in the nudge."""
    with seeded_engine.begin() as conn:
        conn.execute(
            text("UPDATE game SET kickoff_time = :k"),
            {"k": datetime.now(UTC) + timedelta(days=14)},
        )
    _move_game_to(seeded_engine, game_id=1, kickoff=datetime.now(UTC) - timedelta(minutes=30))
    page = logged_in_client.get("/").text
    assert _UNBET_NUDGE_SNIPPET not in page


def test_unbet_nudge_hidden_for_anonymous_visitor(
    auth_client: TestClient,
    seeded_engine,
) -> None:
    """The nudge is user-specific; anonymous visitors never see it even
    when an imminent unbet match is technically present."""
    with seeded_engine.begin() as conn:
        conn.execute(
            text("UPDATE game SET kickoff_time = :k"),
            {"k": datetime.now(UTC) + timedelta(days=14)},
        )
    _move_game_to(seeded_engine, game_id=1, kickoff=datetime.now(UTC) + timedelta(hours=12))
    page = auth_client.get("/").text
    assert _UNBET_NUDGE_SNIPPET not in page


# ---------------------------------------------------------------------------
# Recent shouts panel
# ---------------------------------------------------------------------------


def test_shouts_panel_shows_recent_messages(
    logged_in_client: TestClient,
) -> None:
    logged_in_client.post("/shouts", data={"message": "Hello from the home test"})
    page = logged_in_client.get("/").text
    assert "Hello from the home test" in page
    assert "No shouts yet." not in page


# ---------------------------------------------------------------------------
# Localisation
# ---------------------------------------------------------------------------


def test_home_renders_german_when_language_cookie_set(
    auth_client: TestClient,
) -> None:
    auth_client.cookies.set(LANGUAGE_COOKIE_NAME, "de")
    page = auth_client.get("/").text
    assert "Willkommen bei" in page
    assert "Anmelden" in page
    assert "Konto anlegen" in page


def test_home_nav_link_is_active_on_root(logged_in_client: TestClient) -> None:
    """The Home nav item is highlighted as active when we're on ``/``."""
    page = logged_in_client.get("/").text
    # Looks for the active class on the Home link. The id is implicit via
    # the icon class, but the nav label is the most stable handle.
    assert 'class="nav-link active"' in page
    # url_for renders absolute URLs in the TestClient (http://testserver/),
    # so check the path component instead of a bare ``href="/"``.
    assert 'http://testserver/"' in page


# ---------------------------------------------------------------------------
# User without a name still renders cleanly
# ---------------------------------------------------------------------------


def test_home_handles_an_anonymous_user_with_no_questions_or_games(
    auth_client: TestClient,
    seeded_engine,
) -> None:
    """Even if every upcoming match were removed, ``/`` must not 500."""
    with seeded_engine.begin() as conn:
        # Push every kickoff into the far past so nothing is upcoming.
        conn.execute(text("UPDATE game SET kickoff_time = '2020-01-01T00:00:00+00:00'"))
    r = auth_client.get("/")
    assert r.status_code == 200
    assert "No more matches scheduled." in r.text
