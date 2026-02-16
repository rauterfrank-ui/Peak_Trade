from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class P78SupervisorPlanV1:
    mode: str  # "paper" | "shadow"
    out_dir: Path
    run_id: str
    interval_sec: int
    iterations: int
    pidfile: Path
    max_logs: int
    gate_variant: str = "p86"  # "p76" | "p86" — P87: p86 = readiness+ingest gate (default)


def build_supervisor_plan_v1(
    *,
    mode: str,
    out_dir: Path,
    run_id: str,
    interval_sec: int = 30,
    iterations: int = 0,
    pidfile: Optional[Path] = None,
    max_logs: int = 50,
    gate_variant: str = "p86",
) -> P78SupervisorPlanV1:
    if mode not in ("paper", "shadow"):
        raise ValueError("mode must be 'paper' or 'shadow' (live/record hard-blocked)")
    if gate_variant not in ("p76", "p86"):
        raise ValueError("gate_variant must be 'p76' or 'p86'")
    if interval_sec < 0:
        raise ValueError("interval_sec must be >= 0")
    if iterations < 0:
        raise ValueError("iterations must be >= 0")
    if max_logs < 1:
        raise ValueError("max_logs must be >= 1")
    if pidfile is None:
        pidfile = Path("/tmp/p78_online_readiness_supervisor.pid")
    return P78SupervisorPlanV1(
        mode=mode,
        out_dir=out_dir,
        run_id=run_id,
        interval_sec=interval_sec,
        iterations=iterations,
        pidfile=pidfile,
        max_logs=max_logs,
        gate_variant=gate_variant,
    )
