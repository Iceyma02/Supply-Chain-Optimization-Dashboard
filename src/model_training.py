"""
Delay Prediction Model
XGBoost classifier to predict shipment delays
Features: weather, traffic, route complexity, driver experience, temporal patterns
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import (classification_report, confusion_matrix,
                             roc_auc_score, average_precision_score)
from sklearn.pipeline import Pipeline
import xgboost as xgb
import joblib
import json
import os
import warnings
warnings.filterwarnings("ignore")

DATA_PATH  = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "shipments_3yr.csv")
MODEL_DIR  = os.path.join(os.path.dirname(__file__), "..", "models")
os.makedirs(MODEL_DIR, exist_ok=True)

FEATURES = [
    "weather_score", "traffic_index", "route_complexity", "distance_km",
    "driver_experience", "driver_rating", "departure_hour", "day_of_week",
    "month", "is_holiday", "is_weekend", "weight_kg", "cargo_type_enc",
    "planned_hours",
]
TARGET = "is_delayed"

def load_and_engineer(path):
    df = pd.read_csv(path, parse_dates=["date"])

    # Encode cargo type
    le = LabelEncoder()
    df["cargo_type_enc"] = le.fit_transform(df["cargo_type"])

    # Extra features
    df["hour_sin"] = np.sin(2 * np.pi * df["departure_hour"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["departure_hour"] / 24)
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)

    full_features = FEATURES + ["hour_sin", "hour_cos", "month_sin", "month_cos"]

    X = df[full_features].copy()
    y = df[TARGET]
    return X, y, le, full_features

def train():
    print("=" * 60)
    print("  SUPPLY CHAIN DELAY PREDICTION MODEL")
    print("  XGBoost Classifier | 3-Year Dataset")
    print("=" * 60)

    X, y, le, features = load_and_engineer(DATA_PATH)
    print(f"\n📊 Dataset: {len(X):,} records | Delay rate: {y.mean()*100:.1f}%")

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    print(f"   Train: {len(X_train):,} | Test: {len(X_test):,}")

    # ── Model ─────────────────────────────────────────────────────────────
    model = xgb.XGBClassifier(
        n_estimators=400,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=(y_train == 0).sum() / (y_train == 1).sum(),
        use_label_encoder=False,
        eval_metric="auc",
        random_state=42,
        n_jobs=-1,
    )

    print("\n⟳ Training XGBoost model...")
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=False,
    )

    # ── Evaluation ────────────────────────────────────────────────────────
    y_pred  = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    roc_auc = roc_auc_score(y_test, y_proba)
    pr_auc  = average_precision_score(y_test, y_proba)

    print("\n📈 Model Performance:")
    print(f"   ROC-AUC:  {roc_auc:.4f}")
    print(f"   PR-AUC:   {pr_auc:.4f}")
    print("\n" + classification_report(y_test, y_pred, target_names=["On-Time", "Delayed"]))

    # ── Feature Importance ────────────────────────────────────────────────
    importance = pd.DataFrame({
        "feature":    features,
        "importance": model.feature_importances_
    }).sort_values("importance", ascending=False)

    print("🔍 Top Feature Importances:")
    for _, row in importance.head(10).iterrows():
        bar = "█" * int(row["importance"] * 100)
        print(f"   {row['feature']:<25} {bar} {row['importance']:.4f}")

    # ── Cross-Val ─────────────────────────────────────────────────────────
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(model, X, y, cv=cv, scoring="roc_auc", n_jobs=-1)
    print(f"\n📊 5-Fold CV ROC-AUC: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

    # ── Save ──────────────────────────────────────────────────────────────
    joblib.dump(model, os.path.join(MODEL_DIR, "delay_predictor.pkl"))
    joblib.dump(le,    os.path.join(MODEL_DIR, "label_encoder.pkl"))

    metrics = {
        "roc_auc": round(roc_auc, 4),
        "pr_auc":  round(pr_auc, 4),
        "cv_roc_auc_mean": round(cv_scores.mean(), 4),
        "cv_roc_auc_std":  round(cv_scores.std(), 4),
        "features": features,
        "n_train": int(len(X_train)),
        "n_test":  int(len(X_test)),
        "delay_rate": float(round(y.mean(), 4)),
    }
    with open(os.path.join(MODEL_DIR, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)

    importance.to_csv(os.path.join(MODEL_DIR, "feature_importance.csv"), index=False)

    print(f"\n✅ Model saved → {MODEL_DIR}/delay_predictor.pkl")
    return model, metrics

if __name__ == "__main__":
    train()