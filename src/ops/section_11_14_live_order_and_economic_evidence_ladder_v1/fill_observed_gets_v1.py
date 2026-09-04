"""Minimum governed private GETs for §11.14 LIVE_FILL_OBSERVED.

Exactly two GETs on eea.okx.com:
1. GET /api/v5/trade/order?instId=<bound>&ordId=<bound>
2. GET /api/v5/trade/fills?instType=FUTURES&instId=<bound>&ordId=<bound>

Does not POST, cancel, amend, retry, or second-submit. Secrets are never
logged, printed, or persisted.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import parse_qs, urlencode, urlparse

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    ENDPOINT_ORDER_GET,
    ENDPOINT_TRADE_FILLS,
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
    LIVE_SUBMIT_ACK_OBSERVED,
    POST_ALLOWED,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.fill_observed_identity_v1 import (
    BOUND_INST_TYPE,
    BOUND_INSTID,
    BOUND_ORDID,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.reachability_private_get_v1 import (
    _header_presence_v1,
)

THIS_OWNER_GO = "PEAK_TRADE_OWNER_GO_SECTION_11_14_LIVE_FILL_OBSERVED_MAXIMUM_SAFE_LEVERAGE_V1"
EXPECTED_ORIGIN_MAIN_SHA = "fead386cc6746524301a01b7b7489bea0621e4f3"
FILL_GET_REST_HOST = REUSED_BINDING_REST_HOST
FILL_GET_REST_BASE = f"https://{FILL_GET_REST_HOST}"
FILL_GET_METHOD = "GET"
FILL_GET_MAX_REQUEST_COUNT = 2
FILL_GET_MAX_RETRIES = 0
FILL_GET_TIMEOUT_SECONDS = 10.0

ORDER_ROW_ALLOWLIST = frozenset(
    {
        "accFillSz",
        "avgPx",
        "cTime",
        "clOrdId",
        "fee",
        "feeCcy",
        "fillPx",
        "fillSz",
        "instId",
        "instType",
        "ordId",
        "ordType",
        "posSide",
        "px",
        "side",
        "state",
        "sz",
        "tdMode",
        "uTime",
    }
)
FILL_ROW_ALLOWLIST = frozenset(
    {
        "billId",
        "clOrdId",
        "execType",
        "fee",
        "feeCcy",
        "fillPx",
        "fillSz",
        "fillTime",
        "instId",
        "instType",
        "ordId",
        "posSide",
        "side",
        "subType",
        "tradeId",
        "ts",
    }
)


def bound_order_get_endpoint_v1() -> str:
    query = urlencode({"instId": BOUND_INSTID, "ordId": BOUND_ORDID})
    return f"{ENDPOINT_ORDER_GET}?{query}"


def bound_fills_get_endpoint_v1() -> str:
    query = urlencode(
        {
            "instType": BOUND_INST_TYPE,
            "instId": BOUND_INSTID,
            "ordId": BOUND_ORDID,
        }
    )
    return f"{ENDPOINT_TRADE_FILLS}?{query}"


def bind_fill_observed_gets_before_request_v1() -> dict[str, Any]:
    return {
        "WHY_GET_REQUIRED": (
            "LIVE_FILL_OBSERVED requires a current venue fill bound to the "
            "Peak_Trade Live submit identity. GET /api/v5/trade/fills scoped to "
            "the bound ordId/instId is the fill-row source. GET /api/v5/trade/order "
            "scoped to the same identity is supporting order-state context only."
        ),
        "REQUIRED_FACT": "CURRENT_VENUE_FILL_BOUND_TO_ACK_IDENTITY",
        "ENDPOINTS": [bound_order_get_endpoint_v1(), bound_fills_get_endpoint_v1()],
        "ENDPOINT_PATHS": [ENDPOINT_ORDER_GET, ENDPOINT_TRADE_FILLS],
        "METHOD": FILL_GET_METHOD,
        "EXPECTED_MUTATION": "NONE",
        "MAXIMUM_REQUEST_COUNT": FILL_GET_MAX_REQUEST_COUNT,
        "RETRY": False,
        "PUBLIC_GET": False,
        "PRIVATE_GET": True,
        "POST": False,
        "CANCEL": False,
        "AMEND": False,
        "BOUND_ORDID": BOUND_ORDID,
        "BOUND_INSTID": BOUND_INSTID,
        "LIVE_FEE_OBSERVED_PROMOTION": False,
        "LIVE_POSITION_RECONCILED_PROMOTION": False,
    }


def _utc_now_iso_v1() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _path_only_v1(endpoint: str) -> str:
    parsed = urlparse(endpoint if "://" in endpoint else f"{FILL_GET_REST_BASE}{endpoint}")
    return parsed.path or endpoint.split("?", 1)[0]


def _query_from_endpoint_v1(endpoint: str) -> dict[str, str]:
    parsed = urlparse(endpoint if "://" in endpoint else f"{FILL_GET_REST_BASE}{endpoint}")
    raw = parse_qs(parsed.query, keep_blank_values=True)
    return {key: values[0] if values else "" for key, values in raw.items()}


def _sanitize_row_v1(row: Mapping[str, Any], allowlist: frozenset[str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in dict(row).items():
        if str(key) not in allowlist:
            continue
        if isinstance(value, (str, int, float, bool)) or value is None:
            out[str(key)] = value
    return out


def _sanitize_payload_v1(
    payload: Mapping[str, Any] | None,
    allowlist: frozenset[str],
) -> dict[str, Any] | None:
    if payload is None:
        return None
    data = payload.get("data")
    rows = data if isinstance(data, list) else []
    return {
        "code": payload.get("code"),
        "msg": sanitize_okx_message_v1(str(payload.get("msg") or "")[:200]),
        "data": [_sanitize_row_v1(item, allowlist) for item in rows if isinstance(item, Mapping)],
        "ROW_FIELDS_REDACTED_TO_ALLOWLIST": True,
    }


def _body_utf8_exact_v1(body_bytes: bytes) -> str | None:
    if not body_bytes:
        return None
    try:
        return body_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return None


def execute_fill_observed_gets_v1(
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
    if LIVE_SUBMIT_ACK_OBSERVED is not True:
        raise Section1114OfflineSurfaceError("ACK_PREDECESSOR_FALSE")
    if POST_ALLOWED is True:
        raise Section1114OfflineSurfaceError("POST_MUST_REMAIN_FORBIDDEN")
    order_endpoint = bound_order_get_endpoint_v1()
    fills_endpoint = bound_fills_get_endpoint_v1()
    for endpoint in (order_endpoint, fills_endpoint):
        path = _path_only_v1(endpoint)
        if path not in GET_ENDPOINTS_PRIVATE:
            raise Section1114OfflineSurfaceError(f"ENDPOINT_NOT_PRIVATE_ALLOWLIST:{path}")
    binding = bind_fill_observed_gets_before_request_v1()
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
        rest_base=FILL_GET_REST_BASE,
        rest_host=FILL_GET_REST_HOST,
        transport=live_transport,
        max_request_count=FILL_GET_MAX_REQUEST_COUNT,
        max_retries=FILL_GET_MAX_RETRIES,
        timeout_seconds=FILL_GET_TIMEOUT_SECONDS,
    )
    planned = (
        ("ORDER_STATUS", ENDPOINT_ORDER_GET, order_endpoint, ORDER_ROW_ALLOWLIST),
        ("FILLS", ENDPOINT_TRADE_FILLS, fills_endpoint, FILL_ROW_ALLOWLIST),
    )
    observations: list[dict[str, Any]] = []
    raw_exchanges: list[dict[str, Any]] = []
    any_redirect = False
    any_error: str | None = None
    send_attempted = False
    try:
        for role, expected_path, endpoint, allowlist in planned:
            path = _path_only_v1(endpoint)
            if path != expected_path:
                raise Section1114OfflineSurfaceError("ENDPOINT_PATH_MISMATCH")
            query = _query_from_endpoint_v1(endpoint)
            if query.get("ordId") != BOUND_ORDID or query.get("instId") != BOUND_INSTID:
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
                    url = f"{FILL_GET_REST_BASE}{endpoint}"
                    parsed = urlparse(url)
                    if parsed.hostname != FILL_GET_REST_HOST:
                        raise Section1114OfflineSurfaceError("HOST_MISMATCH")
                    if parsed.path != expected_path:
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
            data_rows = data if isinstance(data, list) else []
            if redirect_followed:
                any_redirect = True
            sanitized = _sanitize_payload_v1(payload, allowlist)
            object_rows = [item for item in data_rows if isinstance(item, Mapping)]
            observations.append(
                {
                    "GET_ROLE": role,
                    "ENDPOINT": endpoint,
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
                    "DATA_ROW_COUNT": len(data_rows) if isinstance(data, list) else None,
                    "REDIRECT_FOLLOWED": redirect_followed,
                    "ELAPSED_SECONDS": elapsed_seconds,
                    "BODY_SHA256": hashlib.sha256(body_bytes).hexdigest() if body_bytes else None,
                    "BODY_BYTE_LEN": len(body_bytes),
                    "HEADER_PRESENCE": header_presence,
                    "SANITIZED_PAYLOAD": sanitized,
                    "OBJECT_ROWS": [_sanitize_row_v1(item, allowlist) for item in object_rows],
                    "VALUES_INCLUDED": False,
                }
            )
            raw_exchanges.append(
                {
                    "DOCUMENT_CLASS": "SECTION_11_14_LIVE_FILL_OBSERVED_RAW_EXCHANGE_V1",
                    "DOCUMENT_ROLE": "FORENSIC_RAW_NOT_CANONICAL_NOT_ADJUDICATION",
                    "AUTHORITY": "NONE",
                    "THIS_ARTIFACT_IS_NOT_CANONICAL": True,
                    "GET_ROLE": role,
                    "METHOD": "GET",
                    "HOST": FILL_GET_REST_HOST,
                    "ENDPOINT": endpoint,
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
        if client.counters.request_count > FILL_GET_MAX_REQUEST_COUNT:
            raise Section1114OfflineSurfaceError("MAX_REQUEST_COUNT_EXCEEDED")
        if "POST" in client.counters.methods_used:
            raise Section1114OfflineSurfaceError("POST_INVOKED_BY_FILL_OBSERVATION")
        if int(client.counters.write_request_count or 0) != 0:
            raise Section1114OfflineSurfaceError("WRITE_REQUEST_INVOKED_BY_FILL_OBSERVATION")
    finally:
        if handle is not None:
            release_live_canary_ephemeral_material_v1(handle)
    by_role = {str(row["GET_ROLE"]): row for row in observations}
    order_row = by_role.get("ORDER_STATUS") or {}
    fills_row = by_role.get("FILLS") or {}
    order_objects = list(order_row.get("OBJECT_ROWS") or [])
    fills_objects = list(fills_row.get("OBJECT_ROWS") or [])
    return {
        "GET_BINDING": binding,
        "OWNER_GO": THIS_OWNER_GO,
        "METHOD": "GET",
        "ENDPOINTS": [order_endpoint, fills_endpoint],
        "HOST": FILL_GET_REST_HOST,
        "REQUEST_TIME_UTC": observations[0]["REQUEST_TIME_UTC"] if observations else None,
        "RESPONSE_TIME_UTC": observations[-1]["RESPONSE_TIME_UTC"] if observations else None,
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
        "NO_POST": True,
        "source_kind": "GOVERNED_CURRENT_PRIVATE_GET",
        "FILLS_GET_PERFORMED": bool(fills_row),
        "ORDER_GET_PERFORMED": bool(order_row),
        "fills_http_status": fills_row.get("HTTP_STATUS"),
        "fills_okx_code": fills_row.get("OKX_CODE"),
        "fills_json_parse_ok": fills_row.get("PARSED_OK"),
        "fills_redirect_followed": bool(fills_row.get("REDIRECT_FOLLOWED")),
        "fills_method": "GET",
        "fills_rows": fills_objects,
        "order_row": order_objects[0] if order_objects else {},
        "order_rows": order_objects,
        "LIVE_FEE_OBSERVED": False,
        "LIVE_POSITION_RECONCILED": False,
        "VALUES_INCLUDED": False,
        "SECRET_VALUES_INCLUDED": False,
    }
