"""CRUD helpers for the projects table."""
from __future__ import annotations
from typing import Optional
from .database import get_connection


def create_project(data: dict) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO projects
               (project_name,client_name,site_location,project_type,
                plot_area,built_up_area,num_floors,construction_quality,
                start_date,expected_completion,status,notes)
               VALUES(:project_name,:client_name,:site_location,:project_type,
                      :plot_area,:built_up_area,:num_floors,:construction_quality,
                      :start_date,:expected_completion,:status,:notes)""",
            data,
        )
        conn.commit()
        return cur.lastrowid


def get_all_projects(status_filter: Optional[str] = None) -> list[dict]:
    with get_connection() as conn:
        if status_filter:
            rows = conn.execute(
                "SELECT * FROM projects WHERE status=? ORDER BY created_at DESC",
                (status_filter,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM projects ORDER BY created_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]


def get_project(project_id: int) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM projects WHERE id=?", (project_id,)
        ).fetchone()
        return dict(row) if row else None


def update_project(project_id: int, data: dict) -> None:
    data["id"] = project_id
    with get_connection() as conn:
        conn.execute(
            """UPDATE projects SET
               project_name=:project_name, client_name=:client_name,
               site_location=:site_location, project_type=:project_type,
               plot_area=:plot_area, built_up_area=:built_up_area,
               num_floors=:num_floors, construction_quality=:construction_quality,
               start_date=:start_date, expected_completion=:expected_completion,
               status=:status, notes=:notes
               WHERE id=:id""",
            data,
        )
        conn.commit()


def delete_project(project_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM projects WHERE id=?", (project_id,))
        conn.commit()


def search_projects(query: str) -> list[dict]:
    with get_connection() as conn:
        q = f"%{query}%"
        rows = conn.execute(
            """SELECT * FROM projects
               WHERE project_name LIKE ? OR client_name LIKE ? OR site_location LIKE ?
               ORDER BY created_at DESC""",
            (q, q, q),
        ).fetchall()
        return [dict(r) for r in rows]


def get_dashboard_stats() -> dict:
    with get_connection() as conn:
        # single pass over projects table
        counts = conn.execute(
            """SELECT COUNT(*),
                      SUM(status='Active'),
                      SUM(status='Completed')
               FROM projects"""
        ).fetchone()
        financials = conn.execute(
            """SELECT
                 (SELECT COALESCE(SUM(grand_total),0) FROM cost_estimates),
                 (SELECT COALESCE(SUM(amount),0)      FROM expenses)"""
        ).fetchone()
    est, actual = financials
    return {
        "total_projects":     counts[0] or 0,
        "active_projects":    counts[1] or 0,
        "completed_projects": counts[2] or 0,
        "total_estimated":    est,
        "total_actual":       actual,
        "cost_variance":      actual - est,
    }
