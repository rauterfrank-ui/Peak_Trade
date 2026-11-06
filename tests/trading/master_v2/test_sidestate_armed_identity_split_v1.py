"""Direct identity-split tests for SideState ARMED overload removal.

Authority: OWNER_GO_SIDESTATE_ARMED_IDENTITY_SPLIT_MINIMUM_ATOMIC_REPAIR_V1.
This is identity disambiguation, not a policy change: ScopeDirection prefix,
ActiveSide freeze, and Entry/Exit ARMED eligibility stay as previously bound.
"""

from __future__ import annotations

import pytest

from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.sidestate_restore_v1 import (
    INVALID_PERSISTED_SIDESTATE,
    SideStateRestoreError,
    parse_persisted_side_state_v1,
)
from trading.master_v2.deterministic_scope_event_generator_v1 import ScopeDirectionState
from trading.master_v2.double_play_entry_exit_policy_v0 import EntryExitDirectionState
from trading.master_v2.double_play_entry_exit_scenario_binding_adapter_v0 import (
    side_state_to_entry_exit_direction,
)
from trading.master_v2.double_play_state import (
    ActiveSide,
    DynamicScopeRules,
    RuntimeEnvelope,
    RuntimeScopeState,
    ScopeEvent,
    SideState,
    StaticHardLimits,
    derive_active_side,
    transition_state,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    _side_state_to_entry_exit_direction,
    scope_direction_from_side_state_v1,
)

_GOOD = StaticHardLimits(
    max_notional=1.0,
    max_leverage=1.0,
    max_switches_per_window=100,
    min_band_width=1.0,
    max_band_width=100.0,
)
_ENVELOPE = RuntimeEnvelope(static=_GOOD, live_authorization=False)
_RULES = DynamicScopeRules(
    min_band_width=1.0,
    max_band_width=50.0,
    min_switch_cooldown_ticks=0,
    max_switches_per_window=1_000_000,
    volatility_estimate=0.1,
)
_ST = RuntimeScopeState()

_LONG_ARMED_IDENTITIES = (
    SideState.LONG_ARMED,
    SideState.LONG_ARMED_NEUTRAL_START,
    SideState.LONG_ARMED_SWITCH_TERMINAL,
)
_SHORT_ARMED_IDENTITIES = (
    SideState.SHORT_ARMED,
    SideState.SHORT_ARMED_NEUTRAL_START,
    SideState.SHORT_ARMED_SWITCH_TERMINAL,
)


def _t(side: SideState, event: ScopeEvent, st: RuntimeScopeState = _ST, now: int = 0):
    return transition_state(
        side_state=side,
        event=event,
        scope_state=st,
        rules=_RULES,
        envelope=_ENVELOPE,
        now_tick=now,
    )


def test_neutral_to_long_start_is_distinct_identity() -> None:
    side, _st, decision = _t(SideState.NEUTRAL_OBSERVE, ScopeEvent.UPSCOPE_CONFIRMED)
    assert decision.allowed is True
    assert side is SideState.LONG_ARMED_NEUTRAL_START
    assert side is not SideState.LONG_ARMED
    assert side is not SideState.LONG_ARMED_SWITCH_TERMINAL


def test_neutral_to_short_start_is_distinct_identity() -> None:
    side, _st, decision = _t(SideState.NEUTRAL_OBSERVE, ScopeEvent.DOWNSCOPE_CONFIRMED)
    assert decision.allowed is True
    assert side is SideState.SHORT_ARMED_NEUTRAL_START
    assert side is not SideState.SHORT_ARMED
    assert side is not SideState.SHORT_ARMED_SWITCH_TERMINAL


def test_pipeline_terminal_to_long_is_distinct_from_neutral_start() -> None:
    side, st, d0 = _t(SideState.SHORT_ACTIVE, ScopeEvent.DOWNSCOPE_CONFIRMED, _ST, 0)
    assert side is SideState.SWITCH_SHORT_TO_LONG_PENDING and d0.allowed
    side, st, d1 = _t(side, ScopeEvent.DOWNSCOPE_CONFIRMED, st, 1)
    assert side is SideState.SHORT_BLOCKED and d1.allowed
    side, _st, d2 = _t(side, ScopeEvent.DOWNSCOPE_CONFIRMED, st, 2)
    assert side is SideState.LONG_ARMED_SWITCH_TERMINAL and d2.allowed
    start, _st2, _dn = _t(SideState.NEUTRAL_OBSERVE, ScopeEvent.UPSCOPE_CONFIRMED)
    assert start is SideState.LONG_ARMED_NEUTRAL_START
    assert start is not side


