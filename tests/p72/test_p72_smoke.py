from pathlib import Path

import pytest

from src.ops.p72 import P72PackContextV1, run_shadowloop_pack_v1


def test_p72_smoke() -> None:
    import src.ops.p72  # noqa: F401

    assert True


def test_p72_pack_gate_then_loop(tmp_path: Path) -> None:
    ctx = P72PackContextV1(
        mode="shadow",
        run_id="t",
        out_dir=tmp_path,
        allow_bull_strategies=["s1"],
        allow_bear_strategies=["s1"],
        iterations=1,
        interval_seconds=0.0,
    )
    out = run_shadowloop_pack_v1(ctx)
    assert out["gate_ok"] is True
    assert out["loop_run"] is not None
    assert (tmp_path / "p71_health_gate_report.json").exists()


def test_p72_blocks_live_record(tmp_path: Path) -> None:
    with pytest.raises(PermissionError):
        run_shadowloop_pack_v1(P72PackContextV1(mode="live", run_id="x", out_dir=tmp_path))
