from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class LoanScenario(Base):
    __tablename__ = "loan_scenarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    credit_score: Mapped[int] = mapped_column(Integer)
    ltv: Mapped[float] = mapped_column(Float)
    dti: Mapped[float] = mapped_column(Float)
    income: Mapped[float] = mapped_column(Float)
    loan_amount: Mapped[float] = mapped_column(Float)
    interest_rate: Mapped[float] = mapped_column(Float)
    tenure_years: Mapped[int] = mapped_column(Integer)

    defaulted: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    retained: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
