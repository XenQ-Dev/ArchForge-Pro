"""
Atlas widget — displays atlas.png with a rotating wireframe overlay on the sphere.
Light-mode inversion uses QPainter composition (O(1) Python, GPU-backed).
"""
from __future__ import annotations
import math
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QTimer, QPointF, Qt
from PyQt6.QtGui import QPainter, QPen, QColor, QPixmap

from app.utils.paths import resource
_IMG_PATH = resource("app/resources/images/atlas.png.png")

_MAX_W = 200
_MAX_H = 220

# Sphere position inside the ORIGINAL image (as fractions of original dims).
_CX_FRAC = 0.50
_CY_FRAC = 0.30
_R_FRAC  = 0.37   # fraction of original image width


class SphereWidget(QWidget):
    def __init__(self, parent=None, **_):
        super().__init__(parent)
        self._angle = 0.0
        self._pulse = 0.0
        self._dark  = True

        # sphere overlay in scaled-image pixel coords
        self._sph_cx = 0.0
        self._sph_cy = 0.0
        self._sph_r  = 0.0
        self._x_off  = 0   # horizontal centering offset inside widget

        self._img_dark : QPixmap | None = None
        self._img_light: QPixmap | None = None
        self._load_image()

        h = self._img_dark.height() if self._img_dark else _MAX_H
        self.setFixedSize(_MAX_W, h)

        t = QTimer(self)
        t.timeout.connect(self._tick)
        t.start(33)

    # ── image ──────────────────────────────────────────────────────
    def _load_image(self) -> None:
        if not _IMG_PATH.exists():
            return
        pm = QPixmap(str(_IMG_PATH))
        if pm.isNull():
            return

        orig_w, orig_h = pm.width(), pm.height()
        pm = pm.scaled(_MAX_W, _MAX_H,
                       Qt.AspectRatioMode.KeepAspectRatio,
                       Qt.TransformationMode.SmoothTransformation)
        self._img_dark = pm

        # sphere overlay coords in scaled image pixels
        scale = pm.width() / orig_w
        self._sph_cx = orig_w * _CX_FRAC * scale
        self._sph_cy = orig_h * _CY_FRAC * scale
        self._sph_r  = orig_w * _R_FRAC  * scale
        self._x_off  = max(0, (_MAX_W - pm.width()) // 2 - 18)

        # invert for light mode using QPainter composition — no pixel loops
        inv = QPixmap(pm.size())
        inv.fill(QColor(255, 255, 255))
        p = QPainter(inv)
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Difference)
        p.drawPixmap(0, 0, pm)
        p.end()
        self._img_light = inv

    # ── state ──────────────────────────────────────────────────────
    def set_theme(self, theme: str) -> None:
        self._dark = (theme == "dark")
        self.update()

    def _tick(self) -> None:
        self._angle = (self._angle + 0.7) % 360
        self._pulse = (self._pulse + 0.04) % (2 * math.pi)
        self.update()

    def _c(self, a: int) -> QColor:
        v = 255 if self._dark else 0
        return QColor(v, v, v, max(0, min(255, a)))

    # ── paint ──────────────────────────────────────────────────────
    def paintEvent(self, event) -> None:  # type: ignore[override]
        if not self._img_dark:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(Qt.BrushStyle.NoBrush)

        pm = self._img_dark if self._dark else self._img_light
        p.drawPixmap(self._x_off, 0, pm)

        cx = self._sph_cx + self._x_off
        cy = self._sph_cy
        r  = self._sph_r
        glow    = 0.5 + 0.5 * math.sin(self._pulse)
        lon_off = math.radians(self._angle)

        for i in range(12):
            lon     = lon_off + i * math.pi / 6
            cos_lon = math.cos(lon)
            alpha   = int(35 + 90 * cos_lon) if cos_lon >= 0 else int(14 * abs(cos_lon))
            pen = QPen(self._c(alpha))
            pen.setWidthF(0.7)
            p.setPen(pen)
            p.drawEllipse(QPointF(cx, cy), r * abs(cos_lon), r)

        pen = QPen(self._c(int(45 + glow * 30)))
        pen.setWidthF(1.0)
        p.setPen(pen)
        p.drawEllipse(QPointF(cx, cy), r, r * 0.30)

        p.end()
