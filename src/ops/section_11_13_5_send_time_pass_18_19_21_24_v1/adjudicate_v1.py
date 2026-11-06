"""Offline SEND_TIME_PASS_18_19_21_24 adjudication. No GET. No POST."""

from __future__ import annotations

from typing import Any

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
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_productive_transport_v1 import (
    GatedProductiveFlattenTransportV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.position_observation_freshness_contract_v1 import (
    PRE_SEND_EVIDENCE_KIND,
    PositionObservationFreshnessEvidenceV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.prerequisite_08_fresh_position_observation_v1 import (
    adjudicate_prerequisite_08_window_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.send_time_pass_18_19_21_24_v1 import (
    NAMED_REMAINING_AFTER_SEND_TIME_PASS,
    PASS_OFFLINE_CONTRACT,
    REASON_18_FLATTEN_FLOW_NOT_BOUND,
    REASON_18_OPEN_ORDER_CONFLICT,
    REASON_18_REDUCE_ONLY_REQUIRED,
    REASON_19_INSTRUMENT_MISMATCH,
    REASON_21_DUPLICATE_POST_REQUIRED,
    REASON_21_ONE_SHOT_REQUIRED,
    REASON_24_AUDIT_BOUNDARY_MISSING,
    REASON_24_HTTP_200_IMPLIES_SUCCESS,
    REASON_FLATTEN_EXECUTE,
    REASON_GET,
    REASON_IMPLEMENTATION_GO_AS_EXECUTE,
    REASON_LINEAGE_MISMATCH,
    REASON_LIVE_AUTHORIZED_SUBSTITUTE,
    REASON_MISSING_P25,
    REASON_MISSING_REMAINING,
    REASON_NETWORK_SESSION,
    REASON_P25_NOT_PASS,
    REASON_POST,
    REASON_PROVEN_AT_SEND_CLAIM,
    REASON_REMAINING_MISMATCH,
    REASON_RUNTIME_PERMIT,
    evaluate_send_time_pass_18_19_21_24_v1,
)
from src.ops.section_11_13_5_p25_execution_prerequisite_25_no_additional_owner_decision_v1.contract_v1 import (
    EXECUTION_PREREQUISITE_25_STATUS,
)
from src.ops.section_11_13_5_send_time_pass_18_19_21_24_v1.constants_v1 import (
    CASE_VALUE,
    CONFLICT_COUNT,
    EARLIEST_UNRESOLVED_DEPENDENCY,
    EXPECTED_ORIGIN_MAIN_SHA,
    FAIL_CLOSED_IF_MARKED_PROVEN_AT_SEND_FROM_OFFLINE_CODE_ALONE_VALUE,
    LAST_CANONICALLY_CLOSED_STEP,
    NAMED_REMAINING_HIGHER_AUTHORITY,
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
    PREDECESSOR_SLICE,
    PRIOR_OWNER_GO,
    PREREQUISITE_18_PROVEN_AT_SEND_VALUE,
    PREREQUISITE_19_PROVEN_AT_SEND_VALUE,
    PREREQUISITE_21_PROVEN_AT_SEND_VALUE,
    PREREQUISITE_24_PROVEN_AT_SEND_VALUE,
    PRIVATE_AUTH_USED,
    PUBLIC_SPEC_RETRIEVAL_PERFORMED,
    RUNTIME_GET_PERFORMED,
    RUNTIME_GET_REQUIRED,
    SEND_TIME_PASS_18_19_21_24,
    STP_DOES_NOT_AUTHORIZE_AUTHENTICATED_PRODUCTIVE_TRANSPORT_VALUE,
    STP_DOES_NOT_AUTHORIZE_FLATTEN_VALUE,
    STP_DOES_NOT_AUTHORIZE_NETWORK_SESSION_VALUE,
    STP_DOES_NOT_GRANT_EXECUTION_READINESS_VALUE,
    STP_DOES_NOT_ISSUE_RUNTIME_PERMIT_VALUE,
    STP_DOES_NOT_SET_LIVE_AUTHORIZED_VALUE,
    STP_FLATTEN_EXECUTE_AUTHORIZED_VALUE,
    STP_MECHANISM_IMPLEMENTED,
    STP_NAMED_CONTRACT_CLOSED,
    STP_NETWORK_SESSION_AUTHORIZED_VALUE,
    STP_RUNTIME_RESIDUAL,
    STP_SEND_TIME_REOBSERVATION_PROVEN_VALUE,
    TARGET_INSTRUMENT_ID,
    THIS_SLICE,
    WORKPACKAGE_ID,
)
from src.ops.section_11_13_5_send_time_pass_18_19_21_24_v1.lineage_v1 import (
    lineage_census_summary_v1,
    send_time_pass_lineage_v1,
)

QUOTE_TS = "1787145055768"
EVAL_TS = "1787145056000"
DECISION_ID = "stp-offline-contract-decision"
WRONG_INSTRUMENT_ID = "BTC-USD_UM_XPERP-000000"
WINDOW_EARLIER_THAN_STP = {
    "EXECUTION_PREREQUISITE_08_TARGET_POSITION_NONZERO_PROVEN",
    "EXECUTION_PREREQUISITE_09_TARGET_POSITION_QTY_NUMERIC",
    "EXECUTION_PREREQUISITE_16_BOUNDED_ACTIVATION_WITHOUT_GLOBAL_LIVE_AUTHORIZED",
    "EXECUTION_PREREQUISITE_20_MUTATION_LIMITED_TO_PROVEN_POSITION",
    "EXECUTION_PREREQUISITE_25_NO_ADDITIONAL_OWNER_DECISION_REQUIRED",
    "SEND_TIME_PASS_18_19_21_24",
}


class SendTimePass182124AdjudicationError(RuntimeError):
    """Fail-closed SEND_TIME_PASS_18_19_21_24 adjudication violation."""


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
        "position_observation_freshness_evidence": PositionObservationFreshnessEvidenceV1(
            response_received_monotonic_ms=0,
            decision_id=DECISION_ID,
            evidence_kind=PRE_SEND_EVIDENCE_KIND,
        ),
        "monotonic_ms_clock": (lambda: 0),
        "bounded_activation_permit": permit,
    }
    payload.update(overrides)
    return FlattenPreSendGateInputV1(**payload)


def _eval(**overrides: Any) -> tuple[bool, tuple[str, ...]]:
    payload: dict[str, Any] = {
        "p25_status": EXECUTION_PREREQUISITE_25_STATUS,
        "reduce_only": True,
        "flatten_flow_bound": True,
        "dedicated_flatten_transport": True,
        "open_order_conflict": False,
        "instrument_id": TARGET_INSTRUMENT_ID,
        "expected_instrument_id": TARGET_INSTRUMENT_ID,
        "duplicate_post_protection": True,
        "one_shot_no_retry": True,
        "audit_boundary_present": True,
        "http_200_implies_flatten_success": False,
        "claimed_remaining_after_send_time_pass": NAMED_REMAINING_AFTER_SEND_TIME_PASS,
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
        "flatten_execute_owner_go": None,
        "predecessor_lineage_ok": True,
    }
    payload.update(overrides)
    return evaluate_send_time_pass_18_19_21_24_v1(**payload)


def adjudicate_send_time_pass_18_19_21_24_v1(
    *,
    origin_main_sha: str,
) -> dict[str, Any]:
    bound_sha = str(origin_main_sha or "").strip()
    if bound_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise SendTimePass182124AdjudicationError("ORIGIN_MAIN_SHA_MISMATCH")
    if LIVE_AUTHORIZED is not False or LIVE_ENABLED is not False or LIVE_ARMED is not False:
        raise SendTimePass182124AdjudicationError("STANDING_LIVE_FLAGS_UNLOCKED")
    if OWNER_GO not in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS:
        raise SendTimePass182124AdjudicationError("IMPLEMENTATION_GO_MUST_BE_FORBIDDEN_EXECUTE")
    execute_ok, _execute_reasons = evaluate_flatten_execute_authority_v1(
        token=FLATTEN_EXECUTE_CONFIRM_TOKEN_CANONICAL,
        purpose=FLATTEN_EXECUTE_PURPOSE_CANONICAL,
        owner_go=OWNER_GO,
    )
    if execute_ok:
        raise SendTimePass182124AdjudicationError("IMPLEMENTATION_GO_ACCEPTED_AS_FLATTEN_EXECUTE")
    missing_p25_ok, missing_p25 = _eval(p25_status=None)
    if missing_p25_ok or REASON_MISSING_P25 not in missing_p25:
        raise SendTimePass182124AdjudicationError("MISSING_P25_MUST_DENY")
    unproven_p25_ok, unproven_p25 = _eval(p25_status="UNPROVEN")
    if unproven_p25_ok or REASON_P25_NOT_PASS not in unproven_p25:
        raise SendTimePass182124AdjudicationError("UNPROVEN_P25_MUST_DENY")
    missing_remaining_ok, missing_remaining = _eval(claimed_remaining_after_send_time_pass=None)
    if missing_remaining_ok or REASON_MISSING_REMAINING not in missing_remaining:
        raise SendTimePass182124AdjudicationError("MISSING_REMAINING_MUST_DENY")
    mismatch_ok, mismatch = _eval(claimed_remaining_after_send_time_pass=("FLATTEN_EXECUTE",))
    if mismatch_ok or REASON_REMAINING_MISMATCH not in mismatch:
        raise SendTimePass182124AdjudicationError("REMAINING_MISMATCH_MUST_DENY")
    flow_ok, flow_reasons = _eval(flatten_flow_bound=False)
    if flow_ok or REASON_18_FLATTEN_FLOW_NOT_BOUND not in flow_reasons:
        raise SendTimePass182124AdjudicationError("FLATTEN_FLOW_UNBOUND_MUST_DENY")
    reduce_ok, reduce_reasons = _eval(reduce_only=False)
    if reduce_ok or REASON_18_REDUCE_ONLY_REQUIRED not in reduce_reasons:
        raise SendTimePass182124AdjudicationError("REDUCE_ONLY_FALSE_MUST_DENY")
    conflict_ok, conflict_reasons = _eval(open_order_conflict=True)
    if conflict_ok or REASON_18_OPEN_ORDER_CONFLICT not in conflict_reasons:
        raise SendTimePass182124AdjudicationError("OPEN_ORDER_CONFLICT_MUST_DENY")
    inst_ok, inst_reasons = _eval(instrument_id=WRONG_INSTRUMENT_ID)
    if inst_ok or REASON_19_INSTRUMENT_MISMATCH not in inst_reasons:
        raise SendTimePass182124AdjudicationError("WRONG_INSTRUMENT_MUST_DENY")
    dup_ok, dup_reasons = _eval(duplicate_post_protection=False)
    if dup_ok or REASON_21_DUPLICATE_POST_REQUIRED not in dup_reasons:
        raise SendTimePass182124AdjudicationError("DUPLICATE_POST_FALSE_MUST_DENY")
    shot_ok, shot_reasons = _eval(one_shot_no_retry=False)
    if shot_ok or REASON_21_ONE_SHOT_REQUIRED not in shot_reasons:
        raise SendTimePass182124AdjudicationError("ONE_SHOT_FALSE_MUST_DENY")
    audit_ok, audit_reasons = _eval(audit_boundary_present=False)
    if audit_ok or REASON_24_AUDIT_BOUNDARY_MISSING not in audit_reasons:
        raise SendTimePass182124AdjudicationError("AUDIT_BOUNDARY_MISSING_MUST_DENY")
    http_ok, http_reasons = _eval(http_200_implies_flatten_success=True)
    if http_ok or REASON_24_HTTP_200_IMPLIES_SUCCESS not in http_reasons:
        raise SendTimePass182124AdjudicationError("HTTP_200_SUCCESS_CLAIM_MUST_DENY")
    proven_ok, proven_reasons = _eval(proven_at_send_18=True)
    if proven_ok or REASON_PROVEN_AT_SEND_CLAIM not in proven_reasons:
        raise SendTimePass182124AdjudicationError("PROVEN_AT_SEND_CLAIM_MUST_DENY")
    live_ok, live_reasons = _eval(live_authorized_claim=True)
    if live_ok or REASON_LIVE_AUTHORIZED_SUBSTITUTE not in live_reasons:
        raise SendTimePass182124AdjudicationError("LIVE_AUTHORIZED_SUBSTITUTE_MUST_DENY")
    permit_ok, permit_reasons = _eval(runtime_permit_issuance_claim=True)
    if permit_ok or REASON_RUNTIME_PERMIT not in permit_reasons:
        raise SendTimePass182124AdjudicationError("RUNTIME_PERMIT_MUST_DENY")
    flatten_ok, flatten_reasons = _eval(flatten_execute_authorized_claim=True)
    if flatten_ok or REASON_FLATTEN_EXECUTE not in flatten_reasons:
        raise SendTimePass182124AdjudicationError("FLATTEN_EXECUTE_CLAIM_MUST_DENY")
    network_ok, network_reasons = _eval(network_session_authorized_claim=True)
    if network_ok or REASON_NETWORK_SESSION not in network_reasons:
        raise SendTimePass182124AdjudicationError("NETWORK_SESSION_CLAIM_MUST_DENY")
    post_ok, post_reasons = _eval(post_performed_claim=True)
    if post_ok or REASON_POST not in post_reasons:
        raise SendTimePass182124AdjudicationError("POST_CLAIM_MUST_DENY")
    get_ok, get_reasons = _eval(get_performed_claim=True)
    if get_ok or REASON_GET not in get_reasons:
        raise SendTimePass182124AdjudicationError("GET_CLAIM_MUST_DENY")
    go_ok, go_reasons = _eval(flatten_execute_owner_go=OWNER_GO)
    if go_ok or REASON_IMPLEMENTATION_GO_AS_EXECUTE not in go_reasons:
        raise SendTimePass182124AdjudicationError("IMPLEMENTATION_GO_AS_EXECUTE_MUST_DENY")
    lineage_ok, lineage_reasons = _eval(predecessor_lineage_ok=False)
    if lineage_ok or REASON_LINEAGE_MISMATCH not in lineage_reasons:
        raise SendTimePass182124AdjudicationError("LINEAGE_MISMATCH_MUST_DENY")
    matching_ok, matching_reasons = _eval()
    if matching_ok is not True or matching_reasons:
        raise SendTimePass182124AdjudicationError(f"MATCHING_CONTRACT_MUST_PASS:{matching_reasons}")
    if EXECUTION_PREREQUISITE_25_STATUS != PASS_OFFLINE_CONTRACT:
        raise SendTimePass182124AdjudicationError("P25_STATUS_DRIFT")
    execute_as_stp = evaluate_flatten_pre_send_gate_v1(_gate(flatten_execute_owner_go=OWNER_GO))
    if execute_as_stp.allowed is True:
        raise SendTimePass182124AdjudicationError("STP_GO_AS_EXECUTE_GATE_MUST_DENY")
    stp_execute_deny = [
        item for item in execute_as_stp.audit_decisions if item[0] == "SEND_TIME_PASS_18_19_21_24"
    ]
    if not stp_execute_deny or not str(stp_execute_deny[0][1]).startswith("DENY:"):
        raise SendTimePass182124AdjudicationError("STP_GO_AS_EXECUTE_STP_GATE_MUST_DENY")
    reachable = evaluate_flatten_pre_send_gate_v1(_gate())
    if reachable.allowed is not True:
        raise SendTimePass182124AdjudicationError(
            f"BOUNDED_PATH_NOT_STRUCTURALLY_REACHABLE:{reachable.reasons}"
        )
    stp_pass = [
        item for item in reachable.audit_decisions if item[0] == "SEND_TIME_PASS_18_19_21_24"
    ]
    if not stp_pass or stp_pass[0][1] != "PASS":
        raise SendTimePass182124AdjudicationError("MATCHING_FIXTURE_STP_GATE_MUST_PASS")
    transport = GatedProductiveFlattenTransportV1()
    if transport.network_session_authorized is not False:
        raise SendTimePass182124AdjudicationError("NETWORK_SESSION_DEFAULT_NOT_FALSE")
    window = adjudicate_prerequisite_08_window_v1(positions_payload=_positions())
    window_earliest = str(window.get("EARLIEST_UNRESOLVED_DEPENDENCY") or "")
    if window_earliest in WINDOW_EARLIER_THAN_STP:
        raise SendTimePass182124AdjudicationError("WINDOW_EARLIEST_DEPENDENCY_DRIFT")
    lineage = send_time_pass_lineage_v1()
    census = lineage_census_summary_v1()
    if int(census["SEAM_COUNT"]) != len(lineage):
        raise SendTimePass182124AdjudicationError("LINEAGE_CENSUS_DRIFT")
    return {
        "OWNER_GO": OWNER_GO,
        "PRIOR_OWNER_GO": PRIOR_OWNER_GO,
        "THIS_SLICE": THIS_SLICE,
        "PREDECESSOR_SLICE": PREDECESSOR_SLICE,
        "WORKPACKAGE_ID": WORKPACKAGE_ID,
        "BOUND_ORIGIN_MAIN_SHA": bound_sha,
        "TARGET_INSTRUMENT_ID": TARGET_INSTRUMENT_ID,
        "CASE": CASE_VALUE,
        "SEND_TIME_PASS_18_19_21_24": SEND_TIME_PASS_18_19_21_24,
        "STP_NAMED_SEND_TIME_EVALUATION_CONTRACT_CLOSED": STP_NAMED_CONTRACT_CLOSED,
        "STP_SEND_TIME_EVALUATION_GATE_IMPLEMENTED": STP_MECHANISM_IMPLEMENTED,
        "PREREQUISITE_18_PROVEN_AT_SEND": PREREQUISITE_18_PROVEN_AT_SEND_VALUE,
        "PREREQUISITE_19_PROVEN_AT_SEND": PREREQUISITE_19_PROVEN_AT_SEND_VALUE,
        "PREREQUISITE_21_PROVEN_AT_SEND": PREREQUISITE_21_PROVEN_AT_SEND_VALUE,
        "PREREQUISITE_24_PROVEN_AT_SEND": PREREQUISITE_24_PROVEN_AT_SEND_VALUE,
        "STP_SEND_TIME_REOBSERVATION_PROVEN": STP_SEND_TIME_REOBSERVATION_PROVEN_VALUE,
        "STP_NETWORK_SESSION_AUTHORIZED": STP_NETWORK_SESSION_AUTHORIZED_VALUE,
        "STP_FLATTEN_EXECUTE_AUTHORIZED": STP_FLATTEN_EXECUTE_AUTHORIZED_VALUE,
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
        "P16_TEXT_REWRITTEN": P16_TEXT_REWRITTEN_VALUE,
        "P20_TEXT_REWRITTEN": P20_TEXT_REWRITTEN_VALUE,
        "P25_TEXT_REWRITTEN": P25_TEXT_REWRITTEN_VALUE,
        "LAST_CANONICALLY_CLOSED_STEP": LAST_CANONICALLY_CLOSED_STEP,
        "EARLIEST_UNRESOLVED_DEPENDENCY": EARLIEST_UNRESOLVED_DEPENDENCY,
        "NEXT_AUTHORITY_BOUNDARY": NEXT_AUTHORITY_BOUNDARY,
        "STP_RUNTIME_RESIDUAL": STP_RUNTIME_RESIDUAL,
        "STP_DOES_NOT_GRANT_EXECUTION_READINESS": STP_DOES_NOT_GRANT_EXECUTION_READINESS_VALUE,
        "STP_DOES_NOT_AUTHORIZE_FLATTEN": STP_DOES_NOT_AUTHORIZE_FLATTEN_VALUE,
        "STP_DOES_NOT_SET_LIVE_AUTHORIZED": STP_DOES_NOT_SET_LIVE_AUTHORIZED_VALUE,
        "STP_DOES_NOT_ISSUE_RUNTIME_PERMIT": STP_DOES_NOT_ISSUE_RUNTIME_PERMIT_VALUE,
        "STP_DOES_NOT_AUTHORIZE_NETWORK_SESSION": STP_DOES_NOT_AUTHORIZE_NETWORK_SESSION_VALUE,
        "STP_DOES_NOT_AUTHORIZE_AUTHENTICATED_PRODUCTIVE_TRANSPORT": (
            STP_DOES_NOT_AUTHORIZE_AUTHENTICATED_PRODUCTIVE_TRANSPORT_VALUE
        ),
        "FAIL_CLOSED_IF_MARKED_PROVEN_AT_SEND_FROM_OFFLINE_CODE_ALONE": (
            FAIL_CLOSED_IF_MARKED_PROVEN_AT_SEND_FROM_OFFLINE_CODE_ALONE_VALUE
        ),
        "RUNTIME_GET_REQUIRED": RUNTIME_GET_REQUIRED,
        "RUNTIME_GET_PERFORMED": RUNTIME_GET_PERFORMED,
        "PRIVATE_AUTH_USED": PRIVATE_AUTH_USED,
        "PUBLIC_SPEC_RETRIEVAL_PERFORMED": PUBLIC_SPEC_RETRIEVAL_PERFORMED,
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
