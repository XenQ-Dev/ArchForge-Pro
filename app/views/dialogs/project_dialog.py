"""Add / Edit Project dialog."""
from __future__ import annotations
from datetime import date

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox,
    QDateEdit, QTextEdit, QFormLayout, QGroupBox, QMessageBox,
)
from PyQt6.QtCore import QDate

from app.models.project_model import create_project, update_project, get_project
from app.models.timeline_model import init_project_phases


class ProjectDialog(QDialog):
    def __init__(self, parent=None, project_id: int | None = None):
        super().__init__(parent)
        self._project_id = project_id
        self.setWindowTitle("Edit Project" if project_id else "New Project")
        self.setMinimumWidth(520)
        self._build_ui()
        if project_id:
            self._load_project(project_id)

    def _build_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setSpacing(16)

        form_group = QGroupBox("Project Details")
        form = QFormLayout(form_group)
        form.setSpacing(10)

        self._name = QLineEdit()
        self._name.setPlaceholderText("e.g. Sharma Residence")
        form.addRow("Project Name *:", self._name)

        self._client = QLineEdit()
        self._client.setPlaceholderText("e.g. Mr. Rajesh Sharma")
        form.addRow("Client Name *:", self._client)

        self._location = QLineEdit()
        self._location.setPlaceholderText("e.g. Pune, Maharashtra")
        form.addRow("Site Location *:", self._location)

        self._type = QComboBox()
        self._type.addItems(["Residential", "Commercial", "Industrial"])
        form.addRow("Project Type *:", self._type)

        self._plot_area = QDoubleSpinBox()
        self._plot_area.setRange(100, 1000000)
        self._plot_area.setValue(2000)
        self._plot_area.setSuffix(" sq.ft")
        self._plot_area.setSingleStep(100)
        form.addRow("Plot Area *:", self._plot_area)

        self._bua = QDoubleSpinBox()
        self._bua.setRange(100, 800000)
        self._bua.setValue(1500)
        self._bua.setSuffix(" sq.ft")
        self._bua.setSingleStep(100)
        form.addRow("Built-up Area *:", self._bua)

        self._floors = QSpinBox()
        self._floors.setRange(1, 50)
        self._floors.setValue(2)
        form.addRow("Number of Floors *:", self._floors)

        self._quality = QComboBox()
        self._quality.addItems(["Standard", "Premium", "Luxury"])
        form.addRow("Construction Quality *:", self._quality)

        self._start = QDateEdit()
        self._start.setCalendarPopup(True)
        self._start.setDate(QDate.currentDate())
        self._start.setDisplayFormat("dd-MM-yyyy")
        form.addRow("Start Date *:", self._start)

        self._completion = QDateEdit()
        self._completion.setCalendarPopup(True)
        self._completion.setDate(QDate.currentDate().addMonths(12))
        self._completion.setDisplayFormat("dd-MM-yyyy")
        form.addRow("Expected Completion *:", self._completion)

        self._status = QComboBox()
        self._status.addItems(["Active", "Completed", "On Hold", "Cancelled"])
        form.addRow("Status:", self._status)

        self._notes = QTextEdit()
        self._notes.setMaximumHeight(80)
        self._notes.setPlaceholderText("Optional notes…")
        form.addRow("Notes:", self._notes)

        lay.addWidget(form_group)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("btn_secondary")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Save Project")
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        lay.addLayout(btn_row)

    def _load_project(self, pid: int) -> None:
        p = get_project(pid)
        if not p:
            return
        self._name.setText(p["project_name"])
        self._client.setText(p["client_name"])
        self._location.setText(p["site_location"])
        self._type.setCurrentText(p["project_type"])
        self._plot_area.setValue(p["plot_area"])
        self._bua.setValue(p["built_up_area"])
        self._floors.setValue(p["num_floors"])
        self._quality.setCurrentText(p["construction_quality"])
        self._start.setDate(QDate.fromString(p["start_date"], "yyyy-MM-dd"))
        self._completion.setDate(QDate.fromString(p["expected_completion"], "yyyy-MM-dd"))
        self._status.setCurrentText(p["status"])
        self._notes.setPlainText(p.get("notes") or "")

    def _save(self) -> None:
        if not self._name.text().strip():
            QMessageBox.warning(self, "Validation", "Project Name is required.")
            return
        if not self._client.text().strip():
            QMessageBox.warning(self, "Validation", "Client Name is required.")
            return

        data = {
            "project_name": self._name.text().strip(),
            "client_name": self._client.text().strip(),
            "site_location": self._location.text().strip() or "—",
            "project_type": self._type.currentText(),
            "plot_area": self._plot_area.value(),
            "built_up_area": self._bua.value(),
            "num_floors": self._floors.value(),
            "construction_quality": self._quality.currentText(),
            "start_date": self._start.date().toString("yyyy-MM-dd"),
            "expected_completion": self._completion.date().toString("yyyy-MM-dd"),
            "status": self._status.currentText(),
            "notes": self._notes.toPlainText().strip(),
        }
        if self._project_id:
            update_project(self._project_id, data)
        else:
            new_id = create_project(data)
            init_project_phases(new_id)
        self.accept()
