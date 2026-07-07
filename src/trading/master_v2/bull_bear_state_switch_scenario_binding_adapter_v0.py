# src/trading/master_v2/bull_bear_state_switch_scenario_binding_adapter_v0.py
"""
Scenario replay adapter: binds offline Double Play scenario ticks to the canonical
``double_play_state.transition_state`` owner without duplicating state-switch logic.

Wiring-only parity slice — no runtime authority, no trading semantic extension.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Tuple

from trading.master_v2.double_play_state import (
    ActiveSide,
    DynamicScopeRules,
    RuntimeEnvelope,
    RuntimeScopeState,
    ScopeEvent,
    SideState,
    TransitionDecision,
    derive_active_side,
    transition_state,
)

BULL_BEAR_STATE_SWITCH_SCENARIO_BINDING_ADAPTER_LAYER_VERSION = "v0"
BULL_BEAR_STATE_SWITCH_SCENARIO_BINDING_ADAPTER_OWNER = (
    "trading.master_v2.bull_bear_state_switch_scenario_binding_adapter_v0"
)
CANONICAL_STATE_SWITCH_OWNER = "trading.master_v2.double_play_state"

STATE_SWITCH_EFFECT_BOUND_OFFLINE = "BOUND_OFFLINE"
STATE_SWITCH_EFFECT_NONE = "NONE"

RUNTIME_AUTHORITY_EFFECT_NONE = "NONE"
ORDER_EFFECT_NONE = "NONE"


@dataclass(frozen=True)
class ScenarioStateSwitchContextV0:
    """Explicit offline scenario state-switch context — never inferred from shortcuts."""

    instrument_id: str
    trading_epoch: int
    context_reference: str
    side_state: SideState
    scope_event: ScopeEvent
    scope_state: RuntimeScopeState
    rules: DynamicScopeRules
    envelope: RuntimeEnvelope
    now_tick: int
    scope_event_id: str = ""


@dataclass(frozen=True)
class ScenarioStateSwitchBindingResultV0:
    side_state_before: SideState
    side_state_after: SideState
    scope_state_after: RuntimeScopeState
    transition: TransitionDecision
    bull_layer_state: SideState
    bear_layer_state: SideState
    active_side: ActiveSide
    state_switch_ref: str
    state_switch_effect: str
    runtime_authority_effect: str = RUNTIME_AUTHORITY_EFFECT_NONE
    order_effect: str = ORDER_EFFECT_NONE


def project_bull_layer_side_state_v0(side: SideState) -> SideState:
    """Canonical bull-layer projection from unified side state (reuse contract)."""
    if side in (
        SideState.LONG_ACTIVE,
        SideState.LONG_ARMED,
        SideState.LONG_BLOCKED,
        SideState.SWITCH_LONG_TO_SHORT_PENDING,
    ):
        return side
    if side in (SideState.SHORT_ACTIVE, SideState.SHORT_ARMED, SideState.SHORT_BLOCKED):
        return SideState.LONG_BLOCKED
    return SideState.NEUTRAL_OBSERVE


def project_bear_layer_side_state_v0(side: SideState) -> SideState:
    """Canonical bear-layer projection from unified side state (reuse contract)."""
    if side in (
        SideState.SHORT_ACTIVE,
        SideState.SHORT_ARMED,
        SideState.SHORT_BLOCKED,
        SideState.SWITCH_SHORT_TO_LONG_PENDING,
    ):
        return side
    if side in (SideState.LONG_ACTIVE, SideState.LONG_ARMED, SideState.LONG_BLOCKED):
        return SideState.SHORT_BLOCKED
    return SideState.NEUTRAL_OBSERVE


def _derive_state_switch_id(
    *,
    instrument_id: str,
    trading_epoch: int,
    scope_event_id: str,
) -> str:
    material = f"{instrument_id}|{trading_epoch}|{scope_event_id}"
    return f"state-switch-{hashlib.sha256(material.encode('utf-8')).hexdigest()[:24]}"


def compute_state_switch_semantic_digest_v0(
    *,
    state_switch_id: str,
    instrument_id: str,
    trading_epoch: int,
    previous_side_state: str,
    next_side_state: str,
    scope_event_type: str,
    transition_allowed: bool,
    transition_reason_code: str,
) -> str:
    payload = {
        "instrument_id": instrument_id,
        "next_side_state": next_side_state,
        "previous_side_state": previous_side_state,
        "scope_event_type": scope_event_type,
        "state_switch_id": state_switch_id,
        "trading_epoch": trading_epoch,
        "transition_allowed": transition_allowed,
        "transition_reason_code": transition_reason_code,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def evaluate_scenario_state_switch_v0(
    ctx: ScenarioStateSwitchContextV0,
) -> ScenarioStateSwitchBindingResultV0:
    """Evaluate one scenario tick through canonical ``transition_state`` only."""
    side_before = ctx.side_state
    side_after, scope_after, transition = transition_state(
        side_state=ctx.side_state,
        event=ctx.scope_event,
        scope_state=ctx.scope_state,
        rules=ctx.rules,
        envelope=ctx.envelope,
        now_tick=ctx.now_tick,
    )
    scope_event_id = ctx.scope_event_id or f"{ctx.context_reference}-{ctx.scope_event.value}"
    state_switch_id = _derive_state_switch_id(
        instrument_id=ctx.instrument_id,
        trading_epoch=ctx.trading_epoch,
        scope_event_id=scope_event_id,
    )
    return ScenarioStateSwitchBindingResultV0(
        side_state_before=side_before,
        side_state_after=side_after,
        scope_state_after=scope_after,
        transition=transition,
        bull_layer_state=project_bull_layer_side_state_v0(side_after),
        bear_layer_state=project_bear_layer_side_state_v0(side_after),
        active_side=derive_active_side(side_after),
        state_switch_ref=state_switch_id,
        state_switch_effect=STATE_SWITCH_EFFECT_BOUND_OFFLINE,
    )


def state_switch_binding_non_authority_boundary_ok_v0(
    binding: ScenarioStateSwitchBindingResultV0,
) -> bool:
    if binding.runtime_authority_effect != RUNTIME_AUTHORITY_EFFECT_NONE:
        return False
    if binding.order_effect != ORDER_EFFECT_NONE:
        return False
    if binding.transition.live_authorization_granted:
        return False
    if binding.state_switch_effect not in {
        STATE_SWITCH_EFFECT_NONE,
        STATE_SWITCH_EFFECT_BOUND_OFFLINE,
    }:
        return False
    if (
        binding.state_switch_effect == STATE_SWITCH_EFFECT_BOUND_OFFLINE
        and not binding.state_switch_ref
    ):
        return False
    return True


def system_economic_evidence_admissible_v0(
    binding: ScenarioStateSwitchBindingResultV0,
) -> bool:
    return False


def state_switch_parity_aligned_v0(
    *,
    integrated_previous: str,
    integrated_next: str,
    integrated_transition_allowed: bool,
    integrated_transition_reason: str,
    scenario_binding: ScenarioStateSwitchBindingResultV0,
) -> bool:
    return (
        integrated_previous == scenario_binding.side_state_before.value
        and integrated_next == scenario_binding.side_state_after.value
        and integrated_transition_allowed == scenario_binding.transition.allowed
        and integrated_transition_reason == scenario_binding.transition.reason_code
    )


def mirrored_side_states_parity_ok_v0(
    long_side: SideState,
    short_side: SideState,
) -> bool:
    """Long-path vs mirrored short-path must remain mutually exclusive at active states."""
    long_active = long_side == SideState.LONG_ACTIVE
    short_active = short_side == SideState.SHORT_ACTIVE
    return not (long_active and short_active)
