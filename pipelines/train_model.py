from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

DEFAULT_MODEL_PATH = Path("./data/model_bundle.joblib")
FEATURES = [
    "credit_score",
    "ltv",
    "dti",
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
    income = rng.uniform(40_000, 250_000, size=n_samples)
    loan_amount = rng.uniform(80_000, 1_000_000, size=n_samples)
    interest_rate = rng.uniform(2.5, 10.5, size=n_samples)
    tenure_years = rng.integers(10, 31, size=n_samples)

    raw_default = (
        0.015 * (ltv - 80)
        + 0.02 * (dti - 35)
        + 0.02 * (interest_rate - 6)
        + 0.000002 * (loan_amount - 450000)
        - 0.02 * ((credit_score - 700) / 20)
    )
    prob_default = 1 / (1 + np.exp(-raw_default))
    defaulted = (rng.random(n_samples) < prob_default).astype(int)

    raw_retention = (
        -0.018 * (interest_rate - 5)
        - 0.012 * (dti - 30)
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
            "income": income,
            "loan_amount": loan_amount,
            "interest_rate": interest_rate,
            "tenure_years": tenure_years,
            "defaulted": defaulted,
            "retained": retained,
        }
    )


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

    bundle = {
        "version": "v1",
        "features": FEATURES,
        "default_model": default_pipeline,
        "retention_model": retention_pipeline,
        "metrics": {
            "default_accuracy": default_acc,
            "retention_accuracy": retention_acc,
        },
    }
    joblib.dump(bundle, model_path)
    return bundle


if __name__ == "__main__":
    trained = train_and_save_model()
    print(f"Saved model to: {DEFAULT_MODEL_PATH}")
    print(f"Metrics: {trained['metrics']}")
