"""Typed P01 application-predicate input-domain identity and boundary.

Owner-ratifies TYPED_GOVERNED_P01_RECONSTRUCTION_CONTEXT_V1 as the
predicate input-domain class. Identity/boundary ratification is not
concrete member selection, true/false rule, formula, operator, sign,
source, producer, runtime binding, or algebra completeness.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Mapping

from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    P01_APPLICATION_FALSE_RULE_RESOLVED,
    P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_CONTRACT_AUTHORITY_EFFECT,
    P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_CONTRACT_SCHEMA_PRESENT,
    P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_REQUIRED_FIELDS,
    P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_SELECTED_OPTION,
    P01_APPLICATION_PREDICATE_INPUT_DOMAIN_RESOLVED,
    P01_APPLICATION_PREDICATE_IDENTITY_RESOLVED,
    P01_APPLICATION_PREDICATE_MODEL,
    P01_APPLICATION_TRUE_RULE_RESOLVED,
    P01_COMBINATION_PRECEDENCE_RESOLVED,
    P01_EXACT_MEMBER_IDENTITY_SET,
    P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED,
    P01_INPUT_FRESHNESS_RULE_RESOLVED,
    P01_INPUT_NORMALIZATION_RULE_RESOLVED,
    P01_INPUT_READINESS_RULE_RESOLVED,
    P01_MEMBER_ROLE_SIGN_UNIT_RESOLVED,
    P01_PREDICATE_CONCRETE_INPUT_MEMBERS_RESOLVED,
    P01_PREDICATE_INPUT_DOMAIN_ALLOWED_INPUT_CLASS,
    P01_PREDICATE_INPUT_DOMAIN_BOUNDARY_RESOLVED,
    P01_PREDICATE_INPUT_DOMAIN_CLASS,
    P01_PREDICATE_INPUT_DOMAIN_DEFAULT,
    P01_PREDICATE_INPUT_DOMAIN_GOVERNED,
    P01_PREDICATE_INPUT_DOMAIN_IDENTITY_RESOLVED,
    P01_PREDICATE_INPUT_DOMAIN_IS_CLOSED_WORLD,
    P01_PREDICATE_INPUT_DOMAIN_TYPED,
    P01_PREDICATE_OPTIONAL_FIELDS_RESOLVED,
    P01_PREDICATE_REQUIRED_FIELDS_RESOLVED,
    P01_RUNTIME_INSTANCE_PRESENT,
    P01_TERM_SEMANTICS_RESOLVED,
    P01_TERM_SET_RESOLVED,
    P01_VALUE_UNIT_CLASS_RESOLVED,
    RECONSTRUCTION_ALGEBRA_COMPLETE,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_application_predicate_identity_contract_v1 import (
    PREDICATE_MODEL,
    SCHEMA_CLASS as PARENT_IDENTITY_SCHEMA_CLASS,
    REMAINING_UNRESOLVED_SEMANTICS as PARENT_REMAINING_UNRESOLVED_SEMANTICS,
    build_p01_application_predicate_identity_contract_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_applicability_class_contract_v1 import (
    APPLICABILITY_CLASS,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_haircut_reserve_depletion_term_contract_v1 import (
    SCHEMA_CLASS as P01_TERM_SCHEMA_CLASS,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_value_unit_class_contract_v1 import (
    MEMBER_ID,
    VALUE_UNIT_CLASS,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.reconstruction_algebra_contract_v1 import (
    CONTRADICTION_NONE,
    DIMENSION_ID,
    NUMERIC_MISSING,
    NUMERIC_PRESENT_ZERO,
    TERM_P01_HAIRCUT_RESERVE_DEPLETION,
)

SCHEMA_CLASS = "P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_CONTRACT_V1"
CONTRACT_VERSION = "v1"
POLICY_ID = "P01"
TERM_ID = TERM_P01_HAIRCUT_RESERVE_DEPLETION
PARENT_IDENTITY_CONTRACT_SCHEMA_CLASS = PARENT_IDENTITY_SCHEMA_CLASS
PARENT_TERM_CONTRACT_SCHEMA_CLASS = P01_TERM_SCHEMA_CLASS
RATIFICATION_SCOPE = "APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_AND_BOUNDARY_ONLY"
SELECTED_OPTION = P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_SELECTED_OPTION
INPUT_DOMAIN_CLASS = P01_PREDICATE_INPUT_DOMAIN_CLASS
ALLOWED_INPUT_CLASS = P01_PREDICATE_INPUT_DOMAIN_ALLOWED_INPUT_CLASS
INPUT_DOMAIN_DEFAULT = P01_PREDICATE_INPUT_DOMAIN_DEFAULT
UNKNOWN_FAIL_CLOSED = "UNKNOWN_FAIL_CLOSED"
FORBIDDEN_PIN = "FORBIDDEN"
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
CLOSED_WORLD_PIN = "true"
REMAINING_UNRESOLVED_SEMANTICS = PARENT_REMAINING_UNRESOLVED_SEMANTICS.replace(
    "P01_APPLICATION_PREDICATE_INPUT_DOMAIN_UNSPECIFIED,",
    "P01_PREDICATE_CONCRETE_INPUT_MEMBERS_UNSPECIFIED,",
)
REJECTED_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_INFERENCES = (
    "IDENTITY_IS_NOT_CONCRETE_MEMBERS;"
    "IDENTITY_IS_NOT_REQUIRED_FIELDS;"
    "IDENTITY_IS_NOT_OPTIONAL_FIELDS;"
    "IDENTITY_IS_NOT_TRUE_RULE;"
    "IDENTITY_IS_NOT_FALSE_RULE;"
    "IDENTITY_IS_NOT_FORMULA;"
    "IDENTITY_IS_NOT_OPERATOR;"
    "IDENTITY_IS_NOT_SIGN;"
    "IDENTITY_IS_NOT_ACCOUNT_EQUITY_AUTHORITY;"
    "IDENTITY_IS_NOT_PARALLEL_PRODUCER;"
    "IDENTITY_IS_NOT_TRADING_LOGIC_AUTHORITY;"
    "DOMAIN_IS_NOT_P01_VALUE;"
    "DOMAIN_IS_NOT_P01_ZERO;"
    "DOMAIN_IS_NOT_P01_ABSENCE;"
    "DOMAIN_IS_NOT_REQUIREDNESS;"
    "DOMAIN_IS_NOT_COMPLETENESS;"
    "MISSING_IS_NOT_DOES_NOT_APPLY;"
    "ZERO_IS_NOT_DOES_NOT_APPLY;"
    "ABSENCE_IS_NOT_DOES_NOT_APPLY;"
    "RECONSTRUCTION_INCOMPLETE_IS_NOT_DOES_NOT_APPLY;"
    "UNRATIFIED_FACT_ADMISSION_FORBIDDEN;"
    "IMPLICIT_INPUT_PROMOTION_FORBIDDEN;"
    "FOREIGN_SYSTEM_STATE_PROMOTION_FORBIDDEN;"
    "U04_U05_U06_INPUT_INHERITANCE_FORBIDDEN;"
    "VENUE_RAW_IS_NOT_P01_PREDICATE_INPUT_AUTHORITY;"
    "STEP_29P_IS_NOT_P01_PREDICATE_INPUT_AUTHORITY;"
    "LIVE_ACCOUNT_BOUND_IS_NOT_P01_PREDICATE_INPUT_AUTHORITY;"
    "MASTER_V2_IS_NOT_P01_PREDICATE_INPUT_AUTHORITY;"
    "DOUBLE_PLAY_IS_NOT_P01_PREDICATE_INPUT_AUTHORITY;"
    "TOP20_IS_NOT_P01_PREDICATE_INPUT_AUTHORITY;"
    "LEARNING_IS_NOT_P01_PREDICATE_INPUT_AUTHORITY;"
    "FULL_CORE_AUTONOMY_IS_NOT_P01_PREDICATE_INPUT_AUTHORITY;"
    "RISK_SIZING_INPUT_DOMAINS_ARE_NOT_P01_PREDICATE_INPUT"
)
EVIDENCE_CLASSIFICATION = (
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_AO_OWNER_RATIFIED_INPUT_DOMAIN_IDENTITY;"
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_AN_OWNER_RATIFIED_PREDICATE_IDENTITY;"
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_AM_OWNER_RATIFIED_APPLICABILITY_CLASS;"
    "OWNER_SELECTION=P01_OP_APPLICATION_PREDICATE_INPUT_DOMAIN_TYPED_RECONSTRUCTION_CONTEXT_V1;"
    "RATIFICATION_SCOPE=APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_AND_BOUNDARY_ONLY;"
    "STRUCTURAL_REUSE_ONLY=P01_APPLICATION_PREDICATE_IDENTITY_CONTRACT_V1;"
    "NAVIGATION=MAP_OF_TRUTH_NON_SSOT;"
    "INTERPRETATION=NONE;"
    "HYPOTHESIS=NONE;"
    "REJECTED=CONCRETE_MEMBERS_TRUE_FALSE_FORMULA_OPERATOR_SIGN_VALUE_ZERO_ABSENCE_PROTECTED_SURFACES;"
    "UNRESOLVED=CONCRETE_MEMBERS_REQUIRED_OPTIONAL_TRUE_RULE_FALSE_RULE_READINESS_FRESHNESS_NORMALIZATION;"
    "UNSPECIFIED=P01_PREDICATE_CONCRETE_INPUT_MEMBERS_AND_TERM_SEMANTICS_REMAIN_UNSPECIFIED"
)
_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")
_FORBIDDEN_IDENTITY_TOKENS: tuple[str, ...] = (
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
    "wiresendpermitted",
    "step29p",
    "canary",
    "marginmode",
    "bullbear",
    "learning",
    "promotion",
    "risksizing",
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
    name
    for name in P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_REQUIRED_FIELDS
    if name != "provenance_digest"
)


class P01ApplicationPredicateInputDomainIdentityContractError(ValueError):
    """Fail-closed P01 predicate input-domain identity contract violation."""


def _fold(value: str) -> str:
    return str(value or "").strip().lower().replace("_", "").replace("-", "").replace(".", "")


def _require_non_empty_str(*, field: str, raw: Any) -> str:
    if raw is None:
        raise P01ApplicationPredicateInputDomainIdentityContractError(f"P01_FIELD_MISSING:{field}")
    if isinstance(raw, bool) or not isinstance(raw, str):
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            f"P01_FIELD_NOT_STRING:{field}"
        )
    text = raw.strip()
    if text == "" or text != raw:
        raise P01ApplicationPredicateInputDomainIdentityContractError(f"P01_FIELD_MISSING:{field}")
    return text


def _sha256_hex(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _canonical_json(payload: Mapping[str, str]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_p01_application_predicate_input_domain_identity_digest_v1(
    canonical: Mapping[str, str],
) -> str:
    payload = {
        key: canonical[key]
        for key in P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_REQUIRED_FIELDS
        if key != "provenance_digest"
    }
    return _sha256_hex(_canonical_json(payload))


def attach_p01_application_predicate_input_domain_identity_digest_v1(
    fields: Mapping[str, Any],
) -> dict[str, Any]:
    canonical: dict[str, str] = {}
    for canonical_name in P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_REQUIRED_FIELDS:
        if canonical_name == "provenance_digest":
            continue
        if canonical_name not in fields:
            raise P01ApplicationPredicateInputDomainIdentityContractError(
                f"P01_FIELD_MISSING:{canonical_name}"
            )
        raw = fields[canonical_name]
        canonical[canonical_name] = "" if raw is None else str(raw)
    attached = dict(fields)
    attached["provenance_digest"] = (
        compute_p01_application_predicate_input_domain_identity_digest_v1(canonical)
    )
    return attached


def _require_true_pin(*, raw: str, error: str) -> None:
    if raw != TRUE_PIN or raw.lower() != "true":
        raise P01ApplicationPredicateInputDomainIdentityContractError(error)


def _require_false_pin(*, raw: str, error: str) -> None:
    if raw.lower() == "true" or raw != FALSE_PIN:
        raise P01ApplicationPredicateInputDomainIdentityContractError(error)


def _reject_forbidden_identity(*, field: str, raw: str) -> None:
    folded = _fold(raw)
    _ = field
    if folded == _fold(INPUT_DOMAIN_CLASS):
        return
    if folded == _fold(ALLOWED_INPUT_CLASS):
        return
    if folded == _fold(PREDICATE_MODEL):
        return
    for token in _FORBIDDEN_IDENTITY_TOKENS:
        if token == folded or token in folded:
            raise P01ApplicationPredicateInputDomainIdentityContractError(
                "P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_INFERRED_FORBIDDEN"
            )
    if folded in _ZERO_OR_FALSE_TOKENS:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_INFERRED_FORBIDDEN"
        )


@dataclass(frozen=True)
class P01ApplicationPredicateInputDomainIdentityContractV1:
    """Typed immutable P01 predicate input-domain identity. Not members."""

    p01_application_predicate_input_domain_identity_contract_id: str
    p01_application_predicate_input_domain_identity_contract_version: str
    parent_p01_application_predicate_identity_contract_schema_class: str
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
    p01_application_predicate_identity_resolved_status: str
    p01_application_predicate_model: str
    p01_predicate_input_domain_identity_resolved_status: str
    p01_predicate_input_domain_boundary_resolved_status: str
    p01_predicate_input_domain_class: str
    p01_predicate_input_domain_typed: str
    p01_predicate_input_domain_governed: str
    p01_predicate_input_domain_must_remain_inside_existing_reconstruction_boundary: str
    p01_predicate_input_domain_is_not_account_equity_authority: str
    p01_predicate_input_domain_is_not_parallel_producer: str
    p01_predicate_input_domain_is_not_trading_logic_authority: str
    allowed_input_class: str
    input_domain_is_closed_world: str
    input_domain_default: str
    input_domain_authority_effect: str
    new_authority_owner: str
    new_parallel_producer: str
    new_universe: str
    cross_system_inputs_allowed: str
    trading_logic_inputs_allowed: str
    venue_raw_inputs_allowed: str
    live_execution_state_inputs_allowed: str
    unratified_fact_admission: str
    implicit_input_promotion: str
    foreign_system_state_promotion: str
    missing_required_input_result: str
    malformed_input_result: str
    contradictory_input_result: str
    unsupported_input_result: str
    unratified_input_result: str
    does_not_apply_requires_explicit_false_rule: str
    missing_does_not_mean_does_not_apply: str
    zero_does_not_mean_does_not_apply: str
    absence_does_not_mean_does_not_apply: str
    reconstruction_incomplete_does_not_mean_does_not_apply: str
    p01_application_predicate_input_domain_resolved_status: str
    p01_predicate_concrete_input_members_resolved_status: str
    p01_predicate_required_fields_resolved_status: str
    p01_predicate_optional_fields_resolved_status: str
    p01_application_true_rule_resolved_status: str
    p01_application_false_rule_resolved_status: str
    p01_input_readiness_rule_resolved_status: str
    p01_input_freshness_rule_resolved_status: str
    p01_input_normalization_rule_resolved_status: str
    identity_does_not_ratify_concrete_members: str
    identity_does_not_ratify_required_fields: str
    identity_does_not_ratify_optional_fields: str
    identity_does_not_ratify_true_rule: str
    identity_does_not_ratify_false_rule: str
    identity_does_not_ratify_formula: str
    identity_does_not_ratify_operator: str
    identity_does_not_ratify_sign: str
    identity_does_not_ratify_source_mapping: str
    identity_does_not_close_p01_term_semantics: str
    master_v2_is_not_p01_predicate_input_authority: str
    double_play_is_not_p01_predicate_input_authority: str
    top20_is_not_p01_predicate_input_authority: str
    learning_is_not_p01_predicate_input_authority: str
    full_core_autonomy_is_not_p01_predicate_input_authority: str
    venue_raw_is_not_p01_predicate_input_authority: str
    step_29p_is_not_p01_predicate_input_authority: str
    live_account_bound_is_not_p01_predicate_input_authority: str
    u04_u05_u06_input_inheritance_forbidden: str
    risk_sizing_input_domains_are_not_p01_predicate_input: str
    missing_input_fail_closed: str
    malformed_input_fail_closed: str
    rejected_application_predicate_input_domain_identity_inferences: str
    remaining_unresolved_semantics: str
    evidence_classification: str
    contradiction_state: str
    term_semantics_resolved_status: str
    unspecified_closed_status: str
    p01_runtime_instance_present: str
    p01_authority_effect: str
    p01_application_predicate_input_domain_identity_contract_authority_effect: str
    provenance_digest: str

    def __post_init__(self) -> None:
        _validate_p01_application_predicate_input_domain_identity_contract_v1(self)

    def to_canonical_dict(self) -> dict[str, str]:
        values = {name: getattr(self, name) for name in _VECTOR_FIELDS}
        values["provenance_digest"] = self.provenance_digest
        return {
            key: values[key]
            for key in P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_REQUIRED_FIELDS
        }


def _validate_p01_application_predicate_input_domain_identity_contract_v1(
    contract: P01ApplicationPredicateInputDomainIdentityContractV1,
) -> None:
    if P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_CONTRACT_SCHEMA_PRESENT is not True:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_CONTRACT_SCHEMA_PRESENT_REQUIRED"
        )
    if P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_CONTRACT_RUNTIME_INSTANCE_PRESENT is True:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_RUNTIME_INSTANCE_FORBIDDEN"
        )
    if P01_RUNTIME_INSTANCE_PRESENT is True:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_RUNTIME_INSTANCE_FORBIDDEN"
        )
    if P01_TERM_SET_RESOLVED is not True:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_TERM_SET_RESOLVED_REQUIRED"
        )
    if P01_VALUE_UNIT_CLASS_RESOLVED is not True:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_VALUE_UNIT_CLASS_RESOLVED_REQUIRED"
        )
    if P01_APPLICATION_PREDICATE_IDENTITY_RESOLVED is not True:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_APPLICATION_PREDICATE_IDENTITY_RESOLVED_REQUIRED"
        )
    if P01_PREDICATE_INPUT_DOMAIN_IDENTITY_RESOLVED is not True:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_PREDICATE_INPUT_DOMAIN_IDENTITY_RESOLVED_REQUIRED"
        )
    if P01_PREDICATE_INPUT_DOMAIN_BOUNDARY_RESOLVED is not True:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_PREDICATE_INPUT_DOMAIN_BOUNDARY_RESOLVED_REQUIRED"
        )
    if P01_PREDICATE_INPUT_DOMAIN_TYPED is not True:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_PREDICATE_INPUT_DOMAIN_TYPED_REQUIRED"
        )
    if P01_PREDICATE_INPUT_DOMAIN_GOVERNED is not True:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_PREDICATE_INPUT_DOMAIN_GOVERNED_REQUIRED"
        )
    if P01_PREDICATE_INPUT_DOMAIN_IS_CLOSED_WORLD is not True:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_PREDICATE_INPUT_DOMAIN_IS_CLOSED_WORLD_REQUIRED"
        )
    if P01_APPLICATION_PREDICATE_INPUT_DOMAIN_RESOLVED is True:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_APPLICATION_PREDICATE_INPUT_DOMAIN_RESOLVED_PIN_FORBIDDEN"
        )
    if P01_PREDICATE_CONCRETE_INPUT_MEMBERS_RESOLVED is True:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_PREDICATE_CONCRETE_INPUT_MEMBERS_RESOLVED_PIN_FORBIDDEN"
        )
    if P01_PREDICATE_REQUIRED_FIELDS_RESOLVED is True:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_PREDICATE_REQUIRED_FIELDS_RESOLVED_PIN_FORBIDDEN"
        )
    if P01_PREDICATE_OPTIONAL_FIELDS_RESOLVED is True:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_PREDICATE_OPTIONAL_FIELDS_RESOLVED_PIN_FORBIDDEN"
        )
    if P01_APPLICATION_TRUE_RULE_RESOLVED is True:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_APPLICATION_TRUE_RULE_RESOLVED_PIN_FORBIDDEN"
        )
    if P01_APPLICATION_FALSE_RULE_RESOLVED is True:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_APPLICATION_FALSE_RULE_RESOLVED_PIN_FORBIDDEN"
        )
    if P01_INPUT_READINESS_RULE_RESOLVED is True:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_INPUT_READINESS_RULE_RESOLVED_PIN_FORBIDDEN"
        )
    if P01_INPUT_FRESHNESS_RULE_RESOLVED is True:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_INPUT_FRESHNESS_RULE_RESOLVED_PIN_FORBIDDEN"
        )
    if P01_INPUT_NORMALIZATION_RULE_RESOLVED is True:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_INPUT_NORMALIZATION_RULE_RESOLVED_PIN_FORBIDDEN"
        )
    if P01_MEMBER_ROLE_SIGN_UNIT_RESOLVED is True:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_MEMBER_ROLE_SIGN_UNIT_RESOLVED_PIN_FORBIDDEN"
        )
    if P01_COMBINATION_PRECEDENCE_RESOLVED is True:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_COMBINATION_PRECEDENCE_RESOLVED_PIN_FORBIDDEN"
        )
    if P01_TERM_SEMANTICS_RESOLVED is True:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_TERM_SEMANTICS_RESOLVED_PIN_FORBIDDEN"
        )
    if P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED is True:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED_PIN_FORBIDDEN"
        )
    if RECONSTRUCTION_ALGEBRA_COMPLETE is True:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_RECONSTRUCTION_ALGEBRA_COMPLETE_PIN_FORBIDDEN"
        )
    if (
        P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_CONTRACT_AUTHORITY_EFFECT
        != AUTHORITY_EFFECT_NONE
    ):
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_AUTHORITY_EFFECT_MUST_REMAIN_NONE"
        )
    if P01_EXACT_MEMBER_IDENTITY_SET != MEMBER_ID:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_EXACT_MEMBER_IDENTITY_SET_MISMATCH"
        )

    for field in _VECTOR_FIELDS:
        _require_non_empty_str(field=field, raw=getattr(contract, field))
    digest = _require_non_empty_str(field="provenance_digest", raw=contract.provenance_digest)
    if _SHA256_HEX.fullmatch(digest) is None:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_PROVENANCE_DIGEST_MALFORMED"
        )
    expected_digest = compute_p01_application_predicate_input_domain_identity_digest_v1(
        {key: getattr(contract, key) for key in _VECTOR_FIELDS}
    )
    if digest != expected_digest:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_PROVENANCE_DIGEST_MISMATCH"
        )

    if contract.ratification_scope != RATIFICATION_SCOPE:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_RATIFICATION_SCOPE_MISMATCH"
        )
    if contract.selected_option != SELECTED_OPTION:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_SELECTED_OPTION_MISMATCH"
        )
    if contract.p01_term_set_resolved_status != RESOLVED_STATUS_TRUE:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_TERM_SET_RESOLVED_STATUS_MISMATCH"
        )
    if contract.p01_value_unit_class_resolved_status != RESOLVED_STATUS_TRUE:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_VALUE_UNIT_CLASS_RESOLVED_STATUS_MISMATCH"
        )
    if contract.p01_value_unit_class != VALUE_UNIT_CLASS:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_VALUE_UNIT_CLASS_MISMATCH"
        )
    if contract.member_id != MEMBER_ID:
        raise P01ApplicationPredicateInputDomainIdentityContractError("P01_MEMBER_ID_MISMATCH")
    if contract.p01_applicability_class != APPLICABILITY_CLASS:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_APPLICABILITY_CLASS_MISMATCH"
        )
    if contract.p01_application_predicate_identity_resolved_status != RESOLVED_STATUS_TRUE:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_APPLICATION_PREDICATE_IDENTITY_RESOLVED_STATUS_MISMATCH"
        )
    if contract.p01_application_predicate_model != PREDICATE_MODEL:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_APPLICATION_PREDICATE_MODEL_MISMATCH"
        )
    if contract.p01_predicate_input_domain_identity_resolved_status != RESOLVED_STATUS_TRUE:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_PREDICATE_INPUT_DOMAIN_IDENTITY_RESOLVED_STATUS_MISMATCH"
        )
    if contract.p01_predicate_input_domain_boundary_resolved_status != RESOLVED_STATUS_TRUE:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_PREDICATE_INPUT_DOMAIN_BOUNDARY_RESOLVED_STATUS_MISMATCH"
        )
    if contract.p01_predicate_input_domain_class != INPUT_DOMAIN_CLASS:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_PREDICATE_INPUT_DOMAIN_CLASS_MISMATCH"
        )
    _reject_forbidden_identity(
        field="p01_predicate_input_domain_class", raw=contract.p01_predicate_input_domain_class
    )
    if contract.allowed_input_class != ALLOWED_INPUT_CLASS:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_ALLOWED_INPUT_CLASS_MISMATCH"
        )
    if contract.input_domain_default != INPUT_DOMAIN_DEFAULT:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_INPUT_DOMAIN_DEFAULT_MISMATCH"
        )
    if contract.input_domain_authority_effect != AUTHORITY_EFFECT_NONE:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_AUTHORITY_EFFECT_MUST_REMAIN_NONE"
        )
    if contract.remaining_unresolved_semantics != REMAINING_UNRESOLVED_SEMANTICS:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_REMAINING_UNRESOLVED_SEMANTICS_MISMATCH"
        )
    if "P01_PREDICATE_CONCRETE_INPUT_MEMBERS_UNSPECIFIED" not in (
        contract.remaining_unresolved_semantics
    ):
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_PREDICATE_CONCRETE_INPUT_MEMBERS_MUST_REMAIN_UNSPECIFIED"
        )
    if "P01_APPLICATION_TRUE_RULE_UNSPECIFIED" not in contract.remaining_unresolved_semantics:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_APPLICATION_TRUE_RULE_MUST_REMAIN_UNSPECIFIED"
        )
    if "P01_APPLICATION_FALSE_RULE_UNSPECIFIED" not in contract.remaining_unresolved_semantics:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_APPLICATION_FALSE_RULE_MUST_REMAIN_UNSPECIFIED"
        )
    if contract.term_semantics_resolved_status != TERM_SEMANTICS_RESOLVED_STATUS:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_TERM_SEMANTICS_RESOLVED_STATUS_MISMATCH"
        )
    if contract.unspecified_closed_status != UNSPECIFIED_CLOSED_STATUS:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_UNSPECIFIED_CLOSED_STATUS_MISMATCH"
        )
    if contract.contradiction_state != CONTRADICTION_NONE:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_CONTRADICTION_STATE_MISMATCH"
        )
    if (
        contract.rejected_application_predicate_input_domain_identity_inferences
        != REJECTED_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_INFERENCES
    ):
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_REJECTED_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_INFERENCES_MISMATCH"
        )
    if contract.evidence_classification != EVIDENCE_CLASSIFICATION:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_EVIDENCE_CLASSIFICATION_MISMATCH"
        )
    if contract.p01_runtime_instance_present != RUNTIME_INSTANCE_PRESENT_STATUS:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_RUNTIME_INSTANCE_FORBIDDEN"
        )
    if contract.p01_authority_effect != AUTHORITY_EFFECT_NONE:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_AUTHORITY_EFFECT_MUST_REMAIN_NONE"
        )
    if (
        contract.p01_application_predicate_input_domain_identity_contract_authority_effect
        != AUTHORITY_EFFECT_NONE
    ):
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_AUTHORITY_EFFECT_MUST_REMAIN_NONE"
        )
    if contract.parent_p01_application_predicate_identity_contract_schema_class != (
        PARENT_IDENTITY_CONTRACT_SCHEMA_CLASS
    ):
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_PARENT_IDENTITY_SCHEMA_MISMATCH"
        )
    if contract.parent_p01_term_contract_schema_class != PARENT_TERM_CONTRACT_SCHEMA_CLASS:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_PARENT_TERM_SCHEMA_MISMATCH"
        )
    if contract.target_semantic_dimension_id != DIMENSION_ID:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_TARGET_DIMENSION_MISMATCH"
        )
    if contract.policy_id != POLICY_ID or contract.term_id != TERM_ID:
        raise P01ApplicationPredicateInputDomainIdentityContractError("P01_POLICY_OR_TERM_MISMATCH")
    for result_field in (
        "missing_required_input_result",
        "malformed_input_result",
        "contradictory_input_result",
        "unsupported_input_result",
        "unratified_input_result",
    ):
        if getattr(contract, result_field) != UNKNOWN_FAIL_CLOSED:
            raise P01ApplicationPredicateInputDomainIdentityContractError(
                f"P01_{result_field.upper()}_MUST_BE_UNKNOWN_FAIL_CLOSED"
            )
    for forbidden_field in (
        "unratified_fact_admission",
        "implicit_input_promotion",
        "foreign_system_state_promotion",
    ):
        if getattr(contract, forbidden_field) != FORBIDDEN_PIN:
            raise P01ApplicationPredicateInputDomainIdentityContractError(
                f"P01_{forbidden_field.upper()}_MUST_REMAIN_FORBIDDEN"
            )
    _require_false_pin(
        raw=contract.p01_application_predicate_input_domain_resolved_status,
        error="P01_APPLICATION_PREDICATE_INPUT_DOMAIN_RESOLVED_FORBIDDEN",
    )
    _require_false_pin(
        raw=contract.p01_predicate_concrete_input_members_resolved_status,
        error="P01_PREDICATE_CONCRETE_INPUT_MEMBERS_RESOLVED_FORBIDDEN",
    )
    _require_false_pin(
        raw=contract.p01_predicate_required_fields_resolved_status,
        error="P01_PREDICATE_REQUIRED_FIELDS_RESOLVED_FORBIDDEN",
    )
    _require_false_pin(
        raw=contract.p01_predicate_optional_fields_resolved_status,
        error="P01_PREDICATE_OPTIONAL_FIELDS_RESOLVED_FORBIDDEN",
    )
    _require_false_pin(
        raw=contract.p01_application_true_rule_resolved_status,
        error="P01_APPLICATION_TRUE_RULE_RESOLVED_FORBIDDEN",
    )
    _require_false_pin(
        raw=contract.p01_application_false_rule_resolved_status,
        error="P01_APPLICATION_FALSE_RULE_RESOLVED_FORBIDDEN",
    )
    _require_false_pin(
        raw=contract.p01_input_readiness_rule_resolved_status,
        error="P01_INPUT_READINESS_RULE_RESOLVED_FORBIDDEN",
    )
    _require_false_pin(
        raw=contract.p01_input_freshness_rule_resolved_status,
        error="P01_INPUT_FRESHNESS_RULE_RESOLVED_FORBIDDEN",
    )
    _require_false_pin(
        raw=contract.p01_input_normalization_rule_resolved_status,
        error="P01_INPUT_NORMALIZATION_RULE_RESOLVED_FORBIDDEN",
    )
    _require_false_pin(raw=contract.new_authority_owner, error="P01_NEW_AUTHORITY_OWNER_FORBIDDEN")
    _require_false_pin(
        raw=contract.new_parallel_producer, error="P01_NEW_PARALLEL_PRODUCER_FORBIDDEN"
    )
    _require_false_pin(raw=contract.new_universe, error="P01_NEW_UNIVERSE_FORBIDDEN")
    _require_false_pin(
        raw=contract.cross_system_inputs_allowed, error="P01_CROSS_SYSTEM_INPUTS_FORBIDDEN"
    )
    _require_false_pin(
        raw=contract.trading_logic_inputs_allowed, error="P01_TRADING_LOGIC_INPUTS_FORBIDDEN"
    )
    _require_false_pin(
        raw=contract.venue_raw_inputs_allowed, error="P01_VENUE_RAW_INPUTS_FORBIDDEN"
    )
    _require_false_pin(
        raw=contract.live_execution_state_inputs_allowed,
        error="P01_LIVE_EXECUTION_STATE_INPUTS_FORBIDDEN",
    )
    for field in (
        "p01_predicate_input_domain_typed",
        "p01_predicate_input_domain_governed",
        "p01_predicate_input_domain_must_remain_inside_existing_reconstruction_boundary",
        "p01_predicate_input_domain_is_not_account_equity_authority",
        "p01_predicate_input_domain_is_not_parallel_producer",
        "p01_predicate_input_domain_is_not_trading_logic_authority",
        "input_domain_is_closed_world",
        "does_not_apply_requires_explicit_false_rule",
        "missing_does_not_mean_does_not_apply",
        "zero_does_not_mean_does_not_apply",
        "absence_does_not_mean_does_not_apply",
        "reconstruction_incomplete_does_not_mean_does_not_apply",
        "identity_does_not_ratify_concrete_members",
        "identity_does_not_ratify_required_fields",
        "identity_does_not_ratify_optional_fields",
        "identity_does_not_ratify_true_rule",
        "identity_does_not_ratify_false_rule",
        "identity_does_not_ratify_formula",
        "identity_does_not_ratify_operator",
        "identity_does_not_ratify_sign",
        "identity_does_not_ratify_source_mapping",
        "identity_does_not_close_p01_term_semantics",
        "master_v2_is_not_p01_predicate_input_authority",
        "double_play_is_not_p01_predicate_input_authority",
        "top20_is_not_p01_predicate_input_authority",
        "learning_is_not_p01_predicate_input_authority",
        "full_core_autonomy_is_not_p01_predicate_input_authority",
        "venue_raw_is_not_p01_predicate_input_authority",
        "step_29p_is_not_p01_predicate_input_authority",
        "live_account_bound_is_not_p01_predicate_input_authority",
        "u04_u05_u06_input_inheritance_forbidden",
        "risk_sizing_input_domains_are_not_p01_predicate_input",
        "missing_input_fail_closed",
        "malformed_input_fail_closed",
    ):
        _require_true_pin(raw=getattr(contract, field), error=f"P01_{field.upper()}_REQUIRED")


def build_p01_application_predicate_input_domain_identity_contract_v1(
    *,
    p01_application_predicate_input_domain_identity_contract_id: str,
    **overrides: Any,
) -> P01ApplicationPredicateInputDomainIdentityContractV1:
    parent = build_p01_application_predicate_identity_contract_v1(
        p01_application_predicate_identity_contract_id=(
            "SYNTHETIC_P01_APPLICATION_PREDICATE_IDENTITY_CONTRACT_ID"
        )
    )
    if parent.p01_authority_effect != AUTHORITY_EFFECT_NONE:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_PARENT_AUTHORITY_EFFECT_MUST_REMAIN_NONE"
        )
    payload: dict[str, Any] = dict(overrides)
    defaults: dict[str, str] = {
        "p01_application_predicate_input_domain_identity_contract_id": (
            p01_application_predicate_input_domain_identity_contract_id
        ),
        "p01_application_predicate_input_domain_identity_contract_version": CONTRACT_VERSION,
        "parent_p01_application_predicate_identity_contract_schema_class": (
            PARENT_IDENTITY_CONTRACT_SCHEMA_CLASS
        ),
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
        "p01_application_predicate_identity_resolved_status": RESOLVED_STATUS_TRUE,
        "p01_application_predicate_model": PREDICATE_MODEL,
        "p01_predicate_input_domain_identity_resolved_status": RESOLVED_STATUS_TRUE,
        "p01_predicate_input_domain_boundary_resolved_status": RESOLVED_STATUS_TRUE,
        "p01_predicate_input_domain_class": INPUT_DOMAIN_CLASS,
        "p01_predicate_input_domain_typed": TRUE_PIN,
        "p01_predicate_input_domain_governed": TRUE_PIN,
        "p01_predicate_input_domain_must_remain_inside_existing_reconstruction_boundary": TRUE_PIN,
        "p01_predicate_input_domain_is_not_account_equity_authority": TRUE_PIN,
        "p01_predicate_input_domain_is_not_parallel_producer": TRUE_PIN,
        "p01_predicate_input_domain_is_not_trading_logic_authority": TRUE_PIN,
        "allowed_input_class": ALLOWED_INPUT_CLASS,
        "input_domain_is_closed_world": CLOSED_WORLD_PIN,
        "input_domain_default": INPUT_DOMAIN_DEFAULT,
        "input_domain_authority_effect": AUTHORITY_EFFECT_NONE,
        "new_authority_owner": FALSE_PIN,
        "new_parallel_producer": FALSE_PIN,
        "new_universe": FALSE_PIN,
        "cross_system_inputs_allowed": FALSE_PIN,
        "trading_logic_inputs_allowed": FALSE_PIN,
        "venue_raw_inputs_allowed": FALSE_PIN,
        "live_execution_state_inputs_allowed": FALSE_PIN,
        "unratified_fact_admission": FORBIDDEN_PIN,
        "implicit_input_promotion": FORBIDDEN_PIN,
        "foreign_system_state_promotion": FORBIDDEN_PIN,
        "missing_required_input_result": UNKNOWN_FAIL_CLOSED,
        "malformed_input_result": UNKNOWN_FAIL_CLOSED,
        "contradictory_input_result": UNKNOWN_FAIL_CLOSED,
        "unsupported_input_result": UNKNOWN_FAIL_CLOSED,
        "unratified_input_result": UNKNOWN_FAIL_CLOSED,
        "does_not_apply_requires_explicit_false_rule": TRUE_PIN,
        "missing_does_not_mean_does_not_apply": TRUE_PIN,
        "zero_does_not_mean_does_not_apply": TRUE_PIN,
        "absence_does_not_mean_does_not_apply": TRUE_PIN,
        "reconstruction_incomplete_does_not_mean_does_not_apply": TRUE_PIN,
        "p01_application_predicate_input_domain_resolved_status": RESOLVED_STATUS_FALSE,
        "p01_predicate_concrete_input_members_resolved_status": RESOLVED_STATUS_FALSE,
        "p01_predicate_required_fields_resolved_status": RESOLVED_STATUS_FALSE,
        "p01_predicate_optional_fields_resolved_status": RESOLVED_STATUS_FALSE,
        "p01_application_true_rule_resolved_status": RESOLVED_STATUS_FALSE,
        "p01_application_false_rule_resolved_status": RESOLVED_STATUS_FALSE,
        "p01_input_readiness_rule_resolved_status": RESOLVED_STATUS_FALSE,
        "p01_input_freshness_rule_resolved_status": RESOLVED_STATUS_FALSE,
        "p01_input_normalization_rule_resolved_status": RESOLVED_STATUS_FALSE,
        "identity_does_not_ratify_concrete_members": TRUE_PIN,
        "identity_does_not_ratify_required_fields": TRUE_PIN,
        "identity_does_not_ratify_optional_fields": TRUE_PIN,
        "identity_does_not_ratify_true_rule": TRUE_PIN,
        "identity_does_not_ratify_false_rule": TRUE_PIN,
        "identity_does_not_ratify_formula": TRUE_PIN,
        "identity_does_not_ratify_operator": TRUE_PIN,
        "identity_does_not_ratify_sign": TRUE_PIN,
        "identity_does_not_ratify_source_mapping": TRUE_PIN,
        "identity_does_not_close_p01_term_semantics": TRUE_PIN,
        "master_v2_is_not_p01_predicate_input_authority": TRUE_PIN,
        "double_play_is_not_p01_predicate_input_authority": TRUE_PIN,
        "top20_is_not_p01_predicate_input_authority": TRUE_PIN,
        "learning_is_not_p01_predicate_input_authority": TRUE_PIN,
        "full_core_autonomy_is_not_p01_predicate_input_authority": TRUE_PIN,
        "venue_raw_is_not_p01_predicate_input_authority": TRUE_PIN,
        "step_29p_is_not_p01_predicate_input_authority": TRUE_PIN,
        "live_account_bound_is_not_p01_predicate_input_authority": TRUE_PIN,
        "u04_u05_u06_input_inheritance_forbidden": TRUE_PIN,
        "risk_sizing_input_domains_are_not_p01_predicate_input": TRUE_PIN,
        "missing_input_fail_closed": MISSING_INPUT_FAIL_CLOSED,
        "malformed_input_fail_closed": MALFORMED_INPUT_FAIL_CLOSED,
        "rejected_application_predicate_input_domain_identity_inferences": (
            REJECTED_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_INFERENCES
        ),
        "remaining_unresolved_semantics": REMAINING_UNRESOLVED_SEMANTICS,
        "evidence_classification": EVIDENCE_CLASSIFICATION,
        "contradiction_state": CONTRADICTION_NONE,
        "term_semantics_resolved_status": TERM_SEMANTICS_RESOLVED_STATUS,
        "unspecified_closed_status": UNSPECIFIED_CLOSED_STATUS,
        "p01_runtime_instance_present": RUNTIME_INSTANCE_PRESENT_STATUS,
        "p01_authority_effect": AUTHORITY_EFFECT_NONE,
        "p01_application_predicate_input_domain_identity_contract_authority_effect": (
            AUTHORITY_EFFECT_NONE
        ),
    }
    for key, value in defaults.items():
        payload.setdefault(key, value)
    missing = [name for name in _VECTOR_FIELDS if name not in payload]
    if missing:
        raise P01ApplicationPredicateInputDomainIdentityContractError(
            "P01_FIELD_MISSING:" + ",".join(missing)
        )
    attached = attach_p01_application_predicate_input_domain_identity_digest_v1(payload)
    return P01ApplicationPredicateInputDomainIdentityContractV1(
        **{
            name: attached[name]
            for name in P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_REQUIRED_FIELDS
        }
    )


def reject_p01_unratified_fact_admission_v1(*, fact: str) -> None:
    """Unratified facts cannot enter the predicate input domain."""

    _ = fact
    raise P01ApplicationPredicateInputDomainIdentityContractError(
        "P01_UNRATIFIED_FACT_ADMISSION_FORBIDDEN"
    )


def reject_p01_implicit_input_promotion_v1(*, source: str) -> None:
    """Implicit promotion into the predicate input domain is forbidden."""

    _ = source
    raise P01ApplicationPredicateInputDomainIdentityContractError(
        "P01_IMPLICIT_INPUT_PROMOTION_FORBIDDEN"
    )


def reject_p01_foreign_system_state_promotion_v1(*, source: str) -> None:
    """Foreign system state cannot become predicate input."""

    _ = source
    raise P01ApplicationPredicateInputDomainIdentityContractError(
        "P01_FOREIGN_SYSTEM_STATE_PROMOTION_FORBIDDEN"
    )


def reject_p01_concrete_input_member_inference_v1(*, member: str) -> None:
    """Input-domain identity cannot invent concrete members."""

    _ = member
    raise P01ApplicationPredicateInputDomainIdentityContractError(
        "P01_IDENTITY_IS_NOT_CONCRETE_MEMBERS"
    )


def reject_p01_missing_required_input_as_does_not_apply_v1(*, input_name: str) -> None:
    """Missing required input must fail closed as UNKNOWN, not DOES_NOT_APPLY."""

    _ = input_name
    raise P01ApplicationPredicateInputDomainIdentityContractError(
        "P01_MISSING_IS_NOT_DOES_NOT_APPLY"
    )
