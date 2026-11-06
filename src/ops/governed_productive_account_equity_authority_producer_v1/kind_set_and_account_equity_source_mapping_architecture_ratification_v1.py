"""Ratify KIND_SET / mapping architecture after three durable UNKNOWNs.

Consumes the workpackage Owner-GO. Satisfies the CI-named ratification GO.
Does not GET. Does not POST. Does not INCLUDE or EXCLUDE U05/U06/residual.
Does not redefine canonical mapping validity to bypass KIND_SET closure.
Does not convert DURABLE_UNKNOWN into INCLUDE, EXCLUDE, absent, zero,
none, or not-applicable. AUTHORITY_EFFECT=NONE.

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
from src.ops.governed_productive_account_equity_authority_producer_v1.account_equity_source_mapping_ratification_v1 import (
    MAPPING_COVERAGE_PARTIAL,
    SOURCE_MAPPING_STORE_RELPATH,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.bj_future_admissible_evidence_and_include_exclude_qualification_law_v1 import (
    CLASS_RESIDUAL,
    CLASS_U05,
    CLASS_U06,
    OUTCOME_EXCLUDE,
    OUTCOME_INCLUDE,
    TARGET_RESIDUAL,
    TARGET_U05,
    TARGET_U06,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    ACCOUNT_BILLS_REMAINS_CURRENT_NONCANONICAL,
    AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT,
    C17_CREATED,
    CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING,
    COMPLETE_EVENT_STREAM_PROVEN,
    D6_FULLY_CLOSED,
    D7_AUTHORIZED,
    EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED,
    KIND_SET_CLOSEOUT_STATUS,
    KIND_SET_EVIDENCE_PERSIST_STATUS,
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
from src.ops.governed_productive_account_equity_authority_producer_v1.reconstruction_algebra_contract_v1 import (
    EARLIEST_UNRESOLVED_ALGEBRA_TERM,
    UNRESOLVED_ALGEBRA_TERMS,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.residual_positive_necessary_kind_exhaustiveness_durable_unknown_pin_v1 import (
    BLOCKER_ID as PARENT_BLOCKER_ID,
    CANONICAL_PACK_RELPATH as CANONICAL_CI_PACK_RELPATH,
    NEXT_OWNER_GO as PIN_OWNER_GO,
    ResidualPositiveNecessaryKindExhaustivenessDurableUnknownPinError,
    reject_durable_unknown_as_include_or_exclude_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u06_paired_fee_event_and_once_only_equity_stock_effect_primary_proof_surface_binding_v1 import (
    reject_hope_get_v1,
)

OWNER_GO = "OWNER_GO_KIND_SET_ACCOUNT_EQUITY_MAPPING_TO_NEXT_DEFINITIVE_BLOCK_V1"
EXPECTED_ORIGIN_MAIN_SHA = "7d4dbad87a85ad2219f6d1a7fa0f733c233aa2af"
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_kind_set_and_account_equity_source_mapping_"
    "architecture_ratification_v1/2026-09-15T060000Z"
)
CANONICAL_BE_PACK_RELPATH = f"{SOURCE_MAPPING_STORE_RELPATH}/2026-09-13T192000Z"
CANONICAL_PERSIST_AS_OF = "2026-09-15T06:00:00Z"
SCHEMA_CLASS = "KIND_SET_AND_ACCOUNT_EQUITY_SOURCE_MAPPING_ARCHITECTURE_RATIFICATION_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
NONE_TOKEN = "NONE"
DURABLE_UNKNOWN_TOKEN = "DURABLE_UNKNOWN"
KIND_SET_EMPTY = "EMPTY_FAIL_CLOSED"
STATE_KNOWN_INCLUDED = "KNOWN_INCLUDED"
STATE_KNOWN_EXCLUDED = "KNOWN_EXCLUDED"
STATE_DURABLE_UNKNOWN = "DURABLE_UNKNOWN"
STATE_UNRESOLVED = "UNRESOLVED"
COMPLETE_REQUIRES = (
    "RATIFIED_CLASSIFIED_KIND_SET_RESOLVED_AND_NON_EMPTY_AND_"
    "AUTHORIZED_SOURCE_AND_RANGE_AND_ORDERING_AND_PROVENANCE"
)
RATIFIED_MAPPING_ARCHITECTURE = (
    "FAIL_CLOSED_KNOWN_VS_DURABLE_UNKNOWN_VS_UNRESOLVED_DISTINCTION_WITHOUT_CANONICAL_VALIDITY"
)
CANDIDATE_A = "GOVERNED_PARTIAL_MAPPING_WITH_UNKNOWN_AS_FIRST_CLASS_UNRESOLVED_STATE"
CANDIDATE_B = "MAPPING_VALIDITY_CONDITIONAL_ON_UNRESOLVED_NECESSARY_KINDS"
CANDIDATE_C = "FAIL_CLOSED_DISTINCTION_KNOWN_MAPPINGS_VS_DURABLE_UNKNOWN_DIMENSIONS"
CANDIDATE_D = "IMPOSSIBILITY_OF_CANONICAL_MAPPING_VALIDITY_WITHOUT_NEW_EVIDENCE"
VERDICT_A = (
    "REJECTED_AS_CURRENT_CANONICAL_VALIDITY_ALREADY_PERSISTED_AS_PARTIAL_FAIL_CLOSED_NO_UPLIFT"
)
VERDICT_B = "RATIFIED_AS_VALIDITY_RULE_CONDITION_CURRENTLY_UNSATISFIED"
VERDICT_C = "RATIFIED_AS_ARCHITECTURE_WITHOUT_VALIDITY_CLAIM"
VERDICT_D = "RATIFIED_FOR_CANONICAL_VALIDITY_CLAIM_IMPOSSIBLE_ON_CURRENT_EVIDENCE"
MAPPING_COVERAGE_CONSUMED = MAPPING_COVERAGE_PARTIAL
KNOWN_INCLUDED_SOURCE_KINDS = NONE_TOKEN
DURABLE_UNKNOWN_DIMENSIONS = (
    "U05_EMBEDDING_IDENTITY,U06_PLACEMENT_IDENTITY,RESIDUAL_EXHAUSTIVENESS_IDENTITY"
)
UNRESOLVED_DIMENSIONS = (
    "U04_PENDING_ORDER_RESERVATION_INCLUSION,"
    "F12_F13_F16_F17_F18,"
    "RETENTION_COVERAGE,"
    "ORDERING_COMPLETENESS,"
    "AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM,"
    "STEP29P_SEMANTIC_MAPPING_RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING"
)
EXACT_MISSING_PREDICATE = (
    "KIND_SET_RESOLVED_REQUIRES_INCLUDE_OR_EXCLUDE_NOT_REMAIN_UNKNOWN_AND_NOT_"
    "DURABLE_UNKNOWN_SUBSTITUTE_FOR_U05_U06_AND_RESIDUAL_AND_COMPLETE_REQUIRES_"
    "NON_EMPTY_RATIFIED_CLASSIFIED_KIND_SET_AND_AUTHORIZED_SOURCE_AND_RANGE_"
    "AND_ORDERING_AND_PROVENANCE_AND_29P_SOURCE_SEMANTIC_FOR_RUNNING_ACCOUNT_"
    "EQUITY_AVAILABLE_FOR_SIZING"
)
BLOCKER_ID = (
    "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING_KIND_SET_CLOSURE_"
    "REQUIRES_INCLUDE_OR_EXCLUDE_OF_U05_U06_RESIDUAL_COMPLETE_REQUIRES_"
    "UNSATISFIED_29P_SEMANTIC_MAPPING_UNBOUND"
)
ARCHITECTURE_BLOCKER = (
    "CANONICAL_MAPPING_VALIDITY_REQUIRES_KIND_SET_CLOSURE_AND_COMPLETE_REQUIRES_"
    "CONJUNCTION_DURABLE_UNKNOWN_IS_NOT_INCLUDE_OR_EXCLUDE_NO_LOCAL_VALIDITY_UPLIFT"
)
NEXT_PRODUCTIVE_NODE = "INCLUDE_OR_EXCLUDE_PROOF_FOR_NAMED_REMAINING_UNKNOWN_NECESSARY_KINDS"
NEXT_OWNER_GO = (
    "OWNER_GO_REQUIRED_TO_PROVE_INCLUDE_OR_EXCLUDE_FOR_NAMED_REMAINING_UNKNOWN_"
    "NECESSARY_KINDS_U05_U06_RESIDUAL_OR_TO_ACQUIRE_NEW_EVIDENCE_THAT_CAN_"
    "SUPPORT_THOSE_DECISIONS_V1"
)
NEXT_ACTION = (
    "STOP_FIRST_DEFINITIVE_BLOCK_NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_"
    "MAPPING_KIND_SET_CLOSURE_UNPROVEN_NO_GET"
)
CLAIMS_FILE = "claims.json"
SECRET_MARKERS: tuple[str, ...] = (
    "ok-access",
    "api_secret",
    "api-secret",
    "passphrase",
    "secretref://",
)
_VALIDITY_UPLIFT_TOKENS = frozenset(
    {
        OUTCOME_INCLUDE,
        OUTCOME_EXCLUDE,
        "INCLUDE",
        "EXCLUDE",
        "true",
        "TRUE",
        "VALID",
        "MAPPING_VALID",
        "KIND_SET_RESOLVED_TRUE",
        "CANONICALLY_VALID",
        "ABSENT",
        "absent",
        "0",
        "zero",
        "NONE",
        "N/A",
        "NOT_APPLICABLE",
        "NO_RESIDUAL",
    }
)
_REPO_ROOT = Path(__file__).resolve().parents[3]


class KindSetAndAccountEquitySourceMappingArchitectureRatificationError(ValueError):
    """Fail-closed KIND_SET / mapping architecture ratification violation."""


@dataclass(frozen=True)
class KindSetAndAccountEquitySourceMappingArchitectureRatificationResultV1:
    genesis_id: str
    persist_as_of: str
    store_root: str
    ratified_mapping_architecture: str
    kind_set: str
    kind_set_resolved: str
    canonically_valid_account_equity_source_mapping: str
    first_definitive_block: str
    exact_missing_predicate: str
    reconstruction_status: str
    equity_stock_readiness: str
    risk_sizing_readiness: str
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
        raise KindSetAndAccountEquitySourceMappingArchitectureRatificationError(
            f"JSON_NOT_OBJECT:{path.name}"
        )
    return payload


def _require_token(*, field: str, payload: Mapping[str, Any], expected: str) -> None:
    actual = str(payload.get(field) or "")
    if actual != expected:
        raise KindSetAndAccountEquitySourceMappingArchitectureRatificationError(
            f"{field}_DRIFT:{actual}"
        )


def reject_mapping_validity_redefinition_v1(*, claimed: str) -> None:
    if claimed in _VALIDITY_UPLIFT_TOKENS:
        raise KindSetAndAccountEquitySourceMappingArchitectureRatificationError(
            f"MAPPING_VALIDITY_MUST_NOT_BE_REDEFINED:{claimed}"
        )


def reject_kind_set_resolved_while_remaining_unknown_v1(*, claimed: str) -> None:
    if claimed in {"true", "TRUE", "RESOLVED", "KIND_SET_RESOLVED_TRUE"}:
        raise KindSetAndAccountEquitySourceMappingArchitectureRatificationError(
            f"KIND_SET_CANNOT_RESOLVE_WHILE_REMAINING_UNKNOWN:{claimed}"
        )


def reject_durable_unknown_as_kind_include_or_exclude_v1(*, claimed: str) -> None:
    try:
        reject_durable_unknown_as_include_or_exclude_v1(claimed=claimed)
    except ResidualPositiveNecessaryKindExhaustivenessDurableUnknownPinError as exc:
        raise KindSetAndAccountEquitySourceMappingArchitectureRatificationError(str(exc)) from exc


def _assert_standing_pins() -> None:
    if U05_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise KindSetAndAccountEquitySourceMappingArchitectureRatificationError(
            "U05_UNKNOWN_PRESERVED"
        )
    if U06_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise KindSetAndAccountEquitySourceMappingArchitectureRatificationError(
            "U06_UNKNOWN_PRESERVED"
        )
    if RESIDUAL_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise KindSetAndAccountEquitySourceMappingArchitectureRatificationError(
            "RESIDUAL_KIND_DECISION_NOT_REMAIN_UNKNOWN"
        )
    if KIND_SET_RESOLVED is not False:
        raise KindSetAndAccountEquitySourceMappingArchitectureRatificationError(
            "KIND_SET_RESOLVED_NOT_FALSE"
        )
    if RATIFIED_CLASSIFIED_KIND_SET:
        raise KindSetAndAccountEquitySourceMappingArchitectureRatificationError(
            "KIND_SET_MUST_REMAIN_EMPTY"
        )
    if CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING is not False:
        raise KindSetAndAccountEquitySourceMappingArchitectureRatificationError(
            "MAPPING_MUST_REMAIN_NOT_CANONICALLY_VALID"
        )
    if MAPPING_PROVEN is not False:
        raise KindSetAndAccountEquitySourceMappingArchitectureRatificationError(
            "MAPPING_PROVEN_NOT_FALSE"
        )
    if SEMANTIC_MAPPING_PROVEN is not False:
        raise KindSetAndAccountEquitySourceMappingArchitectureRatificationError(
            "SEMANTIC_MAPPING_PROVEN_NOT_FALSE"
        )
    if RECONSTRUCTION_ALGEBRA_COMPLETE is not False:
        raise KindSetAndAccountEquitySourceMappingArchitectureRatificationError(
            "RECONSTRUCTION_ALGEBRA_MUST_REMAIN_INCOMPLETE"
        )
    if AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT is not False:
        raise KindSetAndAccountEquitySourceMappingArchitectureRatificationError(
            "SOURCE_SEAM_MUST_REMAIN_ABSENT"
        )
    if COMPLETE_EVENT_STREAM_PROVEN is not False:
        raise KindSetAndAccountEquitySourceMappingArchitectureRatificationError(
            "COMPLETE_STREAM_MUST_REMAIN_UNPROVEN"
        )
    if EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED is not False:
        raise KindSetAndAccountEquitySourceMappingArchitectureRatificationError(
            "EVENT_ACQUISITION_NETWORK_GET_MUST_REMAIN_UNAUTHORIZED"
        )
    if OBSERVATION_NETWORK_GET_AUTHORIZED is not False:
        raise KindSetAndAccountEquitySourceMappingArchitectureRatificationError(
            "OBSERVATION_NETWORK_GET_MUST_REMAIN_UNAUTHORIZED"
        )
    if MS2_AUTHORIZED is not False:
        raise KindSetAndAccountEquitySourceMappingArchitectureRatificationError(
            "MS2_AUTHORIZED_NOT_FALSE"
        )
    if D6_FULLY_CLOSED is not False:
        raise KindSetAndAccountEquitySourceMappingArchitectureRatificationError(
            "D6_FULLY_CLOSED_NOT_FALSE"
        )
    if D7_AUTHORIZED is not False:
        raise KindSetAndAccountEquitySourceMappingArchitectureRatificationError(
            "D7_AUTHORIZED_NOT_FALSE"
        )
    if C17_CREATED is not False:
        raise KindSetAndAccountEquitySourceMappingArchitectureRatificationError(
            "C17_CREATED_NOT_FALSE"
        )
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        raise KindSetAndAccountEquitySourceMappingArchitectureRatificationError(
            "RAW_EQ_SOURCE_AUTHORITY_NOT_FALSE"
        )
    if ACCOUNT_BILLS_REMAINS_CURRENT_NONCANONICAL is not True:
        raise KindSetAndAccountEquitySourceMappingArchitectureRatificationError(
            "ACCOUNT_BILLS_MUST_REMAIN_NONCANONICAL"
        )
    if DAG_PIN != "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING":
        raise KindSetAndAccountEquitySourceMappingArchitectureRatificationError("DAG_PIN_DRIFT")
    if EARLIEST_UNRESOLVED_ALGEBRA_TERM != "U04_PENDING_ORDER_RESERVATION_INCLUSION_UNRESOLVED":
        raise KindSetAndAccountEquitySourceMappingArchitectureRatificationError(
            "EARLIEST_ALGEBRA_TERM_DRIFT"
        )


def _assert_parent_ci_pack(*, sealed_ci_pack: Path) -> None:
    if verify_manifest_sha256_v1(store_root=sealed_ci_pack) != 0:
        raise KindSetAndAccountEquitySourceMappingArchitectureRatificationError(
            "PARENT_CI_MANIFEST_VERIFY_NOT_ZERO"
        )
    claims = _load_json_object(path=sealed_ci_pack / CLAIMS_FILE)
    _require_token(
        field="SCHEMA_CLASS",
        payload=claims,
        expected=("RESIDUAL_POSITIVE_NECESSARY_KIND_EXHAUSTIVENESS_DURABLE_UNKNOWN_PIN_V1"),
    )
    _require_token(field="NEXT_OWNER_GO_REQUIRED", payload=claims, expected=PIN_OWNER_GO)
    _require_token(field="KIND_SET", payload=claims, expected=KIND_SET_EMPTY)
    _require_token(field="KIND_SET_RESOLVED", payload=claims, expected=FALSE_TOKEN)
    _require_token(
        field="CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING",
        payload=claims,
        expected=FALSE_TOKEN,
    )
    _require_token(field="U05_STATUS", payload=claims, expected=DECISION_REMAIN_UNKNOWN)
    _require_token(field="U06_STATUS", payload=claims, expected=DECISION_REMAIN_UNKNOWN)
    _require_token(
        field="RESIDUAL_DECISION_AFTER", payload=claims, expected=DECISION_REMAIN_UNKNOWN
    )
    _require_token(
        field="EXHAUSTIVENESS_IDENTITY_STATUS",
        payload=claims,
        expected=DURABLE_UNKNOWN_TOKEN,
    )
    _require_token(field="U05_EMBEDDING_IDENTITY", payload=claims, expected=DURABLE_UNKNOWN_TOKEN)
    _require_token(field="U06_PLACEMENT_IDENTITY", payload=claims, expected=DURABLE_UNKNOWN_TOKEN)
    _require_token(field="ACTUAL_GET_COUNT", payload=claims, expected="0")
    _require_token(field="POST_COUNT", payload=claims, expected="0")


def _assert_sealed_be_mapping_pack(*, sealed_be_pack: Path) -> None:
    if verify_manifest_sha256_v1(store_root=sealed_be_pack) != 0:
        raise KindSetAndAccountEquitySourceMappingArchitectureRatificationError(
            "BE_MAPPING_MANIFEST_VERIFY_NOT_ZERO"
        )
    claims = _load_json_object(path=sealed_be_pack / CLAIMS_FILE)
    _require_token(field="RATIFIED_SOURCE_KINDS", payload=claims, expected=NONE_TOKEN)
    _require_token(field="MAPPING_PERSISTED", payload=claims, expected=TRUE_TOKEN)
    _require_token(
        field="MAPPING_COVERAGE_STATUS", payload=claims, expected=MAPPING_COVERAGE_PARTIAL
    )
    _require_token(field="KIND_SET", payload=claims, expected=KIND_SET_EMPTY)
    _require_token(field="KIND_SET_RESOLVED", payload=claims, expected=FALSE_TOKEN)
    _require_token(
        field="CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING",
        payload=claims,
        expected=FALSE_TOKEN,
    )
    _require_token(field="U05_KIND_DECISION", payload=claims, expected=DECISION_REMAIN_UNKNOWN)
    _require_token(field="U06_KIND_DECISION", payload=claims, expected=DECISION_REMAIN_UNKNOWN)
    _require_token(field="RESIDUAL_KIND_DECISION", payload=claims, expected=DECISION_REMAIN_UNKNOWN)


def adjudicate_candidate_architectures_v1() -> dict[str, Any]:
    reject_durable_unknown_as_kind_include_or_exclude_v1(claimed=DURABLE_UNKNOWN_TOKEN)
    reject_durable_unknown_as_kind_include_or_exclude_v1(claimed=DECISION_REMAIN_UNKNOWN)
    reject_kind_set_resolved_while_remaining_unknown_v1(claimed=FALSE_TOKEN)
    reject_mapping_validity_redefinition_v1(claimed=FALSE_TOKEN)
    if KIND_SET_RESOLVED is not False:
        raise KindSetAndAccountEquitySourceMappingArchitectureRatificationError(
            "KIND_SET_RESOLVED_NOT_FALSE"
        )
    if CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING is not False:
        raise KindSetAndAccountEquitySourceMappingArchitectureRatificationError(
            "MAPPING_MUST_REMAIN_NOT_CANONICALLY_VALID"
        )
    return {
        "layer": "ADJUDICATED_CONCLUSION",
        "candidate_a": CANDIDATE_A,
        "candidate_a_verdict": VERDICT_A,
        "candidate_a_basis": (
            "BE_PARTIAL_FAIL_CLOSED_ALREADY_PERSISTED_UNKNOWN_ALREADY_FIRST_CLASS_"
            "UPLIFT_TO_CANONICAL_VALIDITY_WOULD_REQUIRE_KIND_SET_RESOLVED_WHILE_"
            "NAMED_REMAINING_UNKNOWNS_REMAIN_FORBIDDEN"
        ),
        "candidate_b": CANDIDATE_B,
        "candidate_b_verdict": VERDICT_B,
        "candidate_b_basis": (
            f"AU_COMPLETE_REQUIRES={COMPLETE_REQUIRES};"
            "CONDITION_UNSATISFIED_KIND_SET_RESOLVED_FALSE_AND_UNKNOWN_NECESSARY_"
            "CLASS_REMAINS"
        ),
        "candidate_c": CANDIDATE_C,
        "candidate_c_verdict": VERDICT_C,
        "candidate_c_basis": (
            "BE_KNOWN_NON_SOURCE_AND_OTHER_DOMAIN_FIELD_MAPPINGS_PLUS_CE_CG_CI_"
            "DURABLE_UNKNOWN_IDENTITIES_PLUS_UNRESOLVED_ALGEBRA_AND_29P_SEMANTIC_"
            "NO_VALIDITY_CLAIM"
        ),
        "candidate_d": CANDIDATE_D,
        "candidate_d_verdict": VERDICT_D,
        "candidate_d_basis": (
            "CANONICAL_VALIDITY_REQUIRES_KIND_SET_CLOSURE_INCLUDE_OR_EXCLUDE_NOT_"
            "DURABLE_UNKNOWN_SUBSTITUTE_THIS_GO_FORBIDS_REDEFINING_MAPPING_VALID"
        ),
        "ratified_mapping_architecture": RATIFIED_MAPPING_ARCHITECTURE,
        "mapping_validity_redefined": FALSE_TOKEN,
        "kind_set_resolved": FALSE_TOKEN,
        "canonically_valid_account_equity_source_mapping": FALSE_TOKEN,
    }


def build_known_vs_unknown_mapping_states_v1() -> dict[str, Any]:
    return {
        "layer": "CANONICAL_AUTHORITY",
        "known_included_equity_stock_source_kinds": KNOWN_INCLUDED_SOURCE_KINDS,
        "known_included_state": STATE_KNOWN_INCLUDED,
        "known_included_count": "0",
        "known_excluded_as_kind_decision_u05_u06_residual": "NO_EXCLUDE_DECISION",
        "known_excluded_state_for_named_remaining_unknowns": "KIND_EXCLUDE_FORBIDDEN_WHILE_REMAIN_UNKNOWN",
        "known_non_source_or_other_domain_field_mappings": "CONSUMED_FROM_BE_PARTIAL_FAIL_CLOSED",
        "known_non_source_field_mapping_is_not_kind_exclude": TRUE_TOKEN,
        "durable_unknown_dimensions": DURABLE_UNKNOWN_DIMENSIONS,
        "durable_unknown_state": STATE_DURABLE_UNKNOWN,
        "unresolved_dimensions": UNRESOLVED_DIMENSIONS,
        "unresolved_state": STATE_UNRESOLVED,
        "u05_kind_decision": DECISION_REMAIN_UNKNOWN,
        "u06_kind_decision": DECISION_REMAIN_UNKNOWN,
        "residual_kind_decision": DECISION_REMAIN_UNKNOWN,
        "u05_embedding_identity": DURABLE_UNKNOWN_TOKEN,
        "u06_placement_identity": DURABLE_UNKNOWN_TOKEN,
        "residual_exhaustiveness_identity": DURABLE_UNKNOWN_TOKEN,
        "durable_unknown_is_not_include": TRUE_TOKEN,
        "durable_unknown_is_not_exclude": TRUE_TOKEN,
        "durable_unknown_is_not_absent_or_zero": TRUE_TOKEN,
        "field_mapping_coverage_status": MAPPING_COVERAGE_CONSUMED,
        "canonically_valid_account_equity_source_mapping": FALSE_TOKEN,
        "kind_set": KIND_SET_EMPTY,
        "kind_set_resolved": FALSE_TOKEN,
    }


def build_reconstruction_and_downstream_readiness_v1() -> dict[str, Any]:
    unresolved = ",".join(UNRESOLVED_ALGEBRA_TERMS)
    return {
        "layer": "ADJUDICATED_CONCLUSION",
        "reconstruction_algebra_complete": FALSE_TOKEN,
        "reconstruction_implemented": FALSE_TOKEN,
        "reconstruction_status": "INCOMPLETE_U04_U05_U06_UNRESOLVED_RESIDUAL_NOT_AN_ALGEBRA_TERM",
        "earliest_unresolved_algebra_term": EARLIEST_UNRESOLVED_ALGEBRA_TERM,
        "unresolved_algebra_terms": unresolved,
        "u04_algebra_state": STATE_UNRESOLVED,
        "u05_algebra_state": STATE_UNRESOLVED,
        "u06_algebra_state": STATE_UNRESOLVED,
        "u05_kind_identity": DURABLE_UNKNOWN_TOKEN,
        "u06_kind_identity": DURABLE_UNKNOWN_TOKEN,
        "residual_is_not_an_algebra_term": TRUE_TOKEN,
        "durable_unknown_does_not_complete_algebra": TRUE_TOKEN,
        "u04_not_pinned_durable_unknown": TRUE_TOKEN,
        "equity_stock_readiness": "NOT_READY_KIND_SET_UNRESOLVED_AND_MAPPING_NOT_CANONICALLY_VALID",
        "risk_sizing_readiness": (
            "NOT_READY_NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING_AND_"
            "29P_SEMANTIC_MAPPING_UNPROVEN"
        ),
        "d7_authorized": FALSE_TOKEN,
        "ms2_authorized": FALSE_TOKEN,
        "local_reconstruction_advancement_possible": FALSE_TOKEN,
        "local_equity_stock_advancement_possible": FALSE_TOKEN,
        "local_risk_sizing_advancement_possible": FALSE_TOKEN,
    }


def build_downstream_dependency_tree_v1() -> dict[str, Any]:
    records = (
        {
            "node_id": "CANDIDATE_ARCHITECTURE_ADJUDICATION",
            "classification": "CLOSED_THIS_SLICE",
            "status": RATIFIED_MAPPING_ARCHITECTURE,
            "reason": "FOUR_CANDIDATES_TESTED_VALIDITY_NOT_UPLIFTED",
        },
        {
            "node_id": "D6_KIND_SET",
            "classification": "REMAINS_EMPTY_FAIL_CLOSED",
            "status": KIND_SET_EMPTY,
            "reason": (
                "KIND_SET_CANNOT_RESOLVE_WHILE_U05_U06_RESIDUAL_REMAIN_UNKNOWN_"
                "DURABLE_UNKNOWN_IS_NOT_INCLUDE_OR_EXCLUDE"
            ),
        },
        {
            "node_id": "ACCOUNT_EQUITY_SOURCE_MAPPING",
            "classification": "FIRST_DEFINITIVE_BLOCK",
            "status": "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING",
            "reason": ARCHITECTURE_BLOCKER,
        },
        {
            "node_id": "RECONSTRUCTION_ALGEBRA",
            "classification": "BLOCKED_BY_UNRESOLVED_TERMS",
            "status": "INCOMPLETE",
            "reason": (
                "EXISTING_UNRESOLVED_TERMS_U04_U05_U06_RESIDUAL_IS_NOT_AN_ALGEBRA_TERM_"
                "DURABLE_UNKNOWN_DOES_NOT_COMPLETE_ALGEBRA"
            ),
        },
        {
            "node_id": "EQUITY_STOCK_READINESS",
            "classification": "BLOCKED_BY_KIND_SET_AND_MAPPING",
            "status": "NOT_READY",
            "reason": "KIND_SET_UNRESOLVED_AND_MAPPING_NOT_CANONICALLY_VALID",
        },
        {
            "node_id": "RISK_SIZING_READINESS",
            "classification": "BLOCKED_BY_MAPPING",
            "status": "NOT_READY",
            "reason": "29P_SEMANTIC_MAPPING_UNPROVEN_AND_NO_CANONICALLY_VALID_EQUITY_MAPPING",
        },
        {
            "node_id": "MS2",
            "classification": "BLOCKED_BY_KIND_SET",
            "status": "NOT_AUTHORIZED",
            "reason": "MS1_KIND_SET_NOT_FULLY_CLOSED",
        },
        {
            "node_id": "D7",
            "classification": "BLOCKED_BY_D6",
            "status": "NOT_AUTHORIZED",
            "reason": "D6_NOT_FULLY_CLOSED",
        },
        {
            "node_id": "VENUE_GET",
            "classification": "FORBIDDEN_THIS_GO",
            "status": "NOT_AUTHORIZED",
            "reason": "THIS_GO_DOES_NOT_COVER_READ_ONLY_ACQUISITION",
        },
    )
    return {
        "layer": "ADJUDICATED_CONCLUSION",
        "ratified_mapping_architecture": RATIFIED_MAPPING_ARCHITECTURE,
        "next_productive_node": NEXT_PRODUCTIVE_NODE,
        "next_productive_classification": "REQUIRES_NEW_AUTHORITY_OR_NEW_EVIDENCE",
        "first_definitive_block": DAG_PIN,
        "exact_missing_predicate": EXACT_MISSING_PREDICATE,
        "local_advancement_exhausted": TRUE_TOKEN,
        "standing_full_core_dag_pin": DAG_PIN,
        "records": list(records),
    }


def execute_kind_set_and_account_equity_source_mapping_architecture_ratification_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    evidence_root: Path | str,
    repo_root: Path | str | None = None,
    sealed_ci_pack: Path | str | None = None,
    sealed_be_pack: Path | str | None = None,
    persist_as_of: str | None = None,
) -> KindSetAndAccountEquitySourceMappingArchitectureRatificationResultV1:
    if owner_go != OWNER_GO:
        raise KindSetAndAccountEquitySourceMappingArchitectureRatificationError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise KindSetAndAccountEquitySourceMappingArchitectureRatificationError(
            "ORIGIN_MAIN_SHA_MISMATCH"
        )
    _assert_standing_pins()
    reject_hope_get_v1(authorized_get_count="0", actual_get_count="0")
    reject_durable_unknown_as_kind_include_or_exclude_v1(claimed=DURABLE_UNKNOWN_TOKEN)
    reject_durable_unknown_as_kind_include_or_exclude_v1(claimed=DECISION_REMAIN_UNKNOWN)
    reject_kind_set_resolved_while_remaining_unknown_v1(claimed=FALSE_TOKEN)
    reject_mapping_validity_redefinition_v1(claimed=FALSE_TOKEN)
    repo = Path(repo_root) if repo_root is not None else _REPO_ROOT
    ci_pack = (
        Path(sealed_ci_pack) if sealed_ci_pack is not None else repo / CANONICAL_CI_PACK_RELPATH
    )
    be_pack = (
        Path(sealed_be_pack) if sealed_be_pack is not None else repo / CANONICAL_BE_PACK_RELPATH
    )
    _assert_parent_ci_pack(sealed_ci_pack=ci_pack)
    _assert_sealed_be_mapping_pack(sealed_be_pack=be_pack)
    as_of = persist_as_of or CANONICAL_PERSIST_AS_OF
    if as_of is None or not isinstance(as_of, str) or as_of.strip() == "" or as_of != as_of.strip():
        raise KindSetAndAccountEquitySourceMappingArchitectureRatificationError(
            "FIELD_MISSING:persist_as_of"
        )
    store = Path(evidence_root)
    store.mkdir(parents=True, exist_ok=True)
    candidates = adjudicate_candidate_architectures_v1()
    states = build_known_vs_unknown_mapping_states_v1()
    reconstruction = build_reconstruction_and_downstream_readiness_v1()
    tree = build_downstream_dependency_tree_v1()
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
        "PARENT_CI_PACK": CANONICAL_CI_PACK_RELPATH,
        "PARENT_BE_MAPPING_PACK": CANONICAL_BE_PACK_RELPATH,
        "WORKPACKAGE": SCHEMA_CLASS,
        "START_BLOCK": DAG_PIN,
        "RATIFIED_MAPPING_ARCHITECTURE": RATIFIED_MAPPING_ARCHITECTURE,
        "RATIFICATION_BASIS": (
            "CANDIDATE_C_ARCHITECTURE_PLUS_CANDIDATE_B_VALIDITY_RULE_PLUS_"
            "CANDIDATE_D_CURRENT_VALIDITY_IMPOSSIBLE_CANDIDATE_A_REJECTED_AS_UPLIFT"
        ),
        "CANDIDATE_A": CANDIDATE_A,
        "CANDIDATE_A_VERDICT": VERDICT_A,
        "CANDIDATE_B": CANDIDATE_B,
        "CANDIDATE_B_VERDICT": VERDICT_B,
        "CANDIDATE_C": CANDIDATE_C,
        "CANDIDATE_C_VERDICT": VERDICT_C,
        "CANDIDATE_D": CANDIDATE_D,
        "CANDIDATE_D_VERDICT": VERDICT_D,
        "COMPLETE_REQUIRES": COMPLETE_REQUIRES,
        "MAPPING_VALIDITY_REDEFINED": FALSE_TOKEN,
        "KIND_SET": KIND_SET_EMPTY,
        "KIND_SET_RESOLVED": FALSE_TOKEN,
        "KIND_SET_CLOSEOUT_STATUS": KIND_SET_CLOSEOUT_STATUS,
        "KIND_SET_EVIDENCE_PERSIST_STATUS": KIND_SET_EVIDENCE_PERSIST_STATUS,
        "KIND_SET_STATUS": KIND_SET_EMPTY,
        "ACCOUNT_EQUITY_SOURCE_MAPPING": DAG_PIN,
        "ACCOUNT_EQUITY_SOURCE_MAPPING_STATUS": DAG_PIN,
        "CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING": FALSE_TOKEN,
        "MAPPING_PROVEN": FALSE_TOKEN,
        "SEMANTIC_MAPPING_PROVEN": FALSE_TOKEN,
        "FIELD_MAPPING_COVERAGE_STATUS": MAPPING_COVERAGE_CONSUMED,
        "KNOWN_INCLUDED_EQUITY_STOCK_SOURCE_KINDS": KNOWN_INCLUDED_SOURCE_KINDS,
        "KNOWN_EXCLUDED_KIND_DECISION_U05_U06_RESIDUAL": "NO_EXCLUDE_DECISION",
        "KNOWN_NON_SOURCE_FIELD_MAPPING_IS_NOT_KIND_EXCLUDE": TRUE_TOKEN,
        "DURABLE_UNKNOWN_DIMENSIONS": DURABLE_UNKNOWN_DIMENSIONS,
        "UNRESOLVED_DIMENSIONS": UNRESOLVED_DIMENSIONS,
        "U05_EVIDENCE_CLASS": CLASS_U05,
        "U06_EVIDENCE_CLASS": CLASS_U06,
        "RESIDUAL_EVIDENCE_CLASS": CLASS_RESIDUAL,
        "TARGET_U05": TARGET_U05,
        "TARGET_U06": TARGET_U06,
        "TARGET_RESIDUAL": TARGET_RESIDUAL,
        "U05_STATUS": DECISION_REMAIN_UNKNOWN,
        "U06_STATUS": DECISION_REMAIN_UNKNOWN,
        "RESIDUAL_STATUS": DECISION_REMAIN_UNKNOWN,
        "U05_KIND_DECISION": DECISION_REMAIN_UNKNOWN,
        "U06_KIND_DECISION": DECISION_REMAIN_UNKNOWN,
        "RESIDUAL_KIND_DECISION": DECISION_REMAIN_UNKNOWN,
        "U05_EMBEDDING_IDENTITY": DURABLE_UNKNOWN_TOKEN,
        "U06_PLACEMENT_IDENTITY": DURABLE_UNKNOWN_TOKEN,
        "RESIDUAL_EXHAUSTIVENESS_IDENTITY": DURABLE_UNKNOWN_TOKEN,
        "DURABLE_UNKNOWN_NOT_INCLUDE": TRUE_TOKEN,
        "DURABLE_UNKNOWN_NOT_EXCLUDE": TRUE_TOKEN,
        "DURABLE_UNKNOWN_NOT_ABSENT_OR_ZERO": TRUE_TOKEN,
        "U04_STATUS": STATE_UNRESOLVED,
        "U04_NOT_PINNED_DURABLE_UNKNOWN": TRUE_TOKEN,
        "RECONSTRUCTION_ALGEBRA_COMPLETE": FALSE_TOKEN,
        "RECONSTRUCTION_STATUS": reconstruction["reconstruction_status"],
        "EQUITY_STOCK_READINESS": reconstruction["equity_stock_readiness"],
        "RISK_SIZING_READINESS": reconstruction["risk_sizing_readiness"],
        "U05_ECONOMIC_VALUE_SYNTHESIZED": FALSE_TOKEN,
        "U06_ECONOMIC_VALUE_SYNTHESIZED": FALSE_TOKEN,
        "SOURCE_MAPPING_SYNTHESIZED": FALSE_TOKEN,
        "NO_GET_REQUIRED": TRUE_TOKEN,
        "NO_EQ_SOURCE_AUTHORITY": TRUE_TOKEN,
        "NO_ALGEBRAIC_UPLIFT": TRUE_TOKEN,
        "NO_HOPE_GET": TRUE_TOKEN,
        "NO_RETROACTIVE_SEALED_EVIDENCE_UPLIFT": TRUE_TOKEN,
        "MAX_GET_COUNT": "0",
        "AUTHORIZED_GET_COUNT": "0",
        "ACTUAL_GET_COUNT": "0",
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
        "parent_ci_pack": CANONICAL_CI_PACK_RELPATH,
        "parent_be_mapping_pack": CANONICAL_BE_PACK_RELPATH,
        "reconstruction_source_authority": FALSE_TOKEN,
        "hope_get_used": FALSE_TOKEN,
        "eq_source_authority_used": FALSE_TOKEN,
        "algebraic_uplift_used": FALSE_TOKEN,
        "mapping_validity_redefined": FALSE_TOKEN,
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
        "u05_unchanged": TRUE_TOKEN,
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
    architecture = {
        "layer": "CANONICAL_AUTHORITY",
        "blocker_id": BLOCKER_ID,
        "architecture_blocker": ARCHITECTURE_BLOCKER,
        "parent_blocker_id": PARENT_BLOCKER_ID,
        "ratified_mapping_architecture": RATIFIED_MAPPING_ARCHITECTURE,
        "complete_requires": COMPLETE_REQUIRES,
        "mapping_validity_redefined": FALSE_TOKEN,
        "kind_set_resolved": FALSE_TOKEN,
        "canonically_valid_account_equity_source_mapping": FALSE_TOKEN,
        "hope_get_forbidden": TRUE_TOKEN,
        "venue_eq_source_authority": FALSE_TOKEN,
        "durable_unknown_is_not_include": TRUE_TOKEN,
        "durable_unknown_is_not_exclude": TRUE_TOKEN,
        "first_definitive_block": DAG_PIN,
        "exact_missing_predicate": EXACT_MISSING_PREDICATE,
        "next_productive_node": NEXT_PRODUCTIVE_NODE,
        "next_owner_go_required": NEXT_OWNER_GO,
        "next_action": NEXT_ACTION,
    }
    layers = {
        "CANONICAL_AUTHORITY": (
            "architecture_blocker_v1.json,known_vs_unknown_mapping_states_v1.json"
        ),
        "FORENSIC_RAW_EVIDENCE": "CONSUMED_PARENT_CI_AND_BE_PACKS_RE_READ_ONLY",
        "ADJUDICATED_CONCLUSION": (
            "candidate_architecture_adjudication_v1.json,"
            "downstream_dependency_tree_v1.json,"
            "reconstruction_and_downstream_readiness_v1.json"
        ),
        "HISTORICAL": "LINEAGE.json",
        "NAVIGATION": "FORBIDDEN_AS_AUTHORITY",
        "INTERPRETATION": "FORBIDDEN",
        "HYPOTHESIS": "FORBIDDEN",
        "UNRESOLVED_OR_CONTRADICTORY": BLOCKER_ID,
    }
    _persist_json(path=store / CLAIMS_FILE, payload=claims)
    _persist_json(path=store / "candidate_architecture_adjudication_v1.json", payload=candidates)
    _persist_json(path=store / "known_vs_unknown_mapping_states_v1.json", payload=states)
    _persist_json(
        path=store / "reconstruction_and_downstream_readiness_v1.json",
        payload=reconstruction,
    )
    _persist_json(path=store / "downstream_dependency_tree_v1.json", payload=tree)
    _persist_json(path=store / "architecture_blocker_v1.json", payload=architecture)
    _persist_json(path=store / "protected_surfaces_v1.json", payload=protected)
    _persist_json(path=store / "layers_v1.json", payload=layers)
    _persist_json(path=store / "LINEAGE.json", payload=lineage)
    persist_manifest_sha256_v1(store_root=store)
    joined = "\n".join(path.read_text(encoding="utf-8") for path in store.glob("*.json"))
    lowered = joined.lower()
    if any(marker in lowered for marker in SECRET_MARKERS):
        raise KindSetAndAccountEquitySourceMappingArchitectureRatificationError(
            "SECRET_MARKER_PERSISTED"
        )
    if verify_manifest_sha256_v1(store_root=store) != 0:
        raise KindSetAndAccountEquitySourceMappingArchitectureRatificationError(
            "MANIFEST_VERIFY_NOT_ZERO"
        )
    return KindSetAndAccountEquitySourceMappingArchitectureRatificationResultV1(
        genesis_id=EXPECTED_GENESIS_ID,
        persist_as_of=as_of,
        store_root=str(store),
        ratified_mapping_architecture=RATIFIED_MAPPING_ARCHITECTURE,
        kind_set=KIND_SET_EMPTY,
        kind_set_resolved=FALSE_TOKEN,
        canonically_valid_account_equity_source_mapping=FALSE_TOKEN,
        first_definitive_block=DAG_PIN,
        exact_missing_predicate=EXACT_MISSING_PREDICATE,
        reconstruction_status=reconstruction["reconstruction_status"],
        equity_stock_readiness=reconstruction["equity_stock_readiness"],
        risk_sizing_readiness=reconstruction["risk_sizing_readiness"],
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
    "COMPLETE_REQUIRES",
    "EXACT_MISSING_PREDICATE",
    "EXPECTED_ORIGIN_MAIN_SHA",
    "NEXT_ACTION",
    "NEXT_OWNER_GO",
    "NEXT_PRODUCTIVE_NODE",
    "OWNER_GO",
    "PARENT_BLOCKER_ID",
    "PIN_OWNER_GO",
    "RATIFIED_MAPPING_ARCHITECTURE",
    "VERDICT_A",
    "VERDICT_B",
    "VERDICT_C",
    "VERDICT_D",
    "KindSetAndAccountEquitySourceMappingArchitectureRatificationError",
    "adjudicate_candidate_architectures_v1",
    "execute_kind_set_and_account_equity_source_mapping_architecture_ratification_v1",
    "reject_durable_unknown_as_kind_include_or_exclude_v1",
    "reject_kind_set_resolved_while_remaining_unknown_v1",
    "reject_mapping_validity_redefinition_v1",
)
