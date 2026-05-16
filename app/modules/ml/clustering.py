from app.modules.ml.features import build_cluster_features
from app.modules.ml.loader import MODEL_VERSION, load_cluster_artifacts


CLUSTER_NAMES = {
    0: "Работяга",
    1: "Дачник",
    2: "Бизнес-путешественник",
    3: "Экономный",
    4: "Премиум",
}

CLUSTER_FEATURE_ORDER = [
    "trip_frequency",
    "avg_check",
    "weekend_share",
    "is_delayed_payment",
]


def predict_segment(user_id: str) -> dict[str, object]:
    features = build_cluster_features(user_id)
    prediction = predict_segment_from_features(features)
    prediction["features"] = features
    return prediction


def predict_segment_from_features(features: dict[str, float]) -> dict[str, object]:
    artifacts = load_cluster_artifacts()
    if artifacts is not None:
        try:
            import numpy as np

            model, scaler = artifacts
            features_array = np.array(
                [[features[name] for name in CLUSTER_FEATURE_ORDER]],
                dtype=float,
            )
            features_scaled = scaler.transform(features_array)
            cluster_id = int(model.predict(features_scaled)[0])
            return _prediction(cluster_id, source="model")
        except Exception as exc:
            fallback = _fallback_cluster(features)
            fallback["source"] = "fallback_after_model_error"
            fallback["runtime_error"] = str(exc)
            return fallback

    return _fallback_cluster(features)


def _prediction(cluster_id: int, *, source: str) -> dict[str, object]:
    return {
        "ml_cluster_id": cluster_id,
        "segment": CLUSTER_NAMES.get(cluster_id, "Неизвестный сегмент"),
        "model_version": MODEL_VERSION,
        "source": source,
    }


def _fallback_cluster(features: dict[str, float]) -> dict[str, object]:
    trip_frequency = features["trip_frequency"]
    avg_check = features["avg_check"]
    weekend_share = features["weekend_share"]
    delayed_share = features["is_delayed_payment"]

    if avg_check >= 420:
        cluster_id = 4
    elif trip_frequency >= 35 and avg_check >= 240:
        cluster_id = 2
    elif weekend_share >= 0.45:
        cluster_id = 1
    elif trip_frequency < 12 or avg_check <= 170 or delayed_share >= 0.35:
        cluster_id = 3
    else:
        cluster_id = 0

    return _prediction(cluster_id, source="fallback")
