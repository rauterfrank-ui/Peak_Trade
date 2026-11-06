# src/trading/master_v2/naked_mv2_dp_single_boundary_purification_v1.py
"""
Naked MV2+Double Play single-boundary Dynamic Scope purification v1.

Architecture: one counter-movement boundary, R_t internal reference, CM vs D,
GREEN/YELLOW/RED via Candidate→Confirmed.

CALIBRATION_DIRECTION_AUTHORITY=OPEN
NUMERIC_FORMULA_AUTHORITY=NONE — no productive D_t producer (incl. not σ_t * M_t).
"""

from __future__ import annotations

import math
from dataclasses import replace
from typing import Optional, Tuple

from trading.master_v2.canonical_market_context_v1 import (
    BarFinalityStatus,
    CanonicalMarketContextV1,
    ClockTrustStatus,
    DataIntegrityStatus,
)
from trading.master_v2.canonical_volatility_estimate_typed_consumption_contract_v1 import (
    CANONICAL_UNIT,
    validate_canonical_volatility_estimate_v1,
)
from trading.master_v2.deterministic_scope_event_generator_v1 import (
    CanonicalScopeEventType,
    ScopeDirectionState,
    ScopeEventEvidenceV1,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import PolicySignalV0
from trading.master_v2.double_play_state import ActiveSide, RuntimeScopeState, SideState

PURIFICATION_VERSION = "naked_mv2_dp_single_boundary_purification/v1"
PURIFICATION_OWNER = "trading.master_v2.naked_mv2_dp_single_boundary_purification_v1"
CALIBRATION_DIRECTION_AUTHORITY = "OPEN"
NUMERIC_FORMULA_AUTHORITY = "NONE"


def resolve_typed_sigma_for_naked_boundary_v1(
    context: CanonicalMarketContextV1,
) -> Tuple[Optional[float], Tuple[str, ...]]:
    """
    Typed CURRENT CMC σ only. Returns (sigma, block_reasons).
    sigma is None when fail-closed (missing/stale/invalid/<=0).
    """
    reasons: list[str] = []
    estimate = context.canonical_volatility_estimate
    if estimate is None:
        return None, ("naked_typed_sigma_missing",)
    try:
        validated = validate_canonical_volatility_estimate_v1(estimate)
    except Exception as exc:  # noqa: BLE001 — fail-closed surface
        return None, (f"naked_typed_sigma_invalid:{type(exc).__name__}",)
    if validated.unit != CANONICAL_UNIT:
        return None, ("naked_typed_sigma_unit_invalid",)
    value = float(validated.value)
    if not math.isfinite(value) or value <= 0.0:
        return None, ("naked_typed_sigma_non_positive",)
    if context.data_integrity_status is not DataIntegrityStatus.TRUSTED:
        reasons.append("naked_market_data_integrity_untrusted")
    if context.clock_trust_status is not ClockTrustStatus.TRUSTED:
        reasons.append("naked_clock_untrusted")
    if context.bar_finality_status is not BarFinalityStatus.FINALIZED:
        reasons.append("naked_bar_unfinalized")
    if reasons:
        return None, tuple(reasons)
    return value, ()


def compute_single_boundary_distance_v1(
    *,
    sigma_t: float,
    mark_price: float,
) -> Optional[float]:
    """
    Productive boundary distance producer — intentionally unbound.

    DIRECT_VOL (σ_t * M_t) and INVERSE_SENSITIVITY are not authorized here.
    Callers must fail-closed until Owner ratifies a numeric calibration class.
    """
    _ = (sigma_t, mark_price)
    return None


def compute_counter_move_v1(
    *,
    direction: ScopeDirectionState,
    mark_price: float,
    reference_price: float,
) -> float:
    m = float(mark_price)
    r = float(reference_price)
    if direction is ScopeDirectionState.LONG:
        return max(0.0, r - m)
    return max(0.0, m - r)


def update_scope_internal_reference_state_v1(
    *,
    mark_price: float,
    side: ActiveSide,
    st: RuntimeScopeState,
) -> RuntimeScopeState:
    """R_t lifecycle for ACTIVE sides only (not NULLLINE)."""
    if side == ActiveSide.LONG:
        new_r = max(st.anchor_price, mark_price) if st.anchor_price > 0 else mark_price
        return replace(st, anchor_price=new_r)
    if side == ActiveSide.SHORT:
        new_r = min(st.anchor_price, mark_price) if st.anchor_price > 0 else mark_price
        return replace(st, anchor_price=new_r)
    return st


def reset_scope_internal_reference_after_confirmed_switch_v1(
    *,
    st: RuntimeScopeState,
    mark_price: float,
    scope_event_type: CanonicalScopeEventType,
    transition_allowed: bool,
) -> RuntimeScopeState:
    if not transition_allowed:
        return st
    if scope_event_type not in (
        CanonicalScopeEventType.DOWNSCOPE_CONFIRMED,
        CanonicalScopeEventType.UPSCOPE_CONFIRMED,
    ):
        return st
    return replace(st, anchor_price=float(mark_price))


def suppress_naked_active_profit_protection_signal_v1(
    side_state: SideState,
    profit_protection_signal: PolicySignalV0,
) -> PolicySignalV0:
    if side_state in (SideState.LONG_ACTIVE, SideState.SHORT_ACTIVE):
        return PolicySignalV0(triggered=False)
    return profit_protection_signal


def suppress_naked_scope_adverse_exit_signal_v1(
    scope_event: ScopeEventEvidenceV1,
    passthrough: PolicySignalV0,
) -> PolicySignalV0:
    if CanonicalScopeEventType.ADVERSE_EXIT_CANDIDATE.value in scope_event.matched_conditions:
        return PolicySignalV0(triggered=False)
    if scope_event.event_type is CanonicalScopeEventType.ADVERSE_EXIT_CANDIDATE:
        return PolicySignalV0(triggered=False)
    return passthrough


def naked_boundary_fail_closed_reasons_from_distance(
    distance: Optional[float],
) -> Tuple[str, ...]:
    if distance is None:
        return ("naked_boundary_distance_unavailable",)
    if not math.isfinite(distance) or distance <= 0.0:
        return ("naked_boundary_distance_invalid",)
    return ()


__all__ = [
    "PURIFICATION_VERSION",
    "PURIFICATION_OWNER",
    "resolve_typed_sigma_for_naked_boundary_v1",
    "compute_single_boundary_distance_v1",
    "compute_counter_move_v1",
    "update_scope_internal_reference_state_v1",
    "reset_scope_internal_reference_after_confirmed_switch_v1",
    "suppress_naked_active_profit_protection_signal_v1",
    "suppress_naked_scope_adverse_exit_signal_v1",
    "naked_boundary_fail_closed_reasons_from_distance",
]
