from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import joblib
import pandas as pd

from app.core.config import settings
from app.schemas.loan import LoanRequest
from pipelines.train_model import train_and_save_model


@dataclass
class PredictionResultDTO:
    risk_score: float
    retention_score: float
    recommendation: str
    model_version: str


class ModelService:
    def __init__(self, model_path: str | Path | None = None):
        self.model_path = Path(model_path or settings.model_path)
        self.bundle = self._load_or_train()

    def _load_or_train(self) -> dict:
        if not self.model_path.exists():
            return train_and_save_model(self.model_path)
        return joblib.load(self.model_path)

    def _recommendation(self, risk: float, retention: float) -> str:
        if risk >= 0.65 and retention < 0.45:
            return "High risk and low retention: immediate intervention required"
        if risk >= 0.65:
            return "High default risk: tighten underwriting and monitoring"
        if retention < 0.45:
            return "Low retention risk: offer targeted customer retention program"
        return "Portfolio profile stable: monitor routinely"

    def score(self, loan: LoanRequest) -> PredictionResultDTO:
        source_payload = loan.model_dump()
        features = self.bundle.get("features", [])
        payload = pd.DataFrame([{feature: source_payload[feature] for feature in features}])
        default_prob = float(self.bundle["default_model"].predict_proba(payload)[0, 1])
        retention_prob = float(self.bundle["retention_model"].predict_proba(payload)[0, 1])

        return PredictionResultDTO(
            risk_score=round(default_prob, 4),
            retention_score=round(retention_prob, 4),
            recommendation=self._recommendation(default_prob, retention_prob),
            model_version=self.bundle.get("version", "v1"),
        )

    def get_performance_summary(self) -> dict:
        metrics = self.bundle.get("metrics", {})
        return {
            "roc_auc": float(metrics.get("default_roc_auc", 0.0)),
            "precision_high_risk": float(metrics.get("default_precision_high_risk", 0.0)),
            "recall_high_risk": float(metrics.get("default_recall_high_risk", 0.0)),
            "cross_validated_accuracy": float(metrics.get("default_cross_validated_accuracy", 0.0)),
            "top_predictive_features": self.bundle.get("top_predictive_features", []),
        }

    def get_explainability_summary(self) -> dict:
        explainability = self.bundle.get("explainability", {})
        governance = self.bundle.get("model_governance", {})
        return {
            "shap_values_sample": explainability.get("shap_values_sample", {}),
            "shap_method": explainability.get("shap_method", "linear_model_contribution_approximation"),
            "feature_importance": explainability.get("feature_importance", {}),
            "feature_importance_plot_path": explainability.get("feature_importance_plot_path", ""),
            "model_governance": governance,
        }
