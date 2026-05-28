"""HTTP routes for the ``/settings`` page.

Three logically separate forms share the same page (and therefore the same
URL prefix). Each form POSTs to its own endpoint, every endpoint redirects
back to ``/settings`` with a status query param so the page can show a
"saved" badge. POST-redirect-GET keeps the back/refresh behaviour sane.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, File, Form, Request, UploadFile, status
from fastapi.responses import RedirectResponse, Response

from app.config import get_settings
from app.dependencies import DbSession, RequiredUser
from app.routes.auth import MIN_PASSWORD_LEN
from app.services.avatars import (
    AvatarTooLarge,
    InvalidImageData,
    UnsupportedMimeType,
    delete_avatar,
    get_avatar,
    set_avatar,
)
from app.services.users import (
    SUPPORTED_LANGUAGES,
    WrongCurrentPassword,
    change_password,
    update_profile,
)
from app.templating import templates
from app.timezones import SUPPORTED_TIMEZONES

router = APIRouter(tags=["settings"])

# ---- ?saved= / ?error= flags surfaced on the settings page ----------------

_SAVED_PROFILE = "profile"
_SAVED_PASSWORD = "password"
_SAVED_AVATAR = "avatar"
_SAVED_AVATAR_DELETED = "avatar_deleted"


def _redirect(*, saved: str | None = None, error: str | None = None) -> RedirectResponse:
    """Build a POST-redirect-GET response back to /settings.

    Either *saved* (success) or *error* (form error) ends up in the query
    string so the GET handler can render the matching badge.
    """
    url = "/settings"
    if saved is not None:
        url += f"?saved={saved}"
    elif error is not None:
        url += f"?error={error}"
    return RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)


# ---------------------------------------------------------------------------
# GET /settings - render all three forms
# ---------------------------------------------------------------------------


@router.get("/settings", include_in_schema=False)
def settings_page(
    request: Request,
    user: RequiredUser,
    saved: str | None = None,
    error: str | None = None,
) -> Response:
    site = get_settings()
    return templates.TemplateResponse(
        request,
        "settings.html",
        {
            "current_user": user,
            "saved": saved,
            "error": error,
            "supported_languages": SUPPORTED_LANGUAGES,
            "supported_timezones": SUPPORTED_TIMEZONES,
            "min_password_len": MIN_PASSWORD_LEN,
            "default_language": site.default_language,
            "default_timezone": site.default_timezone,
        },
    )


# ---------------------------------------------------------------------------
# POST /settings/profile
# ---------------------------------------------------------------------------


@router.post("/settings/profile", include_in_schema=False)
def update_profile_submit(
    db: DbSession,
    user: RequiredUser,
    name: Annotated[str, Form()],
    preferred_language: Annotated[str, Form()],
    preferred_timezone: Annotated[str, Form()] = "",
) -> RedirectResponse:
    try:
        update_profile(
            db,
            user,
            name=name,
            preferred_language=preferred_language,
            preferred_timezone=preferred_timezone,
        )
    except ValueError:
        return _redirect(error="profile")
    return _redirect(saved=_SAVED_PROFILE)


# ---------------------------------------------------------------------------
# POST /settings/password
# ---------------------------------------------------------------------------


@router.post("/settings/password", include_in_schema=False)
def change_password_submit(
    db: DbSession,
    user: RequiredUser,
    old_password: Annotated[str, Form()],
    new_password: Annotated[str, Form()],
    new_password_confirm: Annotated[str, Form()],
) -> RedirectResponse:
    if new_password != new_password_confirm:
        return _redirect(error="password_mismatch")
    if len(new_password) < MIN_PASSWORD_LEN:
        return _redirect(error="password_too_short")
    try:
        change_password(db, user, old_password=old_password, new_password=new_password)
    except WrongCurrentPassword:
        return _redirect(error="password_wrong_current")
    return _redirect(saved=_SAVED_PASSWORD)


# ---------------------------------------------------------------------------
# POST /settings/avatar - upload
# ---------------------------------------------------------------------------


@router.post("/settings/avatar", include_in_schema=False)
async def upload_avatar_submit(
    db: DbSession,
    user: RequiredUser,
    file: Annotated[UploadFile, File()],
) -> RedirectResponse:
    if not file.filename:
        return _redirect(error="avatar_empty")
    data = await file.read()
    content_type = file.content_type or "application/octet-stream"
    try:
        set_avatar(db, user, data=data, content_type=content_type)
    except AvatarTooLarge:
        return _redirect(error="avatar_too_large")
    except UnsupportedMimeType:
        return _redirect(error="avatar_bad_type")
    except InvalidImageData:
        return _redirect(error="avatar_corrupt")
    return _redirect(saved=_SAVED_AVATAR)


# ---------------------------------------------------------------------------
# POST /settings/avatar/delete
# ---------------------------------------------------------------------------


@router.post("/settings/avatar/delete", include_in_schema=False)
def delete_avatar_submit(
    db: DbSession,
    user: RequiredUser,
) -> RedirectResponse:
    delete_avatar(db, user)
    return _redirect(saved=_SAVED_AVATAR_DELETED)


# ---------------------------------------------------------------------------
# GET /avatars/{user_id} - serve bytes; publicly accessible
# ---------------------------------------------------------------------------


avatars_router = APIRouter(tags=["avatars"])


@avatars_router.get("/avatars/{user_id}", include_in_schema=False)
def serve_avatar(user_id: int, db: DbSession) -> Response:
    avatar = get_avatar(db, user_id)
    if avatar is None:
        # Letting 404 leak the "no avatar" signal is fine - the same info is
        # observable client-side from the navbar/ladder anyway. Other user
        # records are protected by 404 instead of 403 to avoid enumeration
        # of which IDs exist.
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    return Response(
        content=avatar.data,
        media_type=avatar.mime_type,
        headers={"Cache-Control": "private, max-age=300"},
    )
