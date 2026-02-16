from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class P77DaemonPlanV1:
    tick_ts_utc: str
    run_id: str
    out_dir: Optional[Path]


def _utc_ts_compact() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def build_daemon_plan_v1(
    *,
    base_out_dir: Optional[Path],
    run_id_prefix: str,
    tick: int,
    ts_override_utc: Optional[str] = None,
) -> P77DaemonPlanV1:
    """
    Deterministic plan for where each daemon tick writes evidence.
    No IO performed here.
    """
    tick_ts = ts_override_utc or _utc_ts_compact()
    run_id = f"{run_id_prefix}_{tick_ts}_t{tick:04d}"
    out_dir = None
    if base_out_dir is not None:
        out_dir = Path(base_out_dir) / run_id
    return P77DaemonPlanV1(tick_ts_utc=tick_ts, run_id=run_id, out_dir=out_dir)
