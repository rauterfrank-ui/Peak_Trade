"""Exactly one authorized private GET for path-reachability connectivity proof.

Does not POST. Does not retry. Does not promote LIVE_PRIVATE_READ_ONLY_PROVEN.
Secrets are never logged, printed, or persisted.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    ENDPOINT_ACCOUNT_CONFIG,
    GET_ENDPOINTS_PRIVATE,
    REQUIRED_CREDENTIAL_CLASS,
    REQUIRED_SECRETREF_URI,
    REUSED_BINDING_REST_HOST,
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
from src.ops.section_11_13_5_post_z2ds_private_get_current_50110_egress_capture_v1.execute_v1 import (
    sanitize_okx_message_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    EXPECTED_ORIGIN_MAIN_SHA,
    OWNER_GO,
    POST_ALLOWED,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
    assert_contract_invariants_v1,
)

REACHABILITY_GET_ENDPOINT = ENDPOINT_ACCOUNT_CONFIG
REACHABILITY_GET_METHOD = "GET"
REACHABILITY_MAX_REQUEST_COUNT = 1
REACHABILITY_MAX_RETRIES = 0
REACHABILITY_TIMEOUT_SECONDS = 10.0
REACHABILITY_REST_HOST = REUSED_BINDING_REST_HOST
REACHABILITY_REST_BASE = f"https://{REUSED_BINDING_REST_HOST}"
WHY_GET_REQUIRED = (
    "TARGET_HOST_RESOLVABLE_OR_CONNECTABLE, AUTHENTICATION_PATH_FUNCTIONAL, "
    "and CURRENT_ACCOUNT_OR_VENUE_READ_ACCESS_FUNCTIONAL cannot be proven "
    "from current canonical persisted evidence. Historical private GET "
    "success is not current authenticated connectivity."
)
REQUIRED_FACT = "CURRENT_AUTHENTICATED_PRIVATE_READ_CONNECTIVITY"
EXPECTED_MUTATION = "NONE"

_SAFE_RESPONSE_FIELDS = frozenset(
    {
        "posMode",
        "acctLv",
        "acctLvCode",
        "type",
        "level",
        "roleType",
    }
)


def bind_private_get_before_request_v1() -> dict[str, Any]:
    return {
        "WHY_GET_REQUIRED": WHY_GET_REQUIRED,
        "REQUIRED_FACT": REQUIRED_FACT,
        "ENDPOINT": REACHABILITY_GET_ENDPOINT,
        "METHOD": REACHABILITY_GET_METHOD,
        "EXPECTED_MUTATION": EXPECTED_MUTATION,
        "MAXIMUM_REQUEST_COUNT": REACHABILITY_MAX_REQUEST_COUNT,
        "RETRY": False,
        "PUBLIC_GET": False,
        "PRIVATE_GET": True,
        "POST": False,
        "LIVE_PRIVATE_READ_ONLY_PROVEN_PROMOTION": False,
    }


def _utc_now_iso_v1() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _header_presence_v1(headers: Mapping[str, str]) -> dict[str, Any]:
    keys = {str(k).upper() for k in headers}
    return {
        "AUTH_KEY_HEADER_PRESENT": "OK-ACCESS-KEY" in keys,
        "AUTH_SIGN_HEADER_PRESENT": "OK-ACCESS-SIGN" in keys,
        "AUTH_TIMESTAMP_HEADER_PRESENT": "OK-ACCESS-TIMESTAMP" in keys,
        "AUTH_PASSPHRASE_HEADER_PRESENT": "OK-ACCESS-PASSPHRASE" in keys,
        "SIMULATION_HEADER_PRESENT": any("simul" in str(k).lower() for k in headers),
        "SIGNED_METHOD": "GET",
        "VALUES_INCLUDED": False,
    }


def _sanitize_account_config_payload_v1(payload: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if payload is None:
        return None
    data = payload.get("data")
    rows = data if isinstance(data, list) else []
    sanitized_rows: list[dict[str, Any]] = []
    for item in rows:
        if not isinstance(item, Mapping):
            continue
        row = {key: item.get(key) for key in _SAFE_RESPONSE_FIELDS if key in item}
        row["UID_PRESENT"] = bool(str(item.get("uid") or "").strip())
        row["UID_VALUE"] = None
        sanitized_rows.append(row)
    return {
        "code": payload.get("code"),
        "msg": sanitize_okx_message_v1(str(payload.get("msg") or "")[:200]),
        "data": sanitized_rows,
        "ROW_FIELDS_REDACTED_TO_ALLOWLIST": True,
        "UID_VALUES_EXCLUDED": True,
    }


def classify_reachability_get_result_v1(
    *,
    http_status: int | None,
    venue_code: str | None,
    get_error: str | None,
    parsed_ok: bool,
    data_present: bool,
    method: str | None,
    redirect_followed: bool,
) -> dict[str, Any]:
    code = "" if venue_code is None else str(venue_code).strip()
    auth_ok = (
        http_status == 200
        and code == "0"
        and parsed_ok is True
        and data_present is True
        and str(method or "") == "GET"
        and redirect_followed is False
        and not get_error
    )
    host_ok = http_status is not None or (
        get_error is not None and "NETWORK" not in str(get_error).upper()
    )
    if get_error and http_status is None:
        if "NETWORK" in str(get_error).upper() or "TIMEOUT" in str(get_error).upper():
            host_ok = False
            auth_ok = False
        elif "PRODUCTIVE_WIRE_SEND_DISABLED" in str(get_error):
            host_ok = False
            auth_ok = False
    return {
        "TARGET_HOST_RESOLVABLE_OR_CONNECTABLE": bool(host_ok),
        "AUTHENTICATION_PATH_FUNCTIONAL": bool(auth_ok),
        "CURRENT_ACCOUNT_OR_VENUE_READ_ACCESS_FUNCTIONAL": bool(auth_ok),
        "HTTP_200_OKX_0": bool(http_status == 200 and code == "0"),
        "LIVE_PRIVATE_READ_ONLY_PROVEN": False,
    }


def execute_reachability_private_get_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    vault_file: Path | None = None,
    transport: LiveCanaryTransportV1 | None = None,
) -> dict[str, Any]:
    assert_contract_invariants_v1()
    if str(owner_go or "").strip() != OWNER_GO:
        raise Section1114OfflineSurfaceError("OWNER_GO_MISMATCH")
    if str(origin_main_sha or "").strip() != EXPECTED_ORIGIN_MAIN_SHA:
        raise Section1114OfflineSurfaceError("ORIGIN_MAIN_SHA_MISMATCH")
    if POST_ALLOWED is True:
        raise Section1114OfflineSurfaceError("POST_MUST_REMAIN_FORBIDDEN")
    if REACHABILITY_GET_ENDPOINT not in GET_ENDPOINTS_PRIVATE:
        raise Section1114OfflineSurfaceError("ENDPOINT_NOT_PRIVATE_ALLOWLIST")
    binding = bind_private_get_before_request_v1()
    productive = transport is None
    handle = None
    if productive:
        if vault_file is None:
            raise Section1114OfflineSurfaceError("VAULT_FILE_REQUIRED")
        backend = build_file_secretref_vault_backend_v1(vault_file=Path(vault_file))
        handle = resolve_and_load_live_canary_secretref_ephemeral_v1(
            secret_reference=REQUIRED_SECRETREF_URI,
            vault_backend=backend,
            credential_class=REQUIRED_CREDENTIAL_CLASS,
        )
        live_transport: LiveCanaryTransportV1 = UrllibLiveCanaryTransportV1(wire_send_enabled=True)
    else:
        live_transport = transport
    if isinstance(live_transport, UrllibLiveCanaryTransportV1) and not bool(
        getattr(live_transport, "wire_send_enabled", False)
    ):
        raise Section1114OfflineSurfaceError("PRODUCTIVE_WIRE_DISABLED")
    client = LiveCanaryHttpClientV1(
        rest_base=REACHABILITY_REST_BASE,
        rest_host=REACHABILITY_REST_HOST,
        transport=live_transport,
        max_request_count=REACHABILITY_MAX_REQUEST_COUNT,
        max_retries=REACHABILITY_MAX_RETRIES,
        timeout_seconds=REACHABILITY_TIMEOUT_SECONDS,
    )
    auth_headers: dict[str, str] = {}
    header_presence = _header_presence_v1({})
    request_time = _utc_now_iso_v1()
    http_status: int | None = None
    body_bytes = b""
    get_error: str | None = None
    send_attempted = False
    redirect_followed = False
    elapsed_seconds: float | None = None
    response_headers_safe: dict[str, str] = {}
    method = "GET"
    try:
        if productive:
            url = f"{REACHABILITY_REST_BASE}{REACHABILITY_GET_ENDPOINT}"
            parsed = urlparse(url)
            if parsed.hostname != REACHABILITY_REST_HOST:
                raise Section1114OfflineSurfaceError("HOST_MISMATCH")
            if parsed.path != REACHABILITY_GET_ENDPOINT:
                raise Section1114OfflineSurfaceError("ENDPOINT_PATH_MISMATCH")
            auth_headers = build_okx_live_canary_auth_headers_v1(
                handle=handle, url=url, method="GET"
            )
            auth_headers["User-Agent"] = USER_AGENT_CANARY
        header_presence = _header_presence_v1(auth_headers)
        response = client.get(endpoint=REACHABILITY_GET_ENDPOINT, headers=auth_headers or None)
        send_attempted = True
        http_status = int(response.status_code)
        body_bytes = bytes(response.body_bytes)
        redirect_followed = bool(response.redirect_followed)
        elapsed_seconds = float(response.elapsed_seconds)
        response_headers_safe = dict(response.response_headers_safe or {})
        method = str(response.method or "GET")
        if method != "GET":
            raise Section1114OfflineSurfaceError("NON_GET_RESPONSE")
        if redirect_followed:
            raise Section1114OfflineSurfaceError("REDIRECT_FOLLOWED")
        if client.counters.request_count > REACHABILITY_MAX_REQUEST_COUNT:
            raise Section1114OfflineSurfaceError("MAX_REQUEST_COUNT_EXCEEDED")
        if "POST" in client.counters.methods_used:
            raise Section1114OfflineSurfaceError("POST_INVOKED_BY_REACHABILITY_PROOF")
    except LiveCanaryHttpError as exc:
        send_attempted = True
        get_error = str(exc)
    finally:
        auth_headers.clear()
        if handle is not None:
            release_live_canary_ephemeral_material_v1(handle)
    response_time = _utc_now_iso_v1()
    payload: dict[str, Any] | None = None
    parsed_ok = False
    if body_bytes:
        try:
            payload = parse_json_object_v1(body_bytes)
            parsed_ok = True
        except LiveCanaryHttpError as exc:
            get_error = str(exc) if get_error is None else get_error
    venue_code = str((payload or {}).get("code") or "") if payload else None
    data = (payload or {}).get("data") if payload else None
    data_present = isinstance(data, list) and any(isinstance(item, Mapping) for item in data)
    classified = classify_reachability_get_result_v1(
        http_status=http_status,
        venue_code=venue_code,
        get_error=get_error,
        parsed_ok=parsed_ok,
        data_present=data_present,
        method=method,
        redirect_followed=redirect_followed,
    )
    sanitized = _sanitize_account_config_payload_v1(payload)
    body_sha256 = hashlib.sha256(body_bytes).hexdigest() if body_bytes else None
    return {
        "GET_BINDING": binding,
        "OWNER_GO": OWNER_GO,
        "METHOD": "GET",
        "ENDPOINT": REACHABILITY_GET_ENDPOINT,
        "HOST": REACHABILITY_REST_HOST,
        "REQUEST_TIME_UTC": request_time,
        "RESPONSE_TIME_UTC": response_time,
        "SEND_ATTEMPTED": send_attempted,
        "HTTP_STATUS": http_status,
        "OKX_CODE": venue_code,
        "GET_ERROR": get_error,
        "PARSED_OK": parsed_ok,
        "DATA_PRESENT": data_present,
        "REDIRECT_FOLLOWED": redirect_followed,
        "ELAPSED_SECONDS": elapsed_seconds,
        "BODY_SHA256": body_sha256,
        "BODY_BYTE_LEN": len(body_bytes),
        "HEADER_PRESENCE": header_presence,
        "RESPONSE_HEADERS_SAFE": response_headers_safe,
        "SANITIZED_PAYLOAD": sanitized,
        "VENUE_REQUESTS": 1 if send_attempted else 0,
        "PUBLIC_GET_USED": False,
        "PRIVATE_GET_USED": True,
        "CREDENTIAL_USE": bool(productive),
        "POST_USED": False,
        "RETRY_USED": False,
        "LIVE_PRIVATE_READ_ONLY_PROVEN": False,
        **classified,
        "VALUES_INCLUDED": False,
    }


def assert_no_post_in_get_evidence_v1(payload: Mapping[str, Any]) -> None:
    if payload.get("POST_USED") is True or payload.get("METHOD") == "POST":
        raise Section1114OfflineSurfaceError("POST_INVOKED_BY_REACHABILITY_PROOF")
    dumped = json.dumps(dict(payload), sort_keys=True)
    if '"METHOD": "POST"' in dumped and payload.get("METHOD") != "GET":
        raise Section1114OfflineSurfaceError("POST_INVOKED_BY_REACHABILITY_PROOF")
