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

MODEL_REQUIREMENTS = {
    "clustering": {
        "artifacts": ["kmeans", "scaler"],
        "dependencies": ["numpy", "joblib", "sklearn"],
    },
    "spend_prediction": {
        "artifacts": ["spend_predictor"],
        "dependencies": ["pandas", "catboost"],
    },
    "recommendation_ctr": {
        "artifacts": ["ctr"],
        "dependencies": ["pandas", "catboost"],
    },
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
    health = get_model_health()
    return {
        "model_version": MODEL_VERSION,
        "artifacts": get_artifact_status(),
        "dependencies": get_dependency_status(),
        "models": {
            name: bool(report["available"]) for name, report in health.items()
        },
        "health": health,
    }


def get_model_health() -> dict[str, dict[str, object]]:
    cluster_artifacts, cluster_error = _load_cluster_artifacts_result()
    spend_model, spend_error = _load_spend_model_result()
    ctr_model, ctr_error = _load_ctr_model_result()

    return {
        "clustering": _health_report(
            model_name="clustering",
            available=cluster_artifacts is not None,
            load_error=cluster_error,
        ),
        "spend_prediction": _health_report(
            model_name="spend_prediction",
            available=spend_model is not None,
            load_error=spend_error,
        ),
        "recommendation_ctr": _health_report(
            model_name="recommendation_ctr",
            available=ctr_model is not None,
            load_error=ctr_error,
        ),
    }


def load_metadata() -> dict[str, object]:
    metadata_path = Path(get_model_paths()["metadata"])
    if not metadata_path.exists():
        return {}
    return json.loads(metadata_path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_cluster_artifacts() -> tuple[Any, Any] | None:
    return _load_cluster_artifacts_result()[0]


@lru_cache(maxsize=1)
def _load_cluster_artifacts_result() -> tuple[tuple[Any, Any] | None, str | None]:
    paths = get_model_paths()
    kmeans_path = Path(paths["kmeans"])
    scaler_path = Path(paths["scaler"])
    if not kmeans_path.exists() or not scaler_path.exists():
        return None, "Missing kmeans_model.joblib or scaler.joblib"
    try:
        import joblib

        return (joblib.load(kmeans_path), joblib.load(scaler_path)), None
    except Exception as exc:
        return None, _format_exception(exc)


@lru_cache(maxsize=1)
def load_spend_model() -> Any | None:
    return _load_spend_model_result()[0]


@lru_cache(maxsize=1)
def _load_spend_model_result() -> tuple[Any | None, str | None]:
    model_path = Path(get_model_paths()["spend_predictor"])
    if not model_path.exists():
        return None, "Missing spend_predictor.cbm"
    try:
        from catboost import CatBoostRegressor

        model = CatBoostRegressor()
        model.load_model(str(model_path))
        return model, None
    except Exception as exc:
        return None, _format_exception(exc)


@lru_cache(maxsize=1)
def load_ctr_model() -> Any | None:
    return _load_ctr_model_result()[0]


@lru_cache(maxsize=1)
def _load_ctr_model_result() -> tuple[Any | None, str | None]:
    model_path = Path(get_model_paths()["ctr"])
    if not model_path.exists():
        return None, "Missing ctr_model.cbm"
    try:
        from catboost import CatBoostClassifier

        model = CatBoostClassifier()
        model.load_model(str(model_path))
        return model, None
    except Exception as exc:
        return None, _format_exception(exc)


def _dependency_available(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def _health_report(
    *,
    model_name: str,
    available: bool,
    load_error: str | None,
) -> dict[str, object]:
    requirements = MODEL_REQUIREMENTS[model_name]
    artifact_status = get_artifact_status()
    dependency_status = get_dependency_status()
    missing_artifacts = [
        artifact
        for artifact in requirements["artifacts"]
        if not artifact_status[artifact]["exists"]
    ]
    missing_dependencies = [
        dependency
        for dependency in requirements["dependencies"]
        if not dependency_status[dependency]
    ]
    return {
        "available": available,
        "source": "model" if available else "fallback",
        "required_artifacts": requirements["artifacts"],
        "missing_artifacts": missing_artifacts,
        "required_dependencies": requirements["dependencies"],
        "missing_dependencies": missing_dependencies,
        "load_error": load_error,
    }


def _format_exception(exc: Exception) -> str:
    return f"{type(exc).__name__}: {exc}"
