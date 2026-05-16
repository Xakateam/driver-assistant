from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_ml_status_reports_artifacts_and_fallback_runtime() -> None:
    response = client.get("/api/v1/admin/ml/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] in {"ready", "fallback"}
    assert payload["model_version"] == "ml_moscow_transport@4779dba"
    assert payload["runtime"]["artifacts"]["kmeans"]["exists"] is True
    assert payload["runtime"]["artifacts"]["spend_predictor"]["exists"] is True
    assert payload["runtime"]["artifacts"]["ctr"]["exists"] is True


def test_ml_recalculate_me_persists_profile_outputs() -> None:
    recalculate = client.post("/api/v1/ml/recalculate-me")

    assert recalculate.status_code == 200
    payload = recalculate.json()
    assert payload["status"] == "completed"
    assert isinstance(payload["ml_cluster_id"], int)
    assert payload["ml_cluster_name"]
    assert payload["predicted_spend_next_month"] >= 0
    assert payload["favorite_route_name"]
    assert "clustering" in payload["features"]
    assert "spend_prediction" in payload["features"]

    me = client.get("/api/v1/users/me")
    assert me.status_code == 200
    assert me.json()["ml_cluster_id"] == payload["ml_cluster_id"]


def test_recommendations_include_ctr_context() -> None:
    response = client.get("/api/v1/recommendations?include_decided=true")

    assert response.status_code == 200
    recommendations = response.json()
    assert recommendations
    assert 0 <= recommendations[0]["predicted_ctr"] <= 1
    assert recommendations[0]["category_id"] in {1, 2, 3, 4, 5}
    assert recommendations[0]["metadata"]["ctr_source"]
