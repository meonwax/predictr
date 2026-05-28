"""User-facing ``/questions`` route.

Lists every special question with the current user's answer, an inline
edit form (until the deadline) and the earned-points readout once the
admin has stamped a correct answer.

Submitting an empty answer deletes the user's row, mirroring the
"both blank deletes" pattern from ``/bets``.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from app.dependencies import DbSession, RequiredUser
from app.routes._helpers import is_htmx, map_invalid_question
from app.services.questions import (
    MAX_ANSWER_LEN,
    DeadlinePassed,
    InvalidQuestionData,
    QuestionNotFound,
    delete_answer,
    get_question_view_for_user,
    list_other_answers_for_question,
    list_questions_for_user,
    upsert_answer,
)
from app.templating import templates

router = APIRouter(tags=["questions"])


@router.get("/questions", response_class=HTMLResponse, name="questions:index")
def questions_index(
    request: Request,
    db: DbSession,
    user: RequiredUser,
) -> Response:
    entries = list_questions_for_user(db, user)
    return templates.TemplateResponse(
        request,
        "questions.html",
        {
            "current_user": user,
            "entries": entries,
            "max_answer_len": MAX_ANSWER_LEN,
            "active_nav": "questions",
        },
    )


@router.post("/questions/{question_id}", include_in_schema=False)
def save_answer(
    request: Request,
    question_id: int,
    db: DbSession,
    user: RequiredUser,
    answer: Annotated[str, Form()] = "",
) -> Response:
    """Upsert (or, when blank, delete) one answer."""
    error: str | None = None
    error_args: dict[str, object] = {}
    cleaned = answer.strip()
    try:
        if not cleaned:
            delete_answer(db, user, question_id)
        else:
            upsert_answer(db, user, question_id=question_id, answer_text=cleaned)
    except QuestionNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown question.") from None
    except DeadlinePassed:
        error = "error.question.deadline_passed"
    except InvalidQuestionData as exc:
        error, error_args = map_invalid_question(exc)

    if is_htmx(request):
        entry = get_question_view_for_user(db, user, question_id)
        return templates.TemplateResponse(
            request,
            "_answer_cell.html",
            {
                "entry": entry,
                "max_answer_len": MAX_ANSWER_LEN,
                "just_saved": error is None,
                "error": error,
                "error_args": error_args,
                "current_user": user,
            },
        )

    return RedirectResponse(url="/questions", status_code=status.HTTP_303_SEE_OTHER)


# ---------------------------------------------------------------------------
# GET /questions/{id}/others - modal-body fragment listing other players
# ---------------------------------------------------------------------------


@router.get(
    "/questions/{question_id}/others",
    response_class=HTMLResponse,
    include_in_schema=False,
    name="questions:others",
)
def other_answers(
    request: Request,
    question_id: int,
    db: DbSession,
    user: RequiredUser,
) -> Response:
    """Tiny HTML fragment listing every other player's answer for this question.

    Before the question's deadline the response is rendered with
    ``can_view=False`` so the modal shows a placeholder; afterwards we
    list each opponent's answer with the same green/neutral colouring
    used on the user's own row.
    """
    try:
        view = list_other_answers_for_question(db, user, question_id)
    except QuestionNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown question.") from None
    return templates.TemplateResponse(
        request,
        "_other_answers.html",
        {"view": view, "current_user": user},
    )
