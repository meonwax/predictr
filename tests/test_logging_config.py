"""Tests for the ``LOG_LEVEL`` setting and ``app.main._configure_logging``.

These tests deliberately do **not** depend on the seeded-database fixtures
in ``conftest.py``; they only exercise the settings object and the logging
configuration helper.
"""

from __future__ import annotations

import logging

import pytest
from pydantic import ValidationError

from app.config import Settings
from app.main import _configure_logging


def test_log_level_default_is_info(monkeypatch: pytest.MonkeyPatch) -> None:
    """If no env var is set, the setting defaults to ``INFO``.

    Drops ``LOG_LEVEL`` from the environment first because
    ``tests/conftest.py`` pins it to ``WARNING`` for the rest of the suite.
    """
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    settings = Settings(_env_file=None)
    assert settings.log_level == "INFO"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("debug", "DEBUG"),
        ("DEBUG", "DEBUG"),
        ("Info", "INFO"),
        ("warning", "WARNING"),
        ("ERROR", "ERROR"),
        ("critical", "CRITICAL"),
    ],
)
def test_log_level_accepts_case_insensitive_input(raw: str, expected: str) -> None:
    """The validator uppercases the value before Literal matching."""
    settings = Settings(_env_file=None, log_level=raw)  # type: ignore[arg-type]
    assert settings.log_level == expected


def test_log_level_rejects_garbage() -> None:
    """An unknown level raises a Pydantic validation error at startup."""
    with pytest.raises(ValidationError):
        Settings(_env_file=None, log_level="LOUD")  # type: ignore[arg-type]


def test_configure_logging_sets_root_level(monkeypatch: pytest.MonkeyPatch) -> None:
    """``_configure_logging`` applies the configured level to the root logger."""
    root = logging.getLogger()
    original_level = root.level
    original_handlers = list(root.handlers)
    try:
        # Drop any existing handlers so ``basicConfig`` actually adds ours
        # instead of silently no-op'ing (basicConfig is a no-op when root
        # already has handlers).
        for handler in original_handlers:
            root.removeHandler(handler)

        _configure_logging(Settings(_env_file=None, log_level="DEBUG"))  # type: ignore[arg-type]
        assert root.level == logging.DEBUG

        # The handler we installed should be a StreamHandler emitting to
        # stderr; we don't pin the exact stream because pytest's capture
        # plugin may swap it, but the formatter pattern should be ours.
        assert root.handlers, "basicConfig did not attach a handler to root"
        formatter = root.handlers[0].formatter
        assert formatter is not None
        assert "%(name)s" in formatter._fmt  # type: ignore[attr-defined]
    finally:
        # Restore the original root logger state so we don't bleed
        # configuration into other tests.
        for handler in list(root.handlers):
            root.removeHandler(handler)
        for handler in original_handlers:
            root.addHandler(handler)
        root.setLevel(original_level)
