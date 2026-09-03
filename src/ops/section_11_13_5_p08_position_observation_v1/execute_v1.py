"""Execute exactly one unfiltered authenticated GET /api/v5/account/positions.

Constructs LiveCanaryHttpClientV1 itself. Reuses the existing canary GET
signer and live-canary SecretRef. No POST, transfer, order, funding GET,
config GET, whitelist mutation, or capital movement. No second request on
any outcome. P08 closes only on CASE_A. posSide in the GET row is not
submit-body proof.
"""

from __future__ import annotations

import hashlib
import json
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
    TARGET_POSITION_NOT_OBSERVED,
    TARGET_POSITION_ZERO_PROVEN,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.prerequisite_08_fresh_position_observation_v1 import (
    adjudicate_prerequisite_08_window_v1,
    evaluate_freshness_at_adjudication_v1,
    sanitize_positions_payload_v1,
)
from src.ops.section_11_13_5_p08_position_observation_v1.constants_v1 import (
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
    MAX_HTTP_EXCHANGE_COUNT,
    MAX_NETWORK_REQUEST_COUNT,
    NEXT_AUTHORITY_BOUNDARY_CASE_A_QTY_NUMERIC,
    NEXT_AUTHORITY_BOUNDARY_CASE_A_QTY_UNRESOLVED,
    NEXT_AUTHORITY_BOUNDARY_CASE_B,
    NEXT_AUTHORITY_BOUNDARY_CASE_C,
    NEXT_AUTHORITY_BOUNDARY_CASE_D,
    NEXT_AUTHORITY_BOUNDARY_CASE_E,
    NEXT_AUTHORITY_BOUNDARY_CASE_F,
    OWNER_GO,
    P08_CANONICAL_DEFINITION,
    RESULT_CLASS_200_OKX_0,
    RESULT_CLASS_401_50110,
    RESULT_CLASS_OTHER,
    RESULT_CLASS_TRANSPORT,
    REUSED_CREDENTIAL_CLASS,
    REUSED_REST_BASE,
    REUSED_REST_HOST,
    REUSED_SECRETREF_URI,
    REUSED_VENUE,
    TARGET_INSTRUMENT_ID,
    THIS_SLICE,
)
from src.ops.section_11_13_5_p08_position_observation_v1.persist_v1 import (
    persist_p08_position_observation_evidence_v1,
)
from src.ops.section_11_13_5_post_z2ds_private_get_current_50110_egress_capture_v1.execute_v1 import (
    sanitize_okx_message_v1,
)


class P08PositionObservationError(RuntimeError):
    """Fail-closed one-shot P08 positions GET violation."""


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


def _assert_one_get_zero_writes(client: LiveCanaryHttpClientV1) -> dict[str, Any]:
    counters = client.counters.to_dict()
    if int(counters.get("GET_REQUEST_COUNT", 0) or 0) != 1:
        raise P08PositionObservationError("GET_COUNT_NOT_ONE")
    if int(counters.get("REQUEST_COUNT", 0) or 0) != 1:
        raise P08PositionObservationError("REQUEST_COUNT_NOT_ONE")
    if int(counters.get("WRITE_REQUEST_COUNT", 0) or 0) != 0:
        raise P08PositionObservationError("WRITE_REQUEST_DETECTED")
    if int(counters.get("TRANSFER_REQUEST_COUNT", 0) or 0) != 0:
        raise P08PositionObservationError("TRANSFER_REQUEST_DETECTED")
    if int(counters.get("ORDER_REQUEST_COUNT", 0) or 0) != 0:
        raise P08PositionObservationError("ORDER_REQUEST_DETECTED")
    if int(counters.get("ENTRY_SUBMIT_COUNT", 0) or 0) != 0:
        raise P08PositionObservationError("ENTRY_SUBMIT_DETECTED")
    if int(counters.get("FLATTEN_SUBMIT_COUNT", 0) or 0) != 0:
        raise P08PositionObservationError("FLATTEN_SUBMIT_DETECTED")
    if list(client.counters.endpoints_used) != [ENDPOINT]:
        raise P08PositionObservationError("ENDPOINT_SET_MISMATCH")
    if list(client.counters.methods_used) != ["GET"]:
        raise P08PositionObservationError("NON_GET_METHOD_DETECTED")
    return counters


