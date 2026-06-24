"""Dashboard Page v3 — brutalist terminal aesthetic."""
from __future__ import annotations
from datetime import date

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QScrollArea, QSizePolicy,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont

from app.models.project_model import get_dashboard_stats, get_all_projects
from app.models.estimate_model import get_estimate
from app.utils.chart_widget import ChartWidget
from app.utils.formatters import fmt_inr


class _StatCard(QFrame):
    """Sharp-cornered stat card with hover border inversion."""

    def __init__(self, label: str, value: str, dim_label: str = ""):
        super().__init__()
        self.setObjectName("stat_card")
        self.setCursor(Qt.CursorShape.ArrowCursor)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(4)

        if dim_label:
            dim = QLabel(dim_label)
            dim.setObjectName("dim_label")
            lay.addWidget(dim)

        val_lbl = QLabel(value)
        val_lbl.setObjectName("stat_value")
        val_lbl.setWordWrap(True)
        lay.addWidget(val_lbl)

        lbl = QLabel(label)
        lbl.setObjectName("stat_label")
        lay.addWidget(lbl)

        # Bottom thin line
        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet("background:#1e1e1e; margin-top:6px;")
        lay.addWidget(line)


class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setMouseTracking(True)
        self._build_ui()

    def _build_ui(self) -> None:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        content.setStyleSheet("background:transparent;")
        self._lay = QVBoxLayout(content)
        self._lay.setContentsMargins(32, 32, 32, 32)
        self._lay.setSpacing(28)

        # ── Header ──────────────────────────────────────────────────────────
        hdr_row = QHBoxLayout()

        left = QVBoxLayout()
        left.setSpacing(4)
        title = QLabel("// DASHBOARD")
        title.setObjectName("section_title")
        sub = QLabel(
            f"CONSTRUCTION OVERVIEW  ·  {date.today().strftime('%d.%m.%Y')}"
        )
        sub.setObjectName("section_subtitle")
        left.addWidget(title)
        left.addWidget(sub)
        hdr_row.addLayout(left)
        hdr_row.addStretch()

        coord = QLabel("LAT: 18.5204°  ·  LNG: 73.8567°")
        coord.setObjectName("dim_label")
        hdr_row.addWidget(coord)
        self._lay.addLayout(hdr_row)

        # thin full-width separator
        self._lay.addWidget(_HSep())

        # ── KPI cards ────────────────────────────────────────────────────────
        self._cards_row = QHBoxLayout()
        self._cards_row.setSpacing(12)
        self._lay.addLayout(self._cards_row)

        self._lay.addWidget(_HSep())

        # ── Charts ───────────────────────────────────────────────────────────
        charts_label = QLabel("// ANALYTICS")
        charts_label.setObjectName("section_divider")
        self._lay.addWidget(charts_label)

        self._charts_row = QHBoxLayout()
        self._charts_row.setSpacing(12)
        self._lay.addLayout(self._charts_row)

        self._lay.addWidget(_HSep())

        # ── Recent projects ──────────────────────────────────────────────────
        tbl_hdr = QHBoxLayout()
        tbl_title = QLabel("// RECENT PROJECTS")
        tbl_title.setObjectName("section_divider")
        tbl_hdr.addWidget(tbl_title)
        tbl_hdr.addStretch()
        badge = QLabel("LAST 10 RECORDS")
        badge.setObjectName("sidebar_meta")
        tbl_hdr.addWidget(badge)
        self._lay.addLayout(tbl_hdr)

        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels([
            "PROJECT NAME", "CLIENT", "TYPE",
            "STATUS", "ESTIMATED COST", "LOCATION",
        ])
        self._table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self._table.setAlternatingRowColors(True)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.verticalHeader().setVisible(False)
        self._table.setMinimumHeight(240)
        self._table.setShowGrid(False)
        self._lay.addWidget(self._table)

        scroll.setWidget(content)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def refresh(self) -> None:
        self._populate()

    def _populate(self) -> None:
        stats = get_dashboard_stats()
        projects = get_all_projects()

        _clear(self._cards_row)
        _clear(self._charts_row)

        variance = stats["cost_variance"]
        v_sign = "+" if variance > 0 else ""

        cards = [
            ("TOTAL PROJECTS",    str(stats["total_projects"]),       "[TP]"),
            ("ACTIVE",            str(stats["active_projects"]),      "[AC]"),
            ("COMPLETED",         str(stats["completed_projects"]),   "[CP]"),
            ("EST. TOTAL",        fmt_inr(stats["total_estimated"]),  "[ET]"),
            ("ACTUAL SPENT",      fmt_inr(stats["total_actual"]),     "[AS]"),
            ("VARIANCE",          f"{v_sign}{fmt_inr(abs(variance))}", "[CV]"),
        ]
        for label, value, dim in cards:
            self._cards_row.addWidget(_StatCard(label, value, dim))

        # Charts
        status_counts: dict = {}
        for p in projects:
            status_counts[p["status"]] = status_counts.get(p["status"], 0) + 1
        if status_counts:
            self._charts_row.addWidget(
                ChartWidget.pie_chart("PROJECT STATUS", list(status_counts.keys()),
                                      list(status_counts.values()))
            )

        if stats["total_estimated"] or stats["total_actual"]:
            self._charts_row.addWidget(
                ChartWidget.bar_chart(
                    "COST OVERVIEW",
                    ["ESTIMATED", "ACTUAL"],
                    [stats["total_estimated"], stats["total_actual"]],
                    color=["#00d4ff", "#ff6b35"],
                )
            )

        type_counts: dict = {}
        for p in projects:
            type_counts[p["project_type"]] = type_counts.get(p["project_type"], 0) + 1
        if type_counts:
            self._charts_row.addWidget(
                ChartWidget.pie_chart("PROJECT TYPES", list(type_counts.keys()),
                                      list(type_counts.values()))
            )

        # Table
        recent = projects[:10]
        self._table.setRowCount(len(recent))
        STATUS_COL = {
            "Active":    "#00d4ff",
            "Completed": "#22d3a5",
            "On Hold":   "#fbbf24",
            "Cancelled": "#ff6b35",
        }
        mono = QFont("Courier New", 10)
        for row, p in enumerate(recent):
            est = get_estimate(p["id"])
            est_val = est["grand_total"] if est else 0
            cells = [
                p["project_name"], p["client_name"], p["project_type"],
                p["status"], fmt_inr(est_val), p["site_location"],
            ]
            for col, val in enumerate(cells):
                item = QTableWidgetItem(val.upper() if col != 4 else val)
                item.setFont(mono)
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
                )
                if col == 3:
                    item.setForeground(QColor(STATUS_COL.get(val, "#444444")))
                self._table.setItem(row, col, item)
            self._table.setRowHeight(row, 38)


class _HSep(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.Shape.HLine)
        self.setFixedHeight(1)
        self.setStyleSheet("background:#111111;")


def _clear(layout: QHBoxLayout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        if item.widget():
            item.widget().deleteLater()
