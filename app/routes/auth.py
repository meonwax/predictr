"""HTTP routes for the auth pages.

URLs in this module:

* ``GET  /login``                - render the login form
* ``POST /login``                - process credentials, set the session cookie
* ``POST /logout``               - clear the session cookie
* ``GET  /register``             - render the registration form
* ``POST /register``             - create the user, redirect to ``/login``
* ``GET  /lostpwd``              - render the "request a reset" form
* ``POST /lostpwd``              - issue a token, send the email
* ``GET  /password/reset/{token}`` - render the "choose new password" form
* ``POST /password/reset/{token}`` - set the new password

The form/handler split keeps the templates server-rendered (matches the
HTMX-without-Alpine plan); a future enhancement can layer ``hx-post``
fragments on top without changing the routes.
"""

from __future__ import annotations

from typing import Annotated

from email_validator import EmailNotValidError, validate_email
from fastapi import APIRouter, Form, Request, status
from fastapi.responses import RedirectResponse

from app.dependencies import (
    CurrentUser,
    DbSession,
    MailerDep,
    SettingsDep,
)
from app.security import make_session_token
from app.services.users import (
    EmailAlreadyRegistered,
    InvalidResetToken,
    RegistrationData,
    authenticate,
    check_reset_token,
    confirm_password_reset,
    register_user,
    request_password_reset,
    touch_last_login,
)
from app.templating import templates

router = APIRouter(tags=["auth"])

MIN_PASSWORD_LEN = 8


def _validate_email(email: str) -> str:
    """Return a normalised (lowercased, IDNA-encoded) email, or raise ``ValueError``.

    Wraps :mod:`email_validator` so the route layer only ever sees one
    exception type for bad-input handling. ``check_deliverability`` is off
    because we don't want a DNS lookup blocking the request loop on every
    registration attempt.
    """
    try:
        return validate_email(email, check_deliverability=False).normalized
    except EmailNotValidError as exc:
        raise ValueError(str(exc)) from exc


def _set_session_cookie(
    response: RedirectResponse,
    *,
    user_id: int,
    settings,
    remember_me: bool,
) -> None:
    token = make_session_token(user_id, settings=settings)
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        max_age=settings.session_max_age_days * 24 * 3600 if remember_me else None,
        httponly=True,
        samesite="lax",
        secure=settings.secure_cookies,
        path="/",
    )


def _clear_session_cookie(response: RedirectResponse, *, settings) -> None:
    # Match the attributes used in _set_session_cookie. Browsers technically
    # only need name+domain+path to drop a cookie, but mirroring secure /
    # samesite avoids edge cases in stricter cookie jars and proxies.
    response.delete_cookie(
        key=settings.session_cookie_name,
        path="/",
        samesite="lax",
        secure=settings.secure_cookies,
        httponly=True,
    )


# ---------------------------------------------------------------------------
# Login / Logout
# ---------------------------------------------------------------------------


@router.get("/login", include_in_schema=False)
def login_form(
    request: Request,
    user: CurrentUser,
    registered: int = 0,
    next: str = "/",
) -> object:
    if user is not None:
        return RedirectResponse(url=next or "/", status_code=303)
    return templates.TemplateResponse(
        request,
        "auth/login.html",
        {
            "next": next,
            "registered": bool(registered),
            "error": None,
            "email": "",
            "current_user": None,
        },
    )


