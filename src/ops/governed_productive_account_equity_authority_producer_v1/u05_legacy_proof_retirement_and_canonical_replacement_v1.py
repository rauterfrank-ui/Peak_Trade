"""Retire unfulfillable legacy U05 INCLUDE/EXCLUDE as a productive blocker.

Consumes the workpackage Owner-GO. Historical U05 remains REMAIN_UNKNOWN.
Does not INCLUDE or EXCLUDE U05. Does not mint a synthetic witness.
Does not treat NOT_IN_CURRENT_PRODUCTIVE_KIND_SET as EXCLUDE. Does not
GET. Does not POST. Does not Hope-GET. Does not resolve secrets. Mapping
remains not canonically valid. AUTHORITY_EFFECT=NONE.

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
    MAPPING_PROVEN,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY as DAG_PIN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.account_equity_new_discriminating_evidence_surface_v1 import (
    BLOCKER_ID as PARENT_BLOCKER_ID,
    CANONICAL_PACK_RELPATH as CANONICAL_CL_PACK_RELPATH,
    NEXT_OWNER_GO as PIN_OWNER_GO,
    SURFACE_ID as LEGACY_SURFACE_ID,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.bj_future_admissible_evidence_and_include_exclude_qualification_law_v1 import (
    OUTCOME_EXCLUDE,
    OUTCOME_INCLUDE,
    TARGET_RESIDUAL,
    TARGET_U05,
    TARGET_U06,
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
    NAMED_REMAINING_UNKNOWN_NECESSARY_CLASSES,
    OBSERVATION_NETWORK_GET_AUTHORIZED,
    PRODUCTIVE_REMAINING_NECESSARY_EQUITY_STOCK_CLASSES,
    PRODUCTIVE_U05_EQUITY_STOCK_KIND_MEMBERSHIP,
    RAW_EQ_SOURCE_AUTHORITY,
    RECONSTRUCTION_ALGEBRA_COMPLETE,
    RESIDUAL_KIND_DECISION,
    SEMANTIC_MAPPING_PROVEN,
    U05_KIND_DECISION,
    U05_LEGACY_INCLUDE_EXCLUDE_PROOF_RETIRED_AS_PRODUCTIVE_BLOCKER,
    U05_LEGACY_KIND_DECISION,
    U05_PLACEMENT,
    U06_KIND_DECISION,
    U06_PLACEMENT,
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
from src.ops.governed_productive_account_equity_authority_producer_v1.residual_positive_necessary_kind_exhaustiveness_durable_unknown_pin_v1 import (
    reject_durable_unknown_as_include_or_exclude_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u06_paired_fee_event_and_once_only_equity_stock_effect_primary_proof_surface_binding_v1 import (
    reject_hope_get_v1,
)

OWNER_GO = "OWNER_GO_U05_LEGACY_PROOF_RETIREMENT_AND_CANONICAL_REPLACEMENT_V1"
EXPECTED_ORIGIN_MAIN_SHA = "0ffe4db1671173f54fbda46dbb94602e2729e0d4"
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_u05_legacy_proof_retirement_and_canonical_replacement_v1/"
    "2026-09-15T090000Z"
)
CANONICAL_PERSIST_AS_OF = "2026-09-15T09:00:00Z"
SCHEMA_CLASS = "U05_LEGACY_PROOF_RETIREMENT_AND_CANONICAL_REPLACEMENT_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
NONE_TOKEN = "NONE"
DURABLE_UNKNOWN_TOKEN = "DURABLE_UNKNOWN"
KIND_SET_EMPTY = "EMPTY_FAIL_CLOSED"
LEGACY_U05_HISTORICAL_STATUS = DECISION_REMAIN_UNKNOWN
LEGACY_U05_REQUIRED_FOR_PRODUCTIVE_PATH = FALSE_TOKEN
LEGACY_PROOF_DEBT_DISPOSITION = (
    "RETIRED_AS_PRODUCTIVE_BLOCKER_NOT_INCLUDE_NOT_EXCLUDE_HISTORICAL_UNKNOWN_PRESERVED"
)
NEW_CANONICAL_PRODUCTIVE_SEMANTIC = (
    "U05_NOT_IN_CURRENT_PRODUCTIVE_EQUITY_STOCK_KIND_SET_UNTIL_POSITIVE_INDEPENDENT_"
    "LIABILITY_EVENT_AND_SEPARATE_NON_ALGEBRAIC_EMBEDDING_PROVEN"
)
NEW_PROOF_LAW = (
    "PRODUCTIVE_EQUITY_STOCK_KIND_MEMBERSHIP_REQUIRES_POSITIVE_INDEPENDENT_LIABILITY_"
    "EVENT_AND_SEPARATE_NON_ALGEBRAIC_EMBEDDING_ABSENCE_OF_THAT_PROOF_IS_NOT_EXCLUDE_"
    "AND_IS_NOT_INCLUDE_AND_DOES_NOT_MINT_EQUITY_STOCK"
)
AVAILABLE_REAL_EVIDENCE_SOURCE = (
    "OWNER_DECISION_HISTORICAL_WITNESS_WILL_NOT_BE_SUPPLIED_PLUS_SEALED_CE_NO_"
    "ACQUIRABLE_REAL_WORLD_EMBEDDING_WITNESS_PLUS_STANDING_U05_PLACEMENT"
)
PRODUCTIVE_MEMBERSHIP = "NOT_IN_CURRENT_PRODUCTIVE_KIND_SET"
EXACT_MISSING_PREDICATE = (
    "U06_AND_RESIDUAL_REMAIN_DURABLE_UNKNOWN_AFTER_U05_LEGACY_INCLUDE_EXCLUDE_"
    "RETIRED_AS_PRODUCTIVE_BLOCKER_KIND_SET_CANNOT_RESOLVE_MAPPING_CANNOT_BECOME_"
    "CANONICALLY_VALID"
)
BLOCKER_ID = (
    "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING_AFTER_U05_LEGACY_PROOF_"
    "RETIRED_U06_AND_RESIDUAL_REMAIN_UNKNOWN"
)
ARCHITECTURE_BLOCKER = (
    "U05_LEGACY_INCLUDE_EXCLUDE_RETIRED_AS_PRODUCTIVE_BLOCKER_NOT_EXCLUDE_"
    "U06_AND_RESIDUAL_REMAIN_DURABLE_UNKNOWN_MAPPING_STILL_INVALID"
)
NEXT_PRODUCTIVE_NODE = "PRODUCTIVE_REMAINING_NECESSARY_EQUITY_STOCK_KIND_U06_AND_RESIDUAL"
NEXT_OWNER_GO = (
    "OWNER_GO_REQUIRED_TO_PROVE_INCLUDE_OR_EXCLUDE_OR_RATIFY_PRODUCTIVE_SCOPE_FOR_"
    "U06_AND_RESIDUAL_WITHOUT_NORMALIZING_DURABLE_UNKNOWN_V1"
)
NEXT_ACTION = (
    "STOP_FIRST_DEFINITIVE_BLOCK_NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_"
    "MAPPING_U05_LEGACY_RETIRED_U06_AND_RESIDUAL_REMAIN_UNKNOWN_NO_GET"
)
CLAIMS_FILE = "claims.json"
SECRET_MARKERS: tuple[str, ...] = (
    "ok-access",
    "api_secret",
    "api-secret",
    "passphrase",
    "secretref://",
)
_FORBIDDEN_DECISION_TOKENS = frozenset(
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


class U05LegacyProofRetirementAndCanonicalReplacementError(ValueError):
    """Fail-closed U05 legacy-proof retirement violation."""


@dataclass(frozen=True)
class U05LegacyProofRetirementAndCanonicalReplacementResultV1:
    genesis_id: str
    persist_as_of: str
    store_root: str
    legacy_u05_historical_status: str
    legacy_u05_required_for_productive_path: str
    productive_u05_equity_stock_kind_membership: str
    u05_kind_decision: str
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
        raise U05LegacyProofRetirementAndCanonicalReplacementError(f"JSON_NOT_OBJECT:{path.name}")
    return payload


def _require_token(*, field: str, payload: Mapping[str, Any], expected: str) -> None:
    actual = str(payload.get(field) or "")
    if actual != expected:
        raise U05LegacyProofRetirementAndCanonicalReplacementError(f"{field}_DRIFT:{actual}")


def reject_legacy_u05_unknown_as_include_or_exclude_v1(*, claimed: str) -> None:
    if claimed in _FORBIDDEN_DECISION_TOKENS:
        raise U05LegacyProofRetirementAndCanonicalReplacementError(
            f"LEGACY_U05_UNKNOWN_IS_NOT_INCLUDE_OR_EXCLUDE:{claimed}"
        )


def reject_productive_not_in_kind_set_as_exclude_v1(*, claimed: str) -> None:
    if claimed in {OUTCOME_EXCLUDE, "EXCLUDE", "IN_BASE", "U05_NOT_P01"}:
        raise U05LegacyProofRetirementAndCanonicalReplacementError(
            f"PRODUCTIVE_NOT_IN_KIND_SET_IS_NOT_EXCLUDE:{claimed}"
        )


def reject_synthetic_witness_as_productive_proof_v1(*, claimed: str) -> None:
    if claimed in {TRUE_TOKEN, "true", "USED", "FIXTURE", "SYNTHETIC"}:
        raise U05LegacyProofRetirementAndCanonicalReplacementError(
            f"SYNTHETIC_OR_FIXTURE_WITNESS_FORBIDDEN:{claimed}"
        )


def _assert_standing_pins() -> None:
    if U05_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise U05LegacyProofRetirementAndCanonicalReplacementError("U05_UNKNOWN_PRESERVED")
    if U05_LEGACY_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise U05LegacyProofRetirementAndCanonicalReplacementError("LEGACY_U05_UNKNOWN_PRESERVED")
    if U05_LEGACY_INCLUDE_EXCLUDE_PROOF_RETIRED_AS_PRODUCTIVE_BLOCKER is not True:
        raise U05LegacyProofRetirementAndCanonicalReplacementError("U05_LEGACY_NOT_RETIRED")
    if PRODUCTIVE_U05_EQUITY_STOCK_KIND_MEMBERSHIP != PRODUCTIVE_MEMBERSHIP:
        raise U05LegacyProofRetirementAndCanonicalReplacementError(
            "PRODUCTIVE_U05_MEMBERSHIP_DRIFT"
        )
    if PRODUCTIVE_REMAINING_NECESSARY_EQUITY_STOCK_CLASSES != (TARGET_U06, TARGET_RESIDUAL):
        raise U05LegacyProofRetirementAndCanonicalReplacementError(
            "PRODUCTIVE_REMAINING_CLASSES_DRIFT"
        )
    if NAMED_REMAINING_UNKNOWN_NECESSARY_CLASSES != (TARGET_U05, TARGET_U06, TARGET_RESIDUAL):
        raise U05LegacyProofRetirementAndCanonicalReplacementError(
            "LEGACY_NAMED_REMAINING_CLASSES_MUST_REMAIN_HISTORICAL"
        )
    if TARGET_U05 in PRODUCTIVE_REMAINING_NECESSARY_EQUITY_STOCK_CLASSES:
        raise U05LegacyProofRetirementAndCanonicalReplacementError(
            "U05_MUST_NOT_REMAIN_PRODUCTIVE_REMAINING_CLASS"
        )
    if U05_PLACEMENT != "EQUITY_STOCK_ONLY_IF_BORROW_LIAB_NOT_ALREADY_EMBEDDED":
        raise U05LegacyProofRetirementAndCanonicalReplacementError("U05_PLACEMENT_DRIFT")
    if U06_PLACEMENT != "EVENT_OR_RECONCILIATION_NOT_BLIND_SUBTRACTION":
        raise U05LegacyProofRetirementAndCanonicalReplacementError("U06_PLACEMENT_DRIFT")
    if U06_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise U05LegacyProofRetirementAndCanonicalReplacementError("U06_UNKNOWN_PRESERVED")
    if RESIDUAL_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise U05LegacyProofRetirementAndCanonicalReplacementError("RESIDUAL_UNKNOWN_PRESERVED")
    if KIND_SET_RESOLVED is not False:
        raise U05LegacyProofRetirementAndCanonicalReplacementError("KIND_SET_RESOLVED_NOT_FALSE")
    if RATIFIED_CLASSIFIED_KIND_SET:
        raise U05LegacyProofRetirementAndCanonicalReplacementError("KIND_SET_MUST_REMAIN_EMPTY")
    if CURRENT_PRODUCTIVE_ACCOUNT_EQUITY_SOURCE_MAPPING_CLOSURE_CLOSED is True:
        raise U05LegacyProofRetirementAndCanonicalReplacementError(
            "MAPPING_CLOSURE_CONSUMED_REEXECUTE_FORBIDDEN"
        )
    if CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING is not False:
        raise U05LegacyProofRetirementAndCanonicalReplacementError("MAPPING_MUST_REMAIN_INVALID")
    if MAPPING_PROVEN is not False:
        raise U05LegacyProofRetirementAndCanonicalReplacementError("MAPPING_PROVEN_NOT_FALSE")
    if SEMANTIC_MAPPING_PROVEN is not False:
        raise U05LegacyProofRetirementAndCanonicalReplacementError("SEMANTIC_MAPPING_NOT_FALSE")
    if RECONSTRUCTION_ALGEBRA_COMPLETE is not False:
        raise U05LegacyProofRetirementAndCanonicalReplacementError("ALGEBRA_MUST_REMAIN_INCOMPLETE")
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        raise U05LegacyProofRetirementAndCanonicalReplacementError(
            "RAW_EQ_SOURCE_AUTHORITY_NOT_FALSE"
        )
    if AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT is not False:
        raise U05LegacyProofRetirementAndCanonicalReplacementError("SOURCE_SEAM_MUST_REMAIN_ABSENT")
    if COMPLETE_EVENT_STREAM_PROVEN is not False:
        raise U05LegacyProofRetirementAndCanonicalReplacementError(
            "COMPLETE_STREAM_MUST_REMAIN_UNPROVEN"
        )
    if EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED is not False:
        raise U05LegacyProofRetirementAndCanonicalReplacementError("EVENT_GET_NOT_AUTHORIZED")
    if OBSERVATION_NETWORK_GET_AUTHORIZED is not False:
        raise U05LegacyProofRetirementAndCanonicalReplacementError("OBSERVATION_GET_NOT_AUTHORIZED")
    if MS2_AUTHORIZED is not False:
        raise U05LegacyProofRetirementAndCanonicalReplacementError("MS2_AUTHORIZED_NOT_FALSE")
    if D6_FULLY_CLOSED is not False:
        raise U05LegacyProofRetirementAndCanonicalReplacementError("D6_FULLY_CLOSED_NOT_FALSE")
    if D7_AUTHORIZED is not False:
        raise U05LegacyProofRetirementAndCanonicalReplacementError("D7_AUTHORIZED_NOT_FALSE")
    if C17_CREATED is not False:
        raise U05LegacyProofRetirementAndCanonicalReplacementError("C17_CREATED_NOT_FALSE")
    if ACCOUNT_BILLS_REMAINS_CURRENT_NONCANONICAL is not True:
        raise U05LegacyProofRetirementAndCanonicalReplacementError("BILLS_CANONICALIZED_FORBIDDEN")
    if DAG_PIN != "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING":
        raise U05LegacyProofRetirementAndCanonicalReplacementError("DAG_PIN_DRIFT")


def _assert_parent_cl_pack(*, sealed_cl_pack: Path) -> None:
    if not sealed_cl_pack.is_dir():
        raise U05LegacyProofRetirementAndCanonicalReplacementError("PARENT_CL_PACK_MISSING")
    claims = _load_json_object(path=sealed_cl_pack / CLAIMS_FILE)
    _require_token(field="SURFACE_ID", payload=claims, expected=LEGACY_SURFACE_ID)
    _require_token(field="ARTIFACT_PRESENT", payload=claims, expected=FALSE_TOKEN)
    _require_token(field="U05_STATUS", payload=claims, expected=DECISION_REMAIN_UNKNOWN)
    _require_token(field="U06_STATUS", payload=claims, expected=DECISION_REMAIN_UNKNOWN)
    _require_token(field="RESIDUAL_STATUS", payload=claims, expected=DECISION_REMAIN_UNKNOWN)
    _require_token(field="KIND_SET_RESOLVED", payload=claims, expected=FALSE_TOKEN)
    _require_token(
        field="CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING",
        payload=claims,
        expected=FALSE_TOKEN,
    )
    _require_token(field="NEXT_OWNER_GO_REQUIRED", payload=claims, expected=PIN_OWNER_GO)
    if verify_manifest_sha256_v1(store_root=sealed_cl_pack) != 0:
        raise U05LegacyProofRetirementAndCanonicalReplacementError("PARENT_CL_MANIFEST_INVALID")


def split_legacy_and_productive_u05_v1() -> dict[str, str]:
    reject_legacy_u05_unknown_as_include_or_exclude_v1(claimed=U05_KIND_DECISION)
    reject_productive_not_in_kind_set_as_exclude_v1(claimed=PRODUCTIVE_MEMBERSHIP)
    reject_synthetic_witness_as_productive_proof_v1(claimed=FALSE_TOKEN)
    return {
        "layer": "ADJUDICATED_CONCLUSION",
        "legacy_u05_historical_status": LEGACY_U05_HISTORICAL_STATUS,
        "legacy_u05_kind_decision": U05_KIND_DECISION,
        "legacy_u05_required_for_productive_path": LEGACY_U05_REQUIRED_FOR_PRODUCTIVE_PATH,
        "legacy_proof_debt_disposition": LEGACY_PROOF_DEBT_DISPOSITION,
        "legacy_include_proven": FALSE_TOKEN,
        "legacy_exclude_proven": FALSE_TOKEN,
        "legacy_named_remaining_still_includes_u05": TRUE_TOKEN,
        "new_canonical_productive_semantic": NEW_CANONICAL_PRODUCTIVE_SEMANTIC,
        "new_proof_law": NEW_PROOF_LAW,
        "available_real_evidence_source": AVAILABLE_REAL_EVIDENCE_SOURCE,
        "productive_u05_equity_stock_kind_membership": PRODUCTIVE_MEMBERSHIP,
        "synthetic_witness_used": FALSE_TOKEN,
        "fixture_used_as_productive_proof": FALSE_TOKEN,
        "durable_unknown_reopened": FALSE_TOKEN,
        "u05_include_proven": FALSE_TOKEN,
        "u05_exclude_proven": FALSE_TOKEN,
        "u05_status": DECISION_REMAIN_UNKNOWN,
        "u05_embedding_identity": DURABLE_UNKNOWN_TOKEN,
    }


def reevaluate_downstream_v1(*, split: Mapping[str, str]) -> dict[str, Any]:
    if split["u05_status"] != DECISION_REMAIN_UNKNOWN:
        raise U05LegacyProofRetirementAndCanonicalReplacementError("U05_STATUS_MUST_REMAIN_UNKNOWN")
    reject_durable_unknown_as_include_or_exclude_v1(claimed=DURABLE_UNKNOWN_TOKEN)
    return {
        "layer": "ADJUDICATED_CONCLUSION",
        "kind_set": KIND_SET_EMPTY,
        "kind_set_resolved": FALSE_TOKEN,
        "legacy_named_remaining_unknown_necessary_classes": ",".join(
            NAMED_REMAINING_UNKNOWN_NECESSARY_CLASSES
        ),
        "productive_remaining_necessary_equity_stock_classes": ",".join(
            PRODUCTIVE_REMAINING_NECESSARY_EQUITY_STOCK_CLASSES
        ),
        "canonically_valid_account_equity_source_mapping": FALSE_TOKEN,
        "reconstruction_algebra_complete": FALSE_TOKEN,
        "reconstruction_status": "INCOMPLETE_U04_UNRESOLVED_U06_AND_RESIDUAL_REMAIN_UNKNOWN_U05_NOT_CURRENT_PRODUCTIVE_TERM",
        "u04_status": "UNRESOLVED",
        "u05_legacy_status": DECISION_REMAIN_UNKNOWN,
        "u05_status": DECISION_REMAIN_UNKNOWN,
        "u06_status": DECISION_REMAIN_UNKNOWN,
        "residual_status": DECISION_REMAIN_UNKNOWN,
        "u06_unchanged": TRUE_TOKEN,
        "residual_unchanged": TRUE_TOKEN,
        "u04_unchanged": TRUE_TOKEN,
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


def execute_u05_legacy_proof_retirement_and_canonical_replacement_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    evidence_root: Path | str,
    repo_root: Path | str | None = None,
    sealed_cl_pack: Path | str | None = None,
    persist_as_of: str | None = None,
) -> U05LegacyProofRetirementAndCanonicalReplacementResultV1:
    if owner_go != OWNER_GO:
        raise U05LegacyProofRetirementAndCanonicalReplacementError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise U05LegacyProofRetirementAndCanonicalReplacementError("ORIGIN_MAIN_SHA_MISMATCH")
    _assert_standing_pins()
    reject_hope_get_v1(authorized_get_count="0", actual_get_count="0")
    reject_legacy_u05_unknown_as_include_or_exclude_v1(claimed=U05_KIND_DECISION)
    reject_productive_not_in_kind_set_as_exclude_v1(claimed=PRODUCTIVE_MEMBERSHIP)
    reject_synthetic_witness_as_productive_proof_v1(claimed=FALSE_TOKEN)
    repo = Path(repo_root) if repo_root is not None else _REPO_ROOT
    cl_pack = (
        Path(sealed_cl_pack) if sealed_cl_pack is not None else repo / CANONICAL_CL_PACK_RELPATH
    )
    _assert_parent_cl_pack(sealed_cl_pack=cl_pack)
    as_of = persist_as_of or CANONICAL_PERSIST_AS_OF
    if as_of is None or not isinstance(as_of, str) or as_of.strip() == "" or as_of != as_of.strip():
        raise U05LegacyProofRetirementAndCanonicalReplacementError("FIELD_MISSING:persist_as_of")
    store = Path(evidence_root)
    store.mkdir(parents=True, exist_ok=True)
    split = split_legacy_and_productive_u05_v1()
    downstream = reevaluate_downstream_v1(split=split)
    claims = {
        "OWNER_GO": OWNER_GO,
        "OWNER_GO_STATUS": "CONSUMED",
        "PIN_OWNER_GO": PIN_OWNER_GO,
        "PIN_OWNER_GO_STATUS": "SUPERSEDED_BY_OWNER_DECISION_ARTIFACT_WILL_NOT_BE_SUPPLIED",
        "SCHEMA_CLASS": SCHEMA_CLASS,
        "CONTRACT_VERSION": CONTRACT_VERSION,
        "AUTHORITY_EFFECT": AUTHORITY_EFFECT,
        "GENESIS_ID": EXPECTED_GENESIS_ID,
        "GENESIS_AS_OF": EXPECTED_GENESIS_AS_OF,
        "PERSIST_AS_OF": as_of,
        "PARENT_CL_PACK": CANONICAL_CL_PACK_RELPATH,
        "WORKPACKAGE": SCHEMA_CLASS,
        "START_BLOCK": DAG_PIN,
        "LEGACY_U05_HISTORICAL_STATUS": LEGACY_U05_HISTORICAL_STATUS,
        "LEGACY_U05_REQUIRED_FOR_PRODUCTIVE_PATH": LEGACY_U05_REQUIRED_FOR_PRODUCTIVE_PATH,
        "LEGACY_PROOF_DEBT_DISPOSITION": LEGACY_PROOF_DEBT_DISPOSITION,
        "NEW_CANONICAL_PRODUCTIVE_SEMANTIC": NEW_CANONICAL_PRODUCTIVE_SEMANTIC,
        "NEW_PROOF_LAW": NEW_PROOF_LAW,
        "AVAILABLE_REAL_EVIDENCE_SOURCE": AVAILABLE_REAL_EVIDENCE_SOURCE,
        "AUTHORITY_CHANGE": "ADDITIVE_PRODUCTIVE_SCOPE_SPLIT_NO_INCLUDE_OR_EXCLUDE",
        "MIGRATION_STRATEGY": "ADDITIVE_VERSIONED_SPLIT_LEGACY_UNKNOWN_PRESERVED_PRODUCTIVE_MEMBERSHIP_NOT_IN_SET",
        "LEGACY_SURFACE_ID": LEGACY_SURFACE_ID,
        "LEGACY_ARTIFACT_WILL_NOT_BE_SUPPLIED": TRUE_TOKEN,
        "U05_KIND_DECISION": U05_KIND_DECISION,
        "U05_LEGACY_KIND_DECISION": U05_LEGACY_KIND_DECISION,
        "U05_LEGACY_INCLUDE_EXCLUDE_PROOF_RETIRED_AS_PRODUCTIVE_BLOCKER": TRUE_TOKEN,
        "PRODUCTIVE_U05_EQUITY_STOCK_KIND_MEMBERSHIP": PRODUCTIVE_MEMBERSHIP,
        "NAMED_REMAINING_UNKNOWN_NECESSARY_CLASSES": ",".join(
            NAMED_REMAINING_UNKNOWN_NECESSARY_CLASSES
        ),
        "PRODUCTIVE_REMAINING_NECESSARY_EQUITY_STOCK_CLASSES": ",".join(
            PRODUCTIVE_REMAINING_NECESSARY_EQUITY_STOCK_CLASSES
        ),
        "U04_STATUS": "UNRESOLVED",
        "U05_STATUS": DECISION_REMAIN_UNKNOWN,
        "U05_LEGACY_STATUS": DECISION_REMAIN_UNKNOWN,
        "U05_INCLUDE_PROVEN": FALSE_TOKEN,
        "U05_EXCLUDE_PROVEN": FALSE_TOKEN,
        "U05_EMBEDDING_IDENTITY": DURABLE_UNKNOWN_TOKEN,
        "U06_STATUS": DECISION_REMAIN_UNKNOWN,
        "U06_KIND_DECISION": DECISION_REMAIN_UNKNOWN,
        "U06_PLACEMENT_IDENTITY": DURABLE_UNKNOWN_TOKEN,
        "RESIDUAL_STATUS": DECISION_REMAIN_UNKNOWN,
        "RESIDUAL_KIND_DECISION": DECISION_REMAIN_UNKNOWN,
        "RESIDUAL_EXHAUSTIVENESS_IDENTITY": DURABLE_UNKNOWN_TOKEN,
        "DURABLE_UNKNOWN_NOT_INCLUDE": TRUE_TOKEN,
        "DURABLE_UNKNOWN_NOT_EXCLUDE": TRUE_TOKEN,
        "DURABLE_UNKNOWN_NOT_ABSENT_OR_ZERO": TRUE_TOKEN,
        "DURABLE_UNKNOWN_REOPENED": FALSE_TOKEN,
        "SYNTHETIC_WITNESS_USED": FALSE_TOKEN,
        "FIXTURE_USED_AS_PRODUCTIVE_PROOF": FALSE_TOKEN,
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
    }
    lineage = {
        "layer": "HISTORICAL",
        "origin_main_sha": origin_main_sha,
        "owner_go": OWNER_GO,
        "pin_owner_go": PIN_OWNER_GO,
        "genesis_id": EXPECTED_GENESIS_ID,
        "genesis_as_of": EXPECTED_GENESIS_AS_OF,
        "persist_as_of": as_of,
        "parent_cl_pack": CANONICAL_CL_PACK_RELPATH,
        "historical_artifacts_rewritten": FALSE_TOKEN,
        "synthetic_witness_used": FALSE_TOKEN,
        "hope_get_used": FALSE_TOKEN,
        "eq_source_authority_used": FALSE_TOKEN,
        "algebraic_uplift_used": FALSE_TOKEN,
        "include_or_exclude_normalized": FALSE_TOKEN,
    }
    protected = {
        "master_v2_unchanged": TRUE_TOKEN,
        "double_play_unchanged": TRUE_TOKEN,
        "bull_bear_state_switch_unchanged": TRUE_TOKEN,
        "self_learning_unchanged": TRUE_TOKEN,
        "top20_unchanged": TRUE_TOKEN,
        "full_core_autonomy_unchanged": TRUE_TOKEN,
        "step_29p_unchanged": TRUE_TOKEN,
        "trading_logic_unchanged": TRUE_TOKEN,
        "u04_not_reclassified_as_equity_stock_kind": TRUE_TOKEN,
        "u06_unchanged": TRUE_TOKEN,
        "residual_unchanged": TRUE_TOKEN,
        "legacy_u05_unknown_preserved": TRUE_TOKEN,
        "gate_a_not_retried": TRUE_TOKEN,
        "gate_b_not_executed": TRUE_TOKEN,
        "bills_authority_unchanged": TRUE_TOKEN,
        "venue_eq_source_authority": FALSE_TOKEN,
        "ms2_authorized": FALSE_TOKEN,
        "reconstruction_implemented": FALSE_TOKEN,
        "dag_pin": DAG_PIN,
        "named_remaining_historical_tuple_unchanged": TRUE_TOKEN,
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
        "legacy_u05_required_for_productive_path": LEGACY_U05_REQUIRED_FOR_PRODUCTIVE_PATH,
        "productive_u05_equity_stock_kind_membership": PRODUCTIVE_MEMBERSHIP,
        "first_definitive_block": DAG_PIN,
        "exact_missing_predicate": EXACT_MISSING_PREDICATE,
        "next_productive_node": NEXT_PRODUCTIVE_NODE,
        "next_owner_go_required": NEXT_OWNER_GO,
        "next_action": NEXT_ACTION,
    }
    layers = {
        "CANONICAL_AUTHORITY": "architecture_blocker_v1.json",
        "FORENSIC_RAW_EVIDENCE": "NONE_NEW_RAW_BYTES_HISTORICAL_WITNESS_WILL_NOT_BE_SUPPLIED",
        "ADJUDICATED_CONCLUSION": "qualification_v1.json,downstream_dependency_tree_v1.json",
        "HISTORICAL": "LINEAGE.json",
        "NAVIGATION": "FORBIDDEN_AS_AUTHORITY",
        "INTERPRETATION": "FORBIDDEN",
        "HYPOTHESIS": "FORBIDDEN",
        "UNRESOLVED_OR_CONTRADICTORY": BLOCKER_ID,
        "MIGRATION_RATIFICATION": "claims.json",
        "CURRENT_PRODUCTIVE_MAPPING_STATUS": DAG_PIN,
    }
    _persist_json(path=store / CLAIMS_FILE, payload=claims)
    _persist_json(path=store / "qualification_v1.json", payload=split)
    _persist_json(path=store / "downstream_dependency_tree_v1.json", payload=downstream)
    _persist_json(path=store / "architecture_blocker_v1.json", payload=architecture)
    _persist_json(path=store / "protected_surfaces_v1.json", payload=protected)
    _persist_json(path=store / "layers_v1.json", payload=layers)
    _persist_json(path=store / "LINEAGE.json", payload=lineage)
    persist_manifest_sha256_v1(store_root=store)
    joined = "\n".join(path.read_text(encoding="utf-8") for path in store.glob("*.json"))
    lowered = joined.lower()
    if any(marker in lowered for marker in SECRET_MARKERS):
        raise U05LegacyProofRetirementAndCanonicalReplacementError("SECRET_MARKER_PERSISTED")
    if verify_manifest_sha256_v1(store_root=store) != 0:
        raise U05LegacyProofRetirementAndCanonicalReplacementError("MANIFEST_VERIFY_NOT_ZERO")
    return U05LegacyProofRetirementAndCanonicalReplacementResultV1(
        genesis_id=EXPECTED_GENESIS_ID,
        persist_as_of=as_of,
        store_root=str(store),
        legacy_u05_historical_status=LEGACY_U05_HISTORICAL_STATUS,
        legacy_u05_required_for_productive_path=LEGACY_U05_REQUIRED_FOR_PRODUCTIVE_PATH,
        productive_u05_equity_stock_kind_membership=PRODUCTIVE_MEMBERSHIP,
        u05_kind_decision=U05_KIND_DECISION,
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
    "AVAILABLE_REAL_EVIDENCE_SOURCE",
    "BLOCKER_ID",
    "CANONICAL_PACK_RELPATH",
    "CANONICAL_PERSIST_AS_OF",
    "EXACT_MISSING_PREDICATE",
    "EXPECTED_ORIGIN_MAIN_SHA",
    "LEGACY_PROOF_DEBT_DISPOSITION",
    "NEW_CANONICAL_PRODUCTIVE_SEMANTIC",
    "NEW_PROOF_LAW",
    "NEXT_ACTION",
    "NEXT_OWNER_GO",
    "NEXT_PRODUCTIVE_NODE",
    "OWNER_GO",
    "PARENT_BLOCKER_ID",
    "PIN_OWNER_GO",
    "U05LegacyProofRetirementAndCanonicalReplacementError",
    "execute_u05_legacy_proof_retirement_and_canonical_replacement_v1",
    "reject_legacy_u05_unknown_as_include_or_exclude_v1",
    "reject_productive_not_in_kind_set_as_exclude_v1",
    "reject_synthetic_witness_as_productive_proof_v1",
    "split_legacy_and_productive_u05_v1",
)
