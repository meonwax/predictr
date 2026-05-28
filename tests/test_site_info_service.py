"""Unit tests for :mod:`app.services.site_info`."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from app.models import Config, User
from app.services.site_info import (
    DEFAULT_ADMIN_EMAIL,
    DEFAULT_POINTS_RESULT,
    DEFAULT_POINTS_TENDENCY,
    DEFAULT_POINTS_TENDENCY_SPREAD,
    DEFAULT_RULES_MARKDOWN,
    DEFAULT_RULES_MARKDOWN_DE,
    DEFAULT_TITLE,
    get_site_info,
    render_rules_markdown,
)
from app.services.users import RegistrationData, register_user


@pytest.fixture()
def db(seeded_engine) -> Iterator[Session]:
    Session_ = sessionmaker(bind=seeded_engine, expire_on_commit=False, future=True)
    with Session_() as session:
        yield session


@pytest.fixture()
def empty_config(seeded_engine) -> Iterator[None]:
    """Run the test against an empty ``config`` table, then restore the row.

    The session-scoped seed inserts one config singleton; this fixture
    snapshots all current rows, deletes them, runs the test, and restores
    them so other tests still see the seeded state.
    """
    Session_ = sessionmaker(bind=seeded_engine, expire_on_commit=False, future=True)
    with Session_() as s:
        rows = s.query(Config).all()
        snapshot = [
            {
                "id": r.id,
                "title": r.title,
                "owner": r.owner,
                "admin_email": r.admin_email,
                "show_important_message": r.show_important_message,
                "points_result": r.points_result,
                "points_tendency": r.points_tendency,
                "points_tendency_spread": r.points_tendency_spread,
                "rules_en": r.rules_en,
                "rules_de": r.rules_de,
            }
            for r in rows
        ]
    with seeded_engine.begin() as conn:
        conn.execute(text("DELETE FROM config"))
    try:
        yield
    finally:
        with seeded_engine.begin() as conn:
            conn.execute(text("DELETE FROM config"))
            for row in snapshot:
                conn.execute(
                    text(
                        "INSERT INTO config (id, title, owner, admin_email, "
                        "show_important_message, points_result, points_tendency, "
                        "points_tendency_spread, rules_en, rules_de) VALUES "
                        "(:id, :title, :owner, :admin_email, "
                        ":show_important_message, :points_result, :points_tendency, "
                        ":points_tendency_spread, :rules_en, :rules_de)"
                    ),
                    row,
                )


# ---------------------------------------------------------------------------
# render_rules_markdown
# ---------------------------------------------------------------------------


def test_renders_markdown_to_html() -> None:
    html = render_rules_markdown(
        "## Hello\n\nA paragraph.",
        title="x",
        owner="x",
        admin_email="x@x",
        points_result=5,
        points_tendency_spread=3,
        points_tendency=2,
    )
    assert "<h2>Hello</h2>" in html
    assert "<p>A paragraph.</p>" in html


def test_interpolates_point_values() -> None:
    """``{{ points_result }}`` etc. are substituted before markdown runs."""
    html = render_rules_markdown(
        "Exact: {{ points_result }}"
        " / spread: {{ points_tendency_spread }}"
        " / win: {{ points_tendency }}",
        title="x",
        owner="x",
        admin_email="x@x",
        points_result=7,
        points_tendency_spread=4,
        points_tendency=3,
    )
    assert "Exact: 7" in html
    assert "spread: 4" in html
    assert "win: 3" in html


def test_interpolates_admin_email() -> None:
    html = render_rules_markdown(
        "Mail us at {{ admin_email }}.",
        title="x",
        owner="x",
        admin_email="rules@example.com",
        points_result=5,
        points_tendency_spread=3,
        points_tendency=2,
    )
    assert "rules@example.com" in html


def test_renders_pipe_tables() -> None:
    """The ``tables`` extension must be enabled for the scoring table."""
    md_text = "| Outcome | Points |\n| ------- | ------ |\n| Exact   | 5      |\n"
    html = render_rules_markdown(
        md_text,
        title="x",
        owner="x",
        admin_email="x@x",
        points_result=5,
        points_tendency_spread=3,
        points_tendency=2,
    )
    assert "<table>" in html
    assert "<th>Outcome</th>" in html
    assert "<td>Exact</td>" in html


def test_broken_template_falls_back_to_raw() -> None:
    """A syntax error in {{ ... }} doesn't crash the request."""
    html = render_rules_markdown(
        "## Bad {{ unterminated\n\nbody",
        title="x",
        owner="x",
        admin_email="x@x",
        points_result=5,
        points_tendency_spread=3,
        points_tendency=2,
    )
    # The fallback should still produce a heading and a paragraph.
    assert "<h2>" in html
    assert "<p>body</p>" in html


def test_html_is_passed_through() -> None:
    """Markdown allows inline HTML, used by the default ``mailto:`` link."""
    html = render_rules_markdown(
        'Reach us at <a href="mailto:x@x">us</a>.',
        title="x",
        owner="x",
        admin_email="x@x",
        points_result=5,
        points_tendency_spread=3,
        points_tendency=2,
    )
    assert '<a href="mailto:x@x">us</a>' in html


def test_default_rules_render_cleanly() -> None:
    """The shipped default Markdown converts without errors."""
    html = render_rules_markdown(
        DEFAULT_RULES_MARKDOWN,
        title="Predictr",
        owner="Predictr",
        admin_email="admin@example.com",
        points_result=5,
        points_tendency_spread=3,
        points_tendency=2,
    )
    assert "<h2>" in html
    # Point interpolation worked.
    assert "<strong>5</strong>" in html
    assert ">3<" in html
    assert ">2<" in html
    assert "mailto:admin@example.com" in html


