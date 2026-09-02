"""Execute exactly one authenticated GET /api/v5/account/config.

Constructs LiveCanaryHttpClientV1 itself. Reuses the existing canary GET
signer and SecretRef. No POST, transfer, order, funding GET, positions GET,
or capital movement. No second request on any outcome.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

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
from src.ops.section_11_13_5_z2dl_post_remediation_single_private_auth_get_v1.constants_v1 import (
    AUTHORIZED_HOST,
    CANONICAL_LIVE_EARLIEST_UNRESOLVED_DEPENDENCY,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT_SECONDS,
    ENDPOINT,
    EXPECTED_ORIGIN_MAIN_SHA,
    FORBIDDEN_ENDPOINTS,
    MAX_HTTP_EXCHANGE_COUNT,
    MAX_NETWORK_REQUEST_COUNT,
    OWNER_GO,
    REUSED_CREDENTIAL_CLASS,
    REUSED_REST_BASE,
    REUSED_REST_HOST,
    REUSED_SECRETREF_URI,
    REUSED_VENUE,
    SANITIZED_EGRESS_EVIDENCE,
    THIS_SLICE,
)
from src.ops.section_11_13_5_z2dl_post_remediation_single_private_auth_get_v1.persist_v1 import (
    persist_z2dl_private_auth_get_evidence_v1,
)


class Z2DLPrivateAuthGetError(RuntimeError):
    """Fail-closed Z2DL one-shot GET violation."""


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
        raise Z2DLPrivateAuthGetError("GET_COUNT_NOT_ONE")
    if int(counters.get("REQUEST_COUNT", 0) or 0) != 1:
        raise Z2DLPrivateAuthGetError("REQUEST_COUNT_NOT_ONE")
    if int(counters.get("WRITE_REQUEST_COUNT", 0) or 0) != 0:
        raise Z2DLPrivateAuthGetError("WRITE_REQUEST_DETECTED")
    if int(counters.get("TRANSFER_REQUEST_COUNT", 0) or 0) != 0:
        raise Z2DLPrivateAuthGetError("TRANSFER_REQUEST_DETECTED")
    if int(counters.get("ORDER_REQUEST_COUNT", 0) or 0) != 0:
        raise Z2DLPrivateAuthGetError("ORDER_REQUEST_DETECTED")
    if int(counters.get("ENTRY_SUBMIT_COUNT", 0) or 0) != 0:
        raise Z2DLPrivateAuthGetError("ENTRY_SUBMIT_DETECTED")
    if int(counters.get("FLATTEN_SUBMIT_COUNT", 0) or 0) != 0:
        raise Z2DLPrivateAuthGetError("FLATTEN_SUBMIT_DETECTED")
    if list(client.counters.endpoints_used) != [ENDPOINT]:
        raise Z2DLPrivateAuthGetError("ENDPOINT_SET_MISMATCH")
    if list(client.counters.methods_used) != ["GET"]:
        raise Z2DLPrivateAuthGetError("NON_GET_METHOD_DETECTED")
    return counters


def _classify_auth_outcome_v1(
    *,
    http_status: int | None,
    venue_code: str | None,
) -> dict[str, Any]:
    code = "" if venue_code is None else str(venue_code).strip()
    if http_status == 200 and code == "0":
        return {
            "PRIVATE_API_AUTH_SUCCESS": True,
            "AUTHENTICATED_PRIVATE_API_REACHABILITY_PROVEN": True,
            "RUNTIME_50110_CLEARANCE": True,
            "ROOT_CAUSE": "UNPROVEN",
        }
    if code == "50110":
        return {
            "PRIVATE_API_AUTH_SUCCESS": False,
            "AUTHENTICATED_PRIVATE_API_REACHABILITY_PROVEN": False,
            "RUNTIME_50110_CLEARANCE": False,
            "ROOT_CAUSE": "UNPROVEN",
        }
    return {
        "PRIVATE_API_AUTH_SUCCESS": False,
        "AUTHENTICATED_PRIVATE_API_REACHABILITY_PROVEN": False,
        "RUNTIME_50110_CLEARANCE": "NOT_TESTED",
        "ROOT_CAUSE": "UNPROVEN",
    }


def execute_single_actual_private_auth_get_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    evidence_root: Path,
    vault_file: Path | str | None = None,
    transport: LiveCanaryTransportV1 | None = None,
) -> dict[str, Any]:
    """Perform exactly one allowlisted authenticated GET and persist evidence."""
    owned = str(owner_go or "").strip()
    if owned != OWNER_GO:
        raise Z2DLPrivateAuthGetError("OWNER_GO_MISMATCH")
    bound_sha = str(origin_main_sha or "").strip()
    if bound_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise Z2DLPrivateAuthGetError("ORIGIN_MAIN_SHA_MISMATCH")
    if REUSED_REST_HOST != AUTHORIZED_HOST:
        raise Z2DLPrivateAuthGetError("HOST_MISMATCH")
    if "?" in ENDPOINT or ENDPOINT != "/api/v5/account/config":
        raise Z2DLPrivateAuthGetError("ENDPOINT_CONTRACT_DRIFT")
    if ENDPOINT in FORBIDDEN_ENDPOINTS:
        raise Z2DLPrivateAuthGetError("MUTATION_ENDPOINT_FORBIDDEN")

    productive = transport is None
    if productive:
        if vault_file is None or not str(vault_file).strip():
            raise Z2DLPrivateAuthGetError("VAULT_FILE_REQUIRED")
        transport = UrllibLiveCanaryTransportV1(wire_send_enabled=True)
    if isinstance(transport, UrllibLiveCanaryTransportV1) and not bool(
        getattr(transport, "wire_send_enabled", False)
    ):
        raise Z2DLPrivateAuthGetError("PRODUCTIVE_WIRE_DISABLED")

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
    redirect_followed = False
    redirect_status: int | None = None
    try:
        url = f"{REUSED_REST_BASE}{ENDPOINT}"
        parsed = urlparse(url)
        if parsed.path != ENDPOINT or parsed.query:
            raise Z2DLPrivateAuthGetError("SIGNED_REQUEST_TARGET_MISMATCH")
        if parsed.hostname != AUTHORIZED_HOST:
            raise Z2DLPrivateAuthGetError("HOST_MISMATCH")
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
        http_status = int(response.status_code)
        body_bytes = bytes(response.body_bytes)
        redirect_followed = bool(response.redirect_followed)
        redirect_status = response.redirect_status
        if response.method != "GET":
            raise Z2DLPrivateAuthGetError("NON_GET_RESPONSE")
        if redirect_followed:
            raise Z2DLPrivateAuthGetError("REDIRECT_FOLLOWED")
    except LiveCanaryHttpError as exc:
        send_attempted = True
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
            raise Z2DLPrivateAuthGetError("HTTP_EXCHANGE_COUNT_NOT_ONE")
        if productive and http_exchange_count != 1:
            raise Z2DLPrivateAuthGetError("NETWORK_REQUEST_COUNT_NOT_ONE")
    elif http_exchange_count > MAX_HTTP_EXCHANGE_COUNT:
        raise Z2DLPrivateAuthGetError("HTTP_EXCHANGE_COUNT_EXCEEDED")

    payload: dict[str, Any] | None = None
    parse_error: str | None = None
    if body_bytes:
        try:
            payload = parse_json_object_v1(body_bytes)
        except LiveCanaryHttpError as exc:
            parse_error = str(exc)

    venue_code = str((payload or {}).get("code") or "") if payload else None
    venue_msg = str((payload or {}).get("msg") or "")[:200] if payload else None
    data = (payload or {}).get("data") if payload else None
    data_row_count = len(data) if isinstance(data, list) else None
    outcome = _classify_auth_outcome_v1(http_status=http_status, venue_code=venue_code)

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    pack = Path(evidence_root) / run_id
    snapshot = {
        "DOCUMENT_CLASS": "Z2DL_POST_REMEDIATION_SINGLE_PRIVATE_AUTH_GET_V1",
        "DOCUMENT_ROLE": "GET_ONLY_FRESH_EVIDENCE_NON_SSOT",
        "AUTHORITY": "NONE",
        "THIS_ARTIFACT_IS_NOT_CANONICAL": True,
        "OWNER_GO": owned,
        "THIS_SLICE": THIS_SLICE,
        "BOUND_ORIGIN_MAIN_SHA": bound_sha,
        "AUTHORIZED_ENDPOINT": "GET /api/v5/account/config",
        "ENDPOINT": ENDPOINT,
        "METHOD": "GET",
        "HOST": REUSED_REST_HOST,
        "VENUE": REUSED_VENUE,
        "QUERY_PARAMETERS": {},
        "REQUEST_TIME_UTC": request_time,
        "RESPONSE_TIME_UTC": response_time,
        "UTC_TIMESTAMP": request_time,
        "HTTP_STATUS": http_status,
        "OKX_CODE": venue_code,
        "OKX_MESSAGE": venue_msg,
        "SEND_ATTEMPTED": send_attempted,
        "GET_ERROR": get_error,
        "PARSE_ERROR": parse_error,
        "BODY_BYTES": len(body_bytes),
        "BODY_SHA256": hashlib.sha256(body_bytes).hexdigest() if body_bytes else None,
        "COUNTERS": counters,
        "ACTUAL_NETWORK_REQUEST_COUNT": int(counters.get("GET_REQUEST_COUNT", 0) or 0),
        "HTTP_EXCHANGE_COUNT": http_exchange_count,
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
        "SANITIZED_EGRESS_EVIDENCE": SANITIZED_EGRESS_EVIDENCE,
        "AUTH_HEADER_SENT": bool(header_presence.get("AUTH_KEY_HEADER_PRESENT")),
        "SECRET_VALUES_INCLUDED": False,
        "DATA_ROW_COUNT": data_row_count,
        "DATA_VALUES_INCLUDED": False,
        "VENUE_CODE": venue_code,
        "VENUE_MSG": venue_msg,
        **outcome,
        "FUNDING_GET_PERFORMED": False,
        "POSITIONS_GET_PERFORMED": False,
        "BALANCE_GET_PERFORMED": False,
        "POST_PERFORMED": False,
        "ORDER_PERFORMED": False,
        "EXECUTION_PERFORMED": False,
        "LIVE_ARMING_PERFORMED": False,
        "FUNDING_STATE": "UNPROVEN",
        "POSITION_STATE": "UNPROVEN",
        "AVAILABLE_MARGIN": "UNPROVEN",
        "PRETRADE_READY": False,
        "POST_AUTH_VIABILITY": "UNPROVEN",
        "LIVE_AUTHORIZED": False,
        "TESTNET_AUTHORIZED": False,
        "CANARY_AUTHORIZED": False,
        "TRANSFER_ALLOWED": False,
        "POST_ALLOWED": False,
        "ORDER_ALLOWED": False,
        "CAPITAL_MOVEMENT_ALLOWED": False,
        "SUBMIT_UNLOCKED": False,
        "EXECUTION_READY": False,
        "PREREQUISITE_08_CLOSED": False,
        "CANONICAL_LIVE_EARLIEST_UNRESOLVED_DEPENDENCY": (
            CANONICAL_LIVE_EARLIEST_UNRESOLVED_DEPENDENCY
        ),
    }
    summary = {
        "DOCUMENT_CLASS": "Z2DL_POST_REMEDIATION_SINGLE_PRIVATE_AUTH_GET_V1",
        "DOCUMENT_ROLE": "DERIVED_NON_SSOT",
        "OWNER_GO": owned,
        "THIS_SLICE": THIS_SLICE,
        "BOUND_ORIGIN_MAIN_SHA": bound_sha,
        "ENDPOINT": ENDPOINT,
        "METHOD": "GET",
        "HOST": REUSED_REST_HOST,
        "HTTP_STATUS": http_status,
        "OKX_CODE": venue_code,
        "OKX_MESSAGE": venue_msg,
        "GET_REQUEST_COUNT": counters.get("GET_REQUEST_COUNT"),
        "ACTUAL_NETWORK_REQUEST_COUNT": int(counters.get("GET_REQUEST_COUNT", 0) or 0),
        "HTTP_EXCHANGE_COUNT": http_exchange_count,
        "REDIRECT_FOLLOWED": redirect_followed,
        "POST_COUNT": 0,
        "WRITE_REQUEST_COUNT": counters.get("WRITE_REQUEST_COUNT"),
        "TRANSFER_REQUEST_COUNT": counters.get("TRANSFER_REQUEST_COUNT"),
        "ORDER_REQUEST_COUNT": counters.get("ORDER_REQUEST_COUNT"),
        **outcome,
        "DATA_ROW_COUNT": data_row_count,
        "DATA_VALUES_INCLUDED": False,
        "LIVE_AUTHORIZED": False,
        "TESTNET_AUTHORIZED": False,
        "CANARY_AUTHORIZED": False,
        "SUBMIT_UNLOCKED": False,
        "EXECUTION_READY": False,
        "SECRET_VALUES_INCLUDED": False,
        "PREREQUISITE_08_CLOSED": False,
        "FUNDING_STATE": "UNPROVEN",
        "POSITION_STATE": "UNPROVEN",
    }
    verified = persist_z2dl_private_auth_get_evidence_v1(
        pack=pack,
        origin_main_sha=bound_sha,
        snapshot=snapshot,
        summary=summary,
    )
    if get_error:
        raise Z2DLPrivateAuthGetError(f"PRIVATE_AUTH_GET_FAILED:{get_error}")
    if parse_error:
        raise Z2DLPrivateAuthGetError(f"PRIVATE_AUTH_GET_PARSE_FAIL_CLOSED:{parse_error}")
    if outcome["PRIVATE_API_AUTH_SUCCESS"] is not True:
        raise Z2DLPrivateAuthGetError("PRIVATE_AUTH_GET_NOT_SUCCESS")
    return {
        "EVIDENCE_PACK": str(pack),
        "MANIFEST_VERIFY_RC": int(verified.get("MANIFEST_VERIFY_RC", 1)),
        "summary": summary,
    }
