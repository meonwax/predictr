"""Admin-only HTTP routes.

The admin surface is large enough to split by concern:

* The dashboard (``GET /admin``) and the parent router live here.
* :mod:`app.routes.admin.games` owns the games/teams handlers.
* :mod:`app.routes.admin.questions` owns the special-questions CRUD.

The two sub-routers are included into this package's parent router so
``main.py`` can keep wiring a single ``admin`` router, and the
``/admin`` prefix lives in exactly one place.

Every handler in this package is protected by :data:`RequiredAdmin` so
an anonymous request 401s and a non-admin 403s. (See
:func:`app.dependencies.require_admin`.)
"""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, Response

from app.dependencies import DbSession, RequiredAdmin
from app.routes.admin import games, questions
from app.services.admin import get_dashboard_stats
from app.templating import templates

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("", response_class=HTMLResponse, name="admin:index")
def admin_index(
    request: Request,
    db: DbSession,
    user: RequiredAdmin,
) -> Response:
    stats = get_dashboard_stats(db)
    return templates.TemplateResponse(
        request,
        "admin/index.html",
        {"current_user": user, "stats": stats, "active_nav": "admin"},
    )


router.include_router(games.router)
router.include_router(questions.router)

__all__ = ["router"]
