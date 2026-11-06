"""One canonical normalized public-MD event path (reuse existing SSOT types)."""

from __future__ import annotations

from typing import Any, Mapping, Optional

from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.constants_v1 import (
    CANONICAL_NORMALIZED_EVENT_PATH,
    CAPABILITY_ID,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.normalized_market_data_v1 import (
    NormalizedPublicMarketDataV1,
)
from trading.market_state.distinct_market_observation_acceptor_v1 import (
    DistinctMarketObservationAcceptorV1,
    ObservationAcceptanceResultV1,
    ObservationAcceptanceStateV1,
    commit_observation_acceptance_v1,
)
from trading.market_state.observation_identity_v1 import (
    ObservationIdentityV1,
    observation_candidate_from_normalized_public_market_data_v1,
    observation_identity_from_normalized_public_market_data_v1,
)


def canonical_normalized_event_path_descriptor_v1() -> dict[str, Any]:
    return {
        "capability_id": CAPABILITY_ID,
        "path": CANONICAL_NORMALIZED_EVENT_PATH,
        "normalized_event_type": "NormalizedPublicMarketDataV1",
        "identity_type": "ObservationIdentityV1",
        "acceptor_type": "DistinctMarketObservationAcceptorV1",
        "parallel_normalized_event_ssot_allowed": False,
        "modules": {
            "normalized": (
                "src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1"
                ".normalized_market_data_v1"
            ),
            "identity": "trading.market_state.observation_identity_v1",
            "acceptor": "trading.market_state.distinct_market_observation_acceptor_v1",
        },
    }


def map_normalized_to_observation_identity_v1(
    data: NormalizedPublicMarketDataV1,
) -> ObservationIdentityV1:
    return observation_identity_from_normalized_public_market_data_v1(data)


def accept_normalized_public_market_event_v1(
    *,
    data: NormalizedPublicMarketDataV1,
    state: ObservationAcceptanceStateV1,
    poll_attempt: Optional[int] = None,
    runtime_cycle_index: Optional[int] = None,
    heartbeat_sequence: Optional[int] = None,
    transport_latency: Optional[float] = None,
    commit: bool = True,
) -> tuple[ObservationAcceptanceResultV1, ObservationAcceptanceStateV1]:
    """Single canonical acceptance path; duplicates do not advance state."""
    candidate = observation_candidate_from_normalized_public_market_data_v1(
        data,
        poll_attempt=poll_attempt,
        runtime_cycle_index=runtime_cycle_index,
        heartbeat_sequence=heartbeat_sequence,
        transport_latency=transport_latency,
    )
    result = DistinctMarketObservationAcceptorV1.evaluate(state, candidate)
    if commit:
        new_state = commit_observation_acceptance_v1(current_state=state, result=result)
    else:
        new_state = state
    return result, new_state


def assert_no_parallel_normalized_ssot_v1(extra_ssot_declared: bool = False) -> Mapping[str, Any]:
    if extra_ssot_declared:
        raise ValueError("PARALLEL_NORMALIZED_EVENT_SSOT_FORBIDDEN")
    return {
        "ok": True,
        "canonical_path": CANONICAL_NORMALIZED_EVENT_PATH,
        "parallel_ssot": False,
    }
