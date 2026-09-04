"""Offline SEND_TIME_POSITION_REOBSERVATION adjudication. No GET. No POST."""

from __future__ import annotations

from typing import Any

from src.ops.section_11_13_5_authenticated_productive_transport_v1.contract_v1 import (
    AUTHENTICATED_PRODUCTIVE_TRANSPORT_STATUS,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.bounded_activation_permit_v1 import (
    offline_contract_proof_bounded_activation_permit_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_execute_authority_v1 import (
    FLATTEN_EXECUTE_CONFIRM_TOKEN_CANONICAL,
    FLATTEN_EXECUTE_OWNER_GO_CANONICAL,
    FLATTEN_EXECUTE_PURPOSE_CANONICAL,
    FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS,
    evaluate_flatten_execute_authority_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_limit_price_contract_v1 import (
    FRESHNESS_THRESHOLD_MS,
    FlattenPriceInputV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_pre_send_gate_v1 import (
    FlattenPreSendGateInputV1,
    evaluate_flatten_pre_send_gate_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.no_additional_owner_decision_required_v1 import (
    PASS_OFFLINE_CONTRACT,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.position_observation_freshness_contract_v1 import (
    PRE_SEND_EVIDENCE_KIND,
    PositionObservationFreshnessEvidenceV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.prerequisite_08_fresh_position_observation_v1 import (
    adjudicate_prerequisite_08_window_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.send_time_position_reobservation_v1 import (
    NAMED_REMAINING_AFTER_SEND_TIME_POSITION_REOBSERVATION,
    PRODUCER_CLASS_AUTHENTICATED_PRIVATE_GET,
    PRODUCER_CLASS_CALLER_SUPPLIED,
    PRODUCER_CLASS_FAKE_OFFLINE,
    REASON_APT_NOT_PASS,
    REASON_AUTHENTICATED_GET_PRODUCER,
    REASON_CREDENTIAL_USE_CLAIM,
    REASON_EMPTY_DATA_NOT_ZERO,
    REASON_FAKE_COUNTED_AS_GET,
    REASON_FLATTEN_EXECUTE,
    REASON_GET,
    REASON_HISTORICAL_REUSE,
    REASON_IMPLEMENTATION_GO_AS_EXECUTE,
    REASON_INSTRUMENT_MISMATCH,
    REASON_LINEAGE_MISMATCH,
    REASON_LIVE_AUTHORIZED_SUBSTITUTE,
    REASON_MALFORMED_PAYLOAD,
    REASON_MISSING_APT,
    REASON_MISSING_REMAINING,
    REASON_NETWORK_SESSION,
    REASON_OBSERVATION_MISSING,
    REASON_POST,
    REASON_PRIVATE_GET_CLAIM,
    REASON_PROVEN_AT_SEND_CLAIM,
    REASON_REMAINING_MISMATCH,
    REASON_RUNTIME_OBSERVATION_CLAIM,
    REASON_RUNTIME_PERMIT,
    REASON_TARGET_NOT_OBSERVED,
    REASON_TRANSPORT_FAILURE,
    REASON_AUTHENTICATION_FAILURE,
    REASON_ZERO_POSITION,
    RecordingSendTimePositionReobservationProducerV1,
    evaluate_send_time_position_reobservation_v1,
)
from src.ops.section_11_13_5_send_time_position_reobservation_v1.constants_v1 import (
    APT_CLOSED,
    APT_TEXT_REWRITTEN_VALUE,
    CASE_VALUE,
    CONFLICT_COUNT,
    CREDENTIAL_USE_PROVEN_VALUE,
    EARLIEST_UNRESOLVED_DEPENDENCY,
    EXPECTED_ORIGIN_MAIN_SHA,
    FAIL_CLOSED_IF_MARKED_PROVEN_AT_SEND_FROM_OFFLINE_CODE_ALONE_VALUE,
    FAIL_CLOSED_IF_MARKED_RUNTIME_PROVEN_FROM_OFFLINE_CODE_ALONE_VALUE,
    LAST_CANONICALLY_CLOSED_STEP,
    NAMED_REMAINING_HIGHER_AUTHORITY,
    NETWORK_PROVEN_VALUE,
    NEXT_AUTHORITY_BOUNDARY,
    OWNER_GO,
    P08_CLOSED,
    P10_CLOSED,
    P11_CLOSED,
    P12_CLOSED,
    P13_CLOSED,
    P16_CLOSED,
    P16_TEXT_REWRITTEN_VALUE,
    P20_CLOSED,
    P20_TEXT_REWRITTEN_VALUE,
    P25_CLOSED,
    P25_TEXT_REWRITTEN_VALUE,
    POSITION_GET_AUTHORIZED_BY_THIS_OWNER_GO_VALUE,
    POSITION_GET_REQUIRED_THIS_PERSIST_VALUE,
    POST_PROVEN_VALUE,
    PREDECESSOR_SLICE,
    PRIOR_OWNER_GO,
    PRIVATE_AUTH_USED,
    PRIVATE_GET_PROVEN_VALUE,
    PREREQUISITE_18_PROVEN_AT_SEND_VALUE,
    PREREQUISITE_19_PROVEN_AT_SEND_VALUE,
    PREREQUISITE_21_PROVEN_AT_SEND_VALUE,
    PREREQUISITE_24_PROVEN_AT_SEND_VALUE,
    PUBLIC_SPEC_RETRIEVAL_PERFORMED,
    RUNTIME_GET_PERFORMED,
    RUNTIME_GET_REQUIRED,
    SEND_TIME_POSITION_REOBSERVATION,
    STP_CLOSED,
    STP_TEXT_REWRITTEN_VALUE,
    STPR_DOES_NOT_AUTHORIZE_BOUNDED_RUNTIME_PERMIT_ISSUANCE_VALUE,
    STPR_DOES_NOT_AUTHORIZE_FLATTEN_VALUE,
    STPR_DOES_NOT_AUTHORIZE_NETWORK_SESSION_VALUE,
    STPR_DOES_NOT_GRANT_EXECUTION_READINESS_VALUE,
    STPR_DOES_NOT_ISSUE_RUNTIME_PERMIT_VALUE,
    STPR_DOES_NOT_SET_LIVE_AUTHORIZED_VALUE,
    STPR_FLATTEN_EXECUTE_AUTHORIZED_VALUE,
    STPR_MECHANISM_IMPLEMENTED,
    STPR_NAMED_CONTRACT_CLOSED,
    STPR_NETWORK_SESSION_AUTHORIZED_VALUE,
    STPR_OBSERVATION_RUNTIME_PROVEN_VALUE,
    STPR_RUNTIME_PROVEN_VALUE,
    STPR_RUNTIME_RESIDUAL,
    TARGET_INSTRUMENT_ID,
    THIS_SLICE,
    WORKPACKAGE_ID,
)
from src.ops.section_11_13_5_send_time_position_reobservation_v1.lineage_v1 import (
    lineage_census_summary_v1,
    send_time_position_reobservation_lineage_v1,
)

QUOTE_TS = "1787145055768"
EVAL_TS = "1787145056000"
DECISION_ID = "stpr-offline-contract-decision"
WINDOW_EARLIER_THAN_STPR = {
    "EXECUTION_PREREQUISITE_08_TARGET_POSITION_NONZERO_PROVEN",
    "EXECUTION_PREREQUISITE_09_TARGET_POSITION_QTY_NUMERIC",
    "EXECUTION_PREREQUISITE_16_BOUNDED_ACTIVATION_WITHOUT_GLOBAL_LIVE_AUTHORIZED",
    "EXECUTION_PREREQUISITE_20_MUTATION_LIMITED_TO_PROVEN_POSITION",
    "EXECUTION_PREREQUISITE_25_NO_ADDITIONAL_OWNER_DECISION_REQUIRED",
    "SEND_TIME_PASS_18_19_21_24",
    "AUTHENTICATED_PRODUCTIVE_TRANSPORT",
    "SEND_TIME_POSITION_REOBSERVATION",
}


class SendTimePositionReobservationAdjudicationError(RuntimeError):
    """Fail-closed SEND_TIME_POSITION_REOBSERVATION adjudication violation."""


def _positions(*, pos: str = "1", inst_id: str = TARGET_INSTRUMENT_ID) -> dict[str, Any]:
    return {"code": "0", "data": [{"instId": inst_id, "pos": pos}]}


def _pending() -> dict[str, Any]:
    return {"code": "0", "data": []}


def _price() -> FlattenPriceInputV1:
    return FlattenPriceInputV1(
        flatten_side="SELL",
        observed_signed_pos="1",
        bid="0.8209",
        ask="0.8210",
        quote_timestamp_ms=QUOTE_TS,
        evaluation_timestamp_ms=EVAL_TS,
        tick_sz="0.0001",
        freshness_threshold_ms=str(FRESHNESS_THRESHOLD_MS),
    )


def _freshness() -> PositionObservationFreshnessEvidenceV1:
    return PositionObservationFreshnessEvidenceV1(
        response_received_monotonic_ms=0,
        decision_id=DECISION_ID,
        evidence_kind=PRE_SEND_EVIDENCE_KIND,
        observation_get_identity="FAKE_OFFLINE_FIXTURE",
    )


def _gate(**overrides: Any) -> FlattenPreSendGateInputV1:
    permit = overrides.pop(
        "bounded_activation_permit",
        offline_contract_proof_bounded_activation_permit_v1(
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            instrument_id=TARGET_INSTRUMENT_ID,
        ),
    )
    payload: dict[str, Any] = {
        "live_authorized": False,
        "live_enabled": True,
        "live_armed": True,
        "flatten_live_wire_enabled": True,
        "allow_productive_wire_send": True,
        "flatten_execute_token": FLATTEN_EXECUTE_CONFIRM_TOKEN_CANONICAL,
        "flatten_execute_purpose": FLATTEN_EXECUTE_PURPOSE_CANONICAL,
        "flatten_execute_owner_go": FLATTEN_EXECUTE_OWNER_GO_CANONICAL,
        "positions_payload": _positions(),
        "pending_orders_payload": _pending(),
        "price_input": _price(),
        "owner_go": "OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE",
        "origin_main_sha": EXPECTED_ORIGIN_MAIN_SHA,
        "flatten_execute_bound_origin_main_sha": EXPECTED_ORIGIN_MAIN_SHA,
        "instrument_id": TARGET_INSTRUMENT_ID,
        "one_shot_no_retry": True,
        "duplicate_post_protection": True,
        "flatten_pre_send_decision_id": DECISION_ID,
        "position_observation_freshness_evidence": _freshness(),
        "monotonic_ms_clock": (lambda: 0),
        "bounded_activation_permit": permit,
    }
    payload.update(overrides)
    return FlattenPreSendGateInputV1(**payload)


def _eval(**overrides: Any) -> tuple[bool, tuple[str, ...]]:
    payload: dict[str, Any] = {
        "apt_status": AUTHENTICATED_PRODUCTIVE_TRANSPORT_STATUS,
        "positions_payload": _positions(),
        "instrument_id": TARGET_INSTRUMENT_ID,
        "expected_instrument_id": TARGET_INSTRUMENT_ID,
        "freshness_evidence": _freshness(),
        "evaluation_monotonic_ms": 0,
        "current_decision_id": DECISION_ID,
        "claimed_remaining_after_send_time_position_reobservation": (
            NAMED_REMAINING_AFTER_SEND_TIME_POSITION_REOBSERVATION
        ),
        "producer_class": PRODUCER_CLASS_CALLER_SUPPLIED,
        "observation_identity": "FAKE_OFFLINE_FIXTURE",
        "historical_reuse_claim": False,
        "runtime_observation_proven_claim": False,
        "proven_at_send_18": False,
        "proven_at_send_19": False,
        "proven_at_send_21": False,
        "proven_at_send_24": False,
        "live_authorized_claim": False,
        "runtime_permit_issuance_claim": False,
        "flatten_execute_authorized_claim": False,
        "network_session_authorized_claim": False,
        "post_performed_claim": False,
        "get_performed_claim": False,
        "private_get_proven_claim": False,
        "credential_use_proven_claim": False,
        "empty_data_treated_as_zero_claim": False,
        "flatten_execute_owner_go": None,
        "predecessor_lineage_ok": True,
        "transport_error": None,
        "authentication_failure": None,
    }
    payload.update(overrides)
    return evaluate_send_time_position_reobservation_v1(**payload)


def adjudicate_send_time_position_reobservation_v1(
    *,
    origin_main_sha: str,
) -> dict[str, Any]:
    bound_sha = str(origin_main_sha or "").strip()
    if bound_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise SendTimePositionReobservationAdjudicationError("ORIGIN_MAIN_SHA_MISMATCH")
    if LIVE_AUTHORIZED is not False or LIVE_ENABLED is not False or LIVE_ARMED is not False:
        raise SendTimePositionReobservationAdjudicationError("STANDING_LIVE_FLAGS_UNLOCKED")
    if OWNER_GO not in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS:
        raise SendTimePositionReobservationAdjudicationError(
            "IMPLEMENTATION_GO_MUST_BE_FORBIDDEN_EXECUTE"
        )
    execute_ok, _execute_reasons = evaluate_flatten_execute_authority_v1(
        token=FLATTEN_EXECUTE_CONFIRM_TOKEN_CANONICAL,
        purpose=FLATTEN_EXECUTE_PURPOSE_CANONICAL,
        owner_go=OWNER_GO,
    )
    if execute_ok:
        raise SendTimePositionReobservationAdjudicationError(
            "IMPLEMENTATION_GO_ACCEPTED_AS_FLATTEN_EXECUTE"
        )
    missing_apt_ok, missing_apt = _eval(apt_status=None)
    if missing_apt_ok or REASON_MISSING_APT not in missing_apt:
        raise SendTimePositionReobservationAdjudicationError("MISSING_APT_MUST_DENY")
    unproven_apt_ok, unproven_apt = _eval(apt_status="UNPROVEN")
    if unproven_apt_ok or REASON_APT_NOT_PASS not in unproven_apt:
        raise SendTimePositionReobservationAdjudicationError("UNPROVEN_APT_MUST_DENY")
    missing_remaining_ok, missing_remaining = _eval(
        claimed_remaining_after_send_time_position_reobservation=None
    )
    if missing_remaining_ok or REASON_MISSING_REMAINING not in missing_remaining:
        raise SendTimePositionReobservationAdjudicationError("MISSING_REMAINING_MUST_DENY")
    mismatch_ok, mismatch = _eval(
        claimed_remaining_after_send_time_position_reobservation=("FLATTEN_EXECUTE",)
    )
    if mismatch_ok or REASON_REMAINING_MISMATCH not in mismatch:
        raise SendTimePositionReobservationAdjudicationError("REMAINING_MISMATCH_MUST_DENY")
    missing_obs_ok, missing_obs = _eval(positions_payload=None)
    if missing_obs_ok or REASON_OBSERVATION_MISSING not in missing_obs:
        raise SendTimePositionReobservationAdjudicationError("MISSING_OBSERVATION_MUST_DENY")
    empty_ok, empty_reasons = _eval(positions_payload={"code": "0", "data": []})
    if empty_ok or REASON_EMPTY_DATA_NOT_ZERO not in empty_reasons:
        raise SendTimePositionReobservationAdjudicationError("EMPTY_DATA_MUST_DENY")
    if REASON_TARGET_NOT_OBSERVED not in empty_reasons:
        raise SendTimePositionReobservationAdjudicationError("EMPTY_DATA_MUST_NOT_OBSERVE_TARGET")
    mismatch_inst_ok, mismatch_inst = _eval(instrument_id="BTC-USD_UM_XPERP-000000")
    if mismatch_inst_ok or REASON_INSTRUMENT_MISMATCH not in mismatch_inst:
        raise SendTimePositionReobservationAdjudicationError("INSTRUMENT_MISMATCH_MUST_DENY")
    not_obs_ok, not_obs = _eval(
        positions_payload={"code": "0", "data": [{"instId": "BTC-USD_UM_XPERP-000000", "pos": "1"}]}
    )
    if not_obs_ok or REASON_TARGET_NOT_OBSERVED not in not_obs:
        raise SendTimePositionReobservationAdjudicationError("TARGET_NOT_OBSERVED_MUST_DENY")
    zero_ok, zero_reasons = _eval(positions_payload=_positions(pos="0"))
    if zero_ok or REASON_ZERO_POSITION not in zero_reasons:
        raise SendTimePositionReobservationAdjudicationError("ZERO_POSITION_MUST_DENY")
    malformed_ok, malformed = _eval(positions_payload={"code": "0", "data": "not-a-list"})
    if malformed_ok or REASON_MALFORMED_PAYLOAD not in malformed:
        raise SendTimePositionReobservationAdjudicationError("MALFORMED_PAYLOAD_MUST_DENY")
    hist_ok, hist_reasons = _eval(observation_identity="20260903T223726Z")
    if hist_ok or REASON_HISTORICAL_REUSE not in hist_reasons:
        raise SendTimePositionReobservationAdjudicationError("HISTORICAL_REUSE_MUST_DENY")
    hist_claim_ok, hist_claim = _eval(historical_reuse_claim=True)
    if hist_claim_ok or REASON_HISTORICAL_REUSE not in hist_claim:
        raise SendTimePositionReobservationAdjudicationError("HISTORICAL_REUSE_CLAIM_MUST_DENY")
    transport_ok, transport_reasons = _eval(positions_payload=None, transport_error="URLERROR")
    if transport_ok or REASON_TRANSPORT_FAILURE not in transport_reasons:
        raise SendTimePositionReobservationAdjudicationError("TRANSPORT_FAILURE_MUST_DENY")
    auth_ok, auth_reasons = _eval(positions_payload=None, authentication_failure="50110")
    if auth_ok or REASON_AUTHENTICATION_FAILURE not in auth_reasons:
        raise SendTimePositionReobservationAdjudicationError("AUTHENTICATION_FAILURE_MUST_DENY")
    get_producer_ok, get_producer = _eval(producer_class=PRODUCER_CLASS_AUTHENTICATED_PRIVATE_GET)
    if get_producer_ok or REASON_AUTHENTICATED_GET_PRODUCER not in get_producer:
        raise SendTimePositionReobservationAdjudicationError("AUTHENTICATED_GET_PRODUCER_MUST_DENY")
    runtime_ok, runtime_reasons = _eval(runtime_observation_proven_claim=True)
    if runtime_ok or REASON_RUNTIME_OBSERVATION_CLAIM not in runtime_reasons:
        raise SendTimePositionReobservationAdjudicationError("RUNTIME_OBSERVATION_CLAIM_MUST_DENY")
    proven_ok, proven_reasons = _eval(proven_at_send_18=True)
    if proven_ok or REASON_PROVEN_AT_SEND_CLAIM not in proven_reasons:
        raise SendTimePositionReobservationAdjudicationError("PROVEN_AT_SEND_CLAIM_MUST_DENY")
    live_ok, live_reasons = _eval(live_authorized_claim=True)
    if live_ok or REASON_LIVE_AUTHORIZED_SUBSTITUTE not in live_reasons:
        raise SendTimePositionReobservationAdjudicationError("LIVE_AUTHORIZED_SUBSTITUTE_MUST_DENY")
    permit_ok, permit_reasons = _eval(runtime_permit_issuance_claim=True)
    if permit_ok or REASON_RUNTIME_PERMIT not in permit_reasons:
        raise SendTimePositionReobservationAdjudicationError("RUNTIME_PERMIT_MUST_DENY")
    flatten_ok, flatten_reasons = _eval(flatten_execute_authorized_claim=True)
    if flatten_ok or REASON_FLATTEN_EXECUTE not in flatten_reasons:
        raise SendTimePositionReobservationAdjudicationError("FLATTEN_EXECUTE_CLAIM_MUST_DENY")
    network_ok, network_reasons = _eval(network_session_authorized_claim=True)
    if network_ok or REASON_NETWORK_SESSION not in network_reasons:
        raise SendTimePositionReobservationAdjudicationError("NETWORK_SESSION_CLAIM_MUST_DENY")
    post_ok, post_reasons = _eval(post_performed_claim=True)
    if post_ok or REASON_POST not in post_reasons:
        raise SendTimePositionReobservationAdjudicationError("POST_CLAIM_MUST_DENY")
    get_ok, get_reasons = _eval(get_performed_claim=True)
    if get_ok or REASON_GET not in get_reasons or REASON_FAKE_COUNTED_AS_GET not in get_reasons:
        raise SendTimePositionReobservationAdjudicationError("GET_CLAIM_MUST_DENY")
    private_ok, private_reasons = _eval(private_get_proven_claim=True)
    if private_ok or REASON_PRIVATE_GET_CLAIM not in private_reasons:
        raise SendTimePositionReobservationAdjudicationError("PRIVATE_GET_CLAIM_MUST_DENY")
    cred_ok, cred_reasons = _eval(credential_use_proven_claim=True)
    if cred_ok or REASON_CREDENTIAL_USE_CLAIM not in cred_reasons:
        raise SendTimePositionReobservationAdjudicationError("CREDENTIAL_USE_CLAIM_MUST_DENY")
    go_ok, go_reasons = _eval(flatten_execute_owner_go=OWNER_GO)
    if go_ok or REASON_IMPLEMENTATION_GO_AS_EXECUTE not in go_reasons:
        raise SendTimePositionReobservationAdjudicationError(
            "IMPLEMENTATION_GO_AS_EXECUTE_MUST_DENY"
        )
    lineage_ok, lineage_reasons = _eval(predecessor_lineage_ok=False)
    if lineage_ok or REASON_LINEAGE_MISMATCH not in lineage_reasons:
        raise SendTimePositionReobservationAdjudicationError("LINEAGE_MISMATCH_MUST_DENY")
    matching_ok, matching_reasons = _eval()
    if matching_ok is not True or matching_reasons:
        raise SendTimePositionReobservationAdjudicationError(
            f"MATCHING_CONTRACT_MUST_PASS:{matching_reasons}"
        )
    if AUTHENTICATED_PRODUCTIVE_TRANSPORT_STATUS != PASS_OFFLINE_CONTRACT:
        raise SendTimePositionReobservationAdjudicationError("APT_STATUS_DRIFT")
    fake = RecordingSendTimePositionReobservationProducerV1()
    observed = fake.observe()
    if fake.last_get_attempted is True or fake.network_session_authorized is True:
        raise SendTimePositionReobservationAdjudicationError("FAKE_PRODUCER_MUST_NOT_GET")
    if observed.producer_class != PRODUCER_CLASS_FAKE_OFFLINE:
        raise SendTimePositionReobservationAdjudicationError("FAKE_PRODUCER_CLASS_DRIFT")
    execute_as_stpr = evaluate_flatten_pre_send_gate_v1(_gate(flatten_execute_owner_go=OWNER_GO))
    if execute_as_stpr.allowed is True:
        raise SendTimePositionReobservationAdjudicationError("STPR_GO_AS_EXECUTE_GATE_MUST_DENY")
    stpr_execute_deny = [
        item
        for item in execute_as_stpr.audit_decisions
        if item[0] == "SEND_TIME_POSITION_REOBSERVATION"
    ]
    if not stpr_execute_deny or not str(stpr_execute_deny[0][1]).startswith("DENY:"):
        raise SendTimePositionReobservationAdjudicationError(
            "STPR_GO_AS_EXECUTE_STPR_GATE_MUST_DENY"
        )
    reachable = evaluate_flatten_pre_send_gate_v1(_gate())
    if reachable.allowed is not True:
        raise SendTimePositionReobservationAdjudicationError(
            f"BOUNDED_PATH_NOT_STRUCTURALLY_REACHABLE:{reachable.reasons}"
        )
    stpr_pass = [
        item for item in reachable.audit_decisions if item[0] == "SEND_TIME_POSITION_REOBSERVATION"
    ]
    if not stpr_pass or stpr_pass[0][1] != "PASS":
        raise SendTimePositionReobservationAdjudicationError("MATCHING_FIXTURE_STPR_GATE_MUST_PASS")
    window = adjudicate_prerequisite_08_window_v1(positions_payload=_positions())
    window_earliest = str(window.get("EARLIEST_UNRESOLVED_DEPENDENCY") or "")
    if window_earliest in WINDOW_EARLIER_THAN_STPR:
        raise SendTimePositionReobservationAdjudicationError("WINDOW_EARLIEST_DEPENDENCY_DRIFT")
    if window_earliest != EARLIEST_UNRESOLVED_DEPENDENCY:
        raise SendTimePositionReobservationAdjudicationError("WINDOW_EARLIEST_DEPENDENCY_DRIFT")
    lineage = send_time_position_reobservation_lineage_v1()
    census = lineage_census_summary_v1()
    if int(census["SEAM_COUNT"]) != len(lineage):
        raise SendTimePositionReobservationAdjudicationError("LINEAGE_CENSUS_DRIFT")
    return {
        "OWNER_GO": OWNER_GO,
        "PRIOR_OWNER_GO": PRIOR_OWNER_GO,
        "THIS_SLICE": THIS_SLICE,
        "PREDECESSOR_SLICE": PREDECESSOR_SLICE,
        "WORKPACKAGE_ID": WORKPACKAGE_ID,
        "BOUND_ORIGIN_MAIN_SHA": bound_sha,
        "TARGET_INSTRUMENT_ID": TARGET_INSTRUMENT_ID,
        "CASE": CASE_VALUE,
        "SEND_TIME_POSITION_REOBSERVATION": SEND_TIME_POSITION_REOBSERVATION,
        "SEND_TIME_POSITION_REOBSERVATION_OFFLINE_CONTRACT": SEND_TIME_POSITION_REOBSERVATION,
        "STPR_NAMED_REOBSERVATION_CONTRACT_CLOSED": STPR_NAMED_CONTRACT_CLOSED,
        "STPR_REOBSERVATION_GATE_IMPLEMENTED": STPR_MECHANISM_IMPLEMENTED,
        "SEND_TIME_POSITION_REOBSERVATION_RUNTIME_PROVEN": STPR_RUNTIME_PROVEN_VALUE,
        "STPR_OBSERVATION_RUNTIME_PROVEN": STPR_OBSERVATION_RUNTIME_PROVEN_VALUE,
        "NETWORK_PROVEN": NETWORK_PROVEN_VALUE,
        "CREDENTIAL_USE_PROVEN": CREDENTIAL_USE_PROVEN_VALUE,
        "PRIVATE_GET_PROVEN": PRIVATE_GET_PROVEN_VALUE,
        "POST_PROVEN": POST_PROVEN_VALUE,
        "PREREQUISITE_18_PROVEN_AT_SEND": PREREQUISITE_18_PROVEN_AT_SEND_VALUE,
        "PREREQUISITE_19_PROVEN_AT_SEND": PREREQUISITE_19_PROVEN_AT_SEND_VALUE,
        "PREREQUISITE_21_PROVEN_AT_SEND": PREREQUISITE_21_PROVEN_AT_SEND_VALUE,
        "PREREQUISITE_24_PROVEN_AT_SEND": PREREQUISITE_24_PROVEN_AT_SEND_VALUE,
        "STPR_NETWORK_SESSION_AUTHORIZED": STPR_NETWORK_SESSION_AUTHORIZED_VALUE,
        "STPR_FLATTEN_EXECUTE_AUTHORIZED": STPR_FLATTEN_EXECUTE_AUTHORIZED_VALUE,
        "NAMED_REMAINING_HIGHER_AUTHORITY": list(NAMED_REMAINING_HIGHER_AUTHORITY),
        "OFFLINE_CONTRACT_PROOF_CLASS": "OFFLINE_CONTRACT_REGRESSION_FIXTURE_NOT_RUNTIME_PERMIT",
        "STRUCTURAL_ALLOW_IS_NOT_RUNTIME_MUTATION": True,
        "STRUCTURAL_ALLOW_IS_NOT_WIRE_SEND": True,
        "FAIL_CLOSED_STATUS": "PASS",
        "CONFLICT_COUNT": CONFLICT_COUNT,
        "P08_CLOSED": P08_CLOSED,
        "P10_CLOSED": P10_CLOSED,
        "P11_CLOSED": P11_CLOSED,
        "P12_CLOSED": P12_CLOSED,
        "P13_CLOSED": P13_CLOSED,
        "P16_CLOSED": P16_CLOSED,
        "P20_CLOSED": P20_CLOSED,
        "P25_CLOSED": P25_CLOSED,
        "STP_CLOSED": STP_CLOSED,
        "APT_CLOSED": APT_CLOSED,
        "APT_TEXT_REWRITTEN": APT_TEXT_REWRITTEN_VALUE,
        "STP_TEXT_REWRITTEN": STP_TEXT_REWRITTEN_VALUE,
        "P16_TEXT_REWRITTEN": P16_TEXT_REWRITTEN_VALUE,
        "P20_TEXT_REWRITTEN": P20_TEXT_REWRITTEN_VALUE,
        "P25_TEXT_REWRITTEN": P25_TEXT_REWRITTEN_VALUE,
        "LAST_CANONICALLY_CLOSED_STEP": LAST_CANONICALLY_CLOSED_STEP,
        "EARLIEST_UNRESOLVED_DEPENDENCY": EARLIEST_UNRESOLVED_DEPENDENCY,
        "NEXT_AUTHORITY_BOUNDARY": NEXT_AUTHORITY_BOUNDARY,
        "STPR_RUNTIME_RESIDUAL": STPR_RUNTIME_RESIDUAL,
        "STPR_DOES_NOT_GRANT_EXECUTION_READINESS": STPR_DOES_NOT_GRANT_EXECUTION_READINESS_VALUE,
        "STPR_DOES_NOT_AUTHORIZE_FLATTEN": STPR_DOES_NOT_AUTHORIZE_FLATTEN_VALUE,
        "STPR_DOES_NOT_SET_LIVE_AUTHORIZED": STPR_DOES_NOT_SET_LIVE_AUTHORIZED_VALUE,
        "STPR_DOES_NOT_ISSUE_RUNTIME_PERMIT": STPR_DOES_NOT_ISSUE_RUNTIME_PERMIT_VALUE,
        "STPR_DOES_NOT_AUTHORIZE_NETWORK_SESSION": STPR_DOES_NOT_AUTHORIZE_NETWORK_SESSION_VALUE,
        "STPR_DOES_NOT_AUTHORIZE_BOUNDED_RUNTIME_PERMIT_ISSUANCE": (
            STPR_DOES_NOT_AUTHORIZE_BOUNDED_RUNTIME_PERMIT_ISSUANCE_VALUE
        ),
        "FAIL_CLOSED_IF_MARKED_RUNTIME_PROVEN_FROM_OFFLINE_CODE_ALONE": (
            FAIL_CLOSED_IF_MARKED_RUNTIME_PROVEN_FROM_OFFLINE_CODE_ALONE_VALUE
        ),
        "FAIL_CLOSED_IF_MARKED_PROVEN_AT_SEND_FROM_OFFLINE_CODE_ALONE": (
            FAIL_CLOSED_IF_MARKED_PROVEN_AT_SEND_FROM_OFFLINE_CODE_ALONE_VALUE
        ),
        "RUNTIME_GET_REQUIRED": RUNTIME_GET_REQUIRED,
        "RUNTIME_GET_PERFORMED": RUNTIME_GET_PERFORMED,
        "PRIVATE_AUTH_USED": PRIVATE_AUTH_USED,
        "PUBLIC_SPEC_RETRIEVAL_PERFORMED": PUBLIC_SPEC_RETRIEVAL_PERFORMED,
        "POSITION_GET_REQUIRED_THIS_PERSIST": POSITION_GET_REQUIRED_THIS_PERSIST_VALUE,
        "POSITION_GET_AUTHORIZED_BY_THIS_OWNER_GO": POSITION_GET_AUTHORIZED_BY_THIS_OWNER_GO_VALUE,
        "LIVE_EXECUTION": False,
        "CANARY_EXECUTION": False,
        "MERGE_AUTHORIZED_BY_THIS_PERSIST": False,
        "THIS_GO_GET_COUNT": 0,
        "THIS_GO_POST_COUNT": 0,
        "GET_PERFORMED_THIS_PERSIST": False,
        "POST_PERFORMED": False,
        "BOUNDED_RUNTIME_PERMIT_ISSUANCE": False,
        "NETWORK_SESSION_AUTHORIZED_DEFAULT": False,
        "IMPLEMENTATION_GO_FORBIDDEN_AS_FLATTEN_EXECUTE": True,
        "CENSUS": census,
        "LINEAGE": lineage,
        "WINDOW_EARLIEST_UNRESOLVED_DEPENDENCY": window.get("EARLIEST_UNRESOLVED_DEPENDENCY"),
    }
