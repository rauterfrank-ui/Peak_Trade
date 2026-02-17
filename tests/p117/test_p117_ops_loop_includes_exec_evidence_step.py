from pathlib import Path

import pytest

from src.ops.p98 import P98OpsLoopContextV1, run_ops_loop_orchestrator_v1

SUP_BASE = Path("out/ops/online_readiness_supervisor")
HAS_SUPERVISOR = SUP_BASE.exists() and bool(list(SUP_BASE.glob("run_*")))


@pytest.mark.skipif(not HAS_SUPERVISOR, reason="supervisor run_* not present")
def test_p117_step_present_and_skips_by_default(monkeypatch):
    monkeypatch.delenv("P117_ENABLE_EXEC_EVI", raising=False)
    ctx = P98OpsLoopContextV1(mode="shadow", max_age_sec=900, min_ticks=2, dry_run=True)
    rep = run_ops_loop_orchestrator_v1(ctx)
    names = [s["name"] for s in rep["steps"]]
    assert "p117_exec_evidence_optional" in names
    step = next(s for s in rep["steps"] if s["name"] == "p117_exec_evidence_optional")
    assert step["rc"] == 0
    assert "P117_SKIP" in (step.get("out") or "")


@pytest.mark.skipif(not HAS_SUPERVISOR, reason="supervisor run_* not present")
def test_p117_guard_rejects_dry_run_no(monkeypatch):
    monkeypatch.setenv("P117_ENABLE_EXEC_EVI", "YES")
    ctx = P98OpsLoopContextV1(mode="shadow", max_age_sec=900, min_ticks=2, dry_run=False)
    rep = run_ops_loop_orchestrator_v1(ctx)
    step = next(s for s in rep["steps"] if s["name"] == "p117_exec_evidence_optional")
    assert step["rc"] == 3
    assert "dry_run_must_be_yes" in (step.get("out") or "")


@pytest.mark.skipif(not HAS_SUPERVISOR, reason="supervisor run_* not present")
def test_p117_enable_runs_in_shadow_only(monkeypatch):
    monkeypatch.setenv("P117_ENABLE_EXEC_EVI", "YES")
    ctx = P98OpsLoopContextV1(mode="shadow", max_age_sec=900, min_ticks=2, dry_run=True)
    rep = run_ops_loop_orchestrator_v1(ctx)
    step = next(s for s in rep["steps"] if s["name"] == "p117_exec_evidence_optional")
    assert step["rc"] == 0
