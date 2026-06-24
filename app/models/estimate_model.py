"""CRUD helpers for cost_estimates and estimate_items."""
from __future__ import annotations
from typing import Optional
from .database import get_connection


def save_estimate(project_id: int, summary: dict, items: list[dict]) -> int:
    """Upsert an estimate for the given project. Returns estimate id."""
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT id FROM cost_estimates WHERE project_id=?", (project_id,)
        ).fetchone()

        if existing:
            est_id = existing[0]
            conn.execute(
                """UPDATE cost_estimates SET
                   material_cost=:material_cost, labour_cost=:labour_cost,
                   equipment_cost=:equipment_cost, contractor_margin=:contractor_margin,
                   gst_amount=:gst_amount, grand_total=:grand_total,
                   labour_pct=:labour_pct, equipment_pct=:equipment_pct,
                   contractor_pct=:contractor_pct, gst_pct=:gst_pct
                   WHERE id=:id""",
                {**summary, "id": est_id},
            )
            conn.execute("DELETE FROM estimate_items WHERE estimate_id=?", (est_id,))
        else:
            cur = conn.execute(
                """INSERT INTO cost_estimates
                   (project_id,material_cost,labour_cost,equipment_cost,
                    contractor_margin,gst_amount,grand_total,
                    labour_pct,equipment_pct,contractor_pct,gst_pct)
                   VALUES(:project_id,:material_cost,:labour_cost,:equipment_cost,
                          :contractor_margin,:gst_amount,:grand_total,
                          :labour_pct,:equipment_pct,:contractor_pct,:gst_pct)""",
                {**summary, "project_id": project_id},
            )
            est_id = cur.lastrowid

        for item in items:
            conn.execute(
                """INSERT INTO estimate_items(estimate_id,item_name,quantity,unit,rate,amount,category)
                   VALUES(?,?,?,?,?,?,?)""",
                (
                    est_id,
                    item["item_name"],
                    item["quantity"],
                    item["unit"],
                    item["rate"],
                    item["amount"],
                    item.get("category", "Material"),
                ),
            )
        conn.commit()
        return est_id


def get_estimate(project_id: int) -> Optional[dict]:
    with get_connection() as conn:
        est = conn.execute(
            "SELECT * FROM cost_estimates WHERE project_id=?", (project_id,)
        ).fetchone()
        if not est:
            return None
        result = dict(est)
        items = conn.execute(
            "SELECT * FROM estimate_items WHERE estimate_id=? ORDER BY id",
            (result["id"],),
        ).fetchall()
        result["items"] = [dict(i) for i in items]
        return result
