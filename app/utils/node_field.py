"""
Interactive node-field (constellation) background.
Nodes drift, link to nearby nodes, and are attracted toward the cursor.
Cursor position is polled each frame so it works under any overlay widget.
"""
from __future__ import annotations
import math
import random

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QTimer, Qt, QPointF, QLineF
from PyQt6.QtGui import QPainter, QColor, QPen, QCursor, QPainterPath, QPolygonF


class NodeFieldBackground(QWidget):
    def __init__(self, parent: QWidget | None = None, dark: bool = True):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAutoFillBackground(False)

        self._dark      = dark
        self._nodes: list[list[float]] = []   # [x, y, vx, vy]
        self._stars: list[tuple[float, float, int]] = []
        self._size      = (0, 0)

        # tuning
        self._connect   = 130.0    # node-to-node link distance
        self._cursor_r  = 220.0    # cursor influence radius
        self._attract   = 0.06     # cursor pull strength
        self._drift     = 0.7      # base drift speed
        self._min_speed = 0.45     # nodes never drift slower than this
        self._max_speed = 1.8      # cap (allows cursor bursts)

        t = QTimer(self)
        t.timeout.connect(self._tick)
        t.start(24)                # ~42 fps, sits above the ~19ms render budget

    # ── build / rebuild on resize ──────────────────────────────────────────
    def _build(self, w: int, h: int) -> None:
        area = w * h
        n = max(150, min(260, area // 5000))
        self._nodes = [
            [random.uniform(0, w), random.uniform(0, h),
             random.uniform(-self._drift, self._drift),
             random.uniform(-self._drift, self._drift)]
            for _ in range(n)
        ]
        ns = max(70, min(280, area // 7000))
        self._stars = [
            (random.uniform(0, w), random.uniform(0, h), random.randint(12, 75))
            for _ in range(ns)
        ]
        self._size = (w, h)

    # ── physics tick ────────────────────────────────────────────────────────
    def _tick(self) -> None:
        w, h = self.width(), self.height()
        if w == 0 or h == 0:
            return
        if (w, h) != self._size:
            self._build(w, h)

        cp = self.mapFromGlobal(QCursor.pos())
        cx, cy = cp.x(), cp.y()
        inside = (0 <= cx <= w and 0 <= cy <= h)
        R = self._cursor_r

        for nd in self._nodes:
            x, y, vx, vy = nd
            if inside:
                dx, dy = cx - x, cy - y
                d = math.hypot(dx, dy)
                if 1.0 < d < R:
                    f = (1.0 - d / R) * self._attract
                    vx += (dx / d) * f
                    vy += (dy / d) * f

            x += vx
            y += vy

            # light damping lets cursor bursts decay back toward base drift
            vx *= 0.99
            vy *= 0.99

            # enforce a constant baseline speed so nodes never stop moving
            sp = math.hypot(vx, vy)
            if sp < self._min_speed:
                if sp < 1e-4:
                    ang = random.uniform(0, 6.2832)
                    vx, vy = math.cos(ang) * self._min_speed, math.sin(ang) * self._min_speed
                else:
                    k = self._min_speed / sp
                    vx *= k; vy *= k
            elif sp > self._max_speed:
                k = self._max_speed / sp
                vx *= k; vy *= k

            # bounce at edges
            if x < 0:   x = 0;  vx = -vx
            elif x > w: x = w;  vx = -vx
            if y < 0:   y = 0;  vy = -vy
            elif y > h: y = h;  vy = -vy

            nd[0], nd[1], nd[2], nd[3] = x, y, vx, vy

        self.update()

    # ── paint ─────────────────────────────────────────────────────────────
    def paintEvent(self, event) -> None:  # type: ignore[override]
        w, h = self.width(), self.height()
        if w == 0 or h == 0:
            return

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r, g, b = (255, 255, 255) if self._dark else (10, 10, 10)

        nodes = self._nodes
        cd = self._connect
        cd2 = cd * cd
        n = len(nodes)

        # ── spatial grid (cell == link distance) ───────────────────────────
        cell = cd
        buckets: dict[tuple[int, int], list[int]] = {}
        for idx in range(n):
            key = (int(nodes[idx][0] // cell), int(nodes[idx][1] // cell))
            buckets.setdefault(key, []).append(idx)

        # ── collect links, grouped into a few alpha levels (batched draw) ──
        line_levels: dict[int, list[QLineF]] = {}
        _neigh = ((0, 0), (1, 0), (-1, 1), (0, 1), (1, 1))
        for (bx, by), members in buckets.items():
            for (ox, oy) in _neigh:
                other = buckets.get((bx + ox, by + oy))
                if not other:
                    continue
                same = (ox == 0 and oy == 0)
                for i in members:
                    xi, yi = nodes[i][0], nodes[i][1]
                    for j in other:
                        if same and j <= i:
                            continue
                        xj, yj = nodes[j][0], nodes[j][1]
                        dx, dy = xi - xj, yi - yj
                        d2 = dx * dx + dy * dy
                        if d2 < cd2:
                            a = int((1.0 - math.sqrt(d2) / cd) * 72)
                            if a > 4:
                                line_levels.setdefault(a >> 3, []).append(
                                    QLineF(xi, yi, xj, yj))

        # ── cursor links (same alpha buckets) ──────────────────────────────
        cp = self.mapFromGlobal(QCursor.pos())
        cx, cy = cp.x(), cp.y()
        if 0 <= cx <= w and 0 <= cy <= h:
            R = self._cursor_r
            for nd in nodes:
                dx, dy = nd[0] - cx, nd[1] - cy
                d = math.hypot(dx, dy)
                if d < R:
                    a = int((1.0 - d / R) * 95)
                    if a > 4:
                        line_levels.setdefault(a >> 3, []).append(
                            QLineF(nd[0], nd[1], cx, cy))

        # ── draw: starfield (one call per alpha level) ─────────────────────
        star_levels: dict[int, list[QPointF]] = {}
        for sx, sy, sa in self._stars:
            star_levels.setdefault(sa >> 3, []).append(QPointF(sx, sy))
        for lvl, pts in star_levels.items():
            p.setPen(QPen(QColor(r, g, b, min(255, (lvl << 3) + 4)), 1.6))
            p.drawPoints(QPolygonF(pts))

        # ── draw: links (one call per alpha level) ─────────────────────────
        for lvl, lines in line_levels.items():
            p.setPen(QPen(QColor(r, g, b, min(255, (lvl << 3) + 4)), 1))
            p.drawLines(lines)

        # ── draw: all nodes as a single filled path ────────────────────────
        path = QPainterPath()
        for nd in nodes:
            path.addEllipse(QPointF(nd[0], nd[1]), 1.7, 1.7)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(r, g, b, 210))
        p.drawPath(path)

        p.end()
