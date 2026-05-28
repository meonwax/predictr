"""HTTP routes for the ``/shouts`` page.

UX shape:

* ``GET /shouts`` renders the full panel: a one-line submit form on top,
  followed by every previous message in reverse-chronological order.
* ``POST /shouts`` validates the message and stores a new row. For HTMX
  clients (``HX-Request: true``) the response is the *whole* updated
  panel (form + list) which HTMX swaps in place via ``outerHTML``. That
  keeps the wiring trivial: we don't need OOB swaps to surface validation
  errors, and the submit input is re-rendered empty on success or with
  the user's text + an inline error on failure.

Non-HTMX clients (browser without JS) get a vanilla 303 redirect back to
``/shouts`` so the page still works without scripts.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from app.dependencies import DbSession, RequiredUser
from app.routes._helpers import is_htmx
from app.services.shouts import (
    MAX_MESSAGE_LEN,
    InvalidShout,
    create_shout,
    list_shouts,
)
from app.templating import templates

router = APIRouter(tags=["shouts"])


def _render_panel(
    request: Request,
    *,
    db,
    current_user,
    draft: str = "",
    error: str | None = None,
    error_args: dict[str, object] | None = None,
) -> HTMLResponse:
    """Render the shoutbox panel (form + list) - used by both GET and POST."""
    shouts = list_shouts(db)
    return templates.TemplateResponse(
        request,
        "_shoutbox_panel.html",
        {
            "current_user": current_user,
            "shouts": shouts,
            "max_message_len": MAX_MESSAGE_LEN,
            "draft": draft,
            "error": error,
            "error_args": error_args or {},
        },
    )


_SHOUT_ERROR_KEYS: dict[str, tuple[str, dict[str, object]]] = {
    "empty": ("error.shout.empty", {}),
    "too_long": ("error.shout.too_long", {"max": MAX_MESSAGE_LEN}),
}


def _map_invalid_shout(exc: InvalidShout) -> tuple[str, dict[str, object]]:
    """Translate :class:`InvalidShout` into an i18n key + args pair."""
    key, args = _SHOUT_ERROR_KEYS.get(exc.kind or "", ("error.shout.empty", {}))
    return key, dict(args)


@router.get("/shouts", response_class=HTMLResponse, name="shouts:index")
def shouts_index(
    request: Request,
    db: DbSession,
    user: RequiredUser,
) -> Response:
    shouts = list_shouts(db)
    return templates.TemplateResponse(
        request,
        "shouts.html",
        {
            "current_user": user,
            "shouts": shouts,
            "max_message_len": MAX_MESSAGE_LEN,
            "draft": "",
            "error": None,
            "error_args": {},
            "active_nav": "shouts",
        },
    )


@router.post("/shouts", include_in_schema=False)
def shouts_create(
    request: Request,
    db: DbSession,
    user: RequiredUser,
    message: Annotated[str, Form()] = "",
) -> Response:
    error: str | None = None
    error_args: dict[str, object] = {}
    cleaned = message
    try:
        create_shout(db, user, message=message)
        cleaned = ""  # success -> clear the input
    except InvalidShout as exc:
        error, error_args = _map_invalid_shout(exc)

    if is_htmx(request):
        return _render_panel(
            request,
            db=db,
            current_user=user,
            draft=cleaned,
            error=error,
            error_args=error_args,
        )

    return RedirectResponse(url="/shouts", status_code=status.HTTP_303_SEE_OTHER)
