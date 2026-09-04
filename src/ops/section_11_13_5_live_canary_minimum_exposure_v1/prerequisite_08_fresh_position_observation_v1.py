"""GO-gated one-shot unfiltered positions GET for EXECUTION_PREREQUISITE_08.

Reuses §11.13.3 LIVE-RO SecretRef + GET-only urllib. Does not POST, flatten,
retry, invent HMAC plumbing, consume Class D, or claim send-time PASS.
Raw evidence and adjudication remain separate artifacts.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from src.ops.section_11_13_3_live_shadow_with_exchange_reconciliation_v1.binding_v1 import (
    build_live_shadow_recon_venue_binding_v1,
)
from src.ops.section_11_13_3_live_shadow_with_exchange_reconciliation_v1.http_client_v1 import (
    LiveShadowReconHttpClientV1,
    LiveShadowReconHttpError,
    LiveShadowReconHttpRequestV1,
    LiveShadowReconHttpResponseV1,
    TRANSPORT_CLASS_LIVE_PRODUCTIVE_HTTP,
)
from src.ops.section_11_13_3_live_shadow_with_exchange_reconciliation_v1.live_credential_ephemeral_v1 import (
    assert_no_plaintext_in_payload_v1,
    build_file_secretref_vault_backend_v1,
    release_live_ephemeral_material_v1,
    resolve_and_load_live_secretref_ephemeral_v1,
)
from src.ops.section_11_13_3_live_shadow_with_exchange_reconciliation_v1.okx_live_ro_signer_v1 import (
    build_okx_live_ro_get_auth_headers_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.account_positions_query_grammar_v1 import (
    build_account_positions_query_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    ENDPOINT_ACCOUNT_POSITIONS,
    REUSED_BINDING_ACCOUNT_SCOPE,
    REUSED_BINDING_ENTITY,
    REUSED_BINDING_REGION,
    REUSED_BINDING_REST_HOST,
    REUSED_BINDING_VENUE,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.evidence_v1 import (
    verify_manifest_v1,
    write_json_v1,
    write_manifest_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.execution_prerequisite_08_cluster_contract_v1 import (
    AUTHENTICATED_PRODUCTIVE_TRANSPORT_STATUS,
    CLASS_D_CONSUMED,
    EARLIEST_UNRESOLVED_DEPENDENCY,
    EXECUTION_READY,
    LIVE_FLATTEN_PROVABILITY,
    REASON_DEPENDENT_BLOCKED,
    SEND_TIME_PASS_18_19_21_24,
    Z2AP_CONSUMED,
    Z2CN_COMMITTED_BODY_SHA256,
    evaluate_execution_prerequisite_08_cluster_v1,
)
from src.ops.section_11_13_5_p11_pos_to_sz_unit_identity_independent_proof_v1.contract_v1 import (
    TARGET_POSITION_QTY_UNIT_STATUS,
    UNIT_CHAIN_VERDICT,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.position_observation_freshness_contract_v1 import (
    POSITION_OBSERVATION_FRESHNESS_MAX_AGE_MS,
    default_local_monotonic_ms_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_submit_state_v1 import (
    TARGET_POSITION_NONZERO_PROVEN,
    TARGET_POSITION_NOT_OBSERVED,
    TARGET_POSITION_UNKNOWN,
    TARGET_POSITION_ZERO_PROVEN,
    classify_target_position_state_v1,
)

OWNER_GO = (
    "PEAK_TRADE_OWNER_GO_SECTION_11_13_5_PREREQUISITE_08_FRESH_POSITION_OBSERVATION_CLUSTER_V1"
)
THIS_WINDOW_OWNER_GO = (
    "PEAK_TRADE_OWNER_GO_SECTION_11_13_5_PREREQUISITE_08_SINGLE_UNFILTERED_POSITION_OBSERVATION_V1"
)
POST_Z2CY_WINDOW_OWNER_GO = "PEAK_TRADE_OWNER_GO_PREREQUISITE_08_SINGLE_UNFILTERED_POSITIONS_GET_V1"
AUTHORIZED_OBSERVATION_OWNER_GOS = frozenset(
    {OWNER_GO, THIS_WINDOW_OWNER_GO, POST_Z2CY_WINDOW_OWNER_GO}
)
Z2CR_SNAPSHOT_DOCUMENT_CLASS = (
    "SECTION_11_13_5_Z2CR_FRESH_UNFILTERED_TARGET_POSITION_GET_SNAPSHOT_V1"
)
Z2CR_ADJUDICATION_DOCUMENT_CLASS = "SECTION_11_13_5_Z2CR_PREREQUISITE_08_WINDOW_ADJUDICATION_V1"
Z2CT_SNAPSHOT_DOCUMENT_CLASS = (
    "SECTION_11_13_5_Z2CT_FRESH_UNFILTERED_TARGET_POSITION_GET_SNAPSHOT_V1"
)
Z2CT_ADJUDICATION_DOCUMENT_CLASS = "SECTION_11_13_5_Z2CT_PREREQUISITE_08_WINDOW_ADJUDICATION_V1"
Z2CZ_SNAPSHOT_DOCUMENT_CLASS = (
    "SECTION_11_13_5_Z2CZ_FRESH_UNFILTERED_TARGET_POSITION_GET_SNAPSHOT_V1"
)
Z2CZ_ADJUDICATION_DOCUMENT_CLASS = "SECTION_11_13_5_Z2CZ_PREREQUISITE_08_WINDOW_ADJUDICATION_V1"
SHADOW_RECON_SECRETREF = "secretref://vault/peak-trade/live-shadow-recon/okx"
SHADOW_RECON_CREDENTIAL_CLASS = "LIVE_SHADOW_RECONCILIATION_READ_ONLY_API_KEY"
PRODUCTION_REST_BASE = f"https://{REUSED_BINDING_REST_HOST}"
SAFE_RESPONSE_HEADER_ALLOWLIST = frozenset({"content-type", "date", "server"})
FORBIDDEN_HEADER_NAME_MARKERS = (
    "authorization",
    "ok-access",
    "cookie",
    "api-key",
    "secret",
    "sign",
    "passphrase",
)
ROW_FIELD_ALLOWLIST = frozenset(
    {
        "adl",
        "availPos",
        "avgPx",
        "baseBal",
        "bePx",
        "bizRefId",
        "bizRefType",
        "cTime",
        "ccy",
        "imr",
        "idxPx",
        "instFamily",
        "instId",
        "instType",
        "last",
        "lever",
        "liqPx",
        "markPx",
        "margin",
        "mgnMode",
        "mmr",
        "notionalUsd",
        "pos",
        "posCcy",
        "posId",
        "posSide",
        "posSize",
        "quoteBal",
        "realizedPnl",
        "uTime",
        "upl",
        "usdPx",
    }
)
EVIDENCE_DIRNAME = "section_11_13_5_z2cr_prerequisite_08_fresh_position_observation_v1"


def _document_classes_for_owner_go(owned: str) -> tuple[str, str]:
    if owned == POST_Z2CY_WINDOW_OWNER_GO:
        return Z2CZ_SNAPSHOT_DOCUMENT_CLASS, Z2CZ_ADJUDICATION_DOCUMENT_CLASS
    if owned == THIS_WINDOW_OWNER_GO:
        return Z2CT_SNAPSHOT_DOCUMENT_CLASS, Z2CT_ADJUDICATION_DOCUMENT_CLASS
    return Z2CR_SNAPSHOT_DOCUMENT_CLASS, Z2CR_ADJUDICATION_DOCUMENT_CLASS


class LiveCanaryPrerequisite08FreshObservationError(RuntimeError):
    """Fail-closed prerequisite-08 observation violation."""


class ProvenanceUrllibLiveTransportV1:
    """GET-only urllib transport that records safe response header names/values."""

    transport_class = TRANSPORT_CLASS_LIVE_PRODUCTIVE_HTTP
    venue_live_contact = True
    allows_productive_proven = True

    def __init__(self) -> None:
        self.safe_response_headers: dict[str, str] = {}
        self.received_monotonic_ms: int | None = None

    def send(self, request: LiveShadowReconHttpRequestV1) -> LiveShadowReconHttpResponseV1:
        if request.method != "GET":
            raise LiveShadowReconHttpError("URLLIB_TRANSPORT_GET_ONLY")
        req = Request(request.url, method="GET", headers=dict(request.headers))
        started = default_local_monotonic_ms_v1()
        try:
            with urlopen(req, timeout=request.timeout_seconds) as resp:  # noqa: S310
                body = resp.read()
                status = int(getattr(resp, "status", 200))
                self.safe_response_headers = _safe_headers(dict(resp.headers.items()))
        except HTTPError as exc:
            body = exc.read() if hasattr(exc, "read") else b""
            status = int(exc.code)
            headers = getattr(exc, "headers", None)
            self.safe_response_headers = _safe_headers(dict(headers.items()) if headers else {})
        self.received_monotonic_ms = default_local_monotonic_ms_v1()
        elapsed = (self.received_monotonic_ms - started) / 1000.0
        return LiveShadowReconHttpResponseV1(
            status_code=status,
            body_bytes=body,
            elapsed_seconds=elapsed,
            endpoint=request.endpoint,
            method="GET",
        )


def _safe_headers(headers: Mapping[str, str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for key, value in dict(headers).items():
        lowered = str(key).strip().lower()
        if any(marker in lowered for marker in FORBIDDEN_HEADER_NAME_MARKERS):
            continue
        if lowered in SAFE_RESPONSE_HEADER_ALLOWLIST:
            out[str(key)] = str(value)
    return out


def utc_now_iso_v1() -> str:
    return datetime.now(timezone.utc).isoformat()


def sanitize_position_row_v1(row: Mapping[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in dict(row).items():
        name = str(key)
        lowered = name.lower()
        if any(marker in lowered for marker in ("uid", "api_key", "secret", "passphrase", "token")):
            out[name] = "<REDACTED>"
            continue
        if name not in ROW_FIELD_ALLOWLIST:
            continue
        out[name] = value
    return out


def sanitize_positions_payload_v1(payload: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if payload is None:
        return None
    data = payload.get("data")
    rows: list[Any] = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, Mapping):
                rows.append(sanitize_position_row_v1(item))
            else:
                rows.append("<NON_OBJECT_ROW>")
        sanitized_data: Any = rows
    else:
        sanitized_data = data
    return {
        "code": payload.get("code"),
        "data": sanitized_data,
        "msg": payload.get("msg"),
    }


def closeout_position_state_v1(classifier_state: str) -> str:
    if classifier_state == TARGET_POSITION_NONZERO_PROVEN:
        return "NONZERO"
    if classifier_state == TARGET_POSITION_ZERO_PROVEN:
        return "ZERO"
    if classifier_state == TARGET_POSITION_NOT_OBSERVED:
        return "NOT_OBSERVED"
    return "UNADJUDICATED"


def qty_numeric_status_v1(*, classifier_state: str, signed_pos: str | None) -> str:
    if classifier_state in {TARGET_POSITION_NOT_OBSERVED, TARGET_POSITION_UNKNOWN}:
        return "UNRESOLVED"
    if signed_pos is None:
        return "UNRESOLVED"
    try:
        Decimal(str(signed_pos))
    except (InvalidOperation, TypeError, ValueError):
        return "FAIL"
    return "PASS"


def evaluate_freshness_at_adjudication_v1(
    *,
    response_received_monotonic_ms: int | None,
    adjudication_monotonic_ms: int | None,
) -> dict[str, Any]:
    if response_received_monotonic_ms is None or adjudication_monotonic_ms is None:
        return {
            "FRESHNESS_STATUS": "NOT_EVALUABLE",
            "OBSERVATION_AGE_AT_ADJUDICATION_MS": None,
            "FRESHNESS_REJECT_REASON": "FRESHNESS_UNKNOWN",
        }
    age_ms = int(adjudication_monotonic_ms) - int(response_received_monotonic_ms)
    if age_ms < 0:
        return {
            "FRESHNESS_STATUS": "FAIL",
            "OBSERVATION_AGE_AT_ADJUDICATION_MS": age_ms,
            "FRESHNESS_REJECT_REASON": "NEGATIVE_AGE",
        }
    if age_ms > POSITION_OBSERVATION_FRESHNESS_MAX_AGE_MS:
        return {
            "FRESHNESS_STATUS": "FAIL",
            "OBSERVATION_AGE_AT_ADJUDICATION_MS": age_ms,
            "FRESHNESS_REJECT_REASON": "STALE_POSITION_OBSERVATION",
        }
    return {
        "FRESHNESS_STATUS": "PASS",
        "OBSERVATION_AGE_AT_ADJUDICATION_MS": age_ms,
        "FRESHNESS_REJECT_REASON": "",
    }


def adjudicate_prerequisite_08_window_v1(
    *,
    positions_payload: Mapping[str, Any] | None,
    instrument_id: str = DEFAULT_INSTRUMENT_ID,
    body_sha256: str | None = None,
) -> dict[str, Any]:
    """Read-only window adjudication. Not flatten authorization."""
    classified = classify_target_position_state_v1(
        positions_payload=positions_payload,
        instrument_id=instrument_id,
    )
    cluster = evaluate_execution_prerequisite_08_cluster_v1(
        positions_payload=positions_payload,
        instrument_id=instrument_id,
        claimed_body_sha256=body_sha256,
    )
    state = classified.state
    closeout_state = closeout_position_state_v1(state)
    qty_numeric = qty_numeric_status_v1(classifier_state=state, signed_pos=classified.signed_pos)
    target_row_observed = closeout_state in {"NONZERO", "ZERO"}
    if state == TARGET_POSITION_NONZERO_PROVEN:
        status_08 = "PASS_TARGET_POSITION_NONZERO_OBSERVED_THIS_WINDOW"
        earliest = (
            "EXECUTION_PREREQUISITE_25_NO_ADDITIONAL_OWNER_DECISION_REQUIRED"
            if qty_numeric == "PASS"
            else "EXECUTION_PREREQUISITE_09_TARGET_POSITION_QTY_NUMERIC"
        )
        status_09 = "PASS_QTY_NUMERIC_THIS_WINDOW" if qty_numeric == "PASS" else qty_numeric
        status_11 = (
            "PASS"
            if qty_numeric == "PASS"
            else "UNRESOLVED_DEPENDENT_ON_TARGET_POSITION_QTY_NUMERIC"
        )
        status_12 = (
            "PASS"
            if qty_numeric == "PASS"
            else "UNRESOLVED_DEPENDENT_ON_TARGET_POSITION_QTY_NUMERIC"
        )
    elif state == TARGET_POSITION_ZERO_PROVEN:
        status_08 = "UNRESOLVED_TARGET_ZERO_THIS_PAYLOAD"
        earliest = EARLIEST_UNRESOLVED_DEPENDENCY
        status_09 = "PASS_QTY_NUMERIC_ZERO_THIS_WINDOW" if qty_numeric == "PASS" else qty_numeric
        status_11 = "UNRESOLVED_DEPENDENT_ON_TARGET_POSITION_NONZERO"
        status_12 = "UNRESOLVED_DEPENDENT_ON_TARGET_POSITION_NONZERO"
    elif state == TARGET_POSITION_NOT_OBSERVED:
        status_08 = "UNRESOLVED_TARGET_NOT_OBSERVED_THIS_WINDOW"
        earliest = EARLIEST_UNRESOLVED_DEPENDENCY
        status_09 = REASON_DEPENDENT_BLOCKED
        status_11 = "UNRESOLVED_DEPENDENT_ON_TARGET_POSITION_NONZERO"
        status_12 = "UNRESOLVED_DEPENDENT_ON_TARGET_POSITION_NONZERO"
    else:
        status_08 = "UNRESOLVED_TARGET_UNKNOWN_THIS_PAYLOAD"
        earliest = EARLIEST_UNRESOLVED_DEPENDENCY
        status_09 = "UNRESOLVED"
        status_11 = "UNRESOLVED"
        status_12 = "UNRESOLVED"

    matching: list[dict[str, Any]] = []
    if isinstance(positions_payload, Mapping) and isinstance(positions_payload.get("data"), list):
        for item in positions_payload["data"]:
            if isinstance(item, Mapping) and str(item.get("instId") or "").strip() == instrument_id:
                matching.append(sanitize_position_row_v1(item))

    return {
        "instrument_id": classified.instrument_id,
        "classifier_state": classified.state,
        "classifier_reason": classified.reason,
        "signed_pos": classified.signed_pos,
        "TARGET_ROW_OBSERVED": target_row_observed,
        "TARGET_POSITION_STATE": closeout_state,
        "TARGET_POSITION_QTY_RAW": classified.signed_pos,
        "TARGET_POSITION_QTY_NUMERIC": qty_numeric,
        "TARGET_POSITION_QTY_UNIT": TARGET_POSITION_QTY_UNIT_STATUS,
        "UNIT_CHAIN_VERDICT": UNIT_CHAIN_VERDICT,
        "TARGET_ROWS_MATCHED": len(matching),
        "TARGET_ROWS_SUMMARY": matching,
        "EXECUTION_PREREQUISITE_08_STATUS": status_08,
        "EXECUTION_PREREQUISITE_08_TARGET_POSITION_NONZERO_PROVEN": (
            state == TARGET_POSITION_NONZERO_PROVEN
        ),
        "EXECUTION_PREREQUISITE_09_STATUS": status_09,
        "EXECUTION_PREREQUISITE_11_STATUS": status_11,
        "EXECUTION_PREREQUISITE_12_STATUS": status_12,
        "EARLIEST_UNRESOLVED_DEPENDENCY": earliest,
        "cluster_offline_08_proven_token": cluster.prerequisite_08_proven,
        "cluster_offline_08_status": cluster.prerequisite_08_status,
        "CLASS_D_CONSUMED": CLASS_D_CONSUMED,
        "Z2AP_CONSUMED": Z2AP_CONSUMED,
        "EXECUTION_READY": EXECUTION_READY,
        "LIVE_FLATTEN_PROVABILITY": LIVE_FLATTEN_PROVABILITY,
        "SEND_TIME_PASS_18_19_21_24": SEND_TIME_PASS_18_19_21_24,
        "AUTHENTICATED_PRODUCTIVE_TRANSPORT_STATUS": AUTHENTICATED_PRODUCTIVE_TRANSPORT_STATUS,
        "FIXTURE_NONZERO_IS_NOT_PRODUCTIVE_08_PROOF": True,
        "OFFLINE_CLUSTER_PROVEN_TOKEN_IS_NOT_PRODUCTIVE_08_PROOF": True,
        "empty_data_is_zero": False,
        "HTTP_OK_DOES_NOT_PROVE_COMPLETENESS": True,
    }


def run_authorized_fresh_position_observation_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    vault_file: Path | str,
    evidence_root: Path,
) -> dict[str, Any]:
    """Perform exactly one unfiltered authenticated positions GET and persist evidence."""
    owned = str(owner_go or "").strip()
    if owned not in AUTHORIZED_OBSERVATION_OWNER_GOS:
        raise LiveCanaryPrerequisite08FreshObservationError("OWNER_GO_MISMATCH")
    snapshot_document_class, adjudication_document_class = _document_classes_for_owner_go(owned)
    query = build_account_positions_query_v1()
    if query.query or query.inst_id_filter_present or query.pos_id_filter_present:
        raise LiveCanaryPrerequisite08FreshObservationError("INSTID_FILTER_FORBIDDEN")
    endpoint = query.path_with_query()
    if endpoint != ENDPOINT_ACCOUNT_POSITIONS:
        raise LiveCanaryPrerequisite08FreshObservationError("ENDPOINT_MUST_BE_UNFILTERED_POSITIONS")

    binding = build_live_shadow_recon_venue_binding_v1(
        environment="LIVE",
        venue=REUSED_BINDING_VENUE,
        entity=REUSED_BINDING_ENTITY,
        region=REUSED_BINDING_REGION,
        rest_host=REUSED_BINDING_REST_HOST,
        rest_base=PRODUCTION_REST_BASE,
        account_scope=REUSED_BINDING_ACCOUNT_SCOPE,
        instrument_scope=None,
    )
    transport = ProvenanceUrllibLiveTransportV1()
    client = LiveShadowReconHttpClientV1(
        binding=binding,
        transport=transport,
        endpoint_allowlist=(ENDPOINT_ACCOUNT_POSITIONS,),
        max_request_count=1,
        max_retries=0,
        timeout_seconds=10.0,
    )
    backend = build_file_secretref_vault_backend_v1(vault_file=Path(vault_file))
    handle = resolve_and_load_live_secretref_ephemeral_v1(
        secret_reference=SHADOW_RECON_SECRETREF,
        vault_backend=backend,
        credential_class=SHADOW_RECON_CREDENTIAL_CLASS,
    )
    capture_started = utc_now_iso_v1()
    auth_headers: dict[str, str] = {}
    request_header_names: list[str] = []
    http_status: int | None = None
    body_bytes = b""
    elapsed_seconds: float | None = None
    okx_code: str | None = None
    payload: dict[str, Any] | None = None
    get_error: str | None = None
    authenticated_get_status = "NOT_PERFORMED"
    try:
        url = f"{PRODUCTION_REST_BASE}{endpoint}"
        auth_headers = build_okx_live_ro_get_auth_headers_v1(handle=handle, url=url)
        request_header_names = sorted(auth_headers)
        response = client.get(endpoint=endpoint, headers=auth_headers)
        http_status = int(response.status_code)
        body_bytes = bytes(response.body_bytes)
        elapsed_seconds = float(response.elapsed_seconds)
        authenticated_get_status = "HTTP_RESPONSE_RECEIVED"
    except LiveShadowReconHttpError as exc:
        get_error = str(exc)
        authenticated_get_status = "TRANSPORT_OR_CLIENT_FAIL"
    except (URLError, OSError, TimeoutError) as exc:
        get_error = f"{type(exc).__name__}:{exc}"
        authenticated_get_status = "TRANSPORT_OR_CLIENT_FAIL"
    finally:
        auth_headers.clear()
        release_live_ephemeral_material_v1(handle)
    capture_finished = utc_now_iso_v1()
    received_ms = transport.received_monotonic_ms
    if received_ms is None and authenticated_get_status == "HTTP_RESPONSE_RECEIVED":
        received_ms = default_local_monotonic_ms_v1()

    body_sha256 = hashlib.sha256(body_bytes).hexdigest() if body_bytes else None
    if body_bytes:
        try:
            parsed = json.loads(body_bytes.decode("utf-8"))
            if isinstance(parsed, dict):
                payload = parsed
                okx_code = str(parsed.get("code") or "")
        except (UnicodeDecodeError, json.JSONDecodeError):
            payload = None
            authenticated_get_status = "MALFORMED_BODY"

    if http_status in {401, 403}:
        authenticated_get_status = "AUTH_ERROR"
    elif http_status == 200 and okx_code == "0":
        authenticated_get_status = "SUCCESS"
    elif http_status == 200 and payload is not None:
        authenticated_get_status = "VENUE_ERROR"
    elif http_status is not None and authenticated_get_status == "HTTP_RESPONSE_RECEIVED":
        authenticated_get_status = "HTTP_ERROR"

    adjudication_ms = default_local_monotonic_ms_v1()
    freshness = evaluate_freshness_at_adjudication_v1(
        response_received_monotonic_ms=received_ms,
        adjudication_monotonic_ms=adjudication_ms,
    )
    adjudication = adjudicate_prerequisite_08_window_v1(
        positions_payload=payload,
        instrument_id=DEFAULT_INSTRUMENT_ID,
        body_sha256=body_sha256,
    )
    counters = client.counters.to_dict()
    data = payload.get("data") if isinstance(payload, Mapping) else None
    data_count: int | None
    data_shape: str
    if isinstance(data, list):
        data_count = len(data)
        data_shape = "DATA_LIST"
    elif data is None and payload is not None and "data" in payload:
        data_count = None
        data_shape = "DATA_NONE"
    elif payload is None:
        data_count = None
        data_shape = "NO_PARSEABLE_PAYLOAD"
    else:
        data_count = None
        data_shape = "DATA_NOT_LIST"

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    pack = Path(evidence_root) / run_id
    pack.mkdir(parents=True, exist_ok=False)
    snapshot = {
        "DOCUMENT_CLASS": snapshot_document_class,
        "DOCUMENT_ROLE": "RAW_SANITIZED_RUNTIME_EVIDENCE_NOT_SSOT",
        "AUTHORITY": "NONE",
        "SEMANTIC_AUTHORITY": False,
        "THIS_ARTIFACT_IS_NOT_CANONICAL": True,
        "SECRET_VALUES_INCLUDED": False,
        "UID_REDACTED": True,
        "OWNER_GO": owned,
        "bound_origin_main_sha": origin_main_sha,
        "HOST": REUSED_BINDING_REST_HOST,
        "VENUE": "OKX_EEA_PRODUCTION",
        "HTTP_METHOD": "GET",
        "ENDPOINT": endpoint,
        "QUERY_PARAMETERS": {},
        "INSTID_FILTER_USED": False,
        "CAPTURE_STARTED_AT": capture_started,
        "CAPTURE_FINISHED_AT": capture_finished,
        "OBSERVATION_TIMESTAMP_UTC": capture_finished,
        "LOCAL_RESPONSE_RECEIVED_AT": received_ms,
        "CLOCK_DOMAIN": "LOCAL_MONOTONIC_ELAPSED_TIME",
        "HTTP_STATUS": http_status,
        "OKX_CODE": okx_code,
        "OKX_MSG": str((payload or {}).get("msg") or "") if payload is not None else None,
        "AUTHENTICATED_GET_STATUS": authenticated_get_status,
        "GET_ERROR": get_error,
        "BODY_BYTES": len(body_bytes),
        "BODY_SHA256": body_sha256,
        "UNIQUE_WINDOW_IDENTITY_PRESERVED": True,
        "BYTE_IDENTICAL_EMPTY_ENVELOPE_SHA_ALSO_USED_BY_HISTORICAL_Z2CN": (
            body_sha256 == Z2CN_COMMITTED_BODY_SHA256 if body_sha256 else False
        ),
        "BYTE_IDENTICAL_EMPTY_ENVELOPE_SHA_DOES_NOT_MERGE_SOURCE_IDENTITIES": True,
        "RAW_DATA_SHAPE": data_shape,
        "DATA_COUNT": data_count,
        "TARGET_INSTRUMENT": DEFAULT_INSTRUMENT_ID,
        "SAFE_RESPONSE_HEADERS": transport.safe_response_headers,
        "AUTH_PATH": {
            "CREDENTIAL_CLASS": SHADOW_RECON_CREDENTIAL_CLASS,
            "HEADER_NAMES_ONLY": request_header_names,
            "HTTP_CLIENT": "LiveShadowReconHttpClientV1",
            "SECRETREF_URI": SHADOW_RECON_SECRETREF,
            "SIGNER": "build_okx_live_ro_get_auth_headers_v1",
            "TRANSPORT": "ProvenanceUrllibLiveTransportV1",
            "VAULT_BACKEND": "FileSecretRefVaultBackendV1",
        },
        "COUNTERS": counters,
        "GET_REQUEST_COUNT": counters.get("GET_REQUEST_COUNT", 0),
        "POST_COUNT": 0,
        "WRITE_REQUEST_COUNT": counters.get("WRITE_REQUEST_COUNT", 0),
        "REQUEST_ELAPSED_SECONDS": elapsed_seconds,
        "REDACTED_PAYLOAD": sanitize_positions_payload_v1(payload),
        "LIVE_AUTHORIZED": False,
        "TESTNET_AUTHORIZED": False,
        "CANARY_AUTHORIZED": False,
    }
    adjudication_doc = {
        "DOCUMENT_CLASS": adjudication_document_class,
        "DOCUMENT_ROLE": "INTERPRETATION_NOT_RAW_EVIDENCE_NOT_SSOT",
        "AUTHORITY": "NONE",
        "OWNER_GO": owned,
        "bound_origin_main_sha": origin_main_sha,
        "CLASSIFIER": "classify_target_position_state_v1",
        "FRESHNESS_POLICY_MAX_AGE_MS": POSITION_OBSERVATION_FRESHNESS_MAX_AGE_MS,
        "AGE_EVALUATION_POINT_THIS_WINDOW": "ADJUDICATION_AFTER_GET_NOT_FLATTEN_SEND",
        "FLATTEN_PRE_SEND_PERMIT_EVALUATED": False,
        "LOCAL_RESPONSE_RECEIVED_AT": received_ms,
        "ADJUDICATION_MONOTONIC_MS": adjudication_ms,
        **freshness,
        **adjudication,
        "AUTHENTICATED_GET_STATUS": authenticated_get_status,
        "HTTP_STATUS": http_status,
        "OKX_CODE": okx_code,
        "RAW_BODY_SHA256": body_sha256,
        "POSITION_QTY_UNIT_STATUS": "UNPROVEN",
        "BYTE_IDENTICAL_Z2CN_EMPTY_SHA": (
            body_sha256 == Z2CN_COMMITTED_BODY_SHA256 if body_sha256 else False
        ),
        "BYTE_IDENTICAL_Z2CN_EMPTY_SHA_DOES_NOT_MERGE_THIS_WINDOW": True,
        "CLASS_D_CONSUMED": False,
        "Z2AP_CONSUMED": False,
        "EXECUTION_READY": False,
        "LIVE_FLATTEN_PROVABILITY": "UNPROVEN",
        "SEND_TIME_PASS_18_19_21_24": "UNPROVEN",
        "POST_PERFORMED": False,
        "POSITION_MUTATION": False,
        "LIVE_TESTNET_CANARY": False,
        "SECRET_MUTATION": False,
    }
    assert_no_plaintext_in_payload_v1(snapshot)
    assert_no_plaintext_in_payload_v1(adjudication_doc)
    write_json_v1(pack / "GET_SNAPSHOT.sanitized.json", snapshot)
    write_json_v1(pack / "ADJUDICATION.json", adjudication_doc)
    write_manifest_v1(pack, ("GET_SNAPSHOT.sanitized.json", "ADJUDICATION.json"))
    verify = verify_manifest_v1(pack)
    if int(verify["MANIFEST_VERIFY_RC"]) != 0:
        raise LiveCanaryPrerequisite08FreshObservationError("MANIFEST_VERIFY_FAILED")
    return {
        "EVIDENCE_PACK": str(pack),
        "GET_PERFORMED": counters.get("GET_REQUEST_COUNT", 0) == 1
        or authenticated_get_status not in {"NOT_PERFORMED", "TRANSPORT_OR_CLIENT_FAIL"},
        "VENUE_API_CALLS": counters.get("GET_REQUEST_COUNT", 0),
        "POST_PERFORMED": False,
        "AUTHENTICATED_GET_STATUS": authenticated_get_status,
        "HTTP_STATUS": http_status,
        "OKX_CODE": okx_code,
        "RAW_BODY_SHA256": body_sha256,
        "LOCAL_RESPONSE_RECEIVED_AT": received_ms,
        **freshness,
        "TARGET_INSTRUMENT_ID": DEFAULT_INSTRUMENT_ID,
        **{
            k: adjudication[k]
            for k in (
                "TARGET_ROW_OBSERVED",
                "TARGET_POSITION_STATE",
                "TARGET_POSITION_QTY_RAW",
                "TARGET_POSITION_QTY_NUMERIC",
                "TARGET_POSITION_QTY_UNIT",
                "EXECUTION_PREREQUISITE_08_STATUS",
                "EXECUTION_PREREQUISITE_09_STATUS",
                "EARLIEST_UNRESOLVED_DEPENDENCY",
            )
        },
        "MANIFEST_VERIFY_RC": verify["MANIFEST_VERIFY_RC"],
        "GET_ERROR": get_error,
        "WRITE_REQUEST_COUNT": counters.get("WRITE_REQUEST_COUNT", 0),
    }
