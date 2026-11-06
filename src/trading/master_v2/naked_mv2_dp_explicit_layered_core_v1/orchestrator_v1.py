"""Single naked layered-core orchestrator — explicit L1→L10, no hidden shortcuts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

from trading.market_state.distinct_market_observation_acceptor_v1 import (
    ObservationCandidateV1,
    ObservationClassification,
)
from trading.market_state.elementary_direction_v1 import ElementaryDirectionV1
from trading.master_v2.naked_mv2_dp_regime_v1 import NakedRegimeV1
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.contracts_v1 import (
    DynamicScopeGeneratorInputV1,
    DynamicScopeGeneratorV1,
    InitialDirectionInputV1,
    InitialStateInitializationInputV1,
    LayerReachabilityV1,
    MarketObservationInputV1,
    NullLineInputV1,
    RunningReferenceStateV1,
    ScopeStateMaterializationInputV1,
    SelectedFutureInputV1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.layer_catalog_v1 import LayerIdV1
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l1_selected_future_v1 import (
    apply_l1_selected_future_v1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l2_market_observation_v1 import (
    apply_l2_market_observation_v1,
    initial_market_observation_state_v1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l3_initial_direction_v1 import (
    apply_l3_initial_direction_v1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l4_initial_state_v1 import (
    apply_l4_initial_state_initialization_v1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l5_nullline_v1 import (
    apply_l5_nullline_v1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l6_dynamic_scope_generator_v1 import (
    apply_l6_dynamic_scope_generator_v1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l7_scope_state_v1 import (
    apply_l7_scope_state_materialization_v1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l8_running_reference_v1 import (
    apply_l8_running_reference_step_v1,
    initial_running_reference_state_v1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l9_counter_move_v1 import (
    apply_l9_counter_move_v1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l10_bull_bear_switch_v1 import (
    apply_l10_bull_bear_switch_v1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.contracts_v1 import (
    BullBearSwitchInputV1,
    CounterMoveInputV1,
    RunningReferenceStepInputV1,
)


@dataclass(frozen=True)
class LayerTraceEntryV1:
    layer_id: LayerIdV1
    reachability: LayerReachabilityV1


@dataclass
class NakedLayeredCoreOrchestratorStateV1:
    regime: NakedRegimeV1
    nullline_price: float
    running_reference: RunningReferenceStateV1
    scope_d_t: float


@dataclass(frozen=True)
class MechanicalStepSpecV1:
    mark_price_m_t: float
    proposed_d_t: Optional[float]


@dataclass(frozen=True)
class NakedLayeredCoreOrchestratorResultV1:
    fail_closed: bool
    fail_reasons: Tuple[str, ...]
    layer_trace: Tuple[LayerTraceEntryV1, ...]
    final_regime: Optional[NakedRegimeV1]
    final_nullline_price: Optional[float]
    final_running_r_t: Optional[float]


def orchestrate_naked_layered_core_v1(
    *,
    selected: SelectedFutureInputV1,
    initialization_observations: Sequence[ObservationCandidateV1],
    first_mechanical_step: MechanicalStepSpecV1,
    scope_generator: DynamicScopeGeneratorV1,
    follow_on_steps: Sequence[MechanicalStepSpecV1] = (),
) -> NakedLayeredCoreOrchestratorResultV1:
    trace: list[LayerTraceEntryV1] = []

    l1 = apply_l1_selected_future_v1(selected)
    trace.append(LayerTraceEntryV1(LayerIdV1.L1_SELECTED_FUTURE, LayerReachabilityV1.REACHED))

    obs_state = initial_market_observation_state_v1(l1.state)
    nullline = None
    regime_state = None

    for candidate in initialization_observations:
        l2 = apply_l2_market_observation_v1(
            MarketObservationInputV1(observation_state=obs_state, candidate=candidate)
        )
        obs_state = l2.observation_state
        if l2.acceptance_result.classification is not ObservationClassification.DISTINCT:
            continue
        trace.append(
            LayerTraceEntryV1(LayerIdV1.L2_MARKET_OBSERVATION, LayerReachabilityV1.REACHED)
        )

        mark = float(candidate.mark_price)  # type: ignore[arg-type]
        l3 = apply_l3_initial_direction_v1(
            InitialDirectionInputV1(
                acceptance_result=l2.acceptance_result,
                bound_instrument_key=l1.state.instrument_key,
                current_mark=mark,
            )
        )
        trace.append(LayerTraceEntryV1(LayerIdV1.L3_INITIAL_DIRECTION, LayerReachabilityV1.REACHED))
        if l3.direction_result.direction not in (
            ElementaryDirectionV1.BULL,
            ElementaryDirectionV1.BEAR,
        ):
            continue

        l4 = apply_l4_initial_state_initialization_v1(
            InitialStateInitializationInputV1(
                selected=l1.state,
                direction=l3,
                initialization_mark=mark,
            )
        )
        if l4.fail_closed:
            trace.append(
                LayerTraceEntryV1(
                    LayerIdV1.L4_INITIAL_STATE_INITIALIZATION,
                    LayerReachabilityV1.FAIL_CLOSED,
                )
            )
            return NakedLayeredCoreOrchestratorResultV1(
                fail_closed=True,
                fail_reasons=l4.fail_reasons,
                layer_trace=tuple(trace),
                final_regime=None,
                final_nullline_price=None,
                final_running_r_t=None,
            )
        trace.append(
            LayerTraceEntryV1(
                LayerIdV1.L4_INITIAL_STATE_INITIALIZATION,
                LayerReachabilityV1.REACHED,
            )
        )
        regime_state = l4.regime_state

        epoch = int(l2.acceptance_result.state_after.market_observation_epoch.value)
        l5 = apply_l5_nullline_v1(
            NullLineInputV1(
                regime_state=l4.regime_state,
                initialization_mark=mark,
                market_observation_epoch=epoch,
            )
        )
        nullline = l5.nullline
        trace.append(LayerTraceEntryV1(LayerIdV1.L5_NULLLINE, LayerReachabilityV1.REACHED))
        break

    if nullline is None or regime_state is None:
        return NakedLayeredCoreOrchestratorResultV1(
            fail_closed=True,
            fail_reasons=("orchestrator_initialization_incomplete",),
            layer_trace=tuple(trace),
            final_regime=None,
            final_nullline_price=None,
            final_running_r_t=None,
        )

    steps = (first_mechanical_step, *follow_on_steps)
    regime = regime_state.regime
    running = initial_running_reference_state_v1(
        instrument_id=nullline.instrument_id,
        reference_price_r_t=nullline.nullline_price,
    )
    nullline_frozen = nullline.nullline_price

    for step in steps:
        l6 = apply_l6_dynamic_scope_generator_v1(
            scope_generator,
            DynamicScopeGeneratorInputV1(
                nullline=nullline,
                proposed_d_t=step.proposed_d_t,
            ),
        )
        trace.append(
            LayerTraceEntryV1(
                LayerIdV1.L6_DYNAMIC_SCOPE_GENERATOR,
                LayerReachabilityV1.FAIL_CLOSED if l6.fail_closed else LayerReachabilityV1.REACHED,
            )
        )
        if l6.fail_closed:
            for lid in (
                LayerIdV1.L7_SCOPE_STATE,
                LayerIdV1.L8_RUNNING_REFERENCE,
                LayerIdV1.L9_COUNTER_MOVE,
                LayerIdV1.L10_BULL_BEAR_STATE_SWITCH,
            ):
                trace.append(LayerTraceEntryV1(lid, LayerReachabilityV1.NOT_REACHED))
            return NakedLayeredCoreOrchestratorResultV1(
                fail_closed=True,
                fail_reasons=l6.fail_reasons,
                layer_trace=tuple(trace),
                final_regime=regime,
                final_nullline_price=nullline_frozen,
                final_running_r_t=running.reference_price_r_t,
            )

        l7 = apply_l7_scope_state_materialization_v1(
            ScopeStateMaterializationInputV1(nullline=nullline, generator_output=l6)
        )
        trace.append(
            LayerTraceEntryV1(
                LayerIdV1.L7_SCOPE_STATE,
                LayerReachabilityV1.FAIL_CLOSED if l7.fail_closed else LayerReachabilityV1.REACHED,
            )
        )
        if l7.fail_closed or l7.scope is None:
            return NakedLayeredCoreOrchestratorResultV1(
                fail_closed=True,
                fail_reasons=l7.fail_reasons,
                layer_trace=tuple(trace),
                final_regime=regime,
                final_nullline_price=nullline_frozen,
                final_running_r_t=running.reference_price_r_t,
            )

        scope = l7.scope
        l8 = apply_l8_running_reference_step_v1(
            RunningReferenceStepInputV1(
                regime=regime,
                mark_price_m_t=step.mark_price_m_t,
                previous=running,
            )
        )
        trace.append(LayerTraceEntryV1(LayerIdV1.L8_RUNNING_REFERENCE, LayerReachabilityV1.REACHED))

        l9 = apply_l9_counter_move_v1(
            CounterMoveInputV1(
                regime=regime,
                mark_price_m_t=step.mark_price_m_t,
                running_reference=l8.state,
            )
        )
        trace.append(LayerTraceEntryV1(LayerIdV1.L9_COUNTER_MOVE, LayerReachabilityV1.REACHED))

        l10 = apply_l10_bull_bear_switch_v1(
            BullBearSwitchInputV1(
                regime_pre=regime,
                cm_t=l9.counter_move.cm_t,
                d_t=scope.d_t,
                mark_price_m_t=step.mark_price_m_t,
                running_reference_post=l8.state,
            )
        )
        trace.append(
            LayerTraceEntryV1(
                LayerIdV1.L10_BULL_BEAR_STATE_SWITCH,
                LayerReachabilityV1.REACHED,
            )
        )

        regime = l10.regime_post
        running = initial_running_reference_state_v1(
            instrument_id=running.instrument_id,
            reference_price_r_t=l10.persisted_r_t,
        )

    return NakedLayeredCoreOrchestratorResultV1(
        fail_closed=False,
        fail_reasons=(),
        layer_trace=tuple(trace),
        final_regime=regime,
        final_nullline_price=nullline_frozen,
        final_running_r_t=running.reference_price_r_t,
    )


__all__ = [
    "MechanicalStepSpecV1",
    "NakedLayeredCoreOrchestratorResultV1",
    "NakedLayeredCoreOrchestratorStateV1",
    "LayerTraceEntryV1",
    "orchestrate_naked_layered_core_v1",
]
