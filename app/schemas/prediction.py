from datetime import datetime

from pydantic import BaseModel


class ScoreResponse(BaseModel):
    loan_id: int
    prediction_id: int
    risk_score: float
    retention_score: float
    recommendation: str
    model_version: str
    created_at: datetime


class PortfolioSummary(BaseModel):
    total_scored: int
    avg_risk_score: float
    avg_retention_score: float
    high_risk_count: int
    low_retention_count: int
