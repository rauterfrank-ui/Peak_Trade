# src/trading/master_v2/double_play_state.py
"""
Pure, dependency-light state model for Master V2 Double Play (docs-only target semantics).

No I/O, no exchange, no risk layer wiring. See docs/ops/specs/MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from typing import Optional, Tuple

DOUBLE_PLAY_STATE_LAYER_VERSION = "v0"


class SideState(str, Enum):
    """High-level double-play / scope side machine (manifest §4)."""

    NEUTRAL_OBSERVE = "neutral_observe"
    LONG_ARMED = "long_armed"
    LONG_ACTIVE = "long_active"
    LONG_BLOCKED = "long_blocked"
    SHORT_ARMED = "short_armed"
    SHORT_ACTIVE = "short_active"
    SHORT_BLOCKED = "short_blocked"
    SWITCH_LONG_TO_SHORT_PENDING = "switch_long_to_short_pending"
    SWITCH_SHORT_TO_LONG_PENDING = "switch_short_to_long_pending"
    CHOP_GUARD_BLOCK = "chop_guard_block"
    KILL_ALL = "kill_all"


class ScopeEvent(str, Enum):
    """Scope and safety events (manifest §5, extended with NOOP)."""

    DOWNSCOPE_CANDIDATE = "downscope_candidate"
    DOWNSCOPE_CONFIRMED = "downscope_confirmed"
    UPSCOPE_CANDIDATE = "upscope_candidate"
    UPSCOPE_CONFIRMED = "upscope_confirmed"
    CHOP_DETECTED = "chop_detected"
    SCOPE_UNKNOWN = "scope_unknown"
    KILL_ALL_REQUIRED = "kill_all_required"
    NOOP = "noop"


class ActiveSide(str, Enum):
    """Which side holds active exposure; manifest invariant: at most one 'active' side."""

    NEUTRAL = "neutral"
    LONG = "long"
    SHORT = "short"


@dataclass(frozen=True)
class StaticHardLimits:
    """Upper bounds; dynamic rules must not widen these (manifest §7.1)."""

    max_notional: float = 0.0
    max_leverage: float = 0.0
    max_switches_per_window: int = 0
    min_band_width: float = 1.0
    max_band_width: float = 1.0e6


@dataclass(frozen=True)
class RuntimeEnvelope:
    """Pre-authorized envelope: static limits + policy flags."""

    static: StaticHardLimits
    live_authorization: bool = False


@dataclass(frozen=True)
class DynamicScopeRules:
    """Bounded dynamic scope policy (manifest §7.2) — all numeric, no I/O."""

    downscope_band_multiplier: float = 1.0
    upscope_band_multiplier: float = 1.0
    min_band_width: float = 0.0
    max_band_width: float = 1.0e6
    min_switch_cooldown_ticks: int = 0
    # Vol proxy for band width in update_dynamic_boundaries; abstract unit.
    # None = unknown / unmaterialized. Productive paths must supply an explicit
    # quarantined legacy value or a C1-adapted typed float — never invent 1.0.
    volatility_estimate: Optional[float] = None
    # Switches in rolling window (optional enforcement in transition_state)
    max_switches_per_window: int = 1_000_000


@dataclass(frozen=True)
class RuntimeScopeState:
    """
    Hot-path state snapshot: boundaries, anchor, cooldown bookkeeping (manifest §7.3).
    All mutations happen via ``replace`` in pure functions.
    """

    anchor_price: float = 0.0
    current_upscope_boundary: float = 0.0
    current_downscope_boundary: float = 0.0
    current_hysteresis_band: float = 0.0
    last_switch_tick: int = -1_000_000
    now_tick: int = 0
    scope_stability_ticks: int = 0
    switches_in_window: int = 0
    # Window start for switch counting (simplified: reset every N ticks in caller)
    window_start_tick: int = 0
    # Last completed migration to a new ActiveSide (for cooldown)
    last_completed_side_switch_tick: int = -1_000_000
    # Chop scope policy latch (CHOP_SCOPE_EVENT_POLICY_BINDING_CONTRACT_V1).
    # Cleared via NOOP while latched; never invents SideState / Direction / Switch.
    chop_latched: bool = False


@dataclass(frozen=True)
class TransitionDecision:
    """Outcome of ``transition_state``; never authorizes live."""

    allowed: bool
    reason_code: str
    live_authorization_granted: bool = False


def derive_active_side(side: SideState) -> ActiveSide:
    if side in (SideState.LONG_ACTIVE,):
        return ActiveSide.LONG
    if side in (SideState.SHORT_ACTIVE,):
        return ActiveSide.SHORT
    return ActiveSide.NEUTRAL


def _both_active_invariant_ok(side: SideState) -> bool:
    return not (side == SideState.LONG_ACTIVE and side == SideState.SHORT_ACTIVE)


def envelope_valid(envelope: RuntimeEnvelope) -> bool:
    """Fail-closed: invalid envelope blocks transitions."""
    s = envelope.static
    if envelope.live_authorization:
        return False
    if s.min_band_width <= 0 or s.max_band_width < s.min_band_width:
        return False
    if s.max_notional < 0 or s.max_leverage < 0:
        return False
    if s.max_switches_per_window < 0:
        return False
    return True


def rules_valid(rules: DynamicScopeRules) -> bool:
    if rules.min_band_width < 0 or rules.max_band_width < rules.min_band_width:
        return False
    if rules.min_switch_cooldown_ticks < 0:
        return False
    if rules.max_switches_per_window < 0:
        return False
    # Band updates require an explicit volatility estimate. None / non-finite /
    # negative remain invalid (no silent 1.0 constructor materialization).
    if rules.volatility_estimate is not None:
        vol = float(rules.volatility_estimate)
        if vol != vol or vol < 0.0:  # NaN or negative
            return False
    return True


def _switch_count_ok(rule: DynamicScopeRules, st: RuntimeScopeState) -> bool:
    if rule.max_switches_per_window <= 0:
        return True
    return st.switches_in_window < rule.max_switches_per_window


def _cooldown_allows_opposite_switch(
    *,
    now_tick: int,
    st: RuntimeScopeState,
    rules: DynamicScopeRules,
) -> bool:
    if rules.min_switch_cooldown_ticks <= 0:
        return True
    return (now_tick - st.last_completed_side_switch_tick) >= rules.min_switch_cooldown_ticks


def clamp_band_width(raw: float, rules: DynamicScopeRules, env: RuntimeEnvelope) -> float:
    lo = max(rules.min_band_width, env.static.min_band_width)
    hi = min(rules.max_band_width, env.static.max_band_width)
    if hi < lo:
        return lo
    return max(lo, min(hi, raw))


def update_dynamic_boundaries(
    *,
    mark_price: float,
    side: ActiveSide,
    st: RuntimeScopeState,
    rules: DynamicScopeRules,
    env: RuntimeEnvelope,
) -> RuntimeScopeState:
    """
    Update trailing anchor and scope boundaries; band width is clamped (manifest §6–7).

    Long: anchor chases new highs; downscope boundary trails below anchor.
    Short: anchor chases new lows; upscope boundary trails above anchor.

    When ``chop_latched`` is true, trailing updates freeze (defensive CHOP scope policy).
    """
    if not envelope_valid(env) or not rules_valid(rules):
        return st
    if st.chop_latched:
        return st
    if rules.volatility_estimate is None:
        # Unknown volatility: freeze trailing (fail-closed; no 1.0 invention).
        return st
    band = clamp_band_width(float(rules.volatility_estimate) * mark_price, rules, env)
    if side == ActiveSide.LONG:
        new_anchor = max(st.anchor_price, mark_price) if st.anchor_price > 0 else mark_price
        down = new_anchor - band
        up = new_anchor + band  # still bounded; manifest emphasizes downscope side for long
        return replace(
            st,
            anchor_price=new_anchor,
            current_downscope_boundary=down,
            current_upscope_boundary=up,
            current_hysteresis_band=band,
        )
    if side == ActiveSide.SHORT:
        new_anchor = min(st.anchor_price, mark_price) if st.anchor_price > 0 else mark_price
        up = new_anchor + band
        down = new_anchor - band
        return replace(
            st,
            anchor_price=new_anchor,
            current_upscope_boundary=up,
            current_downscope_boundary=down,
            current_hysteresis_band=band,
        )
    return st


def transition_state(
    *,
    side_state: SideState,
    event: ScopeEvent,
    scope_state: RuntimeScopeState,
    rules: DynamicScopeRules,
    envelope: RuntimeEnvelope,
    now_tick: int,
) -> Tuple[SideState, RuntimeScopeState, TransitionDecision]:
    """
    Single-step state transition. Pure: no I/O, no globals.

    * ``live_authorization`` in envelope must be False; otherwise fail-closed.
    * KILL_ALL_REQUIRED from any state -> KILL_ALL.
    * CHOP_DETECTED binds as scope policy only (``chop_latched``); SideState unchanged.
    * Active CHOP scope policy blocks arming / activation / switch confirmations.
    * Downscope / upscope **confirmed** drive long<->short pipelines (manifest §4).
    """
    # Local import keeps double_play_state dependency-light for non-CHOP callers
    # while making the CHOP binding owner explicit on the productive SM path.
    from trading.master_v2.chop_scope_event_policy_binding_v1 import (
        REASON_CHOP_SCOPE_POLICY_BLOCKS_TRANSITION,
        apply_chop_scope_event_policy_v1,
        chop_scope_policy_blocks_side_transition_v1,
    )

    st = replace(scope_state, now_tick=now_tick)

    if not _both_active_invariant_ok(side_state):
        return side_state, st, TransitionDecision(False, "INVARIANT_BROKEN_INTERNAL")

    if not envelope_valid(envelope) or not rules_valid(rules):
        return side_state, st, TransitionDecision(False, "ENVELOPE_OR_RULES_INVALID")

    if side_state == SideState.KILL_ALL and event == ScopeEvent.KILL_ALL_REQUIRED:
        return side_state, st, TransitionDecision(True, "ALREADY_KILL_ALL")
    if event == ScopeEvent.KILL_ALL_REQUIRED:
        st2 = replace(st, last_switch_tick=now_tick)
        return SideState.KILL_ALL, st2, TransitionDecision(True, "KILL_ALL")

    if side_state == SideState.KILL_ALL:
        return side_state, st, TransitionDecision(False, "IN_KILL_ALL")

    if event in (ScopeEvent.SCOPE_UNKNOWN,):
        return side_state, st, TransitionDecision(False, "SCOPE_UNKNOWN_FAIL_CLOSED")

    # Canonical CHOP binding: scope policy only — never mutates SideState here.
    if event in (ScopeEvent.CHOP_DETECTED,):
        policy = apply_chop_scope_event_policy_v1(
            event=event,
            scope_state=st,
            now_tick=now_tick,
        )
        return (
            side_state,
            policy.runtime_scope_state,
            TransitionDecision(policy.transition_allowed, policy.reason_code),
        )

    # Legacy residual SideState.CHOP_GUARD_BLOCK: clear via NOOP; otherwise hold.
    # New CHOP events no longer enter this state (scope latch is SSOT).
    if side_state == SideState.CHOP_GUARD_BLOCK and event == ScopeEvent.NOOP:
        policy = apply_chop_scope_event_policy_v1(
            event=event,
            scope_state=st,
            now_tick=now_tick,
        )
        return (
            SideState.NEUTRAL_OBSERVE,
            policy.runtime_scope_state,
            TransitionDecision(True, "CHOP_CLEAR"),
        )

    if side_state == SideState.CHOP_GUARD_BLOCK:
        return side_state, st, TransitionDecision(False, "CHOP_STILL_BLOCKING")

    # Recovery: NOOP clears active chop latch without SideState rewrite.
    if event == ScopeEvent.NOOP and st.chop_latched:
        policy = apply_chop_scope_event_policy_v1(
            event=event,
            scope_state=st,
            now_tick=now_tick,
        )
        return (
            side_state,
            policy.runtime_scope_state,
            TransitionDecision(policy.transition_allowed, policy.reason_code),
        )

    if chop_scope_policy_blocks_side_transition_v1(chop_latched=st.chop_latched, event=event):
        return (
            side_state,
            st,
            TransitionDecision(False, REASON_CHOP_SCOPE_POLICY_BLOCKS_TRANSITION),
        )

    # Cooldown: block starting a new opposite-direction pipeline from active side
    if event == ScopeEvent.DOWNSCOPE_CONFIRMED and side_state == SideState.LONG_ACTIVE:
        if not _cooldown_allows_opposite_switch(now_tick=now_tick, st=st, rules=rules):
            return side_state, st, TransitionDecision(False, "COOLDOWN_BLOCK")
        if not _switch_count_ok(rules, st):
            return side_state, st, TransitionDecision(False, "MAX_SWITCHES")
        st2 = replace(st, last_switch_tick=now_tick, switches_in_window=st.switches_in_window + 1)
        return (
            SideState.SWITCH_LONG_TO_SHORT_PENDING,
            st2,
            TransitionDecision(True, "DOWNscope_SWITCH_PENDING"),
        )

    if (
        event == ScopeEvent.DOWNSCOPE_CONFIRMED
        and side_state == SideState.SWITCH_LONG_TO_SHORT_PENDING
    ):
        return (
            SideState.LONG_BLOCKED,
            st,
            TransitionDecision(True, "LONG_BLOCKED"),
        )

    if event == ScopeEvent.DOWNSCOPE_CONFIRMED and side_state == SideState.LONG_BLOCKED:
        return SideState.SHORT_ARMED, st, TransitionDecision(True, "SHORT_ARMED")

    if event == ScopeEvent.DOWNSCOPE_CONFIRMED and side_state == SideState.SHORT_ARMED:
        st2 = replace(
            st,
            last_completed_side_switch_tick=now_tick,
            last_switch_tick=now_tick,
        )
        return SideState.SHORT_ACTIVE, st2, TransitionDecision(True, "SHORT_ACTIVE")

    if event == ScopeEvent.UPSCOPE_CONFIRMED and side_state == SideState.SHORT_ACTIVE:
        if not _cooldown_allows_opposite_switch(now_tick=now_tick, st=st, rules=rules):
            return side_state, st, TransitionDecision(False, "COOLDOWN_BLOCK")
        if not _switch_count_ok(rules, st):
            return side_state, st, TransitionDecision(False, "MAX_SWITCHES")
        st2 = replace(st, last_switch_tick=now_tick, switches_in_window=st.switches_in_window + 1)
        return (
            SideState.SWITCH_SHORT_TO_LONG_PENDING,
            st2,
            TransitionDecision(True, "UPscope_SWITCH_PENDING"),
        )

    if (
        event == ScopeEvent.UPSCOPE_CONFIRMED
        and side_state == SideState.SWITCH_SHORT_TO_LONG_PENDING
    ):
        return SideState.SHORT_BLOCKED, st, TransitionDecision(True, "SHORT_BLOCKED")

    if event == ScopeEvent.UPSCOPE_CONFIRMED and side_state == SideState.SHORT_BLOCKED:
        return SideState.LONG_ARMED, st, TransitionDecision(True, "LONG_ARMED")

    if event == ScopeEvent.UPSCOPE_CONFIRMED and side_state == SideState.LONG_ARMED:
        st2 = replace(
            st,
            last_completed_side_switch_tick=now_tick,
            last_switch_tick=now_tick,
        )
        return SideState.LONG_ACTIVE, st2, TransitionDecision(True, "LONG_ACTIVE")

    # Neutral start (manifest: neutral -> armed -> active)
    if event == ScopeEvent.UPSCOPE_CONFIRMED and side_state == SideState.NEUTRAL_OBSERVE:
        return SideState.LONG_ARMED, st, TransitionDecision(True, "NEUTRAL_TO_LONG_ARMED")

    if event == ScopeEvent.DOWNSCOPE_CONFIRMED and side_state == SideState.NEUTRAL_OBSERVE:
        return SideState.SHORT_ARMED, st, TransitionDecision(True, "NEUTRAL_TO_SHORT_ARMED")

    if event in (ScopeEvent.DOWNSCOPE_CANDIDATE, ScopeEvent.UPSCOPE_CANDIDATE):
        st2 = replace(st, scope_stability_ticks=st.scope_stability_ticks + 1)
        return side_state, st2, TransitionDecision(True, "CANDIDATE_ACK")

    if event == ScopeEvent.NOOP:
        return side_state, st, TransitionDecision(True, "NOOP")

    return side_state, st, TransitionDecision(False, "NO_TRANSITION")
