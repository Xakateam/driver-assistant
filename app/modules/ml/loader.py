import importlib.util
import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any


ML_MODELS_DIR = Path(os.getenv("ML_MODELS_DIR", "ml_models"))
MODEL_VERSION = "ml_moscow_transport@4779dba"

MODEL_FILES = {
    "kmeans": "kmeans_model.joblib",
    "scaler": "scaler.joblib",
    "spend_predictor": "spend_predictor.cbm",
    "ctr": "ctr_model.cbm",
    "metadata": "metadata.json",
}


def get_model_paths() -> dict[str, str]:
    return {name: str(ML_MODELS_DIR / path) for name, path in MODEL_FILES.items()}


def get_artifact_status() -> dict[str, dict[str, object]]:
    status = {}
    for name, path in get_model_paths().items():
        artifact_path = Path(path)
        status[name] = {
            "path": str(artifact_path),
            "exists": artifact_path.exists(),
            "size_bytes": artifact_path.stat().st_size if artifact_path.exists() else 0,
        }
    return status


def get_dependency_status() -> dict[str, bool]:
    return {
        "numpy": _dependency_available("numpy"),
        "pandas": _dependency_available("pandas"),
        "joblib": _dependency_available("joblib"),
        "sklearn": _dependency_available("sklearn"),
        "catboost": _dependency_available("catboost"),
    }


def get_runtime_status() -> dict[str, object]:
    return {
        "model_version": MODEL_VERSION,
        "artifacts": get_artifact_status(),
        "dependencies": get_dependency_status(),
        "models": {
            "clustering": load_cluster_artifacts() is not None,
            "spend_prediction": load_spend_model() is not None,
            "recommendation_ctr": load_ctr_model() is not None,
        },
    }


def load_metadata() -> dict[str, object]:
    metadata_path = Path(get_model_paths()["metadata"])
    if not metadata_path.exists():
        return {}
    return json.loads(metadata_path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_cluster_artifacts() -> tuple[Any, Any] | None:
    paths = get_model_paths()
    kmeans_path = Path(paths["kmeans"])
    scaler_path = Path(paths["scaler"])
    if not kmeans_path.exists() or not scaler_path.exists():
        return None
    try:
        import joblib

        return joblib.load(kmeans_path), joblib.load(scaler_path)
    except Exception:
        return None


@lru_cache(maxsize=1)
def load_spend_model() -> Any | None:
    model_path = Path(get_model_paths()["spend_predictor"])
    if not model_path.exists():
        return None
    try:
        from catboost import CatBoostRegressor

        model = CatBoostRegressor()
        model.load_model(str(model_path))
        return model
    except Exception:
        return None


@lru_cache(maxsize=1)
def load_ctr_model() -> Any | None:
    model_path = Path(get_model_paths()["ctr"])
    if not model_path.exists():
        return None
    try:
        from catboost import CatBoostClassifier

        model = CatBoostClassifier()
        model.load_model(str(model_path))
        return model
    except Exception:
        return None


def _dependency_available(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None
