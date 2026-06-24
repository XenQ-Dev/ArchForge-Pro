"""BOQ (Bill of Quantities) Page."""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QFileDialog, QSizePolicy,
)
from PyQt6.QtCore import Qt

from app.models.project_model import get_all_projects
from app.models.estimate_model import get_estimate
from app.models.boq_model import save_boq, get_boq
from app.controllers.boq_controller import BOQController
from app.utils.formatters import fmt_inr


class BOQPage(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(16)

        hdr = QLabel("Bill of Quantities")
        hdr.setObjectName("section_title")
        sub = QLabel("Generate and export BOQ for any project")
        sub.setObjectName("section_subtitle")
        lay.addWidget(hdr)
        lay.addWidget(sub)

        # Toolbar
        toolbar = QHBoxLayout()
        self._proj_combo = QComboBox()
        self._proj_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._proj_combo.currentIndexChanged.connect(self._load_boq)
        toolbar.addWidget(QLabel("Project:"))
        toolbar.addWidget(self._proj_combo, stretch=1)

        gen_btn = QPushButton("Generate BOQ")
        gen_btn.clicked.connect(self._generate_boq)
        toolbar.addWidget(gen_btn)

        pdf_btn = QPushButton("Export PDF")
        pdf_btn.setObjectName("btn_secondary")
        pdf_btn.clicked.connect(self._export_pdf)
        toolbar.addWidget(pdf_btn)

        xls_btn = QPushButton("Export Excel")
        xls_btn.setObjectName("btn_secondary")
        xls_btn.clicked.connect(self._export_excel)
        toolbar.addWidget(xls_btn)

        lay.addLayout(toolbar)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels(
            ["#", "Description", "Qty", "Unit", "Rate (₹)", "Amount (₹)"]
        )
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for c in [0, 2, 3, 4, 5]:
            self._table.horizontalHeader().setSectionResizeMode(
                c, QHeaderView.ResizeMode.ResizeToContents
            )
        self._table.setAlternatingRowColors(True)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        lay.addWidget(self._table, stretch=1)

        # Total row
        total_row = QHBoxLayout()
        total_row.addStretch()
        self._total_lbl = QLabel("Total: ₹0.00")
        self._total_lbl.setStyleSheet("font-size:16px; font-weight:700; color:#f0a500;")
        total_row.addWidget(self._total_lbl)
        lay.addLayout(total_row)

    def refresh(self) -> None:
        projects = get_all_projects()
        self._proj_combo.clear()
        self._proj_combo.addItem("— Select Project —", None)
        for p in projects:
            self._proj_combo.addItem(f"{p['project_name']} ({p['client_name']})", p["id"])

    def _load_boq(self) -> None:
        pid = self._proj_combo.currentData()
        if pid is None:
            self._table.setRowCount(0)
            return
        rows = get_boq(pid)
        self._populate_table(rows)

    def _generate_boq(self) -> None:
        pid = self._proj_combo.currentData()
        if pid is None:
            QMessageBox.warning(self, "No Project", "Please select a project.")
            return
        est = get_estimate(pid)
        if not est:
            QMessageBox.warning(
                self, "No Estimate",
                "No saved estimate found for this project.\n\n"
                "Go to Cost Estimator → select this project → Calculate → Save Estimate."
            )
            return
        try:
            ctrl = BOQController()
            items = ctrl.generate_from_estimate(est)
            save_boq(pid, items)
            self._populate_table(items)
            QMessageBox.information(self, "BOQ Generated", f"BOQ generated with {len(items)} line items.")
        except Exception as exc:
            QMessageBox.critical(self, "BOQ Failed", f"Could not generate BOQ:\n{exc}")

    def _populate_table(self, rows: list[dict]) -> None:
        self._table.setRowCount(len(rows))
        total = 0.0
        for row, item in enumerate(rows):
            vals = [
                str(item.get("item_no", row + 1)),
                item.get("description", ""),
                f"{item.get('quantity', 0):,.2f}",
                item.get("unit", ""),
                fmt_inr(item.get("rate", 0)),
                fmt_inr(item.get("amount", 0)),
            ]
            for col, val in enumerate(vals):
                cell = QTableWidgetItem(val)
                align = Qt.AlignmentFlag.AlignVCenter
                cell.setTextAlignment(align | (Qt.AlignmentFlag.AlignRight if col in [2, 4, 5] else Qt.AlignmentFlag.AlignLeft))
                self._table.setItem(row, col, cell)
            total += item.get("amount", 0)
        self._total_lbl.setText(f"Total: {fmt_inr(total)}")

    def _export_pdf(self) -> None:
        pid = self._proj_combo.currentData()
        if pid is None:
            return
        from app.controllers.report_controller import ReportController
        path, _ = QFileDialog.getSaveFileName(self, "Save BOQ PDF", "", "PDF Files (*.pdf)")
        if path:
            ctrl = ReportController()
            ctrl.export_boq_pdf(pid, path)
            QMessageBox.information(self, "Exported", f"BOQ PDF saved to:\n{path}")

    def _export_excel(self) -> None:
        pid = self._proj_combo.currentData()
        if pid is None:
            return
        from app.controllers.report_controller import ReportController
        path, _ = QFileDialog.getSaveFileName(self, "Save BOQ Excel", "", "Excel Files (*.xlsx)")
        if path:
            ctrl = ReportController()
            ctrl.export_boq_excel(pid, path)
            QMessageBox.information(self, "Exported", f"BOQ Excel saved to:\n{path}")
