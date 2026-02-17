from __future__ import annotations

import requests
import streamlit as st

API_BASE = "http://127.0.0.1:8000"

st.set_page_config(page_title="Mortgage Risk Dashboard", layout="wide")
st.title("Mortgage Risk & Retention Analytics")

st.subheader("Portfolio Summary")
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
    st.error("FastAPI service not reachable. Start API at http://127.0.0.1:8000")

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
