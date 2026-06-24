"""CRUD helpers for the BOQ table."""
from __future__ import annotations
from .database import get_connection


def save_boq(project_id: int, items: list[dict]) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM boq WHERE project_id=?", (project_id,))
        for item in items:
            conn.execute(
                """INSERT INTO boq(project_id,item_no,description,quantity,unit,rate,amount)
                   VALUES(?,?,?,?,?,?,?)""",
                (
                    project_id,
                    item["item_no"],
                    item["description"],
                    item["quantity"],
                    item["unit"],
                    item["rate"],
                    item["amount"],
                ),
            )
        conn.commit()


def get_boq(project_id: int) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM boq WHERE project_id=? ORDER BY item_no",
            (project_id,),
        ).fetchall()
        return [dict(r) for r in rows]
