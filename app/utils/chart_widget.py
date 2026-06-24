"""
Matplotlib charts — brutalist terminal style with vivid accent palette.
Fully theme-aware: call ChartWidget.set_theme("dark"|"light") before rendering.
"""
from __future__ import annotations

import matplotlib
matplotlib.use("QtAgg")

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFrame

# ── Vivid accent palette — pops on both dark and light backgrounds ────────────
_ACCENT = [
    "#00d4ff",  # cyan
    "#ff6b35",  # orange
    "#a855f7",  # purple
    "#22d3a5",  # teal
    "#fbbf24",  # amber
    "#f472b6",  # pink
    "#4ade80",  # green
]

# ── Module-level theme state ──────────────────────────────────────────────────
_THEME = "dark"


def _t() -> dict:
    """Return current theme colours."""
    if _THEME == "dark":
        return {
            "bg":      "#000000",
            "panel":   "#060606",
            "fg":      "#666666",
            "grid":    "#111111",
            "border":  "#1a1a1a",
            "frame_bg":"#000000",
        }
    return {
        "bg":      "#ffffff",
        "panel":   "#f7f7f7",
        "fg":      "#888888",
        "grid":    "#e0e0e0",
        "border":  "#d0d0d0",
        "frame_bg":"#ffffff",
    }


def _fig(w: float = 4.4, h: float = 3.2) -> tuple[Figure, FigureCanvas]:
    c = _t()
    fig = Figure(figsize=(w, h), facecolor=c["bg"])
    fig.subplots_adjust(left=0.12, right=0.97, top=0.88, bottom=0.20)
    canvas = FigureCanvas(fig)
    canvas.setStyleSheet("background:transparent;")
    return fig, canvas


def _wrap(canvas: FigureCanvas) -> QWidget:
    c = _t()
    frame = QFrame()
    frame.setObjectName("stat_card")
    frame.setStyleSheet(
        f"QFrame#stat_card{{"
        f"background:{c['frame_bg']};"
        f"border:1px solid {c['border']};"
        f"border-radius:0px;"
        f"}}"
    )
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(4, 4, 4, 4)
    lay.addWidget(canvas)
    return frame


def _apply_ax_style(ax, c: dict) -> None:
    """Apply common axis styling."""
    ax.set_facecolor(c["panel"])
    ax.tick_params(colors=c["fg"], labelsize=8)
    for tick in ax.get_xticklabels() + ax.get_yticklabels():
        tick.set_fontfamily("monospace")
        tick.set_color(c["fg"])
    for spine in ax.spines.values():
        spine.set_edgecolor(c["grid"])
        spine.set_linewidth(0.5)


