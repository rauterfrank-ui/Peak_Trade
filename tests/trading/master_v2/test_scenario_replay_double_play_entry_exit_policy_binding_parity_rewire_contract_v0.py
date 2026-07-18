"""Entry/exit policy binding parity: integrated offline replay vs scenario replay (offline only)."""

from __future__ import annotations

import ast
import importlib.util
import subprocess
import sys
from pathlib import Path

from trading.master_v2.double_play_composition_matrix_v1 import CompositionStatus
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    DecisionOutcome,
    EntryExitDirectionState,
    ExistingPositionSide,
    PolicySignalV0,
    PositionState,
)
from trading.master_v2.double_play_entry_exit_scenario_binding_adapter_v0 import (
    CANONICAL_ENTRY_EXIT_POLICY_OWNER,
    DOUBLE_PLAY_ENTRY_EXIT_SCENARIO_BINDING_ADAPTER_OWNER,
    ScenarioEntryExitPolicyContextV0,
    entry_exit_decision_non_authority_boundary_ok_v0,
)
from trading.master_v2.deterministic_scope_event_generator_v1 import ScopeDirectionState
from trading.master_v2.double_play_state import SideState
from trading.master_v2.integrated_vs_scenario_replay_full_system_parity_harness_v0 import (
    assert_non_authority_boundary_v0,
    assert_scenario_replay_zero_order_boundary_v0,
    canonical_owner_refs_v0,
    evaluate_scenario_entry_exit_for_fixture_v0,
    evaluate_scenario_matrix_for_side_state_v0,
    extract_entry_exit_policy_parity_envelope_v0,
    extract_integrated_parity_envelope_v0,
    extract_scenario_replay_tick_parity_envelope_v0,
    scan_changed_paths_for_forbidden_runtime_v0,
)
from trading.master_v2.offline_double_play_scenario_replay_v0 import (
    OFFLINE_DOUBLE_PLAY_SCENARIO_REPLAY_OWNER,
    OfflineDoublePlayScenarioReplayInputV0,
    SYNTHETIC_FUTURES_INSTRUMENT,
    build_default_bull_bear_bull_scenario_ticks,
    run_offline_double_play_scenario_replay_v0,
)
from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import _run
import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
_INSTRUMENT = SYNTHETIC_FUTURES_INSTRUMENT
_EPOCH = 48
_CONTEXT = "scenario-entry-exit-policy-binding-parity-v0"

_SLICE_CHANGED_FILES = (
    "src/trading/master_v2/double_play_entry_exit_scenario_binding_adapter_v0.py",
    "src/trading/master_v2/offline_double_play_scenario_replay_v0.py",
    "src/trading/master_v2/integrated_vs_scenario_replay_full_system_parity_harness_v0.py",
    "scripts/ops/run_scenario_replay_double_play_entry_exit_policy_binding_parity_rewire_v0.py",
    "tests/trading/master_v2/test_scenario_replay_double_play_entry_exit_policy_binding_parity_rewire_contract_v0.py",
)

_FORBIDDEN_IMPORT_SCAN_PATHS = (
    REPO_ROOT / "src/trading/master_v2/double_play_entry_exit_scenario_binding_adapter_v0.py",
    REPO_ROOT
    / "src/trading/master_v2/integrated_vs_scenario_replay_full_system_parity_harness_v0.py",
    REPO_ROOT
    / "scripts/ops/run_scenario_replay_double_play_entry_exit_policy_binding_parity_rewire_v0.py",
    REPO_ROOT
    / "tests/trading/master_v2/test_scenario_replay_double_play_entry_exit_policy_binding_parity_rewire_contract_v0.py",
)

ALLOWED_SLICE_CHANGED_PATH_PREFIXES = _SLICE_CHANGED_FILES


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
        refs["entry_exit_scenario_binding_adapter"]
        == DOUBLE_PLAY_ENTRY_EXIT_SCENARIO_BINDING_ADAPTER_OWNER
    )
    assert refs["scenario_replay"] == OFFLINE_DOUBLE_PLAY_SCENARIO_REPLAY_OWNER


def test_forbidden_runtime_paths_guard_v0() -> None:
    ok, violations = scan_changed_paths_for_forbidden_runtime_v0(
        ALLOWED_SLICE_CHANGED_PATH_PREFIXES
    )
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


