"""Minimum governed private GET for §11.14 LIVE_POSITION_RECONCILED.

Exactly one GET on eea.okx.com, identity-scoped to the bound Live submit:
GET /api/v5/account/positions?instType=FUTURES&instId=<bound>

Does not POST, cancel, amend, retry, flatten, or second-submit. Secrets are
never logged, printed, or persisted. Empty data is not treated as zero.
Historical position evidence is not substituted. Fill/fee/order-state are
not inferred as position.
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
    ENDPOINT_ACCOUNT_POSITIONS,
    GET_ENDPOINTS_PRIVATE,
    REQUIRED_CREDENTIAL_CLASS,
    REQUIRED_SECRETREF_URI,
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
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    LIVE_FEE_OBSERVED,
    POST_ALLOWED,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.fill_observed_gets_v1 import (
    FILL_GET_REST_BASE,
    FILL_GET_REST_HOST,
    FILL_GET_TIMEOUT_SECONDS,
    _body_utf8_exact_v1,
    _path_only_v1,
    _query_from_endpoint_v1,
    _sanitize_payload_v1,
    _sanitize_row_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.fill_observed_identity_v1 import (
    BOUND_INST_TYPE,
    BOUND_INSTID,
    BOUND_ORDID,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.reachability_private_get_v1 import (
    _header_presence_v1,
)

THIS_OWNER_GO = (
    "PEAK_TRADE_OWNER_GO_SECTION_11_14_LIVE_POSITION_RECONCILED_MAXIMUM_SAFE_LEVERAGE_V2"
)
EXPECTED_ORIGIN_MAIN_SHA = "2d46611a4485a5422279e75fc762dd2285f7cc15"
POSITION_GET_REST_HOST = FILL_GET_REST_HOST
POSITION_GET_REST_BASE = FILL_GET_REST_BASE
POSITION_GET_METHOD = "GET"
POSITION_GET_MAX_REQUEST_COUNT = 1
POSITION_GET_MAX_RETRIES = 0
POSITION_GET_TIMEOUT_SECONDS = FILL_GET_TIMEOUT_SECONDS

POSITION_ROW_ALLOWLIST = frozenset(
    {
        "availPos",
        "avgPx",
        "cTime",
        "ccy",
        "instId",
        "instType",
        "lever",
        "mgnMode",
        "pos",
        "posCcy",
        "posId",
        "posSide",
        "uTime",
        "upl",
    }
)


def bound_positions_get_endpoint_v1() -> str:
    query = build_account_positions_query_v1(
        inst_type=BOUND_INST_TYPE,
        inst_id=BOUND_INSTID,
    )
    if query.empty_result_is_zero is True:
        raise Section1114OfflineSurfaceError("EMPTY_RESULT_MUST_NOT_BE_ZERO")
    return query.path_with_query()


def bind_position_reconciled_gets_before_request_v1() -> dict[str, Any]:
    return {
        "WHY_GET_REQUIRED": (
            "LIVE_POSITION_RECONCILED requires a current venue-native position "
            "row bound to the observed Peak_Trade Live fill/fee identity. GET "
            "/api/v5/account/positions scoped to the bound instId/instType is "
            "the position-row source. Empty data is not zero. FillSz alone is "
            "not position."
        ),
        "REQUIRED_FACT": "CURRENT_VENUE_POSITION_RECONCILED_TO_FILL_IDENTITY",
        "ENDPOINTS": [bound_positions_get_endpoint_v1()],
        "ENDPOINT_PATHS": [ENDPOINT_ACCOUNT_POSITIONS],
        "METHOD": POSITION_GET_METHOD,
        "EXPECTED_MUTATION": "NONE",
        "MAXIMUM_REQUEST_COUNT": POSITION_GET_MAX_REQUEST_COUNT,
        "RETRY": False,
        "PUBLIC_GET": False,
        "PRIVATE_GET": True,
        "POST": False,
        "CANCEL": False,
        "AMEND": False,
        "FLATTEN_EXECUTE": False,
        "BOUND_ORDID": BOUND_ORDID,
        "BOUND_INSTID": BOUND_INSTID,
        "LIVE_ACCOUNTING_RECONSTRUCTED_PROMOTION": False,
        "EMPTY_DATA_IS_ZERO": False,
        "HISTORICAL_POSITION_SUBSTITUTION": False,
        "INFERENCE_FROM_FILL_ALONE": False,
        "INFERENCE_FROM_FEE_ALONE": False,
        "INFERENCE_FROM_ORDER_STATE_ALONE": False,
    }


def _utc_now_iso_v1() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def execute_position_reconciled_gets_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    vault_file: Path | None = None,
    transport: LiveCanaryTransportV1 | None = None,
) -> dict[str, Any]:
    if str(owner_go or "").strip() != THIS_OWNER_GO:
        raise Section1114OfflineSurfaceError("OWNER_GO_MISMATCH")
    if str(origin_main_sha or "").strip() != EXPECTED_ORIGIN_MAIN_SHA:
        raise Section1114OfflineSurfaceError("ORIGIN_MAIN_SHA_MISMATCH")
    if LIVE_FEE_OBSERVED is not True:
        raise Section1114OfflineSurfaceError("FEE_PREDECESSOR_FALSE")
    if POST_ALLOWED is True:
        raise Section1114OfflineSurfaceError("POST_MUST_REMAIN_FORBIDDEN")
    positions_endpoint = bound_positions_get_endpoint_v1()
    path = _path_only_v1(positions_endpoint)
    if path not in GET_ENDPOINTS_PRIVATE:
        raise Section1114OfflineSurfaceError(f"ENDPOINT_NOT_PRIVATE_ALLOWLIST:{path}")
    if path != ENDPOINT_ACCOUNT_POSITIONS:
        raise Section1114OfflineSurfaceError("ENDPOINT_PATH_MISMATCH")
    binding = bind_position_reconciled_gets_before_request_v1()
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
        rest_base=POSITION_GET_REST_BASE,
        rest_host=POSITION_GET_REST_HOST,
        transport=live_transport,
        max_request_count=POSITION_GET_MAX_REQUEST_COUNT,
        max_retries=POSITION_GET_MAX_RETRIES,
        timeout_seconds=POSITION_GET_TIMEOUT_SECONDS,
    )
    observations: list[dict[str, Any]] = []
    raw_exchanges: list[dict[str, Any]] = []
    any_redirect = False
    any_error: str | None = None
    send_attempted = False
    try:
        query = _query_from_endpoint_v1(positions_endpoint)
        if query.get("instId") != BOUND_INSTID or query.get("instType") != BOUND_INST_TYPE:
            raise Section1114OfflineSurfaceError("QUERY_IDENTITY_MISMATCH")
        auth_headers: dict[str, str] = {}
        request_time = _utc_now_iso_v1()
        http_status: int | None = None
        body_bytes = b""
        get_error: str | None = None
        redirect_followed = False
        redirect_status: int | None = None
        elapsed_seconds: float | None = None
        method = "GET"
        header_presence = _header_presence_v1({})
        response_headers_safe: dict[str, str] = {}
        try:
            if productive:
                url = f"{POSITION_GET_REST_BASE}{positions_endpoint}"
                parsed = urlparse(url)
                if parsed.hostname != POSITION_GET_REST_HOST:
                    raise Section1114OfflineSurfaceError("HOST_MISMATCH")
                if parsed.path != ENDPOINT_ACCOUNT_POSITIONS:
                    raise Section1114OfflineSurfaceError("ENDPOINT_PATH_MISMATCH")
                auth_headers = build_okx_live_canary_auth_headers_v1(
                    handle=handle, url=url, method="GET"
                )
                auth_headers["User-Agent"] = USER_AGENT_CANARY
            header_presence = _header_presence_v1(auth_headers)
            response = client.get(endpoint=positions_endpoint, headers=auth_headers or None)
            send_attempted = True
            http_status = int(response.status_code)
            body_bytes = bytes(response.body_bytes)
            redirect_followed = bool(response.redirect_followed)
            redirect_status = response.redirect_status
            elapsed_seconds = float(response.elapsed_seconds)
            method = str(response.method or "GET")
            response_headers_safe = dict(response.response_headers_safe or {})
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
        parse_error: str | None = None
        if body_bytes:
            try:
                payload = parse_json_object_v1(body_bytes)
                parsed_ok = True
            except LiveCanaryHttpError as exc:
                parse_error = str(exc)
                get_error = str(exc) if get_error is None else get_error
                any_error = get_error if any_error is None else any_error
        venue_code = str((payload or {}).get("code") or "") if payload else None
        data = (payload or {}).get("data") if payload else None
        data_is_list = isinstance(data, list)
        data_rows = data if data_is_list else []
        if redirect_followed:
            any_redirect = True
        sanitized = _sanitize_payload_v1(payload, POSITION_ROW_ALLOWLIST)
        object_rows = [item for item in data_rows if isinstance(item, Mapping)]
        observations.append(
            {
                "GET_ROLE": "POSITIONS",
                "ENDPOINT": positions_endpoint,
                "ENDPOINT_PATH": path,
                "QUERY_PARAMETERS": query,
                "METHOD": "GET",
                "REQUEST_TIME_UTC": request_time,
                "RESPONSE_TIME_UTC": response_time,
                "HTTP_STATUS": http_status,
                "OKX_CODE": venue_code,
                "GET_ERROR": get_error,
                "PARSE_ERROR": parse_error,
                "PARSED_OK": parsed_ok,
                "DATA_IS_LIST": data_is_list,
                "DATA_ROW_COUNT": len(data_rows) if data_is_list else None,
                "REDIRECT_FOLLOWED": redirect_followed,
                "ELAPSED_SECONDS": elapsed_seconds,
                "BODY_SHA256": hashlib.sha256(body_bytes).hexdigest() if body_bytes else None,
                "BODY_BYTE_LEN": len(body_bytes),
                "HEADER_PRESENCE": header_presence,
                "SANITIZED_PAYLOAD": sanitized,
                "OBJECT_ROWS": [
                    _sanitize_row_v1(item, POSITION_ROW_ALLOWLIST) for item in object_rows
                ],
                "VALUES_INCLUDED": False,
            }
        )
        raw_exchanges.append(
            {
                "DOCUMENT_CLASS": "SECTION_11_14_LIVE_POSITION_RECONCILED_RAW_EXCHANGE_V1",
                "DOCUMENT_ROLE": "FORENSIC_RAW_NOT_CANONICAL_NOT_ADJUDICATION",
                "AUTHORITY": "NONE",
                "THIS_ARTIFACT_IS_NOT_CANONICAL": True,
                "GET_ROLE": "POSITIONS",
                "METHOD": "GET",
                "HOST": POSITION_GET_REST_HOST,
                "ENDPOINT": positions_endpoint,
                "ENDPOINT_PATH": path,
                "QUERY_PARAMETERS": query,
                "REQUEST_TIME_UTC": request_time,
                "RESPONSE_TIME_UTC": response_time,
                "HTTP_STATUS": http_status,
                "BODY_BYTES": len(body_bytes),
                "BODY_SHA256": hashlib.sha256(body_bytes).hexdigest() if body_bytes else None,
                "BODY_UTF8_EXACT": _body_utf8_exact_v1(body_bytes),
                "BODY_WAS_JSON_RESERIALIZED": False,
                "RESPONSE_HEADERS_SAFE": dict(response_headers_safe)
                if response_headers_safe
                else safe_response_headers_v1({}),
                "REDIRECT_FOLLOWED": redirect_followed,
                "REDIRECT_STATUS": redirect_status,
                "ELAPSED_SECONDS": elapsed_seconds,
                "SEND_ATTEMPTED": send_attempted,
                "GET_ERROR": get_error,
                "PARSE_ERROR": parse_error,
                "SECRET_VALUES_INCLUDED": False,
            }
        )
        if client.counters.request_count > POSITION_GET_MAX_REQUEST_COUNT:
            raise Section1114OfflineSurfaceError("MAX_REQUEST_COUNT_EXCEEDED")
        if "POST" in client.counters.methods_used:
            raise Section1114OfflineSurfaceError("POST_INVOKED_BY_POSITION_RECONCILIATION")
        if int(client.counters.write_request_count or 0) != 0:
            raise Section1114OfflineSurfaceError("WRITE_REQUEST_INVOKED_BY_POSITION_RECONCILIATION")
    finally:
        if handle is not None:
            release_live_canary_ephemeral_material_v1(handle)
    positions_row = observations[0] if observations else {}
    position_objects = list(positions_row.get("OBJECT_ROWS") or [])
    return {
        "GET_BINDING": binding,
        "OWNER_GO": THIS_OWNER_GO,
        "METHOD": "GET",
        "ENDPOINTS": [positions_endpoint],
        "HOST": POSITION_GET_REST_HOST,
        "REQUEST_TIME_UTC": positions_row.get("REQUEST_TIME_UTC"),
        "RESPONSE_TIME_UTC": positions_row.get("RESPONSE_TIME_UTC"),
        "SEND_ATTEMPTED": send_attempted,
        "OBSERVATIONS": observations,
        "RAW_EXCHANGES": raw_exchanges,
        "GET_ERROR": any_error,
        "REDIRECT_FOLLOWED": any_redirect,
        "VENUE_REQUESTS": len(observations) if send_attempted else 0,
        "GET_REQUEST_COUNT": int(client.counters.get_request_count or 0),
        "PUBLIC_GET_USED": False,
        "PRIVATE_GET_USED": True,
        "CREDENTIAL_USE": bool(productive),
        "POST_USED": False,
        "CANCEL_USED": False,
        "AMEND_USED": False,
        "RETRY_USED": False,
        "FLATTEN_EXECUTE_USED": False,
        "NO_POST": True,
        "source_kind": "GOVERNED_CURRENT_PRIVATE_GET",
        "POSITIONS_GET_PERFORMED": bool(positions_row),
        "positions_http_status": positions_row.get("HTTP_STATUS"),
        "positions_okx_code": positions_row.get("OKX_CODE"),
        "positions_json_parse_ok": positions_row.get("PARSED_OK"),
        "positions_redirect_followed": bool(positions_row.get("REDIRECT_FOLLOWED")),
        "positions_method": "GET",
        "positions_data_is_list": positions_row.get("DATA_IS_LIST"),
        "position_rows": position_objects,
        "LIVE_ACCOUNTING_RECONSTRUCTED": False,
        "EMPTY_DATA_IS_ZERO": False,
        "VALUES_INCLUDED": False,
        "SECRET_VALUES_INCLUDED": False,
    }
