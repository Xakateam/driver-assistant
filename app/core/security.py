from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.config import settings


@dataclass(frozen=True)
class CurrentUser:
    id: str
    phone: str


def create_access_token(
    subject: str,
    expires_delta: timedelta | None = None,
) -> dict[str, Any]:
    # Stub until JWT library is added. Keeps the token payload contract explicit.
    expires_at = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"sub": subject, "exp": expires_at.isoformat()}
