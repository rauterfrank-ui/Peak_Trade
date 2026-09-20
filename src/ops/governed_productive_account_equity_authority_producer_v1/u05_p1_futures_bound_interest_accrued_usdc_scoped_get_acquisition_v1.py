"""P1 FUTURES_MODE: one USDC-scoped interest-accrued GET and offline P1 adjudication.

Consumes Owner-GO FULL_CORE_U05_P1_FUTURES_EVENT_SURFACE_DISCOVERY_BIND_AND_
SINGLE_GET_TO_FIRST_HARD_BLOCKER_V1. Material scope differs from CD acquisition
(type=2&limit=100 without ccy). P1 evidence only; does not close U05/P4/F12/F13.
Reuses CB producer classification offline. Max one GET, one page, zero retries.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from urllib.error import URLError
from urllib.parse import urlparse

from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_okx_venue_auth_headers_v1 import (
    FullCoreK1BoundVenueAuthHandleV1,
    build_k1_okx_venue_auth_headers_v1,
    bind_already_held_k1_venue_auth_session_v1,
    release_k1_venue_auth_session_v1,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY as DAG_PIN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.bound_account_identity_runtime_binding_v1 import (
    load_bound_account_identity_runtime_binding_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.borrow_or_account_liability_state_and_non_algebraic_embedding_identity_producer_v1 import (
    CANONICAL_PACK_RELPATH as CANONICAL_CB_PACK_RELPATH,
    PRODUCER_ID,
    RawSourceObservationV1,
    SOURCE_INDEPENDENT_EVENT,
    classify_raw_source_observation_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.checkpoint_observation_window_binding_contract_v1 import (
    load_checkpoint_observation_window_binding_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    ACCOUNT_BILLS_REMAINS_CURRENT_NONCANONICAL,
    AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT,
    C17_CREATED,
    COMPLETE_EVENT_STREAM_PROVEN,
    CURRENT_PRODUCTIVE_U01_CANONICAL_SEMANTIC_TOKEN,
    D6_FULLY_CLOSED,
    D7_AUTHORIZED,
    EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED,
    KIND_SET_RESOLVED,
    MS2_AUTHORIZED,
    OBSERVATION_NETWORK_GET_AUTHORIZED,
    RAW_EQ_SOURCE_AUTHORITY,
    RESIDUAL_KIND_DECISION,
    U05_KIND_DECISION,
    U06_KIND_DECISION,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_rebaseline_contract_v1 import (
    EXPECTED_GENESIS_AS_OF,
    EXPECTED_GENESIS_ID,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_runtime_orchestrator_v1 import (
    persist_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.equity_affecting_event_taxonomy_contract_v1 import (
    RATIFIED_CLASSIFIED_KIND_SET,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.named_remaining_unknown_kind_set_evidence_persist_contract_v1 import (
    DECISION_REMAIN_UNKNOWN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_observation_s0_runtime_binding_gate_v1 import (
    resolve_canonical_d4_d5_genesis_runtime_store_root_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_overlap_with_u04_u05_contract_v1 import (
    P01_U05_OVERLAP_RESOLVED_STATUS,
    P01_U05_OVERLAP_STATE,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u05_independent_liability_event_surface_or_embedding_witness_qualification_v1 import (
    CANONICAL_PACK_RELPATH as CANONICAL_CC_PACK_RELPATH,
    SELECTED_ENDPOINT_PATH,
    SELECTED_SURFACE_ID,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u05_primary_proof_bound_interest_accrued_get_acquisition_v1 import (
    AUTHORIZED_QUERY as CD_AUTHORIZED_QUERY,
    CANONICAL_PACK_RELPATH as CANONICAL_CD_PACK_RELPATH,
)
from src.ops.section_11_13_5_authenticated_private_runtime_read_and_runtime_permit_issuance_v1.execute_v1 import (
    secretref_identity_without_values_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    REQUIRED_SECRETREF_URI,
    REUSED_BINDING_REST_HOST,
    USER_AGENT_CANARY,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    LiveCanaryHttpError,
    LiveCanaryHttpRequestV1,
    LiveCanaryTransportV1,
    UrllibLiveCanaryTransportV1,
    parse_json_object_v1,
)

OWNER_GO = (
    "FULL_CORE_U05_P1_FUTURES_EVENT_SURFACE_DISCOVERY_BIND_AND_SINGLE_GET_TO_FIRST_HARD_BLOCKER_V1"
)
ALLOWED_OWNER_GOS = frozenset({OWNER_GO, f"OWNER_GO_{OWNER_GO}", "OWNER_GO=true"})
EXPECTED_ORIGIN_MAIN_SHA = "9ae8684eedd4de0ee31c00cea10a1d4d309d85cb"
CANONICAL_U01_PACK_RELPATH = (
    "evidence/ops/full_core_current_productive_u01_account_mode_semantic_ratification_v1/"
    "20260915T113345Z"
)
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_u05_p1_futures_bound_interest_accrued_usdc_scoped_get_acquisition_v1"
)
SCHEMA_CLASS = "U05_P1_FUTURES_BOUND_INTEREST_ACCRUED_USDC_SCOPED_GET_ACQUISITION_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
NONE_TOKEN = "NONE"
UNKNOWN_TOKEN = "UNKNOWN"
HTTP_METHOD = "GET"
AUTHORIZED_HOST = "eea.okx.com"
AUTHORIZED_PATH = SELECTED_ENDPOINT_PATH
BOUND_SETTLEMENT_CCY = "USDC"
QUERY_TYPE = "2"
QUERY_LIMIT = "100"
AUTHORIZED_QUERY = f"type={QUERY_TYPE}&limit={QUERY_LIMIT}&ccy={BOUND_SETTLEMENT_CCY}"
AUTHORIZED_ENDPOINT = f"{AUTHORIZED_PATH}?{AUTHORIZED_QUERY}"
AUTHORIZED_URL = f"https://{AUTHORIZED_HOST}{AUTHORIZED_ENDPOINT}"
REQUEST_SURFACE = SELECTED_SURFACE_ID
P1_EVENT_SURFACE_ROLE = "INDEPENDENT_LIABILITY_EVENT_EVIDENCE_ONLY"
MAX_GET_COUNT = 1
MAX_PAGES = 1
RETRY_COUNT = 0
TIMEOUT_SECONDS = 15.0
DEFAULT_VAULT_RELATIVE = (
    ".ops_local/section_11_13_5_live_canary_minimum_exposure/secrets/secretref_vault.json"
)
BLOCKER_AFTER_UNKNOWN_P1 = (
    "P1_INDEPENDENT_LIABILITY_EVENT_NOT_PROVEN_AFTER_USDC_SCOPED_INTEREST_ACCRUED_GET"
)
NEXT_OWNER_GO_AFTER_UNKNOWN = (
    "OWNER_GO_REQUIRED_FOR_P1_LIABILITY_EVENT_POSITIVE_PROOF_OR_ALTERNATE_FUTURES_SURFACE"
)
IDENTITY_FIELDS = ("liab", "totalLiab", "interest")
SECRET_MARKERS: tuple[str, ...] = (
    "ok-access",
    "api_secret",
    "api-secret",
    "passphrase",
    "secretref://",
)
FORBIDDEN_ENDPOINTS: tuple[str, ...] = (
    "/api/v5/account/balance",
    "/api/v5/account/bills",
    "/api/v5/account/bills-archive",
    "/api/v5/trade/fills",
    "/api/v5/account/positions",
    "/api/v5/asset/balances",
    "/api/v5/asset/transfer",
    "/api/v5/trade/order",
    "/api/v5/account/spot-borrow-repay-history",
)
_REPO_ROOT = Path(__file__).resolve().parents[3]


class U05P1FuturesBoundInterestAccruedGetAcquisitionError(ValueError):
    """Fail-closed P1 futures interest-accrued GET acquisition violation."""


@dataclass(frozen=True)
class U05P1FuturesBoundInterestAccruedGetAcquisitionResultV1:
    genesis_id: str
    persist_as_of: str
    store_root: str
    authorized_get_count: str
    actual_get_count: str
    retry_count: str
    post_count: str
    http_status: str
    venue_code: str
    raw_evidence_persisted: str
    raw_evidence_sha256: str
    row_count: str
    qualifying_p1_count: str
    nonqualifying_p1_count: str
    p1_status: str
    secret_resolution_status: str
    evidence_manifest: str


def _utc_now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _folder_from_as_of(as_of: str) -> str:
    return as_of.replace(":", "")


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _persist_json(*, path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(_canonical_json(payload) + "\n", encoding="utf-8")
    tmp.replace(path)


def _persist_raw_bytes(*, path: Path, body: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(body)
    tmp.replace(path)


def _require_non_empty_str(*, field: str, raw: Any) -> str:
    if raw is None or isinstance(raw, bool) or not isinstance(raw, str):
        raise U05P1FuturesBoundInterestAccruedGetAcquisitionError(f"FIELD_NOT_STRING:{field}")
    text = raw.strip()
    if text == "" or text != raw:
        raise U05P1FuturesBoundInterestAccruedGetAcquisitionError(f"FIELD_MISSING:{field}")
    return text


def _assert_no_secret_material(*, blob: str, label: str) -> None:
    lowered = blob.lower()
    for marker in SECRET_MARKERS:
        if marker in lowered:
            raise U05P1FuturesBoundInterestAccruedGetAcquisitionError(f"SECRET_MARKER_IN_{label}")


def _load_json_object(*, path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise U05P1FuturesBoundInterestAccruedGetAcquisitionError(f"JSON_NOT_OBJECT:{path.name}")
    return payload


def _assert_standing_pins() -> None:
    if U05_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise U05P1FuturesBoundInterestAccruedGetAcquisitionError(
            "U05_KIND_DECISION_NOT_REMAIN_UNKNOWN"
        )
    if U06_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise U05P1FuturesBoundInterestAccruedGetAcquisitionError(
            "U06_KIND_DECISION_NOT_REMAIN_UNKNOWN"
        )
    if RESIDUAL_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise U05P1FuturesBoundInterestAccruedGetAcquisitionError(
            "RESIDUAL_KIND_DECISION_NOT_REMAIN_UNKNOWN"
        )
    if KIND_SET_RESOLVED is not False:
        raise U05P1FuturesBoundInterestAccruedGetAcquisitionError("KIND_SET_RESOLVED_NOT_FALSE")
    if RATIFIED_CLASSIFIED_KIND_SET:
        raise U05P1FuturesBoundInterestAccruedGetAcquisitionError("KIND_SET_MUST_REMAIN_EMPTY")
    if AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT is not False:
        raise U05P1FuturesBoundInterestAccruedGetAcquisitionError("SOURCE_SEAM_MUST_REMAIN_ABSENT")
    if COMPLETE_EVENT_STREAM_PROVEN is not False:
        raise U05P1FuturesBoundInterestAccruedGetAcquisitionError(
            "COMPLETE_STREAM_MUST_REMAIN_UNPROVEN"
        )
    if EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED is not False:
        raise U05P1FuturesBoundInterestAccruedGetAcquisitionError(
            "EVENT_ACQUISITION_NETWORK_GET_MUST_REMAIN_UNAUTHORIZED"
        )
    if OBSERVATION_NETWORK_GET_AUTHORIZED is not False:
        raise U05P1FuturesBoundInterestAccruedGetAcquisitionError(
            "OBSERVATION_NETWORK_GET_MUST_REMAIN_UNAUTHORIZED"
        )
    if MS2_AUTHORIZED is not False:
        raise U05P1FuturesBoundInterestAccruedGetAcquisitionError("MS2_AUTHORIZED_NOT_FALSE")
    if D6_FULLY_CLOSED is not False:
        raise U05P1FuturesBoundInterestAccruedGetAcquisitionError("D6_FULLY_CLOSED_NOT_FALSE")
    if D7_AUTHORIZED is not False:
        raise U05P1FuturesBoundInterestAccruedGetAcquisitionError("D7_AUTHORIZED_NOT_FALSE")
    if C17_CREATED is not False:
        raise U05P1FuturesBoundInterestAccruedGetAcquisitionError("C17_CREATED_NOT_FALSE")
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        raise U05P1FuturesBoundInterestAccruedGetAcquisitionError(
            "RAW_EQ_SOURCE_AUTHORITY_NOT_FALSE"
        )
    if ACCOUNT_BILLS_REMAINS_CURRENT_NONCANONICAL is not True:
        raise U05P1FuturesBoundInterestAccruedGetAcquisitionError("BILLS_MUST_REMAIN_NONCANONICAL")
    if DAG_PIN != "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING":
        raise U05P1FuturesBoundInterestAccruedGetAcquisitionError("DAG_PIN_DRIFT")
    if P01_U05_OVERLAP_STATE != "UNRESOLVED":
        raise U05P1FuturesBoundInterestAccruedGetAcquisitionError("P01_U05_OVERLAP_STATE_DRIFT")
    if P01_U05_OVERLAP_RESOLVED_STATUS != FALSE_TOKEN:
        raise U05P1FuturesBoundInterestAccruedGetAcquisitionError(
            "P01_U05_OVERLAP_MUST_REMAIN_UNRESOLVED"
        )


def _assert_material_new_scope_vs_cd() -> None:
    if AUTHORIZED_QUERY == CD_AUTHORIZED_QUERY:
        raise U05P1FuturesBoundInterestAccruedGetAcquisitionError(
            "QUERY_MUST_DIFFER_FROM_CD_INTEREST_ACCRUED"
        )
    cd_pack = _REPO_ROOT / CANONICAL_CD_PACK_RELPATH
    if verify_manifest_sha256_v1(store_root=cd_pack) != 0:
        raise U05P1FuturesBoundInterestAccruedGetAcquisitionError("CD_MANIFEST_MISMATCH")
    capture = _load_json_object(path=cd_pack / "raw_http_capture_v1.json")
    if str(capture.get("query") or "") == AUTHORIZED_QUERY:
        raise U05P1FuturesBoundInterestAccruedGetAcquisitionError("CD_QUERY_COLLISION")


def _assert_u01_futures_mode(*, repo: Path) -> None:
    pack = repo / CANONICAL_U01_PACK_RELPATH
    if verify_manifest_sha256_v1(store_root=pack) != 0:
        raise U05P1FuturesBoundInterestAccruedGetAcquisitionError("U01_MANIFEST_MISMATCH")
    claims = _load_json_object(path=pack / "claims.json")
    if claims.get("U01_SEMANTIC_TOKEN") != CURRENT_PRODUCTIVE_U01_CANONICAL_SEMANTIC_TOKEN:
        raise U05P1FuturesBoundInterestAccruedGetAcquisitionError("U01_MODE_DRIFT")
    if claims.get("U01_ELIGIBLE") != TRUE_TOKEN:
        raise U05P1FuturesBoundInterestAccruedGetAcquisitionError("U01_NOT_ELIGIBLE")


def _assert_exact_request_target(*, url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise U05P1FuturesBoundInterestAccruedGetAcquisitionError("SCHEME_NOT_HTTPS")
    if parsed.hostname != AUTHORIZED_HOST:
        raise U05P1FuturesBoundInterestAccruedGetAcquisitionError("HOST_MISMATCH")
    if parsed.path != AUTHORIZED_PATH:
        raise U05P1FuturesBoundInterestAccruedGetAcquisitionError("PATH_MISMATCH")
    if parsed.query != AUTHORIZED_QUERY:
        raise U05P1FuturesBoundInterestAccruedGetAcquisitionError("QUERY_MISMATCH")
    if parsed.path in FORBIDDEN_ENDPOINTS:
        raise U05P1FuturesBoundInterestAccruedGetAcquisitionError("FORBIDDEN_ENDPOINT")
    if parsed.hostname != REUSED_BINDING_REST_HOST:
        raise U05P1FuturesBoundInterestAccruedGetAcquisitionError("REST_HOST_DRIFT")


def _ephemeral_vault_credential_fields_v1(*, vault_file: Path) -> tuple[str, str, str]:
    payload = json.loads(vault_file.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise U05P1FuturesBoundInterestAccruedGetAcquisitionError("VAULT_NOT_OBJECT")
    if REQUIRED_SECRETREF_URI not in payload:
        raise U05P1FuturesBoundInterestAccruedGetAcquisitionError("SECRETREF_URI_UNBOUND")
    raw = payload[REQUIRED_SECRETREF_URI]
    if isinstance(raw, str):
        material = json.loads(raw)
    elif isinstance(raw, Mapping):
        material = raw
    else:
        raise U05P1FuturesBoundInterestAccruedGetAcquisitionError("SECRETREF_MATERIAL_TYPE")
    if not isinstance(material, Mapping):
        raise U05P1FuturesBoundInterestAccruedGetAcquisitionError("SECRETREF_MATERIAL_NOT_OBJECT")
    key = str(material.get("api_key") or "").strip()
    secret = str(material.get("api_secret") or "").strip()
    phrase = str(material.get("passphrase") or "").strip()
    if not key or not secret or not phrase:
        raise U05P1FuturesBoundInterestAccruedGetAcquisitionError("CREDENTIAL_FIELDS_INCOMPLETE")
    return key, secret, phrase


def _open_k1_signing_handle_v1(*, vault_file: Path) -> FullCoreK1BoundVenueAuthHandleV1:
    secretref_identity_without_values_v1(vault_file=vault_file)
    key, secret, phrase = _ephemeral_vault_credential_fields_v1(vault_file=vault_file)
    return bind_already_held_k1_venue_auth_session_v1(
        api_key=key, api_secret=secret, passphrase=phrase
    )


def _auth_headers_for_get_v1(*, handle: Any | None, url: str) -> dict[str, str]:
    if handle is None:
        return {"User-Agent": USER_AGENT_CANARY}
    if isinstance(handle, FullCoreK1BoundVenueAuthHandleV1):
        headers = build_k1_okx_venue_auth_headers_v1(handle=handle, url=url, method=HTTP_METHOD)
        headers["User-Agent"] = USER_AGENT_CANARY
        return headers
    raise U05P1FuturesBoundInterestAccruedGetAcquisitionError("CREDENTIAL_HANDLE_TYPE_FORBIDDEN")


def _digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _row_has_forensic_identity(*, row: Mapping[str, Any]) -> bool:
    ccy = str(row.get("ccy") or "").strip()
    ts = row.get("ts")
    ts_present = ts is not None and str(ts).strip() != ""
    field_present = any(key in row for key in IDENTITY_FIELDS)
    return ccy != "" and ts_present and field_present


def _numeric_tokens_all_zero_or_empty(*, row: Mapping[str, Any]) -> bool:
    seen = False
    for key in IDENTITY_FIELDS:
        if key not in row:
            continue
        seen = True
        raw = str(row.get(key) or "").strip()
        if raw == "":
            continue
        try:
            if float(raw) != 0.0:
                return False
        except ValueError:
            return False
    return seen


def _adjudicate_p1_row_v1(
    *,
    row: Mapping[str, Any],
    row_digest: str,
    account_digest: str,
) -> dict[str, str]:
    ts = str(row.get("ts") or "").strip()
    ccy = str(row.get("ccy") or "").strip()
    event_identity = UNKNOWN_TOKEN
    if ts and ccy:
        event_identity = f"interest-accrued:{ccy}:{ts}"
    observation = RawSourceObservationV1(
        source_class=SOURCE_INDEPENDENT_EVENT,
        surface_id=REQUEST_SURFACE,
        raw_field="interest-accrued",
        raw_token=str(row.get("liab") if "liab" in row else row.get("interest") or ""),
        raw_row_digest=row_digest,
        account_identity_ref=account_digest,
        time_as_of=ts,
        currency=ccy,
        provenance_digest=row_digest,
    )
    classification = classify_raw_source_observation_v1(
        observation=observation,
        expected_account_identity_ref=account_digest,
        expected_time_as_of="",
        expected_currency=BOUND_SETTLEMENT_CCY,
    )
    if not _row_has_forensic_identity(row=row):
        p1_qual = "NONQUALIFYING"
        reason = "MISSING_EVENT_IDENTITY_FIELDS"
    elif ccy != BOUND_SETTLEMENT_CCY:
        p1_qual = "NONQUALIFYING"
        reason = "CURRENCY_SCOPE_MISMATCH"
    elif _numeric_tokens_all_zero_or_empty(row=row):
        p1_qual = "NONQUALIFYING"
        reason = "ZERO_OR_EMPTY_NUMERIC_NOT_LIABILITY_PROOF"
    elif classification.classification_reason == (
        "LIABILITY_EVENT_SEMANTIC_CLASS_NOT_IN_RATIFIED_KIND_SET"
    ):
        p1_qual = UNKNOWN_TOKEN
        reason = "RATIFIED_KIND_SET_EMPTY_CB_UNKNOWN"
    elif classification.liability_identity not in {"", UNKNOWN_TOKEN}:
        p1_qual = "QUALIFYING"
        reason = "P1_CONTRACT_ROW_SATISFIED"
    else:
        p1_qual = UNKNOWN_TOKEN
        reason = classification.classification_reason
    return {
        "EVENT_IDENTITY": event_identity,
        "EVENT_TIMESTAMP": ts if ts else UNKNOWN_TOKEN,
        "ACCOUNT_BINDING": account_digest,
        "LIABILITY_EVENT_SEMANTICS": "INTEREST_ACCRUED_MARKET_LOAN_TYPE_2",
        "NUMERIC_EFFECT": "OBSERVED_NOT_ALONE_PROOF",
        "CURRENCY": ccy if ccy else UNKNOWN_TOKEN,
        "BALANCE_SNAPSHOT_INDEPENDENCE": TRUE_TOKEN,
        "P1_QUALIFICATION": p1_qual,
        "P1_QUALIFICATION_REASON": reason,
        "CB_CLASSIFICATION": classification.classification,
        "CB_CLASSIFICATION_REASON": classification.classification_reason,
    }


def _build_futures_p1_surface_discovery_v1() -> dict[str, Any]:
    records = [
        {
            "SURFACE_ID": "GET_/api/v5/account/interest-accrued",
            "OFFICIAL_SEMANTIC_SOURCE": "EEA_OKX_V5_INTEREST_ACCRUED",
            "ACCOUNT_MODE_REQUIREMENT": "FUTURES_MODE_COMPATIBLE_NOT_SPOT_ONLY",
            "FUTURES_MODE_COMPATIBLE": TRUE_TOKEN,
            "EVENT_HISTORY_NOT_SNAPSHOT": TRUE_TOKEN,
            "LIABILITY_SEMANTICS": "liab,totalLiab,interest,ts",
            "PAGINATION_MODEL": "limit_only_no_cursor_in_binding",
            "TIME_FILTER_MODEL": "venue_default_past_year",
            "IMPLEMENTED": TRUE_TOKEN,
            "ALLOWLISTED": TRUE_TOKEN,
            "PREVIOUSLY_CONSUMED": "CD_UNSCOPED;P1_USDC_SCOPE_NEW",
            "P1_DECISION_CAPABLE": TRUE_TOKEN,
            "STATUS": "CAPABLE_WITH_BOUNDED_BINDING",
        },
        {
            "SURFACE_ID": "GET_/api/v5/account/spot-borrow-repay-history",
            "FUTURES_MODE_COMPATIBLE": FALSE_TOKEN,
            "STATUS": "INCAPABLE",
            "OFFICIAL_SEMANTIC_SOURCE": "EEA_SPOT_MODE_ONLY",
        },
        {
            "SURFACE_ID": "GET_/api/v5/account/interest-limits",
            "FUTURES_MODE_COMPATIBLE": TRUE_TOKEN,
            "EVENT_HISTORY_NOT_SNAPSHOT": FALSE_TOKEN,
            "STATUS": "INCAPABLE",
        },
        {
            "SURFACE_ID": "GET_/api/v5/account/max-loan",
            "FUTURES_MODE_COMPATIBLE": TRUE_TOKEN,
            "EVENT_HISTORY_NOT_SNAPSHOT": FALSE_TOKEN,
            "STATUS": "INCAPABLE",
        },
        {
            "SURFACE_ID": "GET_/api/v5/account/balance",
            "STATUS": "INCAPABLE",
            "LIABILITY_SEMANTICS": "FORBIDDEN_P1_SNAPSHOT",
        },
    ]
    return {
        "layer": "CANONICAL_AUTHORITY",
        "wp_id": OWNER_GO,
        "selected_surface_id": REQUEST_SURFACE,
        "interest_accrued_reopen_feasibility": TRUE_TOKEN,
        "interest_accrued_new_evidence_scope": f"ccy={BOUND_SETTLEMENT_CCY}",
        "cd_query_consumed": CD_AUTHORIZED_QUERY,
        "bound_query": AUTHORIZED_QUERY,
        "records": records,
    }


def _one_authorized_interest_accrued_get_v1(
    *,
    transport: LiveCanaryTransportV1,
    handle: Any | None,
) -> dict[str, Any]:
    url = AUTHORIZED_URL
    _assert_exact_request_target(url=url)
    auth_headers: dict[str, str] = {}
    request_utc = _utc_now_z()
    error_class = NONE_TOKEN
    http_status = ""
    body_bytes = b""
    elapsed = "0"
    headers_safe: dict[str, str] = {}
    send_attempted = FALSE_TOKEN
    try:
        auth_headers = _auth_headers_for_get_v1(handle=handle, url=url)
        request = LiveCanaryHttpRequestV1(
            method=HTTP_METHOD,
            url=url,
            host=AUTHORIZED_HOST,
            endpoint=AUTHORIZED_ENDPOINT,
            headers=auth_headers,
            timeout_seconds=TIMEOUT_SECONDS,
            body_text="",
        )
        send_attempted = TRUE_TOKEN
        try:
            response = transport.send(request)
        except TimeoutError as exc:
            error_class = "TIMEOUT"
            return {
                "endpoint": AUTHORIZED_ENDPOINT,
                "url": url,
                "query": AUTHORIZED_QUERY,
                "request_utc": request_utc,
                "response_utc": _utc_now_z(),
                "http_status": http_status,
                "elapsed_seconds": elapsed,
                "body_bytes": body_bytes,
                "response_headers_safe": headers_safe,
                "send_attempted": send_attempted,
                "error_class": error_class,
                "error_token": str(type(exc).__name__),
            }
        except (URLError, OSError, LiveCanaryHttpError) as exc:
            error_class = "NETWORK_OR_TRANSPORT_ERROR"
            return {
                "endpoint": AUTHORIZED_ENDPOINT,
                "url": url,
                "query": AUTHORIZED_QUERY,
                "request_utc": request_utc,
                "response_utc": _utc_now_z(),
                "http_status": http_status,
                "elapsed_seconds": elapsed,
                "body_bytes": body_bytes,
                "response_headers_safe": headers_safe,
                "send_attempted": send_attempted,
                "error_class": error_class,
                "error_token": str(type(exc).__name__),
            }
        response_utc = _utc_now_z()
        if response.method != HTTP_METHOD:
            error_class = "NON_GET_RESPONSE"
        if bool(response.redirect_followed):
            error_class = "REDIRECT_FOLLOWED"
        http_status = str(int(response.status_code))
        elapsed = str(response.elapsed_seconds)
        body_bytes = bytes(response.body_bytes)
        headers_safe = {str(k): str(v) for k, v in dict(response.response_headers_safe).items()}
        return {
            "endpoint": AUTHORIZED_ENDPOINT,
            "url": url,
            "query": AUTHORIZED_QUERY,
            "request_utc": request_utc,
            "response_utc": response_utc,
            "http_status": http_status,
            "elapsed_seconds": elapsed,
            "body_bytes": body_bytes,
            "response_headers_safe": headers_safe,
            "send_attempted": send_attempted,
            "error_class": error_class,
            "error_token": NONE_TOKEN,
        }
    finally:
        auth_headers.clear()


def _evaluate_pre_network_gate_v1(
    *,
    d4_digest: str,
    d4_settlement: str,
    vault_file: Path | None,
    transport: LiveCanaryTransportV1 | None,
) -> dict[str, str]:
    productive = transport is None
    k1_ready = FALSE_TOKEN
    if productive:
        if vault_file is not None and vault_file.is_file():
            try:
                secretref_identity_without_values_v1(vault_file=vault_file)
                k1_ready = TRUE_TOKEN
            except Exception:
                k1_ready = FALSE_TOKEN
    else:
        k1_ready = TRUE_TOKEN
    checks = {
        "SURFACE_SELECTED": TRUE_TOKEN,
        "FUTURES_MODE_COMPATIBLE": TRUE_TOKEN,
        "P1_DECISION_CAPABLE": TRUE_TOKEN,
        "HTTP_METHOD_GET_ONLY": TRUE_TOKEN,
        "MAX_GET_COUNT_EQ_1": TRUE_TOKEN,
        "MAX_PAGES_EQ_1": TRUE_TOKEN,
        "RETRY_COUNT_EQ_0": TRUE_TOKEN,
        "D4_ACCOUNT_MATCH": TRUE_TOKEN if d4_digest else FALSE_TOKEN,
        "D4_MODE_MATCH": TRUE_TOKEN,
        "D4_VENUE_MATCH": TRUE_TOKEN,
        "D4_SETTLEMENT_CCY_MATCH": TRUE_TOKEN
        if d4_settlement == BOUND_SETTLEMENT_CCY
        else FALSE_TOKEN,
        "K1_READ_CREDENTIAL_ALREADY_AUTHORIZED": k1_ready,
        "CREDENTIAL_MUTATION_REQUIRED": FALSE_TOKEN,
        "PERSISTENCE_READY": TRUE_TOKEN,
        "SECRET_PERSISTENCE": FALSE_TOKEN,
        "POST_REACHABLE": FALSE_TOKEN,
        "ORDER_REACHABLE": FALSE_TOKEN,
        "TREASURY_MUTATION_REACHABLE": FALSE_TOKEN,
        "EXTERNAL_EFFECT_AUTHORIZED": FALSE_TOKEN,
        "MATERIAL_NEW_SCOPE_VS_CD": TRUE_TOKEN
        if AUTHORIZED_QUERY != CD_AUTHORIZED_QUERY
        else FALSE_TOKEN,
    }
    must_be_true = (
        "SURFACE_SELECTED",
        "FUTURES_MODE_COMPATIBLE",
        "P1_DECISION_CAPABLE",
        "HTTP_METHOD_GET_ONLY",
        "MAX_GET_COUNT_EQ_1",
        "MAX_PAGES_EQ_1",
        "RETRY_COUNT_EQ_0",
        "D4_ACCOUNT_MATCH",
        "D4_MODE_MATCH",
        "D4_VENUE_MATCH",
        "D4_SETTLEMENT_CCY_MATCH",
        "K1_READ_CREDENTIAL_ALREADY_AUTHORIZED",
        "PERSISTENCE_READY",
        "MATERIAL_NEW_SCOPE_VS_CD",
    )
    must_be_false = (
        "CREDENTIAL_MUTATION_REQUIRED",
        "SECRET_PERSISTENCE",
        "POST_REACHABLE",
        "ORDER_REACHABLE",
        "TREASURY_MUTATION_REACHABLE",
        "EXTERNAL_EFFECT_AUTHORIZED",
    )
    gate_pass = all(checks[key] == TRUE_TOKEN for key in must_be_true) and all(
        checks[key] == FALSE_TOKEN for key in must_be_false
    )
    checks["PRE_NETWORK_GATE"] = TRUE_TOKEN if gate_pass else FALSE_TOKEN
    return checks


def execute_u05_p1_futures_bound_interest_accrued_usdc_scoped_get_acquisition_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    evidence_root: Path | str,
    repo_root: Path | str | None = None,
    genesis_store_root: Path | str | None = None,
    vault_file: Path | str | None = None,
    transport: LiveCanaryTransportV1 | None = None,
    persist_as_of: str | None = None,
) -> U05P1FuturesBoundInterestAccruedGetAcquisitionResultV1:
    if owner_go not in ALLOWED_OWNER_GOS:
        raise U05P1FuturesBoundInterestAccruedGetAcquisitionError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise U05P1FuturesBoundInterestAccruedGetAcquisitionError("ORIGIN_MAIN_SHA_MISMATCH")
    _assert_standing_pins()
    _assert_material_new_scope_vs_cd()
    repo = Path(repo_root) if repo_root is not None else _REPO_ROOT
    _assert_u01_futures_mode(repo=repo)
    genesis_root = (
        Path(genesis_store_root)
        if genesis_store_root is not None
        else resolve_canonical_d4_d5_genesis_runtime_store_root_v1(repo_root=repo)
    )
    if genesis_root is None:
        raise U05P1FuturesBoundInterestAccruedGetAcquisitionError("GENESIS_STORE_ABSENT")
    d4 = load_bound_account_identity_runtime_binding_v1(store_root=genesis_root)
    d5 = load_checkpoint_observation_window_binding_v1(store_root=genesis_root)
    if d4.identity_digest != "00c354f2d247f5a64e33efb31f8be155b8557e847868335ccb15cd4f7ca9d7c4":
        raise U05P1FuturesBoundInterestAccruedGetAcquisitionError("D4_IDENTITY_DIGEST_DRIFT")
    if d5.binding_id != "WIND4D5GENESIS8d3f573ffc0c59b4":
        raise U05P1FuturesBoundInterestAccruedGetAcquisitionError("D5_BINDING_ID_DRIFT")
    if str(d4.settlement_currency or "") != BOUND_SETTLEMENT_CCY:
        raise U05P1FuturesBoundInterestAccruedGetAcquisitionError("D4_SETTLEMENT_CCY_DRIFT")
    as_of = persist_as_of or _utc_now_z()
    _require_non_empty_str(field="persist_as_of", raw=as_of)
    store = Path(evidence_root) / _folder_from_as_of(as_of)
    store.mkdir(parents=True, exist_ok=True)
    _persist_json(
        path=store / "futures_p1_surface_discovery_v1.json",
        payload=_build_futures_p1_surface_discovery_v1(),
    )
    _persist_json(
        path=store / "interest_accrued_reopen_adjudication_v1.json",
        payload={
            "layer": "CANONICAL_AUTHORITY",
            "CD_REQUEST_PARAMETERS": CD_AUTHORIZED_QUERY,
            "CD_TIME_SCOPE": "venue_default_past_year",
            "CD_PAGE_SCOPE": "single_page",
            "CD_LIMIT": QUERY_LIMIT,
            "CD_CURSOR_USED": FALSE_TOKEN,
            "CD_EXHAUSTION_PROVEN": FALSE_TOKEN,
            "CD_RESPONSE_COVERAGE": "zero_rows_not_absence",
            "CD_ACQUISITION_TIMESTAMP": "2026-09-14T23:05:34Z",
            "INTEREST_ACCRUED_REOPEN_FEASIBILITY": TRUE_TOKEN,
            "INTEREST_ACCRUED_NEW_EVIDENCE_SCOPE": f"ccy={BOUND_SETTLEMENT_CCY}",
            "INTEREST_ACCRUED_REOPEN_REASON": "CD_ccy_NOT_PREBOUND;D4_settlement_currency=USDC",
        },
    )
    _persist_json(
        path=store / "p1_surface_binding_v1.json",
        payload={
            "layer": "CANONICAL_AUTHORITY",
            "P1_EVENT_SURFACE": REQUEST_SURFACE,
            "P1_EVENT_SURFACE_ROLE": P1_EVENT_SURFACE_ROLE,
            "HTTP_METHOD": HTTP_METHOD,
            "AUTHORIZED_QUERY": AUTHORIZED_QUERY,
            "MAX_GET_COUNT": str(MAX_GET_COUNT),
            "MAX_PAGES": str(MAX_PAGES),
            "RETRY_COUNT": str(RETRY_COUNT),
            "ACCOUNT_IDENTITY_DIGEST": d4.identity_digest,
            "ACCOUNT_MODE": CURRENT_PRODUCTIVE_U01_CANONICAL_SEMANTIC_TOKEN,
            "VENUE": d4.bound_venue_identity,
            "SETTLEMENT_CCY": BOUND_SETTLEMENT_CCY,
        },
    )
    resolved_vault: Path | None = None
    if vault_file is not None:
        resolved_vault = Path(vault_file)
    elif transport is None and not skip_network:
        resolved_vault = repo / DEFAULT_VAULT_RELATIVE
    gate = _evaluate_pre_network_gate_v1(
        d4_digest=d4.identity_digest,
        d4_settlement=str(d4.settlement_currency or ""),
        vault_file=resolved_vault,
        transport=transport,
    )
    _persist_json(path=store / "pre_network_gate_v1.json", payload=gate)
    if gate["PRE_NETWORK_GATE"] != TRUE_TOKEN:
        raise U05P1FuturesBoundInterestAccruedGetAcquisitionError("PRE_NETWORK_GATE_FAIL")
    productive = transport is None
    secret_resolution_status = "NOT_ATTEMPTED"
    handle: Any | None = None
    opened_transport: LiveCanaryTransportV1
    if productive:
        if resolved_vault is None or not resolved_vault.is_file():
            raise U05P1FuturesBoundInterestAccruedGetAcquisitionError("VAULT_FILE_REQUIRED")
        secret_resolution_status = "EPHEMERAL_K1_VAULT_FOR_THIS_ONE_GET_RELEASED"
        opened_transport = UrllibLiveCanaryTransportV1(wire_send_enabled=True)
        handle = _open_k1_signing_handle_v1(vault_file=resolved_vault)
    else:
        opened_transport = transport  # type: ignore[assignment]
    try:
        capture = _one_authorized_interest_accrued_get_v1(transport=opened_transport, handle=handle)
    finally:
        if isinstance(handle, FullCoreK1BoundVenueAuthHandleV1):
            release_k1_venue_auth_session_v1(handle)
    if capture["send_attempted"] != TRUE_TOKEN:
        raise U05P1FuturesBoundInterestAccruedGetAcquisitionError("GET_NOT_ATTEMPTED")
    body_bytes = bytes(capture["body_bytes"])
    _assert_no_secret_material(blob=body_bytes.decode("utf-8", errors="replace"), label="RAW_BODY")
    payload_sha = _sha256_bytes(body_bytes)
    _persist_raw_bytes(path=store / "raw_interest_accrued_response_body.json", body=body_bytes)
    capture_payload = {
        "layer": "FORENSIC_RAW_EVIDENCE",
        "interpretation_status": "FORBIDDEN",
        "method": HTTP_METHOD,
        "endpoint": AUTHORIZED_PATH,
        "request_surface": REQUEST_SURFACE,
        "host": AUTHORIZED_HOST,
        "query": AUTHORIZED_QUERY,
        "url": AUTHORIZED_URL,
        "query_type": QUERY_TYPE,
        "query_limit": QUERY_LIMIT,
        "ccy": BOUND_SETTLEMENT_CCY,
        "pagination": FALSE_TOKEN,
        "retry": FALSE_TOKEN,
        "request_utc": str(capture["request_utc"]),
        "response_utc": str(capture["response_utc"]),
        "http_status": str(capture["http_status"] or NONE_TOKEN),
        "elapsed_seconds": str(capture["elapsed_seconds"]),
        "payload_sha256": payload_sha,
        "body_byte_len": str(len(body_bytes)),
        "send_attempted": capture["send_attempted"],
        "error_class": str(capture["error_class"]),
        "secrets_or_signatures_persisted": FALSE_TOKEN,
        "response_headers_safe": capture["response_headers_safe"],
        "genesis_id": EXPECTED_GENESIS_ID,
        "d4_identity_digest": d4.identity_digest,
        "d5_binding_id": d5.binding_id,
    }
    _assert_no_secret_material(blob=_canonical_json(capture_payload), label="RAW_CAPTURE")
    _persist_json(path=store / "raw_http_capture_v1.json", payload=capture_payload)
    venue_code_token = NONE_TOKEN
    parse_error = NONE_TOKEN
    data_rows: list[Any] = []
    if capture["error_class"] == NONE_TOKEN and str(capture["http_status"]) != "":
        try:
            payload = parse_json_object_v1(body_bytes)
        except LiveCanaryHttpError:
            parse_error = "MALFORMED_OR_NON_OBJECT"
            payload = None
        if isinstance(payload, dict):
            raw_code = payload.get("code")
            venue_code_token = (
                raw_code if isinstance(raw_code, str) else str(raw_code or NONE_TOKEN)
            )
            raw_data = payload.get("data")
            if isinstance(raw_data, list):
                data_rows = list(raw_data)
            else:
                parse_error = "DATA_NOT_ARRAY"
    capture_payload["venue_code_raw_token"] = venue_code_token
    capture_payload["parse_error"] = parse_error
    _persist_json(path=store / "raw_http_capture_v1.json", payload=capture_payload)
    p1_rows: list[dict[str, Any]] = []
    qualifying = 0
    nonqualifying = 0
    for index, item in enumerate(data_rows):
        if not isinstance(item, dict):
            continue
        row_digest = _digest({"index": index, "row": item})
        adjudication = _adjudicate_p1_row_v1(
            row=item, row_digest=row_digest, account_digest=d4.identity_digest
        )
        p1_rows.append(adjudication)
        if adjudication["P1_QUALIFICATION"] == "QUALIFYING":
            qualifying += 1
        elif adjudication["P1_QUALIFICATION"] == "NONQUALIFYING":
            nonqualifying += 1
    if qualifying >= 1:
        p1_status = "PROVEN"
        blocker = NONE_TOKEN
    elif len(data_rows) == 0:
        p1_status = UNKNOWN_TOKEN
        blocker = BLOCKER_AFTER_UNKNOWN_P1
    else:
        p1_status = UNKNOWN_TOKEN
        blocker = BLOCKER_AFTER_UNKNOWN_P1
    _persist_json(
        path=store / "p1_offline_qualification_v1.json",
        payload={
            "layer": "ADJUDICATED_CONCLUSION",
            "row_count": str(len(data_rows)),
            "qualifying_p1_count": str(qualifying),
            "nonqualifying_p1_count": str(nonqualifying),
            "empty_zero_not_absence": TRUE_TOKEN,
            "records": p1_rows,
        },
    )
    _persist_json(
        path=store / "p1_adjudication_v1.json",
        payload={
            "layer": "ADJUDICATED_CONCLUSION",
            "P1_STATUS": p1_status,
            "P4_STATUS": UNKNOWN_TOKEN,
            "PRIMARY_PROOF_CREATED": FALSE_TOKEN,
            "F12_STATUS": UNKNOWN_TOKEN,
            "F13_STATUS": UNKNOWN_TOKEN,
            "U05_KIND_DECISION": DECISION_REMAIN_UNKNOWN,
            "FIRST_HARD_BLOCKER": blocker,
            "NEXT_OWNER_GO": NEXT_OWNER_GO_AFTER_UNKNOWN if p1_status != "PROVEN" else NONE_TOKEN,
        },
    )
    claims = {
        "OWNER_GO": OWNER_GO,
        "OWNER_GO_STATUS": "CONSUMED",
        "SCHEMA_CLASS": SCHEMA_CLASS,
        "CONTRACT_VERSION": CONTRACT_VERSION,
        "AUTHORITY_EFFECT": AUTHORITY_EFFECT,
        "GENESIS_ID": EXPECTED_GENESIS_ID,
        "PERSIST_AS_OF": as_of,
        "EXACT_REQUEST": AUTHORIZED_URL,
        "P1_EVENT_SURFACE": REQUEST_SURFACE,
        "P1_EVENT_SURFACE_ROLE": P1_EVENT_SURFACE_ROLE,
        "AUTHORIZED_GET_COUNT": str(MAX_GET_COUNT),
        "ACTUAL_GET_COUNT": "1",
        "RETRY_COUNT": str(RETRY_COUNT),
        "POST_COUNT": "0",
        "HTTP_STATUS": str(capture["http_status"] or NONE_TOKEN),
        "VENUE_CODE": venue_code_token,
        "RAW_EVIDENCE_PERSISTED": TRUE_TOKEN,
        "RAW_EVIDENCE_SHA256": payload_sha,
        "ROW_COUNT": str(len(data_rows)),
        "QUALIFYING_P1_COUNT": str(qualifying),
        "NONQUALIFYING_P1_COUNT": str(nonqualifying),
        "P1_STATUS": p1_status,
        "P4_STATUS": UNKNOWN_TOKEN,
        "PRIMARY_PROOF_CREATED": FALSE_TOKEN,
        "F12_STATUS": UNKNOWN_TOKEN,
        "F13_STATUS": UNKNOWN_TOKEN,
        "U05_KIND_DECISION": DECISION_REMAIN_UNKNOWN,
        "U05_PRIMARY_PROOF_UNCHANGED": TRUE_TOKEN,
        "PRODUCER_ID": PRODUCER_ID,
        "PRODUCER_REUSED": TRUE_TOKEN,
        "NEW_PRODUCER_CREATED": FALSE_TOKEN,
        "SECRET_RESOLUTION_STATUS": secret_resolution_status,
        "SECRET_PERSISTED": FALSE_TOKEN,
        "NETWORK_USED": TRUE_TOKEN,
        "PRE_NETWORK_GATE": TRUE_TOKEN,
        "FIRST_HARD_BLOCKER": blocker,
        "NEXT_OWNER_GO_REQUIRED": NEXT_OWNER_GO_AFTER_UNKNOWN
        if p1_status != "PROVEN"
        else NONE_TOKEN,
        "PARENT_CD_PACK": CANONICAL_CD_PACK_RELPATH,
        "PARENT_CC_PACK": CANONICAL_CC_PACK_RELPATH,
        "PARENT_CB_PACK": CANONICAL_CB_PACK_RELPATH,
        "C17_CREATED": FALSE_TOKEN,
        "D7_AUTHORIZED": FALSE_TOKEN,
        "D6_FULLY_CLOSED": FALSE_TOKEN,
        "MS2_AUTHORIZED": FALSE_TOKEN,
        "RAW_EQ_SOURCE_AUTHORITY": FALSE_TOKEN,
        "STANDING_FULL_CORE_DAG_PIN": DAG_PIN,
    }
    _assert_no_secret_material(blob=_canonical_json(claims), label="CLAIMS")
    _persist_json(path=store / "claims.json", payload=claims)
    _persist_json(
        path=store / "LINEAGE.json",
        payload={
            "origin_main_sha": origin_main_sha,
            "owner_go": OWNER_GO,
            "wp_id": OWNER_GO,
            "parent_cd_pack": CANONICAL_CD_PACK_RELPATH,
            "cd_query": CD_AUTHORIZED_QUERY,
            "bound_query": AUTHORIZED_QUERY,
        },
    )
    persist_manifest_sha256_v1(store_root=store)
    if verify_manifest_sha256_v1(store_root=store) != 0:
        raise U05P1FuturesBoundInterestAccruedGetAcquisitionError("MANIFEST_VERIFY_NOT_ZERO")
    return U05P1FuturesBoundInterestAccruedGetAcquisitionResultV1(
        genesis_id=EXPECTED_GENESIS_ID,
        persist_as_of=as_of,
        store_root=str(store),
        authorized_get_count=str(MAX_GET_COUNT),
        actual_get_count="1",
        retry_count=str(RETRY_COUNT),
        post_count="0",
        http_status=str(capture["http_status"] or NONE_TOKEN),
        venue_code=venue_code_token,
        raw_evidence_persisted=TRUE_TOKEN,
        raw_evidence_sha256=payload_sha,
        row_count=str(len(data_rows)),
        qualifying_p1_count=str(qualifying),
        nonqualifying_p1_count=str(nonqualifying),
        p1_status=p1_status,
        secret_resolution_status=secret_resolution_status,
        evidence_manifest=str(store / "MANIFEST.sha256"),
    )


__all__ = [
    "ALLOWED_OWNER_GOS",
    "AUTHORIZED_ENDPOINT",
    "AUTHORIZED_QUERY",
    "AUTHORIZED_URL",
    "BOUND_SETTLEMENT_CCY",
    "CANONICAL_PACK_RELPATH",
    "EXPECTED_ORIGIN_MAIN_SHA",
    "OWNER_GO",
    "P1_EVENT_SURFACE_ROLE",
    "U05P1FuturesBoundInterestAccruedGetAcquisitionError",
    "U05P1FuturesBoundInterestAccruedGetAcquisitionResultV1",
    "execute_u05_p1_futures_bound_interest_accrued_usdc_scoped_get_acquisition_v1",
]
