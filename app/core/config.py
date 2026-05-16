import os
from dataclasses import dataclass, field
from functools import lru_cache


def _getenv_list(key: str, default: list[str]) -> list[str]:
    value = os.getenv(key)
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


def _getenv_optional(key: str) -> str | None:
    value = os.getenv(key)
    if not value:
        return None
    return value.strip() or None


def _getenv_bool(key: str, default: bool) -> bool:
    value = os.getenv(key)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    PROJECT_NAME: str = field(
        default_factory=lambda: os.getenv("PROJECT_NAME", "Driver Assistant API")
    )
    VERSION: str = field(default_factory=lambda: os.getenv("VERSION", "alpha"))
    API_V1_PREFIX: str = field(
        default_factory=lambda: os.getenv("API_V1_PREFIX", "/api/v1")
    )

    DATABASE_URL: str = field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg://driver:driver@localhost:5433/driver_assistant",
        )
    )
    JWT_SECRET_KEY: str = field(
        default_factory=lambda: os.getenv("JWT_SECRET_KEY", "change-me")
    )
    JWT_ALGORITHM: str = field(default_factory=lambda: os.getenv("JWT_ALGORITHM", "HS256"))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = field(
        default_factory=lambda: int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    )

    BACKEND_CORS_ORIGINS: list[str] = field(
        default_factory=lambda: _getenv_list("BACKEND_CORS_ORIGINS", ["*"])
    )
    ADMIN_API_KEY: str | None = field(
        default_factory=lambda: _getenv_optional("ADMIN_API_KEY")
    )
    SENTRY_DSN: str | None = field(default_factory=lambda: _getenv_optional("SENTRY_DSN"))
    SENTRY_ENVIRONMENT: str = field(
        default_factory=lambda: os.getenv("SENTRY_ENVIRONMENT", "local")
    )
    SENTRY_TRACES_SAMPLE_RATE: float = field(
        default_factory=lambda: float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.0"))
    )
    FIREBASE_PROJECT_ID: str | None = field(
        default_factory=lambda: _getenv_optional("FIREBASE_PROJECT_ID")
    )
    FIREBASE_SERVICE_ACCOUNT_PATH: str | None = field(
        default_factory=lambda: _getenv_optional("FIREBASE_SERVICE_ACCOUNT_PATH")
    )
    FIREBASE_SERVICE_ACCOUNT_JSON: str | None = field(
        default_factory=lambda: _getenv_optional("FIREBASE_SERVICE_ACCOUNT_JSON")
    )
    NOTIFICATION_SCHEDULER_ENABLED: bool = field(
        default_factory=lambda: _getenv_bool("NOTIFICATION_SCHEDULER_ENABLED", True)
    )
    NOTIFICATION_TICK_INTERVAL_SECONDS: int = field(
        default_factory=lambda: int(os.getenv("NOTIFICATION_TICK_INTERVAL_SECONDS", "1800"))
    )
    NOTIFICATION_ALLOWED_START_HOUR: int = field(
        default_factory=lambda: int(os.getenv("NOTIFICATION_ALLOWED_START_HOUR", "9"))
    )
    NOTIFICATION_ALLOWED_END_HOUR: int = field(
        default_factory=lambda: int(os.getenv("NOTIFICATION_ALLOWED_END_HOUR", "21"))
    )
    NOTIFICATION_TIMEZONE: str = field(
        default_factory=lambda: os.getenv("NOTIFICATION_TIMEZONE", "Europe/Moscow")
    )
    NOTIFICATION_DEDUP_WINDOW_MINUTES: int = field(
        default_factory=lambda: int(os.getenv("NOTIFICATION_DEDUP_WINDOW_MINUTES", "180"))
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
