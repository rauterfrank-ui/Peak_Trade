from pathlib import Path

import pytest

from src.ops.p62 import P62RunContextV1, run_online_readiness_shadow_session_v1


def test_p62_denies_live() -> None:
    prices = [0.001] * 200
    with pytest.raises(PermissionError):
        run_online_readiness_shadow_session_v1(prices, P62RunContextV1(mode="live", run_id="x"))


def test_p62_denies_record() -> None:
    prices = [0.001] * 200
    with pytest.raises(PermissionError):
        run_online_readiness_shadow_session_v1(prices, P62RunContextV1(mode="record", run_id="x"))


def test_p62_paper_deterministic(tmp_path: Path) -> None:
    prices = [0.001] * 200
    ctx = P62RunContextV1(mode="paper", run_id="demo", out_dir=tmp_path / "a")
    a = run_online_readiness_shadow_session_v1(prices, ctx)

    ctx2 = P62RunContextV1(mode="paper", run_id="demo", out_dir=tmp_path / "b")
    b = run_online_readiness_shadow_session_v1(prices, ctx2)

    assert a["shadow_plan"] == b["shadow_plan"]
    assert a["report"] == b["report"]


def test_p62_evidence_written_only_when_outdir(tmp_path: Path) -> None:
    prices = [0.001] * 200

    # No out_dir => no evidence
    ctx_no = P62RunContextV1(mode="paper", run_id="n", out_dir=None)
    run_online_readiness_shadow_session_v1(prices, ctx_no)
    assert list(tmp_path.glob("*")) == []

    # With out_dir => evidence written
    out_dir = tmp_path / "evi"
    ctx_yes = P62RunContextV1(mode="paper", run_id="y", out_dir=out_dir)
    run_online_readiness_shadow_session_v1(prices, ctx_yes)
    assert (out_dir / "meta.json").is_file()
    assert (out_dir / "shadow_plan.json").is_file()
    assert (out_dir / "readiness_report.json").is_file()
    assert (out_dir / "manifest.json").is_file()


def test_p62_output_json_serializable(tmp_path: Path) -> None:
    import json

    prices = [0.001] * 200
    ctx = P62RunContextV1(mode="paper", run_id="j", out_dir=tmp_path)
    out = run_online_readiness_shadow_session_v1(prices, ctx)

    assert isinstance(out, dict)
    # Must be JSON-serializable (no non-dict objects that fail)
    json_str = json.dumps(out)
    assert isinstance(json_str, str)
    assert "shadow_plan" in out
    assert "report" in out
    assert "meta" in out
