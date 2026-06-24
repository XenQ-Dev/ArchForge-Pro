"""Bundled-font loader. Registers Press Start 2P with Qt and returns its family."""
from __future__ import annotations
from PyQt6.QtGui import QFontDatabase
from app.utils.paths import resource

_cache: dict[str, str] = {}


def pixel_family() -> str:
    """Register and return the Press Start 2P family name (falls back to Courier New)."""
    if "pixel" in _cache:
        return _cache["pixel"]
    path = resource("app/resources/fonts/PressStart2P-Regular.ttf")
    fam = "Courier New"
    try:
        fid = QFontDatabase.addApplicationFont(str(path))
        families = QFontDatabase.applicationFontFamilies(fid)
        if families:
            fam = families[0]
    except Exception:
        pass
    _cache["pixel"] = fam
    return fam
