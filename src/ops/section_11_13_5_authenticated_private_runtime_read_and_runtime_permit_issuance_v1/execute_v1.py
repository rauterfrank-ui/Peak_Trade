"""Execute exactly one authenticated GET /api/v5/account/positions then issue permit.

Reuses LiveCanaryHttpClientV1, UrllibLiveCanaryTransportV1, and the existing
canary HMAC signer. Does not POST. Does not flatten. Does not set
network_session_authorized on GatedProductiveFlattenTransportV1.
Unsigned flatten transport cannot satisfy this GET.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

from src.ops.section_11_13_5_authenticated_private_runtime_read_and_runtime_permit_issuance_v1.constants_v1 import (
    AUTHORIZED_HOST,
    CASE_A_TARGET_NONZERO,
    CASE_B_TARGET_ZERO,
    CASE_C_EMPTY_DATA_NOT_ZERO,
    CASE_D_TARGET_NOT_OBSERVED,
    CASE_E_HTTP_OR_OKX_ERROR,
    CASE_F_AMBIGUOUS,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT_SECONDS,
    EMPTY_DATA_IS_ZERO_VALUE,
    ENDPOINT,
    EXPECTED_ORIGIN_MAIN_SHA,
    FORBIDDEN_ENDPOINTS,
    FRESHNESS_POLICY,
    FRESHNESS_POLICY_MAX_AGE_MS,
    MAX_HTTP_EXCHANGE_COUNT,
    MAX_NETWORK_REQUEST_COUNT,
    OWNER_GO,
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
from src.ops.section_11_13_5_authenticated_private_runtime_read_and_runtime_permit_issuance_v1.runtime_permit_v1 import (
    PRICE_BINDING_ROLE,
    evaluate_runtime_permit_issuance_v1,
    runtime_permit_audit_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.account_positions_query_grammar_v1 import (
    build_account_positions_query_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    USER_AGENT_CANARY,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_productive_transport_v1 import (
    GatedProductiveFlattenTransportV1,
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
    PRE_SEND_EVIDENCE_KIND,
    PositionObservationFreshnessEvidenceV1,
    default_local_monotonic_ms_v1,
    evaluate_position_observation_freshness_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_submit_state_v1 import (
    TARGET_POSITION_NONZERO_PROVEN,
    TARGET_POSITION_NOT_OBSERVED,
    TARGET_POSITION_ZERO_PROVEN,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.prerequisite_08_fresh_position_observation_v1 import (
    adjudicate_prerequisite_08_window_v1,
    sanitize_positions_payload_v1,
)
from src.ops.section_11_13_5_post_z2ds_private_get_current_50110_egress_capture_v1.execute_v1 import (
    sanitize_okx_message_v1,
)


class AuthenticatedPrivateRuntimeReadError(RuntimeError):
    """Fail-closed authenticated private GET / permit issuance violation."""


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


def _assert_not_unsigned_flatten_transport_v1(transport: LiveCanaryTransportV1) -> None:
    if isinstance(transport, GatedProductiveFlattenTransportV1):
        raise AuthenticatedPrivateRuntimeReadError("UNSIGNED_FLATTEN_TRANSPORT_FORBIDDEN")
    name = type(transport).__name__
    if name == "GatedProductiveFlattenTransportV1":
        raise AuthenticatedPrivateRuntimeReadError("UNSIGNED_FLATTEN_TRANSPORT_FORBIDDEN")
    if bool(getattr(transport, "network_session_authorized", False)):
        raise AuthenticatedPrivateRuntimeReadError("FLATTEN_NETWORK_SESSION_FLAG_MUST_REMAIN_FALSE")


def _assert_one_get_zero_writes(client: LiveCanaryHttpClientV1) -> dict[str, Any]:
    counters = client.counters.to_dict()
    if int(counters.get("GET_REQUEST_COUNT", 0) or 0) != 1:
        raise AuthenticatedPrivateRuntimeReadError("GET_COUNT_NOT_ONE")
    if int(counters.get("REQUEST_COUNT", 0) or 0) != 1:
        raise AuthenticatedPrivateRuntimeReadError("REQUEST_COUNT_NOT_ONE")
    if int(counters.get("WRITE_REQUEST_COUNT", 0) or 0) != 0:
        raise AuthenticatedPrivateRuntimeReadError("WRITE_REQUEST_DETECTED")
    if int(counters.get("TRANSFER_REQUEST_COUNT", 0) or 0) != 0:
        raise AuthenticatedPrivateRuntimeReadError("TRANSFER_REQUEST_DETECTED")
    if int(counters.get("ORDER_REQUEST_COUNT", 0) or 0) != 0:
        raise AuthenticatedPrivateRuntimeReadError("ORDER_REQUEST_DETECTED")
    if int(counters.get("ENTRY_SUBMIT_COUNT", 0) or 0) != 0:
        raise AuthenticatedPrivateRuntimeReadError("ENTRY_SUBMIT_DETECTED")
    if int(counters.get("FLATTEN_SUBMIT_COUNT", 0) or 0) != 0:
        raise AuthenticatedPrivateRuntimeReadError("FLATTEN_SUBMIT_DETECTED")
    if list(client.counters.endpoints_used) != [ENDPOINT]:
        raise AuthenticatedPrivateRuntimeReadError("ENDPOINT_SET_MISMATCH")
    if list(client.counters.methods_used) != ["GET"]:
        raise AuthenticatedPrivateRuntimeReadError("NON_GET_METHOD_DETECTED")
    return counters


def secretref_identity_without_values_v1(*, vault_file: Path | str) -> dict[str, Any]:
    """Prove SecretRef binding by URI and field lengths only. Never returns values."""
    path = Path(vault_file)
    if not path.is_file():
        raise AuthenticatedPrivateRuntimeReadError("VAULT_FILE_MISSING")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AuthenticatedPrivateRuntimeReadError("VAULT_FILE_NOT_JSON") from exc
    if not isinstance(payload, Mapping):
        raise AuthenticatedPrivateRuntimeReadError("VAULT_FILE_NOT_OBJECT")
    if REUSED_SECRETREF_URI not in payload:
        raise AuthenticatedPrivateRuntimeReadError("SECRETREF_URI_UNBOUND")
    raw = payload[REUSED_SECRETREF_URI]
    if isinstance(raw, str):
        try:
            material = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise AuthenticatedPrivateRuntimeReadError("SECRETREF_MATERIAL_NOT_JSON") from exc
    elif isinstance(raw, Mapping):
        material = raw
    else:
        raise AuthenticatedPrivateRuntimeReadError("SECRETREF_MATERIAL_TYPE_FORBIDDEN")
    if not isinstance(material, Mapping):
        raise AuthenticatedPrivateRuntimeReadError("SECRETREF_MATERIAL_NOT_OBJECT")
    key_len = len(str(material.get("api_key") or "").strip())
    secret_len = len(str(material.get("api_secret") or "").strip())
    passphrase_len = len(str(material.get("passphrase") or "").strip())
    if key_len <= 0 or secret_len <= 0 or passphrase_len <= 0:
        raise AuthenticatedPrivateRuntimeReadError("CREDENTIAL_FIELDS_INCOMPLETE")
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
    if result_class != RESULT_CLASS_200_OKX_0 or window is None:
        return {
            "POSITION_OBSERVATION_CLASS": CASE_E_HTTP_OR_OKX_ERROR,
            "POSITION_RESPONSE_OBSERVED": payload is not None,
            "TARGET_INSTRUMENT_ROW_OBSERVED": False,
            "POSITION_STATE_OBSERVED": False,
            "TARGET_POSITION_ZERO_PROVEN": False,
            "TARGET_POSITION_NONZERO_PROVEN": False,
        }
    data = payload.get("data") if isinstance(payload, Mapping) else None
    classifier_state = str(window.get("classifier_state") or "")
    classifier_reason = str(window.get("classifier_reason") or "")
    if EMPTY_DATA_IS_ZERO_VALUE:
        raise AuthenticatedPrivateRuntimeReadError("EMPTY_DATA_MUST_NOT_BE_PROMOTED_TO_ZERO")
    if isinstance(data, list) and len(data) == 0:
        return {
            "POSITION_OBSERVATION_CLASS": CASE_C_EMPTY_DATA_NOT_ZERO,
            "POSITION_RESPONSE_OBSERVED": True,
            "TARGET_INSTRUMENT_ROW_OBSERVED": False,
            "POSITION_STATE_OBSERVED": False,
            "TARGET_POSITION_ZERO_PROVEN": False,
            "TARGET_POSITION_NONZERO_PROVEN": False,
        }
    if classifier_state == TARGET_POSITION_NONZERO_PROVEN:
        return {
            "POSITION_OBSERVATION_CLASS": CASE_A_TARGET_NONZERO,
            "POSITION_RESPONSE_OBSERVED": True,
            "TARGET_INSTRUMENT_ROW_OBSERVED": True,
            "POSITION_STATE_OBSERVED": True,
            "TARGET_POSITION_ZERO_PROVEN": False,
            "TARGET_POSITION_NONZERO_PROVEN": True,
        }
    if classifier_state == TARGET_POSITION_ZERO_PROVEN:
        return {
            "POSITION_OBSERVATION_CLASS": CASE_B_TARGET_ZERO,
            "POSITION_RESPONSE_OBSERVED": True,
            "TARGET_INSTRUMENT_ROW_OBSERVED": True,
            "POSITION_STATE_OBSERVED": True,
            "TARGET_POSITION_ZERO_PROVEN": True,
            "TARGET_POSITION_NONZERO_PROVEN": False,
        }
    if classifier_state == TARGET_POSITION_NOT_OBSERVED:
        return {
            "POSITION_OBSERVATION_CLASS": CASE_D_TARGET_NOT_OBSERVED,
            "POSITION_RESPONSE_OBSERVED": True,
            "TARGET_INSTRUMENT_ROW_OBSERVED": False,
            "POSITION_STATE_OBSERVED": False,
            "TARGET_POSITION_ZERO_PROVEN": False,
            "TARGET_POSITION_NONZERO_PROVEN": False,
        }
    if classifier_reason == "AMBIGUOUS_TARGET_POSITION_ROWS":
        return {
            "POSITION_OBSERVATION_CLASS": CASE_F_AMBIGUOUS,
            "POSITION_RESPONSE_OBSERVED": True,
            "TARGET_INSTRUMENT_ROW_OBSERVED": False,
            "POSITION_STATE_OBSERVED": False,
            "TARGET_POSITION_ZERO_PROVEN": False,
            "TARGET_POSITION_NONZERO_PROVEN": False,
        }
    return {
        "POSITION_OBSERVATION_CLASS": CASE_F_AMBIGUOUS,
        "POSITION_RESPONSE_OBSERVED": payload is not None,
        "TARGET_INSTRUMENT_ROW_OBSERVED": False,
        "POSITION_STATE_OBSERVED": False,
        "TARGET_POSITION_ZERO_PROVEN": False,
        "TARGET_POSITION_NONZERO_PROVEN": False,
    }


def observation_identity_v1(
    *,
    body_sha256: str | None,
    received_ms: int | None,
    endpoint: str,
) -> str | None:
    if not body_sha256 or received_ms is None:
        return None
    material = f"GET\n{endpoint}\n{body_sha256}\n{int(received_ms)}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def execute_authenticated_private_runtime_read_and_permit_issuance_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    evidence_root: Path,
    vault_file: Path | str | None = None,
    transport: LiveCanaryTransportV1 | None = None,
    persist: bool = True,
) -> dict[str, Any]:
    """One allowlisted unfiltered positions GET, then permit issuance if gates pass."""
    from src.ops.section_11_13_5_authenticated_private_runtime_read_and_runtime_permit_issuance_v1.assemble_v1 import (
        assemble_authenticated_private_runtime_read_and_permit_issuance_v1,
    )

    owned = str(owner_go or "").strip()
    if owned != OWNER_GO:
        raise AuthenticatedPrivateRuntimeReadError("OWNER_GO_MISMATCH")
    bound_sha = str(origin_main_sha or "").strip()
    if bound_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise AuthenticatedPrivateRuntimeReadError("ORIGIN_MAIN_SHA_MISMATCH")
    if REUSED_REST_HOST != AUTHORIZED_HOST:
        raise AuthenticatedPrivateRuntimeReadError("HOST_MISMATCH")
    query = build_account_positions_query_v1()
    if query.query or query.inst_id_filter_present or query.pos_id_filter_present:
        raise AuthenticatedPrivateRuntimeReadError("INSTID_FILTER_FORBIDDEN")
    endpoint = query.path_with_query()
    if endpoint != ENDPOINT:
        raise AuthenticatedPrivateRuntimeReadError("ENDPOINT_MUST_BE_UNFILTERED_POSITIONS")
    if "?" in ENDPOINT or ENDPOINT != "/api/v5/account/positions":
        raise AuthenticatedPrivateRuntimeReadError("ENDPOINT_CONTRACT_DRIFT")
    if ENDPOINT in FORBIDDEN_ENDPOINTS:
        raise AuthenticatedPrivateRuntimeReadError("MUTATION_ENDPOINT_FORBIDDEN")

    productive = transport is None
    secretref_identity: dict[str, Any] | None = None
    if productive:
        if vault_file is None or not str(vault_file).strip():
            raise AuthenticatedPrivateRuntimeReadError("VAULT_FILE_REQUIRED")
        secretref_identity = secretref_identity_without_values_v1(vault_file=vault_file)
        transport = UrllibLiveCanaryTransportV1(wire_send_enabled=True)
    if transport is None:
        raise AuthenticatedPrivateRuntimeReadError("TRANSPORT_REQUIRED")
    _assert_not_unsigned_flatten_transport_v1(transport)
    if isinstance(transport, UrllibLiveCanaryTransportV1) and not bool(
        getattr(transport, "wire_send_enabled", False)
    ):
        raise AuthenticatedPrivateRuntimeReadError("PRODUCTIVE_WIRE_DISABLED")

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
            raise AuthenticatedPrivateRuntimeReadError("SIGNED_REQUEST_TARGET_MISMATCH")
        if parsed.hostname != AUTHORIZED_HOST:
            raise AuthenticatedPrivateRuntimeReadError("HOST_MISMATCH")
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
            if not (
                header_presence["AUTH_KEY_HEADER_PRESENT"]
                and header_presence["AUTH_SIGN_HEADER_PRESENT"]
                and header_presence["AUTH_TIMESTAMP_HEADER_PRESENT"]
                and header_presence["AUTH_PASSPHRASE_HEADER_PRESENT"]
            ):
                raise AuthenticatedPrivateRuntimeReadError("HMAC_HEADERS_MISSING")
            if header_presence["SIMULATION_HEADER_PRESENT"]:
                raise AuthenticatedPrivateRuntimeReadError("SIMULATION_HEADER_FORBIDDEN")
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
            raise AuthenticatedPrivateRuntimeReadError("NON_GET_RESPONSE")
        if redirect_followed:
            raise AuthenticatedPrivateRuntimeReadError("REDIRECT_FOLLOWED")
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
            raise AuthenticatedPrivateRuntimeReadError("HTTP_EXCHANGE_COUNT_NOT_ONE")
        if productive and http_exchange_count != 1:
            raise AuthenticatedPrivateRuntimeReadError("NETWORK_REQUEST_COUNT_NOT_ONE")
    elif http_exchange_count > MAX_HTTP_EXCHANGE_COUNT:
        raise AuthenticatedPrivateRuntimeReadError("HTTP_EXCHANGE_COUNT_EXCEEDED")

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
    issuance_ms = default_local_monotonic_ms_v1()
    obs_identity = observation_identity_v1(
        body_sha256=body_sha256,
        received_ms=received_ms,
        endpoint=ENDPOINT,
    )
    freshness_evidence = None
    if received_ms is not None:
        freshness_evidence = PositionObservationFreshnessEvidenceV1(
            response_received_monotonic_ms=received_ms,
            decision_id="RUNTIME_PERMIT_ISSUANCE",
            evidence_kind=PRE_SEND_EVIDENCE_KIND,
            observation_get_identity=obs_identity,
        )
    freshness = evaluate_position_observation_freshness_v1(
        evidence=freshness_evidence,
        evaluation_monotonic_ms=issuance_ms,
        current_decision_id="RUNTIME_PERMIT_ISSUANCE",
    )
    size_binding = None
    if window is not None:
        raw = window.get("TARGET_POSITION_QTY_RAW")
        if raw is not None and str(raw).strip():
            size_binding = str(raw).strip()
    permit, permit_reasons = evaluate_runtime_permit_issuance_v1(
        origin_main_sha=bound_sha,
        instrument_id=TARGET_INSTRUMENT_ID,
        observation_class=str(observation["POSITION_OBSERVATION_CLASS"]),
        observation_identity=obs_identity,
        observation_body_sha256=body_sha256,
        size_binding=size_binding,
        freshness_allowed=bool(freshness.allowed),
        freshness_reject_reason=freshness.reject_reason or None,
        issuance_monotonic_ms=issuance_ms,
        response_received_monotonic_ms=received_ms,
        result_class=result_class,
        authentication_failure=(get_error if result_class == RESULT_CLASS_401_50110 else None),
        transport_error=get_error if result_class == RESULT_CLASS_TRANSPORT else None,
        unsigned_flatten_transport_used=False,
        live_authorized_claim=False,
        post_performed_claim=False,
        flatten_execute_authorized_claim=False,
        historical_reuse_claim=False,
        price_binding_claimed=PRICE_BINDING_ROLE,
    )
    permit_audit = runtime_permit_audit_v1(permit=permit, deny_reasons=permit_reasons)
    runtime_facts = {
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
        "WINDOW": window,
        "OBSERVATION": observation,
        "OBSERVATION_IDENTITY": obs_identity,
        "LOCAL_RESPONSE_RECEIVED_AT": received_ms,
        "ISSUANCE_MONOTONIC_MS": issuance_ms,
        "FRESHNESS": freshness.to_dict(),
        "FRESHNESS_POLICY": FRESHNESS_POLICY,
        "FRESHNESS_POLICY_MAX_AGE_MS": FRESHNESS_POLICY_MAX_AGE_MS,
        "SIZE_BINDING": size_binding,
        "PERMIT_AUDIT": permit_audit,
        "PRIVATE_GET_EXECUTED": owner_go_consumed,
        "POSITIONS_GET_PERFORMED": True,
        "PRIVATE_AUTH_USED": productive and owner_go_consumed,
        "CREDENTIAL_USE_PROVEN": productive and owner_go_consumed,
        "NETWORK_PROVEN": productive and send_attempted,
        "GET_PERFORMED_THIS_PERSIST": owner_go_consumed,
        "RUNTIME_GET_PERFORMED": owner_go_consumed,
        "PUBLIC_GET_PERFORMED": False,
        "PENDING_ORDERS_GET_PERFORMED": False,
        "BALANCE_GET_PERFORMED": False,
        "CONFIG_GET_PERFORMED": False,
        "MAX_SIZE_GET_PERFORMED": False,
        "FUNDING_GET_PERFORMED": False,
        "POST_PERFORMED": False,
        "ORDER_PERFORMED": False,
        "FLATTEN_EXECUTE_USED": False,
        "FUNDING_USED": False,
        "PRODUCTIVE_EXECUTION_USED": False,
        "LIVE_AUTHORIZED": False,
        "CANARY_AUTHORIZED": False,
        "SUBMIT_UNLOCKED": False,
        "LIVE_ENABLED": False,
        "LIVE_ARMED": False,
        "NETWORK_SESSION_AUTHORIZED": False,
        "FLATTEN_EXECUTE_AUTHORIZED": False,
        "PRODUCTIVE_FLATTEN_POST_AUTHORIZED": False,
        "EMPTY_DATA_IS_ZERO": False,
        "ABSENT_TARGET_ROW_IS_ZERO": False,
        "UNSIGNED_FLATTEN_TRANSPORT_USED": False,
        "GATED_PRODUCTIVE_FLATTEN_TRANSPORT_USED": False,
    }
    assembled = assemble_authenticated_private_runtime_read_and_permit_issuance_v1(
        origin_main_sha=bound_sha,
        runtime_facts=runtime_facts,
        evidence_root=evidence_root if persist else None,
    )
    assembled["runtime_facts"] = runtime_facts
    assembled["permit_audit"] = permit_audit
    return assembled
