"""Execute distinct first-party private GETs to discriminate P08.

Constructs LiveCanaryHttpClientV1 itself. Reuses the existing canary GET
signer, live-canary SecretRef, positions query grammar (posId path only),
and P08 CASE_A..F classifier for the canonical positions elicitation.
History and risk remain independent non-canonical channels. No POST,
transfer, order, funding GET, config GET, whitelist mutation, unfiltered
positions GET, or capital movement. Empty data is never promoted to zero.
Historical P08/Z2CH envelopes remain historical.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
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
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.prerequisite_08_fresh_position_observation_v1 import (
    adjudicate_prerequisite_08_window_v1,
    evaluate_freshness_at_adjudication_v1,
    sanitize_positions_payload_v1,
)
from src.ops.section_11_13_5_p08_distinct_first_party_evidence_v1.classify_v1 import (
    classify_history_channel_v1,
    classify_risk_channel_v1,
    merge_independently_proven_pos_ids_v1,
    synthesize_package_v1,
)
from src.ops.section_11_13_5_p08_distinct_first_party_evidence_v1.constants_v1 import (
    AUTHORIZED_ENDPOINT_PATHS,
    AUTHORIZED_HOST,
    CASE_C_EMPTY_DATA_NOT_ZERO,
    CASE_E_HTTP_OR_OKX_ERROR,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT_SECONDS,
    EMPTY_DATA_IS_ZERO,
    ENDPOINT_ACCOUNT_POSITION_RISK,
    ENDPOINT_ACCOUNT_POSITIONS_HISTORY,
    ENDPOINT_ACCOUNT_POSITIONS_REUSED,
    EXPECTED_ORIGIN_MAIN_SHA,
    FORBIDDEN_ENDPOINTS,
    FRESHNESS_POLICY,
    GET_PURPOSE_ACCOUNT_POSITION_RISK,
    GET_PURPOSE_HISTORY_PAGINATION,
    GET_PURPOSE_POSID_POSITIONS,
    GET_PURPOSE_TARGET_HISTORY,
    GET_PURPOSE_TYPED_HISTORY,
    GET_ROLE_ACCOUNT_POSITION_RISK,
    GET_ROLE_HISTORY_PAGINATION,
    GET_ROLE_POSID_POSITIONS,
    GET_ROLE_TARGET_HISTORY,
    GET_ROLE_TYPED_HISTORY,
    HISTORICAL_EMPTY_ENVELOPE_SHA256,
    HISTORICAL_P08_EMPTY_DATA_EVIDENCE_PACK,
    HISTORICAL_P08_POSITION_OBSERVATION_PACK,
    HISTORY_CLASS_EMPTY,
    HISTORY_CLASS_HTTP_OR_OKX_ERROR,
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
    REUSED_VENUE,
    TARGET_INST_TYPE,
    TARGET_INSTRUMENT_ID,
    THIS_SLICE,
)
from src.ops.section_11_13_5_p08_distinct_first_party_evidence_v1.persist_claims_v1 import (
    CLAIMS,
)
from src.ops.section_11_13_5_p08_distinct_first_party_evidence_v1.persist_v1 import (
    persist_p08_distinct_first_party_evidence_v1,
)
from src.ops.section_11_13_5_p08_distinct_first_party_evidence_v1.query_grammar_v1 import (
    build_account_position_risk_query_v1,
    build_proven_posid_positions_query_v1,
    build_target_positions_history_query_v1,
    build_typed_positions_history_query_v1,
)
from src.ops.section_11_13_5_p08_position_observation_v1.execute_v1 import (
    classify_http_okx_result_v1,
    classify_position_observation_v1,
    secretref_identity_without_values_v1,
)
from src.ops.section_11_13_5_post_z2ds_private_get_current_50110_egress_capture_v1.execute_v1 import (
    sanitize_okx_message_v1,
)

_HISTORY_ROW_ALLOWLIST = frozenset(
    {
        "cTime",
        "closeAvgPx",
        "closeTotalPos",
        "direction",
        "instId",
        "instType",
        "lever",
        "mgnMode",
        "openAvgPx",
        "pnl",
        "pnlRatio",
        "posId",
        "posSide",
        "type",
        "uTime",
        "uly",
    }
)
_RISK_ROW_ALLOWLIST = frozenset(
    {
        "avgPx",
        "ccy",
        "imr",
        "instId",
        "instType",
        "lever",
        "liqPx",
        "margin",
        "markPx",
        "mgnMode",
        "mmr",
        "notionalUsd",
        "pos",
        "posCcy",
        "posId",
        "posSide",
        "upl",
        "uplRatio",
    }
)


class P08DistinctFirstPartyEvidenceError(RuntimeError):
    """Fail-closed P08 distinct first-party GET-package violation."""


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


def _sanitize_row_v1(row: Mapping[str, Any], allowlist: frozenset[str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in dict(row).items():
        name = str(key)
        lowered = name.lower()
        if any(marker in lowered for marker in ("uid", "api_key", "secret", "passphrase", "token")):
            out[name] = "<REDACTED>"
            continue
        if name not in allowlist:
            continue
        out[name] = value
    return out


def _sanitize_history_payload_v1(payload: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if payload is None:
        return None
    data = payload.get("data")
    if isinstance(data, list):
        rows: list[Any] = []
        for item in data:
            if isinstance(item, Mapping):
                rows.append(_sanitize_row_v1(item, _HISTORY_ROW_ALLOWLIST))
            else:
                rows.append("<NON_OBJECT_ROW>")
        sanitized: Any = rows
    else:
        sanitized = data
    return {"code": payload.get("code"), "data": sanitized, "msg": payload.get("msg")}


def _sanitize_risk_payload_v1(payload: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if payload is None:
        return None
    data = payload.get("data")
    sanitized_data: Any
    if isinstance(data, list):
        envelopes: list[Any] = []
        for item in data:
            if not isinstance(item, Mapping):
                envelopes.append("<NON_OBJECT_ROW>")
                continue
            pos_data = item.get("posData")
            rows: list[Any] = []
            if isinstance(pos_data, list):
                for pos_item in pos_data:
                    if isinstance(pos_item, Mapping):
                        rows.append(_sanitize_row_v1(pos_item, _RISK_ROW_ALLOWLIST))
                    else:
                        rows.append("<NON_OBJECT_ROW>")
            envelopes.append({"adjEq": item.get("adjEq"), "posData": rows})
        sanitized_data = envelopes
    else:
        sanitized_data = data
    return {"code": payload.get("code"), "data": sanitized_data, "msg": payload.get("msg")}


def _assert_gets_zero_writes(
    client: LiveCanaryHttpClientV1,
    *,
    expected_get_count: int,
) -> dict[str, Any]:
    counters = client.counters.to_dict()
    get_count = int(counters.get("GET_REQUEST_COUNT", 0) or 0)
    if get_count != expected_get_count:
        raise P08DistinctFirstPartyEvidenceError("GET_COUNT_MISMATCH")
    if get_count < 1 or get_count > MAX_NETWORK_REQUEST_COUNT:
        raise P08DistinctFirstPartyEvidenceError("GET_COUNT_OUT_OF_BOUNDS")
    if int(counters.get("REQUEST_COUNT", 0) or 0) != get_count:
        raise P08DistinctFirstPartyEvidenceError("REQUEST_COUNT_MISMATCH")
    if int(counters.get("WRITE_REQUEST_COUNT", 0) or 0) != 0:
        raise P08DistinctFirstPartyEvidenceError("WRITE_REQUEST_DETECTED")
    if int(counters.get("TRANSFER_REQUEST_COUNT", 0) or 0) != 0:
        raise P08DistinctFirstPartyEvidenceError("TRANSFER_REQUEST_DETECTED")
    if int(counters.get("ORDER_REQUEST_COUNT", 0) or 0) != 0:
        raise P08DistinctFirstPartyEvidenceError("ORDER_REQUEST_DETECTED")
    if int(counters.get("ENTRY_SUBMIT_COUNT", 0) or 0) != 0:
        raise P08DistinctFirstPartyEvidenceError("ENTRY_SUBMIT_DETECTED")
    if int(counters.get("FLATTEN_SUBMIT_COUNT", 0) or 0) != 0:
        raise P08DistinctFirstPartyEvidenceError("FLATTEN_SUBMIT_DETECTED")
    if list(client.counters.methods_used) != ["GET"] * get_count:
        raise P08DistinctFirstPartyEvidenceError("NON_GET_METHOD_DETECTED")
    for used in client.counters.endpoints_used:
        path = _path_only_v1(str(used))
        if path not in AUTHORIZED_ENDPOINT_PATHS:
            raise P08DistinctFirstPartyEvidenceError("ENDPOINT_SET_MISMATCH")
        if path in FORBIDDEN_ENDPOINTS:
            raise P08DistinctFirstPartyEvidenceError("MUTATION_ENDPOINT_FORBIDDEN")
    return counters


def _body_utf8_exact_v1(body_bytes: bytes) -> str | None:
    if not body_bytes:
        return None
    try:
        return body_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return None


def execute_p08_distinct_first_party_evidence_gets_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    evidence_root: Path,
    vault_file: Path | str | None = None,
    transport: LiveCanaryTransportV1 | None = None,
) -> dict[str, Any]:
    """Perform distinct private GETs and persist evidence."""
    owned = str(owner_go or "").strip()
    if owned != OWNER_GO:
        raise P08DistinctFirstPartyEvidenceError("OWNER_GO_MISMATCH")
    bound_sha = str(origin_main_sha or "").strip()
    if bound_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise P08DistinctFirstPartyEvidenceError("ORIGIN_MAIN_SHA_MISMATCH")
    if REUSED_REST_HOST != AUTHORIZED_HOST:
        raise P08DistinctFirstPartyEvidenceError("HOST_MISMATCH")
    if EMPTY_DATA_IS_ZERO:
        raise P08DistinctFirstPartyEvidenceError("EMPTY_DATA_MUST_NOT_BE_PROMOTED_TO_ZERO")
    if not POSID_GET_REQUIRES_INDEPENDENT_PROOF:
        raise P08DistinctFirstPartyEvidenceError("POSID_MUST_REQUIRE_INDEPENDENT_PROOF")

    target_history_query = build_target_positions_history_query_v1()
    typed_history_query = build_typed_positions_history_query_v1()
    risk_query = build_account_position_risk_query_v1()
    if target_history_query.query.get("instId") != TARGET_INSTRUMENT_ID:
        raise P08DistinctFirstPartyEvidenceError("TARGET_HISTORY_QUERY_INVALID")
    if typed_history_query.query.get("instType") != TARGET_INST_TYPE:
        raise P08DistinctFirstPartyEvidenceError("TYPED_HISTORY_QUERY_INVALID")
    if "instId" in typed_history_query.query:
        raise P08DistinctFirstPartyEvidenceError("TYPED_HISTORY_MUST_OMIT_INSTID")
    if risk_query.query != {"instType": TARGET_INST_TYPE}:
        raise P08DistinctFirstPartyEvidenceError("RISK_QUERY_INVALID")

    productive = transport is None
    secretref_identity: dict[str, Any] | None = None
    if productive:
        if vault_file is None or not str(vault_file).strip():
            raise P08DistinctFirstPartyEvidenceError("VAULT_FILE_REQUIRED")
        secretref_identity = secretref_identity_without_values_v1(vault_file=vault_file)
        transport = UrllibLiveCanaryTransportV1(wire_send_enabled=True)
    if isinstance(transport, UrllibLiveCanaryTransportV1) and not bool(
        getattr(transport, "wire_send_enabled", False)
    ):
        raise P08DistinctFirstPartyEvidenceError("PRODUCTIVE_WIRE_DISABLED")

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

    def _issue(
        *,
        role: str,
        purpose: str,
        endpoint: str,
        query: dict[str, str],
        expected_path: str,
    ) -> dict[str, Any]:
        nonlocal owner_go_consumed, first_received_ms, last_received_ms
        path = _path_only_v1(endpoint)
        if path != expected_path:
            raise P08DistinctFirstPartyEvidenceError("ENDPOINT_PATH_MISMATCH")
        if path not in AUTHORIZED_ENDPOINT_PATHS:
            raise P08DistinctFirstPartyEvidenceError("ENDPOINT_NOT_AUTHORIZED")
        if path == ENDPOINT_ACCOUNT_POSITIONS_REUSED:
            if "posId" not in query:
                raise P08DistinctFirstPartyEvidenceError("POSITIONS_GET_REQUIRES_PROVEN_POSID")
            if "instId" in query or "instType" in query:
                raise P08DistinctFirstPartyEvidenceError("EQUIVALENT_POSITIONS_PROBE_FORBIDDEN")
        parsed = urlparse(f"{REUSED_REST_BASE}{endpoint}")
        if parsed.path != expected_path:
            raise P08DistinctFirstPartyEvidenceError("SIGNED_REQUEST_TARGET_MISMATCH")
        if parsed.hostname != AUTHORIZED_HOST:
            raise P08DistinctFirstPartyEvidenceError("HOST_MISMATCH")
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
                raise P08DistinctFirstPartyEvidenceError("NON_GET_RESPONSE")
            if redirect_followed:
                raise P08DistinctFirstPartyEvidenceError("REDIRECT_FOLLOWED")
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
            "BYTE_IDENTICAL_HISTORICAL_EMPTY_ENVELOPE_SHA": (
                body_sha256 == HISTORICAL_EMPTY_ENVELOPE_SHA256
            ),
            "BYTE_IDENTICAL_EMPTY_SHA_IS_NOT_CURRENT_08_PROOF": True,
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
            "HISTORY_EMPTY_IS_NEVER_HELD": False,
            "HISTORY_EMPTY_IS_CURRENT_ZERO": False,
            "RISK_POSDATA_EMPTY_IS_ZERO": False,
        }
        if path == ENDPOINT_ACCOUNT_POSITIONS_HISTORY:
            history = classify_history_channel_v1(
                result_class=result_class,
                payload=payload,
                instrument_id=TARGET_INSTRUMENT_ID,
            )
            data = (payload or {}).get("data") if payload else None
            record["DATA_ROW_COUNT"] = len(data) if isinstance(data, list) else None
            record["RAW_DATA_SHAPE"] = (
                "DATA_LIST"
                if isinstance(data, list)
                else "NO_PARSEABLE_PAYLOAD"
                if payload is None
                else "DATA_NOT_LIST"
            )
            record["REDACTED_PAYLOAD"] = _sanitize_history_payload_v1(payload)
            record.update(history)
        elif path == ENDPOINT_ACCOUNT_POSITION_RISK:
            risk = classify_risk_channel_v1(
                result_class=result_class,
                payload=payload,
                instrument_id=TARGET_INSTRUMENT_ID,
            )
            record["REDACTED_PAYLOAD"] = _sanitize_risk_payload_v1(payload)
            record["RAW_DATA_SHAPE"] = "RISK_ENVELOPE"
            record.update(risk)
        else:
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
                raise P08DistinctFirstPartyEvidenceError("EMPTY_DATA_MUST_NOT_BE_PROMOTED_TO_ZERO")
            data = (payload or {}).get("data") if payload else None
            record["DATA_ROW_COUNT"] = len(data) if isinstance(data, list) else None
            record["RAW_DATA_SHAPE"] = (
                "DATA_LIST"
                if isinstance(data, list)
                else "NO_PARSEABLE_PAYLOAD"
                if payload is None
                else "DATA_NOT_LIST"
            )
            record["REDACTED_PAYLOAD"] = sanitize_positions_payload_v1(payload)
            record["TARGET_POSITION_QTY_NUMERIC"] = (window or {}).get(
                "TARGET_POSITION_QTY_NUMERIC"
            )
            record["WINDOW"] = window
            record["CHANNEL"] = "ACCOUNT_POSITIONS_POSID"
            record["CHANNEL_IS_CANONICAL_P08_AUTHORITY"] = True
            record.update(observation)
        body_utf8 = _body_utf8_exact_v1(body_bytes)
        raw = {
            "DOCUMENT_CLASS": "P08_DISTINCT_FIRST_PARTY_RAW_EXCHANGE_V2",
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
        first_history = _issue(
            role=GET_ROLE_TARGET_HISTORY,
            purpose=GET_PURPOSE_TARGET_HISTORY,
            endpoint=target_history_query.path_with_query(),
            query=dict(target_history_query.query),
            expected_path=ENDPOINT_ACCOUNT_POSITIONS_HISTORY,
        )
        first_ok = (
            str(first_history.get("RESULT_CLASS") or "") == RESULT_CLASS_200_OKX_0
            and str(first_history.get("HISTORY_OBSERVATION_CLASS") or "")
            != HISTORY_CLASS_HTTP_OR_OKX_ERROR
        )
        history_pos_ids = tuple(first_history.get("TARGET_POS_ID_CANDIDATES") or [])
        if (
            first_ok
            and str(first_history.get("HISTORY_OBSERVATION_CLASS") or "") == HISTORY_CLASS_EMPTY
            and not history_pos_ids
        ):
            typed = _issue(
                role=GET_ROLE_TYPED_HISTORY,
                purpose=GET_PURPOSE_TYPED_HISTORY,
                endpoint=typed_history_query.path_with_query(),
                query=dict(typed_history_query.query),
                expected_path=ENDPOINT_ACCOUNT_POSITIONS_HISTORY,
            )
            history_pos_ids = merge_independently_proven_pos_ids_v1(
                history_pos_ids,
                tuple(typed.get("TARGET_POS_ID_CANDIDATES") or []),
            )
        elif first_ok and bool(first_history.get("PAGINATION_TRUNCATED")) and not history_pos_ids:
            cursor = str(first_history.get("PAGINATION_CURSOR") or "").strip()
            if cursor:
                paged = build_target_positions_history_query_v1(after=cursor)
                paged_record = _issue(
                    role=GET_ROLE_HISTORY_PAGINATION,
                    purpose=GET_PURPOSE_HISTORY_PAGINATION,
                    endpoint=paged.path_with_query(),
                    query=dict(paged.query),
                    expected_path=ENDPOINT_ACCOUNT_POSITIONS_HISTORY,
                )
                history_pos_ids = merge_independently_proven_pos_ids_v1(
                    history_pos_ids,
                    tuple(paged_record.get("TARGET_POS_ID_CANDIDATES") or []),
                )
        risk_record: dict[str, Any] | None = None
        skip_risk = (
            str(first_history.get("HISTORY_OBSERVATION_CLASS") or "")
            == (HISTORY_CLASS_HTTP_OR_OKX_ERROR)
            and str(first_history.get("RESULT_CLASS") or "") != RESULT_CLASS_200_OKX_0
        )
        if not skip_risk:
            risk_record = _issue(
                role=GET_ROLE_ACCOUNT_POSITION_RISK,
                purpose=GET_PURPOSE_ACCOUNT_POSITION_RISK,
                endpoint=risk_query.path_with_query(),
                query=dict(risk_query.query),
                expected_path=ENDPOINT_ACCOUNT_POSITION_RISK,
            )
        risk_pos_ids = tuple((risk_record or {}).get("TARGET_POS_ID_CANDIDATES") or [])
        merged_ids = merge_independently_proven_pos_ids_v1(history_pos_ids, risk_pos_ids)
        positions_record: dict[str, Any] | None = None
        if len(merged_ids) >= 1:
            posid_query = build_proven_posid_positions_query_v1(pos_id=",".join(merged_ids))
            positions_record = _issue(
                role=GET_ROLE_POSID_POSITIONS,
                purpose=GET_PURPOSE_POSID_POSITIONS,
                endpoint=posid_query.path_with_query(),
                query=dict(posid_query.query),
                expected_path=ENDPOINT_ACCOUNT_POSITIONS_REUSED,
            )
    finally:
        if handle is not None:
            release_live_canary_ephemeral_material_v1(handle)

    expected_gets = len(exchanges)
    counters = _assert_gets_zero_writes(client, expected_get_count=expected_gets)
    http_exchange_count = _exchange_count_v1(transport)
    if http_exchange_count != expected_gets:
        raise P08DistinctFirstPartyEvidenceError("HTTP_EXCHANGE_COUNT_MISMATCH")
    if http_exchange_count > MAX_HTTP_EXCHANGE_COUNT:
        raise P08DistinctFirstPartyEvidenceError("HTTP_EXCHANGE_COUNT_EXCEEDED")

    history_records = [
        item
        for item in exchanges
        if item.get("ENDPOINT_PATH") == ENDPOINT_ACCOUNT_POSITIONS_HISTORY
    ]
    risk_records = [
        item for item in exchanges if item.get("ENDPOINT_PATH") == ENDPOINT_ACCOUNT_POSITION_RISK
    ]
    positions_records = [
        item for item in exchanges if item.get("ENDPOINT_PATH") == ENDPOINT_ACCOUNT_POSITIONS_REUSED
    ]
    history_for_synth = history_records[0] if history_records else None
    if len(history_records) > 1:
        merged_history_ids = merge_independently_proven_pos_ids_v1(
            *[tuple(item.get("TARGET_POS_ID_CANDIDATES") or []) for item in history_records]
        )
        history_for_synth = dict(history_records[0])
        history_for_synth["TARGET_POS_ID_CANDIDATES"] = list(merged_history_ids)
        history_for_synth["TARGET_POS_ID_PROVEN"] = len(merged_history_ids) == 1
        history_for_synth["TARGET_POS_ID"] = (
            merged_history_ids[0] if len(merged_history_ids) == 1 else None
        )
        history_for_synth["TARGET_HISTORY_ROW_OBSERVED"] = any(
            bool(item.get("TARGET_HISTORY_ROW_OBSERVED")) for item in history_records
        )
    package = synthesize_package_v1(
        history=history_for_synth,
        risk=risk_records[0] if risk_records else None,
        positions=positions_records[0] if positions_records else None,
    )
    adjudication_ms = default_local_monotonic_ms_v1()
    freshness = evaluate_freshness_at_adjudication_v1(
        response_received_monotonic_ms=last_received_ms,
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
        "FILTERED_EMPTY_IS_ZERO": False,
        "TYPED_EMPTY_IS_ZERO": False,
        "HISTORY_EMPTY_IS_ZERO": False,
        "HISTORY_EMPTY_IS_NEVER_HELD": False,
        "HISTORY_EMPTY_IS_CURRENT_ZERO": False,
        "RISK_POSDATA_EMPTY_IS_ZERO": False,
        "CROSS_CHECK_IS_CANONICAL_AUTHORITY": False,
        "HISTORICAL_STATE_IS_CURRENT_STATE": False,
    }
    snapshot = {
        "DOCUMENT_CLASS": "P08_DISTINCT_FIRST_PARTY_EVIDENCE_GET_PACKAGE_V2",
        "DOCUMENT_ROLE": "GET_ONLY_FRESH_EVIDENCE_NON_SSOT",
        "AUTHORITY": "NONE",
        "THIS_ARTIFACT_IS_NOT_CANONICAL": True,
        "OWNER_GO": owned,
        "OWNER_GO_CONSUMED": owner_go_consumed,
        "THIS_SLICE": THIS_SLICE,
        "BOUND_ORIGIN_MAIN_SHA": bound_sha,
        "AUTHORIZED_ENDPOINTS": [
            "GET /api/v5/account/positions-history",
            "GET /api/v5/account/account-position-risk",
            "GET /api/v5/account/positions?posId=",
        ],
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
        "HISTORICAL_P08_EMPTY_DATA_EVIDENCE_PACK": HISTORICAL_P08_EMPTY_DATA_EVIDENCE_PACK,
        "HISTORICAL_P08_POSITION_OBSERVATION_PACK": HISTORICAL_P08_POSITION_OBSERVATION_PACK,
        "HISTORICAL_P08_IS_CURRENT_08_PROOF": False,
        "HISTORICAL_Z2CH_IS_CURRENT_08_PROOF": False,
        "EQUIVALENT_ACCOUNT_POSITIONS_EMPTY_PROBE_REPEATED": False,
        "FUNDING_GET_PERFORMED": False,
        "POSITIONS_UNFILTERED_GET_PERFORMED": False,
        "POSITIONS_INSTID_GET_PERFORMED": False,
        "POSITIONS_INSTTYPE_GET_PERFORMED": False,
        "POSITIONS_HISTORY_GET_PERFORMED": any(
            item.get("ENDPOINT_PATH") == ENDPOINT_ACCOUNT_POSITIONS_HISTORY for item in exchanges
        ),
        "ACCOUNT_POSITION_RISK_GET_PERFORMED": any(
            item.get("ENDPOINT_PATH") == ENDPOINT_ACCOUNT_POSITION_RISK for item in exchanges
        ),
        "POSID_POSITIONS_GET_PERFORMED": any(
            item.get("ENDPOINT_PATH") == ENDPOINT_ACCOUNT_POSITIONS_REUSED for item in exchanges
        ),
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
    adjudication = {
        "DOCUMENT_CLASS": "P08_DISTINCT_FIRST_PARTY_WINDOW_ADJUDICATION_V2",
        "DOCUMENT_ROLE": "INTERPRETATION_NOT_RAW_EVIDENCE_NOT_SSOT",
        "AUTHORITY": "NONE",
        "OWNER_GO": owned,
        "BOUND_ORIGIN_MAIN_SHA": bound_sha,
        "P08_CANONICAL_DEFINITION": P08_CANONICAL_DEFINITION_REUSED,
        "HISTORY_CLASSIFIER": "classify_history_channel_v1",
        "RISK_CLASSIFIER": "classify_risk_channel_v1",
        "POSITIONS_CLASSIFIER": "classify_position_observation_v1",
        "PACKAGE_CLASSIFIER": "synthesize_package_v1",
        "FRESHNESS_POLICY": FRESHNESS_POLICY,
        "FRESHNESS_POLICY_MAX_AGE_MS": POSITION_OBSERVATION_FRESHNESS_MAX_AGE_MS,
        "AGE_EVALUATION_POINT_THIS_WINDOW": "ADJUDICATION_AFTER_LAST_GET_NOT_FLATTEN_SEND",
        "FLATTEN_PRE_SEND_PERMIT_EVALUATED": False,
        "LOCAL_RESPONSE_RECEIVED_AT": last_received_ms,
        "FIRST_RESPONSE_RECEIVED_AT": first_received_ms,
        "ADJUDICATION_MONOTONIC_MS": adjudication_ms,
        "GET_REQUEST_COUNT": expected_gets,
        "HTTP_EXCHANGE_COUNT": http_exchange_count,
        "GET_ROLES_PERFORMED": [item["GET_ROLE"] for item in exchanges],
        "CHANNEL_ADJUDICATIONS": {
            "HISTORY": [
                {
                    "GET_ROLE": item.get("GET_ROLE"),
                    "HISTORY_OBSERVATION_CLASS": item.get("HISTORY_OBSERVATION_CLASS"),
                    "TARGET_HISTORY_ROW_OBSERVED": item.get("TARGET_HISTORY_ROW_OBSERVED"),
                    "TARGET_POS_ID_PROVEN": item.get("TARGET_POS_ID_PROVEN"),
                    "TARGET_POS_ID_CANDIDATES": item.get("TARGET_POS_ID_CANDIDATES"),
                }
                for item in history_records
            ],
            "RISK": [
                {
                    "GET_ROLE": item.get("GET_ROLE"),
                    "RISK_OBSERVATION_CLASS": item.get("RISK_OBSERVATION_CLASS"),
                    "TARGET_RISK_ROW_OBSERVED": item.get("TARGET_RISK_ROW_OBSERVED"),
                    "TARGET_POS_ID_PROVEN": item.get("TARGET_POS_ID_PROVEN"),
                    "TARGET_POS_ID_CANDIDATES": item.get("TARGET_POS_ID_CANDIDATES"),
                }
                for item in risk_records
            ],
            "POSID_POSITIONS": [
                {
                    "GET_ROLE": item.get("GET_ROLE"),
                    "POSITION_OBSERVATION_CLASS": item.get("POSITION_OBSERVATION_CLASS"),
                    "TARGET_INSTRUMENT_ROW_OBSERVED": item.get("TARGET_INSTRUMENT_ROW_OBSERVED"),
                    "TARGET_POSITION_ZERO_PROVEN": item.get("TARGET_POSITION_ZERO_PROVEN"),
                    "TARGET_POSITION_NONZERO_PROVEN": item.get("TARGET_POSITION_NONZERO_PROVEN"),
                }
                for item in positions_records
            ],
        },
        "HYPOTHESIS": (
            "Distinct first-party history and risk envelopes can discriminate "
            "posId recovery and current-state cross-checks without repeating "
            "equivalent empty /account/positions listings. This sentence is "
            "interpretation context, not proof."
        ),
        "HYPOTHESIS_IS_NOT_PROOF": True,
        **freshness,
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
        "HISTORY_EMPTY_IS_NEVER_HELD": False,
        "HISTORY_EMPTY_IS_CURRENT_ZERO": False,
        "RISK_POSDATA_EMPTY_IS_ZERO": False,
        "CROSS_CHECK_IS_CANONICAL_AUTHORITY": False,
        "HISTORICAL_STATE_IS_CURRENT_STATE": False,
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
    first = exchanges[0] if exchanges else {}
    summary = {
        "DOCUMENT_CLASS": "P08_DISTINCT_FIRST_PARTY_EVIDENCE_GET_PACKAGE_V2",
        "DOCUMENT_ROLE": "DERIVED_NON_SSOT",
        "OWNER_GO": owned,
        "OWNER_GO_CONSUMED": owner_go_consumed,
        "THIS_SLICE": THIS_SLICE,
        "BOUND_ORIGIN_MAIN_SHA": bound_sha,
        "METHOD": "GET",
        "HOST": REUSED_REST_HOST,
        "TARGET_INSTRUMENT_ID": TARGET_INSTRUMENT_ID,
        "TARGET_INST_TYPE": TARGET_INST_TYPE,
        "GET_ROLES_PERFORMED": [item["GET_ROLE"] for item in exchanges],
        "RESULT_CLASS": first.get("RESULT_CLASS"),
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
        "TARGET_POS_ID_PROVEN": package["TARGET_POS_ID_PROVEN"],
        "TARGET_POS_ID": package["TARGET_POS_ID"],
        "POSITION_OBSERVATION_CLASS": package["POSITION_OBSERVATION_CLASS"],
        "P08_CLOSED": package["P08_CLOSED"],
        "P08_VERDICT": package["P08_VERDICT"],
        "G_POSMODE_SUBMIT_BODY_PROVEN": False,
        "HISTORY_PROMOTED_TO_CURRENT_STATE": False,
        "RISK_PROMOTED_TO_CANONICAL_AUTHORITY": False,
        "EQUIVALENT_ACCOUNT_POSITIONS_EMPTY_PROBE_REPEATED": False,
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
        "HTTP_STATUS": first.get("HTTP_STATUS"),
        "OKX_CODE": first.get("OKX_CODE"),
        "GET_ERROR": first.get("GET_ERROR"),
        "PARSE_ERROR": first.get("PARSE_ERROR"),
    }
    census = {
        "DOCUMENT_CLASS": "P08_DISTINCT_FIRST_PARTY_PATH_CENSUS_V2",
        "DOCUMENT_ROLE": "NAVIGATION_INVENTORY_NOT_SSOT_NOT_AUTHORITY",
        "AUTHORITY": "NONE",
        "BOUND_ORIGIN_MAIN_SHA": bound_sha,
        "PREDECESSOR_SLICE": "11.13.5.P08_EMPTY_DATA_NOT_ZERO",
        "PREDECESSOR_EVIDENCE_PACK": HISTORICAL_P08_EMPTY_DATA_EVIDENCE_PACK,
        "PREDECESSOR_IS_HISTORICAL": True,
        "PREDECESSOR_IS_NOT_CURRENT_08_PROOF": True,
        "CURRENT_PACKAGE": THIS_SLICE,
        "DISTINCT_CHANNELS": [
            "GET /api/v5/account/positions-history",
            "GET /api/v5/account/account-position-risk",
            "GET /api/v5/account/positions?posId=INDEPENDENTLY_PROVEN",
        ],
        "NOT_REPEATED": [
            "GET /api/v5/account/positions unfiltered",
            "GET /api/v5/account/positions?instId=",
            "GET /api/v5/account/positions?instType=FUTURES",
        ],
        "PRODUCTIVE_OWNERS": {
            "PREDECESSOR_EXECUTOR": (
                "src/ops/section_11_13_5_p08_empty_data_not_zero_v1/execute_v1.py"
            ),
            "THIS_EXECUTOR": (
                "src/ops/section_11_13_5_p08_distinct_first_party_evidence_v1/execute_v1.py"
            ),
            "CLASSIFIER": (
                "src/ops/section_11_13_5_p08_distinct_first_party_evidence_v1/classify_v1.py"
            ),
            "QUERY_GRAMMAR": (
                "src/ops/section_11_13_5_p08_distinct_first_party_evidence_v1/query_grammar_v1.py"
            ),
            "POSITIONS_QUERY_GRAMMAR": (
                "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
                "account_positions_query_grammar_v1.py"
            ),
            "HTTP_CLIENT": (
                "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/http_client_v1.py"
            ),
            "PERSISTENCE": (
                "src/ops/section_11_13_5_p08_distinct_first_party_evidence_v1/persist_v1.py"
            ),
        },
        "CLAIMS_SNAPSHOT": dict(CLAIMS),
        "CALLERS_THIS_PACKAGE": [
            "scripts/ops/run_section_11_13_5_p08_distinct_first_party_evidence_v1.py",
            "tests/ops/test_section_11_13_5_p08_distinct_first_party_evidence_v1.py",
        ],
        "PERSISTENCE_SURFACES": [
            "GET_TARGET_HISTORY.raw.json",
            "GET_TYPED_HISTORY.raw.json",
            "GET_TARGET_HISTORY_AFTER.raw.json",
            "GET_ACCOUNT_POSITION_RISK.raw.json",
            "GET_POSID_POSITIONS.raw.json",
            "GET_SNAPSHOT.sanitized.json",
            "ADJUDICATION.json",
            "SUMMARY.json",
            "CENSUS.json",
            "claims.json",
            "MANIFEST.sha256",
        ],
        "TEST_OWNERS": [
            "tests/ops/test_section_11_13_5_p08_distinct_first_party_evidence_v1.py",
            "tests/ops/test_section_11_13_5_p08_distinct_first_party_evidence_persist_v1.py",
        ],
    }
    verified = persist_p08_distinct_first_party_evidence_v1(
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
