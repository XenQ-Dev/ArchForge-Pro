"""
Generates a synthetic dataset of 10,000 Indian construction projects.
All cost values are in INR.  No external data or API required.
"""
from __future__ import annotations
import random
import math
import pandas as pd


# ── Seed rates (INR per unit) — realistic Indian market 2024 ──────────────
CEMENT_RATE   = 420   # per 50 kg bag
STEEL_RATE    = 72000 # per MT
SAND_RATE     = 1800  # per Cu.M
AGG_RATE      = 2000  # per Cu.M
BRICK_RATE    = 9     # per Nos

# Labour as % of material cost by quality
LABOUR_PCT = {"Standard": 0.25, "Premium": 0.28, "Luxury": 0.32}
EQUIP_PCT  = {"Standard": 0.05, "Premium": 0.06, "Luxury": 0.07}
MARGIN_PCT = 0.10
GST_PCT    = 0.18

# Base cost per sq.ft (INR) before quality/type adjustment — approximate all-in
BASE_COST_PER_SQFT = {
    ("Residential", "Standard"): 1800,
    ("Residential", "Premium"):  2600,
    ("Residential", "Luxury"):   4200,
    ("Commercial",  "Standard"): 2200,
    ("Commercial",  "Premium"):  3200,
    ("Commercial",  "Luxury"):   5000,
    ("Industrial",  "Standard"): 1600,
    ("Industrial",  "Premium"):  2400,
    ("Industrial",  "Luxury"):   3800,
}

# Duration (days) per 1000 sq.ft by quality
DURATION_PER_1000SQFT = {
    "Standard": 45,
    "Premium":  55,
    "Luxury":   75,
}

PROJECT_TYPES = ["Residential", "Commercial", "Industrial"]
QUALITIES     = ["Standard", "Premium", "Luxury"]
CITIES        = [
    "Mumbai", "Pune", "Delhi", "Bangalore", "Chennai",
    "Hyderabad", "Kolkata", "Ahmedabad", "Jaipur", "Surat",
    "Lucknow", "Nagpur", "Indore", "Bhopal", "Vadodara",
]


def generate_dataset(n: int = 10_000, seed: int = 42) -> pd.DataFrame:
    rng = random.Random(seed)
    records = []

    for _ in range(n):
        proj_type = rng.choice(PROJECT_TYPES)
        quality   = rng.choice(QUALITIES)

        # Built-up area (sq.ft) — varies by type
        if proj_type == "Residential":
            bua = rng.uniform(600, 8000)
        elif proj_type == "Commercial":
            bua = rng.uniform(1000, 50000)
        else:
            bua = rng.uniform(2000, 100000)

        plot_area = bua * rng.uniform(1.1, 2.5)
        num_floors = rng.randint(1, 15 if proj_type == "Commercial" else 5)

        # Effective area = bua * floors (for multi-storey)
        eff_area = bua  # bua already represents per-floor for simplicity

        base = BASE_COST_PER_SQFT[(proj_type, quality)]
        # Floor premium: each additional floor adds 3% cost
        floor_adj = 1 + (num_floors - 1) * 0.03
        # Noise: ±15%
        noise = rng.uniform(0.85, 1.15)
        city = rng.choice(CITIES)
        # City tier premium
        city_factor = 1.25 if city in ("Mumbai", "Delhi", "Bangalore") else (
            1.10 if city in ("Pune", "Chennai", "Hyderabad") else 1.0
        )

        cost_per_sqft = base * floor_adj * city_factor * noise
        total_cost = cost_per_sqft * eff_area

        # Duration
        base_days = DURATION_PER_1000SQFT[quality]
        duration_days = (eff_area / 1000) * base_days * num_floors * rng.uniform(0.9, 1.1)
        duration_days = max(30, duration_days)

        records.append({
            "plot_area":       round(plot_area, 0),
            "built_up_area":   round(bua, 0),
            "num_floors":      num_floors,
            "project_type":    proj_type,
            "quality":         quality,
            "city_tier":       city_factor,
            "total_cost":      round(total_cost, 0),
            "duration_days":   round(duration_days, 0),
        })

    return pd.DataFrame(records)
