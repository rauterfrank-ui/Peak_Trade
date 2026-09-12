"""Typed P01 equity-base inclusion adjudication contract.

Encodes the forensic result that canonical evidence does not prove whether
P01 is included in EQUITY_BASE, excluded from it, conditionally included,
partially embedded, or independently subtracted. Unknown remains
fail-closed. Schema presence is not P01 resolution.

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
    P01_EQUITY_BASE_INCLUSION_CONTRACT_AUTHORITY_EFFECT,
    P01_EQUITY_BASE_INCLUSION_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_EQUITY_BASE_INCLUSION_CONTRACT_SCHEMA_PRESENT,
    P01_EQUITY_BASE_INCLUSION_PROVENANCE_REQUIRED_FIELDS,
    P01_EQUITY_BASE_INCLUSION_RESOLVED,
    P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED,
    P01_TERM_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_TERM_CONTRACT_SCHEMA_PRESENT,
    P01_TERM_SEMANTICS_RESOLVED,
    P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_SCHEMA_PRESENT,
    P01_VALUE_UNIT_CLASS_RESOLVED,
    RECONSTRUCTION_ALGEBRA_COMPLETE,
    SOURCE_OBJECT_PRESENT,
    SOURCE_SELECTED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_applicability_contract_v1 import (
    P01_APPLICABILITY_STATUS,
    REMAINING_UNRESOLVED_SEMANTICS as PARENT_REMAINING_UNRESOLVED_SEMANTICS,
    SCHEMA_CLASS as P01_APPLICABILITY_SCHEMA_CLASS,
    build_p01_applicability_contract_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_haircut_reserve_depletion_term_contract_v1 import (
    EMBEDDED_STATE as PARENT_EMBEDDED_STATE,
    INCLUSION_STATE as PARENT_INCLUSION_STATE,
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
    EMBEDDED_UNRESOLVED,
    INCLUSION_IN_BASE,
    INCLUSION_NOT_APPLICABLE,
    INCLUSION_NOT_IN_BASE,
    INCLUSION_UNRESOLVED,
    NUMERIC_MISSING,
    NUMERIC_PRESENT_ZERO,
    ROLE_REDUCTION_ONLY_UNSPECIFIED,
    TERM_EQUITY_BASE,
    TERM_FEE,
    TERM_LIABILITY,
    TERM_P01_HAIRCUT_RESERVE_DEPLETION,
    TERM_PENDING_ORDER_RESERVATION,
    UNRESOLVED_ALGEBRA_TERMS,
    build_reconstruction_algebra_contract_v1,
)

SCHEMA_CLASS = "P01_EQUITY_BASE_INCLUSION_CONTRACT_V1"
CONTRACT_VERSION = "v1"
POLICY_ID = "P01"
TERM_ID = TERM_P01_HAIRCUT_RESERVE_DEPLETION
PARENT_APPLICABILITY_CONTRACT_SCHEMA_CLASS = P01_APPLICABILITY_SCHEMA_CLASS
PARENT_TERM_SET_CONTRACT_SCHEMA_CLASS = P01_TERM_SET_SCHEMA_CLASS
PARENT_TERM_CONTRACT_SCHEMA_CLASS = P01_TERM_SCHEMA_CLASS
P01_EQUITY_BASE_INCLUSION_STATUS = INCLUSION_UNRESOLVED
P01_EQUITY_BASE_INCLUSION_RESOLVED_STATUS = "false"
P01_EQUITY_BASE_INCLUSION_RULE = "UNSPECIFIED_FAIL_CLOSED"
P01_EQUITY_BASE_INCLUSION_ADJUDICATION = "UNKNOWN_RELATIONSHIP_FAIL_CLOSED"
TYPED_INCLUSION_STATE_UNKNOWN = "UNKNOWN"
TYPED_INCLUSION_STATE_INCLUDED = "INCLUDED_IN_EQUITY_BASE"
TYPED_INCLUSION_STATE_EXCLUDED = "EXCLUDED_FROM_EQUITY_BASE"
TYPED_INCLUSION_STATE_CONDITIONAL = "CONDITIONALLY_INCLUDED"
TYPED_INCLUSION_STATE_PARTIAL = "PARTIALLY_EMBEDDED"
TYPED_INCLUSION_STATE_INDEPENDENT = "INDEPENDENT_REDUCTION"
TYPED_INCLUSION_STATE = TYPED_INCLUSION_STATE_UNKNOWN
UNKNOWN_IS_NOT_EXCLUDED = "true"
ZERO_IS_NOT_EMBEDDED_OR_EXCLUDED = "true"
ABSENCE_IS_NOT_NOT_EMBEDDED = "true"
MISSING_INPUT_FAIL_CLOSED = "true"
MALFORMED_INPUT_FAIL_CLOSED = "true"
TERM_SET_UNRESOLVED_DOES_NOT_DECIDE_INCLUSION = "true"
APPLICABILITY_UNRESOLVED_DOES_NOT_DECIDE_INCLUSION = "true"
UNIT_UNRESOLVED_DOES_NOT_DECIDE_INCLUSION = "true"
SEPARATE_SCHEMA_DOES_NOT_PROVE_INDEPENDENT_DEDUCTION = "true"
UNKNOWN_INCLUSION_CANNOT_AUTHORIZE_SUBTRACTION = "true"
UNKNOWN_INCLUSION_CANNOT_AUTHORIZE_OMISSION = "true"
NO_DOUBLE_COUNTING_PERMISSION = "true"
AUTHORITY_EFFECT_NONE = "NONE"
TERM_SEMANTICS_RESOLVED_STATUS = "false"
UNSPECIFIED_CLOSED_STATUS = "false"
REMAINING_UNRESOLVED_SEMANTICS = PARENT_REMAINING_UNRESOLVED_SEMANTICS
REJECTED_INCLUSION_INFERENCES = (
    "INCLUDED_IN_EQUITY_BASE_UNPROVEN;"
    "EXCLUDED_FROM_EQUITY_BASE_UNPROVEN;"
    "CONDITIONALLY_INCLUDED_UNPROVEN;"
    "PARTIALLY_EMBEDDED_UNPROVEN;"
    "INDEPENDENT_REDUCTION_UNPROVEN;"
    "REDUCTION_ONLY_DOES_NOT_PROVE_SEPARATE_FROM_EQUITY_BASE;"
    "RESERVE_DOES_NOT_PROVE_EXCLUDED;"
    "PARENT_DIMENSION_USDC_IS_NOT_MONETARY_INCLUSION;"
    "MISSING_CODE_IS_NOT_EXCLUDED;"
    "VALUE_ZERO_IS_NOT_EMBEDDED_OR_EXCLUDED;"
    "TERM_ABSENCE_IS_NOT_NOT_EMBEDDED;"
    "SEPARATE_SCHEMA_FIELD_IS_NOT_INDEPENDENT_DEDUCTION;"
    "ARITHMETIC_COMPATIBILITY_IS_NOT_NORMATIVE_INCLUSION;"
    "U02_U03_IN_BASE_TREATMENT_IS_NOT_P01_INCLUSION;"
    "U04_U05_U06_STATE_IS_NOT_P01_INCLUSION;"
    "VENUE_RAW_FIELD_IS_NOT_P01_INCLUSION;"
    "UNRESOLVED_TERM_SET_DOES_NOT_DECIDE_INCLUSION;"
    "UNRESOLVED_APPLICABILITY_DOES_NOT_DECIDE_INCLUSION;"
    "UNRESOLVED_UNIT_DOES_NOT_DECIDE_INCLUSION;"
    "UNKNOWN_INCLUSION_CANNOT_AUTHORIZE_SUBTRACTION_OR_OMISSION;"
    "OPTIONAL_DISABLED_INACTIVE_SAFE_OMITTED_DEFAULT_FALSE_FORBIDDEN"
)
EVIDENCE_CLASSIFICATION = (
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_T_P01_REDUCTION_ONLY_UNSPECIFIED_FAIL_CLOSED;"
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_AA_P01_INCLUSION_UNRESOLVED;"
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_AB_P01_EQUITY_BASE_INCLUSION_UNRESOLVED;"
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_AD_WHETHER_P01_INSIDE_EQUITY_BASE_UNPROVEN;"
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_T_U02_U03_IN_EQUITY_BASE_ONLY_NOT_P01;"
    "FORENSIC_EVIDENCE=SRC_RISK_HAS_NO_P01_HAIRCUT_IMPLEMENTATION;"
    "FORENSIC_EVIDENCE=ALGEBRA_LISTS_P01_AS_SEPARATE_SLOT_NOT_INCLUSION_PROOF;"
    "FORENSIC_EVIDENCE=NO_PRODUCTIVE_P01_SUBTRACTION_OR_EMBEDDING_RULE;"
    "HISTORICAL_STATE=11_2_1_N_HAIRCUTS_RESERVE_DEPLETION_FROZEN_PENDING_OWNER_POLICY_SUPERSEDED;"
    "STRUCTURAL_REUSE_ONLY=P01_APPLICABILITY_CONTRACT_V1;"
    "NAVIGATION=MAP_OF_TRUTH_NON_SSOT;"
    "REJECTED=INCLUDED_EXCLUDED_CONDITIONAL_PARTIAL_INDEPENDENT_U04_U05_U06_VENUE_ZERO_SCHEMA;"
    "UNRESOLVED=P01_EQUITY_BASE_INCLUSION_RELATIONSHIP"
)
_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")
_INFERRED_INCLUSION_TOKENS: tuple[str, ...] = (
    "includedinequitybase",
    "excludedfromequitybase",
    "conditionallyincluded",
    "partiallyembedded",
    "independentreduction",
    "included",
    "excluded",
    "independent",
    "embedded",
    "partial",
    "notinbase",
    "inbase",
    "notapplicable",
    "doesnotapply",
    "notembedded",
    "reductiononly",
    "reserve",
    "optional",
    "disabled",
    "inactive",
    "omitted",
    "safe",
    "separateschema",
    "separateschemafield",
    NUMERIC_PRESENT_ZERO.lower().replace("_", ""),
    NUMERIC_MISSING.lower(),
    ROLE_REDUCTION_ONLY_UNSPECIFIED.lower().replace("_", ""),
    TERM_EQUITY_BASE.lower().replace("_", ""),
    TERM_PENDING_ORDER_RESERVATION.lower().replace("_", ""),
    TERM_LIABILITY.lower(),
    TERM_FEE.lower(),
    "u04",
    "u05",
    "u06",
    "u02",
    "u03",
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
_SUBTRACTION_OR_OMISSION_TOKENS: tuple[str, ...] = (
    "subtract",
    "subtraction",
    "deduct",
    "deduction",
    "omit",
    "omission",
    "ignore",
    "skip",
)
_VECTOR_FIELDS: tuple[str, ...] = tuple(
    name
    for name in P01_EQUITY_BASE_INCLUSION_PROVENANCE_REQUIRED_FIELDS
    if name != "provenance_digest"
)


class P01EquityBaseInclusionContractError(ValueError):
    """Fail-closed P01 equity-base inclusion contract violation."""


def _fold(value: str) -> str:
    return str(value or "").strip().lower().replace("_", "").replace("-", "")


def _require_non_empty_str(*, field: str, raw: Any) -> str:
    if raw is None:
        raise P01EquityBaseInclusionContractError(f"P01_FIELD_MISSING:{field}")
    if isinstance(raw, bool) or not isinstance(raw, str):
        raise P01EquityBaseInclusionContractError(f"P01_FIELD_NOT_STRING:{field}")
    text = raw.strip()
    if text == "" or text != raw:
        raise P01EquityBaseInclusionContractError(f"P01_FIELD_MISSING:{field}")
    return text


def _sha256_hex(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _canonical_json(payload: Mapping[str, str]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_p01_equity_base_inclusion_provenance_digest_v1(canonical: Mapping[str, str]) -> str:
    payload = {
        key: canonical[key]
        for key in P01_EQUITY_BASE_INCLUSION_PROVENANCE_REQUIRED_FIELDS
        if key != "provenance_digest"
    }
    return _sha256_hex(_canonical_json(payload))


def attach_p01_equity_base_inclusion_provenance_digest_v1(
    fields: Mapping[str, Any],
) -> dict[str, Any]:
    canonical: dict[str, str] = {}
    for canonical_name in P01_EQUITY_BASE_INCLUSION_PROVENANCE_REQUIRED_FIELDS:
        if canonical_name == "provenance_digest":
            continue
        if canonical_name not in fields:
            raise P01EquityBaseInclusionContractError(f"P01_FIELD_MISSING:{canonical_name}")
        raw = fields[canonical_name]
        canonical[canonical_name] = "" if raw is None else str(raw)
    attached = dict(fields)
    attached["provenance_digest"] = compute_p01_equity_base_inclusion_provenance_digest_v1(
        canonical
    )
    return attached


def _reject_coerced_inclusion(*, field: str, raw: str) -> None:
    folded = _fold(raw)
    _ = field
    if raw in {INCLUSION_NOT_APPLICABLE, INCLUSION_IN_BASE, INCLUSION_NOT_IN_BASE} or folded in {
        "notapplicable",
        "doesnotapply",
        "na",
        "n/a",
        "inbase",
        "notinbase",
    }:
        raise P01EquityBaseInclusionContractError("P01_UNKNOWN_INCLUSION_AUTO_EXCLUDED_FORBIDDEN")
    if folded in _ZERO_OR_ABSENCE_TOKENS or folded in {"0", "false"}:
        raise P01EquityBaseInclusionContractError("P01_ZERO_OR_ABSENCE_INCLUSION_FORBIDDEN")
    if any(token in folded for token in _INFERRED_INCLUSION_TOKENS):
        raise P01EquityBaseInclusionContractError("P01_INCLUSION_INFERRED_FROM_LABEL_FORBIDDEN")


@dataclass(frozen=True)
class P01EquityBaseInclusionContractV1:
    """Typed immutable P01 equity-base inclusion adjudication. Not a numeric instance."""

    p01_equity_base_inclusion_contract_id: str
    p01_equity_base_inclusion_contract_version: str
    parent_p01_applicability_contract_schema_class: str
    parent_p01_term_set_and_unit_class_contract_schema_class: str
    parent_p01_term_contract_schema_class: str
    target_semantic_dimension_id: str
    policy_id: str
    term_id: str
    p01_equity_base_inclusion_status: str
    p01_equity_base_inclusion_resolved_status: str
    p01_equity_base_inclusion_rule: str
    p01_equity_base_inclusion_adjudication: str
    typed_inclusion_state: str
    unknown_is_not_excluded: str
    zero_is_not_embedded_or_excluded: str
    absence_is_not_not_embedded: str
    missing_input_fail_closed: str
    malformed_input_fail_closed: str
    term_set_unresolved_does_not_decide_inclusion: str
    applicability_unresolved_does_not_decide_inclusion: str
    unit_unresolved_does_not_decide_inclusion: str
    separate_schema_does_not_prove_independent_deduction: str
    unknown_inclusion_cannot_authorize_subtraction: str
    unknown_inclusion_cannot_authorize_omission: str
    no_double_counting_permission: str
    rejected_inclusion_inferences: str
    remaining_unresolved_semantics: str
    evidence_classification: str
    contradiction_state: str
    term_semantics_resolved_status: str
    unspecified_closed_status: str
    p01_equity_base_inclusion_contract_authority_effect: str
    provenance_digest: str

    def __post_init__(self) -> None:
        _validate_p01_equity_base_inclusion_contract_v1(self)

    def to_canonical_dict(self) -> dict[str, str]:
        values = {
            "p01_equity_base_inclusion_contract_id": self.p01_equity_base_inclusion_contract_id,
            "p01_equity_base_inclusion_contract_version": (
                self.p01_equity_base_inclusion_contract_version
            ),
            "parent_p01_applicability_contract_schema_class": (
                self.parent_p01_applicability_contract_schema_class
            ),
            "parent_p01_term_set_and_unit_class_contract_schema_class": (
                self.parent_p01_term_set_and_unit_class_contract_schema_class
            ),
            "parent_p01_term_contract_schema_class": (self.parent_p01_term_contract_schema_class),
            "target_semantic_dimension_id": self.target_semantic_dimension_id,
            "policy_id": self.policy_id,
            "term_id": self.term_id,
            "p01_equity_base_inclusion_status": self.p01_equity_base_inclusion_status,
            "p01_equity_base_inclusion_resolved_status": (
                self.p01_equity_base_inclusion_resolved_status
            ),
            "p01_equity_base_inclusion_rule": self.p01_equity_base_inclusion_rule,
            "p01_equity_base_inclusion_adjudication": (self.p01_equity_base_inclusion_adjudication),
            "typed_inclusion_state": self.typed_inclusion_state,
            "unknown_is_not_excluded": self.unknown_is_not_excluded,
            "zero_is_not_embedded_or_excluded": self.zero_is_not_embedded_or_excluded,
            "absence_is_not_not_embedded": self.absence_is_not_not_embedded,
            "missing_input_fail_closed": self.missing_input_fail_closed,
            "malformed_input_fail_closed": self.malformed_input_fail_closed,
            "term_set_unresolved_does_not_decide_inclusion": (
                self.term_set_unresolved_does_not_decide_inclusion
            ),
            "applicability_unresolved_does_not_decide_inclusion": (
                self.applicability_unresolved_does_not_decide_inclusion
            ),
            "unit_unresolved_does_not_decide_inclusion": (
                self.unit_unresolved_does_not_decide_inclusion
            ),
            "separate_schema_does_not_prove_independent_deduction": (
                self.separate_schema_does_not_prove_independent_deduction
            ),
            "unknown_inclusion_cannot_authorize_subtraction": (
                self.unknown_inclusion_cannot_authorize_subtraction
            ),
            "unknown_inclusion_cannot_authorize_omission": (
                self.unknown_inclusion_cannot_authorize_omission
            ),
            "no_double_counting_permission": self.no_double_counting_permission,
            "rejected_inclusion_inferences": self.rejected_inclusion_inferences,
            "remaining_unresolved_semantics": self.remaining_unresolved_semantics,
            "evidence_classification": self.evidence_classification,
            "contradiction_state": self.contradiction_state,
            "term_semantics_resolved_status": self.term_semantics_resolved_status,
            "unspecified_closed_status": self.unspecified_closed_status,
            "p01_equity_base_inclusion_contract_authority_effect": (
                self.p01_equity_base_inclusion_contract_authority_effect
            ),
            "provenance_digest": self.provenance_digest,
        }
        return {key: values[key] for key in P01_EQUITY_BASE_INCLUSION_PROVENANCE_REQUIRED_FIELDS}


def _validate_p01_equity_base_inclusion_contract_v1(
    contract: P01EquityBaseInclusionContractV1,
) -> None:
    if P01_EQUITY_BASE_INCLUSION_CONTRACT_SCHEMA_PRESENT is not True:
        raise P01EquityBaseInclusionContractError(
            "P01_EQUITY_BASE_INCLUSION_CONTRACT_SCHEMA_PRESENT_REQUIRED"
        )
    if P01_EQUITY_BASE_INCLUSION_CONTRACT_RUNTIME_INSTANCE_PRESENT is True:
        raise P01EquityBaseInclusionContractError("P01_RUNTIME_INSTANCE_FORBIDDEN")
    if P01_EQUITY_BASE_INCLUSION_RESOLVED is True:
        raise P01EquityBaseInclusionContractError(
            "P01_EQUITY_BASE_INCLUSION_RESOLVED_PIN_FORBIDDEN"
        )
    if P01_APPLICABILITY_CONTRACT_SCHEMA_PRESENT is not True:
        raise P01EquityBaseInclusionContractError(
            "P01_APPLICABILITY_CONTRACT_SCHEMA_PRESENT_REQUIRED"
        )
    if P01_APPLICABILITY_CONTRACT_RUNTIME_INSTANCE_PRESENT is True:
        raise P01EquityBaseInclusionContractError(
            "P01_PARENT_APPLICABILITY_RUNTIME_INSTANCE_FORBIDDEN"
        )
    if P01_APPLICABILITY_RESOLVED is True:
        raise P01EquityBaseInclusionContractError("P01_APPLICABILITY_RESOLVED_PIN_FORBIDDEN")
    if P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_SCHEMA_PRESENT is not True:
        raise P01EquityBaseInclusionContractError(
            "P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_SCHEMA_PRESENT_REQUIRED"
        )
    if P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_RUNTIME_INSTANCE_PRESENT is True:
        raise P01EquityBaseInclusionContractError("P01_PARENT_TERM_SET_RUNTIME_INSTANCE_FORBIDDEN")
    if P01_TERM_CONTRACT_SCHEMA_PRESENT is not True:
        raise P01EquityBaseInclusionContractError("P01_TERM_CONTRACT_SCHEMA_PRESENT_REQUIRED")
    if P01_TERM_CONTRACT_RUNTIME_INSTANCE_PRESENT is True:
        raise P01EquityBaseInclusionContractError("P01_PARENT_RUNTIME_INSTANCE_FORBIDDEN")
    if P01_VALUE_UNIT_CLASS_RESOLVED is True:
        raise P01EquityBaseInclusionContractError("P01_VALUE_UNIT_CLASS_RESOLVED_PIN_FORBIDDEN")
    if P01_TERM_SEMANTICS_RESOLVED is True:
        raise P01EquityBaseInclusionContractError("P01_TERM_SEMANTICS_RESOLVED_PIN_FORBIDDEN")
    if P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED is True:
        raise P01EquityBaseInclusionContractError(
            "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED_PIN_FORBIDDEN"
        )
    if RECONSTRUCTION_ALGEBRA_COMPLETE is True:
        raise P01EquityBaseInclusionContractError(
            "P01_RECONSTRUCTION_ALGEBRA_COMPLETE_PIN_FORBIDDEN"
        )
    if SOURCE_SELECTED is True or SOURCE_OBJECT_PRESENT is True:
        raise P01EquityBaseInclusionContractError("P01_SOURCE_SELECTION_FORBIDDEN")
    contract_id = _require_non_empty_str(
        field="p01_equity_base_inclusion_contract_id",
        raw=contract.p01_equity_base_inclusion_contract_id,
    )
    version = _require_non_empty_str(
        field="p01_equity_base_inclusion_contract_version",
        raw=contract.p01_equity_base_inclusion_contract_version,
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
    status = _require_non_empty_str(
        field="p01_equity_base_inclusion_status",
        raw=contract.p01_equity_base_inclusion_status,
    )
    resolved = _require_non_empty_str(
        field="p01_equity_base_inclusion_resolved_status",
        raw=contract.p01_equity_base_inclusion_resolved_status,
    )
    rule = _require_non_empty_str(
        field="p01_equity_base_inclusion_rule", raw=contract.p01_equity_base_inclusion_rule
    )
    adjudication = _require_non_empty_str(
        field="p01_equity_base_inclusion_adjudication",
        raw=contract.p01_equity_base_inclusion_adjudication,
    )
    typed_state = _require_non_empty_str(
        field="typed_inclusion_state", raw=contract.typed_inclusion_state
    )
    unknown_flag = _require_non_empty_str(
        field="unknown_is_not_excluded", raw=contract.unknown_is_not_excluded
    )
    zero_flag = _require_non_empty_str(
        field="zero_is_not_embedded_or_excluded",
        raw=contract.zero_is_not_embedded_or_excluded,
    )
    absence_flag = _require_non_empty_str(
        field="absence_is_not_not_embedded", raw=contract.absence_is_not_not_embedded
    )
    missing_flag = _require_non_empty_str(
        field="missing_input_fail_closed", raw=contract.missing_input_fail_closed
    )
    malformed_flag = _require_non_empty_str(
        field="malformed_input_fail_closed", raw=contract.malformed_input_fail_closed
    )
    term_set_flag = _require_non_empty_str(
        field="term_set_unresolved_does_not_decide_inclusion",
        raw=contract.term_set_unresolved_does_not_decide_inclusion,
    )
    applicability_flag = _require_non_empty_str(
        field="applicability_unresolved_does_not_decide_inclusion",
        raw=contract.applicability_unresolved_does_not_decide_inclusion,
    )
    unit_flag = _require_non_empty_str(
        field="unit_unresolved_does_not_decide_inclusion",
        raw=contract.unit_unresolved_does_not_decide_inclusion,
    )
    schema_flag = _require_non_empty_str(
        field="separate_schema_does_not_prove_independent_deduction",
        raw=contract.separate_schema_does_not_prove_independent_deduction,
    )
    subtract_flag = _require_non_empty_str(
        field="unknown_inclusion_cannot_authorize_subtraction",
        raw=contract.unknown_inclusion_cannot_authorize_subtraction,
    )
    omit_flag = _require_non_empty_str(
        field="unknown_inclusion_cannot_authorize_omission",
        raw=contract.unknown_inclusion_cannot_authorize_omission,
    )
    double_count_flag = _require_non_empty_str(
        field="no_double_counting_permission", raw=contract.no_double_counting_permission
    )
    rejected = _require_non_empty_str(
        field="rejected_inclusion_inferences", raw=contract.rejected_inclusion_inferences
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
        field="p01_equity_base_inclusion_contract_authority_effect",
        raw=contract.p01_equity_base_inclusion_contract_authority_effect,
    )
    digest = _require_non_empty_str(field="provenance_digest", raw=contract.provenance_digest)
    if version != CONTRACT_VERSION:
        raise P01EquityBaseInclusionContractError("P01_CONTRACT_VERSION_MISMATCH")
    if parent_applicability != PARENT_APPLICABILITY_CONTRACT_SCHEMA_CLASS:
        raise P01EquityBaseInclusionContractError(
            "P01_PARENT_APPLICABILITY_CONTRACT_REFERENCE_MISMATCH"
        )
    if parent_term_set != PARENT_TERM_SET_CONTRACT_SCHEMA_CLASS:
        raise P01EquityBaseInclusionContractError("P01_PARENT_TERM_SET_CONTRACT_REFERENCE_MISMATCH")
    if parent_term != PARENT_TERM_CONTRACT_SCHEMA_CLASS:
        raise P01EquityBaseInclusionContractError("P01_PARENT_TERM_CONTRACT_REFERENCE_MISMATCH")
    if target != DIMENSION_ID:
        raise P01EquityBaseInclusionContractError("P01_TARGET_DIMENSION_MISMATCH")
    if policy_id != POLICY_ID:
        raise P01EquityBaseInclusionContractError("P01_POLICY_ID_MISMATCH")
    if term_id != TERM_ID:
        raise P01EquityBaseInclusionContractError("P01_TERM_ID_MISMATCH")
    _reject_coerced_inclusion(field="p01_equity_base_inclusion_status", raw=status)
    if status in {
        TYPED_INCLUSION_STATE_INCLUDED,
        TYPED_INCLUSION_STATE_EXCLUDED,
        TYPED_INCLUSION_STATE_CONDITIONAL,
        TYPED_INCLUSION_STATE_PARTIAL,
        TYPED_INCLUSION_STATE_INDEPENDENT,
    }:
        raise P01EquityBaseInclusionContractError("P01_EQUITY_BASE_INCLUSION_CANDIDATE_UNPROVEN")
    if status != P01_EQUITY_BASE_INCLUSION_STATUS:
        raise P01EquityBaseInclusionContractError("P01_EQUITY_BASE_INCLUSION_STATUS_MISMATCH")
    if resolved.lower() == "true":
        raise P01EquityBaseInclusionContractError("P01_EQUITY_BASE_INCLUSION_RESOLVED_FORBIDDEN")
    if resolved != P01_EQUITY_BASE_INCLUSION_RESOLVED_STATUS:
        raise P01EquityBaseInclusionContractError(
            "P01_EQUITY_BASE_INCLUSION_RESOLVED_STATUS_MISMATCH"
        )
    _reject_coerced_inclusion(field="p01_equity_base_inclusion_rule", raw=rule)
    if rule != P01_EQUITY_BASE_INCLUSION_RULE:
        raise P01EquityBaseInclusionContractError("P01_EQUITY_BASE_INCLUSION_RULE_MISMATCH")
    _reject_coerced_inclusion(field="p01_equity_base_inclusion_adjudication", raw=adjudication)
    if adjudication != P01_EQUITY_BASE_INCLUSION_ADJUDICATION:
        raise P01EquityBaseInclusionContractError("P01_EQUITY_BASE_INCLUSION_ADJUDICATION_MISMATCH")
    if typed_state in {
        TYPED_INCLUSION_STATE_INCLUDED,
        TYPED_INCLUSION_STATE_EXCLUDED,
        TYPED_INCLUSION_STATE_CONDITIONAL,
        TYPED_INCLUSION_STATE_PARTIAL,
        TYPED_INCLUSION_STATE_INDEPENDENT,
        INCLUSION_IN_BASE,
        INCLUSION_NOT_IN_BASE,
        INCLUSION_NOT_APPLICABLE,
    }:
        raise P01EquityBaseInclusionContractError("P01_EQUITY_BASE_INCLUSION_CANDIDATE_UNPROVEN")
    if typed_state != TYPED_INCLUSION_STATE:
        raise P01EquityBaseInclusionContractError("P01_TYPED_INCLUSION_STATE_MISMATCH")
    if unknown_flag.lower() != "true" or unknown_flag != UNKNOWN_IS_NOT_EXCLUDED:
        raise P01EquityBaseInclusionContractError("P01_UNKNOWN_IS_NOT_EXCLUDED_REQUIRED")
    if zero_flag.lower() != "true" or zero_flag != ZERO_IS_NOT_EMBEDDED_OR_EXCLUDED:
        raise P01EquityBaseInclusionContractError("P01_ZERO_IS_NOT_EMBEDDED_OR_EXCLUDED_REQUIRED")
    if absence_flag.lower() != "true" or absence_flag != ABSENCE_IS_NOT_NOT_EMBEDDED:
        raise P01EquityBaseInclusionContractError("P01_ABSENCE_IS_NOT_NOT_EMBEDDED_REQUIRED")
    if missing_flag.lower() != "true" or missing_flag != MISSING_INPUT_FAIL_CLOSED:
        raise P01EquityBaseInclusionContractError("P01_MISSING_INPUT_FAIL_CLOSED_REQUIRED")
    if malformed_flag.lower() != "true" or malformed_flag != MALFORMED_INPUT_FAIL_CLOSED:
        raise P01EquityBaseInclusionContractError("P01_MALFORMED_INPUT_FAIL_CLOSED_REQUIRED")
    if (
        term_set_flag.lower() != "true"
        or term_set_flag != TERM_SET_UNRESOLVED_DOES_NOT_DECIDE_INCLUSION
    ):
        raise P01EquityBaseInclusionContractError("P01_TERM_SET_MUST_NOT_DECIDE_INCLUSION")
    if (
        applicability_flag.lower() != "true"
        or applicability_flag != APPLICABILITY_UNRESOLVED_DOES_NOT_DECIDE_INCLUSION
    ):
        raise P01EquityBaseInclusionContractError("P01_APPLICABILITY_MUST_NOT_DECIDE_INCLUSION")
    if unit_flag.lower() != "true" or unit_flag != UNIT_UNRESOLVED_DOES_NOT_DECIDE_INCLUSION:
        raise P01EquityBaseInclusionContractError("P01_UNIT_MUST_NOT_DECIDE_INCLUSION")
    if (
        schema_flag.lower() != "true"
        or schema_flag != SEPARATE_SCHEMA_DOES_NOT_PROVE_INDEPENDENT_DEDUCTION
    ):
        raise P01EquityBaseInclusionContractError("P01_SEPARATE_SCHEMA_MUST_NOT_DECIDE_INCLUSION")
    if (
        subtract_flag.lower() != "true"
        or subtract_flag != UNKNOWN_INCLUSION_CANNOT_AUTHORIZE_SUBTRACTION
    ):
        raise P01EquityBaseInclusionContractError("P01_UNKNOWN_INCLUSION_SUBTRACTION_FORBIDDEN")
    if omit_flag.lower() != "true" or omit_flag != UNKNOWN_INCLUSION_CANNOT_AUTHORIZE_OMISSION:
        raise P01EquityBaseInclusionContractError("P01_UNKNOWN_INCLUSION_OMISSION_FORBIDDEN")
    if double_count_flag.lower() != "true" or double_count_flag != NO_DOUBLE_COUNTING_PERMISSION:
        raise P01EquityBaseInclusionContractError("P01_NO_DOUBLE_COUNTING_PERMISSION_REQUIRED")
    if rejected != REJECTED_INCLUSION_INFERENCES:
        raise P01EquityBaseInclusionContractError("P01_REJECTED_INCLUSION_INFERENCES_MISMATCH")
    if remaining != REMAINING_UNRESOLVED_SEMANTICS:
        raise P01EquityBaseInclusionContractError("P01_REMAINING_UNRESOLVED_SEMANTICS_MISMATCH")
    if "P01_EQUITY_BASE_INCLUSION_UNRESOLVED" not in remaining:
        raise P01EquityBaseInclusionContractError(
            "P01_EQUITY_BASE_INCLUSION_MUST_REMAIN_UNRESOLVED"
        )
    if "P01_APPLICABILITY_UNSPECIFIED" not in remaining:
        raise P01EquityBaseInclusionContractError("P01_APPLICABILITY_MUST_REMAIN_UNSPECIFIED")
    if evidence != EVIDENCE_CLASSIFICATION:
        raise P01EquityBaseInclusionContractError("P01_EVIDENCE_CLASSIFICATION_MISMATCH")
    if contradiction != CONTRADICTION_NONE:
        raise P01EquityBaseInclusionContractError("P01_CONTRADICTION_STATUS_MISMATCH")
    if semantics_resolved.lower() == "true":
        raise P01EquityBaseInclusionContractError("P01_TERM_SEMANTICS_RESOLVED_FORBIDDEN")
    if semantics_resolved != TERM_SEMANTICS_RESOLVED_STATUS:
        raise P01EquityBaseInclusionContractError("P01_TERM_SEMANTICS_RESOLVED_STATUS_MISMATCH")
    if closed.lower() == "true":
        raise P01EquityBaseInclusionContractError(
            "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED_FORBIDDEN"
        )
    if closed != UNSPECIFIED_CLOSED_STATUS:
        raise P01EquityBaseInclusionContractError("P01_UNSPECIFIED_CLOSED_STATUS_MISMATCH")
    if (
        effect != P01_EQUITY_BASE_INCLUSION_CONTRACT_AUTHORITY_EFFECT
        or effect != AUTHORITY_EFFECT_NONE
    ):
        raise P01EquityBaseInclusionContractError("P01_AUTHORITY_EFFECT_MUST_REMAIN_NONE")
    if P01_APPLICABILITY_CONTRACT_AUTHORITY_EFFECT != AUTHORITY_EFFECT_NONE:
        raise P01EquityBaseInclusionContractError("P01_PARENT_AUTHORITY_EFFECT_MUST_REMAIN_NONE")
    if EARLIEST_UNRESOLVED_ALGEBRA_TERM != "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED":
        raise P01EquityBaseInclusionContractError("P01_EARLIEST_ALGEBRA_TERM_DRIFT")
    if "U04_PENDING_ORDER_RESERVATION_INCLUSION_UNRESOLVED" not in UNRESOLVED_ALGEBRA_TERMS:
        raise P01EquityBaseInclusionContractError("P01_U04_MUST_REMAIN_UNRESOLVED")
    if "U05_LIABILITY_INCLUSION_OR_VALUE_UNRESOLVED" not in UNRESOLVED_ALGEBRA_TERMS:
        raise P01EquityBaseInclusionContractError("P01_U05_MUST_REMAIN_UNRESOLVED")
    if "U06_FEE_INCLUSION_UNRESOLVED" not in UNRESOLVED_ALGEBRA_TERMS:
        raise P01EquityBaseInclusionContractError("P01_U06_MUST_REMAIN_UNRESOLVED")
    parent_term_contract = build_p01_haircut_reserve_depletion_term_contract_v1(
        p01_term_contract_id="P01_EQUITY_BASE_INCLUSION_PARENT_TERM_ALIGNMENT"
    )
    if parent_term_contract.inclusion_state != PARENT_INCLUSION_STATE:
        raise P01EquityBaseInclusionContractError("P01_PARENT_INCLUSION_ALIGNMENT_MISMATCH")
    if parent_term_contract.embedded_state != PARENT_EMBEDDED_STATE:
        raise P01EquityBaseInclusionContractError("P01_PARENT_EMBEDDED_ALIGNMENT_MISMATCH")
    if parent_term_contract.inclusion_state != INCLUSION_UNRESOLVED:
        raise P01EquityBaseInclusionContractError("P01_PARENT_INCLUSION_MUST_REMAIN_UNRESOLVED")
    if parent_term_contract.embedded_state != EMBEDDED_UNRESOLVED:
        raise P01EquityBaseInclusionContractError("P01_PARENT_EMBEDDED_MUST_REMAIN_UNRESOLVED")
    parent_term_set_contract = build_p01_term_set_and_unit_class_contract_v1(
        p01_term_set_and_unit_class_contract_id="P01_EQUITY_BASE_INCLUSION_PARENT_TERM_SET_ALIGNMENT"
    )
    if parent_term_set_contract.p01_term_set_resolved_status != "false":
        raise P01EquityBaseInclusionContractError("P01_PARENT_TERM_SET_RESOLVED_ALIGNMENT")
    if parent_term_set_contract.p01_value_unit_class_resolved_status != "false":
        raise P01EquityBaseInclusionContractError("P01_PARENT_UNIT_RESOLVED_ALIGNMENT")
    parent_applicability_contract = build_p01_applicability_contract_v1(
        p01_applicability_contract_id="P01_EQUITY_BASE_INCLUSION_PARENT_APPLICABILITY_ALIGNMENT"
    )
    if parent_applicability_contract.p01_applicability_status != P01_APPLICABILITY_STATUS:
        raise P01EquityBaseInclusionContractError("P01_PARENT_APPLICABILITY_ALIGNMENT_MISMATCH")
    algebra = build_reconstruction_algebra_contract_v1(
        algebra_contract_id="P01_EQUITY_BASE_INCLUSION_ALGEBRA_ALIGNMENT"
    )
    p01_term = next(term for term in algebra.terms if term.term_id == TERM_ID)
    if p01_term.inclusion_state != INCLUSION_UNRESOLVED:
        raise P01EquityBaseInclusionContractError("P01_ALGEBRA_INCLUSION_MUST_REMAIN_UNRESOLVED")
    if p01_term.embedded_term_state != EMBEDDED_UNRESOLVED:
        raise P01EquityBaseInclusionContractError("P01_ALGEBRA_EMBEDDED_MUST_REMAIN_UNRESOLVED")
    if algebra.algebra_completeness_status != "INCOMPLETE":
        raise P01EquityBaseInclusionContractError("P01_ALGEBRA_COMPLETENESS_ALIGNMENT")
    canonical = contract.to_canonical_dict()
    expected_digest = compute_p01_equity_base_inclusion_provenance_digest_v1(canonical)
    if not _SHA256_HEX.fullmatch(digest):
        raise P01EquityBaseInclusionContractError("P01_PROVENANCE_DIGEST_NOT_SHA256")
    if digest != expected_digest:
        raise P01EquityBaseInclusionContractError("P01_PROVENANCE_DIGEST_MISMATCH")
    _ = contract_id


def build_p01_equity_base_inclusion_contract_v1(**fields: Any) -> P01EquityBaseInclusionContractV1:
    """Construct the typed P01 equity-base inclusion contract. Does not resolve P01."""

    payload = dict(fields)
    defaults = {
        "p01_equity_base_inclusion_contract_version": CONTRACT_VERSION,
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
        "p01_equity_base_inclusion_status": P01_EQUITY_BASE_INCLUSION_STATUS,
        "p01_equity_base_inclusion_resolved_status": P01_EQUITY_BASE_INCLUSION_RESOLVED_STATUS,
        "p01_equity_base_inclusion_rule": P01_EQUITY_BASE_INCLUSION_RULE,
        "p01_equity_base_inclusion_adjudication": P01_EQUITY_BASE_INCLUSION_ADJUDICATION,
        "typed_inclusion_state": TYPED_INCLUSION_STATE,
        "unknown_is_not_excluded": UNKNOWN_IS_NOT_EXCLUDED,
        "zero_is_not_embedded_or_excluded": ZERO_IS_NOT_EMBEDDED_OR_EXCLUDED,
        "absence_is_not_not_embedded": ABSENCE_IS_NOT_NOT_EMBEDDED,
        "missing_input_fail_closed": MISSING_INPUT_FAIL_CLOSED,
        "malformed_input_fail_closed": MALFORMED_INPUT_FAIL_CLOSED,
        "term_set_unresolved_does_not_decide_inclusion": (
            TERM_SET_UNRESOLVED_DOES_NOT_DECIDE_INCLUSION
        ),
        "applicability_unresolved_does_not_decide_inclusion": (
            APPLICABILITY_UNRESOLVED_DOES_NOT_DECIDE_INCLUSION
        ),
        "unit_unresolved_does_not_decide_inclusion": (UNIT_UNRESOLVED_DOES_NOT_DECIDE_INCLUSION),
        "separate_schema_does_not_prove_independent_deduction": (
            SEPARATE_SCHEMA_DOES_NOT_PROVE_INDEPENDENT_DEDUCTION
        ),
        "unknown_inclusion_cannot_authorize_subtraction": (
            UNKNOWN_INCLUSION_CANNOT_AUTHORIZE_SUBTRACTION
        ),
        "unknown_inclusion_cannot_authorize_omission": (
            UNKNOWN_INCLUSION_CANNOT_AUTHORIZE_OMISSION
        ),
        "no_double_counting_permission": NO_DOUBLE_COUNTING_PERMISSION,
        "rejected_inclusion_inferences": REJECTED_INCLUSION_INFERENCES,
        "remaining_unresolved_semantics": REMAINING_UNRESOLVED_SEMANTICS,
        "evidence_classification": EVIDENCE_CLASSIFICATION,
        "contradiction_state": CONTRADICTION_NONE,
        "term_semantics_resolved_status": TERM_SEMANTICS_RESOLVED_STATUS,
        "unspecified_closed_status": UNSPECIFIED_CLOSED_STATUS,
        "p01_equity_base_inclusion_contract_authority_effect": AUTHORITY_EFFECT_NONE,
    }
    for key, value in defaults.items():
        payload.setdefault(key, value)
    missing = [name for name in _VECTOR_FIELDS if name not in payload]
    if missing:
        raise P01EquityBaseInclusionContractError("P01_FIELD_MISSING:" + ",".join(missing))
    attached = attach_p01_equity_base_inclusion_provenance_digest_v1(payload)
    return P01EquityBaseInclusionContractV1(
        **{name: attached[name] for name in P01_EQUITY_BASE_INCLUSION_PROVENANCE_REQUIRED_FIELDS}
    )


def reject_p01_unknown_inclusion_as_excluded_v1(*, inclusion_status: str) -> None:
    """Unknown P01 equity-base inclusion is not EXCLUDED."""

    _reject_coerced_inclusion(field="p01_equity_base_inclusion_status", raw=inclusion_status)
    if inclusion_status in {
        INCLUSION_NOT_IN_BASE,
        INCLUSION_NOT_APPLICABLE,
        TYPED_INCLUSION_STATE_EXCLUDED,
        TYPED_INCLUSION_STATE_INCLUDED,
    }:
        raise P01EquityBaseInclusionContractError("P01_UNKNOWN_INCLUSION_AUTO_EXCLUDED_FORBIDDEN")
    raise P01EquityBaseInclusionContractError("P01_EQUITY_BASE_INCLUSION_STATUS_MISMATCH")


def reject_p01_zero_or_absence_as_embedded_or_excluded_v1(*, inclusion_status: str) -> None:
    """Zero or term absence is not P01 embedded or excluded."""

    _reject_coerced_inclusion(field="p01_equity_base_inclusion_status", raw=inclusion_status)
    raise P01EquityBaseInclusionContractError("P01_EQUITY_BASE_INCLUSION_STATUS_MISMATCH")


def reject_p01_inclusion_inferred_from_u04_u05_u06_schema_or_venue_v1(
    *, inclusion_rule: str
) -> None:
    """U04/U05/U06, separate schema, or venue-raw state is not a P01 inclusion rule."""

    _reject_coerced_inclusion(field="p01_equity_base_inclusion_rule", raw=inclusion_rule)
    raise P01EquityBaseInclusionContractError("P01_EQUITY_BASE_INCLUSION_RULE_MISMATCH")


def reject_p01_unknown_inclusion_as_subtraction_or_omission_v1(
    *, inclusion_status: str, requested_action: str
) -> None:
    """Unknown P01 inclusion cannot authorize subtraction or omission."""

    _reject_coerced_inclusion(field="p01_equity_base_inclusion_status", raw=inclusion_status)
    folded = _fold(requested_action)
    if folded in _SUBTRACTION_OR_OMISSION_TOKENS:
        raise P01EquityBaseInclusionContractError(
            "P01_UNKNOWN_INCLUSION_SUBTRACTION_OR_OMISSION_FORBIDDEN"
        )
    raise P01EquityBaseInclusionContractError("P01_EQUITY_BASE_INCLUSION_STATUS_MISMATCH")
