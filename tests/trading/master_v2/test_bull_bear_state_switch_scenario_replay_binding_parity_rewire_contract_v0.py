"""Bull/Bear state switch binding parity: integrated offline replay vs scenario replay (offline only)."""

from __future__ import annotations

import ast
import importlib.util
import subprocess
import sys
from pathlib import Path

from trading.master_v2.bull_bear_state_switch_scenario_binding_adapter_v0 import (
    BULL_BEAR_STATE_SWITCH_SCENARIO_BINDING_ADAPTER_OWNER,
    CANONICAL_STATE_SWITCH_OWNER,
    STATE_SWITCH_EFFECT_BOUND_OFFLINE,
    mirrored_side_states_parity_ok_v0,
    state_switch_binding_non_authority_boundary_ok_v0,
    state_switch_parity_aligned_v0,
)
from trading.master_v2.deterministic_scope_event_generator_v1 import ScopeDirectionState
from trading.master_v2.double_play_composition_matrix_v1 import CompositionStatus
from trading.master_v2.double_play_state import ScopeEvent, SideState
from trading.master_v2.integrated_vs_scenario_replay_full_system_parity_harness_v0 import (
    assert_scenario_replay_zero_order_boundary_v0,
    assert_state_switch_non_authority_boundary_v0,
    canonical_owner_refs_v0,
    evaluate_scenario_matrix_for_side_state_v0,
    evaluate_scenario_state_switch_for_fixture_v0,
    extract_integrated_parity_envelope_v0,
    extract_scenario_replay_tick_state_switch_envelope_v0,
    extract_state_switch_parity_envelope_v0,
    scan_changed_paths_for_forbidden_runtime_v0,
)
from trading.master_v2.offline_double_play_scenario_replay_v0 import (
    OFFLINE_DOUBLE_PLAY_SCENARIO_REPLAY_OWNER,
    OfflineDoublePlayScenarioReplayInputV0,
    SYNTHETIC_FUTURES_INSTRUMENT,
    build_default_bull_bear_bull_scenario_ticks,
    run_offline_double_play_scenario_replay_v0,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    _canonical_scope_event_to_scope_event,
)
from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import _run
import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
_INSTRUMENT = SYNTHETIC_FUTURES_INSTRUMENT
_EPOCH = 48
_CONTEXT = "bull-bear-state-switch-binding-parity-v0"

_SLICE_CHANGED_FILES = (
    "src/trading/master_v2/bull_bear_state_switch_scenario_binding_adapter_v0.py",
    "src/trading/master_v2/offline_double_play_scenario_replay_v0.py",
    "src/trading/master_v2/integrated_vs_scenario_replay_full_system_parity_harness_v0.py",
    "src/trading/master_v2/full_canonical_system_backtest_parity_gap_assessment_v0.py",
    "scripts/ops/run_bull_bear_state_switch_scenario_replay_binding_parity_rewire_v0.py",
    "tests/trading/master_v2/test_bull_bear_state_switch_scenario_replay_binding_parity_rewire_contract_v0.py",
    "tests/trading/master_v2/test_scenario_replay_double_play_entry_exit_policy_binding_parity_rewire_contract_v0.py",
    "tests/trading/master_v2/test_full_canonical_system_backtest_parity_gap_assessment_contract_v0.py",
)

