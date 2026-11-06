"""Typed P01 exact member identity ratification.

Owner-ratifies exactly one member identity inside the existing P01
reconstruction term. Identity ratification is not formula, unit, source,
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
    P01_EXACT_MEMBER_COUNT,
    P01_EXACT_MEMBER_IDENTITY_CONTRACT_AUTHORITY_EFFECT,
    P01_EXACT_MEMBER_IDENTITY_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_EXACT_MEMBER_IDENTITY_CONTRACT_SCHEMA_PRESENT,
    P01_EXACT_MEMBER_IDENTITY_REQUIRED_FIELDS,
    P01_EXACT_MEMBER_IDENTITY_SET,
    P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED,
    P01_MEMBER_ROLE_SIGN_UNIT_RESOLVED,
    P01_RUNTIME_INSTANCE_PRESENT,
    P01_TERM_SEMANTICS_RESOLVED,
    P01_TERM_SET_RESOLVED,
    P01_ZERO_ABSENCE_NA_RESOLVED,
    RECONSTRUCTION_ALGEBRA_COMPLETE,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_haircut_reserve_depletion_semantics_contract_v1 import (
    REMAINING_UNRESOLVED_SEMANTICS as PARENT_REMAINING_UNRESOLVED_SEMANTICS,
    SCHEMA_CLASS as P01_SEMANTICS_SCHEMA_CLASS,
    build_p01_haircut_reserve_depletion_semantics_contract_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_haircut_reserve_depletion_term_contract_v1 import (
    SCHEMA_CLASS as P01_TERM_SCHEMA_CLASS,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.reconstruction_algebra_contract_v1 import (
    CONTRADICTION_NONE,
    DIMENSION_ID,
    TERM_P01_HAIRCUT_RESERVE_DEPLETION,
)

SCHEMA_CLASS = "P01_EXACT_MEMBER_IDENTITY_CONTRACT_V1"
CONTRACT_VERSION = "v1"
POLICY_ID = "P01"
TERM_ID = TERM_P01_HAIRCUT_RESERVE_DEPLETION
PARENT_SEMANTICS_CONTRACT_SCHEMA_CLASS = P01_SEMANTICS_SCHEMA_CLASS
PARENT_TERM_CONTRACT_SCHEMA_CLASS = P01_TERM_SCHEMA_CLASS
RATIFICATION_SCOPE = "EXACT_MEMBER_IDENTITIES_ONLY"
MEMBER_ID = "P01M_GOVERNED_DEPLOYABILITY_CONSERVATISM_REDUCTION"
EXACT_MEMBER_IDENTITY_SET = P01_EXACT_MEMBER_IDENTITY_SET
EXACT_MEMBER_COUNT = str(P01_EXACT_MEMBER_COUNT)
IDENTITY_LEVEL_MEANING = (
    "GOVERNED_POLICY_IDENTITY_INSIDE_EXISTING_P01_RECONSTRUCTION_TERM_"
    "OWNER_DEFINED_DEPLOYABILITY_CONSERVATISM_CATEGORY"
)
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
IDENTITY_DOES_NOT_AUTHORIZE_ARITHMETIC = "true"
IDENTITY_DOES_NOT_CLOSE_P01_TERM_SEMANTICS = "true"
IDENTITY_DOES_NOT_CLOSE_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED = "true"
REMAINING_UNRESOLVED_SEMANTICS = PARENT_REMAINING_UNRESOLVED_SEMANTICS.replace(
    "P01_TERM_SET_UNSPECIFIED,", ""
)
REJECTED_MEMBER_INFERENCES = (
    "HAIRCUT_FAMILY_LABEL_IS_NOT_P01_MEMBER;"
    "RESERVE_FAMILY_LABEL_IS_NOT_P01_MEMBER;"
    "DEPLETION_FAMILY_LABEL_IS_NOT_P01_MEMBER;"
    "U04_PENDING_ORDER_RESERVATION_IS_NOT_P01_MEMBER;"
    "U05_LIABILITY_IS_NOT_P01_MEMBER;"
    "U06_ACCRUED_FEE_IS_NOT_P01_MEMBER;"
    "VENUE_RAW_IS_NOT_P01_MEMBER;"
    "AVAILEQ_IS_NOT_P01_MEMBER;"
    "EQ_IS_NOT_P01_MEMBER;"
    "TOTALEQ_IS_NOT_P01_MEMBER;"
    "CANARY_ENVELOPE_IS_NOT_P01_MEMBER;"
    "MARGIN_RESERVE_ALIAS_IS_NOT_P01_MEMBER;"
    "FUTURE_FEE_PERMISSION_IS_NOT_P01_MEMBER;"
    "EMPTY_SET_IS_NOT_THIS_RATIFICATION;"
    "IDENTITY_IS_NOT_FORMULA"
)
EVIDENCE_CLASSIFICATION = (
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_AK_OWNER_RATIFIED_EXACT_MEMBER_IDENTITY;"
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_T_P01_FAMILY_REDUCTION_ONLY;"
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_AJ_FAMILY_LABELS_ARE_NOT_INDEPENDENT_MEMBERS;"
    "OWNER_SELECTION=P01_OP_SINGLE_RESIDUAL_POLICY_REDUCTION_IDENTITY_V1;"
    "RATIFICATION_SCOPE=EXACT_MEMBER_IDENTITIES_ONLY;"
    "STRUCTURAL_REUSE_ONLY=P01_HAIRCUT_RESERVE_DEPLETION_SEMANTICS_CONTRACT_V1;"
    "NAVIGATION=MAP_OF_TRUTH_NON_SSOT;"
    "INTERPRETATION=NONE;"
    "HYPOTHESIS=NONE;"
    "REJECTED=HAIRCUT_RESERVE_DEPLETION_U04_U05_U06_VENUE_RAW_ALIASES;"
    "UNRESOLVED=UNIT_APPLICABILITY_INCLUSION_EMBEDDING_OVERLAP_PROVENANCE_FRESHNESS_ROLE_SIGN_ZERO_COMBINATION;"
    "UNSPECIFIED=P01_TERM_SEMANTICS_REMAIN_UNSPECIFIED"
)
_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")
_FORBIDDEN_MEMBER_TOKENS: tuple[str, ...] = (
    "haircut",
    "reserve",
    "depletion",
    "u04",
    "u05",
    "u06",
    "availeq",
    "totaleq",
    "canaryenvelope",
    "marginreserve",
    "futurefee",
    "empty",
)
_VECTOR_FIELDS: tuple[str, ...] = tuple(
    name for name in P01_EXACT_MEMBER_IDENTITY_REQUIRED_FIELDS if name != "provenance_digest"
)


class P01ExactMemberIdentityContractError(ValueError):
    """Fail-closed P01 exact member identity contract violation."""


def _fold(value: str) -> str:
    return str(value or "").strip().lower().replace("_", "").replace("-", "").replace(".", "")


def _require_non_empty_str(*, field: str, raw: Any) -> str:
    if raw is None:
        raise P01ExactMemberIdentityContractError(f"P01_FIELD_MISSING:{field}")
    if isinstance(raw, bool) or not isinstance(raw, str):
        raise P01ExactMemberIdentityContractError(f"P01_FIELD_NOT_STRING:{field}")
    text = raw.strip()
    if text == "" or text != raw:
        raise P01ExactMemberIdentityContractError(f"P01_FIELD_MISSING:{field}")
    return text


def _sha256_hex(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _canonical_json(payload: Mapping[str, str]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_p01_exact_member_identity_digest_v1(canonical: Mapping[str, str]) -> str:
    payload = {
        key: canonical[key]
        for key in P01_EXACT_MEMBER_IDENTITY_REQUIRED_FIELDS
        if key != "provenance_digest"
    }
    return _sha256_hex(_canonical_json(payload))


def attach_p01_exact_member_identity_digest_v1(fields: Mapping[str, Any]) -> dict[str, Any]:
    canonical: dict[str, str] = {}
    for canonical_name in P01_EXACT_MEMBER_IDENTITY_REQUIRED_FIELDS:
        if canonical_name == "provenance_digest":
            continue
        if canonical_name not in fields:
            raise P01ExactMemberIdentityContractError(f"P01_FIELD_MISSING:{canonical_name}")
        raw = fields[canonical_name]
        canonical[canonical_name] = "" if raw is None else str(raw)
    attached = dict(fields)
    attached["provenance_digest"] = compute_p01_exact_member_identity_digest_v1(canonical)
    return attached


def _require_true_pin(*, raw: str, error: str) -> None:
    if raw != TRUE_PIN or raw.lower() != "true":
        raise P01ExactMemberIdentityContractError(error)


def _reject_forbidden_member(*, field: str, raw: str) -> None:
    folded = _fold(raw)
    _ = field
    if folded != _fold(MEMBER_ID):
        for token in _FORBIDDEN_MEMBER_TOKENS:
            if token == folded or token in folded:
                raise P01ExactMemberIdentityContractError("P01_MEMBER_IDENTITY_INFERRED_FORBIDDEN")


@dataclass(frozen=True)
class P01ExactMemberIdentityContractV1:
    """Typed immutable P01 exact member identity ratification. Not a numeric instance."""

    p01_exact_member_identity_contract_id: str
    p01_exact_member_identity_contract_version: str
    parent_p01_haircut_reserve_depletion_semantics_contract_schema_class: str
    parent_p01_term_contract_schema_class: str
    target_semantic_dimension_id: str
    policy_id: str
    term_id: str
    ratification_scope: str
    p01_term_set_resolved_status: str
    p01_exact_member_identity_set: str
    p01_exact_member_count: str
    member_id: str
    identity_level_meaning: str
    identity_is_not_numeric_value: str
    identity_is_not_operator: str
    identity_is_not_formula: str
    identity_is_not_sign: str
    identity_is_not_unit: str
    identity_is_not_applicability: str
    identity_is_not_source: str
    identity_is_not_producer: str
    identity_is_not_freshness: str
    identity_is_not_equity_base_inclusion: str
    identity_is_not_embedding: str
    identity_is_not_u04_u05_u06_overlap: str
    identity_is_not_zero_absence_na: str
    identity_is_not_combination: str
    identity_is_not_precedence: str
    identity_is_not_runtime_binding: str
    identity_is_not_execution_effect: str
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
    p01_member_role_sign_unit_resolved_status: str
    p01_zero_absence_na_resolved_status: str
    p01_combination_precedence_resolved_status: str
    p01_value_unit_class_resolved_status: str
    p01_applicability_resolved_status: str
    missing_input_fail_closed: str
    malformed_input_fail_closed: str
    identity_does_not_authorize_arithmetic: str
    identity_does_not_close_p01_term_semantics: str
    identity_does_not_close_haircut_reserve_depletion_unspecified: str
    rejected_member_inferences: str
    remaining_unresolved_semantics: str
    evidence_classification: str
    contradiction_state: str
    term_semantics_resolved_status: str
    unspecified_closed_status: str
    p01_runtime_instance_present: str
    p01_authority_effect: str
    p01_exact_member_identity_contract_authority_effect: str
    provenance_digest: str

    def __post_init__(self) -> None:
        _validate_p01_exact_member_identity_contract_v1(self)

    def to_canonical_dict(self) -> dict[str, str]:
        values = {name: getattr(self, name) for name in _VECTOR_FIELDS}
        values["provenance_digest"] = self.provenance_digest
        return {key: values[key] for key in P01_EXACT_MEMBER_IDENTITY_REQUIRED_FIELDS}


def _validate_p01_exact_member_identity_contract_v1(
    contract: P01ExactMemberIdentityContractV1,
) -> None:
    if P01_EXACT_MEMBER_IDENTITY_CONTRACT_SCHEMA_PRESENT is not True:
        raise P01ExactMemberIdentityContractError(
            "P01_EXACT_MEMBER_IDENTITY_CONTRACT_SCHEMA_PRESENT_REQUIRED"
        )
    if P01_EXACT_MEMBER_IDENTITY_CONTRACT_RUNTIME_INSTANCE_PRESENT is True:
        raise P01ExactMemberIdentityContractError("P01_RUNTIME_INSTANCE_FORBIDDEN")
    if P01_RUNTIME_INSTANCE_PRESENT is True:
        raise P01ExactMemberIdentityContractError("P01_RUNTIME_INSTANCE_FORBIDDEN")
    if P01_TERM_SET_RESOLVED is not True:
        raise P01ExactMemberIdentityContractError("P01_TERM_SET_RESOLVED_REQUIRED")
    if RECONSTRUCTION_ALGEBRA_COMPLETE is True:
        raise P01ExactMemberIdentityContractError(
            "P01_RECONSTRUCTION_ALGEBRA_COMPLETE_PIN_FORBIDDEN"
        )
    if P01_EXACT_MEMBER_IDENTITY_CONTRACT_AUTHORITY_EFFECT != AUTHORITY_EFFECT_NONE:
        raise P01ExactMemberIdentityContractError("P01_AUTHORITY_EFFECT_MUST_REMAIN_NONE")
    if P01_EXACT_MEMBER_COUNT != 1:
        raise P01ExactMemberIdentityContractError("P01_EXACT_MEMBER_COUNT_MUST_BE_ONE")
    if P01_EXACT_MEMBER_IDENTITY_SET != MEMBER_ID:
        raise P01ExactMemberIdentityContractError("P01_EXACT_MEMBER_IDENTITY_SET_MISMATCH")

    for field in _VECTOR_FIELDS:
        _require_non_empty_str(field=field, raw=getattr(contract, field))
    digest = _require_non_empty_str(field="provenance_digest", raw=contract.provenance_digest)
    if _SHA256_HEX.fullmatch(digest) is None:
        raise P01ExactMemberIdentityContractError("P01_PROVENANCE_DIGEST_MALFORMED")
    expected_digest = compute_p01_exact_member_identity_digest_v1(
        {key: getattr(contract, key) for key in _VECTOR_FIELDS}
    )
    if digest != expected_digest:
        raise P01ExactMemberIdentityContractError("P01_PROVENANCE_DIGEST_MISMATCH")

    if contract.ratification_scope != RATIFICATION_SCOPE:
        raise P01ExactMemberIdentityContractError("P01_RATIFICATION_SCOPE_MISMATCH")
    if contract.p01_term_set_resolved_status != RESOLVED_STATUS_TRUE:
        raise P01ExactMemberIdentityContractError("P01_TERM_SET_RESOLVED_STATUS_MISMATCH")
    if contract.p01_exact_member_identity_set != EXACT_MEMBER_IDENTITY_SET:
        raise P01ExactMemberIdentityContractError("P01_EXACT_MEMBER_IDENTITY_SET_MISMATCH")
    if contract.p01_exact_member_count != EXACT_MEMBER_COUNT:
        raise P01ExactMemberIdentityContractError("P01_EXACT_MEMBER_COUNT_MISMATCH")
    if contract.member_id != MEMBER_ID:
        raise P01ExactMemberIdentityContractError("P01_MEMBER_ID_MISMATCH")
    _reject_forbidden_member(field="member_id", raw=contract.member_id)
    if contract.identity_level_meaning != IDENTITY_LEVEL_MEANING:
        raise P01ExactMemberIdentityContractError("P01_IDENTITY_LEVEL_MEANING_MISMATCH")
    if contract.remaining_unresolved_semantics != REMAINING_UNRESOLVED_SEMANTICS:
        raise P01ExactMemberIdentityContractError("P01_REMAINING_UNRESOLVED_SEMANTICS_MISMATCH")
    if "P01_TERM_SET_UNSPECIFIED" in contract.remaining_unresolved_semantics:
        raise P01ExactMemberIdentityContractError("P01_TERM_SET_UNSPECIFIED_MUST_BE_CLOSED")
    if "P01_VALUE_UNIT_CLASS_UNSPECIFIED" not in contract.remaining_unresolved_semantics:
        raise P01ExactMemberIdentityContractError("P01_VALUE_UNIT_CLASS_MUST_REMAIN_UNSPECIFIED")
    if contract.term_semantics_resolved_status != TERM_SEMANTICS_RESOLVED_STATUS:
        raise P01ExactMemberIdentityContractError("P01_TERM_SEMANTICS_RESOLVED_STATUS_MISMATCH")
    if contract.unspecified_closed_status != UNSPECIFIED_CLOSED_STATUS:
        raise P01ExactMemberIdentityContractError("P01_UNSPECIFIED_CLOSED_STATUS_MISMATCH")
    if contract.contradiction_state != CONTRADICTION_NONE:
        raise P01ExactMemberIdentityContractError("P01_CONTRADICTION_STATE_MISMATCH")
    if contract.rejected_member_inferences != REJECTED_MEMBER_INFERENCES:
        raise P01ExactMemberIdentityContractError("P01_REJECTED_MEMBER_INFERENCES_MISMATCH")
    if contract.evidence_classification != EVIDENCE_CLASSIFICATION:
        raise P01ExactMemberIdentityContractError("P01_EVIDENCE_CLASSIFICATION_MISMATCH")
    if contract.p01_runtime_instance_present != RUNTIME_INSTANCE_PRESENT_STATUS:
        raise P01ExactMemberIdentityContractError("P01_RUNTIME_INSTANCE_FORBIDDEN")
    if contract.p01_authority_effect != AUTHORITY_EFFECT_NONE:
        raise P01ExactMemberIdentityContractError("P01_AUTHORITY_EFFECT_MUST_REMAIN_NONE")
    if contract.p01_exact_member_identity_contract_authority_effect != AUTHORITY_EFFECT_NONE:
        raise P01ExactMemberIdentityContractError("P01_AUTHORITY_EFFECT_MUST_REMAIN_NONE")
    if contract.parent_p01_haircut_reserve_depletion_semantics_contract_schema_class != (
        PARENT_SEMANTICS_CONTRACT_SCHEMA_CLASS
    ):
        raise P01ExactMemberIdentityContractError("P01_PARENT_SEMANTICS_SCHEMA_MISMATCH")
    if contract.parent_p01_term_contract_schema_class != PARENT_TERM_CONTRACT_SCHEMA_CLASS:
        raise P01ExactMemberIdentityContractError("P01_PARENT_TERM_SCHEMA_MISMATCH")
    if contract.target_semantic_dimension_id != DIMENSION_ID:
        raise P01ExactMemberIdentityContractError("P01_TARGET_DIMENSION_MISMATCH")
    if contract.policy_id != POLICY_ID or contract.term_id != TERM_ID:
        raise P01ExactMemberIdentityContractError("P01_POLICY_OR_TERM_MISMATCH")
    for field, expected, error in (
        (
            "p01_member_role_sign_unit_resolved_status",
            RESOLVED_STATUS_FALSE,
            "P01_MEMBER_ROLE_SIGN_UNIT_RESOLVED_FORBIDDEN",
        ),
        (
            "p01_zero_absence_na_resolved_status",
            RESOLVED_STATUS_FALSE,
            "P01_ZERO_ABSENCE_NA_RESOLVED_FORBIDDEN",
        ),
        (
            "p01_combination_precedence_resolved_status",
            RESOLVED_STATUS_FALSE,
            "P01_COMBINATION_PRECEDENCE_RESOLVED_FORBIDDEN",
        ),
        (
            "p01_value_unit_class_resolved_status",
            RESOLVED_STATUS_FALSE,
            "P01_VALUE_UNIT_CLASS_RESOLVED_FORBIDDEN",
        ),
        (
            "p01_applicability_resolved_status",
            RESOLVED_STATUS_FALSE,
            "P01_APPLICABILITY_RESOLVED_FORBIDDEN",
        ),
    ):
        raw = getattr(contract, field)
        if raw.lower() == "true" or raw != expected:
            raise P01ExactMemberIdentityContractError(error)
    for field in (
        "identity_is_not_numeric_value",
        "identity_is_not_operator",
        "identity_is_not_formula",
        "identity_is_not_sign",
        "identity_is_not_unit",
        "identity_is_not_applicability",
        "identity_is_not_source",
        "identity_is_not_producer",
        "identity_is_not_freshness",
        "identity_is_not_equity_base_inclusion",
        "identity_is_not_embedding",
        "identity_is_not_u04_u05_u06_overlap",
        "identity_is_not_zero_absence_na",
        "identity_is_not_combination",
        "identity_is_not_precedence",
        "identity_is_not_runtime_binding",
        "identity_is_not_execution_effect",
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
        "identity_does_not_authorize_arithmetic",
        "identity_does_not_close_p01_term_semantics",
        "identity_does_not_close_haircut_reserve_depletion_unspecified",
    ):
        _require_true_pin(raw=getattr(contract, field), error=f"P01_{field.upper()}_REQUIRED")


def build_p01_exact_member_identity_contract_v1(
    *,
    p01_exact_member_identity_contract_id: str,
    **overrides: Any,
) -> P01ExactMemberIdentityContractV1:
    parent = build_p01_haircut_reserve_depletion_semantics_contract_v1(
        p01_haircut_reserve_depletion_semantics_contract_id=(
            "SYNTHETIC_P01_HAIRCUT_RESERVE_DEPLETION_SEMANTICS_CONTRACT_ID"
        )
    )
    if parent.p01_authority_effect != AUTHORITY_EFFECT_NONE:
        raise P01ExactMemberIdentityContractError("P01_PARENT_AUTHORITY_EFFECT_MUST_REMAIN_NONE")
    payload: dict[str, Any] = dict(overrides)
    defaults: dict[str, str] = {
        "p01_exact_member_identity_contract_id": p01_exact_member_identity_contract_id,
        "p01_exact_member_identity_contract_version": CONTRACT_VERSION,
        "parent_p01_haircut_reserve_depletion_semantics_contract_schema_class": (
            PARENT_SEMANTICS_CONTRACT_SCHEMA_CLASS
        ),
        "parent_p01_term_contract_schema_class": PARENT_TERM_CONTRACT_SCHEMA_CLASS,
        "target_semantic_dimension_id": DIMENSION_ID,
        "policy_id": POLICY_ID,
        "term_id": TERM_ID,
        "ratification_scope": RATIFICATION_SCOPE,
        "p01_term_set_resolved_status": RESOLVED_STATUS_TRUE,
        "p01_exact_member_identity_set": EXACT_MEMBER_IDENTITY_SET,
        "p01_exact_member_count": EXACT_MEMBER_COUNT,
        "member_id": MEMBER_ID,
        "identity_level_meaning": IDENTITY_LEVEL_MEANING,
        "identity_is_not_numeric_value": TRUE_PIN,
        "identity_is_not_operator": TRUE_PIN,
        "identity_is_not_formula": TRUE_PIN,
        "identity_is_not_sign": TRUE_PIN,
        "identity_is_not_unit": TRUE_PIN,
        "identity_is_not_applicability": TRUE_PIN,
        "identity_is_not_source": TRUE_PIN,
        "identity_is_not_producer": TRUE_PIN,
        "identity_is_not_freshness": TRUE_PIN,
        "identity_is_not_equity_base_inclusion": TRUE_PIN,
        "identity_is_not_embedding": TRUE_PIN,
        "identity_is_not_u04_u05_u06_overlap": TRUE_PIN,
        "identity_is_not_zero_absence_na": TRUE_PIN,
        "identity_is_not_combination": TRUE_PIN,
        "identity_is_not_precedence": TRUE_PIN,
        "identity_is_not_runtime_binding": TRUE_PIN,
        "identity_is_not_execution_effect": TRUE_PIN,
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
        "p01_member_role_sign_unit_resolved_status": RESOLVED_STATUS_FALSE,
        "p01_zero_absence_na_resolved_status": RESOLVED_STATUS_FALSE,
        "p01_combination_precedence_resolved_status": RESOLVED_STATUS_FALSE,
        "p01_value_unit_class_resolved_status": RESOLVED_STATUS_FALSE,
        "p01_applicability_resolved_status": RESOLVED_STATUS_FALSE,
        "missing_input_fail_closed": MISSING_INPUT_FAIL_CLOSED,
        "malformed_input_fail_closed": MALFORMED_INPUT_FAIL_CLOSED,
        "identity_does_not_authorize_arithmetic": IDENTITY_DOES_NOT_AUTHORIZE_ARITHMETIC,
        "identity_does_not_close_p01_term_semantics": IDENTITY_DOES_NOT_CLOSE_P01_TERM_SEMANTICS,
        "identity_does_not_close_haircut_reserve_depletion_unspecified": (
            IDENTITY_DOES_NOT_CLOSE_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED
        ),
        "rejected_member_inferences": REJECTED_MEMBER_INFERENCES,
        "remaining_unresolved_semantics": REMAINING_UNRESOLVED_SEMANTICS,
        "evidence_classification": EVIDENCE_CLASSIFICATION,
        "contradiction_state": CONTRADICTION_NONE,
        "term_semantics_resolved_status": TERM_SEMANTICS_RESOLVED_STATUS,
        "unspecified_closed_status": UNSPECIFIED_CLOSED_STATUS,
        "p01_runtime_instance_present": RUNTIME_INSTANCE_PRESENT_STATUS,
        "p01_authority_effect": AUTHORITY_EFFECT_NONE,
        "p01_exact_member_identity_contract_authority_effect": AUTHORITY_EFFECT_NONE,
    }
    for key, value in defaults.items():
        payload.setdefault(key, value)
    missing = [name for name in _VECTOR_FIELDS if name not in payload]
    if missing:
        raise P01ExactMemberIdentityContractError("P01_FIELD_MISSING:" + ",".join(missing))
    attached = attach_p01_exact_member_identity_digest_v1(payload)
    return P01ExactMemberIdentityContractV1(
        **{name: attached[name] for name in P01_EXACT_MEMBER_IDENTITY_REQUIRED_FIELDS}
    )


def reject_p01_inferred_member_identity_v1(*, member_id: str) -> None:
    """Family labels, Uxx slots, and venue fields are not P01 members."""

    _reject_forbidden_member(field="member_id", raw=member_id)
    raise P01ExactMemberIdentityContractError("P01_MEMBER_IDENTITY_INFERRED_FORBIDDEN")


def reject_p01_identity_as_formula_v1(*, formula: str) -> None:
    """Exact member identity cannot authorize a reconstruction formula."""

    _ = formula
    raise P01ExactMemberIdentityContractError("P01_IDENTITY_IS_NOT_FORMULA")
