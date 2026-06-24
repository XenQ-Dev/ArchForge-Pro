"""Timeline Page — 9-phase project progress tracker."""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QSizePolicy,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from app.models.project_model import get_all_projects
from app.models.timeline_model import get_phases, init_project_phases
from app.views.dialogs.phase_dialog import PhaseDialog


class TimelinePage(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(16)

        hdr = QLabel("Project Timeline")
        hdr.setObjectName("section_title")
        sub = QLabel("Track progress across 9 construction phases")
        sub.setObjectName("section_subtitle")
        lay.addWidget(hdr)
        lay.addWidget(sub)

        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("Project:"))
        self._proj_combo = QComboBox()
        self._proj_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._proj_combo.currentIndexChanged.connect(self._load_timeline)
        toolbar.addWidget(self._proj_combo, stretch=1)
        lay.addLayout(toolbar)

        # Overall progress
        prog_row = QHBoxLayout()
        prog_row.addWidget(QLabel("Overall Progress:"))
        self._overall_bar = QProgressBar()
        self._overall_bar.setRange(0, 100)
        self._overall_bar.setValue(0)
        self._overall_bar.setFormat("%p%")
        self._overall_bar.setFixedHeight(18)
        prog_row.addWidget(self._overall_bar, stretch=1)
        self._overall_lbl = QLabel("0%")
        self._overall_lbl.setStyleSheet("font-weight:700; color:#f0a500;")
        prog_row.addWidget(self._overall_lbl)
        lay.addLayout(prog_row)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(8)
        self._table.setHorizontalHeaderLabels([
            "#", "Phase", "Planned Start", "Planned End",
            "Actual Start", "Actual End", "Progress", "Status",
        ])
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for c in [0, 2, 3, 4, 5, 6, 7]:
            self._table.horizontalHeader().setSectionResizeMode(
                c, QHeaderView.ResizeMode.ResizeToContents
            )
        self._table.setAlternatingRowColors(True)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.doubleClicked.connect(self._edit_phase)
        lay.addWidget(self._table, stretch=1)

        hint = QLabel("Double-click a row to update phase progress.")
        hint.setObjectName("section_subtitle")
        lay.addWidget(hint)

    def refresh(self) -> None:
        projects = get_all_projects()
        self._proj_combo.clear()
        self._proj_combo.addItem("— Select Project —", None)
        for p in projects:
            self._proj_combo.addItem(f"{p['project_name']} ({p['client_name']})", p["id"])

    def _load_timeline(self) -> None:
        pid = self._proj_combo.currentData()
        if pid is None:
            self._table.setRowCount(0)
            return
        init_project_phases(pid)
        phases = get_phases(pid)
        self._table.setRowCount(len(phases))
        self._phase_ids = [p["id"] for p in phases]

        total_pct = 0.0
        status_colors = {
            "Pending": "#6b7280", "In Progress": "#f0a500",
            "Completed": "#27ae60", "Delayed": "#e74c3c",
        }

        for row, phase in enumerate(phases):
            vals = [
                str(phase["phase_order"]),
                phase["phase_name"],
                phase.get("planned_start") or "—",
                phase.get("planned_end") or "—",
                phase.get("actual_start") or "—",
                phase.get("actual_end") or "—",
            ]
            for col, val in enumerate(vals):
                cell = QTableWidgetItem(val)
                cell.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                self._table.setItem(row, col, cell)

            # Progress bar in cell
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(int(phase["completion_pct"]))
            bar.setFormat(f"{int(phase['completion_pct'])}%")
            bar.setFixedHeight(16)
            self._table.setCellWidget(row, 6, bar)

            # Status
            status_item = QTableWidgetItem(phase["status"])
            status_item.setForeground(QColor(status_colors.get(phase["status"], "#9ca3af")))
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 7, status_item)

            total_pct += phase["completion_pct"]

        avg_pct = total_pct / len(phases) if phases else 0
        self._overall_bar.setValue(int(avg_pct))
        self._overall_lbl.setText(f"{avg_pct:.1f}%")

    def _edit_phase(self, index) -> None:
        row = index.row()
        if not hasattr(self, "_phase_ids") or row >= len(self._phase_ids):
            return
        phase_id = self._phase_ids[row]
        dlg = PhaseDialog(self, phase_id=phase_id)
        if dlg.exec():
            self._load_timeline()
