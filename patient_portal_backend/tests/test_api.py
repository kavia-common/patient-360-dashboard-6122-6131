import os
from fastapi.testclient import TestClient

# Ensure no real DB requirement for tests
os.environ.pop("BACKEND_DB_URL", None)

from src.api.main import app  # noqa: E402

client = TestClient(app)


def get_auth_header():
    # Login to get a token
    resp = client.post("/auth/login", data={"username": "tester", "password": "secret"})
    assert resp.status_code == 200, resp.text
    token = resp.json()["token"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_health_check():
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["message"] == "Healthy"
    assert "db_connected" in data


def test_auth_status_anonymous():
    res = client.get("/auth/status")
    assert res.status_code == 200
    data = res.json()
    assert data["authenticated"] is False


def test_auth_login_and_status():
    headers = get_auth_header()
    res = client.get("/auth/status", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["authenticated"] is True
    assert data["username"] == "tester"


def test_patients_crud_flow():
    headers = get_auth_header()

    # List (should have demo data)
    res = client.get("/patients", headers=headers)
    assert res.status_code == 200
    patients = res.json()
    assert isinstance(patients, list)
    base_count = len(patients)

    # Create
    payload = {
        "first_name": "Grace",
        "last_name": "Hopper",
        "email": "grace@example.com",
        "age": 45,
        "conditions": ["thyroid"],
    }
    res = client.post("/patients", json=payload, headers=headers)
    assert res.status_code == 201, res.text
    created = res.json()
    assert created["email"] == "grace@example.com"
    new_id = created["id"]

    # Get
    res = client.get(f"/patients/{new_id}", headers=headers)
    assert res.status_code == 200
    fetched = res.json()
    assert fetched["id"] == new_id

    # Update
    res = client.put(f"/patients/{new_id}", json={"age": 46}, headers=headers)
    assert res.status_code == 200
    updated = res.json()
    assert updated["age"] == 46

    # Delete
    res = client.delete(f"/patients/{new_id}", headers=headers)
    assert res.status_code == 204

    # List to verify count restored
    res = client.get("/patients", headers=headers)
    assert res.status_code == 200
    assert len(res.json()) == base_count


def test_chatbot_send():
    headers = get_auth_header()
    res = client.post("/chatbot/send", json={"message": "Hello bot"}, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "reply" in data
    assert "model" in data
    assert "Hello bot" in data["reply"]
