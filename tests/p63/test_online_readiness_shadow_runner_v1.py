from pathlib import Path

import pytest

from src.ops.p63 import P63RunContextV1, run_online_readiness_shadow_runner_v1


def test_p63_blocks_live_record() -> None:
    with pytest.raises(PermissionError):
        run_online_readiness_shadow_runner_v1(
            [0.001] * 200, P63RunContextV1(mode="live", run_id="x")
        )


def test_p63_paper_jsonable_no_outdir() -> None:
    out = run_online_readiness_shadow_runner_v1(
        [0.001] * 200, P63RunContextV1(mode="paper", run_id="x")
    )
    assert out["meta"]["p63_run_id"] == "x"
    assert isinstance(out, dict)


def test_p63_shadow_with_allowlists() -> None:
    out = run_online_readiness_shadow_runner_v1(
        [0.002] * 220,
        P63RunContextV1(mode="shadow", run_id="x", allow_bull_strategies=["s1"]),
    )
    assert out["meta"]["mode"] == "shadow"


def test_p63_writes_only_when_outdir(tmp_path: Path) -> None:
    out = run_online_readiness_shadow_runner_v1(
        [0.001] * 200,
        P63RunContextV1(mode="paper", run_id="x", out_dir=tmp_path),
    )
    assert out["meta"]["out_dir"] is not None
