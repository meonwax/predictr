"""``/admin/games`` handlers.

A single endpoint per row:

* ``POST /admin/games/{id}`` accepts every editable field on the row
  (score, notes, and -- for knockout fixtures -- the resolved team
  selections) and persists them in one transaction.

The previous split into ``POST /admin/games/{id}`` and
``POST /admin/games/{id}/teams`` made the row layout look cluttered
(two save buttons on knockout rows) without any real win, so they were
folded together. The HTMX swap shape mirrors the user-facing ``/bets``
page: HTMX clients get the freshly-rendered row fragment back, vanilla
browser POSTs get a 303 to ``/admin/games``.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from app.dependencies import DbSession, RequiredAdmin
from app.models import Game
from app.routes._helpers import is_htmx, map_invalid_score, parse_score
from app.services.admin import (
    MAX_NOTES_LEN,
    InvalidTeamAssignment,
    NotesTooLong,
    list_games_for_admin,
    list_teams_grouped,
    save_admin_game,
)
from app.services.games import MAX_SCORE, MIN_SCORE, GameNotFound, InvalidScore
from app.team_data import KNOCKOUT_GROUP_IDS
from app.templating import templates

router = APIRouter()


_TEAM_ERROR_KEYS: dict[str, str] = {
    "unknown_team": "error.team.unknown",
    "same_team": "error.team.same",
    "not_knockout": "error.team.not_knockout",
}


def _map_invalid_team(exc: InvalidTeamAssignment) -> tuple[str, dict[str, object]]:
    return _TEAM_ERROR_KEYS.get(exc.kind, "error.team.unknown"), {}


# ---------------------------------------------------------------------------
# GET /admin/games - editable games table
# ---------------------------------------------------------------------------


@router.get("/games", response_class=HTMLResponse, name="admin:games")
def admin_games(
    request: Request,
    db: DbSession,
    user: RequiredAdmin,
) -> Response:
    games = list_games_for_admin(db)
    teams_by_group = list_teams_grouped(db)
    return templates.TemplateResponse(
        request,
        "admin/games.html",
        {
            "current_user": user,
            "games": games,
            "teams_by_group": teams_by_group,
            "knockout_group_ids": KNOCKOUT_GROUP_IDS,
            "min_score": MIN_SCORE,
            "max_score": MAX_SCORE,
            "max_notes_len": MAX_NOTES_LEN,
            "active_nav": "admin",
        },
    )


# ---------------------------------------------------------------------------
# POST /admin/games/{id} - persist score + notes + (optional) teams
# ---------------------------------------------------------------------------


@router.post("/games/{game_id}", include_in_schema=False)
def save_game(
    request: Request,
    game_id: int,
    db: DbSession,
    user: RequiredAdmin,
    score_home: Annotated[str, Form()] = "",
    score_away: Annotated[str, Form()] = "",
    notes: Annotated[str, Form()] = "",
    team_home_id: Annotated[str, Form()] = "",
    team_away_id: Annotated[str, Form()] = "",
) -> Response:
    """Persist the editable fields for *game_id*.

    Score fields:

    * Both blank -> clear the recorded result.
    * Both set   -> store the result. Out-of-range / non-numeric values
      surface as inline errors via the row fragment.
    * Mixed (one blank / one set) -> validation error.

    Team fields are honoured only on knockout fixtures (decided here from
    the game's ``group_id``, not from the form payload shape, because
    FastAPI cannot reliably tell "field absent" from "field empty"). The
    legitimate UI never sends team selects on group-stage rows, and any
    out-of-band POST that does include them is silently ignored. Empty
    strings on knockout rows clear the slot back to the bracket placeholder.
    """
    error: str | None = None
    error_args: dict[str, object] = {}

    home: int | None = None
    away: int | None = None
    try:
        home = parse_score(score_home)
        away = parse_score(score_away)
    except ValueError:
        error = "error.score.invalid"

    if error is None and ((home is None) ^ (away is None)):
        error = "error.score.partial"

    # Pre-load the game so we can decide whether the team fields apply
    # before delegating. Group-stage rows ignore them; knockout rows pass
    # them through to the service for validation + persistence.
    game = db.get(Game, game_id)
    if game is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown game.")
    apply_teams = game.group_id in KNOCKOUT_GROUP_IDS

    if error is None:
        try:
            save_admin_game(
                db,
                game_id=game_id,
                score_home=home,
                score_away=away,
                notes=notes,
                team_home_id=team_home_id,
                team_away_id=team_away_id,
                apply_teams=apply_teams,
            )
        except GameNotFound:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown game.") from None
        except InvalidScore as exc:
            error, error_args = map_invalid_score(exc)
        except NotesTooLong:
            error = "error.admin.notes_too_long"
            error_args = {"max": MAX_NOTES_LEN}
        except InvalidTeamAssignment as exc:
            error, error_args = _map_invalid_team(exc)

    if is_htmx(request):
        # ``game`` was loaded above; ``save_admin_game`` either mutated +
        # committed it via the same identity map, or raised before
        # mutating (so the row reflects the persisted state either way).
        return templates.TemplateResponse(
            request,
            "admin/_game_result_row.html",
            {
                "game": game,
                "teams_by_group": list_teams_grouped(db),
                "knockout_group_ids": KNOCKOUT_GROUP_IDS,
                "min_score": MIN_SCORE,
                "max_score": MAX_SCORE,
                "max_notes_len": MAX_NOTES_LEN,
                "just_saved": error is None,
                "error": error,
                "error_args": error_args,
                "current_user": user,
            },
        )

    return RedirectResponse(url="/admin/games", status_code=status.HTTP_303_SEE_OTHER)


__all__ = ["router"]
