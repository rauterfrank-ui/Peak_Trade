"""Reversal preparation binding parity: scenario replay entry-exit path (offline only)."""

from __future__ import annotations

import ast
from pathlib import Path

from trading.master_v2.double_play_composition_matrix_v1 import (
    CompositionSelectedSide,
    CompositionStatus,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    DecisionOutcome,
    ExitClass,
    ExistingPositionSide,
    PositionState,
    ReversalState,
)
from trading.master_v2.double_play_entry_exit_scenario_binding_adapter_v0 import (
    CANONICAL_ENTRY_EXIT_POLICY_OWNER,
    default_scenario_entry_exit_policy_context_v0,
)
from trading.master_v2.full_canonical_system_backtest_parity_gap_assessment_v0 import (
    ALLOWED_SLICE_CHANGED_PATH_PREFIXES,
    NEXT_RECOMMENDED_SLICE,
    parity_surface_assessments_v0,
    parity_status_counts_v0,
    scan_changed_paths_for_forbidden_runtime_v0,
)
from trading.master_v2.integrated_vs_scenario_replay_full_system_parity_harness_v0 import (
    canonical_owner_refs_v0,
    evaluate_reversal_preparation_matrix_v0,
)
from trading.master_v2.offline_double_play_scenario_replay_v0 import (
    OFFLINE_DOUBLE_PLAY_SCENARIO_REPLAY_OWNER,
    SYNTHETIC_FUTURES_INSTRUMENT,
    build_default_bull_bear_bull_scenario_ticks,
    run_offline_double_play_scenario_replay_v0,
    OfflineDoublePlayScenarioReplayInputV0,
)
from trading.master_v2.reversal_preparation_scenario_binding_adapter_v0 import (
    REVERSAL_PREPARATION_SCENARIO_BINDING_ADAPTER_OWNER,
    derive_reversal_preparation_position_context_v0,
    evaluate_scenario_reversal_preparation_entry_exit_v0,
    is_reversal_preparation_composition_v0,
    project_composition_for_reversal_preparation_entry_exit_v0,
    reversal_preparation_binding_non_authority_boundary_ok_v0,
    reversal_preparation_decision_is_reduce_only_preparation_v0,
)
from trading.master_v2.double_play_state import SideState

REPO_ROOT = Path(__file__).resolve().parents[3]
_INSTRUMENT = SYNTHETIC_FUTURES_INSTRUMENT
_EPOCH = 52
_CONTEXT = "reversal-preparation-binding-parity-v0"

_SLICE_CHANGED_FILES = ALLOWED_SLICE_CHANGED_PATH_PREFIXES

