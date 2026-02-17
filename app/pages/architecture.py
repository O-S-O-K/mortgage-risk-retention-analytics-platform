ARCHITECTURE_TITLE = "Architecture Overview"

ARCHITECTURE_CONTENT = """
System flow:
1) Training pipeline (`pipelines/train_model.py`) generates synthetic data, trains two models,
    computes model performance metrics, and saves a reusable model bundle.
2) FastAPI app (`app/main.py` + `app/api/routes.py`) loads model services and exposes APIs.
3) Scoring requests are validated, stored in SQLite, scored, and returned with recommendations.
4) Portfolio summary endpoint aggregates historical prediction records.
5) Explainability endpoint returns SHAP-style contributions, feature importance, and governance metadata.
6) Optimization endpoint simulates threshold and staffing choices for underwriter operations.
7) Report service builds an executive PDF with KPI metrics and a chart.
8) Streamlit dashboard calls API endpoints for interactive demos.

Core components:
- API Layer: request/response contract and endpoint orchestration.
- Services Layer: model scoring, explainability, optimization, and report generation.
- Data Layer: SQLAlchemy models and session management.
- UI Layer: Streamlit dashboard for stakeholders.
""".strip()


def get_architecture_page() -> dict[str, str]:
    return {"title": ARCHITECTURE_TITLE, "content": ARCHITECTURE_CONTENT}
