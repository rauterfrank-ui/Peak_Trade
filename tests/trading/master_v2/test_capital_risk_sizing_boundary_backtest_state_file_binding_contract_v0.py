"""Contract: capital/risk/sizing boundary backtest state-file binding v0 (offline only)."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from src.backtest.mv2_research_wiring_v1 import (
    CapitalRiskSizingBacktestStateFileBindingConfigV1,
    run_mv2_research_backtest_wiring_v1,
)
from src.governance.capital_risk_sizing_v1 import (
    CONTRACT_VERSION as CAPITAL_RISK_SIZING_CONTRACT_VERSION,
)
from trading.master_v2.capital_risk_sizing_boundary_backtest_state_file_binding_adapter_v0 import (
    CAPITAL_RISK_SIZING_BOUNDARY_BACKTEST_STATE_FILE_BINDING_ADAPTER_OWNER,
    CAPITAL_RISK_SIZING_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION,
    apply_backtest_capital_risk_sizing_exposure_gate_v0,
    backtest_capital_risk_sizing_state_file_binding_non_authority_ok_v0,
    bind_capital_risk_sizing_boundary_backtest_state_file_evidence_v0,
    compute_backtest_state_file_digest_from_payload_v0,
    evaluate_backtest_capital_risk_sizing_state_file_boundary_only_v0,
    parse_capital_risk_sizing_backtest_state_file_v0,
    verify_capital_risk_sizing_backtest_state_file_digest_v0,
)
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    CAPITAL_RISK_SIZING_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER,
    build_scenario_tick_decision_evidence_v0,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import DecisionOutcome
from trading.master_v2.full_canonical_system_backtest_parity_gap_assessment_v0 import (
    NEXT_RECOMMENDED_SLICE,
    parity_surface_assessments_v0,
)
from trading.master_v2.killswitch_boundary_backtest_state_file_binding_adapter_v0 import (
    KILLSWITCH_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION,
    compute_backtest_state_file_digest_from_payload_v0 as killswitch_digest,
    parse_killswitch_backtest_state_file_v0,
)
from trading.master_v2.killswitch_boundary_offline_replay_binding_adapter_v0 import (
    KillSwitchBoundaryMode,
)
from trading.master_v2.reconciliation_boundary_backtest_state_file_binding_adapter_v0 import (
    RECONCILIATION_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION,
    compute_backtest_state_file_digest_from_payload_v0 as reconciliation_digest,
    parse_reconciliation_backtest_state_file_v0,
)
from meta.learning_loop.runtime_state_reconciliation_v1 import RECONCILIATION_CONTRACT_VERSION
from src.meta.learning_loop.killswitch_writer_fencing_and_independent_read_paths_v1 import (
    KILL_SWITCH_CONTRACT_DIGEST,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    ExistingPositionSide,
    PositionState,
    ReconciliationState,
)
from tests.backtest.test_mv2_research_wiring_v1 import _bars, _cfg

REPO_ROOT = Path(__file__).resolve().parents[3]

_FORBIDDEN_IMPORT_SCAN_PATHS = (
    REPO_ROOT
    / "src/trading/master_v2/capital_risk_sizing_boundary_backtest_state_file_binding_adapter_v0.py",
    REPO_ROOT / "scripts/ops/run_backtest_capital_risk_sizing_wiring_v0.py",
    REPO_ROOT
    / "tests/trading/master_v2/test_capital_risk_sizing_boundary_backtest_state_file_binding_contract_v0.py",
)


def _scan_forbidden_imports(path: Path, forbidden_tokens: frozenset[str]) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if any(token in alias.name for token in forbidden_tokens):
                    hits.append(alias.name)
        if isinstance(node, ast.ImportFrom) and node.module:
            if any(token in node.module for token in forbidden_tokens):
                hits.append(node.module)
    return hits


def _state_file_payload(
    *,
    per_trade_risk_limit: str = "25",
    daily_loss_remaining_budget: str = "25",
    scope_capital_limit: str = "500",
) -> dict[str, object]:
    base = {
        "schema_version": CAPITAL_RISK_SIZING_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION,
        "instrument_id": "inst-eth-usdt-perp",
        "reference_price": "3500",
        "protective_stop_price": "3400",
        "account_equity": "10000",
        "scope_capital_limit": scope_capital_limit,
        "per_trade_risk_limit": per_trade_risk_limit,
        "total_capital_limit": "500",
        "daily_loss_remaining_budget": daily_loss_remaining_budget,
        "current_reconciled_exposure": "0",
        "lot_size": "0.01",
        "minimum_quantity": "0.01",
        "maximum_quantity": "100",
        "minimum_notional": "5",
        "tick_size": "0.01",
        "capital_risk_sizing_owner_digest_ref": CAPITAL_RISK_SIZING_CONTRACT_VERSION,
    }
    digest = compute_backtest_state_file_digest_from_payload_v0(base)
    return {**base, "state_file_digest_ref": digest}


def _base_evidence(*, decision_outcome: str = DecisionOutcome.ENTER_LONG.value):
    return build_scenario_tick_decision_evidence_v0(
        decision_id="backtest-capital-risk-sizing-state-file-decision",
        replay_id="backtest-capital-risk-sizing-state-file-replay",
        instrument_id="inst-eth-usdt-perp",
        trading_epoch=1,
        composition_result_id="composition",
        entry_exit_policy_ref="policy",
        selected_side="long",
        decision_outcome=decision_outcome,
        reason_codes=("PASS",),
        decision_precedence_trace=("enter_long",),
        config_digest="config",
        implementation_digest="impl",
    )


def _record(**kwargs: object):
    return parse_capital_risk_sizing_backtest_state_file_v0(payload=_state_file_payload(**kwargs))


def test_owner_constants_reuse_surface_h_adapter_v0() -> None:
    assert CAPITAL_RISK_SIZING_BOUNDARY_BACKTEST_STATE_FILE_BINDING_ADAPTER_OWNER.endswith(
        "capital_risk_sizing_boundary_backtest_state_file_binding_adapter_v0"
    )


def test_slice_sources_exclude_runtime_imports_v0() -> None:
    forbidden = frozenset(
        {
            "execution",
            "scheduler",
            "credentials",
            "live_runtime",
            "testnet",
            "shadow",
            "paper_lane",
            "risk_layer.kill_switch.core",
        }
    )
    for path in _FORBIDDEN_IMPORT_SCAN_PATHS:
        assert path.is_file(), f"missing slice source: {path}"
        hits = _scan_forbidden_imports(path, forbidden)
        assert hits == [], f"forbidden imports in {path}: {hits}"


def test_valid_caps_bind_quantity_provenance_and_risk_limits_v0() -> None:
    evidence = evaluate_backtest_capital_risk_sizing_state_file_boundary_only_v0(_record())
    assert evidence.quantity_provenance_represented is True
    assert evidence.risk_limits_represented is True
    assert evidence.quantity_provenance_ref
    assert evidence.risk_sizing_ref
    assert evidence.quantity_status in {"PASS", "REDUCE", "ROUNDED_DOWN"}
    assert apply_backtest_capital_risk_sizing_exposure_gate_v0(1, evidence=evidence) == 1


def test_observe_decision_without_provenance_remains_non_executable_v0() -> None:
    evidence = evaluate_backtest_capital_risk_sizing_state_file_boundary_only_v0(
        _record(),
        decision_outcome=DecisionOutcome.OBSERVE.value,
    )
    assert evidence.quantity_provenance_represented is False
    assert evidence.offline_binding.binding_applied is False
    assert apply_backtest_capital_risk_sizing_exposure_gate_v0(1, evidence=evidence) == 0


def test_exceeded_daily_loss_budget_blocks_exposure_v0() -> None:
    evidence = evaluate_backtest_capital_risk_sizing_state_file_boundary_only_v0(
        _record(daily_loss_remaining_budget="0")
    )
    assert evidence.sizing_outcome == "BLOCKED"
    assert apply_backtest_capital_risk_sizing_exposure_gate_v0(1, evidence=evidence) == 0


def test_missing_cap_field_fails_closed_v0() -> None:
    payload = _state_file_payload()
    del payload["scope_capital_limit"]
    with pytest.raises(ValueError, match="scope_capital_limit_missing"):
        parse_capital_risk_sizing_backtest_state_file_v0(payload=payload)


def test_malformed_cap_value_fails_closed_v0() -> None:
    payload = _state_file_payload()
    payload["per_trade_risk_limit"] = "not-a-number"
    with pytest.raises(ValueError, match="per_trade_risk_limit_invalid"):
        parse_capital_risk_sizing_backtest_state_file_v0(payload=payload)


def test_rounding_does_not_increase_risk_v0() -> None:
    evidence = evaluate_backtest_capital_risk_sizing_state_file_boundary_only_v0(_record())
    decision = evidence.offline_binding.sizing_decision
    assert decision is not None
    position_sizing = decision.canonical_position_sizing
    assert position_sizing is not None
    assert position_sizing.rounded_quantity <= position_sizing.bounded_quantity_before_rounding


def test_missing_state_file_input_fails_closed_v0() -> None:
    with pytest.raises(ValueError, match="capital_risk_sizing_backtest_state_file_input_missing"):
        parse_capital_risk_sizing_backtest_state_file_v0()


def test_corrupted_state_file_digest_fails_closed_v0() -> None:
    payload = _state_file_payload()
    payload["state_file_digest_ref"] = "0" * 64
    with pytest.raises(ValueError, match="capital_risk_sizing_backtest_state_file_digest_mismatch"):
        parse_capital_risk_sizing_backtest_state_file_v0(payload=payload)


def test_backtest_binding_uses_surface_h_adapter_not_duplicate_semantics_v0() -> None:
    evidence = _base_evidence(decision_outcome=DecisionOutcome.ENTER_LONG.value)
    bound = bind_capital_risk_sizing_boundary_backtest_state_file_evidence_v0(
        evidence,
        state_file=_record(daily_loss_remaining_budget="0"),
    )
    assert (
        bound.surface_h_adapter_owner_ref
        == CAPITAL_RISK_SIZING_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER
    )
    assert bound.offline_binding.binding_applied is True


def test_non_authority_invariants_v0() -> None:
    evidence = evaluate_backtest_capital_risk_sizing_state_file_boundary_only_v0(_record())
    assert evidence.runtime_authority is False
    assert evidence.orders_allowed is False
    assert evidence.credentials_used is False
    assert evidence.economic_evaluation is False
    assert evidence.order_intent_boundary_not_adapter_compatible is True
    assert backtest_capital_risk_sizing_state_file_binding_non_authority_ok_v0(evidence)


def test_parity_gap_assessment_surface_h_backtest_state_file_pass_v0() -> None:
    sizing = next(item for item in parity_surface_assessments_v0() if item.surface_id == "H")
    assert sizing.parity_status == "PASS"
    assert sizing.missing_binding_if_any == ""
    assert "bind_capital_risk_sizing_boundary_backtest_state_file_evidence_v0" in (
        sizing.current_backtest_binding
    )
    assert NEXT_RECOMMENDED_SLICE == "BACKTEST_SAFETY_KERNEL_WIRING_V0"


def test_mv2_research_wiring_binds_state_file_and_represents_sizing_v0(tmp_path: Path) -> None:
    payload = _state_file_payload()
    state_path = tmp_path / "capital_risk_sizing_backtest_state.json"
    state_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    result = run_mv2_research_backtest_wiring_v1(
        _bars(n=6),
        strategy_id="ma_crossover",
        cfg=_cfg(),
        explicit_zero_cost_non_economic=True,
        capital_risk_sizing_state_file_binding=CapitalRiskSizingBacktestStateFileBindingConfigV1(
            state_file_path=state_path,
            expected_state_file_digest_ref=str(payload["state_file_digest_ref"]),
        ),
    )
    assert result.bar_outcomes
    bound = [o for o in result.bar_outcomes if o.capital_risk_sizing_backtest_state_file_evidence]
    assert len(bound) == len(result.bar_outcomes)
    sample = bound[0].capital_risk_sizing_backtest_state_file_evidence
    assert sample is not None
    assert sample.capital_risk_sizing_boundary_backtest_state_file_bound is True
    assert sample.risk_limits_represented is True


def test_mv2_research_wiring_legacy_without_state_file_unchanged_v0() -> None:
    result = run_mv2_research_backtest_wiring_v1(
        _bars(n=6),
        strategy_id="ma_crossover",
        cfg=_cfg(),
        explicit_zero_cost_non_economic=True,
    )
    assert all(
        o.capital_risk_sizing_backtest_state_file_evidence is None for o in result.bar_outcomes
    )


def test_required_state_file_missing_fails_closed_v0() -> None:
    with pytest.raises(ValueError, match="capital_risk_sizing_backtest_state_file_missing"):
        run_mv2_research_backtest_wiring_v1(
            _bars(n=4),
            strategy_id="ma_crossover",
            cfg=_cfg(),
            explicit_zero_cost_non_economic=True,
            capital_risk_sizing_state_file_binding=CapitalRiskSizingBacktestStateFileBindingConfigV1(
                require_state_file=True,
            ),
        )


def test_verify_state_file_digest_ref_v0() -> None:
    record = _record()
    verify_capital_risk_sizing_backtest_state_file_digest_v0(
        record,
        expected_digest_ref=record.state_file_digest_ref,
    )
    with pytest.raises(ValueError, match="capital_risk_sizing_backtest_state_file_digest_mismatch"):
        verify_capital_risk_sizing_backtest_state_file_digest_v0(
            record, expected_digest_ref="0" * 64
        )


def test_killswitch_state_file_binding_remains_compatible_v0(tmp_path: Path) -> None:
    """PR #4957 KillSwitch state-file path unchanged when capital/risk/sizing binding added."""
    from src.backtest.mv2_research_wiring_v1 import KillSwitchBacktestStateFileBindingConfigV1

    ks_base = {
        "schema_version": KILLSWITCH_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION,
        "killswitch_boundary_mode": KillSwitchBoundaryMode.BLOCK_NEW.value,
        "fencing_digest_ref": KILL_SWITCH_CONTRACT_DIGEST,
        "prior_killswitch_active": False,
    }
    ks_payload = {**ks_base, "state_file_digest_ref": killswitch_digest(ks_base)}
    ks_path = tmp_path / "killswitch_backtest_state.json"
    ks_path.write_text(json.dumps(ks_payload, indent=2), encoding="utf-8")

    crs_payload = _state_file_payload()
    crs_path = tmp_path / "capital_risk_sizing_backtest_state.json"
    crs_path.write_text(json.dumps(crs_payload, indent=2), encoding="utf-8")

    result = run_mv2_research_backtest_wiring_v1(
        _bars(n=6),
        strategy_id="ma_crossover",
        cfg=_cfg(),
        explicit_zero_cost_non_economic=True,
        killswitch_state_file_binding=KillSwitchBacktestStateFileBindingConfigV1(
            state_file_path=ks_path,
            expected_state_file_digest_ref=str(ks_payload["state_file_digest_ref"]),
        ),
        capital_risk_sizing_state_file_binding=CapitalRiskSizingBacktestStateFileBindingConfigV1(
            state_file_path=crs_path,
            expected_state_file_digest_ref=str(crs_payload["state_file_digest_ref"]),
        ),
    )
    assert all(o.killswitch_backtest_state_file_evidence is not None for o in result.bar_outcomes)
    assert all(
        o.capital_risk_sizing_backtest_state_file_evidence is not None for o in result.bar_outcomes
    )
    assert all(o.position_signal == 0 for o in result.bar_outcomes)
    assert parse_killswitch_backtest_state_file_v0(path=ks_path).killswitch_boundary_mode == (
        KillSwitchBoundaryMode.BLOCK_NEW.value
    )


