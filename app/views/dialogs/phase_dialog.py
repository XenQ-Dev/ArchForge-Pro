"""Edit Phase dialog."""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QFormLayout,
    QGroupBox, QDoubleSpinBox, QComboBox, QDateEdit, QLineEdit, QMessageBox,
)
from PyQt6.QtCore import QDate

from app.models.timeline_model import update_phase
from app.models.database import get_connection


class PhaseDialog(QDialog):
    def __init__(self, parent=None, phase_id: int | None = None):
        super().__init__(parent)
        self._phase_id = phase_id
        self.setWindowTitle("Update Phase Progress")
        self.setMinimumWidth(400)
        self._build_ui()
        if phase_id:
            self._load_phase()

    def _build_ui(self) -> None:
        lay = QVBoxLayout(self)

        group = QGroupBox("Phase Details")
        form = QFormLayout(group)
        form.setSpacing(10)

        self._planned_start = QDateEdit()
        self._planned_start.setCalendarPopup(True)
        self._planned_start.setDisplayFormat("dd-MM-yyyy")
        self._planned_start.setSpecialValueText("Not set")
        form.addRow("Planned Start:", self._planned_start)

        self._planned_end = QDateEdit()
        self._planned_end.setCalendarPopup(True)
        self._planned_end.setDisplayFormat("dd-MM-yyyy")
        form.addRow("Planned End:", self._planned_end)

        self._actual_start = QDateEdit()
        self._actual_start.setCalendarPopup(True)
        self._actual_start.setDisplayFormat("dd-MM-yyyy")
        form.addRow("Actual Start:", self._actual_start)

        self._actual_end = QDateEdit()
        self._actual_end.setCalendarPopup(True)
        self._actual_end.setDisplayFormat("dd-MM-yyyy")
        form.addRow("Actual End:", self._actual_end)

        self._completion = QDoubleSpinBox()
        self._completion.setRange(0, 100)
        self._completion.setSuffix(" %")
        self._completion.setSingleStep(5)
        form.addRow("Completion %:", self._completion)

        self._status = QComboBox()
        self._status.addItems(["Pending", "In Progress", "Completed", "Delayed"])
        form.addRow("Status:", self._status)

        self._notes = QLineEdit()
        form.addRow("Notes:", self._notes)

        lay.addWidget(group)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("btn_secondary")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Update Phase")
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        lay.addLayout(btn_row)

    def _load_phase(self) -> None:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM project_phases WHERE id=?", (self._phase_id,)
            ).fetchone()
        if not row:
            return
        r = dict(row)

        def _set_date(widget: QDateEdit, val) -> None:
            if val:
                d = QDate.fromString(val, "yyyy-MM-dd")
                if d.isValid():
                    widget.setDate(d)
                    return
            widget.setDate(QDate.currentDate())

        _set_date(self._planned_start, r.get("planned_start"))
        _set_date(self._planned_end, r.get("planned_end"))
        _set_date(self._actual_start, r.get("actual_start"))
        _set_date(self._actual_end, r.get("actual_end"))
        self._completion.setValue(r.get("completion_pct", 0))
        self._status.setCurrentText(r.get("status", "Pending"))
        self._notes.setText(r.get("notes") or "")

    def _save(self) -> None:
        data = {
            "planned_start": self._planned_start.date().toString("yyyy-MM-dd"),
            "planned_end": self._planned_end.date().toString("yyyy-MM-dd"),
            "actual_start": self._actual_start.date().toString("yyyy-MM-dd"),
            "actual_end": self._actual_end.date().toString("yyyy-MM-dd"),
            "completion_pct": self._completion.value(),
            "status": self._status.currentText(),
            "notes": self._notes.text().strip(),
        }
        update_phase(self._phase_id, data)
        self.accept()
