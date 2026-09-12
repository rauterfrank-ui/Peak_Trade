"""P01 reconstruction semantic and algebra closeout persist.

Owner-closes remaining P01 product/algebra semantics via
GOVERNED_P01_REDUCTION_DIRECTIVE_V1. Not a productive source/producer.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Mapping

from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    DOUBLE_COUNTING_FORBIDDEN,
    FORMULA_RATIFIED,
    OPERATOR_RATIFIED,
    P01_ABSENCE_SEMANTICS_RESOLVED,
    P01_APPLICATION_FALSE_RULE_RESOLVED,
    P01_APPLICATION_PREDICATE,
    P01_APPLICATION_PREDICATE_INPUT_DOMAIN_RESOLVED,
    P01_APPLICATION_PREDICATE_RESOLVED,
    P01_APPLICATION_TRUE_RULE_RESOLVED,
    P01_CLOSEOUT_MODEL,
    P01_CLOSEOUT_SELECTED_OPTION,
    P01_COMBINATION_PRECEDENCE_RESOLVED,
    P01_EMBEDDED_STATE,
    P01_EMBEDDED_STATE_RESOLVED,
    P01_EQUITY_BASE_INCLUSION_RESOLVED,
    P01_EQUITY_BASE_INCLUSION_STATUS,
    P01_EXACT_MEMBER_IDENTITY_SET,
    P01_GOVERNED_REDUCTION_IS_SEPARATE_RECONSTRUCTION_TERM,
    P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED,
    P01_INPUT_FRESHNESS_RULE_RESOLVED,
    P01_INPUT_NORMALIZATION_RULE_RESOLVED,
    P01_INPUT_READINESS_RULE_RESOLVED,
    P01_INTERNAL_VALUE_SEMANTICS_RESOLVED,
    P01_NUMERIC_VALUE_SEMANTICS_RESOLVED,
    P01_OPERATOR,
    P01_OPTIONALITY_RESOLVED,
    P01_PREDICATE_CONCRETE_INPUT_MEMBER_COUNT,
    P01_PREDICATE_CONCRETE_INPUT_MEMBERS_RESOLVED,
    P01_PREDICATE_INPUT_MEMBER,
    P01_PREDICATE_INPUT_MEMBER_CLASS,
    P01_PREDICATE_OPTIONAL_FIELDS_RESOLVED,
    P01_PREDICATE_REQUIRED_FIELDS_RESOLVED,
    P01_PRODUCTIVE_DIRECTIVE_PRODUCER_IMPLEMENTED,
    P01_PRODUCTIVE_EXTERNAL_SOURCE_MAPPING_BLOCKER,
    P01_PRODUCTIVE_EXTERNAL_SOURCE_MAPPING_RESOLVED,
    P01_PRODUCTIVE_RUNTIME_BINDING_ADDED,
    P01_PRODUCT_SEMANTICS_COMPLETE,
    P01_RECONSTRUCTION_ALGEBRA_CONTRACT_COMPLETE,
    P01_RECONSTRUCTION_SEMANTIC_AND_ALGEBRA_CLOSEOUT_CONTRACT_AUTHORITY_EFFECT,
    P01_RECONSTRUCTION_SEMANTIC_AND_ALGEBRA_CLOSEOUT_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_RECONSTRUCTION_SEMANTIC_AND_ALGEBRA_CLOSEOUT_CONTRACT_SCHEMA_PRESENT,
    P01_RECONSTRUCTION_SEMANTIC_AND_ALGEBRA_CLOSEOUT_REQUIRED_FIELDS,
    P01_REQUIREDNESS_RESOLVED,
    P01_RUNTIME_INSTANCE_PRESENT,
    P01_SIGN_SEMANTICS,
    P01_TERM_SEMANTICS_RESOLVED,
    P01_U04_OVERLAP_RESOLVED,
    P01_U04_OVERLAP_STATE,
    P01_U05_OVERLAP_RESOLVED,
    P01_U05_OVERLAP_STATE,
    P01_ZERO_ABSENCE_NA_RESOLVED,
    P01_ZERO_SEMANTICS_RESOLVED,
    PRE_P01_EQUITY_BASE_EXCLUDES_P01_GOVERNED_REDUCTION,
    RECONSTRUCTION_ALGEBRA_COMPLETE,
    SIGN_RATIFIED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_application_predicate_input_domain_identity_contract_v1 import (
    SCHEMA_CLASS as PARENT_INPUT_DOMAIN_SCHEMA_CLASS,
    build_p01_application_predicate_input_domain_identity_contract_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_haircut_reserve_depletion_term_contract_v1 import (
    SCHEMA_CLASS as P01_TERM_SCHEMA_CLASS,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_value_unit_class_contract_v1 import (
    MEMBER_ID,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.reconstruction_algebra_contract_v1 import (
    CONTRADICTION_NONE,
    DIMENSION_ID,
    TERM_P01_HAIRCUT_RESERVE_DEPLETION,
)

SCHEMA_CLASS = "P01_RECONSTRUCTION_SEMANTIC_AND_ALGEBRA_CLOSEOUT_CONTRACT_V1"
CONTRACT_VERSION = "v1"
POLICY_ID = "P01"
TERM_ID = TERM_P01_HAIRCUT_RESERVE_DEPLETION
RATIFICATION_SCOPE = "P01_RECONSTRUCTION_SEMANTIC_AND_ALGEBRA_CLOSEOUT_ONLY"
SELECTED_OPTION = P01_CLOSEOUT_SELECTED_OPTION
TRUE_PIN = "true"
FALSE_PIN = "false"
AUTHORITY_EFFECT_NONE = "NONE"
REMAINING_UNRESOLVED_SEMANTICS = (
    "P01_PRODUCTIVE_EXTERNAL_SOURCE_MAPPING_UNSPECIFIED,"
    "P01_INPUT_FRESHNESS_RULE_UNSPECIFIED,"
    "U04_PENDING_ORDER_RESERVATION_INCLUSION_UNRESOLVED,"
    "U05_LIABILITY_INCLUSION_OR_VALUE_UNRESOLVED,"
    "U06_FEE_INCLUSION_UNRESOLVED"
)
EVIDENCE_CLASSIFICATION = (
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_AP_OWNER_RATIFIED_P01_CLOSEOUT;"
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_AO_OWNER_RATIFIED_INPUT_DOMAIN_IDENTITY;"
    "OWNER_SELECTION=P01_OP_GOVERNED_REDUCTION_DIRECTIVE_SINGLE_PR_CLOSEOUT_V1;"
    "RATIFICATION_SCOPE=P01_RECONSTRUCTION_SEMANTIC_AND_ALGEBRA_CLOSEOUT_ONLY;"
    "STRUCTURAL_REUSE_ONLY=P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_CONTRACT_V1;"
    "NAVIGATION=MAP_OF_TRUTH_NON_SSOT;"
    "INTERPRETATION=NONE;"
    "HYPOTHESIS=NONE;"
    "REJECTED=PRIOR_CANDIDATES_FOREIGN_SYSTEM_VENUE_RAW_U04_U05_U06_PROTECTED_SURFACES;"
    "UNRESOLVED=PRODUCTIVE_EXTERNAL_SOURCE_FRESHNESS_U04_U05_U06;"
    "UNSPECIFIED=P01_PRODUCTIVE_GOVERNED_REDUCTION_DIRECTIVE_SOURCE"
)
_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")
_VECTOR_FIELDS: tuple[str, ...] = tuple(
    name
    for name in P01_RECONSTRUCTION_SEMANTIC_AND_ALGEBRA_CLOSEOUT_REQUIRED_FIELDS
    if name != "provenance_digest"
)


class P01ReconstructionSemanticAndAlgebraCloseoutContractError(ValueError):
    """Fail-closed P01 closeout contract violation."""


def _require_non_empty_str(*, field: str, raw: Any) -> str:
    if raw is None:
        raise P01ReconstructionSemanticAndAlgebraCloseoutContractError(f"P01_FIELD_MISSING:{field}")
    if isinstance(raw, bool) or not isinstance(raw, str):
        raise P01ReconstructionSemanticAndAlgebraCloseoutContractError(
            f"P01_FIELD_NOT_STRING:{field}"
        )
    text = raw.strip()
    if text == "" or text != raw:
        raise P01ReconstructionSemanticAndAlgebraCloseoutContractError(f"P01_FIELD_MISSING:{field}")
    return text


def _canonical_json(payload: Mapping[str, str]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_p01_reconstruction_semantic_and_algebra_closeout_digest_v1(
    canonical: Mapping[str, str],
) -> str:
    payload = {key: canonical[key] for key in _VECTOR_FIELDS}
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _require_true_pin(*, raw: str, error: str) -> None:
    if raw != TRUE_PIN:
        raise P01ReconstructionSemanticAndAlgebraCloseoutContractError(error)


def _require_false_pin(*, raw: str, error: str) -> None:
    if raw != FALSE_PIN:
        raise P01ReconstructionSemanticAndAlgebraCloseoutContractError(error)


@dataclass(frozen=True)
class P01ReconstructionSemanticAndAlgebraCloseoutContractV1:
    """Typed immutable P01 closeout persist. Not a producer."""

    p01_reconstruction_semantic_and_algebra_closeout_contract_id: str
    p01_reconstruction_semantic_and_algebra_closeout_contract_version: str
    parent_p01_application_predicate_input_domain_identity_contract_schema_class: str
    parent_p01_term_contract_schema_class: str
    target_semantic_dimension_id: str
    policy_id: str
    term_id: str
    member_id: str
    ratification_scope: str
    selected_option: str
    p01_closeout_model: str
    p01_predicate_input_member: str
    p01_predicate_input_member_class: str
    p01_predicate_concrete_input_member_count: str
    p01_predicate_concrete_input_members_resolved_status: str
    p01_predicate_required_fields_resolved_status: str
    p01_predicate_optional_fields_resolved_status: str
    p01_application_true_rule_resolved_status: str
    p01_application_false_rule_resolved_status: str
    p01_application_predicate_resolved_status: str
    p01_application_predicate: str
    p01_application_predicate_input_domain_resolved_status: str
    p01_requiredness_resolved_status: str
    p01_optionality_resolved_status: str
    p01_zero_semantics_resolved_status: str
    p01_absence_semantics_resolved_status: str
    p01_zero_absence_na_resolved_status: str
    p01_input_readiness_rule_resolved_status: str
    p01_input_freshness_rule_resolved_status: str
    p01_input_normalization_rule_resolved_status: str
    p01_numeric_value_semantics_resolved_status: str
    p01_internal_value_semantics_resolved_status: str
    p01_productive_external_source_mapping_resolved_status: str
    formula_ratified_status: str
    operator_ratified_status: str
    sign_ratified_status: str
    p01_operator: str
    p01_sign_semantics: str
    p01_equity_base_inclusion_resolved_status: str
    p01_equity_base_inclusion_status: str
    p01_embedded_state_resolved_status: str
    p01_embedded_state: str
    p01_u04_overlap_resolved_status: str
    p01_u04_overlap_state: str
    p01_u05_overlap_resolved_status: str
    p01_u05_overlap_state: str
    double_counting_forbidden: str
    pre_p01_equity_base_excludes_p01_governed_reduction: str
    p01_governed_reduction_is_separate_reconstruction_term: str
    p01_product_semantics_complete_status: str
    p01_reconstruction_algebra_contract_complete_status: str
    p01_haircut_reserve_depletion_unspecified_closed_status: str
    reconstruction_algebra_complete_status: str
    p01_productive_directive_producer_implemented_status: str
    p01_productive_runtime_binding_added_status: str
    external_p01_runtime_blocker: str
    identity_does_not_promote_prior_candidates: str
    u04_u05_u06_input_inheritance_forbidden: str
    u04_u05_u06_predicate_inheritance_forbidden: str
    master_v2_is_not_p01_authority: str
    double_play_is_not_p01_authority: str
    live_execution_is_not_p01_authority: str
    missing_does_not_mean_does_not_apply: str
    zero_does_not_mean_does_not_apply: str
    absence_does_not_mean_does_not_apply: str
    reconstruction_incomplete_does_not_mean_does_not_apply: str
    does_not_apply_requires_explicit_false_rule: str
    p01_authority_effect: str
    p01_reconstruction_semantic_and_algebra_closeout_contract_authority_effect: str
    remaining_unresolved_semantics: str
    evidence_classification: str
    contradiction_state: str
    p01_runtime_instance_present: str
    provenance_digest: str

    def __post_init__(self) -> None:
        _validate_p01_reconstruction_semantic_and_algebra_closeout_contract_v1(self)

    def to_canonical_dict(self) -> dict[str, str]:
        values = {name: getattr(self, name) for name in _VECTOR_FIELDS}
        values["provenance_digest"] = self.provenance_digest
        return {
            key: values[key]
            for key in P01_RECONSTRUCTION_SEMANTIC_AND_ALGEBRA_CLOSEOUT_REQUIRED_FIELDS
        }


def _validate_p01_reconstruction_semantic_and_algebra_closeout_contract_v1(
    contract: P01ReconstructionSemanticAndAlgebraCloseoutContractV1,
) -> None:
    if P01_RECONSTRUCTION_SEMANTIC_AND_ALGEBRA_CLOSEOUT_CONTRACT_SCHEMA_PRESENT is not True:
        raise P01ReconstructionSemanticAndAlgebraCloseoutContractError(
            "P01_CLOSEOUT_SCHEMA_PRESENT_REQUIRED"
        )
    if P01_RECONSTRUCTION_SEMANTIC_AND_ALGEBRA_CLOSEOUT_CONTRACT_RUNTIME_INSTANCE_PRESENT is True:
        raise P01ReconstructionSemanticAndAlgebraCloseoutContractError(
            "P01_RUNTIME_INSTANCE_FORBIDDEN"
        )
    if P01_RUNTIME_INSTANCE_PRESENT is True:
        raise P01ReconstructionSemanticAndAlgebraCloseoutContractError(
            "P01_RUNTIME_INSTANCE_FORBIDDEN"
        )
    if P01_PREDICATE_CONCRETE_INPUT_MEMBERS_RESOLVED is not True:
        raise P01ReconstructionSemanticAndAlgebraCloseoutContractError(
            "P01_PREDICATE_CONCRETE_INPUT_MEMBERS_RESOLVED_REQUIRED"
        )
    if P01_APPLICATION_TRUE_RULE_RESOLVED is not True:
        raise P01ReconstructionSemanticAndAlgebraCloseoutContractError(
            "P01_APPLICATION_TRUE_RULE_RESOLVED_REQUIRED"
        )
    if P01_APPLICATION_FALSE_RULE_RESOLVED is not True:
        raise P01ReconstructionSemanticAndAlgebraCloseoutContractError(
            "P01_APPLICATION_FALSE_RULE_RESOLVED_REQUIRED"
        )
    if P01_TERM_SEMANTICS_RESOLVED is not True:
        raise P01ReconstructionSemanticAndAlgebraCloseoutContractError(
            "P01_TERM_SEMANTICS_RESOLVED_REQUIRED"
        )
    if P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED is not True:
        raise P01ReconstructionSemanticAndAlgebraCloseoutContractError(
            "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED_REQUIRED"
        )
    if RECONSTRUCTION_ALGEBRA_COMPLETE is True:
        raise P01ReconstructionSemanticAndAlgebraCloseoutContractError(
            "P01_RECONSTRUCTION_ALGEBRA_COMPLETE_PIN_FORBIDDEN"
        )
    if P01_PRODUCTIVE_EXTERNAL_SOURCE_MAPPING_RESOLVED is True:
        raise P01ReconstructionSemanticAndAlgebraCloseoutContractError(
            "P01_PRODUCTIVE_EXTERNAL_SOURCE_MAPPING_FORBIDDEN"
        )
    if P01_INPUT_FRESHNESS_RULE_RESOLVED is True:
        raise P01ReconstructionSemanticAndAlgebraCloseoutContractError(
            "P01_INPUT_FRESHNESS_RULE_RESOLVED_PIN_FORBIDDEN"
        )
    if (
        P01_RECONSTRUCTION_SEMANTIC_AND_ALGEBRA_CLOSEOUT_CONTRACT_AUTHORITY_EFFECT
        != AUTHORITY_EFFECT_NONE
    ):
        raise P01ReconstructionSemanticAndAlgebraCloseoutContractError(
            "P01_AUTHORITY_EFFECT_MUST_REMAIN_NONE"
        )
    for field in _VECTOR_FIELDS:
        _require_non_empty_str(field=field, raw=getattr(contract, field))
    digest = _require_non_empty_str(field="provenance_digest", raw=contract.provenance_digest)
    if _SHA256_HEX.fullmatch(digest) is None:
        raise P01ReconstructionSemanticAndAlgebraCloseoutContractError(
            "P01_PROVENANCE_DIGEST_MALFORMED"
        )
    expected = compute_p01_reconstruction_semantic_and_algebra_closeout_digest_v1(
        {key: getattr(contract, key) for key in _VECTOR_FIELDS}
    )
    if digest != expected:
        raise P01ReconstructionSemanticAndAlgebraCloseoutContractError(
            "P01_PROVENANCE_DIGEST_MISMATCH"
        )
    if contract.ratification_scope != RATIFICATION_SCOPE:
        raise P01ReconstructionSemanticAndAlgebraCloseoutContractError(
            "P01_RATIFICATION_SCOPE_MISMATCH"
        )
    if contract.selected_option != SELECTED_OPTION:
        raise P01ReconstructionSemanticAndAlgebraCloseoutContractError(
            "P01_SELECTED_OPTION_MISMATCH"
        )
    if contract.p01_closeout_model != P01_CLOSEOUT_MODEL:
        raise P01ReconstructionSemanticAndAlgebraCloseoutContractError(
            "P01_CLOSEOUT_MODEL_MISMATCH"
        )
    if contract.member_id != MEMBER_ID or contract.member_id != P01_EXACT_MEMBER_IDENTITY_SET:
        raise P01ReconstructionSemanticAndAlgebraCloseoutContractError("P01_MEMBER_ID_MISMATCH")
    if contract.p01_predicate_input_member != P01_PREDICATE_INPUT_MEMBER:
        raise P01ReconstructionSemanticAndAlgebraCloseoutContractError(
            "P01_PREDICATE_INPUT_MEMBER_MISMATCH"
        )
    if contract.p01_predicate_input_member_class != P01_PREDICATE_INPUT_MEMBER_CLASS:
        raise P01ReconstructionSemanticAndAlgebraCloseoutContractError(
            "P01_PREDICATE_INPUT_MEMBER_CLASS_MISMATCH"
        )
    if contract.p01_predicate_concrete_input_member_count != str(
        P01_PREDICATE_CONCRETE_INPUT_MEMBER_COUNT
    ):
        raise P01ReconstructionSemanticAndAlgebraCloseoutContractError(
            "P01_PREDICATE_CONCRETE_INPUT_MEMBER_COUNT_MISMATCH"
        )
    if contract.p01_application_predicate != P01_APPLICATION_PREDICATE:
        raise P01ReconstructionSemanticAndAlgebraCloseoutContractError(
            "P01_APPLICATION_PREDICATE_MISMATCH"
        )
    if contract.p01_operator != P01_OPERATOR:
        raise P01ReconstructionSemanticAndAlgebraCloseoutContractError("P01_OPERATOR_MISMATCH")
    if contract.p01_sign_semantics != P01_SIGN_SEMANTICS:
        raise P01ReconstructionSemanticAndAlgebraCloseoutContractError(
            "P01_SIGN_SEMANTICS_MISMATCH"
        )
    if contract.p01_equity_base_inclusion_status != P01_EQUITY_BASE_INCLUSION_STATUS:
        raise P01ReconstructionSemanticAndAlgebraCloseoutContractError(
            "P01_EQUITY_BASE_INCLUSION_STATUS_MISMATCH"
        )
    if contract.p01_embedded_state != P01_EMBEDDED_STATE:
        raise P01ReconstructionSemanticAndAlgebraCloseoutContractError(
            "P01_EMBEDDED_STATE_MISMATCH"
        )
    if contract.p01_u04_overlap_state != P01_U04_OVERLAP_STATE:
        raise P01ReconstructionSemanticAndAlgebraCloseoutContractError(
            "P01_U04_OVERLAP_STATE_MISMATCH"
        )
    if contract.p01_u05_overlap_state != P01_U05_OVERLAP_STATE:
        raise P01ReconstructionSemanticAndAlgebraCloseoutContractError(
            "P01_U05_OVERLAP_STATE_MISMATCH"
        )
    if contract.external_p01_runtime_blocker != P01_PRODUCTIVE_EXTERNAL_SOURCE_MAPPING_BLOCKER:
        raise P01ReconstructionSemanticAndAlgebraCloseoutContractError(
            "P01_EXTERNAL_RUNTIME_BLOCKER_MISMATCH"
        )
    if contract.remaining_unresolved_semantics != REMAINING_UNRESOLVED_SEMANTICS:
        raise P01ReconstructionSemanticAndAlgebraCloseoutContractError(
            "P01_REMAINING_UNRESOLVED_SEMANTICS_MISMATCH"
        )
    if contract.evidence_classification != EVIDENCE_CLASSIFICATION:
        raise P01ReconstructionSemanticAndAlgebraCloseoutContractError(
            "P01_EVIDENCE_CLASSIFICATION_MISMATCH"
        )
    if contract.contradiction_state != CONTRADICTION_NONE:
        raise P01ReconstructionSemanticAndAlgebraCloseoutContractError(
            "P01_CONTRADICTION_STATE_MISMATCH"
        )
    if contract.target_semantic_dimension_id != DIMENSION_ID:
        raise P01ReconstructionSemanticAndAlgebraCloseoutContractError(
            "P01_TARGET_DIMENSION_MISMATCH"
        )
    if contract.policy_id != POLICY_ID or contract.term_id != TERM_ID:
        raise P01ReconstructionSemanticAndAlgebraCloseoutContractError(
            "P01_POLICY_OR_TERM_MISMATCH"
        )
    if (
        contract.parent_p01_application_predicate_input_domain_identity_contract_schema_class
        != PARENT_INPUT_DOMAIN_SCHEMA_CLASS
    ):
        raise P01ReconstructionSemanticAndAlgebraCloseoutContractError(
            "P01_PARENT_INPUT_DOMAIN_SCHEMA_MISMATCH"
        )
    if contract.parent_p01_term_contract_schema_class != P01_TERM_SCHEMA_CLASS:
        raise P01ReconstructionSemanticAndAlgebraCloseoutContractError(
            "P01_PARENT_TERM_SCHEMA_MISMATCH"
        )
    for field in (
        "p01_predicate_concrete_input_members_resolved_status",
        "p01_predicate_required_fields_resolved_status",
        "p01_predicate_optional_fields_resolved_status",
        "p01_application_true_rule_resolved_status",
        "p01_application_false_rule_resolved_status",
        "p01_application_predicate_resolved_status",
        "p01_application_predicate_input_domain_resolved_status",
        "p01_requiredness_resolved_status",
        "p01_optionality_resolved_status",
        "p01_zero_semantics_resolved_status",
        "p01_absence_semantics_resolved_status",
        "p01_zero_absence_na_resolved_status",
        "p01_input_readiness_rule_resolved_status",
        "p01_input_normalization_rule_resolved_status",
        "p01_numeric_value_semantics_resolved_status",
        "p01_internal_value_semantics_resolved_status",
        "formula_ratified_status",
        "operator_ratified_status",
        "sign_ratified_status",
        "p01_equity_base_inclusion_resolved_status",
        "p01_embedded_state_resolved_status",
        "p01_u04_overlap_resolved_status",
        "p01_u05_overlap_resolved_status",
        "double_counting_forbidden",
        "pre_p01_equity_base_excludes_p01_governed_reduction",
        "p01_governed_reduction_is_separate_reconstruction_term",
        "p01_product_semantics_complete_status",
        "p01_reconstruction_algebra_contract_complete_status",
        "p01_haircut_reserve_depletion_unspecified_closed_status",
        "identity_does_not_promote_prior_candidates",
        "u04_u05_u06_input_inheritance_forbidden",
        "u04_u05_u06_predicate_inheritance_forbidden",
        "master_v2_is_not_p01_authority",
        "double_play_is_not_p01_authority",
        "live_execution_is_not_p01_authority",
        "missing_does_not_mean_does_not_apply",
        "zero_does_not_mean_does_not_apply",
        "absence_does_not_mean_does_not_apply",
        "reconstruction_incomplete_does_not_mean_does_not_apply",
        "does_not_apply_requires_explicit_false_rule",
    ):
        _require_true_pin(raw=getattr(contract, field), error=f"P01_{field.upper()}_REQUIRED")
    for field in (
        "p01_input_freshness_rule_resolved_status",
        "p01_productive_external_source_mapping_resolved_status",
        "reconstruction_algebra_complete_status",
        "p01_productive_directive_producer_implemented_status",
        "p01_productive_runtime_binding_added_status",
        "p01_runtime_instance_present",
    ):
        _require_false_pin(raw=getattr(contract, field), error=f"P01_{field.upper()}_FORBIDDEN")
    if contract.p01_authority_effect != AUTHORITY_EFFECT_NONE:
        raise P01ReconstructionSemanticAndAlgebraCloseoutContractError(
            "P01_AUTHORITY_EFFECT_MUST_REMAIN_NONE"
        )
    if (
        contract.p01_reconstruction_semantic_and_algebra_closeout_contract_authority_effect
        != AUTHORITY_EFFECT_NONE
    ):
        raise P01ReconstructionSemanticAndAlgebraCloseoutContractError(
            "P01_AUTHORITY_EFFECT_MUST_REMAIN_NONE"
        )
    _ = (
        FORMULA_RATIFIED,
        OPERATOR_RATIFIED,
        SIGN_RATIFIED,
        P01_APPLICATION_PREDICATE_RESOLVED,
        P01_APPLICATION_PREDICATE_INPUT_DOMAIN_RESOLVED,
        P01_PREDICATE_REQUIRED_FIELDS_RESOLVED,
        P01_PREDICATE_OPTIONAL_FIELDS_RESOLVED,
        P01_REQUIREDNESS_RESOLVED,
        P01_OPTIONALITY_RESOLVED,
        P01_ZERO_SEMANTICS_RESOLVED,
        P01_ABSENCE_SEMANTICS_RESOLVED,
        P01_ZERO_ABSENCE_NA_RESOLVED,
        P01_INPUT_READINESS_RULE_RESOLVED,
        P01_INPUT_NORMALIZATION_RULE_RESOLVED,
        P01_NUMERIC_VALUE_SEMANTICS_RESOLVED,
        P01_INTERNAL_VALUE_SEMANTICS_RESOLVED,
        P01_EQUITY_BASE_INCLUSION_RESOLVED,
        P01_EMBEDDED_STATE_RESOLVED,
        P01_U04_OVERLAP_RESOLVED,
        P01_U05_OVERLAP_RESOLVED,
        DOUBLE_COUNTING_FORBIDDEN,
        PRE_P01_EQUITY_BASE_EXCLUDES_P01_GOVERNED_REDUCTION,
        P01_GOVERNED_REDUCTION_IS_SEPARATE_RECONSTRUCTION_TERM,
        P01_PRODUCT_SEMANTICS_COMPLETE,
        P01_RECONSTRUCTION_ALGEBRA_CONTRACT_COMPLETE,
        P01_PRODUCTIVE_DIRECTIVE_PRODUCER_IMPLEMENTED,
        P01_PRODUCTIVE_RUNTIME_BINDING_ADDED,
        P01_COMBINATION_PRECEDENCE_RESOLVED,
    )


def build_p01_reconstruction_semantic_and_algebra_closeout_contract_v1(
    *,
    p01_reconstruction_semantic_and_algebra_closeout_contract_id: str,
    **overrides: Any,
) -> P01ReconstructionSemanticAndAlgebraCloseoutContractV1:
    parent = build_p01_application_predicate_input_domain_identity_contract_v1(
        p01_application_predicate_input_domain_identity_contract_id=(
            "SYNTHETIC_P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_CONTRACT_ID"
        )
    )
    if parent.p01_authority_effect != AUTHORITY_EFFECT_NONE:
        raise P01ReconstructionSemanticAndAlgebraCloseoutContractError(
            "P01_PARENT_AUTHORITY_EFFECT_MUST_REMAIN_NONE"
        )
    payload: dict[str, Any] = dict(overrides)
    defaults: dict[str, str] = {
        "p01_reconstruction_semantic_and_algebra_closeout_contract_id": (
            p01_reconstruction_semantic_and_algebra_closeout_contract_id
        ),
        "p01_reconstruction_semantic_and_algebra_closeout_contract_version": CONTRACT_VERSION,
        "parent_p01_application_predicate_input_domain_identity_contract_schema_class": (
            PARENT_INPUT_DOMAIN_SCHEMA_CLASS
        ),
        "parent_p01_term_contract_schema_class": P01_TERM_SCHEMA_CLASS,
        "target_semantic_dimension_id": DIMENSION_ID,
        "policy_id": POLICY_ID,
        "term_id": TERM_ID,
        "member_id": MEMBER_ID,
        "ratification_scope": RATIFICATION_SCOPE,
        "selected_option": SELECTED_OPTION,
        "p01_closeout_model": P01_CLOSEOUT_MODEL,
        "p01_predicate_input_member": P01_PREDICATE_INPUT_MEMBER,
        "p01_predicate_input_member_class": P01_PREDICATE_INPUT_MEMBER_CLASS,
        "p01_predicate_concrete_input_member_count": str(P01_PREDICATE_CONCRETE_INPUT_MEMBER_COUNT),
        "p01_predicate_concrete_input_members_resolved_status": TRUE_PIN,
        "p01_predicate_required_fields_resolved_status": TRUE_PIN,
        "p01_predicate_optional_fields_resolved_status": TRUE_PIN,
        "p01_application_true_rule_resolved_status": TRUE_PIN,
        "p01_application_false_rule_resolved_status": TRUE_PIN,
        "p01_application_predicate_resolved_status": TRUE_PIN,
        "p01_application_predicate": P01_APPLICATION_PREDICATE,
        "p01_application_predicate_input_domain_resolved_status": TRUE_PIN,
        "p01_requiredness_resolved_status": TRUE_PIN,
        "p01_optionality_resolved_status": TRUE_PIN,
        "p01_zero_semantics_resolved_status": TRUE_PIN,
        "p01_absence_semantics_resolved_status": TRUE_PIN,
        "p01_zero_absence_na_resolved_status": TRUE_PIN,
        "p01_input_readiness_rule_resolved_status": TRUE_PIN,
        "p01_input_freshness_rule_resolved_status": FALSE_PIN,
        "p01_input_normalization_rule_resolved_status": TRUE_PIN,
        "p01_numeric_value_semantics_resolved_status": TRUE_PIN,
        "p01_internal_value_semantics_resolved_status": TRUE_PIN,
        "p01_productive_external_source_mapping_resolved_status": FALSE_PIN,
        "formula_ratified_status": TRUE_PIN,
        "operator_ratified_status": TRUE_PIN,
        "sign_ratified_status": TRUE_PIN,
        "p01_operator": P01_OPERATOR,
        "p01_sign_semantics": P01_SIGN_SEMANTICS,
        "p01_equity_base_inclusion_resolved_status": TRUE_PIN,
        "p01_equity_base_inclusion_status": P01_EQUITY_BASE_INCLUSION_STATUS,
        "p01_embedded_state_resolved_status": TRUE_PIN,
        "p01_embedded_state": P01_EMBEDDED_STATE,
        "p01_u04_overlap_resolved_status": TRUE_PIN,
        "p01_u04_overlap_state": P01_U04_OVERLAP_STATE,
        "p01_u05_overlap_resolved_status": TRUE_PIN,
        "p01_u05_overlap_state": P01_U05_OVERLAP_STATE,
        "double_counting_forbidden": TRUE_PIN,
        "pre_p01_equity_base_excludes_p01_governed_reduction": TRUE_PIN,
        "p01_governed_reduction_is_separate_reconstruction_term": TRUE_PIN,
        "p01_product_semantics_complete_status": TRUE_PIN,
        "p01_reconstruction_algebra_contract_complete_status": TRUE_PIN,
        "p01_haircut_reserve_depletion_unspecified_closed_status": TRUE_PIN,
        "reconstruction_algebra_complete_status": FALSE_PIN,
        "p01_productive_directive_producer_implemented_status": FALSE_PIN,
        "p01_productive_runtime_binding_added_status": FALSE_PIN,
        "external_p01_runtime_blocker": P01_PRODUCTIVE_EXTERNAL_SOURCE_MAPPING_BLOCKER,
        "identity_does_not_promote_prior_candidates": TRUE_PIN,
        "u04_u05_u06_input_inheritance_forbidden": TRUE_PIN,
        "u04_u05_u06_predicate_inheritance_forbidden": TRUE_PIN,
        "master_v2_is_not_p01_authority": TRUE_PIN,
        "double_play_is_not_p01_authority": TRUE_PIN,
        "live_execution_is_not_p01_authority": TRUE_PIN,
        "missing_does_not_mean_does_not_apply": TRUE_PIN,
        "zero_does_not_mean_does_not_apply": TRUE_PIN,
        "absence_does_not_mean_does_not_apply": TRUE_PIN,
        "reconstruction_incomplete_does_not_mean_does_not_apply": TRUE_PIN,
        "does_not_apply_requires_explicit_false_rule": TRUE_PIN,
        "p01_authority_effect": AUTHORITY_EFFECT_NONE,
        "p01_reconstruction_semantic_and_algebra_closeout_contract_authority_effect": (
            AUTHORITY_EFFECT_NONE
        ),
        "remaining_unresolved_semantics": REMAINING_UNRESOLVED_SEMANTICS,
        "evidence_classification": EVIDENCE_CLASSIFICATION,
        "contradiction_state": CONTRADICTION_NONE,
        "p01_runtime_instance_present": FALSE_PIN,
    }
    for key, value in defaults.items():
        payload.setdefault(key, value)
    missing = [name for name in _VECTOR_FIELDS if name not in payload]
    if missing:
        raise P01ReconstructionSemanticAndAlgebraCloseoutContractError(
            "P01_FIELD_MISSING:" + ",".join(missing)
        )
    digest = compute_p01_reconstruction_semantic_and_algebra_closeout_digest_v1(
        {key: str(payload[key]) for key in _VECTOR_FIELDS}
    )
    payload["provenance_digest"] = digest
    return P01ReconstructionSemanticAndAlgebraCloseoutContractV1(
        **{
            name: payload[name]
            for name in P01_RECONSTRUCTION_SEMANTIC_AND_ALGEBRA_CLOSEOUT_REQUIRED_FIELDS
        }
    )
