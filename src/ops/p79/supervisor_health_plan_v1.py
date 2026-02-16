from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class P79HealthPlanV1:
    mode: str  # paper|shadow only
    out_dir: Path
    pidfile: Optional[Path]
    max_age_sec: int
    require_p76_files: bool

    def validate(self) -> None:
        if self.mode not in ("paper", "shadow"):
            raise PermissionError(f"mode not allowed: {self.mode} (paper/shadow only)")
        if self.max_age_sec <= 0:
            raise ValueError("max_age_sec must be > 0")


def build_health_plan_v1(
    *,
    mode: str,
    out_dir: Path,
    pidfile: Optional[Path] = None,
    max_age_sec: int = 300,
    require_p76_files: bool = True,
) -> P79HealthPlanV1:
    plan = P79HealthPlanV1(
        mode=mode,
        out_dir=out_dir,
        pidfile=pidfile,
        max_age_sec=max_age_sec,
        require_p76_files=require_p76_files,
    )
    plan.validate()
    return plan
