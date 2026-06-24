"""
ArchForge Pro — Main Window  v3.1
· Fixed theme toggle (simple dark/light swap)
· Rotating sphere + Sisyphus figure in sidebar
· Dot-grid animated background on content area
"""
from __future__ import annotations
from datetime import datetime

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget, QStatusBar,
    QSizePolicy, QFrame, QApplication, QScrollArea,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QObject, QEvent

from app.models.settings_model import get_setting, set_setting
from app.utils.animated_bg   import AnimatedBackground
from app.utils.sphere_widget import SphereWidget
from app.utils.chart_widget  import ChartWidget
from app.views.pages.dashboard_page   import DashboardPage
from app.views.pages.projects_page    import ProjectsPage
from app.views.pages.estimator_page   import EstimatorPage
from app.views.pages.boq_page         import BOQPage
from app.views.pages.expenses_page    import ExpensesPage
from app.views.pages.timeline_page    import TimelinePage
from app.views.pages.reports_page     import ReportsPage
from app.views.pages.ml_page          import MLPredictionPage
from app.views.pages.materials_page   import MaterialsPage
from app.views.pages.settings_page    import SettingsPage

from app.utils.paths import resource
STYLE_DIR = resource("app/resources/styles")

NAV_ITEMS = [
    ("[01]", "DASHBOARD",      DashboardPage),
    ("[02]", "PROJECTS",       ProjectsPage),
    ("[03]", "COST ESTIMATOR", EstimatorPage),
    ("[04]", "BOQ",            BOQPage),
    ("[05]", "EXPENSES",       ExpensesPage),
    ("[06]", "TIMELINE",       TimelinePage),
    ("[07]", "REPORTS",        ReportsPage),
    ("[08]", "ML PREDICTION",  MLPredictionPage),
    ("[09]", "MATERIALS",      MaterialsPage),
    ("[10]", "SETTINGS",       SettingsPage),
]

def _nav_style(active: bool, theme: str) -> str:
    """Full per-button QSS including hover, for dark or light theme."""
    base = (
        "font-family:'Courier New',monospace; font-size:11px; "
        "letter-spacing:2px; border-radius:0px; text-align:left; padding:10px 18px;"
    )
    if theme == "dark":
        if active:
            return (
                f"QPushButton {{ {base} background:transparent; color:#ffffff; "
                "font-weight:700; border:1px solid #ffffff; }"
                "QPushButton:hover { border:1px solid #ffffff; color:#ffffff; }"
            )
        return (
            f"QPushButton {{ {base} background:transparent; color:#bbbbbb; "
            "border:1px solid transparent; }"
            "QPushButton:hover { color:#ffffff; border:1px solid #888888; }"
        )
    else:  # light
        if active:
            return (
                f"QPushButton {{ {base} background:transparent; color:#000000; "
                "font-weight:700; border:1px solid #000000; }"
                "QPushButton:hover { border:1px solid #000000; color:#000000; }"
            )
        return (
            f"QPushButton {{ {base} background:transparent; color:#444444; "
            "border:1px solid transparent; }"
            "QPushButton:hover { color:#000000; border:1px solid #666666; }"
        )


class _GlobalMouseTracker(QObject):
    """App-level event filter — feeds cursor position to the active wrapper's
    AnimatedBackground regardless of which child widget the mouse is over."""

    def __init__(self, window: "MainWindow", parent=None):
        super().__init__(parent)
        self._win = window

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.MouseMove:
            win = self._win
            idx = win._active_idx
            if 0 <= idx < len(win._wrappers):
                wrapper = win._wrappers[idx]
                pos = wrapper.mapFromGlobal(event.globalPosition().toPoint())
                wrapper.bg().set_cursor_pos(pos.x(), pos.y())
        return False   # never consume the event


