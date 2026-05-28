"""End-to-end test: fresh Postgres -> Alembic upgrade -> load seeds/wc2026.sql -> verify.

The Postgres testcontainer and the ``seeded_engine`` fixture live in
``tests/conftest.py`` so they're shared across every test module. SQLite-in-
tests has been removed because it silently disables FK enforcement, stores
naive datetimes for ``TIMESTAMPTZ`` columns, and diverges from Postgres on
several other behaviours we rely on.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy import Engine, func, select
from sqlalchemy.orm import Session

from app.models import Game, Group, Team, Venue
from app.seed import (
    _split_statements,
    _strip_line_comments,
    is_target_seeded,
    load_seed_file,
)
from tests.conftest import SEED_FILE

# --- Row-count assertions ----------------------------------------------------


def test_group_count_is_18(seeded_engine: Engine) -> None:
    """12 group-stage groups (A..L) + 6 knockout pseudo-groups."""
    with Session(seeded_engine) as s:
        assert s.scalar(select(func.count()).select_from(Group)) == 18


def test_team_count_is_48(seeded_engine: Engine) -> None:
    with Session(seeded_engine) as s:
        assert s.scalar(select(func.count()).select_from(Team)) == 48


def test_venue_count_is_16(seeded_engine: Engine) -> None:
    with Session(seeded_engine) as s:
        assert s.scalar(select(func.count()).select_from(Venue)) == 16


def test_game_count_is_104(seeded_engine: Engine) -> None:
    with Session(seeded_engine) as s:
        assert s.scalar(select(func.count()).select_from(Game)) == 104


def test_each_group_stage_group_has_exactly_four_teams(seeded_engine: Engine) -> None:
    with Session(seeded_engine) as s:
        rows = s.execute(
            select(Team.group_id, func.count(Team.id))
            .group_by(Team.group_id)
            .order_by(Team.group_id)
        ).all()
    by_group = dict(rows)
    for letter in "abcdefghijkl":
        assert by_group[letter] == 4, f"group {letter!r} should have 4 teams"
    # Knockout pseudo-groups have no teams attached.
    for pseudo in ("r32", "r16", "qf", "sf", "3rd", "fin"):
        assert pseudo not in by_group


# --- Specific row assertions -------------------------------------------------


def test_opening_match_is_mexico_vs_south_africa(seeded_engine: Engine) -> None:
    """Match 1: MEX v RSA, Estadio Azteca (venue 8), 11 June 2026 19:00 UTC."""
    with Session(seeded_engine) as s:
        game = s.get(Game, 1)
    assert game is not None
    assert game.team_home_id == "mex"
    assert game.team_away_id == "rsa"
    assert game.group_id == "a"
    assert game.venue_id == 8
    expected = datetime(2026, 6, 11, 19, 0, 0, tzinfo=UTC)
    assert game.kickoff_time == expected
    assert game.kickoff_time.tzinfo is not None, "expected a tz-aware datetime"


def test_estadio_azteca_is_venue_8(seeded_engine: Engine) -> None:
    with Session(seeded_engine) as s:
        venue = s.get(Venue, 8)
    assert venue is not None
    assert venue.stadium == "Estadio Azteca, Mexico City, MEX"
    assert venue.city == "mex"


def test_levis_stadium_apostrophe_escaped_correctly(seeded_engine: Engine) -> None:
    """The seed escapes 'Levi''s' as a SQL apostrophe; verify the loader handled it."""
    with Session(seeded_engine) as s:
        venue = s.get(Venue, 13)
    assert venue is not None
    assert venue.stadium == "Levi's Stadium, Santa Clara, USA"


def test_final_is_match_104_at_metlife_with_null_teams(seeded_engine: Engine) -> None:
    with Session(seeded_engine) as s:
        game = s.get(Game, 104)
    assert game is not None
    assert game.group_id == "fin"
    assert game.venue_id == 11
    assert game.team_home_id is None
    assert game.team_away_id is None


def test_knockout_games_have_null_teams(seeded_engine: Engine) -> None:
    """All 32 knockout matches (R32 through Final) are unresolved at seed time."""
    with Session(seeded_engine) as s:
        count = s.scalar(
            select(func.count())
            .select_from(Game)
            .where(Game.group_id.in_(["r32", "r16", "qf", "sf", "3rd", "fin"]))
        )
        nulls = s.scalar(
            select(func.count())
            .select_from(Game)
            .where(
                Game.team_home_id.is_(None),
                Game.team_away_id.is_(None),
            )
        )
    # 16 R32 + 8 R16 + 4 QF + 2 SF + 1 3rd + 1 Final == 32
    assert count == 32
    assert nulls == 32


def test_group_stage_games_all_have_both_teams(seeded_engine: Engine) -> None:
    """The 72 group-stage matches must have both home and away teams set."""
    with Session(seeded_engine) as s:
        unresolved = s.scalar(
            select(func.count())
            .select_from(Game)
            .where(
                Game.group_id.in_(list("abcdefghijkl")),
                (Game.team_home_id.is_(None) | Game.team_away_id.is_(None)),
            )
        )
        total = s.scalar(
            select(func.count()).select_from(Game).where(Game.group_id.in_(list("abcdefghijkl")))
        )
    assert unresolved == 0
    assert total == 72


def test_usa_first_match_is_against_paraguay(seeded_engine: Engine) -> None:
    """Sanity-check the host nation's opener (match 4): USA v PAR at SoFi Stadium."""
    with Session(seeded_engine) as s:
        game = s.get(Game, 4)
    assert game is not None
    assert game.team_home_id == "usa"
    assert game.team_away_id == "par"
    assert game.group_id == "d"


