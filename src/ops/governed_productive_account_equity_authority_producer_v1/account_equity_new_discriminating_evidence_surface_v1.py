"""Bind the new U05 owner-supplied embedding-witness evidence surface.

Consumes the workpackage Owner-GO. Satisfies the CK-named GO that
authorized a new discriminating surface not already adjudicated
NONE_BINDABLE or GET-alone nonqualifying. Operationalizes the sealed CE
owner-supply assumption. Does not GET. Does not POST. Does not Hope-GET.
Does not resolve secrets. Does not reuse interest-accrued GET-alone or
NONE_BINDABLE candidates. Absent artifact is UNKNOWN, not INCLUDE or
EXCLUDE. AUTHORITY_EFFECT=NONE.

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
    MAPPING_PROVEN,
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
    TARGET_U05,
    evaluate_u05_primary_proof_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_ACCOUNT_EQUITY_SOURCE_MAPPING_CLOSURE_CLOSED,
    ACCOUNT_BILLS_REMAINS_CURRENT_NONCANONICAL,
    AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT,
    C17_CREATED,
    CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING,
    COMPLETE_EVENT_STREAM_PROVEN,
    D6_FULLY_CLOSED,
    D7_AUTHORIZED,
    EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED,
    KIND_SET_RESOLVED,
    MS2_AUTHORIZED,
    OBSERVATION_NETWORK_GET_AUTHORIZED,
    RAW_EQ_SOURCE_AUTHORITY,
    RECONSTRUCTION_ALGEBRA_COMPLETE,
    RESIDUAL_KIND_DECISION,
    SEMANTIC_MAPPING_PROVEN,
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
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.remaining_necessary_kind_evidence_classification_v1 import (
    BLOCKER_ID as PARENT_BLOCKER_ID,
    CANONICAL_PACK_RELPATH as CANONICAL_CK_PACK_RELPATH,
    NEXT_OWNER_GO as PIN_OWNER_GO,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.residual_positive_necessary_kind_exhaustiveness_durable_unknown_pin_v1 import (
    reject_durable_unknown_as_include_or_exclude_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u05_durable_unknown_embedding_identity_pin_v1 import (
    CANONICAL_PACK_RELPATH as CANONICAL_CE_PACK_RELPATH,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u06_paired_fee_event_and_once_only_equity_stock_effect_primary_proof_surface_binding_v1 import (
    reject_hope_get_v1,
)

OWNER_GO = "OWNER_GO_ACCOUNT_EQUITY_NEW_DISCRIMINATING_EVIDENCE_SURFACE_V1"
EXPECTED_ORIGIN_MAIN_SHA = "64deebb5373ba5f7b34c2d1564910d5122b8685f"
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_account_equity_new_discriminating_evidence_surface_v1/"
    "2026-09-15T080000Z"
)
CANONICAL_INPUT_SURFACE_RELPATH = (
    "evidence/ops/owner_supplied_u05_non_algebraic_embedding_witness_input_v1"
)
CANONICAL_PERSIST_AS_OF = "2026-09-15T08:00:00Z"
SCHEMA_CLASS = "ACCOUNT_EQUITY_NEW_DISCRIMINATING_EVIDENCE_SURFACE_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
NONE_TOKEN = "NONE"
UNKNOWN_TOKEN = "UNKNOWN"
DURABLE_UNKNOWN_TOKEN = "DURABLE_UNKNOWN"
KIND_SET_EMPTY = "EMPTY_FAIL_CLOSED"
SURFACE_ID = "OWNER_SUPPLIED_NON_ALGEBRAIC_EMBEDDING_WITNESS_ARTIFACT_V1"
SURFACE_KIND = "OWNER_SUPPLIED_NON_GET_EMBEDDING_WITNESS"
PRIMARY_PROOF_ROLE = "INDEPENDENT_NON_ALGEBRAIC_EMBEDDING_WITNESS"
SELECTED_DIMENSION = "U05_EMBEDDING_WITNESS"
ADMISSIBLE_SOURCE_CLASS = "OWNER_SUPPLIED_FORENSIC_EMBEDDING_WITNESS"
SURFACE_BINDING_STATUS = "BOUND"
SURFACE_STATUS_MISSING = "MISSING"
SURFACE_STATUS_EMPTY = "EMPTY"
SURFACE_STATUS_PRESENT = "PRESENT"
DISCRIMINATING_CAPABILITY = "BJ_U05_PRIMARY_PROOF_INCLUDE_OR_EXCLUDE"
FORBIDDEN_REUSED_SURFACES: frozenset[str] = frozenset(
    {
        "GET_/api/v5/account/interest-accrued",
        "GET_/api/v5/account/balance",
        "GET_/api/v5/account/bills",
        "GET_/api/v5/account/bills-archive",
        "GET_/api/v5/trade/fills",
        "GET_/api/v5/account/max-withdrawal",
        "GET_/api/v5/account/interest-limits",
        "GET_/api/v5/account/max-loan",
        "GET_/api/v5/account/spot-borrow-repay-history",
        "GET_/api/v5/trade/orders-pending",
        "EQUITY_AFFECTING_EVENT_TAXONOMY_CONTRACT_V1",
        "PATH_C_ARCHITECTURAL_UNKNOWN_CLOSEOUT",
        "INDEPENDENT_TAXONOMY_EXHAUSTIVENESS_CERTIFICATE_NOT_GET",
    }
)
EXACT_MISSING_PREDICATE = (
    "OWNER_SUPPLIED_U05_NON_ALGEBRAIC_EMBEDDING_WITNESS_ARTIFACT_ABSENT_"
    "SURFACE_BOUND_AND_DECISION_CAPABLE_ABSENT_IS_NOT_INCLUDE_OR_EXCLUDE_"
    "U06_AND_RESIDUAL_REMAIN_DURABLE_UNKNOWN_KIND_SET_CANNOT_RESOLVE_"
    "MAPPING_CANNOT_BECOME_CANONICALLY_VALID"
)
BLOCKER_ID = (
    "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING_AFTER_U05_OWNER_"
    "SUPPLIED_EMBEDDING_WITNESS_SURFACE_BOUND_ARTIFACT_ABSENT"
)
ARCHITECTURE_BLOCKER = (
    "NEW_DISCRIMINATING_U05_EMBEDDING_WITNESS_SURFACE_BOUND_OWNER_SUPPLIED_"
    "ARTIFACT_ABSENT_IS_UNKNOWN_NOT_INCLUDE_OR_EXCLUDE_U06_RESIDUAL_"
    "UNCHANGED_NO_GET"
)
NEXT_PRODUCTIVE_NODE = "OWNER_SUPPLIED_U05_NON_ALGEBRAIC_EMBEDDING_WITNESS_ARTIFACT_SUPPLY"
NEXT_OWNER_GO = (
    "OWNER_GO_REQUIRED_TO_SUPPLY_OWNER_SUPPLIED_U05_NON_ALGEBRAIC_EMBEDDING_WITNESS_ARTIFACT_V1"
)
NEXT_ACTION = (
    "STOP_FIRST_DEFINITIVE_BLOCK_NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_"
    "MAPPING_U05_SURFACE_BOUND_ARTIFACT_ABSENT_NO_GET"
)
CLAIMS_FILE = "claims.json"
SECRET_MARKERS: tuple[str, ...] = (
    "ok-access",
    "api_secret",
    "api-secret",
    "passphrase",
    "secretref://",
)
_FORBIDDEN_ABSENT_DECISION_TOKENS = frozenset(
    {
        OUTCOME_INCLUDE,
        OUTCOME_EXCLUDE,
        "INCLUDE",
        "EXCLUDE",
        "true",
        "TRUE",
        "ABSENT",
        "absent",
        "0",
        "zero",
        "NONE",
        "N/A",
        "NOT_APPLICABLE",
    }
)
_REPO_ROOT = Path(__file__).resolve().parents[3]


class AccountEquityNewDiscriminatingEvidenceSurfaceError(ValueError):
    """Fail-closed new discriminating evidence-surface violation."""


@dataclass(frozen=True)
class OwnerSuppliedEmbeddingWitnessSurfaceScanV1:
    surface_relpath: str
    surface_status: str
    artifact_present: str
    artifact_count: str
    artifact_path: str
    raw_bytes_digest: str


@dataclass(frozen=True)
class AccountEquityNewDiscriminatingEvidenceSurfaceResultV1:
    genesis_id: str
    persist_as_of: str
    store_root: str
    surface_id: str
    surface_binding_status: str
    artifact_present: str
    u05_bj_outcome: str
    u05_status: str
    u06_status: str
    residual_status: str
    kind_set: str
    kind_set_resolved: str
    canonically_valid_account_equity_source_mapping: str
    first_definitive_block: str
    exact_missing_predicate: str
    authorized_get_count: str
    actual_get_count: str
    post_count: str
    evidence_manifest: str


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _persist_json(*, path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(_canonical_json(payload) + "\n", encoding="utf-8")
    tmp.replace(path)


def _load_json_object(*, path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AccountEquityNewDiscriminatingEvidenceSurfaceError(f"JSON_NOT_OBJECT:{path.name}")
    return payload


def _require_token(*, field: str, payload: Mapping[str, Any], expected: str) -> None:
    actual = str(payload.get(field) or "")
    if actual != expected:
        raise AccountEquityNewDiscriminatingEvidenceSurfaceError(f"{field}_DRIFT:{actual}")


def reject_already_adjudicated_surface_as_this_surface_v1(*, claimed_surface_id: str) -> None:
    if claimed_surface_id in FORBIDDEN_REUSED_SURFACES or claimed_surface_id in {
        NONE_TOKEN,
        "",
        "GET_ALONE",
        "GET_/api/v5/account/interest-accrued",
    }:
        raise AccountEquityNewDiscriminatingEvidenceSurfaceError(
            f"ALREADY_ADJUDICATED_NONE_BINDABLE_OR_GET_ALONE_NOT_THIS_SURFACE:{claimed_surface_id}"
        )


def reject_absent_artifact_as_include_or_exclude_v1(*, claimed: str) -> None:
    if claimed in _FORBIDDEN_ABSENT_DECISION_TOKENS:
        raise AccountEquityNewDiscriminatingEvidenceSurfaceError(
            f"ABSENT_ARTIFACT_IS_NOT_INCLUDE_OR_EXCLUDE:{claimed}"
        )


def reject_venue_eq_as_embedding_witness_v1(*, claimed_venue_eq_source: str) -> None:
    if claimed_venue_eq_source in {TRUE_TOKEN, "true", "USED", "SOURCE"}:
        raise AccountEquityNewDiscriminatingEvidenceSurfaceError(
            f"VENUE_EQ_CANNOT_BE_EMBEDDING_WITNESS:{claimed_venue_eq_source}"
        )


def reject_kind_set_resolved_while_remaining_unknown_v1(*, claimed: str) -> None:
    if claimed in {"true", "TRUE", "RESOLVED", "KIND_SET_RESOLVED_TRUE"}:
        raise AccountEquityNewDiscriminatingEvidenceSurfaceError(
            f"KIND_SET_CANNOT_RESOLVE_WHILE_REMAINING_UNKNOWN:{claimed}"
        )


def _assert_standing_pins() -> None:
    if U05_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise AccountEquityNewDiscriminatingEvidenceSurfaceError("U05_UNKNOWN_PRESERVED")
    if U06_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise AccountEquityNewDiscriminatingEvidenceSurfaceError("U06_UNKNOWN_PRESERVED")
    if RESIDUAL_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise AccountEquityNewDiscriminatingEvidenceSurfaceError("RESIDUAL_UNKNOWN_PRESERVED")
    if KIND_SET_RESOLVED is not False:
        raise AccountEquityNewDiscriminatingEvidenceSurfaceError("KIND_SET_RESOLVED_NOT_FALSE")
    if RATIFIED_CLASSIFIED_KIND_SET:
        raise AccountEquityNewDiscriminatingEvidenceSurfaceError("KIND_SET_MUST_REMAIN_EMPTY")
    if CURRENT_PRODUCTIVE_ACCOUNT_EQUITY_SOURCE_MAPPING_CLOSURE_CLOSED is True:
        raise AccountEquityNewDiscriminatingEvidenceSurfaceError(
            "MAPPING_CLOSURE_CONSUMED_REEXECUTE_FORBIDDEN"
        )
    if CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING is not False:
        raise AccountEquityNewDiscriminatingEvidenceSurfaceError("MAPPING_MUST_REMAIN_INVALID")
    if MAPPING_PROVEN is not False:
        raise AccountEquityNewDiscriminatingEvidenceSurfaceError("MAPPING_PROVEN_NOT_FALSE")
    if SEMANTIC_MAPPING_PROVEN is not False:
        raise AccountEquityNewDiscriminatingEvidenceSurfaceError("SEMANTIC_MAPPING_NOT_FALSE")
    if RECONSTRUCTION_ALGEBRA_COMPLETE is not False:
        raise AccountEquityNewDiscriminatingEvidenceSurfaceError("ALGEBRA_MUST_REMAIN_INCOMPLETE")
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        raise AccountEquityNewDiscriminatingEvidenceSurfaceError(
            "RAW_EQ_SOURCE_AUTHORITY_NOT_FALSE"
        )
    if AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT is not False:
        raise AccountEquityNewDiscriminatingEvidenceSurfaceError("SOURCE_SEAM_MUST_REMAIN_ABSENT")
    if COMPLETE_EVENT_STREAM_PROVEN is not False:
        raise AccountEquityNewDiscriminatingEvidenceSurfaceError(
            "COMPLETE_STREAM_MUST_REMAIN_UNPROVEN"
        )
    if EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED is not False:
        raise AccountEquityNewDiscriminatingEvidenceSurfaceError("EVENT_GET_NOT_AUTHORIZED")
    if OBSERVATION_NETWORK_GET_AUTHORIZED is not False:
        raise AccountEquityNewDiscriminatingEvidenceSurfaceError("OBSERVATION_GET_NOT_AUTHORIZED")
    if MS2_AUTHORIZED is not False:
        raise AccountEquityNewDiscriminatingEvidenceSurfaceError("MS2_AUTHORIZED_NOT_FALSE")
    if D6_FULLY_CLOSED is not False:
        raise AccountEquityNewDiscriminatingEvidenceSurfaceError("D6_FULLY_CLOSED_NOT_FALSE")
    if D7_AUTHORIZED is not False:
        raise AccountEquityNewDiscriminatingEvidenceSurfaceError("D7_AUTHORIZED_NOT_FALSE")
    if C17_CREATED is not False:
        raise AccountEquityNewDiscriminatingEvidenceSurfaceError("C17_CREATED_NOT_FALSE")
    if ACCOUNT_BILLS_REMAINS_CURRENT_NONCANONICAL is not True:
        raise AccountEquityNewDiscriminatingEvidenceSurfaceError("BILLS_CANONICALIZED_FORBIDDEN")
    if DAG_PIN != "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING":
        raise AccountEquityNewDiscriminatingEvidenceSurfaceError("DAG_PIN_DRIFT")


def _assert_parent_ck_pack(*, sealed_ck_pack: Path) -> None:
    if not sealed_ck_pack.is_dir():
        raise AccountEquityNewDiscriminatingEvidenceSurfaceError("PARENT_CK_PACK_MISSING")
    claims = _load_json_object(path=sealed_ck_pack / CLAIMS_FILE)
    _require_token(
        field="KIND_SET",
        payload=claims,
        expected=KIND_SET_EMPTY,
    )
    _require_token(field="KIND_SET_RESOLVED", payload=claims, expected=FALSE_TOKEN)
    _require_token(
        field="CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING",
        payload=claims,
        expected=FALSE_TOKEN,
    )
    _require_token(field="U05_STATUS", payload=claims, expected=DECISION_REMAIN_UNKNOWN)
    _require_token(field="U06_STATUS", payload=claims, expected=DECISION_REMAIN_UNKNOWN)
    _require_token(field="RESIDUAL_STATUS", payload=claims, expected=DECISION_REMAIN_UNKNOWN)
    _require_token(field="NEW_EVIDENCE_ACQUIRED", payload=claims, expected=FALSE_TOKEN)
    _require_token(field="NEXT_OWNER_GO_REQUIRED", payload=claims, expected=PIN_OWNER_GO)
    if verify_manifest_sha256_v1(store_root=sealed_ck_pack) != 0:
        raise AccountEquityNewDiscriminatingEvidenceSurfaceError("PARENT_CK_MANIFEST_INVALID")


def _assert_parent_ce_pack(*, sealed_ce_pack: Path) -> None:
    if not sealed_ce_pack.is_dir():
        raise AccountEquityNewDiscriminatingEvidenceSurfaceError("PARENT_CE_PACK_MISSING")
    claims = _load_json_object(path=sealed_ce_pack / CLAIMS_FILE)
    _require_token(
        field="NON_ALGEBRAIC_EMBEDDING_IDENTITY",
        payload=claims,
        expected=DURABLE_UNKNOWN_TOKEN,
    )
    _require_token(
        field="PREVIOUS_OWNER_SUPPLY_ASSUMPTION",
        payload=claims,
        expected="NOT_OPERATIONALIZED",
    )
    _require_token(
        field="FURTHER_U05_EMBEDDING_WITNESS_ACQUISITION",
        payload=claims,
        expected="STOPPED",
    )


def scan_owner_supplied_embedding_witness_surface_v1(
    *,
    repo_root: Path,
    surface_relpath: str = CANONICAL_INPUT_SURFACE_RELPATH,
) -> OwnerSuppliedEmbeddingWitnessSurfaceScanV1:
    _assert_standing_pins()
    surface = Path(repo_root) / surface_relpath
    if not surface.exists():
        return OwnerSuppliedEmbeddingWitnessSurfaceScanV1(
            surface_relpath=surface_relpath,
            surface_status=SURFACE_STATUS_MISSING,
            artifact_present=FALSE_TOKEN,
            artifact_count="0",
            artifact_path="",
            raw_bytes_digest="",
        )
    if not surface.is_dir():
        raise AccountEquityNewDiscriminatingEvidenceSurfaceError("INPUT_SURFACE_NOT_DIRECTORY")
    artifacts = sorted(
        path for path in surface.iterdir() if path.is_file() and path.name.endswith(".json")
    )
    if not artifacts:
        return OwnerSuppliedEmbeddingWitnessSurfaceScanV1(
            surface_relpath=surface_relpath,
            surface_status=SURFACE_STATUS_EMPTY,
            artifact_present=FALSE_TOKEN,
            artifact_count="0",
            artifact_path="",
            raw_bytes_digest="",
        )
    if len(artifacts) != 1:
        raise AccountEquityNewDiscriminatingEvidenceSurfaceError(
            f"MULTIPLE_ARTIFACTS_CONTRADICTORY:{len(artifacts)}"
        )
    first = artifacts[0]
    raw = first.read_bytes()
    return OwnerSuppliedEmbeddingWitnessSurfaceScanV1(
        surface_relpath=surface_relpath,
        surface_status=SURFACE_STATUS_PRESENT,
        artifact_present=TRUE_TOKEN,
        artifact_count="1",
        artifact_path=str(first.relative_to(repo_root)),
        raw_bytes_digest=hashlib.sha256(raw).hexdigest(),
    )


def _proof_from_artifact(payload: Mapping[str, Any]) -> dict[str, Any]:
    nested = payload.get("proof")
    if isinstance(nested, dict):
        return dict(nested)
    return dict(payload)


def evaluate_owner_supplied_embedding_witness_v1(
    *,
    scan: OwnerSuppliedEmbeddingWitnessSurfaceScanV1,
    repo_root: Path,
) -> dict[str, str]:
    reject_already_adjudicated_surface_as_this_surface_v1(claimed_surface_id=SURFACE_ID)
    reject_venue_eq_as_embedding_witness_v1(claimed_venue_eq_source=FALSE_TOKEN)
    if scan.artifact_present != TRUE_TOKEN:
        reject_absent_artifact_as_include_or_exclude_v1(claimed=DECISION_REMAIN_UNKNOWN)
        return {
            "layer": "ADJUDICATED_CONCLUSION",
            "surface_id": SURFACE_ID,
            "artifact_present": FALSE_TOKEN,
            "raw_bytes_digest": "",
            "artifact_source_class": NONE_TOKEN,
            "original_values_preserved": TRUE_TOKEN,
            "u05_bj_outcome": OUTCOME_NONQUALIFYING,
            "u05_bj_basis": "OWNER_SUPPLIED_EMBEDDING_WITNESS_ARTIFACT_ABSENT",
            "u05_include_proven": FALSE_TOKEN,
            "u05_exclude_proven": FALSE_TOKEN,
            "u05_status": DECISION_REMAIN_UNKNOWN,
            "u05_embedding_identity": DURABLE_UNKNOWN_TOKEN,
            "durable_unknown_reopened": FALSE_TOKEN,
            "new_discriminating_evidence_acquired": FALSE_TOKEN,
            "target_unknown": TARGET_U05,
            "evidence_class_id": CLASS_U05,
        }
    artifact_path = Path(repo_root) / scan.artifact_path
    raw = artifact_path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != scan.raw_bytes_digest:
        raise AccountEquityNewDiscriminatingEvidenceSurfaceError("RAW_EVIDENCE_DIGEST_MISMATCH")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise AccountEquityNewDiscriminatingEvidenceSurfaceError("JSON_MALFORMED") from exc
    if not isinstance(payload, dict):
        raise AccountEquityNewDiscriminatingEvidenceSurfaceError("ARTIFACT_JSON_NOT_OBJECT")
    claimed_surface = str(payload.get("surface_id") or SURFACE_ID)
    reject_already_adjudicated_surface_as_this_surface_v1(claimed_surface_id=claimed_surface)
    claimed_eq = str(payload.get("venue_eq_source_authority") or FALSE_TOKEN)
    reject_venue_eq_as_embedding_witness_v1(claimed_venue_eq_source=claimed_eq)
    claimed_digest = str(payload.get("raw_evidence_digest") or "")
    if claimed_digest and claimed_digest != digest:
        raise AccountEquityNewDiscriminatingEvidenceSurfaceError("RAW_EVIDENCE_DIGEST_MISMATCH")
    proof = _proof_from_artifact(payload)
    if "source_pack" not in proof and payload.get("source_pack"):
        proof["source_pack"] = payload["source_pack"]
    outcome = evaluate_u05_primary_proof_v1(proof=proof)
    include_proven = TRUE_TOKEN if outcome.outcome == OUTCOME_INCLUDE else FALSE_TOKEN
    exclude_proven = TRUE_TOKEN if outcome.outcome == OUTCOME_EXCLUDE else FALSE_TOKEN
    if outcome.outcome == OUTCOME_INCLUDE:
        u05_status = OUTCOME_INCLUDE
        embedding_identity = "SEPARATE"
        reopened = TRUE_TOKEN
        acquired = TRUE_TOKEN
    elif outcome.outcome == OUTCOME_EXCLUDE:
        u05_status = OUTCOME_EXCLUDE
        embedding_identity = "IN_BASE"
        reopened = TRUE_TOKEN
        acquired = TRUE_TOKEN
    else:
        u05_status = DECISION_REMAIN_UNKNOWN
        embedding_identity = DURABLE_UNKNOWN_TOKEN
        reopened = FALSE_TOKEN
        acquired = TRUE_TOKEN
    return {
        "layer": "ADJUDICATED_CONCLUSION",
        "surface_id": SURFACE_ID,
        "artifact_present": TRUE_TOKEN,
        "raw_bytes_digest": digest,
        "artifact_source_class": str(payload.get("artifact_class") or ADMISSIBLE_SOURCE_CLASS),
        "original_values_preserved": TRUE_TOKEN,
        "u05_bj_outcome": outcome.outcome,
        "u05_bj_basis": outcome.basis,
        "u05_include_proven": include_proven,
        "u05_exclude_proven": exclude_proven,
        "u05_status": u05_status,
        "u05_embedding_identity": embedding_identity,
        "durable_unknown_reopened": reopened,
        "new_discriminating_evidence_acquired": acquired,
        "target_unknown": TARGET_U05,
        "evidence_class_id": CLASS_U05,
    }


def already_adjudicated_exclusion_v1() -> dict[str, Any]:
    return {
        "layer": "ADJUDICATED_CONCLUSION",
        "census_kind": "FROZEN_ALREADY_ADJUDICATED_SURFACES_NOT_RESEARCHED",
        "this_surface_id": SURFACE_ID,
        "this_surface_kind": SURFACE_KIND,
        "already_adjudicated_count": str(len(FORBIDDEN_REUSED_SURFACES)),
        "records": [
            {
                "surface_id": surface_id,
                "reuse_as_this_surface": FALSE_TOKEN,
                "reason": "ALREADY_ADJUDICATED_NONE_BINDABLE_OR_GET_ALONE_NONQUALIFYING",
            }
            for surface_id in sorted(FORBIDDEN_REUSED_SURFACES)
        ],
    }


def reevaluate_downstream_v1(*, qualification: Mapping[str, str]) -> dict[str, Any]:
    u05_status = qualification["u05_status"]
    kind_set_closure_provable = FALSE_TOKEN
    if u05_status not in {OUTCOME_INCLUDE, OUTCOME_EXCLUDE}:
        reject_kind_set_resolved_while_remaining_unknown_v1(claimed=FALSE_TOKEN)
    return {
        "layer": "ADJUDICATED_CONCLUSION",
        "kind_set": KIND_SET_EMPTY,
        "kind_set_resolved": FALSE_TOKEN,
        "kind_set_closure_provable": kind_set_closure_provable,
        "canonically_valid_account_equity_source_mapping": FALSE_TOKEN,
        "reconstruction_algebra_complete": FALSE_TOKEN,
        "reconstruction_status": "INCOMPLETE_U04_U05_U06_UNRESOLVED_RESIDUAL_NOT_AN_ALGEBRA_TERM",
        "u04_status": "UNRESOLVED",
        "u05_status": u05_status,
        "u06_status": DECISION_REMAIN_UNKNOWN,
        "residual_status": DECISION_REMAIN_UNKNOWN,
        "u06_unchanged": TRUE_TOKEN,
        "residual_unchanged": TRUE_TOKEN,
        "equity_stock_readiness": (
            "NOT_READY_KIND_SET_UNRESOLVED_AND_MAPPING_NOT_CANONICALLY_VALID"
        ),
        "running_account_equity_available_for_sizing_status": (
            "UNBOUND_29P_SEMANTIC_MAPPING_UNPROVEN"
        ),
        "risk_sizing_readiness": (
            "NOT_READY_NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING_"
            "AND_29P_SEMANTIC_MAPPING_UNPROVEN"
        ),
        "local_advancement_exhausted": TRUE_TOKEN,
        "first_definitive_block": DAG_PIN,
        "exact_missing_predicate": EXACT_MISSING_PREDICATE,
        "next_productive_node": NEXT_PRODUCTIVE_NODE,
        "standing_full_core_dag_pin": DAG_PIN,
    }


def fixture_u05_include_witness_payload_v1() -> dict[str, str]:
    return {
        "surface_id": SURFACE_ID,
        "artifact_class": ADMISSIBLE_SOURCE_CLASS,
        "venue_eq_source_authority": FALSE_TOKEN,
        "unique_event_id": "LIAB-EVT-OWNER-SUPPLIED-001",
        "event_digest": "a" * 64,
        "ordering_key": "2026-09-15T07:30:00Z",
        "bound_account_identity_ref": "D4_BOUND_ACCOUNT",
        "bound_account_identity_digest": "b" * 64,
        "prior_anchor_id": "GOVERNED_TODAY_INITIAL_STOCK_ANCHOR_5d6c32292e0cb733",
        "event_after_prior_as_of": TRUE_TOKEN,
        "liability_event_semantic_class": "INDEPENDENT_LIABILITY_STOCK_EVENT",
        "mapped_numeric_effect": "12.5",
        "currency_domain": "USDC",
        "embedding_state": "SEPARATE",
        "embedding_proof_id": "NON_ALGEBRAIC_EMBEDDING_OWNER_SUPPLIED_001",
        "p01_overlap_state": "NON_OVERLAPPING",
        "independent_of_balance_snapshot": TRUE_TOKEN,
        "independent_of_algebraic_eq_identity": TRUE_TOKEN,
    }


def fixture_u05_exclude_witness_payload_v1() -> dict[str, str]:
    payload = fixture_u05_include_witness_payload_v1()
    payload["embedding_state"] = "IN_BASE"
    payload["p01_overlap_state"] = "U05_NOT_P01"
    payload["embedding_proof_id"] = "NON_ALGEBRAIC_EMBEDDING_IN_BASE_OWNER_SUPPLIED_001"
    return payload


def execute_account_equity_new_discriminating_evidence_surface_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    evidence_root: Path | str,
    repo_root: Path | str | None = None,
    input_surface_relpath: str | None = None,
    sealed_ck_pack: Path | str | None = None,
    sealed_ce_pack: Path | str | None = None,
    persist_as_of: str | None = None,
) -> AccountEquityNewDiscriminatingEvidenceSurfaceResultV1:
    if owner_go != OWNER_GO:
        raise AccountEquityNewDiscriminatingEvidenceSurfaceError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise AccountEquityNewDiscriminatingEvidenceSurfaceError("ORIGIN_MAIN_SHA_MISMATCH")
    _assert_standing_pins()
    reject_hope_get_v1(authorized_get_count="0", actual_get_count="0")
    reject_durable_unknown_as_include_or_exclude_v1(claimed=DURABLE_UNKNOWN_TOKEN)
    reject_already_adjudicated_surface_as_this_surface_v1(claimed_surface_id=SURFACE_ID)
    reject_venue_eq_as_embedding_witness_v1(claimed_venue_eq_source=FALSE_TOKEN)
    repo = Path(repo_root) if repo_root is not None else _REPO_ROOT
    ck_pack = (
        Path(sealed_ck_pack) if sealed_ck_pack is not None else repo / CANONICAL_CK_PACK_RELPATH
    )
    ce_pack = (
        Path(sealed_ce_pack) if sealed_ce_pack is not None else repo / CANONICAL_CE_PACK_RELPATH
    )
    _assert_parent_ck_pack(sealed_ck_pack=ck_pack)
    _assert_parent_ce_pack(sealed_ce_pack=ce_pack)
    as_of = persist_as_of or CANONICAL_PERSIST_AS_OF
    if as_of is None or not isinstance(as_of, str) or as_of.strip() == "" or as_of != as_of.strip():
        raise AccountEquityNewDiscriminatingEvidenceSurfaceError("FIELD_MISSING:persist_as_of")
    store = Path(evidence_root)
    store.mkdir(parents=True, exist_ok=True)
    surface_relpath = input_surface_relpath or CANONICAL_INPUT_SURFACE_RELPATH
    scan = scan_owner_supplied_embedding_witness_surface_v1(
        repo_root=repo,
        surface_relpath=surface_relpath,
    )
    qualification = evaluate_owner_supplied_embedding_witness_v1(scan=scan, repo_root=repo)
    downstream = reevaluate_downstream_v1(qualification=qualification)
    exclusion = already_adjudicated_exclusion_v1()
    claims = {
        "OWNER_GO": OWNER_GO,
        "OWNER_GO_STATUS": "CONSUMED",
        "PIN_OWNER_GO": PIN_OWNER_GO,
        "PIN_OWNER_GO_STATUS": "SATISFIED_BY_WORKPACKAGE",
        "SCHEMA_CLASS": SCHEMA_CLASS,
        "CONTRACT_VERSION": CONTRACT_VERSION,
        "AUTHORITY_EFFECT": AUTHORITY_EFFECT,
        "GENESIS_ID": EXPECTED_GENESIS_ID,
        "GENESIS_AS_OF": EXPECTED_GENESIS_AS_OF,
        "PERSIST_AS_OF": as_of,
        "PARENT_CK_PACK": CANONICAL_CK_PACK_RELPATH,
        "PARENT_CE_PACK": CANONICAL_CE_PACK_RELPATH,
        "WORKPACKAGE": SCHEMA_CLASS,
        "START_BLOCK": DAG_PIN,
        "SELECTED_DIMENSION": SELECTED_DIMENSION,
        "NEW_RAW_EVIDENCE_SURFACE": SURFACE_ID,
        "SURFACE_ID": SURFACE_ID,
        "SURFACE_KIND": SURFACE_KIND,
        "SURFACE_BINDING_STATUS": SURFACE_BINDING_STATUS,
        "PRIMARY_PROOF_ROLE": PRIMARY_PROOF_ROLE,
        "DISCRIMINATING_CAPABILITY": DISCRIMINATING_CAPABILITY,
        "INPUT_SURFACE": CANONICAL_INPUT_SURFACE_RELPATH,
        "SURFACE_STATUS": scan.surface_status,
        "ARTIFACT_PRESENT": scan.artifact_present,
        "ARTIFACT_COUNT": scan.artifact_count,
        "ARTIFACT_PATH": scan.artifact_path,
        "RAW_BYTES_DIGEST": scan.raw_bytes_digest,
        "ADMISSIBLE_SOURCE_CLASS": ADMISSIBLE_SOURCE_CLASS,
        "PREVIOUS_OWNER_SUPPLY_ASSUMPTION": "OPERATIONALIZED",
        "FURTHER_U05_VENUE_EMBEDDING_WITNESS_GET_ACQUISITION": "STOPPED",
        "CE_WITNESS_BRANCH_REOPEN_STATUS": "SURFACE_BOUND_NO_QUALIFYING_ARTIFACT"
        if scan.artifact_present != TRUE_TOKEN
        else "SURFACE_BOUND_ARTIFACT_EVALUATED",
        "U05_BJ_OUTCOME": qualification["u05_bj_outcome"],
        "U05_BJ_BASIS": qualification["u05_bj_basis"],
        "U05_INCLUDE_PROVEN": qualification["u05_include_proven"],
        "U05_EXCLUDE_PROVEN": qualification["u05_exclude_proven"],
        "U05_STATUS": qualification["u05_status"],
        "U05_KIND_DECISION": U05_KIND_DECISION,
        "U05_EMBEDDING_IDENTITY": qualification["u05_embedding_identity"],
        "U06_STATUS": DECISION_REMAIN_UNKNOWN,
        "U06_KIND_DECISION": DECISION_REMAIN_UNKNOWN,
        "U06_PLACEMENT_IDENTITY": DURABLE_UNKNOWN_TOKEN,
        "RESIDUAL_STATUS": DECISION_REMAIN_UNKNOWN,
        "RESIDUAL_KIND_DECISION": DECISION_REMAIN_UNKNOWN,
        "RESIDUAL_EXHAUSTIVENESS_IDENTITY": DURABLE_UNKNOWN_TOKEN,
        "DURABLE_UNKNOWN_NOT_INCLUDE": TRUE_TOKEN,
        "DURABLE_UNKNOWN_NOT_EXCLUDE": TRUE_TOKEN,
        "DURABLE_UNKNOWN_NOT_ABSENT_OR_ZERO": TRUE_TOKEN,
        "DURABLE_UNKNOWN_REOPENED": qualification["durable_unknown_reopened"],
        "NEW_DISCRIMINATING_SURFACE_BOUND": TRUE_TOKEN,
        "NEW_DISCRIMINATING_EVIDENCE_ACQUIRED": qualification[
            "new_discriminating_evidence_acquired"
        ],
        "ORIGINAL_VALUES_PRESERVED": TRUE_TOKEN,
        "KIND_SET": KIND_SET_EMPTY,
        "KIND_SET_RESOLVED": FALSE_TOKEN,
        "KIND_SET_STATUS": KIND_SET_EMPTY,
        "ACCOUNT_EQUITY_SOURCE_MAPPING": DAG_PIN,
        "ACCOUNT_EQUITY_SOURCE_MAPPING_STATUS": DAG_PIN,
        "CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING": FALSE_TOKEN,
        "MAPPING_PROVEN": FALSE_TOKEN,
        "SEMANTIC_MAPPING_PROVEN": FALSE_TOKEN,
        "RECONSTRUCTION_ALGEBRA_COMPLETE": FALSE_TOKEN,
        "RECONSTRUCTION_STATUS": downstream["reconstruction_status"],
        "EQUITY_STOCK_READINESS": downstream["equity_stock_readiness"],
        "RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING_STATUS": downstream[
            "running_account_equity_available_for_sizing_status"
        ],
        "RISK_SIZING_READINESS": downstream["risk_sizing_readiness"],
        "NO_GET_REQUIRED": TRUE_TOKEN,
        "NO_EQ_SOURCE_AUTHORITY": TRUE_TOKEN,
        "NO_ALGEBRAIC_UPLIFT": TRUE_TOKEN,
        "NO_HOPE_GET": TRUE_TOKEN,
        "NO_RETROACTIVE_SEALED_EVIDENCE_UPLIFT": TRUE_TOKEN,
        "MAX_GET_COUNT": "0",
        "AUTHORIZED_GET_COUNT": "0",
        "ACTUAL_GET_COUNT": "0",
        "VENUE_GET_COUNT": "0",
        "VENUE_GET_SURFACES": NONE_TOKEN,
        "RETRY_COUNT": "0",
        "POST_COUNT": "0",
        "SECRET_RESOLUTION_STATUS": "NOT_ATTEMPTED",
        "VENUE_EQ_SOURCE_AUTHORITY": FALSE_TOKEN,
        "ACCOUNT_BILLS_CANONICALIZED": FALSE_TOKEN,
        "GATE_A_REOPENED": FALSE_TOKEN,
        "GATE_B_REEXECUTED": FALSE_TOKEN,
        "MS2_AUTHORIZED": FALSE_TOKEN,
        "D6_FULLY_CLOSED": FALSE_TOKEN,
        "D7_AUTHORIZED": FALSE_TOKEN,
        "C17_CREATED": FALSE_TOKEN,
        "PRODUCTIVE_ACQUISITION_AUTHORIZED": FALSE_TOKEN,
        "PRODUCTIVE_ACQUISITION_EXECUTED": FALSE_TOKEN,
        "HOPE_GET_FORBIDDEN": TRUE_TOKEN,
        "LOCAL_ADVANCEMENT_EXHAUSTED": TRUE_TOKEN,
        "FIRST_DEFINITIVE_BLOCK": DAG_PIN,
        "EXACT_MISSING_PREDICATE": EXACT_MISSING_PREDICATE,
        "STANDING_FULL_CORE_DAG_PIN": DAG_PIN,
        "NEXT_PRODUCTIVE_NODE": NEXT_PRODUCTIVE_NODE,
        "BLOCKER_ID": BLOCKER_ID,
        "ARCHITECTURE_BLOCKER": ARCHITECTURE_BLOCKER,
        "PARENT_BLOCKER_ID": PARENT_BLOCKER_ID,
        "NEXT_OWNER_GO_REQUIRED": NEXT_OWNER_GO,
        "NEXT_ACTION": NEXT_ACTION,
        "PROTECTED_SURFACES_UNCHANGED": TRUE_TOKEN,
        "ATLAS_AUTHORITY": NONE_TOKEN,
        "U04_STATUS": "UNRESOLVED",
    }
    lineage = {
        "layer": "HISTORICAL",
        "origin_main_sha": origin_main_sha,
        "owner_go": OWNER_GO,
        "pin_owner_go": PIN_OWNER_GO,
        "genesis_id": EXPECTED_GENESIS_ID,
        "genesis_as_of": EXPECTED_GENESIS_AS_OF,
        "persist_as_of": as_of,
        "parent_ck_pack": CANONICAL_CK_PACK_RELPATH,
        "parent_ce_pack": CANONICAL_CE_PACK_RELPATH,
        "new_evidence_acquired": qualification["new_discriminating_evidence_acquired"],
        "hope_get_used": FALSE_TOKEN,
        "eq_source_authority_used": FALSE_TOKEN,
        "algebraic_uplift_used": FALSE_TOKEN,
        "duplicate_acquisition_used": FALSE_TOKEN,
        "already_adjudicated_surfaces_reused": FALSE_TOKEN,
    }
    protected = {
        "master_v2_unchanged": TRUE_TOKEN,
        "double_play_unchanged": TRUE_TOKEN,
        "bull_bear_state_switch_unchanged": TRUE_TOKEN,
        "self_learning_unchanged": TRUE_TOKEN,
        "top20_unchanged": TRUE_TOKEN,
        "full_core_autonomy_unchanged": TRUE_TOKEN,
        "step_29p_unchanged": TRUE_TOKEN,
        "trading_authority_unchanged": TRUE_TOKEN,
        "u04_not_reclassified_as_equity_stock_kind": TRUE_TOKEN,
        "u06_unchanged": TRUE_TOKEN,
        "residual_unchanged": TRUE_TOKEN,
        "gate_a_not_retried": TRUE_TOKEN,
        "gate_b_not_executed": TRUE_TOKEN,
        "bills_authority_unchanged": TRUE_TOKEN,
        "venue_eq_source_authority": FALSE_TOKEN,
        "ms2_authorized": FALSE_TOKEN,
        "reconstruction_implemented": FALSE_TOKEN,
        "dag_pin": DAG_PIN,
        "interest_accrued_get_not_retried": TRUE_TOKEN,
    }
    architecture = {
        "layer": "CANONICAL_AUTHORITY",
        "blocker_id": BLOCKER_ID,
        "architecture_blocker": ARCHITECTURE_BLOCKER,
        "parent_blocker_id": PARENT_BLOCKER_ID,
        "kind_set_resolved": FALSE_TOKEN,
        "canonically_valid_account_equity_source_mapping": FALSE_TOKEN,
        "hope_get_forbidden": TRUE_TOKEN,
        "venue_eq_source_authority": FALSE_TOKEN,
        "durable_unknown_is_not_include": TRUE_TOKEN,
        "durable_unknown_is_not_exclude": TRUE_TOKEN,
        "new_discriminating_surface_bound": TRUE_TOKEN,
        "surface_id": SURFACE_ID,
        "artifact_present": scan.artifact_present,
        "first_definitive_block": DAG_PIN,
        "exact_missing_predicate": EXACT_MISSING_PREDICATE,
        "next_productive_node": NEXT_PRODUCTIVE_NODE,
        "next_owner_go_required": NEXT_OWNER_GO,
        "next_action": NEXT_ACTION,
    }
    scan_payload = {
        "layer": "FORENSIC_RAW_EVIDENCE",
        "surface_id": SURFACE_ID,
        "surface_relpath": scan.surface_relpath,
        "surface_status": scan.surface_status,
        "artifact_present": scan.artifact_present,
        "artifact_count": scan.artifact_count,
        "artifact_path": scan.artifact_path,
        "raw_bytes_digest": scan.raw_bytes_digest,
        "original_values_preserved": TRUE_TOKEN,
        "unknown_explicit": TRUE_TOKEN if scan.artifact_present != TRUE_TOKEN else FALSE_TOKEN,
    }
    binding = {
        "layer": "CANONICAL_AUTHORITY",
        "surface_id": SURFACE_ID,
        "surface_kind": SURFACE_KIND,
        "surface_binding_status": SURFACE_BINDING_STATUS,
        "primary_proof_role": PRIMARY_PROOF_ROLE,
        "discriminating_capability": DISCRIMINATING_CAPABILITY,
        "http_method": NONE_TOKEN,
        "bound_endpoint": NONE_TOKEN,
        "max_get_count": "0",
        "not_get_alone": TRUE_TOKEN,
        "not_none_bindable_reuse": TRUE_TOKEN,
        "not_venue_eq_source": TRUE_TOKEN,
        "selected_dimension": SELECTED_DIMENSION,
    }
    layers = {
        "CANONICAL_AUTHORITY": "architecture_blocker_v1.json,surface_binding_v1.json",
        "FORENSIC_RAW_EVIDENCE": "scan_v1.json",
        "ADJUDICATED_CONCLUSION": (
            "qualification_v1.json,already_adjudicated_exclusion_v1.json,"
            "downstream_dependency_tree_v1.json"
        ),
        "HISTORICAL": "LINEAGE.json",
        "NAVIGATION": "FORBIDDEN_AS_AUTHORITY",
        "INTERPRETATION": "FORBIDDEN",
        "HYPOTHESIS": "FORBIDDEN",
        "UNRESOLVED_OR_CONTRADICTORY": BLOCKER_ID,
    }
    _persist_json(path=store / CLAIMS_FILE, payload=claims)
    _persist_json(path=store / "scan_v1.json", payload=scan_payload)
    _persist_json(path=store / "surface_binding_v1.json", payload=binding)
    _persist_json(path=store / "qualification_v1.json", payload=qualification)
    _persist_json(path=store / "already_adjudicated_exclusion_v1.json", payload=exclusion)
    _persist_json(path=store / "downstream_dependency_tree_v1.json", payload=downstream)
    _persist_json(path=store / "architecture_blocker_v1.json", payload=architecture)
    _persist_json(path=store / "protected_surfaces_v1.json", payload=protected)
    _persist_json(path=store / "layers_v1.json", payload=layers)
    _persist_json(path=store / "LINEAGE.json", payload=lineage)
    persist_manifest_sha256_v1(store_root=store)
    joined = "\n".join(path.read_text(encoding="utf-8") for path in store.glob("*.json"))
    lowered = joined.lower()
    if any(marker in lowered for marker in SECRET_MARKERS):
        raise AccountEquityNewDiscriminatingEvidenceSurfaceError("SECRET_MARKER_PERSISTED")
    if verify_manifest_sha256_v1(store_root=store) != 0:
        raise AccountEquityNewDiscriminatingEvidenceSurfaceError("MANIFEST_VERIFY_NOT_ZERO")
    return AccountEquityNewDiscriminatingEvidenceSurfaceResultV1(
        genesis_id=EXPECTED_GENESIS_ID,
        persist_as_of=as_of,
        store_root=str(store),
        surface_id=SURFACE_ID,
        surface_binding_status=SURFACE_BINDING_STATUS,
        artifact_present=scan.artifact_present,
        u05_bj_outcome=qualification["u05_bj_outcome"],
        u05_status=qualification["u05_status"],
        u06_status=DECISION_REMAIN_UNKNOWN,
        residual_status=DECISION_REMAIN_UNKNOWN,
        kind_set=KIND_SET_EMPTY,
        kind_set_resolved=FALSE_TOKEN,
        canonically_valid_account_equity_source_mapping=FALSE_TOKEN,
        first_definitive_block=DAG_PIN,
        exact_missing_predicate=EXACT_MISSING_PREDICATE,
        authorized_get_count="0",
        actual_get_count="0",
        post_count="0",
        evidence_manifest=str(store / "MANIFEST.sha256"),
    )


__all__ = (
    "ARCHITECTURE_BLOCKER",
    "BLOCKER_ID",
    "CANONICAL_INPUT_SURFACE_RELPATH",
    "CANONICAL_PACK_RELPATH",
    "CANONICAL_PERSIST_AS_OF",
    "EXACT_MISSING_PREDICATE",
    "EXPECTED_ORIGIN_MAIN_SHA",
    "FORBIDDEN_REUSED_SURFACES",
    "NEXT_ACTION",
    "NEXT_OWNER_GO",
    "NEXT_PRODUCTIVE_NODE",
    "OWNER_GO",
    "PARENT_BLOCKER_ID",
    "PIN_OWNER_GO",
    "SURFACE_ID",
    "AccountEquityNewDiscriminatingEvidenceSurfaceError",
    "already_adjudicated_exclusion_v1",
    "evaluate_owner_supplied_embedding_witness_v1",
    "execute_account_equity_new_discriminating_evidence_surface_v1",
    "fixture_u05_exclude_witness_payload_v1",
    "fixture_u05_include_witness_payload_v1",
    "reject_absent_artifact_as_include_or_exclude_v1",
    "reject_already_adjudicated_surface_as_this_surface_v1",
    "reject_venue_eq_as_embedding_witness_v1",
    "scan_owner_supplied_embedding_witness_surface_v1",
)
