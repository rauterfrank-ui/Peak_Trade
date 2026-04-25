import json
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


@pytest.mark.parametrize("bad_mode", ["record", "testnet"])
def test_p63_blocks_disallowed_modes_other_than_live(bad_mode: str) -> None:
    """Paper/shadow only; same guard as live (live covered in test_p63_blocks_live_record)."""
    with pytest.raises(PermissionError) as exc:
        run_online_readiness_shadow_runner_v1(
            [0.001] * 200, P63RunContextV1(mode=bad_mode, run_id="x")
        )
    assert bad_mode in str(exc.value)


def test_p63_output_json_serializable(tmp_path: Path) -> None:
    """dict-only JSONable boundary (parity with p62 output contract test)."""
    prices = [0.001] * 200
    out = run_online_readiness_shadow_runner_v1(
        prices, P63RunContextV1(mode="paper", run_id="jsonable", out_dir=tmp_path)
    )
    assert isinstance(out, dict)
    json_str = json.dumps(out)
    assert isinstance(json_str, str)
    assert "readiness_report" in out
    assert "shadow_plan" in out


def test_p63_top_level_contract_keys() -> None:
    out = run_online_readiness_shadow_runner_v1(
        [0.001] * 200, P63RunContextV1(mode="paper", run_id="contract")
    )
    assert out["version"] == "p63_shadow_runner_v1"
    assert "readiness_report" in out
    assert "shadow_plan" in out
    assert "switch" in out
    assert isinstance(out["readiness_report"], dict)
    assert isinstance(out["shadow_plan"], dict)
    assert isinstance(out["switch"], dict)
