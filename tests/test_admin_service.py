"""Unit tests for :mod:`app.services.admin`."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.orm import Session, sessionmaker

from app.models import Game, User
from app.services.admin import (
    MAX_NOTES_LEN,
    GameNotFound,
    InvalidTeamAssignment,
    NotesTooLong,
    clear_game_result,
    get_dashboard_stats,
    list_games_for_admin,
    list_teams_grouped,
    set_game_result,
    set_game_teams,
)
from app.services.bets import InvalidScore, upsert_bet
from app.services.users import RegistrationData, register_user

GAME_OPENER_ID = 1
GAME_OPENER_KICKOFF = datetime(2026, 6, 11, 19, 0, tzinfo=UTC)
# First Round of 32 match in the WC 2026 seed, group_id='r32', both team
# slots NULL with placeholders '2A' / '2B'.
GAME_R32_FIRST_ID = 73


@pytest.fixture()
def fresh_db(clean_user_tables: None, seeded_engine) -> Iterator[Session]:
    Session_ = sessionmaker(bind=seeded_engine, expire_on_commit=False, future=True)
    with Session_() as session:
        yield session


@pytest.fixture()
def user(fresh_db: Session) -> User:
    return register_user(
        fresh_db,
        RegistrationData(name="Admin", email="admin@example.com", password="hunter222"),
    )


# Tests in this module set game.score_home/away on shared seeded rows.
# Always reset them on teardown to avoid leaking state into other tests.
@pytest.fixture(autouse=True)
def _reset_game_scores(seeded_engine) -> Iterator[None]:
    yield
    with seeded_engine.begin() as conn:
        from sqlalchemy import text

        conn.execute(text("UPDATE game SET score_home = NULL, score_away = NULL, notes = NULL"))


# Restore the knockout team slots to NULL (their seeded state) so each
# test starts from a clean bracket.
@pytest.fixture(autouse=True)
def _reset_knockout_teams(seeded_engine) -> Iterator[None]:
    yield
    with seeded_engine.begin() as conn:
        from sqlalchemy import text

        conn.execute(
            text(
                "UPDATE game SET team_home_id = NULL, team_away_id = NULL "
                "WHERE group_id IN ('r32','r16','qf','sf','3rd','fin')"
            )
        )


# ---------------------------------------------------------------------------
# set_game_result
# ---------------------------------------------------------------------------


def test_set_result_stores_scores(fresh_db: Session) -> None:
    game = set_game_result(
        fresh_db,
        game_id=GAME_OPENER_ID,
        score_home=3,
        score_away=2,
    )
    assert game.score_home == 3
    assert game.score_away == 2
    assert game.notes is None


def test_set_result_stores_notes(fresh_db: Session) -> None:
    game = set_game_result(
        fresh_db,
        game_id=GAME_OPENER_ID,
        score_home=1,
        score_away=1,
        notes="AET",
    )
    assert game.notes == "AET"


def test_set_result_normalises_blank_notes_to_none(fresh_db: Session) -> None:
    game = set_game_result(
        fresh_db,
        game_id=GAME_OPENER_ID,
        score_home=0,
        score_away=0,
        notes="   ",
    )
    assert game.notes is None


def test_set_result_unknown_game(fresh_db: Session) -> None:
    with pytest.raises(GameNotFound):
        set_game_result(fresh_db, game_id=99999, score_home=1, score_away=0)


@pytest.mark.parametrize(
    "home, away",
    [
        (-1, 0),
        (0, -1),
        (100, 0),
        (0, 100),
    ],
)
def test_set_result_rejects_out_of_range(
    fresh_db: Session,
    home: int,
    away: int,
) -> None:
    with pytest.raises(InvalidScore):
        set_game_result(
            fresh_db,
            game_id=GAME_OPENER_ID,
            score_home=home,
            score_away=away,
        )


def test_set_result_rejects_overly_long_notes(fresh_db: Session) -> None:
    with pytest.raises(NotesTooLong):
        set_game_result(
            fresh_db,
            game_id=GAME_OPENER_ID,
            score_home=1,
            score_away=0,
            notes="x" * (MAX_NOTES_LEN + 1),
        )


def test_set_result_can_overwrite_previous_result(fresh_db: Session) -> None:
    """Admins can correct a previously-entered result."""
    set_game_result(
        fresh_db, game_id=GAME_OPENER_ID, score_home=1, score_away=0, notes="early call"
    )
    game = set_game_result(
        fresh_db,
        game_id=GAME_OPENER_ID,
        score_home=2,
        score_away=1,
        notes="AET",
    )
    assert (game.score_home, game.score_away, game.notes) == (2, 1, "AET")


# ---------------------------------------------------------------------------
# clear_game_result
# ---------------------------------------------------------------------------


def test_clear_result_removes_scores_and_notes(fresh_db: Session) -> None:
    set_game_result(fresh_db, game_id=GAME_OPENER_ID, score_home=2, score_away=1, notes="AET")
    game = clear_game_result(fresh_db, game_id=GAME_OPENER_ID)
    assert game.score_home is None
    assert game.score_away is None
    assert game.notes is None


def test_clear_result_is_noop_when_unset(fresh_db: Session) -> None:
    game = clear_game_result(fresh_db, game_id=GAME_OPENER_ID)
    assert game.score_home is None  # was already None


def test_clear_result_unknown_game(fresh_db: Session) -> None:
    with pytest.raises(GameNotFound):
        clear_game_result(fresh_db, game_id=99999)


# ---------------------------------------------------------------------------
# list_games_for_admin
# ---------------------------------------------------------------------------


def test_list_games_returns_all(fresh_db: Session) -> None:
    games = list_games_for_admin(fresh_db)
    expected = fresh_db.query(Game).count()
    assert len(games) == expected


def test_list_games_is_sorted_by_kickoff_then_id(fresh_db: Session) -> None:
    games = list_games_for_admin(fresh_db)
    sortkeys = [(g.kickoff_time, g.id) for g in games]
    assert sortkeys == sorted(sortkeys)


# ---------------------------------------------------------------------------
# get_dashboard_stats
# ---------------------------------------------------------------------------


def test_dashboard_counts_users_and_games(fresh_db: Session, user: User) -> None:
    stats = get_dashboard_stats(
        fresh_db,
        now=GAME_OPENER_KICKOFF - timedelta(days=30),
    )
    assert stats.user_count == 1
    assert stats.admin_count == 0
    assert stats.bet_count == 0
    assert stats.games_total > 0
    assert stats.games_finished == 0
    assert stats.games_pending_result == 0
    # With "now" 30 days before the opener, every game is upcoming.
    assert stats.games_upcoming == stats.games_total


def test_dashboard_counts_bets(fresh_db: Session, user: User) -> None:
    before = GAME_OPENER_KICKOFF - timedelta(days=1)
    upsert_bet(fresh_db, user, game_id=GAME_OPENER_ID, score_home=1, score_away=1, now=before)
    stats = get_dashboard_stats(fresh_db, now=before)
    assert stats.bet_count == 1


def test_dashboard_marks_kickoff_no_result_as_pending(
    fresh_db: Session,
) -> None:
    """Games whose kickoff has passed but have no score yet count as pending."""
    after_opener = GAME_OPENER_KICKOFF + timedelta(hours=2)
    stats = get_dashboard_stats(fresh_db, now=after_opener)
    # At least the opener kicked off but has no result yet.
    assert stats.games_pending_result >= 1


def test_dashboard_marks_resulted_game_as_finished(fresh_db: Session) -> None:
    set_game_result(fresh_db, game_id=GAME_OPENER_ID, score_home=2, score_away=1)
    stats = get_dashboard_stats(fresh_db)
    assert stats.games_finished >= 1


# ---------------------------------------------------------------------------
# set_game_teams (knockout placeholder resolution)
# ---------------------------------------------------------------------------


def test_set_teams_resolves_both_slots(fresh_db: Session) -> None:
    game = set_game_teams(
        fresh_db,
        game_id=GAME_R32_FIRST_ID,
        team_home_id="mex",
        team_away_id="can",
    )
    assert game.team_home_id == "mex"
    assert game.team_away_id == "can"
    # Placeholders stay on the row so we know "this was a 2A v 2B slot
    # before the bracket settled" - useful for audit/QA.
    assert game.placeholder_home == "2A"
    assert game.placeholder_away == "2B"


def test_set_teams_resolves_only_one_slot(fresh_db: Session) -> None:
    """Half-resolved is fine - admins may enter the home side as soon as
    group A finishes, before group B does."""
    game = set_game_teams(
        fresh_db,
        game_id=GAME_R32_FIRST_ID,
        team_home_id="mex",
        team_away_id=None,
    )
    assert game.team_home_id == "mex"
    assert game.team_away_id is None


def test_set_teams_clears_back_to_null(fresh_db: Session) -> None:
    set_game_teams(
        fresh_db,
        game_id=GAME_R32_FIRST_ID,
        team_home_id="mex",
        team_away_id="can",
    )
    game = set_game_teams(
        fresh_db,
        game_id=GAME_R32_FIRST_ID,
        team_home_id=None,
        team_away_id=None,
    )
    assert game.team_home_id is None
    assert game.team_away_id is None


def test_set_teams_normalises_case_and_whitespace(fresh_db: Session) -> None:
    game = set_game_teams(
        fresh_db,
        game_id=GAME_R32_FIRST_ID,
        team_home_id="  MEX  ",
        team_away_id="CAN",
    )
    assert (game.team_home_id, game.team_away_id) == ("mex", "can")


def test_set_teams_treats_blank_as_clear(fresh_db: Session) -> None:
    game = set_game_teams(
        fresh_db,
        game_id=GAME_R32_FIRST_ID,
        team_home_id="   ",
        team_away_id="",
    )
    assert game.team_home_id is None
    assert game.team_away_id is None


def test_set_teams_rejects_unknown_team(fresh_db: Session) -> None:
    with pytest.raises(InvalidTeamAssignment) as info:
        set_game_teams(
            fresh_db,
            game_id=GAME_R32_FIRST_ID,
            team_home_id="zzz",
            team_away_id="can",
        )
    assert info.value.kind == "unknown_team"


def test_set_teams_rejects_same_team(fresh_db: Session) -> None:
    with pytest.raises(InvalidTeamAssignment) as info:
        set_game_teams(
            fresh_db,
            game_id=GAME_R32_FIRST_ID,
            team_home_id="mex",
            team_away_id="mex",
        )
    assert info.value.kind == "same_team"


def test_set_teams_rejects_group_stage_game(fresh_db: Session) -> None:
    """Group-stage teams come straight from the seed - admins can't edit them."""
    with pytest.raises(InvalidTeamAssignment) as info:
        set_game_teams(
            fresh_db,
            game_id=GAME_OPENER_ID,
            team_home_id="cze",
            team_away_id="rsa",
        )
    assert info.value.kind == "not_knockout"


