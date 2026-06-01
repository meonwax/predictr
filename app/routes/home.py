"""Public ``/`` home dashboard.

Replaces the placeholder redirect to ``/games`` with a real landing page:

* Anonymous visitors see a welcome hero plus sign-in / register CTAs and
  a link to the rules. Currently-live matches (if any) are still shown -
  the live strip is universally interesting and ``/games`` already
  surfaces this data to anonymous visitors anyway.
* Authenticated users get the full dashboard: a personalised greeting,
  the optional admin "important message" banner, live matches, the next
  upcoming matches, their open special questions, and the most recent
  shouts. Each panel renders an empty state when its dataset is empty so
  the layout stays predictable.

The route stays read-only and never raises on a sparse database (no
games seeded, no questions, no shouts): every section degrades to its
empty state.
"""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.dependencies import CurrentUser, DbSession
from app.services.home import (
    DEFAULT_OPEN_QUESTIONS_LIMIT,
    DEFAULT_UPCOMING_LIMIT,
    has_unanswered_open_questions,
    has_unbet_imminent_games,
    live_games,
    open_questions_for_user,
    upcoming_games,
)
from app.services.shouts import list_shouts
from app.services.site_info import get_site_info
from app.templating import templates

router = APIRouter(tags=["home"])

#: Cap for the recent-shouts strip on the home dashboard. Matches the
#: density of the other home panels - a "see full shoutbox" link below
#: handles the long tail.
RECENT_SHOUTS_LIMIT: int = 5


@router.get("/", response_class=HTMLResponse, name="home:index")
def home_index(
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
) -> HTMLResponse:
    site_info = get_site_info(db, current_user)
    live = live_games(db)
    upcoming = upcoming_games(db, limit=DEFAULT_UPCOMING_LIMIT)

    if current_user is not None:
        questions = open_questions_for_user(
            db,
            current_user,
            limit=DEFAULT_OPEN_QUESTIONS_LIMIT,
        )
        shouts = list_shouts(db, limit=RECENT_SHOUTS_LIMIT)
        unanswered = has_unanswered_open_questions(questions)
        unbet_imminent = has_unbet_imminent_games(db, current_user)
    else:
        questions = []
        shouts = []
        unanswered = False
        unbet_imminent = False

    return templates.TemplateResponse(
        request,
        "home.html",
        {
            "current_user": current_user,
            "site_info": site_info,
            "live": live,
            "upcoming": upcoming,
            "open_questions": questions,
            "shouts": shouts,
            "has_unanswered_questions": unanswered,
            "has_unbet_imminent_games": unbet_imminent,
            "active_nav": "home",
        },
    )
