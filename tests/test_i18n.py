"""Unit tests for the ``app.i18n`` catalogue and lookup helpers.

These tests touch the catalogue itself (no DB, no HTTP) and pin the
properties the rest of the suite - and the route layer - relies on:

* every key exists in both the EN and DE catalogues, so falling back
  between languages never returns a different key shape;
* placeholders match across languages, so ``_('foo', x=1)`` works
  regardless of the user's preference;
* :func:`gettext` and :func:`resolve_language` handle the obvious
  edge cases (missing key, unknown language, blank inputs).
"""

from __future__ import annotations

import re

import pytest

from app.i18n import (
    DE,
    DEFAULT_LANGUAGE,
    EN,
    SUPPORTED_LANGUAGES,
    gettext,
    parse_accept_language,
    resolve_language,
)

_PLACEHOLDER_RE = re.compile(r"\{(\w+)\}")


def _placeholders(template: str) -> frozenset[str]:
    return frozenset(_PLACEHOLDER_RE.findall(template))


def test_default_language_is_supported() -> None:
    assert DEFAULT_LANGUAGE in SUPPORTED_LANGUAGES


def test_german_catalog_covers_every_english_key() -> None:
    """Translators may not skip strings - that would surface English text
    inside an otherwise German UI, which looks broken."""
    missing = sorted(set(EN) - set(DE))
    assert missing == [], f"Missing German translations: {missing}"


def test_english_catalog_covers_every_german_key() -> None:
    """Stale German entries (key removed in EN) flag drift in the other
    direction. The English catalogue is the canonical key listing."""
    extra = sorted(set(DE) - set(EN))
    assert extra == [], f"German keys not in English catalogue: {extra}"


@pytest.mark.parametrize("key", sorted(EN))
def test_placeholders_match_across_languages(key: str) -> None:
    """``str.format`` will raise if a key is missing from the template -
    keep the set identical so route-layer kwargs work in both languages."""
    en = _placeholders(EN[key])
    de = _placeholders(DE[key])
    assert en == de, f"Placeholder mismatch for {key!r}: en={en} de={de}"


def test_gettext_returns_requested_language() -> None:
    assert gettext("nav.games", "en") == "Games"
    assert gettext("nav.games", "de") == "Spiele"


def test_gettext_falls_back_to_english_for_unknown_language() -> None:
    assert gettext("nav.games", "xx") == "Games"


def test_gettext_returns_key_for_unknown_key() -> None:
    # The key itself is the safe fallback so the missing translation
    # shows up loudly rather than as an empty span.
    assert gettext("does.not.exist", "en") == "does.not.exist"


def test_gettext_formats_kwargs() -> None:
    msg = gettext("admin.dash.matches_upcoming", "en", count=7)
    assert msg == "7 still upcoming"
    msg = gettext("admin.dash.matches_upcoming", "de", count=7)
    assert msg == "7 noch ausstehend"


def test_gettext_swallows_bad_format_args() -> None:
    """A missing placeholder should log + return the raw template rather
    than crash the page render."""
    out = gettext("admin.dash.matches_upcoming", "en")  # no `count`
    assert "{count}" in out


@pytest.mark.parametrize(
    ("input_lang", "default", "expected"),
    [
        (None, "de", "de"),
        ("", "de", "de"),
        ("  ", "de", "de"),
        ("EN", "de", "en"),
        ("De", "en", "de"),
        ("fr", "en", "en"),  # unsupported -> default
        ("en", "de", "en"),
    ],
)
def test_resolve_language(input_lang: str | None, default: str, expected: str) -> None:
    assert resolve_language(input_lang, default=default) == expected


def test_brand_name_is_identical_in_both_languages() -> None:
    """Brand names don't get translated."""
    assert EN["brand.name"] == DE["brand.name"] == "Predictr"


# ---------------------------------------------------------------------------
# parse_accept_language
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("header", [None, "", "   "])
def test_parse_accept_language_empty_returns_empty(header: str | None) -> None:
    assert parse_accept_language(header) == []


def test_parse_accept_language_single_supported() -> None:
    assert parse_accept_language("de") == ["de"]
    assert parse_accept_language("en") == ["en"]


def test_parse_accept_language_strips_region_subtags() -> None:
    """Browsers usually send country sub-tags (de-DE, en-US). We collapse
    them to the primary tag so the catalogue lookup works."""
    assert parse_accept_language("de-DE") == ["de"]
    assert parse_accept_language("en-US") == ["en"]


def test_parse_accept_language_drops_unsupported_languages() -> None:
    """Only languages we actually translate to make it into the result."""
    assert parse_accept_language("fr,it,es") == []


def test_parse_accept_language_orders_by_quality_descending() -> None:
    # German preferred (q=0.9) over English (q=0.7).
    assert parse_accept_language("en;q=0.7,de;q=0.9") == ["de", "en"]
    # And the reverse.
    assert parse_accept_language("en;q=0.9,de;q=0.7") == ["en", "de"]


def test_parse_accept_language_preserves_order_for_equal_quality() -> None:
    """Two items at q=1.0 should appear in their original header order."""
    assert parse_accept_language("en,de") == ["en", "de"]
    assert parse_accept_language("de,en") == ["de", "en"]


def test_parse_accept_language_skips_q0_items() -> None:
    """q=0 means 'do not serve me this language' per RFC 9110."""
    assert parse_accept_language("en;q=0,de") == ["de"]


def test_parse_accept_language_ignores_wildcard() -> None:
    """``*`` is a fallback marker, not a real language code."""
    assert parse_accept_language("*") == []


def test_parse_accept_language_mixed_realistic_header() -> None:
    """A header Firefox might actually send."""
    header = "de-DE,de;q=0.9,en-US;q=0.7,en;q=0.5,fr;q=0.3"
    assert parse_accept_language(header) == ["de", "en"]


def test_parse_accept_language_deduplicates_primary_codes() -> None:
    """``de-DE,de`` should produce a single ``de`` entry, not two."""
    assert parse_accept_language("de-DE,de;q=0.9") == ["de"]


def test_parse_accept_language_handles_bogus_q_value() -> None:
    """Garbage ``q=`` values default to 0 (i.e. drop the item) instead of crashing."""
    assert parse_accept_language("de;q=abc,en") == ["en"]
