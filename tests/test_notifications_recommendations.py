from fastapi.testclient import TestClient

from app.main import app
from app.modules.notifications.service import notification_service
from app.modules.recommendations.service import recommendation_service


client = TestClient(app)


def setup_function() -> None:
    notification_service.reset()
    recommendation_service.reset()


def test_notifications_device_read_action_and_rules() -> None:
    register_response = client.post(
        "/api/v1/notifications/devices/register",
        json={"platform": "android", "fcm_token": "token-1"},
    )
    assert register_response.status_code == 200
    assert register_response.json()["status"] == "registered"

    list_response = client.get("/api/v1/notifications")
    assert list_response.status_code == 200
    notifications = list_response.json()
    assert len(notifications) >= 2

    notification_id = notifications[0]["id"]
    read_response = client.patch(f"/api/v1/notifications/{notification_id}/read")
    assert read_response.status_code == 200
    assert read_response.json()["status"] == "read"

    action_response = client.post(
        f"/api/v1/notifications/{notification_id}/action",
        json={"action": "accepted"},
    )
    assert action_response.status_code == 200
    assert action_response.json()["action"] == "accepted"

    rules_response = client.get("/api/v1/notifications/rules")
    assert rules_response.status_code == 200
    assert rules_response.json()

    rule_response = client.patch(
        "/api/v1/notifications/rules/low_balance_forecast",
        json={"enabled": False},
    )
    assert rule_response.status_code == 200
    assert rule_response.json()["enabled"] is False

    manual_response = client.post(
        "/api/v1/admin/notifications/send",
        json={
            "phone": "+79990000000",
            "type": "admin_message",
            "title": "Тестовое уведомление",
            "body": "Проверяем ручную отправку.",
            "deep_link": "driverassistant://notifications",
            "ignore_quiet_hours": True,
        },
    )
    assert manual_response.status_code == 200
    manual_payload = manual_response.json()
    assert manual_payload["created"] == 1
    assert manual_payload["results"][0]["deliveries"][0]["provider"] in {
        "mock",
        "fcm",
        "none",
    }


def test_notification_not_found_returns_404() -> None:
    response = client.get("/api/v1/notifications/missing")

    assert response.status_code == 404


def test_recommendations_accept_decline_and_not_found() -> None:
    list_response = client.get("/api/v1/recommendations")
    assert list_response.status_code == 200
    recommendations = list_response.json()
    assert len(recommendations) >= 2
    assert all(recommendation["status"] == "pending" for recommendation in recommendations)

    first_id = recommendations[0]["id"]
    accept_response = client.post(f"/api/v1/recommendations/{first_id}/accept")
    assert accept_response.status_code == 200
    assert accept_response.json()["status"] == "accepted"

    second_id = recommendations[1]["id"]
    decline_response = client.post(f"/api/v1/recommendations/{second_id}/decline")
    assert decline_response.status_code == 200
    assert decline_response.json()["status"] == "declined"

    missing_response = client.post("/api/v1/recommendations/missing/accept")
    assert missing_response.status_code == 404

    active_response = client.get("/api/v1/recommendations")
    assert active_response.status_code == 200
    assert all(
        recommendation["status"] == "pending"
        for recommendation in active_response.json()
    )

    history_response = client.get("/api/v1/recommendations?include_decided=true")
    assert history_response.status_code == 200
    statuses = {recommendation["status"] for recommendation in history_response.json()}
    assert {"accepted", "declined"}.issubset(statuses)
