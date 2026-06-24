"""CRUD helpers for material_categories and materials tables."""
from __future__ import annotations
from typing import Optional
from .database import get_connection


def get_all_categories() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM material_categories ORDER BY name").fetchall()
        return [dict(r) for r in rows]


def get_all_materials(category_id: Optional[int] = None) -> list[dict]:
    with get_connection() as conn:
        if category_id:
            rows = conn.execute(
                """SELECT m.*, c.name as category_name FROM materials m
                   JOIN material_categories c ON m.category_id=c.id
                   WHERE m.category_id=? ORDER BY m.name""",
                (category_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT m.*, c.name as category_name FROM materials m
                   JOIN material_categories c ON m.category_id=c.id
                   ORDER BY c.name, m.name"""
            ).fetchall()
        return [dict(r) for r in rows]


def get_material(material_id: int) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM materials WHERE id=?", (material_id,)
        ).fetchone()
        return dict(row) if row else None


def get_material_by_name(name: str) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM materials WHERE name=?", (name,)
        ).fetchone()
        return dict(row) if row else None


def update_material_rate(material_id: int, rate: float) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE materials SET rate=?, last_updated=datetime('now','localtime') WHERE id=?",
            (rate, material_id),
        )
        conn.commit()


def add_material(data: dict) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO materials(category_id,name,unit,rate,gst_rate)
               VALUES(:category_id,:name,:unit,:rate,:gst_rate)""",
            data,
        )
        conn.commit()
        return cur.lastrowid


def update_material(material_id: int, data: dict) -> None:
    data["id"] = material_id
    with get_connection() as conn:
        conn.execute(
            """UPDATE materials SET category_id=:category_id, name=:name,
               unit=:unit, rate=:rate, gst_rate=:gst_rate,
               last_updated=datetime('now','localtime') WHERE id=:id""",
            data,
        )
        conn.commit()


def delete_material(material_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM materials WHERE id=?", (material_id,))
        conn.commit()


def search_materials(query: str) -> list[dict]:
    with get_connection() as conn:
        q = f"%{query}%"
        rows = conn.execute(
            """SELECT m.*, c.name as category_name FROM materials m
               JOIN material_categories c ON m.category_id=c.id
               WHERE m.name LIKE ? OR c.name LIKE ?
               ORDER BY c.name, m.name""",
            (q, q),
        ).fetchall()
        return [dict(r) for r in rows]
