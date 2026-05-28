"""Static lookup tables for the 48 teams in the WC 2026 seed.

The DB stores each team only by its FIFA 3-letter code (``team.id``). For
display we need three more things:

* an **ISO 3166-1 alpha-2** code (with the four GB sub-tags ``gb-eng``,
  ``gb-sct``, ``gb-wls``, ``gb-nir``) - used to pick a flag image from
  ``app/static/img/flags/``;
* an **English name** - used in EN UI surfaces;
* a **German name** - used in DE UI surfaces.

Team names are kept in code (rather than the i18n message catalogue)
because they are *data* tied to the seeded ``team.id`` set, not free-form
UI copy: every code in this dict must have a row in ``seeds/wc2026.sql``
and vice versa, and that coupling is much easier to audit when the names
sit next to their FIFA codes than when they are spread across two
language dicts in ``app/i18n.py``. Adding a third language is a single
field on :class:`TeamInfo`.
"""

from __future__ import annotations

from typing import NamedTuple


class TeamInfo(NamedTuple):
    iso: str
    name_en: str
    name_de: str


class GroupInfo(NamedTuple):
    name_en: str
    name_de: str


# Source of truth: the 48 ``team.id`` values seeded by ``seeds/wc2026.sql``.
TEAM_INFO: dict[str, TeamInfo] = {
    # Group A
    "mex": TeamInfo("mx", "Mexico", "Mexiko"),
    "rsa": TeamInfo("za", "South Africa", "Südafrika"),
    "kor": TeamInfo("kr", "Korea Republic", "Südkorea"),
    "cze": TeamInfo("cz", "Czechia", "Tschechien"),
    # Group B
    "can": TeamInfo("ca", "Canada", "Kanada"),
    "bih": TeamInfo("ba", "Bosnia and Herzegovina", "Bosnien und Herzegowina"),
    "qat": TeamInfo("qa", "Qatar", "Katar"),
    "sui": TeamInfo("ch", "Switzerland", "Schweiz"),
    # Group C
    "bra": TeamInfo("br", "Brazil", "Brasilien"),
    "mar": TeamInfo("ma", "Morocco", "Marokko"),
    "hai": TeamInfo("ht", "Haiti", "Haiti"),
    "sco": TeamInfo("gb-sct", "Scotland", "Schottland"),
    # Group D
    "usa": TeamInfo("us", "United States", "USA"),
    "par": TeamInfo("py", "Paraguay", "Paraguay"),
    "aus": TeamInfo("au", "Australia", "Australien"),
    "tur": TeamInfo("tr", "Türkiye", "Türkei"),
    # Group E
    "ger": TeamInfo("de", "Germany", "Deutschland"),
    "cuw": TeamInfo("cw", "Curaçao", "Curaçao"),
    "civ": TeamInfo("ci", "Côte d'Ivoire", "Elfenbeinküste"),
    "ecu": TeamInfo("ec", "Ecuador", "Ecuador"),
    # Group F
    "ned": TeamInfo("nl", "Netherlands", "Niederlande"),
    "jpn": TeamInfo("jp", "Japan", "Japan"),
    "swe": TeamInfo("se", "Sweden", "Schweden"),
    "tun": TeamInfo("tn", "Tunisia", "Tunesien"),
    # Group G
    "bel": TeamInfo("be", "Belgium", "Belgien"),
    "egy": TeamInfo("eg", "Egypt", "Ägypten"),
    "irn": TeamInfo("ir", "Iran", "Iran"),
    "nzl": TeamInfo("nz", "New Zealand", "Neuseeland"),
    # Group H
    "esp": TeamInfo("es", "Spain", "Spanien"),
    "cpv": TeamInfo("cv", "Cape Verde", "Kap Verde"),
    "ksa": TeamInfo("sa", "Saudi Arabia", "Saudi-Arabien"),
    "uru": TeamInfo("uy", "Uruguay", "Uruguay"),
    # Group I
    "fra": TeamInfo("fr", "France", "Frankreich"),
    "sen": TeamInfo("sn", "Senegal", "Senegal"),
    "irq": TeamInfo("iq", "Iraq", "Irak"),
    "nor": TeamInfo("no", "Norway", "Norwegen"),
    # Group J
    "arg": TeamInfo("ar", "Argentina", "Argentinien"),
    "alg": TeamInfo("dz", "Algeria", "Algerien"),
    "aut": TeamInfo("at", "Austria", "Österreich"),
    "jor": TeamInfo("jo", "Jordan", "Jordanien"),
    # Group K
    "por": TeamInfo("pt", "Portugal", "Portugal"),
    "cod": TeamInfo("cd", "DR Congo", "DR Kongo"),
    "uzb": TeamInfo("uz", "Uzbekistan", "Usbekistan"),
    "col": TeamInfo("co", "Colombia", "Kolumbien"),
    # Group L
    "eng": TeamInfo("gb-eng", "England", "England"),
    "cro": TeamInfo("hr", "Croatia", "Kroatien"),
    "gha": TeamInfo("gh", "Ghana", "Ghana"),
    "pan": TeamInfo("pa", "Panama", "Panama"),
}


