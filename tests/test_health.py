from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "version" in payload


def test_home_empty(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "No albums logged yet" in response.text
