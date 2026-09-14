"""Execute exactly one bound U05 interest-accrued GET and consume it.

Consumes Owner-GO
OWNER_GO_REQUIRED_TO_EXECUTE_EXACTLY_ONE_BOUND_U05_PRIMARY_PROOF_GET_OR_WITNESS_ACQUISITION_V1.
Reuses the existing productive vault, signer, and urllib transport. Does
not expand the canary GET allowlist. Does not retry. Does not paginate.
Does not POST. Does not acquire an embedding witness. Empty/zero/absent
remain UNKNOWN. GET alone may not INCLUDE or EXCLUDE. AUTHORITY_EFFECT=NONE.

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

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_ENABLED,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY as DAG_PIN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.bj_future_admissible_evidence_and_include_exclude_qualification_law_v1 import (
    CLASS_U05,
    OUTCOME_EXCLUDE,
    OUTCOME_INCLUDE,
    OUTCOME_NONQUALIFYING,
    evaluate_u05_primary_proof_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.bound_account_identity_runtime_binding_v1 import (
    load_bound_account_identity_runtime_binding_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.borrow_or_account_liability_state_and_non_algebraic_embedding_identity_producer_v1 import (
    CANONICAL_PACK_RELPATH as CANONICAL_CB_PACK_RELPATH,
    PRODUCER_ID,
    PRODUCER_STATUS,
    RawSourceObservationV1,
    SOURCE_INDEPENDENT_EVENT,
    assess_non_algebraic_embedding_identity_v1,
    build_borrow_or_account_liability_state_v1,
    classify_raw_source_observation_v1,
    evaluate_u05_eligibility_from_liability_state_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.checkpoint_observation_window_binding_contract_v1 import (
    load_checkpoint_observation_window_binding_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    ACCOUNT_BILLS_REMAINS_CURRENT_NONCANONICAL,
    AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT,
    C17_CREATED,
    COMPLETE_EVENT_STREAM_PROVEN,
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
from src.ops.governed_productive_account_equity_authority_producer_v1.f12_f13_primary_liability_stock_observation_v1 import (
    F12F13PrimaryLiabilityStockObservationError,
    _open_transport_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_today_initial_stock_anchor_v1 import (
    AUTHORIZED_ANCHOR_ID,
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
    NEXT_OWNER_GO as PARENT_CC_NEXT_OWNER_GO,
    SELECTED_ENDPOINT_PATH,
    SELECTED_SURFACE_ID,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    REUSED_BINDING_REST_HOST,
    USER_AGENT_CANARY,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    LiveCanaryHttpError,
    LiveCanaryHttpRequestV1,
    LiveCanaryTransportV1,
    parse_json_object_v1,
    safe_response_headers_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.live_credential_ephemeral_v1 import (
    release_live_canary_ephemeral_material_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.okx_live_canary_signer_v1 import (
    build_okx_live_canary_auth_headers_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.credential_presence_v1 import (
    default_vault_path_v1,
    inspect_credential_material_presence_v1,
)

OWNER_GO = (
    "OWNER_GO_REQUIRED_TO_EXECUTE_EXACTLY_ONE_BOUND_U05_PRIMARY_PROOF_GET_OR_WITNESS_ACQUISITION_V1"
)
EXPECTED_ORIGIN_MAIN_SHA = "d94b1d57e74b71bf161c915b54d7a90805901557"
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_u05_primary_proof_bound_interest_accrued_get_"
    "acquisition_v1/2026-09-15T010500Z"
)
CANONICAL_PERSIST_AS_OF = "2026-09-15T01:05:00Z"
SCHEMA_CLASS = "U05_PRIMARY_PROOF_BOUND_INTEREST_ACCRUED_GET_ACQUISITION_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
NONE_TOKEN = "NONE"
UNKNOWN_TOKEN = "UNKNOWN"
HTTP_METHOD = "GET"
AUTHORIZED_HOST = "eea.okx.com"
AUTHORIZED_PATH = "/api/v5/account/interest-accrued"
AUTHORIZED_QUERY = "type=2&limit=100"
AUTHORIZED_ENDPOINT = f"{AUTHORIZED_PATH}?{AUTHORIZED_QUERY}"
AUTHORIZED_URL = f"https://{AUTHORIZED_HOST}{AUTHORIZED_ENDPOINT}"
REQUEST_SURFACE = SELECTED_SURFACE_ID
QUERY_TYPE = "2"
QUERY_LIMIT = "100"
TIMEOUT_SECONDS = 15.0
PRIMARY_PROOF_ROLE = "INDEPENDENT_LIABILITY_EVENT_SURFACE_NOT_EMBEDDING_WITNESS"
PRIMARY_PROOF_STATUS = (
    "ACQUIRED_EVENT_SURFACE_GET_CONSUMED_EMBEDDING_WITNESS_UNBOUND_U05_REMAIN_UNKNOWN"
)
DECISION_BASIS = (
    "BOUND_INTEREST_ACCRUED_GET_CONSUMED_GET_ALONE_MAY_NOT_INCLUDE_OR_EXCLUDE_"
    "EMBEDDING_WITNESS_UNBOUND"
)
BLOCKER_ID = (
    "INDEPENDENT_NON_ALGEBRAIC_EMBEDDING_WITNESS_UNBOUND_AFTER_BOUND_INTEREST_ACCRUED_GET_CONSUMED"
)
ARCHITECTURE_BLOCKER = (
    "U05_STILL_REQUIRES_INDEPENDENT_NON_ALGEBRAIC_EMBEDDING_WITNESS_AFTER_INTEREST_ACCRUED_GET"
)
NEXT_OWNER_GO = (
    "OWNER_GO_REQUIRED_TO_SUPPLY_OR_AUTHORIZE_AN_INDEPENDENT_NON_ALGEBRAIC_"
    "EMBEDDING_WITNESS_NOT_VENUE_EQ_SOURCE_V1"
)
NEXT_ACTION = "STOP_AWAIT_OWNER_GO_FOR_INDEPENDENT_NON_ALGEBRAIC_EMBEDDING_WITNESS"
SECRET_RESOLUTION_EPHEMERAL = "EPHEMERAL_FOR_THIS_ONE_GET_RELEASED"
RAW_BODY_FILE = "raw_interest_accrued_response_body.json"
RAW_CAPTURE_FILE = "raw_http_capture_v1.json"
CLAIMS_FILE = "claims.json"
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
)
_REPO_ROOT = Path(__file__).resolve().parents[3]


class U05PrimaryProofBoundInterestAccruedGetAcquisitionError(ValueError):
    """Fail-closed bound interest-accrued GET acquisition violation."""


@dataclass(frozen=True)
class U05PrimaryProofBoundInterestAccruedGetAcquisitionResultV1:
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
    producer_executed: str
    qualifying_liability_rows: str
    independent_liability_event_proven: str
    non_algebraic_embedding_identity: str
    u05_decision_after: str
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
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError(f"FIELD_NOT_STRING:{field}")
    text = raw.strip()
    if text == "" or text != raw:
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError(f"FIELD_MISSING:{field}")
    return text


def _assert_no_secret_material(*, blob: str, label: str) -> None:
    lowered = blob.lower()
    for marker in SECRET_MARKERS:
        if marker in lowered:
            raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError(
                f"SECRET_MARKER_IN_{label}"
            )


def _load_json_object(*, path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError(f"JSON_NOT_OBJECT:{path.name}")
    return payload


def _assert_standing_pins() -> None:
    if LIVE_ENABLED is not False:
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError("LIVE_ENABLED_NOT_FALSE")
    if LIVE_ARMED is not False:
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError("LIVE_ARMED_NOT_FALSE")
    if WIRE_SEND_PERMITTED is not False:
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError(
            "WIRE_SEND_PERMITTED_NOT_FALSE"
        )
    if U05_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError(
            "U05_KIND_DECISION_NOT_REMAIN_UNKNOWN"
        )
    if U06_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError(
            "U06_KIND_DECISION_NOT_REMAIN_UNKNOWN"
        )
    if RESIDUAL_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError(
            "RESIDUAL_KIND_DECISION_NOT_REMAIN_UNKNOWN"
        )
    if KIND_SET_RESOLVED is not False:
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError("KIND_SET_RESOLVED_NOT_FALSE")
    if RATIFIED_CLASSIFIED_KIND_SET:
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError("KIND_SET_MUST_REMAIN_EMPTY")
    if AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT is not False:
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError(
            "SOURCE_SEAM_MUST_REMAIN_ABSENT"
        )
    if COMPLETE_EVENT_STREAM_PROVEN is not False:
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError(
            "COMPLETE_STREAM_MUST_REMAIN_UNPROVEN"
        )
    if EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED is not False:
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError(
            "EVENT_ACQUISITION_NETWORK_GET_MUST_REMAIN_UNAUTHORIZED"
        )
    if OBSERVATION_NETWORK_GET_AUTHORIZED is not False:
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError(
            "OBSERVATION_NETWORK_GET_MUST_REMAIN_UNAUTHORIZED"
        )
    if MS2_AUTHORIZED is not False:
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError("MS2_AUTHORIZED_NOT_FALSE")
    if D6_FULLY_CLOSED is not False:
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError("D6_FULLY_CLOSED_NOT_FALSE")
    if D7_AUTHORIZED is not False:
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError("D7_AUTHORIZED_NOT_FALSE")
    if C17_CREATED is not False:
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError("C17_CREATED_NOT_FALSE")
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError(
            "RAW_EQ_SOURCE_AUTHORITY_NOT_FALSE"
        )
    if ACCOUNT_BILLS_REMAINS_CURRENT_NONCANONICAL is not True:
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError(
            "BILLS_MUST_REMAIN_NONCANONICAL"
        )
    if DAG_PIN != "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING":
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError("DAG_PIN_DRIFT")
    if P01_U05_OVERLAP_STATE != "UNRESOLVED":
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError("P01_U05_OVERLAP_STATE_DRIFT")
    if P01_U05_OVERLAP_RESOLVED_STATUS != FALSE_TOKEN:
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError(
            "P01_U05_OVERLAP_MUST_REMAIN_UNRESOLVED"
        )


def _assert_parent_cc_pack(*, sealed_cc_pack: Path) -> None:
    if verify_manifest_sha256_v1(store_root=sealed_cc_pack) != 0:
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError("CC_MANIFEST_MISMATCH")
    claims = _load_json_object(path=sealed_cc_pack / CLAIMS_FILE)
    if claims.get("SELECTED_SINGLE_CANDIDATE_ID") != SELECTED_SURFACE_ID:
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError("CC_SELECTED_SURFACE_DRIFT")
    if claims.get("BOUND_ENDPOINT") != SELECTED_ENDPOINT_PATH:
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError("CC_BOUND_ENDPOINT_DRIFT")
    if claims.get("SURFACE_BINDING_STATUS") != "PRE_ACQUISITION_CONTRACT_BOUND":
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError(
            "CC_SURFACE_NOT_PRE_ACQUISITION_BOUND"
        )
    if claims.get("ACTUAL_GET_COUNT") != "0":
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError("CC_GET_COUNT_NOT_ZERO")
    if claims.get("POST_COUNT") != "0":
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError("CC_POST_COUNT_NOT_ZERO")
    if claims.get("NEXT_OWNER_GO_REQUIRED") != PARENT_CC_NEXT_OWNER_GO:
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError("CC_NEXT_OWNER_GO_DRIFT")
    if claims.get("PRIMARY_PROOF_ROLE_BOUND") != PRIMARY_PROOF_ROLE:
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError("CC_PRIMARY_PROOF_ROLE_DRIFT")
    contract = _load_json_object(path=sealed_cc_pack / "pre_acquisition_contract_v1.json")
    if contract.get("venue_host") != AUTHORIZED_HOST:
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError("CC_HOST_DRIFT")
    if contract.get("endpoint_path") != AUTHORIZED_PATH:
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError("CC_PATH_DRIFT")
    if contract.get("query_type") != QUERY_TYPE:
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError("CC_QUERY_TYPE_DRIFT")
    if contract.get("query_limit") != QUERY_LIMIT:
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError("CC_QUERY_LIMIT_DRIFT")
    if contract.get("http_method") != HTTP_METHOD:
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError("CC_HTTP_METHOD_DRIFT")


def _assert_exact_request_target(*, url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError("SCHEME_NOT_HTTPS")
    if parsed.hostname != AUTHORIZED_HOST:
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError("HOST_MISMATCH")
    if parsed.path != AUTHORIZED_PATH:
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError("PATH_MISMATCH")
    if parsed.query != AUTHORIZED_QUERY:
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError("QUERY_MISMATCH")
    if parsed.path in FORBIDDEN_ENDPOINTS:
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError("FORBIDDEN_ENDPOINT")
    if parsed.hostname != REUSED_BINDING_REST_HOST:
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError("REST_HOST_DRIFT")


def _row_has_forensic_identity(*, row: Mapping[str, Any]) -> bool:
    ccy = str(row.get("ccy") or "").strip()
    ts = row.get("ts")
    ts_present = ts is not None and str(ts).strip() != ""
    field_present = any(key in row for key in IDENTITY_FIELDS)
    return ccy != "" and ts_present and field_present


def _digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _one_authorized_interest_accrued_get_v1(
    *,
    transport: LiveCanaryTransportV1,
    handle: Any,
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
        if handle is not None:
            auth_headers = build_okx_live_canary_auth_headers_v1(
                handle=handle, url=url, method=HTTP_METHOD
            )
            auth_headers["User-Agent"] = USER_AGENT_CANARY
        else:
            auth_headers = {"User-Agent": USER_AGENT_CANARY}
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


def execute_u05_primary_proof_bound_interest_accrued_get_acquisition_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    evidence_root: Path | str,
    repo_root: Path | str | None = None,
    genesis_store_root: Path | str | None = None,
    sealed_cc_pack: Path | str | None = None,
    vault_file: Path | str | None = None,
    transport: LiveCanaryTransportV1 | None = None,
    persist_as_of: str | None = None,
) -> U05PrimaryProofBoundInterestAccruedGetAcquisitionResultV1:
    if owner_go != OWNER_GO:
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError("ORIGIN_MAIN_SHA_MISMATCH")
    _assert_standing_pins()
    repo = Path(repo_root) if repo_root is not None else _REPO_ROOT
    cc_pack = (
        Path(sealed_cc_pack) if sealed_cc_pack is not None else repo / CANONICAL_CC_PACK_RELPATH
    )
    _assert_parent_cc_pack(sealed_cc_pack=cc_pack)
    genesis_root = (
        Path(genesis_store_root)
        if genesis_store_root is not None
        else resolve_canonical_d4_d5_genesis_runtime_store_root_v1(repo_root=repo)
    )
    if genesis_root is None:
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError("GENESIS_STORE_ABSENT")
    d4 = load_bound_account_identity_runtime_binding_v1(store_root=genesis_root)
    d5 = load_checkpoint_observation_window_binding_v1(store_root=genesis_root)
    if d4.identity_digest != "00c354f2d247f5a64e33efb31f8be155b8557e847868335ccb15cd4f7ca9d7c4":
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError("D4_IDENTITY_DIGEST_DRIFT")
    if d5.binding_id != "WIND4D5GENESIS8d3f573ffc0c59b4":
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError("D5_BINDING_ID_DRIFT")
    as_of = persist_as_of or _utc_now_z()
    _require_non_empty_str(field="persist_as_of", raw=as_of)
    productive = transport is None
    resolved_vault: Path | None = None
    secret_resolution_status = "NOT_ATTEMPTED"
    if productive:
        resolved_vault = (
            Path(vault_file) if vault_file is not None else default_vault_path_v1(repo_root=repo)
        )
        presence = inspect_credential_material_presence_v1(vault_file=resolved_vault)
        if presence.get("VALUES_INCLUDED") is not False:
            raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError(
                "SECRET_VALUES_MUST_NOT_BE_INCLUDED"
            )
        if presence.get("available") is not True:
            raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError(
                f"VAULT_UNAVAILABLE:{presence.get('reason')}"
            )
        secret_resolution_status = SECRET_RESOLUTION_EPHEMERAL
    try:
        opened_transport, handle, _productive = _open_transport_v1(
            vault_file=resolved_vault, transport=transport
        )
    except F12F13PrimaryLiabilityStockObservationError as exc:
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError(str(exc)) from exc
    try:
        capture = _one_authorized_interest_accrued_get_v1(transport=opened_transport, handle=handle)
    finally:
        if handle is not None:
            release_live_canary_ephemeral_material_v1(handle)
    if capture["send_attempted"] != TRUE_TOKEN:
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError("GET_NOT_ATTEMPTED")
    body_bytes = bytes(capture["body_bytes"])
    _assert_no_secret_material(blob=body_bytes.decode("utf-8", errors="replace"), label="RAW_BODY")
    store = Path(evidence_root) / _folder_from_as_of(as_of)
    store.mkdir(parents=True, exist_ok=True)
    payload_sha = _sha256_bytes(body_bytes)
    _persist_raw_bytes(path=store / RAW_BODY_FILE, body=body_bytes)
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
        "instId": "UNBOUND",
        "ccy": "NOT_PREBOUND",
        "after_before": "NOT_AUTHORIZED",
        "pagination": FALSE_TOKEN,
        "retry": FALSE_TOKEN,
        "request_utc": str(capture["request_utc"]),
        "response_utc": str(capture["response_utc"]),
        "http_status": str(capture["http_status"] or NONE_TOKEN),
        "elapsed_seconds": str(capture["elapsed_seconds"]),
        "payload_sha256": payload_sha,
        "body_byte_len": str(len(body_bytes)),
        "raw_body_filename": RAW_BODY_FILE,
        "send_attempted": capture["send_attempted"],
        "error_class": str(capture["error_class"]),
        "error_token": str(capture["error_token"]),
        "secrets_or_signatures_persisted": FALSE_TOKEN,
        "response_headers_safe": capture["response_headers_safe"],
        "genesis_id": EXPECTED_GENESIS_ID,
        "d4_identity_digest": d4.identity_digest,
        "d5_binding_id": d5.binding_id,
    }
    _assert_no_secret_material(blob=_canonical_json(capture_payload), label="RAW_CAPTURE")
    _persist_json(path=store / RAW_CAPTURE_FILE, payload=capture_payload)
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
    _persist_json(path=store / RAW_CAPTURE_FILE, payload=capture_payload)
    forensic_rows: list[dict[str, Any]] = []
    identity_rows = 0
    for index, item in enumerate(data_rows):
        if not isinstance(item, dict):
            continue
        identity = TRUE_TOKEN if _row_has_forensic_identity(row=item) else FALSE_TOKEN
        if identity == TRUE_TOKEN:
            identity_rows += 1
        row_view = {
            "row_index": str(index),
            "ccy_present": TRUE_TOKEN if str(item.get("ccy") or "").strip() else FALSE_TOKEN,
            "ts_present": TRUE_TOKEN if item.get("ts") not in {None, ""} else FALSE_TOKEN,
            "liab_key_present": TRUE_TOKEN if "liab" in item else FALSE_TOKEN,
            "totalLiab_key_present": TRUE_TOKEN if "totalLiab" in item else FALSE_TOKEN,
            "interest_key_present": TRUE_TOKEN if "interest" in item else FALSE_TOKEN,
            "identity_row": identity,
            "row_digest": _digest({"index": index, "row": item}),
        }
        forensic_rows.append(row_view)
    forensic = {
        "layer": "FORENSIC_RAW_EVIDENCE",
        "row_count": str(len(data_rows)),
        "identity_row_count": str(identity_rows),
        "empty_zero_absent_not_absence_proof": TRUE_TOKEN,
        "liab_totalLiab_interest_not_embedding_proof": TRUE_TOKEN,
        "records": forensic_rows,
    }
    _persist_json(path=store / "forensic_interest_accrued_rows_v1.json", payload=forensic)
    classified: list[dict[str, Any]] = []
    producer_qualifying = 0
    last_embedding_state = UNKNOWN_TOKEN
    for item, row_view in zip(data_rows, forensic_rows):
        if not isinstance(item, dict):
            continue
        raw_token = str(item.get("liab") if "liab" in item else item.get("interest") or "")
        observation = RawSourceObservationV1(
            source_class=SOURCE_INDEPENDENT_EVENT,
            surface_id=REQUEST_SURFACE,
            raw_field="interest-accrued",
            raw_token=raw_token,
            raw_row_digest=str(row_view["row_digest"]),
            account_identity_ref=d4.identity_digest,
            time_as_of=str(item.get("ts") or ""),
            currency=str(item.get("ccy") or ""),
            provenance_digest=str(row_view["row_digest"]),
        )
        classification = classify_raw_source_observation_v1(
            observation=observation,
            expected_account_identity_ref=d4.identity_digest,
            expected_time_as_of="",
            expected_currency=observation.currency,
        )
        embedding = assess_non_algebraic_embedding_identity_v1(
            classification=classification,
            algebraic_eq_identity_used=FALSE_TOKEN,
            embedding_witness_id="",
            claimed_embedding_state=UNKNOWN_TOKEN,
        )
        state = build_borrow_or_account_liability_state_v1(
            observation=observation,
            classification=classification,
            bound_account_identity=d4.identity_digest,
            checkpoint_as_of=d5.binding_id,
        )
        eligibility = evaluate_u05_eligibility_from_liability_state_v1(
            state=state, embedding=embedding
        )
        if classification.liability_identity not in {"", UNKNOWN_TOKEN}:
            producer_qualifying += 1
        last_embedding_state = embedding.non_algebraic_embedding_identity
        classified.append(
            {
                "source_class": observation.source_class,
                "surface_id": observation.surface_id,
                "classification": classification.classification,
                "classification_reason": classification.classification_reason,
                "liability_identity": classification.liability_identity,
                "liability_exists": classification.liability_exists,
                "affects_equity_stock": classification.affects_equity_stock,
                "already_embedded_in_eq": classification.already_embedded_in_eq,
                "account_scope_identity_status": classification.account_scope_identity_status,
                "time_scope_identity_status": classification.time_scope_identity_status,
                "currency_scope_identity_status": classification.currency_scope_identity_status,
                "non_algebraic_embedding_identity": embedding.non_algebraic_embedding_identity,
                "assessment_reason": embedding.assessment_reason,
                "law_outcome": eligibility["law_outcome"],
                "u05_decision": eligibility["u05_decision"],
            }
        )
    if producer_qualifying != 0:
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError(
            "PRODUCER_QUALIFYING_MUST_REMAIN_ZERO_KIND_SET_EMPTY"
        )
    law_outcome = evaluate_u05_primary_proof_v1(proof={})
    if law_outcome.outcome in {OUTCOME_INCLUDE, OUTCOME_EXCLUDE}:
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError("ABSENT_PROOF_MUST_NOT_DECIDE")
    if law_outcome.outcome != OUTCOME_NONQUALIFYING:
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError(
            "ABSENT_PROOF_MUST_BE_NONQUALIFYING"
        )
    if last_embedding_state != UNKNOWN_TOKEN:
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError(
            "EMBEDDING_MUST_REMAIN_UNKNOWN"
        )
    independent_event_proven = FALSE_TOKEN
    producer_payload = {
        "layer": "ADJUDICATED_CONCLUSION",
        "producer_id": PRODUCER_ID,
        "producer_status": PRODUCER_STATUS,
        "producer_executed": TRUE_TOKEN,
        "classified_observation_count": str(len(classified)),
        "producer_qualifying_liability_event_count": str(producer_qualifying),
        "forensic_identity_row_count": str(identity_rows),
        "independent_liability_event_proven": independent_event_proven,
        "non_algebraic_embedding_identity": UNKNOWN_TOKEN,
        "u05_evidence_class": CLASS_U05,
        "law_outcome": law_outcome.outcome,
        "law_basis": law_outcome.basis,
        "get_alone_may_include": FALSE_TOKEN,
        "get_alone_may_exclude": FALSE_TOKEN,
        "records": classified,
    }
    _persist_json(path=store / "producer_consumption_v1.json", payload=producer_payload)
    evaluation = {
        "layer": "ADJUDICATED_CONCLUSION",
        "u05_decision_before": DECISION_REMAIN_UNKNOWN,
        "u05_decision_after": DECISION_REMAIN_UNKNOWN,
        "u05_decision_basis": DECISION_BASIS,
        "u05_primary_proof_status": PRIMARY_PROOF_STATUS,
        "u06_decision_unchanged": DECISION_REMAIN_UNKNOWN,
        "residual_decision_unchanged": DECISION_REMAIN_UNKNOWN,
        "independent_liability_event_proven": independent_event_proven,
        "non_algebraic_embedding_identity": UNKNOWN_TOKEN,
        "p01_u05_overlap_disproven": FALSE_TOKEN,
        "once_only_equity_stock_effect_proven": FALSE_TOKEN,
        "venue_eq_source_authority": FALSE_TOKEN,
        "account_bills_canonicalized": FALSE_TOKEN,
        "get_alone_may_include": FALSE_TOKEN,
        "get_alone_may_exclude": FALSE_TOKEN,
        "include_from_unknown": "FORBIDDEN_UNTIL_POSITIVE_PRIMARY_PROOF",
        "exclude_from_unknown": "FORBIDDEN_UNTIL_POSITIVE_IN_BASE_PROOF",
    }
    _persist_json(path=store / "current_proof_evaluation_v1.json", payload=evaluation)
    architecture = {
        "layer": "CANONICAL_AUTHORITY",
        "blocker_id": BLOCKER_ID,
        "architecture_blocker": ARCHITECTURE_BLOCKER,
        "missing_positive_proof_component": "INDEPENDENT_NON_ALGEBRAIC_EMBEDDING_WITNESS",
        "next_owner_go_required": NEXT_OWNER_GO,
        "next_action": NEXT_ACTION,
        "owner_go_consumed": TRUE_TOKEN,
        "retry_forbidden": TRUE_TOKEN,
        "why_u05_remains_unknown": (
            "The bound interest-accrued GET was consumed once. GET alone may not "
            "INCLUDE or EXCLUDE. Independent liability events remain unproven as a "
            "classified KIND_SET member. The selected surface is not an embedding "
            "witness. liab/totalLiab/interest values must not infer P01/U05 overlap."
        ),
    }
    _persist_json(path=store / "architecture_blocker_v1.json", payload=architecture)
    http_status = str(capture["http_status"] or NONE_TOKEN)
    claims = {
        "OWNER_GO": OWNER_GO,
        "OWNER_GO_STATUS": "CONSUMED",
        "PARENT_CC_NEXT_OWNER_GO": PARENT_CC_NEXT_OWNER_GO,
        "SCHEMA_CLASS": SCHEMA_CLASS,
        "CONTRACT_VERSION": CONTRACT_VERSION,
        "AUTHORITY_EFFECT": AUTHORITY_EFFECT,
        "GENESIS_ID": EXPECTED_GENESIS_ID,
        "GENESIS_AS_OF": EXPECTED_GENESIS_AS_OF,
        "PERSIST_AS_OF": as_of,
        "EXACT_REQUEST": AUTHORIZED_URL,
        "HTTP_METHOD": HTTP_METHOD,
        "BOUND_ENDPOINT": AUTHORIZED_PATH,
        "QUERY": AUTHORIZED_QUERY,
        "PRIMARY_PROOF_ROLE_BOUND": PRIMARY_PROOF_ROLE,
        "PRODUCER_ID": PRODUCER_ID,
        "PRODUCTIVE_ACQUISITION_AUTHORIZED": TRUE_TOKEN,
        "PRODUCTIVE_ACQUISITION_EXECUTED": TRUE_TOKEN,
        "AUTHORIZED_GET_COUNT": "1",
        "ACTUAL_GET_COUNT": "1",
        "RETRY_COUNT": "0",
        "POST_COUNT": "0",
        "SECRET_RESOLUTION_STATUS": secret_resolution_status,
        "SECRET_PERSISTED": FALSE_TOKEN,
        "HTTP_STATUS": http_status,
        "VENUE_CODE": venue_code_token,
        "RAW_EVIDENCE_PERSISTED": TRUE_TOKEN,
        "RAW_EVIDENCE_SHA256": payload_sha,
        "PRODUCER_EXECUTED": TRUE_TOKEN,
        "QUALIFYING_LIABILITY_ROWS": str(identity_rows),
        "PRODUCER_QUALIFYING_LIABILITY_EVENT_COUNT": str(producer_qualifying),
        "INDEPENDENT_LIABILITY_EVENT_PROVEN": independent_event_proven,
        "NON_ALGEBRAIC_EMBEDDING_IDENTITY": UNKNOWN_TOKEN,
        "U05_DECISION_BEFORE": DECISION_REMAIN_UNKNOWN,
        "U05_DECISION_AFTER": DECISION_REMAIN_UNKNOWN,
        "U05_DECISION_BASIS": DECISION_BASIS,
        "U05_PRIMARY_PROOF_STATUS": PRIMARY_PROOF_STATUS,
        "U06_DECISION_UNCHANGED": DECISION_REMAIN_UNKNOWN,
        "RESIDUAL_DECISION_UNCHANGED": DECISION_REMAIN_UNKNOWN,
        "VENUE_EQ_SOURCE_AUTHORITY": FALSE_TOKEN,
        "ACCOUNT_BILLS_CANONICALIZED": FALSE_TOKEN,
        "GATE_A_REOPENED": FALSE_TOKEN,
        "GATE_B_REEXECUTED": FALSE_TOKEN,
        "MS2_AUTHORIZED": FALSE_TOKEN,
        "D6_FULLY_CLOSED": FALSE_TOKEN,
        "D7_AUTHORIZED": FALSE_TOKEN,
        "C17_CREATED": FALSE_TOKEN,
        "STANDING_FULL_CORE_DAG_PIN": DAG_PIN,
        "BLOCKER_ID": BLOCKER_ID,
        "ARCHITECTURE_BLOCKER": ARCHITECTURE_BLOCKER,
        "NEXT_OWNER_GO_REQUIRED": NEXT_OWNER_GO,
        "NEXT_ACTION": NEXT_ACTION,
        "ERROR_CLASS": str(capture["error_class"]),
        "PARSE_ERROR": parse_error,
        "SECRETS_OR_SIGNATURES_PERSISTED": FALSE_TOKEN,
        "PROTECTED_SURFACES_UNCHANGED": TRUE_TOKEN,
        "PRIOR_ANCHOR_ID": AUTHORIZED_ANCHOR_ID,
        "PARENT_CB_PACK": CANONICAL_CB_PACK_RELPATH,
        "PARENT_CC_PACK": CANONICAL_CC_PACK_RELPATH,
    }
    _assert_no_secret_material(blob=_canonical_json(claims), label="CLAIMS")
    _persist_json(path=store / CLAIMS_FILE, payload=claims)
    _persist_json(
        path=store / "LINEAGE.json",
        payload={
            "origin_main_sha": origin_main_sha,
            "owner_go": OWNER_GO,
            "genesis_id": EXPECTED_GENESIS_ID,
            "genesis_as_of": EXPECTED_GENESIS_AS_OF,
            "persist_as_of": as_of,
            "parent_cc_pack": CANONICAL_CC_PACK_RELPATH,
            "parent_cb_pack": CANONICAL_CB_PACK_RELPATH,
            "d4_identity_digest": d4.identity_digest,
            "d5_binding_id": d5.binding_id,
            "prior_anchor_id": AUTHORIZED_ANCHOR_ID,
            "reconstruction_source_authority": FALSE_TOKEN,
            "witness_acquisition_authorized": FALSE_TOKEN,
        },
    )
    _persist_json(
        path=store / "protected_surfaces_v1.json",
        payload={
            "master_v2_unchanged": TRUE_TOKEN,
            "double_play_unchanged": TRUE_TOKEN,
            "bull_bear_state_switch_unchanged": TRUE_TOKEN,
            "self_learning_unchanged": TRUE_TOKEN,
            "top20_unchanged": TRUE_TOKEN,
            "full_core_autonomy_unchanged": TRUE_TOKEN,
            "step_29p_unchanged": TRUE_TOKEN,
            "u06_unchanged": TRUE_TOKEN,
            "residual_unchanged": TRUE_TOKEN,
            "gate_a_not_retried": TRUE_TOKEN,
            "gate_b_not_executed": TRUE_TOKEN,
            "bills_authority_unchanged": TRUE_TOKEN,
            "venue_eq_source_authority": FALSE_TOKEN,
            "p01_authority_unchanged": TRUE_TOKEN,
            "ms2_authorized": FALSE_TOKEN,
            "reconstruction_implemented": FALSE_TOKEN,
            "dag_pin": DAG_PIN,
            "live_gates_unchanged": TRUE_TOKEN,
            "venue_execution_authority_unchanged": TRUE_TOKEN,
        },
    )
    _persist_json(
        path=store / "layers_v1.json",
        payload={
            "CANONICAL_AUTHORITY": "architecture_blocker_v1.json",
            "FORENSIC_RAW_EVIDENCE": f"{RAW_CAPTURE_FILE},{RAW_BODY_FILE},forensic_interest_accrued_rows_v1.json",
            "ADJUDICATED_CONCLUSION": "producer_consumption_v1.json,current_proof_evaluation_v1.json",
            "HISTORICAL": "LINEAGE.json",
            "NAVIGATION": "FORBIDDEN_AS_AUTHORITY",
            "INTERPRETATION": "FORBIDDEN",
            "HYPOTHESIS": "FORBIDDEN",
            "UNRESOLVED_OR_CONTRADICTORY": BLOCKER_ID,
        },
    )
    persist_manifest_sha256_v1(store_root=store)
    if verify_manifest_sha256_v1(store_root=store) != 0:
        raise U05PrimaryProofBoundInterestAccruedGetAcquisitionError("MANIFEST_VERIFY_NOT_ZERO")
    return U05PrimaryProofBoundInterestAccruedGetAcquisitionResultV1(
        genesis_id=EXPECTED_GENESIS_ID,
        persist_as_of=as_of,
        store_root=str(store),
        authorized_get_count="1",
        actual_get_count="1",
        retry_count="0",
        post_count="0",
        http_status=http_status,
        venue_code=venue_code_token,
        raw_evidence_persisted=TRUE_TOKEN,
        raw_evidence_sha256=payload_sha,
        producer_executed=TRUE_TOKEN,
        qualifying_liability_rows=str(identity_rows),
        independent_liability_event_proven=independent_event_proven,
        non_algebraic_embedding_identity=UNKNOWN_TOKEN,
        u05_decision_after=DECISION_REMAIN_UNKNOWN,
        secret_resolution_status=secret_resolution_status,
        evidence_manifest=str(store / "MANIFEST.sha256"),
    )


__all__ = [
    "ARCHITECTURE_BLOCKER",
    "AUTHORIZED_ENDPOINT",
    "AUTHORIZED_URL",
    "BLOCKER_ID",
    "CANONICAL_PACK_RELPATH",
    "CANONICAL_PERSIST_AS_OF",
    "DECISION_BASIS",
    "EXPECTED_ORIGIN_MAIN_SHA",
    "HTTP_METHOD",
    "NEXT_OWNER_GO",
    "OWNER_GO",
    "PRIMARY_PROOF_ROLE",
    "PRIMARY_PROOF_STATUS",
    "U05PrimaryProofBoundInterestAccruedGetAcquisitionError",
    "U05PrimaryProofBoundInterestAccruedGetAcquisitionResultV1",
    "execute_u05_primary_proof_bound_interest_accrued_get_acquisition_v1",
]
