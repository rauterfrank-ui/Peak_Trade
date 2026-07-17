"""Contracts for OBL_B05 Bollinger long-semantic decision + baseline v1.

Decision C: CONTRACT_REMAINS_AMBIGUOUS — no productive side activation.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import src.backtest.strategy_signal_suitability_agreement_adapter_v1 as adapter_mod
from src.backtest.strategy_signal_suitability_agreement_adapter_v1 import (
    normalize_strategy_signal_to_suitability_agreement_material_v1,
)
from trading.master_v2.strategy_suitability_agreement_material_v1 import (
    StrategyAgreementEventKindV1,
    StrategyEntrySideCarrierV1,
    StrategySignalEncodingClassV1,
)
from tests.backtest.test_strategy_signal_suitability_agreement_adapter_v1 import (
    _binding,
    _provenance,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SSOT_PATH = REPO_ROOT / "config" / "governance" / "obl_b05_bollinger_long_semantic_decision_v1.json"
GOV_DOC = REPO_ROOT / "docs" / "governance" / "OBL_B05_BOLLINGER_LONG_SEMANTIC_DECISION_V1.md"
RUNNER = (
    REPO_ROOT / "scripts" / "ops" / "run_obl_b05_bollinger_long_semantic_decision_baseline_v1.py"
)
ADAPTER = REPO_ROOT / "src" / "backtest" / "strategy_signal_suitability_agreement_adapter_v1.py"
BOLLINGER_SRC = REPO_ROOT / "src" / "strategies" / "bollinger.py"

_ALLOWED_DECISIONS = frozenset(
    {
        "LONG_ONLY_ENTRY_EXIT",
        "SIDE_NEUTRAL_ENTRY_EXIT",
        "CONTRACT_REMAINS_AMBIGUOUS",
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
    assert data["slice_id"].startswith("OBL_B05_BOLLINGER_LONG_SEMANTIC_DECISION")
    assert data["BOLLINGER_LONG_SEMANTIC_DECISION_COMPLETE"] is True
    assert data["BOLLINGER_QUANTITATIVE_BASELINE_COMPLETE"] is True
    assert data["BOLLINGER_DECISION"] == "CONTRACT_REMAINS_AMBIGUOUS"
    assert data["BOLLINGER_DECISION"] in _ALLOWED_DECISIONS
    assert data["BOLLINGER_SIDE_ACTIVATED"] is False
    assert data["BOLLINGER_SHORT_EMISSION"] is False
    assert data["OTHER_PRODUCER_SIDE_EMISSION_CHANGED"] is False
    assert data["PRODUCTIVE_SEMANTICS_CHANGED"] is False
    assert data["LIVE_AUTHORIZED"] is False
    assert data["ORDERS_ENABLED"] is False
    assert "DOCS_TOKEN_OBL_B05_BOLLINGER_LONG_SEMANTIC_DECISION_V1" in body
    assert "BOLLINGER_DECISION: CONTRACT_REMAINS_AMBIGUOUS" in body


def test_quantitative_baseline_reconciles_and_none_side() -> None:
    data = _ssot()
    panel_ev = data["bollinger_event_baseline_panel"]
    panel_mv2 = data["bollinger_panel_entry_mv2"]
    assert panel_ev["total_bars"] == 348454
    assert panel_ev["entry_plus_one"] == panel_mv2["entry_bar_count"] == 185
    assert panel_ev["exit_minus_one"] == 20754
    assert (
        panel_ev["neutral_zero"] + panel_ev["entry_plus_one"] + panel_ev["exit_minus_one"]
        == panel_ev["total_bars"]
    )
    assert panel_mv2["entry_side_counts"].get("NONE", 0) == 185
    assert panel_mv2["entry_side_counts"].get("LONG", 0) == 0
    assert panel_mv2["entry_side_counts"].get("SHORT", 0) == 0
    assert panel_mv2["BLOCKED_DIRECTIONAL_AGREEMENT"] == 185
    assert panel_mv2["ENTER_LONG"] == 0
    assert panel_mv2["ENTER_SHORT"] == 0
    assert panel_mv2["entry_bar_count"] == sum(panel_mv2["taxonomy_outcome_counts"].values())
    assert panel_mv2["entry_bar_count"] == sum(panel_mv2["first_failed_stage_counts"].values())


def test_short_reference_contrast_and_minus_one_not_short_for_bollinger() -> None:
    data = _ssot()
    assert data["comparison_table"]["short_reference_entry_count"] == 53870
    assert data["short_reference"]["producer_id"] == "rsi_reversion"
    assert data["short_reference"]["minus_one_meaning"] == "SHORT_ENTRY_POSITIONAL"
    assert data["decision_evidence"]["productive_minus_one_meaning"] == "EXIT_EVENT"
    src = BOLLINGER_SRC.read_text(encoding="utf-8")
    assert "-1 (exit)" in src or "1=entry" in src
    assert "signals[cross_exit] = -1" in src
    assert "short_entry" not in src.lower()


def test_productive_adapter_still_emits_none_for_bollinger_entry_and_exit() -> None:
    boll_prov = _provenance(
        configured_strategy_id="bollinger_bands",
        executed_strategy_id="bollinger_bands",
        strategy_owner="strategies.bollinger",
    )
    # ENTRY +1
    mat_entry = normalize_strategy_signal_to_suitability_agreement_material_v1(
        _binding([0, 1, 0], provenance=boll_prov),
        instrument_id="okx:linear_perpetual:1INCH:USDT:USDT:perp",
        trading_epoch=1,
    )
    assert mat_entry.encoding_class is StrategySignalEncodingClassV1.ENTRY_EXIT_EVENT_V1
    assert mat_entry.event_kind is StrategyAgreementEventKindV1.ENTRY
    assert mat_entry.entry_side is StrategyEntrySideCarrierV1.NONE
    # EXIT -1 must never become SHORT
    mat_exit = normalize_strategy_signal_to_suitability_agreement_material_v1(
        _binding([0, -1, 0], provenance=boll_prov),
        instrument_id="okx:linear_perpetual:1INCH:USDT:USDT:perp",
        trading_epoch=1,
    )
    assert mat_exit.event_kind is StrategyAgreementEventKindV1.EXIT
    assert mat_exit.entry_side is StrategyEntrySideCarrierV1.NONE
    # MACD unchanged
    macd_prov = _provenance(
        configured_strategy_id="macd",
        executed_strategy_id="macd",
        strategy_owner="strategies.macd",
    )
    mat_macd = normalize_strategy_signal_to_suitability_agreement_material_v1(
        _binding([0, 1, 0], provenance=macd_prov),
        instrument_id="okx:linear_perpetual:1INCH:USDT:USDT:perp",
        trading_epoch=1,
    )
    assert mat_macd.entry_side is StrategyEntrySideCarrierV1.NONE
    # Only TF remains ratified; Bollinger not in ratification owner.
    assert adapter_mod._TREND_FOLLOWING_ENTRY_SIDE_RATIFIED_OWNER == "trend_following"
    assert "bollinger" not in adapter_mod._TREND_FOLLOWING_ENTRY_SIDE_RATIFIED_OWNER


def test_no_productive_semantics_and_next_blocker_is_da() -> None:
    data = _ssot()
    assert data["PRODUCTIVE_SEMANTICS_CHANGED"] is False
    assert data["changed_bar_count"] == 0
    assert data["control_dominant_first_failed_stage"] == "directional_agreement"
    assert data["ratified_dominant_first_failed_stage"] == "directional_agreement"
    assert data["next_dominant_blocker"]["stage"] == "directional_agreement"


def test_eval_only_runner_smoke(tmp_path: Path) -> None:
    archive = Path(
        "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
        "research/full_canonical_system_economic_evidence_generation_v1_offline_execution_v0_"
        "20260716T015033Z"
    )
    if not archive.is_dir():
        pytest.skip("durable archive unavailable")
    import subprocess
    import sys

    out = tmp_path / "baseline"
    proc = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--go-token",
            "GO_OBL_B05_BOLLINGER_LONG_SEMANTIC_DECISION_AND_QUANTITATIVE_BASELINE_V1",
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
    summary = json.loads((out / "baseline_summary.json").read_text(encoding="utf-8"))
    assert summary["BOLLINGER_DECISION"] == "CONTRACT_REMAINS_AMBIGUOUS"
    assert summary["BOLLINGER_SIDE_ACTIVATED"] is False
    assert summary["bollinger_eval_entry_mv2"]["entry_side_counts"].get("NONE", 0) == 1
    assert summary["bollinger_eval_entry_mv2"]["dominant_first_failed_stage"] == (
        "directional_agreement"
    )
