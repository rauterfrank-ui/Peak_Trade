"""Hardening-v2 overlay-inert: ScopeDirectionState is a SideState projection."""

from __future__ import annotations

import inspect
from pathlib import Path
from types import SimpleNamespace

from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.hardening_cycle_bridge_v2 import (
    HardenedBridgeSessionStateV2,
    _update_session_state_from_replay,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.decision_economics_cycle_bridge_v1 import (
    BridgeSessionStateV1,
    _update_session_state_from_replay as _cap72_update_session_state_from_replay,
)
from trading.master_v2.deterministic_scope_event_generator_v1 import ScopeDirectionState
from trading.master_v2.double_play_composition_matrix_v1 import (
    CompositionDirectionState,
    CompositionSelectedSide,
)
from trading.master_v2.double_play_state import SideState
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    scope_direction_from_side_state_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
HOST = (
    REPO_ROOT
    / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2"
    / "hardening_cycle_bridge_v2.py"
)

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
_ALL_SIDESTATES = tuple(SideState)
_PENDING_UNCHANGED = (
    (SideState.SWITCH_LONG_TO_SHORT_PENDING, ScopeDirectionState.LONG),
    (SideState.SWITCH_SHORT_TO_LONG_PENDING, ScopeDirectionState.SHORT),
)


def _replay_result(*, next_side: SideState, selected: CompositionSelectedSide) -> SimpleNamespace:
    return SimpleNamespace(
        intermediate=SimpleNamespace(
            state_switch=SimpleNamespace(next_side_state=next_side),
            composition_result=SimpleNamespace(selected_side=selected),
        )
    )


def test_selected_side_short_cannot_overwrite_long_sidestate_projection() -> None:
    state = HardenedBridgeSessionStateV2()
    _update_session_state_from_replay(
        state,
        result=_replay_result(
            next_side=SideState.LONG_ACTIVE,
            selected=CompositionSelectedSide.SHORT,
        ),
    )
    assert state.previous_composition_direction_state is CompositionDirectionState.SHORT
    assert state.scope_direction_state is ScopeDirectionState.LONG
    assert state.scope_direction_state is scope_direction_from_side_state_v1(SideState.LONG_ACTIVE)


def test_selected_side_long_cannot_overwrite_short_sidestate_projection() -> None:
    state = HardenedBridgeSessionStateV2()
    _update_session_state_from_replay(
        state,
        result=_replay_result(
            next_side=SideState.SHORT_ACTIVE,
            selected=CompositionSelectedSide.LONG,
        ),
    )
    assert state.previous_composition_direction_state is CompositionDirectionState.LONG
    assert state.scope_direction_state is ScopeDirectionState.SHORT
    assert state.scope_direction_state is scope_direction_from_side_state_v1(SideState.SHORT_ACTIVE)


def test_neutral_chop_kill_ignore_selected_side_overlay() -> None:
    for side in _FALLBACK_LONG:
        state = HardenedBridgeSessionStateV2()
        state.scope_direction_state = ScopeDirectionState.SHORT
        _update_session_state_from_replay(
            state,
            result=_replay_result(next_side=side, selected=CompositionSelectedSide.SHORT),
        )
        assert state.side_state is side
        assert state.scope_direction_state is ScopeDirectionState.LONG
        assert state.previous_composition_direction_state is CompositionDirectionState.SHORT
        assert state.scope_direction_state is scope_direction_from_side_state_v1(side)


def test_pending_mappings_remain_unchanged() -> None:
    for side, expected in _PENDING_UNCHANGED:
        assert scope_direction_from_side_state_v1(side) is expected
        state = HardenedBridgeSessionStateV2()
        _update_session_state_from_replay(
            state,
            result=_replay_result(next_side=side, selected=CompositionSelectedSide.SHORT),
        )
        assert state.scope_direction_state is expected


def test_overlay_writer_source_is_projection_only() -> None:
    text = inspect.getsource(_update_session_state_from_replay)
    assert "state.scope_direction_state = ScopeDirectionState.LONG" not in text
    assert "state.scope_direction_state = ScopeDirectionState.SHORT" not in text
    assert "scope_direction_from_side_state_v1(state.side_state)" in text


def test_all_eleven_sidestates_runtime_projection_parity() -> None:
    assert len(_ALL_SIDESTATES) == 11
    for side in _ALL_SIDESTATES:
        projected = scope_direction_from_side_state_v1(side)
        state = HardenedBridgeSessionStateV2()
        state.side_state = SideState.LONG_ACTIVE
        state.scope_direction_state = ScopeDirectionState.SHORT
        _update_session_state_from_replay(
            state,
            result=_replay_result(next_side=side, selected=CompositionSelectedSide.SHORT),
        )
        assert state.side_state is side
        assert state.scope_direction_state is projected


def test_hardening_v2_matches_cap72_scope_direction_authority() -> None:
    for selected in (CompositionSelectedSide.LONG, CompositionSelectedSide.SHORT):
        for side in _ALL_SIDESTATES:
            hardened = HardenedBridgeSessionStateV2()
            cap72 = BridgeSessionStateV1(require_selection_binding=False)
            result = _replay_result(next_side=side, selected=selected)
            _update_session_state_from_replay(hardened, result=result)
            _cap72_update_session_state_from_replay(cap72, result=result)
            assert hardened.scope_direction_state is cap72.scope_direction_state
            assert (
                hardened.previous_composition_direction_state
                is cap72.previous_composition_direction_state
            )


def test_mapped_short_and_long_tables_unchanged() -> None:
    for side in _MAPPED_SHORT:
        assert scope_direction_from_side_state_v1(side) is ScopeDirectionState.SHORT
    for side in _MAPPED_LONG:
        assert scope_direction_from_side_state_v1(side) is ScopeDirectionState.LONG


def test_next_cycle_cursor_is_sidestate_projection() -> None:
    host_src = HOST.read_text(encoding="utf-8")
    assert "scope_direction_state=state.scope_direction_state" in host_src
    replay_src = inspect.getsource(_update_session_state_from_replay)
    assert "scope_direction_from_side_state_v1(state.side_state)" in replay_src


def test_core_logic_change_is_adjudicated_honestly() -> None:
    runbook = (REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md").read_text(
        encoding="utf-8"
    )
    section_at = runbook.index("11.2.1.E HARDENING_V2_SCOPE_DIRECTION_OVERLAY_GENERATOR_INERT")
    section = runbook[section_at : runbook.index("## 11.3 Autonomy state model", section_at)]
    assert "CORE_LOGIC_CHANGE=true" in section
    assert "HARDENING_V2_OVERLAY_SYNCHRONIZED=true" in section
    assert "COMPOSITION_SELECTED_SIDE_MAY_WRITE_SCOPE_DIRECTION_STATE=false" in section
    assert "HARD_STOP_AFTER_THIS_TASK=true" in section
