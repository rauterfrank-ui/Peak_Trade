"""Typed P01 applicability class ratification.

Owner-ratifies GOVERNED_CONDITIONAL for the already-ratified P01 member.
Class ratification is not a predicate, formula, operator, sign, source,
producer, runtime binding, or algebra completeness.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Mapping

from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    P01_ABSENCE_SEMANTICS_RESOLVED,
    P01_APPLICABILITY_CLASS,
    P01_APPLICABILITY_CLASS_CONTRACT_AUTHORITY_EFFECT,
    P01_APPLICABILITY_CLASS_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_APPLICABILITY_CLASS_CONTRACT_SCHEMA_PRESENT,
    P01_APPLICABILITY_CLASS_REQUIRED_FIELDS,
    P01_APPLICABILITY_CLASS_RESOLVED,
    P01_APPLICABILITY_CLASS_SELECTED_OPTION,
    P01_APPLICABILITY_IS_DISTINCT_FROM_ABSENCE,
    P01_APPLICABILITY_IS_DISTINCT_FROM_NOT_APPLICABLE_VALUE_ENCODING,
    P01_APPLICABILITY_IS_DISTINCT_FROM_VALUE,
    P01_APPLICABILITY_IS_DISTINCT_FROM_ZERO,
    P01_APPLICABILITY_RESOLVED,
    P01_APPLICABILITY_STATE_MODEL,
    P01_APPLICATION_PREDICATE_RESOLVED,
    P01_COMBINATION_PRECEDENCE_RESOLVED,
    P01_EXACT_MEMBER_IDENTITY_SET,
    P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED,
    P01_INPUT_PRECONDITIONS_RESOLVED,
    P01_MEMBER_ROLE_SIGN_UNIT_RESOLVED,
    P01_OPTIONALITY_RESOLVED,
    P01_RECONSTRUCTION_STATE_PRECONDITIONS_RESOLVED,
    P01_REQUIREDNESS_RESOLVED,
    P01_RUNTIME_INSTANCE_PRESENT,
    P01_TERM_SEMANTICS_RESOLVED,
    P01_TERM_SET_RESOLVED,
    P01_VALUE_UNIT_CLASS_RESOLVED,
    P01_ZERO_ABSENCE_NA_RESOLVED,
    P01_ZERO_SEMANTICS_RESOLVED,
    RECONSTRUCTION_ALGEBRA_COMPLETE,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_haircut_reserve_depletion_term_contract_v1 import (
    SCHEMA_CLASS as P01_TERM_SCHEMA_CLASS,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_value_unit_class_contract_v1 import (
    MEMBER_ID,
    REMAINING_UNRESOLVED_SEMANTICS as PARENT_REMAINING_UNRESOLVED_SEMANTICS,
    SCHEMA_CLASS as PARENT_UNIT_SCHEMA_CLASS,
    VALUE_UNIT_CLASS,
    build_p01_value_unit_class_contract_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.reconstruction_algebra_contract_v1 import (
    CONTRADICTION_NONE,
    DIMENSION_ID,
    NUMERIC_MISSING,
    NUMERIC_PRESENT_ZERO,
    TERM_P01_HAIRCUT_RESERVE_DEPLETION,
)

SCHEMA_CLASS = "P01_APPLICABILITY_CLASS_CONTRACT_V1"
CONTRACT_VERSION = "v1"
POLICY_ID = "P01"
TERM_ID = TERM_P01_HAIRCUT_RESERVE_DEPLETION
PARENT_UNIT_CONTRACT_SCHEMA_CLASS = PARENT_UNIT_SCHEMA_CLASS
PARENT_TERM_CONTRACT_SCHEMA_CLASS = P01_TERM_SCHEMA_CLASS
RATIFICATION_SCOPE = "APPLICABILITY_CLASS_ONLY"
SELECTED_OPTION = P01_APPLICABILITY_CLASS_SELECTED_OPTION
APPLICABILITY_CLASS = P01_APPLICABILITY_CLASS
APPLICABILITY_STATE_MODEL = P01_APPLICABILITY_STATE_MODEL
APPLICATION_PREDICATE = "UNSPECIFIED_FAIL_CLOSED"
STATE_APPLIES = "APPLIES"
STATE_DOES_NOT_APPLY = "DOES_NOT_APPLY"
STATE_UNKNOWN_FAIL_CLOSED = "UNKNOWN_FAIL_CLOSED"
TRUE_PIN = "true"
FALSE_PIN = "false"
AUTHORITY_EFFECT_NONE = "NONE"
RESOLVED_STATUS_TRUE = "true"
RESOLVED_STATUS_FALSE = "false"
RUNTIME_INSTANCE_PRESENT_STATUS = "false"
TERM_SEMANTICS_RESOLVED_STATUS = "false"
UNSPECIFIED_CLOSED_STATUS = "false"
MISSING_INPUT_FAIL_CLOSED = "true"
MALFORMED_INPUT_FAIL_CLOSED = "true"
REMAINING_UNRESOLVED_SEMANTICS = PARENT_REMAINING_UNRESOLVED_SEMANTICS.replace(
    "P01_APPLICABILITY_UNSPECIFIED,",
    "P01_APPLICATION_PREDICATE_UNSPECIFIED,",
)
REJECTED_APPLICABILITY_CLASS_INFERENCES = (
    "ALWAYS_APPLIES_IS_NOT_THIS_CLASS;"
    "NEVER_APPLIES_IS_NOT_THIS_CLASS;"
    "OPTIONAL_IS_NOT_THIS_CLASS;"
    "MANDATORY_IS_NOT_THIS_CLASS;"
    "DEFAULT_OFF_IS_NOT_THIS_CLASS;"
    "DEFAULT_ON_IS_NOT_THIS_CLASS;"
    "ZERO_WHEN_NOT_APPLICABLE_UNPROVEN;"
    "ZERO_WHEN_MISSING_UNPROVEN;"
    "NA_WHEN_MISSING_UNPROVEN;"
    "ABSENT_WHEN_NOT_APPLICABLE_UNPROVEN;"
    "UNKNOWN_IS_NOT_FALSE;"
    "UNKNOWN_IS_NOT_DOES_NOT_APPLY;"
    "UNKNOWN_IS_NOT_NOT_APPLICABLE;"
    "UNKNOWN_IS_NOT_ZERO;"
    "MISSING_IS_NOT_ZERO;"
    "MISSING_IS_NOT_DOES_NOT_APPLY;"
    "DOES_NOT_APPLY_IS_NOT_NUMERIC_ZERO;"
    "APPLIES_DOES_NOT_IMPLY_VALID_NUMERIC_VALUE;"
    "CLASS_IS_NOT_PREDICATE;"
    "CLASS_IS_NOT_FORMULA;"
    "U04_U05_U06_APPLICABILITY_INHERITANCE_FORBIDDEN;"
    "VENUE_RAW_IS_NOT_P01_APPLICABILITY_AUTHORITY;"
    "STEP_29P_IS_NOT_P01_APPLICABILITY_AUTHORITY;"
    "LIVE_ACCOUNT_BOUND_IS_NOT_P01_APPLICABILITY_AUTHORITY;"
    "MASTER_V2_IS_NOT_P01_APPLICABILITY_AUTHORITY;"
    "DOUBLE_PLAY_IS_NOT_P01_APPLICABILITY_AUTHORITY;"
    "TOP20_IS_NOT_P01_APPLICABILITY_AUTHORITY;"
    "LEARNING_IS_NOT_P01_APPLICABILITY_AUTHORITY;"
    "FULL_CORE_AUTONOMY_IS_NOT_P01_APPLICABILITY_AUTHORITY"
)
EVIDENCE_CLASSIFICATION = (
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_AM_OWNER_RATIFIED_APPLICABILITY_CLASS;"
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_AL_OWNER_RATIFIED_VALUE_UNIT_CLASS;"
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_AK_OWNER_RATIFIED_EXACT_MEMBER_IDENTITY;"
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_AD_UNKNOWN_FAIL_CLOSED_NOT_NOT_APPLICABLE;"
    "OWNER_SELECTION=P01_OP_APPLICABILITY_GOVERNED_CONDITIONAL_V1;"
    "RATIFICATION_SCOPE=APPLICABILITY_CLASS_ONLY;"
    "STRUCTURAL_REUSE_ONLY=P01_VALUE_UNIT_CLASS_CONTRACT_V1;"
    "NAVIGATION=MAP_OF_TRUTH_NON_SSOT;"
    "INTERPRETATION=NONE;"
    "HYPOTHESIS=NONE;"
    "REJECTED=ALWAYS_NEVER_OPTIONAL_MANDATORY_DEFAULT_ZERO_NA_U04_U05_U06_VENUE_PROTECTED_SURFACES;"
    "UNRESOLVED=PREDICATE_REQUIREDNESS_OPTIONALITY_ZERO_ABSENCE_NA_INCLUSION_EMBEDDING_OVERLAP_PROVENANCE_FRESHNESS_ROLE_SIGN;"
    "UNSPECIFIED=P01_APPLICATION_PREDICATE_AND_TERM_SEMANTICS_REMAIN_UNSPECIFIED"
)
_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")
_FORBIDDEN_CLASS_TOKENS: tuple[str, ...] = (
    "alwaysapplies",
    "neverapplies",
    "always",
    "never",
    "optional",
    "mandatory",
    "defaultoff",
    "defaulton",
    "unconditional",
    NUMERIC_PRESENT_ZERO.lower().replace("_", ""),
    NUMERIC_MISSING.lower(),
    "notapplicable",
    "u04",
    "u05",
    "u06",
    "availeq",
    "totaleq",
    "masterv2",
    "doubleplay",
    "top20",
    "liveenabled",
    "livearmed",
)
_ZERO_OR_FALSE_TOKENS: tuple[str, ...] = (
    "0",
    "0.0",
    "zero",
    "false",
    "none",
    "null",
    "absent",
    "missing",
    "n/a",
    "na",
)
_VECTOR_FIELDS: tuple[str, ...] = tuple(
    name for name in P01_APPLICABILITY_CLASS_REQUIRED_FIELDS if name != "provenance_digest"
)


class P01ApplicabilityClassContractError(ValueError):
    """Fail-closed P01 applicability class contract violation."""


def _fold(value: str) -> str:
    return str(value or "").strip().lower().replace("_", "").replace("-", "").replace(".", "")


def _require_non_empty_str(*, field: str, raw: Any) -> str:
    if raw is None:
        raise P01ApplicabilityClassContractError(f"P01_FIELD_MISSING:{field}")
    if isinstance(raw, bool) or not isinstance(raw, str):
        raise P01ApplicabilityClassContractError(f"P01_FIELD_NOT_STRING:{field}")
    text = raw.strip()
    if text == "" or text != raw:
        raise P01ApplicabilityClassContractError(f"P01_FIELD_MISSING:{field}")
    return text


def _sha256_hex(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _canonical_json(payload: Mapping[str, str]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_p01_applicability_class_digest_v1(canonical: Mapping[str, str]) -> str:
    payload = {
        key: canonical[key]
        for key in P01_APPLICABILITY_CLASS_REQUIRED_FIELDS
        if key != "provenance_digest"
    }
    return _sha256_hex(_canonical_json(payload))


def attach_p01_applicability_class_digest_v1(fields: Mapping[str, Any]) -> dict[str, Any]:
    canonical: dict[str, str] = {}
    for canonical_name in P01_APPLICABILITY_CLASS_REQUIRED_FIELDS:
        if canonical_name == "provenance_digest":
            continue
        if canonical_name not in fields:
            raise P01ApplicabilityClassContractError(f"P01_FIELD_MISSING:{canonical_name}")
        raw = fields[canonical_name]
        canonical[canonical_name] = "" if raw is None else str(raw)
    attached = dict(fields)
    attached["provenance_digest"] = compute_p01_applicability_class_digest_v1(canonical)
    return attached


def _require_true_pin(*, raw: str, error: str) -> None:
    if raw != TRUE_PIN or raw.lower() != "true":
        raise P01ApplicabilityClassContractError(error)


def _require_false_pin(*, raw: str, error: str) -> None:
    if raw.lower() == "true" or raw != FALSE_PIN:
        raise P01ApplicabilityClassContractError(error)


def _reject_forbidden_class(*, field: str, raw: str) -> None:
    folded = _fold(raw)
    _ = field
    if folded == _fold(APPLICABILITY_CLASS):
        return
    if folded == _fold(APPLICABILITY_STATE_MODEL):
        return
    for token in _FORBIDDEN_CLASS_TOKENS:
        if token == folded or token in folded:
            raise P01ApplicabilityClassContractError("P01_APPLICABILITY_CLASS_INFERRED_FORBIDDEN")
    if folded in _ZERO_OR_FALSE_TOKENS:
        raise P01ApplicabilityClassContractError("P01_APPLICABILITY_CLASS_INFERRED_FORBIDDEN")


def _reject_unknown_coercion(*, field: str, raw: str) -> None:
    folded = _fold(raw)
    if folded in {"doesnotapply", "false", "notapplicable", "na", "n/a"}:
        raise P01ApplicabilityClassContractError("P01_UNKNOWN_CANNOT_BECOME_DOES_NOT_APPLY")
    if folded in {"0", "00", "zero", NUMERIC_PRESENT_ZERO.lower().replace("_", "")}:
        raise P01ApplicabilityClassContractError("P01_UNKNOWN_CANNOT_BECOME_ZERO")
    if folded in {"missing", "none", "null", "absent", "empty"}:
        raise P01ApplicabilityClassContractError("P01_MISSING_CANNOT_AUTO_BECOME_DOES_NOT_APPLY")
    _ = field


@dataclass(frozen=True)
class P01ApplicabilityClassContractV1:
    """Typed immutable P01 applicability class ratification. Not a predicate."""

    p01_applicability_class_contract_id: str
    p01_applicability_class_contract_version: str
    parent_p01_value_unit_class_contract_schema_class: str
    parent_p01_term_contract_schema_class: str
    target_semantic_dimension_id: str
    policy_id: str
    term_id: str
    member_id: str
    ratification_scope: str
    selected_option: str
    p01_term_set_resolved_status: str
    p01_value_unit_class_resolved_status: str
    p01_value_unit_class: str
    p01_applicability_class_resolved_status: str
    p01_applicability_class: str
    p01_applicability_state_model: str
    p01_applicability_state_applies: str
    p01_applicability_state_does_not_apply: str
    p01_applicability_state_unknown_fail_closed: str
    p01_application_predicate_resolved_status: str
    p01_application_predicate: str
    p01_applicability_resolved_status: str
    p01_applicability_is_distinct_from_value: str
    p01_applicability_is_distinct_from_zero: str
    p01_applicability_is_distinct_from_absence: str
    p01_applicability_is_distinct_from_not_applicable_value_encoding: str
    class_is_not_unconditional_always_on: str
    class_is_not_unconditional_never_on: str
    class_does_not_ratify_predicate: str
    class_does_not_ratify_formula: str
    class_does_not_ratify_operator: str
    class_does_not_ratify_sign: str
    class_does_not_ratify_source_mapping: str
    class_does_not_close_p01_term_semantics: str
    class_does_not_close_haircut_reserve_depletion_unspecified: str
    predicate_true_may_mean_applies: str
    predicate_false_may_mean_does_not_apply: str
    predicate_unknown_must_fail_closed: str
    unknown_cannot_become_false: str
    unknown_cannot_become_does_not_apply: str
    unknown_cannot_become_not_applicable: str
    unknown_cannot_become_zero: str
    missing_cannot_become_zero: str
    missing_cannot_auto_become_does_not_apply: str
    does_not_apply_is_not_numeric_zero: str
    applies_does_not_imply_valid_numeric_value: str
    p01_requiredness_resolved_status: str
    p01_optionality_resolved_status: str
    p01_zero_semantics_resolved_status: str
    p01_absence_semantics_resolved_status: str
    p01_zero_absence_na_resolved_status: str
    p01_input_preconditions_resolved_status: str
    p01_reconstruction_state_preconditions_resolved_status: str
    master_v2_is_not_p01_applicability_authority: str
    double_play_is_not_p01_applicability_authority: str
    top20_is_not_p01_applicability_authority: str
    learning_is_not_p01_applicability_authority: str
    full_core_autonomy_is_not_p01_applicability_authority: str
    venue_raw_is_not_p01_applicability_authority: str
    step_29p_is_not_p01_applicability_authority: str
    live_account_bound_is_not_p01_applicability_authority: str
    u04_u05_u06_applicability_inheritance_forbidden: str
    missing_input_fail_closed: str
    malformed_input_fail_closed: str
    rejected_applicability_class_inferences: str
    remaining_unresolved_semantics: str
    evidence_classification: str
    contradiction_state: str
    term_semantics_resolved_status: str
    unspecified_closed_status: str
    p01_runtime_instance_present: str
    p01_authority_effect: str
    p01_applicability_class_contract_authority_effect: str
    provenance_digest: str

    def __post_init__(self) -> None:
        _validate_p01_applicability_class_contract_v1(self)

    def to_canonical_dict(self) -> dict[str, str]:
        values = {name: getattr(self, name) for name in _VECTOR_FIELDS}
        values["provenance_digest"] = self.provenance_digest
        return {key: values[key] for key in P01_APPLICABILITY_CLASS_REQUIRED_FIELDS}


def _validate_p01_applicability_class_contract_v1(
    contract: P01ApplicabilityClassContractV1,
) -> None:
    if P01_APPLICABILITY_CLASS_CONTRACT_SCHEMA_PRESENT is not True:
        raise P01ApplicabilityClassContractError(
            "P01_APPLICABILITY_CLASS_CONTRACT_SCHEMA_PRESENT_REQUIRED"
        )
    if P01_APPLICABILITY_CLASS_CONTRACT_RUNTIME_INSTANCE_PRESENT is True:
        raise P01ApplicabilityClassContractError("P01_RUNTIME_INSTANCE_FORBIDDEN")
    if P01_RUNTIME_INSTANCE_PRESENT is True:
        raise P01ApplicabilityClassContractError("P01_RUNTIME_INSTANCE_FORBIDDEN")
    if P01_TERM_SET_RESOLVED is not True:
        raise P01ApplicabilityClassContractError("P01_TERM_SET_RESOLVED_REQUIRED")
    if P01_VALUE_UNIT_CLASS_RESOLVED is not True:
        raise P01ApplicabilityClassContractError("P01_VALUE_UNIT_CLASS_RESOLVED_REQUIRED")
    if P01_APPLICABILITY_CLASS_RESOLVED is not True:
        raise P01ApplicabilityClassContractError("P01_APPLICABILITY_CLASS_RESOLVED_REQUIRED")
    if P01_APPLICABILITY_IS_DISTINCT_FROM_VALUE is not True:
        raise P01ApplicabilityClassContractError("P01_APPLICABILITY_DISTINCT_FROM_VALUE_REQUIRED")
    if P01_APPLICABILITY_IS_DISTINCT_FROM_ZERO is not True:
        raise P01ApplicabilityClassContractError("P01_APPLICABILITY_DISTINCT_FROM_ZERO_REQUIRED")
    if P01_APPLICABILITY_IS_DISTINCT_FROM_ABSENCE is not True:
        raise P01ApplicabilityClassContractError("P01_APPLICABILITY_DISTINCT_FROM_ABSENCE_REQUIRED")
    if P01_APPLICABILITY_IS_DISTINCT_FROM_NOT_APPLICABLE_VALUE_ENCODING is not True:
        raise P01ApplicabilityClassContractError(
            "P01_APPLICABILITY_DISTINCT_FROM_NA_ENCODING_REQUIRED"
        )
    if RECONSTRUCTION_ALGEBRA_COMPLETE is True:
        raise P01ApplicabilityClassContractError(
            "P01_RECONSTRUCTION_ALGEBRA_COMPLETE_PIN_FORBIDDEN"
        )
    if P01_APPLICABILITY_CLASS_CONTRACT_AUTHORITY_EFFECT != AUTHORITY_EFFECT_NONE:
        raise P01ApplicabilityClassContractError("P01_AUTHORITY_EFFECT_MUST_REMAIN_NONE")
    if P01_EXACT_MEMBER_IDENTITY_SET != MEMBER_ID:
        raise P01ApplicabilityClassContractError("P01_EXACT_MEMBER_IDENTITY_SET_MISMATCH")

    for field in _VECTOR_FIELDS:
        _require_non_empty_str(field=field, raw=getattr(contract, field))
    digest = _require_non_empty_str(field="provenance_digest", raw=contract.provenance_digest)
    if _SHA256_HEX.fullmatch(digest) is None:
        raise P01ApplicabilityClassContractError("P01_PROVENANCE_DIGEST_MALFORMED")
    expected_digest = compute_p01_applicability_class_digest_v1(
        {key: getattr(contract, key) for key in _VECTOR_FIELDS}
    )
    if digest != expected_digest:
        raise P01ApplicabilityClassContractError("P01_PROVENANCE_DIGEST_MISMATCH")

    if contract.ratification_scope != RATIFICATION_SCOPE:
        raise P01ApplicabilityClassContractError("P01_RATIFICATION_SCOPE_MISMATCH")
    if contract.selected_option != SELECTED_OPTION:
        raise P01ApplicabilityClassContractError("P01_SELECTED_OPTION_MISMATCH")
    if contract.p01_term_set_resolved_status != RESOLVED_STATUS_TRUE:
        raise P01ApplicabilityClassContractError("P01_TERM_SET_RESOLVED_STATUS_MISMATCH")
    if contract.p01_value_unit_class_resolved_status != RESOLVED_STATUS_TRUE:
        raise P01ApplicabilityClassContractError("P01_VALUE_UNIT_CLASS_RESOLVED_STATUS_MISMATCH")
    if contract.p01_value_unit_class != VALUE_UNIT_CLASS:
        raise P01ApplicabilityClassContractError("P01_VALUE_UNIT_CLASS_MISMATCH")
    if contract.member_id != MEMBER_ID:
        raise P01ApplicabilityClassContractError("P01_MEMBER_ID_MISMATCH")
    if contract.p01_applicability_class_resolved_status != RESOLVED_STATUS_TRUE:
        raise P01ApplicabilityClassContractError("P01_APPLICABILITY_CLASS_RESOLVED_STATUS_MISMATCH")
    if contract.p01_applicability_class != APPLICABILITY_CLASS:
        raise P01ApplicabilityClassContractError("P01_APPLICABILITY_CLASS_MISMATCH")
    _reject_forbidden_class(field="p01_applicability_class", raw=contract.p01_applicability_class)
    if contract.p01_applicability_state_model != APPLICABILITY_STATE_MODEL:
        raise P01ApplicabilityClassContractError("P01_APPLICABILITY_STATE_MODEL_MISMATCH")
    if contract.p01_applicability_state_applies != STATE_APPLIES:
        raise P01ApplicabilityClassContractError("P01_APPLICABILITY_STATE_APPLIES_MISMATCH")
    if contract.p01_applicability_state_does_not_apply != STATE_DOES_NOT_APPLY:
        raise P01ApplicabilityClassContractError("P01_APPLICABILITY_STATE_DOES_NOT_APPLY_MISMATCH")
    if contract.p01_applicability_state_unknown_fail_closed != STATE_UNKNOWN_FAIL_CLOSED:
        raise P01ApplicabilityClassContractError("P01_APPLICABILITY_STATE_UNKNOWN_MISMATCH")
    if contract.p01_application_predicate_resolved_status != RESOLVED_STATUS_FALSE:
        raise P01ApplicabilityClassContractError("P01_APPLICATION_PREDICATE_RESOLVED_FORBIDDEN")
    if contract.p01_application_predicate != APPLICATION_PREDICATE:
        raise P01ApplicabilityClassContractError("P01_APPLICATION_PREDICATE_MISMATCH")
    _reject_unknown_coercion(
        field="p01_application_predicate", raw=contract.p01_application_predicate
    )
    if contract.remaining_unresolved_semantics != REMAINING_UNRESOLVED_SEMANTICS:
        raise P01ApplicabilityClassContractError("P01_REMAINING_UNRESOLVED_SEMANTICS_MISMATCH")
    if "P01_APPLICATION_PREDICATE_UNSPECIFIED" not in contract.remaining_unresolved_semantics:
        raise P01ApplicabilityClassContractError(
            "P01_APPLICATION_PREDICATE_MUST_REMAIN_UNSPECIFIED"
        )
    if contract.term_semantics_resolved_status != TERM_SEMANTICS_RESOLVED_STATUS:
        raise P01ApplicabilityClassContractError("P01_TERM_SEMANTICS_RESOLVED_STATUS_MISMATCH")
    if contract.unspecified_closed_status != UNSPECIFIED_CLOSED_STATUS:
        raise P01ApplicabilityClassContractError("P01_UNSPECIFIED_CLOSED_STATUS_MISMATCH")
    if contract.contradiction_state != CONTRADICTION_NONE:
        raise P01ApplicabilityClassContractError("P01_CONTRADICTION_STATE_MISMATCH")
    if contract.rejected_applicability_class_inferences != REJECTED_APPLICABILITY_CLASS_INFERENCES:
        raise P01ApplicabilityClassContractError(
            "P01_REJECTED_APPLICABILITY_CLASS_INFERENCES_MISMATCH"
        )
    if contract.evidence_classification != EVIDENCE_CLASSIFICATION:
        raise P01ApplicabilityClassContractError("P01_EVIDENCE_CLASSIFICATION_MISMATCH")
    if contract.p01_runtime_instance_present != RUNTIME_INSTANCE_PRESENT_STATUS:
        raise P01ApplicabilityClassContractError("P01_RUNTIME_INSTANCE_FORBIDDEN")
    if contract.p01_authority_effect != AUTHORITY_EFFECT_NONE:
        raise P01ApplicabilityClassContractError("P01_AUTHORITY_EFFECT_MUST_REMAIN_NONE")
    if contract.p01_applicability_class_contract_authority_effect != AUTHORITY_EFFECT_NONE:
        raise P01ApplicabilityClassContractError("P01_AUTHORITY_EFFECT_MUST_REMAIN_NONE")
    if contract.parent_p01_value_unit_class_contract_schema_class != (
        PARENT_UNIT_CONTRACT_SCHEMA_CLASS
    ):
        raise P01ApplicabilityClassContractError("P01_PARENT_UNIT_SCHEMA_MISMATCH")
    if contract.parent_p01_term_contract_schema_class != PARENT_TERM_CONTRACT_SCHEMA_CLASS:
        raise P01ApplicabilityClassContractError("P01_PARENT_TERM_SCHEMA_MISMATCH")
    if contract.target_semantic_dimension_id != DIMENSION_ID:
        raise P01ApplicabilityClassContractError("P01_TARGET_DIMENSION_MISMATCH")
    if contract.policy_id != POLICY_ID or contract.term_id != TERM_ID:
        raise P01ApplicabilityClassContractError("P01_POLICY_OR_TERM_MISMATCH")
    _require_false_pin(
        raw=contract.p01_applicability_resolved_status,
        error="P01_APPLICABILITY_RESOLVED_FORBIDDEN",
    )
    _require_false_pin(
        raw=contract.p01_requiredness_resolved_status,
        error="P01_REQUIREDNESS_RESOLVED_FORBIDDEN",
    )
    _require_false_pin(
        raw=contract.p01_optionality_resolved_status,
        error="P01_OPTIONALITY_RESOLVED_FORBIDDEN",
    )
    _require_false_pin(
        raw=contract.p01_zero_semantics_resolved_status,
        error="P01_ZERO_SEMANTICS_RESOLVED_FORBIDDEN",
    )
    _require_false_pin(
        raw=contract.p01_absence_semantics_resolved_status,
        error="P01_ABSENCE_SEMANTICS_RESOLVED_FORBIDDEN",
    )
    _require_false_pin(
        raw=contract.p01_zero_absence_na_resolved_status,
        error="P01_ZERO_ABSENCE_NA_RESOLVED_FORBIDDEN",
    )
    _require_false_pin(
        raw=contract.p01_input_preconditions_resolved_status,
        error="P01_INPUT_PRECONDITIONS_RESOLVED_FORBIDDEN",
    )
    _require_false_pin(
        raw=contract.p01_reconstruction_state_preconditions_resolved_status,
        error="P01_RECONSTRUCTION_STATE_PRECONDITIONS_RESOLVED_FORBIDDEN",
    )
    for field in (
        "p01_applicability_is_distinct_from_value",
        "p01_applicability_is_distinct_from_zero",
        "p01_applicability_is_distinct_from_absence",
        "p01_applicability_is_distinct_from_not_applicable_value_encoding",
        "class_is_not_unconditional_always_on",
        "class_is_not_unconditional_never_on",
        "class_does_not_ratify_predicate",
        "class_does_not_ratify_formula",
        "class_does_not_ratify_operator",
        "class_does_not_ratify_sign",
        "class_does_not_ratify_source_mapping",
        "class_does_not_close_p01_term_semantics",
        "class_does_not_close_haircut_reserve_depletion_unspecified",
        "predicate_true_may_mean_applies",
        "predicate_false_may_mean_does_not_apply",
        "predicate_unknown_must_fail_closed",
        "unknown_cannot_become_false",
        "unknown_cannot_become_does_not_apply",
        "unknown_cannot_become_not_applicable",
        "unknown_cannot_become_zero",
        "missing_cannot_become_zero",
        "missing_cannot_auto_become_does_not_apply",
        "does_not_apply_is_not_numeric_zero",
        "applies_does_not_imply_valid_numeric_value",
        "master_v2_is_not_p01_applicability_authority",
        "double_play_is_not_p01_applicability_authority",
        "top20_is_not_p01_applicability_authority",
        "learning_is_not_p01_applicability_authority",
        "full_core_autonomy_is_not_p01_applicability_authority",
        "venue_raw_is_not_p01_applicability_authority",
        "step_29p_is_not_p01_applicability_authority",
        "live_account_bound_is_not_p01_applicability_authority",
        "u04_u05_u06_applicability_inheritance_forbidden",
        "missing_input_fail_closed",
        "malformed_input_fail_closed",
    ):
        _require_true_pin(raw=getattr(contract, field), error=f"P01_{field.upper()}_REQUIRED")


def build_p01_applicability_class_contract_v1(
    *,
    p01_applicability_class_contract_id: str,
    **overrides: Any,
) -> P01ApplicabilityClassContractV1:
    parent = build_p01_value_unit_class_contract_v1(
        p01_value_unit_class_contract_id="SYNTHETIC_P01_VALUE_UNIT_CLASS_CONTRACT_ID"
    )
    if parent.p01_authority_effect != AUTHORITY_EFFECT_NONE:
        raise P01ApplicabilityClassContractError("P01_PARENT_AUTHORITY_EFFECT_MUST_REMAIN_NONE")
    payload: dict[str, Any] = dict(overrides)
    defaults: dict[str, str] = {
        "p01_applicability_class_contract_id": p01_applicability_class_contract_id,
        "p01_applicability_class_contract_version": CONTRACT_VERSION,
        "parent_p01_value_unit_class_contract_schema_class": PARENT_UNIT_CONTRACT_SCHEMA_CLASS,
        "parent_p01_term_contract_schema_class": PARENT_TERM_CONTRACT_SCHEMA_CLASS,
        "target_semantic_dimension_id": DIMENSION_ID,
        "policy_id": POLICY_ID,
        "term_id": TERM_ID,
        "member_id": MEMBER_ID,
        "ratification_scope": RATIFICATION_SCOPE,
        "selected_option": SELECTED_OPTION,
        "p01_term_set_resolved_status": RESOLVED_STATUS_TRUE,
        "p01_value_unit_class_resolved_status": RESOLVED_STATUS_TRUE,
        "p01_value_unit_class": VALUE_UNIT_CLASS,
        "p01_applicability_class_resolved_status": RESOLVED_STATUS_TRUE,
        "p01_applicability_class": APPLICABILITY_CLASS,
        "p01_applicability_state_model": APPLICABILITY_STATE_MODEL,
        "p01_applicability_state_applies": STATE_APPLIES,
        "p01_applicability_state_does_not_apply": STATE_DOES_NOT_APPLY,
        "p01_applicability_state_unknown_fail_closed": STATE_UNKNOWN_FAIL_CLOSED,
        "p01_application_predicate_resolved_status": RESOLVED_STATUS_FALSE,
        "p01_application_predicate": APPLICATION_PREDICATE,
        "p01_applicability_resolved_status": RESOLVED_STATUS_FALSE,
        "p01_applicability_is_distinct_from_value": TRUE_PIN,
        "p01_applicability_is_distinct_from_zero": TRUE_PIN,
        "p01_applicability_is_distinct_from_absence": TRUE_PIN,
        "p01_applicability_is_distinct_from_not_applicable_value_encoding": TRUE_PIN,
        "class_is_not_unconditional_always_on": TRUE_PIN,
        "class_is_not_unconditional_never_on": TRUE_PIN,
        "class_does_not_ratify_predicate": TRUE_PIN,
        "class_does_not_ratify_formula": TRUE_PIN,
        "class_does_not_ratify_operator": TRUE_PIN,
        "class_does_not_ratify_sign": TRUE_PIN,
        "class_does_not_ratify_source_mapping": TRUE_PIN,
        "class_does_not_close_p01_term_semantics": TRUE_PIN,
        "class_does_not_close_haircut_reserve_depletion_unspecified": TRUE_PIN,
        "predicate_true_may_mean_applies": TRUE_PIN,
        "predicate_false_may_mean_does_not_apply": TRUE_PIN,
        "predicate_unknown_must_fail_closed": TRUE_PIN,
        "unknown_cannot_become_false": TRUE_PIN,
        "unknown_cannot_become_does_not_apply": TRUE_PIN,
        "unknown_cannot_become_not_applicable": TRUE_PIN,
        "unknown_cannot_become_zero": TRUE_PIN,
        "missing_cannot_become_zero": TRUE_PIN,
        "missing_cannot_auto_become_does_not_apply": TRUE_PIN,
        "does_not_apply_is_not_numeric_zero": TRUE_PIN,
        "applies_does_not_imply_valid_numeric_value": TRUE_PIN,
        "p01_requiredness_resolved_status": RESOLVED_STATUS_FALSE,
        "p01_optionality_resolved_status": RESOLVED_STATUS_FALSE,
        "p01_zero_semantics_resolved_status": RESOLVED_STATUS_FALSE,
        "p01_absence_semantics_resolved_status": RESOLVED_STATUS_FALSE,
        "p01_zero_absence_na_resolved_status": RESOLVED_STATUS_FALSE,
        "p01_input_preconditions_resolved_status": RESOLVED_STATUS_FALSE,
        "p01_reconstruction_state_preconditions_resolved_status": RESOLVED_STATUS_FALSE,
        "master_v2_is_not_p01_applicability_authority": TRUE_PIN,
        "double_play_is_not_p01_applicability_authority": TRUE_PIN,
        "top20_is_not_p01_applicability_authority": TRUE_PIN,
        "learning_is_not_p01_applicability_authority": TRUE_PIN,
        "full_core_autonomy_is_not_p01_applicability_authority": TRUE_PIN,
        "venue_raw_is_not_p01_applicability_authority": TRUE_PIN,
        "step_29p_is_not_p01_applicability_authority": TRUE_PIN,
        "live_account_bound_is_not_p01_applicability_authority": TRUE_PIN,
        "u04_u05_u06_applicability_inheritance_forbidden": TRUE_PIN,
        "missing_input_fail_closed": MISSING_INPUT_FAIL_CLOSED,
        "malformed_input_fail_closed": MALFORMED_INPUT_FAIL_CLOSED,
        "rejected_applicability_class_inferences": REJECTED_APPLICABILITY_CLASS_INFERENCES,
        "remaining_unresolved_semantics": REMAINING_UNRESOLVED_SEMANTICS,
        "evidence_classification": EVIDENCE_CLASSIFICATION,
        "contradiction_state": CONTRADICTION_NONE,
        "term_semantics_resolved_status": TERM_SEMANTICS_RESOLVED_STATUS,
        "unspecified_closed_status": UNSPECIFIED_CLOSED_STATUS,
        "p01_runtime_instance_present": RUNTIME_INSTANCE_PRESENT_STATUS,
        "p01_authority_effect": AUTHORITY_EFFECT_NONE,
        "p01_applicability_class_contract_authority_effect": AUTHORITY_EFFECT_NONE,
    }
    for key, value in defaults.items():
        payload.setdefault(key, value)
    missing = [name for name in _VECTOR_FIELDS if name not in payload]
    if missing:
        raise P01ApplicabilityClassContractError("P01_FIELD_MISSING:" + ",".join(missing))
    attached = attach_p01_applicability_class_digest_v1(payload)
    return P01ApplicabilityClassContractV1(
        **{name: attached[name] for name in P01_APPLICABILITY_CLASS_REQUIRED_FIELDS}
    )


def reject_p01_unknown_as_does_not_apply_v1(*, applicability_state: str) -> None:
    """UNKNOWN cannot become DOES_NOT_APPLY."""

    _reject_unknown_coercion(field="p01_applicability_state", raw=applicability_state)
    raise P01ApplicabilityClassContractError("P01_UNKNOWN_CANNOT_BECOME_DOES_NOT_APPLY")


def reject_p01_unknown_as_zero_v1(*, applicability_state: str) -> None:
    """UNKNOWN cannot become ZERO."""

    _reject_unknown_coercion(field="p01_applicability_state", raw=applicability_state)
    raise P01ApplicabilityClassContractError("P01_UNKNOWN_CANNOT_BECOME_ZERO")


def reject_p01_missing_as_zero_v1(*, numeric_state: str) -> None:
    """Missing cannot become ZERO."""

    if numeric_state in {NUMERIC_MISSING, "0", "ZERO", NUMERIC_PRESENT_ZERO}:
        raise P01ApplicabilityClassContractError("P01_MISSING_CANNOT_BECOME_ZERO")
    raise P01ApplicabilityClassContractError("P01_MISSING_CANNOT_BECOME_ZERO")


def reject_p01_missing_as_does_not_apply_v1(*, applicability_state: str) -> None:
    """Missing cannot auto-become DOES_NOT_APPLY."""

    _reject_unknown_coercion(field="p01_applicability_state", raw=applicability_state)
    raise P01ApplicabilityClassContractError("P01_MISSING_CANNOT_AUTO_BECOME_DOES_NOT_APPLY")


def reject_p01_does_not_apply_as_numeric_zero_v1(*, numeric_state: str) -> None:
    """DOES_NOT_APPLY is not a numeric-zero encoding."""

    _ = numeric_state
    raise P01ApplicabilityClassContractError("P01_DOES_NOT_APPLY_IS_NOT_NUMERIC_ZERO")


def reject_p01_applies_as_valid_numeric_value_v1(*, numeric_state: str) -> None:
    """APPLIES does not imply a valid numeric P01 value."""

    _ = numeric_state
    raise P01ApplicabilityClassContractError("P01_APPLIES_DOES_NOT_IMPLY_VALID_NUMERIC_VALUE")


def reject_p01_applicability_class_as_formula_v1(*, formula: str) -> None:
    """Applicability class cannot authorize a reconstruction formula."""

    _ = formula
    raise P01ApplicabilityClassContractError("P01_CLASS_IS_NOT_FORMULA")


def reject_p01_applicability_inherited_from_u04_u05_u06_v1(*, source: str) -> None:
    """U04/U05/U06 cannot decide P01 applicability."""

    _ = source
    raise P01ApplicabilityClassContractError("P01_U04_U05_U06_APPLICABILITY_INHERITANCE_FORBIDDEN")


def reject_p01_applicability_authority_from_forbidden_surface_v1(*, source: str) -> None:
    """Protected and venue surfaces are not P01 applicability authority."""

    _ = source
    raise P01ApplicabilityClassContractError("P01_FORBIDDEN_APPLICABILITY_AUTHORITY")
