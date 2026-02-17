from __future__ import annotations

from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import precision_score, recall_score, roc_auc_score
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

DEFAULT_MODEL_PATH = Path("./data/model_bundle.joblib")
FEATURES = [
    "credit_score",
    "ltv",
    "dti",
    "days_in_processing",
    "documentation_completeness_flag",
    "income",
    "loan_amount",
    "interest_rate",
    "tenure_years",
]


def _build_synthetic_dataset(n_samples: int = 2500) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    credit_score = rng.integers(520, 821, size=n_samples)
    ltv = rng.uniform(45, 105, size=n_samples)
    dti = rng.uniform(10, 60, size=n_samples)
    days_in_processing = rng.integers(2, 46, size=n_samples)
    documentation_completeness_flag = rng.integers(0, 2, size=n_samples)
    income = rng.uniform(40_000, 250_000, size=n_samples)
    loan_amount = rng.uniform(80_000, 1_000_000, size=n_samples)
    interest_rate = rng.uniform(2.5, 10.5, size=n_samples)
    tenure_years = rng.integers(10, 31, size=n_samples)

    raw_default = (
        0.015 * (ltv - 80)
        + 0.02 * (dti - 35)
        + 0.018 * (days_in_processing - 14) / 10
        - 0.28 * documentation_completeness_flag
        + 0.02 * (interest_rate - 6)
        + 0.000002 * (loan_amount - 450000)
        - 0.02 * ((credit_score - 700) / 20)
    )
    prob_default = 1 / (1 + np.exp(-raw_default))
    defaulted = (rng.random(n_samples) < prob_default).astype(int)

    raw_retention = (
        -0.018 * (interest_rate - 5)
        - 0.012 * (dti - 30)
        - 0.010 * (days_in_processing - 14) / 10
        + 0.25 * documentation_completeness_flag
        + 0.016 * ((credit_score - 700) / 20)
        + 0.000002 * (income - 100000)
        - 0.000001 * (loan_amount - 400000)
    )
    prob_retention = 1 / (1 + np.exp(-raw_retention))
    retained = (rng.random(n_samples) < prob_retention).astype(int)

    return pd.DataFrame(
        {
            "credit_score": credit_score,
            "ltv": ltv,
            "dti": dti,
            "days_in_processing": days_in_processing,
            "documentation_completeness_flag": documentation_completeness_flag,
            "income": income,
            "loan_amount": loan_amount,
            "interest_rate": interest_rate,
            "tenure_years": tenure_years,
            "defaulted": defaulted,
            "retained": retained,
        }
    )


def _build_feature_importance_plot(feature_scores: dict[str, float], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sorted_items = sorted(feature_scores.items(), key=lambda item: item[1], reverse=True)
    labels = [item[0] for item in sorted_items]
    values = [item[1] for item in sorted_items]

    plt.figure(figsize=(8, 4.2))
    plt.barh(labels[::-1], values[::-1])
    plt.title("Default Risk Model Feature Importance")
    plt.xlabel("Absolute coefficient magnitude")
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


def train_and_save_model(model_path: str | Path = DEFAULT_MODEL_PATH) -> dict:
    model_path = Path(model_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)

    df = _build_synthetic_dataset()
    X = df[FEATURES]

    y_default = df["defaulted"]
    X_train_d, X_test_d, y_train_d, y_test_d = train_test_split(
        X, y_default, test_size=0.2, random_state=42, stratify=y_default
    )
    default_pipeline = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=1200)),
        ]
    )
    default_pipeline.fit(X_train_d, y_train_d)
    default_acc = float(default_pipeline.score(X_test_d, y_test_d))
    default_prob = default_pipeline.predict_proba(X_test_d)[:, 1]
    default_pred = default_pipeline.predict(X_test_d)

    default_roc_auc = float(roc_auc_score(y_test_d, default_prob))
    default_precision = float(precision_score(y_test_d, default_pred, pos_label=1, zero_division=0))
    default_recall = float(recall_score(y_test_d, default_pred, pos_label=1, zero_division=0))

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    default_cv_acc = float(cross_val_score(default_pipeline, X, y_default, cv=cv, scoring="accuracy").mean())

    y_retained = df["retained"]
    X_train_r, X_test_r, y_train_r, y_test_r = train_test_split(
        X, y_retained, test_size=0.2, random_state=42, stratify=y_retained
    )
    retention_pipeline = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=1200)),
        ]
    )
    retention_pipeline.fit(X_train_r, y_train_r)
    retention_acc = float(retention_pipeline.score(X_test_r, y_test_r))

    default_clf = default_pipeline.named_steps["clf"]
    feature_importance = {
        feature: float(abs(weight))
        for feature, weight in zip(FEATURES, default_clf.coef_[0], strict=True)
    }

    scaler = default_pipeline.named_steps["scaler"]
    x_sample = X_test_d.iloc[[0]]
    x_scaled_sample = scaler.transform(x_sample)[0]
    shap_values_sample = {
        feature: float(weight * value)
        for feature, weight, value in zip(FEATURES, default_clf.coef_[0], x_scaled_sample, strict=True)
    }

    top_features = [
        {"feature": feature, "importance": round(score, 4)}
        for feature, score in sorted(feature_importance.items(), key=lambda item: item[1], reverse=True)[:5]
    ]

    feature_plot_path = Path("./reports/generated/feature_importance_default.png")
    _build_feature_importance_plot(feature_importance, feature_plot_path)

    bundle = {
        "version": "v1",
        "features": FEATURES,
        "default_model": default_pipeline,
        "retention_model": retention_pipeline,
        "metrics": {
            "default_accuracy": default_acc,
            "default_roc_auc": default_roc_auc,
            "default_precision_high_risk": default_precision,
            "default_recall_high_risk": default_recall,
            "default_cross_validated_accuracy": default_cv_acc,
            "retention_accuracy": retention_acc,
        },
        "top_predictive_features": top_features,
        "explainability": {
            "shap_values_sample": {k: round(v, 4) for k, v in shap_values_sample.items()},
            "shap_method": "linear_model_contribution_approximation",
            "feature_importance": {k: round(v, 4) for k, v in feature_importance.items()},
            "feature_importance_plot_path": str(feature_plot_path),
        },
        "model_governance": {
            "purpose": "Estimate default risk and customer retention probability for mortgage loan workflows.",
            "training_data": "Synthetic mortgage-like dataset generated for demonstration.",
            "limitations": [
                "Not trained on production portfolio data.",
                "Should not be used for final credit decisions without validation and compliance review.",
            ],
            "monitoring_recommendations": [
                "Track drift in feature distributions monthly.",
                "Monitor precision/recall by borrower segment.",
                "Recalibrate threshold policies quarterly.",
            ],
        },
    }
    joblib.dump(bundle, model_path)
    return bundle


if __name__ == "__main__":
    trained = train_and_save_model()
    print(f"Saved model to: {DEFAULT_MODEL_PATH}")
    print(f"Metrics: {trained['metrics']}")
