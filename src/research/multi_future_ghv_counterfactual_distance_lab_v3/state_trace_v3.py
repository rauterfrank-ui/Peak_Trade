from __future__ import annotations

from typing import Any, Mapping, Optional

from trading.market_state.distinct_market_observation_acceptor_v1 import (
    ObservationAcceptanceResultV1,
    ObservationClassification,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    IntegratedOfflineReplayResultV1,
)

from research.multi_future_ghv_counterfactual_distance_lab_v3.state_carrier_v3 import (
    FlightLaneStateRootV3,
)


def _epoch_from_carrier(state: FlightLaneStateRootV3) -> object:
    cp = state.directional_confirmation_progress
    if cp is None:
        return "NOT_SET"
    try:
        long_p = cp.long_side.confirmation_progress if cp.long_side else None
        short_p = cp.short_side.confirmation_progress if cp.short_side else None
        return {
            "long_epoch": getattr(
                getattr(long_p, "latest_accepted_market_observation_epoch", None), "value", None
            ),
            "short_epoch": getattr(
                getattr(short_p, "latest_accepted_market_observation_epoch", None), "value", None
            ),
        }
    except Exception:
        return "UNREADABLE"


def build_confirmation_state_trace_row_v3(
    *,
    flight_id: str,
    cycle_id: int,
    model_id: str,
    lane_id: str,
    state_before: FlightLaneStateRootV3,
    state_after: FlightLaneStateRootV3,
    c1_result: Optional[ObservationAcceptanceResultV1],
    result: IntegratedOfflineReplayResultV1,
    state_source_cycle_id: int,
) -> Mapping[str, Any]:
    c1_accepted = None
    c1_obs_id = None
    if c1_result is not None:
        c1_accepted = c1_result.classification is ObservationClassification.DISTINCT
        if c1_result.observation_identity is not None:
            ident = c1_result.observation_identity
            c1_obs_id = f"{ident.venue_event_time}:{ident.mark_price}"
    continuity_fail = None
    continuity_valid = True
    if cycle_id > 0 and state_before.c1_acceptance_state is None:
        continuity_valid = False
        continuity_fail = "C1_STATE_MISSING_AT_CYCLE_START"
    return {
        "FLIGHT_ID": flight_id,
        "CYCLE_ID": cycle_id,
        "MODEL_ID": model_id,
        "LANE_ID": lane_id,
        "C1_OBSERVATION_ID": c1_obs_id,
        "C1_ACCEPTED": c1_accepted,
        "C1_STATE_BEFORE": state_before.c1_acceptance_state is not None,
        "C1_STATE_AFTER": state_after.c1_acceptance_state is not None,
        "CONFIRMATION_CARRIER_BEFORE": state_before.directional_confirmation_progress is not None,
        "CONFIRMATION_CARRIER_AFTER": state_after.directional_confirmation_progress is not None,
        "CONFIRMATION_EPOCH_BEFORE": _epoch_from_carrier(state_before),
        "CONFIRMATION_EPOCH_AFTER": _epoch_from_carrier(state_after),
        "CONFIRMATION_CONTIGUOUS": c1_accepted if c1_accepted is not None else "UNKNOWN",
        "CONFIRMATION_RESET": False,
        "CONFIRMATION_RESET_REASON": None,
        "SCOPE_STATE_BEFORE": state_before.scope_confirmation_state,
        "SCOPE_STATE_AFTER": state_after.scope_confirmation_state,
        "SIDE_STATE_BEFORE": state_before.side_state.value,
        "SIDE_STATE_AFTER": state_after.side_state.value,
        "DECISION_EPOCH_BEFORE": state_before.last_evaluated_trading_epoch,
        "DECISION_EPOCH_AFTER": state_after.last_evaluated_trading_epoch,
        "STATE_SOURCE_CYCLE_ID": state_source_cycle_id,
        "STATE_CONTINUITY_VALID": continuity_valid,
        "STATE_CONTINUITY_FAIL_REASON": continuity_fail,
        "REPLAY_PASS": result.replay_pass,
        "DECISION_OUTCOME": result.evidence.decision_outcome,
    }
