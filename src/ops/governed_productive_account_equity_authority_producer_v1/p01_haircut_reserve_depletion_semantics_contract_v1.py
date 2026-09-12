"""Typed P01 haircut/reserve/depletion semantics adjudication.

Encodes the forensic result that Haircut, Reserve, and Depletion are
family class labels, not proven independent members, and that canonical
evidence does not prove per-term algebraic role, sign encoding, unit
class, applicability, zero/absence/NA treatment, or combination order.
Family reduction-only is not a per-term role. Unspecified semantics
cannot authorize arithmetic. Schema presence is not P01 resolution.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Mapping

from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    P01_APPLICABILITY_RESOLVED,
    P01_DEPLETION_SEMANTICS_RESOLVED,
    P01_EMBEDDED_STATE_RESOLVED,
    P01_EQUITY_BASE_INCLUSION_RESOLVED,
    P01_HAIRCUT_RESERVE_DEPLETION_SEMANTICS_CONTRACT_AUTHORITY_EFFECT,
    P01_HAIRCUT_RESERVE_DEPLETION_SEMANTICS_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_HAIRCUT_RESERVE_DEPLETION_SEMANTICS_CONTRACT_SCHEMA_PRESENT,
    P01_HAIRCUT_RESERVE_DEPLETION_SEMANTICS_REQUIRED_FIELDS,
    P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED,
    P01_HAIRCUT_SEMANTICS_RESOLVED,
    P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_AUTHORITY_EFFECT,
    P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_SCHEMA_PRESENT,
    P01_MEMBER_FRESHNESS_INHERITANCE_RESOLVED,
    P01_NUMERIC_VALUE_PROVENANCE_RESOLVED,
    P01_RESERVE_SEMANTICS_RESOLVED,
    P01_RUNTIME_INSTANCE_PRESENT,
    P01_TERM_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_TERM_SEMANTICS_RESOLVED,
    P01_U04_OVERLAP_RESOLVED,
    P01_U05_OVERLAP_RESOLVED,
    P01_VALUE_UNIT_CLASS_RESOLVED,
    RECONSTRUCTION_ALGEBRA_COMPLETE,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_haircut_reserve_depletion_term_contract_v1 import (
    SCHEMA_CLASS as P01_TERM_SCHEMA_CLASS,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_member_freshness_inheritance_contract_v1 import (
    P01_MEMBER_FRESHNESS_STATUS,
    REMAINING_UNRESOLVED_SEMANTICS as PARENT_REMAINING_UNRESOLVED_SEMANTICS,
    SCHEMA_CLASS as P01_MEMBER_FRESHNESS_SCHEMA_CLASS,
    build_p01_member_freshness_inheritance_contract_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_term_set_and_unit_class_contract_v1 import (
    FAMILY_CLASS_LABELS,
    FAMILY_LABELS_ARE_NOT_EXACT_TERM_SET,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.reconstruction_algebra_contract_v1 import (
    CONTRADICTION_NONE,
    DIMENSION_ID,
    TERM_P01_HAIRCUT_RESERVE_DEPLETION,
)

SCHEMA_CLASS = "P01_HAIRCUT_RESERVE_DEPLETION_SEMANTICS_CONTRACT_V1"
CONTRACT_VERSION = "v1"
POLICY_ID = "P01"
TERM_ID = TERM_P01_HAIRCUT_RESERVE_DEPLETION
PARENT_MEMBER_FRESHNESS_CONTRACT_SCHEMA_CLASS = P01_MEMBER_FRESHNESS_SCHEMA_CLASS
PARENT_TERM_CONTRACT_SCHEMA_CLASS = P01_TERM_SCHEMA_CLASS
FAMILY_LABELS_ARE_NOT_INDEPENDENT_MEMBERS = "true"
FAMILY_REDUCTION_ONLY = "true"
FAMILY_MUST_NOT_INCREASE_EQUITY = "true"
FAMILY_NEGATIVE_ALLOWED = "false"
FAMILY_ZERO_ONLY_BY_EXPLICIT_POLICY = "true"
FAMILY_REDUCTION_ONLY_IS_NOT_PER_TERM_ROLE = "true"
FAMILY_SIGN_CONSTRAINT_IS_NOT_PER_TERM_SIGN = "true"
VENUE_RAW_HAIRCUTS_FORBIDDEN = "true"
FUTURE_FEES_PERMISSION_IS_NOT_RESERVE_DEFINITION = "true"
U06_ACCRUED_DISTINCT_IS_NOT_P01_DEFINITION = "true"
TERMS_INSUFFICIENTLY_DEFINED_FOR_ALGEBRAIC_ROLE = "true"
IDENTITY_CLASS = "FAMILY_CLASS_LABEL"
ROLE_UNSPECIFIED = "UNSPECIFIED"
SIGN_UNSPECIFIED = "UNSPECIFIED"
UNIT_UNSPECIFIED = "UNSPECIFIED"
APPLICABILITY_UNSPECIFIED = "UNSPECIFIED"
POSITIVE_DEFINITION_ABSENT = "ABSENT"
RESOLVED_STATUS_FALSE = "false"
ZERO_ABSENCE_NA_RULE = "UNSPECIFIED"
COMBINATION_RULE = "UNSPECIFIED"
PRECEDENCE_RULE = "UNSPECIFIED"
UNKNOWN_IS_NOT_ZERO = "true"
UNSPECIFIED_IS_NOT_ZERO = "true"
MISSING_IS_NOT_ZERO = "true"
NOT_APPLICABLE_IS_NOT_ZERO = "true"
ABSENT_IS_NOT_ZERO = "true"
UNAVAILABLE_IS_NOT_ZERO = "true"
EMBEDDED_IS_NOT_OMIT = "true"
OVERLAP_IS_NOT_DEDUPLICATE = "true"
MISSING_INPUT_FAIL_CLOSED = "true"
MALFORMED_INPUT_FAIL_CLOSED = "true"
UNSPECIFIED_CANNOT_AUTHORIZE_SUBTRACTION = "true"
UNSPECIFIED_CANNOT_AUTHORIZE_MULTIPLICATION = "true"
UNSPECIFIED_CANNOT_AUTHORIZE_ADDITION = "true"
UNSPECIFIED_CANNOT_AUTHORIZE_NETTING = "true"
UNSPECIFIED_CANNOT_AUTHORIZE_OMISSION = "true"
UNSPECIFIED_CANNOT_AUTHORIZE_IGNORE = "true"
NAMING_DOES_NOT_PROVE_ALGEBRA = "true"
SEPARATE_LABELS_DO_NOT_PROVE_SEPARATE_NUMERIC_EFFECT = "true"
SAME_SOURCE_DOES_NOT_PROVE_SHARED_SEMANTICS = "true"
MISSING_IMPLEMENTATION_IS_NOT_ZERO = "true"
MISSING_IMPLEMENTATION_IS_NOT_NOT_APPLICABLE = "true"
U04_U05_U06_U09_ARE_NOT_P01_TERM_AUTHORITY = "true"
AUTHORITY_EFFECT_NONE = "NONE"
RUNTIME_INSTANCE_PRESENT_STATUS = "false"
TERM_SEMANTICS_RESOLVED_STATUS = "false"
UNSPECIFIED_CLOSED_STATUS = "false"
REMAINING_UNRESOLVED_SEMANTICS = PARENT_REMAINING_UNRESOLVED_SEMANTICS
REJECTED_ROLE_INFERENCES = (
    "ADDITIVE_POSITIVE_COMPONENT_UNPROVEN;"
    "ADDITIVE_NEGATIVE_COMPONENT_UNPROVEN;"
    "SUBTRACTIVE_ADJUSTMENT_UNPROVEN;"
    "MULTIPLICATIVE_HAIRCUT_UNPROVEN;"
    "CAP_FLOOR_UNPROVEN;"
    "RESERVE_LOCK_UNPROVEN;"
    "AVAILABILITY_REDUCTION_UNPROVEN;"
    "DEPLETION_STATE_UNPROVEN;"
    "EMBEDDED_NOT_SEPARATE_UNPROVEN;"
    "CONDITIONAL_MODIFIER_UNPROVEN;"
    "INFORMATIONAL_ONLY_UNPROVEN;"
    "FAMILY_REDUCTION_ONLY_IS_NOT_PER_TERM_ROLE;"
    "FAMILY_LABEL_IS_NOT_INDEPENDENT_MEMBER;"
    "NAMING_DOES_NOT_PROVE_ALGEBRA"
)
REJECTED_FORMULA_INFERENCES = (
    "P01_IS_NOT_EQUITY_BASE_MINUS_RESERVE;"
    "P01_IS_NOT_EQUITY_BASE_TIMES_ONE_MINUS_HAIRCUT;"
    "P01_IS_NOT_EQUITY_BASE_MINUS_DEPLETION;"
    "RESERVE_IS_NOT_ZERO;"
    "HAIRCUT_IS_NOT_ZERO;"
    "DEPLETION_IS_NOT_ZERO;"
    "MISSING_IS_NOT_ZERO;"
    "NOT_APPLICABLE_IS_NOT_ZERO;"
    "EMBEDDED_IS_NOT_OMIT;"
    "OVERLAP_IS_NOT_DEDUPLICATE;"
    "UNKNOWN_IS_NOT_ZERO"
)
REJECTED_COMBINATION_INFERENCES = (
    "RESERVE_BEFORE_HAIRCUT_UNPROVEN;"
    "HAIRCUT_BEFORE_RESERVE_UNPROVEN;"
    "DEPLETION_AFTER_RESERVE_UNPROVEN;"
    "MUTUALLY_EXCLUSIVE_UNPROVEN;"
    "CUMULATIVE_UNPROVEN;"
    "MEMBER_DEPENDENT_UNPROVEN;"
    "STATE_DEPENDENT_UNPROVEN;"
    "FAMILY_LISTING_IS_NOT_PRECEDENCE"
)
EVIDENCE_CLASSIFICATION = (
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_T_P01_FAMILY_REDUCTION_ONLY;"
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_T_EACH_TERM_NON_NEGATIVE_MUST_NOT_INCREASE_EQUITY;"
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_T_ZERO_ONLY_BY_EXPLICIT_POLICY;"
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_T_NO_VENUE_RAW_HAIRCUTS;"
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_T_U06_FUTURE_FEES_MAY_EXIST_ONLY_AS_SEPARATE_P01_RESERVE_TERM;"
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_AC_FAMILY_LABELS_ARE_NOT_EXACT_TERM_SET;"
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_AC_FUTURE_FEE_PERMISSION_IS_NOT_MEMBERSHIP;"
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_AB_P01_ALGEBRAIC_ROLE_REDUCTION_ONLY_UNSPECIFIED;"
    "FORENSIC_EVIDENCE=NO_ISOLATED_POSITIVE_DEFINITION_FOR_HAIRCUT;"
    "FORENSIC_EVIDENCE=NO_ISOLATED_POSITIVE_DEFINITION_FOR_RESERVE;"
    "FORENSIC_EVIDENCE=NO_ISOLATED_POSITIVE_DEFINITION_FOR_DEPLETION;"
    "FORENSIC_EVIDENCE=NO_PER_TERM_ALGEBRAIC_ROLE;"
    "FORENSIC_EVIDENCE=NO_PER_TERM_SIGN_ENCODING;"
    "FORENSIC_EVIDENCE=NO_PRECEDENCE_OR_COMBINATION_RULE;"
    "FORENSIC_EVIDENCE=SRC_RISK_HAS_NO_P01_HAIRCUT_IMPLEMENTATION;"
    "HISTORICAL_STATE=11_2_1_N_HAIRCUTS_RESERVE_DEPLETION_FROZEN_PENDING_OWNER_POLICY_SUPERSEDED;"
    "HISTORICAL_STATE=11_13_5_USD_USDC_HAIRCUT_UNINSTANTIATED_NOT_P01;"
    "STRUCTURAL_REUSE_ONLY=P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_V1;"
    "NAVIGATION=MAP_OF_TRUTH_NON_SSOT;"
    "INTERPRETATION=NONE;"
    "HYPOTHESIS=NONE;"
    "REJECTED=INFERRED_FORMULAS_ROLES_COMBINATION_ZERO_COERCION;"
    "UNRESOLVED=PER_TERM_ROLE_SIGN_UNIT_APPLICABILITY_ZERO_ABSENCE_NA_COMBINATION;"
    "UNSPECIFIED=P01_HAIRCUT_RESERVE_DEPLETION_PER_TERM_SEMANTICS;"
    "CONTRADICTORY=NONE"
)
CANDIDATE_ROLES_CLASSIFICATION = (
    "CANDIDATE=ADDITIVE_POSITIVE_COMPONENT|CLASS=REJECTED|REASON=UNPROVEN;"
    "CANDIDATE=ADDITIVE_NEGATIVE_COMPONENT|CLASS=REJECTED|REASON=UNPROVEN;"
    "CANDIDATE=SUBTRACTIVE_ADJUSTMENT|CLASS=REJECTED|REASON=UNPROVEN;"
    "CANDIDATE=MULTIPLICATIVE_HAIRCUT|CLASS=REJECTED|REASON=UNPROVEN;"
    "CANDIDATE=CAP_FLOOR|CLASS=REJECTED|REASON=UNPROVEN;"
    "CANDIDATE=RESERVE_LOCK|CLASS=REJECTED|REASON=UNPROVEN;"
    "CANDIDATE=AVAILABILITY_REDUCTION|CLASS=REJECTED|REASON=UNPROVEN;"
    "CANDIDATE=DEPLETION_STATE|CLASS=REJECTED|REASON=UNPROVEN;"
    "CANDIDATE=EMBEDDED_NOT_SEPARATE|CLASS=REJECTED|REASON=UNPROVEN;"
    "CANDIDATE=CONDITIONAL_MODIFIER|CLASS=REJECTED|REASON=UNPROVEN;"
    "CANDIDATE=INFORMATIONAL_ONLY|CLASS=REJECTED|REASON=UNPROVEN;"
    "CANDIDATE=FAMILY_REDUCTION_ONLY|CLASS=CANONICAL_AUTHORITY|"
    "REASON=FAMILY_CONSTRAINT_NOT_PER_TERM_ROLE;"
    "NO_WINNER_RATIFIED=true"
)
_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")
_INFERRED_SEMANTICS_TOKENS: tuple[str, ...] = (
    "additivepositive",
    "additivenegative",
    "subtractiveadjustment",
    "subtractive",
    "multiplicativehaircut",
    "multiplicative",
    "capfloor",
    "reservelock",
    "availabilityreduction",
    "depletionstate",
    "embeddednotseparate",
    "conditionalmodifier",
    "informationalonly",
    "equitybaseminusreserve",
    "equitybaseminusdepletion",
    "oneminushaircut",
    "reserve0",
    "haircut0",
    "depletion0",
    "missingiszero",
    "naiszero",
    "notapplicableiszero",
    "embeddedomit",
    "overlapdedup",
    "reservebeforehaircut",
    "haircutbeforereserve",
    "depletionafterreserve",
    "mutuallyexclusive",
    "cumulative",
    "resolved",
)
_VECTOR_FIELDS: tuple[str, ...] = tuple(
    name
    for name in P01_HAIRCUT_RESERVE_DEPLETION_SEMANTICS_REQUIRED_FIELDS
    if name != "provenance_digest"
)


class P01HaircutReserveDepletionSemanticsContractError(ValueError):
    """Fail-closed P01 haircut/reserve/depletion semantics contract violation."""


def _fold(value: str) -> str:
    return str(value or "").strip().lower().replace("_", "").replace("-", "").replace(".", "")


def _require_non_empty_str(*, field: str, raw: Any) -> str:
    if raw is None:
        raise P01HaircutReserveDepletionSemanticsContractError(f"P01_FIELD_MISSING:{field}")
    if isinstance(raw, bool) or not isinstance(raw, str):
        raise P01HaircutReserveDepletionSemanticsContractError(f"P01_FIELD_NOT_STRING:{field}")
    text = raw.strip()
    if text == "" or text != raw:
        raise P01HaircutReserveDepletionSemanticsContractError(f"P01_FIELD_MISSING:{field}")
    return text


def _sha256_hex(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _canonical_json(payload: Mapping[str, str]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_p01_haircut_reserve_depletion_semantics_digest_v1(
    canonical: Mapping[str, str],
) -> str:
    payload = {
        key: canonical[key]
        for key in P01_HAIRCUT_RESERVE_DEPLETION_SEMANTICS_REQUIRED_FIELDS
        if key != "provenance_digest"
    }
    return _sha256_hex(_canonical_json(payload))


def attach_p01_haircut_reserve_depletion_semantics_digest_v1(
    fields: Mapping[str, Any],
) -> dict[str, Any]:
    canonical: dict[str, str] = {}
    for canonical_name in P01_HAIRCUT_RESERVE_DEPLETION_SEMANTICS_REQUIRED_FIELDS:
        if canonical_name == "provenance_digest":
            continue
        if canonical_name not in fields:
            raise P01HaircutReserveDepletionSemanticsContractError(
                f"P01_FIELD_MISSING:{canonical_name}"
            )
        raw = fields[canonical_name]
        canonical[canonical_name] = "" if raw is None else str(raw)
    attached = dict(fields)
    attached["provenance_digest"] = compute_p01_haircut_reserve_depletion_semantics_digest_v1(
        canonical
    )
    return attached


def _reject_coerced_semantics(*, field: str, raw: str) -> None:
    folded = _fold(raw)
    _ = field
    if folded in _INFERRED_SEMANTICS_TOKENS:
        raise P01HaircutReserveDepletionSemanticsContractError(
            "P01_TERM_SEMANTICS_INFERRED_FORBIDDEN"
        )
    if any(len(token) > 3 and token in folded for token in _INFERRED_SEMANTICS_TOKENS):
        raise P01HaircutReserveDepletionSemanticsContractError(
            "P01_TERM_SEMANTICS_INFERRED_FORBIDDEN"
        )


def _require_true_pin(*, field: str, raw: str, expected: str, error: str) -> None:
    if raw.lower() != "true" or raw != expected:
        raise P01HaircutReserveDepletionSemanticsContractError(error)
    _ = field


def _require_unspecified(*, field: str, raw: str, expected: str, error: str) -> None:
    if raw != expected or raw != ROLE_UNSPECIFIED:
        raise P01HaircutReserveDepletionSemanticsContractError(error)
    _reject_coerced_semantics(field=field, raw=raw)


@dataclass(frozen=True)
class P01HaircutReserveDepletionSemanticsContractV1:
    """Typed immutable P01 term-semantics adjudication. Not a numeric instance."""

    p01_haircut_reserve_depletion_semantics_contract_id: str
    p01_haircut_reserve_depletion_semantics_contract_version: str
    parent_p01_member_freshness_inheritance_contract_schema_class: str
    parent_p01_term_contract_schema_class: str
    target_semantic_dimension_id: str
    policy_id: str
    term_id: str
    family_class_labels: str
    family_labels_are_not_exact_term_set: str
    family_labels_are_not_independent_members: str
    family_reduction_only: str
    family_must_not_increase_equity: str
    family_negative_allowed: str
    family_zero_only_by_explicit_policy: str
    family_reduction_only_is_not_per_term_role: str
    family_sign_constraint_is_not_per_term_sign: str
    venue_raw_haircuts_forbidden: str
    future_fees_permission_is_not_reserve_definition: str
    u06_accrued_distinct_is_not_p01_definition: str
    terms_insufficiently_defined_for_algebraic_role: str
    p01_haircut_semantics_resolved_status: str
    p01_haircut_identity_class: str
    p01_haircut_role: str
    p01_haircut_sign_semantics: str
    p01_haircut_unit_class: str
    p01_haircut_applicability: str
    p01_haircut_positive_definition_state: str
    p01_reserve_semantics_resolved_status: str
    p01_reserve_identity_class: str
    p01_reserve_role: str
    p01_reserve_sign_semantics: str
    p01_reserve_unit_class: str
    p01_reserve_applicability: str
    p01_reserve_positive_definition_state: str
    p01_depletion_semantics_resolved_status: str
    p01_depletion_identity_class: str
    p01_depletion_role: str
    p01_depletion_sign_semantics: str
    p01_depletion_unit_class: str
    p01_depletion_applicability: str
    p01_depletion_positive_definition_state: str
    p01_zero_absence_na_rule: str
    p01_haircut_reserve_depletion_combination_rule: str
    p01_precedence_rule: str
    unknown_is_not_zero: str
    unspecified_is_not_zero: str
    missing_is_not_zero: str
    not_applicable_is_not_zero: str
    absent_is_not_zero: str
    unavailable_is_not_zero: str
    embedded_is_not_omit: str
    overlap_is_not_deduplicate: str
    missing_input_fail_closed: str
    malformed_input_fail_closed: str
    unspecified_cannot_authorize_subtraction: str
    unspecified_cannot_authorize_multiplication: str
    unspecified_cannot_authorize_addition: str
    unspecified_cannot_authorize_netting: str
    unspecified_cannot_authorize_omission: str
    unspecified_cannot_authorize_ignore: str
    naming_does_not_prove_algebra: str
    separate_labels_do_not_prove_separate_numeric_effect: str
    same_source_does_not_prove_shared_semantics: str
    missing_implementation_is_not_zero: str
    missing_implementation_is_not_not_applicable: str
    u04_u05_u06_u09_are_not_p01_term_authority: str
    rejected_role_inferences: str
    rejected_formula_inferences: str
    rejected_combination_inferences: str
    remaining_unresolved_semantics: str
    evidence_classification: str
    candidate_roles_classification: str
    contradiction_state: str
    term_semantics_resolved_status: str
    unspecified_closed_status: str
    p01_runtime_instance_present: str
    p01_authority_effect: str
    p01_haircut_reserve_depletion_semantics_contract_authority_effect: str
    provenance_digest: str

    def __post_init__(self) -> None:
        _validate_p01_haircut_reserve_depletion_semantics_contract_v1(self)

    def to_canonical_dict(self) -> dict[str, str]:
        values = {name: getattr(self, name) for name in _VECTOR_FIELDS}
        values["provenance_digest"] = self.provenance_digest
        return {key: values[key] for key in P01_HAIRCUT_RESERVE_DEPLETION_SEMANTICS_REQUIRED_FIELDS}


def _validate_p01_haircut_reserve_depletion_semantics_contract_v1(
    contract: P01HaircutReserveDepletionSemanticsContractV1,
) -> None:
    if P01_HAIRCUT_RESERVE_DEPLETION_SEMANTICS_CONTRACT_SCHEMA_PRESENT is not True:
        raise P01HaircutReserveDepletionSemanticsContractError(
            "P01_HAIRCUT_RESERVE_DEPLETION_SEMANTICS_CONTRACT_SCHEMA_PRESENT_REQUIRED"
        )
    if P01_HAIRCUT_RESERVE_DEPLETION_SEMANTICS_CONTRACT_RUNTIME_INSTANCE_PRESENT is True:
        raise P01HaircutReserveDepletionSemanticsContractError("P01_RUNTIME_INSTANCE_FORBIDDEN")
    if P01_RUNTIME_INSTANCE_PRESENT is True:
        raise P01HaircutReserveDepletionSemanticsContractError("P01_RUNTIME_INSTANCE_FORBIDDEN")
    if P01_HAIRCUT_SEMANTICS_RESOLVED is True:
        raise P01HaircutReserveDepletionSemanticsContractError(
            "P01_HAIRCUT_SEMANTICS_RESOLVED_PIN_FORBIDDEN"
        )
    if P01_RESERVE_SEMANTICS_RESOLVED is True:
        raise P01HaircutReserveDepletionSemanticsContractError(
            "P01_RESERVE_SEMANTICS_RESOLVED_PIN_FORBIDDEN"
        )
    if P01_DEPLETION_SEMANTICS_RESOLVED is True:
        raise P01HaircutReserveDepletionSemanticsContractError(
            "P01_DEPLETION_SEMANTICS_RESOLVED_PIN_FORBIDDEN"
        )
    if P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_SCHEMA_PRESENT is not True:
        raise P01HaircutReserveDepletionSemanticsContractError(
            "P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_SCHEMA_PRESENT_REQUIRED"
        )
    if P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_RUNTIME_INSTANCE_PRESENT is True:
        raise P01HaircutReserveDepletionSemanticsContractError(
            "P01_PARENT_FRESHNESS_RUNTIME_INSTANCE_FORBIDDEN"
        )
    if P01_MEMBER_FRESHNESS_INHERITANCE_RESOLVED is True:
        raise P01HaircutReserveDepletionSemanticsContractError(
            "P01_MEMBER_FRESHNESS_INHERITANCE_RESOLVED_PIN_FORBIDDEN"
        )
    if P01_MEMBER_FRESHNESS_STATUS != "UNPROVEN":
        raise P01HaircutReserveDepletionSemanticsContractError(
            "P01_MEMBER_FRESHNESS_STATUS_MISMATCH"
        )
    if P01_TERM_CONTRACT_RUNTIME_INSTANCE_PRESENT is True:
        raise P01HaircutReserveDepletionSemanticsContractError(
            "P01_PARENT_TERM_RUNTIME_INSTANCE_FORBIDDEN"
        )
    if P01_VALUE_UNIT_CLASS_RESOLVED is True:
        raise P01HaircutReserveDepletionSemanticsContractError(
            "P01_VALUE_UNIT_CLASS_RESOLVED_PIN_FORBIDDEN"
        )
    if P01_APPLICABILITY_RESOLVED is True:
        raise P01HaircutReserveDepletionSemanticsContractError(
            "P01_APPLICABILITY_RESOLVED_PIN_FORBIDDEN"
        )
    if P01_EQUITY_BASE_INCLUSION_RESOLVED is True:
        raise P01HaircutReserveDepletionSemanticsContractError(
            "P01_EQUITY_BASE_INCLUSION_RESOLVED_PIN_FORBIDDEN"
        )
    if P01_EMBEDDED_STATE_RESOLVED is True:
        raise P01HaircutReserveDepletionSemanticsContractError(
            "P01_EMBEDDED_STATE_RESOLVED_PIN_FORBIDDEN"
        )
    if P01_U04_OVERLAP_RESOLVED is True:
        raise P01HaircutReserveDepletionSemanticsContractError(
            "P01_U04_OVERLAP_RESOLVED_PIN_FORBIDDEN"
        )
    if P01_U05_OVERLAP_RESOLVED is True:
        raise P01HaircutReserveDepletionSemanticsContractError(
            "P01_U05_OVERLAP_RESOLVED_PIN_FORBIDDEN"
        )
    if P01_NUMERIC_VALUE_PROVENANCE_RESOLVED is True:
        raise P01HaircutReserveDepletionSemanticsContractError(
            "P01_NUMERIC_VALUE_PROVENANCE_RESOLVED_PIN_FORBIDDEN"
        )
    if P01_TERM_SEMANTICS_RESOLVED is True:
        raise P01HaircutReserveDepletionSemanticsContractError(
            "P01_TERM_SEMANTICS_RESOLVED_PIN_FORBIDDEN"
        )
    if P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED is True:
        raise P01HaircutReserveDepletionSemanticsContractError(
            "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED_PIN_FORBIDDEN"
        )
    if RECONSTRUCTION_ALGEBRA_COMPLETE is True:
        raise P01HaircutReserveDepletionSemanticsContractError(
            "P01_RECONSTRUCTION_ALGEBRA_COMPLETE_PIN_FORBIDDEN"
        )
    if P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_AUTHORITY_EFFECT != AUTHORITY_EFFECT_NONE:
        raise P01HaircutReserveDepletionSemanticsContractError(
            "P01_PARENT_AUTHORITY_EFFECT_MUST_REMAIN_NONE"
        )
    if P01_HAIRCUT_RESERVE_DEPLETION_SEMANTICS_CONTRACT_AUTHORITY_EFFECT != AUTHORITY_EFFECT_NONE:
        raise P01HaircutReserveDepletionSemanticsContractError(
            "P01_AUTHORITY_EFFECT_MUST_REMAIN_NONE"
        )

    for field in _VECTOR_FIELDS:
        raw = getattr(contract, field)
        _require_non_empty_str(field=field, raw=raw)
    digest = _require_non_empty_str(field="provenance_digest", raw=contract.provenance_digest)
    if _SHA256_HEX.fullmatch(digest) is None:
        raise P01HaircutReserveDepletionSemanticsContractError("P01_PROVENANCE_DIGEST_MALFORMED")
    expected_digest = compute_p01_haircut_reserve_depletion_semantics_digest_v1(
        {key: getattr(contract, key) for key in _VECTOR_FIELDS}
    )
    if digest != expected_digest:
        raise P01HaircutReserveDepletionSemanticsContractError("P01_PROVENANCE_DIGEST_MISMATCH")

    if contract.family_class_labels != FAMILY_CLASS_LABELS:
        raise P01HaircutReserveDepletionSemanticsContractError("P01_FAMILY_CLASS_LABELS_MISMATCH")
    if contract.family_labels_are_not_exact_term_set != FAMILY_LABELS_ARE_NOT_EXACT_TERM_SET:
        raise P01HaircutReserveDepletionSemanticsContractError(
            "P01_FAMILY_LABELS_ARE_NOT_EXACT_TERM_SET_REQUIRED"
        )
    if contract.p01_haircut_identity_class != IDENTITY_CLASS:
        raise P01HaircutReserveDepletionSemanticsContractError(
            "P01_HAIRCUT_IDENTITY_CLASS_MISMATCH"
        )
    if contract.p01_reserve_identity_class != IDENTITY_CLASS:
        raise P01HaircutReserveDepletionSemanticsContractError(
            "P01_RESERVE_IDENTITY_CLASS_MISMATCH"
        )
    if contract.p01_depletion_identity_class != IDENTITY_CLASS:
        raise P01HaircutReserveDepletionSemanticsContractError(
            "P01_DEPLETION_IDENTITY_CLASS_MISMATCH"
        )
    for field, expected, error in (
        ("p01_haircut_role", ROLE_UNSPECIFIED, "P01_HAIRCUT_ROLE_UNSPECIFIED_REQUIRED"),
        ("p01_haircut_sign_semantics", SIGN_UNSPECIFIED, "P01_HAIRCUT_SIGN_UNSPECIFIED_REQUIRED"),
        ("p01_haircut_unit_class", UNIT_UNSPECIFIED, "P01_HAIRCUT_UNIT_UNSPECIFIED_REQUIRED"),
        (
            "p01_haircut_applicability",
            APPLICABILITY_UNSPECIFIED,
            "P01_HAIRCUT_APPLICABILITY_UNSPECIFIED_REQUIRED",
        ),
        ("p01_reserve_role", ROLE_UNSPECIFIED, "P01_RESERVE_ROLE_UNSPECIFIED_REQUIRED"),
        ("p01_reserve_sign_semantics", SIGN_UNSPECIFIED, "P01_RESERVE_SIGN_UNSPECIFIED_REQUIRED"),
        ("p01_reserve_unit_class", UNIT_UNSPECIFIED, "P01_RESERVE_UNIT_UNSPECIFIED_REQUIRED"),
        (
            "p01_reserve_applicability",
            APPLICABILITY_UNSPECIFIED,
            "P01_RESERVE_APPLICABILITY_UNSPECIFIED_REQUIRED",
        ),
        ("p01_depletion_role", ROLE_UNSPECIFIED, "P01_DEPLETION_ROLE_UNSPECIFIED_REQUIRED"),
        (
            "p01_depletion_sign_semantics",
            SIGN_UNSPECIFIED,
            "P01_DEPLETION_SIGN_UNSPECIFIED_REQUIRED",
        ),
        ("p01_depletion_unit_class", UNIT_UNSPECIFIED, "P01_DEPLETION_UNIT_UNSPECIFIED_REQUIRED"),
        (
            "p01_depletion_applicability",
            APPLICABILITY_UNSPECIFIED,
            "P01_DEPLETION_APPLICABILITY_UNSPECIFIED_REQUIRED",
        ),
        (
            "p01_zero_absence_na_rule",
            ZERO_ABSENCE_NA_RULE,
            "P01_ZERO_ABSENCE_NA_RULE_UNSPECIFIED_REQUIRED",
        ),
        (
            "p01_haircut_reserve_depletion_combination_rule",
            COMBINATION_RULE,
            "P01_COMBINATION_RULE_UNSPECIFIED_REQUIRED",
        ),
        ("p01_precedence_rule", PRECEDENCE_RULE, "P01_PRECEDENCE_RULE_UNSPECIFIED_REQUIRED"),
    ):
        _require_unspecified(
            field=field,
            raw=getattr(contract, field),
            expected=expected,
            error=error,
        )
    for field, expected, error in (
        (
            "p01_haircut_semantics_resolved_status",
            RESOLVED_STATUS_FALSE,
            "P01_HAIRCUT_SEMANTICS_RESOLVED_FORBIDDEN",
        ),
        (
            "p01_reserve_semantics_resolved_status",
            RESOLVED_STATUS_FALSE,
            "P01_RESERVE_SEMANTICS_RESOLVED_FORBIDDEN",
        ),
        (
            "p01_depletion_semantics_resolved_status",
            RESOLVED_STATUS_FALSE,
            "P01_DEPLETION_SEMANTICS_RESOLVED_FORBIDDEN",
        ),
    ):
        raw = getattr(contract, field)
        if raw.lower() == "true" or raw != expected:
            raise P01HaircutReserveDepletionSemanticsContractError(error)
    if contract.p01_haircut_positive_definition_state != POSITIVE_DEFINITION_ABSENT:
        raise P01HaircutReserveDepletionSemanticsContractError(
            "P01_HAIRCUT_POSITIVE_DEFINITION_ABSENT_REQUIRED"
        )
    if contract.p01_reserve_positive_definition_state != POSITIVE_DEFINITION_ABSENT:
        raise P01HaircutReserveDepletionSemanticsContractError(
            "P01_RESERVE_POSITIVE_DEFINITION_ABSENT_REQUIRED"
        )
    if contract.p01_depletion_positive_definition_state != POSITIVE_DEFINITION_ABSENT:
        raise P01HaircutReserveDepletionSemanticsContractError(
            "P01_DEPLETION_POSITIVE_DEFINITION_ABSENT_REQUIRED"
        )
    if contract.p01_runtime_instance_present != RUNTIME_INSTANCE_PRESENT_STATUS:
        raise P01HaircutReserveDepletionSemanticsContractError("P01_RUNTIME_INSTANCE_FORBIDDEN")
    if contract.p01_authority_effect != AUTHORITY_EFFECT_NONE:
        raise P01HaircutReserveDepletionSemanticsContractError(
            "P01_AUTHORITY_EFFECT_MUST_REMAIN_NONE"
        )
    if (
        contract.p01_haircut_reserve_depletion_semantics_contract_authority_effect
        != AUTHORITY_EFFECT_NONE
    ):
        raise P01HaircutReserveDepletionSemanticsContractError(
            "P01_AUTHORITY_EFFECT_MUST_REMAIN_NONE"
        )
    if contract.remaining_unresolved_semantics != REMAINING_UNRESOLVED_SEMANTICS:
        raise P01HaircutReserveDepletionSemanticsContractError(
            "P01_REMAINING_UNRESOLVED_SEMANTICS_MISMATCH"
        )
    if contract.term_semantics_resolved_status != TERM_SEMANTICS_RESOLVED_STATUS:
        raise P01HaircutReserveDepletionSemanticsContractError(
            "P01_TERM_SEMANTICS_RESOLVED_STATUS_MISMATCH"
        )
    if contract.unspecified_closed_status != UNSPECIFIED_CLOSED_STATUS:
        raise P01HaircutReserveDepletionSemanticsContractError(
            "P01_UNSPECIFIED_CLOSED_STATUS_MISMATCH"
        )
    if contract.contradiction_state != CONTRADICTION_NONE:
        raise P01HaircutReserveDepletionSemanticsContractError("P01_CONTRADICTION_STATE_MISMATCH")
    if contract.rejected_role_inferences != REJECTED_ROLE_INFERENCES:
        raise P01HaircutReserveDepletionSemanticsContractError(
            "P01_REJECTED_ROLE_INFERENCES_MISMATCH"
        )
    if contract.rejected_formula_inferences != REJECTED_FORMULA_INFERENCES:
        raise P01HaircutReserveDepletionSemanticsContractError(
            "P01_REJECTED_FORMULA_INFERENCES_MISMATCH"
        )
    if contract.rejected_combination_inferences != REJECTED_COMBINATION_INFERENCES:
        raise P01HaircutReserveDepletionSemanticsContractError(
            "P01_REJECTED_COMBINATION_INFERENCES_MISMATCH"
        )
    if contract.evidence_classification != EVIDENCE_CLASSIFICATION:
        raise P01HaircutReserveDepletionSemanticsContractError(
            "P01_EVIDENCE_CLASSIFICATION_MISMATCH"
        )
    if contract.candidate_roles_classification != CANDIDATE_ROLES_CLASSIFICATION:
        raise P01HaircutReserveDepletionSemanticsContractError(
            "P01_CANDIDATE_ROLES_CLASSIFICATION_MISMATCH"
        )
    for field, expected, error in (
        (
            "family_labels_are_not_independent_members",
            FAMILY_LABELS_ARE_NOT_INDEPENDENT_MEMBERS,
            "P01_FAMILY_LABELS_ARE_NOT_INDEPENDENT_MEMBERS_REQUIRED",
        ),
        ("family_reduction_only", FAMILY_REDUCTION_ONLY, "P01_FAMILY_REDUCTION_ONLY_REQUIRED"),
        (
            "family_must_not_increase_equity",
            FAMILY_MUST_NOT_INCREASE_EQUITY,
            "P01_FAMILY_MUST_NOT_INCREASE_EQUITY_REQUIRED",
        ),
        (
            "family_reduction_only_is_not_per_term_role",
            FAMILY_REDUCTION_ONLY_IS_NOT_PER_TERM_ROLE,
            "P01_FAMILY_REDUCTION_ONLY_IS_NOT_PER_TERM_ROLE_REQUIRED",
        ),
        (
            "family_sign_constraint_is_not_per_term_sign",
            FAMILY_SIGN_CONSTRAINT_IS_NOT_PER_TERM_SIGN,
            "P01_FAMILY_SIGN_IS_NOT_PER_TERM_SIGN_REQUIRED",
        ),
        (
            "venue_raw_haircuts_forbidden",
            VENUE_RAW_HAIRCUTS_FORBIDDEN,
            "P01_VENUE_RAW_HAIRCUTS_FORBIDDEN_REQUIRED",
        ),
        (
            "future_fees_permission_is_not_reserve_definition",
            FUTURE_FEES_PERMISSION_IS_NOT_RESERVE_DEFINITION,
            "P01_FUTURE_FEES_PERMISSION_IS_NOT_RESERVE_DEFINITION_REQUIRED",
        ),
        (
            "terms_insufficiently_defined_for_algebraic_role",
            TERMS_INSUFFICIENTLY_DEFINED_FOR_ALGEBRAIC_ROLE,
            "P01_TERMS_INSUFFICIENTLY_DEFINED_REQUIRED",
        ),
        (
            "family_zero_only_by_explicit_policy",
            FAMILY_ZERO_ONLY_BY_EXPLICIT_POLICY,
            "P01_FAMILY_ZERO_ONLY_BY_EXPLICIT_POLICY_REQUIRED",
        ),
        (
            "u06_accrued_distinct_is_not_p01_definition",
            U06_ACCRUED_DISTINCT_IS_NOT_P01_DEFINITION,
            "P01_U06_ACCRUED_DISTINCT_IS_NOT_P01_DEFINITION_REQUIRED",
        ),
        (
            "unspecified_cannot_authorize_ignore",
            UNSPECIFIED_CANNOT_AUTHORIZE_IGNORE,
            "P01_UNSPECIFIED_CANNOT_AUTHORIZE_IGNORE_REQUIRED",
        ),
        (
            "separate_labels_do_not_prove_separate_numeric_effect",
            SEPARATE_LABELS_DO_NOT_PROVE_SEPARATE_NUMERIC_EFFECT,
            "P01_SEPARATE_LABELS_DO_NOT_PROVE_SEPARATE_NUMERIC_EFFECT_REQUIRED",
        ),
        (
            "same_source_does_not_prove_shared_semantics",
            SAME_SOURCE_DOES_NOT_PROVE_SHARED_SEMANTICS,
            "P01_SAME_SOURCE_DOES_NOT_PROVE_SHARED_SEMANTICS_REQUIRED",
        ),
        (
            "missing_implementation_is_not_zero",
            MISSING_IMPLEMENTATION_IS_NOT_ZERO,
            "P01_MISSING_IMPLEMENTATION_IS_NOT_ZERO_REQUIRED",
        ),
        (
            "missing_implementation_is_not_not_applicable",
            MISSING_IMPLEMENTATION_IS_NOT_NOT_APPLICABLE,
            "P01_MISSING_IMPLEMENTATION_IS_NOT_NOT_APPLICABLE_REQUIRED",
        ),
        (
            "missing_input_fail_closed",
            MISSING_INPUT_FAIL_CLOSED,
            "P01_MISSING_INPUT_FAIL_CLOSED_REQUIRED",
        ),
        (
            "malformed_input_fail_closed",
            MALFORMED_INPUT_FAIL_CLOSED,
            "P01_MALFORMED_INPUT_FAIL_CLOSED_REQUIRED",
        ),
        ("unknown_is_not_zero", UNKNOWN_IS_NOT_ZERO, "P01_UNKNOWN_IS_NOT_ZERO_REQUIRED"),
        (
            "unspecified_is_not_zero",
            UNSPECIFIED_IS_NOT_ZERO,
            "P01_UNSPECIFIED_IS_NOT_ZERO_REQUIRED",
        ),
        ("missing_is_not_zero", MISSING_IS_NOT_ZERO, "P01_MISSING_IS_NOT_ZERO_REQUIRED"),
        (
            "not_applicable_is_not_zero",
            NOT_APPLICABLE_IS_NOT_ZERO,
            "P01_NOT_APPLICABLE_IS_NOT_ZERO_REQUIRED",
        ),
        ("absent_is_not_zero", ABSENT_IS_NOT_ZERO, "P01_ABSENT_IS_NOT_ZERO_REQUIRED"),
        (
            "unavailable_is_not_zero",
            UNAVAILABLE_IS_NOT_ZERO,
            "P01_UNAVAILABLE_IS_NOT_ZERO_REQUIRED",
        ),
        ("embedded_is_not_omit", EMBEDDED_IS_NOT_OMIT, "P01_EMBEDDED_IS_NOT_OMIT_REQUIRED"),
        (
            "overlap_is_not_deduplicate",
            OVERLAP_IS_NOT_DEDUPLICATE,
            "P01_OVERLAP_IS_NOT_DEDUPLICATE_REQUIRED",
        ),
        (
            "unspecified_cannot_authorize_subtraction",
            UNSPECIFIED_CANNOT_AUTHORIZE_SUBTRACTION,
            "P01_UNSPECIFIED_CANNOT_AUTHORIZE_SUBTRACTION_REQUIRED",
        ),
        (
            "unspecified_cannot_authorize_multiplication",
            UNSPECIFIED_CANNOT_AUTHORIZE_MULTIPLICATION,
            "P01_UNSPECIFIED_CANNOT_AUTHORIZE_MULTIPLICATION_REQUIRED",
        ),
        (
            "unspecified_cannot_authorize_addition",
            UNSPECIFIED_CANNOT_AUTHORIZE_ADDITION,
            "P01_UNSPECIFIED_CANNOT_AUTHORIZE_ADDITION_REQUIRED",
        ),
        (
            "unspecified_cannot_authorize_netting",
            UNSPECIFIED_CANNOT_AUTHORIZE_NETTING,
            "P01_UNSPECIFIED_CANNOT_AUTHORIZE_NETTING_REQUIRED",
        ),
        (
            "unspecified_cannot_authorize_omission",
            UNSPECIFIED_CANNOT_AUTHORIZE_OMISSION,
            "P01_UNSPECIFIED_CANNOT_AUTHORIZE_OMISSION_REQUIRED",
        ),
        (
            "naming_does_not_prove_algebra",
            NAMING_DOES_NOT_PROVE_ALGEBRA,
            "P01_NAMING_DOES_NOT_PROVE_ALGEBRA_REQUIRED",
        ),
        (
            "u04_u05_u06_u09_are_not_p01_term_authority",
            U04_U05_U06_U09_ARE_NOT_P01_TERM_AUTHORITY,
            "P01_U04_U05_U06_U09_ARE_NOT_P01_TERM_AUTHORITY_REQUIRED",
        ),
    ):
        _require_true_pin(field=field, raw=getattr(contract, field), expected=expected, error=error)
    if contract.family_negative_allowed != FAMILY_NEGATIVE_ALLOWED:
        raise P01HaircutReserveDepletionSemanticsContractError(
            "P01_FAMILY_NEGATIVE_ALLOWED_MISMATCH"
        )


def build_p01_haircut_reserve_depletion_semantics_contract_v1(
    *,
    p01_haircut_reserve_depletion_semantics_contract_id: str,
    **overrides: Any,
) -> P01HaircutReserveDepletionSemanticsContractV1:
    parent = build_p01_member_freshness_inheritance_contract_v1(
        p01_member_freshness_inheritance_contract_id=(
            "SYNTHETIC_P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_ID"
        )
    )
    if parent.p01_member_freshness_status != P01_MEMBER_FRESHNESS_STATUS:
        raise P01HaircutReserveDepletionSemanticsContractError(
            "P01_MEMBER_FRESHNESS_STATUS_MISMATCH"
        )
    payload: dict[str, Any] = dict(overrides)
    defaults: dict[str, str] = {
        "p01_haircut_reserve_depletion_semantics_contract_id": (
            p01_haircut_reserve_depletion_semantics_contract_id
        ),
        "p01_haircut_reserve_depletion_semantics_contract_version": CONTRACT_VERSION,
        "parent_p01_member_freshness_inheritance_contract_schema_class": (
            PARENT_MEMBER_FRESHNESS_CONTRACT_SCHEMA_CLASS
        ),
        "parent_p01_term_contract_schema_class": PARENT_TERM_CONTRACT_SCHEMA_CLASS,
        "target_semantic_dimension_id": DIMENSION_ID,
        "policy_id": POLICY_ID,
        "term_id": TERM_ID,
        "family_class_labels": FAMILY_CLASS_LABELS,
        "family_labels_are_not_exact_term_set": FAMILY_LABELS_ARE_NOT_EXACT_TERM_SET,
        "family_labels_are_not_independent_members": FAMILY_LABELS_ARE_NOT_INDEPENDENT_MEMBERS,
        "family_reduction_only": FAMILY_REDUCTION_ONLY,
        "family_must_not_increase_equity": FAMILY_MUST_NOT_INCREASE_EQUITY,
        "family_negative_allowed": FAMILY_NEGATIVE_ALLOWED,
        "family_zero_only_by_explicit_policy": FAMILY_ZERO_ONLY_BY_EXPLICIT_POLICY,
        "family_reduction_only_is_not_per_term_role": FAMILY_REDUCTION_ONLY_IS_NOT_PER_TERM_ROLE,
        "family_sign_constraint_is_not_per_term_sign": (
            FAMILY_SIGN_CONSTRAINT_IS_NOT_PER_TERM_SIGN
        ),
        "venue_raw_haircuts_forbidden": VENUE_RAW_HAIRCUTS_FORBIDDEN,
        "future_fees_permission_is_not_reserve_definition": (
            FUTURE_FEES_PERMISSION_IS_NOT_RESERVE_DEFINITION
        ),
        "u06_accrued_distinct_is_not_p01_definition": U06_ACCRUED_DISTINCT_IS_NOT_P01_DEFINITION,
        "terms_insufficiently_defined_for_algebraic_role": (
            TERMS_INSUFFICIENTLY_DEFINED_FOR_ALGEBRAIC_ROLE
        ),
        "p01_haircut_semantics_resolved_status": RESOLVED_STATUS_FALSE,
        "p01_haircut_identity_class": IDENTITY_CLASS,
        "p01_haircut_role": ROLE_UNSPECIFIED,
        "p01_haircut_sign_semantics": SIGN_UNSPECIFIED,
        "p01_haircut_unit_class": UNIT_UNSPECIFIED,
        "p01_haircut_applicability": APPLICABILITY_UNSPECIFIED,
        "p01_haircut_positive_definition_state": POSITIVE_DEFINITION_ABSENT,
        "p01_reserve_semantics_resolved_status": RESOLVED_STATUS_FALSE,
        "p01_reserve_identity_class": IDENTITY_CLASS,
        "p01_reserve_role": ROLE_UNSPECIFIED,
        "p01_reserve_sign_semantics": SIGN_UNSPECIFIED,
        "p01_reserve_unit_class": UNIT_UNSPECIFIED,
        "p01_reserve_applicability": APPLICABILITY_UNSPECIFIED,
        "p01_reserve_positive_definition_state": POSITIVE_DEFINITION_ABSENT,
        "p01_depletion_semantics_resolved_status": RESOLVED_STATUS_FALSE,
        "p01_depletion_identity_class": IDENTITY_CLASS,
        "p01_depletion_role": ROLE_UNSPECIFIED,
        "p01_depletion_sign_semantics": SIGN_UNSPECIFIED,
        "p01_depletion_unit_class": UNIT_UNSPECIFIED,
        "p01_depletion_applicability": APPLICABILITY_UNSPECIFIED,
        "p01_depletion_positive_definition_state": POSITIVE_DEFINITION_ABSENT,
        "p01_zero_absence_na_rule": ZERO_ABSENCE_NA_RULE,
        "p01_haircut_reserve_depletion_combination_rule": COMBINATION_RULE,
        "p01_precedence_rule": PRECEDENCE_RULE,
        "unknown_is_not_zero": UNKNOWN_IS_NOT_ZERO,
        "unspecified_is_not_zero": UNSPECIFIED_IS_NOT_ZERO,
        "missing_is_not_zero": MISSING_IS_NOT_ZERO,
        "not_applicable_is_not_zero": NOT_APPLICABLE_IS_NOT_ZERO,
        "absent_is_not_zero": ABSENT_IS_NOT_ZERO,
        "unavailable_is_not_zero": UNAVAILABLE_IS_NOT_ZERO,
        "embedded_is_not_omit": EMBEDDED_IS_NOT_OMIT,
        "overlap_is_not_deduplicate": OVERLAP_IS_NOT_DEDUPLICATE,
        "missing_input_fail_closed": MISSING_INPUT_FAIL_CLOSED,
        "malformed_input_fail_closed": MALFORMED_INPUT_FAIL_CLOSED,
        "unspecified_cannot_authorize_subtraction": UNSPECIFIED_CANNOT_AUTHORIZE_SUBTRACTION,
        "unspecified_cannot_authorize_multiplication": UNSPECIFIED_CANNOT_AUTHORIZE_MULTIPLICATION,
        "unspecified_cannot_authorize_addition": UNSPECIFIED_CANNOT_AUTHORIZE_ADDITION,
        "unspecified_cannot_authorize_netting": UNSPECIFIED_CANNOT_AUTHORIZE_NETTING,
        "unspecified_cannot_authorize_omission": UNSPECIFIED_CANNOT_AUTHORIZE_OMISSION,
        "unspecified_cannot_authorize_ignore": UNSPECIFIED_CANNOT_AUTHORIZE_IGNORE,
        "naming_does_not_prove_algebra": NAMING_DOES_NOT_PROVE_ALGEBRA,
        "separate_labels_do_not_prove_separate_numeric_effect": (
            SEPARATE_LABELS_DO_NOT_PROVE_SEPARATE_NUMERIC_EFFECT
        ),
        "same_source_does_not_prove_shared_semantics": SAME_SOURCE_DOES_NOT_PROVE_SHARED_SEMANTICS,
        "missing_implementation_is_not_zero": MISSING_IMPLEMENTATION_IS_NOT_ZERO,
        "missing_implementation_is_not_not_applicable": (
            MISSING_IMPLEMENTATION_IS_NOT_NOT_APPLICABLE
        ),
        "u04_u05_u06_u09_are_not_p01_term_authority": U04_U05_U06_U09_ARE_NOT_P01_TERM_AUTHORITY,
        "rejected_role_inferences": REJECTED_ROLE_INFERENCES,
        "rejected_formula_inferences": REJECTED_FORMULA_INFERENCES,
        "rejected_combination_inferences": REJECTED_COMBINATION_INFERENCES,
        "remaining_unresolved_semantics": REMAINING_UNRESOLVED_SEMANTICS,
        "evidence_classification": EVIDENCE_CLASSIFICATION,
        "candidate_roles_classification": CANDIDATE_ROLES_CLASSIFICATION,
        "contradiction_state": CONTRADICTION_NONE,
        "term_semantics_resolved_status": TERM_SEMANTICS_RESOLVED_STATUS,
        "unspecified_closed_status": UNSPECIFIED_CLOSED_STATUS,
        "p01_runtime_instance_present": RUNTIME_INSTANCE_PRESENT_STATUS,
        "p01_authority_effect": AUTHORITY_EFFECT_NONE,
        "p01_haircut_reserve_depletion_semantics_contract_authority_effect": AUTHORITY_EFFECT_NONE,
    }
    for key, value in defaults.items():
        payload.setdefault(key, value)
    missing = [name for name in _VECTOR_FIELDS if name not in payload]
    if missing:
        raise P01HaircutReserveDepletionSemanticsContractError(
            "P01_FIELD_MISSING:" + ",".join(missing)
        )
    attached = attach_p01_haircut_reserve_depletion_semantics_digest_v1(payload)
    return P01HaircutReserveDepletionSemanticsContractV1(
        **{name: attached[name] for name in P01_HAIRCUT_RESERVE_DEPLETION_SEMANTICS_REQUIRED_FIELDS}
    )


def reject_p01_inferred_role_v1(*, role: str) -> None:
    """Unproven algebraic roles are not ratified P01 term roles."""

    _reject_coerced_semantics(field="p01_haircut_role", raw=role)
    raise P01HaircutReserveDepletionSemanticsContractError("P01_TERM_ROLE_INFERRED_FORBIDDEN")


def reject_p01_inferred_formula_v1(*, formula: str) -> None:
    """Unspecified P01 semantics cannot authorize a reconstruction formula."""

    _reject_coerced_semantics(field="canonical_formula", raw=formula)
    raise P01HaircutReserveDepletionSemanticsContractError("P01_INFERRED_FORMULA_FORBIDDEN")


def reject_p01_missing_as_zero_v1(*, treatment: str) -> None:
    """Missing, unknown, N/A, absent, and unavailable are not zero."""

    _reject_coerced_semantics(field="p01_zero_absence_na_rule", raw=treatment)
    raise P01HaircutReserveDepletionSemanticsContractError("P01_MISSING_IS_NOT_ZERO")


def reject_p01_unspecified_semantics_as_arithmetic_v1(*, requested_op: str) -> None:
    """Unspecified haircut/reserve/depletion semantics cannot authorize arithmetic."""

    _reject_coerced_semantics(field="requested_op", raw=requested_op)
    raise P01HaircutReserveDepletionSemanticsContractError(
        "P01_UNSPECIFIED_SEMANTICS_ARITHMETIC_FORBIDDEN"
    )


def reject_p01_combination_rule_v1(*, combination_rule: str) -> None:
    """Precedence and combination effects are not ratified."""

    _reject_coerced_semantics(
        field="p01_haircut_reserve_depletion_combination_rule", raw=combination_rule
    )
    raise P01HaircutReserveDepletionSemanticsContractError(
        "P01_COMBINATION_RULE_INFERRED_FORBIDDEN"
    )
