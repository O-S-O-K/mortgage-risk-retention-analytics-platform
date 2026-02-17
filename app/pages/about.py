ABOUT_TITLE = "About This Platform"

ABOUT_CONTENT = """
Mortgage Risk & Retention Analytics Platform

Mortgage lenders face revenue leakage due to loan fallout and customer attrition.
This platform addresses that by predicting:
- Probability of loan fallout
- Customer refinance risk
- Portfolio risk segmentation

This project demonstrates an end-to-end analytics product for mortgage portfolios,
combining model training, API scoring, operational persistence, and executive reporting.

What it includes:
- SQL-backed persistence for scored loan scenarios.
- Machine learning models for default risk and retention probability.
- FastAPI endpoints for scoring, summary metrics, and PDF report generation.
- Streamlit dashboard for business-facing interaction and demos.

Why it matters:
- Early intervention workflows for at-risk loans.
- Targeted retention offers for refinance-risk borrowers.
- Improved underwriting resource allocation.
- Executive-ready reporting for leadership teams.
""".strip()


def get_about_page() -> dict[str, str]:
    return {"title": ABOUT_TITLE, "content": ABOUT_CONTENT}