def test_pipeline_terminal_to_short_is_distinct_from_neutral_start() -> None:
    side, st, d0 = _t(SideState.LONG_ACTIVE, ScopeEvent.DOWNSCOPE_CONFIRMED, _ST, 0)
    assert side is SideState.SWITCH_LONG_TO_SHORT_PENDING and d0.allowed
    side, st, d1 = _t(side, ScopeEvent.DOWNSCOPE_CONFIRMED, st, 1)
    assert side is SideState.LONG_BLOCKED and d1.allowed
    side, _st, d2 = _t(side, ScopeEvent.DOWNSCOPE_CONFIRMED, st, 2)
    assert side is SideState.SHORT_ARMED_SWITCH_TERMINAL and d2.allowed
    start, _st2, _dn = _t(SideState.NEUTRAL_OBSERVE, ScopeEvent.DOWNSCOPE_CONFIRMED)
    assert start is SideState.SHORT_ARMED_NEUTRAL_START
    assert start is not side


def test_start_and_terminal_are_unequal() -> None:
    assert SideState.LONG_ARMED_NEUTRAL_START is not SideState.LONG_ARMED_SWITCH_TERMINAL
    assert SideState.SHORT_ARMED_NEUTRAL_START is not SideState.SHORT_ARMED_SWITCH_TERMINAL
    assert SideState.LONG_ARMED_NEUTRAL_START.value != SideState.LONG_ARMED_SWITCH_TERMINAL.value
    assert SideState.SHORT_ARMED_NEUTRAL_START.value != SideState.SHORT_ARMED_SWITCH_TERMINAL.value
    assert SideState.LONG_ARMED_NEUTRAL_START.value != SideState.LONG_ARMED.value
    assert SideState.SHORT_ARMED_NEUTRAL_START.value != SideState.SHORT_ARMED.value


def test_both_long_variants_project_bound_scope_direction_prefix() -> None:
    for side in _LONG_ARMED_IDENTITIES:
        assert scope_direction_from_side_state_v1(side) is ScopeDirectionState.LONG


def test_both_short_variants_project_bound_scope_direction_prefix() -> None:
    for side in _SHORT_ARMED_IDENTITIES:
        assert scope_direction_from_side_state_v1(side) is ScopeDirectionState.SHORT


def test_armed_identities_keep_trailing_freeze_neutral() -> None:
    for side in _LONG_ARMED_IDENTITIES + _SHORT_ARMED_IDENTITIES:
        assert derive_active_side(side) is ActiveSide.NEUTRAL
    assert derive_active_side(SideState.LONG_ACTIVE) is ActiveSide.LONG
    assert derive_active_side(SideState.SHORT_ACTIVE) is ActiveSide.SHORT


def test_entry_exit_armed_eligibility_parity_for_replaced_states() -> None:
    for side in _LONG_ARMED_IDENTITIES:
        assert _side_state_to_entry_exit_direction(side) is EntryExitDirectionState.LONG_ARMED
        assert side_state_to_entry_exit_direction(side) is EntryExitDirectionState.LONG_ARMED
    for side in _SHORT_ARMED_IDENTITIES:
        assert _side_state_to_entry_exit_direction(side) is EntryExitDirectionState.SHORT_ARMED
        assert side_state_to_entry_exit_direction(side) is EntryExitDirectionState.SHORT_ARMED


