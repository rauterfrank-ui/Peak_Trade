"""Direct contract and behavior tests for directional mapping runtime bind v1.

Authority: docs/ops/specs/DIRECTIONAL_MAPPING_CONTRACT_REPAIR_V1.md §5 TARGET,
bound by OWNER_GO_DIRECTIONAL_MAPPING_RUNTIME_BIND_MINIMUM_ATOMIC_REPAIR_V1.

These tests prove the canonical mapping, not helper-return trivia:
- SHORT→LONG starts on DOWNSCOPE_CONFIRMED, not UPSCOPE_CONFIRMED
- PENDING generator orientation holds the departing side
- Armed identities keep destination-prefix ScopeDirection and are distinct
"""

from __future__ import annotations

import inspect

from src.backtest.mv2_research_wiring_v1 import (
    project_mv2_integrated_replay_bar_sequence_state_from_intermediate_v1,
)
from trading.master_v2.deterministic_scope_event_generator_v1 import ScopeDirectionState
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


def _t(side: SideState, event: ScopeEvent, st: RuntimeScopeState, now: int = 0):
    return transition_state(
        side_state=side,
        event=event,
        scope_state=st,
        rules=_RULES,
        envelope=_ENVELOPE,
        now_tick=now,
    )


def test_a_short_to_long_contract_consumes_downscope_confirmed() -> None:
    """A. SHORT→LONG trigger/event is DOWNSCOPE_CONFIRMED, not UPSCOPE_CONFIRMED."""
    side, _st, decision = _t(SideState.SHORT_ACTIVE, ScopeEvent.DOWNSCOPE_CONFIRMED, _ST, 0)
    assert decision.allowed is True
    assert side is SideState.SWITCH_SHORT_TO_LONG_PENDING
    assert decision.reason_code == "DOWNscope_SWITCH_PENDING"


def test_d_negative_short_to_long_rejects_legacy_upscope_polarity() -> None:
    """D. Old false SHORT→LONG polarity is not accepted on the productive path."""
    side, _st, decision = _t(SideState.SHORT_ACTIVE, ScopeEvent.UPSCOPE_CONFIRMED, _ST, 0)
    assert side is SideState.SHORT_ACTIVE
    assert decision.allowed is False
    assert decision.reason_code == "NO_TRANSITION"


def test_b_long_to_short_pending_holds_departing_long() -> None:
    """B. SWITCH_LONG_TO_SHORT_PENDING generator orientation is LONG."""
    assert (
        scope_direction_from_side_state_v1(SideState.SWITCH_LONG_TO_SHORT_PENDING)
        is ScopeDirectionState.LONG
    )


def test_c_short_to_long_pending_holds_departing_short() -> None:
    """C. SWITCH_SHORT_TO_LONG_PENDING generator orientation is SHORT."""
    assert (
        scope_direction_from_side_state_v1(SideState.SWITCH_SHORT_TO_LONG_PENDING)
        is ScopeDirectionState.SHORT
    )


def test_e_short_to_long_full_pipeline_behavior() -> None:
    """E. Full SHORT→LONG state transition, not an isolated helper return."""
    st = _ST
    side, st, d0 = _t(SideState.SHORT_ACTIVE, ScopeEvent.DOWNSCOPE_CONFIRMED, st, 0)
    assert side is SideState.SWITCH_SHORT_TO_LONG_PENDING and d0.allowed
    side, st, d1 = _t(side, ScopeEvent.DOWNSCOPE_CONFIRMED, st, 1)
    assert side is SideState.SHORT_BLOCKED and d1.allowed
    side, st, d2 = _t(side, ScopeEvent.DOWNSCOPE_CONFIRMED, st, 2)
    assert side is SideState.LONG_ARMED_SWITCH_TERMINAL and d2.allowed
    side, st, d3 = _t(side, ScopeEvent.UPSCOPE_CONFIRMED, st, 3)
    assert side is SideState.LONG_ACTIVE and d3.allowed
    assert d3.reason_code == "LONG_ACTIVE"


def test_e_long_to_short_full_pipeline_behavior_unchanged() -> None:
    """E/F. LONG→SHORT still consumes DOWNSCOPE_CONFIRMED at every pipeline step."""
    st = _ST
    side, st, d0 = _t(SideState.LONG_ACTIVE, ScopeEvent.DOWNSCOPE_CONFIRMED, st, 0)
    assert side is SideState.SWITCH_LONG_TO_SHORT_PENDING and d0.allowed
    side, st, d1 = _t(side, ScopeEvent.DOWNSCOPE_CONFIRMED, st, 1)
    assert side is SideState.LONG_BLOCKED and d1.allowed
    side, st, d2 = _t(side, ScopeEvent.DOWNSCOPE_CONFIRMED, st, 2)
    assert side is SideState.SHORT_ARMED_SWITCH_TERMINAL and d2.allowed
    side, st, d3 = _t(side, ScopeEvent.DOWNSCOPE_CONFIRMED, st, 3)
    assert side is SideState.SHORT_ACTIVE and d3.allowed
    assert d3.reason_code == "SHORT_ACTIVE"


