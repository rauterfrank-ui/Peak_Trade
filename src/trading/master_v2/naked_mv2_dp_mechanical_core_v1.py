# src/trading/master_v2/naked_mv2_dp_mechanical_core_v1.py
"""
Isolated naked mechanical core for Master V2 + Double Play (v1).

Single price-based switch rule: CM_t >= D_t with explicit external D_t only.
No confirmation, cooldown, volatility bands, or legacy scope distances.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, Tuple

from trading.master_v2.naked_mv2_dp_regime_v1 import NakedRegimeV1

from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.contracts_v1 import ScopeStateV1
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l8_running_reference_v1 import (
    initial_running_reference_state_v1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.running_mechanics_pipeline_v1 import (
    run_running_mechanics_l8_through_l10_v1,
)
from trading.master_v2.naked_mv2_dp_single_boundary_purification_v1 import (
    naked_boundary_fail_closed_reasons_from_distance,
)

MECHANICAL_CORE_VERSION = "naked_mv2_dp_mechanical_core/v1"
MECHANICAL_CORE_OWNER = "trading.master_v2.naked_mv2_dp_mechanical_core_v1"
D_T_ROLE = "EXPLICIT_EXTERNAL_REQUIRED_INPUT"
D_T_INTERNAL_DERIVATION_PRESENT = False
SOLE_PRICE_SWITCH_RULE = "CM_t>=D_t"


@dataclass(frozen=True)
class NakedMechanicalStateV1:
    instrument_id: str
    regime: NakedRegimeV1
    reference_price_r_t: float


@dataclass(frozen=True)
class NakedMechanicalStepInputV1:
    instrument_id: str
    mark_price_m_t: float
    previous_state: NakedMechanicalStateV1
    dynamic_scope_d_t: Optional[float]


@dataclass(frozen=True)
class NakedMechanicalStepResultV1:
    instrument_id: str
    m_t: float
    r_t_pre: float
    r_t_post: float
    cm_t: float
    d_t: Optional[float]
    state_pre: NakedRegimeV1
    switch_condition_met: bool
    state_post: NakedRegimeV1
    r_t_reset_performed: bool
    fail_closed: bool
    fail_reasons: Tuple[str, ...]


def _validate_mark_price(m_t: float) -> Tuple[str, ...]:
    if not math.isfinite(m_t) or m_t <= 0.0:
        return ("naked_mechanical_mark_price_invalid",)
    return ()


def execute_naked_mechanical_step_v1(
    inp: NakedMechanicalStepInputV1,
) -> NakedMechanicalStepResultV1:
    """
    Deterministic one-step naked mechanical owner.

    Consumes explicit D_t; never derives scope distance internally.
    """
    m_t = float(inp.mark_price_m_t)
    prev = inp.previous_state
    r_t_pre = float(prev.reference_price_r_t)
    d_raw = inp.dynamic_scope_d_t

    base = NakedMechanicalStepResultV1(
        instrument_id=inp.instrument_id,
        m_t=m_t,
        r_t_pre=r_t_pre,
        r_t_post=r_t_pre,
        cm_t=0.0,
        d_t=d_raw,
        state_pre=prev.regime,
        switch_condition_met=False,
        state_post=prev.regime,
        r_t_reset_performed=False,
        fail_closed=False,
        fail_reasons=(),
    )

    reasons: list[str] = []
    if inp.instrument_id != prev.instrument_id:
        reasons.append("naked_mechanical_instrument_mismatch")
    reasons.extend(_validate_mark_price(m_t))
    reasons.extend(naked_boundary_fail_closed_reasons_from_distance(d_raw))
    if reasons:
        return _fail_closed_step_result(base, tuple(reasons), prev)

    assert d_raw is not None  # fail-closed above when None
    d_t = float(d_raw)

    scope = ScopeStateV1(
        instrument_id=inp.instrument_id,
        d_t=d_t,
        nullline_price=0.0,
        nullline_provenance_epoch=0,
        generator_id="mechanical_core_legacy_scope_adapter/v1",
        valid=True,
    )
    running = initial_running_reference_state_v1(
        instrument_id=inp.instrument_id,
        reference_price_r_t=r_t_pre,
    )
    layered = run_running_mechanics_l8_through_l10_v1(
        scope=scope,
        regime=prev.regime,
        mark_price_m_t=m_t,
        running_reference=running,
    )

    return NakedMechanicalStepResultV1(
        instrument_id=inp.instrument_id,
        m_t=m_t,
        r_t_pre=layered.r_t_pre,
        r_t_post=layered.r_t_post,
        cm_t=layered.cm_t,
        d_t=d_t,
        state_pre=layered.state_pre,
        switch_condition_met=layered.switch_condition_met,
        state_post=layered.state_post,
        r_t_reset_performed=layered.r_t_reset_performed,
        fail_closed=False,
        fail_reasons=(),
    )


def next_naked_mechanical_state_v1(
    *,
    previous: NakedMechanicalStateV1,
    step: NakedMechanicalStepResultV1,
) -> NakedMechanicalStateV1:
    """Derive persisted state after a step (unchanged when fail-closed)."""
    if step.fail_closed:
        return previous
    r_t = step.m_t if step.r_t_reset_performed else step.r_t_post
    return NakedMechanicalStateV1(
        instrument_id=step.instrument_id,
        regime=step.state_post,
        reference_price_r_t=r_t,
    )


def _fail_closed_step_result(
    base: NakedMechanicalStepResultV1,
    reasons: Tuple[str, ...],
    prev: NakedMechanicalStateV1,
) -> NakedMechanicalStepResultV1:
    return NakedMechanicalStepResultV1(
        instrument_id=base.instrument_id,
        m_t=base.m_t,
        r_t_pre=base.r_t_pre,
        r_t_post=base.r_t_pre,
        cm_t=0.0,
        d_t=base.d_t,
        state_pre=prev.regime,
        switch_condition_met=False,
        state_post=prev.regime,
        r_t_reset_performed=False,
        fail_closed=True,
        fail_reasons=reasons,
    )


__all__ = [
    "MECHANICAL_CORE_VERSION",
    "MECHANICAL_CORE_OWNER",
    "D_T_ROLE",
    "D_T_INTERNAL_DERIVATION_PRESENT",
    "SOLE_PRICE_SWITCH_RULE",
    "NakedRegimeV1",
    "NakedMechanicalStateV1",
    "NakedMechanicalStepInputV1",
    "NakedMechanicalStepResultV1",
    "execute_naked_mechanical_step_v1",
    "next_naked_mechanical_state_v1",
]
