import subprocess
from pathlib import Path

import pytest

from src.ops.p98 import P98OpsLoopContextV1, run_ops_loop_orchestrator_v1

SUP_BASE = Path("out/ops/online_readiness_supervisor")
HAS_SUPERVISOR = SUP_BASE.exists() and bool(list(SUP_BASE.glob("run_*")))


def _p95_launchd_ready() -> bool:
    """True if p95 meta gate would pass (launchd jobs present)."""
    try:
        uid = subprocess.run(
            ["id", "-u"], capture_output=True, text=True, check=True
        ).stdout.strip()
        r = subprocess.run(
            ["launchctl", "print", f"gui/{uid}/com.peaktrade.p93-status-dashboard"],
            capture_output=True,
            timeout=2,
        )
        return r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


HAS_P95_READY = _p95_launchd_ready()


@pytest.mark.skipif(
    not HAS_SUPERVISOR or not HAS_P95_READY,
    reason="supervisor run_* not present or p95 launchd jobs missing",
)
def test_p98_smoke_jsonable_dict_boundary() -> None:
    ctx = P98OpsLoopContextV1(
        out_dir=None, mode="shadow", max_age_sec=900, min_ticks=2, dry_run=True
    )
    out = run_ops_loop_orchestrator_v1(ctx)
    assert isinstance(out, dict)
    assert out["meta"]["ok"] is True
    assert isinstance(out["steps"], list)


def test_p98_context_instantiation() -> None:
    ctx = P98OpsLoopContextV1(
        out_dir=None, mode="shadow", max_age_sec=900, min_ticks=2, dry_run=True
    )
    assert ctx.mode == "shadow"
    assert ctx.dry_run is True