def test_1_entry_allowed_long_path_bound_v0() -> None:
    decision = evaluate_scenario_entry_exit_for_fixture_v0(
        side_state=SideState.LONG_ARMED,
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
    )
    env = extract_entry_exit_policy_parity_envelope_v0(
        decision,
        previous_side_state=SideState.NEUTRAL_OBSERVE.value,
        next_side_state=SideState.LONG_ARMED.value,
        composition_status=CompositionStatus.LONG_SELECTED.value,
    )
    assert decision.decision_outcome is DecisionOutcome.ENTER_LONG
    assert env.entry_or_exit_policy_ref == decision.policy_decision_id
    assert_non_authority_boundary_v0(env)
    assert entry_exit_decision_non_authority_boundary_ok_v0(decision)

    integrated = _run(
        side_state=SideState.LONG_ARMED,
        direction_state=EntryExitDirectionState.LONG_ARMED,
    )
    integrated_env = extract_integrated_parity_envelope_v0(integrated)
    assert integrated_env.entry_or_exit_policy_ref
    assert_non_authority_boundary_v0(integrated_env)


def test_2_entry_allowed_short_path_bound_v0() -> None:
    decision = evaluate_scenario_entry_exit_for_fixture_v0(
        side_state=SideState.SHORT_ARMED,
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
    )
    assert decision.decision_outcome is DecisionOutcome.ENTER_SHORT
    env = extract_entry_exit_policy_parity_envelope_v0(decision)
    assert_non_authority_boundary_v0(env)

    integrated = _run(
        side_state=SideState.SHORT_ARMED,
        direction_state=EntryExitDirectionState.SHORT_ARMED,
        scope_direction_state=ScopeDirectionState.SHORT,
        price_path=(3500.0, 3400.0),
    )
    integrated_env = extract_integrated_parity_envelope_v0(integrated)
    assert integrated_env.entry_or_exit_policy_ref
    assert_non_authority_boundary_v0(integrated_env)


def test_3_adverse_scope_exit_path_bound_v0() -> None:
    matrix = evaluate_scenario_matrix_for_side_state_v0(
        side_state=SideState.LONG_ACTIVE,
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
    )
    ctx = ScenarioEntryExitPolicyContextV0(
        position_state=PositionState.OPEN_FULL,
        existing_position_side=ExistingPositionSide.LONG,
        venue_flat=False,
        scope_adverse_exit_signal=PolicySignalV0(triggered=True, reason_code="adverse_scope"),
    )
    decision = evaluate_scenario_entry_exit_for_fixture_v0(
        side_state=SideState.LONG_ACTIVE,
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
        policy_context=ctx,
        matrix_result=matrix,
    )
    assert decision.decision_outcome in (DecisionOutcome.EXIT, DecisionOutcome.REDUCE)
    env = extract_entry_exit_policy_parity_envelope_v0(decision)
    assert (
        "adverse_scope_exit" in env.decision_precedence_trace or "adverse_scope" in env.reason_codes
    )
    assert_non_authority_boundary_v0(env)

    integrated = _run(
        position_state=PositionState.OPEN_FULL,
        existing_position_side=ExistingPositionSide.LONG,
        side_state=SideState.LONG_ACTIVE,
        direction_state=EntryExitDirectionState.LONG_ACTIVE,
        scope_adverse_exit_signal=PolicySignalV0(triggered=True, reason_code="adverse_scope"),
        venue_flat=False,
    )
    integrated_env = extract_integrated_parity_envelope_v0(integrated)
    assert integrated_env.decision_outcome in (
        DecisionOutcome.EXIT.value,
        DecisionOutcome.REDUCE.value,
    )


def test_4_reversal_preparation_path_bound_v0() -> None:
    matrix = evaluate_scenario_matrix_for_side_state_v0(
        side_state=SideState.SHORT_ACTIVE,
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
    )
    ctx = ScenarioEntryExitPolicyContextV0(
        position_state=PositionState.OPEN_FULL,
        existing_position_side=ExistingPositionSide.LONG,
        venue_flat=False,
    )
    decision = evaluate_scenario_entry_exit_for_fixture_v0(
        side_state=SideState.SHORT_ARMED,
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
        policy_context=ctx,
        matrix_result=matrix,
    )
    assert decision.exit_class.value == "reversal_preparation_exit"
    assert decision.decision_outcome is not DecisionOutcome.ENTER_SHORT
    assert "reversal_preparation" in decision.reason_codes
    env = extract_entry_exit_policy_parity_envelope_v0(decision)
    assert_non_authority_boundary_v0(env)

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


