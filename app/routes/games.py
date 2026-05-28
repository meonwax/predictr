"""Read-only ``/games`` route: the full tournament schedule."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.dependencies import CurrentUser, DbSession
from app.models import Game, Group
from app.templating import templates

router = APIRouter(tags=["games"])


@router.get("/games", response_class=HTMLResponse, name="games:index")
def games_index(
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
) -> HTMLResponse:
    """List every group and its games in tournament order."""
    sections = db.scalars(
        select(Group)
        .options(selectinload(Group.games).joinedload(Game.venue))
        .order_by(Group.priority)
    ).all()
    return templates.TemplateResponse(
        request,
        "games.html",
        {"sections": sections, "current_user": current_user},
    )
