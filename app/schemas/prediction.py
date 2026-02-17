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


class TopFeature(BaseModel):
    feature: str
    importance: float


class ModelPerformanceResponse(BaseModel):
    roc_auc: float
    precision_high_risk: float
    recall_high_risk: float
    cross_validated_accuracy: float
    top_predictive_features: list[TopFeature]


class ModelExplainabilityResponse(BaseModel):
    shap_values_sample: dict[str, float]
    shap_method: str
    feature_importance: dict[str, float]
    feature_importance_plot_path: str
    model_governance: dict[str, str | list[str]]
