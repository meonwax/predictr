"""FastAPI application entry point.

Builds the ASGI app, mounts the ``/static`` directory and the routers
defined under :mod:`app.routes`. Templates and Jinja2 globals live in
:mod:`app.templating`.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import __version__
from app.config import Settings, get_settings
from app.dependencies import provide_site_title
from app.middleware import LanguageMiddleware
from app.routes import admin as admin_routes
from app.routes import auth as auth_routes
from app.routes import bets as bets_routes
from app.routes import games as games_routes
from app.routes import home as home_routes
from app.routes import info as info_routes
from app.routes import ladder as ladder_routes
from app.routes import language as language_routes
from app.routes import questions as questions_routes
from app.routes import settings as settings_routes
from app.routes import shouts as shouts_routes
from app.templating import templates

LOGGER = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).resolve().parent / "static"

#: Path of the liveness probe. The container healthcheck (and Caddy, and any
#: external monitor) polls it every few seconds, forever, so its access-log
#: line is pure noise on the INFO log. See :class:`_HealthCheckAccessLogFilter`.
HEALTHZ_PATH = "/healthz"


class _HealthCheckAccessLogFilter(logging.Filter):
    """Demote ``uvicorn.access`` lines for the health probe to DEBUG.

    uvicorn logs every request through the ``uvicorn.access`` logger as
    ``'%s - "%s %s HTTP/%s" %d'`` with ``record.args`` of
    ``(client_addr, method, path, http_version, status_code)``. The probe
    fires several times a minute, drowning the INFO log in identical
    ``GET /healthz 200`` lines.

    Rather than dropping those records outright we relabel them DEBUG, so
    they stay reachable when an operator turns ``LOG_LEVEL=DEBUG`` to chase
    a problem, and suppress them whenever DEBUG output is off (the default).
    """

    def __init__(self, *, debug_enabled: bool) -> None:
        super().__init__()
        self._debug_enabled = debug_enabled

    def filter(self, record: logging.LogRecord) -> bool:
        args = record.args
        if not (isinstance(args, tuple) and len(args) >= 3):
            return True
        path = args[2]
        if not (isinstance(path, str) and path.split("?", 1)[0] == HEALTHZ_PATH):
            return True
        record.levelno = logging.DEBUG
        record.levelname = "DEBUG"
        return self._debug_enabled


def _install_access_log_filter(settings: Settings) -> None:
    """Attach (idempotently) the health-check filter to ``uvicorn.access``.

    Called from :func:`_configure_logging`. We strip any filter we added on
    a previous call first so repeated ``create_app()`` invocations (notably
    in the test suite) don't stack duplicates.
    """
    access_logger = logging.getLogger("uvicorn.access")
    access_logger.filters = [
        f for f in access_logger.filters if not isinstance(f, _HealthCheckAccessLogFilter)
    ]
    debug_enabled = getattr(logging, settings.log_level) <= logging.DEBUG
    access_logger.addFilter(_HealthCheckAccessLogFilter(debug_enabled=debug_enabled))


def _configure_logging(settings: Settings) -> None:
    """Configure the root logger from ``settings.log_level``.

    Uvicorn's default ``LOGGING_CONFIG`` only attaches handlers to its own
    loggers (``uvicorn``, ``uvicorn.error``, ``uvicorn.access``) and leaves
    the root logger at the Python default (``WARNING``, no handler). That
    means any ``LOGGER.info(...)`` call in the ``app.*`` hierarchy would
    be silently dropped in production. Calling :func:`logging.basicConfig`
    here adds a single ``StreamHandler`` to root with our format and the
    configured level, so app-level INFO / DEBUG lines reach stdout and
    show up in ``docker compose logs``.

    Forcing :class:`logging.Formatter` onto ``time.gmtime`` makes the
    timestamp prefix UTC, matching the backup-sidecar log format and
    keeping every container's logs on the same clock regardless of host
    timezone.
    """
    logging.Formatter.converter = time.gmtime
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)sZ %(levelname)-8s %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    _install_access_log_filter(settings)


#: Status codes that get a dedicated branded error page when the client
#: accepts HTML. Anything else (400, 422, 502, ...) keeps the default JSON
#: detail response so APIs and form validation feedback are not affected.
_HTML_ERROR_STATUS_CODES: frozenset[int] = frozenset({401, 403, 404})


def _wants_html(request: Request) -> bool:
    """Whether to render an HTML error page for *request*.

    We render HTML when the ``Accept`` header asks for ``text/html`` or
    when it is missing entirely (the conservative default for browsers).
    Callers that explicitly opt into JSON only - i.e. ``Accept`` mentions
    ``application/json`` but not ``text/html`` - keep getting the plain
    FastAPI-style JSON ``{"detail": ...}`` response, which preserves the
    contract for any future API client.
    """
    accept = request.headers.get("accept", "")
    if not accept:
        return True
    if "text/html" in accept:
        return True
    return "application/json" not in accept


def _render_error_page(
    request: Request,
    status_code: int,
    template_name: str,
) -> Response:
    """Render *template_name* with the given status code.

    Wrapped in a defensive ``try`` because template rendering during
    error handling must never raise a second exception (which would
    shadow the original error and break the response cycle).
    """
    try:
        return templates.TemplateResponse(
            request,
            template_name,
            {"current_user": getattr(request.state, "user", None)},
            status_code=status_code,
        )
    except Exception:
        LOGGER.exception("Failed to render error template %s", template_name)
        return Response(
            content=f"<h1>{status_code}</h1>",
            status_code=status_code,
            media_type="text/html",
        )


def create_app() -> FastAPI:
    settings = get_settings()
    _configure_logging(settings)
    app = FastAPI(
        title="Predictr",
        version=__version__,
        description="A football prediction game (FIFA World Cup 2026).",
        debug=settings.debug,
    )

    app.add_middleware(LanguageMiddleware)

    app.mount(
        "/static",
        StaticFiles(directory=str(STATIC_DIR)),
        name="static",
    )

    @app.get("/healthz", tags=["health"])
    def healthz() -> dict[str, str]:
        """Liveness probe used by Docker Compose, Caddy, and monitoring."""
        return {"status": "ok"}

    # Page-rendering routers resolve the database-configured site title into
    # ``request.state`` so the shared chrome (``<title>``, navbar, footer) can
    # show it. Non-page routers (language redirects, avatar bytes, health) are
    # excluded to avoid a needless query on those hot paths.
    page_chrome = [Depends(provide_site_title)]
    app.include_router(home_routes.router, dependencies=page_chrome)
    app.include_router(auth_routes.router, dependencies=page_chrome)
    app.include_router(games_routes.router, dependencies=page_chrome)
    app.include_router(info_routes.router, dependencies=page_chrome)
    app.include_router(bets_routes.router, dependencies=page_chrome)
    app.include_router(ladder_routes.router, dependencies=page_chrome)
    app.include_router(language_routes.router)
    app.include_router(questions_routes.router, dependencies=page_chrome)
    app.include_router(shouts_routes.router, dependencies=page_chrome)
    app.include_router(settings_routes.router, dependencies=page_chrome)
    app.include_router(settings_routes.avatars_router)
    app.include_router(admin_routes.router, dependencies=page_chrome)

    @app.exception_handler(StarletteHTTPException)
    async def _http_exception_handler(
        request: Request,
        exc: StarletteHTTPException,
    ) -> Response:
        """Render a branded HTML page for 401/403/404 when the client wants HTML.

        FastAPI's own ``HTTPException`` is a subclass of
        :class:`starlette.exceptions.HTTPException`, so registering against
        the Starlette type catches both. Status codes outside the
        :data:`_HTML_ERROR_STATUS_CODES` set (e.g. 400, 422, 502) fall
        back to FastAPI's default JSON detail body to keep the contract
        intact for API-shaped consumers.
        """
        if exc.status_code in _HTML_ERROR_STATUS_CODES and _wants_html(request):
            return _render_error_page(
                request,
                exc.status_code,
                f"errors/{exc.status_code}.html",
            )
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)

    if not settings.debug:

        @app.exception_handler(Exception)
        async def _unhandled_exception_handler(
            request: Request,
            exc: Exception,
        ) -> Response:
            """Catch-all 500 handler - rendered only outside debug mode.

            When ``settings.debug`` is ``True`` we deliberately leave this
            handler unregistered so Starlette's :class:`ServerErrorMiddleware`
            still emits its full traceback HTML for developers. In
            production (``debug=False``) we log the exception and render
            the branded 500 page instead of the default plain-text
            ``Internal Server Error`` response.
            """
            LOGGER.exception("Unhandled exception while serving %s", request.url.path)
            if _wants_html(request):
                return _render_error_page(request, 500, "errors/500.html")
            return JSONResponse(
                {"detail": "Internal Server Error"},
                status_code=500,
            )

    return app


app = create_app()
