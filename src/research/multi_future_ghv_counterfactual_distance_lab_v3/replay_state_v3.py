from __future__ import annotations

from dataclasses import replace
from typing import Optional, Tuple

from trading.market_state.distinct_market_observation_acceptor_v1 import (
    ObservationAcceptanceResultV1,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    IntegratedOfflineReplayInputV1,
    IntegratedOfflineReplayResultV1,
)

from research.multi_future_ghv_counterfactual_distance_lab_v3.c1_cycle_transport_v3 import (
    advance_c1_for_cycle_v3,
    instrument_observation_key_v3,
)
from research.multi_future_ghv_counterfactual_distance_lab_v3.state_carrier_v3 import (
    FlightLaneStateRootV3,
)


def init_lane_state_v3(
    state: FlightLaneStateRootV3,
    *,
    instrument_id: str,
    confirmation_session_id: str,
    confirmation_venue: str = "okx_eea",
) -> FlightLaneStateRootV3:
    key = instrument_observation_key_v3(instrument_id)
    return replace(
        state,
        confirmation_session_id=confirmation_session_id,
        confirmation_venue=confirmation_venue,
        confirmation_instrument=key,
    )


def apply_lane_state_to_replay_input_v3(
    inp: IntegratedOfflineReplayInputV1,
    state: FlightLaneStateRootV3,
    *,
    instrument_id: str,
    cycle_id: int,
    mark_price: float,
    use_c1_transport: bool = True,
) -> Tuple[IntegratedOfflineReplayInputV1, FlightLaneStateRootV3, Optional[ObservationAcceptanceResultV1]]:
    """Attach persisted CURRENT contract fields; optionally advance C1 for this cycle."""
    c1_result: Optional[ObservationAcceptanceResultV1] = None
    st = state
    if use_c1_transport:
        c1_result, st = advance_c1_for_cycle_v3(
            st,
            instrument_id=instrument_id,
            mark_price=mark_price,
            cycle_id=cycle_id,
        )
    out = inp
    if st.existing_scope is not None:
        out = replace(out, existing_scope=st.existing_scope)
    if st.runtime_scope_state is not None:
        out = replace(
            out,
            runtime_scope_state=st.runtime_scope_state,
            runtime_scope_bound_instrument_id=instrument_id,
        )
    if st.directional_confirmation_progress is not None:
        out = replace(out, directional_confirmation_progress=st.directional_confirmation_progress)
    if st.scope_confirmation_state is not None:
        out = replace(out, scope_confirmation_state=st.scope_confirmation_state)
    if st.scope_cooldown_state is not None:
        out = replace(out, scope_cooldown_state=st.scope_cooldown_state)
    out = replace(
        out,
        side_state=st.side_state,
        previous_composition_direction_state=st.previous_composition_direction,
        last_evaluated_trading_epoch=st.last_evaluated_trading_epoch,
    )
    if c1_result is not None:
        out = replace(out, observation_acceptance_result=c1_result)
    if st.confirmation_session_id:
        out = replace(
            out,
            confirmation_progress_session_id=st.confirmation_session_id,
            confirmation_progress_venue=st.confirmation_venue,
            confirmation_progress_instrument=st.confirmation_instrument,
        )
    return out, st, c1_result


def update_lane_state_from_result_v3(
    state: FlightLaneStateRootV3,
    result: IntegratedOfflineReplayResultV1,
) -> FlightLaneStateRootV3:
    im = result.intermediate
    if im is None:
        return state
    st = state
    st = replace(st, existing_scope=im.current_scope, runtime_scope_state=im.runtime_scope_state_after)
    if im.directional_confirmation_progress_after is not None:
        st = replace(st, directional_confirmation_progress=im.directional_confirmation_progress_after)
    if im.scope_event is not None:
        st = replace(st, scope_confirmation_state=im.scope_event.next_confirmation_state)
    try:
        from trading.master_v2.double_play_state import SideState

        st = replace(st, side_state=SideState(im.state_switch.next_side_state))
    except Exception:
        pass
    epoch = im.composition_result.trading_epoch
    st = replace(st, last_evaluated_trading_epoch=epoch)
    return st
