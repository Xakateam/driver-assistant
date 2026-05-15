from pathlib import Path


ML_MODELS_DIR = Path("ml_models")


def get_model_paths() -> dict[str, str]:
    return {
        "clustering": str(ML_MODELS_DIR / "clustering.joblib"),
        "recommender": str(ML_MODELS_DIR / "recommender.joblib"),
        "metadata": str(ML_MODELS_DIR / "metadata.json"),
    }
