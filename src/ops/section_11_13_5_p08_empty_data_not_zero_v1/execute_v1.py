"""Execute the minimum necessary private positions GETs to resolve CASE_C.

Constructs LiveCanaryHttpClientV1 itself. Reuses the existing canary GET
signer, live-canary SecretRef, query grammar, and P08 CASE_A..F classifier.
No POST, transfer, order, funding GET, config GET, whitelist mutation, or
capital movement. Empty data is never promoted to zero. Historical P08
empty envelopes remain historical.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.account_positions_query_grammar_v1 import (
    build_account_positions_query_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    USER_AGENT_CANARY,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    LiveCanaryHttpClientV1,
    LiveCanaryHttpError,
    LiveCanaryTransportV1,
    UrllibLiveCanaryTransportV1,
    parse_json_object_v1,
    safe_response_headers_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.live_credential_ephemeral_v1 import (
    build_file_secretref_vault_backend_v1,
    release_live_canary_ephemeral_material_v1,
    resolve_and_load_live_canary_secretref_ephemeral_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.okx_live_canary_signer_v1 import (
    build_okx_live_canary_auth_headers_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.position_observation_freshness_contract_v1 import (
    POSITION_OBSERVATION_FRESHNESS_MAX_AGE_MS,
    default_local_monotonic_ms_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_submit_state_v1 import (
    TARGET_POSITION_NONZERO_PROVEN,
    TARGET_POSITION_ZERO_PROVEN,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.prerequisite_08_fresh_position_observation_v1 import (
    adjudicate_prerequisite_08_window_v1,
    evaluate_freshness_at_adjudication_v1,
    sanitize_positions_payload_v1,
)
from src.ops.section_11_13_5_p08_empty_data_not_zero_v1.constants_v1 import (
    AUTHORIZED_HOST,
    CASE_A_TARGET_NONZERO,
    CASE_B_TARGET_ZERO,
    CASE_C_EMPTY_DATA_NOT_ZERO,
    CASE_D_TARGET_NOT_OBSERVED,
    CASE_E_HTTP_OR_OKX_ERROR,
    CASE_F_AMBIGUOUS,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT_SECONDS,
    EMPTY_DATA_IS_ZERO,
    ENDPOINT,
    EXPECTED_ORIGIN_MAIN_SHA,
    FORBIDDEN_ENDPOINTS,
    FRESHNESS_POLICY,
    GET_1_ROLE,
    GET_2_ROLE,
    GET_3_ROLE,
    HISTORICAL_P08_BODY_SHA256,
    HISTORICAL_P08_EVIDENCE_PACK,
    MAX_HTTP_EXCHANGE_COUNT,
    MAX_NETWORK_REQUEST_COUNT,
    NEXT_AUTHORITY_BOUNDARY_CASE_A_QTY_NUMERIC_REUSED,
    NEXT_AUTHORITY_BOUNDARY_CASE_A_QTY_UNRESOLVED_REUSED,
    NEXT_AUTHORITY_BOUNDARY_CASE_B_REUSED,
    NEXT_AUTHORITY_BOUNDARY_CASE_C_REMAINS,
    NEXT_AUTHORITY_BOUNDARY_CASE_D_REUSED,
    NEXT_AUTHORITY_BOUNDARY_CASE_E_REUSED,
    NEXT_AUTHORITY_BOUNDARY_CASE_F_REUSED,
    NEXT_AUTHORITY_BOUNDARY_CONTRADICTION,
    OWNER_GO,
    P08_CANONICAL_DEFINITION_REUSED,
    RESULT_CLASS_200_OKX_0,
    REUSED_CREDENTIAL_CLASS,
    REUSED_REST_BASE,
    REUSED_REST_HOST,
    REUSED_SECRETREF_URI,
    REUSED_VENUE,
    TARGET_INST_TYPE,
    TARGET_INSTRUMENT_ID,
    THIS_SLICE,
)
from src.ops.section_11_13_5_p08_empty_data_not_zero_v1.persist_claims_v1 import (
    CLAIMS,
)
from src.ops.section_11_13_5_p08_empty_data_not_zero_v1.persist_v1 import (
    persist_p08_empty_data_not_zero_evidence_v1,
)
from src.ops.section_11_13_5_p08_position_observation_v1.execute_v1 import (
    classify_http_okx_result_v1,
    classify_position_observation_v1,
    secretref_identity_without_values_v1,
)
from src.ops.section_11_13_5_post_z2ds_private_get_current_50110_egress_capture_v1.execute_v1 import (
    sanitize_okx_message_v1,
)


class P08EmptyDataNotZeroError(RuntimeError):
    """Fail-closed P08 empty-data-not-zero GET-package violation."""


def _utc_now_iso_v1() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _header_presence_v1(headers: dict[str, str]) -> dict[str, Any]:
    keys = {str(k).upper() for k in headers}
    return {
        "AUTH_KEY_HEADER_PRESENT": "OK-ACCESS-KEY" in keys,
        "AUTH_SIGN_HEADER_PRESENT": "OK-ACCESS-SIGN" in keys,
        "AUTH_TIMESTAMP_HEADER_PRESENT": "OK-ACCESS-TIMESTAMP" in keys,
        "AUTH_PASSPHRASE_HEADER_PRESENT": "OK-ACCESS-PASSPHRASE" in keys,
        "SIMULATION_HEADER_PRESENT": any("simul" in str(k).lower() for k in headers),
        "SIGNED_METHOD": "GET",
    }


def _exchange_count_v1(transport: LiveCanaryTransportV1) -> int:
    wire_count = int(getattr(transport, "http_exchange_count", 0) or 0)
    if wire_count > 0:
        return wire_count
    calls = getattr(transport, "calls", None)
    if isinstance(calls, list):
        return len(calls)
    return wire_count


def _path_only_v1(endpoint: str) -> str:
    parsed = urlparse(endpoint if "://" in endpoint else f"https://{AUTHORIZED_HOST}{endpoint}")
    return parsed.path or endpoint.split("?", 1)[0]


def _assert_positions_gets_zero_writes(
    client: LiveCanaryHttpClientV1,
    *,
    expected_get_count: int,
) -> dict[str, Any]:
    counters = client.counters.to_dict()
    get_count = int(counters.get("GET_REQUEST_COUNT", 0) or 0)
    if get_count != expected_get_count:
        raise P08EmptyDataNotZeroError("GET_COUNT_MISMATCH")
    if get_count < 1 or get_count > MAX_NETWORK_REQUEST_COUNT:
        raise P08EmptyDataNotZeroError("GET_COUNT_OUT_OF_BOUNDS")
    if int(counters.get("REQUEST_COUNT", 0) or 0) != get_count:
        raise P08EmptyDataNotZeroError("REQUEST_COUNT_MISMATCH")
    if int(counters.get("WRITE_REQUEST_COUNT", 0) or 0) != 0:
        raise P08EmptyDataNotZeroError("WRITE_REQUEST_DETECTED")
    if int(counters.get("TRANSFER_REQUEST_COUNT", 0) or 0) != 0:
        raise P08EmptyDataNotZeroError("TRANSFER_REQUEST_DETECTED")
    if int(counters.get("ORDER_REQUEST_COUNT", 0) or 0) != 0:
        raise P08EmptyDataNotZeroError("ORDER_REQUEST_DETECTED")
    if int(counters.get("ENTRY_SUBMIT_COUNT", 0) or 0) != 0:
        raise P08EmptyDataNotZeroError("ENTRY_SUBMIT_DETECTED")
    if int(counters.get("FLATTEN_SUBMIT_COUNT", 0) or 0) != 0:
        raise P08EmptyDataNotZeroError("FLATTEN_SUBMIT_DETECTED")
    if list(client.counters.methods_used) != ["GET"] * get_count:
        raise P08EmptyDataNotZeroError("NON_GET_METHOD_DETECTED")
    for used in client.counters.endpoints_used:
        if _path_only_v1(str(used)) != ENDPOINT:
            raise P08EmptyDataNotZeroError("ENDPOINT_SET_MISMATCH")
        if _path_only_v1(str(used)) in FORBIDDEN_ENDPOINTS:
            raise P08EmptyDataNotZeroError("MUTATION_ENDPOINT_FORBIDDEN")
    return counters


def _body_utf8_exact_v1(body_bytes: bytes) -> str | None:
    if not body_bytes:
        return None
    try:
        return body_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return None


def classify_package_observation_v1(
    exchanges: tuple[Mapping[str, Any], ...],
) -> dict[str, Any]:
    """Package-level CASE from first-party GETs. Empty is never zero.

    HYPOTHESIS is not used here. Direct support only: CASE_A requires a unique
    nonzero target row on at least one GET; CASE_B requires a unique zero
    target row and no CASE_A; contradictory A+B is CASE_F.
    """
    if EMPTY_DATA_IS_ZERO:
        raise P08EmptyDataNotZeroError("EMPTY_DATA_MUST_NOT_BE_PROMOTED_TO_ZERO")
    if not exchanges:
        return {
            "POSITION_OBSERVATION_CLASS": CASE_E_HTTP_OR_OKX_ERROR,
            "POSITION_RESPONSE_OBSERVED": False,
            "TARGET_INSTRUMENT_ROW_OBSERVED": False,
            "POSITION_STATE_OBSERVED": False,
            "TARGET_POSITION_ZERO_PROVEN": False,
            "TARGET_POSITION_NONZERO_PROVEN": False,
            "P08_CLOSED": False,
            "P08_VERDICT": "P08_NOT_CLOSED_NO_EXCHANGE",
            "NEXT_AUTHORITY_BOUNDARY": NEXT_AUTHORITY_BOUNDARY_CASE_E_REUSED,
        }
    classes = [str(item.get("POSITION_OBSERVATION_CLASS") or "") for item in exchanges]
    has_a = CASE_A_TARGET_NONZERO in classes
    has_b = CASE_B_TARGET_ZERO in classes
    has_f = CASE_F_AMBIGUOUS in classes
    has_d = CASE_D_TARGET_NOT_OBSERVED in classes
    has_e = CASE_E_HTTP_OR_OKX_ERROR in classes
    all_c = classes and all(item == CASE_C_EMPTY_DATA_NOT_ZERO for item in classes)
    if has_a and has_b:
        return {
            "POSITION_OBSERVATION_CLASS": CASE_F_AMBIGUOUS,
            "POSITION_RESPONSE_OBSERVED": True,
            "TARGET_INSTRUMENT_ROW_OBSERVED": True,
            "POSITION_STATE_OBSERVED": False,
            "TARGET_POSITION_ZERO_PROVEN": False,
            "TARGET_POSITION_NONZERO_PROVEN": False,
            "P08_CLOSED": False,
            "P08_VERDICT": "P08_NOT_CLOSED_CONTRADICTORY_ZERO_AND_NONZERO_ROWS",
            "NEXT_AUTHORITY_BOUNDARY": NEXT_AUTHORITY_BOUNDARY_CONTRADICTION,
        }
    if has_a:
        qty_pass = any(
            str(item.get("TARGET_POSITION_QTY_NUMERIC") or "") == "PASS"
            and str(item.get("POSITION_OBSERVATION_CLASS") or "") == CASE_A_TARGET_NONZERO
            for item in exchanges
        )
        return {
            "POSITION_OBSERVATION_CLASS": CASE_A_TARGET_NONZERO,
            "POSITION_RESPONSE_OBSERVED": True,
            "TARGET_INSTRUMENT_ROW_OBSERVED": True,
            "POSITION_STATE_OBSERVED": True,
            "TARGET_POSITION_ZERO_PROVEN": False,
            "TARGET_POSITION_NONZERO_PROVEN": True,
            "P08_CLOSED": True,
            "P08_VERDICT": "P08_CLOSED_UNIQUE_TARGET_NONZERO_ROW_THIS_WINDOW",
            "NEXT_AUTHORITY_BOUNDARY": (
                NEXT_AUTHORITY_BOUNDARY_CASE_A_QTY_NUMERIC_REUSED
                if qty_pass
                else NEXT_AUTHORITY_BOUNDARY_CASE_A_QTY_UNRESOLVED_REUSED
            ),
        }
    if has_b:
        return {
            "POSITION_OBSERVATION_CLASS": CASE_B_TARGET_ZERO,
            "POSITION_RESPONSE_OBSERVED": True,
            "TARGET_INSTRUMENT_ROW_OBSERVED": True,
            "POSITION_STATE_OBSERVED": True,
            "TARGET_POSITION_ZERO_PROVEN": True,
            "TARGET_POSITION_NONZERO_PROVEN": False,
            "P08_CLOSED": False,
            "P08_VERDICT": "P08_NOT_CLOSED_ZERO_ROW_DOES_NOT_SATISFY_NONZERO_PROOF",
            "NEXT_AUTHORITY_BOUNDARY": NEXT_AUTHORITY_BOUNDARY_CASE_B_REUSED,
        }
    if has_f:
        return {
            "POSITION_OBSERVATION_CLASS": CASE_F_AMBIGUOUS,
            "POSITION_RESPONSE_OBSERVED": True,
            "TARGET_INSTRUMENT_ROW_OBSERVED": False,
            "POSITION_STATE_OBSERVED": False,
            "TARGET_POSITION_ZERO_PROVEN": False,
            "TARGET_POSITION_NONZERO_PROVEN": False,
            "P08_CLOSED": False,
            "P08_VERDICT": "P08_NOT_CLOSED_AMBIGUOUS_OR_CONTRADICTORY_ROWS",
            "NEXT_AUTHORITY_BOUNDARY": NEXT_AUTHORITY_BOUNDARY_CASE_F_REUSED,
        }
    if has_d:
        return {
            "POSITION_OBSERVATION_CLASS": CASE_D_TARGET_NOT_OBSERVED,
            "POSITION_RESPONSE_OBSERVED": True,
            "TARGET_INSTRUMENT_ROW_OBSERVED": False,
            "POSITION_STATE_OBSERVED": False,
            "TARGET_POSITION_ZERO_PROVEN": False,
            "TARGET_POSITION_NONZERO_PROVEN": False,
            "P08_CLOSED": False,
            "P08_VERDICT": "P08_NOT_CLOSED_TARGET_INSTRUMENT_NOT_OBSERVED",
            "NEXT_AUTHORITY_BOUNDARY": NEXT_AUTHORITY_BOUNDARY_CASE_D_REUSED,
        }
    if all_c:
        return {
            "POSITION_OBSERVATION_CLASS": CASE_C_EMPTY_DATA_NOT_ZERO,
            "POSITION_RESPONSE_OBSERVED": True,
            "TARGET_INSTRUMENT_ROW_OBSERVED": False,
            "POSITION_STATE_OBSERVED": False,
            "TARGET_POSITION_ZERO_PROVEN": False,
            "TARGET_POSITION_NONZERO_PROVEN": False,
            "P08_CLOSED": False,
            "P08_VERDICT": "P08_NOT_CLOSED_EMPTY_DATA_REMAINS_NOT_ZERO",
            "NEXT_AUTHORITY_BOUNDARY": NEXT_AUTHORITY_BOUNDARY_CASE_C_REMAINS,
        }
    if has_e:
        return {
            "POSITION_OBSERVATION_CLASS": CASE_E_HTTP_OR_OKX_ERROR,
            "POSITION_RESPONSE_OBSERVED": any(
                item.get("POSITION_RESPONSE_OBSERVED") for item in exchanges
            ),
            "TARGET_INSTRUMENT_ROW_OBSERVED": False,
            "POSITION_STATE_OBSERVED": False,
            "TARGET_POSITION_ZERO_PROVEN": False,
            "TARGET_POSITION_NONZERO_PROVEN": False,
            "P08_CLOSED": False,
            "P08_VERDICT": "P08_NOT_CLOSED_HTTP_OR_OKX_OR_TRANSPORT_ERROR",
            "NEXT_AUTHORITY_BOUNDARY": NEXT_AUTHORITY_BOUNDARY_CASE_E_REUSED,
        }
    return {
        "POSITION_OBSERVATION_CLASS": CASE_F_AMBIGUOUS,
        "POSITION_RESPONSE_OBSERVED": True,
        "TARGET_INSTRUMENT_ROW_OBSERVED": False,
        "POSITION_STATE_OBSERVED": False,
        "TARGET_POSITION_ZERO_PROVEN": False,
        "TARGET_POSITION_NONZERO_PROVEN": False,
        "P08_CLOSED": False,
        "P08_VERDICT": "P08_NOT_CLOSED_UNCLASSIFIED_PACKAGE",
        "NEXT_AUTHORITY_BOUNDARY": NEXT_AUTHORITY_BOUNDARY_CASE_F_REUSED,
    }


def _should_issue_get2_v1(first: Mapping[str, Any]) -> bool:
    return (
        str(first.get("POSITION_OBSERVATION_CLASS") or "") == CASE_C_EMPTY_DATA_NOT_ZERO
        and str(first.get("RESULT_CLASS") or "") == RESULT_CLASS_200_OKX_0
        and str(first.get("GET_ERROR") or "") == ""
    )


def _should_issue_get3_v1(first: Mapping[str, Any], second: Mapping[str, Any] | None) -> bool:
    if second is None:
        return False
    if not _should_issue_get2_v1(first):
        return False
    if str(second.get("RESULT_CLASS") or "") != RESULT_CLASS_200_OKX_0:
        return False
    if bool(second.get("TARGET_INSTRUMENT_ROW_OBSERVED")):
        return False
    second_class = str(second.get("POSITION_OBSERVATION_CLASS") or "")
    if second_class in {
        CASE_A_TARGET_NONZERO,
        CASE_B_TARGET_ZERO,
        CASE_E_HTTP_OR_OKX_ERROR,
        CASE_F_AMBIGUOUS,
    }:
        return False
    return second_class in {CASE_C_EMPTY_DATA_NOT_ZERO, CASE_D_TARGET_NOT_OBSERVED}


def execute_p08_empty_data_not_zero_gets_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    evidence_root: Path,
    vault_file: Path | str | None = None,
    transport: LiveCanaryTransportV1 | None = None,
) -> dict[str, Any]:
    """Perform the minimum necessary positions GETs and persist evidence."""
    owned = str(owner_go or "").strip()
    if owned != OWNER_GO:
        raise P08EmptyDataNotZeroError("OWNER_GO_MISMATCH")
    bound_sha = str(origin_main_sha or "").strip()
    if bound_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise P08EmptyDataNotZeroError("ORIGIN_MAIN_SHA_MISMATCH")
    if REUSED_REST_HOST != AUTHORIZED_HOST:
        raise P08EmptyDataNotZeroError("HOST_MISMATCH")

    unfiltered = build_account_positions_query_v1()
    instid_query = build_account_positions_query_v1(inst_id=TARGET_INSTRUMENT_ID)
    insttype_query = build_account_positions_query_v1(inst_type=TARGET_INST_TYPE)
    if unfiltered.query or unfiltered.inst_id_filter_present:
        raise P08EmptyDataNotZeroError("GET1_MUST_BE_UNFILTERED")
    if not instid_query.inst_id_filter_present or instid_query.query != {
        "instId": TARGET_INSTRUMENT_ID
    }:
        raise P08EmptyDataNotZeroError("GET2_INSTID_QUERY_INVALID")
    if insttype_query.query != {"instType": TARGET_INST_TYPE}:
        raise P08EmptyDataNotZeroError("GET3_INSTTYPE_QUERY_INVALID")

    productive = transport is None
    secretref_identity: dict[str, Any] | None = None
    if productive:
        if vault_file is None or not str(vault_file).strip():
            raise P08EmptyDataNotZeroError("VAULT_FILE_REQUIRED")
        secretref_identity = secretref_identity_without_values_v1(vault_file=vault_file)
        transport = UrllibLiveCanaryTransportV1(wire_send_enabled=True)
    if isinstance(transport, UrllibLiveCanaryTransportV1) and not bool(
        getattr(transport, "wire_send_enabled", False)
    ):
        raise P08EmptyDataNotZeroError("PRODUCTIVE_WIRE_DISABLED")

    client = LiveCanaryHttpClientV1(
        rest_base=REUSED_REST_BASE,
        rest_host=REUSED_REST_HOST,
        transport=transport,
        max_request_count=MAX_NETWORK_REQUEST_COUNT,
        max_retries=DEFAULT_MAX_RETRIES,
        timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
    )
    handle = None
    owner_go_consumed = False
    exchanges: list[dict[str, Any]] = []
    raw_exchanges: list[dict[str, Any]] = []
    first_received_ms: int | None = None
    last_received_ms: int | None = None
    planned = (
        (1, GET_1_ROLE, unfiltered.path_with_query(), dict(unfiltered.query)),
        (2, GET_2_ROLE, instid_query.path_with_query(), dict(instid_query.query)),
        (3, GET_3_ROLE, insttype_query.path_with_query(), dict(insttype_query.query)),
    )

    def _issue(index: int, role: str, endpoint: str, query: dict[str, str]) -> dict[str, Any]:
        nonlocal owner_go_consumed, first_received_ms, last_received_ms
        if _path_only_v1(endpoint) != ENDPOINT:
            raise P08EmptyDataNotZeroError("ENDPOINT_MUST_BE_POSITIONS")
        if "?" in ENDPOINT:
            raise P08EmptyDataNotZeroError("ENDPOINT_CONTRACT_DRIFT")
        parsed = urlparse(f"{REUSED_REST_BASE}{endpoint}")
        if parsed.path != ENDPOINT:
            raise P08EmptyDataNotZeroError("SIGNED_REQUEST_TARGET_MISMATCH")
        if parsed.hostname != AUTHORIZED_HOST:
            raise P08EmptyDataNotZeroError("HOST_MISMATCH")
        auth_headers: dict[str, str] = {}
        header_presence = _header_presence_v1({})
        request_time = _utc_now_iso_v1()
        http_status: int | None = None
        body_bytes = b""
        get_error: str | None = None
        send_attempted = False
        redirect_followed = False
        redirect_status: int | None = None
        received_ms: int | None = None
        response_headers_safe: dict[str, str] = {}
        elapsed_seconds: float | None = None
        try:
            if productive:
                url = f"{REUSED_REST_BASE}{endpoint}"
                auth_headers = build_okx_live_canary_auth_headers_v1(
                    handle=handle, url=url, method="GET"
                )
                auth_headers["User-Agent"] = USER_AGENT_CANARY
            header_presence = _header_presence_v1(auth_headers)
            response = client.get(endpoint=endpoint, headers=auth_headers or None)
            send_attempted = True
            owner_go_consumed = True
            received_ms = default_local_monotonic_ms_v1()
            if first_received_ms is None:
                first_received_ms = received_ms
            last_received_ms = received_ms
            http_status = int(response.status_code)
            body_bytes = bytes(response.body_bytes)
            redirect_followed = bool(response.redirect_followed)
            redirect_status = response.redirect_status
            elapsed_seconds = float(response.elapsed_seconds)
            response_headers_safe = dict(response.response_headers_safe or {})
            if response.method != "GET":
                raise P08EmptyDataNotZeroError("NON_GET_RESPONSE")
            if redirect_followed:
                raise P08EmptyDataNotZeroError("REDIRECT_FOLLOWED")
        except LiveCanaryHttpError as exc:
            send_attempted = True
            owner_go_consumed = True
            get_error = str(exc)
        finally:
            auth_headers.clear()
        response_time = _utc_now_iso_v1()
        payload: dict[str, Any] | None = None
        parse_error: str | None = None
        if body_bytes:
            try:
                payload = parse_json_object_v1(body_bytes)
            except LiveCanaryHttpError as exc:
                parse_error = str(exc)
        venue_code = str((payload or {}).get("code") or "") if payload else None
        venue_msg_raw = str((payload or {}).get("msg") or "")[:200] if payload else None
        venue_msg = sanitize_okx_message_v1(venue_msg_raw)
        data = (payload or {}).get("data") if payload else None
        data_row_count = len(data) if isinstance(data, list) else None
        result_class = classify_http_okx_result_v1(
            http_status=http_status,
            venue_code=venue_code,
            get_error=get_error,
        )
        body_sha256 = hashlib.sha256(body_bytes).hexdigest() if body_bytes else None
        window: dict[str, Any] | None = None
        if result_class == RESULT_CLASS_200_OKX_0 and payload is not None:
            window = adjudicate_prerequisite_08_window_v1(
                positions_payload=payload,
                instrument_id=TARGET_INSTRUMENT_ID,
                body_sha256=body_sha256,
            )
        observation = classify_position_observation_v1(
            result_class=result_class,
            payload=payload,
            window=window,
        )
        if (
            observation["POSITION_OBSERVATION_CLASS"] == CASE_C_EMPTY_DATA_NOT_ZERO
            and observation["TARGET_POSITION_ZERO_PROVEN"]
        ):
            raise P08EmptyDataNotZeroError("EMPTY_DATA_MUST_NOT_BE_PROMOTED_TO_ZERO")
        record = {
            "GET_INDEX": index,
            "GET_ROLE": role,
            "ENDPOINT": endpoint,
            "ENDPOINT_PATH": ENDPOINT,
            "QUERY_PARAMETERS": query,
            "INSTID_FILTER_USED": "instId" in query,
            "INSTTYPE_FILTER_USED": "instType" in query,
            "REQUEST_TIME_UTC": request_time,
            "RESPONSE_TIME_UTC": response_time,
            "HTTP_STATUS": http_status,
            "OKX_CODE": venue_code,
            "OKX_MESSAGE": venue_msg,
            "SANITIZED_OKX_MESSAGE": venue_msg,
            "SEND_ATTEMPTED": send_attempted,
            "GET_ERROR": get_error,
            "PARSE_ERROR": parse_error,
            "BODY_BYTES": len(body_bytes),
            "BODY_SHA256": body_sha256,
            "BYTE_IDENTICAL_HISTORICAL_P08_EMPTY_ENVELOPE_SHA": (
                body_sha256 == HISTORICAL_P08_BODY_SHA256
            ),
            "BYTE_IDENTICAL_EMPTY_SHA_IS_NOT_CURRENT_08_PROOF": True,
            "DATA_ROW_COUNT": data_row_count,
            "RAW_DATA_SHAPE": (
                "DATA_LIST"
                if isinstance(data, list)
                else "NO_PARSEABLE_PAYLOAD"
                if payload is None
                else "DATA_NOT_LIST"
            ),
            "RESULT_CLASS": result_class,
            "REDACTED_PAYLOAD": sanitize_positions_payload_v1(payload),
            "REDIRECT_FOLLOWED": redirect_followed,
            "REDIRECT_STATUS": redirect_status,
            "ELAPSED_SECONDS": elapsed_seconds,
            "RESPONSE_HEADERS_SAFE": dict(response_headers_safe)
            if response_headers_safe
            else safe_response_headers_v1({}),
            "AUTH_HEADER_SENT": bool(header_presence.get("AUTH_KEY_HEADER_PRESENT")),
            "HEADER_PRESENCE": header_presence,
            "LOCAL_RESPONSE_RECEIVED_AT": received_ms,
            "TARGET_POSITION_QTY_NUMERIC": (window or {}).get("TARGET_POSITION_QTY_NUMERIC"),
            **observation,
            "WINDOW": window,
            "EMPTY_DATA_IS_ZERO": False,
            "ABSENT_TARGET_ROW_IS_ZERO": False,
            "FILTERED_EMPTY_IS_ZERO": False,
            "TYPED_EMPTY_IS_ZERO": False,
        }
        body_utf8 = _body_utf8_exact_v1(body_bytes)
        raw = {
            "DOCUMENT_CLASS": "P08_EMPTY_DATA_NOT_ZERO_FIRST_PARTY_RAW_EXCHANGE_V1",
            "DOCUMENT_ROLE": "FORENSIC_RAW_NOT_CANONICAL_NOT_ADJUDICATION",
            "AUTHORITY": "NONE",
            "THIS_ARTIFACT_IS_NOT_CANONICAL": True,
            "GET_INDEX": index,
            "GET_ROLE": role,
            "METHOD": "GET",
            "HOST": REUSED_REST_HOST,
            "ENDPOINT": endpoint,
            "ENDPOINT_PATH": ENDPOINT,
            "QUERY_PARAMETERS": query,
            "REQUEST_TIME_UTC": request_time,
            "RESPONSE_TIME_UTC": response_time,
            "HTTP_STATUS": http_status,
            "BODY_BYTES": len(body_bytes),
            "BODY_SHA256": body_sha256,
            "BODY_UTF8_EXACT": body_utf8,
            "BODY_WAS_JSON_RESERIALIZED": False,
            "RESPONSE_HEADERS_SAFE": record["RESPONSE_HEADERS_SAFE"],
            "REDIRECT_FOLLOWED": redirect_followed,
            "REDIRECT_STATUS": redirect_status,
            "ELAPSED_SECONDS": elapsed_seconds,
            "SEND_ATTEMPTED": send_attempted,
            "GET_ERROR": get_error,
            "PARSE_ERROR": parse_error,
            "SECRET_VALUES_INCLUDED": False,
        }
        raw_exchanges.append(raw)
        exchanges.append(record)
        return record

    try:
        if productive:
            backend = build_file_secretref_vault_backend_v1(vault_file=vault_file)
            handle = resolve_and_load_live_canary_secretref_ephemeral_v1(
                secret_reference=REUSED_SECRETREF_URI,
                vault_backend=backend,
                credential_class=REUSED_CREDENTIAL_CLASS,
            )
        first = _issue(*planned[0])
        second: dict[str, Any] | None = None
        if _should_issue_get2_v1(first):
            second = _issue(*planned[1])
        if _should_issue_get3_v1(first, second):
            _issue(*planned[2])
    finally:
        if handle is not None:
            release_live_canary_ephemeral_material_v1(handle)

    expected_gets = len(exchanges)
    counters = _assert_positions_gets_zero_writes(client, expected_get_count=expected_gets)
    http_exchange_count = _exchange_count_v1(transport)
    if http_exchange_count != expected_gets:
        raise P08EmptyDataNotZeroError("HTTP_EXCHANGE_COUNT_MISMATCH")
    if http_exchange_count > MAX_HTTP_EXCHANGE_COUNT:
        raise P08EmptyDataNotZeroError("HTTP_EXCHANGE_COUNT_EXCEEDED")

    package = classify_package_observation_v1(tuple(exchanges))
    adjudication_ms = default_local_monotonic_ms_v1()
    freshness = evaluate_freshness_at_adjudication_v1(
        response_received_monotonic_ms=last_received_ms,
        adjudication_monotonic_ms=adjudication_ms,
    )
    unfiltered_empty = bool(
        exchanges and exchanges[0]["POSITION_OBSERVATION_CLASS"] == CASE_C_EMPTY_DATA_NOT_ZERO
    )
    typed_nonempty = any(
        item["GET_ROLE"] == GET_3_ROLE
        and isinstance(item.get("DATA_ROW_COUNT"), int)
        and int(item["DATA_ROW_COUNT"]) > 0
        for item in exchanges
    )
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    pack = Path(evidence_root) / run_id
    standing = {
        "G_POSMODE_SUBMIT_BODY_PROVEN": False,
        "P08_CLOSED_INFERRED": False,
        "ACCOUNT_CONFIG_USED_AS_POSSIDE_PROOF": False,
        "CLASS_D_CONSUMED": False,
        "Z2AP_CONSUMED": False,
        "EXECUTION_READY": False,
        "EMPTY_DATA_IS_ZERO": False,
        "ABSENT_TARGET_ROW_IS_ZERO": False,
        "FILTERED_EMPTY_IS_ZERO": False,
        "TYPED_EMPTY_IS_ZERO": False,
    }
    first_sha = exchanges[0].get("BODY_SHA256") if exchanges else None
    snapshot = {
        "DOCUMENT_CLASS": "P08_EMPTY_DATA_NOT_ZERO_GET_PACKAGE_V1",
        "DOCUMENT_ROLE": "GET_ONLY_FRESH_EVIDENCE_NON_SSOT",
        "AUTHORITY": "NONE",
        "THIS_ARTIFACT_IS_NOT_CANONICAL": True,
        "OWNER_GO": owned,
        "OWNER_GO_CONSUMED": owner_go_consumed,
        "THIS_SLICE": THIS_SLICE,
        "BOUND_ORIGIN_MAIN_SHA": bound_sha,
        "AUTHORIZED_ENDPOINT": "GET /api/v5/account/positions",
        "ENDPOINT": ENDPOINT,
        "METHOD": "GET",
        "HOST": REUSED_REST_HOST,
        "VENUE": REUSED_VENUE,
        "TARGET_INSTRUMENT": TARGET_INSTRUMENT_ID,
        "TARGET_INSTRUMENT_ID": TARGET_INSTRUMENT_ID,
        "TARGET_INST_TYPE": TARGET_INST_TYPE,
        "COUNTERS": counters,
        "ACTUAL_NETWORK_REQUEST_COUNT": int(counters.get("GET_REQUEST_COUNT", 0) or 0),
        "HTTP_EXCHANGE_COUNT": http_exchange_count,
        "GET_REQUEST_COUNT": int(counters.get("GET_REQUEST_COUNT", 0) or 0),
        "WRITE_REQUEST_COUNT": int(counters.get("WRITE_REQUEST_COUNT", 0) or 0),
        "POST_COUNT": 0,
        "RETRY_COUNT": 0,
        "ENDPOINTS_USED": list(client.counters.endpoints_used),
        "METHODS_USED": list(client.counters.methods_used),
        "AUTH_PATH": {
            "CREDENTIAL_CLASS": REUSED_CREDENTIAL_CLASS,
            "SECRETREF_URI": REUSED_SECRETREF_URI,
            "SIGNER": "build_okx_live_canary_auth_headers_v1",
            "HTTP_CLIENT": "LiveCanaryHttpClientV1",
            "TRANSPORT": type(transport).__name__,
        },
        "AUTH_SIGNING_OWNER": "build_okx_live_canary_auth_headers_v1",
        "SANITIZED_SECRETREF": REUSED_SECRETREF_URI,
        "TARGET_SECRETREF_URI": REUSED_SECRETREF_URI,
        "SECRET_VALUES_INCLUDED": False,
        "SECRETREF_IDENTITY": secretref_identity,
        "EXCHANGES": exchanges,
        "HISTORICAL_P08_EVIDENCE_PACK": HISTORICAL_P08_EVIDENCE_PACK,
        "HISTORICAL_P08_IS_CURRENT_08_PROOF": False,
        "BYTE_IDENTICAL_HISTORICAL_P08_EMPTY_ENVELOPE_SHA": first_sha == HISTORICAL_P08_BODY_SHA256,
        "BYTE_IDENTICAL_EMPTY_SHA_IS_NOT_CURRENT_08_PROOF": True,
        "UNFILTERED_EMPTY_AND_TYPED_NONEMPTY": unfiltered_empty and typed_nonempty,
        "UNFILTERED_EMPTY_AND_TYPED_NONEMPTY_IS_NOT_TARGET_ZERO": True,
        "FUNDING_GET_PERFORMED": False,
        "POSITIONS_GET_PERFORMED": True,
        "BALANCE_GET_PERFORMED": False,
        "CONFIG_GET_PERFORMED": False,
        "MAX_SIZE_GET_PERFORMED": False,
        "PUBLIC_GET_PERFORMED": False,
        "POST_PERFORMED": False,
        "ORDER_PERFORMED": False,
        "ORDER_SUBMIT_EXECUTED": False,
        "POSITION_CREATION_EXECUTED": False,
        "POSITION_MODIFICATION_EXECUTED": False,
        "EXECUTION_PERFORMED": False,
        "LIVE_EXECUTION": False,
        "CANARY_EXECUTION": False,
        "LIVE_ARMING_PERFORMED": False,
        "WHITELIST_MUTATION_PERFORMED": False,
        "FUNDING_ACTION": False,
        "CORE_CHANGED": False,
        "NEW_AUTHORITY_CREATED": False,
        "ATLAS_AUTHORITY": "NONE",
        "LANDSCAPE_AUTHORITY": "NONE",
        "LIVE_AUTHORIZED": False,
        "TESTNET_AUTHORIZED": False,
        "CANARY_AUTHORIZED": False,
        "TRANSFER_ALLOWED": False,
        "POST_ALLOWED": False,
        "ORDER_ALLOWED": False,
        "SUBMIT_UNLOCKED": False,
        **standing,
        **package,
    }
    first_window = exchanges[0].get("WINDOW") if exchanges else None
    adjudication = {
        "DOCUMENT_CLASS": "P08_EMPTY_DATA_NOT_ZERO_WINDOW_ADJUDICATION_V1",
        "DOCUMENT_ROLE": "INTERPRETATION_NOT_RAW_EVIDENCE_NOT_SSOT",
        "AUTHORITY": "NONE",
        "OWNER_GO": owned,
        "BOUND_ORIGIN_MAIN_SHA": bound_sha,
        "P08_CANONICAL_DEFINITION": P08_CANONICAL_DEFINITION_REUSED,
        "CLASSIFIER": "classify_target_position_state_v1",
        "PACKAGE_CLASSIFIER": "classify_package_observation_v1",
        "FRESHNESS_POLICY": FRESHNESS_POLICY,
        "FRESHNESS_POLICY_MAX_AGE_MS": POSITION_OBSERVATION_FRESHNESS_MAX_AGE_MS,
        "AGE_EVALUATION_POINT_THIS_WINDOW": "ADJUDICATION_AFTER_LAST_GET_NOT_FLATTEN_SEND",
        "FLATTEN_PRE_SEND_PERMIT_EVALUATED": False,
        "LOCAL_RESPONSE_RECEIVED_AT": last_received_ms,
        "FIRST_RESPONSE_RECEIVED_AT": first_received_ms,
        "ADJUDICATION_MONOTONIC_MS": adjudication_ms,
        "GET_REQUEST_COUNT": expected_gets,
        "HTTP_EXCHANGE_COUNT": http_exchange_count,
        "EXCHANGE_CLASSES": [
            str(item.get("POSITION_OBSERVATION_CLASS") or "") for item in exchanges
        ],
        "UNFILTERED_EMPTY_AND_TYPED_NONEMPTY": unfiltered_empty and typed_nonempty,
        "UNFILTERED_EMPTY_AND_TYPED_NONEMPTY_IS_NOT_TARGET_ZERO": True,
        "HYPOTHESIS": (
            "OKX net-mode listings may omit explicit zero rows; empty data is not a "
            "zero-row observation. This sentence is interpretation context, not proof."
        ),
        "HYPOTHESIS_IS_NOT_PROOF": True,
        **freshness,
        **(first_window or {}),
        **package,
        "G_POSMODE_SUBMIT_BODY_PROVEN": False,
        "POST_PERFORMED": False,
        "POSITION_MUTATION": False,
        "LIVE_TESTNET_CANARY": False,
        "SECRET_MUTATION": False,
        "CLASS_D_CONSUMED": False,
        "Z2AP_CONSUMED": False,
        "EXECUTION_READY": False,
        "EMPTY_DATA_IS_ZERO": False,
        "ABSENT_TARGET_ROW_IS_ZERO": False,
        "FILTERED_EMPTY_IS_ZERO": False,
        "TYPED_EMPTY_IS_ZERO": False,
        "P09_WORK_PERFORMED": False,
        "EARLIEST_UNRESOLVED_DEPENDENCY": (
            "EXECUTION_PREREQUISITE_08_TARGET_POSITION_NONZERO_PROVEN"
            if not package["P08_CLOSED"]
            else package["NEXT_AUTHORITY_BOUNDARY"]
        ),
        "EXECUTION_PREREQUISITE_08_TARGET_POSITION_NONZERO_PROVEN": package[
            "TARGET_POSITION_NONZERO_PROVEN"
        ],
        "TARGET_INSTRUMENT_ID": TARGET_INSTRUMENT_ID,
    }
    summary = {
        "DOCUMENT_CLASS": "P08_EMPTY_DATA_NOT_ZERO_GET_PACKAGE_V1",
        "DOCUMENT_ROLE": "DERIVED_NON_SSOT",
        "OWNER_GO": owned,
        "OWNER_GO_CONSUMED": owner_go_consumed,
        "THIS_SLICE": THIS_SLICE,
        "BOUND_ORIGIN_MAIN_SHA": bound_sha,
        "ENDPOINT": ENDPOINT,
        "METHOD": "GET",
        "HOST": REUSED_REST_HOST,
        "TARGET_INSTRUMENT_ID": TARGET_INSTRUMENT_ID,
        "TARGET_INST_TYPE": TARGET_INST_TYPE,
        "GET_ROLES_PERFORMED": [item["GET_ROLE"] for item in exchanges],
        "RESULT_CLASS": exchanges[0]["RESULT_CLASS"] if exchanges else None,
        "GET_REQUEST_COUNT": int(counters.get("GET_REQUEST_COUNT", 0) or 0),
        "HTTP_EXCHANGE_COUNT": http_exchange_count,
        "RETRY_COUNT": 0,
        "POST_COUNT": 0,
        "WRITE_REQUEST_COUNT": int(counters.get("WRITE_REQUEST_COUNT", 0) or 0),
        "PRIVATE_GET_EXECUTED": owner_go_consumed,
        "POSITION_RESPONSE_OBSERVED": package["POSITION_RESPONSE_OBSERVED"],
        "TARGET_INSTRUMENT_ROW_OBSERVED": package["TARGET_INSTRUMENT_ROW_OBSERVED"],
        "POSITION_STATE_OBSERVED": package["POSITION_STATE_OBSERVED"],
        "TARGET_POSITION_ZERO_PROVEN": package["TARGET_POSITION_ZERO_PROVEN"],
        "TARGET_POSITION_NONZERO_PROVEN": package["TARGET_POSITION_NONZERO_PROVEN"],
        "POSITION_OBSERVATION_CLASS": package["POSITION_OBSERVATION_CLASS"],
        "P08_CLOSED": package["P08_CLOSED"],
        "P08_VERDICT": package["P08_VERDICT"],
        "G_POSMODE_SUBMIT_BODY_PROVEN": False,
        "ORDER_SUBMIT_EXECUTED": False,
        "POSITION_CREATION_EXECUTED": False,
        "POSITION_MODIFICATION_EXECUTED": False,
        "FUNDING_ACTION": False,
        "LIVE_EXECUTION": False,
        "CANARY_EXECUTION": False,
        "CORE_CHANGED": False,
        "NEW_AUTHORITY_CREATED": False,
        "ATLAS_AUTHORITY": "NONE",
        "LANDSCAPE_AUTHORITY": "NONE",
        "NEXT_AUTHORITY_BOUNDARY": package["NEXT_AUTHORITY_BOUNDARY"],
        "MERGE_AUTHORIZED": False,
        "UNFILTERED_EMPTY_AND_TYPED_NONEMPTY": unfiltered_empty and typed_nonempty,
        "HTTP_STATUS": exchanges[0]["HTTP_STATUS"] if exchanges else None,
        "OKX_CODE": exchanges[0]["OKX_CODE"] if exchanges else None,
        "GET_ERROR": exchanges[0].get("GET_ERROR") if exchanges else None,
        "PARSE_ERROR": exchanges[0].get("PARSE_ERROR") if exchanges else None,
    }
    census = {
        "DOCUMENT_CLASS": "P08_POSITION_OBSERVATION_PATH_CENSUS_V1",
        "DOCUMENT_ROLE": "NAVIGATION_INVENTORY_NOT_SSOT_NOT_AUTHORITY",
        "AUTHORITY": "NONE",
        "BOUND_ORIGIN_MAIN_SHA": bound_sha,
        "PREDECESSOR_SLICE": "11.13.5.P08_POSITION_OBSERVATION",
        "PREDECESSOR_EVIDENCE_PACK": HISTORICAL_P08_EVIDENCE_PACK,
        "PREDECESSOR_IS_HISTORICAL": True,
        "PREDECESSOR_IS_NOT_CURRENT_08_PROOF": True,
        "CURRENT_PACKAGE": THIS_SLICE,
        "PRODUCTIVE_OWNERS": {
            "PREDECESSOR_EXECUTOR": (
                "src/ops/section_11_13_5_p08_position_observation_v1/execute_v1.py"
            ),
            "THIS_EXECUTOR": ("src/ops/section_11_13_5_p08_empty_data_not_zero_v1/execute_v1.py"),
            "CLASSIFIER": (
                "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/pre_submit_state_v1.py"
            ),
            "QUERY_GRAMMAR": (
                "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
                "account_positions_query_grammar_v1.py"
            ),
            "HTTP_CLIENT": (
                "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/http_client_v1.py"
            ),
            "PERSISTENCE": ("src/ops/section_11_13_5_p08_empty_data_not_zero_v1/persist_v1.py"),
        },
        "TAXONOMY": {
            "CASE_A_TARGET_NONZERO": CASE_A_TARGET_NONZERO,
            "CASE_B_TARGET_ZERO": CASE_B_TARGET_ZERO,
            "CASE_C_EMPTY_DATA_NOT_ZERO": CASE_C_EMPTY_DATA_NOT_ZERO,
            "CASE_D_TARGET_NOT_OBSERVED": CASE_D_TARGET_NOT_OBSERVED,
            "CASE_E_HTTP_OR_OKX_ERROR": CASE_E_HTTP_OR_OKX_ERROR,
            "CASE_F_AMBIGUOUS": CASE_F_AMBIGUOUS,
        },
        "CLAIMS_SNAPSHOT": dict(CLAIMS),
        "CALLERS_THIS_PACKAGE": [
            "scripts/ops/run_section_11_13_5_p08_empty_data_not_zero_v1.py",
            "tests/ops/test_section_11_13_5_p08_empty_data_not_zero_v1.py",
        ],
        "PERSISTENCE_SURFACES": [
            "GET_01_UNFILTERED.raw.json",
            "GET_02_INSTID.raw.json",
            "GET_03_INSTTYPE.raw.json",
            "GET_SNAPSHOT.sanitized.json",
            "ADJUDICATION.json",
            "SUMMARY.json",
            "CENSUS.json",
            "claims.json",
            "MANIFEST.sha256",
        ],
        "TEST_OWNERS": [
            "tests/ops/test_section_11_13_5_p08_empty_data_not_zero_v1.py",
            "tests/ops/test_section_11_13_5_p08_empty_data_not_zero_persist_v1.py",
        ],
    }
    verified = persist_p08_empty_data_not_zero_evidence_v1(
        pack=pack,
        origin_main_sha=bound_sha,
        snapshot=snapshot,
        adjudication=adjudication,
        summary=summary,
        census=census,
        raw_exchanges=tuple(raw_exchanges),
    )
    return {
        "EVIDENCE_PACK": str(pack),
        "MANIFEST_VERIFY_RC": verified.get("MANIFEST_VERIFY_RC"),
        "summary": summary,
        "adjudication": adjudication,
    }
