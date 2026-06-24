"""Reports Page — generate professional PDF reports."""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QListWidget, QListWidgetItem, QFileDialog,
    QMessageBox, QGroupBox, QSizePolicy, QTextEdit, QFrame,
)
from PyQt6.QtCore import Qt

from app.models.project_model import get_all_projects


REPORT_TYPES = [
    ("Cost Estimate Report",     "cost_estimate"),
    ("BOQ Report",               "boq"),
    ("Project Summary Report",   "project_summary"),
    ("Expense Report",           "expense"),
    ("Variance Analysis Report", "variance"),
]


class ReportsPage(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(16)

        hdr = QLabel("Reports")
        hdr.setObjectName("section_title")
        sub = QLabel("Generate professional PDF reports for projects")
        sub.setObjectName("section_subtitle")
        lay.addWidget(hdr)
        lay.addWidget(sub)

        main_row = QHBoxLayout()
        main_row.setSpacing(24)

        # ── Left: config panel ───────────────────────────────────────────────
        left = QGroupBox("Report Configuration")
        left.setFixedWidth(320)
        left_lay = QVBoxLayout(left)
        left_lay.setContentsMargins(14, 14, 14, 14)
        left_lay.setSpacing(8)

        proj_lbl = QLabel("Project")
        proj_lbl.setObjectName("form_label")
        left_lay.addWidget(proj_lbl)

        self._proj_combo = QComboBox()
        self._proj_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._proj_combo.currentIndexChanged.connect(self._update_preview)
        left_lay.addWidget(self._proj_combo)

        left_lay.addSpacing(12)

        type_lbl = QLabel("Report Type")
        type_lbl.setObjectName("form_label")
        left_lay.addWidget(type_lbl)

        self._report_list = QListWidget()
        self._report_list.setSpacing(2)
        for label, key in REPORT_TYPES:
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, key)
            self._report_list.addItem(item)
        self._report_list.setCurrentRow(0)
        self._report_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._report_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._report_list.currentRowChanged.connect(self._update_preview)
        # 52px per item (padding from QSS: 10px top+bottom + font) × 5 items + 2px border
        self._report_list.setFixedHeight(52 * len(REPORT_TYPES) + 4)
        left_lay.addWidget(self._report_list)

        left_lay.addSpacing(12)

        gen_btn = QPushButton("Generate PDF Report")
        gen_btn.setMinimumHeight(40)
        gen_btn.setToolTip("Save report as PDF")
        gen_btn.clicked.connect(self._generate_report)
        left_lay.addWidget(gen_btn)

        left_lay.addStretch()
        main_row.addWidget(left)

        # ── Right: preview / info ────────────────────────────────────────────
        right = QGroupBox("Report Preview Info")
        right_lay = QVBoxLayout(right)
        right_lay.setContentsMargins(14, 14, 14, 14)
        self._preview_text = QTextEdit()
        self._preview_text.setReadOnly(True)
        self._preview_text.setPlaceholderText(
            "Select a project and report type, then click Generate."
        )
        right_lay.addWidget(self._preview_text)
        main_row.addWidget(right, stretch=1)

        lay.addLayout(main_row, stretch=1)

    def refresh(self) -> None:
        projects = get_all_projects()
        self._proj_combo.clear()
        self._proj_combo.addItem("— Select Project —", None)
        for p in projects:
            self._proj_combo.addItem(f"{p['project_name']} ({p['client_name']})", p["id"])

    def _update_preview(self) -> None:
        pid = self._proj_combo.currentData()
        item = self._report_list.currentItem()
        if pid is None or item is None:
            return
        self._preview_text.setPlainText(
            f"Ready to generate:\n\n"
            f"  Report Type : {item.text()}\n"
            f"  Project ID  : {pid}\n\n"
            f"Click 'Generate PDF Report' to save."
        )

    def _generate_report(self) -> None:
        pid = self._proj_combo.currentData()
        if pid is None:
            QMessageBox.warning(self, "No Project", "Please select a project.")
            return

        selected = self._report_list.currentItem()
        if not selected:
            return
        report_key = selected.data(Qt.ItemDataRole.UserRole)

        path, _ = QFileDialog.getSaveFileName(
            self, "Save Report", f"report_{report_key}.pdf", "PDF Files (*.pdf)"
        )
        if not path:
            return

        try:
            from app.controllers.report_controller import ReportController
            ctrl = ReportController()
            method = getattr(ctrl, f"generate_{report_key}_report", None)
            if method:
                method(pid, path)
                self._preview_text.setPlainText(
                    f"Report generated successfully!\n\n"
                    f"Saved to:\n{path}\n\n"
                    f"Project ID  : {pid}\n"
                    f"Report Type : {selected.text()}"
                )
                QMessageBox.information(self, "Success", f"Report saved:\n{path}")
            else:
                QMessageBox.warning(self, "Not Implemented", f"'{selected.text()}' is not yet available.")
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))
