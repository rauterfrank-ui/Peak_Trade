"""Flat-before-opposite-side binding parity: scenario replay entry-exit path (offline only)."""

from __future__ import annotations

import ast
from pathlib import Path

from trading.master_v2.double_play_composition_matrix_v1 import (
    CompositionSelectedSide,
    CompositionStatus,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    DecisionOutcome,
    ExistingPositionSide,
    PositionState,
    ReconciliationState,
)
from trading.master_v2.double_play_entry_exit_scenario_binding_adapter_v0 import (
    CANONICAL_ENTRY_EXIT_POLICY_OWNER,
    ScenarioEntryExitPolicyContextV0,
    default_scenario_entry_exit_policy_context_v0,
)
from trading.master_v2.full_canonical_system_backtest_parity_gap_assessment_v0 import (
    ALLOWED_SLICE_CHANGED_PATH_PREFIXES,
    NEXT_RECOMMENDED_SLICE,
    parity_surface_assessments_v0,
    parity_status_counts_v0,
    scan_changed_paths_for_forbidden_runtime_v0,
)
from trading.master_v2.flat_before_opposite_side_scenario_binding_adapter_v0 import (
    FLAT_BEFORE_OPPOSITE_SIDE_SCENARIO_BINDING_ADAPTER_OWNER,
    derive_flat_before_opposite_side_position_context_v0,
    evaluate_scenario_flat_before_opposite_side_entry_exit_v0,
    flat_before_opposite_side_binding_non_authority_boundary_ok_v0,
    flat_before_opposite_side_blocks_opposite_entry_v0,
    merge_flat_before_opposite_side_policy_context_v0,
)
from trading.master_v2.integrated_vs_scenario_replay_full_system_parity_harness_v0 import (
    canonical_owner_refs_v0,
    evaluate_scenario_matrix_for_side_state_v0,
)
from trading.master_v2.offline_double_play_scenario_replay_v0 import (
    OFFLINE_DOUBLE_PLAY_SCENARIO_REPLAY_OWNER,
    OfflineDoublePlayScenarioReplayInputV0,
    SYNTHETIC_FUTURES_INSTRUMENT,
    build_default_bull_bear_bull_scenario_ticks,
    run_offline_double_play_scenario_replay_v0,
)
from trading.master_v2.double_play_state import SideState

REPO_ROOT = Path(__file__).resolve().parents[3]
_INSTRUMENT = SYNTHETIC_FUTURES_INSTRUMENT
_EPOCH = 54
_CONTEXT = "flat-before-opposite-side-binding-parity-v0"

_SLICE_CHANGED_FILES = ALLOWED_SLICE_CHANGED_PATH_PREFIXES