GROUP_NAMES: dict[str, GroupInfo] = {
    # Group stage - alphabetical labels share their letter across languages,
    # only the noun changes.
    "a": GroupInfo("Group A", "Gruppe A"),
    "b": GroupInfo("Group B", "Gruppe B"),
    "c": GroupInfo("Group C", "Gruppe C"),
    "d": GroupInfo("Group D", "Gruppe D"),
    "e": GroupInfo("Group E", "Gruppe E"),
    "f": GroupInfo("Group F", "Gruppe F"),
    "g": GroupInfo("Group G", "Gruppe G"),
    "h": GroupInfo("Group H", "Gruppe H"),
    "i": GroupInfo("Group I", "Gruppe I"),
    "j": GroupInfo("Group J", "Gruppe J"),
    "k": GroupInfo("Group K", "Gruppe K"),
    "l": GroupInfo("Group L", "Gruppe L"),
    # Knockout rounds - the German football vocabulary uses an internal
    # numbering where the Round of 32 is the "Sechzehntelfinale" (16th
    # finals, because each tie ends in 16 winners) and the Round of 16
    # is the "Achtelfinale" (8th finals). This is the canonical match-
    # day naming used by DFB and ARD/ZDF broadcasts, not a literal
    # translation of the English label.
    "r32": GroupInfo("Round of 32", "Sechzehntelfinale"),
    "r16": GroupInfo("Round of 16", "Achtelfinale"),
    "qf": GroupInfo("Quarter-finals", "Viertelfinale"),
    "sf": GroupInfo("Semi-finals", "Halbfinale"),
    "3rd": GroupInfo("Third-place play-off", "Spiel um Platz 3"),
    "fin": GroupInfo("Final", "Finale"),
}


GROUP_STAGE_IDS: frozenset[str] = frozenset("abcdefghijkl")
KNOCKOUT_GROUP_IDS: tuple[str, ...] = ("r32", "r16", "qf", "sf", "3rd", "fin")


def team_iso(fifa_code: str | None) -> str | None:
    """Return the ISO/sub-tag for a FIFA 3-letter code, or None for an unknown one."""
    if fifa_code is None:
        return None
    info = TEAM_INFO.get(fifa_code)
    return info.iso if info else None


def team_name(fifa_code: str | None, language: str = "en") -> str:
    """Return the localised name for a FIFA 3-letter code.

    *language* must be ``"en"`` or ``"de"``; unknown codes fall back to
    English. Unknown FIFA codes return the uppercase code so the UI still
    shows *something* rather than an empty cell (mirrors how knockout
    placeholders are rendered elsewhere).
    """
    if fifa_code is None:
        return ""
    info = TEAM_INFO.get(fifa_code)
    if info is None:
        return fifa_code.upper()
    if language == "de":
        return info.name_de
    return info.name_en


def group_label(group_id: str | None, language: str = "en") -> str:
    """Return the localised label for a group / knockout stage id.

    Mirrors :func:`team_name`: ``"de"`` returns the German label,
    anything else (or ``"en"``) returns the English label. Unknown ids
    fall back to their uppercase id so misconfigured DB rows still
    render as *something* rather than a blank cell.
    """
    if group_id is None:
        return ""
    info = GROUP_NAMES.get(group_id)
    if info is None:
        return group_id.upper()
    if language == "de":
        return info.name_de
    return info.name_en
