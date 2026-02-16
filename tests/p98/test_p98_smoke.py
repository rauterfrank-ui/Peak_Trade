from pathlib import Path

import pytest

from src.ops.p98 import P98OpsLoopContextV1, run_ops_loop_orchestrator_v1

SUP_BASE = Path("out/ops/online_readiness_supervisor")
HAS_SUPERVISOR = SUP_BASE.exists() and bool(list(SUP_BASE.glob("run_*")))


@pytest.mark.skipif(not HAS_SUPERVISOR, reason="supervisor run_* not present")
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
