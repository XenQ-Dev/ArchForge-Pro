"""Projects Page — CRUD for projects with search, filter, sort and shortcuts."""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QLineEdit, QComboBox, QMessageBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QKeySequence, QShortcut

from app.models.project_model import get_all_projects, delete_project, search_projects
from app.utils.formatters import fmt_inr, fmt_date
from app.views.dialogs.project_dialog import ProjectDialog

_STATUS_COLOR = {
    "Active":    "#00d4ff",
    "Completed": "#22d3a5",
    "On Hold":   "#fbbf24",
    "Cancelled": "#ff6b35",
}


class ProjectsPage(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()
        self._setup_shortcuts()

    def _build_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(16)

        hdr = QLabel("Projects")
        hdr.setObjectName("section_title")
        sub = QLabel("Manage all construction projects  ·  Ctrl+N to add  ·  Double-click row to edit")
        sub.setObjectName("section_subtitle")
        lay.addWidget(hdr)
        lay.addWidget(sub)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search by name, client or location…  (Ctrl+F)")
        self._search.setToolTip("Search projects  [Ctrl+F]")
        self._search.textChanged.connect(self._do_search)
        self._search.returnPressed.connect(self._do_search_enter)
        toolbar.addWidget(self._search, stretch=1)

        self._filter_combo = QComboBox()
        self._filter_combo.addItems(["All", "Active", "Completed", "On Hold", "Cancelled"])
        self._filter_combo.setToolTip("Filter by status")
        self._filter_combo.currentTextChanged.connect(self._do_filter)
        toolbar.addWidget(self._filter_combo)

        add_btn = QPushButton("+ New Project")
        add_btn.setToolTip("Add new project  [Ctrl+N]")
        add_btn.clicked.connect(self._add_project)
        toolbar.addWidget(add_btn)

        lay.addLayout(toolbar)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels([
            "ID", "Project Name", "Client", "Type", "Quality", "Status", "Start Date",
        ])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._table.setAlternatingRowColors(True)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.verticalHeader().setVisible(False)
        self._table.setSortingEnabled(True)
        self._table.setToolTip("Double-click a row to edit  ·  Click column header to sort")
        self._table.doubleClicked.connect(self._on_row_double_click)
        lay.addWidget(self._table)

        # Bottom bar
        bottom = QHBoxLayout()
        self._status_lbl = QLabel("")
        self._status_lbl.setObjectName("section_subtitle")
        bottom.addWidget(self._status_lbl)
        bottom.addStretch()

        self._edit_btn = QPushButton("Edit Selected")
        self._edit_btn.setObjectName("btn_secondary")
        self._edit_btn.setToolTip("Edit selected project  [Enter]")
        self._edit_btn.clicked.connect(self._edit_selected)
        bottom.addWidget(self._edit_btn)

        self._del_btn = QPushButton("Delete Selected")
        self._del_btn.setObjectName("btn_danger")
        self._del_btn.setToolTip("Delete selected project  [Del]")
        self._del_btn.clicked.connect(self._delete_selected)
        bottom.addWidget(self._del_btn)

        lay.addLayout(bottom)

        self._load_projects()

    def _setup_shortcuts(self) -> None:
        QShortcut(QKeySequence("Ctrl+N"), self).activated.connect(self._add_project)
        QShortcut(QKeySequence("Ctrl+F"), self).activated.connect(self._focus_search)
        QShortcut(QKeySequence("Return"),  self).activated.connect(self._edit_selected)
        QShortcut(QKeySequence("Delete"),  self).activated.connect(self._delete_selected)
        QShortcut(QKeySequence("Escape"),  self).activated.connect(self._clear_search)

    def refresh(self) -> None:
        self._load_projects()

    def _load_projects(self, projects: list[dict] | None = None) -> None:
        if projects is None:
            f = self._filter_combo.currentText() if hasattr(self, "_filter_combo") else "All"
            projects = get_all_projects(None if f == "All" else f)

        self._table.setSortingEnabled(False)
        self._table.setRowCount(len(projects))
        for row, p in enumerate(projects):
            color = _STATUS_COLOR.get(p["status"], "#888888")
            cells = [
                str(p["id"]), p["project_name"], p["client_name"],
                p["project_type"], p["construction_quality"],
                p["status"], fmt_date(p["start_date"]),
            ]
            for col, val in enumerate(cells):
                item = QTableWidgetItem(val)
                item.setData(Qt.ItemDataRole.UserRole, p["id"])
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                if col == 5:
                    item.setForeground(QColor(color))
                self._table.setItem(row, col, item)
            self._table.setRowHeight(row, 42)

        self._table.setSortingEnabled(True)
        n = len(projects)
        self._status_lbl.setText(f"{n} project{'s' if n != 1 else ''} shown")

    def _current_project_id(self) -> int | None:
        row = self._table.currentRow()
        if row < 0:
            return None
        item = self._table.item(row, 0)
        return int(item.text()) if item else None

    def _on_row_double_click(self, index) -> None:
        pid = self._current_project_id()
        if pid:
            self._edit_project(pid)

    def _do_search(self, text: str) -> None:
        if text.strip():
            self._load_projects(search_projects(text.strip()))
        else:
            self._load_projects()

    def _do_search_enter(self) -> None:
        self._do_search(self._search.text())

    def _do_filter(self) -> None:
        self._load_projects()

    def _focus_search(self) -> None:
        self._search.setFocus()
        self._search.selectAll()

    def _clear_search(self) -> None:
        if self._search.text():
            self._search.clear()
        else:
            self._table.clearSelection()

    def _add_project(self) -> None:
        dlg = ProjectDialog(self)
        if dlg.exec():
            self._load_projects()

    def _edit_project(self, project_id: int) -> None:
        dlg = ProjectDialog(self, project_id=project_id)
        if dlg.exec():
            self._load_projects()

    def _edit_selected(self) -> None:
        pid = self._current_project_id()
        if pid:
            self._edit_project(pid)

    def _delete_selected(self) -> None:
        pid = self._current_project_id()
        if pid:
            self._delete_project(pid)

    def _delete_project(self, project_id: int) -> None:
        reply = QMessageBox.question(
            self, "Confirm Delete",
            "Delete this project and ALL its associated data?\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            delete_project(project_id)
            self._load_projects()
