"""Application settings, loaded from environment variables / .env."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """
    Runtime configuration.

    Values are read first from the environment, then from a local `.env`
    file (handy for development), then from these defaults.

    The only setting that must be set in production is `database_url`.
    """

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Core --------------------------------------------------------------
    database_url: str = Field(
        default="postgresql+psycopg://predictr:predictr@localhost:5432/predictr",
        description=(
            "SQLAlchemy connection string. The default matches the local "
            "docker-compose Postgres service; production overrides this via "
            "the DATABASE_URL environment variable."
        ),
    )
    debug: bool = Field(default=False, description="Toggle debug mode and SQL echo.")
    sql_echo: bool = Field(default=False, description="If true, SQLAlchemy logs every statement.")
    log_level: LogLevel = Field(
        default="INFO",
        description=(
            "Python logging level for the application's own loggers (the "
            "``app.*`` hierarchy). Applied to the root logger at startup by "
            "``app.main._configure_logging``. Uvicorn's own access / error "
            "loggers are left at their defaults so request lines keep their "
            "familiar format. Accepts case-insensitive input (``debug`` and "
            "``DEBUG`` both work)."
        ),
    )

    @field_validator("log_level", mode="before")
    @classmethod
    def _uppercase_log_level(cls, value: object) -> object:
        """Accept lowercase / mixed-case env var values."""
        if isinstance(value, str):
            return value.upper()
        return value

    # --- Mail -------------------------------------------------------------
    mail_host: str = Field(
        default="",
        description=(
            "SMTP server hostname. If empty, mail goes to the in-memory "
            "backend (logged + accessible from tests) instead of being sent."
        ),
    )
    mail_port: int = 25
    mail_username: str = ""
    mail_password: str = ""
    mail_use_tls: bool = False
    mail_sender: str = "noreply@predictr.local"

    # --- Auth / sessions --------------------------------------------------
    session_secret: str = Field(
        default="change-me-in-production",
        description="Secret used to sign session cookies. MUST be overridden in prod.",
    )
    session_cookie_name: str = "predictr_session"
    secure_cookies: bool = Field(
        default=False,
        description=(
            "If true, every cookie the app writes (session, language, "
            "timezone) carries the ``Secure`` attribute and is therefore "
            "only sent over HTTPS. MUST be true in production behind a TLS "
            "terminator; leave false in local development where the app "
            "speaks plain HTTP. The default is false so dev just works; "
            "shipping it as false to production is the trade-off that "
            "warrants the explicit operator flag."
        ),
    )
    session_max_age_days: int = Field(
        default=7,
        description=(
            "Maximum lifetime of a 'remember me' session cookie, in days. "
            "Without 'remember me' the cookie is browser-session-scoped but "
            "the underlying signed token still expires after this many days."
        ),
    )
    password_reset_ttl_hours: int = Field(
        default=24,
        description="How long a password reset token stays valid, in hours.",
    )
    base_url: str = Field(
        default="http://localhost:8000",
        description=(
            "Public base URL of the application. Used to render absolute "
            "links in outbound emails (e.g. password reset)."
        ),
    )

    # --- Localisation -----------------------------------------------------
    default_language: str = Field(
        default="de",
        description=(
            "ISO 639-1 code used for anonymous visitors and as the implicit "
            "preference for newly-registered users. Must be one of the codes "
            "in ``app.i18n.SUPPORTED_LANGUAGES``; unknown values fall back "
            "to German at render time."
        ),
    )
    default_timezone: str = Field(
        default="Europe/Berlin",
        description=(
            "IANA timezone name used for anonymous visitors and as the "
            "implicit preference for newly-registered users. Stored "
            "timestamps remain UTC; this only affects display. Unknown "
            "names fall back to UTC at render time."
        ),
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings accessor. Use this everywhere - never instantiate Settings directly."""
    return Settings()
