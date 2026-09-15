"""Ratify productive-scope for U06 and residual without INCLUDE/EXCLUDE.

Consumes the workpackage Owner-GO. Historical U06 and residual remain
REMAIN_UNKNOWN. Does not INCLUDE or EXCLUDE either class. Does not
treat NOT_IN_CURRENT_PRODUCTIVE_KIND_SET as EXCLUDE. Does not GET.
Does not POST. Does not Hope-GET. Does not resolve secrets. Does not
resolve U04. Mapping remains not canonically valid. AUTHORITY_EFFECT=NONE.

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
from src.ops.governed_productive_account_equity_authority_producer_v1.bj_future_admissible_evidence_and_include_exclude_qualification_law_v1 import (
    OUTCOME_EXCLUDE,
    OUTCOME_INCLUDE,
    TARGET_RESIDUAL,
    TARGET_U05,
    TARGET_U06,
    evaluate_residual_primary_proof_v1,
    evaluate_u06_primary_proof_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    ACCOUNT_BILLS_REMAINS_CURRENT_NONCANONICAL,
    AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT,
    C17_CREATED,
    CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING,
    COMPLETE_EVENT_STREAM_PROVEN,
    CURRENT_PRODUCTIVE_REMAINING_NECESSARY_EQUITY_STOCK_CLASSES,
    D6_FULLY_CLOSED,
    D7_AUTHORIZED,
    EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED,
    KIND_SET_RESOLVED,
    MS2_AUTHORIZED,
    NAMED_REMAINING_UNKNOWN_NECESSARY_CLASSES,
    OBSERVATION_NETWORK_GET_AUTHORIZED,
    PRODUCTIVE_REMAINING_NECESSARY_EQUITY_STOCK_CLASSES,
    PRODUCTIVE_RESIDUAL_EQUITY_STOCK_KIND_MEMBERSHIP,
    PRODUCTIVE_U05_EQUITY_STOCK_KIND_MEMBERSHIP,
    PRODUCTIVE_U06_EQUITY_STOCK_KIND_MEMBERSHIP,
    RAW_EQ_SOURCE_AUTHORITY,
    RECONSTRUCTION_ALGEBRA_COMPLETE,
    RESIDUAL_KIND_DECISION,
    RESIDUAL_LEGACY_INCLUDE_EXCLUDE_PROOF_RETIRED_AS_PRODUCTIVE_BLOCKER,
    RESIDUAL_LEGACY_KIND_DECISION,
    SEMANTIC_MAPPING_PROVEN,
    U04_PLACEMENT,
    U05_KIND_DECISION,
    U06_KIND_DECISION,
    U06_LEGACY_INCLUDE_EXCLUDE_PROOF_RETIRED_AS_PRODUCTIVE_BLOCKER,
    U06_LEGACY_KIND_DECISION,
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
from src.ops.governed_productive_account_equity_authority_producer_v1.reconstruction_algebra_contract_v1 import (
    EARLIEST_UNRESOLVED_ALGEBRA_TERM,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.residual_positive_necessary_kind_exhaustiveness_durable_unknown_pin_v1 import (
    reject_durable_unknown_as_include_or_exclude_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u05_legacy_proof_retirement_and_canonical_replacement_v1 import (
    BLOCKER_ID as PARENT_BLOCKER_ID,
    CANONICAL_PACK_RELPATH as CANONICAL_CM_PACK_RELPATH,
    NEXT_OWNER_GO as PIN_OWNER_GO,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u06_paired_fee_event_and_once_only_equity_stock_effect_primary_proof_surface_binding_v1 import (
    reject_hope_get_v1,
)

OWNER_GO = "OWNER_GO_PRODUCTIVE_REMAINING_NECESSARY_EQUITY_STOCK_KIND_U06_AND_RESIDUAL_V1"
EXPECTED_ORIGIN_MAIN_SHA = "59c663c61352c16f888df669d2546e933858424d"
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_productive_remaining_necessary_equity_stock_kind_u06_and_residual_v1/"
    "2026-09-15T120000Z"
)
CANONICAL_PERSIST_AS_OF = "2026-09-15T12:00:00Z"
SCHEMA_CLASS = "PRODUCTIVE_REMAINING_NECESSARY_EQUITY_STOCK_KIND_U06_AND_RESIDUAL_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
NONE_TOKEN = "NONE"
DURABLE_UNKNOWN_TOKEN = "DURABLE_UNKNOWN"
KIND_SET_EMPTY = "EMPTY_FAIL_CLOSED"
PRODUCTIVE_MEMBERSHIP = "NOT_IN_CURRENT_PRODUCTIVE_KIND_SET"
U06_PROOF_LAW = (
    "PRODUCTIVE_EQUITY_STOCK_KIND_MEMBERSHIP_REQUIRES_POSITIVE_PAIRED_ONCE_ONLY_FEE_EVENT_"
    "WITH_EVENT_SEPARATE_PLACEMENT_ABSENCE_IS_NOT_EXCLUDE_AND_NOT_INCLUDE_AND_DOES_NOT_"
    "BLIND_SUBTRACT"
)
RESIDUAL_PROOF_LAW = (
    "PRODUCTIVE_EQUITY_STOCK_KIND_MEMBERSHIP_REQUIRES_POSITIVE_UNNAMED_NECESSARY_CLASS_"
    "INCLUDE_OR_POSITIVE_EXHAUSTIVENESS_CERTIFICATE_EXCLUDE_ABSENCE_IS_NOT_EXCLUDE_AND_"
    "NOT_INCLUDE_AND_IS_NOT_AN_ALGEBRA_TERM"
)
EXACT_MISSING_PREDICATE = (
    "U04_UNRESOLVED_AND_NO_RATIFIED_SOURCE_KIND_AFTER_U06_AND_RESIDUAL_LEGACY_INCLUDE_"
    "EXCLUDE_RETIRED_AS_PRODUCTIVE_BLOCKER_KIND_SET_CANNOT_RESOLVE_MAPPING_CANNOT_BECOME_"
    "CANONICALLY_VALID"
)
BLOCKER_ID = (
    "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING_AFTER_U06_AND_RESIDUAL_LEGACY_"
    "PROOF_RETIRED_U04_UNRESOLVED"
)
ARCHITECTURE_BLOCKER = (
    "U06_AND_RESIDUAL_LEGACY_INCLUDE_EXCLUDE_RETIRED_AS_PRODUCTIVE_BLOCKER_NOT_EXCLUDE_"
    "CURRENT_PRODUCTIVE_REMAINING_EMPTY_U04_UNRESOLVED_MAPPING_STILL_INVALID"
)
NEXT_PRODUCTIVE_NODE = "U04_PENDING_ORDER_RESERVATION_INCLUSION_UNRESOLVED"
NEXT_OWNER_GO = (
    "OWNER_GO_REQUIRED_TO_RESOLVE_U04_PENDING_ORDER_RESERVATION_INCLUSION_OR_TO_RATIFY_"
    "ACCOUNT_EQUITY_SOURCE_MAPPING_WITHOUT_KIND_SET_UPLIFT_V1"
)
NEXT_ACTION = (
    "STOP_FIRST_DEFINITIVE_BLOCK_NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_"
    "MAPPING_U06_AND_RESIDUAL_LEGACY_RETIRED_U04_UNRESOLVED_NO_GET"
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
        "IN_BASE",
        "EVENT_SEPARATE",
    }
)
_REPO_ROOT = Path(__file__).resolve().parents[3]


class ProductiveRemainingU06AndResidualError(ValueError):
    """Fail-closed U06/residual productive-scope violation."""


@dataclass(frozen=True)
class ProductiveRemainingU06AndResidualResultV1:
    genesis_id: str
    persist_as_of: str
    store_root: str
    u06_legacy_status: str
    u06_productive_scope_status: str
    residual_legacy_status: str
    residual_productive_scope_status: str
    current_productive_remaining: str
    kind_set_resolved: str
    canonically_valid_account_equity_source_mapping: str
    u04_status: str
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
        raise ProductiveRemainingU06AndResidualError(f"JSON_NOT_OBJECT:{path.name}")
    return payload


def _require_token(*, field: str, payload: Mapping[str, Any], expected: str) -> None:
    actual = str(payload.get(field) or "")
    if actual != expected:
        raise ProductiveRemainingU06AndResidualError(f"{field}_DRIFT:{actual}")


def reject_legacy_unknown_as_include_or_exclude_v1(*, claimed: str) -> None:
    if claimed in _FORBIDDEN_DECISION_TOKENS:
        raise ProductiveRemainingU06AndResidualError(
            f"LEGACY_UNKNOWN_IS_NOT_INCLUDE_OR_EXCLUDE:{claimed}"
        )


def reject_productive_not_in_kind_set_as_exclude_v1(*, claimed: str) -> None:
    if claimed in {OUTCOME_EXCLUDE, "EXCLUDE", "IN_BASE"}:
        raise ProductiveRemainingU06AndResidualError(
            f"PRODUCTIVE_NOT_IN_KIND_SET_IS_NOT_EXCLUDE:{claimed}"
        )


def _assert_standing_pins() -> None:
    if LIVE_ENABLED is not False:
        raise ProductiveRemainingU06AndResidualError("LIVE_ENABLED_NOT_FALSE")
    if LIVE_ARMED is not False:
        raise ProductiveRemainingU06AndResidualError("LIVE_ARMED_NOT_FALSE")
    if WIRE_SEND_PERMITTED is not False:
        raise ProductiveRemainingU06AndResidualError("WIRE_SEND_PERMITTED_NOT_FALSE")
    if U05_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise ProductiveRemainingU06AndResidualError("U05_UNKNOWN_PRESERVED")
    if PRODUCTIVE_U05_EQUITY_STOCK_KIND_MEMBERSHIP != PRODUCTIVE_MEMBERSHIP:
        raise ProductiveRemainingU06AndResidualError("PRODUCTIVE_U05_MEMBERSHIP_DRIFT")
    if U06_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise ProductiveRemainingU06AndResidualError("U06_UNKNOWN_PRESERVED")
    if U06_LEGACY_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise ProductiveRemainingU06AndResidualError("LEGACY_U06_UNKNOWN_PRESERVED")
    if U06_LEGACY_INCLUDE_EXCLUDE_PROOF_RETIRED_AS_PRODUCTIVE_BLOCKER is not True:
        raise ProductiveRemainingU06AndResidualError("U06_LEGACY_NOT_RETIRED")
    if PRODUCTIVE_U06_EQUITY_STOCK_KIND_MEMBERSHIP != PRODUCTIVE_MEMBERSHIP:
        raise ProductiveRemainingU06AndResidualError("PRODUCTIVE_U06_MEMBERSHIP_DRIFT")
    if RESIDUAL_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise ProductiveRemainingU06AndResidualError("RESIDUAL_UNKNOWN_PRESERVED")
    if RESIDUAL_LEGACY_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise ProductiveRemainingU06AndResidualError("LEGACY_RESIDUAL_UNKNOWN_PRESERVED")
    if RESIDUAL_LEGACY_INCLUDE_EXCLUDE_PROOF_RETIRED_AS_PRODUCTIVE_BLOCKER is not True:
        raise ProductiveRemainingU06AndResidualError("RESIDUAL_LEGACY_NOT_RETIRED")
    if PRODUCTIVE_RESIDUAL_EQUITY_STOCK_KIND_MEMBERSHIP != PRODUCTIVE_MEMBERSHIP:
        raise ProductiveRemainingU06AndResidualError("PRODUCTIVE_RESIDUAL_MEMBERSHIP_DRIFT")
    if PRODUCTIVE_REMAINING_NECESSARY_EQUITY_STOCK_CLASSES != (TARGET_U06, TARGET_RESIDUAL):
        raise ProductiveRemainingU06AndResidualError("CM_ERA_PRODUCTIVE_REMAINING_MUST_REMAIN")
    if CURRENT_PRODUCTIVE_REMAINING_NECESSARY_EQUITY_STOCK_CLASSES != ():
        raise ProductiveRemainingU06AndResidualError("CURRENT_PRODUCTIVE_REMAINING_MUST_BE_EMPTY")
    if TARGET_U06 in CURRENT_PRODUCTIVE_REMAINING_NECESSARY_EQUITY_STOCK_CLASSES:
        raise ProductiveRemainingU06AndResidualError("U06_MUST_NOT_REMAIN_CURRENT_PRODUCTIVE")
    if TARGET_RESIDUAL in CURRENT_PRODUCTIVE_REMAINING_NECESSARY_EQUITY_STOCK_CLASSES:
        raise ProductiveRemainingU06AndResidualError("RESIDUAL_MUST_NOT_REMAIN_CURRENT_PRODUCTIVE")
    if NAMED_REMAINING_UNKNOWN_NECESSARY_CLASSES != (TARGET_U05, TARGET_U06, TARGET_RESIDUAL):
        raise ProductiveRemainingU06AndResidualError("LEGACY_NAMED_REMAINING_MUST_REMAIN")
    if U06_PLACEMENT != "EVENT_OR_RECONCILIATION_NOT_BLIND_SUBTRACTION":
        raise ProductiveRemainingU06AndResidualError("U06_PLACEMENT_DRIFT")
    if U04_PLACEMENT != "AVAILABLE_FOR_SIZING_OR_RISK_SIZING":
        raise ProductiveRemainingU06AndResidualError("U04_PLACEMENT_DRIFT")
    if EARLIEST_UNRESOLVED_ALGEBRA_TERM != "U04_PENDING_ORDER_RESERVATION_INCLUSION_UNRESOLVED":
        raise ProductiveRemainingU06AndResidualError("U04_ALGEBRA_TERM_DRIFT")
    if KIND_SET_RESOLVED is not False:
        raise ProductiveRemainingU06AndResidualError("KIND_SET_RESOLVED_NOT_FALSE")
    if RATIFIED_CLASSIFIED_KIND_SET:
        raise ProductiveRemainingU06AndResidualError("KIND_SET_MUST_REMAIN_EMPTY")
    if CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING is not False:
        raise ProductiveRemainingU06AndResidualError("MAPPING_MUST_REMAIN_INVALID")
    if MAPPING_PROVEN is not False:
        raise ProductiveRemainingU06AndResidualError("MAPPING_PROVEN_NOT_FALSE")
    if SEMANTIC_MAPPING_PROVEN is not False:
        raise ProductiveRemainingU06AndResidualError("SEMANTIC_MAPPING_NOT_FALSE")
    if RECONSTRUCTION_ALGEBRA_COMPLETE is not False:
        raise ProductiveRemainingU06AndResidualError("ALGEBRA_MUST_REMAIN_INCOMPLETE")
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        raise ProductiveRemainingU06AndResidualError("RAW_EQ_SOURCE_AUTHORITY_NOT_FALSE")
    if AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT is not False:
        raise ProductiveRemainingU06AndResidualError("SOURCE_SEAM_MUST_REMAIN_ABSENT")
    if COMPLETE_EVENT_STREAM_PROVEN is not False:
        raise ProductiveRemainingU06AndResidualError("COMPLETE_STREAM_MUST_REMAIN_UNPROVEN")
    if EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED is not False:
        raise ProductiveRemainingU06AndResidualError("EVENT_GET_NOT_AUTHORIZED")
    if OBSERVATION_NETWORK_GET_AUTHORIZED is not False:
        raise ProductiveRemainingU06AndResidualError("OBSERVATION_GET_NOT_AUTHORIZED")
    if MS2_AUTHORIZED is not False:
        raise ProductiveRemainingU06AndResidualError("MS2_AUTHORIZED_NOT_FALSE")
    if D6_FULLY_CLOSED is not False:
        raise ProductiveRemainingU06AndResidualError("D6_FULLY_CLOSED_NOT_FALSE")
    if D7_AUTHORIZED is not False:
        raise ProductiveRemainingU06AndResidualError("D7_AUTHORIZED_NOT_FALSE")
    if C17_CREATED is not False:
        raise ProductiveRemainingU06AndResidualError("C17_CREATED_NOT_FALSE")
    if ACCOUNT_BILLS_REMAINS_CURRENT_NONCANONICAL is not True:
        raise ProductiveRemainingU06AndResidualError("BILLS_CANONICALIZED_FORBIDDEN")
    if DAG_PIN != "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING":
        raise ProductiveRemainingU06AndResidualError("DAG_PIN_DRIFT")


def _assert_parent_cm_pack(*, sealed_cm_pack: Path) -> None:
    if not sealed_cm_pack.is_dir():
        raise ProductiveRemainingU06AndResidualError("PARENT_CM_PACK_MISSING")
    claims = _load_json_object(path=sealed_cm_pack / CLAIMS_FILE)
    _require_token(field="U06_STATUS", payload=claims, expected=DECISION_REMAIN_UNKNOWN)
    _require_token(field="RESIDUAL_STATUS", payload=claims, expected=DECISION_REMAIN_UNKNOWN)
    _require_token(field="KIND_SET_RESOLVED", payload=claims, expected=FALSE_TOKEN)
    _require_token(
        field="CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING",
        payload=claims,
        expected=FALSE_TOKEN,
    )
    _require_token(
        field="PRODUCTIVE_REMAINING_NECESSARY_EQUITY_STOCK_CLASSES",
        payload=claims,
        expected=f"{TARGET_U06},{TARGET_RESIDUAL}",
    )
    _require_token(field="NEXT_OWNER_GO_REQUIRED", payload=claims, expected=PIN_OWNER_GO)
    if verify_manifest_sha256_v1(store_root=sealed_cm_pack) != 0:
        raise ProductiveRemainingU06AndResidualError("PARENT_CM_MANIFEST_INVALID")


def classify_u06_and_residual_productive_scope_v1() -> dict[str, str]:
    reject_legacy_unknown_as_include_or_exclude_v1(claimed=U06_KIND_DECISION)
    reject_legacy_unknown_as_include_or_exclude_v1(claimed=RESIDUAL_KIND_DECISION)
    reject_productive_not_in_kind_set_as_exclude_v1(claimed=PRODUCTIVE_MEMBERSHIP)
    u06_law = evaluate_u06_primary_proof_v1(proof={})
    residual_law = evaluate_residual_primary_proof_v1(proof={})
    if u06_law.outcome in {OUTCOME_INCLUDE, OUTCOME_EXCLUDE}:
        raise ProductiveRemainingU06AndResidualError("U06_ABSENT_PROOF_MUST_BE_NONQUALIFYING")
    if residual_law.outcome in {OUTCOME_INCLUDE, OUTCOME_EXCLUDE}:
        raise ProductiveRemainingU06AndResidualError("RESIDUAL_ABSENT_PROOF_MUST_BE_NONQUALIFYING")
    return {
        "layer": "ADJUDICATED_CONCLUSION",
        "u06_legacy_status": DECISION_REMAIN_UNKNOWN,
        "u06_kind_decision": U06_KIND_DECISION,
        "u06_bj_outcome": u06_law.outcome,
        "u06_bj_basis": u06_law.basis,
        "u06_include_proven": FALSE_TOKEN,
        "u06_exclude_proven": FALSE_TOKEN,
        "u06_placement_identity": DURABLE_UNKNOWN_TOKEN,
        "u06_productive_scope_status": PRODUCTIVE_MEMBERSHIP,
        "u06_proof_law": U06_PROOF_LAW,
        "u06_evidence": (
            "SEALED_CF_NONE_BINDABLE_PLUS_CG_PLACEMENT_DURABLE_UNKNOWN_PLUS_STANDING_"
            "U06_PLACEMENT_EVENT_OR_RECONCILIATION_NOT_BLIND_SUBTRACTION_PLUS_ABSENT_BJ_PROOF"
        ),
        "residual_legacy_status": DECISION_REMAIN_UNKNOWN,
        "residual_kind_decision": RESIDUAL_KIND_DECISION,
        "residual_bj_outcome": residual_law.outcome,
        "residual_bj_basis": residual_law.basis,
        "residual_include_proven": FALSE_TOKEN,
        "residual_exclude_proven": FALSE_TOKEN,
        "residual_exhaustiveness_identity": DURABLE_UNKNOWN_TOKEN,
        "residual_productive_scope_status": PRODUCTIVE_MEMBERSHIP,
        "residual_proof_law": RESIDUAL_PROOF_LAW,
        "residual_evidence": (
            "SEALED_CH_NONE_BINDABLE_PLUS_CI_EXHAUSTIVENESS_DURABLE_UNKNOWN_PLUS_ABSENT_"
            "CERTIFICATE_PLUS_RESIDUAL_NOT_AN_ALGEBRA_TERM"
        ),
        "cm_era_productive_remaining": ",".join(
            PRODUCTIVE_REMAINING_NECESSARY_EQUITY_STOCK_CLASSES
        ),
        "current_productive_remaining": ",".join(
            CURRENT_PRODUCTIVE_REMAINING_NECESSARY_EQUITY_STOCK_CLASSES
        ),
        "synthetic_witness_used": FALSE_TOKEN,
        "durable_unknown_reopened": FALSE_TOKEN,
    }


def reevaluate_downstream_v1(*, split: Mapping[str, str]) -> dict[str, Any]:
    if split["u06_legacy_status"] != DECISION_REMAIN_UNKNOWN:
        raise ProductiveRemainingU06AndResidualError("U06_STATUS_MUST_REMAIN_UNKNOWN")
    if split["residual_legacy_status"] != DECISION_REMAIN_UNKNOWN:
        raise ProductiveRemainingU06AndResidualError("RESIDUAL_STATUS_MUST_REMAIN_UNKNOWN")
    reject_durable_unknown_as_include_or_exclude_v1(claimed=DURABLE_UNKNOWN_TOKEN)
    return {
        "layer": "ADJUDICATED_CONCLUSION",
        "kind_set": KIND_SET_EMPTY,
        "kind_set_resolved": FALSE_TOKEN,
        "legacy_named_remaining_unknown_necessary_classes": ",".join(
            NAMED_REMAINING_UNKNOWN_NECESSARY_CLASSES
        ),
        "cm_era_productive_remaining_necessary_equity_stock_classes": split[
            "cm_era_productive_remaining"
        ],
        "current_productive_remaining_necessary_equity_stock_classes": split[
            "current_productive_remaining"
        ],
        "canonically_valid_account_equity_source_mapping": FALSE_TOKEN,
        "reconstruction_algebra_complete": FALSE_TOKEN,
        "reconstruction_status": (
            "INCOMPLETE_U04_UNRESOLVED_U06_AND_RESIDUAL_NOT_CURRENT_PRODUCTIVE_TERMS"
        ),
        "u04_status": "UNRESOLVED",
        "u04_kind_set_disposition": "NOT_EQUITY_STOCK_AFFECTING",
        "u05_legacy_status": DECISION_REMAIN_UNKNOWN,
        "u06_legacy_status": DECISION_REMAIN_UNKNOWN,
        "residual_legacy_status": DECISION_REMAIN_UNKNOWN,
        "u04_unchanged": TRUE_TOKEN,
        "u05_unchanged": TRUE_TOKEN,
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
        "earliest_unresolved_algebra_term": EARLIEST_UNRESOLVED_ALGEBRA_TERM,
    }


def execute_productive_remaining_necessary_equity_stock_kind_u06_and_residual_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    evidence_root: Path | str,
    repo_root: Path | str | None = None,
    sealed_cm_pack: Path | str | None = None,
    persist_as_of: str | None = None,
) -> ProductiveRemainingU06AndResidualResultV1:
    if owner_go != OWNER_GO:
        raise ProductiveRemainingU06AndResidualError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise ProductiveRemainingU06AndResidualError("ORIGIN_MAIN_SHA_MISMATCH")
    _assert_standing_pins()
    reject_hope_get_v1(authorized_get_count="0", actual_get_count="0")
    reject_legacy_unknown_as_include_or_exclude_v1(claimed=U06_KIND_DECISION)
    reject_legacy_unknown_as_include_or_exclude_v1(claimed=RESIDUAL_KIND_DECISION)
    reject_productive_not_in_kind_set_as_exclude_v1(claimed=PRODUCTIVE_MEMBERSHIP)
    repo = Path(repo_root) if repo_root is not None else _REPO_ROOT
    cm_pack = (
        Path(sealed_cm_pack) if sealed_cm_pack is not None else repo / CANONICAL_CM_PACK_RELPATH
    )
    _assert_parent_cm_pack(sealed_cm_pack=cm_pack)
    as_of = persist_as_of or CANONICAL_PERSIST_AS_OF
    if as_of is None or not isinstance(as_of, str) or as_of.strip() == "" or as_of != as_of.strip():
        raise ProductiveRemainingU06AndResidualError("FIELD_MISSING:persist_as_of")
    store = Path(evidence_root)
    store.mkdir(parents=True, exist_ok=True)
    split = classify_u06_and_residual_productive_scope_v1()
    downstream = reevaluate_downstream_v1(split=split)
    claims = {
        "OWNER_GO": OWNER_GO,
        "OWNER_GO_STATUS": "CONSUMED",
        "PIN_OWNER_GO": PIN_OWNER_GO,
        "PIN_OWNER_GO_STATUS": "SATISFIED_BY_PRODUCTIVE_SCOPE_RATIFICATION_NOT_INCLUDE_OR_EXCLUDE",
        "SCHEMA_CLASS": SCHEMA_CLASS,
        "CONTRACT_VERSION": CONTRACT_VERSION,
        "AUTHORITY_EFFECT": AUTHORITY_EFFECT,
        "GENESIS_ID": EXPECTED_GENESIS_ID,
        "GENESIS_AS_OF": EXPECTED_GENESIS_AS_OF,
        "PERSIST_AS_OF": as_of,
        "PARENT_CM_PACK": CANONICAL_CM_PACK_RELPATH,
        "WORKPACKAGE": SCHEMA_CLASS,
        "START_BLOCK": DAG_PIN,
        "U06_LEGACY_STATUS": DECISION_REMAIN_UNKNOWN,
        "U06_PRODUCTIVE_SCOPE_STATUS": PRODUCTIVE_MEMBERSHIP,
        "U06_EVIDENCE": split["u06_evidence"],
        "U06_PROOF_LAW": U06_PROOF_LAW,
        "U06_BJ_OUTCOME": split["u06_bj_outcome"],
        "U06_BJ_BASIS": split["u06_bj_basis"],
        "U06_INCLUDE_PROVEN": FALSE_TOKEN,
        "U06_EXCLUDE_PROVEN": FALSE_TOKEN,
        "U06_KIND_DECISION": U06_KIND_DECISION,
        "U06_LEGACY_KIND_DECISION": U06_LEGACY_KIND_DECISION,
        "U06_LEGACY_INCLUDE_EXCLUDE_PROOF_RETIRED_AS_PRODUCTIVE_BLOCKER": TRUE_TOKEN,
        "PRODUCTIVE_U06_EQUITY_STOCK_KIND_MEMBERSHIP": PRODUCTIVE_MEMBERSHIP,
        "U06_PLACEMENT_IDENTITY": DURABLE_UNKNOWN_TOKEN,
        "RESIDUAL_LEGACY_STATUS": DECISION_REMAIN_UNKNOWN,
        "RESIDUAL_PRODUCTIVE_SCOPE_STATUS": PRODUCTIVE_MEMBERSHIP,
        "RESIDUAL_EVIDENCE": split["residual_evidence"],
        "RESIDUAL_PROOF_LAW": RESIDUAL_PROOF_LAW,
        "RESIDUAL_BJ_OUTCOME": split["residual_bj_outcome"],
        "RESIDUAL_BJ_BASIS": split["residual_bj_basis"],
        "RESIDUAL_INCLUDE_PROVEN": FALSE_TOKEN,
        "RESIDUAL_EXCLUDE_PROVEN": FALSE_TOKEN,
        "RESIDUAL_KIND_DECISION": RESIDUAL_KIND_DECISION,
        "RESIDUAL_LEGACY_KIND_DECISION": RESIDUAL_LEGACY_KIND_DECISION,
        "RESIDUAL_LEGACY_INCLUDE_EXCLUDE_PROOF_RETIRED_AS_PRODUCTIVE_BLOCKER": TRUE_TOKEN,
        "PRODUCTIVE_RESIDUAL_EQUITY_STOCK_KIND_MEMBERSHIP": PRODUCTIVE_MEMBERSHIP,
        "RESIDUAL_EXHAUSTIVENESS_IDENTITY": DURABLE_UNKNOWN_TOKEN,
        "AUTHORITY_CHANGE": "ADDITIVE_PRODUCTIVE_SCOPE_SPLIT_NO_INCLUDE_OR_EXCLUDE",
        "MIGRATION_STRATEGY": (
            "ADDITIVE_VERSIONED_SPLIT_CM_ERA_PRODUCTIVE_REMAINING_PRESERVED_"
            "CURRENT_PRODUCTIVE_REMAINING_EMPTY"
        ),
        "NAMED_REMAINING_UNKNOWN_NECESSARY_CLASSES": ",".join(
            NAMED_REMAINING_UNKNOWN_NECESSARY_CLASSES
        ),
        "CM_ERA_PRODUCTIVE_REMAINING_NECESSARY_EQUITY_STOCK_CLASSES": ",".join(
            PRODUCTIVE_REMAINING_NECESSARY_EQUITY_STOCK_CLASSES
        ),
        "CURRENT_PRODUCTIVE_REMAINING_NECESSARY_EQUITY_STOCK_CLASSES": ",".join(
            CURRENT_PRODUCTIVE_REMAINING_NECESSARY_EQUITY_STOCK_CLASSES
        ),
        "U04_STATUS": "UNRESOLVED",
        "U04_KIND_SET_DISPOSITION": "NOT_EQUITY_STOCK_AFFECTING",
        "EARLIEST_UNRESOLVED_ALGEBRA_TERM": EARLIEST_UNRESOLVED_ALGEBRA_TERM,
        "U05_STATUS": DECISION_REMAIN_UNKNOWN,
        "U05_LEGACY_STATUS": DECISION_REMAIN_UNKNOWN,
        "U06_STATUS": DECISION_REMAIN_UNKNOWN,
        "RESIDUAL_STATUS": DECISION_REMAIN_UNKNOWN,
        "DURABLE_UNKNOWN_NOT_INCLUDE": TRUE_TOKEN,
        "DURABLE_UNKNOWN_NOT_EXCLUDE": TRUE_TOKEN,
        "DURABLE_UNKNOWN_NOT_ABSENT_OR_ZERO": TRUE_TOKEN,
        "DURABLE_UNKNOWN_REOPENED": FALSE_TOKEN,
        "SYNTHETIC_WITNESS_USED": FALSE_TOKEN,
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
        "parent_cm_pack": CANONICAL_CM_PACK_RELPATH,
        "historical_artifacts_rewritten": FALSE_TOKEN,
        "synthetic_witness_used": FALSE_TOKEN,
        "hope_get_used": FALSE_TOKEN,
        "eq_source_authority_used": FALSE_TOKEN,
        "include_or_exclude_normalized": FALSE_TOKEN,
        "u04_resolved": FALSE_TOKEN,
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
        "u04_not_resolved": TRUE_TOKEN,
        "legacy_u05_unknown_preserved": TRUE_TOKEN,
        "legacy_u06_unknown_preserved": TRUE_TOKEN,
        "legacy_residual_unknown_preserved": TRUE_TOKEN,
        "cm_era_productive_remaining_unchanged": TRUE_TOKEN,
        "named_remaining_historical_tuple_unchanged": TRUE_TOKEN,
        "gate_a_not_retried": TRUE_TOKEN,
        "gate_b_not_executed": TRUE_TOKEN,
        "bills_authority_unchanged": TRUE_TOKEN,
        "venue_eq_source_authority": FALSE_TOKEN,
        "ms2_authorized": FALSE_TOKEN,
        "reconstruction_implemented": FALSE_TOKEN,
        "dag_pin": DAG_PIN,
    }
    architecture = {
        "layer": "CANONICAL_AUTHORITY",
        "blocker_id": BLOCKER_ID,
        "architecture_blocker": ARCHITECTURE_BLOCKER,
        "parent_blocker_id": PARENT_BLOCKER_ID,
        "kind_set_resolved": FALSE_TOKEN,
        "canonically_valid_account_equity_source_mapping": FALSE_TOKEN,
        "u06_productive_scope_status": PRODUCTIVE_MEMBERSHIP,
        "residual_productive_scope_status": PRODUCTIVE_MEMBERSHIP,
        "current_productive_remaining": "",
        "u04_status": "UNRESOLVED",
        "first_definitive_block": DAG_PIN,
        "exact_missing_predicate": EXACT_MISSING_PREDICATE,
        "next_productive_node": NEXT_PRODUCTIVE_NODE,
        "next_owner_go_required": NEXT_OWNER_GO,
        "next_action": NEXT_ACTION,
        "atlas_authority": NONE_TOKEN,
    }
    layers = {
        "CANONICAL_AUTHORITY": "architecture_blocker_v1.json",
        "FORENSIC_RAW_EVIDENCE": "NONE_NEW_RAW_BYTES_SEALED_CF_CG_CH_CI_CONSUMED",
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
        raise ProductiveRemainingU06AndResidualError("SECRET_MARKER_PERSISTED")
    if verify_manifest_sha256_v1(store_root=store) != 0:
        raise ProductiveRemainingU06AndResidualError("MANIFEST_VERIFY_NOT_ZERO")
    return ProductiveRemainingU06AndResidualResultV1(
        genesis_id=EXPECTED_GENESIS_ID,
        persist_as_of=as_of,
        store_root=str(store),
        u06_legacy_status=DECISION_REMAIN_UNKNOWN,
        u06_productive_scope_status=PRODUCTIVE_MEMBERSHIP,
        residual_legacy_status=DECISION_REMAIN_UNKNOWN,
        residual_productive_scope_status=PRODUCTIVE_MEMBERSHIP,
        current_productive_remaining=",".join(
            CURRENT_PRODUCTIVE_REMAINING_NECESSARY_EQUITY_STOCK_CLASSES
        ),
        kind_set_resolved=FALSE_TOKEN,
        canonically_valid_account_equity_source_mapping=FALSE_TOKEN,
        u04_status="UNRESOLVED",
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
    "CANONICAL_PACK_RELPATH",
    "CANONICAL_PERSIST_AS_OF",
    "EXACT_MISSING_PREDICATE",
    "EXPECTED_ORIGIN_MAIN_SHA",
    "NEXT_ACTION",
    "NEXT_OWNER_GO",
    "NEXT_PRODUCTIVE_NODE",
    "OWNER_GO",
    "PARENT_BLOCKER_ID",
    "PIN_OWNER_GO",
    "ProductiveRemainingU06AndResidualError",
    "classify_u06_and_residual_productive_scope_v1",
    "execute_productive_remaining_necessary_equity_stock_kind_u06_and_residual_v1",
    "reject_legacy_unknown_as_include_or_exclude_v1",
    "reject_productive_not_in_kind_set_as_exclude_v1",
)
