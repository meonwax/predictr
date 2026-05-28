"""``/admin/questions`` handlers.

The admin CRUD for the special-questions feature:

* ``GET /admin/questions``                     - list + new-question form
* ``POST /admin/questions/new``                - create
* ``POST /admin/questions/{id}``               - update (HTMX-swappable row)
* ``POST /admin/questions/{id}/delete``        - delete (HTMX-swappable row)

Validation errors raised by the service layer surface as i18n keys in
two different ways: HTMX swaps render them inline via the template's
``_()`` global; the create-form redirect carries the translated text as
a query parameter, which is why this module owns the small
``_admin_language`` / ``_translate`` helpers.
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
from app.models import Answer, Question, User
from app.routes._helpers import is_htmx, map_invalid_question
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
from app.templating import templates

router = APIRouter()


_QUESTION_TEMPLATE_CTX = {
    "min_points": MIN_POINTS,
    "max_points": MAX_POINTS,
    "max_question_len": MAX_QUESTION_LEN,
    "max_correct_answer_len": MAX_CORRECT_ANSWER_LEN,
}


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


__all__ = ["router"]
