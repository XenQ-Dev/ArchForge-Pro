"""Add / Edit Expense dialog."""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QFormLayout,
    QGroupBox, QLineEdit, QDoubleSpinBox, QComboBox, QDateEdit, QMessageBox,
)
from PyQt6.QtCore import QDate

from app.models.expense_model import add_expense, update_expense
from app.models.database import get_connection


class ExpenseDialog(QDialog):
    def __init__(self, parent=None, project_id: int | None = None, expense_id: int | None = None):
        super().__init__(parent)
        self._project_id = project_id
        self._expense_id = expense_id
        self.setWindowTitle("Edit Expense" if expense_id else "Add Expense")
        self.setMinimumWidth(420)
        self._build_ui()
        if expense_id:
            self._load_expense()

    def _build_ui(self) -> None:
        lay = QVBoxLayout(self)

        group = QGroupBox("Expense Details")
        form = QFormLayout(group)
        form.setSpacing(10)

        self._date = QDateEdit()
        self._date.setCalendarPopup(True)
        self._date.setDate(QDate.currentDate())
        self._date.setDisplayFormat("dd-MM-yyyy")
        form.addRow("Date *:", self._date)

        self._category = QComboBox()
        self._category.addItems(["Material", "Labour", "Equipment", "Miscellaneous"])
        form.addRow("Category *:", self._category)

        self._desc = QLineEdit()
        self._desc.setPlaceholderText("Brief description of the expense")
        form.addRow("Description *:", self._desc)

        self._amount = QDoubleSpinBox()
        self._amount.setRange(0, 999999999)
        self._amount.setPrefix("₹ ")
        self._amount.setDecimals(2)
        self._amount.setSingleStep(1000)
        form.addRow("Amount (₹) *:", self._amount)

        self._receipt = QLineEdit()
        self._receipt.setPlaceholderText("Optional receipt/voucher reference")
        form.addRow("Receipt Ref:", self._receipt)

        lay.addWidget(group)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("btn_secondary")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Save Expense")
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        lay.addLayout(btn_row)

    def _load_expense(self) -> None:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM expenses WHERE id=?", (self._expense_id,)
            ).fetchone()
        if not row:
            return
        r = dict(row)
        self._date.setDate(QDate.fromString(r["expense_date"], "yyyy-MM-dd"))
        self._category.setCurrentText(r["category"])
        self._desc.setText(r["description"])
        self._amount.setValue(r["amount"])
        self._receipt.setText(r.get("receipt_ref") or "")
        self._project_id = r["project_id"]

    def _save(self) -> None:
        if not self._desc.text().strip():
            QMessageBox.warning(self, "Validation", "Description is required.")
            return
        if self._amount.value() <= 0:
            QMessageBox.warning(self, "Validation", "Amount must be greater than 0.")
            return

        data = {
            "project_id": self._project_id,
            "expense_date": self._date.date().toString("yyyy-MM-dd"),
            "category": self._category.currentText(),
            "description": self._desc.text().strip(),
            "amount": self._amount.value(),
            "receipt_ref": self._receipt.text().strip() or None,
        }
        if self._expense_id:
            update_expense(self._expense_id, data)
        else:
            add_expense(data)
        self.accept()
