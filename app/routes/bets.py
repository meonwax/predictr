"""HTTP routes for the ``/bets`` page.

UX shape:

* ``GET /bets`` renders one row per fixture, grouped by tournament phase.
  For each cell the user can still edit, the row shows a two-input form
  (home / away score) and a save button. For locked rows it shows the
  user's prior bet read-only, plus the points they earned once the
  result is in.
* ``POST /bets/{game_id}`` upserts (or, when both fields are blank,
  deletes) a single bet. The request body is form-encoded:

  ::

      score_home=2&score_away=1            # upsert
      score_home=&score_away=              # delete

  Mixed (one blank, one set) is a validation error.

* HTMX clients (identified by ``HX-Request: true``) get the updated
  ``<td>`` fragment swapped in place. Non-HTMX clients are redirected
  back to ``/bets`` so the page still works with JS disabled.

CSRF: the session cookie is ``SameSite=Lax``, so cross-site POSTs from
attacker pages don't carry it - they 401 before reaching this handler.
We rely on that rather than an explicit token; revisit if any future
endpoint needs cross-site embedding.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from app.dependencies import DbSession, RequiredUser
from app.services.bets import (
    MAX_SCORE,
    MIN_SCORE,
    BetDeadlinePassed,
    GameNotFound,
    InvalidScore,
    delete_bet,
    get_cell_view,
    list_games_with_bets_grouped,
    list_other_bets_for_game,
    upsert_bet,
)
from app.templating import templates

router = APIRouter(tags=["bets"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _is_htmx(request: Request) -> bool:
    return request.headers.get("HX-Request", "").lower() == "true"


def _parse_score(raw: str) -> int | None:
    """Parse a score form value into an int, or return None for blank.

    Raises :class:`ValueError` if *raw* is non-blank but not a clean integer.
    """
    s = raw.strip()
    if s == "":
        return None
    return int(s)  # may raise ValueError


# ---------------------------------------------------------------------------
# GET /bets - full page
# ---------------------------------------------------------------------------


@router.get("/bets", response_class=HTMLResponse, name="bets:index")
def bets_index(
    request: Request,
    db: DbSession,
    user: RequiredUser,
) -> Response:
    """Render every fixture with the current user's bets and scoring."""
    sections = list_games_with_bets_grouped(db, user)
    return templates.TemplateResponse(
        request,
        "bets.html",
        {
            "sections": sections,
            "current_user": user,
            "min_score": MIN_SCORE,
            "max_score": MAX_SCORE,
        },
    )


# ---------------------------------------------------------------------------
# POST /bets/{game_id} - upsert / delete a single bet
# ---------------------------------------------------------------------------


@router.post("/bets/{game_id}", include_in_schema=False)
def save_bet(
    request: Request,
    game_id: int,
    db: DbSession,
    user: RequiredUser,
    score_home: Annotated[str, Form()] = "",
    score_away: Annotated[str, Form()] = "",
) -> Response:
    """Upsert (or delete) one bet and return either an HTMX fragment or a 303.

    Validation errors are rendered into the bet-cell as an i18n key (``error``)
    plus a ``error_args`` dict, so the template translates the message into
    the user's language at render time.
    """
    error: str | None = None
    error_args: dict[str, object] = {}
    try:
        home = _parse_score(score_home)
        away = _parse_score(score_away)
    except ValueError:
        error = "error.score.invalid"
        home = away = None

    if error is None:
        if home is None and away is None:
            try:
                delete_bet(db, user, game_id)
            except GameNotFound:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown game.") from None
            except BetDeadlinePassed:
                error = "error.bet.deadline_passed"
        elif home is None or away is None:
            error = "error.score.partial"
        else:
            try:
                upsert_bet(
                    db,
                    user,
                    game_id=game_id,
                    score_home=home,
                    score_away=away,
                )
            except GameNotFound:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown game.") from None
            except BetDeadlinePassed:
                error = "error.bet.deadline_passed"
            except InvalidScore as exc:
                error, error_args = _map_invalid_score(exc)

    if _is_htmx(request):
        # Fetch the fresh cell state and return just the <td> fragment.
        entry = get_cell_view(db, user, game_id)
        return templates.TemplateResponse(
            request,
            "_bet_cell.html",
            {
                "entry": entry,
                "min_score": MIN_SCORE,
                "max_score": MAX_SCORE,
                "just_saved": error is None,
                "error": error,
                "error_args": error_args,
                "current_user": user,
            },
        )

    # No HTMX -> vanilla browser POST. Round-trip via PRG.
    return RedirectResponse(url="/bets", status_code=status.HTTP_303_SEE_OTHER)


def _map_invalid_score(exc: InvalidScore) -> tuple[str, dict[str, object]]:
    """Translate an :class:`InvalidScore` into an i18n key + args pair.

    The route never trusts the exception's message - it only inspects the
    structured ``field`` / ``kind`` attributes so the same error wording
    surfaces consistently in both languages.
    """
    field_key = "error.score.home" if exc.field == "score_home" else "error.score.away"
    if exc.kind == "range":
        return "error.score.range", {
            "field_key": field_key,
            "min": MIN_SCORE,
            "max": MAX_SCORE,
        }
    return "error.score.not_int", {"field_key": field_key}


# ---------------------------------------------------------------------------
# GET /bets/{game_id}/others - modal-body fragment listing other players
# ---------------------------------------------------------------------------


@router.get(
    "/bets/{game_id}/others",
    response_class=HTMLResponse,
    include_in_schema=False,
    name="bets:others",
)
def other_bets(
    request: Request,
    game_id: int,
    db: DbSession,
    user: RequiredUser,
) -> Response:
    """Tiny HTML fragment listing every other player's bet on this game.

    The view is kickoff-gated for fairness: before kickoff the response
    is rendered with ``can_view=False`` so the modal shows a "wait until
    kickoff" placeholder rather than the table, which would otherwise
    leak everyone's prediction to a player who hasn't bet yet.
    """
    try:
        view = list_other_bets_for_game(db, user, game_id)
    except GameNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown game.") from None
    return templates.TemplateResponse(
        request,
        "_other_bets.html",
        {"view": view, "current_user": user},
    )
