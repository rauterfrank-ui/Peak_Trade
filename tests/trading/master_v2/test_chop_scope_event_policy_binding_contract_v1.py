# tests/trading/master_v2/test_chop_scope_event_policy_binding_contract_v1.py
"""Focused contract tests for CHOP_SCOPE_EVENT_POLICY_BINDING_CONTRACT_V1."""

from __future__ import annotations

from dataclasses import replace

from trading.master_v2.chop_scope_event_policy_binding_v1 import (
    CHOP_BINDING_STATUS,
    CHOP_CAN_BYPASS_TRANSITION_STATE,
    CHOP_CAN_CREATE_DIRECTION,
    CHOP_CAN_MUTATE_SIDE_STATE,
    CHOP_CAN_TRIGGER_SWITCH,
    CHOP_SCOPE_POLICY_OWNER,
    CHOP_SEMANTIC_SSOT_COUNT,
    COMPOSITION_CHOP_STATUS,
    LIVE_AUTHORIZED,
    ORDERS_ENABLED,
    RUNTIME_BRIDGE_STATUS,
    SOLE_BULL_BEAR_STATE_OWNER,
    SOLE_SCOPE_STATE_OWNER,
    SOLE_SWITCH_AUTHORITY,
    UNKNOWN_BINDING_STATUS,
    ChopScopePolicyStatus,
    apply_chop_scope_event_policy_v1,
    assert_chop_scope_policy_invariants_v1,
    build_chop_scope_event_policy_status_fields_v1,
    project_composition_chop_guard_from_scope_policy_v1,
)
from trading.master_v2.directional_assessment_v1 import DirectionalAssessmentSide
from trading.master_v2.double_play_composition_matrix_v1 import (
    COMPOSITION_BOTH_SIDES_CONFIRMED_ROLE,
    CompositionChopGuardStatus,
    CompositionConflictStatus,
    CompositionSelectedSide,
    CompositionStatus,
)
from trading.master_v2.double_play_state import (
    ActiveSide,
    DynamicScopeRules,
    RuntimeEnvelope,
    RuntimeScopeState,
    ScopeEvent,
    SideState,
    StaticHardLimits,
    transition_state,
    update_dynamic_boundaries,
)


def _env() -> RuntimeEnvelope:
    return RuntimeEnvelope(static=StaticHardLimits(min_band_width=1.0), live_authorization=False)


def _rules() -> DynamicScopeRules:
    return DynamicScopeRules(min_band_width=1.0, volatility_estimate=0.01)


def _ts(
    side: SideState,
    event: ScopeEvent,
    st: RuntimeScopeState,
    tick: int,
) -> tuple[SideState, RuntimeScopeState, object]:
    return transition_state(
        side_state=side,
        event=event,
        scope_state=st,
        rules=_rules(),
        envelope=_env(),
        now_tick=tick,
    )


def test_status_markers_bound_as_scope_policy() -> None:
    fields = build_chop_scope_event_policy_status_fields_v1()
    assert fields["CHOP_BINDING_STATUS"] == CHOP_BINDING_STATUS == "BOUND_AS_SCOPE_POLICY"
    assert fields["UNKNOWN_BINDING_STATUS"] == UNKNOWN_BINDING_STATUS == "NOT_BOUND_FAIL_CLOSED"
    assert fields["CHOP_SCOPE_POLICY_OWNER"] == CHOP_SCOPE_POLICY_OWNER
    assert fields["SOLE_SCOPE_STATE_OWNER"] == SOLE_SCOPE_STATE_OWNER
    assert fields["SOLE_BULL_BEAR_STATE_OWNER"] == SOLE_BULL_BEAR_STATE_OWNER
    assert fields["SOLE_SWITCH_AUTHORITY"] == SOLE_SWITCH_AUTHORITY
    assert (
        fields["COMPOSITION_CHOP_STATUS"] == COMPOSITION_CHOP_STATUS == "CONSUMER_PROJECTION_ONLY"
    )
    assert fields["CHOP_SEMANTIC_SSOT_COUNT"] == CHOP_SEMANTIC_SSOT_COUNT == "1"
    assert fields["CHOP_CAN_CREATE_DIRECTION"] == CHOP_CAN_CREATE_DIRECTION == "false"
    assert fields["CHOP_CAN_TRIGGER_SWITCH"] == CHOP_CAN_TRIGGER_SWITCH == "false"
    assert fields["CHOP_CAN_MUTATE_SIDE_STATE"] == CHOP_CAN_MUTATE_SIDE_STATE == "false"
    assert fields["CHOP_CAN_BYPASS_TRANSITION_STATE"] == CHOP_CAN_BYPASS_TRANSITION_STATE == "false"
    assert fields["LIVE_AUTHORIZED"] == LIVE_AUTHORIZED == "false"
    assert fields["ORDERS_ENABLED"] == ORDERS_ENABLED == "false"
    assert fields["RUNTIME_BRIDGE_STATUS"] == RUNTIME_BRIDGE_STATUS == "BOUND_NOT_ACTIVATED"
    assert COMPOSITION_BOTH_SIDES_CONFIRMED_ROLE == "COMPOSITION_CONFLICT_NOT_SCOPE_CHOP_SSOT"


def test_chop_event_binds_scope_policy_without_direction_or_switch() -> None:
    st = RuntimeScopeState(anchor_price=100.0)
    for side in (
        SideState.LONG_ACTIVE,
        SideState.SHORT_ACTIVE,
        SideState.LONG_ARMED,
        SideState.SHORT_ARMED,
        SideState.NEUTRAL_OBSERVE,
    ):
        next_side, next_st, decision = _ts(side, ScopeEvent.CHOP_DETECTED, st, 1)
        assert next_side is side
        assert next_st.chop_latched is True
        assert decision.allowed is True
        assert decision.reason_code == "CHOP_SCOPE_POLICY_APPLIED"
        assert decision.live_authorization_granted is False


