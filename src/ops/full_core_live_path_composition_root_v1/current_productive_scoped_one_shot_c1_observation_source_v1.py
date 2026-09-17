"""CURRENT_PRODUCTIVE scoped one-shot C1 observation source.

MS02 PAYLOAD-TO-OBSERVATION MAPPING ONLY.
Maps an injected candles payload through extract_finalized_candle_closes_v1
to at most one CurrentProductiveC1ObservationV1. Does not compare cursor
floors, GET, poll, daemonize, sleep-loop, dispatch EG, or execute a
runtime cycle.

EG remains owner of dedup, cursor accept/reject, trigger, and exactly-one
cycle dispatch. V5 remains the N=1 cycle host. This module does not call
those surfaces.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_next_c1_trigger_and_exactly_one_cycle_orchestration_v1 import (
    REQUIRED_BAR,
    CurrentProductiveC1ObservationV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    extract_finalized_candle_closes_v1,
)

OWNER_GO = "OWNER_GO_CURRENT_PRODUCTIVE_SCOPED_ONE_SHOT_C1_OBSERVATION_SOURCE_V1"
OWNER_GO_SCOPE = "MS01_AUTHORITY_PERSIST_AND_OWNER_PINS_ONLY"
THIS_SLICE = "11.2.1.EH.FULL_CORE_CURRENT_PRODUCTIVE_SCOPED_ONE_SHOT_C1_OBSERVATION_SOURCE"
JOIN_SEAM_ID = "CURRENT_PRODUCTIVE_SCOPED_ONE_SHOT_C1_OBSERVATION_SOURCE_SEAM_V1"
OWNER = (
    "ops.full_core_live_path_composition_root_v1."
    "current_productive_scoped_one_shot_c1_observation_source_v1"
)
PRODUCER_AUTHORITY = "ONE_SHOT_PUBLIC_1M_C1_OBSERVATION_ACQUISITION_ONLY"
EG_AUTHORITY_BOUNDARY_UNCHANGED = "NEXT_C1_TRIGGER_AND_SINGLE_CYCLE_ORCHESTRATION_ONLY"
MS01_IMPLEMENTATION_STATUS = "AUTHORITY_SCAFFOLD_ONLY"
BOUNDED_POLL_AUTHORIZED = False
DAEMON_AUTHORIZED = False
CADENCE_OWNER_AUTHORIZED = False
CONTINUOUS_RUNTIME_AUTHORIZED = False
RUNTIME_CYCLE_AUTHORIZED = False
PERFORM_GET_DEFAULT = False
LIVE_GET_EXECUTED = False
MS02_AUTHORIZED = False
MS03_AUTHORIZED = False
MS04_AUTHORIZED = False
MS05_AUTHORIZED = False
AUTONOMY_CAN_CHANGE_TRADING_LOGIC = False
AUTONOMY_CAN_RESELECT_DOWNSTREAM = False
AUTONOMY_CAN_MINT_PERMIT = False
AUTONOMY_CAN_POST = False
DISPOSITION_EMITTED = "EMITTED"
DISPOSITION_FAIL_CLOSED = "FAIL_CLOSED"
REASON_OWNER_GO_MISMATCH = "OWNER_GO_MISMATCH"
REASON_UNFINALIZED_OR_ABSENT = "UNFINALIZED_OR_ABSENT"
CONFIRM_FINALIZED = "1"


@dataclass(frozen=True)
class CurrentProductiveScopedOneShotC1ObservationMapResultV1:
    disposition: str
    observation: CurrentProductiveC1ObservationV1 | None
    get_count: int
    reason_code: str


def _fail_closed(reason_code: str) -> CurrentProductiveScopedOneShotC1ObservationMapResultV1:
    return CurrentProductiveScopedOneShotC1ObservationMapResultV1(
        disposition=DISPOSITION_FAIL_CLOSED,
        observation=None,
        get_count=0,
        reason_code=reason_code,
    )


def map_injected_candles_payload_to_current_productive_c1_observation_v1(
    *,
    owner_go: str,
    candles_payload: object,
    native_id: str,
) -> CurrentProductiveScopedOneShotC1ObservationMapResultV1:
    if owner_go != OWNER_GO:
        return _fail_closed(REASON_OWNER_GO_MISMATCH)
    if not isinstance(candles_payload, Mapping):
        return _fail_closed(REASON_UNFINALIZED_OR_ABSENT)
    _closes, last_ts = extract_finalized_candle_closes_v1(candles_payload)
    if last_ts is None:
        return _fail_closed(REASON_UNFINALIZED_OR_ABSENT)
    payload: Mapping[str, Any] = candles_payload
    return CurrentProductiveScopedOneShotC1ObservationMapResultV1(
        disposition=DISPOSITION_EMITTED,
        observation=CurrentProductiveC1ObservationV1(
            venue_event_time=last_ts,
            confirm=CONFIRM_FINALIZED,
            native_id=native_id,
            bar=REQUIRED_BAR,
            payload=payload,
        ),
        get_count=0,
        reason_code="",
    )
