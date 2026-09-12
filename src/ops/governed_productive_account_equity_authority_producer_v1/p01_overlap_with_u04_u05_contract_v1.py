"""Typed P01 overlap/equivalence adjudication versus U04 and U05.

Encodes the forensic result that canonical evidence does not prove whether
P01 is economically equivalent, partially overlapping, fully overlapping,
disjoint, nested, member-dependent, or applicability-dependent with U04
pending-order reservation semantics or U05 liability semantics. Unknown
remains fail-closed independently for each counterpart. Schema presence is
not P01 resolution. This slice does not reopen broader embedding or
equity-base inclusion except as inherited unresolved context.

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
    P01_OVERLAP_WITH_U04_U05_CONTRACT_AUTHORITY_EFFECT,
    P01_OVERLAP_WITH_U04_U05_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_OVERLAP_WITH_U04_U05_CONTRACT_SCHEMA_PRESENT,
    P01_OVERLAP_WITH_U04_U05_PROVENANCE_REQUIRED_FIELDS,
    P01_TERM_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_TERM_CONTRACT_SCHEMA_PRESENT,
    P01_TERM_SEMANTICS_RESOLVED,
    P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_SCHEMA_PRESENT,
    P01_U04_OVERLAP_RESOLVED,
    P01_U05_OVERLAP_RESOLVED,
    RECONSTRUCTION_ALGEBRA_COMPLETE,
    SOURCE_OBJECT_PRESENT,
    SOURCE_SELECTED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_applicability_contract_v1 import (
    SCHEMA_CLASS as P01_APPLICABILITY_SCHEMA_CLASS,
    build_p01_applicability_contract_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_embedding_state_contract_v1 import (
    P01_EMBEDDED_STATE,
    P01_OVERLAP_STATE as PARENT_AF_OVERLAP_STATE,
    REMAINING_UNRESOLVED_SEMANTICS as PARENT_REMAINING_UNRESOLVED_SEMANTICS,
    SCHEMA_CLASS as P01_EMBEDDING_STATE_SCHEMA_CLASS,
    build_p01_embedding_state_contract_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_equity_base_inclusion_contract_v1 import (
    P01_EQUITY_BASE_INCLUSION_STATUS,
    SCHEMA_CLASS as P01_EQUITY_BASE_INCLUSION_SCHEMA_CLASS,
    build_p01_equity_base_inclusion_contract_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_haircut_reserve_depletion_term_contract_v1 import (
    EMBEDDED_STATE as PARENT_EMBEDDED_STATE,
    OVERLAP_STATE as PARENT_TERM_OVERLAP_STATE,
    SCHEMA_CLASS as P01_TERM_SCHEMA_CLASS,
    build_p01_haircut_reserve_depletion_term_contract_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_term_set_and_unit_class_contract_v1 import (
    SCHEMA_CLASS as P01_TERM_SET_SCHEMA_CLASS,
    build_p01_term_set_and_unit_class_contract_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.reconstruction_algebra_contract_v1 import (
    CONTRADICTION_NONE,
    DIMENSION_ID,
    EARLIEST_UNRESOLVED_ALGEBRA_TERM,
    NUMERIC_PRESENT_ZERO,
    TERM_EQUITY_BASE,
    TERM_FEE,
    TERM_LIABILITY,
    TERM_P01_HAIRCUT_RESERVE_DEPLETION,
    TERM_PENDING_ORDER_RESERVATION,
    U04_PENDING_ORDER_RESERVATIONS,
    U05_LIABILITIES_BORROWINGS,
    UNRESOLVED_ALGEBRA_TERMS,
    build_reconstruction_algebra_contract_v1,
)

SCHEMA_CLASS = "P01_OVERLAP_WITH_U04_U05_CONTRACT_V1"
CONTRACT_VERSION = "v1"
POLICY_ID = "P01"
TERM_ID = TERM_P01_HAIRCUT_RESERVE_DEPLETION
PARENT_EMBEDDING_CONTRACT_SCHEMA_CLASS = P01_EMBEDDING_STATE_SCHEMA_CLASS
PARENT_INCLUSION_CONTRACT_SCHEMA_CLASS = P01_EQUITY_BASE_INCLUSION_SCHEMA_CLASS
PARENT_APPLICABILITY_CONTRACT_SCHEMA_CLASS = P01_APPLICABILITY_SCHEMA_CLASS
PARENT_TERM_SET_CONTRACT_SCHEMA_CLASS = P01_TERM_SET_SCHEMA_CLASS
PARENT_TERM_CONTRACT_SCHEMA_CLASS = P01_TERM_SCHEMA_CLASS
OVERLAP_UNRESOLVED = "UNRESOLVED"
P01_U04_OVERLAP_STATE = OVERLAP_UNRESOLVED
P01_U04_OVERLAP_RESOLVED_STATUS = "false"
P01_U04_OVERLAP_ADJUDICATION = "UNKNOWN_RELATIONSHIP_FAIL_CLOSED"
P01_U05_OVERLAP_STATE = OVERLAP_UNRESOLVED
P01_U05_OVERLAP_RESOLVED_STATUS = "false"
P01_U05_OVERLAP_ADJUDICATION = "UNKNOWN_RELATIONSHIP_FAIL_CLOSED"
TYPED_OVERLAP_STATE_UNKNOWN = "UNKNOWN"
TYPED_OVERLAP_STATE_EQUIVALENT = "EQUIVALENT"
TYPED_OVERLAP_STATE_PARTIALLY_OVERLAPPING = "PARTIALLY_OVERLAPPING"
TYPED_OVERLAP_STATE_FULLY_OVERLAPPING = "FULLY_OVERLAPPING"
TYPED_OVERLAP_STATE_DISJOINT = "DISJOINT"
TYPED_OVERLAP_STATE_P01_CONTAINS_U04 = "P01_CONTAINS_U04"
TYPED_OVERLAP_STATE_U04_CONTAINS_P01 = "U04_CONTAINS_P01"
TYPED_OVERLAP_STATE_P01_CONTAINS_U05 = "P01_CONTAINS_U05"
TYPED_OVERLAP_STATE_U05_CONTAINS_P01 = "U05_CONTAINS_P01"
TYPED_OVERLAP_STATE_MEMBER_DEPENDENT = "MEMBER_DEPENDENT_OVERLAP"
TYPED_OVERLAP_STATE_APPLICABILITY_DEPENDENT = "APPLICABILITY_DEPENDENT_OVERLAP"
TYPED_U04_OVERLAP_STATE = TYPED_OVERLAP_STATE_UNKNOWN
TYPED_U05_OVERLAP_STATE = TYPED_OVERLAP_STATE_UNKNOWN
SEMANTIC_EQUIVALENCE_STATE = "UNRESOLVED"
ECONOMIC_OVERLAP_STATE = "UNRESOLVED"
REPRESENTATIONAL_NESTING_STATE = "UNRESOLVED"
SHARED_PROVENANCE_STATE = "UNRESOLVED"
SHARED_NUMERIC_VALUE_STATE = "UNRESOLVED"
SHARED_UNIT_STATE = "UNRESOLVED"
SIMULTANEOUS_APPLICABILITY_STATE = "UNRESOLVED"
ARITHMETIC_INTERACTION_STATE = "UNRESOLVED"
P01_OVERLAP_STATE = (
    "U06_ACCRUED_FEES_DISTINCT_P01_U04_OVERLAP_UNRESOLVED_"
    "P01_U05_OVERLAP_UNRESOLVED_UNKNOWN_OVERLAP_FAIL_CLOSED"
)
U06_ACCRUED_FEES_DISTINCT_PIN = "U06_ACCRUED_FEES_DISTINCT"
UNKNOWN_IS_NOT_DISJOINT = "true"
UNKNOWN_IS_NOT_EQUIVALENT = "true"
UNKNOWN_IS_NOT_NON_OVERLAPPING = "true"
MISSING_INPUT_FAIL_CLOSED = "true"
MALFORMED_INPUT_FAIL_CLOSED = "true"
ZERO_DOES_NOT_PROVE_NON_OVERLAP = "true"
ABSENCE_DOES_NOT_PROVE_DISJOINT = "true"
EQUAL_VALUES_DO_NOT_PROVE_EQUIVALENCE = "true"
SHARED_SOURCE_DOES_NOT_PROVE_EQUIVALENCE = "true"
SHARED_UNIT_DOES_NOT_PROVE_EQUIVALENCE = "true"
TERM_SET_UNRESOLVED_DOES_NOT_DECIDE_OVERLAP = "true"
APPLICABILITY_UNRESOLVED_DOES_NOT_DECIDE_OVERLAP = "true"
EMBEDDING_UNRESOLVED_DOES_NOT_DECIDE_OVERLAP = "true"
U04_U05_LABELS_DO_NOT_DECIDE_OVERLAP = "true"
U06_DISTINCTNESS_DOES_NOT_DECIDE_P01_U06 = "true"
UNKNOWN_OVERLAP_CANNOT_AUTHORIZE_SUMMATION = "true"
UNKNOWN_OVERLAP_CANNOT_AUTHORIZE_DEDUPLICATION = "true"
UNKNOWN_OVERLAP_CANNOT_AUTHORIZE_NETTING = "true"
UNKNOWN_OVERLAP_CANNOT_AUTHORIZE_SUBTRACTION = "true"
UNKNOWN_OVERLAP_CANNOT_AUTHORIZE_OMISSION = "true"
NO_DOUBLE_COUNTING_PERMISSION = "true"
AUTHORITY_EFFECT_NONE = "NONE"
TERM_SEMANTICS_RESOLVED_STATUS = "false"
UNSPECIFIED_CLOSED_STATUS = "false"
REMAINING_UNRESOLVED_SEMANTICS = PARENT_REMAINING_UNRESOLVED_SEMANTICS
REJECTED_OVERLAP_INFERENCES = (
    "P01_U04_EQUIVALENT_UNPROVEN;"
    "P01_U04_PARTIALLY_OVERLAPPING_UNPROVEN;"
    "P01_U04_FULLY_OVERLAPPING_UNPROVEN;"
    "P01_U04_DISJOINT_UNPROVEN;"
    "P01_CONTAINS_U04_UNPROVEN;"
    "U04_CONTAINS_P01_UNPROVEN;"
    "P01_U04_MEMBER_DEPENDENT_OVERLAP_UNPROVEN;"
    "P01_U04_APPLICABILITY_DEPENDENT_OVERLAP_UNPROVEN;"
    "P01_U05_EQUIVALENT_UNPROVEN;"
    "P01_U05_PARTIALLY_OVERLAPPING_UNPROVEN;"
    "P01_U05_FULLY_OVERLAPPING_UNPROVEN;"
    "P01_U05_DISJOINT_UNPROVEN;"
    "P01_CONTAINS_U05_UNPROVEN;"
    "U05_CONTAINS_P01_UNPROVEN;"
    "P01_U05_MEMBER_DEPENDENT_OVERLAP_UNPROVEN;"
    "P01_U05_APPLICABILITY_DEPENDENT_OVERLAP_UNPROVEN;"
    "SAME_NUMERIC_VALUE_IS_NOT_EQUIVALENCE;"
    "SAME_CURRENCY_IS_NOT_EQUIVALENCE;"
    "SAME_SOURCE_FIELD_IS_NOT_EQUIVALENCE;"
    "SAME_EPOCH_IS_NOT_OVERLAP;"
    "SAME_SIGN_IS_NOT_EQUIVALENCE;"
    "BOTH_REDUCING_AVAILABLE_CAPITAL_IS_NOT_EQUIVALENCE;"
    "RESERVE_OR_LIABILITY_LABEL_IS_NOT_OVERLAP;"
    "COMMON_VENUE_PROVENANCE_IS_NOT_EQUIVALENCE;"
    "SAME_BALANCE_OBJECT_IS_NOT_OVERLAP;"
    "SIMULTANEOUS_NONZERO_IS_NOT_OVERLAP;"
    "ZERO_IS_NOT_NON_OVERLAP;"
    "ABSENCE_IS_NOT_DISJOINT;"
    "SEPARATE_SCHEMA_FIELDS_ARE_NOT_DISJOINT;"
    "ADJACENT_ALGEBRA_SLOTS_ARE_NOT_INDEPENDENCE;"
    "MISSING_OVERLAP_IMPLEMENTATION_IS_NOT_DISJOINT;"
    "MISSING_NESTING_IS_NOT_INDEPENDENCE;"
    "SHARED_PROVENANCE_IS_NOT_SEMANTIC_EQUIVALENCE;"
    "P01_REDUCTION_ONLY_IS_NOT_U04_OR_U05_EQUIVALENCE;"
    "U06_ACCRUED_FEES_DISTINCT_IS_NOT_P01_U06_DISJOINT_OR_EQUIVALENT;"
    "UNRESOLVED_TERM_SET_DOES_NOT_DECIDE_OVERLAP;"
    "UNRESOLVED_APPLICABILITY_DOES_NOT_DECIDE_OVERLAP;"
    "UNRESOLVED_EMBEDDING_DOES_NOT_DECIDE_OVERLAP;"
    "UNKNOWN_OVERLAP_CANNOT_AUTHORIZE_SUM_NET_SUBTRACT_OMIT_DEDUPLICATE"
)
EVIDENCE_CLASSIFICATION = (
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_AF_P01_OVERLAP_WITH_U04_U05_UNRESOLVED;"
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_T_U04_CONDITIONAL_SUBTRACTIVE_IF_NOT_IN_BASE;"
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_T_U05_CONDITIONAL_SUBTRACTIVE_IF_NOT_IN_BASE;"
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_T_P01_REDUCTION_ONLY_UNSPECIFIED;"
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_T_U06_ACCRUED_FEES_DISTINCT_NOT_P01_U06_RELATION;"
    "FORENSIC_EVIDENCE=ALGEBRA_SEPARATE_SLOTS_DO_NOT_PROVE_DISJOINT_OR_EQUIVALENT;"
    "FORENSIC_EVIDENCE=U04_INCLUSION_UNRESOLVED_U05_INCLUSION_OR_VALUE_UNRESOLVED;"
    "FORENSIC_EVIDENCE=NO_PRODUCTIVE_P01_U04_OR_P01_U05_OVERLAP_RULE;"
    "HISTORICAL_STATE=AF_AGGREGATE_U04_U05_EQUIVALENCE_UNPROVEN_PRESERVED_AS_PARENT_PIN;"
    "STRUCTURAL_REUSE_ONLY=P01_EMBEDDING_STATE_CONTRACT_V1;"
    "NAVIGATION=MAP_OF_TRUTH_NON_SSOT;"
    "REJECTED=EQUIVALENT_PARTIAL_FULL_DISJOINT_CONTAINS_MEMBER_APPLICABILITY_SAFE_ARITHMETIC;"
    "UNRESOLVED=P01_U04_OVERLAP;UNRESOLVED=P01_U05_OVERLAP"
)
_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")
_INFERRED_OVERLAP_TOKENS: tuple[str, ...] = (
    "equivalent",
    "partiallyoverlapping",
    "fullyoverlapping",
    "disjoint",
    "nonoverlapping",
    "p01containsu04",
    "u04containsp01",
    "p01containsu05",
    "u05containsp01",
    "memberdependentoverlap",
    "applicabilitydependentoverlap",
    "safetosum",
    "safetonet",
    "safetosubtract",
    "safetoomit",
    "safetodeduplicate",
    "safetocombine",
    "pendingorderreservation",
    "liability",
    TERM_PENDING_ORDER_RESERVATION.lower().replace("_", ""),
    TERM_LIABILITY.lower(),
    TERM_FEE.lower(),
    TERM_EQUITY_BASE.lower().replace("_", ""),
    "u04",
    "u05",
    "u06",
    "equalvalue",
    "sharedsource",
    "sharedprovenance",
    "sharedunit",
    "samecurrency",
    "sameepoch",
    "samesign",
    "samebalanceobject",
    "separateschemafield",
    "separateschema",
    "ordfrozen",
    "frozenbal",
    "isoeq",
    "availeq",
    "totaleq",
    "adjeq",
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
)
_VECTOR_FIELDS: tuple[str, ...] = tuple(
    name
    for name in P01_OVERLAP_WITH_U04_U05_PROVENANCE_REQUIRED_FIELDS
    if name != "provenance_digest"
)


class P01OverlapWithU04U05ContractError(ValueError):
    """Fail-closed P01 overlap/equivalence contract violation."""


def _fold(value: str) -> str:
    return str(value or "").strip().lower().replace("_", "").replace("-", "")


def _require_non_empty_str(*, field: str, raw: Any) -> str:
    if raw is None:
        raise P01OverlapWithU04U05ContractError(f"P01_FIELD_MISSING:{field}")
    if isinstance(raw, bool) or not isinstance(raw, str):
        raise P01OverlapWithU04U05ContractError(f"P01_FIELD_NOT_STRING:{field}")
    text = raw.strip()
    if text == "" or text != raw:
        raise P01OverlapWithU04U05ContractError(f"P01_FIELD_MISSING:{field}")
    return text


def _sha256_hex(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _canonical_json(payload: Mapping[str, str]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_p01_overlap_with_u04_u05_provenance_digest_v1(canonical: Mapping[str, str]) -> str:
    payload = {
        key: canonical[key]
        for key in P01_OVERLAP_WITH_U04_U05_PROVENANCE_REQUIRED_FIELDS
        if key != "provenance_digest"
    }
    return _sha256_hex(_canonical_json(payload))


def attach_p01_overlap_with_u04_u05_provenance_digest_v1(
    fields: Mapping[str, Any],
) -> dict[str, Any]:
    canonical: dict[str, str] = {}
    for canonical_name in P01_OVERLAP_WITH_U04_U05_PROVENANCE_REQUIRED_FIELDS:
        if canonical_name == "provenance_digest":
            continue
        if canonical_name not in fields:
            raise P01OverlapWithU04U05ContractError(f"P01_FIELD_MISSING:{canonical_name}")
        raw = fields[canonical_name]
        canonical[canonical_name] = "" if raw is None else str(raw)
    attached = dict(fields)
    attached["provenance_digest"] = compute_p01_overlap_with_u04_u05_provenance_digest_v1(canonical)
    return attached


def _reject_coerced_overlap(*, field: str, raw: str) -> None:
    folded = _fold(raw)
    _ = field
    if folded in _ZERO_OR_ABSENCE_TOKENS or folded in {"0", "false"}:
        raise P01OverlapWithU04U05ContractError("P01_ZERO_OR_ABSENCE_OVERLAP_FORBIDDEN")
    if any(token in folded for token in _INFERRED_OVERLAP_TOKENS):
        raise P01OverlapWithU04U05ContractError("P01_OVERLAP_INFERRED_FROM_LABEL_FORBIDDEN")


@dataclass(frozen=True)
class P01OverlapWithU04U05ContractV1:
    """Typed immutable P01↔U04/U05 overlap adjudication. Not a numeric instance."""

    p01_overlap_with_u04_u05_contract_id: str
    p01_overlap_with_u04_u05_contract_version: str
    parent_p01_embedding_state_contract_schema_class: str
    parent_p01_equity_base_inclusion_contract_schema_class: str
    parent_p01_applicability_contract_schema_class: str
    parent_p01_term_set_and_unit_class_contract_schema_class: str
    parent_p01_term_contract_schema_class: str
    target_semantic_dimension_id: str
    policy_id: str
    term_id: str
    p01_u04_overlap_state: str
    p01_u04_overlap_resolved_status: str
    p01_u04_overlap_adjudication: str
    typed_u04_overlap_state: str
    p01_u05_overlap_state: str
    p01_u05_overlap_resolved_status: str
    p01_u05_overlap_adjudication: str
    typed_u05_overlap_state: str
    semantic_equivalence_state: str
    economic_overlap_state: str
    representational_nesting_state: str
    shared_provenance_state: str
    shared_numeric_value_state: str
    shared_unit_state: str
    simultaneous_applicability_state: str
    arithmetic_interaction_state: str
    p01_overlap_state: str
    u06_accrued_fees_distinct_pin: str
    unknown_is_not_disjoint: str
    unknown_is_not_equivalent: str
    unknown_is_not_non_overlapping: str
    missing_input_fail_closed: str
    malformed_input_fail_closed: str
    zero_does_not_prove_non_overlap: str
    absence_does_not_prove_disjoint: str
    equal_values_do_not_prove_equivalence: str
    shared_source_does_not_prove_equivalence: str
    shared_unit_does_not_prove_equivalence: str
    term_set_unresolved_does_not_decide_overlap: str
    applicability_unresolved_does_not_decide_overlap: str
    embedding_unresolved_does_not_decide_overlap: str
    u04_u05_labels_do_not_decide_overlap: str
    u06_distinctness_does_not_decide_p01_u06: str
    unknown_overlap_cannot_authorize_summation: str
    unknown_overlap_cannot_authorize_deduplication: str
    unknown_overlap_cannot_authorize_netting: str
    unknown_overlap_cannot_authorize_subtraction: str
    unknown_overlap_cannot_authorize_omission: str
    no_double_counting_permission: str
    rejected_overlap_inferences: str
    remaining_unresolved_semantics: str
    evidence_classification: str
    contradiction_state: str
    term_semantics_resolved_status: str
    unspecified_closed_status: str
    p01_overlap_with_u04_u05_contract_authority_effect: str
    provenance_digest: str

    def __post_init__(self) -> None:
        _validate_p01_overlap_with_u04_u05_contract_v1(self)

    def to_canonical_dict(self) -> dict[str, str]:
        values = {
            "p01_overlap_with_u04_u05_contract_id": self.p01_overlap_with_u04_u05_contract_id,
            "p01_overlap_with_u04_u05_contract_version": (
                self.p01_overlap_with_u04_u05_contract_version
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
            "p01_u04_overlap_state": self.p01_u04_overlap_state,
            "p01_u04_overlap_resolved_status": self.p01_u04_overlap_resolved_status,
            "p01_u04_overlap_adjudication": self.p01_u04_overlap_adjudication,
            "typed_u04_overlap_state": self.typed_u04_overlap_state,
            "p01_u05_overlap_state": self.p01_u05_overlap_state,
            "p01_u05_overlap_resolved_status": self.p01_u05_overlap_resolved_status,
            "p01_u05_overlap_adjudication": self.p01_u05_overlap_adjudication,
            "typed_u05_overlap_state": self.typed_u05_overlap_state,
            "semantic_equivalence_state": self.semantic_equivalence_state,
            "economic_overlap_state": self.economic_overlap_state,
            "representational_nesting_state": self.representational_nesting_state,
            "shared_provenance_state": self.shared_provenance_state,
            "shared_numeric_value_state": self.shared_numeric_value_state,
            "shared_unit_state": self.shared_unit_state,
            "simultaneous_applicability_state": self.simultaneous_applicability_state,
            "arithmetic_interaction_state": self.arithmetic_interaction_state,
            "p01_overlap_state": self.p01_overlap_state,
            "u06_accrued_fees_distinct_pin": self.u06_accrued_fees_distinct_pin,
            "unknown_is_not_disjoint": self.unknown_is_not_disjoint,
            "unknown_is_not_equivalent": self.unknown_is_not_equivalent,
            "unknown_is_not_non_overlapping": self.unknown_is_not_non_overlapping,
            "missing_input_fail_closed": self.missing_input_fail_closed,
            "malformed_input_fail_closed": self.malformed_input_fail_closed,
            "zero_does_not_prove_non_overlap": self.zero_does_not_prove_non_overlap,
            "absence_does_not_prove_disjoint": self.absence_does_not_prove_disjoint,
            "equal_values_do_not_prove_equivalence": self.equal_values_do_not_prove_equivalence,
            "shared_source_does_not_prove_equivalence": (
                self.shared_source_does_not_prove_equivalence
            ),
            "shared_unit_does_not_prove_equivalence": self.shared_unit_does_not_prove_equivalence,
            "term_set_unresolved_does_not_decide_overlap": (
                self.term_set_unresolved_does_not_decide_overlap
            ),
            "applicability_unresolved_does_not_decide_overlap": (
                self.applicability_unresolved_does_not_decide_overlap
            ),
            "embedding_unresolved_does_not_decide_overlap": (
                self.embedding_unresolved_does_not_decide_overlap
            ),
            "u04_u05_labels_do_not_decide_overlap": self.u04_u05_labels_do_not_decide_overlap,
            "u06_distinctness_does_not_decide_p01_u06": (
                self.u06_distinctness_does_not_decide_p01_u06
            ),
            "unknown_overlap_cannot_authorize_summation": (
                self.unknown_overlap_cannot_authorize_summation
            ),
            "unknown_overlap_cannot_authorize_deduplication": (
                self.unknown_overlap_cannot_authorize_deduplication
            ),
            "unknown_overlap_cannot_authorize_netting": (
                self.unknown_overlap_cannot_authorize_netting
            ),
            "unknown_overlap_cannot_authorize_subtraction": (
                self.unknown_overlap_cannot_authorize_subtraction
            ),
            "unknown_overlap_cannot_authorize_omission": (
                self.unknown_overlap_cannot_authorize_omission
            ),
            "no_double_counting_permission": self.no_double_counting_permission,
            "rejected_overlap_inferences": self.rejected_overlap_inferences,
            "remaining_unresolved_semantics": self.remaining_unresolved_semantics,
            "evidence_classification": self.evidence_classification,
            "contradiction_state": self.contradiction_state,
            "term_semantics_resolved_status": self.term_semantics_resolved_status,
            "unspecified_closed_status": self.unspecified_closed_status,
            "p01_overlap_with_u04_u05_contract_authority_effect": (
                self.p01_overlap_with_u04_u05_contract_authority_effect
            ),
            "provenance_digest": self.provenance_digest,
        }
        return {key: values[key] for key in P01_OVERLAP_WITH_U04_U05_PROVENANCE_REQUIRED_FIELDS}


def _require_true_pin(*, field: str, raw: str, expected: str, error: str) -> None:
    if raw.lower() != "true" or raw != expected:
        raise P01OverlapWithU04U05ContractError(error)
    _ = field


def _validate_p01_overlap_with_u04_u05_contract_v1(
    contract: P01OverlapWithU04U05ContractV1,
) -> None:
    if P01_OVERLAP_WITH_U04_U05_CONTRACT_SCHEMA_PRESENT is not True:
        raise P01OverlapWithU04U05ContractError(
            "P01_OVERLAP_WITH_U04_U05_CONTRACT_SCHEMA_PRESENT_REQUIRED"
        )
    if P01_OVERLAP_WITH_U04_U05_CONTRACT_RUNTIME_INSTANCE_PRESENT is True:
        raise P01OverlapWithU04U05ContractError("P01_RUNTIME_INSTANCE_FORBIDDEN")
    if P01_EMBEDDING_STATE_CONTRACT_SCHEMA_PRESENT is not True:
        raise P01OverlapWithU04U05ContractError(
            "P01_EMBEDDING_STATE_CONTRACT_SCHEMA_PRESENT_REQUIRED"
        )
    if P01_EMBEDDING_STATE_CONTRACT_RUNTIME_INSTANCE_PRESENT is True:
        raise P01OverlapWithU04U05ContractError("P01_PARENT_EMBEDDING_RUNTIME_INSTANCE_FORBIDDEN")
    if P01_EQUITY_BASE_INCLUSION_CONTRACT_SCHEMA_PRESENT is not True:
        raise P01OverlapWithU04U05ContractError(
            "P01_EQUITY_BASE_INCLUSION_CONTRACT_SCHEMA_PRESENT_REQUIRED"
        )
    if P01_EQUITY_BASE_INCLUSION_CONTRACT_RUNTIME_INSTANCE_PRESENT is True:
        raise P01OverlapWithU04U05ContractError("P01_PARENT_INCLUSION_RUNTIME_INSTANCE_FORBIDDEN")
    if P01_APPLICABILITY_CONTRACT_SCHEMA_PRESENT is not True:
        raise P01OverlapWithU04U05ContractError(
            "P01_APPLICABILITY_CONTRACT_SCHEMA_PRESENT_REQUIRED"
        )
    if P01_APPLICABILITY_CONTRACT_RUNTIME_INSTANCE_PRESENT is True:
        raise P01OverlapWithU04U05ContractError(
            "P01_PARENT_APPLICABILITY_RUNTIME_INSTANCE_FORBIDDEN"
        )
    if P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_SCHEMA_PRESENT is not True:
        raise P01OverlapWithU04U05ContractError(
            "P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_SCHEMA_PRESENT_REQUIRED"
        )
    if P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_RUNTIME_INSTANCE_PRESENT is True:
        raise P01OverlapWithU04U05ContractError("P01_PARENT_TERM_SET_RUNTIME_INSTANCE_FORBIDDEN")
    if P01_TERM_CONTRACT_SCHEMA_PRESENT is not True:
        raise P01OverlapWithU04U05ContractError("P01_TERM_CONTRACT_SCHEMA_PRESENT_REQUIRED")
    if P01_TERM_CONTRACT_RUNTIME_INSTANCE_PRESENT is True:
        raise P01OverlapWithU04U05ContractError("P01_PARENT_RUNTIME_INSTANCE_FORBIDDEN")
    if RECONSTRUCTION_ALGEBRA_COMPLETE is True:
        raise P01OverlapWithU04U05ContractError("P01_RECONSTRUCTION_ALGEBRA_COMPLETE_PIN_FORBIDDEN")
    if SOURCE_SELECTED is True or SOURCE_OBJECT_PRESENT is True:
        raise P01OverlapWithU04U05ContractError("P01_SOURCE_SELECTION_FORBIDDEN")
    contract_id = _require_non_empty_str(
        field="p01_overlap_with_u04_u05_contract_id",
        raw=contract.p01_overlap_with_u04_u05_contract_id,
    )
    version = _require_non_empty_str(
        field="p01_overlap_with_u04_u05_contract_version",
        raw=contract.p01_overlap_with_u04_u05_contract_version,
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
    u04_state = _require_non_empty_str(
        field="p01_u04_overlap_state", raw=contract.p01_u04_overlap_state
    )
    u04_resolved = _require_non_empty_str(
        field="p01_u04_overlap_resolved_status",
        raw=contract.p01_u04_overlap_resolved_status,
    )
    u04_adjudication = _require_non_empty_str(
        field="p01_u04_overlap_adjudication", raw=contract.p01_u04_overlap_adjudication
    )
    typed_u04 = _require_non_empty_str(
        field="typed_u04_overlap_state", raw=contract.typed_u04_overlap_state
    )
    u05_state = _require_non_empty_str(
        field="p01_u05_overlap_state", raw=contract.p01_u05_overlap_state
    )
    u05_resolved = _require_non_empty_str(
        field="p01_u05_overlap_resolved_status",
        raw=contract.p01_u05_overlap_resolved_status,
    )
    u05_adjudication = _require_non_empty_str(
        field="p01_u05_overlap_adjudication", raw=contract.p01_u05_overlap_adjudication
    )
    typed_u05 = _require_non_empty_str(
        field="typed_u05_overlap_state", raw=contract.typed_u05_overlap_state
    )
    equivalence = _require_non_empty_str(
        field="semantic_equivalence_state", raw=contract.semantic_equivalence_state
    )
    economic = _require_non_empty_str(
        field="economic_overlap_state", raw=contract.economic_overlap_state
    )
    nesting = _require_non_empty_str(
        field="representational_nesting_state", raw=contract.representational_nesting_state
    )
    shared_provenance = _require_non_empty_str(
        field="shared_provenance_state", raw=contract.shared_provenance_state
    )
    shared_numeric = _require_non_empty_str(
        field="shared_numeric_value_state", raw=contract.shared_numeric_value_state
    )
    shared_unit = _require_non_empty_str(field="shared_unit_state", raw=contract.shared_unit_state)
    simultaneous = _require_non_empty_str(
        field="simultaneous_applicability_state",
        raw=contract.simultaneous_applicability_state,
    )
    arithmetic = _require_non_empty_str(
        field="arithmetic_interaction_state", raw=contract.arithmetic_interaction_state
    )
    overlap_pin = _require_non_empty_str(field="p01_overlap_state", raw=contract.p01_overlap_state)
    u06_pin = _require_non_empty_str(
        field="u06_accrued_fees_distinct_pin", raw=contract.u06_accrued_fees_distinct_pin
    )
    unknown_not_disjoint = _require_non_empty_str(
        field="unknown_is_not_disjoint", raw=contract.unknown_is_not_disjoint
    )
    unknown_not_equivalent = _require_non_empty_str(
        field="unknown_is_not_equivalent", raw=contract.unknown_is_not_equivalent
    )
    unknown_not_non_overlapping = _require_non_empty_str(
        field="unknown_is_not_non_overlapping", raw=contract.unknown_is_not_non_overlapping
    )
    missing_flag = _require_non_empty_str(
        field="missing_input_fail_closed", raw=contract.missing_input_fail_closed
    )
    malformed_flag = _require_non_empty_str(
        field="malformed_input_fail_closed", raw=contract.malformed_input_fail_closed
    )
    zero_flag = _require_non_empty_str(
        field="zero_does_not_prove_non_overlap",
        raw=contract.zero_does_not_prove_non_overlap,
    )
    absence_flag = _require_non_empty_str(
        field="absence_does_not_prove_disjoint",
        raw=contract.absence_does_not_prove_disjoint,
    )
    equal_flag = _require_non_empty_str(
        field="equal_values_do_not_prove_equivalence",
        raw=contract.equal_values_do_not_prove_equivalence,
    )
    source_flag = _require_non_empty_str(
        field="shared_source_does_not_prove_equivalence",
        raw=contract.shared_source_does_not_prove_equivalence,
    )
    unit_flag = _require_non_empty_str(
        field="shared_unit_does_not_prove_equivalence",
        raw=contract.shared_unit_does_not_prove_equivalence,
    )
    term_set_flag = _require_non_empty_str(
        field="term_set_unresolved_does_not_decide_overlap",
        raw=contract.term_set_unresolved_does_not_decide_overlap,
    )
    applicability_flag = _require_non_empty_str(
        field="applicability_unresolved_does_not_decide_overlap",
        raw=contract.applicability_unresolved_does_not_decide_overlap,
    )
    embedding_flag = _require_non_empty_str(
        field="embedding_unresolved_does_not_decide_overlap",
        raw=contract.embedding_unresolved_does_not_decide_overlap,
    )
    label_flag = _require_non_empty_str(
        field="u04_u05_labels_do_not_decide_overlap",
        raw=contract.u04_u05_labels_do_not_decide_overlap,
    )
    u06_flag = _require_non_empty_str(
        field="u06_distinctness_does_not_decide_p01_u06",
        raw=contract.u06_distinctness_does_not_decide_p01_u06,
    )
    sum_flag = _require_non_empty_str(
        field="unknown_overlap_cannot_authorize_summation",
        raw=contract.unknown_overlap_cannot_authorize_summation,
    )
    dedupe_flag = _require_non_empty_str(
        field="unknown_overlap_cannot_authorize_deduplication",
        raw=contract.unknown_overlap_cannot_authorize_deduplication,
    )
    net_flag = _require_non_empty_str(
        field="unknown_overlap_cannot_authorize_netting",
        raw=contract.unknown_overlap_cannot_authorize_netting,
    )
    subtract_flag = _require_non_empty_str(
        field="unknown_overlap_cannot_authorize_subtraction",
        raw=contract.unknown_overlap_cannot_authorize_subtraction,
    )
    omit_flag = _require_non_empty_str(
        field="unknown_overlap_cannot_authorize_omission",
        raw=contract.unknown_overlap_cannot_authorize_omission,
    )
    double_count_flag = _require_non_empty_str(
        field="no_double_counting_permission", raw=contract.no_double_counting_permission
    )
    rejected = _require_non_empty_str(
        field="rejected_overlap_inferences", raw=contract.rejected_overlap_inferences
    )
    remaining = _require_non_empty_str(
        field="remaining_unresolved_semantics", raw=contract.remaining_unresolved_semantics
    )
    evidence = _require_non_empty_str(
        field="evidence_classification", raw=contract.evidence_classification
    )
    contradiction = _require_non_empty_str(
        field="contradiction_state", raw=contract.contradiction_state
    )
    semantics_resolved = _require_non_empty_str(
        field="term_semantics_resolved_status", raw=contract.term_semantics_resolved_status
    )
    closed = _require_non_empty_str(
        field="unspecified_closed_status", raw=contract.unspecified_closed_status
    )
    effect = _require_non_empty_str(
        field="p01_overlap_with_u04_u05_contract_authority_effect",
        raw=contract.p01_overlap_with_u04_u05_contract_authority_effect,
    )
    digest = _require_non_empty_str(field="provenance_digest", raw=contract.provenance_digest)
    if version != CONTRACT_VERSION:
        raise P01OverlapWithU04U05ContractError("P01_CONTRACT_VERSION_MISMATCH")
    if parent_embedding != PARENT_EMBEDDING_CONTRACT_SCHEMA_CLASS:
        raise P01OverlapWithU04U05ContractError("P01_PARENT_EMBEDDING_CONTRACT_REFERENCE_MISMATCH")
    if parent_inclusion != PARENT_INCLUSION_CONTRACT_SCHEMA_CLASS:
        raise P01OverlapWithU04U05ContractError("P01_PARENT_INCLUSION_CONTRACT_REFERENCE_MISMATCH")
    if parent_applicability != PARENT_APPLICABILITY_CONTRACT_SCHEMA_CLASS:
        raise P01OverlapWithU04U05ContractError(
            "P01_PARENT_APPLICABILITY_CONTRACT_REFERENCE_MISMATCH"
        )
    if parent_term_set != PARENT_TERM_SET_CONTRACT_SCHEMA_CLASS:
        raise P01OverlapWithU04U05ContractError("P01_PARENT_TERM_SET_CONTRACT_REFERENCE_MISMATCH")
    if parent_term != PARENT_TERM_CONTRACT_SCHEMA_CLASS:
        raise P01OverlapWithU04U05ContractError("P01_PARENT_TERM_CONTRACT_REFERENCE_MISMATCH")
    if target != DIMENSION_ID:
        raise P01OverlapWithU04U05ContractError("P01_TARGET_DIMENSION_MISMATCH")
    if policy_id != POLICY_ID:
        raise P01OverlapWithU04U05ContractError("P01_POLICY_ID_MISMATCH")
    if term_id != TERM_ID:
        raise P01OverlapWithU04U05ContractError("P01_TERM_ID_MISMATCH")
    candidate_states = {
        TYPED_OVERLAP_STATE_EQUIVALENT,
        TYPED_OVERLAP_STATE_PARTIALLY_OVERLAPPING,
        TYPED_OVERLAP_STATE_FULLY_OVERLAPPING,
        TYPED_OVERLAP_STATE_DISJOINT,
        TYPED_OVERLAP_STATE_P01_CONTAINS_U04,
        TYPED_OVERLAP_STATE_U04_CONTAINS_P01,
        TYPED_OVERLAP_STATE_P01_CONTAINS_U05,
        TYPED_OVERLAP_STATE_U05_CONTAINS_P01,
        TYPED_OVERLAP_STATE_MEMBER_DEPENDENT,
        TYPED_OVERLAP_STATE_APPLICABILITY_DEPENDENT,
    }
    _reject_coerced_overlap(field="p01_u04_overlap_state", raw=u04_state)
    if u04_state in candidate_states:
        raise P01OverlapWithU04U05ContractError("P01_U04_OVERLAP_CANDIDATE_UNPROVEN")
    if u04_state != P01_U04_OVERLAP_STATE:
        raise P01OverlapWithU04U05ContractError("P01_U04_OVERLAP_STATE_MISMATCH")
    if u04_resolved.lower() == "true":
        raise P01OverlapWithU04U05ContractError("P01_U04_OVERLAP_RESOLVED_FORBIDDEN")
    if u04_resolved != P01_U04_OVERLAP_RESOLVED_STATUS:
        raise P01OverlapWithU04U05ContractError("P01_U04_OVERLAP_RESOLVED_STATUS_MISMATCH")
    _reject_coerced_overlap(field="p01_u04_overlap_adjudication", raw=u04_adjudication)
    if u04_adjudication != P01_U04_OVERLAP_ADJUDICATION:
        raise P01OverlapWithU04U05ContractError("P01_U04_OVERLAP_ADJUDICATION_MISMATCH")
    if typed_u04 in candidate_states:
        raise P01OverlapWithU04U05ContractError("P01_U04_OVERLAP_CANDIDATE_UNPROVEN")
    if typed_u04 != TYPED_U04_OVERLAP_STATE:
        raise P01OverlapWithU04U05ContractError("P01_TYPED_U04_OVERLAP_STATE_MISMATCH")
    _reject_coerced_overlap(field="p01_u05_overlap_state", raw=u05_state)
    if u05_state in candidate_states:
        raise P01OverlapWithU04U05ContractError("P01_U05_OVERLAP_CANDIDATE_UNPROVEN")
    if u05_state != P01_U05_OVERLAP_STATE:
        raise P01OverlapWithU04U05ContractError("P01_U05_OVERLAP_STATE_MISMATCH")
    if u05_resolved.lower() == "true":
        raise P01OverlapWithU04U05ContractError("P01_U05_OVERLAP_RESOLVED_FORBIDDEN")
    if u05_resolved != P01_U05_OVERLAP_RESOLVED_STATUS:
        raise P01OverlapWithU04U05ContractError("P01_U05_OVERLAP_RESOLVED_STATUS_MISMATCH")
    _reject_coerced_overlap(field="p01_u05_overlap_adjudication", raw=u05_adjudication)
    if u05_adjudication != P01_U05_OVERLAP_ADJUDICATION:
        raise P01OverlapWithU04U05ContractError("P01_U05_OVERLAP_ADJUDICATION_MISMATCH")
    if typed_u05 in candidate_states:
        raise P01OverlapWithU04U05ContractError("P01_U05_OVERLAP_CANDIDATE_UNPROVEN")
    if typed_u05 != TYPED_U05_OVERLAP_STATE:
        raise P01OverlapWithU04U05ContractError("P01_TYPED_U05_OVERLAP_STATE_MISMATCH")
    if equivalence != SEMANTIC_EQUIVALENCE_STATE:
        raise P01OverlapWithU04U05ContractError("P01_SEMANTIC_EQUIVALENCE_MUST_REMAIN_UNRESOLVED")
    if economic != ECONOMIC_OVERLAP_STATE:
        raise P01OverlapWithU04U05ContractError("P01_ECONOMIC_OVERLAP_MUST_REMAIN_UNRESOLVED")
    if nesting != REPRESENTATIONAL_NESTING_STATE:
        raise P01OverlapWithU04U05ContractError(
            "P01_REPRESENTATIONAL_NESTING_MUST_REMAIN_UNRESOLVED"
        )
    if shared_provenance != SHARED_PROVENANCE_STATE:
        raise P01OverlapWithU04U05ContractError("P01_SHARED_PROVENANCE_MUST_REMAIN_UNRESOLVED")
    if shared_numeric != SHARED_NUMERIC_VALUE_STATE:
        raise P01OverlapWithU04U05ContractError("P01_SHARED_NUMERIC_VALUE_MUST_REMAIN_UNRESOLVED")
    if shared_unit != SHARED_UNIT_STATE:
        raise P01OverlapWithU04U05ContractError("P01_SHARED_UNIT_MUST_REMAIN_UNRESOLVED")
    if simultaneous != SIMULTANEOUS_APPLICABILITY_STATE:
        raise P01OverlapWithU04U05ContractError(
            "P01_SIMULTANEOUS_APPLICABILITY_MUST_REMAIN_UNRESOLVED"
        )
    if arithmetic != ARITHMETIC_INTERACTION_STATE:
        raise P01OverlapWithU04U05ContractError("P01_ARITHMETIC_INTERACTION_MUST_REMAIN_UNRESOLVED")
    if overlap_pin != P01_OVERLAP_STATE:
        raise P01OverlapWithU04U05ContractError("P01_OVERLAP_STATE_MISMATCH")
    if U06_ACCRUED_FEES_DISTINCT_PIN not in overlap_pin:
        raise P01OverlapWithU04U05ContractError("P01_U06_DISTINCT_PIN_REQUIRED_IN_AGGREGATE")
    if u06_pin != U06_ACCRUED_FEES_DISTINCT_PIN:
        raise P01OverlapWithU04U05ContractError("P01_U06_DISTINCT_PIN_MISMATCH")
    dimension_values = (
        equivalence,
        economic,
        nesting,
        shared_provenance,
        shared_numeric,
        shared_unit,
        simultaneous,
        arithmetic,
    )
    if len(set(dimension_values)) != 1 or dimension_values[0] != "UNRESOLVED":
        raise P01OverlapWithU04U05ContractError("P01_OVERLAP_DIMENSIONS_COLLAPSED")
    _require_true_pin(
        field="unknown_is_not_disjoint",
        raw=unknown_not_disjoint,
        expected=UNKNOWN_IS_NOT_DISJOINT,
        error="P01_UNKNOWN_IS_NOT_DISJOINT_REQUIRED",
    )
    _require_true_pin(
        field="unknown_is_not_equivalent",
        raw=unknown_not_equivalent,
        expected=UNKNOWN_IS_NOT_EQUIVALENT,
        error="P01_UNKNOWN_IS_NOT_EQUIVALENT_REQUIRED",
    )
    _require_true_pin(
        field="unknown_is_not_non_overlapping",
        raw=unknown_not_non_overlapping,
        expected=UNKNOWN_IS_NOT_NON_OVERLAPPING,
        error="P01_UNKNOWN_IS_NOT_NON_OVERLAPPING_REQUIRED",
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
        field="zero_does_not_prove_non_overlap",
        raw=zero_flag,
        expected=ZERO_DOES_NOT_PROVE_NON_OVERLAP,
        error="P01_ZERO_DOES_NOT_PROVE_NON_OVERLAP_REQUIRED",
    )
    _require_true_pin(
        field="absence_does_not_prove_disjoint",
        raw=absence_flag,
        expected=ABSENCE_DOES_NOT_PROVE_DISJOINT,
        error="P01_ABSENCE_DOES_NOT_PROVE_DISJOINT_REQUIRED",
    )
    _require_true_pin(
        field="equal_values_do_not_prove_equivalence",
        raw=equal_flag,
        expected=EQUAL_VALUES_DO_NOT_PROVE_EQUIVALENCE,
        error="P01_EQUAL_VALUES_MUST_NOT_PROVE_EQUIVALENCE",
    )
    _require_true_pin(
        field="shared_source_does_not_prove_equivalence",
        raw=source_flag,
        expected=SHARED_SOURCE_DOES_NOT_PROVE_EQUIVALENCE,
        error="P01_SHARED_SOURCE_MUST_NOT_PROVE_EQUIVALENCE",
    )
    _require_true_pin(
        field="shared_unit_does_not_prove_equivalence",
        raw=unit_flag,
        expected=SHARED_UNIT_DOES_NOT_PROVE_EQUIVALENCE,
        error="P01_SHARED_UNIT_MUST_NOT_PROVE_EQUIVALENCE",
    )
    _require_true_pin(
        field="term_set_unresolved_does_not_decide_overlap",
        raw=term_set_flag,
        expected=TERM_SET_UNRESOLVED_DOES_NOT_DECIDE_OVERLAP,
        error="P01_TERM_SET_MUST_NOT_DECIDE_OVERLAP",
    )
    _require_true_pin(
        field="applicability_unresolved_does_not_decide_overlap",
        raw=applicability_flag,
        expected=APPLICABILITY_UNRESOLVED_DOES_NOT_DECIDE_OVERLAP,
        error="P01_APPLICABILITY_MUST_NOT_DECIDE_OVERLAP",
    )
    _require_true_pin(
        field="embedding_unresolved_does_not_decide_overlap",
        raw=embedding_flag,
        expected=EMBEDDING_UNRESOLVED_DOES_NOT_DECIDE_OVERLAP,
        error="P01_EMBEDDING_MUST_NOT_DECIDE_OVERLAP",
    )
    _require_true_pin(
        field="u04_u05_labels_do_not_decide_overlap",
        raw=label_flag,
        expected=U04_U05_LABELS_DO_NOT_DECIDE_OVERLAP,
        error="P01_U04_U05_LABELS_MUST_NOT_DECIDE_OVERLAP",
    )
    _require_true_pin(
        field="u06_distinctness_does_not_decide_p01_u06",
        raw=u06_flag,
        expected=U06_DISTINCTNESS_DOES_NOT_DECIDE_P01_U06,
        error="P01_U06_DISTINCTNESS_MUST_NOT_DECIDE_P01_U06",
    )
    _require_true_pin(
        field="unknown_overlap_cannot_authorize_summation",
        raw=sum_flag,
        expected=UNKNOWN_OVERLAP_CANNOT_AUTHORIZE_SUMMATION,
        error="P01_UNKNOWN_OVERLAP_SUMMATION_FORBIDDEN",
    )
    _require_true_pin(
        field="unknown_overlap_cannot_authorize_deduplication",
        raw=dedupe_flag,
        expected=UNKNOWN_OVERLAP_CANNOT_AUTHORIZE_DEDUPLICATION,
        error="P01_UNKNOWN_OVERLAP_DEDUPLICATION_FORBIDDEN",
    )
    _require_true_pin(
        field="unknown_overlap_cannot_authorize_netting",
        raw=net_flag,
        expected=UNKNOWN_OVERLAP_CANNOT_AUTHORIZE_NETTING,
        error="P01_UNKNOWN_OVERLAP_NETTING_FORBIDDEN",
    )
    _require_true_pin(
        field="unknown_overlap_cannot_authorize_subtraction",
        raw=subtract_flag,
        expected=UNKNOWN_OVERLAP_CANNOT_AUTHORIZE_SUBTRACTION,
        error="P01_UNKNOWN_OVERLAP_SUBTRACTION_FORBIDDEN",
    )
    _require_true_pin(
        field="unknown_overlap_cannot_authorize_omission",
        raw=omit_flag,
        expected=UNKNOWN_OVERLAP_CANNOT_AUTHORIZE_OMISSION,
        error="P01_UNKNOWN_OVERLAP_OMISSION_FORBIDDEN",
    )
    _require_true_pin(
        field="no_double_counting_permission",
        raw=double_count_flag,
        expected=NO_DOUBLE_COUNTING_PERMISSION,
        error="P01_NO_DOUBLE_COUNTING_PERMISSION_REQUIRED",
    )
    if rejected != REJECTED_OVERLAP_INFERENCES:
        raise P01OverlapWithU04U05ContractError("P01_REJECTED_OVERLAP_INFERENCES_MISMATCH")
    if remaining != REMAINING_UNRESOLVED_SEMANTICS:
        raise P01OverlapWithU04U05ContractError("P01_REMAINING_UNRESOLVED_SEMANTICS_MISMATCH")
    if "P01_OVERLAP_WITH_U04_U05_UNRESOLVED" not in remaining:
        raise P01OverlapWithU04U05ContractError("P01_OVERLAP_MUST_REMAIN_UNRESOLVED")
    if "P01_EMBEDDING_UNRESOLVED" not in remaining:
        raise P01OverlapWithU04U05ContractError("P01_EMBEDDING_MUST_REMAIN_UNRESOLVED")
    if "P01_NUMERIC_VALUE_PROVENANCE_UNSPECIFIED" not in remaining:
        raise P01OverlapWithU04U05ContractError(
            "P01_NUMERIC_VALUE_PROVENANCE_MUST_REMAIN_UNSPECIFIED"
        )
    if evidence != EVIDENCE_CLASSIFICATION:
        raise P01OverlapWithU04U05ContractError("P01_EVIDENCE_CLASSIFICATION_MISMATCH")
    if contradiction != CONTRADICTION_NONE:
        raise P01OverlapWithU04U05ContractError("P01_CONTRADICTION_STATUS_MISMATCH")
    if semantics_resolved.lower() == "true":
        raise P01OverlapWithU04U05ContractError("P01_TERM_SEMANTICS_RESOLVED_FORBIDDEN")
    if semantics_resolved != TERM_SEMANTICS_RESOLVED_STATUS:
        raise P01OverlapWithU04U05ContractError("P01_TERM_SEMANTICS_RESOLVED_STATUS_MISMATCH")
    if closed.lower() == "true":
        raise P01OverlapWithU04U05ContractError(
            "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED_FORBIDDEN"
        )
    if closed != UNSPECIFIED_CLOSED_STATUS:
        raise P01OverlapWithU04U05ContractError("P01_UNSPECIFIED_CLOSED_STATUS_MISMATCH")
    if (
        effect != P01_OVERLAP_WITH_U04_U05_CONTRACT_AUTHORITY_EFFECT
        or effect != AUTHORITY_EFFECT_NONE
    ):
        raise P01OverlapWithU04U05ContractError("P01_AUTHORITY_EFFECT_MUST_REMAIN_NONE")
    if P01_EMBEDDING_STATE_CONTRACT_AUTHORITY_EFFECT != AUTHORITY_EFFECT_NONE:
        raise P01OverlapWithU04U05ContractError("P01_PARENT_AUTHORITY_EFFECT_MUST_REMAIN_NONE")
    if P01_EQUITY_BASE_INCLUSION_CONTRACT_AUTHORITY_EFFECT != AUTHORITY_EFFECT_NONE:
        raise P01OverlapWithU04U05ContractError("P01_PARENT_AUTHORITY_EFFECT_MUST_REMAIN_NONE")
    if P01_APPLICABILITY_CONTRACT_AUTHORITY_EFFECT != AUTHORITY_EFFECT_NONE:
        raise P01OverlapWithU04U05ContractError("P01_PARENT_AUTHORITY_EFFECT_MUST_REMAIN_NONE")
    if EARLIEST_UNRESOLVED_ALGEBRA_TERM != "U04_PENDING_ORDER_RESERVATION_INCLUSION_UNRESOLVED":
        raise P01OverlapWithU04U05ContractError("P01_EARLIEST_ALGEBRA_TERM_DRIFT")
    if "U04_PENDING_ORDER_RESERVATION_INCLUSION_UNRESOLVED" not in UNRESOLVED_ALGEBRA_TERMS:
        raise P01OverlapWithU04U05ContractError("P01_U04_MUST_REMAIN_UNRESOLVED")
    if "U05_LIABILITY_INCLUSION_OR_VALUE_UNRESOLVED" not in UNRESOLVED_ALGEBRA_TERMS:
        raise P01OverlapWithU04U05ContractError("P01_U05_MUST_REMAIN_UNRESOLVED")
    if "U06_FEE_INCLUSION_UNRESOLVED" not in UNRESOLVED_ALGEBRA_TERMS:
        raise P01OverlapWithU04U05ContractError("P01_U06_MUST_REMAIN_UNRESOLVED")
    parent_term_contract = build_p01_haircut_reserve_depletion_term_contract_v1(
        p01_term_contract_id="P01_OVERLAP_PARENT_TERM_ALIGNMENT"
    )
    if parent_term_contract.embedded_state != PARENT_EMBEDDED_STATE:
        raise P01OverlapWithU04U05ContractError("P01_PARENT_EMBEDDED_ALIGNMENT_MISMATCH")
    if parent_term_contract.overlap_state != PARENT_TERM_OVERLAP_STATE:
        raise P01OverlapWithU04U05ContractError("P01_PARENT_TERM_OVERLAP_MUST_REMAIN_UNCHANGED")
    parent_term_set_contract = build_p01_term_set_and_unit_class_contract_v1(
        p01_term_set_and_unit_class_contract_id="P01_OVERLAP_PARENT_TERM_SET_ALIGNMENT"
    )
    if parent_term_set_contract.p01_term_set_resolved_status != "false":
        raise P01OverlapWithU04U05ContractError("P01_PARENT_TERM_SET_RESOLVED_ALIGNMENT")
    if parent_term_set_contract.p01_value_unit_class_resolved_status != "false":
        raise P01OverlapWithU04U05ContractError("P01_PARENT_UNIT_RESOLVED_ALIGNMENT")
    parent_applicability_contract = build_p01_applicability_contract_v1(
        p01_applicability_contract_id="P01_OVERLAP_PARENT_APPLICABILITY_ALIGNMENT"
    )
    if parent_applicability_contract.p01_applicability_resolved_status != "false":
        raise P01OverlapWithU04U05ContractError("P01_PARENT_APPLICABILITY_RESOLVED_ALIGNMENT")
    parent_inclusion_contract = build_p01_equity_base_inclusion_contract_v1(
        p01_equity_base_inclusion_contract_id="P01_OVERLAP_PARENT_INCLUSION_ALIGNMENT"
    )
    if (
        parent_inclusion_contract.p01_equity_base_inclusion_status
        != P01_EQUITY_BASE_INCLUSION_STATUS
    ):
        raise P01OverlapWithU04U05ContractError("P01_PARENT_INCLUSION_ALIGNMENT_MISMATCH")
    parent_embedding_contract = build_p01_embedding_state_contract_v1(
        p01_embedding_state_contract_id="P01_OVERLAP_PARENT_EMBEDDING_ALIGNMENT"
    )
    if parent_embedding_contract.p01_embedded_state != P01_EMBEDDED_STATE:
        raise P01OverlapWithU04U05ContractError("P01_PARENT_EMBEDDING_ALIGNMENT_MISMATCH")
    if parent_embedding_contract.p01_overlap_state != PARENT_AF_OVERLAP_STATE:
        raise P01OverlapWithU04U05ContractError("P01_PARENT_AF_OVERLAP_PIN_MUST_REMAIN_UNCHANGED")
    algebra = build_reconstruction_algebra_contract_v1(
        algebra_contract_id="P01_OVERLAP_ALGEBRA_ALIGNMENT"
    )
    p01_term = next(term for term in algebra.terms if term.term_id == TERM_ID)
    _ = p01_term
    u04_term = next(
        term for term in algebra.terms if term.term_id == TERM_PENDING_ORDER_RESERVATION
    )
    u05_term = next(term for term in algebra.terms if term.term_id == TERM_LIABILITY)
    if u04_term.operator_semantics != U04_PENDING_ORDER_RESERVATIONS:
        raise P01OverlapWithU04U05ContractError("P01_U04_ALGEBRA_PIN_DRIFT")
    if u05_term.operator_semantics != U05_LIABILITIES_BORROWINGS:
        raise P01OverlapWithU04U05ContractError("P01_U05_ALGEBRA_PIN_DRIFT")
    if algebra.algebra_completeness_status != "INCOMPLETE":
        raise P01OverlapWithU04U05ContractError("P01_ALGEBRA_COMPLETENESS_ALIGNMENT")
    canonical = contract.to_canonical_dict()
    expected_digest = compute_p01_overlap_with_u04_u05_provenance_digest_v1(canonical)
    if not _SHA256_HEX.fullmatch(digest):
        raise P01OverlapWithU04U05ContractError("P01_PROVENANCE_DIGEST_NOT_SHA256")
    if digest != expected_digest:
        raise P01OverlapWithU04U05ContractError("P01_PROVENANCE_DIGEST_MISMATCH")
    _ = contract_id


def build_p01_overlap_with_u04_u05_contract_v1(**fields: Any) -> P01OverlapWithU04U05ContractV1:
    """Construct the typed P01↔U04/U05 overlap contract. Does not resolve P01."""

    payload = dict(fields)
    defaults = {
        "p01_overlap_with_u04_u05_contract_version": CONTRACT_VERSION,
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
        "p01_u04_overlap_state": P01_U04_OVERLAP_STATE,
        "p01_u04_overlap_resolved_status": P01_U04_OVERLAP_RESOLVED_STATUS,
        "p01_u04_overlap_adjudication": P01_U04_OVERLAP_ADJUDICATION,
        "typed_u04_overlap_state": TYPED_U04_OVERLAP_STATE,
        "p01_u05_overlap_state": P01_U05_OVERLAP_STATE,
        "p01_u05_overlap_resolved_status": P01_U05_OVERLAP_RESOLVED_STATUS,
        "p01_u05_overlap_adjudication": P01_U05_OVERLAP_ADJUDICATION,
        "typed_u05_overlap_state": TYPED_U05_OVERLAP_STATE,
        "semantic_equivalence_state": SEMANTIC_EQUIVALENCE_STATE,
        "economic_overlap_state": ECONOMIC_OVERLAP_STATE,
        "representational_nesting_state": REPRESENTATIONAL_NESTING_STATE,
        "shared_provenance_state": SHARED_PROVENANCE_STATE,
        "shared_numeric_value_state": SHARED_NUMERIC_VALUE_STATE,
        "shared_unit_state": SHARED_UNIT_STATE,
        "simultaneous_applicability_state": SIMULTANEOUS_APPLICABILITY_STATE,
        "arithmetic_interaction_state": ARITHMETIC_INTERACTION_STATE,
        "p01_overlap_state": P01_OVERLAP_STATE,
        "u06_accrued_fees_distinct_pin": U06_ACCRUED_FEES_DISTINCT_PIN,
        "unknown_is_not_disjoint": UNKNOWN_IS_NOT_DISJOINT,
        "unknown_is_not_equivalent": UNKNOWN_IS_NOT_EQUIVALENT,
        "unknown_is_not_non_overlapping": UNKNOWN_IS_NOT_NON_OVERLAPPING,
        "missing_input_fail_closed": MISSING_INPUT_FAIL_CLOSED,
        "malformed_input_fail_closed": MALFORMED_INPUT_FAIL_CLOSED,
        "zero_does_not_prove_non_overlap": ZERO_DOES_NOT_PROVE_NON_OVERLAP,
        "absence_does_not_prove_disjoint": ABSENCE_DOES_NOT_PROVE_DISJOINT,
        "equal_values_do_not_prove_equivalence": EQUAL_VALUES_DO_NOT_PROVE_EQUIVALENCE,
        "shared_source_does_not_prove_equivalence": SHARED_SOURCE_DOES_NOT_PROVE_EQUIVALENCE,
        "shared_unit_does_not_prove_equivalence": SHARED_UNIT_DOES_NOT_PROVE_EQUIVALENCE,
        "term_set_unresolved_does_not_decide_overlap": (
            TERM_SET_UNRESOLVED_DOES_NOT_DECIDE_OVERLAP
        ),
        "applicability_unresolved_does_not_decide_overlap": (
            APPLICABILITY_UNRESOLVED_DOES_NOT_DECIDE_OVERLAP
        ),
        "embedding_unresolved_does_not_decide_overlap": (
            EMBEDDING_UNRESOLVED_DOES_NOT_DECIDE_OVERLAP
        ),
        "u04_u05_labels_do_not_decide_overlap": U04_U05_LABELS_DO_NOT_DECIDE_OVERLAP,
        "u06_distinctness_does_not_decide_p01_u06": U06_DISTINCTNESS_DOES_NOT_DECIDE_P01_U06,
        "unknown_overlap_cannot_authorize_summation": (UNKNOWN_OVERLAP_CANNOT_AUTHORIZE_SUMMATION),
        "unknown_overlap_cannot_authorize_deduplication": (
            UNKNOWN_OVERLAP_CANNOT_AUTHORIZE_DEDUPLICATION
        ),
        "unknown_overlap_cannot_authorize_netting": UNKNOWN_OVERLAP_CANNOT_AUTHORIZE_NETTING,
        "unknown_overlap_cannot_authorize_subtraction": (
            UNKNOWN_OVERLAP_CANNOT_AUTHORIZE_SUBTRACTION
        ),
        "unknown_overlap_cannot_authorize_omission": UNKNOWN_OVERLAP_CANNOT_AUTHORIZE_OMISSION,
        "no_double_counting_permission": NO_DOUBLE_COUNTING_PERMISSION,
        "rejected_overlap_inferences": REJECTED_OVERLAP_INFERENCES,
        "remaining_unresolved_semantics": REMAINING_UNRESOLVED_SEMANTICS,
        "evidence_classification": EVIDENCE_CLASSIFICATION,
        "contradiction_state": CONTRADICTION_NONE,
        "term_semantics_resolved_status": TERM_SEMANTICS_RESOLVED_STATUS,
        "unspecified_closed_status": UNSPECIFIED_CLOSED_STATUS,
        "p01_overlap_with_u04_u05_contract_authority_effect": AUTHORITY_EFFECT_NONE,
    }
    for key, value in defaults.items():
        payload.setdefault(key, value)
    missing = [name for name in _VECTOR_FIELDS if name not in payload]
    if missing:
        raise P01OverlapWithU04U05ContractError("P01_FIELD_MISSING:" + ",".join(missing))
    attached = attach_p01_overlap_with_u04_u05_provenance_digest_v1(payload)
    return P01OverlapWithU04U05ContractV1(
        **{name: attached[name] for name in P01_OVERLAP_WITH_U04_U05_PROVENANCE_REQUIRED_FIELDS}
    )


def reject_p01_unknown_overlap_as_disjoint_v1(*, overlap_state: str) -> None:
    """Unknown P01 overlap is not DISJOINT or NON_OVERLAPPING."""

    _reject_coerced_overlap(field="p01_u04_overlap_state", raw=overlap_state)
    if overlap_state in {TYPED_OVERLAP_STATE_DISJOINT, "NON_OVERLAPPING"}:
        raise P01OverlapWithU04U05ContractError("P01_UNKNOWN_OVERLAP_AUTO_DISJOINT_FORBIDDEN")
    raise P01OverlapWithU04U05ContractError("P01_U04_OVERLAP_STATE_MISMATCH")


def reject_p01_zero_or_absence_as_non_overlap_v1(*, overlap_state: str) -> None:
    """Zero or absence is not P01 non-overlap or disjointness."""

    _reject_coerced_overlap(field="p01_u04_overlap_state", raw=overlap_state)
    raise P01OverlapWithU04U05ContractError("P01_U04_OVERLAP_STATE_MISMATCH")


def reject_p01_equal_values_or_shared_source_as_equivalence_v1(*, overlap_rule: str) -> None:
    """Equal numeric values or shared source/provenance do not prove equivalence."""

    _reject_coerced_overlap(field="p01_u04_overlap_adjudication", raw=overlap_rule)
    raise P01OverlapWithU04U05ContractError("P01_U04_OVERLAP_ADJUDICATION_MISMATCH")


def reject_p01_u04_u05_labels_as_overlap_v1(*, overlap_rule: str) -> None:
    """U04/U05 labels, separate schema, or venue-raw state is not an overlap rule."""

    _reject_coerced_overlap(field="p01_u04_overlap_adjudication", raw=overlap_rule)
    raise P01OverlapWithU04U05ContractError("P01_U04_OVERLAP_ADJUDICATION_MISMATCH")


def reject_p01_u06_distinctness_as_p01_u06_relation_v1(*, overlap_rule: str) -> None:
    """U06 accrued-fee distinctness is not a P01↔U06 overlap, disjoint, or equivalent rule."""

    _reject_coerced_overlap(field="p01_u04_overlap_adjudication", raw=overlap_rule)
    raise P01OverlapWithU04U05ContractError("P01_U04_OVERLAP_ADJUDICATION_MISMATCH")


def reject_p01_unknown_overlap_as_arithmetic_v1(
    *, overlap_state: str, requested_action: str
) -> None:
    """Unknown overlap cannot authorize summation, netting, omission, or deduplication."""

    _reject_coerced_overlap(field="p01_u04_overlap_state", raw=overlap_state)
    folded = _fold(requested_action)
    if folded in _ARITHMETIC_ACTION_TOKENS:
        raise P01OverlapWithU04U05ContractError("P01_UNKNOWN_OVERLAP_ARITHMETIC_FORBIDDEN")
    raise P01OverlapWithU04U05ContractError("P01_U04_OVERLAP_STATE_MISMATCH")