class ChartWidget:

    @staticmethod
    def set_theme(theme: str) -> None:
        global _THEME
        _THEME = theme

    @staticmethod
    def pie_chart(title: str, labels: list, values: list) -> QWidget:
        c = _t()
        fig, canvas = _fig(4.2, 3.0)
        ax = fig.add_subplot(111, facecolor=c["bg"])
        fig.patch.set_facecolor(c["bg"])

        if not any(v > 0 for v in values):
            ax.text(0.5, 0.5, "NO DATA", ha="center", va="center",
                    color=c["fg"], fontsize=10, fontfamily="monospace",
                    transform=ax.transAxes)
        else:
            wedges, texts, auto = ax.pie(
                values,
                labels=None,
                autopct="%1.0f%%",
                colors=_ACCENT[:len(values)],
                startangle=90,
                wedgeprops={"edgecolor": c["bg"], "linewidth": 2},
                pctdistance=0.72,
            )
            for a in auto:
                a.set_color("#000000")
                a.set_fontfamily("monospace")
                a.set_fontsize(8)
                a.set_fontweight("bold")

            ax.legend(
                wedges, [l.upper() for l in labels],
                loc="lower center",
                bbox_to_anchor=(0.5, -0.18),
                ncol=min(len(labels), 4),
                fontsize=7,
                frameon=False,
                labelcolor=c["fg"],
                prop={"family": "monospace", "size": 7},
            )

        ax.set_title(
            f"// {title}",
            color=c["fg"], fontsize=9, fontfamily="monospace",
            fontweight="bold", pad=8, loc="left",
        )
        return _wrap(canvas)

    @staticmethod
    def bar_chart(title: str, labels: list, values: list,
                  color: list | str | None = None) -> QWidget:
        c = _t()
        fig, canvas = _fig(4.4, 3.2)
        ax = fig.add_subplot(111, facecolor=c["panel"])
        fig.patch.set_facecolor(c["bg"])

        bar_colors = (color if isinstance(color, list)
                      else ([color] * len(labels) if color else _ACCENT))

        bars = ax.bar(
            [l.upper() for l in labels],
            values,
            color=bar_colors[:len(labels)],
            edgecolor=c["bg"],
            linewidth=1,
            zorder=3,
            width=0.5,
        )

        _apply_ax_style(ax, c)
        ax.yaxis.grid(True, color=c["grid"], linestyle="--", linewidth=0.5, zorder=1)
        ax.set_axisbelow(True)

        for bar in bars:
            h = bar.get_height()
            if h > 0:
                lbl = f"₹{h/1e5:.1f}L" if h >= 1e5 else f"{h:,.0f}"
                ax.annotate(
                    lbl,
                    xy=(bar.get_x() + bar.get_width() / 2, h),
                    xytext=(0, 4), textcoords="offset points",
                    ha="center", va="bottom",
                    color=c["fg"], fontsize=7, fontfamily="monospace",
                )

        ax.set_title(
            f"// {title}", color=c["fg"], fontsize=9,
            fontfamily="monospace", fontweight="bold", pad=8, loc="left",
        )
        return _wrap(canvas)

    @staticmethod
    def line_chart(title: str, x: list, y: list,
                   x_label: str = "", y_label: str = "") -> QWidget:
        c = _t()
        fig, canvas = _fig(5.0, 3.2)
        ax = fig.add_subplot(111, facecolor=c["panel"])
        fig.patch.set_facecolor(c["bg"])

        ax.plot(x, y, color=_ACCENT[0], linewidth=2,
                marker="s", markersize=5,
                markerfacecolor=_ACCENT[0],
                markeredgecolor=c["bg"],
                markeredgewidth=1.5,
                zorder=3)
        ax.fill_between(range(len(y)), y, alpha=0.12, color=_ACCENT[0])

        ax.set_xticks(range(len(x)))
        ax.set_xticklabels([str(v).upper() for v in x],
                           rotation=30, ha="right", fontsize=7)
        _apply_ax_style(ax, c)
        ax.yaxis.grid(True, color=c["grid"], linestyle="--", linewidth=0.5)

        if x_label:
            ax.set_xlabel(x_label.upper(), color=c["fg"], fontsize=8, fontfamily="monospace")
        if y_label:
            ax.set_ylabel(y_label.upper(), color=c["fg"], fontsize=8, fontfamily="monospace")
        ax.set_title(
            f"// {title}", color=c["fg"], fontsize=9,
            fontfamily="monospace", fontweight="bold", pad=8, loc="left",
        )
        return _wrap(canvas)

    @staticmethod
    def horizontal_bar(title: str, labels: list, values: list) -> QWidget:
        c = _t()
        fig, canvas = _fig(5.0, max(3.0, len(labels) * 0.55 + 1.2))
        ax = fig.add_subplot(111, facecolor=c["panel"])
        fig.patch.set_facecolor(c["bg"])

        ax.barh([l.upper() for l in labels], values,
                color=_ACCENT[:len(labels)],
                edgecolor=c["bg"],
                linewidth=1, zorder=3)
        ax.xaxis.grid(True, color=c["grid"], linestyle="--", linewidth=0.5, zorder=1)
        ax.set_axisbelow(True)
        _apply_ax_style(ax, c)

        ax.set_title(
            f"// {title}", color=c["fg"], fontsize=9,
            fontfamily="monospace", fontweight="bold", pad=8, loc="left",
        )
        return _wrap(canvas)