@router.post("/login", include_in_schema=False)
def login_submit(
    request: Request,
    db: DbSession,
    settings: SettingsDep,
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
    remember_me: Annotated[bool, Form()] = False,
    next: Annotated[str, Form()] = "/",
) -> object:
    user = authenticate(db, email, password)
    if user is None:
        return templates.TemplateResponse(
            request,
            "auth/login.html",
            {
                "next": next,
                "registered": False,
                "error": "error.auth.invalid_credentials",
                "email": email,
                "current_user": None,
            },
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    touch_last_login(db, user)
    destination = next or "/"
    response = RedirectResponse(url=destination, status_code=303)
    _set_session_cookie(response, user_id=user.id, settings=settings, remember_me=remember_me)
    return response


@router.post("/logout", include_in_schema=False)
def logout(settings: SettingsDep) -> RedirectResponse:
    response = RedirectResponse(url="/login", status_code=303)
    _clear_session_cookie(response, settings=settings)
    return response


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


@router.get("/register", include_in_schema=False)
def register_form(request: Request, user: CurrentUser) -> object:
    if user is not None:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse(
        request,
        "auth/register.html",
        {
            "error": None,
            "name": "",
            "email": "",
            "min_password_len": MIN_PASSWORD_LEN,
            "current_user": None,
        },
    )


@router.post("/register", include_in_schema=False)
def register_submit(
    request: Request,
    db: DbSession,
    name: Annotated[str, Form()],
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
) -> object:
    def _render_error(error_key: str, code: int = status.HTTP_400_BAD_REQUEST):
        return templates.TemplateResponse(
            request,
            "auth/register.html",
            {
                "error": error_key,
                "name": name,
                "email": email,
                "min_password_len": MIN_PASSWORD_LEN,
                "current_user": None,
            },
            status_code=code,
        )

    if len(name.strip()) < 2:
        return _render_error("error.auth.name_too_short")
    if len(password) < MIN_PASSWORD_LEN:
        return _render_error("error.auth.password_too_short")
    try:
        normalised_email = _validate_email(email)
    except ValueError:
        return _render_error("error.auth.invalid_email")

    try:
        register_user(
            db,
            RegistrationData(
                name=name,
                email=normalised_email,
                password=password,
            ),
        )
    except EmailAlreadyRegistered:
        return _render_error("error.auth.email_taken")

    return RedirectResponse(url="/login?registered=1", status_code=303)


# ---------------------------------------------------------------------------
# Lost password
# ---------------------------------------------------------------------------


@router.get("/lostpwd", include_in_schema=False)
def lostpwd_form(request: Request, user: CurrentUser, sent: int = 0) -> object:
    return templates.TemplateResponse(
        request,
        "auth/lostpwd.html",
        {
            "sent": bool(sent),
            "error": None,
            "email": "",
            "current_user": user,
        },
    )


@router.post("/lostpwd", include_in_schema=False)
def lostpwd_submit(
    request: Request,
    db: DbSession,
    settings: SettingsDep,
    mailer: MailerDep,
    email: Annotated[str, Form()],
) -> object:
    try:
        normalised_email = _validate_email(email)
    except ValueError:
        return templates.TemplateResponse(
            request,
            "auth/lostpwd.html",
            {
                "sent": False,
                "error": "error.auth.invalid_email",
                "email": email,
                "current_user": None,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # Intentionally always returns the same response so an attacker can't
    # enumerate which email addresses are registered.
    request_password_reset(
        db,
        email=normalised_email,
        settings=settings,
        mailer=mailer,
        base_url=str(request.base_url),
    )
    return RedirectResponse(url="/lostpwd?sent=1", status_code=303)


# ---------------------------------------------------------------------------
# Reset password (via tokenised link)
# ---------------------------------------------------------------------------


@router.get("/password/reset/{token}", include_in_schema=False)
def reset_form(request: Request, db: DbSession, token: str) -> object:
    try:
        check_reset_token(db, token)
    except InvalidResetToken as exc:
        # ``exc.reason`` is one of ("unknown", "expired") - see InvalidResetToken.
        # Map straight to a self-contained i18n key so the user-facing message
        # never includes an English ``str(exc)`` fragment.
        error_key = f"error.auth.reset_invalid_{exc.reason}"
        return templates.TemplateResponse(
            request,
            "auth/reset_password.html",
            {
                "token": token,
                "error": error_key,
                "expired": True,
                "min_password_len": MIN_PASSWORD_LEN,
                "current_user": None,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    return templates.TemplateResponse(
        request,
        "auth/reset_password.html",
        {
            "token": token,
            "error": None,
            "expired": False,
            "min_password_len": MIN_PASSWORD_LEN,
            "current_user": None,
        },
    )


@router.post("/password/reset/{token}", include_in_schema=False)
def reset_submit(
    request: Request,
    db: DbSession,
    token: str,
    password: Annotated[str, Form()],
    password_confirm: Annotated[str, Form()],
) -> object:
    def _render_error(
        error_key: str,
        *,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        expired: bool = False,
    ):
        return templates.TemplateResponse(
            request,
            "auth/reset_password.html",
            {
                "token": token,
                "error": error_key,
                "expired": expired,
                "min_password_len": MIN_PASSWORD_LEN,
                "current_user": None,
            },
            status_code=status_code,
        )

    if password != password_confirm:
        return _render_error("error.auth.password_mismatch")
    if len(password) < MIN_PASSWORD_LEN:
        return _render_error("error.auth.password_too_short")

    try:
        confirm_password_reset(db, token_value=token, new_password=password)
    except InvalidResetToken as exc:
        # Mirror the GET handler: render the page with a localised message
        # and ``expired=True`` so the form collapses to the "request a new
        # link" affordance. Surfacing ``str(exc)`` here would leak English
        # into the translated UI; see InvalidResetToken's docstring.
        return _render_error(f"error.auth.reset_invalid_{exc.reason}", expired=True)

    return RedirectResponse(url="/login?registered=0&reset=1", status_code=303)
