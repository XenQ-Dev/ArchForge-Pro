"""
ML Trainer — trains Random Forest and XGBoost on the synthetic dataset.
Saves: cost_model.pkl, duration_model.pkl, metrics.json
"""
from __future__ import annotations
import json
import pickle
from typing import Callable

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor

from app.ml.dataset_generator import generate_dataset
from app.utils.paths import data

MODEL_DIR = data("ml_models")


class ModelTrainer:
    def train(self, log_callback: Callable[[str], None] | None = None) -> dict:
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        log = log_callback or print

        log("Generating 10,000 project records…")
        df = generate_dataset(n=10_000)
        log(f"Dataset shape: {df.shape}")

        # Feature engineering
        log("Engineering features…")
        df = self._encode_features(df)
        feature_cols = ["plot_area", "built_up_area", "num_floors",
                        "project_type_enc", "quality_enc", "city_tier",
                        "area_per_floor", "floor_area_product"]

        X = df[feature_cols]
        y_cost = df["total_cost"]
        y_days = df["duration_days"]

        X_train, X_test, yc_train, yc_test, yd_train, yd_test = train_test_split(
            X, y_cost, y_days, test_size=0.2, random_state=42
        )
        log(f"Train size: {len(X_train)}, Test size: {len(X_test)}")

        metrics: dict = {}

        # ── Random Forest ───────────────────────────────────────────────────
        log("\nTraining Random Forest — Cost model…")
        rf_cost = RandomForestRegressor(
            n_estimators=200, max_depth=15, min_samples_split=4,
            n_jobs=-1, random_state=42
        )
        rf_cost.fit(X_train, yc_train)
        yc_pred_rf = rf_cost.predict(X_test)

        log("Training Random Forest — Duration model…")
        rf_days = RandomForestRegressor(
            n_estimators=200, max_depth=12, min_samples_split=4,
            n_jobs=-1, random_state=42
        )
        rf_days.fit(X_train, yd_train)
        yd_pred_rf = rf_days.predict(X_test)

        rf_metrics = {
            "cost_mae":  float(mean_absolute_error(yc_test, yc_pred_rf)),
            "cost_rmse": float(np.sqrt(mean_squared_error(yc_test, yc_pred_rf))),
            "cost_r2":   float(r2_score(yc_test, yc_pred_rf)),
            "days_mae":  float(mean_absolute_error(yd_test, yd_pred_rf)),
            "days_rmse": float(np.sqrt(mean_squared_error(yd_test, yd_pred_rf))),
            "days_r2":   float(r2_score(yd_test, yd_pred_rf)),
        }
        metrics["Random Forest"] = rf_metrics
        log(f"RF Cost  — MAE: ₹{rf_metrics['cost_mae']:,.0f} | R²: {rf_metrics['cost_r2']:.4f}")
        log(f"RF Days  — MAE: {rf_metrics['days_mae']:.1f} | R²: {rf_metrics['days_r2']:.4f}")

        # ── XGBoost ────────────────────────────────────────────────────────
        log("\nTraining XGBoost — Cost model…")
        xgb_cost = XGBRegressor(
            n_estimators=300, learning_rate=0.08, max_depth=8,
            subsample=0.8, colsample_bytree=0.8,
            random_state=42, n_jobs=-1, verbosity=0,
        )
        xgb_cost.fit(X_train, yc_train,
                     eval_set=[(X_test, yc_test)],
                     verbose=False)
        yc_pred_xgb = xgb_cost.predict(X_test)

        log("Training XGBoost — Duration model…")
        xgb_days = XGBRegressor(
            n_estimators=300, learning_rate=0.08, max_depth=7,
            subsample=0.8, colsample_bytree=0.8,
            random_state=42, n_jobs=-1, verbosity=0,
        )
        xgb_days.fit(X_train, yd_train,
                     eval_set=[(X_test, yd_test)],
                     verbose=False)
        yd_pred_xgb = xgb_days.predict(X_test)

        xgb_metrics = {
            "cost_mae":  float(mean_absolute_error(yc_test, yc_pred_xgb)),
            "cost_rmse": float(np.sqrt(mean_squared_error(yc_test, yc_pred_xgb))),
            "cost_r2":   float(r2_score(yc_test, yc_pred_xgb)),
            "days_mae":  float(mean_absolute_error(yd_test, yd_pred_xgb)),
            "days_rmse": float(np.sqrt(mean_squared_error(yd_test, yd_pred_xgb))),
            "days_r2":   float(r2_score(yd_test, yd_pred_xgb)),
        }
        metrics["XGBoost"] = xgb_metrics
        log(f"XGB Cost — MAE: ₹{xgb_metrics['cost_mae']:,.0f} | R²: {xgb_metrics['cost_r2']:.4f}")
        log(f"XGB Days — MAE: {xgb_metrics['days_mae']:.1f} | R²: {xgb_metrics['days_r2']:.4f}")

        # ── Save models ─────────────────────────────────────────────────────
        log("\nSaving models…")
        models = {
            "rf_cost": rf_cost,
            "rf_days": rf_days,
            "xgb_cost": xgb_cost,
            "xgb_days": xgb_days,
        }
        with open(MODEL_DIR / "cost_model.pkl", "wb") as f:
            pickle.dump({"rf": rf_cost, "xgb": xgb_cost}, f)
        with open(MODEL_DIR / "duration_model.pkl", "wb") as f:
            pickle.dump({"rf": rf_days, "xgb": xgb_days}, f)
        with open(MODEL_DIR / "metrics.json", "w") as f:
            json.dump(metrics, f, indent=2)

        log("Models saved: cost_model.pkl, duration_model.pkl")
        return metrics

    @staticmethod
    def _encode_features(df: pd.DataFrame) -> pd.DataFrame:
        type_map  = {"Residential": 0, "Commercial": 1, "Industrial": 2}
        qual_map  = {"Standard": 0, "Premium": 1, "Luxury": 2}
        df["project_type_enc"] = df["project_type"].map(type_map)
        df["quality_enc"]      = df["quality"].map(qual_map)
        df["area_per_floor"]   = df["built_up_area"] / df["num_floors"]
        df["floor_area_product"] = df["built_up_area"] * df["num_floors"]
        return df