def test_f_unaffected_neutral_and_long_armed_still_use_upscope() -> None:
    """F. Neutral start and Long-armed completion remain UPSCOPE_CONFIRMED."""
    side, _st, d_n = _t(SideState.NEUTRAL_OBSERVE, ScopeEvent.UPSCOPE_CONFIRMED, _ST, 0)
    assert side is SideState.LONG_ARMED_NEUTRAL_START and d_n.allowed
    side, _st, d_d = _t(SideState.NEUTRAL_OBSERVE, ScopeEvent.DOWNSCOPE_CONFIRMED, _ST, 0)
    assert side is SideState.SHORT_ARMED_NEUTRAL_START and d_d.allowed
    for armed in (
        SideState.LONG_ARMED,
        SideState.LONG_ARMED_NEUTRAL_START,
        SideState.LONG_ARMED_SWITCH_TERMINAL,
    ):
        nxt, _st, d_a = _t(armed, ScopeEvent.UPSCOPE_CONFIRMED, _ST, 0)
        assert nxt is SideState.LONG_ACTIVE and d_a.allowed
        nxt, _st, d_wrong = _t(armed, ScopeEvent.DOWNSCOPE_CONFIRMED, _ST, 0)
        assert nxt is armed
        assert d_wrong.allowed is False
        assert d_wrong.reason_code == "NO_TRANSITION"


def test_f_unaffected_active_side_and_non_pending_generator_rows() -> None:
    """F. Trailing active-side and non-PENDING generator rows stay unchanged."""
    assert derive_active_side(SideState.LONG_ACTIVE) is ActiveSide.LONG
    assert derive_active_side(SideState.SHORT_ACTIVE) is ActiveSide.SHORT
    assert derive_active_side(SideState.SWITCH_LONG_TO_SHORT_PENDING) is ActiveSide.NEUTRAL
    assert derive_active_side(SideState.SWITCH_SHORT_TO_LONG_PENDING) is ActiveSide.NEUTRAL
    assert scope_direction_from_side_state_v1(SideState.LONG_ACTIVE) is ScopeDirectionState.LONG
    assert scope_direction_from_side_state_v1(SideState.SHORT_ACTIVE) is ScopeDirectionState.SHORT
    assert scope_direction_from_side_state_v1(SideState.LONG_BLOCKED) is ScopeDirectionState.LONG
    assert scope_direction_from_side_state_v1(SideState.SHORT_BLOCKED) is ScopeDirectionState.SHORT


def test_g_armed_identities_keep_bound_destination_prefix() -> None:
    """G. Armed identities keep destination-prefix ScopeDirection; no last_active_side."""
    assert scope_direction_from_side_state_v1(SideState.LONG_ARMED) is ScopeDirectionState.LONG
    assert (
        scope_direction_from_side_state_v1(SideState.LONG_ARMED_NEUTRAL_START)
        is ScopeDirectionState.LONG
    )
    assert (
        scope_direction_from_side_state_v1(SideState.LONG_ARMED_SWITCH_TERMINAL)
        is ScopeDirectionState.LONG
    )
    assert scope_direction_from_side_state_v1(SideState.SHORT_ARMED) is ScopeDirectionState.SHORT
    assert (
        scope_direction_from_side_state_v1(SideState.SHORT_ARMED_NEUTRAL_START)
        is ScopeDirectionState.SHORT
    )
    assert (
        scope_direction_from_side_state_v1(SideState.SHORT_ARMED_SWITCH_TERMINAL)
        is ScopeDirectionState.SHORT
    )
    assert derive_active_side(SideState.LONG_ARMED) is ActiveSide.NEUTRAL
    assert derive_active_side(SideState.LONG_ARMED_NEUTRAL_START) is ActiveSide.NEUTRAL
    assert derive_active_side(SideState.LONG_ARMED_SWITCH_TERMINAL) is ActiveSide.NEUTRAL
    assert derive_active_side(SideState.SHORT_ARMED) is ActiveSide.NEUTRAL
    assert derive_active_side(SideState.SHORT_ARMED_NEUTRAL_START) is ActiveSide.NEUTRAL
    assert derive_active_side(SideState.SHORT_ARMED_SWITCH_TERMINAL) is ActiveSide.NEUTRAL
    side, _st, decision = _t(SideState.SHORT_BLOCKED, ScopeEvent.DOWNSCOPE_CONFIRMED, _ST, 0)
    assert side is SideState.LONG_ARMED_SWITCH_TERMINAL and decision.allowed
    assert scope_direction_from_side_state_v1(side) is ScopeDirectionState.LONG
    start, _st, _d = _t(SideState.NEUTRAL_OBSERVE, ScopeEvent.UPSCOPE_CONFIRMED, _ST, 0)
    assert start is SideState.LONG_ARMED_NEUTRAL_START
    assert start is not side


def test_research_pending_consumer_delegates_to_bound_owner() -> None:
    """Research bar-sequence projector has no local PENDING table; it calls the bound owner."""
    src = inspect.getsource(project_mv2_integrated_replay_bar_sequence_state_from_intermediate_v1)
    assert "scope_direction_from_side_state_v1(" in src
    assert "SWITCH_LONG_TO_SHORT_PENDING" not in src
    assert "SWITCH_SHORT_TO_LONG_PENDING" not in src
    assert (
        scope_direction_from_side_state_v1(SideState.SWITCH_LONG_TO_SHORT_PENDING)
        is ScopeDirectionState.LONG
    )
    assert (
        scope_direction_from_side_state_v1(SideState.SWITCH_SHORT_TO_LONG_PENDING)
        is ScopeDirectionState.SHORT
    )
