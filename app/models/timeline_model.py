"""CRUD helpers for project_phases."""
from __future__ import annotations
from typing import Optional
from .database import get_connection

DEFAULT_PHASES = [
    (1, "Foundation"),
    (2, "Structure / RCC Frame"),
    (3, "Brickwork / Masonry"),
    (4, "Plumbing"),
    (5, "Electrical"),
    (6, "Plastering"),
    (7, "Flooring"),
    (8, "Painting"),
    (9, "Finishing & Handover"),
]


def init_project_phases(project_id: int) -> None:
    """Create default phases for a new project if not already present."""
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT COUNT(*) FROM project_phases WHERE project_id=?", (project_id,)
        ).fetchone()[0]
        if existing == 0:
            for order, name in DEFAULT_PHASES:
                conn.execute(
                    """INSERT INTO project_phases(project_id,phase_order,phase_name)
                       VALUES(?,?,?)""",
                    (project_id, order, name),
                )
            conn.commit()


def get_phases(project_id: int) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM project_phases WHERE project_id=? ORDER BY phase_order",
            (project_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def update_phase(phase_id: int, data: dict) -> None:
    data["id"] = phase_id
    with get_connection() as conn:
        conn.execute(
            """UPDATE project_phases SET
               planned_start=:planned_start, planned_end=:planned_end,
               actual_start=:actual_start, actual_end=:actual_end,
               completion_pct=:completion_pct, status=:status, notes=:notes
               WHERE id=:id""",
            data,
        )
        conn.commit()
