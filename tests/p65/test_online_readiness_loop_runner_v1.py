from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.p65 import P65RunContextV1, run_online_readiness_loop_runner_v1


def test_p65_blocks_live_and_record() -> None:
    prices = [0.001] * 200
    with pytest.raises(PermissionError):
        run_online_readiness_loop_runner_v1(
            prices, P65RunContextV1(mode="live", run_id="x", loops=1)
        )
    with pytest.raises(PermissionError):
        run_online_readiness_loop_runner_v1(
            prices, P65RunContextV1(mode="record", run_id="x", loops=1)
        )


def test_p65_loops_must_be_positive() -> None:
    prices = [0.001] * 200
    with pytest.raises(ValueError):
        run_online_readiness_loop_runner_v1(
            prices, P65RunContextV1(mode="paper", run_id="x", loops=0)
        )


def test_p65_returns_jsonable_dict_and_has_expected_shape(tmp_path: Path) -> None:
    prices = [0.001] * 200
    out = run_online_readiness_loop_runner_v1(
        prices,
        P65RunContextV1(mode="paper", run_id="demo", loops=2, out_dir=tmp_path / "p65_demo"),
    )
    assert isinstance(out, dict)
    assert set(out.keys()) == {"meta", "loops"}
    assert out["meta"]["loops"] == 2
    assert len(out["loops"]) == 2
    json.dumps(out)  # jsonable boundary


def test_p65_allowlist_can_enable_shadow_in_bull(tmp_path: Path) -> None:
    prices = [0.002] * 200  # bullish
    out = run_online_readiness_loop_runner_v1(
        prices,
        P65RunContextV1(
            mode="paper",
            run_id="bull",
            loops=1,
            out_dir=tmp_path / "p65_bull",
            allow_bull_strategies=["s1"],
        ),
    )
    loop0 = out["loops"][0]
    # P64 returns {"meta":..., "p63": {...}}; routing is in p63.switch
    p63 = loop0["p63"]
    routing = p63["switch"]["routing"]
    assert routing["ai_mode"] in ("shadow", "disabled")
    # with allowlist, bull should be shadow (deny-by-default overridden)
    assert routing["ai_mode"] == "shadow"