_FORBIDDEN_IMPORT_SCAN_PATHS = (
    REPO_ROOT / "src/trading/master_v2/reversal_preparation_scenario_binding_adapter_v0.py",
    REPO_ROOT
    / "src/trading/master_v2/integrated_vs_scenario_replay_full_system_parity_harness_v0.py",
    REPO_ROOT / "scripts/ops/run_reversal_preparation_scenario_replay_binding_parity_rewire_v0.py",
    REPO_ROOT
    / "tests/trading/master_v2/test_reversal_preparation_scenario_replay_binding_parity_rewire_contract_v0.py",
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


def test_owner_constants_and_canonical_reuse_v0() -> None:
    refs = canonical_owner_refs_v0()
    assert refs["entry_exit_policy"] == CANONICAL_ENTRY_EXIT_POLICY_OWNER
    assert (
        refs["reversal_preparation_scenario_binding_adapter"]
        == REVERSAL_PREPARATION_SCENARIO_BINDING_ADAPTER_OWNER
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


def test_scenario_reversal_preparation_exit_via_canonical_policy_v0() -> None:
    matrix = evaluate_reversal_preparation_matrix_v0(
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
    )
    assert is_reversal_preparation_composition_v0(matrix)
    decision = evaluate_scenario_reversal_preparation_entry_exit_v0(
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
        composition_result=matrix,
        side_state=SideState.LONG_ACTIVE,
        policy_context=default_scenario_entry_exit_policy_context_v0(),
    )
    assert decision.exit_class is ExitClass.REVERSAL_PREPARATION_EXIT
    assert decision.reversal_state is ReversalState.PREPARATION
    assert reversal_preparation_decision_is_reduce_only_preparation_v0(decision)
    assert reversal_preparation_binding_non_authority_boundary_ok_v0(decision)


def test_reversal_preparation_no_enter_opposite_side_v0() -> None:
    matrix = evaluate_reversal_preparation_matrix_v0(
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
    )
    decision = evaluate_scenario_reversal_preparation_entry_exit_v0(
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
        composition_result=matrix,
        side_state=SideState.LONG_ACTIVE,
        policy_context=default_scenario_entry_exit_policy_context_v0(),
    )
    assert decision.decision_outcome is not DecisionOutcome.ENTER_SHORT
    assert decision.decision_outcome is not DecisionOutcome.ENTER_LONG
    assert decision.position_flip_allowed is False


def test_reversal_preparation_reduce_only_preparation_bound_v0() -> None:
    matrix = evaluate_reversal_preparation_matrix_v0(
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
    )
    decision = evaluate_scenario_reversal_preparation_entry_exit_v0(
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
        composition_result=matrix,
        side_state=SideState.LONG_ACTIVE,
        policy_context=default_scenario_entry_exit_policy_context_v0(),
    )
    assert decision.decision_outcome in (DecisionOutcome.REDUCE, DecisionOutcome.EXIT)
    assert "reversal_preparation" in decision.reason_codes


def test_untrusted_input_blocks_reversal_authority_v0() -> None:
    matrix = evaluate_reversal_preparation_matrix_v0(
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
    )
    decision = evaluate_scenario_reversal_preparation_entry_exit_v0(
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
        composition_result=matrix,
        side_state=SideState.LONG_ACTIVE,
        policy_context=default_scenario_entry_exit_policy_context_v0(
            safety_decision_allowed=False,
        ),
    )
    assert decision.exit_class is not ExitClass.REVERSAL_PREPARATION_EXIT
    assert reversal_preparation_binding_non_authority_boundary_ok_v0(decision)


def test_adapter_no_runtime_order_authority_v0() -> None:
    matrix = evaluate_reversal_preparation_matrix_v0(
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
    )
    decision = evaluate_scenario_reversal_preparation_entry_exit_v0(
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
        composition_result=matrix,
        side_state=SideState.LONG_ACTIVE,
        policy_context=default_scenario_entry_exit_policy_context_v0(),
    )
    assert decision.runtime_effect == "NONE"
    assert decision.authority_effect == "NONE"
    assert decision.execution_eligible is False


def test_project_composition_sets_opposite_selected_side_v0() -> None:
    matrix = evaluate_reversal_preparation_matrix_v0(
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
    )
    projected = project_composition_for_reversal_preparation_entry_exit_v0(matrix)
    assert projected.selected_side is CompositionSelectedSide.SHORT
    ctx = derive_reversal_preparation_position_context_v0(matrix)
    assert ctx is not None
    assert ctx.existing_position_side is ExistingPositionSide.LONG
    assert ctx.position_state is PositionState.OPEN_FULL


def test_surface_c_pass_dep_unchanged_partial_v0() -> None:
    counts = parity_status_counts_v0()
    assert counts["PASS"] == 14
    assert counts["PARTIAL"] == 2
    surface_c = next(item for item in parity_surface_assessments_v0() if item.surface_id == "C")
    assert surface_c.parity_status == "PASS"
    assert surface_c.missing_binding_if_any == ""
    surface_d = next(item for item in parity_surface_assessments_v0() if item.surface_id == "D")
    assert surface_d.parity_status == "PASS"
    for surface_id in ("E", "P"):
        item = next(s for s in parity_surface_assessments_v0() if s.surface_id == surface_id)
        assert item.parity_status == "PARTIAL"
    assert NEXT_RECOMMENDED_SLICE == "SURVIVAL_SUITABILITY_SCENARIO_REPLAY_BINDING_PARITY_REWIRE_V0"


def test_default_scenario_replay_still_passes_v0() -> None:
    result = run_offline_double_play_scenario_replay_v0(
        OfflineDoublePlayScenarioReplayInputV0(
            selected_future_id=_INSTRUMENT,
            ticks=build_default_bull_bear_bull_scenario_ticks(),
            correlation_id_prefix="reversal-prep-default-scenario-v0",
        )
    )
    assert result.replay_pass is True


def test_non_reversal_composition_passthrough_v0() -> None:
    from trading.master_v2.integrated_vs_scenario_replay_full_system_parity_harness_v0 import (
        evaluate_scenario_matrix_for_side_state_v0,
    )

    matrix = evaluate_scenario_matrix_for_side_state_v0(
        side_state=SideState.LONG_ACTIVE,
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
    )
    assert matrix.composition_status is not CompositionStatus.REVERSAL_PREPARATION
    decision = evaluate_scenario_reversal_preparation_entry_exit_v0(
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
        composition_result=matrix,
        side_state=SideState.LONG_ACTIVE,
        policy_context=default_scenario_entry_exit_policy_context_v0(),
    )
    assert decision.exit_class is not ExitClass.REVERSAL_PREPARATION_EXIT
