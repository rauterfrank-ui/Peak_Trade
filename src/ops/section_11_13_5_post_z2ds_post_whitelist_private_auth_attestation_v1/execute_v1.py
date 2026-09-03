"""Execute exactly one authenticated GET /api/v5/account/config after whitelist add.

Constructs LiveCanaryHttpClientV1 itself. Reuses the existing canary GET
signer and SecretRef. No POST, transfer, order, funding GET, positions GET,
whitelist mutation, or capital movement. No second request on any outcome.
Does not close P08 and does not treat account/config as posSide proof.
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
from src.ops.section_11_13_5_post_z2ds_post_whitelist_private_auth_attestation_v1.constants_v1 import (
    AUTH_SUCCESS_FALSE,
    AUTH_SUCCESS_NOT_PROVEN,
    AUTH_SUCCESS_PROVEN,
    AUTHORIZED_HOST,
    BLOCKER_CLEARED,
    BLOCKER_NOT_PROVEN,
    BLOCKER_OPEN,
    CANONICAL_LIVE_EARLIEST_UNRESOLVED_DEPENDENCY,
    CLEARANCE_FALSE,
    CLEARANCE_NOT_PROVEN,
    CLEARANCE_PROVEN,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT_SECONDS,
    ENDPOINT,
    EXPECTED_ORIGIN_MAIN_SHA,
    FORBIDDEN_ENDPOINTS,
    MAX_HTTP_EXCHANGE_COUNT,
    MAX_NETWORK_REQUEST_COUNT,
    NEXT_AUTHORITY_BOUNDARY_CASE_A,
    NEXT_AUTHORITY_BOUNDARY_CASE_B,
    NEXT_AUTHORITY_BOUNDARY_CASE_C,
    OWNER_GO,
    PRIVATE_AUTH_RESULT_OTHER,
    RESULT_CLASS_200_OKX_0,
    RESULT_CLASS_401_50110,
    RESULT_CLASS_OTHER,
    REUSED_CREDENTIAL_CLASS,
    REUSED_REST_BASE,
    REUSED_REST_HOST,
    REUSED_SECRETREF_URI,
    REUSED_VENUE,
    THIS_SLICE,
)
from src.ops.section_11_13_5_post_z2ds_post_whitelist_private_auth_attestation_v1.persist_v1 import (
    persist_post_whitelist_private_auth_attestation_evidence_v1,
)
from src.ops.section_11_13_5_post_z2ds_private_get_current_50110_egress_capture_v1.execute_v1 import (
    extract_okx_reported_egress_ipv4_v1,
    sanitize_okx_message_v1,
)


class PostWhitelistPrivateAuthAttestationError(RuntimeError):
    """Fail-closed one-shot post-whitelist private auth GET violation."""


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
        raise PostWhitelistPrivateAuthAttestationError("GET_COUNT_NOT_ONE")
    if int(counters.get("REQUEST_COUNT", 0) or 0) != 1:
        raise PostWhitelistPrivateAuthAttestationError("REQUEST_COUNT_NOT_ONE")
    if int(counters.get("WRITE_REQUEST_COUNT", 0) or 0) != 0:
        raise PostWhitelistPrivateAuthAttestationError("WRITE_REQUEST_DETECTED")
    if int(counters.get("TRANSFER_REQUEST_COUNT", 0) or 0) != 0:
        raise PostWhitelistPrivateAuthAttestationError("TRANSFER_REQUEST_DETECTED")
    if int(counters.get("ORDER_REQUEST_COUNT", 0) or 0) != 0:
        raise PostWhitelistPrivateAuthAttestationError("ORDER_REQUEST_DETECTED")
    if int(counters.get("ENTRY_SUBMIT_COUNT", 0) or 0) != 0:
        raise PostWhitelistPrivateAuthAttestationError("ENTRY_SUBMIT_DETECTED")
    if int(counters.get("FLATTEN_SUBMIT_COUNT", 0) or 0) != 0:
        raise PostWhitelistPrivateAuthAttestationError("FLATTEN_SUBMIT_DETECTED")
    if list(client.counters.endpoints_used) != [ENDPOINT]:
        raise PostWhitelistPrivateAuthAttestationError("ENDPOINT_SET_MISMATCH")
    if list(client.counters.methods_used) != ["GET"]:
        raise PostWhitelistPrivateAuthAttestationError("NON_GET_METHOD_DETECTED")
    return counters


def adjudicate_private_auth_attestation_v1(
    *,
    http_status: int | None,
    venue_code: str | None,
    egress_ipv4: str | None,
) -> dict[str, Any]:
    code = "" if venue_code is None else str(venue_code).strip()
    if http_status == 200 and code == "0":
        return {
            "RESULT_CLASS": RESULT_CLASS_200_OKX_0,
            "PRIVATE_API_AUTH_SUCCESS": AUTH_SUCCESS_PROVEN,
            "RUNTIME_50110_CLEARANCE": CLEARANCE_PROVEN,
            "PRIVATE_AUTH_BLOCKER_50110": BLOCKER_CLEARED,
            "PRIVATE_AUTH_RESULT": RESULT_CLASS_200_OKX_0,
            "OKX_REPORTED_EGRESS_IPV4": "NONE",
            "OKX_REPORTED_EGRESS_IPV4_CAPTURED": False,
            "FORENSIC_RAW_OKX_REPORTED_EGRESS_IPV4": None,
            "NEXT_AUTHORITY_BOUNDARY": NEXT_AUTHORITY_BOUNDARY_CASE_A,
            "FAIL_CLOSED_RECORD": False,
            "ROOT_CAUSE": "UNPROVEN",
            "DO_NOT_INFER_ROOT_CAUSE": True,
        }
    if http_status == 401 and code == "50110":
        captured = bool(egress_ipv4)
        return {
            "RESULT_CLASS": RESULT_CLASS_401_50110,
            "PRIVATE_API_AUTH_SUCCESS": AUTH_SUCCESS_FALSE,
            "RUNTIME_50110_CLEARANCE": CLEARANCE_FALSE,
            "PRIVATE_AUTH_BLOCKER_50110": BLOCKER_OPEN,
            "PRIVATE_AUTH_RESULT": RESULT_CLASS_401_50110,
            "OKX_REPORTED_EGRESS_IPV4": egress_ipv4 if captured else "NOT_OBSERVED",
            "OKX_REPORTED_EGRESS_IPV4_CAPTURED": captured,
            "FORENSIC_RAW_OKX_REPORTED_EGRESS_IPV4": egress_ipv4 if captured else None,
            "NEXT_AUTHORITY_BOUNDARY": NEXT_AUTHORITY_BOUNDARY_CASE_B,
            "FAIL_CLOSED_RECORD": not captured,
            "ROOT_CAUSE": "UNPROVEN",
            "DO_NOT_INFER_ROOT_CAUSE": True,
        }
    return {
        "RESULT_CLASS": RESULT_CLASS_OTHER,
        "PRIVATE_API_AUTH_SUCCESS": AUTH_SUCCESS_NOT_PROVEN,
        "RUNTIME_50110_CLEARANCE": CLEARANCE_NOT_PROVEN,
        "PRIVATE_AUTH_BLOCKER_50110": BLOCKER_NOT_PROVEN,
        "PRIVATE_AUTH_RESULT": PRIVATE_AUTH_RESULT_OTHER,
        "OKX_REPORTED_EGRESS_IPV4": "NOT_OBSERVED",
        "OKX_REPORTED_EGRESS_IPV4_CAPTURED": False,
        "FORENSIC_RAW_OKX_REPORTED_EGRESS_IPV4": None,
        "NEXT_AUTHORITY_BOUNDARY": NEXT_AUTHORITY_BOUNDARY_CASE_C,
        "FAIL_CLOSED_RECORD": True,
        "ROOT_CAUSE": "UNPROVEN",
        "DO_NOT_INFER_ROOT_CAUSE": True,
    }


def execute_single_post_whitelist_private_auth_attestation_get_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    evidence_root: Path,
    vault_file: Path | str | None = None,
    transport: LiveCanaryTransportV1 | None = None,
) -> dict[str, Any]:
    """Perform exactly one allowlisted authenticated GET and persist attestation evidence."""
    owned = str(owner_go or "").strip()
    if owned != OWNER_GO:
        raise PostWhitelistPrivateAuthAttestationError("OWNER_GO_MISMATCH")
    bound_sha = str(origin_main_sha or "").strip()
    if bound_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise PostWhitelistPrivateAuthAttestationError("ORIGIN_MAIN_SHA_MISMATCH")
    if REUSED_REST_HOST != AUTHORIZED_HOST:
        raise PostWhitelistPrivateAuthAttestationError("HOST_MISMATCH")
    if "?" in ENDPOINT or ENDPOINT != "/api/v5/account/config":
        raise PostWhitelistPrivateAuthAttestationError("ENDPOINT_CONTRACT_DRIFT")
    if ENDPOINT in FORBIDDEN_ENDPOINTS:
        raise PostWhitelistPrivateAuthAttestationError("MUTATION_ENDPOINT_FORBIDDEN")

    productive = transport is None
    if productive:
        if vault_file is None or not str(vault_file).strip():
            raise PostWhitelistPrivateAuthAttestationError("VAULT_FILE_REQUIRED")
        transport = UrllibLiveCanaryTransportV1(wire_send_enabled=True)
    if isinstance(transport, UrllibLiveCanaryTransportV1) and not bool(
        getattr(transport, "wire_send_enabled", False)
    ):
        raise PostWhitelistPrivateAuthAttestationError("PRODUCTIVE_WIRE_DISABLED")

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
    try:
        url = f"{REUSED_REST_BASE}{ENDPOINT}"
        parsed = urlparse(url)
        if parsed.path != ENDPOINT or parsed.query:
            raise PostWhitelistPrivateAuthAttestationError("SIGNED_REQUEST_TARGET_MISMATCH")
        if parsed.hostname != AUTHORIZED_HOST:
            raise PostWhitelistPrivateAuthAttestationError("HOST_MISMATCH")
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
        http_status = int(response.status_code)
        body_bytes = bytes(response.body_bytes)
        redirect_followed = bool(response.redirect_followed)
        redirect_status = response.redirect_status
        if response.method != "GET":
            raise PostWhitelistPrivateAuthAttestationError("NON_GET_RESPONSE")
        if redirect_followed:
            raise PostWhitelistPrivateAuthAttestationError("REDIRECT_FOLLOWED")
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
            raise PostWhitelistPrivateAuthAttestationError("HTTP_EXCHANGE_COUNT_NOT_ONE")
        if productive and http_exchange_count != 1:
            raise PostWhitelistPrivateAuthAttestationError("NETWORK_REQUEST_COUNT_NOT_ONE")
    elif http_exchange_count > MAX_HTTP_EXCHANGE_COUNT:
        raise PostWhitelistPrivateAuthAttestationError("HTTP_EXCHANGE_COUNT_EXCEEDED")

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
    egress_ipv4 = extract_okx_reported_egress_ipv4_v1(venue_msg_raw)
    data = (payload or {}).get("data") if payload else None
    data_row_count = len(data) if isinstance(data, list) else None
    outcome = adjudicate_private_auth_attestation_v1(
        http_status=http_status,
        venue_code=venue_code,
        egress_ipv4=egress_ipv4,
    )
    standing_closed = {
        "PREREQUISITE_08_CLOSED": False,
        "TARGET_POSITION_NONZERO_PROVEN": False,
        "POSITION_STATE_OBSERVED": False,
        "G_POSMODE_SUBMIT_BODY_PROVEN": False,
        "P08_OBSERVATION_PERFORMED": False,
        "P08_CLOSED_INFERRED": False,
        "FUNDING_CLOSED_INFERRED": False,
        "ACCOUNT_CONFIG_USED_AS_POSSIDE_PROOF": False,
        "G_POSMODE_REOPENED": False,
        "G_POSMODE_CLOSED": False,
    }

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    pack = Path(evidence_root) / run_id
    snapshot = {
        "DOCUMENT_CLASS": "POST_Z2DS_POST_WHITELIST_PRIVATE_AUTH_ATTESTATION_SINGLE_GET_V1",
        "DOCUMENT_ROLE": "GET_ONLY_FRESH_EVIDENCE_NON_SSOT",
        "AUTHORITY": "NONE",
        "THIS_ARTIFACT_IS_NOT_CANONICAL": True,
        "OWNER_GO": owned,
        "OWNER_GO_CONSUMED": owner_go_consumed,
        "THIS_SLICE": THIS_SLICE,
        "BOUND_ORIGIN_MAIN_SHA": bound_sha,
        "AUTHORIZED_ENDPOINT": "GET /api/v5/account/config",
        "ENDPOINT": ENDPOINT,
        "ENDPOINT_IDENTITY": ENDPOINT,
        "METHOD": "GET",
        "HOST": REUSED_REST_HOST,
        "VENUE": REUSED_VENUE,
        "QUERY_PARAMETERS": {},
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
        "BODY_SHA256": hashlib.sha256(body_bytes).hexdigest() if body_bytes else None,
        "COUNTERS": counters,
        "ACTUAL_NETWORK_REQUEST_COUNT": int(counters.get("GET_REQUEST_COUNT", 0) or 0),
        "HTTP_EXCHANGE_COUNT": http_exchange_count,
        "GET_REQUEST_COUNT": int(counters.get("GET_REQUEST_COUNT", 0) or 0),
        "WRITE_REQUEST_COUNT": int(counters.get("WRITE_REQUEST_COUNT", 0) or 0),
        "POST_COUNT": 0,
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
        "DATA_ROW_COUNT": data_row_count,
        "DATA_VALUES_INCLUDED": False,
        "VENUE_CODE": venue_code,
        "VENUE_MSG": venue_msg,
        **outcome,
        **standing_closed,
        "FUNDING_GET_PERFORMED": False,
        "POSITIONS_GET_PERFORMED": False,
        "BALANCE_GET_PERFORMED": False,
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
        "CANONICAL_LIVE_EARLIEST_UNRESOLVED_DEPENDENCY": (
            CANONICAL_LIVE_EARLIEST_UNRESOLVED_DEPENDENCY
        ),
    }
    summary = {
        "DOCUMENT_CLASS": "POST_Z2DS_POST_WHITELIST_PRIVATE_AUTH_ATTESTATION_SINGLE_GET_V1",
        "DOCUMENT_ROLE": "DERIVED_NON_SSOT",
        "OWNER_GO": owned,
        "OWNER_GO_CONSUMED": owner_go_consumed,
        "THIS_SLICE": THIS_SLICE,
        "BOUND_ORIGIN_MAIN_SHA": bound_sha,
        "ENDPOINT": ENDPOINT,
        "ENDPOINT_IDENTITY": ENDPOINT,
        "METHOD": "GET",
        "HOST": REUSED_REST_HOST,
        "HTTP_STATUS": http_status,
        "OKX_CODE": venue_code,
        "OKX_MESSAGE": venue_msg,
        "SANITIZED_OKX_MESSAGE": venue_msg,
        "SEND_ATTEMPTED": send_attempted,
        "AUTH_HEADER_SENT": bool(header_presence.get("AUTH_KEY_HEADER_PRESENT")),
        "GET_REQUEST_COUNT": counters.get("GET_REQUEST_COUNT"),
        "ACTUAL_NETWORK_REQUEST_COUNT": int(counters.get("GET_REQUEST_COUNT", 0) or 0),
        "HTTP_EXCHANGE_COUNT": http_exchange_count,
        "ENDPOINTS_USED": list(client.counters.endpoints_used),
        "METHODS_USED": list(client.counters.methods_used),
        "REDIRECT_FOLLOWED": redirect_followed,
        "POST_COUNT": 0,
        "WRITE_REQUEST_COUNT": counters.get("WRITE_REQUEST_COUNT"),
        "TRANSFER_REQUEST_COUNT": counters.get("TRANSFER_REQUEST_COUNT"),
        "ORDER_REQUEST_COUNT": counters.get("ORDER_REQUEST_COUNT"),
        **outcome,
        **standing_closed,
        "DATA_ROW_COUNT": data_row_count,
        "DATA_VALUES_INCLUDED": False,
        "WHITELIST_MUTATION_PERFORMED": False,
        "FUNDING_ACTION": False,
        "ORDER_SUBMIT_EXECUTED": False,
        "POSITION_CREATION_EXECUTED": False,
        "POSITION_MODIFICATION_EXECUTED": False,
        "LIVE_EXECUTION": False,
        "CANARY_EXECUTION": False,
        "CORE_CHANGED": False,
        "NEW_AUTHORITY_CREATED": False,
        "ATLAS_AUTHORITY": "NONE",
        "LANDSCAPE_AUTHORITY": "NONE",
        "LIVE_AUTHORIZED": False,
        "TESTNET_AUTHORIZED": False,
        "CANARY_AUTHORIZED": False,
        "SUBMIT_UNLOCKED": False,
        "EXECUTION_READY": False,
        "SECRET_VALUES_INCLUDED": False,
        "FUNDING_STATE": "UNPROVEN",
        "POSITION_STATE": "UNPROVEN",
        "REQUEST_TIMESTAMP": request_time,
        "RESPONSE_TIMESTAMP": response_time,
        "TARGET_SECRETREF_URI": REUSED_SECRETREF_URI,
    }
    verified = persist_post_whitelist_private_auth_attestation_evidence_v1(
        pack=pack,
        origin_main_sha=bound_sha,
        snapshot=snapshot,
        summary=summary,
    )
    if get_error:
        raise PostWhitelistPrivateAuthAttestationError(f"PRIVATE_AUTH_GET_FAILED:{get_error}")
    if parse_error:
        raise PostWhitelistPrivateAuthAttestationError(
            f"PRIVATE_AUTH_GET_PARSE_FAIL_CLOSED:{parse_error}"
        )
    return {
        "EVIDENCE_PACK": str(pack),
        "MANIFEST_VERIFY_RC": int(verified.get("MANIFEST_VERIFY_RC", 1)),
        "summary": summary,
    }
