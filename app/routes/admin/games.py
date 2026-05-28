"""``/admin/games`` handlers.

Two interactive flows on the same row:

* Setting / clearing the official result (``POST /admin/games/{id}``).
* Resolving knockout placeholders into concrete teams
  (``POST /admin/games/{id}/teams``).

Both follow the same HTMX swap shape as the user-facing ``/bets`` page:
the response body is the freshly-rendered row fragment for HTMX clients,
and a 303 back to ``/admin/games`` for vanilla browser POSTs.
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
    clear_game_result,
    list_games_for_admin,
    list_teams_grouped,
    set_game_result,
    set_game_teams,
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
# POST /admin/games/{game_id} - set / clear the result
# ---------------------------------------------------------------------------


@router.post("/games/{game_id}", include_in_schema=False)
def save_game_result(
    request: Request,
    game_id: int,
    db: DbSession,
    user: RequiredAdmin,
    score_home: Annotated[str, Form()] = "",
    score_away: Annotated[str, Form()] = "",
    notes: Annotated[str, Form()] = "",
) -> Response:
    """Upsert (or clear) the official result for *game_id*.

    Both score fields blank -> clear the result. Both set -> store. Mixed
    (one blank, one set) -> validation error.
    """
    error: str | None = None
    error_args: dict[str, object] = {}
    try:
        home = parse_score(score_home)
        away = parse_score(score_away)
    except ValueError:
        error = "error.score.invalid"
        home = away = None

    if error is None:
        if home is None and away is None:
            try:
                clear_game_result(db, game_id=game_id)
            except GameNotFound:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown game.") from None
        elif home is None or away is None:
            error = "error.score.partial"
        else:
            try:
                set_game_result(
                    db,
                    game_id=game_id,
                    score_home=home,
                    score_away=away,
                    notes=notes,
                )
            except GameNotFound:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown game.") from None
            except InvalidScore as exc:
                error, error_args = map_invalid_score(exc)
            except NotesTooLong:
                error = "error.admin.notes_too_long"
                error_args = {"max": MAX_NOTES_LEN}

    if is_htmx(request):
        # Reload the row so the swap reflects the persisted state.
        game = db.get(Game, game_id)
        if game is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown game.")
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


# ---------------------------------------------------------------------------
# POST /admin/games/{game_id}/teams - resolve knockout placeholders
# ---------------------------------------------------------------------------


@router.post("/games/{game_id}/teams", include_in_schema=False)
def save_game_teams(
    request: Request,
    game_id: int,
    db: DbSession,
    user: RequiredAdmin,
    team_home_id: Annotated[str, Form()] = "",
    team_away_id: Annotated[str, Form()] = "",
) -> Response:
    """Resolve a knockout placeholder by setting one or both team slots.

    Empty form values clear that side back to the placeholder. Used by
    the ``/admin/games`` row picker once group standings settle. Bets on
    the fixture are preserved (see :func:`app.services.admin.set_game_teams`).
    """
    error: str | None = None
    error_args: dict[str, object] = {}
    home = team_home_id.strip() or None
    away = team_away_id.strip() or None
    try:
        set_game_teams(
            db,
            game_id=game_id,
            team_home_id=home,
            team_away_id=away,
        )
    except GameNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown game.") from None
    except InvalidTeamAssignment as exc:
        error, error_args = _map_invalid_team(exc)

    if is_htmx(request):
        game = db.get(Game, game_id)
        if game is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown game.")
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
