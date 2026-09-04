"""Persist verified P5 evidence, then issue at most two private read-only GETs.

Reuses LiveCanaryHttpClientV1, UrllibLiveCanaryTransportV1, the canary HMAC
signer, and the existing unfiltered positions query builder. Pending GET is
the unfiltered flatten-reconciliation surface `/api/v5/trade/orders-pending`.
No POST, retry, cancel, flatten, or funding.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

from src.ops.section_11_13_5_authenticated_private_runtime_read_and_runtime_permit_issuance_v1.execute_v1 import (
    observation_identity_v1,
)
from src.ops.section_11_13_5_g12_canonical_delayed_zero_persist_and_pending_related_observations_v1.adjudicate_v1 import (
    closeout_fields_v1,
    evaluate_full_g12_conjunction_v1,
)
from src.ops.section_11_13_5_g12_canonical_delayed_zero_persist_and_pending_related_observations_v1.constants_v1 import (
    AUTHORIZED_HOST_VALUE,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT_SECONDS,
    DEFAULT_VAULT_RELATIVE,
    DELAYED_ZERO_REQUEST_PATH,
    EVIDENCE_DIRNAME,
    EXPECTED_ORIGIN_MAIN_SHA,
    MAX_HTTP_EXCHANGE_COUNT,
    MAX_NETWORK_REQUEST_COUNT,
    OWNER_GO,
    PENDING_REQUEST_PATH,
    PENDING_ROW_ALLOWLIST,
    PROVEN_POS_ID,
    RELATED_REQUEST_PATH,
    REUSED_CREDENTIAL_CLASS,
    REUSED_REST_BASE,
    REUSED_REST_HOST,
    REUSED_SECRETREF_URI,
    REUSED_USER_AGENT,
    TARGET_INSTRUMENT_ID_VALUE,
    THIS_SLICE,
)
from src.ops.section_11_13_5_g12_canonical_delayed_zero_persist_and_pending_related_observations_v1.contract_v1 import (
    G12CanonicalDelayedZeroPersistError,
    assert_contract_invariants_v1,
)
from src.ops.section_11_13_5_g12_canonical_delayed_zero_persist_and_pending_related_observations_v1.lineage_bind_v1 import (
    bind_flatten_lineage_v1,
)
from src.ops.section_11_13_5_g12_canonical_delayed_zero_persist_and_pending_related_observations_v1.persist_v1 import (
    persist_g12_delayed_zero_pack_v1,
)
from src.ops.section_11_13_5_g12_canonical_delayed_zero_persist_and_pending_related_observations_v1.verify_local_capture_v1 import (
    verify_local_delayed_zero_capture_v1,
)
from src.ops.section_11_13_5_g12_delayed_posid_zero_row_full_conjunction_proof_contract_v1.constants_v1 import (
    PENDING_ENDPOINT,
    POSITIONS_ENDPOINT,
)
from src.ops.section_11_13_5_g12_delayed_posid_zero_row_full_conjunction_proof_contract_v1.types_v1 import (
    ObservationSlotV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.account_positions_query_grammar_v1 import (
    build_account_positions_query_v1,
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
    sanitize_positions_payload_v1,
)
from src.ops.section_11_13_5_p08_position_observation_v1.execute_v1 import (
    classify_http_okx_result_v1,
)
from src.ops.section_11_13_5_post_z2ds_private_get_current_50110_egress_capture_v1.execute_v1 import (
    sanitize_okx_message_v1,
)


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


def _sanitize_pending_payload_v1(payload: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if payload is None:
        return None
    data = payload.get("data")
    rows = data if isinstance(data, list) else []
    redacted_rows = []
    for item in rows:
        if not isinstance(item, Mapping):
            continue
        row: dict[str, Any] = {}
        for key, value in dict(item).items():
            if str(key) not in PENDING_ROW_ALLOWLIST:
                continue
            if isinstance(value, (str, int, float, bool)) or value is None:
                row[str(key)] = value
        redacted_rows.append(row)
    return {
        "code": payload.get("code"),
        "msg": sanitize_okx_message_v1(str(payload.get("msg") or "")[:200]),
        "data": redacted_rows,
        "ROW_FIELDS_REDACTED_TO_ALLOWLIST": True,
    }


def _slot_from_get(
    *,
    endpoint: str,
    query: Mapping[str, str],
    record: Mapping[str, Any],
) -> ObservationSlotV1:
    payload = record.get("REDACTED_PAYLOAD")
    if not isinstance(payload, Mapping):
        raise G12CanonicalDelayedZeroPersistError("GET_PAYLOAD_MISSING")
    return ObservationSlotV1(
        endpoint=endpoint,
        observation_identity=str(record.get("OBSERVATION_IDENTITY") or ""),
        request_time_utc=str(record.get("REQUEST_TIME_UTC") or ""),
        payload=payload,
        query=dict(query),
        body_sha256=str(record.get("BODY_SHA256") or "") or None,
        http_status=int(record["HTTP_STATUS"]) if record.get("HTTP_STATUS") is not None else None,
        venue_code=str(record.get("VENUE_CODE") or "") or None,
    )


def _issue_signed_get_v1(
    *,
    client: LiveCanaryHttpClientV1,
    transport: LiveCanaryTransportV1,
    handle: Any,
    productive: bool,
    endpoint: str,
    expected_path: str,
    role: str,
) -> dict[str, Any]:
    parsed = urlparse(f"{REUSED_REST_BASE}{endpoint}")
    if parsed.path != expected_path:
        raise G12CanonicalDelayedZeroPersistError("ENDPOINT_PATH_MISMATCH")
    if parsed.query:
        raise G12CanonicalDelayedZeroPersistError("QUERY_MUST_BE_EMPTY")
    if parsed.hostname != AUTHORIZED_HOST_VALUE:
        raise G12CanonicalDelayedZeroPersistError("HOST_MISMATCH")
    if _exchange_count_v1(transport) >= MAX_HTTP_EXCHANGE_COUNT:
        raise G12CanonicalDelayedZeroPersistError("MAX_HTTP_EXCHANGE_COUNT_EXCEEDED")
    auth_headers: dict[str, str] = {}
    header_presence = _header_presence_v1({})
    request_time = _utc_now_iso_v1()
    http_status: int | None = None
    body_bytes = b""
    get_error: str | None = None
    send_attempted = False
    redirect_followed = False
    received_ms: int | None = None
    response_headers_safe: dict[str, str] = {}
    elapsed_seconds: float | None = None
    try:
        if productive:
            url = f"{REUSED_REST_BASE}{endpoint}"
            auth_headers = build_okx_live_canary_auth_headers_v1(
                handle=handle, url=url, method="GET"
            )
            auth_headers["User-Agent"] = REUSED_USER_AGENT
            header_presence = _header_presence_v1(auth_headers)
            if not (
                header_presence["AUTH_KEY_HEADER_PRESENT"]
                and header_presence["AUTH_SIGN_HEADER_PRESENT"]
                and header_presence["AUTH_TIMESTAMP_HEADER_PRESENT"]
                and header_presence["AUTH_PASSPHRASE_HEADER_PRESENT"]
            ):
                raise G12CanonicalDelayedZeroPersistError("HMAC_HEADERS_MISSING")
            if header_presence["SIMULATION_HEADER_PRESENT"]:
                raise G12CanonicalDelayedZeroPersistError("SIMULATION_HEADER_FORBIDDEN")
        response = client.get(endpoint=endpoint, headers=auth_headers or None)
        send_attempted = True
        received_ms = default_local_monotonic_ms_v1()
        http_status = int(response.status_code)
        body_bytes = bytes(response.body_bytes)
        redirect_followed = bool(response.redirect_followed)
        elapsed_seconds = float(response.elapsed_seconds)
        response_headers_safe = dict(response.response_headers_safe or {})
        if response.method != "GET":
            raise G12CanonicalDelayedZeroPersistError("NON_GET_RESPONSE")
        if redirect_followed:
            raise G12CanonicalDelayedZeroPersistError("REDIRECT_FOLLOWED")
    except LiveCanaryHttpError as exc:
        send_attempted = True
        get_error = str(exc)
    finally:
        auth_headers.clear()
    if get_error or http_status in {401, 403}:
        raise G12CanonicalDelayedZeroPersistError(
            f"AUTH_OR_TRANSPORT_FAILURE:{role}:{get_error or http_status}"
        )
    response_time = _utc_now_iso_v1()
    payload: dict[str, Any] | None = None
    parse_error: str | None = None
    if body_bytes:
        try:
            payload = parse_json_object_v1(body_bytes)
        except LiveCanaryHttpError as exc:
            parse_error = str(exc)
    if payload is None or parse_error:
        raise G12CanonicalDelayedZeroPersistError(f"GET_PAYLOAD_INCOMPLETE:{role}")
    venue_code = str(payload.get("code") or "")
    venue_msg = sanitize_okx_message_v1(str(payload.get("msg") or "")[:200])
    result_class = classify_http_okx_result_v1(
        http_status=http_status,
        venue_code=venue_code,
        get_error=get_error,
    )
    if result_class != "HTTP_200_OKX_0":
        raise G12CanonicalDelayedZeroPersistError(f"GET_NOT_HTTP_200_OKX_0:{role}:{result_class}")
    data = payload.get("data")
    if not isinstance(data, list):
        raise G12CanonicalDelayedZeroPersistError(f"GET_DATA_NOT_LIST:{role}")
    body_sha256 = hashlib.sha256(body_bytes).hexdigest()
    identity = observation_identity_v1(
        body_sha256=body_sha256,
        received_ms=received_ms,
        endpoint=endpoint,
    )
    if expected_path == PENDING_ENDPOINT:
        redacted = _sanitize_pending_payload_v1(payload)
    else:
        redacted = sanitize_positions_payload_v1(payload)
    return {
        "GET_ROLE": role,
        "ENDPOINT": endpoint,
        "ENDPOINT_PATH": expected_path,
        "QUERY_PARAMETERS": {},
        "REQUEST_TIME_UTC": request_time,
        "RESPONSE_TIME_UTC": response_time,
        "HTTP_STATUS": http_status,
        "VENUE_CODE": venue_code,
        "VENUE_MSG": venue_msg,
        "RESULT_CLASS": result_class,
        "BODY_BYTES": len(body_bytes),
        "BODY_SHA256": body_sha256,
        "OBSERVATION_IDENTITY": identity,
        "DATA_ROW_COUNT": len(data),
        "REDACTED_PAYLOAD": redacted,
        "HEADER_PRESENCE": header_presence,
        "LOCAL_RESPONSE_RECEIVED_AT": received_ms,
        "ELAPSED_SECONDS": elapsed_seconds,
        "RESPONSE_HEADERS_SAFE": response_headers_safe or safe_response_headers_v1({}),
        "SEND_ATTEMPTED": send_attempted,
        "SECRET_VALUES_INCLUDED": False,
        "RAW": {
            "DOCUMENT_CLASS": "G12_P7_P9_RAW_EXCHANGE_V1",
            "DOCUMENT_ROLE": "FORENSIC_RAW_NOT_CANONICAL_NOT_ADJUDICATION",
            "AUTHORITY": "NONE",
            "METHOD": "GET",
            "HOST": REUSED_REST_HOST,
            "ENDPOINT": endpoint,
            "ENDPOINT_PATH": expected_path,
            "REQUEST_TIME_UTC": request_time,
            "HTTP_STATUS": http_status,
            "BODY_BYTES": len(body_bytes),
            "BODY_SHA256": body_sha256,
            "BODY_UTF8_EXACT": body_bytes.decode("utf-8") if body_bytes else None,
            "SECRET_VALUES_INCLUDED": False,
        },
    }


def run_g12_canonical_delayed_zero_persist_and_observations_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    repo_root: Path,
    evidence_root: Path,
    vault_file: Path | None = None,
    transport: LiveCanaryTransportV1 | None = None,
    persist: bool = True,
) -> dict[str, Any]:
    assert_contract_invariants_v1()
    if str(owner_go or "").strip() != OWNER_GO:
        raise G12CanonicalDelayedZeroPersistError("OWNER_GO_MISMATCH")
    if str(origin_main_sha or "").strip() != EXPECTED_ORIGIN_MAIN_SHA:
        raise G12CanonicalDelayedZeroPersistError("ORIGIN_MAIN_SHA_MISMATCH")
    p5 = verify_local_delayed_zero_capture_v1(repo_root=repo_root)
    lineage = bind_flatten_lineage_v1(repo_root=repo_root)
    delayed_slot = ObservationSlotV1(
        endpoint=DELAYED_ZERO_REQUEST_PATH,
        observation_identity=str(p5["DELAYED_ZERO"]["OBSERVATION_IDENTITY"]),
        request_time_utc=str(p5["DELAYED_ZERO"]["REQUEST_TIME_UTC"]),
        payload=p5["DELAYED_ZERO"]["REDACTED_PAYLOAD"],
        query={"posId": PROVEN_POS_ID},
        body_sha256=str(p5["DELAYED_ZERO"]["BODY_SHA256"]),
        http_status=200,
        venue_code="0",
    )
    if delayed_slot.observation_identity == lineage.immediate_post_action_identity:
        raise G12CanonicalDelayedZeroPersistError("DELAYED_IDENTITY_EQUALS_IMMEDIATE_POST")
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    pack = Path(evidence_root) / EVIDENCE_DIRNAME / run_id
    if persist:
        persist_g12_delayed_zero_pack_v1(
            pack=pack,
            origin_main_sha=origin_main_sha,
            documents={
                "GET_HISTORY_POSID.sanitized.json": {
                    "DOCUMENT_CLASS": "G12_P5_HISTORY_POSID_V1",
                    "DOCUMENT_ROLE": "SANITIZED_HISTORY_POSID_EVIDENCE_NOT_SSOT",
                    "AUTHORITY": "NONE",
                    **p5["HISTORY"],
                    "OWNER_GO": OWNER_GO,
                    "PRIOR_CAPTURE_OWNER_GO": p5.get("FORENSIC_LOCAL_CAPTURE_PATH"),
                    "FORENSIC_LOCAL_IS_NOT_CANONICAL": True,
                    "ORIGINAL_WIRE_BODY_BYTES_AVAILABLE": False,
                },
                "GET_DELAYED_POSID_ZERO.sanitized.json": {
                    "DOCUMENT_CLASS": "G12_P5_DELAYED_POSID_ZERO_V1",
                    "DOCUMENT_ROLE": "SANITIZED_DELAYED_EXPLICIT_ZERO_NOT_IMMEDIATE_POST_READBACK",
                    "AUTHORITY": "NONE",
                    **p5["DELAYED_ZERO"],
                    "OWNER_GO": OWNER_GO,
                    "FORENSIC_LOCAL_IS_NOT_CANONICAL": True,
                    "ORIGINAL_WIRE_BODY_BYTES_AVAILABLE": False,
                    "NOT_ORIGINAL_IMMEDIATE_POST_ACTION_READBACK": True,
                },
                "P5_VERIFICATION.json": {
                    "DOCUMENT_CLASS": "G12_P5_VERIFICATION_V1",
                    "P5_SOURCE_LOCAL_CAPTURE_VERIFIED": True,
                    "P5_CANONICAL_PERSIST": "PASS",
                    "FORENSIC_LOCAL_CAPTURE_SHA256": p5["FORENSIC_LOCAL_CAPTURE_SHA256"],
                    "FORENSIC_LOCAL_IS_NOT_CANONICAL": True,
                    "TARGET_POSITION_ZERO_WINDOW_PROVEN": True,
                    "CANONICAL_SSOT_TARGET_POSITION_ZERO_PROVEN": False,
                    "P5_POSID": PROVEN_POS_ID,
                    "P5_ZERO_OBSERVATION_IDENTITY": delayed_slot.observation_identity,
                    "P5_ZERO_TIMESTAMP": delayed_slot.request_time_utc,
                    "OWNER_GO": OWNER_GO,
                    "THIS_SLICE": THIS_SLICE,
                },
            },
        )

    pending_query = build_account_positions_query_v1()
    if pending_query.query:
        raise G12CanonicalDelayedZeroPersistError("RELATED_QUERY_MUST_BE_UNFILTERED")
    related_endpoint = pending_query.path_with_query()
    if related_endpoint != RELATED_REQUEST_PATH:
        raise G12CanonicalDelayedZeroPersistError("RELATED_ENDPOINT_DRIFT")
    if PENDING_REQUEST_PATH != PENDING_ENDPOINT:
        raise G12CanonicalDelayedZeroPersistError("PENDING_ENDPOINT_DRIFT")

    productive = transport is None
    if productive:
        vault = vault_file or (Path(repo_root) / ".ops_local" / DEFAULT_VAULT_RELATIVE)
        backend = build_file_secretref_vault_backend_v1(vault_file=Path(vault))
        handle = resolve_and_load_live_canary_secretref_ephemeral_v1(
            secret_reference=REUSED_SECRETREF_URI,
            vault_backend=backend,
            credential_class=REUSED_CREDENTIAL_CLASS,
        )
        live_transport: LiveCanaryTransportV1 = UrllibLiveCanaryTransportV1(wire_send_enabled=True)
    else:
        handle = None
        live_transport = transport
        if live_transport is None:
            raise G12CanonicalDelayedZeroPersistError("TRANSPORT_REQUIRED")
    if isinstance(live_transport, UrllibLiveCanaryTransportV1) and not bool(
        getattr(live_transport, "wire_send_enabled", False)
    ):
        raise G12CanonicalDelayedZeroPersistError("PRODUCTIVE_WIRE_DISABLED")
    client = LiveCanaryHttpClientV1(
        rest_base=REUSED_REST_BASE,
        rest_host=REUSED_REST_HOST,
        transport=live_transport,
        max_request_count=MAX_NETWORK_REQUEST_COUNT,
        max_retries=DEFAULT_MAX_RETRIES,
        timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
    )
    pending_record: dict[str, Any] | None = None
    related_record: dict[str, Any] | None = None
    try:
        pending_record = _issue_signed_get_v1(
            client=client,
            transport=live_transport,
            handle=handle,
            productive=productive,
            endpoint=PENDING_REQUEST_PATH,
            expected_path=PENDING_ENDPOINT,
            role="P7_PENDING",
        )
        if str(pending_record["REQUEST_TIME_UTC"]) < str(delayed_slot.request_time_utc):
            raise G12CanonicalDelayedZeroPersistError("PENDING_TIMESTAMP_NOT_AFTER_DELAYED_ZERO")
        related_record = _issue_signed_get_v1(
            client=client,
            transport=live_transport,
            handle=handle,
            productive=productive,
            endpoint=RELATED_REQUEST_PATH,
            expected_path=POSITIONS_ENDPOINT,
            role="P9_RELATED",
        )
        if str(related_record["REQUEST_TIME_UTC"]) < str(delayed_slot.request_time_utc):
            raise G12CanonicalDelayedZeroPersistError("RELATED_TIMESTAMP_NOT_AFTER_DELAYED_ZERO")
    finally:
        if handle is not None:
            release_live_canary_ephemeral_material_v1(handle)
    if pending_record is None or related_record is None:
        raise G12CanonicalDelayedZeroPersistError("P7_P9_INCOMPLETE")
    if int(client.counters.get_request_count) != 2:
        raise G12CanonicalDelayedZeroPersistError("GET_COUNT_NOT_TWO")
    if int(client.counters.write_request_count) != 0:
        raise G12CanonicalDelayedZeroPersistError("WRITE_COUNT_NOT_ZERO")

    pending_slot = _slot_from_get(endpoint=PENDING_REQUEST_PATH, query={}, record=pending_record)
    related_slot = _slot_from_get(endpoint=RELATED_REQUEST_PATH, query={}, record=related_record)
    verdict = evaluate_full_g12_conjunction_v1(
        flatten_lineage=lineage,
        delayed_target_zero=delayed_slot,
        pending_orders=pending_slot,
        related_positions=related_slot,
    )
    closeout = closeout_fields_v1(
        verdict=verdict,
        delayed_window_proven=True,
    )
    summary = {
        "DOCUMENT_CLASS": "G12_CANONICAL_DELAYED_ZERO_PERSIST_AND_P7_P9_SUMMARY_V1",
        "OWNER_GO": OWNER_GO,
        "THIS_SLICE": THIS_SLICE,
        "BOUND_ORIGIN_MAIN_SHA": origin_main_sha,
        "TARGET_INSTRUMENT_ID": TARGET_INSTRUMENT_ID_VALUE,
        "P5_CANONICAL_PERSIST": "PASS",
        "P5_POSID": PROVEN_POS_ID,
        "P5_ZERO_OBSERVATION_IDENTITY": delayed_slot.observation_identity,
        "P5_ZERO_TIMESTAMP": delayed_slot.request_time_utc,
        "P7_GET_PERFORMED": True,
        "P7_ENDPOINT": PENDING_REQUEST_PATH,
        "P7_REQUEST_TIMESTAMP": pending_slot.request_time_utc,
        "P7_OBSERVATION_IDENTITY": pending_slot.observation_identity,
        "P7_PENDING_EMPTY": closeout["P7_PENDING_EMPTY"],
        "P9_GET_PERFORMED": True,
        "P9_ENDPOINT": RELATED_REQUEST_PATH,
        "P9_REQUEST_TIMESTAMP": related_slot.request_time_utc,
        "P9_OBSERVATION_IDENTITY": related_slot.observation_identity,
        "P9_NO_UNEXPECTED_RELATED_NONZERO": closeout["P9_NO_UNEXPECTED_RELATED_NONZERO"],
        "TOTAL_NEW_HTTP_GET_COUNT": 2,
        "TOTAL_WRITE_COUNT": 0,
        "POST_USED": False,
        "RETRY_USED": False,
        "CREDENTIALS_EXPOSED": False,
        "DATA_EMPTY_PROMOTED_TO_ZERO": False,
        **closeout,
        "EVALUATOR": verdict.to_dict(),
        "COUNTERS": client.counters.to_dict(),
    }
    if persist:
        persist_g12_delayed_zero_pack_v1(
            pack=pack,
            origin_main_sha=origin_main_sha,
            documents={
                "GET_ORDERS_PENDING.sanitized.json": {
                    "DOCUMENT_CLASS": "G12_P7_PENDING_V1",
                    "DOCUMENT_ROLE": "SANITIZED_PENDING_EMPTY_OBSERVATION_NOT_SSOT",
                    "AUTHORITY": "NONE",
                    **{k: v for k, v in pending_record.items() if k != "RAW"},
                    "OWNER_GO": OWNER_GO,
                },
                "GET_ORDERS_PENDING.raw.json": pending_record["RAW"],
                "GET_ACCOUNT_POSITIONS_UNFILTERED.sanitized.json": {
                    "DOCUMENT_CLASS": "G12_P9_RELATED_V1",
                    "DOCUMENT_ROLE": "SANITIZED_UNFILTERED_RELATED_COMPLETENESS_NOT_SSOT",
                    "AUTHORITY": "NONE",
                    **{k: v for k, v in related_record.items() if k != "RAW"},
                    "OWNER_GO": OWNER_GO,
                },
                "GET_ACCOUNT_POSITIONS_UNFILTERED.raw.json": related_record["RAW"],
                "ADJUDICATION.json": {
                    "DOCUMENT_CLASS": "G12_FULL_CONJUNCTION_ADJUDICATION_V1",
                    "AUTHORITY": "NONE",
                    **closeout,
                    "OWNER_GO": OWNER_GO,
                    "THIS_SLICE": THIS_SLICE,
                },
                "SUMMARY.json": summary,
            },
        )
    summary["EVIDENCE_PACK"] = str(pack) if persist else ""
    return summary
