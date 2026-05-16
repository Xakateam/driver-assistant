from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_admin_control_room_user_actions_and_panel() -> None:
    panel = client.get("/admin-panel")
    assert panel.status_code == 200
    assert "Сириус · админ-панель" in panel.text

    create_user = client.post(
        "/api/v1/admin/users",
        json={
            "phone": "+79998887766",
            "plate_number": "М777ММ777",
            "vehicle_name": "Demo Car",
        },
    )
    assert create_user.status_code == 200
    user_id = create_user.json()["user"]["id"]

    set_balance = client.post(
        f"/api/v1/admin/users/{user_id}/balance",
        json={"amount": 321},
    )
    assert set_balance.status_code == 200
    assert set_balance.json()["amount"] == 321

    debt = client.post(
        f"/api/v1/admin/users/{user_id}/debts",
        json={
            "road_name": "ЦКАД",
            "amount": 222,
            "entry_point": "А-107",
            "exit_point": "М-7",
            "distance_km": 41,
        },
    )
    assert debt.status_code == 200
    assert debt.json()["status"] == "debt"
    assert debt.json()["road_name"] == "ЦКАД"
    assert debt.json()["entry_point"] == "А-107"
    assert debt.json()["exit_point"] == "М-7"
    assert debt.json()["distance_km"] == 41
    assert debt.json()["notification"]["type"] == "debt_warning"
    assert debt.json()["deliveries"][0]["status"] in {"sent", "skipped", "failed"}

    recalculate = client.post(f"/api/v1/admin/users/{user_id}/ml/recalculate")
    assert recalculate.status_code == 200
    assert recalculate.json()["status"] == "completed"

    detail = client.get(f"/api/v1/admin/users/{user_id}")
    assert detail.status_code == 200
    assert detail.json()["dashboard"]["debts_summary"]["has_overdues"] is True

    scenario = client.post(
        "/api/v1/admin/demo/scenarios/low_balance",
        json={"phone": "+79998887766", "send_push": False},
    )
    assert scenario.status_code == 200
    assert scenario.json()["scenario"] == "low_balance"
