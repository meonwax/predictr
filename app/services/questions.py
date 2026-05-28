"""Business logic for special questions and per-user answers.

Two surfaces share this module:

* The user-facing ``/questions`` page reads via :func:`list_questions_for_user`
  and writes via :func:`upsert_answer` / :func:`delete_answer`. Once a
  question's ``deadline`` is in the past, all per-user write paths are
  closed and the correct answer (plus the user's earned points) becomes
  readable.
* The admin ``/admin/questions`` page uses :func:`list_all_questions`,
  :func:`create_question`, :func:`update_question`, and :func:`delete_question`.

Both surfaces lean on :mod:`app.services.scoring` for point computation,
keeping the rules defined in exactly one place.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import NamedTuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models import Answer, Question, User
from app.services.scoring import calculate_answer_points

LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Validation constants
# ---------------------------------------------------------------------------

MIN_QUESTION_LEN: int = 5
MAX_QUESTION_LEN: int = 500
MIN_POINTS: int = 1
MAX_POINTS: int = 999
MAX_CORRECT_ANSWER_LEN: int = 500
MAX_ANSWER_LEN: int = 500


# ---------------------------------------------------------------------------
# Domain exceptions
# ---------------------------------------------------------------------------


class QuestionNotFound(KeyError):
    """Raised when the supplied question id doesn't exist."""


class DeadlinePassed(Exception):
    """Raised when a user tries to upsert/delete an answer after the deadline."""


class InvalidQuestionData(ValueError):
    """Raised when admin or user input fails validation (text length, points range).

    Carries a machine-readable ``kind`` attribute (one of ``"text_too_short"``,
    ``"text_too_long"``, ``"points_not_int"``, ``"points_range"``,
    ``"points_required"``, ``"correct_too_long"``, ``"answer_empty"``,
    ``"answer_too_long"``, ``"deadline_required"``, ``"deadline_invalid"``)
    so the route layer can pick the right translation key without parsing
    the English text. The base ``args`` still hold the English message for
    log compatibility.
    """

    def __init__(self, message: str, *, kind: str | None = None) -> None:
        super().__init__(message)
        self.kind = kind


# ---------------------------------------------------------------------------
# Read models
# ---------------------------------------------------------------------------


class QuestionForUser(NamedTuple):
    """One row on the user-facing /questions page."""

    question: Question
    answer: Answer | None
    points_earned: int
    can_answer: bool
    correct_answer_display: str | None  # first variant of correct_answer, post-deadline


@dataclass(slots=True, frozen=True)
class QuestionForAdmin:
    """One row on the admin /admin/questions page."""

    question: Question
    answer_count: int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _correct_answer_display(correct_answer: str | None) -> str | None:
    """Return the first comma-separated variant, used as the "canonical" form.

    The full ``correct_answer`` value may list several accepted spellings
    (e.g. ``"Germany,Deutschland,GER"``); the UI shows only the first one
    to players after the deadline so the answer reveal is unambiguous.
    """
    if not correct_answer:
        return None
    first = correct_answer.split(",", 1)[0].strip()
    return first or None


def _ensure_question(db: Session, question_id: int) -> Question:
    q = db.get(Question, question_id)
    if q is None:
        raise QuestionNotFound(question_id)
    return q


def _validate_question_text(text: str) -> str:
    cleaned = (text or "").strip()
    if len(cleaned) < MIN_QUESTION_LEN:
        raise InvalidQuestionData(
            f"Question text must be at least {MIN_QUESTION_LEN} characters.",
            kind="text_too_short",
        )
    if len(cleaned) > MAX_QUESTION_LEN:
        raise InvalidQuestionData(
            f"Question text must be at most {MAX_QUESTION_LEN} characters.",
            kind="text_too_long",
        )
    return cleaned


def _validate_points(points: int) -> int:
    if not isinstance(points, int):  # type: ignore[unreachable]
        raise InvalidQuestionData("Points must be an integer.", kind="points_not_int")
    if points < MIN_POINTS or points > MAX_POINTS:
        raise InvalidQuestionData(
            f"Points must be between {MIN_POINTS} and {MAX_POINTS}.",
            kind="points_range",
        )
    return points


