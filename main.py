"""
ArchForge Pro — Application Entry Point
Run: python main.py
"""
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import QApplication, QSplashScreen
from PyQt6.QtCore import Qt, QTimer, QRect, QPoint
from PyQt6.QtGui import QPixmap, QFont, QColor, QPainter, QPen

from app.models.database import init_database
from app.utils.paths import resource, data
from PyQt6.QtGui import QIcon


def _setup_logging() -> None:
    log_dir = data("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
        handlers=[
            logging.FileHandler(str(log_dir / "archforge.log"), encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def _make_splash() -> QSplashScreen:
    W, H = 960, 480

    pix = QPixmap(W, H)
    pix.fill(QColor("#000000"))

    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

    # ── outer border ──────────────────────────────────────────────
    p.setPen(QPen(QColor("#1e1e1e"), 1))
    p.drawRect(0, 0, W - 1, H - 1)

    # ── subtle dot grid (left half only) ─────────────────────────
    p.setPen(QPen(QColor("#111111"), 1))
    spacing = 28
    for row in range(0, H // spacing + 1):
        for col in range(0, (W // 2) // spacing + 1):
            p.drawPoint(QPoint(col * spacing, row * spacing))

    # ── vertical divider ─────────────────────────────────────────
    p.setPen(QPen(QColor("#1a1a1a"), 1))
    p.drawLine(W // 2, 0, W // 2, H)

    # ── atlas image (right half) ──────────────────────────────────
    img_path = resource("app/resources/images/atlas.png.png")
    if img_path.exists():
        atlas = QPixmap(str(img_path))
        if not atlas.isNull():
            right_w = W // 2
            scaled = atlas.scaled(
                right_w - 40, H - 40,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            ax = W // 2 + (right_w - scaled.width()) // 2
            ay = (H - scaled.height()) // 2
            p.setOpacity(0.88)
            p.drawPixmap(ax, ay, scaled)
            p.setOpacity(1.0)

    # ── left content area ─────────────────────────────────────────
    left_w = W // 2
    pad = 52

    # tag line top
    p.setPen(QColor("#2a2a2a"))
    p.setFont(QFont("Courier New", 8, QFont.Weight.Normal))
    p.drawText(QRect(pad, 36, left_w - pad * 2, 20),
               Qt.AlignmentFlag.AlignLeft, "EST. 2025  //  v1.0.0")

    # logo
    p.setPen(QColor("#ffffff"))
    p.setFont(QFont("Courier New", 30, QFont.Weight.Bold))
    p.drawText(QRect(pad, 70, left_w - pad * 2, 60),
               Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
               "ARCHFORGE")

    p.setFont(QFont("Courier New", 30, QFont.Weight.Bold))
    p.setPen(QColor("#333333"))
    p.drawText(QRect(pad, 112, left_w - pad * 2, 60),
               Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
               "PRO")

    # thin rule under logo
    p.setPen(QPen(QColor("#1e1e1e"), 1))
    p.drawLine(pad, 178, left_w - pad, 178)

    # subtitle
    p.setPen(QColor("#2e2e2e"))
    p.setFont(QFont("Courier New", 9, QFont.Weight.Normal))
    p.drawText(QRect(pad, 192, left_w - pad * 2, 20),
               Qt.AlignmentFlag.AlignLeft,
               "// CONSTRUCTION COST ESTIMATION SYSTEM")

    p.setPen(QColor("#1e1e1e"))
    p.setFont(QFont("Courier New", 8))
    p.drawText(QRect(pad, 216, left_w - pad * 2, 20),
               Qt.AlignmentFlag.AlignLeft,
               "INDIAN STANDARDS  ·  OFFLINE  ·  SECURE")

    # feature list
    features = [
        "→  RULE-BASED COST ESTIMATOR",
        "→  BILL OF QUANTITIES",
        "→  EXPENSE TRACKER",
        "→  ML COST PREDICTION",
    ]
    p.setPen(QColor("#222222"))
    p.setFont(QFont("Courier New", 8))
    for i, feat in enumerate(features):
        p.drawText(QRect(pad, 260 + i * 18, left_w - pad * 2, 18),
                   Qt.AlignmentFlag.AlignLeft, feat)

    # ── bottom status bar ─────────────────────────────────────────
    bar_y = H - 38
    p.setPen(QPen(QColor("#1a1a1a"), 1))
    p.drawLine(0, bar_y, W, bar_y)
    p.fillRect(0, bar_y + 1, W, H - bar_y - 1, QColor("#050505"))

    p.setPen(QColor("#222222"))
    p.setFont(QFont("Courier New", 8))
    p.drawText(QRect(pad, bar_y + 10, 300, 18),
               Qt.AlignmentFlag.AlignLeft,
               "LAT: 18.5204°  ·  LNG: 73.8567°")

    p.setPen(QColor("#1e1e1e"))
    p.drawText(QRect(W - 250, bar_y + 10, 200, 18),
               Qt.AlignmentFlag.AlignRight,
               "INITIALISING...")

    p.end()

    splash = QSplashScreen(pix, Qt.WindowType.WindowStaysOnTopHint)
    return splash


def main() -> None:
    _setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting ArchForge Pro")

    app = QApplication(sys.argv)
    app.setApplicationName("ArchForge Pro")
    app.setOrganizationName("ArchForge")
    app.setApplicationVersion("1.0.0")

    icon_path = resource("app/resources/images/icon.ico")
    if icon_path.exists():
        icon = QIcon(str(icon_path))
        if not icon.isNull():
            app.setWindowIcon(icon)
            logger.info(f"Application icon loaded: {icon_path}")
        else:
            logger.warning(f"Icon file exists but failed to load: {icon_path}")
    else:
        logger.warning(f"Icon file not found: {icon_path}")

    # Register bundled pixel font (Press Start 2P)
    from app.utils.fonts import pixel_family
    pixel_family()

    splash = _make_splash()
    splash.show()
    app.processEvents()

    try:
        init_database()
        logger.info("Database ready")
    except Exception as exc:
        logger.error("Database initialisation failed: %s", exc)

    # Check for a persisted session
    from app.models.settings_model import get_setting, set_setting
    from app.models.user_model import get_session_user
    from app.utils.auth_session import set_current_user

    token = get_setting("active_session", "")
    user  = get_session_user(token) if token else None

    def _open_main(u: dict, t: str) -> None:
        from app.views.main_window import MainWindow
        set_current_user(u, t)
        try:
            win = MainWindow(user=u, token=t)
        except Exception as exc:
            logger.error("MainWindow failed to open: %s", exc, exc_info=True)
            return
        win.signed_out.connect(lambda: _open_login())
        app._main_win = win
        win.show()
        win.raise_()

    def _open_login() -> None:
        from app.views.auth.login_window import LoginWindow
        login = LoginWindow()
        login.login_success.connect(lambda u, t: _on_login_success(login, u, t))
        app._login_win = login
        login.show()

    def _on_login_success(login_win, u: dict, t: str) -> None:
        set_setting("active_session", t)
        login_win.close()
        _open_main(u, t)

    def _after_splash() -> None:
        if user:
            logger.info("Resuming session for %s", user["email"])
            _open_main(user, token)
        else:
            if token:
                set_setting("active_session", "")
            _open_login()
        splash.close()

    QTimer.singleShot(1800, _after_splash)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
