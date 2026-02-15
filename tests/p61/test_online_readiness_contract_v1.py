from pathlib import Path

import pytest

from src.ops.p61.run_online_readiness_v1 import P61RunContextV1, run_online_readiness_v1


def test_p61_denies_live():
    prices = [0.001] * 200
    with pytest.raises(PermissionError):
        run_online_readiness_v1(prices, P61RunContextV1(mode="live", run_id="x"))


def test_p61_denies_record():
    prices = [0.001] * 200
    with pytest.raises(PermissionError):
        run_online_readiness_v1(prices, P61RunContextV1(mode="record", run_id="x"))


def test_p61_runs_paper_and_is_jsonable(tmp_path: Path):
    prices = [0.001] * 200
    out = run_online_readiness_v1(
        prices, P61RunContextV1(mode="paper", run_id="demo", out_dir=tmp_path)
    )
    assert isinstance(out, dict)
    assert out["meta"]["mode"] == "paper"
    assert out["report"]["version"] == "online_readiness_contract_v1"
    assert "switch" in out
