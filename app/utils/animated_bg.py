"""
Animated dot-grid background.
Grid positions are cached on resize; only alpha/size vary per frame.
"""
from __future__ import annotations
import math

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QTimer, QPointF, Qt
from PyQt6.QtGui import QPainter, QColor, QBrush

_DOT_SPACING = 32
_DOT_RADIUS  = 1.0
_NEAR_R      = 100
_MID_R       = 200
_PULSE_SPEED = 0.018


class AnimatedBackground(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAutoFillBackground(False)

        self._mx: float = -9999
        self._my: float = -9999
        self._tick: float = 0.0
        self._is_dark = True
        self._dot_rgb = (255, 255, 255)
        self._bg_color = QColor(0, 0, 0, 0)

        # cached grid: list of (x, y, phase_offset)
        self._grid: list[tuple[float, float, float]] = []
        self._grid_size = (0, 0)   # (width, height) when grid was built

        t = QTimer(self)
        t.timeout.connect(self._on_tick)
        t.start(16)

    def set_theme(self, theme: str) -> None:
        self._is_dark = (theme == "dark")
        if self._is_dark:
            self._dot_rgb = (255, 255, 255)
            self._bg_color = QColor(0, 0, 0, 0)
        else:
            self._dot_rgb = (0, 0, 0)
            self._bg_color = QColor(255, 255, 255, 255)
        self.update()

    def set_cursor_pos(self, x: float, y: float) -> None:
        self._mx = x
        self._my = y

    def _on_tick(self) -> None:
        self._tick += _PULSE_SPEED
        self.update()

    def _rebuild_grid(self, w: int, h: int) -> None:
        cols = w // _DOT_SPACING + 2
        rows = h // _DOT_SPACING + 2
        self._grid = [
            (col * _DOT_SPACING,
             row * _DOT_SPACING,
             (col * 3 + row * 7) % 20 * 0.31)
            for row in range(rows)
            for col in range(cols)
        ]
        self._grid_size = (w, h)

    def paintEvent(self, event) -> None:  # type: ignore[override]
        w, h = self.width(), self.height()
        if w == 0 or h == 0:
            return

        # rebuild grid only when widget is resized
        if (w, h) != self._grid_size:
            self._rebuild_grid(w, h)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if not self._is_dark:
            painter.fillRect(0, 0, w, h, self._bg_color)

        painter.setPen(Qt.PenStyle.NoPen)

        mx, my = self._mx, self._my
        t = self._tick
        dr, dg, db = self._dot_rgb

        for x, y, phase in self._grid:
            dx   = x - mx
            dy   = y - my
            dist = math.hypot(dx, dy)
            pulse = math.sin(t + phase) * 0.3 + 0.7

            if dist < _NEAR_R:
                ratio = 1.0 - dist / _NEAR_R
                alpha = int(6 + ratio * 55 * pulse)
                r     = _DOT_RADIUS + ratio * 0.8
            elif dist < _MID_R:
                ratio = 1.0 - (dist - _NEAR_R) / (_MID_R - _NEAR_R)
                alpha = int(6 + ratio * 18 * pulse)
                r     = _DOT_RADIUS
            else:
                alpha = int(5 * pulse)
                r     = _DOT_RADIUS

            alpha = min(255, max(0, alpha))
            painter.setBrush(QBrush(QColor(dr, dg, db, alpha)))
            painter.drawEllipse(QPointF(x, y), r, r)

        painter.end()