def test_set_teams_unknown_game(fresh_db: Session) -> None:
    with pytest.raises(GameNotFound):
        set_game_teams(
            fresh_db,
            game_id=99999,
            team_home_id="mex",
            team_away_id="can",
        )


def test_set_teams_preserves_existing_bets(
    fresh_db: Session,
    user: User,
) -> None:
    """A bet placed on a knockout slot survives a placeholder resolution.

    Users bet on the *game*, not on a particular team pair; re-shuffling
    the bracket shouldn't wipe everyone's predictions.
    """
    # Place a bet on the R32 fixture before any team is set.
    upsert_bet(
        fresh_db,
        user,
        game_id=GAME_R32_FIRST_ID,
        score_home=2,
        score_away=1,
        now=GAME_OPENER_KICKOFF - timedelta(days=1),
    )
    set_game_teams(
        fresh_db,
        game_id=GAME_R32_FIRST_ID,
        team_home_id="mex",
        team_away_id="can",
    )
    bet_count = fresh_db.query(Game).filter(Game.id == GAME_R32_FIRST_ID).one().bets
    assert len(bet_count) == 1
    assert (bet_count[0].score_home, bet_count[0].score_away) == (2, 1)


# ---------------------------------------------------------------------------
# list_teams_grouped
# ---------------------------------------------------------------------------


def test_list_teams_grouped_returns_all_12_groups(fresh_db: Session) -> None:
    groups = list_teams_grouped(fresh_db)
    assert len(groups) == 12
    assert [g[0] for g in groups] == list("abcdefghijkl")


def test_list_teams_grouped_each_group_has_four_teams(
    fresh_db: Session,
) -> None:
    for _, teams in list_teams_grouped(fresh_db):
        assert len(teams) == 4


def test_list_teams_grouped_omits_knockout_pseudo_groups(
    fresh_db: Session,
) -> None:
    group_ids = [g[0] for g in list_teams_grouped(fresh_db)]
    for pseudo in ("r32", "r16", "qf", "sf", "3rd", "fin"):
        assert pseudo not in group_ids
