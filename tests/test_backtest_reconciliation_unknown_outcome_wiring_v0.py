"""Contract: Reconciliation / Unknown Outcome backtest wiring v0 after PR4962 (offline only)."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from meta.learning_loop.runtime_state_reconciliation_v1 import RECONCILIATION_CONTRACT_VERSION
from src.backtest.mv2_research_wiring_v1 import (
    ReconciliationBacktestStateFileBindingConfigV1,
    run_mv2_research_backtest_wiring_v1,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    DecisionOutcome,
    ExistingPositionSide,
    PositionState,
    ReconciliationState,
)
from trading.master_v2.full_canonical_system_backtest_parity_gap_assessment_v0 import (
    NEXT_RECOMMENDED_SLICE,
    parity_surface_assessments_v0,
)
from trading.master_v2.reconciliation_boundary_backtest_state_file_binding_adapter_v0 import (
    RECONCILIATION_BOUNDARY_BACKTEST_STATE_FILE_BINDING_ADAPTER_OWNER,
    RECONCILIATION_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION,
    apply_backtest_reconciliation_exposure_gate_v0,
    backtest_reconciliation_state_file_binding_non_authority_ok_v0,
    bind_reconciliation_boundary_backtest_state_file_evidence_v0,
    compute_backtest_state_file_digest_from_payload_v0,
    evaluate_backtest_reconciliation_state_file_boundary_only_v0,
    parse_reconciliation_backtest_state_file_v0,
    reconciliation_boundary_semantics_represented_in_backtest_v0,
    verify_reconciliation_backtest_state_file_digest_v0,
)
from trading.master_v2.reconciliation_unknown_outcome_offline_replay_binding_adapter_v0 import (
    RECONCILIATION_UNKNOWN_OUTCOME_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER,
)
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    build_scenario_tick_decision_evidence_v0,
)
from tests.backtest.test_mv2_research_wiring_v1 import _bars, _cfg

REPO_ROOT = Path(__file__).resolve().parents[1]

_FORBIDDEN_IMPORT_SCAN_PATHS = (
    REPO_ROOT
    / "src/trading/master_v2/reconciliation_boundary_backtest_state_file_binding_adapter_v0.py",
    REPO_ROOT / "scripts/ops/run_backtest_reconciliation_unknown_outcome_wiring_v0.py",
    REPO_ROOT / "tests/test_backtest_reconciliation_unknown_outcome_wiring_v0.py",
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


def _payload(**kwargs: object) -> dict[str, object]:
    base = {
        "schema_version": RECONCILIATION_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION,
        "reconciliation_state": ReconciliationState.RECONCILED.value,
        "position_state": PositionState.FLAT_RECONCILED.value,
        "venue_flat": True,
        "existing_position_side": ExistingPositionSide.NONE.value,
        "intent_snapshot_unresolved": False,
        "order_snapshot_unresolved": False,
        "fill_snapshot_unresolved": False,
        "reconciliation_owner_digest_ref": RECONCILIATION_CONTRACT_VERSION,
        **kwargs,
    }
    digest = compute_backtest_state_file_digest_from_payload_v0(base)
    return {**base, "state_file_digest_ref": digest}


def _record(**kwargs: object):
    return parse_reconciliation_backtest_state_file_v0(payload=_payload(**kwargs))


def _base_evidence(*, decision_outcome: str = DecisionOutcome.ENTER_LONG.value):
    return build_scenario_tick_decision_evidence_v0(
        decision_id="backtest-reconciliation-unknown-outcome-decision",
        replay_id="backtest-reconciliation-unknown-outcome-replay",
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


def test_owner_constants_reuse_surface_l_adapter_v0() -> None:
    assert RECONCILIATION_BOUNDARY_BACKTEST_STATE_FILE_BINDING_ADAPTER_OWNER.endswith(
        "reconciliation_boundary_backtest_state_file_binding_adapter_v0"
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


def test_reconciliation_semantics_represented_in_backtest_v0() -> None:
    evidence = evaluate_backtest_reconciliation_state_file_boundary_only_v0(_record())
    assert evidence.reconciliation_semantics_represented_in_backtest is True
    assert reconciliation_boundary_semantics_represented_in_backtest_v0(evidence)


def test_unknown_outcome_and_no_auto_resubmit_represented_v0() -> None:
    evidence = evaluate_backtest_reconciliation_state_file_boundary_only_v0(
        _record(position_state=PositionState.SUBMISSION_UNKNOWN.value)
    )
    assert evidence.unknown_outcome_semantics_represented_in_backtest is True
    assert evidence.no_auto_resubmit_after_unknown_outcome_represented_in_backtest is True
    assert (
        "unknown_outcome_no_auto_resubmit" in evidence.offline_binding.boundary.hard_block_reasons
    )
    assert apply_backtest_reconciliation_exposure_gate_v0(1, evidence=evidence) == 0


def test_query_by_client_order_id_represented_v0() -> None:
    evidence = evaluate_backtest_reconciliation_state_file_boundary_only_v0(
        _record(
            position_state=PositionState.SUBMISSION_UNKNOWN.value,
            order_snapshot_unresolved=True,
        )
    )
    assert evidence.query_by_client_order_id_represented_in_backtest is True


def test_open_orders_fills_position_reconciliation_represented_v0() -> None:
    evidence = evaluate_backtest_reconciliation_state_file_boundary_only_v0(
        _record(
            fill_snapshot_unresolved=True,
            reconciliation_state=ReconciliationState.RECONCILIATION_REQUIRED.value,
        )
    )
    assert (
        evidence.open_orders_recent_orders_fills_position_reconciliation_represented_in_backtest
        is True
    )
    assert evidence.reconciliation_failure_blocks_new_exposure_represented_in_backtest is True


def test_opposite_side_requires_reconciled_flat_represented_v0() -> None:
    evidence = evaluate_backtest_reconciliation_state_file_boundary_only_v0(
        _record(
            position_state=PositionState.REDUCING_PARTIAL.value,
            venue_flat=True,
            existing_position_side=ExistingPositionSide.LONG.value,
        )
    )
    assert evidence.opposite_side_requires_reconciled_flat_represented_in_backtest is True
    assert evidence.no_position_increase_during_unresolved_reconciliation_represented_in_backtest


def test_backtest_binding_uses_surface_l_adapter_not_duplicate_semantics_v0() -> None:
    bound = bind_reconciliation_boundary_backtest_state_file_evidence_v0(
        _base_evidence(decision_outcome=DecisionOutcome.ENTER_LONG.value),
        state_file=_record(reconciliation_state=ReconciliationState.RECONCILIATION_REQUIRED.value),
    )
    assert (
        bound.surface_l_adapter_owner_ref
        == RECONCILIATION_UNKNOWN_OUTCOME_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER
    )
    assert bound.offline_binding.binding_applied is True


def test_non_authority_invariants_v0() -> None:
    evidence = evaluate_backtest_reconciliation_state_file_boundary_only_v0(
        _record(position_state=PositionState.SUBMISSION_UNKNOWN.value)
    )
    assert evidence.runtime_authority is False
    assert evidence.orders_allowed is False
    assert evidence.credentials_used is False
    assert evidence.economic_evaluation is False
    assert backtest_reconciliation_state_file_binding_non_authority_ok_v0(evidence)


def test_parity_gap_assessment_surface_l_backtest_wiring_pass_v0() -> None:
    reconciliation = next(
        item for item in parity_surface_assessments_v0() if item.surface_id == "L"
    )
    assert reconciliation.parity_status == "PASS"
    assert reconciliation.missing_binding_if_any == ""
    assert "bind_reconciliation_boundary_backtest_state_file_evidence_v0" in (
        reconciliation.current_backtest_binding
    )
    assert (
        NEXT_RECOMMENDED_SLICE == "INTEGRATED_VS_SCENARIO_REPLAY_FULL_SYSTEM_4_WAY_PARITY_REWIRE_V0"
    )


def test_mv2_research_wiring_binds_state_file_and_blocks_unresolved_v0(tmp_path: Path) -> None:
    payload = _payload(
        reconciliation_state=ReconciliationState.RECONCILIATION_REQUIRED.value,
    )
    state_path = tmp_path / "reconciliation_backtest_state.json"
    state_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    result = run_mv2_research_backtest_wiring_v1(
        _bars(n=6),
        strategy_id="ma_crossover",
        cfg=_cfg(),
        explicit_zero_cost_non_economic=True,
        reconciliation_state_file_binding=ReconciliationBacktestStateFileBindingConfigV1(
            state_file_path=state_path,
            expected_state_file_digest_ref=str(payload["state_file_digest_ref"]),
        ),
    )
    assert result.bar_outcomes
    sample = result.bar_outcomes[0].reconciliation_backtest_state_file_evidence
    assert sample is not None
    assert sample.reconciliation_semantics_represented_in_backtest is True
    assert sample.reconciliation_failure_blocks_new_exposure_represented_in_backtest is True
    assert all(o.position_signal == 0 for o in result.bar_outcomes)


def test_mv2_research_wiring_legacy_without_state_file_unchanged_v0() -> None:
    result = run_mv2_research_backtest_wiring_v1(
        _bars(n=6),
        strategy_id="ma_crossover",
        cfg=_cfg(),
        explicit_zero_cost_non_economic=True,
    )
    assert all(o.reconciliation_backtest_state_file_evidence is None for o in result.bar_outcomes)


def test_required_state_file_missing_fails_closed_v0() -> None:
    with pytest.raises(ValueError, match="reconciliation_backtest_state_file_missing"):
        run_mv2_research_backtest_wiring_v1(
            _bars(n=4),
            strategy_id="ma_crossover",
            cfg=_cfg(),
            explicit_zero_cost_non_economic=True,
            reconciliation_state_file_binding=ReconciliationBacktestStateFileBindingConfigV1(
                require_state_file=True,
            ),
        )


def test_verify_state_file_digest_ref_v0() -> None:
    record = _record()
    verify_reconciliation_backtest_state_file_digest_v0(
        record,
        expected_digest_ref=record.state_file_digest_ref,
    )
    with pytest.raises(ValueError, match="reconciliation_backtest_state_file_digest_mismatch"):
        verify_reconciliation_backtest_state_file_digest_v0(record, expected_digest_ref="0" * 64)
