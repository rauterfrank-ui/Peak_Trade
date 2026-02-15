from pathlib import Path

import pytest

from src.ops.p58 import P58RunContextV1, run_switch_layer_online_readiness_v1


def test_p58_denies_live_record() -> None:
    prices = [0.001] * 200
    with pytest.raises(PermissionError):
        run_switch_layer_online_readiness_v1(prices, P58RunContextV1(mode="live", run_id="x"))
    with pytest.raises(PermissionError):
        run_switch_layer_online_readiness_v1(prices, P58RunContextV1(mode="record", run_id="x"))


def test_p58_no_outdir_no_write(tmp_path: Path) -> None:
    prices = [0.001] * 200
    out = run_switch_layer_online_readiness_v1(
        prices, P58RunContextV1(mode="paper", run_id="demo", out_dir=None)
    )
    assert "readiness" in out
    assert out["readiness"]["has_out_dir"] is False


def test_p58_with_outdir_writes_evidence(tmp_path: Path) -> None:
    prices = [0.001] * 200
    outdir = tmp_path / "p58"
    out = run_switch_layer_online_readiness_v1(
        prices, P58RunContextV1(mode="paper", run_id="demo", out_dir=outdir)
    )
    assert outdir.exists()
    assert (outdir / "manifest.json").exists()
    assert (outdir / "routing.json").exists()
    assert (outdir / "switch_decision.json").exists()
    assert (outdir / "meta.json").exists()


def test_p58_allowlist_fields_roundtrip(tmp_path: Path) -> None:
    prices = [0.002] * 200
    outdir = tmp_path / "p58_allow"
    out = run_switch_layer_online_readiness_v1(
        prices,
        P58RunContextV1(
            mode="shadow",
            run_id="demo",
            out_dir=outdir,
            allow_bull_strategies=["s1"],
            allow_bear_strategies=[],
        ),
    )
    assert out["readiness"]["allow_bull_n"] == 1
    assert out["readiness"]["allow_bear_n"] == 0
