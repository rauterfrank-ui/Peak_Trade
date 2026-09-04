"""Offline remaining execution-path census adjudication. No GET. No POST."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.bounded_activation_permit_v1 import (
    offline_contract_proof_bounded_activation_permit_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.bounded_runtime_permit_issuance_v1 import (
    NAMED_REMAINING_AFTER_BOUNDED_RUNTIME_PERMIT_ISSUANCE,
    REASON_FLATTEN_EXECUTE,
    REASON_GET,
    REASON_IMPLEMENTATION_GO_AS_EXECUTE,
    REASON_IMPLEMENTATION_GO_AS_PERMIT,
    REASON_LIVE_AUTHORIZED_SUBSTITUTE,
    REASON_MISSING_REMAINING,
    REASON_MISSING_STPR,
    REASON_NETWORK_SESSION,
    REASON_POST,
    REASON_REMAINING_MISMATCH,
    REASON_RUNTIME_ISSUANCE_CLAIM,
    REASON_STPR_NOT_PASS,
    evaluate_bounded_runtime_permit_issuance_v1,
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
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.remaining_execution_path_census_v1 import (
    TERMINAL_EXECUTION_ENDPOINT,
    assert_census_exhaustion_v1,
    remaining_execution_path_census_summary_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.send_time_position_reobservation_v1 import (
    NAMED_REMAINING_AFTER_SEND_TIME_POSITION_REOBSERVATION,
)
from src.ops.section_11_13_5_remaining_execution_path_end_to_end_census_v1.constants_v1 import (
    APT_CLOSED,
    APT_TEXT_REWRITTEN_VALUE,
    BOUNDED_RUNTIME_PERMIT_ISSUANCE,
    BRPI_NAMED_CONTRACT_CLOSED,
    BRPI_RUNTIME_PROVEN_VALUE,
    CASE_VALUE,
    CENSUS_COMPLETE_VALUE,
    CENSUS_DOES_NOT_AUTHORIZE_FLATTEN_VALUE,
    CENSUS_DOES_NOT_AUTHORIZE_GET_VALUE,
    CENSUS_DOES_NOT_AUTHORIZE_NETWORK_SESSION_VALUE,
    CENSUS_DOES_NOT_AUTHORIZE_POST_VALUE,
    CENSUS_DOES_NOT_GRANT_EXECUTION_READINESS_VALUE,
    CENSUS_DOES_NOT_ISSUE_RUNTIME_PERMIT_VALUE,
    CENSUS_DOES_NOT_SET_LIVE_AUTHORIZED_VALUE,
    CENSUS_EXHAUSTION_PROVEN_VALUE,
    CENSUS_RUNTIME_RESIDUAL,
    CONFLICT_COUNT,
    CREDENTIAL_USE_PROVEN_VALUE,
    EARLIEST_UNRESOLVED_DEPENDENCY,
    EXPECTED_ORIGIN_MAIN_SHA,
    EXTERNAL_STATE_GAPS_REMAINING,
    FAIL_CLOSED_IF_MARKED_RUNTIME_PROVEN_FROM_OFFLINE_CODE_ALONE_VALUE,
    FLATTEN_EXECUTE,
    FLATTEN_EXECUTE_AUTHORIZED_VALUE,
    FLATTEN_EXECUTE_NAMED_CLOSED,
    LAST_CANONICALLY_CLOSED_STEP,
    LATENT_GAP_CENSUS_COMPLETE_VALUE,
    LATENT_OFFLINE_GAPS_BEFORE_WORK,
    LATENT_OFFLINE_GAPS_CLOSED,
    LATENT_OFFLINE_GAPS_REMAINING,
    MINIMUM_ADDITIONAL_OWNER_GO_COUNT,
    NAMED_REMAINING_HIGHER_AUTHORITY,
    NETWORK_PROVEN_VALUE,
    NETWORK_SESSION,
    NETWORK_SESSION_AUTHORIZED_VALUE,
    NETWORK_SESSION_NAMED_CLOSED,
    NEXT_AUTHORITY_BOUNDARY,
    NEXT_OWNER_GO_REQUIRED,
    NEXT_WORKPACKAGE,
    OWNER_DECISIONS_REMAINING,
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
    PUBLIC_SPEC_RETRIEVAL_PERFORMED,
    REMAINING_EXECUTION_PATH_CENSUS,
    RUNTIME_GAPS_REMAINING,
    RUNTIME_GET_PERFORMED,
    RUNTIME_GET_REQUIRED,
    RUNTIME_PERMIT_ISSUED_VALUE,
    START_NODE_VALUE,
    STP_CLOSED,
    STP_TEXT_REWRITTEN_VALUE,
    STPR_CLOSED,
    STPR_TEXT_REWRITTEN_VALUE,
    TARGET_INSTRUMENT_ID,
    TERMINAL_EXECUTION_ENDPOINT_VALUE,
    THIS_SLICE,
    TOTAL_EDGE_COUNT,
    TOTAL_KNOWN_GAP_COUNT,
    TOTAL_REMAINING_NODE_COUNT,
    WORKPACKAGE_COUNT,
    WORKPACKAGE_ID,
)
from src.ops.section_11_13_5_remaining_execution_path_end_to_end_census_v1.lineage_v1 import (
    lineage_census_summary_v1,
    remaining_execution_path_census_lineage_v1,
)
from src.ops.section_11_13_5_send_time_position_reobservation_v1.contract_v1 import (
    SEND_TIME_POSITION_REOBSERVATION_STATUS,
)

QUOTE_TS = "1787145055768"
EVAL_TS = "1787145056000"
DECISION_ID = "census-offline-contract-decision"
WINDOW_EARLIER_THAN_CENSUS = {
    "EXECUTION_PREREQUISITE_08_TARGET_POSITION_NONZERO_PROVEN",
    "EXECUTION_PREREQUISITE_09_TARGET_POSITION_QTY_NUMERIC",
    "EXECUTION_PREREQUISITE_16_BOUNDED_ACTIVATION_WITHOUT_GLOBAL_LIVE_AUTHORIZED",
    "EXECUTION_PREREQUISITE_20_MUTATION_LIMITED_TO_PROVEN_POSITION",
    "EXECUTION_PREREQUISITE_25_NO_ADDITIONAL_OWNER_DECISION_REQUIRED",
    "SEND_TIME_PASS_18_19_21_24",
    "AUTHENTICATED_PRODUCTIVE_TRANSPORT",
    "SEND_TIME_POSITION_REOBSERVATION",
    "BOUNDED_RUNTIME_PERMIT_ISSUANCE",
}


class RemainingExecutionPathCensusAdjudicationError(RuntimeError):
    """Fail-closed remaining execution-path census adjudication violation."""


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
        "stpr_status": SEND_TIME_POSITION_REOBSERVATION_STATUS,
        "claimed_remaining_after_census": NAMED_REMAINING_AFTER_BOUNDED_RUNTIME_PERMIT_ISSUANCE,
        "runtime_permit_issuance_claim": False,
        "flatten_execute_authorized_claim": False,
        "network_session_authorized_claim": False,
        "post_performed_claim": False,
        "get_performed_claim": False,
        "live_authorized_claim": False,
        "flatten_execute_owner_go": None,
        "permit_owner_go": None,
        "origin_main_sha": EXPECTED_ORIGIN_MAIN_SHA,
        "instrument_id": TARGET_INSTRUMENT_ID,
        "evaluation_monotonic_ms": 0,
    }
    payload.update(overrides)
    return evaluate_bounded_runtime_permit_issuance_v1(**payload)


def _assert_network_session_never_set_true() -> None:
    transport_path = (
        Path(__file__).resolve().parents[1]
        / "section_11_13_5_live_canary_minimum_exposure_v1"
        / "flatten_productive_transport_v1.py"
    )
    text = transport_path.read_text(encoding="utf-8")
    if "network_session_authorized: bool = False" not in text:
        raise RemainingExecutionPathCensusAdjudicationError("NETWORK_SESSION_DEFAULT_NOT_FALSE")
    if "never sets" not in text.lower() and "never set" not in text.lower():
        raise RemainingExecutionPathCensusAdjudicationError(
            "NETWORK_SESSION_NEVER_SET_TRUE_DOC_MISSING"
        )
    if "network_session_authorized = True" in text or "network_session_authorized=True" in text:
        raise RemainingExecutionPathCensusAdjudicationError("NETWORK_SESSION_SET_TRUE_IN_MODULE")


def adjudicate_remaining_execution_path_end_to_end_census_v1(
    *,
    origin_main_sha: str,
) -> dict[str, Any]:
    bound_sha = str(origin_main_sha or "").strip()
    if bound_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise RemainingExecutionPathCensusAdjudicationError("ORIGIN_MAIN_SHA_MISMATCH")
    if LIVE_AUTHORIZED is not False or LIVE_ENABLED is not False or LIVE_ARMED is not False:
        raise RemainingExecutionPathCensusAdjudicationError("STANDING_LIVE_FLAGS_UNLOCKED")
    if OWNER_GO not in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS:
        raise RemainingExecutionPathCensusAdjudicationError(
            "IMPLEMENTATION_GO_MUST_BE_FORBIDDEN_EXECUTE"
        )
    execute_ok, _execute_reasons = evaluate_flatten_execute_authority_v1(
        token=FLATTEN_EXECUTE_CONFIRM_TOKEN_CANONICAL,
        purpose=FLATTEN_EXECUTE_PURPOSE_CANONICAL,
        owner_go=OWNER_GO,
    )
    if execute_ok:
        raise RemainingExecutionPathCensusAdjudicationError(
            "IMPLEMENTATION_GO_ACCEPTED_AS_FLATTEN_EXECUTE"
        )
    frozen = set(NAMED_REMAINING_AFTER_SEND_TIME_POSITION_REOBSERVATION)
    if frozen != {"BOUNDED_RUNTIME_PERMIT_ISSUANCE", "FLATTEN_EXECUTE", "NETWORK_SESSION"}:
        raise RemainingExecutionPathCensusAdjudicationError("STPR_NAMED_REMAINING_REWRITTEN")
    if SEND_TIME_POSITION_REOBSERVATION_STATUS != PASS_OFFLINE_CONTRACT:
        raise RemainingExecutionPathCensusAdjudicationError("STPR_STATUS_DRIFT")
    missing_stpr_ok, missing_stpr = _eval(stpr_status=None)
    if missing_stpr_ok or REASON_MISSING_STPR not in missing_stpr:
        raise RemainingExecutionPathCensusAdjudicationError("MISSING_STPR_MUST_DENY")
    unproven_stpr_ok, unproven_stpr = _eval(stpr_status="UNPROVEN")
    if unproven_stpr_ok or REASON_STPR_NOT_PASS not in unproven_stpr:
        raise RemainingExecutionPathCensusAdjudicationError("UNPROVEN_STPR_MUST_DENY")
    missing_remaining_ok, missing_remaining = _eval(claimed_remaining_after_census=None)
    if missing_remaining_ok or REASON_MISSING_REMAINING not in missing_remaining:
        raise RemainingExecutionPathCensusAdjudicationError("MISSING_REMAINING_MUST_DENY")
    mismatch_ok, mismatch = _eval(claimed_remaining_after_census=("FLATTEN_EXECUTE",))
    if mismatch_ok or REASON_REMAINING_MISMATCH not in mismatch:
        raise RemainingExecutionPathCensusAdjudicationError("REMAINING_MISMATCH_MUST_DENY")
    runtime_ok, runtime_reasons = _eval(runtime_permit_issuance_claim=True)
    if runtime_ok or REASON_RUNTIME_ISSUANCE_CLAIM not in runtime_reasons:
        raise RemainingExecutionPathCensusAdjudicationError("RUNTIME_ISSUANCE_CLAIM_MUST_DENY")
    flatten_ok, flatten_reasons = _eval(flatten_execute_authorized_claim=True)
    if flatten_ok or REASON_FLATTEN_EXECUTE not in flatten_reasons:
        raise RemainingExecutionPathCensusAdjudicationError("FLATTEN_EXECUTE_CLAIM_MUST_DENY")
    network_ok, network_reasons = _eval(network_session_authorized_claim=True)
    if network_ok or REASON_NETWORK_SESSION not in network_reasons:
        raise RemainingExecutionPathCensusAdjudicationError("NETWORK_SESSION_CLAIM_MUST_DENY")
    post_ok, post_reasons = _eval(post_performed_claim=True)
    if post_ok or REASON_POST not in post_reasons:
        raise RemainingExecutionPathCensusAdjudicationError("POST_CLAIM_MUST_DENY")
    get_ok, get_reasons = _eval(get_performed_claim=True)
    if get_ok or REASON_GET not in get_reasons:
        raise RemainingExecutionPathCensusAdjudicationError("GET_CLAIM_MUST_DENY")
    live_ok, live_reasons = _eval(live_authorized_claim=True)
    if live_ok or REASON_LIVE_AUTHORIZED_SUBSTITUTE not in live_reasons:
        raise RemainingExecutionPathCensusAdjudicationError("LIVE_AUTHORIZED_SUBSTITUTE_MUST_DENY")
    go_ok, go_reasons = _eval(flatten_execute_owner_go=OWNER_GO)
    if go_ok or REASON_IMPLEMENTATION_GO_AS_EXECUTE not in go_reasons:
        raise RemainingExecutionPathCensusAdjudicationError(
            "IMPLEMENTATION_GO_AS_EXECUTE_MUST_DENY"
        )
    permit_go_ok, permit_go_reasons = _eval(permit_owner_go=OWNER_GO)
    if permit_go_ok or REASON_IMPLEMENTATION_GO_AS_PERMIT not in permit_go_reasons:
        raise RemainingExecutionPathCensusAdjudicationError("IMPLEMENTATION_GO_AS_PERMIT_MUST_DENY")
    matching_ok, matching_reasons = _eval()
    if matching_ok is not True or matching_reasons:
        raise RemainingExecutionPathCensusAdjudicationError(
            f"MATCHING_CONTRACT_MUST_PASS:{matching_reasons}"
        )
    _assert_network_session_never_set_true()
    execute_as_census = evaluate_flatten_pre_send_gate_v1(_gate(flatten_execute_owner_go=OWNER_GO))
    if execute_as_census.allowed is True:
        raise RemainingExecutionPathCensusAdjudicationError("CENSUS_GO_AS_EXECUTE_GATE_MUST_DENY")
    reachable = evaluate_flatten_pre_send_gate_v1(_gate())
    if reachable.allowed is not True:
        raise RemainingExecutionPathCensusAdjudicationError(
            f"BOUNDED_PATH_NOT_STRUCTURALLY_REACHABLE:{reachable.reasons}"
        )
    brpi_pass = [
        item for item in reachable.audit_decisions if item[0] == "BOUNDED_RUNTIME_PERMIT_ISSUANCE"
    ]
    if not brpi_pass or brpi_pass[0][1] != "PASS":
        raise RemainingExecutionPathCensusAdjudicationError("MATCHING_FIXTURE_BRPI_GATE_MUST_PASS")
    assert_census_exhaustion_v1()
    dag = remaining_execution_path_census_summary_v1()
    if int(dag["TOTAL_REMAINING_NODE_COUNT"]) != TOTAL_REMAINING_NODE_COUNT:
        raise RemainingExecutionPathCensusAdjudicationError("CENSUS_NODE_COUNT_DRIFT")
    if int(dag["TOTAL_EDGE_COUNT"]) != TOTAL_EDGE_COUNT:
        raise RemainingExecutionPathCensusAdjudicationError("CENSUS_EDGE_COUNT_DRIFT")
    if int(dag["TOTAL_KNOWN_GAP_COUNT"]) != TOTAL_KNOWN_GAP_COUNT:
        raise RemainingExecutionPathCensusAdjudicationError("CENSUS_GAP_COUNT_DRIFT")
    if str(dag["TERMINAL_EXECUTION_ENDPOINT"]) != TERMINAL_EXECUTION_ENDPOINT:
        raise RemainingExecutionPathCensusAdjudicationError("TERMINAL_ENDPOINT_DRIFT")
    if int(dag["LATENT_OFFLINE_GAPS_CLOSED"]) != LATENT_OFFLINE_GAPS_CLOSED:
        raise RemainingExecutionPathCensusAdjudicationError("LATENT_OFFLINE_CLOSED_DRIFT")
    window = adjudicate_prerequisite_08_window_v1(positions_payload=_positions())
    window_earliest = str(window.get("EARLIEST_UNRESOLVED_DEPENDENCY") or "")
    if window_earliest in WINDOW_EARLIER_THAN_CENSUS:
        raise RemainingExecutionPathCensusAdjudicationError("WINDOW_EARLIEST_DEPENDENCY_DRIFT")
    if window_earliest != EARLIEST_UNRESOLVED_DEPENDENCY:
        raise RemainingExecutionPathCensusAdjudicationError("WINDOW_EARLIEST_DEPENDENCY_DRIFT")
    lineage = remaining_execution_path_census_lineage_v1()
    census = lineage_census_summary_v1()
    if int(census["SEAM_COUNT"]) != len(lineage):
        raise RemainingExecutionPathCensusAdjudicationError("LINEAGE_CENSUS_DRIFT")
    return {
        "OWNER_GO": OWNER_GO,
        "PRIOR_OWNER_GO": PRIOR_OWNER_GO,
        "THIS_SLICE": THIS_SLICE,
        "PREDECESSOR_SLICE": PREDECESSOR_SLICE,
        "WORKPACKAGE_ID": WORKPACKAGE_ID,
        "BOUND_ORIGIN_MAIN_SHA": bound_sha,
        "TARGET_INSTRUMENT_ID": TARGET_INSTRUMENT_ID,
        "CASE": CASE_VALUE,
        "REMAINING_EXECUTION_PATH_CENSUS": REMAINING_EXECUTION_PATH_CENSUS,
        "REMAINING_EXECUTION_PATH_CENSUS_COMPLETE": CENSUS_COMPLETE_VALUE,
        "CENSUS_EXHAUSTION_PROVEN": CENSUS_EXHAUSTION_PROVEN_VALUE,
        "LATENT_GAP_CENSUS_COMPLETE": LATENT_GAP_CENSUS_COMPLETE_VALUE,
        "BOUNDED_RUNTIME_PERMIT_ISSUANCE": BOUNDED_RUNTIME_PERMIT_ISSUANCE,
        "BOUNDED_RUNTIME_PERMIT_ISSUANCE_OFFLINE_CONTRACT": BOUNDED_RUNTIME_PERMIT_ISSUANCE,
        "BOUNDED_RUNTIME_PERMIT_ISSUANCE_RUNTIME_PROVEN": BRPI_RUNTIME_PROVEN_VALUE,
        "BRPI_NAMED_ISSUANCE_CONTRACT_CLOSED": BRPI_NAMED_CONTRACT_CLOSED,
        "FLATTEN_EXECUTE": FLATTEN_EXECUTE,
        "FLATTEN_EXECUTE_OFFLINE_CONTRACT": FLATTEN_EXECUTE,
        "FLATTEN_EXECUTE_AUTHORIZED": FLATTEN_EXECUTE_AUTHORIZED_VALUE,
        "FLATTEN_EXECUTE_NAMED_CONTRACT_CLOSED": FLATTEN_EXECUTE_NAMED_CLOSED,
        "NETWORK_SESSION": NETWORK_SESSION,
        "NETWORK_SESSION_OFFLINE_CONTRACT": NETWORK_SESSION,
        "NETWORK_SESSION_AUTHORIZED": NETWORK_SESSION_AUTHORIZED_VALUE,
        "NETWORK_SESSION_NAMED_CONTRACT_CLOSED": NETWORK_SESSION_NAMED_CLOSED,
        "START_NODE": START_NODE_VALUE,
        "TERMINAL_EXECUTION_ENDPOINT": TERMINAL_EXECUTION_ENDPOINT_VALUE,
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
        "STPR_CLOSED": STPR_CLOSED,
        "STPR_TEXT_REWRITTEN": STPR_TEXT_REWRITTEN_VALUE,
        "APT_TEXT_REWRITTEN": APT_TEXT_REWRITTEN_VALUE,
        "STP_TEXT_REWRITTEN": STP_TEXT_REWRITTEN_VALUE,
        "P16_TEXT_REWRITTEN": P16_TEXT_REWRITTEN_VALUE,
        "P20_TEXT_REWRITTEN": P20_TEXT_REWRITTEN_VALUE,
        "P25_TEXT_REWRITTEN": P25_TEXT_REWRITTEN_VALUE,
        "LAST_CANONICALLY_CLOSED_STEP": LAST_CANONICALLY_CLOSED_STEP,
        "EARLIEST_UNRESOLVED_DEPENDENCY": EARLIEST_UNRESOLVED_DEPENDENCY,
        "NEXT_AUTHORITY_BOUNDARY": NEXT_AUTHORITY_BOUNDARY,
        "CENSUS_RUNTIME_RESIDUAL": CENSUS_RUNTIME_RESIDUAL,
        "NEXT_WORKPACKAGE": NEXT_WORKPACKAGE,
        "NEXT_OWNER_GO_REQUIRED": NEXT_OWNER_GO_REQUIRED,
        "WORKPACKAGE_COUNT": WORKPACKAGE_COUNT,
        "MINIMUM_ADDITIONAL_OWNER_GO_COUNT": MINIMUM_ADDITIONAL_OWNER_GO_COUNT,
        "TOTAL_REMAINING_NODE_COUNT": TOTAL_REMAINING_NODE_COUNT,
        "TOTAL_EDGE_COUNT": TOTAL_EDGE_COUNT,
        "TOTAL_KNOWN_GAP_COUNT": TOTAL_KNOWN_GAP_COUNT,
        "LATENT_OFFLINE_GAPS_BEFORE_WORK": LATENT_OFFLINE_GAPS_BEFORE_WORK,
        "LATENT_OFFLINE_GAPS_CLOSED": LATENT_OFFLINE_GAPS_CLOSED,
        "LATENT_OFFLINE_GAPS_REMAINING": LATENT_OFFLINE_GAPS_REMAINING,
        "RUNTIME_GAPS_REMAINING": RUNTIME_GAPS_REMAINING,
        "EXTERNAL_STATE_GAPS_REMAINING": EXTERNAL_STATE_GAPS_REMAINING,
        "OWNER_DECISIONS_REMAINING": OWNER_DECISIONS_REMAINING,
        "THIS_GO_GET_COUNT": 0,
        "THIS_GO_POST_COUNT": 0,
        "GET_PERFORMED_THIS_PERSIST": False,
        "POST_PERFORMED": False,
        "RUNTIME_GET_REQUIRED": RUNTIME_GET_REQUIRED,
        "RUNTIME_GET_PERFORMED": RUNTIME_GET_PERFORMED,
        "PRIVATE_AUTH_USED": PRIVATE_AUTH_USED,
        "PUBLIC_SPEC_RETRIEVAL_PERFORMED": PUBLIC_SPEC_RETRIEVAL_PERFORMED,
        "POSITION_GET_REQUIRED_THIS_PERSIST": POSITION_GET_REQUIRED_THIS_PERSIST_VALUE,
        "POSITION_GET_AUTHORIZED_BY_THIS_OWNER_GO": POSITION_GET_AUTHORIZED_BY_THIS_OWNER_GO_VALUE,
        "CENSUS_DOES_NOT_GRANT_EXECUTION_READINESS": CENSUS_DOES_NOT_GRANT_EXECUTION_READINESS_VALUE,
        "CENSUS_DOES_NOT_AUTHORIZE_FLATTEN": CENSUS_DOES_NOT_AUTHORIZE_FLATTEN_VALUE,
        "CENSUS_DOES_NOT_SET_LIVE_AUTHORIZED": CENSUS_DOES_NOT_SET_LIVE_AUTHORIZED_VALUE,
        "CENSUS_DOES_NOT_ISSUE_RUNTIME_PERMIT": CENSUS_DOES_NOT_ISSUE_RUNTIME_PERMIT_VALUE,
        "CENSUS_DOES_NOT_AUTHORIZE_NETWORK_SESSION": (
            CENSUS_DOES_NOT_AUTHORIZE_NETWORK_SESSION_VALUE
        ),
        "CENSUS_DOES_NOT_AUTHORIZE_GET": CENSUS_DOES_NOT_AUTHORIZE_GET_VALUE,
        "CENSUS_DOES_NOT_AUTHORIZE_POST": CENSUS_DOES_NOT_AUTHORIZE_POST_VALUE,
        "FAIL_CLOSED_IF_MARKED_RUNTIME_PROVEN_FROM_OFFLINE_CODE_ALONE": (
            FAIL_CLOSED_IF_MARKED_RUNTIME_PROVEN_FROM_OFFLINE_CODE_ALONE_VALUE
        ),
        "NETWORK_PROVEN": NETWORK_PROVEN_VALUE,
        "CREDENTIAL_USE_PROVEN": CREDENTIAL_USE_PROVEN_VALUE,
        "PRIVATE_GET_PROVEN": PRIVATE_GET_PROVEN_VALUE,
        "POST_PROVEN": POST_PROVEN_VALUE,
        "RUNTIME_PERMIT_ISSUED": RUNTIME_PERMIT_ISSUED_VALUE,
        "LIVE_EXECUTION": False,
        "CANARY_EXECUTION": False,
        "MERGE_AUTHORIZED_BY_THIS_PERSIST": False,
        "NETWORK_SESSION_AUTHORIZED_DEFAULT": False,
        "IMPLEMENTATION_GO_FORBIDDEN_AS_FLATTEN_EXECUTE": True,
        "CENSUS": census,
        "LINEAGE": lineage,
        "DAG": dag,
        "WINDOW_EARLIEST_UNRESOLVED_DEPENDENCY": window.get("EARLIEST_UNRESOLVED_DEPENDENCY"),
    }
