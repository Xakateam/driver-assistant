from app.modules.ml.features import build_recommendation_features
from app.modules.ml.loader import MODEL_VERSION, load_ctr_model


CATEGORY_BY_RECOMMENDATION_TYPE = {
    "debt_warning": 1,
    "debt_payment": 1,
    "subscription_offer": 2,
    "balance_topup": 3,
    "autopay_offer": 3,
    "offpeak_departure": 4,
    "weekend_discount": 4,
    "recommendation_available": 5,
}


def get_recommendation_category(recommendation_type: str) -> int:
    return CATEGORY_BY_RECOMMENDATION_TYPE.get(recommendation_type, 5)


def predict_recommendation_ctr(
    user_id: str,
    category_id: int,
    *,
    ml_cluster_id: int | None = None,
    predicted_spend_next_month: float | None = None,
) -> dict[str, object]:
    features = build_recommendation_features(
        user_id,
        category_id,
        ml_cluster_id=ml_cluster_id,
        predicted_spend_next_month=predicted_spend_next_month,
    )
    model = load_ctr_model()
    if model is not None:
        try:
            import pandas as pd

            probability = float(model.predict_proba(pd.DataFrame([features]))[0][1])
            return {
                "predicted_ctr": round(_clamp_probability(probability), 4),
                "features": features,
                "model_version": MODEL_VERSION,
                "source": "model",
            }
        except Exception as exc:
            fallback = _fallback_ctr(features)
            fallback["source"] = "fallback_after_model_error"
            fallback["runtime_error"] = str(exc)
            return fallback

    return _fallback_ctr(features)


def _fallback_ctr(features: dict[str, float]) -> dict[str, object]:
    balance = features["current_balance"]
    debt_amount = features["debt_amount"]
    predicted_spend = features["predicted_spend_next_month"]
    category_id = int(features["category_id"])

    if category_id == 1:
        probability = 0.78 if debt_amount > 0 else 0.12
    elif category_id == 2:
        probability = 0.58 if predicted_spend >= 2500 else 0.28
    elif category_id == 3:
        risk_threshold = max(predicted_spend * 0.2, 500)
        probability = 0.66 if balance < risk_threshold else 0.32
    elif category_id == 4:
        probability = 0.46 if predicted_spend >= 1500 else 0.26
    else:
        probability = 0.24

    return {
        "predicted_ctr": round(_clamp_probability(probability), 4),
        "features": features,
        "model_version": MODEL_VERSION,
        "source": "fallback",
    }


def _clamp_probability(value: float) -> float:
    return max(0.0, min(1.0, value))
