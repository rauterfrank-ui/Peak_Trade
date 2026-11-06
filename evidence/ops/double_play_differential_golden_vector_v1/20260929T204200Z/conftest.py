"""Pytest path bootstrap for WP-2 evidence harness (non-production)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

_ROOT = Path(os.environ.get("WP2_REPO_ROOT", Path(__file__).resolve().parents[4]))
_SRC = _ROOT / "src"
for p in (_SRC, _ROOT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
