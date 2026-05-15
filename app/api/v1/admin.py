from fastapi import APIRouter

from app.core.database import SessionLocal, seed_demo_data as seed_db_demo_data
from app.modules.ml import service as ml_service
from app.modules.notifications.scheduler import run_notification_tick
from app.modules.notifications.service import notification_service
from app.modules.recommendations.service import recommendation_service

router = APIRouter()


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
