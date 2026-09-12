"""Typed P01 numeric value provenance adjudication.

Encodes the forensic result that canonical evidence does not prove a
numeric producer, source object, source field, transformation chain, or
fallback for P01. Unspecified provenance is not numeric authorization.
Schema presence is not a P01 value. This slice does not invent a number,
elevate venue fields, or complete reconstruction algebra.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Mapping

from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    P01_APPLICABILITY_CONTRACT_AUTHORITY_EFFECT,
    P01_APPLICABILITY_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_APPLICABILITY_CONTRACT_SCHEMA_PRESENT,
    P01_APPLICABILITY_RESOLVED,
    P01_EMBEDDED_STATE_RESOLVED,
    P01_EMBEDDING_STATE_CONTRACT_AUTHORITY_EFFECT,
    P01_EMBEDDING_STATE_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_EMBEDDING_STATE_CONTRACT_SCHEMA_PRESENT,
    P01_EQUITY_BASE_INCLUSION_CONTRACT_AUTHORITY_EFFECT,
    P01_EQUITY_BASE_INCLUSION_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_EQUITY_BASE_INCLUSION_CONTRACT_SCHEMA_PRESENT,
    P01_EQUITY_BASE_INCLUSION_RESOLVED,
    P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED,
    P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_AUTHORITY_EFFECT,
    P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_SCHEMA_PRESENT,
    P01_NUMERIC_VALUE_PROVENANCE_REQUIRED_FIELDS,
    P01_NUMERIC_VALUE_PROVENANCE_RESOLVED,
    P01_OVERLAP_WITH_U04_U05_CONTRACT_AUTHORITY_EFFECT,
    P01_OVERLAP_WITH_U04_U05_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_OVERLAP_WITH_U04_U05_CONTRACT_SCHEMA_PRESENT,
    P01_TERM_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_TERM_CONTRACT_SCHEMA_PRESENT,
    P01_TERM_SEMANTICS_RESOLVED,
    P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_SCHEMA_PRESENT,
    P01_U04_OVERLAP_RESOLVED,
    P01_U05_OVERLAP_RESOLVED,
    P01_VALUE_UNIT_CLASS_RESOLVED,
    RECONSTRUCTION_ALGEBRA_COMPLETE,
    SOURCE_OBJECT_PRESENT,
    SOURCE_SELECTED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_applicability_contract_v1 import (
    SCHEMA_CLASS as P01_APPLICABILITY_SCHEMA_CLASS,
    build_p01_applicability_contract_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_embedding_state_contract_v1 import (
    SCHEMA_CLASS as P01_EMBEDDING_STATE_SCHEMA_CLASS,
    build_p01_embedding_state_contract_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_equity_base_inclusion_contract_v1 import (
    SCHEMA_CLASS as P01_EQUITY_BASE_INCLUSION_SCHEMA_CLASS,
    build_p01_equity_base_inclusion_contract_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_haircut_reserve_depletion_term_contract_v1 import (
    NUMERIC_STATE as PARENT_NUMERIC_STATE,
    ORIGIN_CLASS as PARENT_ORIGIN_CLASS,
    SCHEMA_CLASS as P01_TERM_SCHEMA_CLASS,
    build_p01_haircut_reserve_depletion_term_contract_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_overlap_with_u04_u05_contract_v1 import (
    P01_U04_OVERLAP_STATE,
    P01_U05_OVERLAP_STATE,
    REMAINING_UNRESOLVED_SEMANTICS as PARENT_REMAINING_UNRESOLVED_SEMANTICS,
    SCHEMA_CLASS as P01_OVERLAP_SCHEMA_CLASS,
    build_p01_overlap_with_u04_u05_contract_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_term_set_and_unit_class_contract_v1 import (
    SCHEMA_CLASS as P01_TERM_SET_SCHEMA_CLASS,
    build_p01_term_set_and_unit_class_contract_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.reconstruction_algebra_contract_v1 import (
    CONTRADICTION_NONE,
    DIMENSION_ID,
    EARLIEST_UNRESOLVED_ALGEBRA_TERM,
    NUMERIC_NOT_COMPUTED,
    NUMERIC_PRESENT_ZERO,
    TERM_P01_HAIRCUT_RESERVE_DEPLETION,
    UNRESOLVED_ALGEBRA_TERMS,
    build_reconstruction_algebra_contract_v1,
)

SCHEMA_CLASS = "P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_V1"
CONTRACT_VERSION = "v1"
POLICY_ID = "P01"
TERM_ID = TERM_P01_HAIRCUT_RESERVE_DEPLETION
PARENT_OVERLAP_CONTRACT_SCHEMA_CLASS = P01_OVERLAP_SCHEMA_CLASS
PARENT_EMBEDDING_CONTRACT_SCHEMA_CLASS = P01_EMBEDDING_STATE_SCHEMA_CLASS
PARENT_INCLUSION_CONTRACT_SCHEMA_CLASS = P01_EQUITY_BASE_INCLUSION_SCHEMA_CLASS
PARENT_APPLICABILITY_CONTRACT_SCHEMA_CLASS = P01_APPLICABILITY_SCHEMA_CLASS
PARENT_TERM_SET_CONTRACT_SCHEMA_CLASS = P01_TERM_SET_SCHEMA_CLASS
PARENT_TERM_CONTRACT_SCHEMA_CLASS = P01_TERM_SCHEMA_CLASS
P01_NUMERIC_VALUE_PROVENANCE_RESOLVED_STATUS = "false"
P01_NUMERIC_VALUE_PROVENANCE_STATUS = "UNSPECIFIED"
P01_NUMERIC_VALUE_SOURCE = "UNSPECIFIED"
P01_NUMERIC_VALUE_TRANSFORMATION = "UNSPECIFIED"
TYPED_PROVENANCE_CLASS_UNKNOWN = "UNKNOWN"
TYPED_PROVENANCE_CLASS_VENUE_NATIVE = "VENUE_NATIVE"
TYPED_PROVENANCE_CLASS_INTERNALLY_RECONSTRUCTED = "INTERNALLY_RECONSTRUCTED"
TYPED_PROVENANCE_CLASS_POLICY_DERIVED = "POLICY_DERIVED"
TYPED_PROVENANCE_CLASS_CONFIGURATION_DERIVED = "CONFIGURATION_DERIVED"
TYPED_PROVENANCE_CLASS_RISK_MODEL_DERIVED = "RISK_MODEL_DERIVED"
TYPED_PROVENANCE_CLASS_LEDGER_DERIVED = "LEDGER_DERIVED"
TYPED_PROVENANCE_CLASS_ACCOUNTING_DERIVED = "ACCOUNTING_DERIVED"
TYPED_PROVENANCE_CLASS_COMPOSITE = "COMPOSITE"
TYPED_PROVENANCE_CLASS = TYPED_PROVENANCE_CLASS_UNKNOWN
PRODUCER_STATE = "NO_PRODUCTIVE_PRODUCER"
SOURCE_OBJECT_ID = "UNSPECIFIED"
SOURCE_FIELD_ID = "UNSPECIFIED"
SOURCE_CONTRACT_ID = "UNSPECIFIED"
TRANSFORMATION_CHAIN_STATE = "UNSPECIFIED"
TIME_SEMANTICS_STATE = "P01_MEMBER_FRESHNESS_INHERITANCE_UNPROVEN"
UNIT_DIMENSION_TRANSFORM_STATE = "UNSPECIFIED"
MISSING_VALUE_TREATMENT = "FAIL_CLOSED_UNSPECIFIED"
STALE_VALUE_TREATMENT = "FAIL_CLOSED_UNSPECIFIED"
UNAVAILABLE_VALUE_TREATMENT = "FAIL_CLOSED_UNSPECIFIED"
CONTRADICTORY_VALUE_TREATMENT = "FAIL_CLOSED_UNSPECIFIED"
PARTIAL_EVIDENCE_TREATMENT = "FAIL_CLOSED_UNSPECIFIED"
MULTIPLE_CANDIDATE_TREATMENT = "NO_WINNER_RATIFIED_FAIL_CLOSED"
FALLBACK_SOURCE_STATE = "FORBIDDEN"
NUMERIC_COMPUTATION_RULE_STATE = "SEMANTIC_SLOT_ONLY"
HAIRCUT_RESERVE_DEPLETION_CONSTRUCTION_STATE = "NOT_ANTICIPATED_UNSPECIFIED_FAIL_CLOSED"
UNKNOWN_IS_NOT_NUMERIC_AUTHORIZATION = "true"
UNSPECIFIED_IS_NOT_NUMERIC_AUTHORIZATION = "true"
MISSING_INPUT_FAIL_CLOSED = "true"
MALFORMED_INPUT_FAIL_CLOSED = "true"
ZERO_IS_NOT_P01_VALUE = "true"
ABSENCE_IS_NOT_P01_VALUE = "true"
VENUE_FIELD_IS_NOT_P01_VALUE = "true"
NAME_SIMILARITY_DOES_NOT_PROVE_SOURCE = "true"
NUMERIC_EQUALITY_DOES_NOT_PROVE_SOURCE = "true"
POLICY_SLOT_IS_NOT_NUMERIC_SOURCE = "true"
ALGEBRA_SLOT_IS_NOT_NUMERIC_SOURCE = "true"
UNSPECIFIED_HAIRCUT_CANNOT_CONSTRUCT_P01 = "true"
UNSPECIFIED_CANNOT_AUTHORIZE_SUBTRACTION = "true"
UNSPECIFIED_CANNOT_AUTHORIZE_ADDITION = "true"
UNSPECIFIED_CANNOT_AUTHORIZE_NETTING = "true"
UNSPECIFIED_CANNOT_AUTHORIZE_OMISSION = "true"
UNSPECIFIED_CANNOT_AUTHORIZE_IGNORE = "true"
AUTHORITY_EFFECT_NONE = "NONE"
TERM_SEMANTICS_RESOLVED_STATUS = "false"
UNSPECIFIED_CLOSED_STATUS = "false"
REMAINING_UNRESOLVED_SEMANTICS = PARENT_REMAINING_UNRESOLVED_SEMANTICS
REJECTED_PROVENANCE_INFERENCES = (
    "VENUE_NATIVE_UNPROVEN;"
    "INTERNALLY_RECONSTRUCTED_UNPROVEN;"
    "POLICY_DERIVED_NUMERIC_UNPROVEN;"
    "CONFIGURATION_DERIVED_UNPROVEN;"
    "RISK_MODEL_DERIVED_UNPROVEN;"
    "LEDGER_DERIVED_UNPROVEN;"
    "ACCOUNTING_DERIVED_UNPROVEN;"
    "COMPOSITE_UNPROVEN;"
    "AVAILEQ_IS_NOT_P01;"
    "TOTALEQ_IS_NOT_P01;"
    "EQ_IS_NOT_P01;"
    "ADJEQ_IS_NOT_P01;"
    "AVAILBAL_IS_NOT_P01;"
    "CASHBAL_IS_NOT_P01;"
    "FROZENBAL_IS_NOT_P01;"
    "ISOEQ_IS_NOT_P01;"
    "ORDFROZEN_IS_NOT_P01;"
    "UPL_IS_NOT_P01;"
    "C01_C21_NOT_ELEVATED;"
    "NAME_SIMILARITY_IS_NOT_SOURCE;"
    "NUMERIC_EQUALITY_IS_NOT_SOURCE;"
    "SHARED_EPOCH_IS_NOT_SOURCE;"
    "SHARED_UNIT_IS_NOT_SOURCE;"
    "P01_STATUS_DECIDED_IS_NOT_NUMERIC_SOURCE;"
    "POLICY_OPERATOR_FAMILY_IS_NOT_NUMERIC_PRODUCER;"
    "ALGEBRA_SLOT_IS_NOT_NUMERIC_PRODUCER;"
    "NUMERIC_NOT_COMPUTED_IS_NOT_ZERO;"
    "MISSING_IS_NOT_ZERO;"
    "ABSENCE_IS_NOT_P01_VALUE;"
    "FALLBACK_SOURCE_FORBIDDEN;"
    "UNSPECIFIED_HAIRCUT_CANNOT_CONSTRUCT_P01;"
    "UNSPECIFIED_PROVENANCE_CANNOT_AUTHORIZE_ADD_SUBTRACT_NET_OMIT_IGNORE"
)
EVIDENCE_CLASSIFICATION = (
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_AG_P01_NUMERIC_VALUE_PROVENANCE_UNSPECIFIED;"
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_T_P01_REDUCTION_ONLY_UNSPECIFIED;"
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_S_NO_CANONICALLY_VALID_MAPPING;"
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_T_AVAILEQ_IS_NOT_29P_EQUITY_AUTHORITY;"
    "FORENSIC_EVIDENCE=SOURCE_SELECTED_FALSE_SOURCE_OBJECT_ABSENT_PRODUCER_ABSENT;"
    "FORENSIC_EVIDENCE=NUMERIC_NOT_COMPUTED_SEMANTIC_SLOT_ONLY;"
    "FORENSIC_EVIDENCE=P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CANNOT_CONSTRUCT_VALUE;"
    "HISTORICAL_STATE=C01_C21_REJECTED_NOT_ELEVATED;"
    "STRUCTURAL_REUSE_ONLY=P01_OVERLAP_WITH_U04_U05_CONTRACT_V1;"
    "NAVIGATION=MAP_OF_TRUTH_NON_SSOT;"
    "INTERPRETATION=NONE;"
    "HYPOTHESIS=NONE;"
    "REJECTED=AVAILEQ_TOTALEQ_EQ_ADJEQ_AVAILBAL_CASHBAL_FROZENBAL_ISOEQ_ORDFROZEN_UPL_C01_C21;"
    "UNSPECIFIED=P01_NUMERIC_VALUE_PROVENANCE;"
    "UNRESOLVED=NO_CANONICAL_SOURCE_DEFINED;"
    "CONTRADICTORY=NONE"
)
CANDIDATE_SOURCES_CLASSIFICATION = (
    "CANDIDATE=details.availEq|CLASS=REJECTED|REASON=AVAILABLE_MARGIN_NOT_P01;"
    "CANDIDATE=availEq|CLASS=REJECTED|REASON=AVAILEQ_IS_NOT_29P_EQUITY_AUTHORITY;"
    "CANDIDATE=totalEq|CLASS=REJECTED|REASON=VENUE_RAW_NOT_P01;"
    "CANDIDATE=eq|CLASS=REJECTED|REASON=VENUE_RAW_NOT_P01;"
    "CANDIDATE=adjEq|CLASS=REJECTED|REASON=VENUE_RAW_NOT_P01;"
    "CANDIDATE=availBal|CLASS=REJECTED|REASON=VENUE_RAW_NOT_P01;"
    "CANDIDATE=cashBal|CLASS=REJECTED|REASON=VENUE_RAW_NOT_P01;"
    "CANDIDATE=frozenBal|CLASS=REJECTED|REASON=VENUE_RAW_NOT_P01;"
    "CANDIDATE=isoEq|CLASS=REJECTED|REASON=VENUE_RAW_NOT_P01;"
    "CANDIDATE=ordFrozen|CLASS=REJECTED|REASON=VENUE_RAW_NOT_P01;"
    "CANDIDATE=upl|CLASS=REJECTED|REASON=VENUE_RAW_NOT_P01;"
    "CANDIDATE=C01_C21|CLASS=REJECTED|REASON=NOT_ELEVATED;"
    "CANDIDATE=AccountingPortfolioStateV1|CLASS=REJECTED|REASON=NOT_ELEVATED;"
    "CANDIDATE=LedgerSnapshot.equity_by_ccy|CLASS=REJECTED|REASON=NOT_ELEVATED;"
    "CANDIDATE=SimulatedPortfolioStateV1|CLASS=REJECTED|REASON=NOT_ELEVATED;"
    "CANDIDATE=P01_STATUS_DECIDED|CLASS=CANONICAL_AUTHORITY|"
    "REASON=FAMILY_EXISTENCE_NOT_NUMERIC_SOURCE;"
    "CANDIDATE=ORIGIN_CLASS_POLICY_DEFINED_OPERATOR|CLASS=CANONICAL_AUTHORITY|"
    "REASON=OPERATOR_FAMILY_NOT_NUMERIC_PRODUCER;"
    "CANDIDATE=INTERNAL_RECONSTRUCTION|CLASS=STRUCTURAL_REUSE_ONLY|"
    "REASON=SCHEMA_ONLY_RUNTIME_ABSENT;"
    "NO_WINNER_RATIFIED=true"
)
_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")
_INFERRED_SOURCE_TOKENS: tuple[str, ...] = (
    "venuenative",
    "internallyreconstructed",
    "policyderived",
    "configurationderived",
    "riskmodelderived",
    "ledgerderived",
    "accountingderived",
    "composite",
    "detailsavaileq",
    "availeq",
    "totaleq",
    "adjeq",
    "availbal",
    "cashbal",
    "frozenbal",
    "isoeq",
    "ordfrozen",
    "eq",
    "upl",
    "c01",
    "c21",
    "accountingportfoliostatev1",
    "ledgersnapshot",
    "equitybyccy",
    "simulatedportfoliostatev1",
    "p01statusdecided",
    "policydefinedoperator",
    PARENT_ORIGIN_CLASS.lower().replace("_", ""),
    "internalreconstruction",
    "fallback",
    "resolved",
    "computed",
    "bound",
    "mapped",
)
_ZERO_OR_ABSENCE_TOKENS: tuple[str, ...] = (
    "0",
    "0.0",
    "zero",
    "presentzero",
    NUMERIC_PRESENT_ZERO.lower().replace("_", ""),
    "none",
    "null",
    "absent",
    "absence",
    "missing",
    "empty",
    "n/a",
    "na",
    "false",
)
_ARITHMETIC_ACTION_TOKENS: tuple[str, ...] = (
    "sum",
    "summation",
    "add",
    "addition",
    "combine",
    "combination",
    "deduplicate",
    "deduplication",
    "net",
    "netting",
    "subtract",
    "subtraction",
    "omit",
    "omission",
    "ignore",
    "ignored",
)
_VECTOR_FIELDS: tuple[str, ...] = tuple(
    name for name in P01_NUMERIC_VALUE_PROVENANCE_REQUIRED_FIELDS if name != "provenance_digest"
)


class P01NumericValueProvenanceContractError(ValueError):
    """Fail-closed P01 numeric value provenance contract violation."""


def _fold(value: str) -> str:
    return str(value or "").strip().lower().replace("_", "").replace("-", "").replace(".", "")


def _require_non_empty_str(*, field: str, raw: Any) -> str:
    if raw is None:
        raise P01NumericValueProvenanceContractError(f"P01_FIELD_MISSING:{field}")
    if isinstance(raw, bool) or not isinstance(raw, str):
        raise P01NumericValueProvenanceContractError(f"P01_FIELD_NOT_STRING:{field}")
    text = raw.strip()
    if text == "" or text != raw:
        raise P01NumericValueProvenanceContractError(f"P01_FIELD_MISSING:{field}")
    return text


def _sha256_hex(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _canonical_json(payload: Mapping[str, str]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_p01_numeric_value_provenance_digest_v1(canonical: Mapping[str, str]) -> str:
    payload = {
        key: canonical[key]
        for key in P01_NUMERIC_VALUE_PROVENANCE_REQUIRED_FIELDS
        if key != "provenance_digest"
    }
    return _sha256_hex(_canonical_json(payload))


def attach_p01_numeric_value_provenance_digest_v1(
    fields: Mapping[str, Any],
) -> dict[str, Any]:
    canonical: dict[str, str] = {}
    for canonical_name in P01_NUMERIC_VALUE_PROVENANCE_REQUIRED_FIELDS:
        if canonical_name == "provenance_digest":
            continue
        if canonical_name not in fields:
            raise P01NumericValueProvenanceContractError(f"P01_FIELD_MISSING:{canonical_name}")
        raw = fields[canonical_name]
        canonical[canonical_name] = "" if raw is None else str(raw)
    attached = dict(fields)
    attached["provenance_digest"] = compute_p01_numeric_value_provenance_digest_v1(canonical)
    return attached


def _reject_coerced_source(*, field: str, raw: str) -> None:
    folded = _fold(raw)
    _ = field
    if folded in _ZERO_OR_ABSENCE_TOKENS or folded in {"0", "false"}:
        raise P01NumericValueProvenanceContractError("P01_ZERO_OR_ABSENCE_VALUE_FORBIDDEN")
    if folded in _INFERRED_SOURCE_TOKENS:
        raise P01NumericValueProvenanceContractError("P01_NUMERIC_SOURCE_INFERRED_FORBIDDEN")
    if any(len(token) > 3 and token in folded for token in _INFERRED_SOURCE_TOKENS):
        raise P01NumericValueProvenanceContractError("P01_NUMERIC_SOURCE_INFERRED_FORBIDDEN")


@dataclass(frozen=True)
class P01NumericValueProvenanceContractV1:
    """Typed immutable P01 numeric provenance adjudication. Not a numeric instance."""

    p01_numeric_value_provenance_contract_id: str
    p01_numeric_value_provenance_contract_version: str
    parent_p01_overlap_with_u04_u05_contract_schema_class: str
    parent_p01_embedding_state_contract_schema_class: str
    parent_p01_equity_base_inclusion_contract_schema_class: str
    parent_p01_applicability_contract_schema_class: str
    parent_p01_term_set_and_unit_class_contract_schema_class: str
    parent_p01_term_contract_schema_class: str
    target_semantic_dimension_id: str
    policy_id: str
    term_id: str
    p01_numeric_value_provenance_resolved_status: str
    p01_numeric_value_provenance_status: str
    p01_numeric_value_source: str
    p01_numeric_value_transformation: str
    typed_provenance_class: str
    producer_state: str
    source_object_id: str
    source_field_id: str
    source_contract_id: str
    transformation_chain_state: str
    time_semantics_state: str
    unit_dimension_transform_state: str
    missing_value_treatment: str
    stale_value_treatment: str
    unavailable_value_treatment: str
    contradictory_value_treatment: str
    partial_evidence_treatment: str
    multiple_candidate_treatment: str
    fallback_source_state: str
    numeric_computation_rule_state: str
    haircut_reserve_depletion_construction_state: str
    unknown_is_not_numeric_authorization: str
    unspecified_is_not_numeric_authorization: str
    missing_input_fail_closed: str
    malformed_input_fail_closed: str
    zero_is_not_p01_value: str
    absence_is_not_p01_value: str
    venue_field_is_not_p01_value: str
    name_similarity_does_not_prove_source: str
    numeric_equality_does_not_prove_source: str
    policy_slot_is_not_numeric_source: str
    algebra_slot_is_not_numeric_source: str
    unspecified_haircut_cannot_construct_p01: str
    unspecified_cannot_authorize_subtraction: str
    unspecified_cannot_authorize_addition: str
    unspecified_cannot_authorize_netting: str
    unspecified_cannot_authorize_omission: str
    unspecified_cannot_authorize_ignore: str
    rejected_provenance_inferences: str
    remaining_unresolved_semantics: str
    evidence_classification: str
    candidate_sources_classification: str
    contradiction_state: str
    term_semantics_resolved_status: str
    unspecified_closed_status: str
    p01_numeric_value_provenance_contract_authority_effect: str
    provenance_digest: str

    def __post_init__(self) -> None:
        _validate_p01_numeric_value_provenance_contract_v1(self)

    def to_canonical_dict(self) -> dict[str, str]:
        values = {
            "p01_numeric_value_provenance_contract_id": (
                self.p01_numeric_value_provenance_contract_id
            ),
            "p01_numeric_value_provenance_contract_version": (
                self.p01_numeric_value_provenance_contract_version
            ),
            "parent_p01_overlap_with_u04_u05_contract_schema_class": (
                self.parent_p01_overlap_with_u04_u05_contract_schema_class
            ),
            "parent_p01_embedding_state_contract_schema_class": (
                self.parent_p01_embedding_state_contract_schema_class
            ),
            "parent_p01_equity_base_inclusion_contract_schema_class": (
                self.parent_p01_equity_base_inclusion_contract_schema_class
            ),
            "parent_p01_applicability_contract_schema_class": (
                self.parent_p01_applicability_contract_schema_class
            ),
            "parent_p01_term_set_and_unit_class_contract_schema_class": (
                self.parent_p01_term_set_and_unit_class_contract_schema_class
            ),
            "parent_p01_term_contract_schema_class": self.parent_p01_term_contract_schema_class,
            "target_semantic_dimension_id": self.target_semantic_dimension_id,
            "policy_id": self.policy_id,
            "term_id": self.term_id,
            "p01_numeric_value_provenance_resolved_status": (
                self.p01_numeric_value_provenance_resolved_status
            ),
            "p01_numeric_value_provenance_status": self.p01_numeric_value_provenance_status,
            "p01_numeric_value_source": self.p01_numeric_value_source,
            "p01_numeric_value_transformation": self.p01_numeric_value_transformation,
            "typed_provenance_class": self.typed_provenance_class,
            "producer_state": self.producer_state,
            "source_object_id": self.source_object_id,
            "source_field_id": self.source_field_id,
            "source_contract_id": self.source_contract_id,
            "transformation_chain_state": self.transformation_chain_state,
            "time_semantics_state": self.time_semantics_state,
            "unit_dimension_transform_state": self.unit_dimension_transform_state,
            "missing_value_treatment": self.missing_value_treatment,
            "stale_value_treatment": self.stale_value_treatment,
            "unavailable_value_treatment": self.unavailable_value_treatment,
            "contradictory_value_treatment": self.contradictory_value_treatment,
            "partial_evidence_treatment": self.partial_evidence_treatment,
            "multiple_candidate_treatment": self.multiple_candidate_treatment,
            "fallback_source_state": self.fallback_source_state,
            "numeric_computation_rule_state": self.numeric_computation_rule_state,
            "haircut_reserve_depletion_construction_state": (
                self.haircut_reserve_depletion_construction_state
            ),
            "unknown_is_not_numeric_authorization": self.unknown_is_not_numeric_authorization,
            "unspecified_is_not_numeric_authorization": (
                self.unspecified_is_not_numeric_authorization
            ),
            "missing_input_fail_closed": self.missing_input_fail_closed,
            "malformed_input_fail_closed": self.malformed_input_fail_closed,
            "zero_is_not_p01_value": self.zero_is_not_p01_value,
            "absence_is_not_p01_value": self.absence_is_not_p01_value,
            "venue_field_is_not_p01_value": self.venue_field_is_not_p01_value,
            "name_similarity_does_not_prove_source": (self.name_similarity_does_not_prove_source),
            "numeric_equality_does_not_prove_source": (self.numeric_equality_does_not_prove_source),
            "policy_slot_is_not_numeric_source": self.policy_slot_is_not_numeric_source,
            "algebra_slot_is_not_numeric_source": self.algebra_slot_is_not_numeric_source,
            "unspecified_haircut_cannot_construct_p01": (
                self.unspecified_haircut_cannot_construct_p01
            ),
            "unspecified_cannot_authorize_subtraction": (
                self.unspecified_cannot_authorize_subtraction
            ),
            "unspecified_cannot_authorize_addition": self.unspecified_cannot_authorize_addition,
            "unspecified_cannot_authorize_netting": self.unspecified_cannot_authorize_netting,
            "unspecified_cannot_authorize_omission": self.unspecified_cannot_authorize_omission,
            "unspecified_cannot_authorize_ignore": self.unspecified_cannot_authorize_ignore,
            "rejected_provenance_inferences": self.rejected_provenance_inferences,
            "remaining_unresolved_semantics": self.remaining_unresolved_semantics,
            "evidence_classification": self.evidence_classification,
            "candidate_sources_classification": self.candidate_sources_classification,
            "contradiction_state": self.contradiction_state,
            "term_semantics_resolved_status": self.term_semantics_resolved_status,
            "unspecified_closed_status": self.unspecified_closed_status,
            "p01_numeric_value_provenance_contract_authority_effect": (
                self.p01_numeric_value_provenance_contract_authority_effect
            ),
            "provenance_digest": self.provenance_digest,
        }
        return {key: values[key] for key in P01_NUMERIC_VALUE_PROVENANCE_REQUIRED_FIELDS}


def _require_true_pin(*, field: str, raw: str, expected: str, error: str) -> None:
    if raw.lower() != "true" or raw != expected:
        raise P01NumericValueProvenanceContractError(error)
    _ = field


def _validate_p01_numeric_value_provenance_contract_v1(
    contract: P01NumericValueProvenanceContractV1,
) -> None:
    if P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_SCHEMA_PRESENT is not True:
        raise P01NumericValueProvenanceContractError(
            "P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_SCHEMA_PRESENT_REQUIRED"
        )
    if P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_RUNTIME_INSTANCE_PRESENT is True:
        raise P01NumericValueProvenanceContractError("P01_RUNTIME_INSTANCE_FORBIDDEN")
    if P01_NUMERIC_VALUE_PROVENANCE_RESOLVED is True:
        raise P01NumericValueProvenanceContractError(
            "P01_NUMERIC_VALUE_PROVENANCE_RESOLVED_PIN_FORBIDDEN"
        )
    if P01_OVERLAP_WITH_U04_U05_CONTRACT_SCHEMA_PRESENT is not True:
        raise P01NumericValueProvenanceContractError(
            "P01_OVERLAP_WITH_U04_U05_CONTRACT_SCHEMA_PRESENT_REQUIRED"
        )
    if P01_OVERLAP_WITH_U04_U05_CONTRACT_RUNTIME_INSTANCE_PRESENT is True:
        raise P01NumericValueProvenanceContractError(
            "P01_PARENT_OVERLAP_RUNTIME_INSTANCE_FORBIDDEN"
        )
    if P01_U04_OVERLAP_RESOLVED is True:
        raise P01NumericValueProvenanceContractError("P01_U04_OVERLAP_RESOLVED_PIN_FORBIDDEN")
    if P01_U05_OVERLAP_RESOLVED is True:
        raise P01NumericValueProvenanceContractError("P01_U05_OVERLAP_RESOLVED_PIN_FORBIDDEN")
    if P01_EMBEDDING_STATE_CONTRACT_SCHEMA_PRESENT is not True:
        raise P01NumericValueProvenanceContractError(
            "P01_EMBEDDING_STATE_CONTRACT_SCHEMA_PRESENT_REQUIRED"
        )
    if P01_EMBEDDING_STATE_CONTRACT_RUNTIME_INSTANCE_PRESENT is True:
        raise P01NumericValueProvenanceContractError(
            "P01_PARENT_EMBEDDING_RUNTIME_INSTANCE_FORBIDDEN"
        )
    if P01_EMBEDDED_STATE_RESOLVED is True:
        raise P01NumericValueProvenanceContractError("P01_EMBEDDED_STATE_RESOLVED_PIN_FORBIDDEN")
    if P01_EQUITY_BASE_INCLUSION_CONTRACT_SCHEMA_PRESENT is not True:
        raise P01NumericValueProvenanceContractError(
            "P01_EQUITY_BASE_INCLUSION_CONTRACT_SCHEMA_PRESENT_REQUIRED"
        )
    if P01_EQUITY_BASE_INCLUSION_CONTRACT_RUNTIME_INSTANCE_PRESENT is True:
        raise P01NumericValueProvenanceContractError(
            "P01_PARENT_INCLUSION_RUNTIME_INSTANCE_FORBIDDEN"
        )
    if P01_EQUITY_BASE_INCLUSION_RESOLVED is True:
        raise P01NumericValueProvenanceContractError(
            "P01_EQUITY_BASE_INCLUSION_RESOLVED_PIN_FORBIDDEN"
        )
    if P01_APPLICABILITY_CONTRACT_SCHEMA_PRESENT is not True:
        raise P01NumericValueProvenanceContractError(
            "P01_APPLICABILITY_CONTRACT_SCHEMA_PRESENT_REQUIRED"
        )
    if P01_APPLICABILITY_CONTRACT_RUNTIME_INSTANCE_PRESENT is True:
        raise P01NumericValueProvenanceContractError(
            "P01_PARENT_APPLICABILITY_RUNTIME_INSTANCE_FORBIDDEN"
        )
    if P01_APPLICABILITY_RESOLVED is True:
        raise P01NumericValueProvenanceContractError("P01_APPLICABILITY_RESOLVED_PIN_FORBIDDEN")
    if P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_SCHEMA_PRESENT is not True:
        raise P01NumericValueProvenanceContractError(
            "P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_SCHEMA_PRESENT_REQUIRED"
        )
    if P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_RUNTIME_INSTANCE_PRESENT is True:
        raise P01NumericValueProvenanceContractError(
            "P01_PARENT_TERM_SET_RUNTIME_INSTANCE_FORBIDDEN"
        )
    if P01_TERM_CONTRACT_SCHEMA_PRESENT is not True:
        raise P01NumericValueProvenanceContractError("P01_TERM_CONTRACT_SCHEMA_PRESENT_REQUIRED")
    if P01_TERM_CONTRACT_RUNTIME_INSTANCE_PRESENT is True:
        raise P01NumericValueProvenanceContractError("P01_PARENT_RUNTIME_INSTANCE_FORBIDDEN")
    if P01_VALUE_UNIT_CLASS_RESOLVED is True:
        raise P01NumericValueProvenanceContractError("P01_VALUE_UNIT_CLASS_RESOLVED_PIN_FORBIDDEN")
    if P01_TERM_SEMANTICS_RESOLVED is True:
        raise P01NumericValueProvenanceContractError("P01_TERM_SEMANTICS_RESOLVED_PIN_FORBIDDEN")
    if P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED is True:
        raise P01NumericValueProvenanceContractError(
            "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED_PIN_FORBIDDEN"
        )
    if RECONSTRUCTION_ALGEBRA_COMPLETE is True:
        raise P01NumericValueProvenanceContractError(
            "P01_RECONSTRUCTION_ALGEBRA_COMPLETE_PIN_FORBIDDEN"
        )
    if SOURCE_SELECTED is True or SOURCE_OBJECT_PRESENT is True:
        raise P01NumericValueProvenanceContractError("P01_SOURCE_SELECTION_FORBIDDEN")
    contract_id = _require_non_empty_str(
        field="p01_numeric_value_provenance_contract_id",
        raw=contract.p01_numeric_value_provenance_contract_id,
    )
    version = _require_non_empty_str(
        field="p01_numeric_value_provenance_contract_version",
        raw=contract.p01_numeric_value_provenance_contract_version,
    )
    parent_overlap = _require_non_empty_str(
        field="parent_p01_overlap_with_u04_u05_contract_schema_class",
        raw=contract.parent_p01_overlap_with_u04_u05_contract_schema_class,
    )
    parent_embedding = _require_non_empty_str(
        field="parent_p01_embedding_state_contract_schema_class",
        raw=contract.parent_p01_embedding_state_contract_schema_class,
    )
    parent_inclusion = _require_non_empty_str(
        field="parent_p01_equity_base_inclusion_contract_schema_class",
        raw=contract.parent_p01_equity_base_inclusion_contract_schema_class,
    )
    parent_applicability = _require_non_empty_str(
        field="parent_p01_applicability_contract_schema_class",
        raw=contract.parent_p01_applicability_contract_schema_class,
    )
    parent_term_set = _require_non_empty_str(
        field="parent_p01_term_set_and_unit_class_contract_schema_class",
        raw=contract.parent_p01_term_set_and_unit_class_contract_schema_class,
    )
    parent_term = _require_non_empty_str(
        field="parent_p01_term_contract_schema_class",
        raw=contract.parent_p01_term_contract_schema_class,
    )
    target = _require_non_empty_str(
        field="target_semantic_dimension_id", raw=contract.target_semantic_dimension_id
    )
    policy_id = _require_non_empty_str(field="policy_id", raw=contract.policy_id)
    term_id = _require_non_empty_str(field="term_id", raw=contract.term_id)
    resolved = _require_non_empty_str(
        field="p01_numeric_value_provenance_resolved_status",
        raw=contract.p01_numeric_value_provenance_resolved_status,
    )
    status = _require_non_empty_str(
        field="p01_numeric_value_provenance_status",
        raw=contract.p01_numeric_value_provenance_status,
    )
    source = _require_non_empty_str(
        field="p01_numeric_value_source", raw=contract.p01_numeric_value_source
    )
    transformation = _require_non_empty_str(
        field="p01_numeric_value_transformation",
        raw=contract.p01_numeric_value_transformation,
    )
    typed_class = _require_non_empty_str(
        field="typed_provenance_class", raw=contract.typed_provenance_class
    )
    producer = _require_non_empty_str(field="producer_state", raw=contract.producer_state)
    source_object = _require_non_empty_str(field="source_object_id", raw=contract.source_object_id)
    source_field = _require_non_empty_str(field="source_field_id", raw=contract.source_field_id)
    source_contract = _require_non_empty_str(
        field="source_contract_id", raw=contract.source_contract_id
    )
    chain = _require_non_empty_str(
        field="transformation_chain_state", raw=contract.transformation_chain_state
    )
    time_state = _require_non_empty_str(
        field="time_semantics_state", raw=contract.time_semantics_state
    )
    unit_state = _require_non_empty_str(
        field="unit_dimension_transform_state",
        raw=contract.unit_dimension_transform_state,
    )
    missing_treatment = _require_non_empty_str(
        field="missing_value_treatment", raw=contract.missing_value_treatment
    )
    stale_treatment = _require_non_empty_str(
        field="stale_value_treatment", raw=contract.stale_value_treatment
    )
    unavailable_treatment = _require_non_empty_str(
        field="unavailable_value_treatment", raw=contract.unavailable_value_treatment
    )
    contradictory_treatment = _require_non_empty_str(
        field="contradictory_value_treatment",
        raw=contract.contradictory_value_treatment,
    )
    partial_treatment = _require_non_empty_str(
        field="partial_evidence_treatment", raw=contract.partial_evidence_treatment
    )
    multiple_treatment = _require_non_empty_str(
        field="multiple_candidate_treatment", raw=contract.multiple_candidate_treatment
    )
    fallback = _require_non_empty_str(
        field="fallback_source_state", raw=contract.fallback_source_state
    )
    computation = _require_non_empty_str(
        field="numeric_computation_rule_state",
        raw=contract.numeric_computation_rule_state,
    )
    haircut_construction = _require_non_empty_str(
        field="haircut_reserve_depletion_construction_state",
        raw=contract.haircut_reserve_depletion_construction_state,
    )
    unknown_flag = _require_non_empty_str(
        field="unknown_is_not_numeric_authorization",
        raw=contract.unknown_is_not_numeric_authorization,
    )
    unspecified_flag = _require_non_empty_str(
        field="unspecified_is_not_numeric_authorization",
        raw=contract.unspecified_is_not_numeric_authorization,
    )
    missing_flag = _require_non_empty_str(
        field="missing_input_fail_closed", raw=contract.missing_input_fail_closed
    )
    malformed_flag = _require_non_empty_str(
        field="malformed_input_fail_closed", raw=contract.malformed_input_fail_closed
    )
    zero_flag = _require_non_empty_str(
        field="zero_is_not_p01_value", raw=contract.zero_is_not_p01_value
    )
    absence_flag = _require_non_empty_str(
        field="absence_is_not_p01_value", raw=contract.absence_is_not_p01_value
    )
    venue_flag = _require_non_empty_str(
        field="venue_field_is_not_p01_value", raw=contract.venue_field_is_not_p01_value
    )
    name_flag = _require_non_empty_str(
        field="name_similarity_does_not_prove_source",
        raw=contract.name_similarity_does_not_prove_source,
    )
    equality_flag = _require_non_empty_str(
        field="numeric_equality_does_not_prove_source",
        raw=contract.numeric_equality_does_not_prove_source,
    )
    policy_flag = _require_non_empty_str(
        field="policy_slot_is_not_numeric_source",
        raw=contract.policy_slot_is_not_numeric_source,
    )
    algebra_flag = _require_non_empty_str(
        field="algebra_slot_is_not_numeric_source",
        raw=contract.algebra_slot_is_not_numeric_source,
    )
    haircut_flag = _require_non_empty_str(
        field="unspecified_haircut_cannot_construct_p01",
        raw=contract.unspecified_haircut_cannot_construct_p01,
    )
    subtract_flag = _require_non_empty_str(
        field="unspecified_cannot_authorize_subtraction",
        raw=contract.unspecified_cannot_authorize_subtraction,
    )
    add_flag = _require_non_empty_str(
        field="unspecified_cannot_authorize_addition",
        raw=contract.unspecified_cannot_authorize_addition,
    )
    net_flag = _require_non_empty_str(
        field="unspecified_cannot_authorize_netting",
        raw=contract.unspecified_cannot_authorize_netting,
    )
    omit_flag = _require_non_empty_str(
        field="unspecified_cannot_authorize_omission",
        raw=contract.unspecified_cannot_authorize_omission,
    )
    ignore_flag = _require_non_empty_str(
        field="unspecified_cannot_authorize_ignore",
        raw=contract.unspecified_cannot_authorize_ignore,
    )
    rejected = _require_non_empty_str(
        field="rejected_provenance_inferences",
        raw=contract.rejected_provenance_inferences,
    )
    remaining = _require_non_empty_str(
        field="remaining_unresolved_semantics",
        raw=contract.remaining_unresolved_semantics,
    )
    evidence = _require_non_empty_str(
        field="evidence_classification", raw=contract.evidence_classification
    )
    candidates = _require_non_empty_str(
        field="candidate_sources_classification",
        raw=contract.candidate_sources_classification,
    )
    contradiction = _require_non_empty_str(
        field="contradiction_state", raw=contract.contradiction_state
    )
    semantics_resolved = _require_non_empty_str(
        field="term_semantics_resolved_status",
        raw=contract.term_semantics_resolved_status,
    )
    closed = _require_non_empty_str(
        field="unspecified_closed_status", raw=contract.unspecified_closed_status
    )
    effect = _require_non_empty_str(
        field="p01_numeric_value_provenance_contract_authority_effect",
        raw=contract.p01_numeric_value_provenance_contract_authority_effect,
    )
    digest = _require_non_empty_str(field="provenance_digest", raw=contract.provenance_digest)
    if version != CONTRACT_VERSION:
        raise P01NumericValueProvenanceContractError("P01_CONTRACT_VERSION_MISMATCH")
    if parent_overlap != PARENT_OVERLAP_CONTRACT_SCHEMA_CLASS:
        raise P01NumericValueProvenanceContractError("P01_PARENT_OVERLAP_SCHEMA_MISMATCH")
    if parent_embedding != PARENT_EMBEDDING_CONTRACT_SCHEMA_CLASS:
        raise P01NumericValueProvenanceContractError("P01_PARENT_EMBEDDING_SCHEMA_MISMATCH")
    if parent_inclusion != PARENT_INCLUSION_CONTRACT_SCHEMA_CLASS:
        raise P01NumericValueProvenanceContractError("P01_PARENT_INCLUSION_SCHEMA_MISMATCH")
    if parent_applicability != PARENT_APPLICABILITY_CONTRACT_SCHEMA_CLASS:
        raise P01NumericValueProvenanceContractError("P01_PARENT_APPLICABILITY_SCHEMA_MISMATCH")
    if parent_term_set != PARENT_TERM_SET_CONTRACT_SCHEMA_CLASS:
        raise P01NumericValueProvenanceContractError("P01_PARENT_TERM_SET_SCHEMA_MISMATCH")
    if parent_term != PARENT_TERM_CONTRACT_SCHEMA_CLASS:
        raise P01NumericValueProvenanceContractError("P01_PARENT_TERM_SCHEMA_MISMATCH")
    if target != DIMENSION_ID:
        raise P01NumericValueProvenanceContractError("P01_TARGET_DIMENSION_MISMATCH")
    if policy_id != POLICY_ID:
        raise P01NumericValueProvenanceContractError("P01_POLICY_ID_MISMATCH")
    if term_id != TERM_ID:
        raise P01NumericValueProvenanceContractError("P01_TERM_ID_MISMATCH")
    if resolved.lower() == "true":
        raise P01NumericValueProvenanceContractError(
            "P01_NUMERIC_VALUE_PROVENANCE_RESOLVED_FORBIDDEN"
        )
    if resolved != P01_NUMERIC_VALUE_PROVENANCE_RESOLVED_STATUS:
        raise P01NumericValueProvenanceContractError(
            "P01_NUMERIC_VALUE_PROVENANCE_RESOLVED_STATUS_MISMATCH"
        )
    _reject_coerced_source(field="p01_numeric_value_provenance_status", raw=status)
    if status != P01_NUMERIC_VALUE_PROVENANCE_STATUS:
        raise P01NumericValueProvenanceContractError("P01_NUMERIC_VALUE_PROVENANCE_STATUS_MISMATCH")
    _reject_coerced_source(field="p01_numeric_value_source", raw=source)
    if source != P01_NUMERIC_VALUE_SOURCE:
        raise P01NumericValueProvenanceContractError("P01_NUMERIC_VALUE_SOURCE_MISMATCH")
    _reject_coerced_source(field="p01_numeric_value_transformation", raw=transformation)
    if transformation != P01_NUMERIC_VALUE_TRANSFORMATION:
        raise P01NumericValueProvenanceContractError("P01_NUMERIC_VALUE_TRANSFORMATION_MISMATCH")
    _reject_coerced_source(field="typed_provenance_class", raw=typed_class)
    if typed_class != TYPED_PROVENANCE_CLASS:
        raise P01NumericValueProvenanceContractError("P01_TYPED_PROVENANCE_CLASS_UNPROVEN")
    if typed_class in {
        TYPED_PROVENANCE_CLASS_VENUE_NATIVE,
        TYPED_PROVENANCE_CLASS_INTERNALLY_RECONSTRUCTED,
        TYPED_PROVENANCE_CLASS_POLICY_DERIVED,
        TYPED_PROVENANCE_CLASS_CONFIGURATION_DERIVED,
        TYPED_PROVENANCE_CLASS_RISK_MODEL_DERIVED,
        TYPED_PROVENANCE_CLASS_LEDGER_DERIVED,
        TYPED_PROVENANCE_CLASS_ACCOUNTING_DERIVED,
        TYPED_PROVENANCE_CLASS_COMPOSITE,
    }:
        raise P01NumericValueProvenanceContractError("P01_TYPED_PROVENANCE_CLASS_UNPROVEN")
    _reject_coerced_source(field="producer_state", raw=producer)
    if producer != PRODUCER_STATE:
        raise P01NumericValueProvenanceContractError("P01_PRODUCER_STATE_MISMATCH")
    _reject_coerced_source(field="source_object_id", raw=source_object)
    if source_object != SOURCE_OBJECT_ID:
        raise P01NumericValueProvenanceContractError("P01_SOURCE_OBJECT_ID_MISMATCH")
    _reject_coerced_source(field="source_field_id", raw=source_field)
    if source_field != SOURCE_FIELD_ID:
        raise P01NumericValueProvenanceContractError("P01_SOURCE_FIELD_ID_MISMATCH")
    _reject_coerced_source(field="source_contract_id", raw=source_contract)
    if source_contract != SOURCE_CONTRACT_ID:
        raise P01NumericValueProvenanceContractError("P01_SOURCE_CONTRACT_ID_MISMATCH")
    _reject_coerced_source(field="transformation_chain_state", raw=chain)
    if chain != TRANSFORMATION_CHAIN_STATE:
        raise P01NumericValueProvenanceContractError("P01_TRANSFORMATION_CHAIN_STATE_MISMATCH")
    if time_state != TIME_SEMANTICS_STATE:
        raise P01NumericValueProvenanceContractError("P01_TIME_SEMANTICS_STATE_MISMATCH")
    if unit_state != UNIT_DIMENSION_TRANSFORM_STATE:
        raise P01NumericValueProvenanceContractError("P01_UNIT_DIMENSION_TRANSFORM_STATE_MISMATCH")
    if missing_treatment != MISSING_VALUE_TREATMENT:
        raise P01NumericValueProvenanceContractError("P01_MISSING_VALUE_TREATMENT_MISMATCH")
    if stale_treatment != STALE_VALUE_TREATMENT:
        raise P01NumericValueProvenanceContractError("P01_STALE_VALUE_TREATMENT_MISMATCH")
    if unavailable_treatment != UNAVAILABLE_VALUE_TREATMENT:
        raise P01NumericValueProvenanceContractError("P01_UNAVAILABLE_VALUE_TREATMENT_MISMATCH")
    if contradictory_treatment != CONTRADICTORY_VALUE_TREATMENT:
        raise P01NumericValueProvenanceContractError("P01_CONTRADICTORY_VALUE_TREATMENT_MISMATCH")
    if partial_treatment != PARTIAL_EVIDENCE_TREATMENT:
        raise P01NumericValueProvenanceContractError("P01_PARTIAL_EVIDENCE_TREATMENT_MISMATCH")
    if multiple_treatment != MULTIPLE_CANDIDATE_TREATMENT:
        raise P01NumericValueProvenanceContractError("P01_MULTIPLE_CANDIDATE_TREATMENT_MISMATCH")
    _reject_coerced_source(field="fallback_source_state", raw=fallback)
    if fallback != FALLBACK_SOURCE_STATE:
        raise P01NumericValueProvenanceContractError("P01_FALLBACK_SOURCE_STATE_MISMATCH")
    if computation != NUMERIC_COMPUTATION_RULE_STATE:
        raise P01NumericValueProvenanceContractError("P01_NUMERIC_COMPUTATION_RULE_STATE_MISMATCH")
    if haircut_construction != HAIRCUT_RESERVE_DEPLETION_CONSTRUCTION_STATE:
        raise P01NumericValueProvenanceContractError(
            "P01_HAIRCUT_RESERVE_DEPLETION_CONSTRUCTION_STATE_MISMATCH"
        )
    _require_true_pin(
        field="unknown_is_not_numeric_authorization",
        raw=unknown_flag,
        expected=UNKNOWN_IS_NOT_NUMERIC_AUTHORIZATION,
        error="P01_UNKNOWN_MUST_NOT_AUTHORIZE_NUMERIC",
    )
    _require_true_pin(
        field="unspecified_is_not_numeric_authorization",
        raw=unspecified_flag,
        expected=UNSPECIFIED_IS_NOT_NUMERIC_AUTHORIZATION,
        error="P01_UNSPECIFIED_MUST_NOT_AUTHORIZE_NUMERIC",
    )
    _require_true_pin(
        field="missing_input_fail_closed",
        raw=missing_flag,
        expected=MISSING_INPUT_FAIL_CLOSED,
        error="P01_MISSING_INPUT_FAIL_CLOSED_REQUIRED",
    )
    _require_true_pin(
        field="malformed_input_fail_closed",
        raw=malformed_flag,
        expected=MALFORMED_INPUT_FAIL_CLOSED,
        error="P01_MALFORMED_INPUT_FAIL_CLOSED_REQUIRED",
    )
    _require_true_pin(
        field="zero_is_not_p01_value",
        raw=zero_flag,
        expected=ZERO_IS_NOT_P01_VALUE,
        error="P01_ZERO_IS_NOT_P01_VALUE_REQUIRED",
    )
    _require_true_pin(
        field="absence_is_not_p01_value",
        raw=absence_flag,
        expected=ABSENCE_IS_NOT_P01_VALUE,
        error="P01_ABSENCE_IS_NOT_P01_VALUE_REQUIRED",
    )
    _require_true_pin(
        field="venue_field_is_not_p01_value",
        raw=venue_flag,
        expected=VENUE_FIELD_IS_NOT_P01_VALUE,
        error="P01_VENUE_FIELD_IS_NOT_P01_VALUE_REQUIRED",
    )
    _require_true_pin(
        field="name_similarity_does_not_prove_source",
        raw=name_flag,
        expected=NAME_SIMILARITY_DOES_NOT_PROVE_SOURCE,
        error="P01_NAME_SIMILARITY_MUST_NOT_PROVE_SOURCE",
    )
    _require_true_pin(
        field="numeric_equality_does_not_prove_source",
        raw=equality_flag,
        expected=NUMERIC_EQUALITY_DOES_NOT_PROVE_SOURCE,
        error="P01_NUMERIC_EQUALITY_MUST_NOT_PROVE_SOURCE",
    )
    _require_true_pin(
        field="policy_slot_is_not_numeric_source",
        raw=policy_flag,
        expected=POLICY_SLOT_IS_NOT_NUMERIC_SOURCE,
        error="P01_POLICY_SLOT_MUST_NOT_BE_NUMERIC_SOURCE",
    )
    _require_true_pin(
        field="algebra_slot_is_not_numeric_source",
        raw=algebra_flag,
        expected=ALGEBRA_SLOT_IS_NOT_NUMERIC_SOURCE,
        error="P01_ALGEBRA_SLOT_MUST_NOT_BE_NUMERIC_SOURCE",
    )
    _require_true_pin(
        field="unspecified_haircut_cannot_construct_p01",
        raw=haircut_flag,
        expected=UNSPECIFIED_HAIRCUT_CANNOT_CONSTRUCT_P01,
        error="P01_UNSPECIFIED_HAIRCUT_CONSTRUCTION_FORBIDDEN",
    )
    _require_true_pin(
        field="unspecified_cannot_authorize_subtraction",
        raw=subtract_flag,
        expected=UNSPECIFIED_CANNOT_AUTHORIZE_SUBTRACTION,
        error="P01_UNSPECIFIED_SUBTRACTION_FORBIDDEN",
    )
    _require_true_pin(
        field="unspecified_cannot_authorize_addition",
        raw=add_flag,
        expected=UNSPECIFIED_CANNOT_AUTHORIZE_ADDITION,
        error="P01_UNSPECIFIED_ADDITION_FORBIDDEN",
    )
    _require_true_pin(
        field="unspecified_cannot_authorize_netting",
        raw=net_flag,
        expected=UNSPECIFIED_CANNOT_AUTHORIZE_NETTING,
        error="P01_UNSPECIFIED_NETTING_FORBIDDEN",
    )
    _require_true_pin(
        field="unspecified_cannot_authorize_omission",
        raw=omit_flag,
        expected=UNSPECIFIED_CANNOT_AUTHORIZE_OMISSION,
        error="P01_UNSPECIFIED_OMISSION_FORBIDDEN",
    )
    _require_true_pin(
        field="unspecified_cannot_authorize_ignore",
        raw=ignore_flag,
        expected=UNSPECIFIED_CANNOT_AUTHORIZE_IGNORE,
        error="P01_UNSPECIFIED_IGNORE_FORBIDDEN",
    )
    if rejected != REJECTED_PROVENANCE_INFERENCES:
        raise P01NumericValueProvenanceContractError("P01_REJECTED_PROVENANCE_INFERENCES_MISMATCH")
    if remaining != REMAINING_UNRESOLVED_SEMANTICS:
        raise P01NumericValueProvenanceContractError("P01_REMAINING_UNRESOLVED_SEMANTICS_MISMATCH")
    if "P01_NUMERIC_VALUE_PROVENANCE_UNSPECIFIED" not in remaining:
        raise P01NumericValueProvenanceContractError(
            "P01_NUMERIC_VALUE_PROVENANCE_MUST_REMAIN_UNSPECIFIED"
        )
    if "P01_OVERLAP_WITH_U04_U05_UNRESOLVED" not in remaining:
        raise P01NumericValueProvenanceContractError("P01_OVERLAP_MUST_REMAIN_UNRESOLVED")
    if evidence != EVIDENCE_CLASSIFICATION:
        raise P01NumericValueProvenanceContractError("P01_EVIDENCE_CLASSIFICATION_MISMATCH")
    if candidates != CANDIDATE_SOURCES_CLASSIFICATION:
        raise P01NumericValueProvenanceContractError(
            "P01_CANDIDATE_SOURCES_CLASSIFICATION_MISMATCH"
        )
    if contradiction != CONTRADICTION_NONE:
        raise P01NumericValueProvenanceContractError("P01_CONTRADICTION_STATUS_MISMATCH")
    if semantics_resolved.lower() == "true":
        raise P01NumericValueProvenanceContractError("P01_TERM_SEMANTICS_RESOLVED_FORBIDDEN")
    if semantics_resolved != TERM_SEMANTICS_RESOLVED_STATUS:
        raise P01NumericValueProvenanceContractError("P01_TERM_SEMANTICS_RESOLVED_STATUS_MISMATCH")
    if closed.lower() == "true":
        raise P01NumericValueProvenanceContractError(
            "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED_FORBIDDEN"
        )
    if closed != UNSPECIFIED_CLOSED_STATUS:
        raise P01NumericValueProvenanceContractError("P01_UNSPECIFIED_CLOSED_STATUS_MISMATCH")
    if (
        effect != P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_AUTHORITY_EFFECT
        or effect != AUTHORITY_EFFECT_NONE
    ):
        raise P01NumericValueProvenanceContractError("P01_AUTHORITY_EFFECT_MUST_REMAIN_NONE")
    if P01_OVERLAP_WITH_U04_U05_CONTRACT_AUTHORITY_EFFECT != AUTHORITY_EFFECT_NONE:
        raise P01NumericValueProvenanceContractError("P01_PARENT_AUTHORITY_EFFECT_MUST_REMAIN_NONE")
    if P01_EMBEDDING_STATE_CONTRACT_AUTHORITY_EFFECT != AUTHORITY_EFFECT_NONE:
        raise P01NumericValueProvenanceContractError("P01_PARENT_AUTHORITY_EFFECT_MUST_REMAIN_NONE")
    if P01_EQUITY_BASE_INCLUSION_CONTRACT_AUTHORITY_EFFECT != AUTHORITY_EFFECT_NONE:
        raise P01NumericValueProvenanceContractError("P01_PARENT_AUTHORITY_EFFECT_MUST_REMAIN_NONE")
    if P01_APPLICABILITY_CONTRACT_AUTHORITY_EFFECT != AUTHORITY_EFFECT_NONE:
        raise P01NumericValueProvenanceContractError("P01_PARENT_AUTHORITY_EFFECT_MUST_REMAIN_NONE")
    if EARLIEST_UNRESOLVED_ALGEBRA_TERM != "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED":
        raise P01NumericValueProvenanceContractError("P01_EARLIEST_ALGEBRA_TERM_DRIFT")
    if "U04_PENDING_ORDER_RESERVATION_INCLUSION_UNRESOLVED" not in UNRESOLVED_ALGEBRA_TERMS:
        raise P01NumericValueProvenanceContractError("P01_U04_MUST_REMAIN_UNRESOLVED")
    if "U05_LIABILITY_INCLUSION_OR_VALUE_UNRESOLVED" not in UNRESOLVED_ALGEBRA_TERMS:
        raise P01NumericValueProvenanceContractError("P01_U05_MUST_REMAIN_UNRESOLVED")
    if "U06_FEE_INCLUSION_UNRESOLVED" not in UNRESOLVED_ALGEBRA_TERMS:
        raise P01NumericValueProvenanceContractError("P01_U06_MUST_REMAIN_UNRESOLVED")
    parent_term_contract = build_p01_haircut_reserve_depletion_term_contract_v1(
        p01_term_contract_id="P01_NUMERIC_PROVENANCE_PARENT_TERM_ALIGNMENT"
    )
    if parent_term_contract.numeric_state != PARENT_NUMERIC_STATE:
        raise P01NumericValueProvenanceContractError("P01_PARENT_NUMERIC_STATE_ALIGNMENT_MISMATCH")
    if parent_term_contract.numeric_state != NUMERIC_NOT_COMPUTED:
        raise P01NumericValueProvenanceContractError("P01_PARENT_NUMERIC_MUST_REMAIN_NOT_COMPUTED")
    if parent_term_contract.origin_class != PARENT_ORIGIN_CLASS:
        raise P01NumericValueProvenanceContractError("P01_PARENT_ORIGIN_CLASS_ALIGNMENT_MISMATCH")
    parent_term_set_contract = build_p01_term_set_and_unit_class_contract_v1(
        p01_term_set_and_unit_class_contract_id="P01_NUMERIC_PROVENANCE_PARENT_TERM_SET_ALIGNMENT"
    )
    if parent_term_set_contract.p01_term_set_resolved_status != "false":
        raise P01NumericValueProvenanceContractError("P01_PARENT_TERM_SET_RESOLVED_ALIGNMENT")
    if parent_term_set_contract.p01_value_unit_class_resolved_status != "false":
        raise P01NumericValueProvenanceContractError("P01_PARENT_UNIT_RESOLVED_ALIGNMENT")
    parent_applicability_contract = build_p01_applicability_contract_v1(
        p01_applicability_contract_id="P01_NUMERIC_PROVENANCE_PARENT_APPLICABILITY_ALIGNMENT"
    )
    if parent_applicability_contract.p01_applicability_resolved_status != "false":
        raise P01NumericValueProvenanceContractError("P01_PARENT_APPLICABILITY_RESOLVED_ALIGNMENT")
    parent_inclusion_contract = build_p01_equity_base_inclusion_contract_v1(
        p01_equity_base_inclusion_contract_id="P01_NUMERIC_PROVENANCE_PARENT_INCLUSION_ALIGNMENT"
    )
    if parent_inclusion_contract.p01_equity_base_inclusion_resolved_status != "false":
        raise P01NumericValueProvenanceContractError("P01_PARENT_INCLUSION_RESOLVED_ALIGNMENT")
    parent_embedding_contract = build_p01_embedding_state_contract_v1(
        p01_embedding_state_contract_id="P01_NUMERIC_PROVENANCE_PARENT_EMBEDDING_ALIGNMENT"
    )
    if parent_embedding_contract.p01_embedded_state_resolved_status != "false":
        raise P01NumericValueProvenanceContractError("P01_PARENT_EMBEDDING_RESOLVED_ALIGNMENT")
    parent_overlap_contract = build_p01_overlap_with_u04_u05_contract_v1(
        p01_overlap_with_u04_u05_contract_id="P01_NUMERIC_PROVENANCE_PARENT_OVERLAP_ALIGNMENT"
    )
    if parent_overlap_contract.p01_u04_overlap_state != P01_U04_OVERLAP_STATE:
        raise P01NumericValueProvenanceContractError("P01_PARENT_U04_OVERLAP_PIN_MUST_REMAIN")
    if parent_overlap_contract.p01_u05_overlap_state != P01_U05_OVERLAP_STATE:
        raise P01NumericValueProvenanceContractError("P01_PARENT_U05_OVERLAP_PIN_MUST_REMAIN")
    algebra = build_reconstruction_algebra_contract_v1(
        algebra_contract_id="P01_NUMERIC_PROVENANCE_ALGEBRA_ALIGNMENT"
    )
    p01_term = next(term for term in algebra.terms if term.term_id == TERM_ID)
    if p01_term.numeric_participation_state != NUMERIC_NOT_COMPUTED:
        raise P01NumericValueProvenanceContractError("P01_ALGEBRA_NUMERIC_MUST_REMAIN_NOT_COMPUTED")
    if algebra.algebra_completeness_status != "INCOMPLETE":
        raise P01NumericValueProvenanceContractError("P01_ALGEBRA_COMPLETENESS_ALIGNMENT")
    canonical = contract.to_canonical_dict()
    expected_digest = compute_p01_numeric_value_provenance_digest_v1(canonical)
    if not _SHA256_HEX.fullmatch(digest):
        raise P01NumericValueProvenanceContractError("P01_PROVENANCE_DIGEST_NOT_SHA256")
    if digest != expected_digest:
        raise P01NumericValueProvenanceContractError("P01_PROVENANCE_DIGEST_MISMATCH")
    _ = contract_id


def build_p01_numeric_value_provenance_contract_v1(
    **fields: Any,
) -> P01NumericValueProvenanceContractV1:
    """Construct the typed P01 numeric provenance contract. Does not mint a P01 value."""

    payload = dict(fields)
    defaults = {
        "p01_numeric_value_provenance_contract_version": CONTRACT_VERSION,
        "parent_p01_overlap_with_u04_u05_contract_schema_class": (
            PARENT_OVERLAP_CONTRACT_SCHEMA_CLASS
        ),
        "parent_p01_embedding_state_contract_schema_class": PARENT_EMBEDDING_CONTRACT_SCHEMA_CLASS,
        "parent_p01_equity_base_inclusion_contract_schema_class": (
            PARENT_INCLUSION_CONTRACT_SCHEMA_CLASS
        ),
        "parent_p01_applicability_contract_schema_class": (
            PARENT_APPLICABILITY_CONTRACT_SCHEMA_CLASS
        ),
        "parent_p01_term_set_and_unit_class_contract_schema_class": (
            PARENT_TERM_SET_CONTRACT_SCHEMA_CLASS
        ),
        "parent_p01_term_contract_schema_class": PARENT_TERM_CONTRACT_SCHEMA_CLASS,
        "target_semantic_dimension_id": DIMENSION_ID,
        "policy_id": POLICY_ID,
        "term_id": TERM_ID,
        "p01_numeric_value_provenance_resolved_status": (
            P01_NUMERIC_VALUE_PROVENANCE_RESOLVED_STATUS
        ),
        "p01_numeric_value_provenance_status": P01_NUMERIC_VALUE_PROVENANCE_STATUS,
        "p01_numeric_value_source": P01_NUMERIC_VALUE_SOURCE,
        "p01_numeric_value_transformation": P01_NUMERIC_VALUE_TRANSFORMATION,
        "typed_provenance_class": TYPED_PROVENANCE_CLASS,
        "producer_state": PRODUCER_STATE,
        "source_object_id": SOURCE_OBJECT_ID,
        "source_field_id": SOURCE_FIELD_ID,
        "source_contract_id": SOURCE_CONTRACT_ID,
        "transformation_chain_state": TRANSFORMATION_CHAIN_STATE,
        "time_semantics_state": TIME_SEMANTICS_STATE,
        "unit_dimension_transform_state": UNIT_DIMENSION_TRANSFORM_STATE,
        "missing_value_treatment": MISSING_VALUE_TREATMENT,
        "stale_value_treatment": STALE_VALUE_TREATMENT,
        "unavailable_value_treatment": UNAVAILABLE_VALUE_TREATMENT,
        "contradictory_value_treatment": CONTRADICTORY_VALUE_TREATMENT,
        "partial_evidence_treatment": PARTIAL_EVIDENCE_TREATMENT,
        "multiple_candidate_treatment": MULTIPLE_CANDIDATE_TREATMENT,
        "fallback_source_state": FALLBACK_SOURCE_STATE,
        "numeric_computation_rule_state": NUMERIC_COMPUTATION_RULE_STATE,
        "haircut_reserve_depletion_construction_state": (
            HAIRCUT_RESERVE_DEPLETION_CONSTRUCTION_STATE
        ),
        "unknown_is_not_numeric_authorization": UNKNOWN_IS_NOT_NUMERIC_AUTHORIZATION,
        "unspecified_is_not_numeric_authorization": UNSPECIFIED_IS_NOT_NUMERIC_AUTHORIZATION,
        "missing_input_fail_closed": MISSING_INPUT_FAIL_CLOSED,
        "malformed_input_fail_closed": MALFORMED_INPUT_FAIL_CLOSED,
        "zero_is_not_p01_value": ZERO_IS_NOT_P01_VALUE,
        "absence_is_not_p01_value": ABSENCE_IS_NOT_P01_VALUE,
        "venue_field_is_not_p01_value": VENUE_FIELD_IS_NOT_P01_VALUE,
        "name_similarity_does_not_prove_source": NAME_SIMILARITY_DOES_NOT_PROVE_SOURCE,
        "numeric_equality_does_not_prove_source": NUMERIC_EQUALITY_DOES_NOT_PROVE_SOURCE,
        "policy_slot_is_not_numeric_source": POLICY_SLOT_IS_NOT_NUMERIC_SOURCE,
        "algebra_slot_is_not_numeric_source": ALGEBRA_SLOT_IS_NOT_NUMERIC_SOURCE,
        "unspecified_haircut_cannot_construct_p01": UNSPECIFIED_HAIRCUT_CANNOT_CONSTRUCT_P01,
        "unspecified_cannot_authorize_subtraction": UNSPECIFIED_CANNOT_AUTHORIZE_SUBTRACTION,
        "unspecified_cannot_authorize_addition": UNSPECIFIED_CANNOT_AUTHORIZE_ADDITION,
        "unspecified_cannot_authorize_netting": UNSPECIFIED_CANNOT_AUTHORIZE_NETTING,
        "unspecified_cannot_authorize_omission": UNSPECIFIED_CANNOT_AUTHORIZE_OMISSION,
        "unspecified_cannot_authorize_ignore": UNSPECIFIED_CANNOT_AUTHORIZE_IGNORE,
        "rejected_provenance_inferences": REJECTED_PROVENANCE_INFERENCES,
        "remaining_unresolved_semantics": REMAINING_UNRESOLVED_SEMANTICS,
        "evidence_classification": EVIDENCE_CLASSIFICATION,
        "candidate_sources_classification": CANDIDATE_SOURCES_CLASSIFICATION,
        "contradiction_state": CONTRADICTION_NONE,
        "term_semantics_resolved_status": TERM_SEMANTICS_RESOLVED_STATUS,
        "unspecified_closed_status": UNSPECIFIED_CLOSED_STATUS,
        "p01_numeric_value_provenance_contract_authority_effect": AUTHORITY_EFFECT_NONE,
    }
    for key, value in defaults.items():
        payload.setdefault(key, value)
    missing = [name for name in _VECTOR_FIELDS if name not in payload]
    if missing:
        raise P01NumericValueProvenanceContractError("P01_FIELD_MISSING:" + ",".join(missing))
    attached = attach_p01_numeric_value_provenance_digest_v1(payload)
    return P01NumericValueProvenanceContractV1(
        **{name: attached[name] for name in P01_NUMERIC_VALUE_PROVENANCE_REQUIRED_FIELDS}
    )


def reject_p01_unspecified_provenance_as_numeric_authorization_v1(
    *, provenance_status: str
) -> None:
    """Unspecified or unknown provenance is not a numeric P01 authorization."""

    _reject_coerced_source(field="p01_numeric_value_provenance_status", raw=provenance_status)
    raise P01NumericValueProvenanceContractError("P01_UNSPECIFIED_NUMERIC_AUTHORIZATION_FORBIDDEN")


def reject_p01_venue_field_as_numeric_source_v1(*, source: str) -> None:
    """Venue-raw fields are not a P01 numeric source."""

    _reject_coerced_source(field="p01_numeric_value_source", raw=source)
    raise P01NumericValueProvenanceContractError("P01_NUMERIC_VALUE_SOURCE_MISMATCH")


def reject_p01_zero_as_numeric_value_v1(*, numeric_state: str) -> None:
    """Zero or absence is not a P01 numeric value."""

    _reject_coerced_source(field="p01_numeric_value_source", raw=numeric_state)
    raise P01NumericValueProvenanceContractError("P01_NUMERIC_VALUE_SOURCE_MISMATCH")


def reject_p01_name_similarity_or_equality_as_source_v1(*, source_rule: str) -> None:
    """Name similarity or numeric equality does not prove a P01 source."""

    _reject_coerced_source(field="p01_numeric_value_source", raw=source_rule)
    raise P01NumericValueProvenanceContractError("P01_NUMERIC_SOURCE_INFERRED_FORBIDDEN")


def reject_p01_haircut_unspecified_as_numeric_construction_v1(*, construction_state: str) -> None:
    """Unresolved haircut/reserve/depletion semantics cannot construct a P01 number."""

    _reject_coerced_source(
        field="haircut_reserve_depletion_construction_state", raw=construction_state
    )
    if construction_state != HAIRCUT_RESERVE_DEPLETION_CONSTRUCTION_STATE:
        raise P01NumericValueProvenanceContractError(
            "P01_UNSPECIFIED_HAIRCUT_CONSTRUCTION_FORBIDDEN"
        )
    raise P01NumericValueProvenanceContractError("P01_UNSPECIFIED_HAIRCUT_CONSTRUCTION_FORBIDDEN")


def reject_p01_unspecified_provenance_as_arithmetic_v1(
    *, provenance_status: str, requested_action: str
) -> None:
    """Unspecified provenance cannot authorize add, subtract, net, omit, or ignore."""

    _reject_coerced_source(field="p01_numeric_value_provenance_status", raw=provenance_status)
    folded = _fold(requested_action)
    if folded in _ARITHMETIC_ACTION_TOKENS:
        raise P01NumericValueProvenanceContractError(
            "P01_UNSPECIFIED_PROVENANCE_ARITHMETIC_FORBIDDEN"
        )
    raise P01NumericValueProvenanceContractError("P01_NUMERIC_VALUE_PROVENANCE_STATUS_MISMATCH")
