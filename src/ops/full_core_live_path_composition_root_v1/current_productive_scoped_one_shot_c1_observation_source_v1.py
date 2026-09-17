"""CURRENT_PRODUCTIVE scoped one-shot C1 observation source.

MS02 PAYLOAD-TO-OBSERVATION MAPPING.
Maps an injected candles payload through extract_finalized_candle_closes_v1
to at most one CurrentProductiveC1ObservationV1.

MS03 CURSOR-FLOOR AND ABSENCE FAIL-CLOSED.
Resolves the EG-owned persisted last-accepted venue_event_time floor and
evaluates a mapped observation against that floor. Reuses EG load and
compare helpers. Does not synthesize a floor, GET, poll, daemonize,
sleep-loop, dispatch EG, or execute a runtime cycle.

MS04A LIVE GET CONTRACT BINDING.
Binds the existing FullCoreProductiveReadOnlyGetTransportV1 capability
identity and the existing CURRENT_PRODUCTIVE public 1m candles GET query
shape onto this EH seam. Does not construct the transport, call get,
poll, dispatch EG, or execute a runtime cycle.

S1 POST-MS04D T1/T2 AUTHORITY SEPARATION.
Pins T1=PRESENT_HISTORICAL_MS04B_EMITTED_OBSERVATION_TO_EG as
OWNER_GO_ABSENT and not consumed. Restates existing T2 runtime Owner-GO
as DEFINED_NOT_CONSUMED and not consumed. Does not create, define, or
consume a T1 Owner-GO. Does not consume T2. Historical MS04B pack remains
HISTORICAL_EVIDENCE_ONLY and is not standing enablement.

S2+S3 COLLAPSE CANONICAL SINGLE RUNTIME PATH OFFLINE BIND.
Pins the already-carried CURRENT_PRODUCTIVE next-cycle call chain
EH scoped one-shot C1 -> EG exactly-one orchestration -> V5 N=1 host.
Census A/B/C are not equal architecture offers. Historical MS04B as EG
input remains forbidden. Direct V5 as CURRENT_PRODUCTIVE entrypoint
remains forbidden. T1 remains OWNER_GO_ABSENT. T2 remains
DEFINED_NOT_CONSUMED. This bind does not GET, dispatch EG, invoke V5,
or start a runtime cycle.

EG remains owner of dedup, cursor accept/reject, trigger, and exactly-one
cycle dispatch. V5 remains the N=1 cycle host. This module does not call
the EG trigger or V5 host.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_next_c1_trigger_and_exactly_one_cycle_orchestration_v1 import (
    REQUIRED_BAR,
    CurrentProductiveC1ObservationV1,
    CurrentProductiveGovernedNextC1OrchestrationError,
    OWNER_GO as EG_OWNER_GO,
    REASON_CURSOR_INVALID as EG_REASON_CURSOR_INVALID,
    REASON_CURSOR_MISSING as EG_REASON_CURSOR_MISSING,
    cursor_last_accepted_c1_venue_event_time_v1,
    evaluate_current_productive_c1_reject_reason_v1,
    load_current_productive_c1_cursor_or_reason_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    ENDPOINT_MARKET_CANDLES,
    extract_finalized_candle_closes_v1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    METHOD_GET,
    TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET,
)
from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
    AUTHORIZED_HOST,
    CONNECT_TIMEOUT_SECONDS,
    DEFAULT_TIMEOUT_SECONDS,
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
MS04A_CONTRACT_BOUND = True
MS04A_SLICE = "MS04A_EH_LIVE_GET_CONTRACT_AND_OWNER_BINDING_V1"
MS05_AUTHORIZED = False
MS05_STARTED = False
S1_THIS_SLICE = "11.2.1.EH.S1_POST_MS04D_T1_T2_AUTHORITY_SEPARATION"
S1_OWNER_GO = "OWNER_GO_POST_MS04D_T1_T2_AUTHORITY_SEPARATION_PERSIST_V1"
S1_OWNER_GO_SCOPE = "T1_T2_AUTHORITY_SEPARATION_PERSIST_ONLY"
S1_OWNER_GO_STATUS = "CONSUMED"
T1_TRANSITION = "PRESENT_HISTORICAL_MS04B_EMITTED_OBSERVATION_TO_EG"
T1_OWNER_GO_STATUS = "OWNER_GO_ABSENT"
T1_CONSUMED = False
T2_OWNER_GO = (
    "OWNER_GO_CONDITION_GATED_CURRENT_PRODUCTIVE_RUNTIME_CYCLE_AFTER_C1_BOUNDARY_1789527780_V1"
)
T2_OWNER_GO_STATUS = "DEFINED_NOT_CONSUMED"
T2_CONSUMED = False
HISTORICAL_PACK_CLASS = "HISTORICAL_EVIDENCE_ONLY"
HISTORICAL_EVIDENCE_IS_NOT_STANDING_ENABLEMENT = True
CANONICAL_HISTORICAL_EVIDENCE_PACK = (
    "evidence/ops/full_core_current_productive_scoped_one_shot_c1_observation_source_v1/"
    "20260917T130821Z"
)
EG_TRIGGER_EXECUTED = False
RUNTIME_CYCLE_EXECUTED = False
GET_COUNT_THIS_SLICE = 0
EG_DISPATCH_COUNT = 0
V5_INVOKE_COUNT = 0
RUNTIME_CYCLE_COUNT = 0
S2_S3_THIS_SLICE = "11.2.1.EH.S2_S3_CANONICAL_SINGLE_RUNTIME_PATH_OFFLINE_BIND"
S2_S3_OWNER_GO = "OWNER_GO_POST_MS04D_S2_S3_CANONICAL_SINGLE_RUNTIME_PATH_OFFLINE_BIND_V1"
S2_S3_OWNER_GO_SCOPE = "OFFLINE_PATH_SELECTION_AND_CALL_CONTRACT_BIND_ONLY"
S2_S3_OWNER_GO_STATUS = "CONSUMED"
S2_S3_CALL_CONTRACT_BOUND = True
SELECTED_RUNTIME_PATH = "EH_SCOPED_ONE_SHOT_C1_TO_EG_EXACTLY_ONE_TO_V5_N1_HOST"
PATH_CARDINALITY = 1
OBSERVATION_SOURCE = "EH_SCOPED_ONE_SHOT_C1"
ORCHESTRATOR = "EG_NEXT_C1_TRIGGER_AND_EXACTLY_ONE"
CYCLE_HOST = "V5_N1"
EG_CALL_TOKEN = EG_OWNER_GO
EG_CALL_TOKEN_CLASS = "PERSIST_CONSUMED_NOT_TRIGGER_LICENSE"
T2_CLASS = "DEFINED_NOT_CONSUMED_RUNTIME_AUTHORITY_NOT_CONSUMED"
T1_CLASS = "OWNER_GO_ABSENT_NOT_CALL_AUTHORITY"
DIRECT_V5_AS_CURRENT_PRODUCTIVE_ENTRYPOINT = "FORBIDDEN"
HISTORICAL_MS04B_AS_EG_INPUT = "FORBIDDEN"
T1_ONLY_WITHOUT_T2 = "FORBIDDEN"
CENSUS_A_REJECT_BOTH = "UNSELECTED_NOT_A_RUNTIME_PATH"
CENSUS_B_HISTORICAL_OBSERVATION_TO_EG = "FORBIDDEN"
CENSUS_C_ARCHITECTURE = "CARRIED_AS_EH_TO_EG_TO_V5_HOST_OFFLINE_BIND_ONLY"
FRESH_C1_REQUIREMENT = "REQUIRED_FOR_EVENTUAL_RUNTIME_INPUT_THIS_SLICE_GET_UNAUTHORIZED"
FRESH_GET_AUTHORIZED = False
NETWORK_EXECUTION_AUTHORIZED = False
S4_STARTED = False
GET_TRANSPORT_CAPABILITY = "FullCoreProductiveReadOnlyGetTransportV1"
GET_TRANSPORT_CLASS = TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET
GET_HOST = AUTHORIZED_HOST
GET_METHOD = METHOD_GET
GET_PATH = ENDPOINT_MARKET_CANDLES
GET_BAR = REQUIRED_BAR
GET_LIMIT = "100"
GET_AUTH_REQUIRED = False
GET_MAX_REQUEST_COUNT = 1
GET_TIMEOUT_SECONDS = DEFAULT_TIMEOUT_SECONDS
GET_CONNECT_TIMEOUT_SECONDS = CONNECT_TIMEOUT_SECONDS
INST_ID_BINDING_SOURCE = "CURRENT_PRODUCTIVE_CURSOR_VENUE_NATIVE_ID"
LIMIT_BINDING_SOURCE = "EXISTING_CURRENT_PRODUCTIVE_PUBLIC_1M_CANDLES_GET_QUERY"
MS02_HANDOFF = "map_injected_candles_payload_to_current_productive_c1_observation_v1"
MS03_HANDOFF = "evaluate_current_productive_c1_observation_against_cursor_floor_v1"
AUTONOMY_CAN_CHANGE_TRADING_LOGIC = False
AUTONOMY_CAN_RESELECT_DOWNSTREAM = False
AUTONOMY_CAN_MINT_PERMIT = False
AUTONOMY_CAN_POST = False
DISPOSITION_EMITTED = "EMITTED"
DISPOSITION_FAIL_CLOSED = "FAIL_CLOSED"
DISPOSITION_PRESENT = "PRESENT"
PRESENCE_PRESENT = "PRESENT"
PRESENCE_ABSENT = "ABSENT"
REASON_OWNER_GO_MISMATCH = "OWNER_GO_MISMATCH"
REASON_UNFINALIZED_OR_ABSENT = "UNFINALIZED_OR_ABSENT"
REASON_CURSOR_MISSING = EG_REASON_CURSOR_MISSING
REASON_CURSOR_INVALID = EG_REASON_CURSOR_INVALID
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


@dataclass(frozen=True)
class CurrentProductiveScopedOneShotC1CursorFloorResultV1:
    disposition: str
    presence: str
    floor_venue_event_time: float | None
    get_count: int
    reason_code: str


def _floor_fail(
    reason_code: str,
    *,
    presence: str,
    floor_venue_event_time: float | None = None,
) -> CurrentProductiveScopedOneShotC1CursorFloorResultV1:
    return CurrentProductiveScopedOneShotC1CursorFloorResultV1(
        disposition=DISPOSITION_FAIL_CLOSED,
        presence=presence,
        floor_venue_event_time=floor_venue_event_time,
        get_count=0,
        reason_code=reason_code,
    )


def _resolve_cursor_floor_with_payload(
    *,
    owner_go: str,
    cursor_store_root: Path,
) -> tuple[CurrentProductiveScopedOneShotC1CursorFloorResultV1, Mapping[str, Any] | None]:
    if owner_go != OWNER_GO:
        return _floor_fail(REASON_OWNER_GO_MISMATCH, presence=""), None
    cursor, cursor_reason = load_current_productive_c1_cursor_or_reason_v1(Path(cursor_store_root))
    if cursor is None:
        presence = PRESENCE_ABSENT if cursor_reason == REASON_CURSOR_MISSING else ""
        return _floor_fail(cursor_reason, presence=presence), None
    try:
        floor = cursor_last_accepted_c1_venue_event_time_v1(cursor)
    except CurrentProductiveGovernedNextC1OrchestrationError as exc:
        return _floor_fail(exc.reason_code, presence=""), None
    return (
        CurrentProductiveScopedOneShotC1CursorFloorResultV1(
            disposition=DISPOSITION_PRESENT,
            presence=PRESENCE_PRESENT,
            floor_venue_event_time=floor,
            get_count=0,
            reason_code="",
        ),
        cursor,
    )


def resolve_current_productive_c1_cursor_floor_v1(
    *,
    owner_go: str,
    cursor_store_root: Path,
) -> CurrentProductiveScopedOneShotC1CursorFloorResultV1:
    result, _cursor = _resolve_cursor_floor_with_payload(
        owner_go=owner_go,
        cursor_store_root=cursor_store_root,
    )
    return result


def evaluate_current_productive_c1_observation_against_cursor_floor_v1(
    *,
    owner_go: str,
    cursor_store_root: Path,
    observation: CurrentProductiveC1ObservationV1,
) -> CurrentProductiveScopedOneShotC1CursorFloorResultV1:
    floor_result, cursor = _resolve_cursor_floor_with_payload(
        owner_go=owner_go,
        cursor_store_root=cursor_store_root,
    )
    if floor_result.disposition != DISPOSITION_PRESENT or cursor is None:
        return floor_result
    reject = evaluate_current_productive_c1_reject_reason_v1(
        observation=observation,
        cursor=cursor,
    )
    if reject:
        return _floor_fail(
            reject,
            presence=PRESENCE_PRESENT,
            floor_venue_event_time=floor_result.floor_venue_event_time,
        )
    return CurrentProductiveScopedOneShotC1CursorFloorResultV1(
        disposition=DISPOSITION_EMITTED,
        presence=PRESENCE_PRESENT,
        floor_venue_event_time=floor_result.floor_venue_event_time,
        get_count=0,
        reason_code="",
    )


@dataclass(frozen=True)
class CurrentProductiveScopedOneShotC1GetRequestContractV1:
    disposition: str
    host: str
    method: str
    path: str
    inst_id: str
    bar: str
    limit: str
    auth_required: bool
    max_request_count: int
    timeout_seconds: float
    connect_timeout_seconds: float
    endpoint: str
    transport_capability: str
    transport_class: str
    inst_id_binding_source: str
    limit_binding_source: str
    get_count: int
    reason_code: str


def _request_fail(
    reason_code: str,
) -> CurrentProductiveScopedOneShotC1GetRequestContractV1:
    return CurrentProductiveScopedOneShotC1GetRequestContractV1(
        disposition=DISPOSITION_FAIL_CLOSED,
        host="",
        method="",
        path="",
        inst_id="",
        bar="",
        limit="",
        auth_required=GET_AUTH_REQUIRED,
        max_request_count=GET_MAX_REQUEST_COUNT,
        timeout_seconds=GET_TIMEOUT_SECONDS,
        connect_timeout_seconds=GET_CONNECT_TIMEOUT_SECONDS,
        endpoint="",
        transport_capability=GET_TRANSPORT_CAPABILITY,
        transport_class=GET_TRANSPORT_CLASS,
        inst_id_binding_source=INST_ID_BINDING_SOURCE,
        limit_binding_source=LIMIT_BINDING_SOURCE,
        get_count=0,
        reason_code=reason_code,
    )


def bind_current_productive_scoped_one_shot_c1_public_candles_get_request_contract_v1(
    *,
    owner_go: str,
    cursor_store_root: Path,
) -> CurrentProductiveScopedOneShotC1GetRequestContractV1:
    floor_result, cursor = _resolve_cursor_floor_with_payload(
        owner_go=owner_go,
        cursor_store_root=cursor_store_root,
    )
    if floor_result.disposition != DISPOSITION_PRESENT or cursor is None:
        return _request_fail(floor_result.reason_code)
    inst_id = str(cursor.get("venue_native_id") or "").strip()
    if not inst_id:
        return _request_fail(REASON_CURSOR_INVALID)
    endpoint = f"{GET_PATH}?instId={inst_id}&bar={GET_BAR}&limit={GET_LIMIT}"
    return CurrentProductiveScopedOneShotC1GetRequestContractV1(
        disposition=DISPOSITION_PRESENT,
        host=GET_HOST,
        method=GET_METHOD,
        path=GET_PATH,
        inst_id=inst_id,
        bar=GET_BAR,
        limit=GET_LIMIT,
        auth_required=GET_AUTH_REQUIRED,
        max_request_count=GET_MAX_REQUEST_COUNT,
        timeout_seconds=GET_TIMEOUT_SECONDS,
        connect_timeout_seconds=GET_CONNECT_TIMEOUT_SECONDS,
        endpoint=endpoint,
        transport_capability=GET_TRANSPORT_CAPABILITY,
        transport_class=GET_TRANSPORT_CLASS,
        inst_id_binding_source=INST_ID_BINDING_SOURCE,
        limit_binding_source=LIMIT_BINDING_SOURCE,
        get_count=0,
        reason_code="",
    )


@dataclass(frozen=True)
class CurrentProductiveCanonicalSingleRuntimePathCallContractV1:
    disposition: str
    selected_runtime_path: str
    path_cardinality: int
    observation_source: str
    orchestrator: str
    cycle_host: str
    eg_call_token: str
    eg_call_token_class: str
    t2_owner_go: str
    t2_owner_go_status: str
    t1_owner_go_status: str
    direct_v5_as_current_productive_entrypoint: str
    historical_ms04b_as_eg_input: str
    t1_only_without_t2: str
    network_execution_authorized: bool
    fresh_get_authorized: bool
    get_count: int
    eg_dispatch_count: int
    v5_invoke_count: int
    runtime_cycle_count: int
    reason_code: str


def _path_fail(
    reason_code: str,
) -> CurrentProductiveCanonicalSingleRuntimePathCallContractV1:
    return CurrentProductiveCanonicalSingleRuntimePathCallContractV1(
        disposition=DISPOSITION_FAIL_CLOSED,
        selected_runtime_path="",
        path_cardinality=0,
        observation_source="",
        orchestrator="",
        cycle_host="",
        eg_call_token="",
        eg_call_token_class="",
        t2_owner_go="",
        t2_owner_go_status="",
        t1_owner_go_status="",
        direct_v5_as_current_productive_entrypoint=DIRECT_V5_AS_CURRENT_PRODUCTIVE_ENTRYPOINT,
        historical_ms04b_as_eg_input=HISTORICAL_MS04B_AS_EG_INPUT,
        t1_only_without_t2=T1_ONLY_WITHOUT_T2,
        network_execution_authorized=False,
        fresh_get_authorized=False,
        get_count=0,
        eg_dispatch_count=0,
        v5_invoke_count=0,
        runtime_cycle_count=0,
        reason_code=reason_code,
    )


def bind_current_productive_canonical_single_runtime_path_call_contract_v1(
    *,
    owner_go: str,
) -> CurrentProductiveCanonicalSingleRuntimePathCallContractV1:
    if owner_go != S2_S3_OWNER_GO:
        return _path_fail(REASON_OWNER_GO_MISMATCH)
    if PATH_CARDINALITY != 1:
        return _path_fail("PATH_CARDINALITY_DRIFT")
    if T1_OWNER_GO_STATUS != "OWNER_GO_ABSENT" or T1_CONSUMED is True:
        return _path_fail("T1_STATUS_DRIFT")
    if T2_OWNER_GO_STATUS != "DEFINED_NOT_CONSUMED" or T2_CONSUMED is True:
        return _path_fail("T2_STATUS_DRIFT")
    if FRESH_GET_AUTHORIZED is True or NETWORK_EXECUTION_AUTHORIZED is True:
        return _path_fail("NETWORK_PIN_DRIFT")
    if (
        GET_COUNT_THIS_SLICE != 0
        or EG_DISPATCH_COUNT != 0
        or V5_INVOKE_COUNT != 0
        or RUNTIME_CYCLE_COUNT != 0
    ):
        return _path_fail("INVOKE_COUNT_DRIFT")
    return CurrentProductiveCanonicalSingleRuntimePathCallContractV1(
        disposition=DISPOSITION_PRESENT,
        selected_runtime_path=SELECTED_RUNTIME_PATH,
        path_cardinality=PATH_CARDINALITY,
        observation_source=OBSERVATION_SOURCE,
        orchestrator=ORCHESTRATOR,
        cycle_host=CYCLE_HOST,
        eg_call_token=EG_CALL_TOKEN,
        eg_call_token_class=EG_CALL_TOKEN_CLASS,
        t2_owner_go=T2_OWNER_GO,
        t2_owner_go_status=T2_OWNER_GO_STATUS,
        t1_owner_go_status=T1_OWNER_GO_STATUS,
        direct_v5_as_current_productive_entrypoint=DIRECT_V5_AS_CURRENT_PRODUCTIVE_ENTRYPOINT,
        historical_ms04b_as_eg_input=HISTORICAL_MS04B_AS_EG_INPUT,
        t1_only_without_t2=T1_ONLY_WITHOUT_T2,
        network_execution_authorized=NETWORK_EXECUTION_AUTHORIZED,
        fresh_get_authorized=FRESH_GET_AUTHORIZED,
        get_count=GET_COUNT_THIS_SLICE,
        eg_dispatch_count=EG_DISPATCH_COUNT,
        v5_invoke_count=V5_INVOKE_COUNT,
        runtime_cycle_count=RUNTIME_CYCLE_COUNT,
        reason_code="",
    )
