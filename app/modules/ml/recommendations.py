from app.modules.ml.clustering import predict_segment


def build_recommendation_context(user_id: str) -> dict[str, object]:
    return predict_segment(user_id)
