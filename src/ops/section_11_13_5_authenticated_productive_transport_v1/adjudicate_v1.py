"""Offline AUTHENTICATED_PRODUCTIVE_TRANSPORT adjudication. No GET. No POST."""

from __future__ import annotations

from typing import Any

from src.ops.section_11_13_5_authenticated_productive_transport_v1.constants_v1 import (
    APT_AUTHENTICATION_PROVEN_VALUE,
    APT_DOES_NOT_AUTHORIZE_FLATTEN_VALUE,
    APT_DOES_NOT_AUTHORIZE_NETWORK_SESSION_VALUE,
    APT_DOES_NOT_AUTHORIZE_SEND_TIME_POSITION_REOBSERVATION_VALUE,
    APT_DOES_NOT_GRANT_EXECUTION_READINESS_VALUE,
    APT_DOES_NOT_ISSUE_RUNTIME_PERMIT_VALUE,
    APT_DOES_NOT_SET_LIVE_AUTHORIZED_VALUE,
    APT_FLATTEN_EXECUTE_AUTHORIZED_VALUE,
    APT_MECHANISM_IMPLEMENTED,
    APT_NAMED_CONTRACT_CLOSED,
    APT_NETWORK_SESSION_AUTHORIZED_VALUE,
    APT_PRODUCTIVE_SIGNING_REUSE_WIRED_VALUE,
    APT_RUNTIME_PROVEN_VALUE,
    APT_RUNTIME_RESIDUAL,
    AUTHENTICATED_PRODUCTIVE_TRANSPORT,
    CASE_VALUE,
    CONFLICT_COUNT,
    CREDENTIAL_USE_PROVEN_VALUE,
    EARLIEST_UNRESOLVED_DEPENDENCY,
    EXPECTED_ORIGIN_MAIN_SHA,
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
    POST_PROVEN_VALUE,
    PREDECESSOR_SLICE,
    PRIOR_OWNER_GO,
    PRIVATE_AUTH_USED,
    PRIVATE_GET_PROVEN_VALUE,
    PRODUCTIVE_SIGNING_COMPONENT_VALUE,
    PUBLIC_SPEC_RETRIEVAL_PERFORMED,
    RUNTIME_GET_PERFORMED,
    RUNTIME_GET_REQUIRED,
    STP_CLOSED,
    STP_TEXT_REWRITTEN_VALUE,
    TARGET_INSTRUMENT_ID,
    THIS_SLICE,
    WORKPACKAGE_ID,
)
from src.ops.section_11_13_5_authenticated_productive_transport_v1.lineage_v1 import (
    authenticated_productive_transport_lineage_v1,
    lineage_census_summary_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.authenticated_productive_transport_v1 import (
    NAMED_REMAINING_AFTER_AUTHENTICATED_PRODUCTIVE_TRANSPORT,
    PRODUCTIVE_SIGNING_COMPONENT,
    REASON_CREDENTIAL_USE_CLAIM,
    REASON_DEDICATED_AUTH_TRANSPORT_REQUIRED,
    REASON_FLATTEN_EXECUTE,
    REASON_GET,
    REASON_HMAC_REORDERED_BEFORE_08,
    REASON_IMPLEMENTATION_GO_AS_EXECUTE,
    REASON_LINEAGE_MISMATCH,
    REASON_LIVE_AUTHORIZED_SUBSTITUTE,
    REASON_MISSING_REMAINING,
    REASON_MISSING_STP,
    REASON_NETWORK_PROVEN_CLAIM,
    REASON_NETWORK_SESSION,
    REASON_POST,
    REASON_POST_PROVEN_CLAIM,
    REASON_PRIVATE_GET_CLAIM,
    REASON_REMAINING_MISMATCH,
    REASON_RUNTIME_AUTH_CLAIM,
    REASON_RUNTIME_PERMIT,
    REASON_SIGNING_COMPONENT_MISMATCH,
    REASON_SIGNING_ONTOLOGY_INVENTED,
    REASON_STP_NOT_PASS,
    REASON_UNSIGNED_ACCEPTED,
    AuthenticatedGatedProductiveFlattenTransportV1,
    AuthenticatedProductiveTransportError,
    construct_okx_signing_input_v1,
    evaluate_authenticated_productive_transport_v1,
    sign_okx_signing_input_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.bounded_activation_permit_v1 import (
    offline_contract_proof_bounded_activation_permit_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    ENDPOINT_SUBMIT,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    REUSED_BINDING_REST_HOST,
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
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    LiveCanaryHttpRequestV1,
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
from src.ops.section_11_13_5_send_time_pass_18_19_21_24_v1.contract_v1 import (
    SEND_TIME_PASS_18_19_21_24_STATUS,
)

QUOTE_TS = "1787145055768"
EVAL_TS = "1787145056000"
DECISION_ID = "apt-offline-contract-decision"
FIXTURE_TIMESTAMP = "2026-09-04T03:17:00.000Z"
FIXTURE_SECRET = "apt-offline-fixture-secret-not-a-credential"
WINDOW_EARLIER_THAN_APT = {
    "EXECUTION_PREREQUISITE_08_TARGET_POSITION_NONZERO_PROVEN",
    "EXECUTION_PREREQUISITE_09_TARGET_POSITION_QTY_NUMERIC",
    "EXECUTION_PREREQUISITE_16_BOUNDED_ACTIVATION_WITHOUT_GLOBAL_LIVE_AUTHORIZED",
    "EXECUTION_PREREQUISITE_20_MUTATION_LIMITED_TO_PROVEN_POSITION",
    "EXECUTION_PREREQUISITE_25_NO_ADDITIONAL_OWNER_DECISION_REQUIRED",
    "SEND_TIME_PASS_18_19_21_24",
    "AUTHENTICATED_PRODUCTIVE_TRANSPORT",
}


class AuthenticatedProductiveTransportAdjudicationError(RuntimeError):
    """Fail-closed AUTHENTICATED_PRODUCTIVE_TRANSPORT adjudication violation."""


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
        "stp_status": SEND_TIME_PASS_18_19_21_24_STATUS,
        "dedicated_authenticated_transport": True,
        "signing_component": PRODUCTIVE_SIGNING_COMPONENT,
        "signing_ontology_invented": False,
        "hmac_handle_reordered_before_08": False,
        "unsigned_headers_accepted_as_authenticated": False,
        "claimed_remaining_after_authenticated_productive_transport": (
            NAMED_REMAINING_AFTER_AUTHENTICATED_PRODUCTIVE_TRANSPORT
        ),
        "runtime_authentication_proven_claim": False,
        "network_proven_claim": False,
        "credential_use_proven_claim": False,
        "private_get_proven_claim": False,
        "post_proven_claim": False,
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
    return evaluate_authenticated_productive_transport_v1(**payload)


def adjudicate_authenticated_productive_transport_v1(
    *,
    origin_main_sha: str,
) -> dict[str, Any]:
    bound_sha = str(origin_main_sha or "").strip()
    if bound_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise AuthenticatedProductiveTransportAdjudicationError("ORIGIN_MAIN_SHA_MISMATCH")
    if LIVE_AUTHORIZED is not False or LIVE_ENABLED is not False or LIVE_ARMED is not False:
        raise AuthenticatedProductiveTransportAdjudicationError("STANDING_LIVE_FLAGS_UNLOCKED")
    if OWNER_GO not in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS:
        raise AuthenticatedProductiveTransportAdjudicationError(
            "IMPLEMENTATION_GO_MUST_BE_FORBIDDEN_EXECUTE"
        )
    execute_ok, _execute_reasons = evaluate_flatten_execute_authority_v1(
        token=FLATTEN_EXECUTE_CONFIRM_TOKEN_CANONICAL,
        purpose=FLATTEN_EXECUTE_PURPOSE_CANONICAL,
        owner_go=OWNER_GO,
    )
    if execute_ok:
        raise AuthenticatedProductiveTransportAdjudicationError(
            "IMPLEMENTATION_GO_ACCEPTED_AS_FLATTEN_EXECUTE"
        )
    missing_stp_ok, missing_stp = _eval(stp_status=None)
    if missing_stp_ok or REASON_MISSING_STP not in missing_stp:
        raise AuthenticatedProductiveTransportAdjudicationError("MISSING_STP_MUST_DENY")
    unproven_stp_ok, unproven_stp = _eval(stp_status="UNPROVEN")
    if unproven_stp_ok or REASON_STP_NOT_PASS not in unproven_stp:
        raise AuthenticatedProductiveTransportAdjudicationError("UNPROVEN_STP_MUST_DENY")
    missing_remaining_ok, missing_remaining = _eval(
        claimed_remaining_after_authenticated_productive_transport=None
    )
    if missing_remaining_ok or REASON_MISSING_REMAINING not in missing_remaining:
        raise AuthenticatedProductiveTransportAdjudicationError("MISSING_REMAINING_MUST_DENY")
    mismatch_ok, mismatch = _eval(
        claimed_remaining_after_authenticated_productive_transport=("FLATTEN_EXECUTE",)
    )
    if mismatch_ok or REASON_REMAINING_MISMATCH not in mismatch:
        raise AuthenticatedProductiveTransportAdjudicationError("REMAINING_MISMATCH_MUST_DENY")
    transport_ok, transport_reasons = _eval(dedicated_authenticated_transport=False)
    if transport_ok or REASON_DEDICATED_AUTH_TRANSPORT_REQUIRED not in transport_reasons:
        raise AuthenticatedProductiveTransportAdjudicationError(
            "DEDICATED_AUTH_TRANSPORT_MUST_DENY"
        )
    signer_ok, signer_reasons = _eval(signing_component="invented-signer")
    if signer_ok or REASON_SIGNING_COMPONENT_MISMATCH not in signer_reasons:
        raise AuthenticatedProductiveTransportAdjudicationError("SIGNING_COMPONENT_MUST_DENY")
    ontology_ok, ontology_reasons = _eval(signing_ontology_invented=True)
    if ontology_ok or REASON_SIGNING_ONTOLOGY_INVENTED not in ontology_reasons:
        raise AuthenticatedProductiveTransportAdjudicationError("SIGNING_ONTOLOGY_MUST_DENY")
    reorder_ok, reorder_reasons = _eval(hmac_handle_reordered_before_08=True)
    if reorder_ok or REASON_HMAC_REORDERED_BEFORE_08 not in reorder_reasons:
        raise AuthenticatedProductiveTransportAdjudicationError("HMAC_REORDER_MUST_DENY")
    unsigned_ok, unsigned_reasons = _eval(unsigned_headers_accepted_as_authenticated=True)
    if unsigned_ok or REASON_UNSIGNED_ACCEPTED not in unsigned_reasons:
        raise AuthenticatedProductiveTransportAdjudicationError("UNSIGNED_ACCEPTED_MUST_DENY")
    runtime_ok, runtime_reasons = _eval(runtime_authentication_proven_claim=True)
    if runtime_ok or REASON_RUNTIME_AUTH_CLAIM not in runtime_reasons:
        raise AuthenticatedProductiveTransportAdjudicationError("RUNTIME_AUTH_CLAIM_MUST_DENY")
    network_proven_ok, network_proven_reasons = _eval(network_proven_claim=True)
    if network_proven_ok or REASON_NETWORK_PROVEN_CLAIM not in network_proven_reasons:
        raise AuthenticatedProductiveTransportAdjudicationError("NETWORK_PROVEN_CLAIM_MUST_DENY")
    cred_ok, cred_reasons = _eval(credential_use_proven_claim=True)
    if cred_ok or REASON_CREDENTIAL_USE_CLAIM not in cred_reasons:
        raise AuthenticatedProductiveTransportAdjudicationError("CREDENTIAL_USE_CLAIM_MUST_DENY")
    get_proven_ok, get_proven_reasons = _eval(private_get_proven_claim=True)
    if get_proven_ok or REASON_PRIVATE_GET_CLAIM not in get_proven_reasons:
        raise AuthenticatedProductiveTransportAdjudicationError("PRIVATE_GET_CLAIM_MUST_DENY")
    post_proven_ok, post_proven_reasons = _eval(post_proven_claim=True)
    if post_proven_ok or REASON_POST_PROVEN_CLAIM not in post_proven_reasons:
        raise AuthenticatedProductiveTransportAdjudicationError("POST_PROVEN_CLAIM_MUST_DENY")
    live_ok, live_reasons = _eval(live_authorized_claim=True)
    if live_ok or REASON_LIVE_AUTHORIZED_SUBSTITUTE not in live_reasons:
        raise AuthenticatedProductiveTransportAdjudicationError(
            "LIVE_AUTHORIZED_SUBSTITUTE_MUST_DENY"
        )
    permit_ok, permit_reasons = _eval(runtime_permit_issuance_claim=True)
    if permit_ok or REASON_RUNTIME_PERMIT not in permit_reasons:
        raise AuthenticatedProductiveTransportAdjudicationError("RUNTIME_PERMIT_MUST_DENY")
    flatten_ok, flatten_reasons = _eval(flatten_execute_authorized_claim=True)
    if flatten_ok or REASON_FLATTEN_EXECUTE not in flatten_reasons:
        raise AuthenticatedProductiveTransportAdjudicationError("FLATTEN_EXECUTE_CLAIM_MUST_DENY")
    network_ok, network_reasons = _eval(network_session_authorized_claim=True)
    if network_ok or REASON_NETWORK_SESSION not in network_reasons:
        raise AuthenticatedProductiveTransportAdjudicationError("NETWORK_SESSION_CLAIM_MUST_DENY")
    post_ok, post_reasons = _eval(post_performed_claim=True)
    if post_ok or REASON_POST not in post_reasons:
        raise AuthenticatedProductiveTransportAdjudicationError("POST_CLAIM_MUST_DENY")
    get_ok, get_reasons = _eval(get_performed_claim=True)
    if get_ok or REASON_GET not in get_reasons:
        raise AuthenticatedProductiveTransportAdjudicationError("GET_CLAIM_MUST_DENY")
    go_ok, go_reasons = _eval(flatten_execute_owner_go=OWNER_GO)
    if go_ok or REASON_IMPLEMENTATION_GO_AS_EXECUTE not in go_reasons:
        raise AuthenticatedProductiveTransportAdjudicationError(
            "IMPLEMENTATION_GO_AS_EXECUTE_MUST_DENY"
        )
    lineage_ok, lineage_reasons = _eval(predecessor_lineage_ok=False)
    if lineage_ok or REASON_LINEAGE_MISMATCH not in lineage_reasons:
        raise AuthenticatedProductiveTransportAdjudicationError("LINEAGE_MISMATCH_MUST_DENY")
    matching_ok, matching_reasons = _eval()
    if matching_ok is not True or matching_reasons:
        raise AuthenticatedProductiveTransportAdjudicationError(
            f"MATCHING_CONTRACT_MUST_PASS:{matching_reasons}"
        )
    if SEND_TIME_PASS_18_19_21_24_STATUS != PASS_OFFLINE_CONTRACT:
        raise AuthenticatedProductiveTransportAdjudicationError("STP_STATUS_DRIFT")
    execute_as_apt = evaluate_flatten_pre_send_gate_v1(_gate(flatten_execute_owner_go=OWNER_GO))
    if execute_as_apt.allowed is True:
        raise AuthenticatedProductiveTransportAdjudicationError("APT_GO_AS_EXECUTE_GATE_MUST_DENY")
    apt_execute_deny = [
        item
        for item in execute_as_apt.audit_decisions
        if item[0] == "AUTHENTICATED_PRODUCTIVE_TRANSPORT"
    ]
    if not apt_execute_deny or not str(apt_execute_deny[0][1]).startswith("DENY:"):
        raise AuthenticatedProductiveTransportAdjudicationError(
            "APT_GO_AS_EXECUTE_APT_GATE_MUST_DENY"
        )
    reachable = evaluate_flatten_pre_send_gate_v1(_gate())
    if reachable.allowed is not True:
        raise AuthenticatedProductiveTransportAdjudicationError(
            f"BOUNDED_PATH_NOT_STRUCTURALLY_REACHABLE:{reachable.reasons}"
        )
    apt_pass = [
        item
        for item in reachable.audit_decisions
        if item[0] == "AUTHENTICATED_PRODUCTIVE_TRANSPORT"
    ]
    if not apt_pass or apt_pass[0][1] != "PASS":
        raise AuthenticatedProductiveTransportAdjudicationError(
            "MATCHING_FIXTURE_APT_GATE_MUST_PASS"
        )
    unsigned_transport = GatedProductiveFlattenTransportV1()
    if unsigned_transport.network_session_authorized is not False:
        raise AuthenticatedProductiveTransportAdjudicationError("NETWORK_SESSION_DEFAULT_NOT_FALSE")
    auth_transport = AuthenticatedGatedProductiveFlattenTransportV1()
    if auth_transport.network_session_authorized is not False:
        raise AuthenticatedProductiveTransportAdjudicationError(
            "AUTH_TRANSPORT_NETWORK_SESSION_DEFAULT_NOT_FALSE"
        )
    if auth_transport.signing_component != PRODUCTIVE_SIGNING_COMPONENT:
        raise AuthenticatedProductiveTransportAdjudicationError("SIGNING_COMPONENT_DRIFT")
    url = f"https://{REUSED_BINDING_REST_HOST}{ENDPOINT_SUBMIT}"
    body = '{"instId":"SUI-USD_UM_XPERP-310404","sz":"1"}'
    signing_input = construct_okx_signing_input_v1(
        timestamp=FIXTURE_TIMESTAMP,
        method="POST",
        url=url,
        body=body,
    )
    replay = construct_okx_signing_input_v1(
        timestamp=FIXTURE_TIMESTAMP,
        method="POST",
        url=url,
        body=body,
    )
    if signing_input.prehash != replay.prehash:
        raise AuthenticatedProductiveTransportAdjudicationError("SIGNING_INPUT_NOT_DETERMINISTIC")
    if FIXTURE_SECRET in signing_input.prehash:
        raise AuthenticatedProductiveTransportAdjudicationError("SECRET_LEAKED_INTO_SIGNING_INPUT")
    first_sign = sign_okx_signing_input_v1(secret=FIXTURE_SECRET, signing_input=signing_input)
    second_sign = sign_okx_signing_input_v1(secret=FIXTURE_SECRET, signing_input=replay)
    if first_sign != second_sign:
        raise AuthenticatedProductiveTransportAdjudicationError("FIXTURE_HMAC_NOT_DETERMINISTIC")
    unsigned_request = LiveCanaryHttpRequestV1(
        method="POST",
        url=url,
        host=REUSED_BINDING_REST_HOST,
        endpoint=ENDPOINT_SUBMIT,
        headers={"User-Agent": "PeakTrade-Section-11-13-5-FlattenWiring/1"},
        timeout_seconds=1.0,
        body_text=body,
    )
    try:
        auth_transport.send(unsigned_request)
    except Exception as exc:  # noqa: BLE001 — fail-closed unsigned send
        if "UNSIGNED_PRODUCTIVE_HEADERS" not in str(exc) and "RECEIPT_MISSING" not in str(exc):
            raise AuthenticatedProductiveTransportAdjudicationError(
                f"UNSIGNED_SEND_MUST_DENY:{exc}"
            ) from exc
    else:
        raise AuthenticatedProductiveTransportAdjudicationError("UNSIGNED_SEND_MUST_DENY")
    try:
        construct_okx_signing_input_v1(
            timestamp="not-a-timestamp",
            method="POST",
            url=url,
            body=body,
        )
    except Exception as exc:  # noqa: BLE001 — invalid timestamp must fail closed
        if "OKX_ACCESS_TIMESTAMP_FORMAT_INVALID" not in str(exc):
            raise AuthenticatedProductiveTransportAdjudicationError(
                f"INVALID_TIMESTAMP_MUST_DENY:{exc}"
            ) from exc
    else:
        raise AuthenticatedProductiveTransportAdjudicationError("INVALID_TIMESTAMP_MUST_DENY")
    try:
        sign_okx_signing_input_v1(secret="", signing_input=signing_input)
    except AuthenticatedProductiveTransportError:
        pass
    else:
        raise AuthenticatedProductiveTransportAdjudicationError("EMPTY_SECRET_MUST_DENY")
    window = adjudicate_prerequisite_08_window_v1(positions_payload=_positions())
    window_earliest = str(window.get("EARLIEST_UNRESOLVED_DEPENDENCY") or "")
    if window_earliest in WINDOW_EARLIER_THAN_APT:
        raise AuthenticatedProductiveTransportAdjudicationError("WINDOW_EARLIEST_DEPENDENCY_DRIFT")
    if window_earliest != EARLIEST_UNRESOLVED_DEPENDENCY:
        raise AuthenticatedProductiveTransportAdjudicationError("WINDOW_EARLIEST_DEPENDENCY_DRIFT")
    lineage = authenticated_productive_transport_lineage_v1()
    census = lineage_census_summary_v1()
    if int(census["SEAM_COUNT"]) != len(lineage):
        raise AuthenticatedProductiveTransportAdjudicationError("LINEAGE_CENSUS_DRIFT")
    return {
        "OWNER_GO": OWNER_GO,
        "PRIOR_OWNER_GO": PRIOR_OWNER_GO,
        "THIS_SLICE": THIS_SLICE,
        "PREDECESSOR_SLICE": PREDECESSOR_SLICE,
        "WORKPACKAGE_ID": WORKPACKAGE_ID,
        "BOUND_ORIGIN_MAIN_SHA": bound_sha,
        "TARGET_INSTRUMENT_ID": TARGET_INSTRUMENT_ID,
        "CASE": CASE_VALUE,
        "AUTHENTICATED_PRODUCTIVE_TRANSPORT": AUTHENTICATED_PRODUCTIVE_TRANSPORT,
        "AUTHENTICATED_PRODUCTIVE_TRANSPORT_OFFLINE_CONTRACT": AUTHENTICATED_PRODUCTIVE_TRANSPORT,
        "APT_NAMED_AUTHENTICATED_TRANSPORT_CONTRACT_CLOSED": APT_NAMED_CONTRACT_CLOSED,
        "APT_AUTHENTICATED_TRANSPORT_GATE_IMPLEMENTED": APT_MECHANISM_IMPLEMENTED,
        "APT_PRODUCTIVE_SIGNING_REUSE_WIRED": APT_PRODUCTIVE_SIGNING_REUSE_WIRED_VALUE,
        "PRODUCTIVE_SIGNING_COMPONENT": PRODUCTIVE_SIGNING_COMPONENT_VALUE,
        "AUTHENTICATED_PRODUCTIVE_TRANSPORT_RUNTIME_PROVEN": APT_RUNTIME_PROVEN_VALUE,
        "AUTHENTICATION_PROVEN": APT_AUTHENTICATION_PROVEN_VALUE,
        "NETWORK_PROVEN": NETWORK_PROVEN_VALUE,
        "CREDENTIAL_USE_PROVEN": CREDENTIAL_USE_PROVEN_VALUE,
        "PRIVATE_GET_PROVEN": PRIVATE_GET_PROVEN_VALUE,
        "POST_PROVEN": POST_PROVEN_VALUE,
        "APT_NETWORK_SESSION_AUTHORIZED": APT_NETWORK_SESSION_AUTHORIZED_VALUE,
        "APT_FLATTEN_EXECUTE_AUTHORIZED": APT_FLATTEN_EXECUTE_AUTHORIZED_VALUE,
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
        "STP_TEXT_REWRITTEN": STP_TEXT_REWRITTEN_VALUE,
        "P16_TEXT_REWRITTEN": P16_TEXT_REWRITTEN_VALUE,
        "P20_TEXT_REWRITTEN": P20_TEXT_REWRITTEN_VALUE,
        "P25_TEXT_REWRITTEN": P25_TEXT_REWRITTEN_VALUE,
        "LAST_CANONICALLY_CLOSED_STEP": LAST_CANONICALLY_CLOSED_STEP,
        "EARLIEST_UNRESOLVED_DEPENDENCY": EARLIEST_UNRESOLVED_DEPENDENCY,
        "NEXT_AUTHORITY_BOUNDARY": NEXT_AUTHORITY_BOUNDARY,
        "APT_RUNTIME_RESIDUAL": APT_RUNTIME_RESIDUAL,
        "APT_DOES_NOT_GRANT_EXECUTION_READINESS": APT_DOES_NOT_GRANT_EXECUTION_READINESS_VALUE,
        "APT_DOES_NOT_AUTHORIZE_FLATTEN": APT_DOES_NOT_AUTHORIZE_FLATTEN_VALUE,
        "APT_DOES_NOT_SET_LIVE_AUTHORIZED": APT_DOES_NOT_SET_LIVE_AUTHORIZED_VALUE,
        "APT_DOES_NOT_ISSUE_RUNTIME_PERMIT": APT_DOES_NOT_ISSUE_RUNTIME_PERMIT_VALUE,
        "APT_DOES_NOT_AUTHORIZE_NETWORK_SESSION": APT_DOES_NOT_AUTHORIZE_NETWORK_SESSION_VALUE,
        "APT_DOES_NOT_AUTHORIZE_SEND_TIME_POSITION_REOBSERVATION": (
            APT_DOES_NOT_AUTHORIZE_SEND_TIME_POSITION_REOBSERVATION_VALUE
        ),
        "FAIL_CLOSED_IF_MARKED_RUNTIME_PROVEN_FROM_OFFLINE_CODE_ALONE": (
            FAIL_CLOSED_IF_MARKED_RUNTIME_PROVEN_FROM_OFFLINE_CODE_ALONE_VALUE
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
