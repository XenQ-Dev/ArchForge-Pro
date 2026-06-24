"""
Central path resolver — works both in development and when frozen by PyInstaller.

PyInstaller sets sys.frozen=True and sys._MEIPASS to the temp bundle dir
where --add-data files are extracted. User-writable data (the SQLite DB,
ML models) must live next to the .exe, not inside the bundle.
"""
from __future__ import annotations
import sys
from pathlib import Path


def _bundle_dir() -> Path:
    """Read-only resources (QSS, images) extracted by PyInstaller."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)          # type: ignore[attr-defined]
    # development: project root is three levels up from this file
    return Path(__file__).parent.parent.parent


def _install_dir() -> Path:
    """Writable directory next to the .exe (or project root in dev)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent.parent.parent


# ── Public helpers ────────────────────────────────────────────────────────────

def resource(relative: str) -> Path:
    """Path to a bundled read-only resource (image, stylesheet, etc.)."""
    return _bundle_dir() / relative


def data(relative: str) -> Path:
    """Path to a user-writable file (database, ML models, exports)."""
    p = _install_dir() / relative
    p.parent.mkdir(parents=True, exist_ok=True)
    return p
