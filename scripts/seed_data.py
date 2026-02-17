from __future__ import annotations

import random

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.loan import LoanScenario
from app.models.prediction import PredictionResult
from app.schemas.loan import LoanRequest
from app.services.model_service import ModelService


def seed(n: int = 30) -> None:
    Base.metadata.create_all(bind=engine)
    model = ModelService()

    db = SessionLocal()
    try:
        for _ in range(n):
            loan = LoanRequest(
                credit_score=random.randint(580, 810),
                ltv=round(random.uniform(55, 100), 2),
                dti=round(random.uniform(15, 55), 2),
                days_in_processing=random.randint(2, 40),
                documentation_completeness_flag=random.randint(0, 1),
                income=round(random.uniform(55000, 240000), 2),
                loan_amount=round(random.uniform(120000, 900000), 2),
                interest_rate=round(random.uniform(3.2, 9.8), 2),
                tenure_years=random.randint(10, 30),
            )

            payload = loan.model_dump()
            loan_row = LoanScenario(
                credit_score=payload["credit_score"],
                ltv=payload["ltv"],
                dti=payload["dti"],
                income=payload["income"],
                loan_amount=payload["loan_amount"],
                interest_rate=payload["interest_rate"],
                tenure_years=payload["tenure_years"],
            )
            db.add(loan_row)
            db.flush()

            scored = model.score(loan)
            db.add(
                PredictionResult(
                    loan_id=loan_row.id,
                    risk_score=scored.risk_score,
                    retention_score=scored.retention_score,
                    recommendation=scored.recommendation,
                    model_version=scored.model_version,
                )
            )

        db.commit()
        print(f"Seeded {n} records")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
