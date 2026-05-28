"""The ``/ladder`` (leaderboard) route.

Read-only. Login-required, matching ``/bets`` - the ladder lists every
registered user by name, which is information the rest of the app
already exposes only to logged-in users.
"""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.dependencies import DbSession, RequiredUser
from app.services.ladder import compute_ladder
from app.services.scoring import DEFAULT_CONFIG
from app.templating import templates

router = APIRouter(tags=["ladder"])


@router.get("/ladder", response_class=HTMLResponse, name="ladder:index")
def ladder_index(
    request: Request,
    db: DbSession,
    user: RequiredUser,
) -> HTMLResponse:
    entries = compute_ladder(db)
    return templates.TemplateResponse(
        request,
        "ladder.html",
        {
            "current_user": user,
            "entries": entries,
            "scoring": DEFAULT_CONFIG,
            "active_nav": "ladder",
        },
    )
