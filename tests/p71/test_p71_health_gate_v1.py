from pathlib import Path

import pytest

from src.ops.p71 import P71GateContextV1, run_online_readiness_health_gate_v1


def test_p71_blocks_live_record() -> None:
    prices = [0.001] * 200
    with pytest.raises(PermissionError):
        run_online_readiness_health_gate_v1(prices, P71GateContextV1(mode="live", run_id="x"))
    with pytest.raises(PermissionError):
        run_online_readiness_health_gate_v1(prices, P71GateContextV1(mode="record", run_id="x"))


def test_p71_shadow_ok_writes_when_outdir(tmp_path: Path) -> None:
    prices = [0.001] * 240
    ctx = P71GateContextV1(
        mode="shadow",
        run_id="t",
        out_dir=tmp_path,
        allow_bull_strategies=["s1"],
        allow_bear_strategies=["s1"],
    )
    out = run_online_readiness_health_gate_v1(prices, ctx)
    assert out["overall_ok"] is True
    assert (tmp_path / "p71_health_gate_report.json").exists()
    assert (tmp_path / "p71_health_gate_manifest.json").exists()
