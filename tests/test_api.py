from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analyze_endpoint() -> None:
    response = client.post(
        "/api/v1/analyze",
        json={
            "ticker": "AAPL",
            "question": "Should I watch this stock for upcoming catalysts?",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["ticker"] == "AAPL"
    assert payload["tool_calls"]
    assert payload["retrieved_context"]
