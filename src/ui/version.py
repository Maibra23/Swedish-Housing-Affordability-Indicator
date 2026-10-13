"""The app version, read once from pyproject.toml.

It lived in `sidebar.py`, and the page footer carried its own literal
"SHAI v1.3" beside it, so the same release was labelled three ways across the
site. Both now read this.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

_FALLBACK = "1.3.0"


def _app_version() -> str:
    """Read the project version from pyproject.toml, or the fallback if absent."""
    try:
        toml = Path(__file__).resolve().parents[2] / "pyproject.toml"
        with open(toml, "rb") as f:
            return tomllib.load(f)["project"]["version"]
    except (OSError, KeyError, tomllib.TOMLDecodeError):
        return _FALLBACK


APP_VERSION = _app_version()
