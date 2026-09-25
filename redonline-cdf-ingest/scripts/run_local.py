#!/usr/bin/env python
"""Local / VM runner — delegates to redonline_cdf.cli."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from redonline_cdf.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
