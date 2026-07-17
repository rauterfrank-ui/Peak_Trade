"""Contract tests for MV2 zero-trade per-bar decision-outcome diagnostic v1."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.research.mv2_zero_trade_per_bar_decision_outcome_diagnostic_v1 import (
    CLOSED_WORLD_OUTCOMES,
    DIAGNOSTIC_ID,
    GO_TOKEN,
    EntryBarDiagnosticRecordV1,
    EntryBarFinalOutcomeV1,
    ObservationalBarSnapshotV1,
    aggregate_entry_bar_diagnostics_v1,
    classify_entry_bar_snapshot_v1,
    evaluate_price_path_suspicion_v1,
    evaluate_regime_id_suspicion_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_REL = "config/research/mv2_zero_trade_per_bar_decision_outcome_diagnostic_v1.json"
OWNER_REL = "src/research/mv2_zero_trade_per_bar_decision_outcome_diagnostic_v1.py"
WIRING_REL = "src/backtest/mv2_research_wiring_v1.py"
RUNNER_REL = "scripts/research/run_mv2_zero_trade_per_bar_decision_outcome_diagnostic_v1.py"
GOV_REL = "docs/governance/MV2_ZERO_TRADE_PER_BAR_DECISION_OUTCOME_DIAGNOSTIC_V1.md"
BASE_SHA = "147f0bee154e5a2452553d51c9b254350ea10142"


def _snapshot(**overrides: object) -> ObservationalBarSnapshotV1:
    payload = {
        "trading_epoch": 10,
        "bar_timestamp": "2024-08-05T01:00:00+00:00",
        "instrument_id": "inst-eth-usdt-perp",
        "panel_member_instrument_id": "okx:linear_perpetual:1INCH:USDT:USDT:perp",
        "raw_strategy_signal": 1,
        "warmup_status": "WARMUP_COMPLETE",
        "warmup_skipped": False,
        "replay_input_built": True,
        "decision_authority_reached": True,
        "context_id": "ctx-1",
        "context_input_digest": "a" * 64,
        "agreement_event_kind": "ENTRY",
        "agreement_side": "NEUTRAL",
        "agreement_cycle_signal_value": 1,
        "directional_bull_status": "confirmed",
        "directional_bear_status": "observe",
        "survival_bull_status": "pass",
        "survival_bear_status": "fail",
        "suitability_bull_status": "pass",
        "suitability_bear_status": "blocked",
        "composition_status": "long_selected",
        "composition_selected_side": "long",
        "entry_eligibility": "eligible",
        "decision_outcome": "enter_long",
        "evidence_reason_codes": (),
        "mapped_position_signal": 1,
        "price_path": (100.0, 105.0),
        "regime_id": "trending",
        "eligible_strategy_count": 1,
        "regime_wildcard_matched": False,
        "fail_reasons": (),
    }
    payload.update(overrides)
    return ObservationalBarSnapshotV1(**payload)  # type: ignore[arg-type]


def _record_from_snapshot(**overrides: object) -> EntryBarDiagnosticRecordV1:
    return classify_entry_bar_snapshot_v1(_snapshot(**overrides))


class TestMv2ZeroTradePerBarDecisionOutcomeDiagnosticV1:
    def test_closed_world_taxonomy_exact(self) -> None:
        expected = {
            "ENTER_LONG",
            "ENTER_SHORT",
            "HOLD",
            "EXIT_OR_DEMOTION",
            "BLOCKED_WARMUP",
            "BLOCKED_DIRECTIONAL_AGREEMENT",
            "BLOCKED_SURVIVAL",
            "BLOCKED_SUITABILITY",
            "BLOCKED_COMPOSITION",
            "BLOCKED_ENTRY_EXIT",
            "BLOCKED_OTHER",
            "UNOBSERVABLE_FAIL_CLOSED",
        }
        assert CLOSED_WORLD_OUTCOMES == expected
        assert {item.value for item in EntryBarFinalOutcomeV1} == expected

    def test_exactly_one_outcome_per_entry_and_reconciliation(self) -> None:
        records = [
            _record_from_snapshot(warmup_skipped=True, warmup_status="WARMUP_REQUIRED"),
            _record_from_snapshot(
                directional_bull_status="observe",
                directional_bear_status="observe",
                decision_outcome="observe",
                mapped_position_signal=0,
                composition_status="observe",
                entry_eligibility="blocked",
            ),
            _record_from_snapshot(
                composition_status="observe",
                decision_outcome="hold",
                mapped_position_signal=0,
                entry_eligibility="not_applicable",
            ),
            _record_from_snapshot(),
        ]
        aggregate = aggregate_entry_bar_diagnostics_v1(records, expected_entry_count=4)
        assert aggregate.entry_bar_count == 4
        assert aggregate.entry_bars_with_exactly_one_outcome == 4
        assert sum(aggregate.outcome_counts.values()) == 4
        assert aggregate.reconciled is True
        assert aggregate.outcome_counts["BLOCKED_WARMUP"] == 1
        assert aggregate.outcome_counts["ENTER_LONG"] == 1

    def test_entry_count_mismatch_fail_closed(self) -> None:
        records = [_record_from_snapshot()]
        with pytest.raises(ValueError, match="entry_count_reconciliation_failed"):
            aggregate_entry_bar_diagnostics_v1(records, expected_entry_count=2)

    def test_non_entry_raw_signal_rejected(self) -> None:
        with pytest.raises(ValueError, match="classifier_requires_strategy_entry_raw_signal"):
            classify_entry_bar_snapshot_v1(_snapshot(raw_strategy_signal=0))

    def test_price_path_and_regime_suspicion_observational(self) -> None:
        records = [
            _record_from_snapshot(price_path=(1.0, 6.0), regime_id="trending"),
            _record_from_snapshot(price_path=(2.0, 7.0), regime_id="trending"),
        ]
        assert (
            evaluate_price_path_suspicion_v1(records)
            == "OBSERVED_SYNTHETIC_MARK_PLUS_5_ON_ALL_ENTRY_BARS"
        )
        assert (
            evaluate_regime_id_suspicion_v1(records)
            == "OBSERVED_HARDCODED_TRENDING_ON_ALL_ENTRY_BARS"
        )

    def test_config_and_governance_bound(self) -> None:
        config = json.loads((REPO_ROOT / CONFIG_REL).read_text(encoding="utf-8"))
        gov = (REPO_ROOT / GOV_REL).read_text(encoding="utf-8")
        assert config["go_token"] == GO_TOKEN
        assert config["diagnostic_id"] == DIAGNOSTIC_ID
        assert config["base_sha"] == BASE_SHA
        assert config["authority_effect"] == "NONE"
        assert config["runtime_effect"] == "NONE"
        assert config["offline_only"] is True
        assert GO_TOKEN in gov
        assert "NON-NEGOTIABLE" not in gov or "Non-authorizing" in gov

    def test_observational_hook_is_optional_default_none(self) -> None:
        source = (REPO_ROOT / WIRING_REL).read_text(encoding="utf-8")
        assert "observational_bar_hook: Callable[..., None] | None = None" in source
        assert "observational_panel_member_instrument_id: str | None = None" in source
        assert "_emit_observational_bar_hook(" in source
        assert "if observational_bar_hook is None:" in source

    def test_no_strategy_or_sizing_semantics_mutation_markers(self) -> None:
        owner = (REPO_ROOT / OWNER_REL).read_text(encoding="utf-8")
        runner = (REPO_ROOT / RUNNER_REL).read_text(encoding="utf-8")
        assert 'AUTHORITY_EFFECT = "NONE"' in owner
        assert "offline observability" in runner.lower() or "No economic reevaluation" in runner
        assert "entry_threshold =" not in owner
        assert "bb_period =" not in owner
        assert "RiskLimits" not in owner
        assert "max_position_pct" not in owner
