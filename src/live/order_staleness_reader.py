"""
Live Runs Order / Event Staleness Reader — Read-only signal for Ops Cockpit.

Derives ``stale_state.order`` from the newest ``live_runs/*/events.*`` artifact
mtime and non-empty event rows. Does **not** assert exchange order state; log
freshness only. Fail-safe: returns ``unknown`` when no usable signal.

NO execution authority. Read-only.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


def get_live_runs_order_staleness(
    base_dir: Path,
    *,
    max_age_hours: float = 24.0,
) -> Dict[str, Any]:
    """
    Read-only. Uses the same age threshold idea as ``exposure_reader``.

    Returns:
        order_staleness: ``ok`` | ``stale`` | ``unknown``
        data_source: ``live_runs`` | ``none``
        last_events_utc: ISO timestamp of newest qualifying events file, or None
    """
    out: Dict[str, Any] = {
        "order_staleness": "unknown",
        "data_source": "none",
        "last_events_utc": None,
    }

    if not base_dir.exists() or not base_dir.is_dir():
        return out

    try:
        from .run_logging import list_runs, load_run_events
    except ImportError as e:
        logger.debug("order_staleness_reader: run_logging not available: %s", e)
        return out

    run_ids = list_runs(base_dir)
    if not run_ids:
        return out

    latest_mtime: float = 0.0

    for run_id in run_ids:
        run_dir = base_dir / run_id
        if not run_dir.is_dir():
            continue
        try:
            events_df = load_run_events(run_dir)
        except FileNotFoundError:
            continue
        except Exception as e:
            logger.debug("order_staleness_reader: skip run %s: %s", run_id, e)
            continue

        if len(events_df) == 0:
            continue

        for name in ("events.parquet", "events.csv"):
            p = run_dir / name
            if p.exists():
                m = p.stat().st_mtime
                if m > latest_mtime:
                    latest_mtime = m
                break

    if latest_mtime <= 0.0:
        return out

    out["data_source"] = "live_runs"
    dt = datetime.fromtimestamp(latest_mtime, tz=timezone.utc)
    out["last_events_utc"] = dt.isoformat().replace("+00:00", "Z")
    age_hours = (datetime.now(timezone.utc).timestamp() - latest_mtime) / 3600.0
    out["order_staleness"] = "stale" if age_hours > max_age_hours else "ok"

    return out
