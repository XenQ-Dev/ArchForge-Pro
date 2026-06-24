"""Add / Edit Material dialog."""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QFormLayout,
    QGroupBox, QLineEdit, QDoubleSpinBox, QComboBox, QMessageBox,
)

from app.models.material_model import (
    get_all_categories, get_material, add_material, update_material,
)


class MaterialDialog(QDialog):
    def __init__(self, parent=None, material_id: int | None = None):
        super().__init__(parent)
        self._material_id = material_id
        self.setWindowTitle("Edit Material" if material_id else "Add Material")
        self.setMinimumWidth(400)
        self._build_ui()
        if material_id:
            self._load_material()

    def _build_ui(self) -> None:
        lay = QVBoxLayout(self)

        group = QGroupBox("Material Details")
        form = QFormLayout(group)
        form.setSpacing(10)

        self._category = QComboBox()
        cats = get_all_categories()
        for c in cats:
            self._category.addItem(c["name"], c["id"])
        form.addRow("Category *:", self._category)

        self._name = QLineEdit()
        self._name.setPlaceholderText("e.g. OPC Cement 53 Grade")
        form.addRow("Material Name *:", self._name)

        self._unit = QLineEdit()
        self._unit.setPlaceholderText("e.g. Bag (50kg), Cu.M, MT, Nos")
        form.addRow("Unit *:", self._unit)

        self._rate = QDoubleSpinBox()
        self._rate.setRange(0, 9999999)
        self._rate.setPrefix("₹ ")
        self._rate.setDecimals(2)
        self._rate.setSingleStep(10)
        form.addRow("Rate (₹) *:", self._rate)

        self._gst = QDoubleSpinBox()
        self._gst.setRange(0, 28)
        self._gst.setValue(18.0)
        self._gst.setSuffix(" %")
        form.addRow("GST Rate:", self._gst)

        lay.addWidget(group)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("btn_secondary")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Save Material")
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        lay.addLayout(btn_row)

    def _load_material(self) -> None:
        m = get_material(self._material_id)
        if not m:
            return
        idx = self._category.findData(m["category_id"])
        if idx >= 0:
            self._category.setCurrentIndex(idx)
        self._name.setText(m["name"])
        self._unit.setText(m["unit"])
        self._rate.setValue(m["rate"])
        self._gst.setValue(m["gst_rate"])

    def _save(self) -> None:
        if not self._name.text().strip():
            QMessageBox.warning(self, "Validation", "Material name is required.")
            return
        if not self._unit.text().strip():
            QMessageBox.warning(self, "Validation", "Unit is required.")
            return

        data = {
            "category_id": self._category.currentData(),
            "name": self._name.text().strip(),
            "unit": self._unit.text().strip(),
            "rate": self._rate.value(),
            "gst_rate": self._gst.value(),
        }
        if self._material_id:
            update_material(self._material_id, data)
        else:
            add_material(data)
        self.accept()
