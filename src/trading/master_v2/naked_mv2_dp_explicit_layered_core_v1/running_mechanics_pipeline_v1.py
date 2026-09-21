"""Compose L7 scope context → L8 → L9 → L10 for one mechanical step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from trading.master_v2.naked_mv2_dp_regime_v1 import NakedRegimeV1
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.contracts_v1 import (
    BullBearSwitchInputV1,
    CounterMoveInputV1,
    RunningReferenceStateV1,
    RunningReferenceStepInputV1,
    ScopeStateV1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l10_bull_bear_switch_v1 import (
    apply_l10_bull_bear_switch_v1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l8_running_reference_v1 import (
    apply_l8_running_reference_step_v1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l9_counter_move_v1 import (
    apply_l9_counter_move_v1,
)


@dataclass(frozen=True)
class RunningMechanicsStepResultV1:
    instrument_id: str
    m_t: float
    r_t_pre: float
    r_t_post: float
    cm_t: float
    d_t: float
    state_pre: NakedRegimeV1
    switch_condition_met: bool
    state_post: NakedRegimeV1
    r_t_reset_performed: bool
    nullline_price: float


def run_running_mechanics_l8_through_l10_v1(
    *,
    scope: ScopeStateV1,
    regime: NakedRegimeV1,
    mark_price_m_t: float,
    running_reference: RunningReferenceStateV1,
) -> RunningMechanicsStepResultV1:
    l8 = apply_l8_running_reference_step_v1(
        RunningReferenceStepInputV1(
            regime=regime,
            mark_price_m_t=mark_price_m_t,
            previous=running_reference,
        )
    )
    l9 = apply_l9_counter_move_v1(
        CounterMoveInputV1(
            regime=regime,
            mark_price_m_t=mark_price_m_t,
            running_reference=l8.state,
        )
    )
    l10 = apply_l10_bull_bear_switch_v1(
        BullBearSwitchInputV1(
            regime_pre=regime,
            cm_t=l9.counter_move.cm_t,
            d_t=scope.d_t,
            mark_price_m_t=mark_price_m_t,
            running_reference_post=l8.state,
        )
    )
    return RunningMechanicsStepResultV1(
        instrument_id=scope.instrument_id,
        m_t=float(mark_price_m_t),
        r_t_pre=l8.previous_r_t,
        r_t_post=l8.updated_r_t,
        cm_t=l9.counter_move.cm_t,
        d_t=scope.d_t,
        state_pre=l10.regime_pre,
        switch_condition_met=l10.switch_condition_met,
        state_post=l10.regime_post,
        r_t_reset_performed=l10.r_t_reset_performed,
        nullline_price=scope.nullline_price,
    )


__all__ = [
    "RunningMechanicsStepResultV1",
    "run_running_mechanics_l8_through_l10_v1",
]
