"""Admin-only HTTP routes.

Currently three handlers:

* ``GET /admin`` - small dashboard with counts and quick links.
* ``GET /admin/games`` - every game in an editable table; one form per
  row, HTMX-driven the same way ``/bets`` is. Submitting an empty
  scoreline both clears the result.
* ``POST /admin/games/{game_id}`` - upsert / clear the official result.

Every route in this module is protected by :data:`RequiredAdmin` so an
anonymous request 401s and a non-admin 403s. (See
:func:`app.dependencies.require_admin`.)
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy import func as sa_func
from sqlalchemy import select

from app.config import get_settings
from app.dependencies import DbSession, RequiredAdmin
from app.i18n import gettext, resolve_language
from app.models import Answer, Game, Question, User
from app.routes._helpers import (
    is_htmx,
    map_invalid_question,
    map_invalid_score,
    parse_score,
)
from app.services.admin import (
    MAX_NOTES_LEN,
    InvalidTeamAssignment,
    NotesTooLong,
    clear_game_result,
    get_dashboard_stats,
    list_games_for_admin,
    list_teams_grouped,
    set_game_result,
    set_game_teams,
)
from app.services.games import MAX_SCORE, MIN_SCORE, GameNotFound, InvalidScore
from app.services.questions import (
    MAX_CORRECT_ANSWER_LEN,
    MAX_POINTS,
    MAX_QUESTION_LEN,
    MIN_POINTS,
    InvalidQuestionData,
    QuestionForAdmin,
    QuestionNotFound,
    create_question,
    delete_question,
    list_all_questions,
    update_question,
)
from app.team_data import KNOCKOUT_GROUP_IDS
from app.templating import templates

_TEAM_ERROR_KEYS: dict[str, str] = {
    "unknown_team": "error.team.unknown",
    "same_team": "error.team.same",
    "not_knockout": "error.team.not_knockout",
}


def _map_invalid_team(exc: InvalidTeamAssignment) -> tuple[str, dict[str, object]]:
    return _TEAM_ERROR_KEYS.get(exc.kind, "error.team.unknown"), {}


def _admin_language(user: User) -> str:
    """Return the language code we'll use to translate flash messages for *user*."""
    return resolve_language(
        user.preferred_language,
        default=get_settings().default_language,
    )


def _translate(user: User, key: str, args: dict[str, object]) -> str:
    """Translate *key* into the admin user's language, resolving ``*_key`` args.

    Used for PRG flash messages whose URL only carries a final string. For
    HTMX swaps the template-side ``_()`` global does the same job - there
    the request-scoped language is already on the rendering context.
    """
    language = _admin_language(user)
    resolved: dict[str, object] = {}
    for name, value in args.items():
        if name.endswith("_key") and isinstance(value, str):
            resolved[name[:-4]] = gettext(value, language)
        else:
            resolved[name] = value
    return gettext(key, language, **resolved)


router = APIRouter(prefix="/admin", tags=["admin"])


# ---------------------------------------------------------------------------
# GET /admin - dashboard
# ---------------------------------------------------------------------------


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


# ===========================================================================
# Special questions (/admin/questions)
# ===========================================================================


_QUESTION_TEMPLATE_CTX = {
    "min_points": MIN_POINTS,
    "max_points": MAX_POINTS,
    "max_question_len": MAX_QUESTION_LEN,
    "max_correct_answer_len": MAX_CORRECT_ANSWER_LEN,
}


def _parse_deadline(raw: str) -> datetime:
    """Parse the ``<input type="datetime-local">`` value as UTC.

    The HTML widget submits ``YYYY-MM-DDTHH:MM`` (no timezone), which we
    deliberately interpret as UTC because every other timestamp in the app
    is UTC. Admins entering local times should mentally convert; we'll
    revisit timezone handling once we add per-user locale support.
    """
    s = (raw or "").strip()
    if not s:
        raise InvalidQuestionData("Deadline is required.", kind="deadline_required")
    try:
        # Accept both 'YYYY-MM-DDTHH:MM' and the longer 'YYYY-MM-DDTHH:MM:SS'.
        if len(s) == 16:
            s = s + ":00"
        return datetime.fromisoformat(s).replace(tzinfo=UTC)
    except ValueError as exc:
        raise InvalidQuestionData(f"Invalid deadline: {exc}.", kind="deadline_invalid") from exc


