from __future__ import annotations

from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns
from fpdf import FPDF
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.prediction import PredictionResult


class ReportService:
    def __init__(self) -> None:
        self.report_dir = Path(settings.reports_dir)
        self.report_dir.mkdir(parents=True, exist_ok=True)

    def _build_chart(self, avg_risk: float, avg_retention: float, out_path: Path) -> None:
        sns.set_theme(style="whitegrid")
        plt.figure(figsize=(6, 3.5))
        plt.bar(["Avg Risk", "Avg Retention"], [avg_risk, avg_retention])
        plt.ylim(0, 1)
        plt.ylabel("Score")
        plt.title("Portfolio Score Snapshot")
        plt.tight_layout()
        plt.savefig(out_path)
        plt.close()

    def generate_executive_summary(self, db: Session) -> Path:
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

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        pdf_path = self.report_dir / f"executive_summary_{timestamp}.pdf"
        chart_path = self.report_dir / f"portfolio_snapshot_{timestamp}.png"

        self._build_chart(float(avg_risk), float(avg_retention), chart_path)

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=12)
        pdf.add_page()

        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, "Mortgage Risk & Retention Executive Summary", new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", size=11)
        pdf.cell(0, 8, f"Generated: {datetime.utcnow().isoformat()} UTC", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Portfolio KPIs", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", size=11)
        pdf.cell(0, 7, f"- Total loans scored: {int(total_scored)}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 7, f"- Average default risk: {float(avg_risk):.2%}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 7, f"- Average retention score: {float(avg_retention):.2%}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 7, f"- High-risk accounts: {int(high_risk)}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 7, f"- Low-retention accounts: {int(low_retention)}", new_x="LMARGIN", new_y="NEXT")

        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Interpretation", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", size=11)
        pdf.multi_cell(
            0,
            7,
            "Use high default risk populations for underwriting review and collections strategy. "
            "Use low retention cohorts for outreach campaigns, refinancing offers, and customer support prioritization.",
        )

        pdf.ln(4)
        if chart_path.exists():
            pdf.image(str(chart_path), w=170)

        pdf.output(str(pdf_path))
        return pdf_path
