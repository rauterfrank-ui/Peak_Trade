"""
Read-only R&D experiment JSON load + ordering helpers.

Source directory (typical): ``reports/r_and_d_experiments/*.json`` — same contract as
``scripts/view_r_and_d_experiments.py`` and ``src/webui/r_and_d_api.py``.

No writes, no network, no job triggers.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

_SORT_KEYS = frozenset({"timestamp", "sharpe", "return", "total_return"})
_SORT_ORDERS = frozenset({"asc", "desc"})


def load_experiment_json_file(filepath: Path) -> Optional[Dict[str, Any]]:
    """
    Load a single experiment JSON file. Returns None on missing file or parse error.
    Adds ``_filepath`` and ``_filename`` for downstream helpers.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return None
        data["_filepath"] = str(filepath)
        data["_filename"] = filepath.name
        return data
    except (json.JSONDecodeError, OSError, TypeError):
        return None


def load_experiments_from_directory(experiments_dir: Path) -> List[Dict[str, Any]]:
    """
    Load all ``*.json`` under ``experiments_dir``, skip broken files, newest first.

    Sort key: ``experiment.timestamp`` (string, descending). Empty directory → [].
    """
    if not experiments_dir.exists():
        return []

    experiments: List[Dict[str, Any]] = []
    for json_file in sorted(experiments_dir.glob("*.json")):
        data = load_experiment_json_file(json_file)
        if data is not None:
            experiments.append(data)

    def get_timestamp(exp: Dict[str, Any]) -> str:
        return str(exp.get("experiment", {}).get("timestamp", "") or "")

    experiments.sort(key=get_timestamp, reverse=True)
    return experiments


def sort_raw_experiments(
    experiments: List[Dict[str, Any]],
    sort_by: str = "timestamp",
    sort_order: str = "desc",
) -> List[Dict[str, Any]]:
    """
    Stable sort of raw experiment dicts (pre-``extract_flat_fields``).

    - ``sort_by``: ``timestamp`` | ``sharpe`` | ``return`` (alias ``total_return``)
    - ``sort_order``: ``asc`` | ``desc`` (invalid values fall back to ``desc``)
    """
    key = (sort_by or "timestamp").lower()
    if key not in _SORT_KEYS:
        key = "timestamp"
    order = (sort_order or "desc").lower()
    if order not in _SORT_ORDERS:
        order = "desc"
    reverse = order == "desc"

    def sort_key(exp: Dict[str, Any]) -> Any:
        ex = exp.get("experiment", {})
        res = exp.get("results", {}) or {}
        if key == "timestamp":
            return str(ex.get("timestamp", "") or "")
        if key == "sharpe":
            try:
                return float(res.get("sharpe", 0.0))
            except (TypeError, ValueError):
                return 0.0
        # return / total_return
        try:
            return float(res.get("total_return", 0.0))
        except (TypeError, ValueError):
            return 0.0

    # timestamp: string compare works for YYYYMMDD_HHMMSS; desc = newest first
    return sorted(experiments, key=sort_key, reverse=reverse)