def _parse_points(raw: str) -> int:
    s = (raw or "").strip()
    if not s:
        raise InvalidQuestionData("Points is required.", kind="points_required")
    try:
        return int(s)
    except ValueError as exc:
        raise InvalidQuestionData("Points must be a whole number.", kind="points_not_int") from exc


@router.get("/questions", response_class=HTMLResponse, name="admin:questions")
def admin_questions(
    request: Request,
    db: DbSession,
    user: RequiredAdmin,
) -> Response:
    questions = list_all_questions(db)
    return templates.TemplateResponse(
        request,
        "admin/questions.html",
        {
            "current_user": user,
            "questions": questions,
            "active_nav": "admin",
            **_QUESTION_TEMPLATE_CTX,
        },
    )


@router.post("/questions/new", include_in_schema=False)
def admin_create_question(
    db: DbSession,
    user: RequiredAdmin,
    text: Annotated[str, Form(alias="question")] = "",
    deadline: Annotated[str, Form()] = "",
    points: Annotated[str, Form()] = "",
    correct_answer: Annotated[str, Form()] = "",
) -> RedirectResponse:
    try:
        parsed_deadline = _parse_deadline(deadline)
        parsed_points = _parse_points(points)
        create_question(
            db,
            text=text,
            deadline=parsed_deadline,
            points=parsed_points,
            correct_answer=correct_answer,
        )
    except InvalidQuestionData as exc:
        key, args = map_invalid_question(exc)
        return RedirectResponse(
            url=f"/admin/questions?error={quote(_translate(user, key, args))}",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    return RedirectResponse(
        url="/admin/questions?saved=created",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/questions/{question_id}", include_in_schema=False)
def admin_update_question(
    request: Request,
    question_id: int,
    db: DbSession,
    user: RequiredAdmin,
    text: Annotated[str, Form(alias="question")] = "",
    deadline: Annotated[str, Form()] = "",
    points: Annotated[str, Form()] = "",
    correct_answer: Annotated[str, Form()] = "",
) -> Response:
    error: str | None = None
    error_args: dict[str, object] = {}
    try:
        parsed_deadline = _parse_deadline(deadline)
        parsed_points = _parse_points(points)
        update_question(
            db,
            question_id,
            text=text,
            deadline=parsed_deadline,
            points=parsed_points,
            correct_answer=correct_answer,
        )
    except QuestionNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown question.") from None
    except InvalidQuestionData as exc:
        error, error_args = map_invalid_question(exc)

    if is_htmx(request):
        question = db.get(Question, question_id)
        if question is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown question.")
        answer_count = (
            db.scalar(select(sa_func.count(Answer.id)).where(Answer.question_id == question_id))
            or 0
        )
        entry = QuestionForAdmin(question=question, answer_count=int(answer_count))
        return templates.TemplateResponse(
            request,
            "admin/_question_row.html",
            {
                "entry": entry,
                "just_saved": error is None,
                "error": error,
                "error_args": error_args,
                "current_user": user,
                **_QUESTION_TEMPLATE_CTX,
            },
        )
    return RedirectResponse(
        url="/admin/questions" + ("?saved=updated" if error is None else ""),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/questions/{question_id}/delete", include_in_schema=False)
def admin_delete_question(
    request: Request,
    question_id: int,
    db: DbSession,
    user: RequiredAdmin,
) -> Response:
    delete_question(db, question_id)
    if is_htmx(request):
        # Returning an empty body with hx-swap="outerHTML" removes the row.
        return Response(status_code=status.HTTP_200_OK)
    return RedirectResponse(
        url="/admin/questions?saved=deleted",
        status_code=status.HTTP_303_SEE_OTHER,
    )
