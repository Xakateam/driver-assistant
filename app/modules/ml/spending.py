from app.modules.ml.features import build_spend_features
from app.modules.ml.loader import MODEL_VERSION, load_spend_model


SPEND_FEATURE_ORDER = ["trips_count", "total_spent", "ml_cluster_id"]


def predict_next_month_spend(
    user_id: str,
    ml_cluster_id: int | None,
) -> dict[str, object]:
    features = build_spend_features(user_id, ml_cluster_id)
    model = load_spend_model()
    if model is not None:
        try:
            import pandas as pd

            prediction = float(model.predict(pd.DataFrame([features]))[0])
            return {
                "predicted_spend_next_month": round(max(prediction, 0), 2),
                "features": features,
                "model_version": MODEL_VERSION,
                "source": "model",
            }
        except Exception as exc:
            fallback = _fallback_spend(features)
            fallback["source"] = "fallback_after_model_error"
            fallback["runtime_error"] = str(exc)
            return fallback

    return _fallback_spend(features)


def _fallback_spend(features: dict[str, float]) -> dict[str, object]:
    trips_count = features["trips_count"]
    total_spent = features["total_spent"]
    cluster_id = int(features["ml_cluster_id"])

    if trips_count == 0:
        predicted = 0.0
    else:
        cluster_multiplier = {
            0: 1.05,
            1: 0.9,
            2: 1.18,
            3: 0.8,
            4: 1.25,
        }.get(cluster_id, 1.0)
        predicted = total_spent * cluster_multiplier

    return {
        "predicted_spend_next_month": round(max(predicted, 0), 2),
        "features": features,
        "model_version": MODEL_VERSION,
        "source": "fallback",
    }
