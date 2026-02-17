from fastapi import FastAPI

from app.api.routes import router as api_router
from app.db.base import Base
from app.db.session import engine
from app.models.loan import LoanScenario
from app.models.prediction import PredictionResult

app = FastAPI(title="Mortgage Risk & Retention Analytics API", version="0.1.0")

LoanScenario
PredictionResult
Base.metadata.create_all(bind=engine)


@app.get("/health")
def health_check():
    return {"status": "ok"}


app.include_router(api_router)