def test_5_flat_before_opposite_side_blocked_v0() -> None:
    matrix = evaluate_scenario_matrix_for_side_state_v0(
        side_state=SideState.SHORT_ACTIVE,
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
    )
    ctx = ScenarioEntryExitPolicyContextV0(
        position_state=PositionState.OPEN_FULL,
        existing_position_side=ExistingPositionSide.LONG,
        venue_flat=False,
    )
    decision = evaluate_scenario_entry_exit_for_fixture_v0(
        side_state=SideState.SHORT_ARMED,
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
        policy_context=ctx,
        matrix_result=matrix,
    )
    assert decision.decision_outcome is not DecisionOutcome.ENTER_SHORT
    assert decision.position_flip_allowed is False


def test_6_both_sides_confirmed_chop_no_entry_v0() -> None:
    decision = evaluate_scenario_entry_exit_for_fixture_v0(
        side_state=SideState.CHOP_GUARD_BLOCK,
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
    )
    assert decision.decision_outcome is not DecisionOutcome.ENTER_LONG
    assert decision.decision_outcome is not DecisionOutcome.ENTER_SHORT
    env = extract_entry_exit_policy_parity_envelope_v0(decision)
    assert_non_authority_boundary_v0(env)

    integrated = _run(price_path=(3500.0, 3600.0))
    if integrated.intermediate is not None:
        matrix = evaluate_scenario_matrix_for_side_state_v0(
            side_state=SideState.CHOP_GUARD_BLOCK,
            instrument_id=_INSTRUMENT,
            trading_epoch=_EPOCH,
            context_reference=_CONTEXT,
        )
        if matrix.composition_status is CompositionStatus.CHOP_GUARD_BLOCK:
            assert integrated.evidence.decision_outcome in (
                DecisionOutcome.OBSERVE.value,
                DecisionOutcome.BLOCKED.value,
                DecisionOutcome.NO_ACTION.value,
            )


def test_scenario_replay_tick_entry_exit_binding_no_shortcut_v0() -> None:
    result = run_offline_double_play_scenario_replay_v0(
        OfflineDoublePlayScenarioReplayInputV0(
            selected_future_id=_INSTRUMENT,
            ticks=build_default_bull_bear_bull_scenario_ticks(),
            source_revision="entry-exit-binding-parity-v0",
            allow_test_scope_event_injection=True,
        )
    )
    assert result.replay_pass, result.fail_reasons
    assert_scenario_replay_zero_order_boundary_v0(result)

    for tick in result.tick_records:
        assert tick.entry_exit_policy_ref
        assert tick.composition_result_id
        assert tick.entry_exit_decision_outcome
        assert tick.entry_exit_decision_precedence_trace
        env = extract_scenario_replay_tick_parity_envelope_v0(tick)
        assert_non_authority_boundary_v0(env)
        assert env.entry_or_exit_policy_ref == tick.entry_exit_policy_ref
        assert env.decision_outcome == tick.entry_exit_decision_outcome


def test_scenario_replay_no_duplicate_policy_logic_v0() -> None:
    adapter_src = (
        REPO_ROOT / "src/trading/master_v2/double_play_entry_exit_scenario_binding_adapter_v0.py"
    )
    text = adapter_src.read_text(encoding="utf-8")
    assert "evaluate_double_play_entry_exit_policy_v0" in text
    assert "def _entry_preconditions_met" not in text
    assert "def _finalize_decision" not in text


def test_pr4946_parity_suite_still_passes_v0() -> None:
    from tests.trading.master_v2 import (
        test_integrated_vs_scenario_replay_full_system_parity_contract_suite_v0 as pr4946,
    )

    pr4946.test_harness_and_replay_owner_constants_v0()
    pr4946.test_1_long_bull_path_parity_v0()
    pr4946.test_3_both_confirmed_chop_guard_parity_v0()
    pr4946.test_5_reversal_preparation_boundary_parity_v0()
    pr4946.test_scenario_replay_e2e_composition_and_zero_order_boundary_v0()


def test_pr4947_gap_assessment_suite_still_passes_v0() -> None:
    from tests.trading.master_v2 import (
        test_full_canonical_system_backtest_parity_gap_assessment_contract_v0 as pr4947,
    )

    pr4947.test_capital_risk_sizing_surface_pass_v0()
    pr4947.test_entry_exit_surface_pass_after_pr4948_v0()
    pr4947.test_pr4946_parity_suite_still_passes_v0()


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
