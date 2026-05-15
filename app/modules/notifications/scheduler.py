from sqlalchemy import select

from app.core.database import SessionLocal
from app.db.models import UserORM
from app.modules.notifications.rules import evaluate_notification_rules


def run_notification_tick() -> dict[str, object]:
    created: list[dict[str, object]] = []
    with SessionLocal() as db:
        user_ids = db.scalars(select(UserORM.id)).all()
    for user_id in user_ids:
        created.extend(evaluate_notification_rules(user_id))
    return {"status": "completed", "created": len(created)}
