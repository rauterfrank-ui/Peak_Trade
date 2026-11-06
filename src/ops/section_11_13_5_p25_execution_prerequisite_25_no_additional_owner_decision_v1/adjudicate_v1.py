"""Offline EXECUTION_PREREQUISITE_25 adjudication. No GET. No POST."""

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
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.no_additional_owner_decision_required_v1 import (
    NAMED_REMAINING_HIGHER_AUTHORITY_BOUNDARIES,
    PASS_OFFLINE_CONTRACT,
    REASON_ADDITIONAL_PRESENT,
    REASON_FLATTEN_EXECUTE,
    REASON_GET,
    REASON_IMPLEMENTATION_GO_AS_EXECUTE,
    REASON_INSTRUMENT_MISMATCH,
    REASON_LINEAGE_MISMATCH,
    REASON_LIVE_AUTHORIZED_SUBSTITUTE,
    REASON_MISSING_P16,
    REASON_MISSING_P20,
    REASON_MISSING_REMAINING,
    REASON_NETWORK_SESSION,
    REASON_P16_NOT_PASS,
    REASON_P20_NOT_PASS,
    REASON_POST,
    REASON_REMAINING_MISMATCH,
    REASON_RUNTIME_PERMIT,
    evaluate_no_additional_owner_decision_required_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.position_observation_freshness_contract_v1 import (
    PRE_SEND_EVIDENCE_KIND,
    PositionObservationFreshnessEvidenceV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.prerequisite_08_fresh_position_observation_v1 import (
    adjudicate_prerequisite_08_window_v1,
)
from src.ops.section_11_13_5_p16_execution_prerequisite_16_bounded_activation_v1.contract_v1 import (
    EXECUTION_PREREQUISITE_16_STATUS,
)
from src.ops.section_11_13_5_p20_execution_prerequisite_20_mutation_limited_to_proven_position_v1.contract_v1 import (
    EXECUTION_PREREQUISITE_20_STATUS,
)
from src.ops.section_11_13_5_p25_execution_prerequisite_25_no_additional_owner_decision_v1.constants_v1 import (
    CASE_VALUE,
    CONFLICT_COUNT,
    EARLIEST_UNRESOLVED_DEPENDENCY,
    EXECUTION_PREREQUISITE_25_NO_ADDITIONAL_OWNER_DECISION_REQUIRED,
    EXPECTED_ORIGIN_MAIN_SHA,
    FAIL_CLOSED_IF_MARKED_PROVEN_FROM_OFFLINE_CODE_ALONE,
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
    P25_DOES_NOT_AUTHORIZE_FLATTEN_VALUE,
    P25_DOES_NOT_AUTHORIZE_NETWORK_SESSION_VALUE,
    P25_DOES_NOT_AUTHORIZE_SEND_TIME_PASS_VALUE,
    P25_DOES_NOT_GRANT_EXECUTION_READINESS_VALUE,
    P25_DOES_NOT_ISSUE_RUNTIME_PERMIT_VALUE,
    P25_DOES_NOT_SET_LIVE_AUTHORIZED_VALUE,
    P25_MECHANISM_IMPLEMENTED,
    P25_NAMED_CONTRACT_CLOSED,
    P25_RUNTIME_RESIDUAL,
    PREDECESSOR_SLICE,
    PRIOR_OWNER_GO,
    PREREQUISITE_25_FLATTEN_EXECUTE_AUTHORIZED_VALUE,
    PREREQUISITE_25_NETWORK_SESSION_AUTHORIZED_VALUE,
    PREREQUISITE_25_SEND_TIME_REOBSERVATION_PROVEN_VALUE,
    PRIVATE_AUTH_USED,
    PUBLIC_SPEC_RETRIEVAL_PERFORMED,
    RUNTIME_GET_PERFORMED,
    RUNTIME_GET_REQUIRED,
    TARGET_INSTRUMENT_ID,
    THIS_SLICE,
    WORKPACKAGE_ID,
)
from src.ops.section_11_13_5_p25_execution_prerequisite_25_no_additional_owner_decision_v1.lineage_v1 import (
    lineage_census_summary_v1,
    no_additional_owner_decision_lineage_v1,
)

QUOTE_TS = "1787145055768"
EVAL_TS = "1787145056000"
DECISION_ID = "p25-offline-contract-decision"
WRONG_INSTRUMENT_ID = "BTC-USD_UM_XPERP-000000"
WINDOW_EARLIER_THAN_P25 = {
    "EXECUTION_PREREQUISITE_08_TARGET_POSITION_NONZERO_PROVEN",
    "EXECUTION_PREREQUISITE_09_TARGET_POSITION_QTY_NUMERIC",
    "EXECUTION_PREREQUISITE_16_BOUNDED_ACTIVATION_WITHOUT_GLOBAL_LIVE_AUTHORIZED",
    "EXECUTION_PREREQUISITE_20_MUTATION_LIMITED_TO_PROVEN_POSITION",
    "EXECUTION_PREREQUISITE_25_NO_ADDITIONAL_OWNER_DECISION_REQUIRED",
}


class P25NoAdditionalOwnerDecisionAdjudicationError(RuntimeError):
    """Fail-closed EXECUTION_PREREQUISITE_25 adjudication violation."""


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
        "p16_status": EXECUTION_PREREQUISITE_16_STATUS,
        "p20_status": EXECUTION_PREREQUISITE_20_STATUS,
        "additional_owner_decisions": (),
        "claimed_remaining_higher_authority": NAMED_REMAINING_HIGHER_AUTHORITY_BOUNDARIES,
        "live_authorized_claim": False,
        "runtime_permit_issuance_claim": False,
        "flatten_execute_authorized_claim": False,
        "network_session_authorized_claim": False,
        "post_performed_claim": False,
        "get_performed_claim": False,
        "flatten_execute_owner_go": None,
        "instrument_id": TARGET_INSTRUMENT_ID,
        "expected_instrument_id": TARGET_INSTRUMENT_ID,
        "predecessor_lineage_ok": True,
    }
    payload.update(overrides)
    return evaluate_no_additional_owner_decision_required_v1(**payload)


def adjudicate_execution_prerequisite_25_no_additional_owner_decision_v1(
    *,
    origin_main_sha: str,
) -> dict[str, Any]:
    bound_sha = str(origin_main_sha or "").strip()
    if bound_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise P25NoAdditionalOwnerDecisionAdjudicationError("ORIGIN_MAIN_SHA_MISMATCH")
    if LIVE_AUTHORIZED is not False or LIVE_ENABLED is not False or LIVE_ARMED is not False:
        raise P25NoAdditionalOwnerDecisionAdjudicationError("STANDING_LIVE_FLAGS_UNLOCKED")
    if OWNER_GO not in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS:
        raise P25NoAdditionalOwnerDecisionAdjudicationError(
            "IMPLEMENTATION_GO_MUST_BE_FORBIDDEN_EXECUTE"
        )
    execute_ok, _execute_reasons = evaluate_flatten_execute_authority_v1(
        token=FLATTEN_EXECUTE_CONFIRM_TOKEN_CANONICAL,
        purpose=FLATTEN_EXECUTE_PURPOSE_CANONICAL,
        owner_go=OWNER_GO,
    )
    if execute_ok:
        raise P25NoAdditionalOwnerDecisionAdjudicationError(
            "IMPLEMENTATION_GO_ACCEPTED_AS_FLATTEN_EXECUTE"
        )
    missing_p16_ok, missing_p16 = _eval(p16_status=None)
    if missing_p16_ok or REASON_MISSING_P16 not in missing_p16:
        raise P25NoAdditionalOwnerDecisionAdjudicationError("MISSING_P16_MUST_DENY")
    unproven_p16_ok, unproven_p16 = _eval(p16_status="UNPROVEN")
    if unproven_p16_ok or REASON_P16_NOT_PASS not in unproven_p16:
        raise P25NoAdditionalOwnerDecisionAdjudicationError("UNPROVEN_P16_MUST_DENY")
    missing_p20_ok, missing_p20 = _eval(p20_status=None)
    if missing_p20_ok or REASON_MISSING_P20 not in missing_p20:
        raise P25NoAdditionalOwnerDecisionAdjudicationError("MISSING_P20_MUST_DENY")
    unproven_p20_ok, unproven_p20 = _eval(p20_status="UNPROVEN")
    if unproven_p20_ok or REASON_P20_NOT_PASS not in unproven_p20:
        raise P25NoAdditionalOwnerDecisionAdjudicationError("UNPROVEN_P20_MUST_DENY")
    missing_remaining_ok, missing_remaining = _eval(claimed_remaining_higher_authority=None)
    if missing_remaining_ok or REASON_MISSING_REMAINING not in missing_remaining:
        raise P25NoAdditionalOwnerDecisionAdjudicationError("MISSING_REMAINING_MUST_DENY")
    additional_ok, additional = _eval(
        additional_owner_decisions=("INVENTED_OWNER_DECISION",),
    )
    if additional_ok or REASON_ADDITIONAL_PRESENT not in additional:
        raise P25NoAdditionalOwnerDecisionAdjudicationError("ADDITIONAL_DECISION_MUST_DENY")
    mismatch_ok, mismatch = _eval(
        claimed_remaining_higher_authority=("FLATTEN_EXECUTE",),
    )
    if mismatch_ok or REASON_REMAINING_MISMATCH not in mismatch:
        raise P25NoAdditionalOwnerDecisionAdjudicationError("REMAINING_MISMATCH_MUST_DENY")
    live_ok, live_reasons = _eval(live_authorized_claim=True)
    if live_ok or REASON_LIVE_AUTHORIZED_SUBSTITUTE not in live_reasons:
        raise P25NoAdditionalOwnerDecisionAdjudicationError("LIVE_AUTHORIZED_SUBSTITUTE_MUST_DENY")
    permit_ok, permit_reasons = _eval(runtime_permit_issuance_claim=True)
    if permit_ok or REASON_RUNTIME_PERMIT not in permit_reasons:
        raise P25NoAdditionalOwnerDecisionAdjudicationError("RUNTIME_PERMIT_MUST_DENY")
    flatten_ok, flatten_reasons = _eval(flatten_execute_authorized_claim=True)
    if flatten_ok or REASON_FLATTEN_EXECUTE not in flatten_reasons:
        raise P25NoAdditionalOwnerDecisionAdjudicationError("FLATTEN_EXECUTE_CLAIM_MUST_DENY")
    network_ok, network_reasons = _eval(network_session_authorized_claim=True)
    if network_ok or REASON_NETWORK_SESSION not in network_reasons:
        raise P25NoAdditionalOwnerDecisionAdjudicationError("NETWORK_SESSION_CLAIM_MUST_DENY")
    post_ok, post_reasons = _eval(post_performed_claim=True)
    if post_ok or REASON_POST not in post_reasons:
        raise P25NoAdditionalOwnerDecisionAdjudicationError("POST_CLAIM_MUST_DENY")
    get_ok, get_reasons = _eval(get_performed_claim=True)
    if get_ok or REASON_GET not in get_reasons:
        raise P25NoAdditionalOwnerDecisionAdjudicationError("GET_CLAIM_MUST_DENY")
    go_ok, go_reasons = _eval(flatten_execute_owner_go=OWNER_GO)
    if go_ok or REASON_IMPLEMENTATION_GO_AS_EXECUTE not in go_reasons:
        raise P25NoAdditionalOwnerDecisionAdjudicationError(
            "IMPLEMENTATION_GO_AS_EXECUTE_MUST_DENY"
        )
    inst_ok, inst_reasons = _eval(instrument_id=WRONG_INSTRUMENT_ID)
    if inst_ok or REASON_INSTRUMENT_MISMATCH not in inst_reasons:
        raise P25NoAdditionalOwnerDecisionAdjudicationError("WRONG_INSTRUMENT_MUST_DENY")
    lineage_ok, lineage_reasons = _eval(predecessor_lineage_ok=False)
    if lineage_ok or REASON_LINEAGE_MISMATCH not in lineage_reasons:
        raise P25NoAdditionalOwnerDecisionAdjudicationError("LINEAGE_MISMATCH_MUST_DENY")
    matching_ok, matching_reasons = _eval()
    if matching_ok is not True or matching_reasons:
        raise P25NoAdditionalOwnerDecisionAdjudicationError(
            f"MATCHING_CONTRACT_MUST_PASS:{matching_reasons}"
        )
    if EXECUTION_PREREQUISITE_16_STATUS != PASS_OFFLINE_CONTRACT:
        raise P25NoAdditionalOwnerDecisionAdjudicationError("P16_STATUS_DRIFT")
    if EXECUTION_PREREQUISITE_20_STATUS != PASS_OFFLINE_CONTRACT:
        raise P25NoAdditionalOwnerDecisionAdjudicationError("P20_STATUS_DRIFT")
    execute_as_p25 = evaluate_flatten_pre_send_gate_v1(_gate(flatten_execute_owner_go=OWNER_GO))
    if execute_as_p25.allowed is True:
        raise P25NoAdditionalOwnerDecisionAdjudicationError("P25_GO_AS_EXECUTE_GATE_MUST_DENY")
    p25_execute_deny = [
        item
        for item in execute_as_p25.audit_decisions
        if item[0] == "NO_ADDITIONAL_OWNER_DECISION_REQUIRED"
    ]
    if not p25_execute_deny or not str(p25_execute_deny[0][1]).startswith("DENY:"):
        raise P25NoAdditionalOwnerDecisionAdjudicationError("P25_GO_AS_EXECUTE_P25_GATE_MUST_DENY")
    reachable = evaluate_flatten_pre_send_gate_v1(_gate())
    if reachable.allowed is not True:
        raise P25NoAdditionalOwnerDecisionAdjudicationError(
            f"BOUNDED_PATH_NOT_STRUCTURALLY_REACHABLE:{reachable.reasons}"
        )
    p25_pass = [
        item
        for item in reachable.audit_decisions
        if item[0] == "NO_ADDITIONAL_OWNER_DECISION_REQUIRED"
    ]
    if not p25_pass or p25_pass[0][1] != "PASS":
        raise P25NoAdditionalOwnerDecisionAdjudicationError("MATCHING_FIXTURE_P25_GATE_MUST_PASS")
    transport = GatedProductiveFlattenTransportV1()
    if transport.network_session_authorized is not False:
        raise P25NoAdditionalOwnerDecisionAdjudicationError("NETWORK_SESSION_DEFAULT_NOT_FALSE")
    window = adjudicate_prerequisite_08_window_v1(positions_payload=_positions())
    window_earliest = str(window.get("EARLIEST_UNRESOLVED_DEPENDENCY") or "")
    if window_earliest in WINDOW_EARLIER_THAN_P25:
        raise P25NoAdditionalOwnerDecisionAdjudicationError("WINDOW_EARLIEST_DEPENDENCY_DRIFT")
    lineage = no_additional_owner_decision_lineage_v1()
    census = lineage_census_summary_v1()
    if int(census["SEAM_COUNT"]) != len(lineage):
        raise P25NoAdditionalOwnerDecisionAdjudicationError("LINEAGE_CENSUS_DRIFT")
    return {
        "OWNER_GO": OWNER_GO,
        "PRIOR_OWNER_GO": PRIOR_OWNER_GO,
        "THIS_SLICE": THIS_SLICE,
        "PREDECESSOR_SLICE": PREDECESSOR_SLICE,
        "WORKPACKAGE_ID": WORKPACKAGE_ID,
        "BOUND_ORIGIN_MAIN_SHA": bound_sha,
        "TARGET_INSTRUMENT_ID": TARGET_INSTRUMENT_ID,
        "CASE": CASE_VALUE,
        "EXECUTION_PREREQUISITE_25_NO_ADDITIONAL_OWNER_DECISION_REQUIRED": (
            EXECUTION_PREREQUISITE_25_NO_ADDITIONAL_OWNER_DECISION_REQUIRED
        ),
        "P25_NAMED_NO_ADDITIONAL_OWNER_DECISION_CONTRACT_CLOSED": P25_NAMED_CONTRACT_CLOSED,
        "P25_EXHAUSTION_GATE_IMPLEMENTED": P25_MECHANISM_IMPLEMENTED,
        "PREREQUISITE_25_SEND_TIME_REOBSERVATION_PROVEN": (
            PREREQUISITE_25_SEND_TIME_REOBSERVATION_PROVEN_VALUE
        ),
        "PREREQUISITE_25_NETWORK_SESSION_AUTHORIZED": (
            PREREQUISITE_25_NETWORK_SESSION_AUTHORIZED_VALUE
        ),
        "PREREQUISITE_25_FLATTEN_EXECUTE_AUTHORIZED": (
            PREREQUISITE_25_FLATTEN_EXECUTE_AUTHORIZED_VALUE
        ),
        "NAMED_REMAINING_HIGHER_AUTHORITY": list(NAMED_REMAINING_HIGHER_AUTHORITY),
        "ADDITIONAL_OWNER_DECISIONS": [],
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
        "P16_TEXT_REWRITTEN": P16_TEXT_REWRITTEN_VALUE,
        "P20_TEXT_REWRITTEN": P20_TEXT_REWRITTEN_VALUE,
        "LAST_CANONICALLY_CLOSED_STEP": LAST_CANONICALLY_CLOSED_STEP,
        "EARLIEST_UNRESOLVED_DEPENDENCY": EARLIEST_UNRESOLVED_DEPENDENCY,
        "NEXT_AUTHORITY_BOUNDARY": NEXT_AUTHORITY_BOUNDARY,
        "P25_RUNTIME_RESIDUAL": P25_RUNTIME_RESIDUAL,
        "P25_DOES_NOT_GRANT_EXECUTION_READINESS": P25_DOES_NOT_GRANT_EXECUTION_READINESS_VALUE,
        "P25_DOES_NOT_AUTHORIZE_FLATTEN": P25_DOES_NOT_AUTHORIZE_FLATTEN_VALUE,
        "P25_DOES_NOT_SET_LIVE_AUTHORIZED": P25_DOES_NOT_SET_LIVE_AUTHORIZED_VALUE,
        "P25_DOES_NOT_ISSUE_RUNTIME_PERMIT": P25_DOES_NOT_ISSUE_RUNTIME_PERMIT_VALUE,
        "P25_DOES_NOT_AUTHORIZE_NETWORK_SESSION": P25_DOES_NOT_AUTHORIZE_NETWORK_SESSION_VALUE,
        "P25_DOES_NOT_AUTHORIZE_SEND_TIME_PASS": P25_DOES_NOT_AUTHORIZE_SEND_TIME_PASS_VALUE,
        "FAIL_CLOSED_IF_PREREQUISITE_25_MARKED_PROVEN_FROM_OFFLINE_CODE_ALONE": (
            FAIL_CLOSED_IF_MARKED_PROVEN_FROM_OFFLINE_CODE_ALONE
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
        "MISSING_P16_DENIES": True,
        "UNPROVEN_P16_DENIES": True,
        "MISSING_P20_DENIES": True,
        "UNPROVEN_P20_DENIES": True,
        "ADDITIONAL_OWNER_DECISION_DENIES": True,
        "REMAINING_SET_MISMATCH_DENIES": True,
        "GLOBAL_LIVE_AUTHORIZED_SUBSTITUTE_DENIES": True,
        "RUNTIME_PERMIT_CLAIM_DENIES": True,
        "FLATTEN_EXECUTE_CLAIM_DENIES": True,
        "NETWORK_SESSION_CLAIM_DENIES": True,
        "POST_CLAIM_DENIES": True,
        "GET_CLAIM_DENIES": True,
        "IMPLEMENTATION_GO_AS_EXECUTE_DENIES": True,
        "WRONG_INSTRUMENT_DENIES": True,
        "LINEAGE_MISMATCH_DENIES": True,
        "LINEAGE": lineage,
        "CENSUS": census,
        "WINDOW_EARLIEST_UNRESOLVED_DEPENDENCY": window.get("EARLIEST_UNRESOLVED_DEPENDENCY"),
    }
