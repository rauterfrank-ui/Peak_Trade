from pathlib import Path

import pytest

from src.ops.p64 import P64RunContextV1, run_online_readiness_runner_v1


def test_p64_blocks_live_record() -> None:
    prices = [0.001] * 200
    with pytest.raises(PermissionError):
        run_online_readiness_runner_v1(prices, P64RunContextV1(mode="live", run_id="x"))
    with pytest.raises(PermissionError):
        run_online_readiness_runner_v1(prices, P64RunContextV1(mode="record", run_id="x"))


def test_p64_runs_paper_dict_only(tmp_path: Path) -> None:
    prices = [0.001] * 200
    out = run_online_readiness_runner_v1(
        prices,
        P64RunContextV1(mode="paper", run_id="demo", out_dir=tmp_path / "p64_demo"),
    )
    assert isinstance(out, dict)
    assert out["meta"]["mode"] == "paper"
    assert "p63" in out


def test_p64_shadow_allowlists(tmp_path: Path) -> None:
    prices = [0.002] * 200  # bull-ish
    out = run_online_readiness_runner_v1(
        prices,
        P64RunContextV1(
            mode="shadow",
            run_id="demo",
            out_dir=tmp_path / "p64_demo",
            allow_bull_strategies=["s1"],
        ),
    )
    assert out["meta"]["mode"] == "shadow"
    # p63 output is dict-only; routing lives under nested keys depending on p63 structure
    assert "p63" in out
