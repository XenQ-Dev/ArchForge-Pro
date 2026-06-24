"""CRUD helpers for the expenses table."""
from __future__ import annotations
from typing import Optional
from .database import get_connection


def add_expense(data: dict) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO expenses(project_id,expense_date,category,description,amount,receipt_ref)
               VALUES(:project_id,:expense_date,:category,:description,:amount,:receipt_ref)""",
            data,
        )
        conn.commit()
        return cur.lastrowid


def get_expenses(project_id: int) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM expenses WHERE project_id=? ORDER BY expense_date DESC",
            (project_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def update_expense(expense_id: int, data: dict) -> None:
    data["id"] = expense_id
    with get_connection() as conn:
        conn.execute(
            """UPDATE expenses SET expense_date=:expense_date, category=:category,
               description=:description, amount=:amount, receipt_ref=:receipt_ref
               WHERE id=:id""",
            data,
        )
        conn.commit()


def delete_expense(expense_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM expenses WHERE id=?", (expense_id,))
        conn.commit()


def get_expense_summary(project_id: int) -> dict:
    with get_connection() as conn:
        total = conn.execute(
            "SELECT COALESCE(SUM(amount),0) FROM expenses WHERE project_id=?",
            (project_id,),
        ).fetchone()[0]
        by_cat = conn.execute(
            """SELECT category, COALESCE(SUM(amount),0) as total
               FROM expenses WHERE project_id=?
               GROUP BY category""",
            (project_id,),
        ).fetchall()
        return {"total": total, "by_category": {r[0]: r[1] for r in by_cat}}


def get_monthly_spending(project_id: int) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT strftime('%Y-%m', expense_date) as month,
                      SUM(amount) as total
               FROM expenses WHERE project_id=?
               GROUP BY month ORDER BY month""",
            (project_id,),
        ).fetchall()
        return [dict(r) for r in rows]