# ---------------------------------------------------------------------------
# get_site_info - backed by the seed
# ---------------------------------------------------------------------------


def test_returns_seeded_row(db: Session) -> None:
    """The session-scoped seed should populate the singleton config row."""
    info = get_site_info(db)
    assert info.title == "Predictr"
    assert info.admin_email == "admin@example.com"
    assert info.points_result == 5
    assert info.points_tendency_spread == 3
    assert info.points_tendency == 2
    assert "<h2>" in info.rules_html
    # Point values surface in the rendered HTML.
    assert "<strong>5</strong>" in info.rules_html


def test_falls_back_to_defaults_when_table_empty(
    empty_config: None,
    db: Session,
) -> None:
    db.expire_all()
    info = get_site_info(db)
    assert info.title == DEFAULT_TITLE
    assert info.admin_email == DEFAULT_ADMIN_EMAIL
    assert info.points_result == DEFAULT_POINTS_RESULT
    assert info.points_tendency_spread == DEFAULT_POINTS_TENDENCY_SPREAD
    assert info.points_tendency == DEFAULT_POINTS_TENDENCY
    assert "<h2>" in info.rules_html


def test_uses_default_rules_when_rules_en_blank(
    empty_config: None,
    db: Session,
    seeded_engine,
) -> None:
    """A config row with empty/whitespace rules still gets the default text."""
    with seeded_engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO config (title, owner, admin_email, "
                "show_important_message, points_result, points_tendency, "
                "points_tendency_spread, rules_en, rules_de) VALUES "
                "('site', 'owner', 'admin@a.b', false, 4, 2, 1, '   ', NULL)"
            )
        )
    db.expire_all()
    info = get_site_info(db)
    assert info.title == "site"
    # Defaults shine through even though point values come from the row.
    assert "<strong>4</strong>" in info.rules_html
    assert "Welcome to" in info.rules_html  # default rules headline


# ---------------------------------------------------------------------------
# Language selection
# ---------------------------------------------------------------------------


@pytest.fixture()
def fresh_user_db(clean_user_tables: None, seeded_engine) -> Iterator[Session]:
    Session_ = sessionmaker(bind=seeded_engine, expire_on_commit=False, future=True)
    with Session_() as s:
        yield s


def _make_user(db: Session, *, lang: str, email: str = "u@example.com") -> User:
    return register_user(
        db,
        RegistrationData(name="U", email=email, password="hunter222", preferred_language=lang),
    )


def test_anonymous_visitor_gets_english(db: Session) -> None:
    info = get_site_info(db, user=None)
    assert "Welcome to" in info.rules_html
    assert "Willkommen" not in info.rules_html


def test_english_user_gets_english(fresh_user_db: Session) -> None:
    u = _make_user(fresh_user_db, lang="en")
    info = get_site_info(fresh_user_db, u)
    assert "Welcome to" in info.rules_html
    assert "Willkommen" not in info.rules_html


def test_german_user_gets_german(fresh_user_db: Session) -> None:
    u = _make_user(fresh_user_db, lang="de")
    info = get_site_info(fresh_user_db, u)
    assert "Willkommen" in info.rules_html
    assert "Welcome to" not in info.rules_html
    # German still gets the point values interpolated.
    assert "<strong>5</strong>" in info.rules_html


def test_unknown_language_falls_back_to_english(fresh_user_db: Session) -> None:
    u = _make_user(fresh_user_db, lang="en")
    # Force an unsupported code on the model bypassing service validation.
    u.preferred_language = "fr"
    fresh_user_db.commit()
    info = get_site_info(fresh_user_db, u)
    assert "Welcome to" in info.rules_html


def test_blank_rules_de_falls_back_to_english_column(
    empty_config: None,
    fresh_user_db: Session,
    seeded_engine,
) -> None:
    """A German user on a config row with no rules_de still sees content."""
    with seeded_engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO config (title, owner, admin_email, "
                "show_important_message, points_result, points_tendency, "
                "points_tendency_spread, rules_en, rules_de) VALUES "
                "('site', 'owner', 'admin@a.b', false, 5, 2, 3, "
                "'## English only\n\nHi.', '')"
            )
        )
    fresh_user_db.expire_all()
    u = _make_user(fresh_user_db, lang="de")
    info = get_site_info(fresh_user_db, u)
    assert "English only" in info.rules_html


def test_blank_both_columns_uses_packaged_default_for_language(
    empty_config: None,
    fresh_user_db: Session,
    seeded_engine,
) -> None:
    with seeded_engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO config (title, owner, admin_email, "
                "show_important_message, points_result, points_tendency, "
                "points_tendency_spread, rules_en, rules_de) VALUES "
                "('site', 'owner', 'admin@a.b', false, 5, 2, 3, '', '')"
            )
        )
    fresh_user_db.expire_all()
    u = _make_user(fresh_user_db, lang="de")
    info = get_site_info(fresh_user_db, u)
    # The packaged German default kicks in.
    assert "Willkommen" in info.rules_html


def test_default_german_rules_render_cleanly() -> None:
    html = render_rules_markdown(
        DEFAULT_RULES_MARKDOWN_DE,
        title="Predictr",
        owner="Predictr",
        admin_email="admin@example.com",
        points_result=5,
        points_tendency_spread=3,
        points_tendency=2,
    )
    assert "<h2>" in html
    assert "<strong>5</strong>" in html
    assert ">3<" in html
    assert ">2<" in html
    assert "mailto:admin@example.com" in html
