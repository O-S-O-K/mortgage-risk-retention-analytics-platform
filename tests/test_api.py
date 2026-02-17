from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_score_endpoint():
    payload = {
        "credit_score": 710,
        "ltv": 78.5,
        "dti": 31.2,
        "income": 125000,
        "loan_amount": 320000,
        "interest_rate": 6.1,
        "tenure_years": 30,
    }
    response = client.post("/api/v1/score", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert 0.0 <= data["risk_score"] <= 1.0
    assert 0.0 <= data["retention_score"] <= 1.0
