"""Expense Tracker Page."""
from __future__ import annotations
from datetime import date

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QSizePolicy, QFrame,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from app.models.project_model import get_all_projects
from app.models.expense_model import get_expenses, delete_expense, get_expense_summary
from app.models.estimate_model import get_estimate
from app.utils.formatters import fmt_inr, fmt_date
from app.views.dialogs.expense_dialog import ExpenseDialog


class ExpensesPage(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(16)

        hdr = QLabel("Expense Tracker")
        hdr.setObjectName("section_title")
        sub = QLabel("Track actual project expenditure vs estimates")
        sub.setObjectName("section_subtitle")
        lay.addWidget(hdr)
        lay.addWidget(sub)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("Project:"))
        self._proj_combo = QComboBox()
        self._proj_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._proj_combo.currentIndexChanged.connect(self._load_expenses)
        toolbar.addWidget(self._proj_combo, stretch=1)

        add_btn = QPushButton("+ Add Expense")
        add_btn.clicked.connect(self._add_expense)
        toolbar.addWidget(add_btn)

        lay.addLayout(toolbar)

        # Summary cards
        self._summary_row = QHBoxLayout()
        self._summary_row.setSpacing(12)
        lay.addLayout(self._summary_row)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels(
            ["Date", "Category", "Description", "Amount (₹)", "Receipt", "Actions"]
        )
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        for c in [0, 1, 3, 4, 5]:
            self._table.horizontalHeader().setSectionResizeMode(
                c, QHeaderView.ResizeMode.ResizeToContents
            )
        self._table.setAlternatingRowColors(True)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        lay.addWidget(self._table, stretch=1)

    def refresh(self) -> None:
        projects = get_all_projects()
        self._proj_combo.clear()
        self._proj_combo.addItem("— Select Project —", None)
        for p in projects:
            self._proj_combo.addItem(f"{p['project_name']} ({p['client_name']})", p["id"])

    def _load_expenses(self) -> None:
        pid = self._proj_combo.currentData()
        if pid is None:
            self._table.setRowCount(0)
            return

        # Update summary cards
        while self._summary_row.count():
            item = self._summary_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        summary = get_expense_summary(pid)
        est = get_estimate(pid)
        est_total = est["grand_total"] if est else 0
        actual = summary["total"]
        variance = actual - est_total
        variance_color = "#e74c3c" if variance > 0 else "#27ae60"

        cards = [
            ("Estimated", fmt_inr(est_total), "#4a9eff"),
            ("Actual Spent", fmt_inr(actual), "#f0a500"),
            ("Variance", fmt_inr(abs(variance)), variance_color),
        ]
        for cat, val in summary["by_category"].items():
            cards.append((cat, fmt_inr(val), "#8b5cf6"))

        for label, val, color in cards:
            card = _SummaryCard(label, val, color)
            self._summary_row.addWidget(card)
        self._summary_row.addStretch()

        # Load expense rows
        expenses = get_expenses(pid)
        self._table.setRowCount(len(expenses))
        cat_colors = {
            "Material": "#4a9eff", "Labour": "#f0a500",
            "Equipment": "#8b5cf6", "Miscellaneous": "#9ca3af",
        }
        for row, exp in enumerate(expenses):
            cells = [
                fmt_date(exp["expense_date"]),
                exp["category"],
                exp["description"],
                fmt_inr(exp["amount"]),
                exp.get("receipt_ref") or "—",
            ]
            for col, val in enumerate(cells):
                cell = QTableWidgetItem(val)
                cell.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | (
                    Qt.AlignmentFlag.AlignRight if col == 3 else Qt.AlignmentFlag.AlignLeft
                ))
                if col == 1:
                    cell.setForeground(QColor(cat_colors.get(val, "#9ca3af")))
                self._table.setItem(row, col, cell)

            # Action buttons
            aw = QWidget()
            al = QHBoxLayout(aw)
            al.setContentsMargins(4, 2, 4, 2)
            al.setSpacing(4)
            edit_btn = QPushButton("Edit")
            edit_btn.setObjectName("btn_secondary")
            edit_btn.setFixedWidth(52)
            edit_btn.clicked.connect(lambda _, eid=exp["id"]: self._edit_expense(eid))
            del_btn = QPushButton("Del")
            del_btn.setObjectName("btn_danger")
            del_btn.setFixedWidth(46)
            del_btn.clicked.connect(lambda _, eid=exp["id"]: self._delete_expense(eid))
            al.addWidget(edit_btn)
            al.addWidget(del_btn)
            self._table.setCellWidget(row, 5, aw)

    def _add_expense(self) -> None:
        pid = self._proj_combo.currentData()
        if pid is None:
            QMessageBox.warning(self, "No Project", "Please select a project first.")
            return
        dlg = ExpenseDialog(self, project_id=pid)
        if dlg.exec():
            self._load_expenses()

    def _edit_expense(self, expense_id: int) -> None:
        dlg = ExpenseDialog(self, expense_id=expense_id)
        if dlg.exec():
            self._load_expenses()

    def _delete_expense(self, expense_id: int) -> None:
        reply = QMessageBox.question(self, "Confirm", "Delete this expense?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            delete_expense(expense_id)
            self._load_expenses()


class _SummaryCard(QFrame):
    def __init__(self, label: str, value: str, color: str):
        super().__init__()
        self.setObjectName("stat_card")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(2)
        v = QLabel(value)
        v.setStyleSheet(f"color:{color}; font-weight:700; font-size:14px;")
        v.setWordWrap(True)
        l = QLabel(label.upper())
        l.setObjectName("stat_label")
        l.setStyleSheet("font-size:10px;")
        lay.addWidget(v)
        lay.addWidget(l)
