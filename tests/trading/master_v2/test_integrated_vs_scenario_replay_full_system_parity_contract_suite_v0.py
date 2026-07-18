"""Full-system parity contract: integrated offline replay vs scenario replay (offline only)."""

from __future__ import annotations

import ast
import importlib.util
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from trading.master_v2.double_play_composition import (
    DoublePlayCompositionInput,
    DoublePlayCompositionStatus,
    RequestedSide,
)
from trading.master_v2.double_play_composition_matrix_v1 import (
    CompositionConflictStatus,
    CompositionSelectedSide,
    CompositionStatus,
)
from trading.master_v2.double_play_composition_scenario_matrix_adapter_v0 import (
    CANONICAL_DOUBLE_PLAY_COMPOSITION_OWNER,
    DOUBLE_PLAY_COMPOSITION_SCENARIO_MATRIX_ADAPTER_OWNER,
    compose_double_play_scenario_via_canonical_matrix_v0,
    legacy_and_matrix_composition_parity_aligned_v0,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    DecisionOutcome,
    EntryExitDirectionState,
    ExistingPositionSide,
    PositionState,
)
from trading.master_v2.double_play_state import SideState, TransitionDecision
from trading.master_v2.double_play_suitability import project_strategy_suitability
from trading.master_v2.double_play_survival import evaluate_survival_envelope
from trading.master_v2.deterministic_scope_event_generator_v1 import ScopeDirectionState
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER,
)
from trading.master_v2.integrated_vs_scenario_replay_full_system_parity_harness_v0 import (
    ALLOWED_SLICE_CHANGED_PATH_PREFIXES,
    BACKTEST_PARITY_WIRING_OWNER,
    FOUR_WAY_PARITY_REWIRE_SLICE_ID,
    INTEGRATED_VS_SCENARIO_REPLAY_FULL_SYSTEM_PARITY_HARNESS_OWNER,
    RUNTIME_BRIDGE_REFERENCE_OWNER,
    RUNTIME_REFERENCE_INTEGRATION_STATUS_V0,
    assert_non_authority_boundary_v0,
    assert_runtime_reference_lane_v0,
    assert_scenario_replay_zero_order_boundary_v0,
    bind_backtest_bar_four_way_parity_lane_v0,
    scan_forbidden_runtime_import_modules_v0,
    canonical_owner_refs_v0,
    composition_matrix_results_aligned_v0,
    evaluate_reversal_preparation_matrix_v0,
    evaluate_scenario_matrix_for_side_state_v0,
    evaluate_surface_p_four_way_parity_v0,
    extract_integrated_parity_envelope_v0,
    extract_runtime_reference_parity_envelope_v0,
    extract_scenario_matrix_parity_envelope_v0,
    extract_scenario_replay_tick_parity_envelope_v0,
    integrated_assessments_match_scenario_side_state_v0,
    legacy_composition_status_for_matrix_v0,
    scan_changed_paths_for_forbidden_runtime_v0,
)
from trading.master_v2.offline_double_play_scenario_replay_v0 import (
    OFFLINE_DOUBLE_PLAY_SCENARIO_REPLAY_OWNER,
    OfflineDoublePlayScenarioReplayInputV0,
    SYNTHETIC_FUTURES_INSTRUMENT,
    _survival_envelope,
    _suitability_input,
    build_default_bull_bear_bull_scenario_ticks,
    run_offline_double_play_scenario_replay_v0,
)
from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import _run
import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
_INSTRUMENT = SYNTHETIC_FUTURES_INSTRUMENT
_EPOCH = 44
_CONTEXT = "integrated-vs-scenario-full-system-parity-v0"

_SLICE_SOURCE_PATHS = (
    REPO_ROOT
    / "src/trading/master_v2/integrated_vs_scenario_replay_full_system_parity_harness_v0.py",
    REPO_ROOT
    / "scripts/ops/run_integrated_vs_scenario_replay_full_system_parity_contract_suite_v0.py",
    REPO_ROOT
    / "scripts/ops/run_integrated_vs_scenario_replay_full_system_4_way_parity_rewire_v0.py",
    REPO_ROOT
    / "tests/trading/master_v2/test_integrated_vs_scenario_replay_full_system_parity_contract_suite_v0.py",
)