def secretref_identity_without_values_v1(*, vault_file: Path | str) -> dict[str, Any]:
    """Prove SecretRef binding by URI and field lengths only. Never returns values."""
    path = Path(vault_file)
    if not path.is_file():
        raise P08PositionObservationError("VAULT_FILE_MISSING")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise P08PositionObservationError("VAULT_FILE_NOT_JSON") from exc
    if not isinstance(payload, Mapping):
        raise P08PositionObservationError("VAULT_FILE_NOT_OBJECT")
    if REUSED_SECRETREF_URI not in payload:
        raise P08PositionObservationError("SECRETREF_URI_UNBOUND")
    raw = payload[REUSED_SECRETREF_URI]
    if isinstance(raw, str):
        try:
            material = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise P08PositionObservationError("SECRETREF_MATERIAL_NOT_JSON") from exc
    elif isinstance(raw, Mapping):
        material = raw
    else:
        raise P08PositionObservationError("SECRETREF_MATERIAL_TYPE_FORBIDDEN")
    if not isinstance(material, Mapping):
        raise P08PositionObservationError("SECRETREF_MATERIAL_NOT_OBJECT")
    key_len = len(str(material.get("api_key") or "").strip())
    secret_len = len(str(material.get("api_secret") or "").strip())
    passphrase_len = len(str(material.get("passphrase") or "").strip())
    if key_len <= 0 or secret_len <= 0 or passphrase_len <= 0:
        raise P08PositionObservationError("CREDENTIAL_FIELDS_INCOMPLETE")
    return {
        "VAULT_FILE_PRESENT": True,
        "SECRETREF_URI_BOUND": True,
        "SECRETREF_URI": REUSED_SECRETREF_URI,
        "API_KEY_LEN": key_len,
        "API_SECRET_LEN": secret_len,
        "PASSPHRASE_LEN": passphrase_len,
        "VALUES_INCLUDED": False,
    }


def classify_http_okx_result_v1(
    *,
    http_status: int | None,
    venue_code: str | None,
    get_error: str | None,
) -> str:
    code = "" if venue_code is None else str(venue_code).strip()
    if get_error and http_status is None:
        return RESULT_CLASS_TRANSPORT
    if http_status == 200 and code == "0":
        return RESULT_CLASS_200_OKX_0
    if http_status == 401 and code == "50110":
        return RESULT_CLASS_401_50110
    return RESULT_CLASS_OTHER


