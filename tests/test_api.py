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
        "days_in_processing": 11,
        "documentation_completeness_flag": 1,
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


def test_model_performance_and_explainability_endpoints():
    perf_response = client.get("/api/v1/model/performance")
    assert perf_response.status_code == 200
    perf = perf_response.json()
    assert 0.0 <= perf["roc_auc"] <= 1.0
    assert "top_predictive_features" in perf

    explain_response = client.get("/api/v1/model/explainability")
    assert explain_response.status_code == 200
    explain = explain_response.json()
    assert "shap_values_sample" in explain
    assert "feature_importance" in explain


def test_underwriter_capacity_optimization_endpoint():
    payload = {
        "daily_applications": 400,
        "review_capacity_per_underwriter": 35,
        "current_underwriters": 10,
        "max_underwriters": 20,
        "min_threshold": 0.5,
        "max_threshold": 0.8,
        "step": 0.1,
    }
    response = client.post("/api/v1/optimization/underwriter-capacity", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert 0.5 <= data["recommended_threshold"] <= 0.8
    assert data["recommended_underwriters"] >= 1
    assert len(data["scenarios"]) >= 1
