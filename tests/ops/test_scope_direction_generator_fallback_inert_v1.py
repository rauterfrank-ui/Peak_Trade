"""Generator-fallback inert: ScopeDirectionState is a SideState projection."""

from __future__ import annotations

import inspect
from pathlib import Path

from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.hardening_cycle_bridge_v2 import (
    HardenedBridgeSessionStateV2,
    _update_session_state_from_replay as _hardening_update,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.decision_economics_cycle_bridge_v1 import (
    BridgeSessionStateV1,
    _update_session_state_from_replay as _cap72_update,
)
from trading.master_v2.deterministic_scope_event_generator_v1 import ScopeDirectionState
from trading.master_v2.double_play_composition_matrix_v1 import CompositionSelectedSide
from trading.master_v2.double_play_state import SideState
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    run_integrated_offline_trading_logic_replay_v1,
    scope_direction_from_side_state_v1,
)
from tests.ops.test_hardening_v2_scope_direction_overlay_generator_inert_v1 import (
    _replay_result,
)
from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import (
    _replay_input,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
REPLAY = REPO_ROOT / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
_MAPPED_SHORT = (
    SideState.SHORT_ARMED,
    SideState.SHORT_ACTIVE,
    SideState.SHORT_BLOCKED,
    SideState.SWITCH_SHORT_TO_LONG_PENDING,
)
_MAPPED_LONG = (
    SideState.LONG_ARMED,
    SideState.LONG_ACTIVE,
    SideState.LONG_BLOCKED,
    SideState.SWITCH_LONG_TO_SHORT_PENDING,
)
_FALLBACK_LONG = (
    SideState.NEUTRAL_OBSERVE,
    SideState.CHOP_GUARD_BLOCK,
    SideState.KILL_ALL,
)
_PENDING_UNCHANGED = (
    (SideState.SWITCH_LONG_TO_SHORT_PENDING, ScopeDirectionState.LONG),
    (SideState.SWITCH_SHORT_TO_LONG_PENDING, ScopeDirectionState.SHORT),
)
_ALL_SIDESTATES = tuple(SideState)


def _generator_direction(*, side: SideState, injected: ScopeDirectionState) -> ScopeDirectionState:
    result = run_integrated_offline_trading_logic_replay_v1(
        _replay_input(side_state=side, scope_direction_state=injected)
    )
    assert result.intermediate is not None
    return result.intermediate.scope_event.semantic_binding.current_direction_state


def test_selected_side_short_cannot_force_short_when_sidestate_projects_long() -> None:
    direction = _generator_direction(
        side=SideState.LONG_ACTIVE,
        injected=ScopeDirectionState.SHORT,
    )
    assert direction is ScopeDirectionState.LONG
    assert direction is scope_direction_from_side_state_v1(SideState.LONG_ACTIVE)


def test_selected_side_long_cannot_force_long_when_sidestate_projects_short() -> None:
    direction = _generator_direction(
        side=SideState.SHORT_ACTIVE,
        injected=ScopeDirectionState.LONG,
    )
    assert direction is ScopeDirectionState.SHORT
    assert direction is scope_direction_from_side_state_v1(SideState.SHORT_ACTIVE)


def test_neutral_chop_kill_ignore_injected_scope_direction_cursor() -> None:
    for side in _FALLBACK_LONG:
        direction = _generator_direction(side=side, injected=ScopeDirectionState.SHORT)
        assert direction is ScopeDirectionState.LONG
        assert direction is scope_direction_from_side_state_v1(side)


def test_pending_mappings_remain_unchanged() -> None:
    for side, expected in _PENDING_UNCHANGED:
        assert scope_direction_from_side_state_v1(side) is expected
        direction = _generator_direction(side=side, injected=ScopeDirectionState.SHORT)
        assert direction is expected


def test_entry_exit_owner_remains_sidestate_not_scope_direction() -> None:
    long_injected_short = run_integrated_offline_trading_logic_replay_v1(
        _replay_input(
            side_state=SideState.LONG_ACTIVE,
            scope_direction_state=ScopeDirectionState.SHORT,
        )
    )
    long_injected_long = run_integrated_offline_trading_logic_replay_v1(
        _replay_input(
            side_state=SideState.LONG_ACTIVE,
            scope_direction_state=ScopeDirectionState.LONG,
        )
    )
    assert long_injected_short.intermediate is not None
    assert long_injected_long.intermediate is not None
    assert (
        long_injected_short.intermediate.entry_exit_decision.decision_outcome
        is long_injected_long.intermediate.entry_exit_decision.decision_outcome
    )
    assert (
        long_injected_short.intermediate.entry_exit_decision.exit_class
        is long_injected_long.intermediate.entry_exit_decision.exit_class
    )


def test_generator_source_projects_from_sidestate_without_input_cursor_fallback() -> None:
    text = REPLAY.read_text(encoding="utf-8")
    assert "fallback=inp.scope_direction_state" not in text
    assert "scope_direction_from_side_state_v1(inp.side_state)" in text
    source = inspect.getsource(run_integrated_offline_trading_logic_replay_v1)
    assert "CompositionSelectedSide" in source
    assign_at = source.index("effective_scope_direction = scope_direction_from_side_state_v1")
    generator_block = source[assign_at : assign_at + 180]
    assert "selected_side" not in generator_block
    assert "inp.scope_direction_state" not in generator_block


def test_mapped_short_and_long_tables_unchanged() -> None:
    for side in _MAPPED_SHORT:
        assert scope_direction_from_side_state_v1(side) is ScopeDirectionState.SHORT
    for side in _MAPPED_LONG:
        assert scope_direction_from_side_state_v1(side) is ScopeDirectionState.LONG


def test_parity_with_cap72_and_hardening_v2_overlay_writers() -> None:
    for side in _ALL_SIDESTATES:
        projected = scope_direction_from_side_state_v1(side)
        generator_dir = _generator_direction(side=side, injected=ScopeDirectionState.SHORT)
        cap72 = BridgeSessionStateV1(require_selection_binding=False)
        hardened = HardenedBridgeSessionStateV2()
        overlay = _replay_result(next_side=side, selected=CompositionSelectedSide.SHORT)
        _cap72_update(cap72, result=overlay)
        _hardening_update(hardened, result=overlay)
        assert generator_dir is projected
        assert cap72.scope_direction_state is projected
        assert hardened.scope_direction_state is projected


def test_core_logic_change_is_adjudicated_honestly() -> None:
    runbook = (REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md").read_text(
        encoding="utf-8"
    )
    section_at = runbook.index(
        "11.2.1.F SCOPE_DIRECTION_GENERATOR_FALLBACK_AND_SIXTH_ECONOMIC_GUARD_ADMISSION_V1"
    )
    section = runbook[section_at : runbook.index("## 11.3 Autonomy state model", section_at)]
    assert "CORE_LOGIC_CHANGE=true" in section
    assert "COMPOSITION_SELECTED_SIDE_MAY_WRITE_SCOPE_DIRECTION_STATE=false" in section
    assert "MASTER_V2_GENERATOR_FALLBACK_SYNCHRONIZED=true" in section
    assert "HARD_STOP_AFTER_THIS_TASK=true" in section
