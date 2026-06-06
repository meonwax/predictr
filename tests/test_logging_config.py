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
from app.main import (
    HEALTHZ_PATH,
    _configure_logging,
    _HealthCheckAccessLogFilter,
)


def _access_record(path: str, status_code: int = 200) -> logging.LogRecord:
    """Build a record shaped like a ``uvicorn.access`` log line.

    Mirrors uvicorn's call: ``'%s - "%s %s HTTP/%s" %d'`` with args of
    ``(client_addr, method, path, http_version, status_code)``.
    """
    return logging.LogRecord(
        name="uvicorn.access",
        level=logging.INFO,
        pathname=__file__,
        lineno=0,
        msg='%s - "%s %s HTTP/%s" %d',
        args=("127.0.0.1:1234", "GET", path, "1.1", status_code),
        exc_info=None,
    )


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


def test_healthcheck_filter_suppresses_probe_when_debug_off() -> None:
    """With DEBUG off, the probe record is relabelled DEBUG and dropped."""
    log_filter = _HealthCheckAccessLogFilter(debug_enabled=False)
    record = _access_record(HEALTHZ_PATH)

    assert log_filter.filter(record) is False
    assert record.levelname == "DEBUG"
    assert record.levelno == logging.DEBUG


def test_healthcheck_filter_keeps_probe_when_debug_on() -> None:
    """With DEBUG on, the probe record survives but is still labelled DEBUG."""
    log_filter = _HealthCheckAccessLogFilter(debug_enabled=True)
    record = _access_record(HEALTHZ_PATH + "?ignored=1")

    assert log_filter.filter(record) is True
    assert record.levelname == "DEBUG"


def test_healthcheck_filter_passes_other_requests_untouched() -> None:
    """Regular access lines are never demoted, regardless of DEBUG state."""
    log_filter = _HealthCheckAccessLogFilter(debug_enabled=False)
    record = _access_record("/login")

    assert log_filter.filter(record) is True
    assert record.levelname == "INFO"


def test_configure_logging_installs_single_access_filter() -> None:
    """``_configure_logging`` wires exactly one health-check filter, idempotently."""
    access_logger = logging.getLogger("uvicorn.access")
    original_filters = list(access_logger.filters)
    try:
        _configure_logging(Settings(_env_file=None, log_level="INFO"))  # type: ignore[arg-type]
        _configure_logging(Settings(_env_file=None, log_level="INFO"))  # type: ignore[arg-type]

        installed = [f for f in access_logger.filters if isinstance(f, _HealthCheckAccessLogFilter)]
        assert len(installed) == 1

        probe = _access_record(HEALTHZ_PATH)
        assert access_logger.filter(probe) is False
    finally:
        access_logger.filters = original_filters
