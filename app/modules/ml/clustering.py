from app.modules.ml.features import build_user_features


def predict_segment(user_id: str) -> dict[str, object]:
    features = build_user_features(user_id)
    if features["trip_count"] >= 20:
        segment = "heavy_user"
    elif features["balance"] < features["avg_check"]:
        segment = "low_balance_risk"
    else:
        segment = "commuter"
    return {"segment": segment, "features": features, "model_version": "demo"}
