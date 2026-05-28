"""Public ``/info`` route - rules and tournament intro.

Anyone (logged in or not) can read this page. It renders the Markdown
stored on the singleton ``config`` row, with placeholders like
``{{ points_result }}`` interpolated against the currently-configured
scoring values so the rules text never drifts away from what the
scoring code actually does.

If the ``config`` table is empty we still serve a sensible default -
see :data:`app.services.site_info.DEFAULT_RULES_MARKDOWN`.
"""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.dependencies import CurrentUser, DbSession
from app.services.site_info import get_site_info
from app.templating import templates

router = APIRouter(tags=["info"])


@router.get("/info", response_class=HTMLResponse, name="info:index")
def info_index(
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
) -> HTMLResponse:
    site_info = get_site_info(db, current_user)
    return templates.TemplateResponse(
        request,
        "info.html",
        {
            "site_info": site_info,
            "current_user": current_user,
            "active_nav": "info",
        },
    )
