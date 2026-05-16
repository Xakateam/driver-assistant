import asyncio
from contextlib import suppress

from sqlalchemy import select

from app.core.config import settings
from app.core.database import SessionLocal
from app.db.models import UserORM
from app.modules.notifications.rules import evaluate_notification_rules
from app.modules.notifications.service import is_notification_window_open


def run_notification_tick() -> dict[str, object]:
    if not is_notification_window_open():
        return {
            "status": "skipped",
            "reason": "quiet_hours",
            "created": 0,
        }

    created: list[dict[str, object]] = []
    with SessionLocal() as db:
        user_ids = db.scalars(select(UserORM.id)).all()
    for user_id in user_ids:
        created.extend(evaluate_notification_rules(user_id))
    return {"status": "completed", "created": len(created)}


def start_notification_scheduler() -> asyncio.Task | None:
    if not settings.NOTIFICATION_SCHEDULER_ENABLED:
        return None
    return asyncio.create_task(_notification_scheduler_loop())


async def stop_notification_scheduler(task: asyncio.Task | None) -> None:
    if task is None:
        return
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task


async def _notification_scheduler_loop() -> None:
    while True:
        run_notification_tick()
        await asyncio.sleep(settings.NOTIFICATION_TICK_INTERVAL_SECONDS)
