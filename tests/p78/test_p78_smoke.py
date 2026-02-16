from pathlib import Path

import pytest

from src.ops.p78.online_readiness_supervisor_plan_v1 import build_supervisor_plan_v1


def test_p78_build_plan_shadow_ok(tmp_path: Path) -> None:
    plan = build_supervisor_plan_v1(
        mode="shadow",
        out_dir=tmp_path / "out",
        run_id="demo",
        interval_sec=0,
        iterations=1,
    )
    assert plan.mode == "shadow"
    assert plan.iterations == 1


@pytest.mark.parametrize("bad_mode", ["live", "record", "LIVE", ""])
def test_p78_build_plan_blocks_live_record(bad_mode: str, tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        build_supervisor_plan_v1(mode=bad_mode, out_dir=tmp_path, run_id="x")
