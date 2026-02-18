from __future__ import annotations

import os

import requests
import streamlit as st
from sqlalchemy import func

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.loan import LoanScenario
from app.models.prediction import PredictionResult
from app.schemas.loan import LoanRequest
from app.services.model_service import ModelService
from app.services.report_service import ReportService

API_BASE = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
USE_LOCAL_SERVICES = os.getenv("STREAMLIT_LOCAL_SERVICES", "0") == "1" or (
    os.getenv("SPACE_ID") is not None and not os.getenv("API_BASE_URL")
)


@st.cache_resource
def get_local_services() -> tuple[ModelService, ReportService]:
    Base.metadata.create_all(bind=engine)
    return ModelService(), ReportService()

st.set_page_config(page_title="Mortgage Risk Dashboard", layout="wide")
st.title("Mortgage Risk & Retention Analytics")
if USE_LOCAL_SERVICES:
    st.caption("Mode: Streamlit local services (HF-only)")
    st.success("Backend mode: in-process services online")
    st.info(
        "HF free-tier note: local SQLite records and generated report files may reset when the Space rebuilds or restarts."
    )
    local_model_service, local_report_service = get_local_services()
else:
    st.caption(f"Mode: FastAPI backend ({API_BASE})")
    try:
        health_resp = requests.get(f"{API_BASE}/health", timeout=3)
        if health_resp.ok:
            st.success("API connection: online")
        else:
            st.warning("API connection: unhealthy response")
    except requests.RequestException:
        st.warning("API connection: offline")

st.subheader("Portfolio Summary")
if USE_LOCAL_SERVICES:
    db = SessionLocal()
    try:
        total_scored = db.query(func.count(PredictionResult.id)).scalar() or 0
        avg_risk = db.query(func.avg(PredictionResult.risk_score)).scalar() or 0.0
        avg_retention = db.query(func.avg(PredictionResult.retention_score)).scalar() or 0.0
        high_risk = (
            db.query(func.count(PredictionResult.id))
            .filter(PredictionResult.risk_score >= 0.65)
            .scalar()
            or 0
        )
        low_retention = (
            db.query(func.count(PredictionResult.id))
            .filter(PredictionResult.retention_score < 0.45)
            .scalar()
            or 0
        )
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Scored Loans", int(total_scored))
        c2.metric("Avg Risk", f"{float(avg_risk):.2%}")
        c3.metric("Avg Retention", f"{float(avg_retention):.2%}")
        c4.metric("High Risk", int(high_risk))
        c5.metric("Low Retention", int(low_retention))
    finally:
        db.close()
else:
    try:
        summary_resp = requests.get(f"{API_BASE}/api/v1/portfolio/summary", timeout=5)
        if summary_resp.ok:
            summary = summary_resp.json()
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Scored Loans", summary["total_scored"])
            c2.metric("Avg Risk", f"{summary['avg_risk_score']:.2%}")
            c3.metric("Avg Retention", f"{summary['avg_retention_score']:.2%}")
            c4.metric("High Risk", summary["high_risk_count"])
            c5.metric("Low Retention", summary["low_retention_count"])
        else:
            st.warning("Could not load portfolio summary.")
    except requests.RequestException:
        st.error(f"FastAPI service not reachable. Current API_BASE_URL={API_BASE}")

st.divider()
st.subheader("Model Scoring Interface")

with st.form("score_form"):
    c1, c2, c3 = st.columns(3)
    credit_score = c1.number_input("Credit Score", min_value=300, max_value=850, value=700)
    ltv = c1.number_input("LTV (%)", min_value=0.0, max_value=150.0, value=80.0)
    dti = c1.number_input("DTI (%)", min_value=0.0, max_value=100.0, value=32.0)
    days_in_processing = c1.number_input("Days in Processing", min_value=0, max_value=120, value=12)
    documentation_completeness_flag = c1.selectbox(
        "Documentation Complete",
        options=[1, 0],
        format_func=lambda x: "Yes" if x == 1 else "No",
    )

    income = c2.number_input("Income ($)", min_value=1000.0, value=120000.0, step=5000.0)
    loan_amount = c2.number_input("Loan Amount ($)", min_value=1000.0, value=350000.0, step=5000.0)
    interest_rate = c2.number_input("Interest Rate (%)", min_value=0.1, max_value=30.0, value=6.25)

    tenure_years = c3.number_input("Tenure (Years)", min_value=1, max_value=40, value=30)

    submitted = st.form_submit_button("Score Loan")

if submitted:
    payload = {
        "credit_score": int(credit_score),
        "ltv": float(ltv),
        "dti": float(dti),
        "days_in_processing": int(days_in_processing),
        "documentation_completeness_flag": int(documentation_completeness_flag),
        "income": float(income),
        "loan_amount": float(loan_amount),
        "interest_rate": float(interest_rate),
        "tenure_years": int(tenure_years),
    }
    if USE_LOCAL_SERVICES:
        db = SessionLocal()
        try:
            loan_request = LoanRequest(**payload)
            loan_row = LoanScenario(
                credit_score=loan_request.credit_score,
                ltv=loan_request.ltv,
                dti=loan_request.dti,
                income=loan_request.income,
                loan_amount=loan_request.loan_amount,
                interest_rate=loan_request.interest_rate,
                tenure_years=loan_request.tenure_years,
            )
            db.add(loan_row)
            db.flush()

            scored = local_model_service.score(loan_request)

            pred_row = PredictionResult(
                loan_id=loan_row.id,
                risk_score=scored.risk_score,
                retention_score=scored.retention_score,
                recommendation=scored.recommendation,
                model_version=scored.model_version,
            )
            db.add(pred_row)
            db.commit()

            st.success("Scoring completed")
            col_a, col_b = st.columns(2)
            col_a.metric("Default Risk", f"{pred_row.risk_score:.2%}")
            col_b.metric("Retention Score", f"{pred_row.retention_score:.2%}")
            st.info(pred_row.recommendation)
        except Exception as exc:
            db.rollback()
            st.error(f"Scoring failed: {exc}")
        finally:
            db.close()
    else:
        try:
            score_resp = requests.post(f"{API_BASE}/api/v1/score", json=payload, timeout=8)
            if score_resp.ok:
                result = score_resp.json()
                st.success("Scoring completed")
                col_a, col_b = st.columns(2)
                col_a.metric("Default Risk", f"{result['risk_score']:.2%}")
                col_b.metric("Retention Score", f"{result['retention_score']:.2%}")
                st.info(result["recommendation"])
            else:
                st.error(f"Scoring failed: {score_resp.text}")
        except requests.RequestException:
            st.error("FastAPI service not reachable during scoring.")

st.divider()
if st.button("Download Executive Summary PDF"):
    if USE_LOCAL_SERVICES:
        db = SessionLocal()
        try:
            pdf_path = local_report_service.generate_executive_summary(db)
            st.download_button(
                label="Save Executive Summary",
                data=pdf_path.read_bytes(),
                file_name=pdf_path.name,
                mime="application/pdf",
            )
        except Exception as exc:
            st.error(f"Failed to generate report: {exc}")
        finally:
            db.close()
    else:
        try:
            report_resp = requests.get(f"{API_BASE}/api/v1/report/executive-summary", timeout=20)
            if report_resp.ok:
                st.download_button(
                    label="Save Executive Summary",
                    data=report_resp.content,
                    file_name="executive_summary.pdf",
                    mime="application/pdf",
                )
            else:
                st.error("Failed to generate report.")
        except requests.RequestException:
            st.error("FastAPI service not reachable for report generation.")