class _PageWrapper(QWidget):
    def __init__(self, page: QWidget, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self._bg = AnimatedBackground(self)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(page)

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        self._bg.resize(self.size())

    def mouseMoveEvent(self, event) -> None:  # type: ignore[override]
        pos = event.position()
        self._bg.set_cursor_pos(pos.x(), pos.y())
        super().mouseMoveEvent(event)

    def bg(self) -> AnimatedBackground:
        return self._bg


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ARCHFORGE PRO  //  CONSTRUCTION COST ESTIMATION SYSTEM")
        self.setMinimumSize(1280, 800)
        self.setMouseTracking(True)

        self._theme       = get_setting("theme", "dark")
        self._active_idx  = 0
        self._nav_buttons: list[QPushButton] = []
        self._pages:       list[QWidget]     = []
        self._wrappers:    list[_PageWrapper] = []

        self._build_ui()
        self._apply_theme(self._theme, init=True)
        self._navigate(0)

        self._clock = QTimer(self)
        self._clock.timeout.connect(self._tick_status)
        self._clock.start(1000)

        # global mouse tracker — works over every child widget, no right-click needed
        self._mouse_tracker = _GlobalMouseTracker(self, self)
        QApplication.instance().installEventFilter(self._mouse_tracker)

    # ── Build ─────────────────────────────────────────────────────────────────
    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        lay = QHBoxLayout(root)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        lay.addWidget(self._build_sidebar())

        self.stack = QStackedWidget()
        self.stack.setMouseTracking(True)
        for _, label, PageClass in NAV_ITEMS:
            try:
                page = PageClass()
            except Exception as exc:
                page = _PlaceholderPage(label, str(exc))
            self._pages.append(page)
            w = _PageWrapper(page, self.stack)
            self._wrappers.append(w)
            self.stack.addWidget(w)

        lay.addWidget(self.stack, stretch=1)

        self._sb = QStatusBar()
        self._sb.setFixedHeight(24)
        self.setStatusBar(self._sb)

    def _build_sidebar(self) -> QWidget:
        # outer container — fixed width, sets sidebar bg/border via QSS
        outer = QWidget()
        outer.setObjectName("sidebar")
        outer.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        outer_lay = QVBoxLayout(outer)
        outer_lay.setContentsMargins(0, 0, 0, 0)
        outer_lay.setSpacing(0)

        # scrollable inner content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFixedWidth(230)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Logo
        logo = QLabel("ARCHFORGE PRO")
        logo.setObjectName("logo_label")
        lay.addWidget(logo)
        tagline = QLabel("// COST ESTIMATION SYSTEM")
        tagline.setObjectName("tagline_label")
        lay.addWidget(tagline)

        lay.addWidget(_HSep())

        meta = QLabel("  EST. 2025  //  v1.0.0")
        meta.setObjectName("sidebar_meta")
        lay.addWidget(meta)
        lay.addWidget(_HSep())

        nav_sec = QLabel("  // NAVIGATION")
        nav_sec.setObjectName("sidebar_meta")
        lay.addWidget(nav_sec)

        for i, (prefix, label, _) in enumerate(NAV_ITEMS):
            btn = QPushButton(f"  {prefix} {label}")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(36)
            btn.clicked.connect(lambda _checked, idx=i: self._navigate(idx))
            self._nav_buttons.append(btn)
            lay.addWidget(btn)
            if i == 7:
                lay.addWidget(_HSep())

        lay.addWidget(_HSep())

        # Theme toggle
        tm_label = QLabel("  // THEME")
        tm_label.setObjectName("sidebar_meta")
        lay.addWidget(tm_label)

        self._dark_btn  = self._mk_theme_btn("[D] DARK  MODE")
        self._light_btn = self._mk_theme_btn("[L] LIGHT MODE")
        self._dark_btn .clicked.connect(lambda: self._apply_theme("dark"))
        self._light_btn.clicked.connect(lambda: self._apply_theme("light"))
        lay.addWidget(self._dark_btn)
        lay.addWidget(self._light_btn)

        lay.addWidget(_HSep())

        # Atlas animation — centred, no extra wrapper padding
        self._sphere = SphereWidget()
        self._sphere.setContentsMargins(0, 8, 0, 8)
        atlas_wrap = QWidget()
        atlas_wrap.setStyleSheet("background:transparent;")
        aw = QHBoxLayout(atlas_wrap)
        aw.setContentsMargins(0, 0, 0, 0)
        aw.addStretch()
        aw.addWidget(self._sphere)
        aw.addStretch()
        lay.addWidget(atlas_wrap)

        lay.addWidget(_HSep())

        coord = QLabel("  LAT: 18.5204°  ·  LNG: 73.8567°")
        coord.setObjectName("sidebar_meta")
        lay.addWidget(coord)
        lay.addStretch()

        scroll.setWidget(inner)
        outer_lay.addWidget(scroll)
        return outer

    @staticmethod
    def _mk_theme_btn(text: str) -> QPushButton:
        btn = QPushButton(f"  {text}")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(34)
        return btn

    # ── Navigation ────────────────────────────────────────────────────────────
    def _navigate(self, index: int) -> None:
        self._active_idx = index
        self.stack.setCurrentIndex(index)
        self._refresh_nav_styles()

        page = self._pages[index]
        if hasattr(page, "refresh"):
            page.refresh()
        self._tick_status()

    def _refresh_nav_styles(self) -> None:
        for i, btn in enumerate(self._nav_buttons):
            btn.setStyleSheet(_nav_style(i == self._active_idx, self._theme))

    # ── Theme ─────────────────────────────────────────────────────────────────
    def _apply_theme(self, theme: str, init: bool = False) -> None:
        self._theme = theme
        set_setting("theme", theme)

        qss_path = STYLE_DIR / f"{theme}_theme.qss"
        try:
            self.setStyleSheet(qss_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            pass

        self._refresh_nav_styles()
        self._style_theme_buttons(theme)

        # propagate theme to animated backgrounds, sphere, and charts
        for wrapper in self._wrappers:
            wrapper.bg().set_theme(theme)
        self._sphere.set_theme(theme)
        ChartWidget.set_theme(theme)

        # re-render current page so charts pick up new theme colours
        if not init:
            page = self._pages[self._active_idx]
            if hasattr(page, "refresh"):
                page.refresh()
            QApplication.processEvents()

    def _style_theme_buttons(self, active: str) -> None:
        base = (
            "font-family:'Courier New',monospace; font-size:10px; "
            "letter-spacing:2px; text-align:left; padding:6px 18px; "
            "border-radius:0px;"
        )
        if self._theme == "dark":
            on  = f"QPushButton{{{base} background:transparent; color:#ffffff; border:1px solid #ffffff;}} QPushButton:hover{{color:#ffffff; border:1px solid #ffffff;}}"
            off = f"QPushButton{{{base} background:transparent; color:#333333; border:1px solid transparent;}} QPushButton:hover{{color:#aaaaaa; border:1px solid #444444;}}"
        else:
            on  = f"QPushButton{{{base} background:transparent; color:#000000; border:1px solid #000000;}} QPushButton:hover{{color:#000000; border:1px solid #000000;}}"
            off = f"QPushButton{{{base} background:transparent; color:#aaaaaa; border:1px solid transparent;}} QPushButton:hover{{color:#555555; border:1px solid #aaaaaa;}}"

        self._dark_btn .setStyleSheet(on  if active == "dark"  else off)
        self._light_btn.setStyleSheet(on  if active == "light" else off)

    # ── Clock ─────────────────────────────────────────────────────────────────
    def _tick_status(self) -> None:
        if 0 <= self._active_idx < len(NAV_ITEMS):
            label = NAV_ITEMS[self._active_idx][1]
            self._sb.showMessage(
                f"  ARCHFORGE PRO  //  {label}  //  "
                f"{datetime.now().strftime('%H:%M:%S')}"
            )



class _HSep(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.Shape.HLine)
        self.setFixedHeight(1)
        self.setStyleSheet("background:#111111; margin:0;")


class _PlaceholderPage(QWidget):
    def __init__(self, name: str, error: str = ""):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl = QLabel(f"// {name}")
        lbl.setObjectName("section_title")
        lay.addWidget(lbl)
        if error:
            err = QLabel(error)
            err.setObjectName("section_subtitle")
            err.setWordWrap(True)
            lay.addWidget(err)
