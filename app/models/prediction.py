from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PredictionResult(Base):
    __tablename__ = "prediction_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    loan_id: Mapped[int] = mapped_column(ForeignKey("loan_scenarios.id"), index=True)

    risk_score: Mapped[float] = mapped_column(Float)
    retention_score: Mapped[float] = mapped_column(Float)
    recommendation: Mapped[str] = mapped_column(String(255))
    model_version: Mapped[str] = mapped_column(String(50), default="v1")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    loan = relationship("LoanScenario")
