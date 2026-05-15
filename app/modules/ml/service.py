from sqlalchemy import select

from app.core.database import SessionLocal
from app.db.models import UserORM
from app.modules.ml.clustering import predict_segment


def recalculate_user(user_id: str) -> dict[str, object]:
    with SessionLocal() as db:
        user = db.get(UserORM, user_id)
        if not user:
            return {"status": "not_found"}
        prediction = predict_segment(user.id)
        user.segment = str(prediction["segment"])
        db.commit()
        return {
            "status": "completed",
            "user_id": user.id,
            "segment": user.segment,
            "model_version": "demo",
        }


def recalculate_all() -> dict[str, object]:
    with SessionLocal() as db:
        users = db.scalars(select(UserORM)).all()
        for user in users:
            prediction = predict_segment(user.id)
            user.segment = str(prediction["segment"])
        db.commit()
        return {
            "status": "completed",
            "processed_users": len(users),
            "model_version": "demo",
        }


def get_ml_status() -> dict[str, object]:
    with SessionLocal() as db:
        users_count = len(db.scalars(select(UserORM)).all())
        segmented_count = len(
            db.scalars(select(UserORM).where(UserORM.segment.is_not(None))).all()
        )
    return {
        "status": "ready",
        "model_version": "demo",
        "users_with_segments": segmented_count,
        "users_total": users_count,
    }
