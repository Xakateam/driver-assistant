from datetime import UTC, datetime

from sqlalchemy import select

from app.core.database import SessionLocal
from app.db.models import UserORM
from app.modules.ml.clustering import predict_segment
from app.modules.ml.features import get_favorite_route_name
from app.modules.ml.loader import MODEL_VERSION, get_runtime_status
from app.modules.ml.spending import predict_next_month_spend


def recalculate_user(user_id: str) -> dict[str, object]:
    with SessionLocal() as db:
        user = db.get(UserORM, user_id)
        if not user:
            return {"status": "not_found"}

    segment_prediction = predict_segment(user_id)
    spend_prediction = predict_next_month_spend(
        user_id,
        _nullable_int(segment_prediction.get("ml_cluster_id")),
    )

    with SessionLocal() as db:
        user = db.get(UserORM, user_id)
        if not user:
            return {"status": "not_found"}
        _apply_predictions(db, user, segment_prediction, spend_prediction)
        db.commit()
        db.refresh(user)
        return _recalculate_result(user, segment_prediction, spend_prediction)


def recalculate_all() -> dict[str, object]:
    with SessionLocal() as db:
        user_ids = list(db.scalars(select(UserORM.id)).all())

    results = [recalculate_user(user_id) for user_id in user_ids]
    processed_count = sum(1 for result in results if result["status"] == "completed")
    return {
        "status": "completed",
        "processed_users": processed_count,
        "users_total": len(user_ids),
        "model_version": MODEL_VERSION,
        "results": results,
    }


def get_ml_status() -> dict[str, object]:
    runtime_status = get_runtime_status()
    with SessionLocal() as db:
        users_count = len(db.scalars(select(UserORM)).all())
        segmented_count = len(
            db.scalars(select(UserORM).where(UserORM.ml_cluster_id.is_not(None))).all()
        )
        forecasted_count = len(
            db.scalars(
                select(UserORM).where(UserORM.predicted_spend_next_month.is_not(None))
            ).all()
        )

    available_models = runtime_status["models"]
    return {
        "status": "ready" if any(available_models.values()) else "fallback",
        "model_version": runtime_status["model_version"],
        "users_with_segments": segmented_count,
        "users_with_forecasts": forecasted_count,
        "users_total": users_count,
        "runtime": runtime_status,
    }


def _apply_predictions(
    db,
    user: UserORM,
    segment_prediction: dict[str, object],
    spend_prediction: dict[str, object],
) -> None:
    cluster_id = _nullable_int(segment_prediction.get("ml_cluster_id"))
    segment_name = str(segment_prediction["segment"])

    user.segment = segment_name
    user.ml_cluster_id = cluster_id
    user.ml_cluster_name = segment_name
    user.predicted_spend_next_month = float(
        spend_prediction["predicted_spend_next_month"]
    )
    user.favorite_route_name = get_favorite_route_name(user.id, db)
    user.ml_model_version = MODEL_VERSION
    user.ml_updated_at = datetime.now(UTC)


def _recalculate_result(
    user: UserORM,
    segment_prediction: dict[str, object],
    spend_prediction: dict[str, object],
) -> dict[str, object]:
    return {
        "status": "completed",
        "user_id": user.id,
        "segment": user.segment,
        "ml_cluster_id": user.ml_cluster_id,
        "ml_cluster_name": user.ml_cluster_name,
        "predicted_spend_next_month": user.predicted_spend_next_month,
        "favorite_route_name": user.favorite_route_name,
        "model_version": user.ml_model_version,
        "ml_updated_at": user.ml_updated_at.isoformat() if user.ml_updated_at else None,
        "sources": {
            "clustering": segment_prediction["source"],
            "spend_prediction": spend_prediction["source"],
        },
        "features": {
            "clustering": segment_prediction["features"],
            "spend_prediction": spend_prediction["features"],
        },
    }


def _nullable_int(value: object) -> int | None:
    if value is None:
        return None
    return int(value)
