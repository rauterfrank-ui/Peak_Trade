"""Typed P01 broader embedding-state adjudication contract.

Encodes the forensic result that canonical evidence does not prove whether
P01, or any canonically defined P01 component, is economically or
semantically embedded in any other accounting, reconstruction, reserve,
liability, fee, valuation, or policy object. Unknown remains fail-closed.
Schema presence is not P01 resolution. Broader embedding is not the
already-adjudicated EQUITY_BASE inclusion question.

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
    P01_EMBEDDING_STATE_PROVENANCE_REQUIRED_FIELDS,
    P01_EQUITY_BASE_INCLUSION_CONTRACT_AUTHORITY_EFFECT,
    P01_EQUITY_BASE_INCLUSION_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_EQUITY_BASE_INCLUSION_CONTRACT_SCHEMA_PRESENT,
    P01_EQUITY_BASE_INCLUSION_RESOLVED,
    P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED,
    P01_TERM_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_TERM_CONTRACT_SCHEMA_PRESENT,
    P01_TERM_SEMANTICS_RESOLVED,
    P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_SCHEMA_PRESENT,
    P01_TERM_SET_RESOLVED,
    P01_VALUE_UNIT_CLASS_RESOLVED,
    RECONSTRUCTION_ALGEBRA_COMPLETE,
    SOURCE_OBJECT_PRESENT,
    SOURCE_SELECTED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_applicability_contract_v1 import (
    SCHEMA_CLASS as P01_APPLICABILITY_SCHEMA_CLASS,
    build_p01_applicability_contract_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_equity_base_inclusion_contract_v1 import (
    P01_EQUITY_BASE_INCLUSION_STATUS,
    REMAINING_UNRESOLVED_SEMANTICS as PARENT_REMAINING_UNRESOLVED_SEMANTICS,
    SCHEMA_CLASS as P01_EQUITY_BASE_INCLUSION_SCHEMA_CLASS,
    build_p01_equity_base_inclusion_contract_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_haircut_reserve_depletion_term_contract_v1 import (
    EMBEDDED_STATE as PARENT_EMBEDDED_STATE,
    OVERLAP_STATE as PARENT_OVERLAP_STATE,
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
    EMBEDDED_CONDITIONAL,
    EMBEDDED_NO,
    EMBEDDED_NOT_APPLICABLE,
    EMBEDDED_UNRESOLVED,
    EMBEDDED_YES,
    ROLE_EMBEDDED_NOT_SEPARATE,
    TERM_EQUITY_BASE,
    TERM_FEE,
    TERM_LIABILITY,
    TERM_P01_HAIRCUT_RESERVE_DEPLETION,
    TERM_PENDING_ORDER_RESERVATION,
    UNRESOLVED_ALGEBRA_TERMS,
    build_reconstruction_algebra_contract_v1,
)

SCHEMA_CLASS = "P01_EMBEDDING_STATE_CONTRACT_V1"
CONTRACT_VERSION = "v1"
POLICY_ID = "P01"
TERM_ID = TERM_P01_HAIRCUT_RESERVE_DEPLETION
PARENT_INCLUSION_CONTRACT_SCHEMA_CLASS = P01_EQUITY_BASE_INCLUSION_SCHEMA_CLASS
PARENT_APPLICABILITY_CONTRACT_SCHEMA_CLASS = P01_APPLICABILITY_SCHEMA_CLASS
PARENT_TERM_SET_CONTRACT_SCHEMA_CLASS = P01_TERM_SET_SCHEMA_CLASS
PARENT_TERM_CONTRACT_SCHEMA_CLASS = P01_TERM_SCHEMA_CLASS
P01_EMBEDDED_STATE = EMBEDDED_UNRESOLVED
P01_EMBEDDED_STATE_RESOLVED_STATUS = "false"
P01_EMBEDDING_RULE = "UNSPECIFIED_FAIL_CLOSED"
P01_EMBEDDING_ADJUDICATION = "UNKNOWN_RELATIONSHIP_FAIL_CLOSED"
TYPED_EMBEDDING_STATE_UNKNOWN = "UNKNOWN"
TYPED_EMBEDDING_STATE_NOT_EMBEDDED = "NOT_EMBEDDED"
TYPED_EMBEDDING_STATE_FULLY_EMBEDDED = "FULLY_EMBEDDED"
TYPED_EMBEDDING_STATE_PARTIALLY_EMBEDDED = "PARTIALLY_EMBEDDED"
TYPED_EMBEDDING_STATE_EMBEDDED_IN_EQUITY_BASE = "EMBEDDED_IN_EQUITY_BASE"
TYPED_EMBEDDING_STATE_EMBEDDED_IN_U04 = "EMBEDDED_IN_U04"
TYPED_EMBEDDING_STATE_EMBEDDED_IN_U05 = "EMBEDDED_IN_U05"
TYPED_EMBEDDING_STATE_EMBEDDED_IN_U06 = "EMBEDDED_IN_U06"
TYPED_EMBEDDING_STATE_EMBEDDED_IN_ANOTHER_TERM = "EMBEDDED_IN_ANOTHER_ACCOUNTING_TERM"
TYPED_EMBEDDING_STATE_DEPENDS_ON_MEMBER_CLASS = "EMBEDDING_DEPENDS_ON_MEMBER_CLASS"
TYPED_EMBEDDING_STATE_DEPENDS_ON_APPLICABILITY = "EMBEDDING_DEPENDS_ON_APPLICABILITY"
TYPED_EMBEDDING_STATE = TYPED_EMBEDDING_STATE_UNKNOWN
FAMILY_LEVEL_EMBEDDING_STATE = "UNRESOLVED"
MEMBER_LEVEL_EMBEDDING_STATE = "UNRESOLVED"
ECONOMIC_OVERLAP_STATE = "UNRESOLVED"
REPRESENTATIONAL_NESTING_STATE = "UNRESOLVED"
ARITHMETIC_INCLUSION_STATE = "UNRESOLVED"
SEMANTIC_EQUIVALENCE_STATE = "UNRESOLVED"
P01_OVERLAP_STATE = (
    "U06_ACCRUED_FEES_DISTINCT_U04_U05_EQUIVALENCE_UNPROVEN_UNKNOWN_OVERLAP_FAIL_CLOSED"
)
UNKNOWN_IS_NOT_NOT_EMBEDDED = "true"
UNKNOWN_IS_NOT_EMBEDDED = "true"
ZERO_DOES_NOT_PROVE_EMBEDDING = "true"
ABSENCE_DOES_NOT_PROVE_EMBEDDING = "true"
MISSING_INPUT_FAIL_CLOSED = "true"
MALFORMED_INPUT_FAIL_CLOSED = "true"
TERM_SET_UNRESOLVED_DOES_NOT_DECIDE_EMBEDDING = "true"
APPLICABILITY_UNRESOLVED_DOES_NOT_DECIDE_EMBEDDING = "true"
UNIT_UNRESOLVED_DOES_NOT_DECIDE_EMBEDDING = "true"
EQUITY_BASE_INCLUSION_UNRESOLVED_DOES_NOT_DECIDE_BROADER_EMBEDDING = "true"
U04_U05_U06_LABELS_DO_NOT_DECIDE_EMBEDDING = "true"
EQUAL_VALUES_DO_NOT_PROVE_EMBEDDING = "true"
SHARED_SOURCE_DOES_NOT_PROVE_EMBEDDING = "true"
SEPARATE_SCHEMA_DOES_NOT_PROVE_INDEPENDENCE = "true"
UNKNOWN_EMBEDDING_CANNOT_AUTHORIZE_SUBTRACTION = "true"
UNKNOWN_EMBEDDING_CANNOT_AUTHORIZE_OMISSION = "true"
UNKNOWN_EMBEDDING_CANNOT_AUTHORIZE_NETTING = "true"
NO_DOUBLE_COUNTING_PERMISSION = "true"
AUTHORITY_EFFECT_NONE = "NONE"
TERM_SEMANTICS_RESOLVED_STATUS = "false"
UNSPECIFIED_CLOSED_STATUS = "false"
REMAINING_UNRESOLVED_SEMANTICS = PARENT_REMAINING_UNRESOLVED_SEMANTICS
REJECTED_EMBEDDING_INFERENCES = (
    "P01_NOT_EMBEDDED_ANYWHERE_UNPROVEN;"
    "P01_FULLY_EMBEDDED_UNPROVEN;"
    "P01_PARTIALLY_EMBEDDED_UNPROVEN;"
    "P01_EMBEDDED_IN_EQUITY_BASE_UNPROVEN;"
    "P01_EMBEDDED_IN_U04_UNPROVEN;"
    "P01_EMBEDDED_IN_U05_UNPROVEN;"
    "P01_EMBEDDED_IN_U06_UNPROVEN;"
    "P01_EMBEDDED_IN_ANOTHER_ACCOUNTING_TERM_UNPROVEN;"
    "P01_EMBEDDING_DEPENDS_ON_MEMBER_CLASS_UNPROVEN;"
    "P01_EMBEDDING_DEPENDS_ON_APPLICABILITY_UNPROVEN;"
    "U06_ACCRUED_FEES_MAY_BE_DISTINCT_IS_NOT_P01_NOT_EMBEDDED_IN_U06;"
    "EQUITY_BASE_INCLUSION_UNRESOLVED_IS_NOT_BROADER_EMBEDDING;"
    "FAMILY_LEVEL_IS_NOT_MEMBER_LEVEL;"
    "ECONOMIC_OVERLAP_IS_NOT_EMBEDDING;"
    "REPRESENTATIONAL_NESTING_IS_NOT_ARITHMETIC_INCLUSION;"
    "ARITHMETIC_ADJACENCY_IS_NOT_SEMANTIC_EQUIVALENCE;"
    "SHARED_PROVENANCE_IS_NOT_EMBEDDING;"
    "SHARED_UNIT_IS_NOT_EMBEDDING;"
    "COMMON_VENUE_SOURCE_IS_NOT_EMBEDDING;"
    "SEPARATE_ALGEBRA_SLOT_IS_NOT_INDEPENDENCE;"
    "ABSENT_NESTED_FIELD_IS_NOT_NON_EMBEDDING;"
    "U02_U03_EMBEDDED_NOT_SEPARATE_IS_NOT_P01_EMBEDDING;"
    "U04_U05_U06_CONDITIONAL_EMBEDDING_IS_NOT_P01_EMBEDDING;"
    "EQUAL_VALUES_ARE_NOT_EMBEDDING_OR_EQUIVALENCE;"
    "ZERO_IS_NOT_EMBEDDING_OR_NON_EMBEDDING;"
    "ABSENCE_IS_NOT_EMBEDDING_OR_NON_EMBEDDING;"
    "MISSING_CODE_IS_NOT_NOT_EMBEDDED;"
    "UNRESOLVED_TERM_SET_DOES_NOT_DECIDE_EMBEDDING;"
    "UNRESOLVED_APPLICABILITY_DOES_NOT_DECIDE_EMBEDDING;"
    "UNRESOLVED_UNIT_DOES_NOT_DECIDE_EMBEDDING;"
    "UNKNOWN_EMBEDDING_CANNOT_AUTHORIZE_SUBTRACTION_OMISSION_OR_NETTING;"
    "NOT_EMBEDDED_INDEPENDENT_SEPARATE_EMBEDDED_PARTIAL_SAFE_COMBINE_NET_FORBIDDEN"
)
EVIDENCE_CLASSIFICATION = (
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_AE_P01_EMBEDDED_STATE_UNRESOLVED;"
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_AB_P01_EMBEDDED_STATE_UNRESOLVED;"
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_AA_P01_ALGEBRA_EMBEDDED_UNRESOLVED;"
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_T_U02_U03_EMBEDDED_NOT_SEPARATE_NOT_P01;"
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_T_U06_ACCRUED_FEES_DISTINCT_NOT_P01_NON_EMBEDDING;"
    "FORENSIC_EVIDENCE=ALGEBRA_REJECTS_P01_EMBEDDED_NO_AS_P01_NON_EMBEDDING_UNPROVEN;"
    "FORENSIC_EVIDENCE=ALGEBRA_LISTS_P01_SEPARATE_SLOT_WITH_EMBEDDED_UNRESOLVED;"
    "FORENSIC_EVIDENCE=SRC_RISK_HAS_NO_P01_HAIRCUT_IMPLEMENTATION;"
    "FORENSIC_EVIDENCE=NO_PRODUCTIVE_P01_NESTING_OR_CONTAINMENT_RULE;"
    "HISTORICAL_STATE=11_2_1_N_HAIRCUTS_RESERVE_DEPLETION_FROZEN_PENDING_OWNER_POLICY_SUPERSEDED;"
    "STRUCTURAL_REUSE_ONLY=P01_EQUITY_BASE_INCLUSION_CONTRACT_V1;"
    "NAVIGATION=MAP_OF_TRUTH_NON_SSOT;"
    "REJECTED=NOT_EMBEDDED_FULLY_PARTIAL_EQUITY_BASE_U04_U05_U06_OTHER_TERM_MEMBER_CLASS_APPLICABILITY_SAFE;"
    "UNRESOLVED=P01_BROADER_EMBEDDING_RELATIONSHIP"
)
_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")
_INFERRED_EMBEDDING_TOKENS: tuple[str, ...] = (
    "p01notembeddedanywhere",
    "notembeddedanywhere",
    "fullyembedded",
    "partiallyembedded",
    "embeddedinequitybase",
    "embeddedinu04",
    "embeddedinu05",
    "embeddedinu06",
    "embeddedinanotheraccountingterm",
    "embeddingdependsonmemberclass",
    "embeddingdependsonapplicability",
    "notembedded",
    "independent",
    "separate",
    "embedded",
    "partial",
    "safetosubtract",
    "safetoomit",
    "safetocombine",
    "safetonet",
    "safe",
    ROLE_EMBEDDED_NOT_SEPARATE.lower().replace("_", ""),
    EMBEDDED_YES.lower(),
    EMBEDDED_NO.lower().replace("_", ""),
    EMBEDDED_CONDITIONAL.lower(),
    EMBEDDED_NOT_APPLICABLE.lower().replace("_", ""),
    TERM_EQUITY_BASE.lower().replace("_", ""),
    TERM_PENDING_ORDER_RESERVATION.lower().replace("_", ""),
    TERM_LIABILITY.lower(),
    TERM_FEE.lower(),
    "u04",
    "u05",
    "u06",
    "u02",
    "u03",
    "equalvalue",
    "sharedsource",
    "sharedprovenance",
    "frozenbal",
    "ordfrozen",
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
_SUBTRACTION_OMISSION_OR_NETTING_TOKENS: tuple[str, ...] = (
    "subtract",
    "subtraction",
    "deduct",
    "deduction",
    "omit",
    "omission",
    "ignore",
    "skip",
    "net",
    "netting",
    "combine",
    "combination",
)
_VECTOR_FIELDS: tuple[str, ...] = tuple(
    name for name in P01_EMBEDDING_STATE_PROVENANCE_REQUIRED_FIELDS if name != "provenance_digest"
)


class P01EmbeddingStateContractError(ValueError):
    """Fail-closed P01 broader embedding-state contract violation."""


def _fold(value: str) -> str:
    return str(value or "").strip().lower().replace("_", "").replace("-", "")


def _require_non_empty_str(*, field: str, raw: Any) -> str:
    if raw is None:
        raise P01EmbeddingStateContractError(f"P01_FIELD_MISSING:{field}")
    if isinstance(raw, bool) or not isinstance(raw, str):
        raise P01EmbeddingStateContractError(f"P01_FIELD_NOT_STRING:{field}")
    text = raw.strip()
    if text == "" or text != raw:
        raise P01EmbeddingStateContractError(f"P01_FIELD_MISSING:{field}")
    return text


def _sha256_hex(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _canonical_json(payload: Mapping[str, str]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_p01_embedding_state_provenance_digest_v1(canonical: Mapping[str, str]) -> str:
    payload = {
        key: canonical[key]
        for key in P01_EMBEDDING_STATE_PROVENANCE_REQUIRED_FIELDS
        if key != "provenance_digest"
    }
    return _sha256_hex(_canonical_json(payload))


def attach_p01_embedding_state_provenance_digest_v1(
    fields: Mapping[str, Any],
) -> dict[str, Any]:
    canonical: dict[str, str] = {}
    for canonical_name in P01_EMBEDDING_STATE_PROVENANCE_REQUIRED_FIELDS:
        if canonical_name == "provenance_digest":
            continue
        if canonical_name not in fields:
            raise P01EmbeddingStateContractError(f"P01_FIELD_MISSING:{canonical_name}")
        raw = fields[canonical_name]
        canonical[canonical_name] = "" if raw is None else str(raw)
    attached = dict(fields)
    attached["provenance_digest"] = compute_p01_embedding_state_provenance_digest_v1(canonical)
    return attached


def _reject_coerced_embedding(*, field: str, raw: str) -> None:
    folded = _fold(raw)
    _ = field
    if raw in {EMBEDDED_NO, EMBEDDED_YES, EMBEDDED_CONDITIONAL, EMBEDDED_NOT_APPLICABLE} or (
        folded
        in {
            "notapplicable",
            "doesnotapply",
            "na",
            "n/a",
            "notembedded",
            "embedded",
        }
    ):
        raise P01EmbeddingStateContractError("P01_UNKNOWN_EMBEDDING_AUTO_NOT_EMBEDDED_FORBIDDEN")
    if folded in _ZERO_OR_ABSENCE_TOKENS or folded in {"0", "false"}:
        raise P01EmbeddingStateContractError("P01_ZERO_OR_ABSENCE_EMBEDDING_FORBIDDEN")
    if any(token in folded for token in _INFERRED_EMBEDDING_TOKENS):
        raise P01EmbeddingStateContractError("P01_EMBEDDING_INFERRED_FROM_LABEL_FORBIDDEN")


@dataclass(frozen=True)
class P01EmbeddingStateContractV1:
    """Typed immutable P01 broader embedding-state adjudication. Not a numeric instance."""

    p01_embedding_state_contract_id: str
    p01_embedding_state_contract_version: str
    parent_p01_equity_base_inclusion_contract_schema_class: str
    parent_p01_applicability_contract_schema_class: str
    parent_p01_term_set_and_unit_class_contract_schema_class: str
    parent_p01_term_contract_schema_class: str
    target_semantic_dimension_id: str
    policy_id: str
    term_id: str
    p01_embedded_state: str
    p01_embedded_state_resolved_status: str
    p01_embedding_rule: str
    p01_embedding_adjudication: str
    typed_embedding_state: str
    family_level_embedding_state: str
    member_level_embedding_state: str
    economic_overlap_state: str
    representational_nesting_state: str
    arithmetic_inclusion_state: str
    semantic_equivalence_state: str
    p01_overlap_state: str
    unknown_is_not_not_embedded: str
    unknown_is_not_embedded: str
    zero_does_not_prove_embedding: str
    absence_does_not_prove_embedding: str
    missing_input_fail_closed: str
    malformed_input_fail_closed: str
    term_set_unresolved_does_not_decide_embedding: str
    applicability_unresolved_does_not_decide_embedding: str
    unit_unresolved_does_not_decide_embedding: str
    equity_base_inclusion_unresolved_does_not_decide_broader_embedding: str
    u04_u05_u06_labels_do_not_decide_embedding: str
    equal_values_do_not_prove_embedding: str
    shared_source_does_not_prove_embedding: str
    separate_schema_does_not_prove_independence: str
    unknown_embedding_cannot_authorize_subtraction: str
    unknown_embedding_cannot_authorize_omission: str
    unknown_embedding_cannot_authorize_netting: str
    no_double_counting_permission: str
    rejected_embedding_inferences: str
    remaining_unresolved_semantics: str
    evidence_classification: str
    contradiction_state: str
    term_semantics_resolved_status: str
    unspecified_closed_status: str
    p01_embedding_state_contract_authority_effect: str
    provenance_digest: str

    def __post_init__(self) -> None:
        _validate_p01_embedding_state_contract_v1(self)

    def to_canonical_dict(self) -> dict[str, str]:
        values = {
            "p01_embedding_state_contract_id": self.p01_embedding_state_contract_id,
            "p01_embedding_state_contract_version": self.p01_embedding_state_contract_version,
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
            "p01_embedded_state": self.p01_embedded_state,
            "p01_embedded_state_resolved_status": self.p01_embedded_state_resolved_status,
            "p01_embedding_rule": self.p01_embedding_rule,
            "p01_embedding_adjudication": self.p01_embedding_adjudication,
            "typed_embedding_state": self.typed_embedding_state,
            "family_level_embedding_state": self.family_level_embedding_state,
            "member_level_embedding_state": self.member_level_embedding_state,
            "economic_overlap_state": self.economic_overlap_state,
            "representational_nesting_state": self.representational_nesting_state,
            "arithmetic_inclusion_state": self.arithmetic_inclusion_state,
            "semantic_equivalence_state": self.semantic_equivalence_state,
            "p01_overlap_state": self.p01_overlap_state,
            "unknown_is_not_not_embedded": self.unknown_is_not_not_embedded,
            "unknown_is_not_embedded": self.unknown_is_not_embedded,
            "zero_does_not_prove_embedding": self.zero_does_not_prove_embedding,
            "absence_does_not_prove_embedding": self.absence_does_not_prove_embedding,
            "missing_input_fail_closed": self.missing_input_fail_closed,
            "malformed_input_fail_closed": self.malformed_input_fail_closed,
            "term_set_unresolved_does_not_decide_embedding": (
                self.term_set_unresolved_does_not_decide_embedding
            ),
            "applicability_unresolved_does_not_decide_embedding": (
                self.applicability_unresolved_does_not_decide_embedding
            ),
            "unit_unresolved_does_not_decide_embedding": (
                self.unit_unresolved_does_not_decide_embedding
            ),
            "equity_base_inclusion_unresolved_does_not_decide_broader_embedding": (
                self.equity_base_inclusion_unresolved_does_not_decide_broader_embedding
            ),
            "u04_u05_u06_labels_do_not_decide_embedding": (
                self.u04_u05_u06_labels_do_not_decide_embedding
            ),
            "equal_values_do_not_prove_embedding": self.equal_values_do_not_prove_embedding,
            "shared_source_does_not_prove_embedding": self.shared_source_does_not_prove_embedding,
            "separate_schema_does_not_prove_independence": (
                self.separate_schema_does_not_prove_independence
            ),
            "unknown_embedding_cannot_authorize_subtraction": (
                self.unknown_embedding_cannot_authorize_subtraction
            ),
            "unknown_embedding_cannot_authorize_omission": (
                self.unknown_embedding_cannot_authorize_omission
            ),
            "unknown_embedding_cannot_authorize_netting": (
                self.unknown_embedding_cannot_authorize_netting
            ),
            "no_double_counting_permission": self.no_double_counting_permission,
            "rejected_embedding_inferences": self.rejected_embedding_inferences,
            "remaining_unresolved_semantics": self.remaining_unresolved_semantics,
            "evidence_classification": self.evidence_classification,
            "contradiction_state": self.contradiction_state,
            "term_semantics_resolved_status": self.term_semantics_resolved_status,
            "unspecified_closed_status": self.unspecified_closed_status,
            "p01_embedding_state_contract_authority_effect": (
                self.p01_embedding_state_contract_authority_effect
            ),
            "provenance_digest": self.provenance_digest,
        }
        return {key: values[key] for key in P01_EMBEDDING_STATE_PROVENANCE_REQUIRED_FIELDS}


def _validate_p01_embedding_state_contract_v1(contract: P01EmbeddingStateContractV1) -> None:
    if P01_EMBEDDING_STATE_CONTRACT_SCHEMA_PRESENT is not True:
        raise P01EmbeddingStateContractError("P01_EMBEDDING_STATE_CONTRACT_SCHEMA_PRESENT_REQUIRED")
    if P01_EMBEDDING_STATE_CONTRACT_RUNTIME_INSTANCE_PRESENT is True:
        raise P01EmbeddingStateContractError("P01_RUNTIME_INSTANCE_FORBIDDEN")
    if P01_EMBEDDED_STATE_RESOLVED is True:
        raise P01EmbeddingStateContractError("P01_EMBEDDED_STATE_RESOLVED_PIN_FORBIDDEN")
    if P01_EQUITY_BASE_INCLUSION_CONTRACT_SCHEMA_PRESENT is not True:
        raise P01EmbeddingStateContractError(
            "P01_EQUITY_BASE_INCLUSION_CONTRACT_SCHEMA_PRESENT_REQUIRED"
        )
    if P01_EQUITY_BASE_INCLUSION_CONTRACT_RUNTIME_INSTANCE_PRESENT is True:
        raise P01EmbeddingStateContractError("P01_PARENT_INCLUSION_RUNTIME_INSTANCE_FORBIDDEN")
    if P01_EQUITY_BASE_INCLUSION_RESOLVED is True:
        raise P01EmbeddingStateContractError("P01_EQUITY_BASE_INCLUSION_RESOLVED_PIN_FORBIDDEN")
    if P01_APPLICABILITY_CONTRACT_SCHEMA_PRESENT is not True:
        raise P01EmbeddingStateContractError("P01_APPLICABILITY_CONTRACT_SCHEMA_PRESENT_REQUIRED")
    if P01_APPLICABILITY_CONTRACT_RUNTIME_INSTANCE_PRESENT is True:
        raise P01EmbeddingStateContractError("P01_PARENT_APPLICABILITY_RUNTIME_INSTANCE_FORBIDDEN")
    if P01_APPLICABILITY_RESOLVED is True:
        raise P01EmbeddingStateContractError("P01_APPLICABILITY_RESOLVED_PIN_FORBIDDEN")
    if P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_SCHEMA_PRESENT is not True:
        raise P01EmbeddingStateContractError(
            "P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_SCHEMA_PRESENT_REQUIRED"
        )
    if P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_RUNTIME_INSTANCE_PRESENT is True:
        raise P01EmbeddingStateContractError("P01_PARENT_TERM_SET_RUNTIME_INSTANCE_FORBIDDEN")
    if P01_TERM_CONTRACT_SCHEMA_PRESENT is not True:
        raise P01EmbeddingStateContractError("P01_TERM_CONTRACT_SCHEMA_PRESENT_REQUIRED")
    if P01_TERM_CONTRACT_RUNTIME_INSTANCE_PRESENT is True:
        raise P01EmbeddingStateContractError("P01_PARENT_RUNTIME_INSTANCE_FORBIDDEN")
    if P01_TERM_SET_RESOLVED is True:
        raise P01EmbeddingStateContractError("P01_TERM_SET_RESOLVED_PIN_FORBIDDEN")
    if P01_VALUE_UNIT_CLASS_RESOLVED is True:
        raise P01EmbeddingStateContractError("P01_VALUE_UNIT_CLASS_RESOLVED_PIN_FORBIDDEN")
    if P01_TERM_SEMANTICS_RESOLVED is True:
        raise P01EmbeddingStateContractError("P01_TERM_SEMANTICS_RESOLVED_PIN_FORBIDDEN")
    if P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED is True:
        raise P01EmbeddingStateContractError(
            "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED_PIN_FORBIDDEN"
        )
    if RECONSTRUCTION_ALGEBRA_COMPLETE is True:
        raise P01EmbeddingStateContractError("P01_RECONSTRUCTION_ALGEBRA_COMPLETE_PIN_FORBIDDEN")
    if SOURCE_SELECTED is True or SOURCE_OBJECT_PRESENT is True:
        raise P01EmbeddingStateContractError("P01_SOURCE_SELECTION_FORBIDDEN")
    contract_id = _require_non_empty_str(
        field="p01_embedding_state_contract_id",
        raw=contract.p01_embedding_state_contract_id,
    )
    version = _require_non_empty_str(
        field="p01_embedding_state_contract_version",
        raw=contract.p01_embedding_state_contract_version,
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
    status = _require_non_empty_str(field="p01_embedded_state", raw=contract.p01_embedded_state)
    resolved = _require_non_empty_str(
        field="p01_embedded_state_resolved_status",
        raw=contract.p01_embedded_state_resolved_status,
    )
    rule = _require_non_empty_str(field="p01_embedding_rule", raw=contract.p01_embedding_rule)
    adjudication = _require_non_empty_str(
        field="p01_embedding_adjudication", raw=contract.p01_embedding_adjudication
    )
    typed_state = _require_non_empty_str(
        field="typed_embedding_state", raw=contract.typed_embedding_state
    )
    family_level = _require_non_empty_str(
        field="family_level_embedding_state", raw=contract.family_level_embedding_state
    )
    member_level = _require_non_empty_str(
        field="member_level_embedding_state", raw=contract.member_level_embedding_state
    )
    overlap_dimension = _require_non_empty_str(
        field="economic_overlap_state", raw=contract.economic_overlap_state
    )
    nesting = _require_non_empty_str(
        field="representational_nesting_state", raw=contract.representational_nesting_state
    )
    arithmetic = _require_non_empty_str(
        field="arithmetic_inclusion_state", raw=contract.arithmetic_inclusion_state
    )
    equivalence = _require_non_empty_str(
        field="semantic_equivalence_state", raw=contract.semantic_equivalence_state
    )
    overlap_pin = _require_non_empty_str(field="p01_overlap_state", raw=contract.p01_overlap_state)
    unknown_not_not_embedded = _require_non_empty_str(
        field="unknown_is_not_not_embedded", raw=contract.unknown_is_not_not_embedded
    )
    unknown_not_embedded = _require_non_empty_str(
        field="unknown_is_not_embedded", raw=contract.unknown_is_not_embedded
    )
    zero_flag = _require_non_empty_str(
        field="zero_does_not_prove_embedding", raw=contract.zero_does_not_prove_embedding
    )
    absence_flag = _require_non_empty_str(
        field="absence_does_not_prove_embedding",
        raw=contract.absence_does_not_prove_embedding,
    )
    missing_flag = _require_non_empty_str(
        field="missing_input_fail_closed", raw=contract.missing_input_fail_closed
    )
    malformed_flag = _require_non_empty_str(
        field="malformed_input_fail_closed", raw=contract.malformed_input_fail_closed
    )
    term_set_flag = _require_non_empty_str(
        field="term_set_unresolved_does_not_decide_embedding",
        raw=contract.term_set_unresolved_does_not_decide_embedding,
    )
    applicability_flag = _require_non_empty_str(
        field="applicability_unresolved_does_not_decide_embedding",
        raw=contract.applicability_unresolved_does_not_decide_embedding,
    )
    unit_flag = _require_non_empty_str(
        field="unit_unresolved_does_not_decide_embedding",
        raw=contract.unit_unresolved_does_not_decide_embedding,
    )
    inclusion_flag = _require_non_empty_str(
        field="equity_base_inclusion_unresolved_does_not_decide_broader_embedding",
        raw=contract.equity_base_inclusion_unresolved_does_not_decide_broader_embedding,
    )
    u_label_flag = _require_non_empty_str(
        field="u04_u05_u06_labels_do_not_decide_embedding",
        raw=contract.u04_u05_u06_labels_do_not_decide_embedding,
    )
    equal_flag = _require_non_empty_str(
        field="equal_values_do_not_prove_embedding",
        raw=contract.equal_values_do_not_prove_embedding,
    )
    source_flag = _require_non_empty_str(
        field="shared_source_does_not_prove_embedding",
        raw=contract.shared_source_does_not_prove_embedding,
    )
    schema_flag = _require_non_empty_str(
        field="separate_schema_does_not_prove_independence",
        raw=contract.separate_schema_does_not_prove_independence,
    )
    subtract_flag = _require_non_empty_str(
        field="unknown_embedding_cannot_authorize_subtraction",
        raw=contract.unknown_embedding_cannot_authorize_subtraction,
    )
    omit_flag = _require_non_empty_str(
        field="unknown_embedding_cannot_authorize_omission",
        raw=contract.unknown_embedding_cannot_authorize_omission,
    )
    net_flag = _require_non_empty_str(
        field="unknown_embedding_cannot_authorize_netting",
        raw=contract.unknown_embedding_cannot_authorize_netting,
    )
    double_count_flag = _require_non_empty_str(
        field="no_double_counting_permission", raw=contract.no_double_counting_permission
    )
    rejected = _require_non_empty_str(
        field="rejected_embedding_inferences", raw=contract.rejected_embedding_inferences
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
        field="p01_embedding_state_contract_authority_effect",
        raw=contract.p01_embedding_state_contract_authority_effect,
    )
    digest = _require_non_empty_str(field="provenance_digest", raw=contract.provenance_digest)
    if version != CONTRACT_VERSION:
        raise P01EmbeddingStateContractError("P01_CONTRACT_VERSION_MISMATCH")
    if parent_inclusion != PARENT_INCLUSION_CONTRACT_SCHEMA_CLASS:
        raise P01EmbeddingStateContractError("P01_PARENT_INCLUSION_CONTRACT_REFERENCE_MISMATCH")
    if parent_applicability != PARENT_APPLICABILITY_CONTRACT_SCHEMA_CLASS:
        raise P01EmbeddingStateContractError("P01_PARENT_APPLICABILITY_CONTRACT_REFERENCE_MISMATCH")
    if parent_term_set != PARENT_TERM_SET_CONTRACT_SCHEMA_CLASS:
        raise P01EmbeddingStateContractError("P01_PARENT_TERM_SET_CONTRACT_REFERENCE_MISMATCH")
    if parent_term != PARENT_TERM_CONTRACT_SCHEMA_CLASS:
        raise P01EmbeddingStateContractError("P01_PARENT_TERM_CONTRACT_REFERENCE_MISMATCH")
    if target != DIMENSION_ID:
        raise P01EmbeddingStateContractError("P01_TARGET_DIMENSION_MISMATCH")
    if policy_id != POLICY_ID:
        raise P01EmbeddingStateContractError("P01_POLICY_ID_MISMATCH")
    if term_id != TERM_ID:
        raise P01EmbeddingStateContractError("P01_TERM_ID_MISMATCH")
    _reject_coerced_embedding(field="p01_embedded_state", raw=status)
    if status in {
        TYPED_EMBEDDING_STATE_NOT_EMBEDDED,
        TYPED_EMBEDDING_STATE_FULLY_EMBEDDED,
        TYPED_EMBEDDING_STATE_PARTIALLY_EMBEDDED,
        TYPED_EMBEDDING_STATE_EMBEDDED_IN_EQUITY_BASE,
        TYPED_EMBEDDING_STATE_EMBEDDED_IN_U04,
        TYPED_EMBEDDING_STATE_EMBEDDED_IN_U05,
        TYPED_EMBEDDING_STATE_EMBEDDED_IN_U06,
        TYPED_EMBEDDING_STATE_EMBEDDED_IN_ANOTHER_TERM,
        TYPED_EMBEDDING_STATE_DEPENDS_ON_MEMBER_CLASS,
        TYPED_EMBEDDING_STATE_DEPENDS_ON_APPLICABILITY,
    }:
        raise P01EmbeddingStateContractError("P01_EMBEDDING_CANDIDATE_UNPROVEN")
    if status != P01_EMBEDDED_STATE:
        raise P01EmbeddingStateContractError("P01_EMBEDDED_STATE_MISMATCH")
    if resolved.lower() == "true":
        raise P01EmbeddingStateContractError("P01_EMBEDDED_STATE_RESOLVED_FORBIDDEN")
    if resolved != P01_EMBEDDED_STATE_RESOLVED_STATUS:
        raise P01EmbeddingStateContractError("P01_EMBEDDED_STATE_RESOLVED_STATUS_MISMATCH")
    _reject_coerced_embedding(field="p01_embedding_rule", raw=rule)
    if rule != P01_EMBEDDING_RULE:
        raise P01EmbeddingStateContractError("P01_EMBEDDING_RULE_MISMATCH")
    _reject_coerced_embedding(field="p01_embedding_adjudication", raw=adjudication)
    if adjudication != P01_EMBEDDING_ADJUDICATION:
        raise P01EmbeddingStateContractError("P01_EMBEDDING_ADJUDICATION_MISMATCH")
    if typed_state in {
        TYPED_EMBEDDING_STATE_NOT_EMBEDDED,
        TYPED_EMBEDDING_STATE_FULLY_EMBEDDED,
        TYPED_EMBEDDING_STATE_PARTIALLY_EMBEDDED,
        TYPED_EMBEDDING_STATE_EMBEDDED_IN_EQUITY_BASE,
        TYPED_EMBEDDING_STATE_EMBEDDED_IN_U04,
        TYPED_EMBEDDING_STATE_EMBEDDED_IN_U05,
        TYPED_EMBEDDING_STATE_EMBEDDED_IN_U06,
        TYPED_EMBEDDING_STATE_EMBEDDED_IN_ANOTHER_TERM,
        TYPED_EMBEDDING_STATE_DEPENDS_ON_MEMBER_CLASS,
        TYPED_EMBEDDING_STATE_DEPENDS_ON_APPLICABILITY,
        EMBEDDED_YES,
        EMBEDDED_NO,
        EMBEDDED_CONDITIONAL,
        EMBEDDED_NOT_APPLICABLE,
    }:
        raise P01EmbeddingStateContractError("P01_EMBEDDING_CANDIDATE_UNPROVEN")
    if typed_state != TYPED_EMBEDDING_STATE:
        raise P01EmbeddingStateContractError("P01_TYPED_EMBEDDING_STATE_MISMATCH")
    if family_level != FAMILY_LEVEL_EMBEDDING_STATE:
        raise P01EmbeddingStateContractError("P01_FAMILY_LEVEL_EMBEDDING_MUST_REMAIN_UNRESOLVED")
    if member_level != MEMBER_LEVEL_EMBEDDING_STATE:
        raise P01EmbeddingStateContractError("P01_MEMBER_LEVEL_EMBEDDING_MUST_REMAIN_UNRESOLVED")
    if overlap_dimension != ECONOMIC_OVERLAP_STATE:
        raise P01EmbeddingStateContractError("P01_ECONOMIC_OVERLAP_MUST_REMAIN_UNRESOLVED")
    if nesting != REPRESENTATIONAL_NESTING_STATE:
        raise P01EmbeddingStateContractError("P01_REPRESENTATIONAL_NESTING_MUST_REMAIN_UNRESOLVED")
    if arithmetic != ARITHMETIC_INCLUSION_STATE:
        raise P01EmbeddingStateContractError("P01_ARITHMETIC_INCLUSION_MUST_REMAIN_UNRESOLVED")
    if equivalence != SEMANTIC_EQUIVALENCE_STATE:
        raise P01EmbeddingStateContractError("P01_SEMANTIC_EQUIVALENCE_MUST_REMAIN_UNRESOLVED")
    if overlap_pin != P01_OVERLAP_STATE:
        raise P01EmbeddingStateContractError("P01_OVERLAP_STATE_MUST_REMAIN_UNCHANGED")
    if family_level == member_level == ECONOMIC_OVERLAP_STATE and family_level != "UNRESOLVED":
        raise P01EmbeddingStateContractError("P01_EMBEDDING_DIMENSIONS_COLLAPSED")
    if unknown_not_not_embedded.lower() != "true" or (
        unknown_not_not_embedded != UNKNOWN_IS_NOT_NOT_EMBEDDED
    ):
        raise P01EmbeddingStateContractError("P01_UNKNOWN_IS_NOT_NOT_EMBEDDED_REQUIRED")
    if unknown_not_embedded.lower() != "true" or unknown_not_embedded != UNKNOWN_IS_NOT_EMBEDDED:
        raise P01EmbeddingStateContractError("P01_UNKNOWN_IS_NOT_EMBEDDED_REQUIRED")
    if zero_flag.lower() != "true" or zero_flag != ZERO_DOES_NOT_PROVE_EMBEDDING:
        raise P01EmbeddingStateContractError("P01_ZERO_DOES_NOT_PROVE_EMBEDDING_REQUIRED")
    if absence_flag.lower() != "true" or absence_flag != ABSENCE_DOES_NOT_PROVE_EMBEDDING:
        raise P01EmbeddingStateContractError("P01_ABSENCE_DOES_NOT_PROVE_EMBEDDING_REQUIRED")
    if missing_flag.lower() != "true" or missing_flag != MISSING_INPUT_FAIL_CLOSED:
        raise P01EmbeddingStateContractError("P01_MISSING_INPUT_FAIL_CLOSED_REQUIRED")
    if malformed_flag.lower() != "true" or malformed_flag != MALFORMED_INPUT_FAIL_CLOSED:
        raise P01EmbeddingStateContractError("P01_MALFORMED_INPUT_FAIL_CLOSED_REQUIRED")
    if (
        term_set_flag.lower() != "true"
        or term_set_flag != TERM_SET_UNRESOLVED_DOES_NOT_DECIDE_EMBEDDING
    ):
        raise P01EmbeddingStateContractError("P01_TERM_SET_MUST_NOT_DECIDE_EMBEDDING")
    if (
        applicability_flag.lower() != "true"
        or applicability_flag != APPLICABILITY_UNRESOLVED_DOES_NOT_DECIDE_EMBEDDING
    ):
        raise P01EmbeddingStateContractError("P01_APPLICABILITY_MUST_NOT_DECIDE_EMBEDDING")
    if unit_flag.lower() != "true" or unit_flag != UNIT_UNRESOLVED_DOES_NOT_DECIDE_EMBEDDING:
        raise P01EmbeddingStateContractError("P01_UNIT_MUST_NOT_DECIDE_EMBEDDING")
    if (
        inclusion_flag.lower() != "true"
        or inclusion_flag != EQUITY_BASE_INCLUSION_UNRESOLVED_DOES_NOT_DECIDE_BROADER_EMBEDDING
    ):
        raise P01EmbeddingStateContractError("P01_INCLUSION_MUST_NOT_DECIDE_BROADER_EMBEDDING")
    if u_label_flag.lower() != "true" or u_label_flag != U04_U05_U06_LABELS_DO_NOT_DECIDE_EMBEDDING:
        raise P01EmbeddingStateContractError("P01_U04_U05_U06_MUST_NOT_DECIDE_EMBEDDING")
    if equal_flag.lower() != "true" or equal_flag != EQUAL_VALUES_DO_NOT_PROVE_EMBEDDING:
        raise P01EmbeddingStateContractError("P01_EQUAL_VALUES_MUST_NOT_PROVE_EMBEDDING")
    if source_flag.lower() != "true" or source_flag != SHARED_SOURCE_DOES_NOT_PROVE_EMBEDDING:
        raise P01EmbeddingStateContractError("P01_SHARED_SOURCE_MUST_NOT_PROVE_EMBEDDING")
    if schema_flag.lower() != "true" or schema_flag != SEPARATE_SCHEMA_DOES_NOT_PROVE_INDEPENDENCE:
        raise P01EmbeddingStateContractError("P01_SEPARATE_SCHEMA_MUST_NOT_PROVE_INDEPENDENCE")
    if (
        subtract_flag.lower() != "true"
        or subtract_flag != UNKNOWN_EMBEDDING_CANNOT_AUTHORIZE_SUBTRACTION
    ):
        raise P01EmbeddingStateContractError("P01_UNKNOWN_EMBEDDING_SUBTRACTION_FORBIDDEN")
    if omit_flag.lower() != "true" or omit_flag != UNKNOWN_EMBEDDING_CANNOT_AUTHORIZE_OMISSION:
        raise P01EmbeddingStateContractError("P01_UNKNOWN_EMBEDDING_OMISSION_FORBIDDEN")
    if net_flag.lower() != "true" or net_flag != UNKNOWN_EMBEDDING_CANNOT_AUTHORIZE_NETTING:
        raise P01EmbeddingStateContractError("P01_UNKNOWN_EMBEDDING_NETTING_FORBIDDEN")
    if double_count_flag.lower() != "true" or double_count_flag != NO_DOUBLE_COUNTING_PERMISSION:
        raise P01EmbeddingStateContractError("P01_NO_DOUBLE_COUNTING_PERMISSION_REQUIRED")
    if rejected != REJECTED_EMBEDDING_INFERENCES:
        raise P01EmbeddingStateContractError("P01_REJECTED_EMBEDDING_INFERENCES_MISMATCH")
    if remaining != REMAINING_UNRESOLVED_SEMANTICS:
        raise P01EmbeddingStateContractError("P01_REMAINING_UNRESOLVED_SEMANTICS_MISMATCH")
    if "P01_EMBEDDING_UNRESOLVED" not in remaining:
        raise P01EmbeddingStateContractError("P01_EMBEDDING_MUST_REMAIN_UNRESOLVED")
    if "P01_EQUITY_BASE_INCLUSION_UNRESOLVED" not in remaining:
        raise P01EmbeddingStateContractError("P01_EQUITY_BASE_INCLUSION_MUST_REMAIN_UNRESOLVED")
    if "P01_APPLICABILITY_UNSPECIFIED" not in remaining:
        raise P01EmbeddingStateContractError("P01_APPLICABILITY_MUST_REMAIN_UNSPECIFIED")
    if "P01_OVERLAP_WITH_U04_U05_UNRESOLVED" not in remaining:
        raise P01EmbeddingStateContractError("P01_OVERLAP_MUST_REMAIN_UNRESOLVED")
    if evidence != EVIDENCE_CLASSIFICATION:
        raise P01EmbeddingStateContractError("P01_EVIDENCE_CLASSIFICATION_MISMATCH")
    if contradiction != CONTRADICTION_NONE:
        raise P01EmbeddingStateContractError("P01_CONTRADICTION_STATUS_MISMATCH")
    if semantics_resolved.lower() == "true":
        raise P01EmbeddingStateContractError("P01_TERM_SEMANTICS_RESOLVED_FORBIDDEN")
    if semantics_resolved != TERM_SEMANTICS_RESOLVED_STATUS:
        raise P01EmbeddingStateContractError("P01_TERM_SEMANTICS_RESOLVED_STATUS_MISMATCH")
    if closed.lower() == "true":
        raise P01EmbeddingStateContractError(
            "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED_FORBIDDEN"
        )
    if closed != UNSPECIFIED_CLOSED_STATUS:
        raise P01EmbeddingStateContractError("P01_UNSPECIFIED_CLOSED_STATUS_MISMATCH")
    if effect != P01_EMBEDDING_STATE_CONTRACT_AUTHORITY_EFFECT or effect != AUTHORITY_EFFECT_NONE:
        raise P01EmbeddingStateContractError("P01_AUTHORITY_EFFECT_MUST_REMAIN_NONE")
    if P01_EQUITY_BASE_INCLUSION_CONTRACT_AUTHORITY_EFFECT != AUTHORITY_EFFECT_NONE:
        raise P01EmbeddingStateContractError("P01_PARENT_AUTHORITY_EFFECT_MUST_REMAIN_NONE")
    if P01_APPLICABILITY_CONTRACT_AUTHORITY_EFFECT != AUTHORITY_EFFECT_NONE:
        raise P01EmbeddingStateContractError("P01_PARENT_AUTHORITY_EFFECT_MUST_REMAIN_NONE")
    if EARLIEST_UNRESOLVED_ALGEBRA_TERM != "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED":
        raise P01EmbeddingStateContractError("P01_EARLIEST_ALGEBRA_TERM_DRIFT")
    if "U04_PENDING_ORDER_RESERVATION_INCLUSION_UNRESOLVED" not in UNRESOLVED_ALGEBRA_TERMS:
        raise P01EmbeddingStateContractError("P01_U04_MUST_REMAIN_UNRESOLVED")
    if "U05_LIABILITY_INCLUSION_OR_VALUE_UNRESOLVED" not in UNRESOLVED_ALGEBRA_TERMS:
        raise P01EmbeddingStateContractError("P01_U05_MUST_REMAIN_UNRESOLVED")
    if "U06_FEE_INCLUSION_UNRESOLVED" not in UNRESOLVED_ALGEBRA_TERMS:
        raise P01EmbeddingStateContractError("P01_U06_MUST_REMAIN_UNRESOLVED")
    parent_term_contract = build_p01_haircut_reserve_depletion_term_contract_v1(
        p01_term_contract_id="P01_EMBEDDING_STATE_PARENT_TERM_ALIGNMENT"
    )
    if parent_term_contract.embedded_state != PARENT_EMBEDDED_STATE:
        raise P01EmbeddingStateContractError("P01_PARENT_EMBEDDED_ALIGNMENT_MISMATCH")
    if parent_term_contract.embedded_state != EMBEDDED_UNRESOLVED:
        raise P01EmbeddingStateContractError("P01_PARENT_EMBEDDED_MUST_REMAIN_UNRESOLVED")
    if parent_term_contract.overlap_state != PARENT_OVERLAP_STATE:
        raise P01EmbeddingStateContractError("P01_PARENT_OVERLAP_MUST_REMAIN_UNCHANGED")
    parent_term_set_contract = build_p01_term_set_and_unit_class_contract_v1(
        p01_term_set_and_unit_class_contract_id="P01_EMBEDDING_STATE_PARENT_TERM_SET_ALIGNMENT"
    )
    if parent_term_set_contract.p01_term_set_resolved_status != "false":
        raise P01EmbeddingStateContractError("P01_PARENT_TERM_SET_RESOLVED_ALIGNMENT")
    if parent_term_set_contract.p01_value_unit_class_resolved_status != "false":
        raise P01EmbeddingStateContractError("P01_PARENT_UNIT_RESOLVED_ALIGNMENT")
    parent_applicability_contract = build_p01_applicability_contract_v1(
        p01_applicability_contract_id="P01_EMBEDDING_STATE_PARENT_APPLICABILITY_ALIGNMENT"
    )
    if parent_applicability_contract.p01_applicability_resolved_status != "false":
        raise P01EmbeddingStateContractError("P01_PARENT_APPLICABILITY_RESOLVED_ALIGNMENT")
    parent_inclusion_contract = build_p01_equity_base_inclusion_contract_v1(
        p01_equity_base_inclusion_contract_id="P01_EMBEDDING_STATE_PARENT_INCLUSION_ALIGNMENT"
    )
    if (
        parent_inclusion_contract.p01_equity_base_inclusion_status
        != P01_EQUITY_BASE_INCLUSION_STATUS
    ):
        raise P01EmbeddingStateContractError("P01_PARENT_INCLUSION_ALIGNMENT_MISMATCH")
    if parent_inclusion_contract.p01_equity_base_inclusion_resolved_status != "false":
        raise P01EmbeddingStateContractError("P01_PARENT_INCLUSION_RESOLVED_ALIGNMENT")
    algebra = build_reconstruction_algebra_contract_v1(
        algebra_contract_id="P01_EMBEDDING_STATE_ALGEBRA_ALIGNMENT"
    )
    p01_term = next(term for term in algebra.terms if term.term_id == TERM_ID)
    if p01_term.embedded_term_state != EMBEDDED_UNRESOLVED:
        raise P01EmbeddingStateContractError("P01_ALGEBRA_EMBEDDED_MUST_REMAIN_UNRESOLVED")
    if p01_term.embedded_term_state == EMBEDDED_NO:
        raise P01EmbeddingStateContractError("P01_NON_EMBEDDING_UNPROVEN")
    if algebra.algebra_completeness_status != "INCOMPLETE":
        raise P01EmbeddingStateContractError("P01_ALGEBRA_COMPLETENESS_ALIGNMENT")
    canonical = contract.to_canonical_dict()
    expected_digest = compute_p01_embedding_state_provenance_digest_v1(canonical)
    if not _SHA256_HEX.fullmatch(digest):
        raise P01EmbeddingStateContractError("P01_PROVENANCE_DIGEST_NOT_SHA256")
    if digest != expected_digest:
        raise P01EmbeddingStateContractError("P01_PROVENANCE_DIGEST_MISMATCH")
    _ = contract_id


def build_p01_embedding_state_contract_v1(**fields: Any) -> P01EmbeddingStateContractV1:
    """Construct the typed P01 broader embedding-state contract. Does not resolve P01."""

    payload = dict(fields)
    defaults = {
        "p01_embedding_state_contract_version": CONTRACT_VERSION,
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
        "p01_embedded_state": P01_EMBEDDED_STATE,
        "p01_embedded_state_resolved_status": P01_EMBEDDED_STATE_RESOLVED_STATUS,
        "p01_embedding_rule": P01_EMBEDDING_RULE,
        "p01_embedding_adjudication": P01_EMBEDDING_ADJUDICATION,
        "typed_embedding_state": TYPED_EMBEDDING_STATE,
        "family_level_embedding_state": FAMILY_LEVEL_EMBEDDING_STATE,
        "member_level_embedding_state": MEMBER_LEVEL_EMBEDDING_STATE,
        "economic_overlap_state": ECONOMIC_OVERLAP_STATE,
        "representational_nesting_state": REPRESENTATIONAL_NESTING_STATE,
        "arithmetic_inclusion_state": ARITHMETIC_INCLUSION_STATE,
        "semantic_equivalence_state": SEMANTIC_EQUIVALENCE_STATE,
        "p01_overlap_state": P01_OVERLAP_STATE,
        "unknown_is_not_not_embedded": UNKNOWN_IS_NOT_NOT_EMBEDDED,
        "unknown_is_not_embedded": UNKNOWN_IS_NOT_EMBEDDED,
        "zero_does_not_prove_embedding": ZERO_DOES_NOT_PROVE_EMBEDDING,
        "absence_does_not_prove_embedding": ABSENCE_DOES_NOT_PROVE_EMBEDDING,
        "missing_input_fail_closed": MISSING_INPUT_FAIL_CLOSED,
        "malformed_input_fail_closed": MALFORMED_INPUT_FAIL_CLOSED,
        "term_set_unresolved_does_not_decide_embedding": (
            TERM_SET_UNRESOLVED_DOES_NOT_DECIDE_EMBEDDING
        ),
        "applicability_unresolved_does_not_decide_embedding": (
            APPLICABILITY_UNRESOLVED_DOES_NOT_DECIDE_EMBEDDING
        ),
        "unit_unresolved_does_not_decide_embedding": UNIT_UNRESOLVED_DOES_NOT_DECIDE_EMBEDDING,
        "equity_base_inclusion_unresolved_does_not_decide_broader_embedding": (
            EQUITY_BASE_INCLUSION_UNRESOLVED_DOES_NOT_DECIDE_BROADER_EMBEDDING
        ),
        "u04_u05_u06_labels_do_not_decide_embedding": U04_U05_U06_LABELS_DO_NOT_DECIDE_EMBEDDING,
        "equal_values_do_not_prove_embedding": EQUAL_VALUES_DO_NOT_PROVE_EMBEDDING,
        "shared_source_does_not_prove_embedding": SHARED_SOURCE_DOES_NOT_PROVE_EMBEDDING,
        "separate_schema_does_not_prove_independence": (
            SEPARATE_SCHEMA_DOES_NOT_PROVE_INDEPENDENCE
        ),
        "unknown_embedding_cannot_authorize_subtraction": (
            UNKNOWN_EMBEDDING_CANNOT_AUTHORIZE_SUBTRACTION
        ),
        "unknown_embedding_cannot_authorize_omission": (
            UNKNOWN_EMBEDDING_CANNOT_AUTHORIZE_OMISSION
        ),
        "unknown_embedding_cannot_authorize_netting": UNKNOWN_EMBEDDING_CANNOT_AUTHORIZE_NETTING,
        "no_double_counting_permission": NO_DOUBLE_COUNTING_PERMISSION,
        "rejected_embedding_inferences": REJECTED_EMBEDDING_INFERENCES,
        "remaining_unresolved_semantics": REMAINING_UNRESOLVED_SEMANTICS,
        "evidence_classification": EVIDENCE_CLASSIFICATION,
        "contradiction_state": CONTRADICTION_NONE,
        "term_semantics_resolved_status": TERM_SEMANTICS_RESOLVED_STATUS,
        "unspecified_closed_status": UNSPECIFIED_CLOSED_STATUS,
        "p01_embedding_state_contract_authority_effect": AUTHORITY_EFFECT_NONE,
    }
    for key, value in defaults.items():
        payload.setdefault(key, value)
    missing = [name for name in _VECTOR_FIELDS if name not in payload]
    if missing:
        raise P01EmbeddingStateContractError("P01_FIELD_MISSING:" + ",".join(missing))
    attached = attach_p01_embedding_state_provenance_digest_v1(payload)
    return P01EmbeddingStateContractV1(
        **{name: attached[name] for name in P01_EMBEDDING_STATE_PROVENANCE_REQUIRED_FIELDS}
    )


def reject_p01_unknown_embedding_as_not_embedded_v1(*, embedded_state: str) -> None:
    """Unknown P01 broader embedding is not NOT_EMBEDDED."""

    _reject_coerced_embedding(field="p01_embedded_state", raw=embedded_state)
    if embedded_state in {
        EMBEDDED_NO,
        EMBEDDED_YES,
        TYPED_EMBEDDING_STATE_NOT_EMBEDDED,
        TYPED_EMBEDDING_STATE_FULLY_EMBEDDED,
    }:
        raise P01EmbeddingStateContractError("P01_UNKNOWN_EMBEDDING_AUTO_NOT_EMBEDDED_FORBIDDEN")
    raise P01EmbeddingStateContractError("P01_EMBEDDED_STATE_MISMATCH")


def reject_p01_zero_or_absence_as_embedding_v1(*, embedded_state: str) -> None:
    """Zero or term absence is not P01 embedding or non-embedding."""

    _reject_coerced_embedding(field="p01_embedded_state", raw=embedded_state)
    raise P01EmbeddingStateContractError("P01_EMBEDDED_STATE_MISMATCH")


def reject_p01_embedding_inferred_from_u04_u05_u06_schema_or_venue_v1(
    *, embedding_rule: str
) -> None:
    """U04/U05/U06, separate schema, or venue-raw state is not a P01 embedding rule."""

    _reject_coerced_embedding(field="p01_embedding_rule", raw=embedding_rule)
    raise P01EmbeddingStateContractError("P01_EMBEDDING_RULE_MISMATCH")


def reject_p01_equal_values_or_shared_source_as_embedding_v1(*, embedding_rule: str) -> None:
    """Equal numeric values or shared source/provenance do not prove embedding."""

    _reject_coerced_embedding(field="p01_embedding_rule", raw=embedding_rule)
    raise P01EmbeddingStateContractError("P01_EMBEDDING_RULE_MISMATCH")


def reject_p01_unknown_embedding_as_subtraction_omission_or_netting_v1(
    *, embedded_state: str, requested_action: str
) -> None:
    """Unknown P01 embedding cannot authorize subtraction, omission, or netting."""

    _reject_coerced_embedding(field="p01_embedded_state", raw=embedded_state)
    folded = _fold(requested_action)
    if folded in _SUBTRACTION_OMISSION_OR_NETTING_TOKENS:
        raise P01EmbeddingStateContractError(
            "P01_UNKNOWN_EMBEDDING_SUBTRACTION_OMISSION_OR_NETTING_FORBIDDEN"
        )
    raise P01EmbeddingStateContractError("P01_EMBEDDED_STATE_MISMATCH")


def reject_p01_u06_distinctness_as_non_embedding_v1(*, embedding_rule: str) -> None:
    """U06 accrued-fee distinctness does not prove P01 is not embedded in U06."""

    _reject_coerced_embedding(field="p01_embedding_rule", raw=embedding_rule)
    raise P01EmbeddingStateContractError("P01_EMBEDDING_RULE_MISMATCH")
