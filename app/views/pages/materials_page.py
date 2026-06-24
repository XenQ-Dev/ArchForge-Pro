"""Material Rate Database Page — view and update material rates."""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QLineEdit, QMessageBox, QSizePolicy,
)
from PyQt6.QtCore import Qt

from app.models.material_model import (
    get_all_categories, get_all_materials, update_material_rate,
    search_materials, delete_material,
)
from app.utils.formatters import fmt_inr, fmt_date
from app.views.dialogs.material_dialog import MaterialDialog


class MaterialsPage(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(16)

        hdr = QLabel("Material Rate Database")
        hdr.setObjectName("section_title")
        sub = QLabel("Indian construction material rates in INR — update to keep estimates accurate")
        sub.setObjectName("section_subtitle")
        lay.addWidget(hdr)
        lay.addWidget(sub)

        # Toolbar
        toolbar = QHBoxLayout()
        self._search = QLineEdit()
        self._search.setPlaceholderText("🔍  Search materials…")
        self._search.textChanged.connect(self._do_search)
        toolbar.addWidget(self._search, stretch=1)

        self._cat_combo = QComboBox()
        self._cat_combo.addItem("All Categories", None)
        self._cat_combo.currentIndexChanged.connect(self._do_filter)
        toolbar.addWidget(self._cat_combo)

        add_btn = QPushButton("+ Add Material")
        add_btn.clicked.connect(self._add_material)
        toolbar.addWidget(add_btn)

        lay.addLayout(toolbar)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels(
            ["ID", "Category", "Material Name", "Unit", "Rate (₹)", "GST %", "Last Updated"]
        )
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        for c in [0, 1, 3, 4, 5, 6]:
            self._table.horizontalHeader().setSectionResizeMode(
                c, QHeaderView.ResizeMode.ResizeToContents
            )
        self._table.setAlternatingRowColors(True)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.doubleClicked.connect(self._edit_material)
        lay.addWidget(self._table, stretch=1)

        hint = QLabel("Double-click a row to edit rate. All rates are in Indian Rupees (₹).")
        hint.setObjectName("section_subtitle")
        lay.addWidget(hint)

    def refresh(self) -> None:
        self._load_categories()
        self._load_materials()

    def _load_categories(self) -> None:
        cats = get_all_categories()
        self._cat_combo.clear()
        self._cat_combo.addItem("All Categories", None)
        for c in cats:
            self._cat_combo.addItem(c["name"], c["id"])

    def _load_materials(self, materials: list[dict] | None = None) -> None:
        if materials is None:
            cat_id = self._cat_combo.currentData() if self._cat_combo.count() > 0 else None
            materials = get_all_materials(cat_id)

        self._table.setRowCount(len(materials))
        for row, m in enumerate(materials):
            vals = [
                str(m["id"]),
                m.get("category_name", ""),
                m["name"],
                m["unit"],
                fmt_inr(m["rate"]),
                f"{m['gst_rate']:.0f}%",
                fmt_date(m.get("last_updated", "")),
            ]
            for col, val in enumerate(vals):
                cell = QTableWidgetItem(val)
                cell.setData(Qt.ItemDataRole.UserRole, m["id"])
                cell.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | (
                    Qt.AlignmentFlag.AlignRight if col == 4 else Qt.AlignmentFlag.AlignLeft
                ))
                self._table.setItem(row, col, cell)

    def _do_search(self, text: str) -> None:
        if text.strip():
            self._load_materials(search_materials(text.strip()))
        else:
            self._load_materials()

    def _do_filter(self) -> None:
        if self._search.text().strip():
            return
        self._load_materials()

    def _add_material(self) -> None:
        dlg = MaterialDialog(self)
        if dlg.exec():
            self._load_materials()

    def _edit_material(self, index) -> None:
        row = index.row()
        item = self._table.item(row, 0)
        if not item:
            return
        material_id = int(item.text())
        dlg = MaterialDialog(self, material_id=material_id)
        if dlg.exec():
            self._load_materials()
