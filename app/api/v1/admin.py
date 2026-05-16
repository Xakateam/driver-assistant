import os
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.api.v1.schemas import Metadata
from app.core.config import settings
from app.core.database import SessionLocal, seed_demo_data as seed_db_demo_data
from app.db.models import UserORM
from app.modules.ml import service as ml_service
from app.modules.notifications.scheduler import run_notification_tick
from app.modules.notifications.service import notification_service
from app.modules.recommendations.service import recommendation_service


class AdminNotificationSendIn(BaseModel):
    user_id: str | None = None
    phone: str | None = None
    broadcast: bool = False
    type: str = Field(default="admin_message")
    title: str = Field(min_length=1)
    body: str = Field(min_length=1)
    deep_link: str | None = None
    metadata: Metadata = Field(default_factory=dict)
    ignore_quiet_hours: bool = False


async def require_admin_api_key(
    x_admin_api_key: Annotated[str | None, Header(alias="X-Admin-API-Key")] = None,
) -> None:
    expected_key = _expected_admin_api_key()
    if expected_key is None:
        return
    if x_admin_api_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin API key",
        )


def _expected_admin_api_key() -> str | None:
    return os.getenv("ADMIN_API_KEY") or settings.ADMIN_API_KEY


router = APIRouter(dependencies=[Depends(require_admin_api_key)])


@router.get("/status")
async def admin_status() -> dict[str, str]:
    return {"status": "ready"}


@router.post("/ml/recalculate-all")
async def recalculate_all() -> dict[str, object]:
    return ml_service.recalculate_all()


@router.get("/ml/status")
async def ml_status() -> dict[str, object]:
    return ml_service.get_ml_status()


@router.post("/seed")
async def seed_demo_data() -> dict[str, object]:
    notification_service.reset()
    recommendation_service.reset()
    with SessionLocal() as db:
        user = seed_db_demo_data(db)
    return {
        "status": "seeded",
        "demo_user_id": user.id,
        "demo_phone": user.phone,
    }


@router.post("/notifications/tick")
async def notification_tick() -> dict[str, object]:
    return run_notification_tick()


@router.post("/notifications/send")
async def send_notification(payload: AdminNotificationSendIn) -> dict[str, object]:
    user_ids = _resolve_notification_targets(payload)
    if not user_ids:
        raise HTTPException(status_code=404, detail="Notification target not found")

    results = [
        notification_service.dispatch_notification(
            user_id=user_id,
            type=payload.type,
            title=payload.title,
            body=payload.body,
            deep_link=payload.deep_link,
            metadata=payload.metadata,
            ignore_quiet_hours=payload.ignore_quiet_hours,
        )
        for user_id in user_ids
    ]
    return {
        "status": "completed",
        "target_count": len(user_ids),
        "created": sum(1 for result in results if result["notification"] is not None),
        "results": results,
    }


def _resolve_notification_targets(payload: AdminNotificationSendIn) -> list[str]:
    with SessionLocal() as db:
        if payload.broadcast:
            return list(db.scalars(select(UserORM.id)).all())
        if payload.user_id:
            user = db.get(UserORM, payload.user_id)
            return [user.id] if user else []
        if payload.phone:
            user = db.scalar(select(UserORM).where(UserORM.phone == payload.phone))
            return [user.id] if user else []
    raise HTTPException(
        status_code=400,
        detail="Set user_id, phone, or broadcast=true",
    )
