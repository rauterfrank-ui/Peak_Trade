"""D6 F12/F13 primary liability-stock observation.

One Owner-GO-scoped READ-ONLY GET of GET /api/v5/account/balance.
Seals raw venue bytes before forensic token extraction and F12/F13
adjudication. Does not POST. Does not mint D4 identity. Does not treat
empty, zero, blank, missing, or null tokens as kind absence. Non-zero
liability tokens do not automatically ratify an EQUITY_STOCK source kind.
Does not observe F16-F18. Does not authorize MS2 or D7.
Standing OBSERVATION_NETWORK_GET_AUTHORIZED remains false.
AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

from src.ops.governed_productive_account_equity_authority_producer_v1.account_equity_source_mapping_and_complete_event_stream_acquisition_v1 import (
    CANONICAL_MAPPING_PACK_RELPATH,
    reject_observed_value_as_kind_absence_or_embedding_decision_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.account_equity_source_mapping_ratification_v1 import (
    CANONICAL_S6_PACK_RELPATH,
    RATIFIED_SOURCE_KIND_SET,
    reject_unratified_equity_stock_source_kind_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.bound_account_identity_runtime_binding_v1 import (
    load_bound_account_identity_runtime_binding_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.checkpoint_observation_window_binding_contract_v1 import (
    load_checkpoint_observation_window_binding_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT,
    D6_FULLY_CLOSED,
    D7_AUTHORIZED,
    EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED,
    KIND_SET_RESOLVED,
    MS2_AUTHORIZED,
    OBSERVATION_NETWORK_GET_AUTHORIZED,
    RAW_EQ_SOURCE_AUTHORITY,
    RESIDUAL_KIND_DECISION,
    SELECTED_OBSERVATION_SURFACES,
    U05_KIND_DECISION,
    U06_KIND_DECISION,
    UNKNOWN_NECESSARY_CLASS_REMAINS,
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
from src.ops.governed_productive_account_equity_authority_producer_v1.f12_f13_f16_f17_f18_necessary_equity_stock_kind_resolution_v1 import (
    CANONICAL_ACQUISITION_PACK_RELPATH,
    EARLIEST_REMAINING_D6_BLOCKER as BG_EARLIEST_REMAINING_D6_BLOCKER,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.named_remaining_unknown_kind_set_evidence_persist_contract_v1 import (
    DECISION_REMAIN_UNKNOWN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_observation_s0_runtime_binding_gate_v1 import (
    resolve_canonical_d4_d5_genesis_runtime_store_root_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    CANONICAL_SEALED_OBSERVATION_PACK_RELPATH,
    verify_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.path_b_class_c_package_1_trading_account_observation_rules_contract_v1 import (
    SURFACE_ACCOUNT_BALANCE,
    reject_include_exclude_from_unknown_embedding_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    ENDPOINT_ACCOUNT_BALANCE,
    ENDPOINT_ACCOUNT_BILLS,
    ENDPOINT_ACCOUNT_BILLS_ARCHIVE,
    ENDPOINT_ACCOUNT_CONFIG,
    ENDPOINT_ACCOUNT_SUBTYPES,
    REUSED_BINDING_REST_HOST,
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
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.live_credential_ephemeral_v1 import (
    build_file_secretref_vault_backend_v1,
    release_live_canary_ephemeral_material_v1,
    resolve_and_load_live_canary_secretref_ephemeral_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.okx_live_canary_signer_v1 import (
    build_okx_live_canary_auth_headers_v1,
)

OWNER_GO = "OWNER_GO_D6_F12_F13_PRIMARY_LIABILITY_STOCK_OBSERVATION_V1"
EXPECTED_ORIGIN_MAIN_SHA = "d8e707647e4ab845a0cffa1e0a12ccaff38ab3b6"
CANONICAL_BG_RESOLUTION_PACK_RELPATH = (
    "evidence/ops/full_core_d6_f12_f13_f16_f17_f18_necessary_equity_stock_kind_resolution_v1/"
    "2026-09-13T200000Z"
)
OBSERVATION_STORE_RELPATH = (
    "evidence/ops/full_core_d6_f12_f13_primary_liability_stock_observation_v1"
)
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_d6_f12_f13_primary_liability_stock_observation_v1/2026-09-13T221500Z"
)
AUTHORIZED_HOST = "eea.okx.com"
REUSED_REST_BASE = f"https://{REUSED_BINDING_REST_HOST}"
AUTHORIZED_ENDPOINT = ENDPOINT_ACCOUNT_BALANCE
AUTHORIZED_SURFACE = SURFACE_ACCOUNT_BALANCE
FORBIDDEN_ENDPOINTS: tuple[str, ...] = (
    ENDPOINT_ACCOUNT_CONFIG,
    ENDPOINT_ACCOUNT_SUBTYPES,
    ENDPOINT_ACCOUNT_BILLS,
    ENDPOINT_ACCOUNT_BILLS_ARCHIVE,
    "/api/v5/account/positions",
    "/api/v5/asset/balances",
    "/api/v5/asset/transfer",
    "/api/v5/trade/order",
)
U05_RAW_FIELDS: tuple[str, ...] = (
    "liab",
    "crossLiab",
    "isoLiab",
    "borrowFroz",
)
MAX_NETWORK_REQUEST_COUNT = 1
DEFAULT_MAX_RETRIES = 0
DEFAULT_TIMEOUT_SECONDS = 10.0
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
NONE_TOKEN = "NONE"
KIND_SET_EMPTY = "EMPTY_FAIL_CLOSED"
STATUS_UNKNOWN = "UNKNOWN"
DECISION_INCLUDE = "INCLUDE_AS_NECESSARY_EQUITY_STOCK_KIND"
DECISION_EXCLUDE = "EXCLUDE_AS_NON_SOURCE_OR_OTHER_DOMAIN"
RETENTION_FAIL_CLOSED = "FAIL_CLOSED_NOT_PROVEN"
ORDERING_FAIL_CLOSED = "FAIL_CLOSED_NOT_PROVEN"
F16_F17_F18_BLOCKER = (
    "F16_F17_F18_RESOLUTION_REQUIRES_PAIRED_FEE_EVENT_AND_EQUITY_STOCK_OBSERVATION"
    "_OR_RATIFIED_EQ_IDENTITY"
)
BLOCKER_EMPTY_OR_ZERO = (
    "F12_F13_REMAIN_UNKNOWN_AFTER_AUTHORIZED_FRESH_BALANCE_GET_EMPTY_OR_ZERO_DOES_NOT_PROVE_ABSENCE"
)
BLOCKER_NONZERO_UNPROVEN = (
    "F12_F13_REMAIN_UNKNOWN_NONZERO_LIABILITY_TOKEN_OBSERVED_SOURCE_SEMANTICS_"
    "AND_EMBEDDING_UNPROVEN"
)
KIND_SET_BLOCKED_EMPTY_OR_ZERO = (
    "F12_F13_AUTHORIZED_FRESH_BALANCE_GET_EMPTY_OR_ZERO_DOES_NOT_PROVE_ABSENCE"
)
KIND_SET_BLOCKED_NONZERO_UNPROVEN = (
    "F12_F13_NONZERO_LIABILITY_TOKEN_OBSERVED_SOURCE_SEMANTICS_AND_EMBEDDING_UNPROVEN"
)
CLAIMS_FILE = "claims.json"
RAW_BODY_FILE = "raw_account_balance_response_body.json"
RAW_CAPTURE_FILE = "raw_http_capture_v1.json"
FORENSIC_FILE = "forensic_liability_tokens_v1.json"
ADJUDICATION_FILE = "f12_f13_adjudication_v1.json"
_REPO_ROOT = Path(__file__).resolve().parents[3]


class F12F13PrimaryLiabilityStockObservationError(ValueError):
    """Fail-closed F12/F13 primary liability-stock observation violation."""


@dataclass(frozen=True)
class F12F13PrimaryLiabilityStockObservationResultV1:
    genesis_id: str
    genesis_as_of: str
    observation_as_of: str
    store_root: str
    authorized_get_surfaces: str
    get_count: str
    post_count: str
    account_mutation_performed: str
    nonzero_liability_observed: str
    raw_evidence_sealed: str
    f12_decision: str
    f13_decision: str
    f16_decision: str
    f17_decision: str
    f18_decision: str
    ratified_source_kinds: str
    kind_set: str
    kind_set_resolved: str
    raw_eq_source_authority: str
    retention_coverage_status: str
    ordering_completeness_status: str
    complete_classified_event_stream_proven: str
    earliest_remaining_d6_blocker: str
    ms2_authorized: str
    d6_fully_closed: str
    d7_authorized: str
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


def _load_json_object(*, path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise F12F13PrimaryLiabilityStockObservationError(f"JSON_NOT_OBJECT:{path.name}")
    return payload


def _require_token(*, field: str, payload: Mapping[str, Any], expected: str) -> None:
    actual = str(payload.get(field) or "")
    if actual != expected:
        raise F12F13PrimaryLiabilityStockObservationError(f"{field}_DRIFT:{actual}")


def assert_f12_f13_balance_surface_already_selected_v1() -> None:
    if AUTHORIZED_SURFACE not in SELECTED_OBSERVATION_SURFACES:
        raise F12F13PrimaryLiabilityStockObservationError(
            "MINIMAL_GET_SURFACE_NOT_CANONICALLY_SELECTED"
        )
    if AUTHORIZED_ENDPOINT != "/api/v5/account/balance":
        raise F12F13PrimaryLiabilityStockObservationError("AUTHORIZED_ENDPOINT_DRIFT")


def reject_claimed_f12_f13_proof_from_token_shape_v1(
    *,
    claimed_proof: str,
    fact_id: str,
) -> None:
    forbidden = {
        DECISION_INCLUDE,
        DECISION_EXCLUDE,
        "F12_TRUE",
        "F13_TRUE",
        "F12_FALSE",
        "F13_FALSE",
        "EMPTY_LIAB_MEANS_F12_FALSE",
        "ZERO_LIAB_MEANS_F13_TRUE",
        "MISSING_LIAB_MEANS_KIND_ABSENCE",
        "NONZERO_LIAB_MEANS_EQUITY_STOCK_SOURCE",
        "ALGEBRAIC_EQ_IDENTITY",
    }
    if claimed_proof in forbidden:
        raise F12F13PrimaryLiabilityStockObservationError(
            f"F12_F13_CANNOT_{claimed_proof}:{fact_id}"
        )
    if claimed_proof != "REMAIN_UNKNOWN_PRIMARY_EVIDENCE_DOES_NOT_CARRY_DECISION":
        raise F12F13PrimaryLiabilityStockObservationError(f"F12_F13_PROOF_UNKNOWN:{claimed_proof}")
    if fact_id not in {
        "F12_LIABILITY_AFFECTS_EQUITY_STOCK",
        "F13_LIABILITY_ALREADY_EMBEDDED_IN_EQ",
    }:
        raise F12F13PrimaryLiabilityStockObservationError(f"F12_F13_FACT_UNKNOWN:{fact_id}")


def _assert_standing_pins() -> None:
    if KIND_SET_RESOLVED is not False:
        raise F12F13PrimaryLiabilityStockObservationError("KIND_SET_RESOLVED_NOT_FALSE")
    if RATIFIED_CLASSIFIED_KIND_SET or RATIFIED_SOURCE_KIND_SET:
        raise F12F13PrimaryLiabilityStockObservationError("SOURCE_KIND_SET_MUST_REMAIN_EMPTY")
    if U05_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise F12F13PrimaryLiabilityStockObservationError("U05_KIND_DECISION_NOT_REMAIN_UNKNOWN")
    if U06_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise F12F13PrimaryLiabilityStockObservationError("U06_KIND_DECISION_NOT_REMAIN_UNKNOWN")
    if RESIDUAL_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise F12F13PrimaryLiabilityStockObservationError(
            "RESIDUAL_KIND_DECISION_NOT_REMAIN_UNKNOWN"
        )
    if UNKNOWN_NECESSARY_CLASS_REMAINS is not True:
        raise F12F13PrimaryLiabilityStockObservationError("UNKNOWN_NECESSARY_CLASS_MUST_REMAIN")
    if MS2_AUTHORIZED is not False:
        raise F12F13PrimaryLiabilityStockObservationError("MS2_AUTHORIZED_NOT_FALSE")
    if D6_FULLY_CLOSED is not False:
        raise F12F13PrimaryLiabilityStockObservationError("D6_FULLY_CLOSED_NOT_FALSE")
    if D7_AUTHORIZED is not False:
        raise F12F13PrimaryLiabilityStockObservationError("D7_AUTHORIZED_NOT_FALSE")
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        raise F12F13PrimaryLiabilityStockObservationError("RAW_EQ_SOURCE_AUTHORITY_NOT_FALSE")
    if EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED is not False:
        raise F12F13PrimaryLiabilityStockObservationError(
            "EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED_NOT_FALSE"
        )
    if OBSERVATION_NETWORK_GET_AUTHORIZED is not False:
        raise F12F13PrimaryLiabilityStockObservationError(
            "OBSERVATION_NETWORK_GET_AUTHORIZED_MUST_REMAIN_FALSE"
        )
    if AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT is not False:
        raise F12F13PrimaryLiabilityStockObservationError(
            "PRODUCTIVE_EVENT_SOURCE_SEAM_MUST_REMAIN_ABSENT"
        )
    reject_unratified_equity_stock_source_kind_v1(
        event_kind=NONE_TOKEN,
        mapped_numeric_effect="NOT_MAPPED_FAIL_CLOSED",
    )
    reject_include_exclude_from_unknown_embedding_v1(
        fact_id="F12_LIABILITY_AFFECTS_EQUITY_STOCK",
        decision=DECISION_REMAIN_UNKNOWN,
    )
    reject_observed_value_as_kind_absence_or_embedding_decision_v1(
        claimed_proof="NO_UNIQUE_EMBEDDING_OR_KIND_DECISION",
        fact_id="F12_LIABILITY_AFFECTS_EQUITY_STOCK",
    )


def _verify_manifest_or_raise(*, store_root: Path, label: str) -> None:
    if verify_manifest_sha256_v1(store_root=store_root) != 0:
        raise F12F13PrimaryLiabilityStockObservationError(f"{label}_MANIFEST_VERIFY_NOT_ZERO")


def _preflight_sealed_inputs() -> None:
    observation = _REPO_ROOT / CANONICAL_SEALED_OBSERVATION_PACK_RELPATH
    s6_pack = _REPO_ROOT / CANONICAL_S6_PACK_RELPATH
    mapping = _REPO_ROOT / CANONICAL_MAPPING_PACK_RELPATH
    acquisition = _REPO_ROOT / CANONICAL_ACQUISITION_PACK_RELPATH
    bg = _REPO_ROOT / CANONICAL_BG_RESOLUTION_PACK_RELPATH
    _verify_manifest_or_raise(store_root=observation, label="S1_S5")
    _verify_manifest_or_raise(store_root=s6_pack, label="S6")
    _verify_manifest_or_raise(store_root=mapping, label="MAPPING")
    _verify_manifest_or_raise(store_root=acquisition, label="ACQUISITION")
    _verify_manifest_or_raise(store_root=bg, label="BG")
    mapping_claims = _load_json_object(path=mapping / CLAIMS_FILE)
    _require_token(field="GENESIS_ID", payload=mapping_claims, expected=EXPECTED_GENESIS_ID)
    _require_token(field="RATIFIED_SOURCE_KINDS", payload=mapping_claims, expected=NONE_TOKEN)
    _require_token(field="KIND_SET_RESOLVED", payload=mapping_claims, expected=FALSE_TOKEN)
    _require_token(field="RAW_EQ_SOURCE_AUTHORITY", payload=mapping_claims, expected=FALSE_TOKEN)
    bg_claims = _load_json_object(path=bg / CLAIMS_FILE)
    _require_token(field="F12_DECISION", payload=bg_claims, expected=DECISION_REMAIN_UNKNOWN)
    _require_token(field="F13_DECISION", payload=bg_claims, expected=DECISION_REMAIN_UNKNOWN)
    _require_token(field="F16_DECISION", payload=bg_claims, expected=DECISION_REMAIN_UNKNOWN)
    _require_token(
        field="EARLIEST_REMAINING_D6_BLOCKER",
        payload=bg_claims,
        expected=BG_EARLIEST_REMAINING_D6_BLOCKER,
    )
    _require_token(field="NEW_NETWORK_GET_COUNT", payload=bg_claims, expected="0")


def _preflight_genesis(*, genesis_store_root: Path | str | None) -> Path:
    root = (
        Path(genesis_store_root)
        if genesis_store_root is not None
        else resolve_canonical_d4_d5_genesis_runtime_store_root_v1()
    )
    if root is None:
        raise F12F13PrimaryLiabilityStockObservationError("GENESIS_STORE_ABSENT")
    _verify_manifest_or_raise(store_root=root, label="GENESIS")
    claims = _load_json_object(path=root / CLAIMS_FILE)
    _require_token(field="GENESIS_ID", payload=claims, expected=EXPECTED_GENESIS_ID)
    _require_token(field="GENESIS_AS_OF", payload=claims, expected=EXPECTED_GENESIS_AS_OF)
    _require_token(field="D4_RUNTIME_INSTANCE_PRESENT", payload=claims, expected=TRUE_TOKEN)
    _require_token(field="D5_RUNTIME_INSTANCE_PRESENT", payload=claims, expected=TRUE_TOKEN)
    d4 = load_bound_account_identity_runtime_binding_v1(store_root=root)
    d5 = load_checkpoint_observation_window_binding_v1(store_root=root)
    if d4.bound_venue_identity != "OKX":
        raise F12F13PrimaryLiabilityStockObservationError("BOUND_VENUE_IDENTITY_DRIFT")
    if d5.observed_at_as_of != EXPECTED_GENESIS_AS_OF:
        raise F12F13PrimaryLiabilityStockObservationError("D5_WINDOW_AS_OF_DRIFT")
    return root


def _open_transport_v1(
    *,
    vault_file: Path | str | None,
    transport: LiveCanaryTransportV1 | None,
) -> tuple[LiveCanaryTransportV1, Any, bool]:
    if REUSED_BINDING_REST_HOST != AUTHORIZED_HOST:
        raise F12F13PrimaryLiabilityStockObservationError("HOST_MISMATCH")
    productive = transport is None
    if productive:
        if vault_file is None or not str(vault_file).strip():
            raise F12F13PrimaryLiabilityStockObservationError("VAULT_FILE_REQUIRED")
        transport = UrllibLiveCanaryTransportV1(wire_send_enabled=True)
    if isinstance(transport, UrllibLiveCanaryTransportV1) and not bool(
        getattr(transport, "wire_send_enabled", False)
    ):
        raise F12F13PrimaryLiabilityStockObservationError("PRODUCTIVE_WIRE_DISABLED")
    handle = None
    if productive:
        backend = build_file_secretref_vault_backend_v1(vault_file=vault_file)
        handle = resolve_and_load_live_canary_secretref_ephemeral_v1(
            secret_reference=REQUIRED_SECRETREF_URI,
            vault_backend=backend,
            credential_class=REQUIRED_CREDENTIAL_CLASS,
        )
    if transport is None:
        raise F12F13PrimaryLiabilityStockObservationError("TRANSPORT_ABSENT")
    return transport, handle, productive


def _one_authorized_balance_get_v1(
    *,
    client: LiveCanaryHttpClientV1,
    handle: Any,
) -> dict[str, Any]:
    endpoint = AUTHORIZED_ENDPOINT
    if endpoint in FORBIDDEN_ENDPOINTS:
        raise F12F13PrimaryLiabilityStockObservationError("MUTATION_OR_FEE_ENDPOINT_FORBIDDEN")
    url = f"{REUSED_REST_BASE}{endpoint}"
    parsed = urlparse(url)
    if parsed.path != endpoint or parsed.query:
        raise F12F13PrimaryLiabilityStockObservationError("SIGNED_REQUEST_TARGET_MISMATCH")
    if parsed.hostname != AUTHORIZED_HOST:
        raise F12F13PrimaryLiabilityStockObservationError("HOST_MISMATCH")
    auth_headers: dict[str, str] = {}
    try:
        if handle is not None:
            auth_headers = build_okx_live_canary_auth_headers_v1(
                handle=handle, url=url, method="GET"
            )
            auth_headers["User-Agent"] = USER_AGENT_CANARY
        request_utc = _utc_now_z()
        try:
            response = client.get(endpoint=endpoint, headers=auth_headers or None)
        except LiveCanaryHttpError as exc:
            raise F12F13PrimaryLiabilityStockObservationError(
                f"F12_F13_BALANCE_GET_FAILED:{exc}"
            ) from exc
        response_utc = _utc_now_z()
        if response.method != "GET":
            raise F12F13PrimaryLiabilityStockObservationError("NON_GET_RESPONSE")
        if bool(response.redirect_followed):
            raise F12F13PrimaryLiabilityStockObservationError("REDIRECT_FOLLOWED")
        return {
            "endpoint": endpoint,
            "request_utc": request_utc,
            "response_utc": response_utc,
            "http_status": int(response.status_code),
            "elapsed_seconds": str(response.elapsed_seconds),
            "body_bytes": bytes(response.body_bytes),
            "response_headers_safe": {
                str(k): str(v) for k, v in dict(response.response_headers_safe).items()
            },
        }
    finally:
        auth_headers.clear()


def _assert_get_counters_v1(*, client: LiveCanaryHttpClientV1) -> dict[str, Any]:
    counters = client.counters.to_dict()
    if int(counters.get("GET_REQUEST_COUNT", 0) or 0) != 1:
        raise F12F13PrimaryLiabilityStockObservationError("GET_COUNT_NOT_ONE")
    if int(counters.get("REQUEST_COUNT", 0) or 0) != 1:
        raise F12F13PrimaryLiabilityStockObservationError("REQUEST_COUNT_NOT_ONE")
    if int(counters.get("WRITE_REQUEST_COUNT", 0) or 0) != 0:
        raise F12F13PrimaryLiabilityStockObservationError("WRITE_REQUEST_DETECTED")
    if int(counters.get("TRANSFER_REQUEST_COUNT", 0) or 0) != 0:
        raise F12F13PrimaryLiabilityStockObservationError("TRANSFER_REQUEST_DETECTED")
    if int(counters.get("ORDER_REQUEST_COUNT", 0) or 0) != 0:
        raise F12F13PrimaryLiabilityStockObservationError("ORDER_REQUEST_DETECTED")
    if list(client.counters.endpoints_used) != [AUTHORIZED_ENDPOINT]:
        raise F12F13PrimaryLiabilityStockObservationError("ENDPOINT_SET_MISMATCH")
    if list(client.counters.methods_used) != ["GET"]:
        raise F12F13PrimaryLiabilityStockObservationError("NON_GET_METHOD_DETECTED")
    return counters


def _classify_raw_token(*, row: Mapping[str, Any], field: str) -> dict[str, str]:
    key_present = field in row
    if not key_present:
        return {
            "field": field,
            "presence": "ABSENT",
            "python_type": "MISSING",
            "raw_token": "",
            "exact_empty_string": FALSE_TOKEN,
            "exact_zero_string": FALSE_TOKEN,
            "nonzero_string_token": FALSE_TOKEN,
            "empty_zero_null_missing_not_normalized": TRUE_TOKEN,
        }
    raw = row.get(field)
    if raw is None:
        return {
            "field": field,
            "presence": "NULL",
            "python_type": "NoneType",
            "raw_token": "",
            "exact_empty_string": FALSE_TOKEN,
            "exact_zero_string": FALSE_TOKEN,
            "nonzero_string_token": FALSE_TOKEN,
            "empty_zero_null_missing_not_normalized": TRUE_TOKEN,
        }
    if isinstance(raw, bool):
        raise F12F13PrimaryLiabilityStockObservationError(f"FORENSIC_BOOL_TOKEN_FORBIDDEN:{field}")
    if isinstance(raw, (int, float)):
        raise F12F13PrimaryLiabilityStockObservationError(
            f"FORENSIC_NUMERIC_NORMALIZATION_FORBIDDEN:{field}"
        )
    if not isinstance(raw, str):
        raise F12F13PrimaryLiabilityStockObservationError(
            f"FORENSIC_TOKEN_NOT_STRING:{field}:{type(raw).__name__}"
        )
    return {
        "field": field,
        "presence": "STRING",
        "python_type": "str",
        "raw_token": raw,
        "exact_empty_string": TRUE_TOKEN if raw == "" else FALSE_TOKEN,
        "exact_zero_string": TRUE_TOKEN if raw == "0" else FALSE_TOKEN,
        "nonzero_string_token": TRUE_TOKEN if raw not in {"", "0"} else FALSE_TOKEN,
        "empty_zero_null_missing_not_normalized": TRUE_TOKEN,
    }


def _extract_forensic_liability_tokens(*, payload: Mapping[str, Any]) -> dict[str, Any]:
    data = payload.get("data")
    if data is None:
        rows: list[Any] = []
        data_presence = "ABSENT"
    elif not isinstance(data, list):
        raise F12F13PrimaryLiabilityStockObservationError("VENUE_DATA_NOT_LIST")
    else:
        rows = list(data)
        data_presence = "LIST"
    details_out: list[dict[str, Any]] = []
    account_tokens: list[dict[str, str]] = []
    nonzero = False
    if rows and isinstance(rows[0], Mapping):
        account_row = rows[0]
        account_tokens = [
            _classify_raw_token(row=account_row, field=field) for field in U05_RAW_FIELDS
        ]
        nonzero = nonzero or any(
            token["nonzero_string_token"] == TRUE_TOKEN for token in account_tokens
        )
        nested = account_row.get("details")
        if isinstance(nested, list):
            for item in nested:
                if not isinstance(item, Mapping):
                    continue
                ccy_token = _classify_raw_token(row=item, field="ccy")
                field_tokens = [
                    _classify_raw_token(row=item, field=field) for field in U05_RAW_FIELDS
                ]
                nonzero = nonzero or any(
                    token["nonzero_string_token"] == TRUE_TOKEN for token in field_tokens
                )
                details_out.append(
                    {
                        "ccy_presence": ccy_token["presence"],
                        "ccy_raw_token": ccy_token["raw_token"],
                        "tokens": field_tokens,
                    }
                )
    return {
        "layer": "RAW_PRIMARY_EVIDENCE",
        "interpretation_status": "FORBIDDEN",
        "data_presence": data_presence,
        "row_count": str(len(rows)),
        "account_level_u05_tokens": account_tokens,
        "details": details_out,
        "nonzero_liability_observed": TRUE_TOKEN if nonzero else FALSE_TOKEN,
        "empty_or_zero_or_blank_or_missing_does_not_prove_kind_absence": TRUE_TOKEN,
        "nonzero_does_not_prove_equity_stock_source_kind": TRUE_TOKEN,
        "eq_remains_reconciliation_target_only": TRUE_TOKEN,
        "algebraic_eq_identity": "FORBIDDEN",
    }


def _adjudicate_f12_f13(
    *, nonzero_liability_observed: str
) -> tuple[list[dict[str, str]], str, str]:
    if nonzero_liability_observed == TRUE_TOKEN:
        blocker = BLOCKER_NONZERO_UNPROVEN
        blocked_by = KIND_SET_BLOCKED_NONZERO_UNPROVEN
        f12_missing = "RATIFIED_LIABILITY_EQUITY_STOCK_SOURCE_SEMANTICS_AND_AFFECT_PROOF"
        f13_missing = "RATIFIED_EQ_IDENTITY_OR_PROVEN_EMBEDDING_RELATION"
    else:
        blocker = BLOCKER_EMPTY_OR_ZERO
        blocked_by = KIND_SET_BLOCKED_EMPTY_OR_ZERO
        f12_missing = (
            "NONZERO_LIABILITY_STOCK_PRIMARY_OBSERVATION_OR_RATIFIED_EQ_IDENTITY_"
            "EMPTY_OR_ZERO_AFTER_AUTHORIZED_GET_DOES_NOT_PROVE_ABSENCE"
        )
        f13_missing = (
            "RATIFIED_EQ_IDENTITY_OR_PAIRED_LIABILITY_AND_EQ_OBSERVATION_"
            "EMPTY_OR_ZERO_AFTER_AUTHORIZED_GET_DOES_NOT_PROVE_EMBEDDING"
        )
    reject_claimed_f12_f13_proof_from_token_shape_v1(
        claimed_proof="REMAIN_UNKNOWN_PRIMARY_EVIDENCE_DOES_NOT_CARRY_DECISION",
        fact_id="F12_LIABILITY_AFFECTS_EQUITY_STOCK",
    )
    reject_claimed_f12_f13_proof_from_token_shape_v1(
        claimed_proof="REMAIN_UNKNOWN_PRIMARY_EVIDENCE_DOES_NOT_CARRY_DECISION",
        fact_id="F13_LIABILITY_ALREADY_EMBEDDED_IN_EQ",
    )
    facts = [
        {
            "fact_id": "F12_LIABILITY_AFFECTS_EQUITY_STOCK",
            "decision": DECISION_REMAIN_UNKNOWN,
            "status": STATUS_UNKNOWN,
            "kind_candidate": "U05_LIABILITY_AS_CLASSIFIED_EQUITY_STOCK_KIND",
            "kind_disposition": DECISION_REMAIN_UNKNOWN,
            "missing_evidence": f12_missing,
            "selected_observation_surface": AUTHORIZED_SURFACE,
            "new_get_authorized_this_go": TRUE_TOKEN,
            "new_get_consumed": TRUE_TOKEN,
            "repeat_get_for_nonzero_forbidden": TRUE_TOKEN,
            "ratified_eq_identity_present": FALSE_TOKEN,
            "algebraic_inference": "FORBIDDEN",
            "include_from_unknown": "FORBIDDEN",
            "exclude_from_unknown": "FORBIDDEN",
            "empty_or_zero_or_blank_or_missing_does_not_decide": TRUE_TOKEN,
            "nonzero_token_does_not_automatically_include": TRUE_TOKEN,
            "layer": "ADJUDICATED_CONCLUSION",
        },
        {
            "fact_id": "F13_LIABILITY_ALREADY_EMBEDDED_IN_EQ",
            "decision": DECISION_REMAIN_UNKNOWN,
            "status": STATUS_UNKNOWN,
            "kind_candidate": "U05_LIABILITY_AS_CLASSIFIED_EQUITY_STOCK_KIND",
            "kind_disposition": DECISION_REMAIN_UNKNOWN,
            "missing_evidence": f13_missing,
            "selected_observation_surface": AUTHORIZED_SURFACE,
            "new_get_authorized_this_go": TRUE_TOKEN,
            "new_get_consumed": TRUE_TOKEN,
            "repeat_get_for_nonzero_forbidden": TRUE_TOKEN,
            "ratified_eq_identity_present": FALSE_TOKEN,
            "algebraic_inference": "FORBIDDEN",
            "include_from_unknown": "FORBIDDEN",
            "exclude_from_unknown": "FORBIDDEN",
            "empty_or_zero_or_blank_or_missing_does_not_decide": TRUE_TOKEN,
            "nonzero_token_does_not_automatically_prove_embedding": TRUE_TOKEN,
            "layer": "ADJUDICATED_CONCLUSION",
        },
    ]
    return facts, blocker, blocked_by


def execute_f12_f13_primary_liability_stock_observation_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    evidence_root: Path | str,
    genesis_store_root: Path | str | None = None,
    vault_file: Path | str | None = None,
    transport: LiveCanaryTransportV1 | None = None,
    observation_as_of: str | None = None,
) -> F12F13PrimaryLiabilityStockObservationResultV1:
    if owner_go != OWNER_GO:
        raise F12F13PrimaryLiabilityStockObservationError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise F12F13PrimaryLiabilityStockObservationError("ORIGIN_MAIN_SHA_MISMATCH")
    assert_f12_f13_balance_surface_already_selected_v1()
    _assert_standing_pins()
    _preflight_sealed_inputs()
    genesis_root = _preflight_genesis(genesis_store_root=genesis_store_root)
    d4 = load_bound_account_identity_runtime_binding_v1(store_root=genesis_root)
    d5 = load_checkpoint_observation_window_binding_v1(store_root=genesis_root)
    as_of = observation_as_of or _utc_now_z()
    opened_transport, handle, _productive = _open_transport_v1(
        vault_file=vault_file, transport=transport
    )
    client = LiveCanaryHttpClientV1(
        rest_base=REUSED_REST_BASE,
        rest_host=REUSED_BINDING_REST_HOST,
        transport=opened_transport,
        max_request_count=MAX_NETWORK_REQUEST_COUNT,
        max_retries=DEFAULT_MAX_RETRIES,
        timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
    )
    try:
        capture = _one_authorized_balance_get_v1(client=client, handle=handle)
        counters = _assert_get_counters_v1(client=client)
    finally:
        if handle is not None:
            release_live_canary_ephemeral_material_v1(handle)
    body_bytes = bytes(capture["body_bytes"])
    pack_root = Path(evidence_root) / _folder_from_as_of(as_of)
    pack_root.mkdir(parents=True, exist_ok=True)
    _persist_raw_bytes(path=pack_root / RAW_BODY_FILE, body=body_bytes)
    try:
        payload = parse_json_object_v1(body_bytes)
    except LiveCanaryHttpError as exc:
        raise F12F13PrimaryLiabilityStockObservationError(
            f"BALANCE_RESPONSE_NOT_JSON_OBJECT:{exc}"
        ) from exc
    venue_code = payload.get("code")
    venue_msg = payload.get("msg")
    raw_capture = {
        "layer": "RAW_PRIMARY_EVIDENCE",
        "interpretation_status": "FORBIDDEN",
        "method": "GET",
        "endpoint": AUTHORIZED_ENDPOINT,
        "request_surface": AUTHORIZED_SURFACE,
        "host": AUTHORIZED_HOST,
        "query": "",
        "request_utc": str(capture["request_utc"]),
        "response_utc": str(capture["response_utc"]),
        "http_status": str(capture["http_status"]),
        "elapsed_seconds": str(capture["elapsed_seconds"]),
        "venue_code_presence": "ABSENT" if "code" not in payload else "PRESENT",
        "venue_code_python_type": type(venue_code).__name__ if "code" in payload else "MISSING",
        "venue_code_raw_token": venue_code if isinstance(venue_code, str) else "",
        "venue_msg_presence": "ABSENT" if "msg" not in payload else "PRESENT",
        "venue_msg_python_type": type(venue_msg).__name__ if "msg" in payload else "MISSING",
        "venue_msg_raw_token": venue_msg if isinstance(venue_msg, str) else "",
        "response_headers_safe": capture["response_headers_safe"],
        "payload_sha256": _sha256_bytes(body_bytes),
        "body_byte_len": str(len(body_bytes)),
        "raw_body_filename": RAW_BODY_FILE,
        "secrets_or_signatures_persisted": FALSE_TOKEN,
        "genesis_id": EXPECTED_GENESIS_ID,
        "genesis_as_of": EXPECTED_GENESIS_AS_OF,
        "d4_identity_digest": d4.identity_digest,
        "d4_instance_digest": d4.instance_digest,
        "d5_binding_id": d5.binding_id,
        "d4_identity_minted": FALSE_TOKEN,
    }
    _persist_json(path=pack_root / RAW_CAPTURE_FILE, payload=raw_capture)
    forensic = _extract_forensic_liability_tokens(payload=payload)
    _persist_json(path=pack_root / FORENSIC_FILE, payload=forensic)
    facts, blocker, blocked_by = _adjudicate_f12_f13(
        nonzero_liability_observed=str(forensic["nonzero_liability_observed"])
    )
    _persist_json(
        path=pack_root / "observation_authority_v1.json",
        payload={
            "layer": "CANONICAL_AUTHORITY",
            "owner_go": OWNER_GO,
            "observation_authority_validated": TRUE_TOKEN,
            "authorized_get_surfaces": AUTHORIZED_SURFACE,
            "selected_observation_surface_already_present": TRUE_TOKEN,
            "f12_f13_immediate_evidence_fields": ",".join(U05_RAW_FIELDS),
            "account_config_get_authorized": FALSE_TOKEN,
            "bills_get_authorized": FALSE_TOKEN,
            "bills_archive_get_authorized": FALSE_TOKEN,
            "subtypes_get_authorized": FALSE_TOKEN,
            "max_get_count": "1",
            "repeat_get_hoping_for_nonzero_forbidden": TRUE_TOKEN,
            "post_authorized": FALSE_TOKEN,
            "account_mutation_authorized": FALSE_TOKEN,
            "nonzero_liability_creation_authorized": FALSE_TOKEN,
            "f16_f18_primary_observation_authorized": FALSE_TOKEN,
            "standing_observation_network_get_authorized_pin": FALSE_TOKEN,
            "this_go_authorizes_one_balance_get_only": TRUE_TOKEN,
        },
    )
    _persist_json(
        path=pack_root / "prior_adjudication_binding_v1.json",
        payload={
            "layer": "PRIOR_ADJUDICATION",
            "sealed_s1_s5": CANONICAL_SEALED_OBSERVATION_PACK_RELPATH,
            "sealed_s6": CANONICAL_S6_PACK_RELPATH,
            "pr_6452_mapping": CANONICAL_MAPPING_PACK_RELPATH,
            "pr_6453_acquisition": CANONICAL_ACQUISITION_PACK_RELPATH,
            "pr_6454_bg_resolution": CANONICAL_BG_RESOLUTION_PACK_RELPATH,
            "bg_f12_decision": DECISION_REMAIN_UNKNOWN,
            "bg_f13_decision": DECISION_REMAIN_UNKNOWN,
            "bg_earliest_remaining_d6_blocker": BG_EARLIEST_REMAINING_D6_BLOCKER,
            "historical_s2_empty_or_zero_does_not_decide": TRUE_TOKEN,
        },
    )
    _persist_json(
        path=pack_root / ADJUDICATION_FILE,
        payload={
            "layer": "ADJUDICATED_CONCLUSION",
            "facts": facts,
            "f16_decision": DECISION_REMAIN_UNKNOWN,
            "f17_decision": DECISION_REMAIN_UNKNOWN,
            "f18_decision": DECISION_REMAIN_UNKNOWN,
            "f16_f17_f18_not_observed_this_go": TRUE_TOKEN,
            "ratified_source_kinds": NONE_TOKEN,
            "kind_set": KIND_SET_EMPTY,
            "kind_set_resolved": FALSE_TOKEN,
            "raw_eq_source_authority": FALSE_TOKEN,
        },
    )
    _persist_json(
        path=pack_root / "ranked_remaining_d6_blockers_v1.json",
        payload={
            "layer": "UNRESOLVED",
            "narrower_than_bg": TRUE_TOKEN,
            "earliest_remaining_d6_blocker": blocker,
            "kind_set_include_exclude_blocked_by": blocked_by,
            "records": [
                {
                    "rank": "1",
                    "blocker": blocker,
                    "covers_facts": (
                        "F12_LIABILITY_AFFECTS_EQUITY_STOCK,F13_LIABILITY_ALREADY_EMBEDDED_IN_EQ"
                    ),
                    "blocked_by": blocked_by,
                    "role": "EARLIEST_REMAINING_D6_BLOCKER",
                    "new_get_authorized": FALSE_TOKEN,
                    "authorized_get_consumed": TRUE_TOKEN,
                    "repeat_get_hoping_for_nonzero_forbidden": TRUE_TOKEN,
                    "include_exclude_from_unknown": "FORBIDDEN",
                },
                {
                    "rank": "2",
                    "blocker": F16_F17_F18_BLOCKER,
                    "covers_facts": (
                        "F16_FEE_ALREADY_EMBEDDED_IN_EQ,F17_FEE_SEPARATE_ACCOUNT_DELTA,"
                        "F18_FEE_RECONCILIATION_ONLY"
                    ),
                    "new_get_authorized": FALSE_TOKEN,
                    "not_observed_this_go": TRUE_TOKEN,
                },
            ],
        },
    )
    _persist_json(
        path=pack_root / "missing_primary_evidence_v1.json",
        payload={
            "layer": "UNRESOLVED",
            "nonzero_liability_observed": str(forensic["nonzero_liability_observed"]),
            "authorized_fresh_balance_get_consumed": TRUE_TOKEN,
            "empty_or_zero_does_not_prove_absence": TRUE_TOKEN,
            "nonzero_does_not_prove_source_kind": TRUE_TOKEN,
            "ratified_eq_identity_present": FALSE_TOKEN,
            "algebraic_inference": "FORBIDDEN",
            "f16_f18_primary_observation": "NOT_AUTHORIZED_THIS_GO",
        },
    )
    _persist_json(
        path=pack_root / "layers_v1.json",
        payload={
            "CANONICAL_AUTHORITY": "observation_authority_v1.json",
            "RAW_PRIMARY_EVIDENCE": f"{RAW_BODY_FILE},{RAW_CAPTURE_FILE},{FORENSIC_FILE}",
            "PRIOR_ADJUDICATION": "prior_adjudication_binding_v1.json",
            "HISTORICAL_STATE": CANONICAL_BG_RESOLUTION_PACK_RELPATH,
            "NAVIGATION": "NONE",
            "INTERPRETATION": "FORBIDDEN",
            "HYPOTHESIS": "FORBIDDEN",
            "UNRESOLVED": "ranked_remaining_d6_blockers_v1.json,missing_primary_evidence_v1.json",
        },
    )
    claims = {
        "OWNER_GO": OWNER_GO,
        "OWNER_GO_STATUS": "CONSUMED",
        "GENESIS_ID": EXPECTED_GENESIS_ID,
        "GENESIS_AS_OF": EXPECTED_GENESIS_AS_OF,
        "OBSERVATION_AS_OF": as_of,
        "OBSERVATION_AUTHORITY_VALIDATED": TRUE_TOKEN,
        "AUTHORIZED_GET_SURFACES": AUTHORIZED_SURFACE,
        "GET_COUNT": "1",
        "POST_COUNT": "0",
        "ACCOUNT_MUTATION_PERFORMED": FALSE_TOKEN,
        "HTTP_STATUS": str(capture["http_status"]),
        "NONZERO_LIABILITY_OBSERVED": str(forensic["nonzero_liability_observed"]),
        "RAW_EVIDENCE_SEALED": TRUE_TOKEN,
        "F12_DECISION": DECISION_REMAIN_UNKNOWN,
        "F13_DECISION": DECISION_REMAIN_UNKNOWN,
        "F16_DECISION": DECISION_REMAIN_UNKNOWN,
        "F17_DECISION": DECISION_REMAIN_UNKNOWN,
        "F18_DECISION": DECISION_REMAIN_UNKNOWN,
        "RATIFIED_SOURCE_KINDS": NONE_TOKEN,
        "KIND_SET": KIND_SET_EMPTY,
        "KIND_SET_RESOLVED": FALSE_TOKEN,
        "KIND_SET_INCLUDE_EXCLUDE_BLOCKED_BY": blocked_by,
        "EARLIEST_REMAINING_D6_BLOCKER": blocker,
        "RAW_EQ_SOURCE_AUTHORITY": FALSE_TOKEN,
        "U05_KIND_DECISION": DECISION_REMAIN_UNKNOWN,
        "U06_KIND_DECISION": DECISION_REMAIN_UNKNOWN,
        "RESIDUAL_KIND_DECISION": DECISION_REMAIN_UNKNOWN,
        "RETENTION_COVERAGE_STATUS": RETENTION_FAIL_CLOSED,
        "ORDERING_COMPLETENESS_STATUS": ORDERING_FAIL_CLOSED,
        "AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM": FALSE_TOKEN,
        "COMPLETE_CLASSIFIED_EVENT_STREAM_PROVEN": FALSE_TOKEN,
        "MS2_AUTHORIZED": FALSE_TOKEN,
        "D6_FULLY_CLOSED": FALSE_TOKEN,
        "D7_AUTHORIZED": FALSE_TOKEN,
        "D4_IDENTITY_MINTED": FALSE_TOKEN,
        "EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED": FALSE_TOKEN,
        "OBSERVATION_NETWORK_GET_AUTHORIZED": FALSE_TOKEN,
        "NETWORK_POST_PERFORMED": FALSE_TOKEN,
        "GET_REQUEST_COUNT": str(counters.get("GET_REQUEST_COUNT")),
        "PAYLOAD_SHA256": _sha256_bytes(body_bytes),
        "AUTHORITY_EFFECT": "NONE",
    }
    _persist_json(path=pack_root / CLAIMS_FILE, payload=claims)
    _persist_json(
        path=pack_root / "LINEAGE.json",
        payload={
            "owner_go": OWNER_GO,
            "origin_main_sha": origin_main_sha,
            "genesis_id": EXPECTED_GENESIS_ID,
            "d4_identity_digest": d4.identity_digest,
            "parent_bg_resolution": CANONICAL_BG_RESOLUTION_PACK_RELPATH,
            "authorized_endpoint": AUTHORIZED_ENDPOINT,
        },
    )
    manifest = persist_manifest_sha256_v1(store_root=pack_root)
    if verify_manifest_sha256_v1(store_root=pack_root) != 0:
        raise F12F13PrimaryLiabilityStockObservationError("MANIFEST_VERIFY_NOT_ZERO")
    return F12F13PrimaryLiabilityStockObservationResultV1(
        genesis_id=EXPECTED_GENESIS_ID,
        genesis_as_of=EXPECTED_GENESIS_AS_OF,
        observation_as_of=as_of,
        store_root=str(pack_root),
        authorized_get_surfaces=AUTHORIZED_SURFACE,
        get_count="1",
        post_count="0",
        account_mutation_performed=FALSE_TOKEN,
        nonzero_liability_observed=str(forensic["nonzero_liability_observed"]),
        raw_evidence_sealed=TRUE_TOKEN,
        f12_decision=DECISION_REMAIN_UNKNOWN,
        f13_decision=DECISION_REMAIN_UNKNOWN,
        f16_decision=DECISION_REMAIN_UNKNOWN,
        f17_decision=DECISION_REMAIN_UNKNOWN,
        f18_decision=DECISION_REMAIN_UNKNOWN,
        ratified_source_kinds=NONE_TOKEN,
        kind_set=KIND_SET_EMPTY,
        kind_set_resolved=FALSE_TOKEN,
        raw_eq_source_authority=FALSE_TOKEN,
        retention_coverage_status=RETENTION_FAIL_CLOSED,
        ordering_completeness_status=ORDERING_FAIL_CLOSED,
        complete_classified_event_stream_proven=FALSE_TOKEN,
        earliest_remaining_d6_blocker=blocker,
        ms2_authorized=FALSE_TOKEN,
        d6_fully_closed=FALSE_TOKEN,
        d7_authorized=FALSE_TOKEN,
        evidence_manifest=str(manifest),
    )