_FORBIDDEN_IMPORT_SCAN_PATHS = (
    REPO_ROOT / "src/trading/master_v2/bull_bear_state_switch_scenario_binding_adapter_v0.py",
    REPO_ROOT
    / "src/trading/master_v2/integrated_vs_scenario_replay_full_system_parity_harness_v0.py",
    REPO_ROOT
    / "scripts/ops/run_bull_bear_state_switch_scenario_replay_binding_parity_rewire_v0.py",
    REPO_ROOT
    / "tests/trading/master_v2/test_bull_bear_state_switch_scenario_replay_binding_parity_rewire_contract_v0.py",
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
    assert refs["state_switch"] == CANONICAL_STATE_SWITCH_OWNER
    assert (
        refs["bull_bear_state_switch_scenario_binding_adapter"]
        == BULL_BEAR_STATE_SWITCH_SCENARIO_BINDING_ADAPTER_OWNER
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


def test_1_bull_only_confirmed_path_bound_v0() -> None:
    binding = evaluate_scenario_state_switch_for_fixture_v0(
        side_state=SideState.NEUTRAL_OBSERVE,
        scope_event=ScopeEvent.UPSCOPE_CONFIRMED,
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
    )
    assert binding.side_state_after == SideState.LONG_ARMED
    env = extract_state_switch_parity_envelope_v0(binding)
    assert_state_switch_non_authority_boundary_v0(env)
    assert state_switch_binding_non_authority_boundary_ok_v0(binding)

    integrated = _run(side_state=SideState.LONG_ARMED)
    integrated_env = extract_integrated_parity_envelope_v0(integrated)
    assert integrated_env.state_switch_ref
    assert integrated_env.state_switch_effect == STATE_SWITCH_EFFECT_BOUND_OFFLINE


def test_2_bear_only_confirmed_path_bound_v0() -> None:
    binding = evaluate_scenario_state_switch_for_fixture_v0(
        side_state=SideState.NEUTRAL_OBSERVE,
        scope_event=ScopeEvent.DOWNSCOPE_CONFIRMED,
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
    )
    assert binding.side_state_after == SideState.SHORT_ARMED
    env = extract_state_switch_parity_envelope_v0(binding)
    assert_state_switch_non_authority_boundary_v0(env)

    integrated = _run(
        side_state=SideState.SHORT_ARMED,
        scope_direction_state=ScopeDirectionState.SHORT,
        price_path=(3500.0, 3400.0),
    )
    integrated_env = extract_integrated_parity_envelope_v0(integrated)
    assert integrated_env.state_switch_ref
    assert integrated_env.state_switch_effect == STATE_SWITCH_EFFECT_BOUND_OFFLINE


def test_3_both_sides_confirmed_conflict_chop_block_v0() -> None:
    binding = evaluate_scenario_state_switch_for_fixture_v0(
        side_state=SideState.LONG_ARMED,
        scope_event=ScopeEvent.CHOP_DETECTED,
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
    )
    assert binding.side_state_after == SideState.CHOP_GUARD_BLOCK
    matrix = evaluate_scenario_matrix_for_side_state_v0(
        side_state=SideState.CHOP_GUARD_BLOCK,
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
    )
    assert matrix.composition_status is CompositionStatus.CHOP_GUARD_BLOCK
    env = extract_state_switch_parity_envelope_v0(binding)
    assert_state_switch_non_authority_boundary_v0(env)


def test_4_neutral_observe_path_bound_v0() -> None:
    binding = evaluate_scenario_state_switch_for_fixture_v0(
        side_state=SideState.NEUTRAL_OBSERVE,
        scope_event=ScopeEvent.NOOP,
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
    )
    assert binding.side_state_after == SideState.NEUTRAL_OBSERVE
    assert binding.transition.reason_code == "NOOP"
    env = extract_state_switch_parity_envelope_v0(binding)
    assert_state_switch_non_authority_boundary_v0(env)


def test_5_blocked_unknown_required_input_path_v0() -> None:
    binding = evaluate_scenario_state_switch_for_fixture_v0(
        side_state=SideState.LONG_ACTIVE,
        scope_event=ScopeEvent.SCOPE_UNKNOWN,
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
    )
    assert binding.side_state_after == SideState.LONG_ACTIVE
    assert binding.transition.allowed is False
    assert binding.transition.reason_code == "SCOPE_UNKNOWN_FAIL_CLOSED"
    env = extract_state_switch_parity_envelope_v0(binding)
    assert_state_switch_non_authority_boundary_v0(env)


def test_6_mirrored_bull_bear_price_path_parity_v0() -> None:
    long_binding = evaluate_scenario_state_switch_for_fixture_v0(
        side_state=SideState.LONG_ACTIVE,
        scope_event=ScopeEvent.DOWNSCOPE_CONFIRMED,
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=f"{_CONTEXT}-long",
    )
    short_binding = evaluate_scenario_state_switch_for_fixture_v0(
        side_state=SideState.SHORT_ACTIVE,
        scope_event=ScopeEvent.UPSCOPE_CONFIRMED,
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=f"{_CONTEXT}-short",
    )
    assert long_binding.side_state_after == SideState.SWITCH_LONG_TO_SHORT_PENDING
    assert short_binding.side_state_after == SideState.SWITCH_SHORT_TO_LONG_PENDING
    assert mirrored_side_states_parity_ok_v0(
        long_binding.side_state_after,
        short_binding.side_state_after,
    )


def test_7_integrated_vs_scenario_state_switch_parity_v0() -> None:
    integrated = _run(
        side_state=SideState.LONG_ACTIVE,
        price_path=(3500.0, 3400.0),
        scope_direction_state=ScopeDirectionState.SHORT,
    )
    assert integrated.intermediate is not None
    mapped_event = _canonical_scope_event_to_scope_event(
        integrated.intermediate.scope_event.event_type
    )
    scenario_binding = evaluate_scenario_state_switch_for_fixture_v0(
        side_state=SideState(integrated.intermediate.state_switch.previous_side_state),
        scope_event=mapped_event,
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
    )
    assert state_switch_parity_aligned_v0(
        integrated_previous=integrated.intermediate.state_switch.previous_side_state,
        integrated_next=integrated.intermediate.state_switch.next_side_state,
        integrated_transition_allowed=integrated.intermediate.state_switch.transition_allowed,
        integrated_transition_reason=integrated.intermediate.state_switch.transition_reason_code,
        scenario_binding=scenario_binding,
    )


def test_scenario_replay_tick_state_switch_binding_no_shortcut_v0() -> None:
    result = run_offline_double_play_scenario_replay_v0(
        OfflineDoublePlayScenarioReplayInputV0(
            selected_future_id=_INSTRUMENT,
            ticks=build_default_bull_bear_bull_scenario_ticks(),
            source_revision="bull-bear-state-switch-binding-parity-v0",
            allow_test_scope_event_injection=True,
        )
    )
    assert result.replay_pass, result.fail_reasons
    assert_scenario_replay_zero_order_boundary_v0(result)

    bound_ticks = 0
    for tick in result.tick_records:
        env = extract_scenario_replay_tick_state_switch_envelope_v0(tick)
        assert_state_switch_non_authority_boundary_v0(env)
        if tick.state_switch_effect == STATE_SWITCH_EFFECT_BOUND_OFFLINE:
            bound_ticks += 1
            assert tick.state_switch_ref
    assert bound_ticks == len(result.tick_records)


def test_scenario_replay_no_duplicate_state_switch_logic_v0() -> None:
    adapter_src = (
        REPO_ROOT / "src/trading/master_v2/bull_bear_state_switch_scenario_binding_adapter_v0.py"
    )
    replay_src = REPO_ROOT / "src/trading/master_v2/offline_double_play_scenario_replay_v0.py"
    adapter_text = adapter_src.read_text(encoding="utf-8")
    replay_text = replay_src.read_text(encoding="utf-8")
    assert "transition_state" in adapter_text
    assert "def _bull_layer_state" not in replay_text
    assert "def _bear_layer_state" not in replay_text
    assert "evaluate_scenario_state_switch_v0" in replay_text


def test_pr4946_parity_suite_still_passes_v0() -> None:
    from tests.trading.master_v2 import (
        test_integrated_vs_scenario_replay_full_system_parity_contract_suite_v0 as pr4946,
    )

    pr4946.test_harness_and_replay_owner_constants_v0()
    pr4946.test_1_long_bull_path_parity_v0()
    pr4946.test_3_both_confirmed_chop_guard_parity_v0()


def test_entry_exit_binding_suite_still_passes_v0() -> None:
    from tests.trading.master_v2 import (
        test_scenario_replay_double_play_entry_exit_policy_binding_parity_rewire_contract_v0 as pr4948,
    )

    pr4948.test_owner_constants_and_canonical_reuse_v0()
    pr4948.test_scenario_replay_tick_entry_exit_binding_no_shortcut_v0()


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
