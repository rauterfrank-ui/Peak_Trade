"""Canonical import bootstrap for repository `scripts/pt <script.py>` entrypoints."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path


def ensure_peak_trade_script_entry_bootstrap_v1(*, script_path: Path | None = None) -> Path:
    """Establish repo-root import paths and editable-install graph (`trading`, `src.*`)."""
    if script_path is None:
        repo_root = Path(__file__).resolve().parents[2]
    else:
        repo_root = script_path.resolve().parents[1]
    for entry in (repo_root, repo_root / "src"):
        text = str(entry)
        if text not in sys.path:
            sys.path.insert(0, text)
    importlib.import_module("trading")
    return repo_root


__all__ = ["ensure_peak_trade_script_entry_bootstrap_v1"]
