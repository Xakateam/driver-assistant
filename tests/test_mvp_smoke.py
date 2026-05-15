from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_mvp_demo_flow() -> None:
    assert client.get("/health").status_code == 200

    request_code = client.post(
        "/api/v1/auth/request-code",
        json={"phone": "+79991234567"},
    )
    assert request_code.status_code == 200
    assert request_code.json()["demo_code"] == "1234"

    verify = client.post(
        "/api/v1/auth/verify-code",
        json={"phone": "+79991234567", "code": "1234"},
    )
    assert verify.status_code == 200
    access_token = verify.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    me = client.get("/api/v1/users/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["phone"] == "+79991234567"

    vehicle = client.post(
        "/api/v1/vehicles",
        headers=headers,
        json={"plate_number": "A123BC777", "name": "Kia Rio", "is_primary": True},
    )
    assert vehicle.status_code == 201

    top_up = client.post(
        "/api/v1/balance/top-up",
        headers=headers,
        json={"amount": 1000, "payment_method": "demo_card"},
    )
    assert top_up.status_code == 200
    assert top_up.json()["status"] == "success"

    dashboard = client.get("/api/v1/dashboard", headers=headers)
    assert dashboard.status_code == 200
    assert dashboard.json()["notifications"]
    assert dashboard.json()["recommendations"]
