"""GATE_A independently attested productive nonzero liability-stock.

Executes the already persisted GATE_A reopen gate: exactly one
Owner-GO-scoped READ-ONLY GET /api/v5/account/balance on the bound D4
account. Reuses the BH balance GET seam. Does not POST. Does not GET
bills, positions, or any other surface. Does not retry. Zero/empty/
absent is not absence proof. Nonzero is not automatic INCLUDE.
get_alone_may_include=false and get_alone_may_exclude=false remain
binding. Venue eq remains non-source. AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_ENABLED,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY as DAG_PIN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.bound_account_identity_runtime_binding_v1 import (
    load_bound_account_identity_runtime_binding_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.checkpoint_observation_window_binding_contract_v1 import (
    load_checkpoint_observation_window_binding_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    C17_CREATED,
    D6_FULLY_CLOSED,
    D7_AUTHORIZED,
    KIND_SET_RESOLVED,
    MS2_AUTHORIZED,
    RAW_EQ_SOURCE_AUTHORITY,
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
from src.ops.governed_productive_account_equity_authority_producer_v1.f12_f13_kind_set_remaining_unknown_pin_and_reopen_gate_v1 import (
    CANONICAL_PACK_RELPATH as CANONICAL_BJ_PACK_RELPATH,
    GATE_A_ID,
    GATE_B_ID,
    SELECTED_BALANCE_SURFACE,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.f12_f13_primary_liability_stock_observation_v1 import (
    AUTHORIZED_ENDPOINT,
    AUTHORIZED_HOST,
    AUTHORIZED_SURFACE,
    FORBIDDEN_ENDPOINTS,
    MAX_NETWORK_REQUEST_COUNT,
    REUSED_REST_BASE,
    U05_RAW_FIELDS,
    F12F13PrimaryLiabilityStockObservationError,
    _assert_get_counters_v1,
    _extract_forensic_liability_tokens,
    _one_authorized_balance_get_v1,
    _open_transport_v1,
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
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    ENDPOINT_ACCOUNT_BALANCE,
    ENDPOINT_ACCOUNT_BILLS,
    REUSED_BINDING_REST_HOST,
    USER_AGENT_CANARY,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    LiveCanaryHttpClientV1,
    LiveCanaryHttpError,
    LiveCanaryTransportV1,
    parse_json_object_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.live_credential_ephemeral_v1 import (
    release_live_canary_ephemeral_material_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.credential_presence_v1 import (
    default_vault_path_v1,
    inspect_credential_material_presence_v1,
)

OWNER_GO = "OWNER_GO_FULL_CORE_OPTION_D_GATE_A_INDEPENDENTLY_ATTESTED_PRODUCTIVE_NONZERO_LIABILITY_STOCK_V1"
EXPECTED_ORIGIN_MAIN_SHA = "6ee0df2c645b66afa9c9e6b45482d276c241d42a"
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_option_d_gate_a_independently_attested_productive_"
    "nonzero_liability_stock_v1/2026-09-14T200500Z"
)
CANONICAL_PERSIST_AS_OF = "2026-09-14T20:05:00Z"
CANONICAL_BH_PACK_RELPATH = (
    "evidence/ops/full_core_d6_f12_f13_primary_liability_stock_observation_v1/2026-09-13T221500Z"
)
CANONICAL_BW_PACK_RELPATH = (
    "evidence/ops/full_core_live_equity_stock_today_initial_stock_kind_set_"
    "membership_wp1/2026-09-14T212500Z"
)
SCHEMA_CLASS = "GATE_A_INDEPENDENTLY_ATTESTED_PRODUCTIVE_NONZERO_LIABILITY_STOCK_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
NONE_TOKEN = "NONE"
KIND_SET_EMPTY = "EMPTY_FAIL_CLOSED"
STATUS_EXECUTED_QUALIFYING = "EXECUTED_QUALIFYING"
STATUS_EXECUTED_NONQUALIFYING = "EXECUTED_NONQUALIFYING"
SECRET_MARKERS: tuple[str, ...] = (
    "ok-access",
    "api_secret",
    "api-secret",
    "passphrase",
    "secretref://",
)
PREREQUISITE = (
    "INDEPENDENTLY_ATTESTED_GENUINE_PRODUCTIVE_NONZERO_LIABILITY_STOCK_ON_BOUND_D4_ACCOUNT"
)
COVERAGE_SNAPSHOT = "SINGLE_BALANCE_GET_SNAPSHOT_NOT_EVENT_STREAM_COVERAGE"
INDEPENDENCE_INDEPENDENT = "INDEPENDENT_OF_EQ_LIABILITY_FIELDS_ONLY"
BASIS_NONZERO_REOPEN = (
    "PRODUCTIVE_NONZERO_INDEPENDENTLY_ATTESTED_ON_BOUND_D4_ACCOUNT_"
    "SOURCE_SEMANTICS_AND_EMBEDDING_UNPROVEN_GET_ALONE_MAY_NOT_INCLUDE"
)
BASIS_NONQUALIFYING = (
    "EMPTY_ZERO_ABSENT_DOES_NOT_MEET_PRODUCTIVE_NONZERO_THRESHOLD_AND_DOES_NOT_PROVE_ABSENCE"
)
NEXT_OWNER_GO_AFTER_NONQUALIFYING = (
    "OWNER_GO_FULL_CORE_OPTION_D_GATE_B_NEWLY_BOUND_UNIQUE_EXTERNAL_EQ_COMPOSITION_AUTHORITY_V1"
)
NEXT_OWNER_GO_AFTER_QUALIFYING = (
    "OWNER_GO_REQUIRED_TO_DECIDE_U05_WITH_SOURCE_SEMANTICS_AND_EMBEDDING_PROOF"
)
VAULT_RELATIVE = (
    ".ops_local/section_11_13_5_live_canary_minimum_exposure/secrets/secretref_vault.json"
)
DEFAULT_TIMEOUT_SECONDS = 10.0
DEFAULT_MAX_RETRIES = 0
RAW_BODY_FILE = "raw_account_balance_response_body.json"
RAW_CAPTURE_FILE = "raw_http_capture_v1.json"
FORENSIC_FILE = "forensic_liability_tokens_v1.json"
CLAIMS_FILE = "claims.json"
FORBIDDEN_EQ_SOURCE_FIELDS: tuple[str, ...] = (
    "eq",
    "totalEq",
    "availEq",
    "adjEq",
    "availBal",
    "cashBal",
)
_REPO_ROOT = Path(__file__).resolve().parents[3]


class GateAIndependentlyAttestedProductiveNonzeroLiabilityStockError(ValueError):
    """Fail-closed GATE_A execution violation."""


@dataclass(frozen=True)
class GateAIndependentlyAttestedProductiveNonzeroLiabilityStockResultV1:
    genesis_id: str
    genesis_as_of: str
    persist_as_of: str
    store_root: str
    gate_a_id: str
    authorized_surface: str
    authorized_get_count: str
    actual_get_count: str
    post_count: str
    http_status: str
    venue_code: str
    gate_a_execution_status: str
    gate_a_raw_evidence_status: str
    gate_a_coverage_status: str
    gate_a_independence_status: str
    gate_a_productive_nonzero_liability_proven: str
    gate_a_evidence_id: str
    gate_a_evidence_digest: str
    u05_reopened_decision_capable: str
    u05_decision_after: str
    u05_decision_basis: str
    u06_decision: str
    residual_class_decision: str
    evidence_manifest: str


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


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


def _sha256_bytes(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def _folder_from_as_of(as_of: str) -> str:
    return as_of.replace(":", "")


def _assert_no_secret_material(*, blob: bytes, label: str) -> None:
    lowered = blob.lower()
    for marker in SECRET_MARKERS:
        if marker.encode("utf-8") in lowered:
            raise GateAIndependentlyAttestedProductiveNonzeroLiabilityStockError(
                f"SECRET_MARKER_IN_{label}"
            )


def _assert_standing_pins() -> None:
    if LIVE_ENABLED is not False:
        raise GateAIndependentlyAttestedProductiveNonzeroLiabilityStockError(
            "LIVE_ENABLED_NOT_FALSE"
        )
    if LIVE_ARMED is not False:
        raise GateAIndependentlyAttestedProductiveNonzeroLiabilityStockError("LIVE_ARMED_NOT_FALSE")
    if WIRE_SEND_PERMITTED is not False:
        raise GateAIndependentlyAttestedProductiveNonzeroLiabilityStockError(
            "WIRE_SEND_PERMITTED_NOT_FALSE"
        )
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        raise GateAIndependentlyAttestedProductiveNonzeroLiabilityStockError(
            "RAW_EQ_SOURCE_AUTHORITY_NOT_FALSE"
        )
    if MS2_AUTHORIZED is not False:
        raise GateAIndependentlyAttestedProductiveNonzeroLiabilityStockError(
            "MS2_AUTHORIZED_NOT_FALSE"
        )
    if D6_FULLY_CLOSED is not False:
        raise GateAIndependentlyAttestedProductiveNonzeroLiabilityStockError(
            "D6_FULLY_CLOSED_NOT_FALSE"
        )
    if D7_AUTHORIZED is not False:
        raise GateAIndependentlyAttestedProductiveNonzeroLiabilityStockError(
            "D7_AUTHORIZED_NOT_FALSE"
        )
    if C17_CREATED is not False:
        raise GateAIndependentlyAttestedProductiveNonzeroLiabilityStockError(
            "C17_CREATED_NOT_FALSE"
        )
    if KIND_SET_RESOLVED is not False:
        raise GateAIndependentlyAttestedProductiveNonzeroLiabilityStockError(
            "KIND_SET_RESOLVED_NOT_FALSE"
        )
    if RATIFIED_CLASSIFIED_KIND_SET:
        raise GateAIndependentlyAttestedProductiveNonzeroLiabilityStockError(
            "CLASSIFIED_KIND_SET_MUST_REMAIN_EMPTY_FAIL_CLOSED"
        )
    if DAG_PIN != "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING":
        raise GateAIndependentlyAttestedProductiveNonzeroLiabilityStockError("DAG_PIN_DRIFT")
    if AUTHORIZED_ENDPOINT != ENDPOINT_ACCOUNT_BALANCE:
        raise GateAIndependentlyAttestedProductiveNonzeroLiabilityStockError("ENDPOINT_DRIFT")
    if AUTHORIZED_SURFACE != SELECTED_BALANCE_SURFACE:
        raise GateAIndependentlyAttestedProductiveNonzeroLiabilityStockError("SURFACE_DRIFT")
    if AUTHORIZED_ENDPOINT in FORBIDDEN_ENDPOINTS:
        raise GateAIndependentlyAttestedProductiveNonzeroLiabilityStockError(
            "AUTHORIZED_ENDPOINT_MARKED_FORBIDDEN"
        )
    if ENDPOINT_ACCOUNT_BILLS not in FORBIDDEN_ENDPOINTS:
        raise GateAIndependentlyAttestedProductiveNonzeroLiabilityStockError(
            "BILLS_MUST_REMAIN_FORBIDDEN"
        )
    if REUSED_BINDING_REST_HOST != AUTHORIZED_HOST:
        raise GateAIndependentlyAttestedProductiveNonzeroLiabilityStockError("HOST_MISMATCH")
    if USER_AGENT_CANARY.strip() == "":
        raise GateAIndependentlyAttestedProductiveNonzeroLiabilityStockError("USER_AGENT_MISSING")


def _load_json_object(*, path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise GateAIndependentlyAttestedProductiveNonzeroLiabilityStockError(
            f"JSON_NOT_OBJECT:{path.name}"
        )
    return payload


def _assert_bj_gate_a_binding(*, sealed_bj_pack: Path) -> None:
    if verify_manifest_sha256_v1(store_root=sealed_bj_pack) != 0:
        raise GateAIndependentlyAttestedProductiveNonzeroLiabilityStockError("BJ_MANIFEST_MISMATCH")
    gates = _load_json_object(path=sealed_bj_pack / "reopen_gates_v1.json")
    records = gates.get("records")
    if not isinstance(records, list):
        raise GateAIndependentlyAttestedProductiveNonzeroLiabilityStockError("BJ_GATES_NOT_LIST")
    gate_a = next((item for item in records if item.get("gate_id") == GATE_A_ID), None)
    if not isinstance(gate_a, Mapping):
        raise GateAIndependentlyAttestedProductiveNonzeroLiabilityStockError(
            "GATE_A_RECORD_MISSING"
        )
    if str(gate_a.get("prerequisite") or "") != PREREQUISITE:
        raise GateAIndependentlyAttestedProductiveNonzeroLiabilityStockError(
            "GATE_A_PREREQUISITE_DRIFT"
        )
    if str(gate_a.get("authorized_surface_if_later_go") or "") != SELECTED_BALANCE_SURFACE:
        raise GateAIndependentlyAttestedProductiveNonzeroLiabilityStockError("GATE_A_SURFACE_DRIFT")
    if str(gate_a.get("max_get_count_if_later_go") or "") != "1":
        raise GateAIndependentlyAttestedProductiveNonzeroLiabilityStockError("GATE_A_MAX_GET_DRIFT")
    if str(gate_a.get("hope_get_forbidden") or "") != TRUE_TOKEN:
        raise GateAIndependentlyAttestedProductiveNonzeroLiabilityStockError(
            "HOPE_GET_NOT_FORBIDDEN"
        )
    if str(gate_a.get("post_borrow_account_mutation_forbidden") or "") != TRUE_TOKEN:
        raise GateAIndependentlyAttestedProductiveNonzeroLiabilityStockError(
            "POST_BORROW_MUTATION_NOT_FORBIDDEN"
        )
    if str(gate_a.get("get_alone_may_include") or "") != FALSE_TOKEN:
        raise GateAIndependentlyAttestedProductiveNonzeroLiabilityStockError(
            "GET_ALONE_MAY_INCLUDE_NOT_FALSE"
        )
    if str(gate_a.get("get_alone_may_exclude") or "") != FALSE_TOKEN:
        raise GateAIndependentlyAttestedProductiveNonzeroLiabilityStockError(
            "GET_ALONE_MAY_EXCLUDE_NOT_FALSE"
        )
    if (
        str(
            gate_a.get("nonzero_zero_empty_insufficient_without_source_semantics_and_embedding")
            or ""
        )
        != TRUE_TOKEN
    ):
        raise GateAIndependentlyAttestedProductiveNonzeroLiabilityStockError(
            "NONZERO_INSUFFICIENT_PIN_DRIFT"
        )
    gate_b = next((item for item in records if item.get("gate_id") == GATE_B_ID), None)
    if not isinstance(gate_b, Mapping):
        raise GateAIndependentlyAttestedProductiveNonzeroLiabilityStockError(
            "GATE_B_RECORD_MISSING"
        )
    if str(gate_b.get("executed_this_go") or "") != FALSE_TOKEN:
        raise GateAIndependentlyAttestedProductiveNonzeroLiabilityStockError(
            "GATE_B_MUST_REMAIN_UNEXECUTED"
        )


def _assert_eq_not_used_as_source(*, forensic: Mapping[str, Any]) -> None:
    blob = _canonical_json(forensic)
    for field in FORBIDDEN_EQ_SOURCE_FIELDS:
        if f'"field":"{field}"' in blob:
            raise GateAIndependentlyAttestedProductiveNonzeroLiabilityStockError(
                f"EQ_FIELD_USED_AS_LIABILITY_SOURCE:{field}"
            )


def _adjudicate_gate_a(*, nonzero_liability_observed: str) -> dict[str, str]:
    if nonzero_liability_observed == TRUE_TOKEN:
        return {
            "gate_a_execution_status": STATUS_EXECUTED_QUALIFYING,
            "gate_a_productive_nonzero_liability_proven": TRUE_TOKEN,
            "u05_reopened_decision_capable": TRUE_TOKEN,
            "u05_decision_after": DECISION_REMAIN_UNKNOWN,
            "u05_decision_basis": BASIS_NONZERO_REOPEN,
            "next_owner_go_required": NEXT_OWNER_GO_AFTER_QUALIFYING,
        }
    if nonzero_liability_observed != FALSE_TOKEN:
        raise GateAIndependentlyAttestedProductiveNonzeroLiabilityStockError(
            f"NONZERO_TOKEN_MALFORMED:{nonzero_liability_observed}"
        )
    return {
        "gate_a_execution_status": STATUS_EXECUTED_NONQUALIFYING,
        "gate_a_productive_nonzero_liability_proven": FALSE_TOKEN,
        "u05_reopened_decision_capable": FALSE_TOKEN,
        "u05_decision_after": DECISION_REMAIN_UNKNOWN,
        "u05_decision_basis": BASIS_NONQUALIFYING,
        "next_owner_go_required": NEXT_OWNER_GO_AFTER_NONQUALIFYING,
    }


def execute_gate_a_independently_attested_productive_nonzero_liability_stock_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    evidence_root: Path | str,
    repo_root: Path | str | None = None,
    genesis_store_root: Path | str | None = None,
    sealed_bj_pack: Path | str | None = None,
    vault_file: Path | str | None = None,
    transport: LiveCanaryTransportV1 | None = None,
    persist_as_of: str | None = None,
) -> GateAIndependentlyAttestedProductiveNonzeroLiabilityStockResultV1:
    if owner_go != OWNER_GO:
        raise GateAIndependentlyAttestedProductiveNonzeroLiabilityStockError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise GateAIndependentlyAttestedProductiveNonzeroLiabilityStockError(
            "ORIGIN_MAIN_SHA_MISMATCH"
        )
    _assert_standing_pins()
    repo = Path(repo_root) if repo_root is not None else _REPO_ROOT
    bj_pack = (
        Path(sealed_bj_pack) if sealed_bj_pack is not None else repo / CANONICAL_BJ_PACK_RELPATH
    )
    _assert_bj_gate_a_binding(sealed_bj_pack=bj_pack)
    genesis_root = (
        Path(genesis_store_root)
        if genesis_store_root is not None
        else resolve_canonical_d4_d5_genesis_runtime_store_root_v1(repo_root=repo)
    )
    if genesis_root is None:
        raise GateAIndependentlyAttestedProductiveNonzeroLiabilityStockError("GENESIS_STORE_ABSENT")
    d4 = load_bound_account_identity_runtime_binding_v1(store_root=genesis_root)
    d5 = load_checkpoint_observation_window_binding_v1(store_root=genesis_root)
    as_of = persist_as_of or CANONICAL_PERSIST_AS_OF
    productive = transport is None
    resolved_vault: Path | None = None
    if productive:
        resolved_vault = (
            Path(vault_file) if vault_file is not None else default_vault_path_v1(repo_root=repo)
        )
        presence = inspect_credential_material_presence_v1(vault_file=resolved_vault)
        if presence.get("VALUES_INCLUDED") is not False:
            raise GateAIndependentlyAttestedProductiveNonzeroLiabilityStockError(
                "SECRET_VALUES_MUST_NOT_BE_INCLUDED"
            )
        if presence.get("available") is not True:
            raise GateAIndependentlyAttestedProductiveNonzeroLiabilityStockError(
                f"VAULT_UNAVAILABLE:{presence.get('reason')}"
            )
    try:
        opened_transport, handle, _productive = _open_transport_v1(
            vault_file=resolved_vault, transport=transport
        )
    except F12F13PrimaryLiabilityStockObservationError as exc:
        raise GateAIndependentlyAttestedProductiveNonzeroLiabilityStockError(str(exc)) from exc
    client = LiveCanaryHttpClientV1(
        rest_base=REUSED_REST_BASE,
        rest_host=REUSED_BINDING_REST_HOST,
        transport=opened_transport,
        max_request_count=MAX_NETWORK_REQUEST_COUNT,
        max_retries=DEFAULT_MAX_RETRIES,
        timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
    )
    try:
        try:
            capture = _one_authorized_balance_get_v1(client=client, handle=handle)
            counters = _assert_get_counters_v1(client=client)
        except F12F13PrimaryLiabilityStockObservationError as exc:
            raise GateAIndependentlyAttestedProductiveNonzeroLiabilityStockError(
                f"GATE_A_BALANCE_GET_FAILED:{exc}"
            ) from exc
        except LiveCanaryHttpError as exc:
            raise GateAIndependentlyAttestedProductiveNonzeroLiabilityStockError(
                f"GATE_A_BALANCE_GET_FAILED:{exc}"
            ) from exc
    finally:
        if handle is not None:
            release_live_canary_ephemeral_material_v1(handle)
    http_status_int = int(capture["http_status"])
    if http_status_int != 200:
        raise GateAIndependentlyAttestedProductiveNonzeroLiabilityStockError(
            f"GATE_A_BALANCE_GET_FAILED:HTTP_STATUS:{http_status_int}"
        )
    body_bytes = bytes(capture["body_bytes"])
    _assert_no_secret_material(blob=body_bytes, label="RAW_BODY")
    try:
        payload = parse_json_object_v1(body_bytes)
    except LiveCanaryHttpError as exc:
        raise GateAIndependentlyAttestedProductiveNonzeroLiabilityStockError(
            f"BALANCE_RESPONSE_NOT_JSON_OBJECT:{exc}"
        ) from exc
    venue_code = payload.get("code")
    venue_code_token = venue_code if isinstance(venue_code, str) else ""
    if venue_code_token != "0":
        raise GateAIndependentlyAttestedProductiveNonzeroLiabilityStockError(
            f"GATE_A_BALANCE_GET_FAILED:VENUE_CODE:{venue_code_token or 'MISSING'}"
        )
    try:
        forensic = _extract_forensic_liability_tokens(payload=payload)
    except F12F13PrimaryLiabilityStockObservationError as exc:
        raise GateAIndependentlyAttestedProductiveNonzeroLiabilityStockError(
            f"GATE_A_FORENSIC_EXTRACT_FAILED:{exc}"
        ) from exc
    _assert_eq_not_used_as_source(forensic=forensic)
    adjudication = _adjudicate_gate_a(
        nonzero_liability_observed=str(forensic["nonzero_liability_observed"])
    )
    store = Path(evidence_root) / _folder_from_as_of(as_of)
    store.mkdir(parents=True, exist_ok=True)
    evidence_id = f"GATE_A_{EXPECTED_GENESIS_ID}_{_folder_from_as_of(as_of)}"
    qualification = {
        "layer": "ADJUDICATED_CONCLUSION",
        "gate_a_id": GATE_A_ID,
        "prerequisite": PREREQUISITE,
        "authorized_surface": AUTHORIZED_SURFACE,
        "d4_identity_digest": d4.identity_digest,
        "d4_instance_digest": d4.instance_digest,
        "d5_binding_id": d5.binding_id,
        "nonzero_liability_observed": str(forensic["nonzero_liability_observed"]),
        "independence_status": INDEPENDENCE_INDEPENDENT,
        "coverage_status": COVERAGE_SNAPSHOT,
        "get_alone_may_include": FALSE_TOKEN,
        "get_alone_may_exclude": FALSE_TOKEN,
        "eq_used_as_source": FALSE_TOKEN,
        "source_semantics_proven": FALSE_TOKEN,
        "embedding_proven": FALSE_TOKEN,
        **adjudication,
    }
    evidence_digest = hashlib.sha256(_canonical_json(qualification).encode("utf-8")).hexdigest()
    qualification["gate_a_evidence_id"] = evidence_id
    qualification["gate_a_evidence_digest"] = evidence_digest
    venue_code_raw = venue_code_token if venue_code_token else NONE_TOKEN
    http_status = str(capture["http_status"])
    _persist_raw_bytes(path=store / RAW_BODY_FILE, body=body_bytes)
    _persist_json(
        path=store / RAW_CAPTURE_FILE,
        payload={
            "layer": "RAW_PRIMARY_EVIDENCE",
            "interpretation_status": "FORBIDDEN",
            "method": "GET",
            "endpoint": AUTHORIZED_ENDPOINT,
            "request_surface": AUTHORIZED_SURFACE,
            "host": AUTHORIZED_HOST,
            "query": "",
            "request_utc": str(capture["request_utc"]),
            "response_utc": str(capture["response_utc"]),
            "http_status": http_status,
            "elapsed_seconds": str(capture["elapsed_seconds"]),
            "venue_code_raw_token": venue_code_token,
            "payload_sha256": _sha256_bytes(body_bytes),
            "body_byte_len": str(len(body_bytes)),
            "raw_body_filename": RAW_BODY_FILE,
            "secrets_or_signatures_persisted": FALSE_TOKEN,
            "response_headers_safe": capture["response_headers_safe"],
            "genesis_id": EXPECTED_GENESIS_ID,
            "d4_identity_digest": d4.identity_digest,
        },
    )
    _persist_json(path=store / FORENSIC_FILE, payload=forensic)
    _persist_json(
        path=store / "gate_a_authority_binding_v1.json",
        payload={
            "layer": "CANONICAL_AUTHORITY",
            "owner_go": OWNER_GO,
            "gate_a_id": GATE_A_ID,
            "prerequisite": PREREQUISITE,
            "authorized_surface": AUTHORIZED_SURFACE,
            "max_get_count": "1",
            "post_count_allowed": "0",
            "hope_get_forbidden": TRUE_TOKEN,
            "bills_authorized": FALSE_TOKEN,
            "positions_authorized": FALSE_TOKEN,
            "retry_authorized": FALSE_TOKEN,
            "gate_b_executed": FALSE_TOKEN,
            "this_go_authorizes_one_balance_get_only": TRUE_TOKEN,
            "sealed_bj_pack": str(Path(CANONICAL_BJ_PACK_RELPATH)),
        },
    )
    _persist_json(path=store / "gate_a_qualification_v1.json", payload=qualification)
    _persist_json(
        path=store / "u05_epistemic_before_after_v1.json",
        payload={
            "layer": "ADJUDICATED_CONCLUSION",
            "u05_status_before": DECISION_REMAIN_UNKNOWN,
            "u05_reopened_decision_capable": adjudication["u05_reopened_decision_capable"],
            "u05_decision_after": adjudication["u05_decision_after"],
            "u05_decision_basis": adjudication["u05_decision_basis"],
            "u06_decision": DECISION_REMAIN_UNKNOWN,
            "residual_class_decision": DECISION_REMAIN_UNKNOWN,
            "include_from_unknown": "FORBIDDEN",
            "exclude_from_unknown": "FORBIDDEN",
        },
    )
    _persist_json(
        path=store / "source_vs_evidence_vs_witness_v1.json",
        payload={
            "layer": "CANONICAL_AUTHORITY",
            "source_authority": "NOT_DECLARED",
            "acquisition_evidence": AUTHORIZED_SURFACE,
            "venue_eq_role": "RECONCILIATION_TARGET_ONLY",
            "venue_eq_source_authority": FALSE_TOKEN,
            "raw_eq_source_authority": FALSE_TOKEN,
            "today_initial_stock_is_not_flow": TRUE_TOKEN,
            "account_bills_current_noncanonical": TRUE_TOKEN,
        },
    )
    _persist_json(
        path=store / "layers_v1.json",
        payload={
            "CANONICAL_AUTHORITY": "gate_a_authority_binding_v1.json",
            "FORENSIC_RAW_EVIDENCE": f"{RAW_CAPTURE_FILE},{FORENSIC_FILE},{RAW_BODY_FILE}",
            "ADJUDICATED_CONCLUSION": "gate_a_qualification_v1.json,u05_epistemic_before_after_v1.json",
            "HISTORICAL": "LINEAGE.json",
            "NAVIGATION": "FORBIDDEN_AS_AUTHORITY",
            "INTERPRETATION": "FORBIDDEN",
            "HYPOTHESIS": "FORBIDDEN",
            "UNRESOLVED_OR_CONTRADICTORY": "U05_REMAIN_UNKNOWN_UNTIL_SOURCE_SEMANTICS_AND_EMBEDDING",
        },
    )
    _persist_json(
        path=store / "protected_surfaces_v1.json",
        payload={
            "master_v2_unchanged": TRUE_TOKEN,
            "double_play_unchanged": TRUE_TOKEN,
            "bull_bear_state_switch_unchanged": TRUE_TOKEN,
            "full_core_autonomy_unchanged": TRUE_TOKEN,
            "self_learning_unchanged": TRUE_TOKEN,
            "top20_unchanged": TRUE_TOKEN,
            "execution_arming_wire_unchanged": TRUE_TOKEN,
            "treasury_unchanged": TRUE_TOKEN,
            "step_29p_unchanged": TRUE_TOKEN,
            "reconstruction_implemented": FALSE_TOKEN,
            "ms2_authorized": FALSE_TOKEN,
            "dag_pin": DAG_PIN,
        },
    )
    _persist_json(
        path=store / "LINEAGE.json",
        payload={
            "owner_go": OWNER_GO,
            "origin_main_sha": origin_main_sha,
            "genesis_id": EXPECTED_GENESIS_ID,
            "genesis_as_of": EXPECTED_GENESIS_AS_OF,
            "persist_as_of": as_of,
            "parent_bj_pack": CANONICAL_BJ_PACK_RELPATH,
            "parent_bh_pack": CANONICAL_BH_PACK_RELPATH,
            "parent_bw_pack": CANONICAL_BW_PACK_RELPATH,
            "gate_a_evidence_id": evidence_id,
            "gate_a_evidence_digest": evidence_digest,
            "d4_identity_digest": d4.identity_digest,
            "reconstruction_source_authority": FALSE_TOKEN,
        },
    )
    claims = {
        "OWNER_GO": OWNER_GO,
        "OWNER_GO_STATUS": "CONSUMED",
        "SCHEMA_CLASS": SCHEMA_CLASS,
        "CONTRACT_VERSION": CONTRACT_VERSION,
        "AUTHORITY_EFFECT": AUTHORITY_EFFECT,
        "GENESIS_ID": EXPECTED_GENESIS_ID,
        "GENESIS_AS_OF": EXPECTED_GENESIS_AS_OF,
        "PERSIST_AS_OF": as_of,
        "GATE_A_ID": GATE_A_ID,
        "GATE_A_EXECUTED": TRUE_TOKEN,
        "GATE_B_EXECUTED": FALSE_TOKEN,
        "AUTHORIZED_GET_SURFACES": AUTHORIZED_SURFACE,
        "AUTHORIZED_GET_COUNT": "1",
        "ACTUAL_GET_COUNT": str(counters.get("GET_REQUEST_COUNT", "1")),
        "POST_COUNT": "0",
        "HTTP_STATUS": http_status,
        "VENUE_CODE": venue_code_raw,
        "GATE_A_EXECUTION_STATUS": adjudication["gate_a_execution_status"],
        "GATE_A_RAW_EVIDENCE_STATUS": "SEALED",
        "GATE_A_COVERAGE_STATUS": COVERAGE_SNAPSHOT,
        "GATE_A_INDEPENDENCE_STATUS": INDEPENDENCE_INDEPENDENT,
        "GATE_A_PRODUCTIVE_NONZERO_LIABILITY_PROVEN": adjudication[
            "gate_a_productive_nonzero_liability_proven"
        ],
        "GATE_A_EVIDENCE_ID": evidence_id,
        "GATE_A_EVIDENCE_DIGEST": evidence_digest,
        "U05_STATUS_BEFORE": DECISION_REMAIN_UNKNOWN,
        "U05_REOPENED_DECISION_CAPABLE": adjudication["u05_reopened_decision_capable"],
        "U05_DECISION_AFTER": adjudication["u05_decision_after"],
        "U05_DECISION_BASIS": adjudication["u05_decision_basis"],
        "U06_DECISION": DECISION_REMAIN_UNKNOWN,
        "RESIDUAL_CLASS_DECISION": DECISION_REMAIN_UNKNOWN,
        "RATIFIED_CLASSIFIED_EVENT_KIND_SET_STATUS": KIND_SET_EMPTY,
        "ACCOUNT_BILLS_CURRENT_NONCANONICAL": TRUE_TOKEN,
        "MS2_AUTHORIZED": FALSE_TOKEN,
        "VENUE_EQ_SOURCE_AUTHORITY": FALSE_TOKEN,
        "RECONSTRUCTION_IMPLEMENTED": FALSE_TOKEN,
        "D6_FULLY_CLOSED": FALSE_TOKEN,
        "D7_AUTHORIZED": FALSE_TOKEN,
        "STANDING_FULL_CORE_DAG_PIN": DAG_PIN,
        "NEXT_OWNER_GO_REQUIRED": adjudication["next_owner_go_required"],
        "VAULT_RELATIVE": VAULT_RELATIVE if productive else "TEST_TRANSPORT",
        "SECRETS_OR_SIGNATURES_PERSISTED": FALSE_TOKEN,
        "PROTECTED_SURFACES_UNCHANGED": TRUE_TOKEN,
    }
    _persist_json(path=store / CLAIMS_FILE, payload=claims)
    manifest = persist_manifest_sha256_v1(store_root=store)
    if verify_manifest_sha256_v1(store_root=store) != 0:
        raise GateAIndependentlyAttestedProductiveNonzeroLiabilityStockError(
            "MANIFEST_VERIFY_FAILED"
        )
    return GateAIndependentlyAttestedProductiveNonzeroLiabilityStockResultV1(
        genesis_id=EXPECTED_GENESIS_ID,
        genesis_as_of=EXPECTED_GENESIS_AS_OF,
        persist_as_of=as_of,
        store_root=str(store),
        gate_a_id=GATE_A_ID,
        authorized_surface=AUTHORIZED_SURFACE,
        authorized_get_count="1",
        actual_get_count=str(counters.get("GET_REQUEST_COUNT", "1")),
        post_count="0",
        http_status=http_status,
        venue_code=venue_code_raw,
        gate_a_execution_status=adjudication["gate_a_execution_status"],
        gate_a_raw_evidence_status="SEALED",
        gate_a_coverage_status=COVERAGE_SNAPSHOT,
        gate_a_independence_status=INDEPENDENCE_INDEPENDENT,
        gate_a_productive_nonzero_liability_proven=adjudication[
            "gate_a_productive_nonzero_liability_proven"
        ],
        gate_a_evidence_id=evidence_id,
        gate_a_evidence_digest=evidence_digest,
        u05_reopened_decision_capable=adjudication["u05_reopened_decision_capable"],
        u05_decision_after=adjudication["u05_decision_after"],
        u05_decision_basis=adjudication["u05_decision_basis"],
        u06_decision=DECISION_REMAIN_UNKNOWN,
        residual_class_decision=DECISION_REMAIN_UNKNOWN,
        evidence_manifest=str(manifest),
    )


__all__ = [
    "CANONICAL_PACK_RELPATH",
    "EXPECTED_ORIGIN_MAIN_SHA",
    "OWNER_GO",
    "STATUS_EXECUTED_NONQUALIFYING",
    "STATUS_EXECUTED_QUALIFYING",
    "GateAIndependentlyAttestedProductiveNonzeroLiabilityStockError",
    "execute_gate_a_independently_attested_productive_nonzero_liability_stock_v1",
]
