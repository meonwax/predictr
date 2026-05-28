"""Tests for the team lookup tables and the language-aware ``team_name``.

Two layers are exercised:

* The pure :func:`app.team_data.team_name` function with explicit
  ``language`` arguments (returns English or German names, falls back to
  English for unknown languages, and yields the uppercase FIFA code for
  unknown teams).
* The Jinja ``team_name`` global registered in
  :mod:`app.templating`, which picks the language from the rendering
  context. We drive this through the real ``/games`` page using the
  language cookie so the middleware -> templating handshake is covered
  end to end.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.middleware import LANGUAGE_COOKIE_NAME
from app.team_data import (
    GROUP_NAMES,
    KNOCKOUT_GROUP_IDS,
    TEAM_INFO,
    GroupInfo,
    TeamInfo,
    group_label,
    team_name,
)

# ---------------------------------------------------------------------------
# Lookup table integrity
# ---------------------------------------------------------------------------


def test_team_info_has_all_48_teams() -> None:
    """The seed file ships exactly 48 group-stage teams."""
    assert len(TEAM_INFO) == 48


def test_every_team_has_iso_and_both_names() -> None:
    """Every row is a complete :class:`TeamInfo` triple."""
    for code, info in TEAM_INFO.items():
        assert isinstance(info, TeamInfo)
        assert info.iso, f"{code}: missing ISO sub-tag"
        assert info.name_en, f"{code}: missing English name"
        assert info.name_de, f"{code}: missing German name"


def test_english_and_german_names_are_distinct_where_expected() -> None:
    """A few well-known countries must differ between EN and DE.

    Sanity check that German names actually got translated rather than
    copy-pasted from English. Some teams (Japan, Iran, Ghana, Panama,
    ...) legitimately share spellings; this asserts the *non*-identical
    ones are spelled correctly in the German column.
    """
    expected_differences = {
        "ger": ("Germany", "Deutschland"),
        "bra": ("Brazil", "Brasilien"),
        "esp": ("Spain", "Spanien"),
        "fra": ("France", "Frankreich"),
        "ita": None,  # not a participant - ignore if absent
        "aut": ("Austria", "Österreich"),
        "tur": ("Türkiye", "Türkei"),
        "civ": ("Côte d'Ivoire", "Elfenbeinküste"),
    }
    for code, expected in expected_differences.items():
        info = TEAM_INFO.get(code)
        if expected is None:
            continue
        assert info is not None, f"missing seed team {code!r}"
        en, de = expected
        assert info.name_en == en
        assert info.name_de == de


# ---------------------------------------------------------------------------
# Pure function: team_name(code, language)
# ---------------------------------------------------------------------------


def test_team_name_defaults_to_english() -> None:
    assert team_name("ger") == "Germany"
    assert team_name("bra") == "Brazil"


def test_team_name_returns_german_when_requested() -> None:
    assert team_name("ger", language="de") == "Deutschland"
    assert team_name("bra", language="de") == "Brasilien"
    assert team_name("esp", language="de") == "Spanien"


def test_team_name_unknown_language_falls_back_to_english() -> None:
    assert team_name("ger", language="fr") == "Germany"
    assert team_name("ger", language="") == "Germany"


def test_team_name_unknown_code_returns_uppercase_fallback() -> None:
    assert team_name("zzz") == "ZZZ"
    assert team_name("zzz", language="de") == "ZZZ"


def test_team_name_none_returns_empty_string() -> None:
    assert team_name(None) == ""
    assert team_name(None, language="de") == ""


# ---------------------------------------------------------------------------
# Jinja global: language picked from request context
# ---------------------------------------------------------------------------


def test_games_page_renders_english_team_names_for_en_visitors(
    auth_client: TestClient,
) -> None:
    """The default in the test environment is English (see conftest)."""
    page = auth_client.get("/games").text
    # Pick names that do NOT collide with English venue strings in the
    # seed (which intentionally stay English-only). "Czechia" is a
    # country-only label, so its presence/absence is a clean signal.
    assert "Czechia" in page
    assert "Tschechien" not in page


def test_games_page_renders_german_team_names_when_cookie_set(
    auth_client: TestClient,
) -> None:
    """Setting the language cookie to ``de`` flips team labels to German."""
    auth_client.cookies.set(LANGUAGE_COOKIE_NAME, "de")
    page = auth_client.get("/games").text
    assert "Tschechien" in page
    # The English form must be gone (Czechia doesn't appear as a venue).
    assert "Czechia" not in page


# ---------------------------------------------------------------------------
# Group / knockout-stage labels
# ---------------------------------------------------------------------------


def test_group_names_has_12_groups_plus_all_knockout_stages() -> None:
    """12 group-stage rows (a..l) plus one row per KNOCKOUT_GROUP_IDS entry."""
    assert len(GROUP_NAMES) == 12 + len(KNOCKOUT_GROUP_IDS)
    for letter in "abcdefghijkl":
        assert letter in GROUP_NAMES
    for ko in KNOCKOUT_GROUP_IDS:
        assert ko in GROUP_NAMES


def test_every_group_has_both_language_labels() -> None:
    for gid, info in GROUP_NAMES.items():
        assert isinstance(info, GroupInfo)
        assert info.name_en, f"{gid}: missing English label"
        assert info.name_de, f"{gid}: missing German label"


def test_german_knockout_labels_use_canonical_football_vocabulary() -> None:
    """The DE labels follow the standard German football naming, not a
    literal translation of the English label (where they differ).
    """
    assert group_label("r32", language="de") == "Sechzehntelfinale"
    assert group_label("r16", language="de") == "Achtelfinale"
    assert group_label("qf", language="de") == "Viertelfinale"
    assert group_label("sf", language="de") == "Halbfinale"
    assert group_label("3rd", language="de") == "Spiel um Platz 3"
    assert group_label("fin", language="de") == "Finale"


def test_group_label_returns_english_by_default() -> None:
    assert group_label("a") == "Group A"
    assert group_label("r32") == "Round of 32"


def test_group_label_returns_german_when_requested() -> None:
    assert group_label("a", language="de") == "Gruppe A"
    assert group_label("l", language="de") == "Gruppe L"


def test_group_label_unknown_language_falls_back_to_english() -> None:
    assert group_label("a", language="fr") == "Group A"
    assert group_label("a", language="") == "Group A"


def test_group_label_unknown_id_returns_uppercase_fallback() -> None:
    assert group_label("zz") == "ZZ"
    assert group_label("zz", language="de") == "ZZ"


def test_group_label_none_returns_empty_string() -> None:
    assert group_label(None) == ""
    assert group_label(None, language="de") == ""


def test_games_page_renders_english_group_labels_for_en_visitors(
    auth_client: TestClient,
) -> None:
    page = auth_client.get("/games").text
    assert "Group A" in page
    assert "Round of 32" in page
    assert "Gruppe A" not in page
    assert "Sechzehntelfinale" not in page


def test_games_page_renders_german_group_labels_when_cookie_set(
    auth_client: TestClient,
) -> None:
    auth_client.cookies.set(LANGUAGE_COOKIE_NAME, "de")
    page = auth_client.get("/games").text
    assert "Gruppe A" in page
    assert "Sechzehntelfinale" in page
    assert "Achtelfinale" in page
    assert "Group A" not in page
    assert "Round of 32" not in page
