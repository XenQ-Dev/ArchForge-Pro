"""Cost Estimator Page — select project → run engine → view breakdown."""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QDoubleSpinBox, QGroupBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QFrame, QScrollArea,
    QFormLayout, QSplitter, QSizePolicy, QMessageBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut

from app.models.project_model import get_all_projects, get_project
from app.models.estimate_model import save_estimate, get_estimate
from app.controllers.estimation_engine import EstimationEngine
from app.utils.formatters import fmt_inr


class EstimatorPage(QWidget):
    def __init__(self):
        super().__init__()
        self._current_estimate: dict | None = None
        self._build_ui()
        QShortcut(QKeySequence("Ctrl+Return"), self).activated.connect(self._run_estimation)
        QShortcut(QKeySequence("Ctrl+S"), self).activated.connect(self._save_estimate)

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(16)

        hdr = QLabel("Cost Estimator")
        hdr.setObjectName("section_title")
        sub = QLabel("Rule-based cost estimation  ·  Ctrl+Enter to calculate  ·  Ctrl+S to save")
        sub.setObjectName("section_subtitle")
        outer.addWidget(hdr)
        outer.addWidget(sub)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(2)

        # ── Left: Controls ──────────────────────────────────────────────────
        left = QWidget()
        left.setFixedWidth(320)
        left_lay = QVBoxLayout(left)
        left_lay.setContentsMargins(0, 4, 16, 0)
        left_lay.setSpacing(16)

        # Project selector
        proj_group = QGroupBox("Select Project")
        proj_vlay = QVBoxLayout(proj_group)
        proj_vlay.setContentsMargins(10, 10, 10, 10)
        proj_vlay.setSpacing(8)

        self._proj_combo = QComboBox()
        self._proj_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._proj_combo.currentIndexChanged.connect(self._on_project_changed)
        proj_vlay.addWidget(self._proj_combo)

        # Project info grid
        self._info_type    = QLabel("—")
        self._info_area    = QLabel("—")
        self._info_floors  = QLabel("—")
        self._info_quality = QLabel("—")

        for lbl_text, val_lbl in [
            ("Type",         self._info_type),
            ("Built-up Area",self._info_area),
            ("Floors",       self._info_floors),
            ("Quality",      self._info_quality),
        ]:
            row = QHBoxLayout()
            row.setSpacing(6)
            lbl = QLabel(f"{lbl_text}:")
            lbl.setObjectName("form_label")
            lbl.setFixedWidth(100)
            lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            val_lbl.setObjectName("form_label")
            row.addWidget(lbl)
            row.addWidget(val_lbl)
            row.addStretch()
            proj_vlay.addLayout(row)

        left_lay.addWidget(proj_group)

        # Parameters group
        param_group = QGroupBox("Estimation Parameters")
        param_form = QFormLayout(param_group)
        param_form.setContentsMargins(8, 12, 8, 8)
        param_form.setSpacing(12)
        param_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._labour_spin = QDoubleSpinBox()
        self._labour_spin.setRange(5, 60)
        self._labour_spin.setValue(25.0)
        self._labour_spin.setSuffix(" %")
        self._labour_spin.setMinimumWidth(120)
        param_form.addRow("Labour Cost %:", self._labour_spin)

        self._equip_spin = QDoubleSpinBox()
        self._equip_spin.setRange(1, 20)
        self._equip_spin.setValue(5.0)
        self._equip_spin.setSuffix(" %")
        self._equip_spin.setMinimumWidth(120)
        param_form.addRow("Equipment Cost %:", self._equip_spin)

        self._margin_spin = QDoubleSpinBox()
        self._margin_spin.setRange(0, 30)
        self._margin_spin.setValue(10.0)
        self._margin_spin.setSuffix(" %")
        self._margin_spin.setMinimumWidth(120)
        param_form.addRow("Contractor Margin %:", self._margin_spin)

        self._gst_spin = QDoubleSpinBox()
        self._gst_spin.setRange(0, 28)
        self._gst_spin.setValue(18.0)
        self._gst_spin.setSuffix(" %")
        self._gst_spin.setMinimumWidth(120)
        param_form.addRow("GST %:", self._gst_spin)

        left_lay.addWidget(param_group)

        calc_btn = QPushButton("Calculate Estimate")
        calc_btn.setToolTip("Run estimation engine  [Ctrl+Enter]")
        calc_btn.setMinimumHeight(40)
        calc_btn.clicked.connect(self._run_estimation)
        left_lay.addWidget(calc_btn)

        save_btn = QPushButton("Save Estimate")
        save_btn.setObjectName("btn_success")
        save_btn.setToolTip("Save to database  [Ctrl+S]")
        save_btn.setMinimumHeight(40)
        save_btn.clicked.connect(self._save_estimate)
        left_lay.addWidget(save_btn)

        left_lay.addStretch()
        splitter.addWidget(left)

        # ── Right: Results ──────────────────────────────────────────────────
        right = QWidget()
        right_lay = QVBoxLayout(right)
        right_lay.setContentsMargins(32, 4, 0, 0)
        right_lay.setSpacing(14)

        # Summary cards row
        self._summary_row = QHBoxLayout()
        self._summary_row.setSpacing(12)
        right_lay.addLayout(self._summary_row)

        # Items table
        items_lbl = QLabel("Material Quantity Breakdown")
        items_lbl.setObjectName("section_title")
        items_lbl.setStyleSheet("font-size:15px; letter-spacing:3px;")
        right_lay.addWidget(items_lbl)

        self._items_table = QTableWidget()
        self._items_table.setColumnCount(5)
        self._items_table.setHorizontalHeaderLabels(
            ["Item", "Quantity", "Unit", "Rate (₹)", "Amount (₹)"]
        )
        self._items_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        for c in range(1, 5):
            self._items_table.horizontalHeader().setSectionResizeMode(
                c, QHeaderView.ResizeMode.ResizeToContents
            )
        self._items_table.setAlternatingRowColors(True)
        self._items_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._items_table.verticalHeader().setVisible(False)
        right_lay.addWidget(self._items_table, stretch=1)

        splitter.addWidget(right)
        splitter.setSizes([340, 800])
        outer.addWidget(splitter, stretch=1)

    def refresh(self) -> None:
        self._load_projects()

    def _load_projects(self) -> None:
        projects = get_all_projects()
        self._proj_combo.clear()
        self._proj_combo.addItem("— Select Project —", None)
        for p in projects:
            self._proj_combo.addItem(f"{p['project_name']} ({p['client_name']})", p["id"])

    def _on_project_changed(self, index: int) -> None:
        # always reset so stale data from a previous project is never saved
        self._current_estimate = None
        pid = self._proj_combo.currentData()
        if pid is None:
            return
        p = get_project(pid)
        if p:
            self._info_type.setText(p["project_type"])
            self._info_area.setText(f"{p['built_up_area']:,.0f} sq.ft")
            self._info_floors.setText(str(p["num_floors"]))
            self._info_quality.setText(p["construction_quality"])
        # Load existing estimate if present
        est = get_estimate(pid)
        if est:
            self._labour_spin.setValue(est.get("labour_pct", 25.0))
            self._equip_spin.setValue(est.get("equipment_pct", 5.0))
            self._margin_spin.setValue(est.get("contractor_pct", 10.0))
            self._gst_spin.setValue(est.get("gst_pct", 18.0))
            self._current_estimate = est
            self._populate_results(est)

    def _run_estimation(self) -> None:
        pid = self._proj_combo.currentData()
        if pid is None:
            return
        p = get_project(pid)
        if not p:
            return

        engine = EstimationEngine()
        result = engine.estimate(
            built_up_area=p["built_up_area"],
            num_floors=p["num_floors"],
            quality=p["construction_quality"],
            project_type=p["project_type"],
            labour_pct=self._labour_spin.value(),
            equipment_pct=self._equip_spin.value(),
            contractor_pct=self._margin_spin.value(),
            gst_pct=self._gst_spin.value(),
        )
        self._current_estimate = result
        self._populate_results(result)

    def _save_estimate(self) -> None:
        pid = self._proj_combo.currentData()
        if pid is None:
            QMessageBox.warning(self, "No Project", "Please select a project first.")
            return
        if self._current_estimate is None:
            QMessageBox.warning(self, "No Estimate", "Run the estimator first, then save.")
            return
        est = self._current_estimate
        summary = {
            "material_cost":    est["material_cost"],
            "labour_cost":      est["labour_cost"],
            "equipment_cost":   est["equipment_cost"],
            "contractor_margin": est["contractor_margin"],
            "gst_amount":       est["gst_amount"],
            "grand_total":      est["grand_total"],
            "labour_pct":       self._labour_spin.value(),
            "equipment_pct":    self._equip_spin.value(),
            "contractor_pct":   self._margin_spin.value(),
            "gst_pct":          self._gst_spin.value(),
        }
        try:
            save_estimate(pid, summary, est.get("items", []))
            # update in-memory estimate with saved percentages so re-save is consistent
            self._current_estimate.update(summary)
            QMessageBox.information(
                self, "Saved",
                f"Estimate saved successfully.\nGrand Total: {est['grand_total']:,.2f} ₹"
            )
        except Exception as exc:
            QMessageBox.critical(self, "Save Failed", f"Could not save estimate:\n{exc}")

    def _populate_results(self, est: dict) -> None:
        # Clear and rebuild summary cards
        while self._summary_row.count():
            item = self._summary_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        totals = [
            ("Material",  est["material_cost"],    "#4a9eff"),
            ("Labour",    est["labour_cost"],       "#f0a500"),
            ("Equipment", est["equipment_cost"],    "#8b5cf6"),
            ("Margin",    est["contractor_margin"], "#06b6d4"),
            ("GST",       est["gst_amount"],        "#e74c3c"),
            ("GRAND TOTAL", est["grand_total"],     "#27ae60"),
        ]
        for label, val, color in totals:
            card = _MiniCard(label, fmt_inr(val), color)
            self._summary_row.addWidget(card)

        # Items table
        items = est.get("items", [])
        self._items_table.setRowCount(len(items))
        for row, item in enumerate(items):
            vals = [
                item.get("item_name", ""),
                f"{item.get('quantity', 0):,.2f}",
                item.get("unit", ""),
                fmt_inr(item.get("rate", 0)),
                fmt_inr(item.get("amount", 0)),
            ]
            for col, val in enumerate(vals):
                cell = QTableWidgetItem(val)
                align = Qt.AlignmentFlag.AlignVCenter
                if col == 0:
                    align |= Qt.AlignmentFlag.AlignLeft
                else:
                    align |= Qt.AlignmentFlag.AlignRight
                cell.setTextAlignment(align)
                self._items_table.setItem(row, col, cell)


class _MiniCard(QFrame):
    def __init__(self, label: str, value: str, color: str):
        super().__init__()
        self.setObjectName("stat_card")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(2)
        v = QLabel(value)
        v.setStyleSheet(f"color:{color}; font-weight:700; font-size:13px;")
        v.setWordWrap(True)
        l = QLabel(label.upper())
        l.setObjectName("stat_label")
        l.setStyleSheet("font-size:10px;")
        lay.addWidget(v)
        lay.addWidget(l)
