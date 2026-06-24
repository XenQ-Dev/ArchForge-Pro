"""
Construction Cost Estimation Engine.
Uses realistic Indian construction norms (IS codes & CPWD DSR guidelines).

Key references:
- Thumb rule: ~0.4 bags cement per sq.ft of slab (M20 grade, 4" slab)
- Steel: ~4 kg per sq.ft (residential RCC frame)
- Bricks: ~8 bricks per sq.ft of walling (approx 50% of built-up area is wall)
- Sand: ~0.06 Cu.M per sq.ft
- Aggregate: ~0.04 Cu.M per sq.ft
"""
from __future__ import annotations
from dataclasses import dataclass, field

from app.models.material_model import get_material_by_name


@dataclass
class EstimationResult:
    material_cost: float = 0.0
    labour_cost: float = 0.0
    equipment_cost: float = 0.0
    contractor_margin: float = 0.0
    gst_amount: float = 0.0
    grand_total: float = 0.0
    items: list[dict] = field(default_factory=list)


# Quality multipliers relative to Standard
QUALITY_FACTOR = {
    "Standard": 1.00,
    "Premium":  1.35,
    "Luxury":   1.80,
}

# Project type multipliers
TYPE_FACTOR = {
    "Residential": 1.00,
    "Commercial":  1.15,
    "Industrial":  1.05,
}

# Per-sq.ft material consumption norms (Standard quality, ground floor)
# Format: (material_name, quantity_per_sqft, unit)
MATERIAL_NORMS = [
    ("OPC Cement 53 Grade",   0.40,  "Bag (50kg)"),   # for RCC + plaster
    ("TMT Steel Fe500",       0.004, "MT"),             # 4 kg/sqft
    ("River Sand (M-Sand)",   0.06,  "Cu.M"),
    ("Coarse Aggregate 20mm", 0.04,  "Cu.M"),
    ("Red Brick (Modular)",   5.0,   "Nos"),            # walling
    ("Ceramic Floor Tile 600x600", 1.1, "Sq.M"),        # 1 sqft = 0.093 sqm, +10% wastage
    ("Interior Emulsion Paint", 0.04, "Litre"),         # 2 coats, 1L=12 sqm
    ("Copper Wire 2.5 sq.mm", 1.2,  "Mtr"),
    ("CPVC Pipe 25mm",        0.5,   "Mtr"),
    ("Waterproofing Compound", 0.05, "Kg"),
]


class EstimationEngine:
    def estimate(
        self,
        built_up_area: float,
        num_floors: int,
        quality: str,
        project_type: str,
        labour_pct: float = 25.0,
        equipment_pct: float = 5.0,
        contractor_pct: float = 10.0,
        gst_pct: float = 18.0,
    ) -> dict:
        q_factor = QUALITY_FACTOR.get(quality, 1.0)
        t_factor = TYPE_FACTOR.get(project_type, 1.0)
        # Floor factor: each additional floor adds ~85% of ground floor cost
        floor_factor = 1 + (num_floors - 1) * 0.85

        items: list[dict] = []
        total_material_cost = 0.0

        for mat_name, qty_per_sqft, unit in MATERIAL_NORMS:
            quantity = qty_per_sqft * built_up_area * floor_factor * q_factor * t_factor
            mat = get_material_by_name(mat_name)
            rate = mat["rate"] if mat else self._fallback_rate(mat_name)
            amount = quantity * rate
            total_material_cost += amount
            items.append({
                "item_name": mat_name,
                "quantity": round(quantity, 2),
                "unit": unit,
                "rate": round(rate, 2),
                "amount": round(amount, 2),
                "category": "Material",
            })

        # Add finishing costs (tiles upgrade for premium/luxury)
        if quality in ("Premium", "Luxury"):
            total_material_cost *= q_factor * 0.3 + 0.7  # already factored in qty

        # Derived costs
        labour_cost = total_material_cost * (labour_pct / 100)
        equipment_cost = total_material_cost * (equipment_pct / 100)
        subtotal = total_material_cost + labour_cost + equipment_cost
        contractor_margin = subtotal * (contractor_pct / 100)
        pre_gst = subtotal + contractor_margin
        gst_amount = pre_gst * (gst_pct / 100)
        grand_total = pre_gst + gst_amount

        return {
            "material_cost": round(total_material_cost, 2),
            "labour_cost": round(labour_cost, 2),
            "equipment_cost": round(equipment_cost, 2),
            "contractor_margin": round(contractor_margin, 2),
            "gst_amount": round(gst_amount, 2),
            "grand_total": round(grand_total, 2),
            "items": items,
            "labour_pct": labour_pct,
            "equipment_pct": equipment_pct,
            "contractor_pct": contractor_pct,
            "gst_pct": gst_pct,
        }

    @staticmethod
    def _fallback_rate(mat_name: str) -> float:
        """Hardcoded fallback in case material is missing from DB."""
        fallbacks = {
            "OPC Cement 53 Grade": 420,
            "TMT Steel Fe500": 72000,
            "River Sand (M-Sand)": 1800,
            "Coarse Aggregate 20mm": 2000,
            "Red Brick (Modular)": 9,
            "Ceramic Floor Tile 600x600": 450,
            "Interior Emulsion Paint": 280,
            "Copper Wire 2.5 sq.mm": 55,
            "CPVC Pipe 25mm": 145,
            "Waterproofing Compound": 380,
        }
        return fallbacks.get(mat_name, 0)
