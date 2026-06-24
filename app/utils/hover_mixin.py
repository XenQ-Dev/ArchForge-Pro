"""
GlowCard — a QFrame subclass that lifts and glows on hover using
QPropertyAnimation on a custom "glow" property painted in the shadow margin.
No external dependency — pure PyQt6.
"""
from __future__ import annotations

from PyQt6.QtWidgets import QFrame, QGraphicsDropShadowEffect
from PyQt6.QtCore import (
    QPropertyAnimation, QEasingCurve, pyqtProperty,
    QByteArray, Qt,
)
from PyQt6.QtGui import QColor, QEnterEvent


class GlowCard(QFrame):
    """Drop-in replacement for QFrame#stat_card — adds hover lift + glow."""

    def __init__(self, parent=None, accent: str = "#f0a500"):
        super().__init__(parent)
        self.setObjectName("stat_card")
        self._accent = QColor(accent)
        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(12)
        self._shadow.setOffset(0, 4)
        self._shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(self._shadow)

        self._anim_blur = QPropertyAnimation(self._shadow, QByteArray(b"blurRadius"), self)
        self._anim_blur.setDuration(200)
        self._anim_blur.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._anim_color = QPropertyAnimation(self._shadow, QByteArray(b"color"), self)
        self._anim_color.setDuration(200)
        self._anim_color.setEasingCurve(QEasingCurve.Type.OutCubic)

    def enterEvent(self, event: QEnterEvent) -> None:  # type: ignore[override]
        glow = QColor(self._accent)
        glow.setAlpha(140)
        self._anim_blur.stop()
        self._anim_blur.setStartValue(self._shadow.blurRadius())
        self._anim_blur.setEndValue(28)
        self._anim_blur.start()

        self._anim_color.stop()
        self._anim_color.setStartValue(self._shadow.color())
        self._anim_color.setEndValue(glow)
        self._anim_color.start()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # type: ignore[override]
        dark = QColor(0, 0, 0, 80)
        self._anim_blur.stop()
        self._anim_blur.setStartValue(self._shadow.blurRadius())
        self._anim_blur.setEndValue(12)
        self._anim_blur.start()

        self._anim_color.stop()
        self._anim_color.setStartValue(self._shadow.color())
        self._anim_color.setEndValue(dark)
        self._anim_color.start()
        super().leaveEvent(event)
