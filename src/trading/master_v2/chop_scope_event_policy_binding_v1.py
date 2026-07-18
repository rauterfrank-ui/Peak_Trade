# src/trading/master_v2/chop_scope_event_policy_binding_v1.py
"""
CHOP Scope Event Policy Binding Contract v1.

Binds ``ScopeEvent.CHOP_DETECTED`` as the sole canonical CHOP semantic: a
Dynamic-Scope / policy input consumed by ``RuntimeScopeState``. CHOP never
creates Direction, selects Bull/Bear, mutates SideState, or triggers a Switch.

Composition may only project the already-bound scope-policy result.
UNKNOWN remains unbound fail-closed. No Live / Orders / Runtime activation.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from typing import Mapping, Optional, Tuple

from trading.master_v2.double_play_state import RuntimeScopeState, ScopeEvent

CHOP_SCOPE_EVENT_POLICY_BINDING_LAYER_VERSION = "v1"
CHOP_SCOPE_EVENT_POLICY_BINDING_OWNER = "trading.master_v2.chop_scope_event_policy_binding_v1"
PACKAGE_MARKER = "CHOP_SCOPE_EVENT_POLICY_BINDING_CONTRACT_V1=true"

# Canonical binding / authority markers (acceptance surface).
CHOP_BINDING_STATUS = "BOUND_AS_SCOPE_POLICY"
UNKNOWN_BINDING_STATUS = "NOT_BOUND_FAIL_CLOSED"
CHOP_SCOPE_POLICY_OWNER = "trading.master_v2.double_play_state.RuntimeScopeState"
SOLE_SCOPE_STATE_OWNER = "trading.master_v2.double_play_state.RuntimeScopeState"
SOLE_BULL_BEAR_STATE_OWNER = "trading.master_v2.double_play_state.transition_state"
SOLE_SWITCH_AUTHORITY = "trading.master_v2.double_play_state.transition_state"
COMPOSITION_CHOP_STATUS = "CONSUMER_PROJECTION_ONLY"
COMPOSITION_BOTH_SIDES_CONFIRMED_ROLE = "COMPOSITION_CONFLICT_NOT_SCOPE_CHOP_SSOT"
CHOP_SEMANTIC_SSOT_COUNT = "1"
CHOP_CANONICAL_INPUT_EVENT = "ScopeEvent.CHOP_DETECTED"
CHOP_CAN_CREATE_DIRECTION = "false"
CHOP_CAN_TRIGGER_SWITCH = "false"
CHOP_CAN_MUTATE_SIDE_STATE = "false"
CHOP_CAN_BYPASS_TRANSITION_STATE = "false"
UNKNOWN_CAN_CREATE_DIRECTION = "false"
UNKNOWN_CAN_TRIGGER_SWITCH = "false"
PRODUCTIVE_CHOP_BYPASS_PATHS = "0"
PRODUCTIVE_COMPETING_AUTHORITIES = "0"
DYNAMIC_SCOPE_PRECEDES_SWITCH = "true"
MULTI_CYCLE_SCOPE_CONTINUITY = "true"
BACKTEST_RUNTIME_AUTHORITY_PARITY = "FULL"
SCENARIO_SCOPE_EVENT_INJECTION_STATUS = "TEST_ONLY_GUARDED"
LIVE_AUTHORIZED = "false"
ORDERS_ENABLED = "false"
RUNTIME_BRIDGE_STATUS = "BOUND_NOT_ACTIVATED"

REASON_CHOP_SCOPE_POLICY_APPLIED = "CHOP_SCOPE_POLICY_APPLIED"
REASON_CHOP_SCOPE_POLICY_ACTIVE = "CHOP_SCOPE_POLICY_ACTIVE"
REASON_CHOP_SCOPE_POLICY_CLEARED = "CHOP_SCOPE_POLICY_CLEARED"
REASON_CHOP_SCOPE_POLICY_BLOCKS_TRANSITION = "CHOP_SCOPE_POLICY_BLOCKS_TRANSITION"
REASON_CHOP_CONTEXT_MISSING_FAIL_CLOSED = "CHOP_CONTEXT_MISSING_FAIL_CLOSED"
REASON_UNKNOWN_NOT_BOUND_FAIL_CLOSED = "UNKNOWN_NOT_BOUND_FAIL_CLOSED"
REASON_NON_CHOP_PASSTHROUGH = "NON_CHOP_PASSTHROUGH"


class ChopScopePolicyStatus(str, Enum):
    """Canonical CHOP scope-policy result — not Direction, not Switch."""

    INACTIVE = "inactive"
    ACTIVE_DEFENSIVE = "active_defensive"
    BLOCK_OBSERVE = "block_observe"
    FAIL_CLOSED = "fail_closed"


class ChopScopePolicyEvidenceReason(str, Enum):
    """Evidence / reason codes for CHOP scope-policy binding."""

    CHOP_DETECTED_APPLIED = "chop_detected_applied"
    CHOP_LATCH_CONTINUED = "chop_latch_continued"
    CHOP_CLEARED_VIA_NOOP = "chop_cleared_via_noop"
    CHOP_CONTEXT_MISSING = "chop_context_missing"
    UNKNOWN_UNBOUND = "unknown_unbound"
    NON_CHOP_EVENT = "non_chop_event"


@dataclass(frozen=True)
class ChopScopePolicyResultV1:
    """Outcome of binding a scope event to CHOP scope policy."""

    status: ChopScopePolicyStatus
    chop_latched: bool
    entry_blocked: bool
    direction_created: bool
    switch_triggered: bool
    side_state_mutated: bool
    reason_code: str
    evidence_reason: ChopScopePolicyEvidenceReason
    transition_allowed: bool
    runtime_scope_state: RuntimeScopeState


def apply_chop_scope_event_policy_v1(
    *,
    event: Optional[ScopeEvent],
    scope_state: Optional[RuntimeScopeState],
    now_tick: int,
) -> ChopScopePolicyResultV1:
    """
    Bind ``ScopeEvent.CHOP_DETECTED`` (and recovery) to RuntimeScopeState policy.

    Fail-closed when event or scope_state is missing. Never invents Direction,
    never mutates SideState, never triggers a Switch.
    """
    if event is None or scope_state is None:
        empty = scope_state if scope_state is not None else RuntimeScopeState(now_tick=now_tick)
        st = replace(empty, now_tick=now_tick, chop_latched=True)
        return ChopScopePolicyResultV1(
            status=ChopScopePolicyStatus.FAIL_CLOSED,
            chop_latched=True,
            entry_blocked=True,
            direction_created=False,
            switch_triggered=False,
            side_state_mutated=False,
            reason_code=REASON_CHOP_CONTEXT_MISSING_FAIL_CLOSED,
            evidence_reason=ChopScopePolicyEvidenceReason.CHOP_CONTEXT_MISSING,
            transition_allowed=False,
            runtime_scope_state=st,
        )

    st = replace(scope_state, now_tick=now_tick)

    if event is ScopeEvent.SCOPE_UNKNOWN:
        return ChopScopePolicyResultV1(
            status=ChopScopePolicyStatus.FAIL_CLOSED,
            chop_latched=st.chop_latched,
            entry_blocked=True,
            direction_created=False,
            switch_triggered=False,
            side_state_mutated=False,
            reason_code=REASON_UNKNOWN_NOT_BOUND_FAIL_CLOSED,
            evidence_reason=ChopScopePolicyEvidenceReason.UNKNOWN_UNBOUND,
            transition_allowed=False,
            runtime_scope_state=st,
        )

    if event is ScopeEvent.CHOP_DETECTED:
        st2 = replace(st, chop_latched=True)
        return ChopScopePolicyResultV1(
            status=ChopScopePolicyStatus.ACTIVE_DEFENSIVE,
            chop_latched=True,
            entry_blocked=True,
            direction_created=False,
            switch_triggered=False,
            side_state_mutated=False,
            reason_code=REASON_CHOP_SCOPE_POLICY_APPLIED,
            evidence_reason=ChopScopePolicyEvidenceReason.CHOP_DETECTED_APPLIED,
            transition_allowed=True,
            runtime_scope_state=st2,
        )

    if event is ScopeEvent.NOOP and st.chop_latched:
        st2 = replace(st, chop_latched=False)
        return ChopScopePolicyResultV1(
            status=ChopScopePolicyStatus.INACTIVE,
            chop_latched=False,
            entry_blocked=False,
            direction_created=False,
            switch_triggered=False,
            side_state_mutated=False,
            reason_code=REASON_CHOP_SCOPE_POLICY_CLEARED,
            evidence_reason=ChopScopePolicyEvidenceReason.CHOP_CLEARED_VIA_NOOP,
            transition_allowed=True,
            runtime_scope_state=st2,
        )

    if st.chop_latched:
        return ChopScopePolicyResultV1(
            status=ChopScopePolicyStatus.ACTIVE_DEFENSIVE,
            chop_latched=True,
            entry_blocked=True,
            direction_created=False,
            switch_triggered=False,
            side_state_mutated=False,
            reason_code=REASON_CHOP_SCOPE_POLICY_ACTIVE,
            evidence_reason=ChopScopePolicyEvidenceReason.CHOP_LATCH_CONTINUED,
            transition_allowed=True,
            runtime_scope_state=st,
        )

    return ChopScopePolicyResultV1(
        status=ChopScopePolicyStatus.INACTIVE,
        chop_latched=False,
        entry_blocked=False,
        direction_created=False,
        switch_triggered=False,
        side_state_mutated=False,
        reason_code=REASON_NON_CHOP_PASSTHROUGH,
        evidence_reason=ChopScopePolicyEvidenceReason.NON_CHOP_EVENT,
        transition_allowed=True,
        runtime_scope_state=st,
    )


def chop_scope_policy_blocks_side_transition_v1(
    *,
    chop_latched: bool,
    event: ScopeEvent,
) -> bool:
    """True when active CHOP scope policy must block arming / activation / switch."""
    if not chop_latched:
        return False
    return event in (
        ScopeEvent.UPSCOPE_CONFIRMED,
        ScopeEvent.DOWNSCOPE_CONFIRMED,
    )


def project_composition_chop_guard_from_scope_policy_v1(
    *,
    chop_latched: bool,
    policy_status: Optional[ChopScopePolicyStatus] = None,
) -> str:
    """
    Composition-only projection of canonical CHOP scope policy.

    Returns CompositionChopGuardStatus *values* as strings to avoid an import
    cycle; callers map into ``CompositionChopGuardStatus``.
    """
    if policy_status is ChopScopePolicyStatus.FAIL_CLOSED:
        return "chop_guard_block"
    if chop_latched or policy_status is ChopScopePolicyStatus.ACTIVE_DEFENSIVE:
        return "chop_guard_block"
    if policy_status is ChopScopePolicyStatus.BLOCK_OBSERVE:
        return "chop_guard_candidate"
    return "none"


def build_chop_scope_event_policy_status_fields_v1() -> Mapping[str, str]:
    return {
        "PACKAGE_MARKER": PACKAGE_MARKER,
        "CHOP_BINDING_STATUS": CHOP_BINDING_STATUS,
        "UNKNOWN_BINDING_STATUS": UNKNOWN_BINDING_STATUS,
        "CHOP_SCOPE_POLICY_OWNER": CHOP_SCOPE_POLICY_OWNER,
        "SOLE_SCOPE_STATE_OWNER": SOLE_SCOPE_STATE_OWNER,
        "SOLE_BULL_BEAR_STATE_OWNER": SOLE_BULL_BEAR_STATE_OWNER,
        "SOLE_SWITCH_AUTHORITY": SOLE_SWITCH_AUTHORITY,
        "COMPOSITION_CHOP_STATUS": COMPOSITION_CHOP_STATUS,
        "COMPOSITION_BOTH_SIDES_CONFIRMED_ROLE": COMPOSITION_BOTH_SIDES_CONFIRMED_ROLE,
        "CHOP_SEMANTIC_SSOT_COUNT": CHOP_SEMANTIC_SSOT_COUNT,
        "CHOP_CANONICAL_INPUT_EVENT": CHOP_CANONICAL_INPUT_EVENT,
        "CHOP_CAN_CREATE_DIRECTION": CHOP_CAN_CREATE_DIRECTION,
        "CHOP_CAN_TRIGGER_SWITCH": CHOP_CAN_TRIGGER_SWITCH,
        "CHOP_CAN_MUTATE_SIDE_STATE": CHOP_CAN_MUTATE_SIDE_STATE,
        "CHOP_CAN_BYPASS_TRANSITION_STATE": CHOP_CAN_BYPASS_TRANSITION_STATE,
        "UNKNOWN_CAN_CREATE_DIRECTION": UNKNOWN_CAN_CREATE_DIRECTION,
        "UNKNOWN_CAN_TRIGGER_SWITCH": UNKNOWN_CAN_TRIGGER_SWITCH,
        "PRODUCTIVE_CHOP_BYPASS_PATHS": PRODUCTIVE_CHOP_BYPASS_PATHS,
        "PRODUCTIVE_COMPETING_AUTHORITIES": PRODUCTIVE_COMPETING_AUTHORITIES,
        "DYNAMIC_SCOPE_PRECEDES_SWITCH": DYNAMIC_SCOPE_PRECEDES_SWITCH,
        "MULTI_CYCLE_SCOPE_CONTINUITY": MULTI_CYCLE_SCOPE_CONTINUITY,
        "BACKTEST_RUNTIME_AUTHORITY_PARITY": BACKTEST_RUNTIME_AUTHORITY_PARITY,
        "SCENARIO_SCOPE_EVENT_INJECTION_STATUS": SCENARIO_SCOPE_EVENT_INJECTION_STATUS,
        "LIVE_AUTHORIZED": LIVE_AUTHORIZED,
        "ORDERS_ENABLED": ORDERS_ENABLED,
        "RUNTIME_BRIDGE_STATUS": RUNTIME_BRIDGE_STATUS,
    }


def assert_chop_scope_policy_invariants_v1(
    result: ChopScopePolicyResultV1,
) -> Tuple[bool, Tuple[str, ...]]:
    """Machine-checkable invariants for a single binding result."""
    violations: list[str] = []
    if result.direction_created:
        violations.append("CHOP_CREATED_DIRECTION")
    if result.switch_triggered:
        violations.append("CHOP_TRIGGERED_SWITCH")
    if result.side_state_mutated:
        violations.append("CHOP_MUTATED_SIDE_STATE")
    if result.status is ChopScopePolicyStatus.FAIL_CLOSED and not result.entry_blocked:
        violations.append("FAIL_CLOSED_WITHOUT_ENTRY_BLOCK")
    if result.chop_latched and not result.entry_blocked:
        violations.append("LATCHED_WITHOUT_ENTRY_BLOCK")
    return (len(violations) == 0, tuple(violations))
