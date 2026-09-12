"""Typed P01 value unit class ratification.

Owner-ratifies ABSOLUTE_MONETARY_REDUCTION_AMOUNT for the already-ratified
P01 member. Unit ratification is not formula, operator, sign, source,
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
    P01_APPLICABILITY_RESOLVED,
    P01_COMBINATION_PRECEDENCE_RESOLVED,
    P01_DIRECT_ADDITIVE_SUBTRACTION_COMPATIBLE,
    P01_EXACT_MEMBER_IDENTITY_SET,
    P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED,
    P01_MEMBER_ROLE_SIGN_UNIT_RESOLVED,
    P01_PARENT_DIMENSION_COMPATIBILITY,
    P01_PARENT_DIMENSION_IS_NOT_AUTHORITY_SOURCE,
    P01_REQUIRES_DIMENSIONAL_TRANSFORMATION,
    P01_RUNTIME_INSTANCE_PRESENT,
    P01_SEMANTIC_DIMENSION,
    P01_SETTLEMENT_CURRENCY_IS_NOT_UNIT_IDENTITY,
    P01_TERM_SEMANTICS_RESOLVED,
    P01_TERM_SET_RESOLVED,
    P01_UNIT_IDENTITY_IS_DISTINCT_FROM_AUTHORITY_IDENTITY,
    P01_UNIT_IDENTITY_IS_DISTINCT_FROM_MEMBER_IDENTITY,
    P01_VALUE_UNIT_CLASS,
    P01_VALUE_UNIT_CLASS_CONTRACT_AUTHORITY_EFFECT,
    P01_VALUE_UNIT_CLASS_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_VALUE_UNIT_CLASS_CONTRACT_SCHEMA_PRESENT,
    P01_VALUE_UNIT_CLASS_REQUIRED_FIELDS,
    P01_VALUE_UNIT_CLASS_RESOLVED,
    P01_VALUE_UNIT_CLASS_SELECTED_OPTION,
    P01_ZERO_ABSENCE_NA_RESOLVED,
    RECONSTRUCTION_ALGEBRA_COMPLETE,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_exact_member_identity_contract_v1 import (
    MEMBER_ID,
    REMAINING_UNRESOLVED_SEMANTICS as PARENT_REMAINING_UNRESOLVED_SEMANTICS,
    SCHEMA_CLASS as PARENT_IDENTITY_SCHEMA_CLASS,
    build_p01_exact_member_identity_contract_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_haircut_reserve_depletion_term_contract_v1 import (
    SCHEMA_CLASS as P01_TERM_SCHEMA_CLASS,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.reconstruction_algebra_contract_v1 import (
    CONTRADICTION_NONE,
    DIMENSION_ID,
    TERM_P01_HAIRCUT_RESERVE_DEPLETION,
)

SCHEMA_CLASS = "P01_VALUE_UNIT_CLASS_CONTRACT_V1"
CONTRACT_VERSION = "v1"
POLICY_ID = "P01"
TERM_ID = TERM_P01_HAIRCUT_RESERVE_DEPLETION
PARENT_IDENTITY_CONTRACT_SCHEMA_CLASS = PARENT_IDENTITY_SCHEMA_CLASS
PARENT_TERM_CONTRACT_SCHEMA_CLASS = P01_TERM_SCHEMA_CLASS
RATIFICATION_SCOPE = "VALUE_UNIT_CLASS_ONLY"
SELECTED_OPTION = P01_VALUE_UNIT_CLASS_SELECTED_OPTION
VALUE_UNIT_CLASS = P01_VALUE_UNIT_CLASS
SEMANTIC_DIMENSION = P01_SEMANTIC_DIMENSION
PARENT_DIMENSION_COMPATIBILITY = P01_PARENT_DIMENSION_COMPATIBILITY
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
REQUIRES_DIMENSIONAL_TRANSFORMATION_STATUS = "false"
DIRECT_ADDITIVE_SUBTRACTION_COMPATIBLE_STATUS = "true"
REMAINING_UNRESOLVED_SEMANTICS = PARENT_REMAINING_UNRESOLVED_SEMANTICS.replace(
    "P01_VALUE_UNIT_CLASS_UNSPECIFIED,", ""
)
REJECTED_UNIT_CLASS_INFERENCES = (
    "USDC_SETTLEMENT_IS_NOT_P01_UNIT_IDENTITY;"
    "PARENT_DIMENSION_CURRENCY_IS_NOT_P01_UNIT_IDENTITY;"
    "RATIO_PERCENT_BPS_FRACTION_ARE_NOT_THIS_CLASS;"
    "CONTRACTS_QTY_IS_NOT_P01_UNIT;"
    "PYTHON_NUMERIC_TYPE_IS_NOT_P01_UNIT;"
    "U04_U05_U06_UNITS_ARE_NOT_P01_UNIT;"
    "VENUE_FIELD_UNIT_IS_NOT_P01_UNIT;"
    "MARGIN_OR_NOTIONAL_AMOUNT_IS_NOT_THIS_CLASS;"
    "UNIT_IS_NOT_FORMULA;"
    "ADDITIVE_SUBTRACTION_COMPATIBLE_IS_NOT_OPERATOR"
)
EVIDENCE_CLASSIFICATION = (
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_AL_OWNER_RATIFIED_VALUE_UNIT_CLASS;"
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_AK_OWNER_RATIFIED_EXACT_MEMBER_IDENTITY;"
    "OWNER_SELECTION=P01_OP_VU_ABSOLUTE_MONETARY_REDUCTION_V1;"
    "RATIFICATION_SCOPE=VALUE_UNIT_CLASS_ONLY;"
    "STRUCTURAL_REUSE_ONLY=P01_EXACT_MEMBER_IDENTITY_CONTRACT_V1;"
    "NAVIGATION=MAP_OF_TRUTH_NON_SSOT;"
    "INTERPRETATION=NONE;"
    "HYPOTHESIS=NONE;"
    "REJECTED=RATIO_PERCENT_BPS_SETTLEMENT_USDC_VENUE_U04_U05_U06_PYTHON_NUMERIC;"
    "UNRESOLVED=APPLICABILITY_INCLUSION_EMBEDDING_OVERLAP_PROVENANCE_FRESHNESS_ROLE_SIGN_ZERO_COMBINATION;"
    "UNSPECIFIED=P01_TERM_SEMANTICS_REMAIN_UNSPECIFIED"
)
_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")
_FORBIDDEN_UNIT_TOKENS: tuple[str, ...] = (
    "ratio",
    "percent",
    "percentage",
    "bps",
    "fraction",
    "contractsqty",
    "usdc",
    "usd",
    "availeq",
    "totaleq",
    "float",
    "decimal",
    "notional",
    "marginreserve",
    "equity=equity-p01",
)
_VECTOR_FIELDS: tuple[str, ...] = tuple(
    name for name in P01_VALUE_UNIT_CLASS_REQUIRED_FIELDS if name != "provenance_digest"
)


class P01ValueUnitClassContractError(ValueError):
    """Fail-closed P01 value unit class contract violation."""


def _fold(value: str) -> str:
    return str(value or "").strip().lower().replace("_", "").replace("-", "").replace(".", "")


def _require_non_empty_str(*, field: str, raw: Any) -> str:
    if raw is None:
        raise P01ValueUnitClassContractError(f"P01_FIELD_MISSING:{field}")
    if isinstance(raw, bool) or not isinstance(raw, str):
        raise P01ValueUnitClassContractError(f"P01_FIELD_NOT_STRING:{field}")
    text = raw.strip()
    if text == "" or text != raw:
        raise P01ValueUnitClassContractError(f"P01_FIELD_MISSING:{field}")
    return text


def _sha256_hex(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _canonical_json(payload: Mapping[str, str]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_p01_value_unit_class_digest_v1(canonical: Mapping[str, str]) -> str:
    payload = {
        key: canonical[key]
        for key in P01_VALUE_UNIT_CLASS_REQUIRED_FIELDS
        if key != "provenance_digest"
    }
    return _sha256_hex(_canonical_json(payload))


def attach_p01_value_unit_class_digest_v1(fields: Mapping[str, Any]) -> dict[str, Any]:
    canonical: dict[str, str] = {}
    for canonical_name in P01_VALUE_UNIT_CLASS_REQUIRED_FIELDS:
        if canonical_name == "provenance_digest":
            continue
        if canonical_name not in fields:
            raise P01ValueUnitClassContractError(f"P01_FIELD_MISSING:{canonical_name}")
        raw = fields[canonical_name]
        canonical[canonical_name] = "" if raw is None else str(raw)
    attached = dict(fields)
    attached["provenance_digest"] = compute_p01_value_unit_class_digest_v1(canonical)
    return attached


def _require_true_pin(*, raw: str, error: str) -> None:
    if raw != TRUE_PIN or raw.lower() != "true":
        raise P01ValueUnitClassContractError(error)


def _require_false_pin(*, raw: str, error: str) -> None:
    if raw.lower() == "true" or raw != FALSE_PIN:
        raise P01ValueUnitClassContractError(error)


def _reject_forbidden_unit(*, field: str, raw: str) -> None:
    folded = _fold(raw)
    _ = field
    if folded == _fold(VALUE_UNIT_CLASS):
        return
    for token in _FORBIDDEN_UNIT_TOKENS:
        if token == folded or token in folded:
            raise P01ValueUnitClassContractError("P01_VALUE_UNIT_CLASS_INFERRED_FORBIDDEN")


@dataclass(frozen=True)
class P01ValueUnitClassContractV1:
    """Typed immutable P01 value unit class ratification. Not a formula."""

    p01_value_unit_class_contract_id: str
    p01_value_unit_class_contract_version: str
    parent_p01_exact_member_identity_contract_schema_class: str
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
    p01_semantic_dimension: str
    p01_parent_dimension_compatibility: str
    p01_requires_dimensional_transformation: str
    p01_direct_additive_subtraction_compatible: str
    p01_unit_identity_is_distinct_from_authority_identity: str
    p01_unit_identity_is_distinct_from_member_identity: str
    p01_settlement_currency_is_not_unit_identity: str
    p01_parent_dimension_is_not_authority_source: str
    unit_does_not_ratify_formula: str
    unit_does_not_ratify_operator: str
    unit_does_not_ratify_sign: str
    unit_does_not_ratify_applicability: str
    unit_does_not_ratify_source_mapping: str
    unit_does_not_close_p01_term_semantics: str
    unit_does_not_close_haircut_reserve_depletion_unspecified: str
    p01_value_unit_class_is_not_ratio: str
    p01_value_unit_class_is_not_percentage: str
    p01_value_unit_class_is_not_bps: str
    p01_value_unit_class_is_not_contracts_qty: str
    p01_value_unit_class_is_not_python_numeric_type: str
    p01m_governed_deployability_conservatism_reduction_is_not_haircut_alias: str
    p01m_governed_deployability_conservatism_reduction_is_not_reserve_alias: str
    p01m_governed_deployability_conservatism_reduction_is_not_depletion_alias: str
    p01m_governed_deployability_conservatism_reduction_is_not_u04: str
    p01m_governed_deployability_conservatism_reduction_is_not_u05: str
    p01m_governed_deployability_conservatism_reduction_is_not_u06: str
    p01m_governed_deployability_conservatism_reduction_is_not_venue_raw: str
    p01m_governed_deployability_conservatism_reduction_is_not_availeq: str
    p01m_governed_deployability_conservatism_reduction_is_not_eq: str
    p01m_governed_deployability_conservatism_reduction_is_not_totaleq: str
    p01m_governed_deployability_conservatism_reduction_is_not_canary_envelope: str
    p01m_governed_deployability_conservatism_reduction_is_not_margin_reserve_alias: str
    p01m_governed_deployability_conservatism_reduction_is_not_future_fee_permission: str
    p01_applicability_resolved_status: str
    p01_member_role_sign_unit_resolved_status: str
    missing_input_fail_closed: str
    malformed_input_fail_closed: str
    rejected_unit_class_inferences: str
    remaining_unresolved_semantics: str
    evidence_classification: str
    contradiction_state: str
    term_semantics_resolved_status: str
    unspecified_closed_status: str
    p01_runtime_instance_present: str
    p01_authority_effect: str
    p01_value_unit_class_contract_authority_effect: str
    provenance_digest: str

    def __post_init__(self) -> None:
        _validate_p01_value_unit_class_contract_v1(self)

    def to_canonical_dict(self) -> dict[str, str]:
        values = {name: getattr(self, name) for name in _VECTOR_FIELDS}
        values["provenance_digest"] = self.provenance_digest
        return {key: values[key] for key in P01_VALUE_UNIT_CLASS_REQUIRED_FIELDS}


def _validate_p01_value_unit_class_contract_v1(
    contract: P01ValueUnitClassContractV1,
) -> None:
    if P01_VALUE_UNIT_CLASS_CONTRACT_SCHEMA_PRESENT is not True:
        raise P01ValueUnitClassContractError(
            "P01_VALUE_UNIT_CLASS_CONTRACT_SCHEMA_PRESENT_REQUIRED"
        )
    if P01_VALUE_UNIT_CLASS_CONTRACT_RUNTIME_INSTANCE_PRESENT is True:
        raise P01ValueUnitClassContractError("P01_RUNTIME_INSTANCE_FORBIDDEN")
    if P01_RUNTIME_INSTANCE_PRESENT is True:
        raise P01ValueUnitClassContractError("P01_RUNTIME_INSTANCE_FORBIDDEN")
    if P01_TERM_SET_RESOLVED is not True:
        raise P01ValueUnitClassContractError("P01_TERM_SET_RESOLVED_REQUIRED")
    if P01_VALUE_UNIT_CLASS_RESOLVED is not True:
        raise P01ValueUnitClassContractError("P01_VALUE_UNIT_CLASS_RESOLVED_REQUIRED")
    if P01_REQUIRES_DIMENSIONAL_TRANSFORMATION is True:
        raise P01ValueUnitClassContractError(
            "P01_REQUIRES_DIMENSIONAL_TRANSFORMATION_PIN_FORBIDDEN"
        )
    if P01_DIRECT_ADDITIVE_SUBTRACTION_COMPATIBLE is not True:
        raise P01ValueUnitClassContractError("P01_DIRECT_ADDITIVE_SUBTRACTION_COMPATIBLE_REQUIRED")
    if P01_UNIT_IDENTITY_IS_DISTINCT_FROM_AUTHORITY_IDENTITY is not True:
        raise P01ValueUnitClassContractError("P01_UNIT_AUTHORITY_DISTINCTNESS_REQUIRED")
    if P01_UNIT_IDENTITY_IS_DISTINCT_FROM_MEMBER_IDENTITY is not True:
        raise P01ValueUnitClassContractError("P01_UNIT_MEMBER_DISTINCTNESS_REQUIRED")
    if P01_SETTLEMENT_CURRENCY_IS_NOT_UNIT_IDENTITY is not True:
        raise P01ValueUnitClassContractError("P01_SETTLEMENT_IS_NOT_UNIT_IDENTITY_REQUIRED")
    if P01_PARENT_DIMENSION_IS_NOT_AUTHORITY_SOURCE is not True:
        raise P01ValueUnitClassContractError(
            "P01_PARENT_DIMENSION_IS_NOT_AUTHORITY_SOURCE_REQUIRED"
        )
    if P01_APPLICABILITY_RESOLVED is True:
        raise P01ValueUnitClassContractError("P01_APPLICABILITY_RESOLVED_PIN_FORBIDDEN")
    if P01_MEMBER_ROLE_SIGN_UNIT_RESOLVED is True:
        raise P01ValueUnitClassContractError("P01_MEMBER_ROLE_SIGN_UNIT_RESOLVED_PIN_FORBIDDEN")
    if P01_ZERO_ABSENCE_NA_RESOLVED is True:
        raise P01ValueUnitClassContractError("P01_ZERO_ABSENCE_NA_RESOLVED_PIN_FORBIDDEN")
    if P01_COMBINATION_PRECEDENCE_RESOLVED is True:
        raise P01ValueUnitClassContractError("P01_COMBINATION_PRECEDENCE_RESOLVED_PIN_FORBIDDEN")
    if P01_TERM_SEMANTICS_RESOLVED is True:
        raise P01ValueUnitClassContractError("P01_TERM_SEMANTICS_RESOLVED_PIN_FORBIDDEN")
    if P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED is True:
        raise P01ValueUnitClassContractError(
            "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED_PIN_FORBIDDEN"
        )
    if RECONSTRUCTION_ALGEBRA_COMPLETE is True:
        raise P01ValueUnitClassContractError("P01_RECONSTRUCTION_ALGEBRA_COMPLETE_PIN_FORBIDDEN")
    if P01_VALUE_UNIT_CLASS_CONTRACT_AUTHORITY_EFFECT != AUTHORITY_EFFECT_NONE:
        raise P01ValueUnitClassContractError("P01_AUTHORITY_EFFECT_MUST_REMAIN_NONE")
    if P01_EXACT_MEMBER_IDENTITY_SET != MEMBER_ID:
        raise P01ValueUnitClassContractError("P01_EXACT_MEMBER_IDENTITY_SET_MISMATCH")

    for field in _VECTOR_FIELDS:
        _require_non_empty_str(field=field, raw=getattr(contract, field))
    digest = _require_non_empty_str(field="provenance_digest", raw=contract.provenance_digest)
    if _SHA256_HEX.fullmatch(digest) is None:
        raise P01ValueUnitClassContractError("P01_PROVENANCE_DIGEST_MALFORMED")
    expected_digest = compute_p01_value_unit_class_digest_v1(
        {key: getattr(contract, key) for key in _VECTOR_FIELDS}
    )
    if digest != expected_digest:
        raise P01ValueUnitClassContractError("P01_PROVENANCE_DIGEST_MISMATCH")

    if contract.ratification_scope != RATIFICATION_SCOPE:
        raise P01ValueUnitClassContractError("P01_RATIFICATION_SCOPE_MISMATCH")
    if contract.selected_option != SELECTED_OPTION:
        raise P01ValueUnitClassContractError("P01_SELECTED_OPTION_MISMATCH")
    if contract.p01_term_set_resolved_status != RESOLVED_STATUS_TRUE:
        raise P01ValueUnitClassContractError("P01_TERM_SET_RESOLVED_STATUS_MISMATCH")
    if contract.p01_value_unit_class_resolved_status != RESOLVED_STATUS_TRUE:
        raise P01ValueUnitClassContractError("P01_VALUE_UNIT_CLASS_RESOLVED_STATUS_MISMATCH")
    if contract.member_id != MEMBER_ID:
        raise P01ValueUnitClassContractError("P01_MEMBER_ID_MISMATCH")
    if contract.p01_value_unit_class != VALUE_UNIT_CLASS:
        raise P01ValueUnitClassContractError("P01_VALUE_UNIT_CLASS_MISMATCH")
    _reject_forbidden_unit(field="p01_value_unit_class", raw=contract.p01_value_unit_class)
    if contract.p01_semantic_dimension != SEMANTIC_DIMENSION:
        raise P01ValueUnitClassContractError("P01_SEMANTIC_DIMENSION_MISMATCH")
    if contract.p01_parent_dimension_compatibility != PARENT_DIMENSION_COMPATIBILITY:
        raise P01ValueUnitClassContractError("P01_PARENT_DIMENSION_COMPATIBILITY_MISMATCH")
    if contract.p01_requires_dimensional_transformation != (
        REQUIRES_DIMENSIONAL_TRANSFORMATION_STATUS
    ):
        raise P01ValueUnitClassContractError("P01_REQUIRES_DIMENSIONAL_TRANSFORMATION_MISMATCH")
    if contract.p01_direct_additive_subtraction_compatible != (
        DIRECT_ADDITIVE_SUBTRACTION_COMPATIBLE_STATUS
    ):
        raise P01ValueUnitClassContractError("P01_DIRECT_ADDITIVE_SUBTRACTION_COMPATIBLE_MISMATCH")
    if contract.remaining_unresolved_semantics != REMAINING_UNRESOLVED_SEMANTICS:
        raise P01ValueUnitClassContractError("P01_REMAINING_UNRESOLVED_SEMANTICS_MISMATCH")
    if "P01_VALUE_UNIT_CLASS_UNSPECIFIED" in contract.remaining_unresolved_semantics:
        raise P01ValueUnitClassContractError("P01_VALUE_UNIT_CLASS_UNSPECIFIED_MUST_BE_CLOSED")
    if "P01_APPLICABILITY_UNSPECIFIED" not in contract.remaining_unresolved_semantics:
        raise P01ValueUnitClassContractError("P01_APPLICABILITY_MUST_REMAIN_UNSPECIFIED")
    if contract.term_semantics_resolved_status != TERM_SEMANTICS_RESOLVED_STATUS:
        raise P01ValueUnitClassContractError("P01_TERM_SEMANTICS_RESOLVED_STATUS_MISMATCH")
    if contract.unspecified_closed_status != UNSPECIFIED_CLOSED_STATUS:
        raise P01ValueUnitClassContractError("P01_UNSPECIFIED_CLOSED_STATUS_MISMATCH")
    if contract.contradiction_state != CONTRADICTION_NONE:
        raise P01ValueUnitClassContractError("P01_CONTRADICTION_STATE_MISMATCH")
    if contract.rejected_unit_class_inferences != REJECTED_UNIT_CLASS_INFERENCES:
        raise P01ValueUnitClassContractError("P01_REJECTED_UNIT_CLASS_INFERENCES_MISMATCH")
    if contract.evidence_classification != EVIDENCE_CLASSIFICATION:
        raise P01ValueUnitClassContractError("P01_EVIDENCE_CLASSIFICATION_MISMATCH")
    if contract.p01_runtime_instance_present != RUNTIME_INSTANCE_PRESENT_STATUS:
        raise P01ValueUnitClassContractError("P01_RUNTIME_INSTANCE_FORBIDDEN")
    if contract.p01_authority_effect != AUTHORITY_EFFECT_NONE:
        raise P01ValueUnitClassContractError("P01_AUTHORITY_EFFECT_MUST_REMAIN_NONE")
    if contract.p01_value_unit_class_contract_authority_effect != AUTHORITY_EFFECT_NONE:
        raise P01ValueUnitClassContractError("P01_AUTHORITY_EFFECT_MUST_REMAIN_NONE")
    if contract.parent_p01_exact_member_identity_contract_schema_class != (
        PARENT_IDENTITY_CONTRACT_SCHEMA_CLASS
    ):
        raise P01ValueUnitClassContractError("P01_PARENT_IDENTITY_SCHEMA_MISMATCH")
    if contract.parent_p01_term_contract_schema_class != PARENT_TERM_CONTRACT_SCHEMA_CLASS:
        raise P01ValueUnitClassContractError("P01_PARENT_TERM_SCHEMA_MISMATCH")
    if contract.target_semantic_dimension_id != DIMENSION_ID:
        raise P01ValueUnitClassContractError("P01_TARGET_DIMENSION_MISMATCH")
    if contract.policy_id != POLICY_ID or contract.term_id != TERM_ID:
        raise P01ValueUnitClassContractError("P01_POLICY_OR_TERM_MISMATCH")
    _require_false_pin(
        raw=contract.p01_applicability_resolved_status,
        error="P01_APPLICABILITY_RESOLVED_FORBIDDEN",
    )
    _require_false_pin(
        raw=contract.p01_member_role_sign_unit_resolved_status,
        error="P01_MEMBER_ROLE_SIGN_UNIT_RESOLVED_FORBIDDEN",
    )
    for field in (
        "p01_unit_identity_is_distinct_from_authority_identity",
        "p01_unit_identity_is_distinct_from_member_identity",
        "p01_settlement_currency_is_not_unit_identity",
        "p01_parent_dimension_is_not_authority_source",
        "unit_does_not_ratify_formula",
        "unit_does_not_ratify_operator",
        "unit_does_not_ratify_sign",
        "unit_does_not_ratify_applicability",
        "unit_does_not_ratify_source_mapping",
        "unit_does_not_close_p01_term_semantics",
        "unit_does_not_close_haircut_reserve_depletion_unspecified",
        "p01_value_unit_class_is_not_ratio",
        "p01_value_unit_class_is_not_percentage",
        "p01_value_unit_class_is_not_bps",
        "p01_value_unit_class_is_not_contracts_qty",
        "p01_value_unit_class_is_not_python_numeric_type",
        "p01m_governed_deployability_conservatism_reduction_is_not_haircut_alias",
        "p01m_governed_deployability_conservatism_reduction_is_not_reserve_alias",
        "p01m_governed_deployability_conservatism_reduction_is_not_depletion_alias",
        "p01m_governed_deployability_conservatism_reduction_is_not_u04",
        "p01m_governed_deployability_conservatism_reduction_is_not_u05",
        "p01m_governed_deployability_conservatism_reduction_is_not_u06",
        "p01m_governed_deployability_conservatism_reduction_is_not_venue_raw",
        "p01m_governed_deployability_conservatism_reduction_is_not_availeq",
        "p01m_governed_deployability_conservatism_reduction_is_not_eq",
        "p01m_governed_deployability_conservatism_reduction_is_not_totaleq",
        "p01m_governed_deployability_conservatism_reduction_is_not_canary_envelope",
        "p01m_governed_deployability_conservatism_reduction_is_not_margin_reserve_alias",
        "p01m_governed_deployability_conservatism_reduction_is_not_future_fee_permission",
        "missing_input_fail_closed",
        "malformed_input_fail_closed",
    ):
        _require_true_pin(raw=getattr(contract, field), error=f"P01_{field.upper()}_REQUIRED")


def build_p01_value_unit_class_contract_v1(
    *,
    p01_value_unit_class_contract_id: str,
    **overrides: Any,
) -> P01ValueUnitClassContractV1:
    parent = build_p01_exact_member_identity_contract_v1(
        p01_exact_member_identity_contract_id="SYNTHETIC_P01_EXACT_MEMBER_IDENTITY_CONTRACT_ID"
    )
    if parent.p01_authority_effect != AUTHORITY_EFFECT_NONE:
        raise P01ValueUnitClassContractError("P01_PARENT_AUTHORITY_EFFECT_MUST_REMAIN_NONE")
    payload: dict[str, Any] = dict(overrides)
    defaults: dict[str, str] = {
        "p01_value_unit_class_contract_id": p01_value_unit_class_contract_id,
        "p01_value_unit_class_contract_version": CONTRACT_VERSION,
        "parent_p01_exact_member_identity_contract_schema_class": (
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
        "p01_semantic_dimension": SEMANTIC_DIMENSION,
        "p01_parent_dimension_compatibility": PARENT_DIMENSION_COMPATIBILITY,
        "p01_requires_dimensional_transformation": REQUIRES_DIMENSIONAL_TRANSFORMATION_STATUS,
        "p01_direct_additive_subtraction_compatible": (
            DIRECT_ADDITIVE_SUBTRACTION_COMPATIBLE_STATUS
        ),
        "p01_unit_identity_is_distinct_from_authority_identity": TRUE_PIN,
        "p01_unit_identity_is_distinct_from_member_identity": TRUE_PIN,
        "p01_settlement_currency_is_not_unit_identity": TRUE_PIN,
        "p01_parent_dimension_is_not_authority_source": TRUE_PIN,
        "unit_does_not_ratify_formula": TRUE_PIN,
        "unit_does_not_ratify_operator": TRUE_PIN,
        "unit_does_not_ratify_sign": TRUE_PIN,
        "unit_does_not_ratify_applicability": TRUE_PIN,
        "unit_does_not_ratify_source_mapping": TRUE_PIN,
        "unit_does_not_close_p01_term_semantics": TRUE_PIN,
        "unit_does_not_close_haircut_reserve_depletion_unspecified": TRUE_PIN,
        "p01_value_unit_class_is_not_ratio": TRUE_PIN,
        "p01_value_unit_class_is_not_percentage": TRUE_PIN,
        "p01_value_unit_class_is_not_bps": TRUE_PIN,
        "p01_value_unit_class_is_not_contracts_qty": TRUE_PIN,
        "p01_value_unit_class_is_not_python_numeric_type": TRUE_PIN,
        "p01m_governed_deployability_conservatism_reduction_is_not_haircut_alias": TRUE_PIN,
        "p01m_governed_deployability_conservatism_reduction_is_not_reserve_alias": TRUE_PIN,
        "p01m_governed_deployability_conservatism_reduction_is_not_depletion_alias": TRUE_PIN,
        "p01m_governed_deployability_conservatism_reduction_is_not_u04": TRUE_PIN,
        "p01m_governed_deployability_conservatism_reduction_is_not_u05": TRUE_PIN,
        "p01m_governed_deployability_conservatism_reduction_is_not_u06": TRUE_PIN,
        "p01m_governed_deployability_conservatism_reduction_is_not_venue_raw": TRUE_PIN,
        "p01m_governed_deployability_conservatism_reduction_is_not_availeq": TRUE_PIN,
        "p01m_governed_deployability_conservatism_reduction_is_not_eq": TRUE_PIN,
        "p01m_governed_deployability_conservatism_reduction_is_not_totaleq": TRUE_PIN,
        "p01m_governed_deployability_conservatism_reduction_is_not_canary_envelope": TRUE_PIN,
        "p01m_governed_deployability_conservatism_reduction_is_not_margin_reserve_alias": TRUE_PIN,
        "p01m_governed_deployability_conservatism_reduction_is_not_future_fee_permission": TRUE_PIN,
        "p01_applicability_resolved_status": RESOLVED_STATUS_FALSE,
        "p01_member_role_sign_unit_resolved_status": RESOLVED_STATUS_FALSE,
        "missing_input_fail_closed": MISSING_INPUT_FAIL_CLOSED,
        "malformed_input_fail_closed": MALFORMED_INPUT_FAIL_CLOSED,
        "rejected_unit_class_inferences": REJECTED_UNIT_CLASS_INFERENCES,
        "remaining_unresolved_semantics": REMAINING_UNRESOLVED_SEMANTICS,
        "evidence_classification": EVIDENCE_CLASSIFICATION,
        "contradiction_state": CONTRADICTION_NONE,
        "term_semantics_resolved_status": TERM_SEMANTICS_RESOLVED_STATUS,
        "unspecified_closed_status": UNSPECIFIED_CLOSED_STATUS,
        "p01_runtime_instance_present": RUNTIME_INSTANCE_PRESENT_STATUS,
        "p01_authority_effect": AUTHORITY_EFFECT_NONE,
        "p01_value_unit_class_contract_authority_effect": AUTHORITY_EFFECT_NONE,
    }
    for key, value in defaults.items():
        payload.setdefault(key, value)
    missing = [name for name in _VECTOR_FIELDS if name not in payload]
    if missing:
        raise P01ValueUnitClassContractError("P01_FIELD_MISSING:" + ",".join(missing))
    attached = attach_p01_value_unit_class_digest_v1(payload)
    return P01ValueUnitClassContractV1(
        **{name: attached[name] for name in P01_VALUE_UNIT_CLASS_REQUIRED_FIELDS}
    )


def reject_p01_inferred_value_unit_class_v1(*, value_unit_class: str) -> None:
    """Settlement currency, ratios, and venue fields are not the P01 unit class."""

    _reject_forbidden_unit(field="p01_value_unit_class", raw=value_unit_class)
    raise P01ValueUnitClassContractError("P01_VALUE_UNIT_CLASS_INFERRED_FORBIDDEN")


def reject_p01_unit_as_formula_v1(*, formula: str) -> None:
    """Value unit class cannot authorize a reconstruction formula."""

    _ = formula
    raise P01ValueUnitClassContractError("P01_UNIT_IS_NOT_FORMULA")