def test_group_priority_is_zero_to_seventeen(seeded_engine: Engine) -> None:
    with Session(seeded_engine) as s:
        priorities = sorted(row[0] for row in s.execute(select(Group.priority)).all())
    assert priorities == list(range(18))


def test_foreign_keys_are_enforced(seeded_engine: Engine) -> None:
    """Insert a row pointing at a non-existent FK target; Postgres must reject it."""
    from sqlalchemy import text
    from sqlalchemy.exc import IntegrityError

    with seeded_engine.connect() as conn:
        trans = conn.begin()
        try:
            with pytest.raises(IntegrityError):
                conn.execute(
                    text(
                        "INSERT INTO game "
                        "(id, kickoff_time, group_id, venue_id) "
                        "VALUES (9999, '2026-07-20 00:00:00', 'a', 999)"
                    )
                )
        finally:
            trans.rollback()


def test_orm_relationship_resolves_team_to_group(seeded_engine: Engine) -> None:
    """ORM smoke-test: load a team and follow its FK relationship."""
    with Session(seeded_engine) as s:
        mex = s.get(Team, "mex")
        assert mex is not None
        assert mex.group_id == "a"
        assert mex.group.priority == 0
        assert {t.id for t in mex.group.teams} == {"mex", "rsa", "kor", "cze"}


# --- Loader unit tests -------------------------------------------------------


def test_strip_line_comments_removes_dash_dash_comments_only_outside_strings() -> None:
    sql = "-- header comment\nINSERT INTO foo VALUES ('a -- not a comment', 1); -- trailing\n"
    out = _strip_line_comments(sql)
    assert "-- header" not in out
    assert "-- trailing" not in out
    assert "'a -- not a comment'" in out


def test_strip_line_comments_handles_escaped_apostrophes() -> None:
    sql = "INSERT INTO v VALUES ('Levi''s Stadium'); -- ok\n"
    out = _strip_line_comments(sql)
    assert "'Levi''s Stadium'" in out
    assert "-- ok" not in out


def test_split_statements_splits_on_top_level_semicolons() -> None:
    sql = "INSERT INTO a VALUES (1); INSERT INTO b VALUES ('x;y');"
    stmts = _split_statements(sql)
    assert len(stmts) == 2
    assert stmts[1].endswith("('x;y')")


# --- Re-seed / idempotency assertions ---------------------------------------


def test_is_target_seeded_reports_true_after_seeding(seeded_engine: Engine) -> None:
    assert is_target_seeded(seeded_engine) is True


def test_reload_without_if_empty_raises_and_leaves_data_untouched(
    seeded_engine: Engine,
) -> None:
    """Re-running the seed on a populated DB must error AND change nothing.

    This is the "operator accidentally re-seeded prod" safety property: the
    whole load runs in a single transaction, so the first PK collision rolls
    back the entire attempt.
    """
    from sqlalchemy.exc import IntegrityError

    with Session(seeded_engine) as s:
        before_groups = s.scalar(select(func.count()).select_from(Group))
        before_teams = s.scalar(select(func.count()).select_from(Team))
        before_venues = s.scalar(select(func.count()).select_from(Venue))
        before_games = s.scalar(select(func.count()).select_from(Game))

    with pytest.raises(IntegrityError):
        load_seed_file(SEED_FILE, engine=seeded_engine)

    with Session(seeded_engine) as s:
        assert s.scalar(select(func.count()).select_from(Group)) == before_groups
        assert s.scalar(select(func.count()).select_from(Team)) == before_teams
        assert s.scalar(select(func.count()).select_from(Venue)) == before_venues
        assert s.scalar(select(func.count()).select_from(Game)) == before_games


def test_reload_with_if_empty_is_a_safe_noop(seeded_engine: Engine) -> None:
    """Re-running with ``if_empty=True`` must return 0 and touch nothing."""
    with Session(seeded_engine) as s:
        before = s.scalar(select(func.count()).select_from(Group))

    statements_run = load_seed_file(SEED_FILE, engine=seeded_engine, if_empty=True)
    assert statements_run == 0

    with Session(seeded_engine) as s:
        assert s.scalar(select(func.count()).select_from(Group)) == before