def _validate_correct_answer(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    if len(cleaned) > MAX_CORRECT_ANSWER_LEN:
        raise InvalidQuestionData(
            f"Correct answer must be at most {MAX_CORRECT_ANSWER_LEN} characters.",
            kind="correct_too_long",
        )
    return cleaned


def _validate_deadline(deadline: datetime) -> datetime:
    """Coerce to a tz-aware UTC datetime; reject naive input."""
    if deadline.tzinfo is None:
        # The route layer is expected to attach a tzinfo before calling us,
        # but be defensive: treat naive input as already UTC so we don't
        # silently shift hours.
        deadline = deadline.replace(tzinfo=UTC)
    return deadline.astimezone(UTC)


# ---------------------------------------------------------------------------
# User-facing reads
# ---------------------------------------------------------------------------


def list_questions_for_user(
    db: Session,
    user: User,
    *,
    now: datetime | None = None,
) -> list[QuestionForUser]:
    """Return every question paired with *user*'s answer (if any).

    Ordered by deadline ascending so urgent items float to the top.
    Points and correct-answer text are only included once the deadline
    has passed; the route layer can then choose how to render that.
    """
    now = now or datetime.now(UTC)

    questions = db.scalars(select(Question).order_by(Question.deadline, Question.id)).all()

    # One SELECT for all the user's answers, keyed by question_id.
    answers = {
        a.question_id: a for a in db.scalars(select(Answer).where(Answer.user_id == user.id)).all()
    }

    result: list[QuestionForUser] = []
    for q in questions:
        ans = answers.get(q.id)
        # Gate point computation + correct-answer display behind the
        # deadline so users can't reverse-engineer one from the other
        # before they're allowed to.
        if q.deadline > now:
            can_answer = True
            points = 0
            correct_display: str | None = None
        else:
            can_answer = False
            correct_display = _correct_answer_display(q.correct_answer)
            points = (
                calculate_answer_points(
                    ans.answer if ans else None,
                    q.correct_answer,
                    q.points,
                )
                if ans is not None and q.correct_answer
                else 0
            )
        result.append(
            QuestionForUser(
                question=q,
                answer=ans,
                points_earned=points,
                can_answer=can_answer,
                correct_answer_display=correct_display,
            )
        )
    return result


def get_question_view_for_user(
    db: Session,
    user: User,
    question_id: int,
    *,
    now: datetime | None = None,
) -> QuestionForUser:
    """Return one :class:`QuestionForUser` row, used by the HTMX swap."""
    now = now or datetime.now(UTC)
    q = _ensure_question(db, question_id)
    ans = db.scalars(
        select(Answer).where(Answer.user_id == user.id, Answer.question_id == question_id)
    ).one_or_none()
    if q.deadline > now:
        can_answer = True
        points = 0
        correct_display: str | None = None
    else:
        can_answer = False
        correct_display = _correct_answer_display(q.correct_answer)
        points = (
            calculate_answer_points(
                ans.answer if ans else None,
                q.correct_answer,
                q.points,
            )
            if ans is not None and q.correct_answer
            else 0
        )
    return QuestionForUser(
        question=q,
        answer=ans,
        points_earned=points,
        can_answer=can_answer,
        correct_answer_display=correct_display,
    )


# ---------------------------------------------------------------------------
# User-facing mutations
# ---------------------------------------------------------------------------


def upsert_answer(
    db: Session,
    user: User,
    *,
    question_id: int,
    answer_text: str,
    now: datetime | None = None,
) -> Answer:
    """Insert or update *user*'s answer for *question_id*.

    Raises:
        :class:`QuestionNotFound`  unknown question id
        :class:`DeadlinePassed`    deadline already in the past
        :class:`InvalidQuestionData`  answer empty after trim, or too long
    """
    now = now or datetime.now(UTC)
    q = _ensure_question(db, question_id)
    if q.deadline <= now:
        raise DeadlinePassed(question_id)

    cleaned = (answer_text or "").strip()
    if not cleaned:
        raise InvalidQuestionData("Answer must not be empty.", kind="answer_empty")
    if len(cleaned) > MAX_ANSWER_LEN:
        raise InvalidQuestionData(
            f"Answer must be at most {MAX_ANSWER_LEN} characters.",
            kind="answer_too_long",
        )

    ans = db.scalars(
        select(Answer).where(
            Answer.user_id == user.id,
            Answer.question_id == question_id,
        )
    ).one_or_none()
    if ans is None:
        ans = Answer(user_id=user.id, question_id=question_id)
        db.add(ans)
    ans.answer = cleaned
    db.commit()
    db.refresh(ans)
    LOGGER.info(
        "Answer upsert: user=%d question=%d (%d chars)",
        user.id,
        question_id,
        len(cleaned),
    )
    return ans


def delete_answer(
    db: Session,
    user: User,
    question_id: int,
    *,
    now: datetime | None = None,
) -> None:
    """Remove *user*'s answer for *question_id*. No-op if none exists.

    Same deadline rule as :func:`upsert_answer`.
    """
    now = now or datetime.now(UTC)
    q = _ensure_question(db, question_id)
    if q.deadline <= now:
        raise DeadlinePassed(question_id)
    ans = db.scalars(
        select(Answer).where(
            Answer.user_id == user.id,
            Answer.question_id == question_id,
        )
    ).one_or_none()
    if ans is None:
        return
    db.delete(ans)
    db.commit()
    LOGGER.info("Answer deleted: user=%d question=%d", user.id, question_id)


# ---------------------------------------------------------------------------
# Admin reads
# ---------------------------------------------------------------------------


def list_all_questions(db: Session) -> list[QuestionForAdmin]:
    """All questions plus a count of how many users have already answered."""
    counts_subq = (
        select(Answer.question_id, func.count(Answer.id).label("n"))
        .group_by(Answer.question_id)
        .subquery()
    )
    rows = db.execute(
        select(Question, counts_subq.c.n)
        .outerjoin(counts_subq, counts_subq.c.question_id == Question.id)
        .order_by(Question.deadline, Question.id)
    ).all()
    return [QuestionForAdmin(question=q, answer_count=int(n or 0)) for q, n in rows]


# ---------------------------------------------------------------------------
# Admin mutations
# ---------------------------------------------------------------------------


def create_question(
    db: Session,
    *,
    text: str,
    deadline: datetime,
    points: int,
    correct_answer: str | None = None,
) -> Question:
    """Create a new question. All validation lives here."""
    cleaned_text = _validate_question_text(text)
    points = _validate_points(points)
    deadline = _validate_deadline(deadline)
    correct = _validate_correct_answer(correct_answer)

    q = Question(
        question=cleaned_text,
        deadline=deadline,
        points=points,
        correct_answer=correct,
    )
    db.add(q)
    db.commit()
    db.refresh(q)
    LOGGER.info("Question created: id=%d", q.id)
    return q


def update_question(
    db: Session,
    question_id: int,
    *,
    text: str,
    deadline: datetime,
    points: int,
    correct_answer: str | None = None,
) -> Question:
    """Update an existing question; raises :class:`QuestionNotFound`."""
    q = _ensure_question(db, question_id)
    q.question = _validate_question_text(text)
    q.points = _validate_points(points)
    q.deadline = _validate_deadline(deadline)
    q.correct_answer = _validate_correct_answer(correct_answer)
    db.commit()
    db.refresh(q)
    LOGGER.info("Question updated: id=%d", q.id)
    return q


def delete_question(db: Session, question_id: int) -> None:
    """Delete the question; the FK on ``answer`` cascades automatically."""
    q = db.get(Question, question_id)
    if q is None:
        # Idempotent - the route layer can treat "already gone" as success.
        return
    # Manual cascade: the FK constraint isn't declared ON DELETE CASCADE,
    # so wipe the dependent answers explicitly before removing the parent.
    db.query(Answer).filter(Answer.question_id == question_id).delete()
    db.delete(q)
    db.commit()
    LOGGER.info("Question deleted: id=%d", question_id)


# ---------------------------------------------------------------------------
# "Other players' answers" - read-only peek behind the deadline curtain
# ---------------------------------------------------------------------------


class OtherAnswer(NamedTuple):
    """One opponent's answer for a question, post-deadline."""

    user: User
    answer: str | None
    points: int


class OtherAnswersView(NamedTuple):
    """Payload backing the /questions/{id}/others modal.

    ``can_view`` mirrors :class:`app.services.bets.OtherBetsView` - until
    the deadline passes we return ``False`` and an empty list, and the
    route renders the "locked" message instead of the table.
    """

    question: Question
    can_view: bool
    others: list[OtherAnswer]


def list_other_answers_for_question(
    db: Session,
    requesting_user: User,
    question_id: int,
    *,
    now: datetime | None = None,
) -> OtherAnswersView:
    """Answers submitted by everybody else for *question_id*.

    Order: by earned points descending (best first), then user name
    ascending. Excludes the requesting user.

    Raises:
        :class:`QuestionNotFound`  unknown ``question_id``
    """
    now = now or datetime.now(UTC)
    q = _ensure_question(db, question_id)
    if q.deadline > now:
        return OtherAnswersView(question=q, can_view=False, others=[])

    answers = db.scalars(
        select(Answer)
        .options(joinedload(Answer.user))
        .where(
            Answer.question_id == question_id,
            Answer.user_id != requesting_user.id,
        )
    ).all()

    others = [
        OtherAnswer(
            user=ans.user,
            answer=ans.answer,
            points=(
                calculate_answer_points(ans.answer, q.correct_answer, q.points)
                if q.correct_answer
                else 0
            ),
        )
        for ans in answers
    ]
    others.sort(key=lambda o: (-o.points, o.user.name.lower()))
    return OtherAnswersView(question=q, can_view=True, others=others)


__all__ = [
    "MIN_QUESTION_LEN",
    "MAX_QUESTION_LEN",
    "MIN_POINTS",
    "MAX_POINTS",
    "MAX_CORRECT_ANSWER_LEN",
    "MAX_ANSWER_LEN",
    "QuestionNotFound",
    "DeadlinePassed",
    "InvalidQuestionData",
    "QuestionForUser",
    "QuestionForAdmin",
    "OtherAnswer",
    "OtherAnswersView",
    "list_questions_for_user",
    "get_question_view_for_user",
    "upsert_answer",
    "delete_answer",
    "list_all_questions",
    "create_question",
    "update_question",
    "delete_question",
    "list_other_answers_for_question",
]
