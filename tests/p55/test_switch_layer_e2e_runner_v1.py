from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.p55.switch_layer_e2e_runner_v1 import P55RunContextV1, run_switch_layer_e2e_v1


def test_p55_denies_live_by_default() -> None:
    prices = [0.001] * 120
    ctx = P55RunContextV1(mode="live", out_dir=None, run_id="t0")
    with pytest.raises(PermissionError):
        run_switch_layer_e2e_v1(prices, ctx)


def test_p55_no_write_when_outdir_none(tmp_path: Path) -> None:
    prices = [0.001] * 120
    ctx = P55RunContextV1(mode="paper", out_dir=None, run_id="t1")
    out = run_switch_layer_e2e_v1(prices, ctx, meta={"k": "v"})
    assert "decision" in out and "routing" in out and "meta" in out
    # no files written (out_dir None)
    assert list(tmp_path.glob("*")) == []


def test_p55_writes_evidence_pack_when_outdir_set(tmp_path: Path) -> None:
    prices = [0.001] * 120
    out_dir = tmp_path / "evi"
    ctx = P55RunContextV1(mode="paper", out_dir=out_dir, run_id="t2")
    out = run_switch_layer_e2e_v1(prices, ctx)

    assert (out_dir / "meta.json").is_file()
    assert (out_dir / "switch_decision.json").is_file()
    assert (out_dir / "routing.json").is_file()
    assert (out_dir / "manifest.json").is_file()

    # manifest deterministic basics
    manifest = (out_dir / "manifest.json").read_text(encoding="utf-8")
    assert "p55_evidence_pack_v1" in manifest
    assert "switch_decision.json" in manifest
    assert "routing.json" in manifest
    assert out["meta"]["p55_run_id"] == "t2"


def test_p55_deterministic_same_input_same_output(tmp_path: Path) -> None:
    prices = [0.001] * 120
    ctx1 = P55RunContextV1(mode="paper", out_dir=tmp_path / "a", run_id="t3")
    ctx2 = P55RunContextV1(mode="paper", out_dir=tmp_path / "b", run_id="t3")

    out1 = run_switch_layer_e2e_v1(prices, ctx1)
    out2 = run_switch_layer_e2e_v1(prices, ctx2)

    assert out1["decision"] == out2["decision"]
    assert out1["routing"] == out2["routing"]
