from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class P98OpsLoopContextV1:
    out_dir: Path | None = None
    mode: str = "shadow"
    max_age_sec: int = 900
    min_ticks: int = 2
    dry_run: bool = False  # forwards to P96 DRY_RUN


def _sh(
    cmd: list[str], env: dict[str, str] | None = None, cwd: str | None = None
) -> tuple[int, str]:
    p = subprocess.run(cmd, text=True, capture_output=True, env=env, cwd=cwd)
    out = (p.stdout or "") + (p.stderr or "")
    return p.returncode, out.strip()


def run_ops_loop_orchestrator_v1(ctx: P98OpsLoopContextV1) -> dict:
    root = Path(__file__).resolve().parents[3]
    env = os.environ.copy()
    env["MODE"] = ctx.mode
    env["MAX_AGE_SEC"] = str(ctx.max_age_sec)
    env["MIN_TICKS"] = str(ctx.min_ticks)
    if ctx.out_dir is not None:
        env["OUT_DIR"] = str(ctx.out_dir)
    if ctx.dry_run:
        env["DRY_RUN"] = "YES"

    steps = []

    def step(name: str, cmd: list[str]) -> None:
        rc, out = _sh(cmd, env=env, cwd=str(root))
        steps.append({"name": name, "rc": rc, "out": out})
        if rc != 0:
            raise RuntimeError(f"{name} failed rc={rc}")

    # A) Ensure supervisor is alive (status-only; do not start here)
    step("p95_meta_gate", ["bash", str(root / "scripts/ops/p95_ops_health_meta_gate_v1.sh")])

    # B) If P91 is scheduled, guard-kickstart it (DRY_RUN-aware)
    step(
        "p96_p91_kickstart_when_ready",
        ["bash", str(root / "scripts/ops/p91_kickstart_when_ready_v1.sh")],
    )

    # C) Produce one fresh P93 dashboard snapshot (one-shot)
    step(
        "p93_status_dashboard",
        ["bash", str(root / "scripts/ops/p93_online_readiness_status_dashboard_v1.sh")],
    )

    # D) Apply retention for P91 and P93 artifacts (no-op safe)
    step(
        "p92_p91_retention",
        ["bash", str(root / "scripts/ops/p92_p91_audit_snapshot_retention_v1.sh")],
    )
    step(
        "p94_p93_retention",
        ["bash", str(root / "scripts/ops/p94_p93_status_dashboard_retention_v1.sh")],
    )

    report = {
        "meta": {
            "ok": True,
            "mode": ctx.mode,
            "max_age_sec": ctx.max_age_sec,
            "min_ticks": ctx.min_ticks,
            "dry_run": ctx.dry_run,
        },
        "steps": steps,
    }
    return json.loads(json.dumps(report))  # jsonable boundary
