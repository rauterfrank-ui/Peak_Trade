"""Exactly two authorized private GETs for LIVE_PRIVATE_READ_ONLY_PROVEN.

Does not POST. Does not retry. Does not promote LIVE_ORDER_PLAN_OBSERVED.
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
    ENDPOINT_ACCOUNT_BALANCE,
    ENDPOINT_ACCOUNT_CONFIG,
    GET_ENDPOINTS_PRIVATE,
    REQUIRED_CREDENTIAL_CLASS,
    REQUIRED_SECRETREF_URI,
    REUSED_BINDING_ACCOUNT_SCOPE,
    REUSED_BINDING_REST_HOST,
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
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.reachability_private_get_v1 import (
    _header_presence_v1,
    _sanitize_account_config_payload_v1,
)

PRIVATE_READ_ONLY_GET_ENDPOINTS: tuple[str, ...] = (
    ENDPOINT_ACCOUNT_CONFIG,
    ENDPOINT_ACCOUNT_BALANCE,
)
PRIVATE_READ_ONLY_GET_METHOD = "GET"
PRIVATE_READ_ONLY_MAX_REQUEST_COUNT = 2
PRIVATE_READ_ONLY_MAX_RETRIES = 0
PRIVATE_READ_ONLY_TIMEOUT_SECONDS = 10.0
PRIVATE_READ_ONLY_REST_HOST = REUSED_BINDING_REST_HOST
PRIVATE_READ_ONLY_REST_BASE = f"https://{REUSED_BINDING_REST_HOST}"
WHY_GET_REQUIRED = (
    "LIVE_PRIVATE_READ_ONLY_PROVEN requires current authenticated private GET "
    "of /api/v5/account/config and /api/v5/account/balance. A single "
    "reachability GET is not this field. Historical §11.13.2 success is stale."
)
REQUIRED_FACT = "CURRENT_AUTHENTICATED_PRIVATE_READ_CONFIG_AND_BALANCE"
EXPECTED_MUTATION = "NONE"


def bind_private_read_only_gets_before_request_v1() -> dict[str, Any]:
    return {
        "WHY_GET_REQUIRED": WHY_GET_REQUIRED,
        "REQUIRED_FACT": REQUIRED_FACT,
        "ENDPOINTS": list(PRIVATE_READ_ONLY_GET_ENDPOINTS),
        "METHOD": PRIVATE_READ_ONLY_GET_METHOD,
        "EXPECTED_MUTATION": EXPECTED_MUTATION,
        "MAXIMUM_REQUEST_COUNT": PRIVATE_READ_ONLY_MAX_REQUEST_COUNT,
        "RETRY": False,
        "PUBLIC_GET": False,
        "PRIVATE_GET": True,
        "POST": False,
        "LIVE_ORDER_PLAN_OBSERVED_PROMOTION": False,
        "SECTION_11_13_2_TRADE_FALSE_ATTESTATION_NOT_A_1114_CONJUNCT": True,
    }


def _utc_now_iso_v1() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sanitize_account_balance_payload_v1(
    payload: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    if payload is None:
        return None
    data = payload.get("data")
    rows = data if isinstance(data, list) else []
    sanitized_rows: list[dict[str, Any]] = []
    for item in rows:
        if not isinstance(item, Mapping):
            continue
        details = item.get("details")
        detail_rows = details if isinstance(details, list) else []
        ccy_present = 0
        for detail in detail_rows:
            if isinstance(detail, Mapping) and str(detail.get("ccy") or "").strip():
                ccy_present += 1
        sanitized_rows.append(
            {
                "DETAILS_ROW_COUNT": len(detail_rows),
                "CCY_PRESENT_COUNT": ccy_present,
                "EQ_FIELD_PRESENT": "eq" in item,
                "AVAILEQ_FIELD_PRESENT": "availEq" in item,
                "NUMERIC_VALUES_EXCLUDED": True,
            }
        )
    return {
        "code": payload.get("code"),
        "msg": sanitize_okx_message_v1(str(payload.get("msg") or "")[:200]),
        "data": sanitized_rows,
        "ROW_FIELDS_REDACTED_TO_SHAPE": True,
        "NUMERIC_VALUES_EXCLUDED": True,
    }


def _row_success_v1(
    *,
    http_status: int | None,
    venue_code: str | None,
    parsed_ok: bool,
    data_present: bool,
    method: str | None,
    redirect_followed: bool,
    get_error: str | None,
) -> bool:
    code = "" if venue_code is None else str(venue_code).strip()
    return (
        http_status == 200
        and code == "0"
        and parsed_ok is True
        and data_present is True
        and str(method or "") == "GET"
        and redirect_followed is False
        and not get_error
    )


def path_reachable_view_from_read_only_pack_v1(pack: Mapping[str, Any]) -> dict[str, Any]:
    """Connectivity view for PATH_REACHABLE evaluator. Does not claim this field."""

    return {
        "TARGET_HOST_RESOLVABLE_OR_CONNECTABLE": pack.get("TARGET_HOST_RESOLVABLE_OR_CONNECTABLE"),
        "AUTHENTICATION_PATH_FUNCTIONAL": pack.get("AUTHENTICATION_PATH_FUNCTIONAL"),
        "CURRENT_ACCOUNT_OR_VENUE_READ_ACCESS_FUNCTIONAL": pack.get(
            "CURRENT_ACCOUNT_OR_VENUE_READ_ACCESS_FUNCTIONAL"
        ),
        "LIVE_PRIVATE_READ_ONLY_PROVEN": False,
        "POST_USED": pack.get("POST_USED"),
        "PRIVATE_GET_USED": pack.get("PRIVATE_GET_USED"),
        "CREDENTIAL_USE": pack.get("CREDENTIAL_USE"),
        "VENUE_REQUESTS": pack.get("VENUE_REQUESTS"),
        "METHOD": "GET",
        "RESPONSE_TIME_UTC": pack.get("RESPONSE_TIME_UTC"),
    }


def execute_private_read_only_gets_v1(
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
    for endpoint in PRIVATE_READ_ONLY_GET_ENDPOINTS:
        if endpoint not in GET_ENDPOINTS_PRIVATE:
            raise Section1114OfflineSurfaceError(f"ENDPOINT_NOT_PRIVATE_ALLOWLIST:{endpoint}")
    binding = bind_private_read_only_gets_before_request_v1()
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
        rest_base=PRIVATE_READ_ONLY_REST_BASE,
        rest_host=PRIVATE_READ_ONLY_REST_HOST,
        transport=live_transport,
        max_request_count=PRIVATE_READ_ONLY_MAX_REQUEST_COUNT,
        max_retries=PRIVATE_READ_ONLY_MAX_RETRIES,
        timeout_seconds=PRIVATE_READ_ONLY_TIMEOUT_SECONDS,
    )
    observations: list[dict[str, Any]] = []
    any_redirect = False
    any_error: str | None = None
    send_attempted = False
    account_scope_match = False
    try:
        for endpoint in PRIVATE_READ_ONLY_GET_ENDPOINTS:
            auth_headers: dict[str, str] = {}
            request_time = _utc_now_iso_v1()
            http_status: int | None = None
            body_bytes = b""
            get_error: str | None = None
            redirect_followed = False
            elapsed_seconds: float | None = None
            method = "GET"
            header_presence = _header_presence_v1({})
            try:
                if productive:
                    url = f"{PRIVATE_READ_ONLY_REST_BASE}{endpoint}"
                    parsed = urlparse(url)
                    if parsed.hostname != PRIVATE_READ_ONLY_REST_HOST:
                        raise Section1114OfflineSurfaceError("HOST_MISMATCH")
                    if parsed.path != endpoint:
                        raise Section1114OfflineSurfaceError("ENDPOINT_PATH_MISMATCH")
                    auth_headers = build_okx_live_canary_auth_headers_v1(
                        handle=handle, url=url, method="GET"
                    )
                    auth_headers["User-Agent"] = USER_AGENT_CANARY
                header_presence = _header_presence_v1(auth_headers)
                response = client.get(endpoint=endpoint, headers=auth_headers or None)
                send_attempted = True
                http_status = int(response.status_code)
                body_bytes = bytes(response.body_bytes)
                redirect_followed = bool(response.redirect_followed)
                elapsed_seconds = float(response.elapsed_seconds)
                method = str(response.method or "GET")
                if method != "GET":
                    raise Section1114OfflineSurfaceError("NON_GET_RESPONSE")
                if redirect_followed:
                    raise Section1114OfflineSurfaceError("REDIRECT_FOLLOWED")
            except LiveCanaryHttpError as exc:
                send_attempted = True
                get_error = str(exc)
                any_error = get_error if any_error is None else any_error
            finally:
                auth_headers.clear()
            response_time = _utc_now_iso_v1()
            payload: dict[str, Any] | None = None
            parsed_ok = False
            if body_bytes:
                try:
                    payload = parse_json_object_v1(body_bytes)
                    parsed_ok = True
                except LiveCanaryHttpError as exc:
                    get_error = str(exc) if get_error is None else get_error
                    any_error = get_error if any_error is None else any_error
            venue_code = str((payload or {}).get("code") or "") if payload else None
            data = (payload or {}).get("data") if payload else None
            data_present = isinstance(data, list) and any(
                isinstance(item, Mapping) for item in data
            )
            if endpoint == ENDPOINT_ACCOUNT_CONFIG and isinstance(data, list):
                for item in data:
                    if not isinstance(item, Mapping):
                        continue
                    uid = str(item.get("uid") or "").strip()
                    if uid and uid == str(REUSED_BINDING_ACCOUNT_SCOPE):
                        account_scope_match = True
                        break
            if redirect_followed:
                any_redirect = True
            sanitized = (
                _sanitize_account_config_payload_v1(payload)
                if endpoint == ENDPOINT_ACCOUNT_CONFIG
                else _sanitize_account_balance_payload_v1(payload)
            )
            success = _row_success_v1(
                http_status=http_status,
                venue_code=venue_code,
                parsed_ok=parsed_ok,
                data_present=data_present,
                method=method,
                redirect_followed=redirect_followed,
                get_error=get_error,
            )
            observations.append(
                {
                    "ENDPOINT": endpoint,
                    "METHOD": "GET",
                    "REQUEST_TIME_UTC": request_time,
                    "RESPONSE_TIME_UTC": response_time,
                    "HTTP_STATUS": http_status,
                    "OKX_CODE": venue_code,
                    "GET_ERROR": get_error,
                    "PARSED_OK": parsed_ok,
                    "DATA_PRESENT": data_present,
                    "REDIRECT_FOLLOWED": redirect_followed,
                    "ELAPSED_SECONDS": elapsed_seconds,
                    "BODY_SHA256": hashlib.sha256(body_bytes).hexdigest() if body_bytes else None,
                    "BODY_BYTE_LEN": len(body_bytes),
                    "HEADER_PRESENCE": header_presence,
                    "SANITIZED_PAYLOAD": sanitized,
                    "SUCCESS": success,
                    "VALUES_INCLUDED": False,
                }
            )
        if client.counters.request_count > PRIVATE_READ_ONLY_MAX_REQUEST_COUNT:
            raise Section1114OfflineSurfaceError("MAX_REQUEST_COUNT_EXCEEDED")
        if "POST" in client.counters.methods_used:
            raise Section1114OfflineSurfaceError("POST_INVOKED_BY_PRIVATE_READ_ONLY_PROOF")
    finally:
        if handle is not None:
            release_live_canary_ephemeral_material_v1(handle)
    by_endpoint = {str(row["ENDPOINT"]): row for row in observations}
    config_row = by_endpoint.get(ENDPOINT_ACCOUNT_CONFIG) or {}
    balance_row = by_endpoint.get(ENDPOINT_ACCOUNT_BALANCE) or {}
    config_ok = bool(config_row.get("SUCCESS") is True)
    balance_ok = bool(balance_row.get("SUCCESS") is True)
    both_get = all(str(row.get("METHOD") or "") == "GET" for row in observations)
    proven = (
        config_ok and balance_ok and both_get and any_redirect is False and len(observations) == 2
    )
    host_ok = any(row.get("HTTP_STATUS") is not None for row in observations) or (
        any_error is not None and "NETWORK" not in str(any_error).upper()
    )
    if any_error and all(row.get("HTTP_STATUS") is None for row in observations):
        if "NETWORK" in str(any_error).upper() or "TIMEOUT" in str(any_error).upper():
            host_ok = False
        elif "PRODUCTIVE_WIRE_SEND_DISABLED" in str(any_error):
            host_ok = False
    last_response = observations[-1]["RESPONSE_TIME_UTC"] if observations else None
    return {
        "GET_BINDING": binding,
        "OWNER_GO": OWNER_GO,
        "METHOD": "GET",
        "ENDPOINTS": list(PRIVATE_READ_ONLY_GET_ENDPOINTS),
        "HOST": PRIVATE_READ_ONLY_REST_HOST,
        "REQUEST_TIME_UTC": observations[0]["REQUEST_TIME_UTC"] if observations else None,
        "RESPONSE_TIME_UTC": last_response,
        "SEND_ATTEMPTED": send_attempted,
        "OBSERVATIONS": observations,
        "GET_ERROR": any_error,
        "REDIRECT_FOLLOWED": any_redirect,
        "ACCOUNT_SCOPE_MATCH": account_scope_match,
        "ACCOUNT_SCOPE_VALUE_INCLUDED": False,
        "READ_ACCESS_PROVEN_BY_SUCCESSFUL_PRIVATE_GETS": proven,
        "SECTION_11_13_2_TRADE_FALSE_ATTESTATION_USED": False,
        "VENUE_REQUESTS": len(observations) if send_attempted else 0,
        "PUBLIC_GET_USED": False,
        "PRIVATE_GET_USED": True,
        "CREDENTIAL_USE": bool(productive),
        "POST_USED": False,
        "RETRY_USED": False,
        "TARGET_HOST_RESOLVABLE_OR_CONNECTABLE": bool(host_ok),
        "AUTHENTICATION_PATH_FUNCTIONAL": config_ok,
        "CURRENT_ACCOUNT_OR_VENUE_READ_ACCESS_FUNCTIONAL": config_ok,
        "CURRENT_PRIVATE_GET_CONFIG_HTTP_200_OKX_0": config_ok,
        "CURRENT_PRIVATE_GET_BALANCE_HTTP_200_OKX_0": balance_ok,
        "BOTH_METHODS_GET": both_get,
        "NO_POST": True,
        "PARSEABLE_ACCOUNT_CONFIG_DATA": bool(config_row.get("DATA_PRESENT") is True),
        "PARSEABLE_ACCOUNT_BALANCE_DATA": bool(balance_row.get("DATA_PRESENT") is True),
        "NO_REDIRECT": any_redirect is False,
        "LIVE_PRIVATE_READ_ONLY_PROVEN": proven,
        "LIVE_ORDER_PLAN_OBSERVED": False,
        "VALUES_INCLUDED": False,
    }


def assert_no_post_in_read_only_evidence_v1(payload: Mapping[str, Any]) -> None:
    if payload.get("POST_USED") is True or payload.get("METHOD") == "POST":
        raise Section1114OfflineSurfaceError("POST_INVOKED_BY_PRIVATE_READ_ONLY_PROOF")
    dumped = json.dumps(dict(payload), sort_keys=True)
    if '"METHOD": "POST"' in dumped and payload.get("METHOD") != "GET":
        raise Section1114OfflineSurfaceError("POST_INVOKED_BY_PRIVATE_READ_ONLY_PROOF")