_FORBIDDEN_IMPORT_SCAN_PATHS = (
    REPO_ROOT / "src/trading/master_v2/flat_before_opposite_side_scenario_binding_adapter_v0.py",
    REPO_ROOT
    / "src/trading/master_v2/integrated_vs_scenario_replay_full_system_parity_harness_v0.py",
    REPO_ROOT
    / "scripts/ops/run_flat_before_opposite_side_scenario_replay_binding_parity_rewire_v0.py",
    REPO_ROOT
    / "tests/trading/master_v2/test_flat_before_opposite_side_scenario_replay_binding_parity_rewire_contract_v0.py",
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


def _short_selected_matrix():
    return evaluate_scenario_matrix_for_side_state_v0(
        side_state=SideState.SHORT_ARMED,
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
    )


def _long_selected_matrix():
    return evaluate_scenario_matrix_for_side_state_v0(
        side_state=SideState.LONG_ARMED,
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
    )


def test_owner_constants_and_canonical_reuse_v0() -> None:
    refs = canonical_owner_refs_v0()
    assert refs["entry_exit_policy"] == CANONICAL_ENTRY_EXIT_POLICY_OWNER
    assert (
        refs["flat_before_opposite_side_scenario_binding_adapter"]
        == FLAT_BEFORE_OPPOSITE_SIDE_SCENARIO_BINDING_ADAPTER_OWNER
    )
    assert refs["scenario_replay"] == OFFLINE_DOUBLE_PLAY_SCENARIO_REPLAY_OWNER


def test_forbidden_runtime_paths_guard_v0() -> None:
    ok, violations = scan_changed_paths_for_forbidden_runtime_v0(_SLICE_CHANGED_FILES)
    assert ok is True
    assert violations == ()


def test_slice_sources_exclude_execution_runtime_imports_v0() -> None:
    forbidden = frozenset(
        {
            "execution",
            "scheduler",
            "credentials",
            "live_runtime",
            "testnet",
            "shadow",
            "paper_lane",
        }
    )
    for path in _FORBIDDEN_IMPORT_SCAN_PATHS:
        assert path.is_file(), f"missing slice source: {path}"
        hits = _scan_forbidden_imports(path, forbidden)
        assert hits == [], f"forbidden imports in {path}: {hits}"


def test_derive_long_active_open_position_context_v0() -> None:
    derived = derive_flat_before_opposite_side_position_context_v0(SideState.LONG_ACTIVE)
    assert derived is not None
    assert derived.position_state is PositionState.OPEN_FULL
    assert derived.existing_position_side is ExistingPositionSide.LONG
    assert derived.venue_flat is False


def test_derive_switch_pending_preserves_open_position_v0() -> None:
    derived = derive_flat_before_opposite_side_position_context_v0(
        SideState.SWITCH_LONG_TO_SHORT_PENDING
    )
    assert derived is not None
    assert derived.existing_position_side is ExistingPositionSide.LONG


def test_1_opposite_side_candidate_while_position_not_flat_blocked_v0() -> None:
    matrix = _short_selected_matrix()
    ctx = default_scenario_entry_exit_policy_context_v0()
    decision = evaluate_scenario_flat_before_opposite_side_entry_exit_v0(
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
        composition_result=matrix,
        side_state=SideState.LONG_ACTIVE,
        policy_context=ctx,
    )
    assert decision.decision_outcome is not DecisionOutcome.ENTER_SHORT
    assert flat_before_opposite_side_blocks_opposite_entry_v0(decision)
    assert decision.position_flip_allowed is False


def test_2_opposite_side_candidate_reconciliation_unresolved_blocked_v0() -> None:
    matrix = _short_selected_matrix()
    ctx = ScenarioEntryExitPolicyContextV0(
        position_state=PositionState.RECONCILIATION_REQUIRED,
        reconciliation_state=ReconciliationState.RECONCILIATION_REQUIRED,
        existing_position_side=ExistingPositionSide.NONE,
        venue_flat=True,
    )
    decision = evaluate_scenario_flat_before_opposite_side_entry_exit_v0(
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
        composition_result=matrix,
        side_state=SideState.SHORT_ARMED,
        policy_context=ctx,
    )
    assert decision.decision_outcome is DecisionOutcome.RECONCILE_ONLY
    assert decision.decision_outcome is not DecisionOutcome.ENTER_SHORT
    assert flat_before_opposite_side_blocks_opposite_entry_v0(decision)


def test_3_venue_flat_without_reconciled_state_blocked_v0() -> None:
    matrix = _long_selected_matrix()
    ctx = ScenarioEntryExitPolicyContextV0(
        position_state=PositionState.RECONCILIATION_REQUIRED,
        reconciliation_state=ReconciliationState.RECONCILED,
        existing_position_side=ExistingPositionSide.NONE,
        venue_flat=True,
    )
    decision = evaluate_scenario_flat_before_opposite_side_entry_exit_v0(
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
        composition_result=matrix,
        side_state=SideState.LONG_ARMED,
        policy_context=ctx,
    )
    assert decision.decision_outcome is DecisionOutcome.RECONCILE_ONLY
    assert decision.decision_outcome is not DecisionOutcome.ENTER_LONG


def test_4_reconciled_flat_opposite_entry_via_canonical_policy_only_v0() -> None:
    matrix = _long_selected_matrix()
    ctx = default_scenario_entry_exit_policy_context_v0()
    decision = evaluate_scenario_flat_before_opposite_side_entry_exit_v0(
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
        composition_result=matrix,
        side_state=SideState.LONG_ARMED,
        policy_context=ctx,
    )
    assert decision.decision_outcome is DecisionOutcome.ENTER_LONG
    assert decision.position_flip_allowed is False
    assert flat_before_opposite_side_binding_non_authority_boundary_ok_v0(decision)


def test_no_direct_long_to_short_shortcut_v0() -> None:
    matrix = evaluate_scenario_matrix_for_side_state_v0(
        side_state=SideState.SHORT_ACTIVE,
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
    )
    if matrix.composition_status is not CompositionStatus.SHORT_SELECTED:
        matrix = _short_selected_matrix()
    ctx = merge_flat_before_opposite_side_policy_context_v0(
        side_state=SideState.LONG_ACTIVE,
        policy_context=default_scenario_entry_exit_policy_context_v0(),
    )
    decision = evaluate_scenario_flat_before_opposite_side_entry_exit_v0(
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
        composition_result=matrix,
        side_state=SideState.LONG_ACTIVE,
        policy_context=ctx,
    )
    assert decision.decision_outcome is not DecisionOutcome.ENTER_SHORT
    assert matrix.selected_side is not CompositionSelectedSide.LONG


def test_adapter_no_runtime_order_authority_v0() -> None:
    matrix = _long_selected_matrix()
    decision = evaluate_scenario_flat_before_opposite_side_entry_exit_v0(
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
        composition_result=matrix,
        side_state=SideState.LONG_ARMED,
        policy_context=default_scenario_entry_exit_policy_context_v0(),
    )
    assert decision.runtime_effect == "NONE"
    assert decision.authority_effect == "NONE"
    assert decision.execution_eligible is False


def test_scenario_replay_e2e_flat_before_opposite_side_binding_v0() -> None:
    result = run_offline_double_play_scenario_replay_v0(
        OfflineDoublePlayScenarioReplayInputV0(
            selected_future_id=_INSTRUMENT,
            ticks=build_default_bull_bear_bull_scenario_ticks(),
            source_revision="flat-before-opposite-side-binding-parity-v0",
            allow_test_scope_event_injection=True,
        )
    )
    assert result.replay_pass, result.fail_reasons
    assert result.summary.orders_total == 0


def test_gap_assessment_surface_d_pass_v0() -> None:
    surface_d = next(item for item in parity_surface_assessments_v0() if item.surface_id == "D")
    assert surface_d.parity_status == "PASS"
    assert surface_d.missing_binding_if_any == ""
    assert "evaluate_scenario_flat_before_opposite_side_entry_exit_v0" in (
        surface_d.current_scenario_replay_binding
    )


def test_gap_assessment_surface_c_still_pass_v0() -> None:
    surface_c = next(item for item in parity_surface_assessments_v0() if item.surface_id == "C")
    assert surface_c.parity_status == "PASS"


def test_gap_assessment_e_p_residual_partial_v0() -> None:
    surface_e = next(item for item in parity_surface_assessments_v0() if item.surface_id == "E")
    surface_p = next(item for item in parity_surface_assessments_v0() if item.surface_id == "P")
    assert surface_e.parity_status == "PASS"
    assert surface_p.parity_status == "PASS"
    assert surface_p.missing_binding_if_any == ""


def test_gap_assessment_status_distribution_v0() -> None:
    counts = parity_status_counts_v0()
    assert counts["PASS"] == 16
    assert counts["PARTIAL"] == 0
    assert counts["GAP"] == 0


def test_next_recommended_slice_points_to_surface_p_v0() -> None:
    assert NEXT_RECOMMENDED_SLICE == "FULL_CANONICAL_BACKTEST_BOUNDARY_CHAIN_REASSESSMENT_V0"


def test_reversal_preparation_contracts_still_pass_v0() -> None:
    from tests.trading.master_v2 import (
        test_reversal_preparation_scenario_replay_binding_parity_rewire_contract_v0 as pr4969,
    )

    pr4969.test_scenario_reversal_preparation_exit_via_canonical_policy_v0()
    pr4969.test_reversal_preparation_no_enter_opposite_side_v0()
    pr4969.test_reversal_preparation_reduce_only_preparation_bound_v0()


def test_pr4946_parity_suite_still_passes_v0() -> None:
    from tests.trading.master_v2 import (
        test_integrated_vs_scenario_replay_full_system_parity_contract_suite_v0 as pr4946,
    )

    pr4946.test_5_reversal_preparation_boundary_parity_v0()
    pr4946.test_scenario_replay_e2e_composition_and_zero_order_boundary_v0()
