"""Unit tests for :mod:`app.timezones`.

Verifies the curated list is well-formed (every entry loads), the
resolver handles unknown / blank / tampered inputs gracefully, and the
``is_supported`` allow-list is consistent with the list constant.
"""

from __future__ import annotations

from zoneinfo import ZoneInfo

import pytest

from app.timezones import (
    DEFAULT_TIMEZONE,
    SUPPORTED_TIMEZONES,
    get_zone,
    is_supported,
    resolve_timezone,
)


def test_default_timezone_is_in_supported_list() -> None:
    assert DEFAULT_TIMEZONE in SUPPORTED_TIMEZONES


def test_every_supported_timezone_loads() -> None:
    """Catch a typo in the curated list before it hits production."""
    for name in SUPPORTED_TIMEZONES:
        ZoneInfo(name)


def test_utc_is_first_for_easy_dropdown_access() -> None:
    """Anonymous-but-curious users picking UTC shouldn't have to scroll."""
    assert SUPPORTED_TIMEZONES[0] == "UTC"


def test_is_supported_recognises_curated_entries() -> None:
    for name in SUPPORTED_TIMEZONES:
        assert is_supported(name)


def test_is_supported_rejects_unknown_inputs() -> None:
    assert not is_supported("Mars/Olympus_Mons")
    assert not is_supported("")
    assert not is_supported(None)
    # Even valid IANA zones not in our allow-list should be rejected by
    # the form-validation helper (they can still be saved by hand for
    # power users, but not via the settings dropdown).
    assert not is_supported("Africa/Abidjan")


def test_get_zone_returns_named_zone_when_supported() -> None:
    zone = get_zone("Europe/Berlin")
    assert isinstance(zone, ZoneInfo)
    assert str(zone) == "Europe/Berlin"


def test_get_zone_falls_back_to_default_for_unknown() -> None:
    zone = get_zone("Mars/Olympus_Mons", default="Europe/Berlin")
    assert str(zone) == "Europe/Berlin"


def test_get_zone_falls_back_to_utc_when_default_also_invalid() -> None:
    zone = get_zone("Mars/Olympus_Mons", default="Pluto/Charon")
    assert str(zone) == "UTC"


def test_get_zone_handles_none_and_blank() -> None:
    zone = get_zone(None, default="Europe/Berlin")
    assert str(zone) == "Europe/Berlin"
    zone = get_zone("", default="Europe/Berlin")
    assert str(zone) == "Europe/Berlin"


@pytest.mark.parametrize(
    ("user_tz", "expected"),
    [
        ("Europe/Berlin", "Europe/Berlin"),
        ("America/New_York", "America/New_York"),
        ("  Europe/Berlin  ", "Europe/Berlin"),  # whitespace stripped
        (None, "Europe/Berlin"),  # null -> default
        ("", "Europe/Berlin"),  # blank -> default
        ("Mars/Olympus_Mons", "Europe/Berlin"),  # unknown -> default
    ],
)
def test_resolve_timezone(user_tz: str | None, expected: str) -> None:
    assert resolve_timezone(user_tz, default="Europe/Berlin") == expected
