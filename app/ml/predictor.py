"""ML Predictor — loads saved models and makes predictions."""
from __future__ import annotations
import json
import pickle

import numpy as np

from app.utils.paths import data
MODEL_DIR = data("ml_models")

TYPE_MAP = {"Residential": 0, "Commercial": 1, "Industrial": 2}
QUAL_MAP = {"Standard": 0, "Premium": 1, "Luxury": 2}
CITY_DEFAULT = 1.0  # neutral city tier


class MLPredictor:
    def __init__(self):
        self._cost_models = None
        self._duration_models = None

    def models_exist(self) -> bool:
        return (MODEL_DIR / "cost_model.pkl").exists() and \
               (MODEL_DIR / "duration_model.pkl").exists()

    def _load_models(self) -> None:
        if self._cost_models is None:
            with open(MODEL_DIR / "cost_model.pkl", "rb") as f:
                self._cost_models = pickle.load(f)
        if self._duration_models is None:
            with open(MODEL_DIR / "duration_model.pkl", "rb") as f:
                self._duration_models = pickle.load(f)

    def predict(
        self,
        plot_area: float,
        built_up_area: float,
        num_floors: int,
        project_type: str,
        quality: str,
        city_tier: float = CITY_DEFAULT,
    ) -> dict:
        self._load_models()

        area_per_floor = built_up_area / max(num_floors, 1)
        floor_area_product = built_up_area * num_floors

        X = np.array([[
            plot_area,
            built_up_area,
            num_floors,
            TYPE_MAP.get(project_type, 0),
            QUAL_MAP.get(quality, 0),
            city_tier,
            area_per_floor,
            floor_area_product,
        ]])

        rf_cost  = float(self._cost_models["rf"].predict(X)[0])
        xgb_cost = float(self._cost_models["xgb"].predict(X)[0])
        rf_days  = float(self._duration_models["rf"].predict(X)[0])
        xgb_days = float(self._duration_models["xgb"].predict(X)[0])

        return {
            "rf_cost":  max(0, rf_cost),
            "xgb_cost": max(0, xgb_cost),
            "rf_days":  max(1, rf_days),
            "xgb_days": max(1, xgb_days),
        }

    def load_metrics(self) -> dict | None:
        metrics_path = MODEL_DIR / "metrics.json"
        if not metrics_path.exists():
            return None
        with open(metrics_path) as f:
            return json.load(f)