def _transition() -> TransitionDecision:
    return TransitionDecision(
        allowed=True,
        reason_code="TEST",
        live_authorization_granted=False,
    )


def _survival_ok():
    return evaluate_survival_envelope(_survival_envelope())


def _suitability_both_pools():
    return project_strategy_suitability(_suitability_input())


def _suitability_neutral_observe():
    base = _suitability_both_pools()
    proj = replace(base.projection, eligible_for_neutral_pool=True)
    return replace(base, projection=proj, can_enter_neutral_pool=True)


def _legacy_input(
    *,
    side: SideState,
    requested: RequestedSide,
    suitability=None,
) -> DoublePlayCompositionInput:
    return DoublePlayCompositionInput(
        transition=_transition(),
        resulting_side_state=side,
        survival=_survival_ok(),
        suitability=suitability or _suitability_both_pools(),
        requested_side=requested,
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


def test_harness_and_replay_owner_constants_v0() -> None:
    refs = canonical_owner_refs_v0()
    assert refs["integrated_offline_replay"] == INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER
    assert refs["scenario_replay"] == OFFLINE_DOUBLE_PLAY_SCENARIO_REPLAY_OWNER
    assert refs["scenario_matrix_adapter"] == DOUBLE_PLAY_COMPOSITION_SCENARIO_MATRIX_ADAPTER_OWNER
    assert refs["double_play_composition_matrix"] == CANONICAL_DOUBLE_PLAY_COMPOSITION_OWNER
    assert refs["parity_harness"] == INTEGRATED_VS_SCENARIO_REPLAY_FULL_SYSTEM_PARITY_HARNESS_OWNER
    assert refs["backtest_parity_wiring"] == BACKTEST_PARITY_WIRING_OWNER
    assert refs["runtime_bridge_reference"] == RUNTIME_BRIDGE_REFERENCE_OWNER


def test_four_way_parity_slice_constants_v0() -> None:
    assert (
        FOUR_WAY_PARITY_REWIRE_SLICE_ID
        == "INTEGRATED_VS_SCENARIO_REPLAY_FULL_SYSTEM_4_WAY_PARITY_REWIRE_V0"
    )
    assert RUNTIME_REFERENCE_INTEGRATION_STATUS_V0 == "BOUND_NOT_ACTIVATED"


def test_runtime_reference_lane_bound_not_activated_v0() -> None:
    envelope = extract_runtime_reference_parity_envelope_v0()
    assert_runtime_reference_lane_v0(envelope)


def test_backtest_bar_lane_bound_offline_v0() -> None:
    envelope = bind_backtest_bar_four_way_parity_lane_v0()
    assert envelope is not None
    assert envelope.decision_outcome
    assert envelope.authority_effect == "NONE"
    assert envelope.runtime_effect == "NONE"


def test_surface_p_four_way_parity_smoke_assessment_v0() -> None:
    integrated = _run(price_path=(3500.0, 3600.0))
    integrated_env = extract_integrated_parity_envelope_v0(integrated)
    assessment = evaluate_surface_p_four_way_parity_v0(
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
        integrated_envelope=integrated_env,
    )
    assert assessment.scenario_lane_bound is True
    assert assessment.backtest_lane_bound is True
    assert assessment.runtime_reference_lane_bound is True
    assert assessment.integrated_lane_bound is True
    assert assessment.integrated_scenario_composition_aligned is True
    assert assessment.backtest_non_authority_confirmed is True
    assert assessment.runtime_reference_non_authority_confirmed is True
    assert assessment.four_way_parity_rewire_bound is True


def test_forbidden_runtime_paths_guard_v0() -> None:
    ok, violations = scan_changed_paths_for_forbidden_runtime_v0(
        ALLOWED_SLICE_CHANGED_PATH_PREFIXES
    )
    assert ok is True
    assert violations == ()
    assert all(path.endswith(".py") for path in ALLOWED_SLICE_CHANGED_PATH_PREFIXES)


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
    for path in _SLICE_SOURCE_PATHS:
        assert path.is_file(), f"missing slice source: {path}"
        hits = _scan_forbidden_imports(path, forbidden)
        assert hits == [], f"forbidden imports in {path}: {hits}"


def test_integrated_replay_owner_excludes_runtime_imports_v0() -> None:
    src = REPO_ROOT / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
    hits = scan_forbidden_runtime_import_modules_v0(src)
    assert hits == ()


def test_prometheus_client_importable_v0() -> None:
    pytest.importorskip("prometheus_client")
    proc = subprocess.run(
        [
            sys.executable,
            "-c",
            "import prometheus_client; print('PROMETHEUS_CLIENT_IMPORTABLE=true')",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "PROMETHEUS_CLIENT_IMPORTABLE=true" in proc.stdout


def test_1_long_bull_path_parity_v0() -> None:
    matrix = evaluate_scenario_matrix_for_side_state_v0(
        side_state=SideState.LONG_ACTIVE,
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
    )
    adapter = compose_double_play_scenario_via_canonical_matrix_v0(
        _legacy_input(side=SideState.LONG_ACTIVE, requested=RequestedSide.LONG_BULL),
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
    )
    scenario_env = extract_scenario_matrix_parity_envelope_v0(matrix)
    assert matrix.composition_status is CompositionStatus.LONG_SELECTED
    assert legacy_and_matrix_composition_parity_aligned_v0(adapter, matrix)
    assert_non_authority_boundary_v0(scenario_env)
    assert scenario_env.selected_side == CompositionSelectedSide.LONG.value


def test_2_short_bear_path_parity_v0() -> None:
    matrix = evaluate_scenario_matrix_for_side_state_v0(
        side_state=SideState.SHORT_ACTIVE,
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
    )
    adapter = compose_double_play_scenario_via_canonical_matrix_v0(
        _legacy_input(side=SideState.SHORT_ACTIVE, requested=RequestedSide.SHORT_BEAR),
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
    )
    scenario_env = extract_scenario_matrix_parity_envelope_v0(matrix)
    assert matrix.composition_status is CompositionStatus.SHORT_SELECTED
    assert legacy_and_matrix_composition_parity_aligned_v0(adapter, matrix)
    assert_non_authority_boundary_v0(scenario_env)
    assert scenario_env.selected_side == CompositionSelectedSide.SHORT.value


def test_3_both_confirmed_chop_guard_parity_v0() -> None:
    """
    Composition both_sides_confirmed is conflict, not Scope-CHOP SSOT.

    CHOP_SCOPE_EVENT_POLICY_BINDING_CONTRACT_V1: Scope-CHOP is RuntimeScopeState
    latch / scope_chop_policy_active projection; legacy SideState.CHOP_GUARD_BLOCK
    remains a scenario conflict fixture only. Integrated default path does not emit
    CHOP and is not required to mirror the conflict fixture.
    """
    from trading.master_v2.double_play_composition_matrix_v1 import (
        CompositionChopGuardStatus,
        DoublePlayCompositionPolicyV1,
        compute_composition_input_digest,
        evaluate_double_play_composition_matrix_v1,
    )
    from trading.master_v2.double_play_composition_scenario_matrix_adapter_v0 import (
        build_scenario_matrix_composition_input_v0,
    )

    matrix = evaluate_scenario_matrix_for_side_state_v0(
        side_state=SideState.CHOP_GUARD_BLOCK,
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
    )
    scenario_env = extract_scenario_matrix_parity_envelope_v0(matrix)
    assert matrix.composition_status is CompositionStatus.CHOP_GUARD_BLOCK
    assert matrix.conflict_status is CompositionConflictStatus.BOTH_SIDES_CONFIRMED
    assert matrix.chop_guard_status is CompositionChopGuardStatus.NONE
    assert "composition_conflict_not_scope_chop" in matrix.reason_codes
    assert "no_new_entry" in matrix.reason_codes
    assert_non_authority_boundary_v0(scenario_env)

    base_inp = build_scenario_matrix_composition_input_v0(
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
        side_st=SideState.CHOP_GUARD_BLOCK,
    )
    projected_inp = replace(base_inp, scope_chop_policy_active=True, input_digest="")
    projected_inp = replace(
        projected_inp, input_digest=compute_composition_input_digest(projected_inp)
    )
    projected = evaluate_double_play_composition_matrix_v1(
        projected_inp,
        DoublePlayCompositionPolicyV1(validity_epochs=3),
    )
    assert projected.chop_guard_status is CompositionChopGuardStatus.CHOP_GUARD_BLOCK
    assert projected.selected_side is CompositionSelectedSide.NONE
    assert "scope_chop_policy_projection" in projected.reason_codes


def test_4_neutral_observe_no_action_parity_v0() -> None:
    matrix = evaluate_scenario_matrix_for_side_state_v0(
        side_state=SideState.NEUTRAL_OBSERVE,
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
        suitability_neutral_observe=True,
    )
    adapter = compose_double_play_scenario_via_canonical_matrix_v0(
        _legacy_input(
            side=SideState.NEUTRAL_OBSERVE,
            requested=RequestedSide.NEUTRAL_OBSERVE,
            suitability=_suitability_neutral_observe(),
        ),
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
    )
    assert matrix.composition_status in (CompositionStatus.OBSERVE, CompositionStatus.NO_ACTION)
    assert matrix.selected_side is CompositionSelectedSide.NONE
    assert adapter.status is DoublePlayCompositionStatus.OBSERVE_ONLY
    assert_non_authority_boundary_v0(extract_scenario_matrix_parity_envelope_v0(matrix))


def test_5_reversal_preparation_boundary_parity_v0() -> None:
    matrix = evaluate_reversal_preparation_matrix_v0(
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
    )
    assert matrix.composition_status is CompositionStatus.REVERSAL_PREPARATION
    assert "existing_long_position" in matrix.reason_codes
    assert "reversal_preparation" in matrix.reason_codes
    assert_non_authority_boundary_v0(extract_scenario_matrix_parity_envelope_v0(matrix))

    integrated = _run(
        position_state=PositionState.OPEN_FULL,
        existing_position_side=ExistingPositionSide.LONG,
        side_state=SideState.LONG_ACTIVE,
        direction_state=EntryExitDirectionState.LONG_ACTIVE,
        price_path=(3500.0, 3400.0),
        scope_direction_state=ScopeDirectionState.SHORT,
    )
    integrated_env = extract_integrated_parity_envelope_v0(integrated)
    assert integrated_env.decision_outcome != DecisionOutcome.ENTER_SHORT.value
    assert_non_authority_boundary_v0(integrated_env)


def test_scenario_replay_e2e_composition_and_zero_order_boundary_v0() -> None:
    result = run_offline_double_play_scenario_replay_v0(
        OfflineDoublePlayScenarioReplayInputV0(
            selected_future_id=_INSTRUMENT,
            ticks=build_default_bull_bear_bull_scenario_ticks(),
            source_revision="full-system-parity-v0",
            allow_test_scope_event_injection=True,
        )
    )
    assert result.replay_pass, result.fail_reasons
    assert_scenario_replay_zero_order_boundary_v0(result)

    long_ticks = [t for t in result.tick_records if t.side_state is SideState.LONG_ACTIVE]
    short_ticks = [t for t in result.tick_records if t.side_state is SideState.SHORT_ACTIVE]
    assert long_ticks
    assert short_ticks

    long_env = extract_scenario_replay_tick_parity_envelope_v0(long_ticks[0])
    short_env = extract_scenario_replay_tick_parity_envelope_v0(short_ticks[0])
    assert long_env.composition_status == legacy_composition_status_for_matrix_v0(
        CompositionStatus.LONG_SELECTED
    )
    assert short_env.composition_status == legacy_composition_status_for_matrix_v0(
        CompositionStatus.SHORT_SELECTED
    )
    assert_non_authority_boundary_v0(long_env)
    assert_non_authority_boundary_v0(short_env)


def test_integrated_replay_boundary_fields_stable_v0() -> None:
    integrated = _run(price_path=(3500.0, 3600.0))
    env = extract_integrated_parity_envelope_v0(integrated)
    assert env.previous_side_state is not None
    assert env.next_side_state is not None
    assert env.composition_result_id
    assert_non_authority_boundary_v0(env)
    assert integrated.evidence.authority_effect == "NONE"
    assert integrated.evidence.runtime_effect == "NONE"
    assert integrated.evidence.order_effect == "NONE"


def test_pr4945_scenario_matrix_parity_subset_still_passes_v0() -> None:
    from tests.trading.master_v2 import (
        test_double_play_composition_scenario_matrix_parity_contract_v0 as pr4945,
    )

    pr4945.test_1_bull_confirmed_bear_blocked_long_selected_v0()
    pr4945.test_3_both_confirmed_chop_guard_block_v0()
    pr4945.test_scenario_replay_default_still_passes_v0()