def test_pending_maps_unchanged() -> None:
    assert (
        _side_state_to_entry_exit_direction(SideState.SWITCH_LONG_TO_SHORT_PENDING)
        is EntryExitDirectionState.SHORT_ARMED
    )
    assert (
        _side_state_to_entry_exit_direction(SideState.SWITCH_SHORT_TO_LONG_PENDING)
        is EntryExitDirectionState.LONG_ARMED
    )
    assert (
        side_state_to_entry_exit_direction(SideState.SWITCH_LONG_TO_SHORT_PENDING)
        is EntryExitDirectionState.SHORT_ARMED
    )
    assert (
        side_state_to_entry_exit_direction(SideState.SWITCH_SHORT_TO_LONG_PENDING)
        is EntryExitDirectionState.LONG_ARMED
    )
    assert (
        scope_direction_from_side_state_v1(SideState.SWITCH_LONG_TO_SHORT_PENDING)
        is ScopeDirectionState.LONG
    )
    assert (
        scope_direction_from_side_state_v1(SideState.SWITCH_SHORT_TO_LONG_PENDING)
        is ScopeDirectionState.SHORT
    )


def test_new_token_persist_restore_roundtrip() -> None:
    for raw in (
        "long_armed_neutral_start",
        "long_armed_switch_terminal",
        "short_armed_neutral_start",
        "short_armed_switch_terminal",
        SideState.LONG_ARMED_NEUTRAL_START,
        SideState.SHORT_ARMED_SWITCH_TERMINAL,
    ):
        restored = parse_persisted_side_state_v1(raw)
        expected = raw if isinstance(raw, SideState) else SideState(str(raw))
        assert restored is expected
        assert parse_persisted_side_state_v1(restored.value) is restored


def test_legacy_long_armed_short_armed_restore_without_inventing_origin() -> None:
    long_legacy = parse_persisted_side_state_v1("long_armed")
    short_legacy = parse_persisted_side_state_v1("short_armed")
    assert long_legacy is SideState.LONG_ARMED
    assert short_legacy is SideState.SHORT_ARMED
    assert long_legacy is not SideState.LONG_ARMED_NEUTRAL_START
    assert long_legacy is not SideState.LONG_ARMED_SWITCH_TERMINAL
    assert short_legacy is not SideState.SHORT_ARMED_NEUTRAL_START
    assert short_legacy is not SideState.SHORT_ARMED_SWITCH_TERMINAL
    nxt, _st, decision = _t(long_legacy, ScopeEvent.UPSCOPE_CONFIRMED)
    assert nxt is SideState.LONG_ACTIVE and decision.allowed
    nxt, _st, decision = _t(short_legacy, ScopeEvent.DOWNSCOPE_CONFIRMED)
    assert nxt is SideState.SHORT_ACTIVE and decision.allowed


def test_invalid_restore_remains_fail_closed() -> None:
    with pytest.raises(SideStateRestoreError) as caught:
        parse_persisted_side_state_v1("not_a_side_state")
    assert caught.value.reason_code == INVALID_PERSISTED_SIDESTATE
    with pytest.raises(SideStateRestoreError):
        parse_persisted_side_state_v1("LONG_ARMED_NEUTRAL_START")
    with pytest.raises(SideStateRestoreError):
        parse_persisted_side_state_v1("armed")


def test_live_armed_token_absent_from_sidestate() -> None:
    names = {member.name for member in SideState}
    values = {member.value for member in SideState}
    assert "LIVE_ARMED" not in names
    assert "live_armed" not in values


def test_new_identities_complete_on_the_same_events_as_legacy_armed() -> None:
    for armed in _LONG_ARMED_IDENTITIES:
        nxt, _st, decision = _t(armed, ScopeEvent.UPSCOPE_CONFIRMED)
        assert nxt is SideState.LONG_ACTIVE and decision.allowed
    for armed in _SHORT_ARMED_IDENTITIES:
        nxt, _st, decision = _t(armed, ScopeEvent.DOWNSCOPE_CONFIRMED)
        assert nxt is SideState.SHORT_ACTIVE and decision.allowed


def test_blocked_to_neutral_entry_exit_unchanged() -> None:
    assert (
        _side_state_to_entry_exit_direction(SideState.LONG_BLOCKED)
        is EntryExitDirectionState.NEUTRAL
    )
    assert (
        _side_state_to_entry_exit_direction(SideState.SHORT_BLOCKED)
        is EntryExitDirectionState.NEUTRAL
    )
    assert (
        side_state_to_entry_exit_direction(SideState.LONG_BLOCKED)
        is EntryExitDirectionState.NEUTRAL
    )
    assert (
        side_state_to_entry_exit_direction(SideState.SHORT_BLOCKED)
        is EntryExitDirectionState.NEUTRAL
    )
