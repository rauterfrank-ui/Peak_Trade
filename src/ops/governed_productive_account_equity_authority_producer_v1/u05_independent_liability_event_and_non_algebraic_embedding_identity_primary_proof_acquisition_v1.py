"""Forensic acquisition of the U05 primary-proof object.

Consumes the Owner-GO named by §11.2.1.BY. Determines the covered
semantic acquisition surface, max GET count, expected proof object,
and qualification predicates before any venue access. No concrete
GET surface is bound with a ratified U05-Primary-Proof-Role, so this
slice does not GET and does not POST. Absent/empty/zero remains
nonqualifying. U05 remains REMAIN_UNKNOWN. AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

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
from src.ops.governed_productive_account_equity_authority_producer_v1.bj_future_admissible_evidence_and_include_exclude_qualification_law_v1 import (
    ACQUISITION_SURFACE,
    CANONICAL_PACK_RELPATH as CANONICAL_BY_PACK_RELPATH,
    CLASS_U05,
    NEXT_OWNER_GO as CONSUMED_OWNER_GO,
    OUTCOME_EXCLUDE,
    OUTCOME_INCLUDE,
    OUTCOME_NONQUALIFYING,
    PROOF_OBJECT_U05,
    evaluate_u05_primary_proof_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.bound_account_identity_runtime_binding_v1 import (
    load_bound_account_identity_runtime_binding_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.checkpoint_observation_window_binding_contract_v1 import (
    load_checkpoint_observation_window_binding_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    ACCOUNT_BILLS_REMAINS_CURRENT_NONCANONICAL,
    AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT,
    C17_CREATED,
    CANDIDATE_SURFACE_SELECTION,
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
from src.ops.governed_productive_account_equity_authority_producer_v1.f12_f13_kind_set_remaining_unknown_pin_and_reopen_gate_v1 import (
    SELECTED_BALANCE_SURFACE,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_today_initial_stock_anchor_v1 import (
    AUTHORIZED_ANCHOR_ID,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.named_remaining_unknown_kind_set_evidence_persist_contract_v1 import (
    DECISION_REMAIN_UNKNOWN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_overlap_with_u04_u05_contract_v1 import (
    P01_U05_OVERLAP_RESOLVED_STATUS,
    P01_U05_OVERLAP_STATE,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_observation_s0_runtime_binding_gate_v1 import (
    resolve_canonical_d4_d5_genesis_runtime_store_root_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.scoped_read_only_observation_boundary_contract_v1 import (
    CANDIDATE_SURFACE_ACCOUNT_BILLS,
    CANDIDATE_SURFACE_TRADE_FILLS,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.credential_presence_v1 import (
    default_vault_path_v1,
    inspect_credential_material_presence_v1,
)

OWNER_GO = CONSUMED_OWNER_GO
EXPECTED_ORIGIN_MAIN_SHA = "74e64f17f7728a71a52f472264b19d7d627e9507"
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_forensic_acquisition_of_u05_independent_liability_"
    "event_and_non_algebraic_embedding_identity_primary_proof_v1/2026-09-14T231500Z"
)
CANONICAL_PERSIST_AS_OF = "2026-09-14T23:15:00Z"
CANONICAL_GATE_A_PACK_RELPATH = (
    "evidence/ops/full_core_option_d_gate_a_independently_attested_"
    "productive_nonzero_liability_stock_v1/2026-09-14T200500Z"
)
SCHEMA_CLASS = (
    "U05_INDEPENDENT_LIABILITY_EVENT_AND_NON_ALGEBRAIC_EMBEDDING_IDENTITY_"
    "PRIMARY_PROOF_ACQUISITION_V1"
)
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
NONE_TOKEN = "NONE"
KIND_SET_EMPTY = "EMPTY_FAIL_CLOSED"
EMBEDDING_UNKNOWN = "UNKNOWN"
PRIMARY_PROOF_STATUS = "NOT_ACQUIRED_CONCRETE_GET_SURFACE_UNBOUND"
BLOCKER_ID = "NO_CONCRETE_U05_PRIMARY_PROOF_GET_SURFACE_BOUND_WITH_RATIFIED_U05_PRIMARY_PROOF_ROLE"
DECISION_BASIS = (
    "CONCRETE_U05_PRIMARY_PROOF_GET_SURFACE_UNBOUND_AND_NO_RATIFIED_U05_PRIMARY_PROOF_ROLE"
)
NEXT_OWNER_GO = (
    "OWNER_GO_REQUIRED_TO_BIND_CONCRETE_U05_PRIMARY_PROOF_GET_SURFACE_"
    "WITH_RATIFIED_U05_PRIMARY_PROOF_ROLE_AND_MAX_GET_COUNT_V1"
)
SECRET_RESOLUTION_NOT_ATTEMPTED = "NOT_ATTEMPTED_CONCRETE_GET_SURFACE_UNBOUND"
CANDIDATE_SURFACE_BILLS_ARCHIVE = "GET_/api/v5/account/bills-archive"
CANDIDATE_SURFACES_WITHOUT_U05_PRIMARY_PROOF_ROLE: tuple[str, ...] = (
    CANDIDATE_SURFACE_ACCOUNT_BILLS,
    CANDIDATE_SURFACE_BILLS_ARCHIVE,
    CANDIDATE_SURFACE_TRADE_FILLS,
)
SECRET_MARKERS: tuple[str, ...] = (
    "ok-access",
    "api_secret",
    "api-secret",
    "passphrase",
    "secretref://",
)
CLAIMS_FILE = "claims.json"
_REPO_ROOT = Path(__file__).resolve().parents[3]


class U05IndependentLiabilityEventPrimaryProofAcquisitionError(ValueError):
    """Fail-closed U05 primary-proof acquisition violation."""


@dataclass(frozen=True)
class U05IndependentLiabilityEventPrimaryProofAcquisitionResultV1:
    genesis_id: str
    genesis_as_of: str
    persist_as_of: str
    store_root: str
    authorized_acquisition_surface: str
    authorized_get_count: str
    actual_get_count: str
    post_count: str
    vault_available: str
    secret_resolution_status: str
    raw_evidence_status: str
    independent_liability_event_proven: str
    event_after_prior_proven: str
    d4_d5_scope_identity_proven: str
    non_algebraic_embedding_identity: str
    p01_u05_overlap_disproven: str
    once_only_equity_stock_effect_proven: str
    double_counting_guard_proven: str
    u05_primary_proof_status: str
    u05_decision_after: str
    u05_decision_basis: str
    productive_acquisition_executed: str
    evidence_manifest: str


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _persist_json(*, path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(_canonical_json(payload) + "\n", encoding="utf-8")
    tmp.replace(path)


def _require_non_empty_str(*, field: str, raw: Any) -> str:
    if raw is None or isinstance(raw, bool) or not isinstance(raw, str):
        raise U05IndependentLiabilityEventPrimaryProofAcquisitionError(f"FIELD_NOT_STRING:{field}")
    text = raw.strip()
    if text == "" or text != raw:
        raise U05IndependentLiabilityEventPrimaryProofAcquisitionError(f"FIELD_MISSING:{field}")
    return text


def _assert_no_secret_material(*, blob: str, label: str) -> None:
    lowered = blob.lower()
    for marker in SECRET_MARKERS:
        if marker in lowered:
            raise U05IndependentLiabilityEventPrimaryProofAcquisitionError(
                f"SECRET_MARKER_IN_{label}"
            )


def _assert_standing_pins() -> None:
    if WIRE_SEND_PERMITTED is not False:
        raise U05IndependentLiabilityEventPrimaryProofAcquisitionError(
            "WIRE_SEND_PERMITTED_NOT_FALSE"
        )
    if U05_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise U05IndependentLiabilityEventPrimaryProofAcquisitionError(
            "U05_KIND_DECISION_NOT_REMAIN_UNKNOWN"
        )
    if U06_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise U05IndependentLiabilityEventPrimaryProofAcquisitionError(
            "U06_KIND_DECISION_NOT_REMAIN_UNKNOWN"
        )
    if RESIDUAL_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise U05IndependentLiabilityEventPrimaryProofAcquisitionError(
            "RESIDUAL_KIND_DECISION_NOT_REMAIN_UNKNOWN"
        )
    if KIND_SET_RESOLVED is not False:
        raise U05IndependentLiabilityEventPrimaryProofAcquisitionError(
            "KIND_SET_RESOLVED_NOT_FALSE"
        )
    if RATIFIED_CLASSIFIED_KIND_SET:
        raise U05IndependentLiabilityEventPrimaryProofAcquisitionError("KIND_SET_MUST_REMAIN_EMPTY")
    if AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT is not False:
        raise U05IndependentLiabilityEventPrimaryProofAcquisitionError(
            "SOURCE_SEAM_MUST_REMAIN_ABSENT"
        )
    if COMPLETE_EVENT_STREAM_PROVEN is not False:
        raise U05IndependentLiabilityEventPrimaryProofAcquisitionError(
            "COMPLETE_STREAM_MUST_REMAIN_UNPROVEN"
        )
    if EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED is not False:
        raise U05IndependentLiabilityEventPrimaryProofAcquisitionError(
            "EVENT_ACQUISITION_NETWORK_GET_MUST_REMAIN_UNAUTHORIZED"
        )
    if OBSERVATION_NETWORK_GET_AUTHORIZED is not False:
        raise U05IndependentLiabilityEventPrimaryProofAcquisitionError(
            "OBSERVATION_NETWORK_GET_MUST_REMAIN_UNAUTHORIZED"
        )
    if CANDIDATE_SURFACE_SELECTION != "NONE_SELECTED":
        raise U05IndependentLiabilityEventPrimaryProofAcquisitionError(
            "CANDIDATE_SURFACE_SELECTION_NOT_NONE"
        )
    if MS2_AUTHORIZED is not False:
        raise U05IndependentLiabilityEventPrimaryProofAcquisitionError("MS2_AUTHORIZED_NOT_FALSE")
    if D6_FULLY_CLOSED is not False:
        raise U05IndependentLiabilityEventPrimaryProofAcquisitionError("D6_FULLY_CLOSED_NOT_FALSE")
    if D7_AUTHORIZED is not False:
        raise U05IndependentLiabilityEventPrimaryProofAcquisitionError("D7_AUTHORIZED_NOT_FALSE")
    if C17_CREATED is not False:
        raise U05IndependentLiabilityEventPrimaryProofAcquisitionError("C17_CREATED_NOT_FALSE")
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        raise U05IndependentLiabilityEventPrimaryProofAcquisitionError(
            "RAW_EQ_SOURCE_AUTHORITY_NOT_FALSE"
        )
    if ACCOUNT_BILLS_REMAINS_CURRENT_NONCANONICAL is not True:
        raise U05IndependentLiabilityEventPrimaryProofAcquisitionError(
            "BILLS_CANONICALIZED_FORBIDDEN"
        )
    if DAG_PIN != "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING":
        raise U05IndependentLiabilityEventPrimaryProofAcquisitionError("DAG_PIN_DRIFT")
    if P01_U05_OVERLAP_STATE != "UNRESOLVED":
        raise U05IndependentLiabilityEventPrimaryProofAcquisitionError(
            "P01_U05_OVERLAP_STATE_DRIFT"
        )
    if P01_U05_OVERLAP_RESOLVED_STATUS != FALSE_TOKEN:
        raise U05IndependentLiabilityEventPrimaryProofAcquisitionError(
            "P01_U05_OVERLAP_MUST_REMAIN_UNRESOLVED"
        )


def _load_json_object(*, path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise U05IndependentLiabilityEventPrimaryProofAcquisitionError(
            f"JSON_NOT_OBJECT:{path.name}"
        )
    return payload


def _assert_parent_by_pack(*, sealed_by_pack: Path) -> None:
    if verify_manifest_sha256_v1(store_root=sealed_by_pack) != 0:
        raise U05IndependentLiabilityEventPrimaryProofAcquisitionError("BY_MANIFEST_MISMATCH")
    claims = _load_json_object(path=sealed_by_pack / CLAIMS_FILE)
    if claims.get("U05_DECISION_AFTER") != DECISION_REMAIN_UNKNOWN:
        raise U05IndependentLiabilityEventPrimaryProofAcquisitionError(
            "PARENT_BY_U05_NOT_REMAIN_UNKNOWN"
        )
    if claims.get("PRODUCTIVE_ACQUISITION_EXECUTED") != FALSE_TOKEN:
        raise U05IndependentLiabilityEventPrimaryProofAcquisitionError(
            "PARENT_BY_MUST_NOT_HAVE_ACQUIRED"
        )
    if claims.get("NEXT_OWNER_GO_REQUIRED") != OWNER_GO:
        raise U05IndependentLiabilityEventPrimaryProofAcquisitionError(
            "PARENT_BY_NEXT_OWNER_GO_DRIFT"
        )
    definitions = _load_json_object(path=sealed_by_pack / "evidence_class_definitions_v1.json")
    records = definitions.get("records")
    if not isinstance(records, list):
        raise U05IndependentLiabilityEventPrimaryProofAcquisitionError("BY_CLASS_RECORDS_NOT_LIST")
    u05 = next((item for item in records if item.get("evidence_class_id") == CLASS_U05), None)
    if not isinstance(u05, Mapping):
        raise U05IndependentLiabilityEventPrimaryProofAcquisitionError("U05_CLASS_RECORD_MISSING")
    if str(u05.get("primary_proof_object") or "") != PROOF_OBJECT_U05:
        raise U05IndependentLiabilityEventPrimaryProofAcquisitionError("U05_PROOF_OBJECT_DRIFT")
    if str(u05.get("acquisition_surface") or "") != ACQUISITION_SURFACE:
        raise U05IndependentLiabilityEventPrimaryProofAcquisitionError("U05_SURFACE_DRIFT")
    if str(definitions.get("acquisition_authorized_this_go") or "") != FALSE_TOKEN:
        raise U05IndependentLiabilityEventPrimaryProofAcquisitionError("BY_MUST_NOT_AUTHORIZE_GET")


def _inspect_vault_presence(*, repo: Path, vault_file: Path | str | None) -> dict[str, str]:
    resolved = Path(vault_file) if vault_file is not None else default_vault_path_v1(repo_root=repo)
    presence = inspect_credential_material_presence_v1(vault_file=resolved)
    if presence.get("VALUES_INCLUDED") is not False:
        raise U05IndependentLiabilityEventPrimaryProofAcquisitionError(
            "SECRET_VALUES_MUST_NOT_BE_INCLUDED"
        )
    available = presence.get("available") is True
    reason = str(presence.get("reason") or NONE_TOKEN)
    payload = {
        "layer": "FORENSIC_RAW_EVIDENCE",
        "vault_file_present": TRUE_TOKEN if presence.get("VAULT_FILE_PRESENT") else FALSE_TOKEN,
        "secretref_uri_bound": TRUE_TOKEN if presence.get("SECRETREF_URI_BOUND") else FALSE_TOKEN,
        "credential_fields_complete": (
            TRUE_TOKEN if presence.get("CREDENTIAL_FIELDS_COMPLETE") else FALSE_TOKEN
        ),
        "values_included": FALSE_TOKEN,
        "available": TRUE_TOKEN if available else FALSE_TOKEN,
        "reason": reason,
        "secret_resolution_status": SECRET_RESOLUTION_NOT_ATTEMPTED,
        "secrets_or_signatures_persisted": FALSE_TOKEN,
    }
    _assert_no_secret_material(blob=_canonical_json(payload), label="VAULT_PRESENCE")
    return payload


def _surface_inventory() -> dict[str, Any]:
    return {
        "layer": "CANONICAL_AUTHORITY",
        "owner_go": OWNER_GO,
        "semantic_acquisition_surface": ACQUISITION_SURFACE,
        "expected_primary_proof_object": PROOF_OBJECT_U05,
        "concrete_get_surface": NONE_TOKEN,
        "u05_primary_proof_role_bound": FALSE_TOKEN,
        "authorized_get_count": "0",
        "actual_get_count": "0",
        "post_count_allowed": "0",
        "hope_get_forbidden": TRUE_TOKEN,
        "gate_a_retry_forbidden": TRUE_TOKEN,
        "event_acquisition_network_get_authorized": FALSE_TOKEN,
        "observation_network_get_authorized": FALSE_TOKEN,
        "candidate_surface_selection": CANDIDATE_SURFACE_SELECTION,
        "selected_balance_surface_nonqualifying": SELECTED_BALANCE_SURFACE,
        "candidate_surfaces_without_u05_primary_proof_role": ",".join(
            CANDIDATE_SURFACES_WITHOUT_U05_PRIMARY_PROOF_ROLE
        ),
        "account_bills_canonicalized": FALSE_TOKEN,
        "account_bills_current_noncanonical": TRUE_TOKEN,
        "bills_fills_without_u05_primary_proof_role_nonqualifying": TRUE_TOKEN,
        "retroactive_sealed_pack_uplift_forbidden": TRUE_TOKEN,
        "blocker_id": BLOCKER_ID,
        "positive_include_predicate": (
            "independent_liability_event_after_prior_AND_embedding_SEPARATE_"
            "by_non_algebraic_identity_AND_p01_overlap_disproven"
        ),
        "positive_exclude_predicate": (
            "non_algebraic_embedding_IN_BASE_AND_not_from_empty_zero_absent"
        ),
        "nonqualifying_outcomes": (
            "GATE_A_snapshot_tokens;empty_zero_absent;algebraic_eq_identity;"
            "embedding_unresolved;p01_overlap_unresolved;incomplete_proof_object;"
            "retroactive_sealed_pack;unbound_concrete_get_surface"
        ),
    }


def execute_u05_independent_liability_event_and_non_algebraic_embedding_identity_primary_proof_acquisition_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    evidence_root: Path | str,
    repo_root: Path | str | None = None,
    genesis_store_root: Path | str | None = None,
    sealed_by_pack: Path | str | None = None,
    vault_file: Path | str | None = None,
    persist_as_of: str | None = None,
) -> U05IndependentLiabilityEventPrimaryProofAcquisitionResultV1:
    if owner_go != OWNER_GO:
        raise U05IndependentLiabilityEventPrimaryProofAcquisitionError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise U05IndependentLiabilityEventPrimaryProofAcquisitionError("ORIGIN_MAIN_SHA_MISMATCH")
    _assert_standing_pins()
    repo = Path(repo_root) if repo_root is not None else _REPO_ROOT
    by_pack = (
        Path(sealed_by_pack) if sealed_by_pack is not None else repo / CANONICAL_BY_PACK_RELPATH
    )
    _assert_parent_by_pack(sealed_by_pack=by_pack)
    genesis_root = (
        Path(genesis_store_root)
        if genesis_store_root is not None
        else resolve_canonical_d4_d5_genesis_runtime_store_root_v1(repo_root=repo)
    )
    if genesis_root is None:
        raise U05IndependentLiabilityEventPrimaryProofAcquisitionError("GENESIS_STORE_ABSENT")
    d4 = load_bound_account_identity_runtime_binding_v1(store_root=genesis_root)
    d5 = load_checkpoint_observation_window_binding_v1(store_root=genesis_root)
    as_of = persist_as_of or CANONICAL_PERSIST_AS_OF
    _require_non_empty_str(field="persist_as_of", raw=as_of)
    vault_presence = _inspect_vault_presence(repo=repo, vault_file=vault_file)
    law_outcome = evaluate_u05_primary_proof_v1(proof={})
    if law_outcome.outcome in {OUTCOME_INCLUDE, OUTCOME_EXCLUDE}:
        raise U05IndependentLiabilityEventPrimaryProofAcquisitionError(
            "ABSENT_PROOF_MUST_NOT_DECIDE"
        )
    if law_outcome.outcome != OUTCOME_NONQUALIFYING:
        raise U05IndependentLiabilityEventPrimaryProofAcquisitionError(
            "ABSENT_PROOF_MUST_BE_NONQUALIFYING"
        )
    predicates = {
        "layer": "ADJUDICATED_CONCLUSION",
        "independent_liability_event_proven": FALSE_TOKEN,
        "event_after_prior_proven": FALSE_TOKEN,
        "d4_d5_binding_present": TRUE_TOKEN,
        "d4_identity_digest": d4.identity_digest,
        "d4_instance_digest": d4.instance_digest,
        "d5_binding_id": d5.binding_id,
        "d5_bound_account_identity_digest": d5.bound_account_identity_digest,
        "prior_anchor_id_present": AUTHORIZED_ANCHOR_ID,
        "d4_d5_scope_identity_proven": FALSE_TOKEN,
        "d4_d5_scope_identity_basis": "EVENT_NOT_ACQUIRED_SO_EVENT_IDENTITY_NOT_BOUND",
        "non_algebraic_embedding_identity": EMBEDDING_UNKNOWN,
        "p01_u05_overlap_state": P01_U05_OVERLAP_STATE,
        "p01_u05_overlap_disproven": FALSE_TOKEN,
        "once_only_equity_stock_effect_proven": FALSE_TOKEN,
        "double_counting_guard_proven": FALSE_TOKEN,
        "absence_is_not_exclude": TRUE_TOKEN,
        "get_alone_may_include": FALSE_TOKEN,
        "get_alone_may_exclude": FALSE_TOKEN,
    }
    surface = _surface_inventory()
    evaluation = {
        "layer": "ADJUDICATED_CONCLUSION",
        "current_primary_proof_present": FALSE_TOKEN,
        "law_outcome": law_outcome.outcome,
        "law_basis": law_outcome.basis,
        "u05_primary_proof_status": PRIMARY_PROOF_STATUS,
        "blocker_id": BLOCKER_ID,
        "u05_decision_after": DECISION_REMAIN_UNKNOWN,
        "u05_decision_basis": DECISION_BASIS,
        "include_from_unknown": "FORBIDDEN_UNTIL_POSITIVE_PRIMARY_PROOF",
        "exclude_from_unknown": "FORBIDDEN_UNTIL_POSITIVE_IN_BASE_PROOF",
    }
    root = Path(evidence_root)
    root.mkdir(parents=True, exist_ok=True)
    claims = {
        "OWNER_GO": OWNER_GO,
        "OWNER_GO_STATUS": "CONSUMED",
        "SCHEMA_CLASS": SCHEMA_CLASS,
        "CONTRACT_VERSION": CONTRACT_VERSION,
        "AUTHORITY_EFFECT": AUTHORITY_EFFECT,
        "GENESIS_ID": EXPECTED_GENESIS_ID,
        "GENESIS_AS_OF": EXPECTED_GENESIS_AS_OF,
        "PERSIST_AS_OF": as_of,
        "U05_EVIDENCE_CLASS": CLASS_U05,
        "AUTHORIZED_ACQUISITION_SURFACE": ACQUISITION_SURFACE,
        "EXPECTED_PRIMARY_PROOF_OBJECT": PROOF_OBJECT_U05,
        "CONCRETE_GET_SURFACE": NONE_TOKEN,
        "U05_PRIMARY_PROOF_ROLE_BOUND": FALSE_TOKEN,
        "AUTHORIZED_GET_COUNT": "0",
        "ACTUAL_GET_COUNT": "0",
        "POST_COUNT": "0",
        "VAULT_AVAILABLE": vault_presence["available"],
        "SECRET_RESOLUTION_STATUS": SECRET_RESOLUTION_NOT_ATTEMPTED,
        "RAW_EVIDENCE_STATUS": "NOT_ACQUIRED",
        "INDEPENDENT_LIABILITY_EVENT_PROVEN": FALSE_TOKEN,
        "EVENT_AFTER_PRIOR_PROVEN": FALSE_TOKEN,
        "D4_D5_SCOPE_IDENTITY_PROVEN": FALSE_TOKEN,
        "NON_ALGEBRAIC_EMBEDDING_IDENTITY": EMBEDDING_UNKNOWN,
        "P01_U05_OVERLAP_DISPROVEN": FALSE_TOKEN,
        "ONCE_ONLY_EQUITY_STOCK_EFFECT_PROVEN": FALSE_TOKEN,
        "DOUBLE_COUNTING_GUARD_PROVEN": FALSE_TOKEN,
        "U05_PRIMARY_PROOF_STATUS": PRIMARY_PROOF_STATUS,
        "U05_DECISION_BEFORE": DECISION_REMAIN_UNKNOWN,
        "U05_DECISION_AFTER": DECISION_REMAIN_UNKNOWN,
        "U05_DECISION_BASIS": DECISION_BASIS,
        "U06_DECISION_UNCHANGED": DECISION_REMAIN_UNKNOWN,
        "RESIDUAL_DECISION_UNCHANGED": DECISION_REMAIN_UNKNOWN,
        "BLOCKER_ID": BLOCKER_ID,
        "PRODUCTIVE_ACQUISITION_EXECUTED": FALSE_TOKEN,
        "GATE_A_REOPENED": FALSE_TOKEN,
        "GATE_B_REEXECUTED": FALSE_TOKEN,
        "VENUE_EQ_SOURCE_AUTHORITY": FALSE_TOKEN,
        "ACCOUNT_BILLS_CANONICALIZED": FALSE_TOKEN,
        "MS2_AUTHORIZED": FALSE_TOKEN,
        "D6_FULLY_CLOSED": FALSE_TOKEN,
        "D7_AUTHORIZED": FALSE_TOKEN,
        "C17_CREATED": FALSE_TOKEN,
        "STANDING_FULL_CORE_DAG_PIN": DAG_PIN,
        "NEXT_OWNER_GO_REQUIRED": NEXT_OWNER_GO,
        "NEXT_ACTION": "STOP_ON_CONCRETE_AUTH_OR_ACQUISITION_BLOCKER",
        "SECRETS_OR_SIGNATURES_PERSISTED": FALSE_TOKEN,
        "PROTECTED_SURFACES_UNCHANGED": TRUE_TOKEN,
    }
    lineage = {
        "origin_main_sha": origin_main_sha,
        "owner_go": OWNER_GO,
        "genesis_id": EXPECTED_GENESIS_ID,
        "genesis_as_of": EXPECTED_GENESIS_AS_OF,
        "persist_as_of": as_of,
        "parent_by_pack": CANONICAL_BY_PACK_RELPATH,
        "parent_gate_a_pack": CANONICAL_GATE_A_PACK_RELPATH,
        "d4_identity_digest": d4.identity_digest,
        "d5_binding_id": d5.binding_id,
        "prior_anchor_id": AUTHORIZED_ANCHOR_ID,
        "reconstruction_source_authority": FALSE_TOKEN,
    }
    protected = {
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
        "ms2_authorized": FALSE_TOKEN,
        "reconstruction_implemented": FALSE_TOKEN,
        "dag_pin": DAG_PIN,
    }
    layers = {
        "CANONICAL_AUTHORITY": "acquisition_surface_binding_v1.json",
        "FORENSIC_RAW_EVIDENCE": "vault_presence_v1.json",
        "ADJUDICATED_CONCLUSION": (
            "predicate_adjudication_v1.json,current_proof_evaluation_v1.json"
        ),
        "HISTORICAL": "LINEAGE.json",
        "NAVIGATION": "FORBIDDEN_AS_AUTHORITY",
        "INTERPRETATION": "FORBIDDEN",
        "HYPOTHESIS": "FORBIDDEN",
        "UNRESOLVED_OR_CONTRADICTORY": BLOCKER_ID,
    }
    _persist_json(path=root / CLAIMS_FILE, payload=claims)
    _persist_json(path=root / "acquisition_surface_binding_v1.json", payload=surface)
    _persist_json(path=root / "predicate_adjudication_v1.json", payload=predicates)
    _persist_json(path=root / "current_proof_evaluation_v1.json", payload=evaluation)
    _persist_json(path=root / "vault_presence_v1.json", payload=vault_presence)
    _persist_json(path=root / "protected_surfaces_v1.json", payload=protected)
    _persist_json(path=root / "layers_v1.json", payload=layers)
    _persist_json(path=root / "LINEAGE.json", payload=lineage)
    persist_manifest_sha256_v1(store_root=root)
    if verify_manifest_sha256_v1(store_root=root) != 0:
        raise U05IndependentLiabilityEventPrimaryProofAcquisitionError("MANIFEST_VERIFY_NOT_ZERO")
    return U05IndependentLiabilityEventPrimaryProofAcquisitionResultV1(
        genesis_id=EXPECTED_GENESIS_ID,
        genesis_as_of=EXPECTED_GENESIS_AS_OF,
        persist_as_of=as_of,
        store_root=str(root),
        authorized_acquisition_surface=ACQUISITION_SURFACE,
        authorized_get_count="0",
        actual_get_count="0",
        post_count="0",
        vault_available=vault_presence["available"],
        secret_resolution_status=SECRET_RESOLUTION_NOT_ATTEMPTED,
        raw_evidence_status="NOT_ACQUIRED",
        independent_liability_event_proven=FALSE_TOKEN,
        event_after_prior_proven=FALSE_TOKEN,
        d4_d5_scope_identity_proven=FALSE_TOKEN,
        non_algebraic_embedding_identity=EMBEDDING_UNKNOWN,
        p01_u05_overlap_disproven=FALSE_TOKEN,
        once_only_equity_stock_effect_proven=FALSE_TOKEN,
        double_counting_guard_proven=FALSE_TOKEN,
        u05_primary_proof_status=PRIMARY_PROOF_STATUS,
        u05_decision_after=DECISION_REMAIN_UNKNOWN,
        u05_decision_basis=DECISION_BASIS,
        productive_acquisition_executed=FALSE_TOKEN,
        evidence_manifest=str(root / "MANIFEST.sha256"),
    )


__all__ = [
    "BLOCKER_ID",
    "CANONICAL_PACK_RELPATH",
    "CANONICAL_PERSIST_AS_OF",
    "DECISION_BASIS",
    "EXPECTED_ORIGIN_MAIN_SHA",
    "NEXT_OWNER_GO",
    "OWNER_GO",
    "PRIMARY_PROOF_STATUS",
    "U05IndependentLiabilityEventPrimaryProofAcquisitionError",
    "execute_u05_independent_liability_event_and_non_algebraic_embedding_identity_primary_proof_acquisition_v1",
]