def classify_position_observation_v1(
    *,
    result_class: str,
    payload: Mapping[str, Any] | None,
    window: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Map HTTP/OKX plus classifier onto CASE_A..F. Empty data is not zero."""
    if result_class != RESULT_CLASS_200_OKX_0 or window is None:
        return {
            "POSITION_OBSERVATION_CLASS": CASE_E_HTTP_OR_OKX_ERROR,
            "POSITION_RESPONSE_OBSERVED": result_class
            not in {RESULT_CLASS_TRANSPORT, RESULT_CLASS_OTHER}
            or payload is not None,
            "TARGET_INSTRUMENT_ROW_OBSERVED": False,
            "POSITION_STATE_OBSERVED": False,
            "TARGET_POSITION_ZERO_PROVEN": False,
            "TARGET_POSITION_NONZERO_PROVEN": False,
            "P08_CLOSED": False,
            "P08_VERDICT": "P08_NOT_CLOSED_HTTP_OR_OKX_OR_TRANSPORT_ERROR",
            "NEXT_AUTHORITY_BOUNDARY": NEXT_AUTHORITY_BOUNDARY_CASE_E,
        }

    data = payload.get("data") if isinstance(payload, Mapping) else None
    classifier_state = str(window.get("classifier_state") or "")
    classifier_reason = str(window.get("classifier_reason") or "")
    qty_numeric = str(window.get("TARGET_POSITION_QTY_NUMERIC") or "")

    if isinstance(data, list) and len(data) == 0:
        if EMPTY_DATA_IS_ZERO:
            raise P08PositionObservationError("EMPTY_DATA_MUST_NOT_BE_PROMOTED_TO_ZERO")
        return {
            "POSITION_OBSERVATION_CLASS": CASE_C_EMPTY_DATA_NOT_ZERO,
            "POSITION_RESPONSE_OBSERVED": True,
            "TARGET_INSTRUMENT_ROW_OBSERVED": False,
            "POSITION_STATE_OBSERVED": False,
            "TARGET_POSITION_ZERO_PROVEN": False,
            "TARGET_POSITION_NONZERO_PROVEN": False,
            "P08_CLOSED": False,
            "P08_VERDICT": "P08_NOT_CLOSED_EMPTY_DATA_IS_NOT_ZERO",
            "NEXT_AUTHORITY_BOUNDARY": NEXT_AUTHORITY_BOUNDARY_CASE_C,
        }

    if classifier_state == TARGET_POSITION_NONZERO_PROVEN:
        qty_pass = qty_numeric == "PASS"
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
                NEXT_AUTHORITY_BOUNDARY_CASE_A_QTY_NUMERIC
                if qty_pass
                else NEXT_AUTHORITY_BOUNDARY_CASE_A_QTY_UNRESOLVED
            ),
        }

    if classifier_state == TARGET_POSITION_ZERO_PROVEN:
        return {
            "POSITION_OBSERVATION_CLASS": CASE_B_TARGET_ZERO,
            "POSITION_RESPONSE_OBSERVED": True,
            "TARGET_INSTRUMENT_ROW_OBSERVED": True,
            "POSITION_STATE_OBSERVED": True,
            "TARGET_POSITION_ZERO_PROVEN": True,
            "TARGET_POSITION_NONZERO_PROVEN": False,
            "P08_CLOSED": False,
            "P08_VERDICT": "P08_NOT_CLOSED_ZERO_ROW_DOES_NOT_SATISFY_NONZERO_PROOF",
            "NEXT_AUTHORITY_BOUNDARY": NEXT_AUTHORITY_BOUNDARY_CASE_B,
        }

    if classifier_state == TARGET_POSITION_NOT_OBSERVED:
        return {
            "POSITION_OBSERVATION_CLASS": CASE_D_TARGET_NOT_OBSERVED,
            "POSITION_RESPONSE_OBSERVED": True,
            "TARGET_INSTRUMENT_ROW_OBSERVED": False,
            "POSITION_STATE_OBSERVED": False,
            "TARGET_POSITION_ZERO_PROVEN": False,
            "TARGET_POSITION_NONZERO_PROVEN": False,
            "P08_CLOSED": False,
            "P08_VERDICT": "P08_NOT_CLOSED_TARGET_INSTRUMENT_NOT_OBSERVED",
            "NEXT_AUTHORITY_BOUNDARY": NEXT_AUTHORITY_BOUNDARY_CASE_D,
        }

    if classifier_reason == "AMBIGUOUS_TARGET_POSITION_ROWS":
        return {
            "POSITION_OBSERVATION_CLASS": CASE_F_AMBIGUOUS,
            "POSITION_RESPONSE_OBSERVED": True,
            "TARGET_INSTRUMENT_ROW_OBSERVED": False,
            "POSITION_STATE_OBSERVED": False,
            "TARGET_POSITION_ZERO_PROVEN": False,
            "TARGET_POSITION_NONZERO_PROVEN": False,
            "P08_CLOSED": False,
            "P08_VERDICT": "P08_NOT_CLOSED_AMBIGUOUS_OR_CONTRADICTORY_ROWS",
            "NEXT_AUTHORITY_BOUNDARY": NEXT_AUTHORITY_BOUNDARY_CASE_F,
        }

    return {
        "POSITION_OBSERVATION_CLASS": CASE_F_AMBIGUOUS,
        "POSITION_RESPONSE_OBSERVED": payload is not None,
        "TARGET_INSTRUMENT_ROW_OBSERVED": False,
        "POSITION_STATE_OBSERVED": False,
        "TARGET_POSITION_ZERO_PROVEN": False,
        "TARGET_POSITION_NONZERO_PROVEN": False,
        "P08_CLOSED": False,
        "P08_VERDICT": f"P08_NOT_CLOSED_UNCLASSIFIED_OR_MALFORMED:{classifier_reason or classifier_state}",
        "NEXT_AUTHORITY_BOUNDARY": NEXT_AUTHORITY_BOUNDARY_CASE_F,
    }


def execute_single_p08_position_observation_get_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    evidence_root: Path,
    vault_file: Path | str | None = None,
    transport: LiveCanaryTransportV1 | None = None,
) -> dict[str, Any]:
    """Perform exactly one allowlisted unfiltered positions GET and persist evidence."""
    owned = str(owner_go or "").strip()
    if owned != OWNER_GO:
        raise P08PositionObservationError("OWNER_GO_MISMATCH")
    bound_sha = str(origin_main_sha or "").strip()
    if bound_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise P08PositionObservationError("ORIGIN_MAIN_SHA_MISMATCH")
    if REUSED_REST_HOST != AUTHORIZED_HOST:
        raise P08PositionObservationError("HOST_MISMATCH")
    query = build_account_positions_query_v1()
    if query.query or query.inst_id_filter_present or query.pos_id_filter_present:
        raise P08PositionObservationError("INSTID_FILTER_FORBIDDEN")
    endpoint = query.path_with_query()
    if endpoint != ENDPOINT:
        raise P08PositionObservationError("ENDPOINT_MUST_BE_UNFILTERED_POSITIONS")
    if "?" in ENDPOINT or ENDPOINT != "/api/v5/account/positions":
        raise P08PositionObservationError("ENDPOINT_CONTRACT_DRIFT")
    if ENDPOINT in FORBIDDEN_ENDPOINTS:
        raise P08PositionObservationError("MUTATION_ENDPOINT_FORBIDDEN")

    productive = transport is None
    secretref_identity: dict[str, Any] | None = None
    if productive:
        if vault_file is None or not str(vault_file).strip():
            raise P08PositionObservationError("VAULT_FILE_REQUIRED")
        secretref_identity = secretref_identity_without_values_v1(vault_file=vault_file)
        transport = UrllibLiveCanaryTransportV1(wire_send_enabled=True)
    if isinstance(transport, UrllibLiveCanaryTransportV1) and not bool(
        getattr(transport, "wire_send_enabled", False)
    ):
        raise P08PositionObservationError("PRODUCTIVE_WIRE_DISABLED")

    client = LiveCanaryHttpClientV1(
        rest_base=REUSED_REST_BASE,
        rest_host=REUSED_REST_HOST,
        transport=transport,
        max_request_count=MAX_NETWORK_REQUEST_COUNT,
        max_retries=DEFAULT_MAX_RETRIES,
        timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
    )
    auth_headers: dict[str, str] = {}
    header_presence: dict[str, Any] = _header_presence_v1({})
    handle = None
    request_time = _utc_now_iso_v1()
    http_status: int | None = None
    body_bytes = b""
    get_error: str | None = None
    send_attempted = False
    owner_go_consumed = False
    redirect_followed = False
    redirect_status: int | None = None
    received_ms: int | None = None
    try:
        url = f"{REUSED_REST_BASE}{ENDPOINT}"
        parsed = urlparse(url)
        if parsed.path != ENDPOINT or parsed.query:
            raise P08PositionObservationError("SIGNED_REQUEST_TARGET_MISMATCH")
        if parsed.hostname != AUTHORIZED_HOST:
            raise P08PositionObservationError("HOST_MISMATCH")
        if productive:
            backend = build_file_secretref_vault_backend_v1(vault_file=vault_file)
            handle = resolve_and_load_live_canary_secretref_ephemeral_v1(
                secret_reference=REUSED_SECRETREF_URI,
                vault_backend=backend,
                credential_class=REUSED_CREDENTIAL_CLASS,
            )
            auth_headers = build_okx_live_canary_auth_headers_v1(
                handle=handle, url=url, method="GET"
            )
            auth_headers["User-Agent"] = USER_AGENT_CANARY
        header_presence = _header_presence_v1(auth_headers)
        response = client.get(endpoint=ENDPOINT, headers=auth_headers or None)
        send_attempted = True
        owner_go_consumed = True
        received_ms = default_local_monotonic_ms_v1()
        http_status = int(response.status_code)
        body_bytes = bytes(response.body_bytes)
        redirect_followed = bool(response.redirect_followed)
        redirect_status = response.redirect_status
        if response.method != "GET":
            raise P08PositionObservationError("NON_GET_RESPONSE")
        if redirect_followed:
            raise P08PositionObservationError("REDIRECT_FOLLOWED")
    except LiveCanaryHttpError as exc:
        send_attempted = True
        owner_go_consumed = True
        get_error = str(exc)
    finally:
        auth_headers.clear()
        if handle is not None:
            release_live_canary_ephemeral_material_v1(handle)
    response_time = _utc_now_iso_v1()
    counters = client.counters.to_dict()
    http_exchange_count = _exchange_count_v1(transport)
    if get_error is None:
        counters = _assert_one_get_zero_writes(client)
        if http_exchange_count != MAX_HTTP_EXCHANGE_COUNT:
            raise P08PositionObservationError("HTTP_EXCHANGE_COUNT_NOT_ONE")
        if productive and http_exchange_count != 1:
            raise P08PositionObservationError("NETWORK_REQUEST_COUNT_NOT_ONE")
    elif http_exchange_count > MAX_HTTP_EXCHANGE_COUNT:
        raise P08PositionObservationError("HTTP_EXCHANGE_COUNT_EXCEEDED")

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
    adjudication_ms = default_local_monotonic_ms_v1()
    freshness = evaluate_freshness_at_adjudication_v1(
        response_received_monotonic_ms=received_ms,
        adjudication_monotonic_ms=adjudication_ms,
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
    }
    snapshot = {
        "DOCUMENT_CLASS": "P08_POSITION_OBSERVATION_SINGLE_GET_V1",
        "DOCUMENT_ROLE": "GET_ONLY_FRESH_EVIDENCE_NON_SSOT",
        "AUTHORITY": "NONE",
        "THIS_ARTIFACT_IS_NOT_CANONICAL": True,
        "OWNER_GO": owned,
        "OWNER_GO_CONSUMED": owner_go_consumed,
        "THIS_SLICE": THIS_SLICE,
        "BOUND_ORIGIN_MAIN_SHA": bound_sha,
        "AUTHORIZED_ENDPOINT": "GET /api/v5/account/positions",
        "ENDPOINT": ENDPOINT,
        "ENDPOINT_IDENTITY": ENDPOINT,
        "METHOD": "GET",
        "HOST": REUSED_REST_HOST,
        "VENUE": REUSED_VENUE,
        "QUERY_PARAMETERS": {},
        "INSTID_FILTER_USED": False,
        "TARGET_INSTRUMENT": TARGET_INSTRUMENT_ID,
        "TARGET_INSTRUMENT_ID": TARGET_INSTRUMENT_ID,
        "REQUEST_TIME_UTC": request_time,
        "RESPONSE_TIME_UTC": response_time,
        "REQUEST_TIMESTAMP": request_time,
        "RESPONSE_TIMESTAMP": response_time,
        "UTC_TIMESTAMP": request_time,
        "HTTP_STATUS": http_status,
        "OKX_CODE": venue_code,
        "OKX_MESSAGE": venue_msg,
        "SANITIZED_OKX_MESSAGE": venue_msg,
        "SEND_ATTEMPTED": send_attempted,
        "GET_ERROR": get_error,
        "PARSE_ERROR": parse_error,
        "BODY_BYTES": len(body_bytes),
        "BODY_SHA256": body_sha256,
        "COUNTERS": counters,
        "ACTUAL_NETWORK_REQUEST_COUNT": int(counters.get("GET_REQUEST_COUNT", 0) or 0),
        "HTTP_EXCHANGE_COUNT": http_exchange_count,
        "GET_REQUEST_COUNT": int(counters.get("GET_REQUEST_COUNT", 0) or 0),
        "WRITE_REQUEST_COUNT": int(counters.get("WRITE_REQUEST_COUNT", 0) or 0),
        "POST_COUNT": 0,
        "RETRY_COUNT": 0,
        "ENDPOINTS_USED": list(client.counters.endpoints_used),
        "METHODS_USED": list(client.counters.methods_used),
        "REDIRECT_FOLLOWED": redirect_followed,
        "REDIRECT_STATUS": redirect_status,
        "AUTH_PATH": {
            "CREDENTIAL_CLASS": REUSED_CREDENTIAL_CLASS,
            "SECRETREF_URI": REUSED_SECRETREF_URI,
            "SIGNER": "build_okx_live_canary_auth_headers_v1",
            "HTTP_CLIENT": "LiveCanaryHttpClientV1",
            "TRANSPORT": type(transport).__name__,
            "HEADER_PRESENCE": header_presence,
        },
        "AUTH_SIGNING_OWNER": "build_okx_live_canary_auth_headers_v1",
        "SANITIZED_SECRETREF": REUSED_SECRETREF_URI,
        "TARGET_SECRETREF_URI": REUSED_SECRETREF_URI,
        "AUTH_HEADER_SENT": bool(header_presence.get("AUTH_KEY_HEADER_PRESENT")),
        "SECRET_VALUES_INCLUDED": False,
        "SECRETREF_IDENTITY": secretref_identity,
        "DATA_ROW_COUNT": data_row_count,
        "RAW_DATA_SHAPE": (
            "DATA_LIST"
            if isinstance(data, list)
            else "NO_PARSEABLE_PAYLOAD"
            if payload is None
            else "DATA_NOT_LIST"
        ),
        "VENUE_CODE": venue_code,
        "VENUE_MSG": venue_msg,
        "RESULT_CLASS": result_class,
        "REDACTED_PAYLOAD": sanitize_positions_payload_v1(payload),
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
        "EXECUTION_READY": False,
        **standing,
        **observation,
    }
    adjudication = {
        "DOCUMENT_CLASS": "P08_POSITION_OBSERVATION_WINDOW_ADJUDICATION_V1",
        "DOCUMENT_ROLE": "INTERPRETATION_NOT_RAW_EVIDENCE_NOT_SSOT",
        "AUTHORITY": "NONE",
        "OWNER_GO": owned,
        "BOUND_ORIGIN_MAIN_SHA": bound_sha,
        "P08_CANONICAL_DEFINITION": P08_CANONICAL_DEFINITION,
        "CLASSIFIER": "classify_target_position_state_v1",
        "FRESHNESS_POLICY": FRESHNESS_POLICY,
        "FRESHNESS_POLICY_MAX_AGE_MS": POSITION_OBSERVATION_FRESHNESS_MAX_AGE_MS,
        "AGE_EVALUATION_POINT_THIS_WINDOW": "ADJUDICATION_AFTER_GET_NOT_FLATTEN_SEND",
        "FLATTEN_PRE_SEND_PERMIT_EVALUATED": False,
        "LOCAL_RESPONSE_RECEIVED_AT": received_ms,
        "ADJUDICATION_MONOTONIC_MS": adjudication_ms,
        "RESULT_CLASS": result_class,
        "HTTP_STATUS": http_status,
        "OKX_CODE": venue_code,
        "RAW_BODY_SHA256": body_sha256,
        "TARGET_INSTRUMENT_ID": TARGET_INSTRUMENT_ID,
        **freshness,
        **(window or {}),
        **observation,
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
        "P09_WORK_PERFORMED": False,
    }
    summary = {
        "DOCUMENT_CLASS": "P08_POSITION_OBSERVATION_SINGLE_GET_V1",
        "DOCUMENT_ROLE": "DERIVED_NON_SSOT",
        "OWNER_GO": owned,
        "OWNER_GO_CONSUMED": owner_go_consumed,
        "THIS_SLICE": THIS_SLICE,
        "BOUND_ORIGIN_MAIN_SHA": bound_sha,
        "ENDPOINT": ENDPOINT,
        "METHOD": "GET",
        "HOST": REUSED_REST_HOST,
        "TARGET_INSTRUMENT_ID": TARGET_INSTRUMENT_ID,
        "HTTP_STATUS": http_status,
        "OKX_CODE": venue_code,
        "RESULT_CLASS": result_class,
        "GET_REQUEST_COUNT": int(counters.get("GET_REQUEST_COUNT", 0) or 0),
        "HTTP_EXCHANGE_COUNT": http_exchange_count,
        "RETRY_COUNT": 0,
        "POST_COUNT": 0,
        "WRITE_REQUEST_COUNT": int(counters.get("WRITE_REQUEST_COUNT", 0) or 0),
        "PRIVATE_GET_EXECUTED": owner_go_consumed,
        "POSITION_RESPONSE_OBSERVED": observation["POSITION_RESPONSE_OBSERVED"],
        "TARGET_INSTRUMENT_ROW_OBSERVED": observation["TARGET_INSTRUMENT_ROW_OBSERVED"],
        "POSITION_STATE_OBSERVED": observation["POSITION_STATE_OBSERVED"],
        "TARGET_POSITION_ZERO_PROVEN": observation["TARGET_POSITION_ZERO_PROVEN"],
        "TARGET_POSITION_NONZERO_PROVEN": observation["TARGET_POSITION_NONZERO_PROVEN"],
        "POSITION_OBSERVATION_CLASS": observation["POSITION_OBSERVATION_CLASS"],
        "P08_CLOSED": observation["P08_CLOSED"],
        "P08_VERDICT": observation["P08_VERDICT"],
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
        "NEXT_AUTHORITY_BOUNDARY": observation["NEXT_AUTHORITY_BOUNDARY"],
        "MERGE_AUTHORIZED": False,
        "GET_ERROR": get_error,
        "PARSE_ERROR": parse_error,
    }
    verified = persist_p08_position_observation_evidence_v1(
        pack=pack,
        origin_main_sha=bound_sha,
        snapshot=snapshot,
        adjudication=adjudication,
        summary=summary,
    )
    return {
        "EVIDENCE_PACK": str(pack),
        "MANIFEST_VERIFY_RC": verified.get("MANIFEST_VERIFY_RC"),
        "summary": summary,
        "adjudication": adjudication,
    }
