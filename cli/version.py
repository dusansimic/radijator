"""Single source of truth for the Radijator version.

The canonical value lives in the repo-root VERSION file. radijator.spec
bundles it into both binaries, so the same resolver works frozen and from
a checkout.
"""

import sys
from pathlib import Path


def _version_file() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "VERSION"
    return Path(__file__).resolve().parent.parent / "VERSION"


def _read_version() -> str:
    try:
        return _version_file().read_text(encoding="utf-8").strip()
    except OSError:
        return "0.0.0+unknown"


__version__ = _read_version()
