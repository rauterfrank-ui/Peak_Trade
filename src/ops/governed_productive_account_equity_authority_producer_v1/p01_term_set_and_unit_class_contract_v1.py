"""Typed P01 term-set and unit-class adjudication contract.

Encodes the forensic result that neither the exact P01 member set nor the
P01 value unit class is canonically resolvable. Does not invent members.
Does not inherit settlement USDC. Schema presence is not P01 resolution.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Mapping

from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED,
    P01_TERM_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_TERM_CONTRACT_SCHEMA_PRESENT,
    P01_TERM_SEMANTICS_RESOLVED,
    P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_AUTHORITY_EFFECT,
    P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_SCHEMA_PRESENT,
    P01_TERM_SET_AND_UNIT_CLASS_PROVENANCE_REQUIRED_FIELDS,
    RECONSTRUCTION_ALGEBRA_COMPLETE,
    SOURCE_OBJECT_PRESENT,
    SOURCE_SELECTED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_haircut_reserve_depletion_term_contract_v1 import (
    ALGEBRAIC_ROLE,
    CURRENCY_VALUATION_DOMAIN,
    NEGATIVE_ALLOWED,
    SCHEMA_CLASS as P01_TERM_SCHEMA_CLASS,
    SIGN_CONSTRAINTS,
    VALUE_UNIT_CLASS as PARENT_VALUE_UNIT_CLASS,
    build_p01_haircut_reserve_depletion_term_contract_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.reconstruction_algebra_contract_v1 import (
    CONTRADICTION_NONE,
    CURRENCY_DOMAIN_UNSPECIFIED,
    CURRENCY_DOMAIN_USDC,
    DIMENSION_ID,
    EARLIEST_UNRESOLVED_ALGEBRA_TERM,
    TERM_FEE,
    TERM_LIABILITY,
    TERM_P01_HAIRCUT_RESERVE_DEPLETION,
    TERM_PENDING_ORDER_RESERVATION,
    TERM_SET_UNSPECIFIED,
    UNRESOLVED_ALGEBRA_TERMS,
    build_reconstruction_algebra_contract_v1,
)

SCHEMA_CLASS = "P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_V1"
CONTRACT_VERSION = "v1"
POLICY_ID = "P01"
TERM_ID = TERM_P01_HAIRCUT_RESERVE_DEPLETION
PARENT_CONTRACT_SCHEMA_CLASS = P01_TERM_SCHEMA_CLASS
FAMILY_CLASS_LABELS = "HAIRCUT,RESERVE,DEPLETION"
FAMILY_LABELS_ARE_NOT_EXACT_TERM_SET = "true"
P01_TERM_SET = TERM_SET_UNSPECIFIED
P01_VALUE_UNIT_CLASS = PARENT_VALUE_UNIT_CLASS
P01_TERM_SET_RESOLVED_STATUS = "false"
P01_VALUE_UNIT_CLASS_RESOLVED_STATUS = "false"
P01_TERM_SET_ADJUDICATION = "UNSPECIFIED_FAIL_CLOSED"
P01_VALUE_UNIT_CLASS_ADJUDICATION = "UNSPECIFIED_FAIL_CLOSED"
CURRENCY_VALUATION_DOMAIN_STATUS = CURRENCY_VALUATION_DOMAIN
ALGEBRAIC_ROLE_STATUS = ALGEBRAIC_ROLE
SIGN_CONSTRAINTS_STATUS = SIGN_CONSTRAINTS
NEGATIVE_ALLOWED_STATUS = NEGATIVE_ALLOWED
AUTHORITY_EFFECT_NONE = "NONE"
TERM_SEMANTICS_RESOLVED_STATUS = "false"
UNSPECIFIED_CLOSED_STATUS = "false"
REMAINING_UNRESOLVED_SEMANTICS = (
    "P01_TERM_SET_UNSPECIFIED,"
    "P01_VALUE_UNIT_CLASS_UNSPECIFIED,"
    "P01_APPLICABILITY_UNSPECIFIED,"
    "P01_EQUITY_BASE_INCLUSION_UNRESOLVED,"
    "P01_EMBEDDING_UNRESOLVED,"
    "P01_OVERLAP_WITH_U04_U05_UNRESOLVED,"
    "P01_NUMERIC_VALUE_PROVENANCE_UNSPECIFIED"
)
REJECTED_TERM_SET_INFERENCES = (
    "U04_PENDING_ORDER_RESERVATION_LABEL_IS_NOT_P01_MEMBER;"
    "U05_LIABILITY_LABEL_IS_NOT_P01_MEMBER;"
    "U06_ACCRUED_FEE_LABEL_IS_NOT_P01_MEMBER;"
    "U06_FUTURE_FEE_PERMISSION_IS_NOT_P01_MEMBERSHIP;"
    "FAMILY_LABEL_HAIRCUT_RESERVE_DEPLETION_IS_NOT_FINITE_SET;"
    "EMPTY_SET_IS_NOT_ZERO;"
    "GENERIC_SAFETY_BUFFER_IS_NOT_P01_MEMBER;"
    "MARGIN_RESERVE_LABEL_IS_NOT_P01_MEMBER;"
    "VENUE_RAW_FROZENBAL_ORDFROZEN_ISOEQ_REJECTED;"
    "USD_USDC_HAIRCUT_POLICY_IS_NOT_P01_MEMBER;"
    "CANARY_SLIPPAGE_MM_FEE_ENVELOPE_IS_NOT_P01_MEMBER"
)
REJECTED_UNIT_CLASS_INFERENCES = (
    "USDC_SETTLEMENT_IS_NOT_P01_UNIT_CLASS;"
    "PARENT_DIMENSION_CURRENCY_IS_NOT_P01_UNIT;"
    "RATIO_PERCENT_BPS_UNPROVEN;"
    "ABSOLUTE_AMOUNT_UNPROVEN;"
    "CONTRACTS_QTY_IS_NOT_P01_UNIT;"
    "QUOTE_CURRENCY_UNPROVEN"
)
EVIDENCE_CLASSIFICATION = (
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_T_P01_FAMILY_REDUCTION_ONLY_UNSPECIFIED;"
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_AB_TERM_SET_AND_UNIT_UNSPECIFIED;"
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_T_U06_FUTURE_FEES_MAY_EXIST_ONLY_AS_SEPARATE_P01_RESERVE_TERM;"
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_U08_SETTLEMENT_USDC_IS_NOT_P01_UNIT;"
    "FORENSIC_EVIDENCE=NO_FINITE_P01_MEMBER_ENUMERATION_IN_PRODUCTIVE_CODE;"
    "FORENSIC_EVIDENCE=SRC_RISK_HAS_NO_P01_HAIRCUT_IMPLEMENTATION;"
    "HISTORICAL_STATE=11_2_1_N_HAIRCUTS_RESERVE_DEPLETION_FROZEN_PENDING_OWNER_POLICY_SUPERSEDED;"
    "HISTORICAL_STATE=11_13_5_USD_USDC_HAIRCUT_UNINSTANTIATED_NOT_P01;"
    "STRUCTURAL_REUSE_ONLY=P01_HAIRCUT_RESERVE_DEPLETION_TERM_CONTRACT_V1;"
    "NAVIGATION=MAP_OF_TRUTH_NON_SSOT;"
    "REJECTED=U04_U05_U06_LABEL_MEMBERSHIP_USD_USDC_HAIRCUT_VENUE_RAW_EMPTY_SET_ZERO;"
    "UNRESOLVED=EXACT_FINITE_TERM_SET_AND_VALUE_UNIT_CLASS"
)
_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")
_INFERRED_TERM_SET_TOKENS: tuple[str, ...] = (
    "u04",
    "u05",
    "u06",
    TERM_PENDING_ORDER_RESERVATION.lower(),
    TERM_LIABILITY.lower(),
    TERM_FEE.lower(),
    "pendingorder",
    "liabilit",
    "accruedfee",
    "haircut,reserve,depletion",
    "haircut+reserve+depletion",
    "empty",
    "none",
    "zero",
    "safetybuffer",
    "marginreserve",
    "feereserve",
)
_INFERRED_UNIT_TOKENS: tuple[str, ...] = (
    "usdc",
    "usd",
    "currency",
    "amount",
    "ratio",
    "percent",
    "percentage",
    "bps",
    "basispoints",
    "contracts",
    "quote",
)
_VECTOR_FIELDS: tuple[str, ...] = tuple(
    name
    for name in P01_TERM_SET_AND_UNIT_CLASS_PROVENANCE_REQUIRED_FIELDS
    if name != "provenance_digest"
)


class P01TermSetAndUnitClassContractError(ValueError):
    """Fail-closed P01 term-set/unit-class contract violation."""


def _fold(value: str) -> str:
    return str(value or "").strip().lower().replace("_", "").replace("-", "")


def _require_non_empty_str(*, field: str, raw: Any) -> str:
    if raw is None:
        raise P01TermSetAndUnitClassContractError(f"P01_FIELD_MISSING:{field}")
    if not isinstance(raw, str):
        raise P01TermSetAndUnitClassContractError(f"P01_FIELD_NOT_STRING:{field}")
    text = raw.strip()
    if text == "" or text != raw:
        raise P01TermSetAndUnitClassContractError(f"P01_FIELD_MISSING:{field}")
    return text


def _sha256_hex(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _canonical_json(payload: Mapping[str, str]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_p01_term_set_and_unit_class_provenance_digest_v1(
    canonical: Mapping[str, str],
) -> str:
    payload = {
        key: canonical[key]
        for key in P01_TERM_SET_AND_UNIT_CLASS_PROVENANCE_REQUIRED_FIELDS
        if key != "provenance_digest"
    }
    return _sha256_hex(_canonical_json(payload))


def attach_p01_term_set_and_unit_class_provenance_digest_v1(
    fields: Mapping[str, Any],
) -> dict[str, Any]:
    canonical: dict[str, str] = {}
    for canonical_name in P01_TERM_SET_AND_UNIT_CLASS_PROVENANCE_REQUIRED_FIELDS:
        if canonical_name == "provenance_digest":
            continue
        if canonical_name not in fields:
            raise P01TermSetAndUnitClassContractError(f"P01_FIELD_MISSING:{canonical_name}")
        raw = fields[canonical_name]
        canonical[canonical_name] = "" if raw is None else str(raw)
    attached = dict(fields)
    attached["provenance_digest"] = compute_p01_term_set_and_unit_class_provenance_digest_v1(
        canonical
    )
    return attached


@dataclass(frozen=True)
class P01TermSetAndUnitClassContractV1:
    """Typed immutable P01 term-set/unit-class adjudication. Not a numeric instance."""

    p01_term_set_and_unit_class_contract_id: str
    p01_term_set_and_unit_class_contract_version: str
    parent_p01_term_contract_schema_class: str
    target_semantic_dimension_id: str
    policy_id: str
    term_id: str
    family_class_labels: str
    family_labels_are_not_exact_term_set: str
    p01_term_set: str
    p01_term_set_resolved_status: str
    p01_term_set_adjudication: str
    p01_value_unit_class: str
    p01_value_unit_class_resolved_status: str
    p01_value_unit_class_adjudication: str
    currency_valuation_domain: str
    algebraic_role: str
    sign_constraints: str
    negative_allowed: str
    rejected_term_set_inferences: str
    rejected_unit_class_inferences: str
    remaining_unresolved_semantics: str
    evidence_classification: str
    contradiction_state: str
    term_semantics_resolved_status: str
    unspecified_closed_status: str
    p01_term_set_and_unit_class_contract_authority_effect: str
    provenance_digest: str

    def __post_init__(self) -> None:
        _validate_p01_term_set_and_unit_class_contract_v1(self)

    def to_canonical_dict(self) -> dict[str, str]:
        values = {
            "p01_term_set_and_unit_class_contract_id": (
                self.p01_term_set_and_unit_class_contract_id
            ),
            "p01_term_set_and_unit_class_contract_version": (
                self.p01_term_set_and_unit_class_contract_version
            ),
            "parent_p01_term_contract_schema_class": (self.parent_p01_term_contract_schema_class),
            "target_semantic_dimension_id": self.target_semantic_dimension_id,
            "policy_id": self.policy_id,
            "term_id": self.term_id,
            "family_class_labels": self.family_class_labels,
            "family_labels_are_not_exact_term_set": (self.family_labels_are_not_exact_term_set),
            "p01_term_set": self.p01_term_set,
            "p01_term_set_resolved_status": self.p01_term_set_resolved_status,
            "p01_term_set_adjudication": self.p01_term_set_adjudication,
            "p01_value_unit_class": self.p01_value_unit_class,
            "p01_value_unit_class_resolved_status": (self.p01_value_unit_class_resolved_status),
            "p01_value_unit_class_adjudication": self.p01_value_unit_class_adjudication,
            "currency_valuation_domain": self.currency_valuation_domain,
            "algebraic_role": self.algebraic_role,
            "sign_constraints": self.sign_constraints,
            "negative_allowed": self.negative_allowed,
            "rejected_term_set_inferences": self.rejected_term_set_inferences,
            "rejected_unit_class_inferences": self.rejected_unit_class_inferences,
            "remaining_unresolved_semantics": self.remaining_unresolved_semantics,
            "evidence_classification": self.evidence_classification,
            "contradiction_state": self.contradiction_state,
            "term_semantics_resolved_status": self.term_semantics_resolved_status,
            "unspecified_closed_status": self.unspecified_closed_status,
            "p01_term_set_and_unit_class_contract_authority_effect": (
                self.p01_term_set_and_unit_class_contract_authority_effect
            ),
            "provenance_digest": self.provenance_digest,
        }
        return {key: values[key] for key in P01_TERM_SET_AND_UNIT_CLASS_PROVENANCE_REQUIRED_FIELDS}


def _validate_p01_term_set_and_unit_class_contract_v1(
    contract: P01TermSetAndUnitClassContractV1,
) -> None:
    if P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_SCHEMA_PRESENT is not True:
        raise P01TermSetAndUnitClassContractError(
            "P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_SCHEMA_PRESENT_REQUIRED"
        )
    if P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_RUNTIME_INSTANCE_PRESENT is True:
        raise P01TermSetAndUnitClassContractError("P01_RUNTIME_INSTANCE_FORBIDDEN")
    if P01_TERM_CONTRACT_SCHEMA_PRESENT is not True:
        raise P01TermSetAndUnitClassContractError("P01_TERM_CONTRACT_SCHEMA_PRESENT_REQUIRED")
    if P01_TERM_CONTRACT_RUNTIME_INSTANCE_PRESENT is True:
        raise P01TermSetAndUnitClassContractError("P01_PARENT_RUNTIME_INSTANCE_FORBIDDEN")
    if P01_TERM_SEMANTICS_RESOLVED is True:
        raise P01TermSetAndUnitClassContractError("P01_TERM_SEMANTICS_RESOLVED_PIN_FORBIDDEN")
    if P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED is True:
        raise P01TermSetAndUnitClassContractError(
            "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED_PIN_FORBIDDEN"
        )
    if RECONSTRUCTION_ALGEBRA_COMPLETE is True:
        raise P01TermSetAndUnitClassContractError(
            "P01_RECONSTRUCTION_ALGEBRA_COMPLETE_PIN_FORBIDDEN"
        )
    if SOURCE_SELECTED is True or SOURCE_OBJECT_PRESENT is True:
        raise P01TermSetAndUnitClassContractError("P01_SOURCE_SELECTION_FORBIDDEN")
    contract_id = _require_non_empty_str(
        field="p01_term_set_and_unit_class_contract_id",
        raw=contract.p01_term_set_and_unit_class_contract_id,
    )
    version = _require_non_empty_str(
        field="p01_term_set_and_unit_class_contract_version",
        raw=contract.p01_term_set_and_unit_class_contract_version,
    )
    parent = _require_non_empty_str(
        field="parent_p01_term_contract_schema_class",
        raw=contract.parent_p01_term_contract_schema_class,
    )
    target = _require_non_empty_str(
        field="target_semantic_dimension_id", raw=contract.target_semantic_dimension_id
    )
    policy_id = _require_non_empty_str(field="policy_id", raw=contract.policy_id)
    term_id = _require_non_empty_str(field="term_id", raw=contract.term_id)
    family = _require_non_empty_str(field="family_class_labels", raw=contract.family_class_labels)
    family_not_set = _require_non_empty_str(
        field="family_labels_are_not_exact_term_set",
        raw=contract.family_labels_are_not_exact_term_set,
    )
    term_set = _require_non_empty_str(field="p01_term_set", raw=contract.p01_term_set)
    term_set_resolved = _require_non_empty_str(
        field="p01_term_set_resolved_status", raw=contract.p01_term_set_resolved_status
    )
    term_set_adj = _require_non_empty_str(
        field="p01_term_set_adjudication", raw=contract.p01_term_set_adjudication
    )
    unit = _require_non_empty_str(field="p01_value_unit_class", raw=contract.p01_value_unit_class)
    unit_resolved = _require_non_empty_str(
        field="p01_value_unit_class_resolved_status",
        raw=contract.p01_value_unit_class_resolved_status,
    )
    unit_adj = _require_non_empty_str(
        field="p01_value_unit_class_adjudication",
        raw=contract.p01_value_unit_class_adjudication,
    )
    currency = _require_non_empty_str(
        field="currency_valuation_domain", raw=contract.currency_valuation_domain
    )
    role = _require_non_empty_str(field="algebraic_role", raw=contract.algebraic_role)
    sign = _require_non_empty_str(field="sign_constraints", raw=contract.sign_constraints)
    negative = _require_non_empty_str(field="negative_allowed", raw=contract.negative_allowed)
    rejected_set = _require_non_empty_str(
        field="rejected_term_set_inferences", raw=contract.rejected_term_set_inferences
    )
    rejected_unit = _require_non_empty_str(
        field="rejected_unit_class_inferences", raw=contract.rejected_unit_class_inferences
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
        field="p01_term_set_and_unit_class_contract_authority_effect",
        raw=contract.p01_term_set_and_unit_class_contract_authority_effect,
    )
    digest = _require_non_empty_str(field="provenance_digest", raw=contract.provenance_digest)
    if version != CONTRACT_VERSION:
        raise P01TermSetAndUnitClassContractError("P01_CONTRACT_VERSION_MISMATCH")
    if parent != PARENT_CONTRACT_SCHEMA_CLASS:
        raise P01TermSetAndUnitClassContractError("P01_PARENT_CONTRACT_REFERENCE_MISMATCH")
    if target != DIMENSION_ID:
        raise P01TermSetAndUnitClassContractError("P01_TARGET_DIMENSION_MISMATCH")
    if policy_id != POLICY_ID:
        raise P01TermSetAndUnitClassContractError("P01_POLICY_ID_MISMATCH")
    if term_id != TERM_ID:
        raise P01TermSetAndUnitClassContractError("P01_TERM_ID_MISMATCH")
    if family != FAMILY_CLASS_LABELS:
        raise P01TermSetAndUnitClassContractError("P01_FAMILY_CLASS_LABELS_MISMATCH")
    if family_not_set.lower() != "true":
        raise P01TermSetAndUnitClassContractError("P01_FAMILY_LABELS_TREATED_AS_TERM_SET_FORBIDDEN")
    if family_not_set != FAMILY_LABELS_ARE_NOT_EXACT_TERM_SET:
        raise P01TermSetAndUnitClassContractError("P01_FAMILY_LABELS_FLAG_MISMATCH")
    folded_set = _fold(term_set)
    if any(token in folded_set for token in _INFERRED_TERM_SET_TOKENS):
        raise P01TermSetAndUnitClassContractError(
            "P01_TERM_MEMBERSHIP_INFERRED_FROM_LABEL_FORBIDDEN"
        )
    if term_set_resolved.lower() == "true":
        raise P01TermSetAndUnitClassContractError("P01_TERM_SET_RESOLVED_FORBIDDEN")
    if term_set != P01_TERM_SET:
        raise P01TermSetAndUnitClassContractError("P01_TERM_SET_MISMATCH")
    if term_set_resolved != P01_TERM_SET_RESOLVED_STATUS:
        raise P01TermSetAndUnitClassContractError("P01_TERM_SET_RESOLVED_STATUS_MISMATCH")
    if term_set_adj != P01_TERM_SET_ADJUDICATION:
        raise P01TermSetAndUnitClassContractError("P01_TERM_SET_ADJUDICATION_MISMATCH")
    folded_unit = _fold(unit)
    if unit == CURRENCY_DOMAIN_USDC or any(token in folded_unit for token in _INFERRED_UNIT_TOKENS):
        raise P01TermSetAndUnitClassContractError("P01_UNIT_INFERRED_CURRENCY_FORBIDDEN")
    if unit_resolved.lower() == "true":
        raise P01TermSetAndUnitClassContractError("P01_VALUE_UNIT_CLASS_RESOLVED_FORBIDDEN")
    if unit != P01_VALUE_UNIT_CLASS:
        raise P01TermSetAndUnitClassContractError("P01_VALUE_UNIT_CLASS_MISMATCH")
    if unit_resolved != P01_VALUE_UNIT_CLASS_RESOLVED_STATUS:
        raise P01TermSetAndUnitClassContractError("P01_VALUE_UNIT_CLASS_RESOLVED_STATUS_MISMATCH")
    if unit_adj != P01_VALUE_UNIT_CLASS_ADJUDICATION:
        raise P01TermSetAndUnitClassContractError("P01_VALUE_UNIT_CLASS_ADJUDICATION_MISMATCH")
    if currency == CURRENCY_DOMAIN_USDC:
        raise P01TermSetAndUnitClassContractError("P01_UNIT_INFERRED_CURRENCY_FORBIDDEN")
    if currency != CURRENCY_VALUATION_DOMAIN_STATUS:
        raise P01TermSetAndUnitClassContractError("P01_CURRENCY_DOMAIN_MISMATCH")
    if role != ALGEBRAIC_ROLE_STATUS:
        raise P01TermSetAndUnitClassContractError("P01_ALGEBRAIC_ROLE_MISMATCH")
    if sign != SIGN_CONSTRAINTS_STATUS:
        raise P01TermSetAndUnitClassContractError("P01_SIGN_CONSTRAINTS_MISMATCH")
    if negative.lower() in {"true", "yes", "allowed"}:
        raise P01TermSetAndUnitClassContractError("P01_NEGATIVE_FORBIDDEN")
    if negative != NEGATIVE_ALLOWED_STATUS:
        raise P01TermSetAndUnitClassContractError("P01_NEGATIVE_ALLOWED_MISMATCH")
    if rejected_set != REJECTED_TERM_SET_INFERENCES:
        raise P01TermSetAndUnitClassContractError("P01_REJECTED_TERM_SET_INFERENCES_MISMATCH")
    if rejected_unit != REJECTED_UNIT_CLASS_INFERENCES:
        raise P01TermSetAndUnitClassContractError("P01_REJECTED_UNIT_CLASS_INFERENCES_MISMATCH")
    if remaining != REMAINING_UNRESOLVED_SEMANTICS:
        raise P01TermSetAndUnitClassContractError("P01_REMAINING_UNRESOLVED_SEMANTICS_MISMATCH")
    if evidence != EVIDENCE_CLASSIFICATION:
        raise P01TermSetAndUnitClassContractError("P01_EVIDENCE_CLASSIFICATION_MISMATCH")
    if contradiction != CONTRADICTION_NONE:
        raise P01TermSetAndUnitClassContractError("P01_CONTRADICTION_STATUS_MISMATCH")
    if semantics_resolved.lower() == "true":
        raise P01TermSetAndUnitClassContractError("P01_TERM_SEMANTICS_RESOLVED_FORBIDDEN")
    if semantics_resolved != TERM_SEMANTICS_RESOLVED_STATUS:
        raise P01TermSetAndUnitClassContractError("P01_TERM_SEMANTICS_RESOLVED_STATUS_MISMATCH")
    if closed.lower() == "true":
        raise P01TermSetAndUnitClassContractError(
            "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED_FORBIDDEN"
        )
    if closed != UNSPECIFIED_CLOSED_STATUS:
        raise P01TermSetAndUnitClassContractError("P01_UNSPECIFIED_CLOSED_STATUS_MISMATCH")
    if (
        effect != P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_AUTHORITY_EFFECT
        or effect != AUTHORITY_EFFECT_NONE
    ):
        raise P01TermSetAndUnitClassContractError("P01_AUTHORITY_EFFECT_MUST_REMAIN_NONE")
    if EARLIEST_UNRESOLVED_ALGEBRA_TERM != "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED":
        raise P01TermSetAndUnitClassContractError("P01_EARLIEST_ALGEBRA_TERM_DRIFT")
    if "U04_PENDING_ORDER_RESERVATION_INCLUSION_UNRESOLVED" not in UNRESOLVED_ALGEBRA_TERMS:
        raise P01TermSetAndUnitClassContractError("P01_U04_MUST_REMAIN_UNRESOLVED")
    if "U05_LIABILITY_INCLUSION_OR_VALUE_UNRESOLVED" not in UNRESOLVED_ALGEBRA_TERMS:
        raise P01TermSetAndUnitClassContractError("P01_U05_MUST_REMAIN_UNRESOLVED")
    if "U06_FEE_INCLUSION_UNRESOLVED" not in UNRESOLVED_ALGEBRA_TERMS:
        raise P01TermSetAndUnitClassContractError("P01_U06_MUST_REMAIN_UNRESOLVED")
    parent_contract = build_p01_haircut_reserve_depletion_term_contract_v1(
        p01_term_contract_id="P01_TERM_SET_PARENT_ALIGNMENT"
    )
    if parent_contract.value_unit_class != P01_VALUE_UNIT_CLASS:
        raise P01TermSetAndUnitClassContractError("P01_PARENT_UNIT_ALIGNMENT_MISMATCH")
    if parent_contract.algebraic_role != ALGEBRAIC_ROLE_STATUS:
        raise P01TermSetAndUnitClassContractError("P01_PARENT_ROLE_ALIGNMENT_MISMATCH")
    algebra = build_reconstruction_algebra_contract_v1(
        algebra_contract_id="P01_TERM_SET_ALGEBRA_ALIGNMENT"
    )
    p01_term = next(term for term in algebra.terms if term.term_id == TERM_ID)
    if p01_term.term_set_status != TERM_SET_UNSPECIFIED:
        raise P01TermSetAndUnitClassContractError("P01_ALGEBRA_TERM_SET_ALIGNMENT_MISMATCH")
    if p01_term.currency_unit_domain != CURRENCY_DOMAIN_UNSPECIFIED:
        raise P01TermSetAndUnitClassContractError("P01_ALGEBRA_UNIT_ALIGNMENT_MISMATCH")
    if algebra.algebra_completeness_status != "INCOMPLETE":
        raise P01TermSetAndUnitClassContractError("P01_ALGEBRA_COMPLETENESS_ALIGNMENT")
    canonical = contract.to_canonical_dict()
    expected_digest = compute_p01_term_set_and_unit_class_provenance_digest_v1(canonical)
    if not _SHA256_HEX.fullmatch(digest):
        raise P01TermSetAndUnitClassContractError("P01_PROVENANCE_DIGEST_NOT_SHA256")
    if digest != expected_digest:
        raise P01TermSetAndUnitClassContractError("P01_PROVENANCE_DIGEST_MISMATCH")
    _ = contract_id


def build_p01_term_set_and_unit_class_contract_v1(
    **fields: Any,
) -> P01TermSetAndUnitClassContractV1:
    """Construct the typed P01 term-set/unit-class contract. Does not resolve P01."""

    payload = dict(fields)
    defaults = {
        "p01_term_set_and_unit_class_contract_version": CONTRACT_VERSION,
        "parent_p01_term_contract_schema_class": PARENT_CONTRACT_SCHEMA_CLASS,
        "target_semantic_dimension_id": DIMENSION_ID,
        "policy_id": POLICY_ID,
        "term_id": TERM_ID,
        "family_class_labels": FAMILY_CLASS_LABELS,
        "family_labels_are_not_exact_term_set": FAMILY_LABELS_ARE_NOT_EXACT_TERM_SET,
        "p01_term_set": P01_TERM_SET,
        "p01_term_set_resolved_status": P01_TERM_SET_RESOLVED_STATUS,
        "p01_term_set_adjudication": P01_TERM_SET_ADJUDICATION,
        "p01_value_unit_class": P01_VALUE_UNIT_CLASS,
        "p01_value_unit_class_resolved_status": P01_VALUE_UNIT_CLASS_RESOLVED_STATUS,
        "p01_value_unit_class_adjudication": P01_VALUE_UNIT_CLASS_ADJUDICATION,
        "currency_valuation_domain": CURRENCY_VALUATION_DOMAIN_STATUS,
        "algebraic_role": ALGEBRAIC_ROLE_STATUS,
        "sign_constraints": SIGN_CONSTRAINTS_STATUS,
        "negative_allowed": NEGATIVE_ALLOWED_STATUS,
        "rejected_term_set_inferences": REJECTED_TERM_SET_INFERENCES,
        "rejected_unit_class_inferences": REJECTED_UNIT_CLASS_INFERENCES,
        "remaining_unresolved_semantics": REMAINING_UNRESOLVED_SEMANTICS,
        "evidence_classification": EVIDENCE_CLASSIFICATION,
        "contradiction_state": CONTRADICTION_NONE,
        "term_semantics_resolved_status": TERM_SEMANTICS_RESOLVED_STATUS,
        "unspecified_closed_status": UNSPECIFIED_CLOSED_STATUS,
        "p01_term_set_and_unit_class_contract_authority_effect": AUTHORITY_EFFECT_NONE,
    }
    for key, value in defaults.items():
        payload.setdefault(key, value)
    missing = [name for name in _VECTOR_FIELDS if name not in payload]
    if missing:
        raise P01TermSetAndUnitClassContractError("P01_FIELD_MISSING:" + ",".join(missing))
    attached = attach_p01_term_set_and_unit_class_provenance_digest_v1(payload)
    return P01TermSetAndUnitClassContractV1(
        **{name: attached[name] for name in P01_TERM_SET_AND_UNIT_CLASS_PROVENANCE_REQUIRED_FIELDS}
    )


def reject_p01_term_membership_inferred_from_u04_u05_u06_v1(*, term_set: str) -> None:
    """U04/U05/U06 labels are not P01 members."""

    folded = _fold(term_set)
    if any(token in folded for token in _INFERRED_TERM_SET_TOKENS):
        raise P01TermSetAndUnitClassContractError(
            "P01_TERM_MEMBERSHIP_INFERRED_FROM_LABEL_FORBIDDEN"
        )
    raise P01TermSetAndUnitClassContractError("P01_TERM_SET_MISMATCH")


def reject_p01_unit_inherited_from_settlement_currency_v1(*, value_unit_class: str) -> None:
    """Settlement USDC is not the P01 unit class."""

    folded = _fold(value_unit_class)
    if value_unit_class == CURRENCY_DOMAIN_USDC or any(
        token in folded for token in _INFERRED_UNIT_TOKENS
    ):
        raise P01TermSetAndUnitClassContractError("P01_UNIT_INFERRED_CURRENCY_FORBIDDEN")
    raise P01TermSetAndUnitClassContractError("P01_VALUE_UNIT_CLASS_MISMATCH")
