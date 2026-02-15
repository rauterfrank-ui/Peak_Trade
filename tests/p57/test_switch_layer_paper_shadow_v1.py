from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.p57.switch_layer_paper_shadow_v1 import (
    P57RunContextV1,
    run_switch_layer_paper_shadow_v1,
)


def test_p57_denies_live() -> None:
    ctx = P57RunContextV1(mode="live", run_id="t0", out_dir=None)
    with pytest.raises(PermissionError):
        run_switch_layer_paper_shadow_v1([0.001] * 120, ctx)


def test_p57_denies_record() -> None:
    ctx = P57RunContextV1(mode="record", run_id="t1", out_dir=None)
    with pytest.raises(PermissionError):
        run_switch_layer_paper_shadow_v1([0.001] * 120, ctx)


def test_p57_paper_no_write_when_outdir_none(tmp_path: Path) -> None:
    ctx = P57RunContextV1(mode="paper", run_id="t2", out_dir=None)
    out = run_switch_layer_paper_shadow_v1([0.001] * 120, ctx)
    assert "decision" in out and "routing" in out and "meta" in out
    assert list(tmp_path.glob("*")) == []


def test_p57_paper_writes_evidence_when_outdir_set(tmp_path: Path) -> None:
    out_dir = tmp_path / "evi"
    ctx = P57RunContextV1(mode="paper", run_id="t3", out_dir=out_dir)
    out = run_switch_layer_paper_shadow_v1([0.001] * 120, ctx)

    assert (out_dir / "meta.json").is_file()
    assert (out_dir / "switch_decision.json").is_file()
    assert (out_dir / "routing.json").is_file()
    assert (out_dir / "switch_regime.json").is_file()
    assert (out_dir / "manifest.json").is_file()
    assert "p57_evidence_pack_v1" in (out_dir / "manifest.json").read_text()


def test_p57_allowlist_enables_routing(tmp_path: Path) -> None:
    ctx = P57RunContextV1(
        mode="paper",
        run_id="t4",
        out_dir=None,
        allow_bull_strategies=["s1"],
        allow_bear_strategies=[],
    )
    # bull-ish returns
    out = run_switch_layer_paper_shadow_v1([0.003] * 120, ctx)
    assert out["decision"].regime.value == "bull"
    assert out["routing"].ai_mode == "shadow"
    assert out["routing"].allowed_strategies == ("s1",)


def test_p57_deterministic(tmp_path: Path) -> None:
    prices = [0.002] * 120
    ctx1 = P57RunContextV1(mode="paper", run_id="t5", out_dir=tmp_path / "a")
    ctx2 = P57RunContextV1(mode="paper", run_id="t5", out_dir=tmp_path / "b")
    a = run_switch_layer_paper_shadow_v1(prices, ctx1)
    b = run_switch_layer_paper_shadow_v1(prices, ctx2)
    assert a["decision"] == b["decision"]
    assert a["routing"] == b["routing"]