def test_reconciliation_state_file_binding_remains_compatible_v0(tmp_path: Path) -> None:
    """PR #4958 Reconciliation state-file path unchanged when capital/risk/sizing binding added."""
    from src.backtest.mv2_research_wiring_v1 import ReconciliationBacktestStateFileBindingConfigV1

    rec_base = {
        "schema_version": RECONCILIATION_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION,
        "reconciliation_state": ReconciliationState.RECONCILIATION_REQUIRED.value,
        "position_state": PositionState.FLAT_RECONCILED.value,
        "venue_flat": True,
        "existing_position_side": ExistingPositionSide.NONE.value,
        "intent_snapshot_unresolved": False,
        "order_snapshot_unresolved": False,
        "fill_snapshot_unresolved": False,
        "reconciliation_owner_digest_ref": RECONCILIATION_CONTRACT_VERSION,
    }
    rec_payload = {**rec_base, "state_file_digest_ref": reconciliation_digest(rec_base)}
    rec_path = tmp_path / "reconciliation_backtest_state.json"
    rec_path.write_text(json.dumps(rec_payload, indent=2), encoding="utf-8")

    crs_payload = _state_file_payload()
    crs_path = tmp_path / "capital_risk_sizing_backtest_state.json"
    crs_path.write_text(json.dumps(crs_payload, indent=2), encoding="utf-8")

    result = run_mv2_research_backtest_wiring_v1(
        _bars(n=6),
        strategy_id="ma_crossover",
        cfg=_cfg(),
        explicit_zero_cost_non_economic=True,
        reconciliation_state_file_binding=ReconciliationBacktestStateFileBindingConfigV1(
            state_file_path=rec_path,
            expected_state_file_digest_ref=str(rec_payload["state_file_digest_ref"]),
        ),
        capital_risk_sizing_state_file_binding=CapitalRiskSizingBacktestStateFileBindingConfigV1(
            state_file_path=crs_path,
            expected_state_file_digest_ref=str(crs_payload["state_file_digest_ref"]),
        ),
    )
    assert all(
        o.reconciliation_backtest_state_file_evidence is not None for o in result.bar_outcomes
    )
    assert all(
        o.capital_risk_sizing_backtest_state_file_evidence is not None for o in result.bar_outcomes
    )
    assert all(o.position_signal == 0 for o in result.bar_outcomes)
    assert (
        parse_reconciliation_backtest_state_file_v0(path=rec_path).reconciliation_state
        == ReconciliationState.RECONCILIATION_REQUIRED.value
    )
