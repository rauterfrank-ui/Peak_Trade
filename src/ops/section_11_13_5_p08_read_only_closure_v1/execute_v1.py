"""Execute distinct identifier-recovery private GETs for P08 read-only closure.

Constructs LiveCanaryHttpClientV1 itself. Reuses the existing canary GET
signer, live-canary SecretRef, positions query grammar (posId path only),
Category-C algo-pending query builder, and P08 CASE_A..F classifier for the
canonical positions elicitation. Order/fill/algo channels remain independent
non-canonical identifier-recovery surfaces. No POST, transfer, order submit,
funding GET, config GET, whitelist mutation, unfiltered positions GET, or
capital movement. Empty data is never promoted to zero.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import parse_qs, urlparse

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
    default_local_monotonic_ms_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.prerequisite_08_fresh_position_observation_v1 import (
    adjudicate_prerequisite_08_window_v1,
    evaluate_freshness_at_adjudication_v1,
    sanitize_positions_payload_v1,
)
from src.ops.section_11_13_5_p08_distinct_first_party_evidence_v1.classify_v1 import (
    merge_independently_proven_pos_ids_v1,
)
from src.ops.section_11_13_5_p08_position_observation_v1.execute_v1 import (
    classify_http_okx_result_v1,
    classify_position_observation_v1,
)
from src.ops.section_11_13_5_p08_read_only_closure_v1.census_v1 import census_payload_v1
from src.ops.section_11_13_5_p08_read_only_closure_v1.classify_v1 import (
    classify_identifier_channel_v1,
    synthesize_read_only_closure_v1,
)
from src.ops.section_11_13_5_p08_read_only_closure_v1.constants_v1 import (
    ALGO_ORD_TYPE_BY_ROLE,
    AUTHORIZED_ENDPOINT_PATHS,
    AUTHORIZED_HOST,
    CASE_C_EMPTY_DATA_NOT_ZERO,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT_SECONDS,
    EMPTY_DATA_IS_ZERO,
    ENDPOINT_ACCOUNT_POSITIONS,
    ENDPOINT_ORDERS_ALGO_PENDING,
    ENDPOINT_ORDERS_HISTORY,
    ENDPOINT_ORDERS_PENDING,
    ENDPOINT_TRADE_FILLS,
    EXPECTED_ORIGIN_MAIN_SHA,
    FORBIDDEN_ENDPOINTS,
    FRESHNESS_POLICY,
    GET_PURPOSE_ALGO_PENDING,
    GET_PURPOSE_FILLS,
    GET_PURPOSE_ORDERS_HISTORY,
    GET_PURPOSE_ORDERS_PENDING,
    GET_PURPOSE_POSID_POSITIONS,
    GET_ROLE_FILLS,
    GET_ROLE_ORDERS_HISTORY,
    GET_ROLE_ORDERS_PENDING,
    GET_ROLE_POSID_POSITIONS,
    MAX_HTTP_EXCHANGE_COUNT,
    MAX_NETWORK_REQUEST_COUNT,
    OWNER_GO,
    P08_CANONICAL_DEFINITION_REUSED,
    POSID_GET_REQUIRES_INDEPENDENT_PROOF,
    RESULT_CLASS_200_OKX_0,
    REUSED_CREDENTIAL_CLASS,
    REUSED_REST_BASE,
    REUSED_REST_HOST,
    REUSED_SECRETREF_URI,
    TARGET_INSTRUMENT_ID,
    THIS_SLICE,
)
from src.ops.section_11_13_5_p08_read_only_closure_v1.persist_claims_v1 import CLAIMS
from src.ops.section_11_13_5_p08_read_only_closure_v1.persist_v1 import (
    persist_p08_read_only_closure_v1,
)
from src.ops.section_11_13_5_p08_read_only_closure_v1.query_grammar_v1 import (
    build_proven_posid_positions_query_v1,
    build_target_algo_pending_path_v1,
    build_target_fills_query_v1,
    build_target_orders_history_query_v1,
    build_target_orders_pending_query_v1,
)
from src.ops.section_11_13_5_post_z2ds_private_get_current_50110_egress_capture_v1.execute_v1 import (
    sanitize_okx_message_v1,
)

_ID_ROW_ALLOWLIST = frozenset(
    {
        "algoId",
        "avgPx",
        "cTime",
        "clOrdId",
        "fillPx",
        "fillSz",
        "fillTime",
        "instId",
        "instType",
        "ordId",
        "ordType",
        "pnl",
        "posSide",
        "posId",
        "px",
        "reduceOnly",
        "side",
        "state",
        "sz",
        "tdMode",
        "tradeId",
        "uTime",
    }
)


class P08ReadOnlyClosureError(RuntimeError):
    """Fail-closed P08 read-only closure GET-package violation."""


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


def _query_from_endpoint_v1(endpoint: str) -> dict[str, str]:
    parsed = urlparse(endpoint if "://" in endpoint else f"https://{AUTHORIZED_HOST}{endpoint}")
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


def _sanitize_identifier_payload_v1(payload: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if payload is None:
        return None
    data = payload.get("data")
    rows = data if isinstance(data, list) else []
    redacted_rows = [
        _sanitize_row_v1(item, _ID_ROW_ALLOWLIST) for item in rows if isinstance(item, Mapping)
    ]
    return {
        "code": payload.get("code"),
        "msg": sanitize_okx_message_v1(str(payload.get("msg") or "")[:200]),
        "data": redacted_rows,
        "ROW_FIELDS_REDACTED_TO_ALLOWLIST": True,
    }


def _body_utf8_exact_v1(body_bytes: bytes) -> str | None:
    if not body_bytes:
        return None
    try:
        return body_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return None


def execute_p08_read_only_closure_gets_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    evidence_root: Path,
    vault_file: Path | None = None,
    transport: LiveCanaryTransportV1 | None = None,
) -> dict[str, Any]:
    if str(owner_go or "").strip() != OWNER_GO:
        raise P08ReadOnlyClosureError("OWNER_GO_MISMATCH")
    if str(origin_main_sha or "").strip() != EXPECTED_ORIGIN_MAIN_SHA:
        raise P08ReadOnlyClosureError("ORIGIN_MAIN_SHA_MISMATCH")
    if EMPTY_DATA_IS_ZERO:
        raise P08ReadOnlyClosureError("EMPTY_DATA_MUST_NOT_BE_PROMOTED_TO_ZERO")
    if not POSID_GET_REQUIRES_INDEPENDENT_PROOF:
        raise P08ReadOnlyClosureError("POSID_GET_MUST_REQUIRE_INDEPENDENT_PROOF")
    productive = transport is None
    if productive:
        if vault_file is None:
            raise P08ReadOnlyClosureError("VAULT_FILE_REQUIRED")
        backend = build_file_secretref_vault_backend_v1(vault_file=Path(vault_file))
        handle = resolve_and_load_live_canary_secretref_ephemeral_v1(
            secret_reference=REUSED_SECRETREF_URI,
            vault_backend=backend,
            credential_class=REUSED_CREDENTIAL_CLASS,
        )
        live_transport: LiveCanaryTransportV1 = UrllibLiveCanaryTransportV1(wire_send_enabled=True)
    else:
        handle = None
        live_transport = transport
    if isinstance(live_transport, UrllibLiveCanaryTransportV1) and not bool(
        getattr(live_transport, "wire_send_enabled", False)
    ):
        raise P08ReadOnlyClosureError("PRODUCTIVE_WIRE_DISABLED")
    client = LiveCanaryHttpClientV1(
        rest_base=REUSED_REST_BASE,
        rest_host=REUSED_REST_HOST,
        transport=live_transport,
        max_request_count=MAX_NETWORK_REQUEST_COUNT,
        max_retries=DEFAULT_MAX_RETRIES,
        timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
    )
    owner_go_consumed = False
    exchanges: list[dict[str, Any]] = []
    raw_exchanges: list[dict[str, Any]] = []
    identifier_channels: list[dict[str, Any]] = []
    first_received_ms: int | None = None
    last_received_ms: int | None = None
    positions_record: dict[str, Any] | None = None

    def _issue(*, role: str, purpose: str, endpoint: str, expected_path: str) -> dict[str, Any]:
        nonlocal owner_go_consumed, first_received_ms, last_received_ms
        path = _path_only_v1(endpoint)
        if path != expected_path:
            raise P08ReadOnlyClosureError("ENDPOINT_PATH_MISMATCH")
        if path not in AUTHORIZED_ENDPOINT_PATHS:
            raise P08ReadOnlyClosureError("ENDPOINT_NOT_AUTHORIZED")
        if path in FORBIDDEN_ENDPOINTS:
            raise P08ReadOnlyClosureError("FORBIDDEN_ENDPOINT")
        query = _query_from_endpoint_v1(endpoint)
        if path == ENDPOINT_ACCOUNT_POSITIONS:
            if "posId" not in query:
                raise P08ReadOnlyClosureError("POSITIONS_GET_REQUIRES_PROVEN_POSID")
            if "instId" in query or "instType" in query:
                raise P08ReadOnlyClosureError("EQUIVALENT_POSITIONS_PROBE_FORBIDDEN")
        parsed = urlparse(f"{REUSED_REST_BASE}{endpoint}")
        if parsed.path != expected_path:
            raise P08ReadOnlyClosureError("SIGNED_REQUEST_TARGET_MISMATCH")
        if parsed.hostname != AUTHORIZED_HOST:
            raise P08ReadOnlyClosureError("HOST_MISMATCH")
        if _exchange_count_v1(live_transport) >= MAX_HTTP_EXCHANGE_COUNT:
            raise P08ReadOnlyClosureError("MAX_HTTP_EXCHANGE_COUNT_EXCEEDED")
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
                raise P08ReadOnlyClosureError("NON_GET_RESPONSE")
            if redirect_followed:
                raise P08ReadOnlyClosureError("REDIRECT_FOLLOWED")
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
        result_class = classify_http_okx_result_v1(
            http_status=http_status,
            venue_code=venue_code,
            get_error=get_error,
        )
        body_sha256 = hashlib.sha256(body_bytes).hexdigest() if body_bytes else None
        record: dict[str, Any] = {
            "GET_INDEX": len(exchanges) + 1,
            "GET_ROLE": role,
            "GET_PURPOSE": purpose,
            "ENDPOINT": endpoint,
            "ENDPOINT_PATH": path,
            "QUERY_PARAMETERS": query,
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
            "RESULT_CLASS": result_class,
            "REDIRECT_FOLLOWED": redirect_followed,
            "REDIRECT_STATUS": redirect_status,
            "ELAPSED_SECONDS": elapsed_seconds,
            "RESPONSE_HEADERS_SAFE": dict(response_headers_safe)
            if response_headers_safe
            else safe_response_headers_v1({}),
            "AUTH_HEADER_SENT": bool(header_presence.get("AUTH_KEY_HEADER_PRESENT")),
            "HEADER_PRESENCE": header_presence,
            "LOCAL_RESPONSE_RECEIVED_AT": received_ms,
            "EMPTY_DATA_IS_ZERO": False,
            "ABSENT_TARGET_ROW_IS_ZERO": False,
            "ORDERS_EMPTY_IS_NEVER_HELD": False,
            "ORDERS_EMPTY_IS_CURRENT_ZERO": False,
            "FILLS_EMPTY_IS_NEVER_HELD": False,
            "FILLS_EMPTY_IS_CURRENT_ZERO": False,
        }
        if path == ENDPOINT_ACCOUNT_POSITIONS:
            window = None
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
                raise P08ReadOnlyClosureError("EMPTY_DATA_MUST_NOT_BE_PROMOTED_TO_ZERO")
            data = (payload or {}).get("data") if payload else None
            record["DATA_ROW_COUNT"] = len(data) if isinstance(data, list) else None
            record["REDACTED_PAYLOAD"] = sanitize_positions_payload_v1(payload)
            record["TARGET_POSITION_QTY_NUMERIC"] = (window or {}).get(
                "TARGET_POSITION_QTY_NUMERIC"
            )
            record["WINDOW"] = window
            record["CHANNEL"] = "ACCOUNT_POSITIONS_POSID"
            record["CHANNEL_IS_CANONICAL_P08_AUTHORITY"] = True
            record.update(observation)
        else:
            classified = classify_identifier_channel_v1(
                channel=role,
                result_class=result_class,
                payload=payload,
                instrument_id=TARGET_INSTRUMENT_ID,
            )
            data = (payload or {}).get("data") if payload else None
            record["DATA_ROW_COUNT"] = len(data) if isinstance(data, list) else None
            record["REDACTED_PAYLOAD"] = _sanitize_identifier_payload_v1(payload)
            record.update(classified)
            identifier_channels.append(classified)
        raw = {
            "DOCUMENT_CLASS": "P08_READ_ONLY_CLOSURE_RAW_EXCHANGE_V3",
            "DOCUMENT_ROLE": "FORENSIC_RAW_NOT_CANONICAL_NOT_ADJUDICATION",
            "AUTHORITY": "NONE",
            "THIS_ARTIFACT_IS_NOT_CANONICAL": True,
            "GET_INDEX": record["GET_INDEX"],
            "GET_ROLE": role,
            "GET_PURPOSE": purpose,
            "METHOD": "GET",
            "HOST": REUSED_REST_HOST,
            "ENDPOINT": endpoint,
            "ENDPOINT_PATH": path,
            "QUERY_PARAMETERS": query,
            "REQUEST_TIME_UTC": request_time,
            "RESPONSE_TIME_UTC": response_time,
            "HTTP_STATUS": http_status,
            "BODY_BYTES": len(body_bytes),
            "BODY_SHA256": body_sha256,
            "BODY_UTF8_EXACT": _body_utf8_exact_v1(body_bytes),
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
        exchanges.append(record)
        raw_exchanges.append(raw)
        return record

    try:
        pending = build_target_orders_pending_query_v1()
        _issue(
            role=GET_ROLE_ORDERS_PENDING,
            purpose=GET_PURPOSE_ORDERS_PENDING,
            endpoint=pending.path_with_query(),
            expected_path=ENDPOINT_ORDERS_PENDING,
        )
        history = build_target_orders_history_query_v1()
        _issue(
            role=GET_ROLE_ORDERS_HISTORY,
            purpose=GET_PURPOSE_ORDERS_HISTORY,
            endpoint=history.path_with_query(),
            expected_path=ENDPOINT_ORDERS_HISTORY,
        )
        for role, ord_type in ALGO_ORD_TYPE_BY_ROLE:
            algo_path = build_target_algo_pending_path_v1(ord_type=ord_type)
            _issue(
                role=role,
                purpose=GET_PURPOSE_ALGO_PENDING,
                endpoint=algo_path,
                expected_path=ENDPOINT_ORDERS_ALGO_PENDING,
            )
        fills = build_target_fills_query_v1()
        _issue(
            role=GET_ROLE_FILLS,
            purpose=GET_PURPOSE_FILLS,
            endpoint=fills.path_with_query(),
            expected_path=ENDPOINT_TRADE_FILLS,
        )
        merged_ids = merge_independently_proven_pos_ids_v1(
            *[tuple(item.get("TARGET_POS_ID_CANDIDATES") or []) for item in identifier_channels]
        )
        if len(merged_ids) == 1:
            posid_query = build_proven_posid_positions_query_v1(pos_id=merged_ids[0])
            positions_record = _issue(
                role=GET_ROLE_POSID_POSITIONS,
                purpose=GET_PURPOSE_POSID_POSITIONS,
                endpoint=posid_query.path_with_query(),
                expected_path=ENDPOINT_ACCOUNT_POSITIONS,
            )
        synthesis = synthesize_read_only_closure_v1(
            identifier_channels=tuple(identifier_channels),
            positions=positions_record,
        )
        adjudication_ms = default_local_monotonic_ms_v1()
        freshness = evaluate_freshness_at_adjudication_v1(
            response_received_monotonic_ms=last_received_ms,
            adjudication_monotonic_ms=adjudication_ms,
        )
        http_exchange_count = _exchange_count_v1(live_transport)
        if http_exchange_count > MAX_HTTP_EXCHANGE_COUNT:
            raise P08ReadOnlyClosureError("HTTP_EXCHANGE_COUNT_EXCEEDED")
        if client.counters.write_request_count != 0 or client.counters.order_request_count != 0:
            raise P08ReadOnlyClosureError("WRITE_OR_ORDER_COUNTER_NONZERO")
        pack_name = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        pack = Path(evidence_root) / pack_name
        census = census_payload_v1()
        snapshot = {
            "DOCUMENT_CLASS": "P08_READ_ONLY_CLOSURE_GET_PACKAGE_V3",
            "DOCUMENT_ROLE": "GET_ONLY_FRESH_EVIDENCE_NON_SSOT",
            "AUTHORITY": "NONE",
            "ATLAS_AUTHORITY": "NONE",
            "LANDSCAPE_AUTHORITY": "NONE",
            "BOUND_ORIGIN_MAIN_SHA": origin_main_sha,
            "OWNER_GO": OWNER_GO,
            "THIS_SLICE": THIS_SLICE,
            "TARGET_INSTRUMENT_ID": TARGET_INSTRUMENT_ID,
            "AUTH_PATH": {
                "HTTP_CLIENT": "LiveCanaryHttpClientV1",
                "TRANSPORT": "UrllibLiveCanaryTransportV1",
                "SIGNER": "build_okx_live_canary_auth_headers_v1",
                "SECRETREF_URI": REUSED_SECRETREF_URI,
                "CREDENTIAL_CLASS": REUSED_CREDENTIAL_CLASS,
            },
            "GET_ROLES_PERFORMED": [item["GET_ROLE"] for item in exchanges],
            "COUNTERS": dict(client.counters.to_dict()),
            "EXCHANGES": exchanges,
            "EQUIVALENT_ACCOUNT_POSITIONS_EMPTY_PROBE_REPEATED": False,
            "WRITE_REQUEST_COUNT": 0,
            "POST_COUNT": 0,
            "SECRET_VALUES_INCLUDED": False,
        }
        adjudication = {
            "DOCUMENT_CLASS": "P08_READ_ONLY_CLOSURE_WINDOW_ADJUDICATION_V3",
            "DOCUMENT_ROLE": "INTERPRETATION_NOT_RAW_EVIDENCE_NOT_SSOT",
            "AUTHORITY": "NONE",
            "BOUND_ORIGIN_MAIN_SHA": origin_main_sha,
            "OWNER_GO": OWNER_GO,
            "P08_CANONICAL_DEFINITION": P08_CANONICAL_DEFINITION_REUSED,
            "CHANNEL_ADJUDICATIONS": {
                "IDENTIFIER_RECOVERY": identifier_channels,
                "POSID_POSITIONS": [positions_record] if positions_record else [],
            },
            "GET_REQUEST_COUNT": int(client.counters.get_request_count),
            "HTTP_EXCHANGE_COUNT": http_exchange_count,
            "FIRST_RESPONSE_RECEIVED_AT": first_received_ms,
            "LOCAL_RESPONSE_RECEIVED_AT": last_received_ms,
            "FRESHNESS_POLICY": FRESHNESS_POLICY,
            "FRESHNESS_STATUS": freshness.get("FRESHNESS_STATUS"),
            "EMPTY_DATA_IS_ZERO": False,
            "G_POSMODE_SUBMIT_BODY_PROVEN": False,
            "HYPOTHESIS_IS_NOT_PROOF": True,
            "BYTE_IDENTICAL_EMPTY_SHA_IS_NOT_CURRENT_08_PROOF": True,
            "LIVE_TESTNET_CANARY": False,
            "POST_PERFORMED": False,
            "P09_WORK_PERFORMED": False,
            **synthesis,
        }
        summary = {
            "DOCUMENT_CLASS": "P08_READ_ONLY_CLOSURE_GET_PACKAGE_V3",
            "DOCUMENT_ROLE": "DERIVED_NON_SSOT",
            "ATLAS_AUTHORITY": "NONE",
            "LANDSCAPE_AUTHORITY": "NONE",
            "BOUND_ORIGIN_MAIN_SHA": origin_main_sha,
            "OWNER_GO": OWNER_GO,
            "OWNER_GO_CONSUMED": owner_go_consumed,
            "THIS_SLICE": THIS_SLICE,
            "HOST": AUTHORIZED_HOST,
            "METHOD": "GET",
            "GET_REQUEST_COUNT": int(client.counters.get_request_count),
            "HTTP_EXCHANGE_COUNT": http_exchange_count,
            "WRITE_REQUEST_COUNT": 0,
            "POST_COUNT": 0,
            "RETRY_COUNT": 0,
            "P08_READ_ONLY_CANDIDATE_COUNT": census["P08_READ_ONLY_CANDIDATE_COUNT"],
            "P08_DISTINCT_UNCONSUMED_CANDIDATE_COUNT": census[
                "P08_DISTINCT_UNCONSUMED_CANDIDATE_COUNT"
            ],
            "P08_READ_ONLY_REQUEST_COUNT": int(client.counters.get_request_count),
            "GET_ROLES_PERFORMED": [item["GET_ROLE"] for item in exchanges],
            "HTTP_STATUS": exchanges[-1]["HTTP_STATUS"] if exchanges else None,
            "OKX_CODE": exchanges[-1]["OKX_CODE"] if exchanges else None,
            "RESULT_CLASS": exchanges[-1]["RESULT_CLASS"] if exchanges else None,
            "POSID_POSITIONS_GET_PERFORMED": positions_record is not None,
            "EQUIVALENT_ACCOUNT_POSITIONS_EMPTY_PROBE_REPEATED": False,
            "P08_CLOSED": synthesis["P08_CLOSED"],
            "P08_VERDICT": synthesis["P08_VERDICT"],
            "P08_READ_ONLY_CLOSURE_RESULT": synthesis["P08_READ_ONLY_CLOSURE_RESULT"],
            "POSITION_OBSERVATION_CLASS": synthesis["POSITION_OBSERVATION_CLASS"],
            "TARGET_POSITION_ZERO_PROVEN": synthesis["TARGET_POSITION_ZERO_PROVEN"],
            "TARGET_POSITION_NONZERO_PROVEN": synthesis["TARGET_POSITION_NONZERO_PROVEN"],
            "G_POSMODE_SUBMIT_BODY_PROVEN": False,
            "TARGET_POS_ID_PROVEN": synthesis["TARGET_POS_ID_PROVEN"],
            "TARGET_POS_ID": synthesis["TARGET_POS_ID"],
            "NEXT_AUTHORITY_BOUNDARY": synthesis["NEXT_AUTHORITY_BOUNDARY"],
            "HISTORICAL_OR_INDIRECT_PROMOTED_TO_CURRENT_STATE": synthesis[
                "HISTORICAL_OR_INDIRECT_PROMOTED_TO_CURRENT_STATE"
            ],
            "LIVE_EXECUTION": False,
            "CANARY_EXECUTION": False,
            "CORE_CHANGED": False,
            "MERGE_AUTHORIZED": False,
            "NEW_AUTHORITY_CREATED": False,
        }
        verified = persist_p08_read_only_closure_v1(
            pack=pack,
            origin_main_sha=origin_main_sha,
            snapshot=snapshot,
            adjudication=adjudication,
            summary=summary,
            census=census,
            raw_exchanges=tuple(raw_exchanges),
        )
        return {
            "summary": summary,
            "adjudication": adjudication,
            "EVIDENCE_PACK": str(pack),
            "MANIFEST_VERIFY_RC": verified.get("MANIFEST_VERIFY_RC"),
            "CLAIMS": CLAIMS,
        }
    finally:
        if productive and handle is not None:
            release_live_canary_ephemeral_material_v1(handle)
