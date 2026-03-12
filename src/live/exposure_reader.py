"""
Live Runs Exposure Reader — Read-only aggregation for Ops Cockpit.

Reads exposure from live_runs/ (position_size * price per run, summed).
Used by Ops Cockpit exposure_state when live_runs data is available.

NO execution authority. Read-only. Fail-safe (returns empty on error).
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import pandas as pd

logger = logging.getLogger(__name__)


def get_live_runs_exposure_summary(
    base_dir: Path,
    *,
    max_age_hours: float = 24.0,
) -> Dict[str, Any]:
    """
    Read-only. Aggregates exposure from live_runs/ events.

    For each run: last event position_size * (price or close) → sum.
    Returns dict compatible with exposure_state optional fields.

    Args:
        base_dir: Path to live_runs/ directory
        max_age_hours: Treat data stale if newest event file older than this

    Returns:
        Dict with observed_exposure, observed_ccy, last_updated_utc, data_source,
        run_count, stale. Empty dict or partial on error.
    """
    result: Dict[str, Any] = {
        "data_source": "live_runs",
        "run_count": 0,
        "observed_exposure": None,
        "observed_ccy": "unknown",
        "last_updated_utc": None,
        "stale": True,
    }

    if not base_dir.exists() or not base_dir.is_dir():
        return result

    try:
        from .run_logging import list_runs, load_run_events
    except ImportError as e:
        logger.debug("exposure_reader: run_logging not available: %s", e)
        return result

    run_ids = list_runs(base_dir)
    if not run_ids:
        return result

    total_exposure = 0.0
    ccys: set[str] = set()
    latest_mtime: float = 0.0

    for run_id in run_ids:
        run_dir = base_dir / run_id
        try:
            events_df = load_run_events(run_dir)
        except FileNotFoundError:
            continue
        except Exception as e:
            logger.debug("exposure_reader: skip run %s: %s", run_id, e)
            continue

        if len(events_df) == 0:
            continue

        last_row = events_df.iloc[-1]
        position_size = last_row.get("position_size")
        price = last_row.get("price") or last_row.get("close")

        if position_size is None or pd.isna(position_size):
            continue
        if price is None or pd.isna(price):
            continue

        try:
            pos = float(position_size)
            pr = float(price)
            total_exposure += abs(pos * pr)
        except (TypeError, ValueError):
            continue

        # Ccy from metadata if available
        meta_path = run_dir / "meta.json"
        if meta_path.exists():
            try:
                with open(meta_path, encoding="utf-8") as f:
                    meta = json.load(f)
                symbol = meta.get("symbol", "")
                if "/" in symbol:
                    ccys.add(symbol.split("/", 1)[1].strip())
            except Exception:
                pass

        # Freshness from events file mtime
        for name in ("events.parquet", "events.csv"):
            p = run_dir / name
            if p.exists():
                m = p.stat().st_mtime
                if m > latest_mtime:
                    latest_mtime = m
                break

    result["run_count"] = len(run_ids)
    if total_exposure > 0:
        result["observed_exposure"] = round(total_exposure, 2)
        result["observed_ccy"] = (
            list(ccys)[0] if len(ccys) == 1 else ("mixed" if ccys else "unknown")
        )
    if latest_mtime > 0:
        dt = datetime.fromtimestamp(latest_mtime, tz=timezone.utc)
        result["last_updated_utc"] = dt.isoformat().replace("+00:00", "Z")
        age_hours = (datetime.now(timezone.utc).timestamp() - latest_mtime) / 3600.0
        result["stale"] = age_hours > max_age_hours

    return result
