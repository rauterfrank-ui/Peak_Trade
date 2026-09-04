"""Offline §11.14 LIVE_SUBMIT_ACK_OBSERVED contract and mutation-boundary census.

Injected-evidence only. Does not GET. Does not POST. Does not set
LIVE_SUBMIT_ACK_OBSERVED true. Does not invent a missing proof criterion.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    DEFAULT_ORDER_TYPE,
    DEFAULT_SIDE,
    DEFAULT_TD_MODE,
    ENDPOINT_ORDERS_HISTORY,
    ENDPOINT_ORDERS_PENDING,
    ENDPOINT_SUBMIT,
    REUSED_BINDING_REST_HOST,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    AUTHORIZED_PRODUCTIVE_SUBMIT_COUNT_MAX,
    CASE_ADJUDICATION,
    HISTORICAL_ORDER_PLAN_ARTIFACT_REUSE_FOR_POST,
    LIVE_SUBMIT_ACK_OBSERVED,
    LIVE_SUBMIT_ACK_OBSERVED_CANONICAL_STATUS,
    LIVE_SUBMIT_ACK_OBSERVED_PRODUCER,
    LIVE_SUBMIT_ACK_OBSERVED_PRODUCER_BOUND,
    LIVE_SUBMIT_ACK_PROOF_CRITERION_BOUND,
    SUBMIT_ACK_PROOF_CRITERION_FILENAME,
    RETRY_DEFAULT,
    SECOND_SUBMIT_DEFAULT,
    TIMEOUT_MUST_NOT_AUTO_POST,
    TRANSPORT_OK_IS_NOT_LIVE_SUBMIT_ACK_OBSERVED,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)

ACK_PRODUCER_STATUS = LIVE_SUBMIT_ACK_OBSERVED_PRODUCER
TRANSPORT_OK_PRODUCER = (
    "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
    "submit_transport_v1.py::_entry_submit_returned_payload_v1"
)
CANONICAL_SUBMIT_ORCHESTRATOR = (
    "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
    "submit_transport_v1.py::run_canary_submit_transport_v1"
)
HTTP_CLIENT_SUBMIT = (
    "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
    "http_client_v1.py::LiveCanaryHttpClientV1.post_entry_order"
)
EXACT_PRE_WIRE_ORCHESTRATOR_GATE = "refuse_submit_unless_gates_pass_v1"
EXACT_PRE_WIRE_HTTP_LOCK = "_entry_send_attempted"
SUBMIT_COUNT_INCREMENT_SEAM = "LiveCanaryHttpClientV1.post_entry_order after transport.send returns"
VENUE_NATIVE_BODY_KEYS: tuple[str, ...] = (
    "clOrdId",
    "instId",
    "side",
    "ordType",
    "sz",
    "tdMode",
    "px",
)
AUTH_HEADER_PRESENCE_KEYS: tuple[str, ...] = (
    "AUTH_KEY_HEADER_PRESENT",
    "AUTH_SIGN_HEADER_PRESENT",
    "AUTH_TIMESTAMP_HEADER_PRESENT",
    "AUTH_PASSPHRASE_HEADER_PRESENT",
    "USER_AGENT_HEADER_PRESENT",
)

FAILURE_CASES: tuple[str, ...] = (
    "REQUEST_NOT_SENT",
    "LOCAL_ERROR_BEFORE_WIRE",
    "CONNECTION_FAILURE_BEFORE_SEND_ATTEMPTED",
    "CONNECTION_FAILURE_AFTER_SEND_ATTEMPTED",
    "TIMEOUT_AFTER_POSSIBLE_SEND",
    "HTTP_NON_2XX",
    "PARSE_FAILURE",
    "VENUE_CODE_NOT_ZERO",
    "VENUE_CODE_ZERO_WITHOUT_ACK_IDENTITY",
    "UNIQUE_TRANSPORT_OK",
    "CONTRADICTORY_OR_UNCLEAR",
)


def refuse_live_submit_ack_observed_true_v1(*, claimed_true: bool) -> None:
    if claimed_true is True or LIVE_SUBMIT_ACK_OBSERVED is True:
        raise Section1114OfflineSurfaceError("LIVE_SUBMIT_ACK_OBSERVED_MUST_REMAIN_FALSE")


def _row(
    *,
    case: str,
    live_submit_ack_observed: bool,
    submit_count: str,
    send_attempted: bool,
    retry_allowed: bool,
    second_submit_allowed: bool,
    recon: str,
    hard_stop: str,
) -> dict[str, Any]:
    if live_submit_ack_observed is True:
        raise Section1114OfflineSurfaceError("FAILURE_MATRIX_PROMOTED_ACK")
    if retry_allowed is True or second_submit_allowed is True:
        raise Section1114OfflineSurfaceError("FAILURE_MATRIX_ALLOWED_RETRY")
    return {
        "case": case,
        "LIVE_SUBMIT_ACK_OBSERVED": False,
        "SUBMIT_COUNT": submit_count,
        "SEND_ATTEMPTED": send_attempted,
        "RETRY_ALLOWED": False,
        "SECOND_SUBMIT_ALLOWED": False,
        "required_next_read_only_recon": recon,
        "hard_stop": hard_stop,
    }


def build_transport_ok_predicate_v1() -> dict[str, Any]:
    return {
        "owner": TRANSPORT_OK_PRODUCER,
        "is_section_11_14_live_submit_ack_observed": False,
        "http_status_required": 200,
        "http_status_is_part_of_semantics": True,
        "http_2xx_other_than_200_is_not_ok": True,
        "venue_top_level_code_required": "0",
        "venue_scode_required": False,
        "ordId_required": False,
        "clOrdId_required": False,
        "data_length_required": False,
        "json_parse_ok_required": True,
        "redirect_forbidden": True,
        "redirect_followed_forbidden": True,
        "CANARY_EXECUTED_remains_false_even_if_ok": True,
        "TRANSPORT_OK_IS_NOT_LIVE_SUBMIT_ACK_OBSERVED": (
            TRANSPORT_OK_IS_NOT_LIVE_SUBMIT_ACK_OBSERVED
        ),
    }


def build_exact_mutation_contract_v1() -> dict[str, Any]:
    return {
        "schema_version": "section_11_14_exact_mutation_contract.v1",
        "POST_AUTHORIZED_BY_THIS_GO": False,
        "endpoint": ENDPOINT_SUBMIT,
        "http_method": "POST",
        "host": REUSED_BINDING_REST_HOST,
        "url": f"https://{REUSED_BINDING_REST_HOST}{ENDPOINT_SUBMIT}",
        "auth_path": (
            "build_okx_live_canary_auth_headers_v1 method=POST body=serialized_json "
            "headers=OK-ACCESS-KEY/SIGN/TIMESTAMP/PASSPHRASE"
        ),
        "auth_header_presence_keys": list(AUTH_HEADER_PRESENCE_KEYS),
        "auth_header_values_persisted": False,
        "request_body_builder": (
            "src/ops/section_11_12_8_actual_productive_testnet_campaign_run_start_v1/"
            "okx_response_mapper_v1.py::build_venue_native_order_body_v1"
        ),
        "request_body_keys": list(VENUE_NATIVE_BODY_KEYS),
        "instrument": DEFAULT_INSTRUMENT_ID,
        "side": DEFAULT_SIDE.lower(),
        "ordType": DEFAULT_ORDER_TYPE.lower(),
        "sz": "1",
        "px": "FRESH_VENUE_DERIVED_LIMIT_NOT_HISTORICAL_ARTIFACT",
        "tdMode": DEFAULT_TD_MODE,
        "posSide": "OMITTED_ON_OBSERVED_NET_MODE_PLAN",
        "reduceOnly": "OMITTED_FOR_ENTRY",
        "historical_observed_plan_venue_native_keys": list(VENUE_NATIVE_BODY_KEYS),
        "historical_order_plan_artifact_reuse_for_post": (
            HISTORICAL_ORDER_PLAN_ARTIFACT_REUSE_FOR_POST
        ),
        "fresh_plan_required_at_post_time": True,
        "gate_sequence": [
            "_assert_standing_safety",
            "OWNER_GO_EXECUTE match and not consumed",
            "evaluate_canary_submit_gates_v1 + refuse_submit_unless_gates_pass_v1 (pre-sizing)",
            "UrllibLiveCanaryTransportV1 constructible",
            "REST_HOST_NOT_PRODUCTION_EEA",
            "ephemeral SecretRef load",
            "instrument binding",
            "GET instruments/ticker/price-limit/max-size/leverage/config/positions/balance",
            "build_minimum_valid_canary_order_plan_v1",
            "assert_identity_sz_after_contract_sizing_v1",
            "GET /api/v5/trade/orders-pending",
            "evaluate_pre_submit_exchange_state_v1",
            "assert_pre_submit_open_position_cap_allows_v1",
            "evaluate_canary_submit_gates_v1 + refuse_submit_unless_gates_pass_v1 (post-plan)",
            "serialize_signed_post_body_v1 + CanaryEntrySubmitPermitV1",
            "LiveCanaryHttpClientV1.post_entry_order pre-send locks",
            "_build_request POST allowlist/host",
            "_entry_send_attempted=True",
            "transport.send",
            "entry_submit_count += 1 after HTTP response",
        ],
        "EXACT_PRE_WIRE_GATE": EXACT_PRE_WIRE_ORCHESTRATOR_GATE,
        "EXACT_PRE_WIRE_HTTP_LOCK": EXACT_PRE_WIRE_HTTP_LOCK,
        "SUBMIT_COUNT_INCREMENT_SEAM": SUBMIT_COUNT_INCREMENT_SEAM,
        "AUTHORIZED_PRODUCTIVE_SUBMIT_COUNT_MAX": AUTHORIZED_PRODUCTIVE_SUBMIT_COUNT_MAX,
        "RETRY_DEFAULT": RETRY_DEFAULT,
        "SECOND_SUBMIT_DEFAULT": SECOND_SUBMIT_DEFAULT,
        "duplicate_submit_lock": "DUPLICATE_ENTRY_SUBMIT_FORBIDDEN if entry_submit_count>=1",
        "unknown_no_blind_retry_lock": "UNKNOWN_SUBMIT_NO_BLIND_RETRY if _entry_send_attempted",
    }


def build_failure_matrix_v1() -> dict[str, Any]:
    halt = "HALT_NO_POST_NO_RETRY_NO_CANCEL_NO_AMEND_NO_FLATTEN"
    recon_none = "NONE_NO_NETWORK_THIS_GO"
    recon_unknown = (
        f"GET {ENDPOINT_ORDERS_PENDING} then GET {ENDPOINT_ORDERS_HISTORY} match clOrdId; "
        "never a second POST"
    )
    rows = [
        _row(
            case="REQUEST_NOT_SENT",
            live_submit_ack_observed=False,
            submit_count="0",
            send_attempted=False,
            retry_allowed=False,
            second_submit_allowed=False,
            recon=recon_none,
            hard_stop=halt,
        ),
        _row(
            case="LOCAL_ERROR_BEFORE_WIRE",
            live_submit_ack_observed=False,
            submit_count="0",
            send_attempted=False,
            retry_allowed=False,
            second_submit_allowed=False,
            recon=recon_none,
            hard_stop=halt,
        ),
        _row(
            case="CONNECTION_FAILURE_BEFORE_SEND_ATTEMPTED",
            live_submit_ack_observed=False,
            submit_count="0",
            send_attempted=False,
            retry_allowed=False,
            second_submit_allowed=False,
            recon=recon_none,
            hard_stop=halt,
        ),
        _row(
            case="CONNECTION_FAILURE_AFTER_SEND_ATTEMPTED",
            live_submit_ack_observed=False,
            submit_count="0_COUNTER_NOT_INCREMENTED_SEND_MAY_HAVE_LEFT_LOCAL_PROCESS",
            send_attempted=True,
            retry_allowed=False,
            second_submit_allowed=False,
            recon=recon_unknown,
            hard_stop="UNKNOWN_SUBMIT_NO_BLIND_RETRY;" + halt,
        ),
        _row(
            case="TIMEOUT_AFTER_POSSIBLE_SEND",
            live_submit_ack_observed=False,
            submit_count="0_COUNTER_NOT_INCREMENTED_WIRE_MAY_HAVE_BEEN_SENT",
            send_attempted=True,
            retry_allowed=False,
            second_submit_allowed=False,
            recon=recon_unknown,
            hard_stop="UNKNOWN_SUBMIT_TIMEOUT;UNKNOWN_SUBMIT_NO_BLIND_RETRY;" + halt,
        ),
        _row(
            case="HTTP_NON_2XX",
            live_submit_ack_observed=False,
            submit_count="1",
            send_attempted=True,
            retry_allowed=False,
            second_submit_allowed=False,
            recon=recon_unknown,
            hard_stop=halt,
        ),
        _row(
            case="PARSE_FAILURE",
            live_submit_ack_observed=False,
            submit_count="1",
            send_attempted=True,
            retry_allowed=False,
            second_submit_allowed=False,
            recon=recon_unknown,
            hard_stop=halt,
        ),
        _row(
            case="VENUE_CODE_NOT_ZERO",
            live_submit_ack_observed=False,
            submit_count="1",
            send_attempted=True,
            retry_allowed=False,
            second_submit_allowed=False,
            recon=recon_unknown,
            hard_stop="TRANSPORT_OK_FALSE;" + halt,
        ),
        _row(
            case="VENUE_CODE_ZERO_WITHOUT_ACK_IDENTITY",
            live_submit_ack_observed=False,
            submit_count="1",
            send_attempted=True,
            retry_allowed=False,
            second_submit_allowed=False,
            recon=recon_unknown,
            hard_stop=(
                "TRANSPORT_OK_MAY_BE_TRUE_WITHOUT_ORDID_OR_SCODE;"
                "ACK_CRITERION_BOUND_IDENTITY_MISSING_IS_UNKNOWN;" + halt
            ),
        ),
        _row(
            case="UNIQUE_TRANSPORT_OK",
            live_submit_ack_observed=False,
            submit_count="1",
            send_attempted=True,
            retry_allowed=False,
            second_submit_allowed=False,
            recon="NOT_IMPLEMENTED_ON_SUCCESS_RETURN_PATH; LATER_FIELDS_REMAIN_FALSE",
            hard_stop=(
                "TRANSPORT_OK_IS_NOT_LIVE_SUBMIT_ACK_OBSERVED;PRODUCER_BOUND_NO_LIVE_POST;" + halt
            ),
        ),
        _row(
            case="CONTRADICTORY_OR_UNCLEAR",
            live_submit_ack_observed=False,
            submit_count="0_OR_1_FAIL_CLOSED_AS_UNKNOWN",
            send_attempted=True,
            retry_allowed=False,
            second_submit_allowed=False,
            recon=recon_unknown,
            hard_stop="TREAT_AS_UNKNOWN;" + halt,
        ),
    ]
    names = tuple(row["case"] for row in rows)
    if names != FAILURE_CASES:
        raise Section1114OfflineSurfaceError("FAILURE_MATRIX_CASE_DRIFT")
    return {
        "schema_version": "section_11_14_submit_ack_failure_matrix.v1",
        "LIVE_SUBMIT_ACK_OBSERVED": False,
        "AUTHORIZED_PRODUCTIVE_SUBMIT_COUNT_MAX": AUTHORIZED_PRODUCTIVE_SUBMIT_COUNT_MAX,
        "RETRY_DEFAULT": RETRY_DEFAULT,
        "SECOND_SUBMIT_DEFAULT": SECOND_SUBMIT_DEFAULT,
        "TIMEOUT_MUST_NOT_AUTO_POST": TIMEOUT_MUST_NOT_AUTO_POST,
        "row_count": len(rows),
        "rows": rows,
    }


def build_post_submit_recon_contract_v1() -> dict[str, Any]:
    return {
        "schema_version": "section_11_14_post_submit_recon.v1",
        "POST_SUBMIT_RECON_AUTHORIZED_BY_THIS_GO": False,
        "implemented_unknown_path_owner": CANONICAL_SUBMIT_ORCHESTRATOR,
        "sequence_if_unknown_after_send_attempted": [
            ENDPOINT_ORDERS_PENDING,
            ENDPOINT_ORDERS_HISTORY,
        ],
        "identity_for_unknown_resolution": "clOrdId from the just-built plan",
        "classifier": "classify_unknown_submit_from_exchange_v1",
        "unknown_outcomes": [
            "UNKNOWN_SUBMIT_RESOLVED_PENDING",
            "UNKNOWN_SUBMIT_RESOLVED_HISTORY",
            "UNKNOWN_SUBMIT_UNRESOLVED_HALT",
        ],
        "unknown_resolution_is_not_live_submit_ack_observed": True,
        "read_only_recon_may_resolve_existence_without_reclassifying_ack": True,
        "success_return_path_has_no_automatic_recon_gets": True,
        "max_request_count": 12,
        "observed_plan_get_count": 9,
        "budget_after_nine_gets": "POST plus at most two recon GETs fits DEFAULT_MAX_REQUEST_COUNT=12",
        "fills_get_not_part_of_ack_unknown_recon": True,
        "duplicate_submit_excluded_by": [
            "_entry_send_attempted",
            "entry_submit_count>=1 -> DUPLICATE_ENTRY_SUBMIT_FORBIDDEN",
            "clOrdId rebind forbidden",
            "ONE_SHOT_CLORDID_PER_OWNER_GO_BINDING",
        ],
        "LIVE_FILL_OBSERVED_may_adjudicate_only_after": "LIVE_SUBMIT_ACK_OBSERVED=true",
        "LIVE_POSITION_RECONCILED_may_adjudicate_only_after": (
            "LIVE_FILL_OBSERVED and LIVE_FEE_OBSERVED per ladder order"
        ),
        "LIVE_FILL_OBSERVED": False,
        "LIVE_POSITION_RECONCILED": False,
    }


def build_submit_ack_contract_v1() -> dict[str, Any]:
    refuse_live_submit_ack_observed_true_v1(claimed_true=False)
    return {
        "schema_version": "section_11_14_submit_ack_contract.v1",
        "ACK_PRODUCER": ACK_PRODUCER_STATUS,
        "LIVE_SUBMIT_ACK_OBSERVED_PRODUCER_BOUND": LIVE_SUBMIT_ACK_OBSERVED_PRODUCER_BOUND,
        "LIVE_SUBMIT_ACK_PROOF_CRITERION_BOUND": LIVE_SUBMIT_ACK_PROOF_CRITERION_BOUND,
        "canonical_status": LIVE_SUBMIT_ACK_OBSERVED_CANONICAL_STATUS,
        "canonical_runbook_currently_states": "Canonical ACK requires POST of the observed plan.",
        "orchestrator": CANONICAL_SUBMIT_ORCHESTRATOR,
        "http_submit": HTTP_CLIENT_SUBMIT,
        "transport_ok_predicate": build_transport_ok_predicate_v1(),
        "ACK_SUCCESS_SEMANTICS": (
            "HTTP 200 AND top-level code=0 AND json_parse_ok AND no redirect AND "
            "exactly one data row AND sCode=0 AND nonempty ordId AND returned "
            "clOrdId nonempty and equal to sent clOrdId. Transport ok is not sufficient."
        ),
        "ACK_REJECT_SEMANTICS": (
            "Parseable response with top-level code nonempty and !=0, or code=0 "
            "with exactly one data row and sCode present and !=0. Not ACK. No retry."
        ),
        "ACK_UNKNOWN_SEMANTICS": (
            "Timeout/network after send, parse failure, HTTP!=200 without explicit "
            "reject code, redirect, data_count!=1 on would-be success, missing "
            "ordId/sCode/clOrdId, clOrdId mismatch, or contradictory response. "
            "Second POST forbidden. Recon may resolve existence without reclassifying ACK."
        ),
        "lifecycle_contract_ack_handling": "REQUIRE_EXCHANGE_ORDID_OR_EXPLICIT_REJECT_CODE",
        "lifecycle_contract_activated": False,
        "flatten_ack_sCode_and_single_data_row": (
            "SUPPORTING_CONTEXT_EXPLICITLY_ADOPTED_FOR_DATA_CARDINALITY_AND_SCODE_BY_THIS_GO"
        ),
        "cap_11_12_8_mapper_requires_code0_sCode0_ordId": (
            "SEMANTICALLY_DIFFERENT_NOT_THE_PRODUCER_CONJUNCTS_ADOPTED_BY_THIS_GO"
        ),
        "successfully_accepted_order_without_local_ack_possible": True,
        "LIVE_SUBMIT_ACK_OBSERVED": False,
    }


def classify_injected_submit_ack_evidence_v1(
    *,
    send_attempted: bool,
    entry_submit_count: int,
    http_status: int | None = None,
    okx_code: str | None = None,
    json_parse_ok: bool | None = None,
    redirect_followed: bool = False,
    transport_error: str | None = None,
    ord_id: str | None = None,
    s_code: str | None = None,
) -> dict[str, Any]:
    """Classify injected transport evidence. Never a §11.14 ACK promotion."""
    refuse_live_submit_ack_observed_true_v1(claimed_true=False)
    if int(entry_submit_count) > AUTHORIZED_PRODUCTIVE_SUBMIT_COUNT_MAX:
        raise Section1114OfflineSurfaceError("SUBMIT_COUNT_EXCEEDS_AUTHORIZED_MAX")
    err = str(transport_error or "")
    case = "CONTRADICTORY_OR_UNCLEAR"
    if not send_attempted and int(entry_submit_count) == 0 and not err:
        case = "REQUEST_NOT_SENT"
    elif not send_attempted and int(entry_submit_count) == 0:
        case = "LOCAL_ERROR_BEFORE_WIRE"
    elif send_attempted and "TIMEOUT" in err:
        case = "TIMEOUT_AFTER_POSSIBLE_SEND"
    elif send_attempted and ("NETWORK" in err or "URLError" in err or "OSError" in err):
        case = "CONNECTION_FAILURE_AFTER_SEND_ATTEMPTED"
    elif send_attempted and json_parse_ok is False:
        case = "PARSE_FAILURE"
    elif send_attempted and http_status is not None and int(http_status) != 200:
        case = "HTTP_NON_2XX"
    elif send_attempted and str(okx_code or "") not in {"", "0"}:
        case = "VENUE_CODE_NOT_ZERO"
    elif (
        send_attempted
        and json_parse_ok is True
        and str(okx_code or "") == "0"
        and http_status == 200
        and not redirect_followed
    ):
        identity_present = bool(str(ord_id or "").strip()) and str(s_code or "") == "0"
        if identity_present:
            case = "UNIQUE_TRANSPORT_OK"
        else:
            case = "VENUE_CODE_ZERO_WITHOUT_ACK_IDENTITY"
    if case not in FAILURE_CASES:
        raise Section1114OfflineSurfaceError(f"UNKNOWN_FAILURE_CASE:{case}")
    return {
        "case": case,
        "LIVE_SUBMIT_ACK_OBSERVED": False,
        "TRANSPORT_OK_IS_NOT_LIVE_SUBMIT_ACK_OBSERVED": True,
        "RETRY_ALLOWED": False,
        "SECOND_SUBMIT_ALLOWED": False,
        "SEND_ATTEMPTED": bool(send_attempted),
        "ENTRY_SUBMIT_COUNT": int(entry_submit_count),
        "POST_AUTHORIZED_BY_THIS_GO": False,
    }


def adjudicate_submit_ack_forensic_v1() -> dict[str, Any]:
    refuse_live_submit_ack_observed_true_v1(claimed_true=False)
    return {
        "schema_version": "section_11_14_submit_ack_forensic_adjudication.v1",
        "LIVE_ORDER_PLAN_OBSERVED": True,
        "LIVE_SUBMIT_ACK_OBSERVED": False,
        "CASE_ADJUDICATION": CASE_ADJUDICATION,
        "CASE_A_READY_FOR_EXACT_SINGLE_POST_OWNER_GO": True,
        "CASE_B_OFFLINE_IMPLEMENTATION_GAP": False,
        "CASE_C_CANONICAL_SEMANTIC_GAP": False,
        "CASE_D_RUNTIME_OR_VENUE_PRECONDITION_GAP": False,
        "CASE_E_CONTRADICTION_REQUIRES_STOP": False,
        "why_case_a": (
            "The §11.14 ACK producer and synchronous proof criterion are bound. "
            "Single-submit and UNKNOWN_SUBMIT_NO_BLIND_RETRY remain in force. "
            "The standing field is false because this GO forbids POST. Next GO "
            "is an exact single live submit POST, not this GO."
        ),
        "why_not_case_b": (
            "Single-submit locks already exist: DUPLICATE_ENTRY_SUBMIT_FORBIDDEN and "
            "UNKNOWN_SUBMIT_NO_BLIND_RETRY. Timeout cannot auto-POST. The producer "
            "is an offline classifier; live POST wiring is the next Owner-GO."
        ),
        "why_not_case_c": (
            "HTTP 200, top-level code=0, exactly one data row, sCode=0, nonempty "
            "ordId, and returned clOrdId equal to sent clOrdId are now bound."
        ),
        "why_not_case_d": (
            "This GO is offline and does not re-observe venue preconditions. "
            "Standing Live gates remain false by design."
        ),
        "why_not_case_e": (
            "Flatten, Cap 11.12.8, and lifecycle remain non-producers. This GO "
            "explicitly adopts selected conjuncts onto the productive HTTP evidence "
            "surface without treating those modules as §11.14 SSOT."
        ),
        "POST_PERFORMED": False,
        "RETRY_DEFAULT": RETRY_DEFAULT,
        "SECOND_SUBMIT_DEFAULT": SECOND_SUBMIT_DEFAULT,
        "AUTHORIZED_PRODUCTIVE_SUBMIT_COUNT_MAX": AUTHORIZED_PRODUCTIVE_SUBMIT_COUNT_MAX,
        "HARD_STOP": True,
    }


def build_submit_ack_forensic_documents_v1() -> dict[str, dict[str, Any]]:
    return {
        "SUBMIT_ACK_CONTRACT.json": build_submit_ack_contract_v1(),
        "SUBMIT_ACK_FAILURE_MATRIX.json": build_failure_matrix_v1(),
        "SUBMIT_ACK_ADJUDICATION.json": adjudicate_submit_ack_forensic_v1(),
        SUBMIT_ACK_PROOF_CRITERION_FILENAME: {
            "schema_version": "section_11_14_submit_ack_proof_criterion.v1",
            "producer": ACK_PRODUCER_STATUS,
            "LIVE_SUBMIT_ACK_OBSERVED_PRODUCER_BOUND": True,
            "LIVE_SUBMIT_ACK_PROOF_CRITERION_BOUND": True,
            "LIVE_SUBMIT_ACK_OBSERVED": False,
            "HTTP_STATUS_CONTRIBUTES": True,
            "HTTP_STATUS_REQUIRED": 200,
            "TOP_LEVEL_CODE_CONTRIBUTES": True,
            "TOP_LEVEL_CODE_REQUIRED": "0",
            "EXACTLY_ONE_DATA_ROW_REQUIRED": True,
            "SCODE_0_REQUIRED": True,
            "NONEMPTY_ORDID_REQUIRED": True,
            "RETURNED_CLORDID_REQUIRED": True,
            "RETURNED_CLORDID_MUST_EQUAL_SENT": True,
            "TRANSPORT_OK_IS_NOT_LIVE_SUBMIT_ACK_OBSERVED": True,
            "CANARY_EXECUTED_IS_NOT_LIVE_SUBMIT_ACK_OBSERVED": True,
            "UNKNOWN_SUBMIT_IS_NOT_ACK": True,
            "READ_ONLY_RECON_CLORDID_MATCH_IS_NOT_SYNCHRONOUS_ACK": True,
            "canonical_definition": LIVE_SUBMIT_ACK_OBSERVED_CANONICAL_STATUS,
        },
        "EXACT_MUTATION_CONTRACT.json": build_exact_mutation_contract_v1(),
        "POST_SUBMIT_RECON.json": build_post_submit_recon_contract_v1(),
    }
