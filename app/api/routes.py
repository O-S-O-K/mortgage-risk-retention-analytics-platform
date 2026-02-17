from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.loan import LoanScenario
from app.models.prediction import PredictionResult
from app.schemas.loan import LoanRequest
from app.schemas.prediction import PortfolioSummary, ScoreResponse
from app.services.model_service import ModelService
from app.services.report_service import ReportService

router = APIRouter(prefix="/api/v1", tags=["mortgage-analytics"])
model_service = ModelService()
report_service = ReportService()


@router.post("/score", response_model=ScoreResponse)
def score_loan(loan: LoanRequest, db: Session = Depends(get_db)):
    loan_row = LoanScenario(**loan.model_dump())
    db.add(loan_row)
    db.flush()

    scored = model_service.score(loan)

    pred_row = PredictionResult(
        loan_id=loan_row.id,
        risk_score=scored.risk_score,
        retention_score=scored.retention_score,
        recommendation=scored.recommendation,
        model_version=scored.model_version,
    )
    db.add(pred_row)
    db.commit()
    db.refresh(pred_row)

    return ScoreResponse(
        loan_id=loan_row.id,
        prediction_id=pred_row.id,
        risk_score=pred_row.risk_score,
        retention_score=pred_row.retention_score,
        recommendation=pred_row.recommendation,
        model_version=pred_row.model_version,
        created_at=pred_row.created_at,
    )


@router.get("/portfolio/summary", response_model=PortfolioSummary)
def portfolio_summary(db: Session = Depends(get_db)):
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

    return PortfolioSummary(
        total_scored=int(total_scored),
        avg_risk_score=float(avg_risk),
        avg_retention_score=float(avg_retention),
        high_risk_count=int(high_risk),
        low_retention_count=int(low_retention),
    )


@router.get("/report/executive-summary")
def executive_summary_report(db: Session = Depends(get_db)):
    pdf_path = report_service.generate_executive_summary(db)
    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=pdf_path.name,
    )