def test_chop_does_not_mutate_side_state_or_trigger_switch() -> None:
    st = RuntimeScopeState(anchor_price=100.0, chop_latched=False)
    next_side, next_st, _ = _ts(SideState.LONG_ACTIVE, ScopeEvent.CHOP_DETECTED, st, 2)
    assert next_side is SideState.LONG_ACTIVE
    assert next_side is not SideState.SHORT_ACTIVE
    assert next_side is not SideState.CHOP_GUARD_BLOCK
    blocked_side, blocked_st, blocked = _ts(next_side, ScopeEvent.DOWNSCOPE_CONFIRMED, next_st, 3)
    assert blocked_side is SideState.LONG_ACTIVE
    assert blocked_st.chop_latched is True
    assert blocked.allowed is False
    assert blocked.reason_code == "CHOP_SCOPE_POLICY_BLOCKS_TRANSITION"


def test_chop_without_side_state_does_not_invent_side() -> None:
    st = RuntimeScopeState()
    next_side, next_st, decision = _ts(SideState.NEUTRAL_OBSERVE, ScopeEvent.CHOP_DETECTED, st, 0)
    assert next_side is SideState.NEUTRAL_OBSERVE
    assert next_st.chop_latched is True
    assert decision.reason_code == "CHOP_SCOPE_POLICY_APPLIED"


def test_multi_cycle_chop_continuity_and_recovery() -> None:
    st = RuntimeScopeState(anchor_price=100.0)
    side = SideState.SHORT_ACTIVE
    side, st, _ = _ts(side, ScopeEvent.CHOP_DETECTED, st, 1)
    assert st.chop_latched is True
    # Cycle 2: latch continues; trailing freeze
    frozen = update_dynamic_boundaries(
        mark_price=110.0,
        side=ActiveSide.SHORT,
        st=st,
        rules=_rules(),
        env=_env(),
    )
    assert frozen.anchor_price == st.anchor_price
    assert frozen.chop_latched is True
    side, st, d2 = _ts(side, ScopeEvent.NOOP, st, 2)
    assert side is SideState.SHORT_ACTIVE
    assert st.chop_latched is False
    assert d2.reason_code == "CHOP_SCOPE_POLICY_CLEARED"
    # After recovery, switch path may proceed again
    side, st, d3 = _ts(side, ScopeEvent.UPSCOPE_CONFIRMED, st, 3)
    assert d3.allowed is True
    assert side is SideState.SWITCH_SHORT_TO_LONG_PENDING


def test_missing_chop_context_fail_closed() -> None:
    result = apply_chop_scope_event_policy_v1(event=None, scope_state=None, now_tick=0)
    ok, violations = assert_chop_scope_policy_invariants_v1(result)
    assert result.status is ChopScopePolicyStatus.FAIL_CLOSED
    assert result.entry_blocked is True
    assert result.direction_created is False
    assert ok is True
    assert violations == ()


def test_unknown_remains_not_bound_fail_closed() -> None:
    st = RuntimeScopeState(anchor_price=50.0)
    side, next_st, decision = _ts(SideState.LONG_ACTIVE, ScopeEvent.SCOPE_UNKNOWN, st, 1)
    assert side is SideState.LONG_ACTIVE
    assert next_st.chop_latched is False
    assert decision.allowed is False
    assert decision.reason_code == "SCOPE_UNKNOWN_FAIL_CLOSED"
    assert UNKNOWN_BINDING_STATUS == "NOT_BOUND_FAIL_CLOSED"


def test_composition_consumer_projection_only() -> None:
    # Reuse matrix-test builders to avoid duplicating heavy assessment fixtures.
    from tests.trading.master_v2 import test_double_play_composition_matrix_v1 as mx

    bull, bull_s, bull_u = mx._side_bundle(DirectionalAssessmentSide.LONG)
    bear, bear_s, bear_u = mx._side_bundle(DirectionalAssessmentSide.SHORT)

    conflict = mx._evaluate(
        bull_directional_assessment=bull,
        bear_directional_assessment=bear,
        bull_survival_result=bull_s,
        bear_survival_result=bear_s,
        bull_suitability_result=bull_u,
        bear_suitability_result=bear_u,
        scope_chop_policy_active=False,
    )
    assert conflict.composition_status is CompositionStatus.CHOP_GUARD_BLOCK
    assert conflict.conflict_status is CompositionConflictStatus.BOTH_SIDES_CONFIRMED
    assert conflict.chop_guard_status is CompositionChopGuardStatus.NONE
    assert "composition_conflict_not_scope_chop" in conflict.reason_codes

    projected = mx._evaluate(
        bull_directional_assessment=bull,
        bear_directional_assessment=bear,
        bull_survival_result=bull_s,
        bear_survival_result=bear_s,
        bull_suitability_result=bull_u,
        bear_suitability_result=bear_u,
        scope_chop_policy_active=True,
    )
    assert projected.chop_guard_status is CompositionChopGuardStatus.CHOP_GUARD_BLOCK
    assert projected.selected_side is CompositionSelectedSide.NONE
    assert "scope_chop_policy_projection" in projected.reason_codes

    assert project_composition_chop_guard_from_scope_policy_v1(chop_latched=True) == (
        "chop_guard_block"
    )
    assert project_composition_chop_guard_from_scope_policy_v1(chop_latched=False) == "none"


def test_single_canonical_chop_semantic_ssot() -> None:
    assert int(CHOP_SEMANTIC_SSOT_COUNT) == 1
    assert COMPOSITION_CHOP_STATUS == "CONSUMER_PROJECTION_ONLY"
