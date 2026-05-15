from app.core.store import store
from app.modules.ml.clustering import predict_segment


def recalculate_user(user_id: str) -> dict[str, object]:
    user = store.get_user(user_id)
    if not user:
        return {"status": "not_found"}
    prediction = predict_segment(user.id)
    user.segment = str(prediction["segment"])
    return {
        "status": "completed",
        "user_id": user.id,
        "segment": user.segment,
        "model_version": "demo",
    }


def recalculate_all() -> dict[str, object]:
    return {
        "status": "completed",
        "processed_users": len(store.users),
        "model_version": "demo",
    }


def get_ml_status() -> dict[str, object]:
    return {
        "status": "ready",
        "model_version": "demo",
        "users_with_segments": len(store.users),
    }
