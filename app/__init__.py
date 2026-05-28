"""Predictr - football prediction game.

Single source of truth for the version is :file:`pyproject.toml`. We
re-export it as ``app.__version__`` (via ``importlib.metadata``) so
non-packaging callers - :func:`app.main.create_app`, log lines, the
``/healthz`` payload, etc. - can read it without parsing the TOML file.
A ``PackageNotFoundError`` fallback to a literal keeps in-tree imports
working when the project hasn't been installed into the active env
(e.g. when running ``python -m`` straight from a checkout).
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version

try:
    __version__: str = _pkg_version("predictr")
except PackageNotFoundError:  # pragma: no cover - only hit in raw checkouts
    __version__ = "0.0.0+unknown"
