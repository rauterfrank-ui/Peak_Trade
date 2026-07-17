"""Contracts for OBL_B05 trend_following side-impact diagnostic v1.

Read-only diagnostic: no productive semantics mutation.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SSOT_PATH = (
    REPO_ROOT / "config" / "governance" / "obl_b05_trend_following_side_impact_diagnostic_v1.json"
)
GOV_DOC = REPO_ROOT / "docs" / "governance" / "OBL_B05_TREND_FOLLOWING_SIDE_IMPACT_DIAGNOSTIC_V1.md"
RUNNER = (
    REPO_ROOT / "scripts" / "research" / "run_obl_b05_trend_following_side_impact_diagnostic_v1.py"
)
ADAPTER = REPO_ROOT / "src" / "backtest" / "strategy_signal_suitability_agreement_adapter_v1.py"

_ALLOWED_IMPACT = frozenset(
    {
        "NO_OBSERVABLE_IMPACT",
        "DIRECTIONAL_AGREEMENT_UNBLOCKED",
        "SHIFTED_TO_COMPOSITION",
        "SHIFTED_TO_LATER_STAGE",
        "ENTER_OUTCOME_OBSERVED",
        "CONTRACT_OR_RECONCILIATION_FAILURE",
    }
)


def _ssot() -> dict:
    return json.loads(SSOT_PATH.read_text(encoding="utf-8"))


def test_ssot_and_governance_markers_present() -> None:
    assert SSOT_PATH.is_file()
    assert GOV_DOC.is_file()
    assert RUNNER.is_file()
    data = _ssot()
    body = GOV_DOC.read_text(encoding="utf-8")
    assert data["slice_id"] == "OBL_B05_TREND_FOLLOWING_SIDE_IMPACT_DIAGNOSTIC_V1"
    assert data["TREND_FOLLOWING_SIDE_IMPACT_DIAGNOSTIC_COMPLETE"] is True
    assert data["PRODUCTIVE_SEMANTICS_CHANGED"] is False
    assert data["ADDITIONAL_PRODUCER_ACTIVATED"] is False
    assert data["BOLLINGER_SIDE_ACTIVATED"] is False
    assert data["MACD_SIDE_ACTIVATED"] is False
    assert data["LIVE_AUTHORIZED"] is False
    assert data["ORDERS_ENABLED"] is False
    assert "DOCS_TOKEN_OBL_B05_TREND_FOLLOWING_SIDE_IMPACT_DIAGNOSTIC_V1" in body
    assert "TREND_FOLLOWING_SIDE_IMPACT_DIAGNOSTIC_COMPLETE: true" in body


def test_impact_classification_closed_world() -> None:
    data = _ssot()
    classes = data["impact_classification"]
    assert isinstance(classes, list) and classes
    assert set(classes) <= _ALLOWED_IMPACT
    assert "DIRECTIONAL_AGREEMENT_UNBLOCKED" in classes
    assert "SHIFTED_TO_COMPOSITION" in classes
    assert data["ENTER_OUTCOME_OBSERVED"] is False


def test_control_vs_ratified_stage_shift_and_reconciliation() -> None:
    data = _ssot()
    assert data["control_dominant_first_failed_stage"] == "directional_agreement"
    assert data["ratified_dominant_first_failed_stage"] == "composition"
    for key in ("eval_control", "eval_ratified", "panel_control", "panel_ratified"):
        summary = data[key]
        n = summary["entry_bar_count"]
        assert n == sum(summary["taxonomy_outcome_counts"].values())
        assert n == sum(summary["first_failed_stage_counts"].values())
        assert n == sum(summary["entry_side_counts"].values())
        assert n == sum(summary["agreement_direction_counts"].values())
    assert (
        data["eval_control"]["entry_side_counts"].get("NONE", 0)
        == data["eval_control"]["entry_bar_count"]
    )
    assert (
        data["eval_ratified"]["entry_side_counts"].get("LONG", 0)
        == data["eval_ratified"]["entry_bar_count"]
    )
    assert data["eval_ratified"]["entry_side_counts"].get("SHORT", 0) == 0
    # Warmup bars stay NONE/unresolved; only post-warmup ENTRY bars shift.
    assert data["changed_bar_count"] == data["panel_control"]["BLOCKED_DIRECTIONAL_AGREEMENT"]
    assert data["changed_bar_count"] == data["panel_ratified"]["BLOCKED_COMPOSITION"]
    assert data["panel_control"]["first_failed_stage_counts"].get("warmup", 0) == data[
        "panel_ratified"
    ]["first_failed_stage_counts"].get("warmup", 0)
    assert data["changed_bar_count"] > 0


def test_bollinger_non_trend_following_unchanged_and_none_side() -> None:
    data = _ssot()
    assert data["bollinger_eval_unchanged"] is True
    boll = data["bollinger_eval_ratified_path"]
    assert boll["entry_side_counts"].get("NONE", 0) == boll["entry_bar_count"]
    assert boll["entry_side_counts"].get("LONG", 0) == 0
    assert data["unchanged_non_trend_following_bar_count"] == boll["entry_bar_count"]


def test_next_dominant_blocker_is_composition_observe() -> None:
    data = _ssot()
    blocker = data["next_dominant_blocker"]
    assert blocker["stage"] == "composition"
    assert "CompositionStatus.OBSERVE" in blocker["contract_path"]
    assert blocker["panel_count"] == data["panel_ratified"]["BLOCKED_COMPOSITION"]
    assert data["panel_ratified"]["ENTER_LONG"] == 0
    assert data["panel_ratified"]["ENTER_SHORT"] == 0
    assert data["panel_ratified"]["HOLD"] == 0


def test_runner_is_diagnostic_only_and_adapter_not_mutated_by_slice_files() -> None:
    runner = RUNNER.read_text(encoding="utf-8")
    assert "GO_OBL_B05_TREND_FOLLOWING_SIDE_IMPACT_DIAGNOSTIC_V1" in runner
    assert "force_none" in runner
    assert "_resolve_entry_side_carrier_v1" in runner
    # Productive adapter still owns ratification; this slice must not rewrite it.
    adapter = ADAPTER.read_text(encoding="utf-8")
    assert "_TREND_FOLLOWING_ENTRY_SIDE_RATIFIED_OWNER" in adapter
    assert "StrategyEntrySideCarrierV1.LONG" in adapter


def test_eval_only_control_ratified_shift_dynamic(tmp_path: Path) -> None:
    """Dynamic smoke: eval instrument A/B shift DA -> composition."""
    archive = Path(
        "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
        "research/full_canonical_system_economic_evidence_generation_v1_offline_execution_v0_"
        "20260716T015033Z"
    )
    if not archive.is_dir():
        pytest.skip("durable archive unavailable")
    out = tmp_path / "diag"
    import subprocess
    import sys

    proc = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--go-token",
            "GO_OBL_B05_TREND_FOLLOWING_SIDE_IMPACT_DIAGNOSTIC_V1",
            "--archive-dir",
            str(archive),
            "--output-dir",
            str(out),
            "--eval-only",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr[-2000:]
    summary = json.loads((out / "impact_summary.json").read_text(encoding="utf-8"))
    assert summary["eval_control"]["dominant_first_failed_stage"] == "directional_agreement"
    assert summary["eval_ratified"]["dominant_first_failed_stage"] == "composition"
    assert summary["bollinger_eval_unchanged"] is True
    assert summary["PRODUCTIVE_SEMANTICS_CHANGED"] is False
