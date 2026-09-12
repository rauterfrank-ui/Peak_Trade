"""Typed P01 applicability adjudication contract.

Encodes the forensic result that canonical evidence does not prove when
P01 applies, does not apply, or is conditionally applicable. Unknown remains
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
    P01_APPLICABILITY_PROVENANCE_REQUIRED_FIELDS,
    P01_APPLICABILITY_RESOLVED,
    P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED,
    P01_TERM_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_TERM_CONTRACT_SCHEMA_PRESENT,
    P01_TERM_SEMANTICS_RESOLVED,
    P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_SCHEMA_PRESENT,
    RECONSTRUCTION_ALGEBRA_COMPLETE,
    SOURCE_OBJECT_PRESENT,
    SOURCE_SELECTED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_haircut_reserve_depletion_term_contract_v1 import (
    APPLICABILITY_STATE as PARENT_APPLICABILITY_STATE,
    SCHEMA_CLASS as P01_TERM_SCHEMA_CLASS,
    build_p01_haircut_reserve_depletion_term_contract_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_term_set_and_unit_class_contract_v1 import (
    REMAINING_UNRESOLVED_SEMANTICS as PARENT_REMAINING_UNRESOLVED_SEMANTICS,
    SCHEMA_CLASS as P01_TERM_SET_SCHEMA_CLASS,
    build_p01_term_set_and_unit_class_contract_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.reconstruction_algebra_contract_v1 import (
    CONTRADICTION_NONE,
    DIMENSION_ID,
    EARLIEST_UNRESOLVED_ALGEBRA_TERM,
    INCLUSION_NOT_APPLICABLE,
    NUMERIC_MISSING,
    NUMERIC_PRESENT_ZERO,
    TERM_FEE,
    TERM_LIABILITY,
    TERM_P01_HAIRCUT_RESERVE_DEPLETION,
    TERM_PENDING_ORDER_RESERVATION,
    UNRESOLVED_ALGEBRA_TERMS,
    build_reconstruction_algebra_contract_v1,
)

SCHEMA_CLASS = "P01_APPLICABILITY_CONTRACT_V1"
CONTRACT_VERSION = "v1"
POLICY_ID = "P01"
TERM_ID = TERM_P01_HAIRCUT_RESERVE_DEPLETION
PARENT_TERM_SET_CONTRACT_SCHEMA_CLASS = P01_TERM_SET_SCHEMA_CLASS
PARENT_TERM_CONTRACT_SCHEMA_CLASS = P01_TERM_SCHEMA_CLASS
P01_APPLICABILITY_STATUS = PARENT_APPLICABILITY_STATE
P01_APPLICABILITY_RESOLVED_STATUS = "false"
P01_APPLICABILITY_RULE = "UNSPECIFIED_FAIL_CLOSED"
P01_APPLICABILITY_ADJUDICATION = "UNSPECIFIED_FAIL_CLOSED"
TYPED_APPLICABILITY_STATE_UNKNOWN = "UNKNOWN"
TYPED_APPLICABILITY_STATE_APPLIES = "APPLIES"
TYPED_APPLICABILITY_STATE_DOES_NOT_APPLY = "DOES_NOT_APPLY"
TYPED_APPLICABILITY_STATE = TYPED_APPLICABILITY_STATE_UNKNOWN
UNKNOWN_IS_NOT_NOT_APPLICABLE = "true"
ZERO_IS_NOT_NOT_APPLICABLE = "true"
ABSENCE_IS_NOT_NOT_APPLICABLE = "true"
MISSING_INPUT_FAIL_CLOSED = "true"
MALFORMED_INPUT_FAIL_CLOSED = "true"
TERM_SET_UNRESOLVED_DOES_NOT_DECIDE_APPLICABILITY = "true"
UNIT_UNRESOLVED_DOES_NOT_DECIDE_APPLICABILITY = "true"
AUTHORITY_EFFECT_NONE = "NONE"
TERM_SEMANTICS_RESOLVED_STATUS = "false"
UNSPECIFIED_CLOSED_STATUS = "false"
REMAINING_UNRESOLVED_SEMANTICS = PARENT_REMAINING_UNRESOLVED_SEMANTICS
REJECTED_APPLICABILITY_INFERENCES = (
    "ALWAYS_APPLIES_UNPROVEN_P01_STATUS_DECIDED_IS_EXISTENCE_NOT_APPLICABILITY;"
    "NEVER_APPLIES_CONTRADICTED_BY_DECIDED_REDUCTION_ONLY_FAMILY;"
    "POLICY_SELECTED_ORIGIN_IS_NOT_APPLICABILITY_SELECTOR;"
    "WHEN_RESERVE_CONFIGURED_UNPROVEN;"
    "WHEN_SPECIFIC_EXPOSURE_EXISTS_UNPROVEN;"
    "WHEN_HAIRCUT_EVENT_EXISTS_UNPROVEN;"
    "WHEN_LIABILITY_EXISTS_IS_NOT_P01_APPLICABILITY;"
    "WHEN_PENDING_ORDERS_EXIST_IS_NOT_P01_APPLICABILITY;"
    "WHEN_FEES_EXIST_IS_NOT_P01_APPLICABILITY;"
    "VENUE_DEPENDENT_UNPROVEN;"
    "ACCOUNT_STATE_DEPENDENT_UNPROVEN;"
    "INSTRUMENT_STATE_DEPENDENT_UNPROVEN;"
    "VALUE_ZERO_IS_NOT_NOT_APPLICABLE;"
    "TERM_ABSENCE_IS_NOT_NOT_APPLICABLE;"
    "MISSING_OR_MALFORMED_IS_NOT_NOT_APPLICABLE;"
    "U04_U05_U06_STATE_IS_NOT_P01_APPLICABILITY;"
    "VENUE_RAW_FIELD_IS_NOT_P01_APPLICABILITY;"
    "USD_USDC_HAIRCUT_IS_NOT_P01_APPLICABILITY;"
    "CANARY_FEE_SLIPPAGE_RESERVE_IS_NOT_P01_APPLICABILITY;"
    "OPTIONAL_DISABLED_INACTIVE_EMBEDDED_SAFE_OMITTED_DEFAULT_FALSE_FORBIDDEN"
)
EVIDENCE_CLASSIFICATION = (
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_T_P01_FAMILY_EXISTS_REDUCTION_ONLY;"
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_AB_UNKNOWN_APPLICABILITY_NOT_NOT_APPLICABLE;"
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_AC_ALWAYS_VS_CONDITIONAL_APPLICABILITY_UNPROVEN;"
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_T_UNSPECIFIED_OR_UNCLEAR_FAIL_CLOSED;"
    "FORENSIC_EVIDENCE=SRC_RISK_HAS_NO_P01_HAIRCUT_IMPLEMENTATION;"
    "FORENSIC_EVIDENCE=NO_PRODUCTIVE_P01_APPLICABILITY_SELECTOR;"
    "FORENSIC_EVIDENCE=NO_OPERATOR_POLICY_SEAM_SELECTING_P01_APPLICABILITY;"
    "HISTORICAL_STATE=11_13_5_USD_USDC_HAIRCUT_AND_FEE_SLIPPAGE_RESERVE_NOT_P01;"
    "STRUCTURAL_REUSE_ONLY=P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_V1;"
    "NAVIGATION=MAP_OF_TRUTH_NON_SSOT;"
    "REJECTED=ALWAYS_NEVER_POLICY_SELECTED_STATE_VENUE_ZERO_ABSENCE_U04_U05_U06;"
    "UNRESOLVED=ALWAYS_VS_CONDITIONAL_APPLICABILITY_RULE"
)
_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")
_INFERRED_APPLICABILITY_TOKENS: tuple[str, ...] = (
    "alwaysapplies",
    "neverapplies",
    "policyselected",
    "whenreserveconfigured",
    "whenspecificexposureexists",
    "whenhaircuteventexists",
    "whenliabilityexists",
    "whenpendingordersexist",
    "whenfeesexist",
    "venuedependent",
    "accountstatedependent",
    "instrumentstatedependent",
    "notapplicable",
    "doesnotapply",
    "applies",
    "optional",
    "disabled",
    "inactive",
    "embedded",
    "omitted",
    "safe",
    NUMERIC_PRESENT_ZERO.lower().replace("_", ""),
    NUMERIC_MISSING.lower(),
    TERM_PENDING_ORDER_RESERVATION.lower().replace("_", ""),
    TERM_LIABILITY.lower(),
    TERM_FEE.lower(),
    "u04",
    "u05",
    "u06",
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
_VECTOR_FIELDS: tuple[str, ...] = tuple(
    name for name in P01_APPLICABILITY_PROVENANCE_REQUIRED_FIELDS if name != "provenance_digest"
)


class P01ApplicabilityContractError(ValueError):
    """Fail-closed P01 applicability contract violation."""


def _fold(value: str) -> str:
    return str(value or "").strip().lower().replace("_", "").replace("-", "")


def _require_non_empty_str(*, field: str, raw: Any) -> str:
    if raw is None:
        raise P01ApplicabilityContractError(f"P01_FIELD_MISSING:{field}")
    if isinstance(raw, bool) or not isinstance(raw, str):
        raise P01ApplicabilityContractError(f"P01_FIELD_NOT_STRING:{field}")
    text = raw.strip()
    if text == "" or text != raw:
        raise P01ApplicabilityContractError(f"P01_FIELD_MISSING:{field}")
    return text


def _sha256_hex(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _canonical_json(payload: Mapping[str, str]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_p01_applicability_provenance_digest_v1(canonical: Mapping[str, str]) -> str:
    payload = {
        key: canonical[key]
        for key in P01_APPLICABILITY_PROVENANCE_REQUIRED_FIELDS
        if key != "provenance_digest"
    }
    return _sha256_hex(_canonical_json(payload))


def attach_p01_applicability_provenance_digest_v1(fields: Mapping[str, Any]) -> dict[str, Any]:
    canonical: dict[str, str] = {}
    for canonical_name in P01_APPLICABILITY_PROVENANCE_REQUIRED_FIELDS:
        if canonical_name == "provenance_digest":
            continue
        if canonical_name not in fields:
            raise P01ApplicabilityContractError(f"P01_FIELD_MISSING:{canonical_name}")
        raw = fields[canonical_name]
        canonical[canonical_name] = "" if raw is None else str(raw)
    attached = dict(fields)
    attached["provenance_digest"] = compute_p01_applicability_provenance_digest_v1(canonical)
    return attached


def _reject_coerced_applicability(*, field: str, raw: str) -> None:
    folded = _fold(raw)
    _ = field
    if raw == INCLUSION_NOT_APPLICABLE or folded in {
        "notapplicable",
        "doesnotapply",
        "na",
        "n/a",
    }:
        raise P01ApplicabilityContractError("P01_UNKNOWN_APPLICABILITY_AUTO_NA_FORBIDDEN")
    if folded in _ZERO_OR_ABSENCE_TOKENS or folded in {"0", "false"}:
        raise P01ApplicabilityContractError("P01_ZERO_OR_ABSENCE_NOT_APPLICABLE_FORBIDDEN")
    if any(token in folded for token in _INFERRED_APPLICABILITY_TOKENS):
        raise P01ApplicabilityContractError("P01_APPLICABILITY_INFERRED_FROM_LABEL_FORBIDDEN")


@dataclass(frozen=True)
class P01ApplicabilityContractV1:
    """Typed immutable P01 applicability adjudication. Not a numeric instance."""

    p01_applicability_contract_id: str
    p01_applicability_contract_version: str
    parent_p01_term_set_and_unit_class_contract_schema_class: str
    parent_p01_term_contract_schema_class: str
    target_semantic_dimension_id: str
    policy_id: str
    term_id: str
    p01_applicability_status: str
    p01_applicability_resolved_status: str
    p01_applicability_rule: str
    p01_applicability_adjudication: str
    typed_applicability_state: str
    unknown_is_not_not_applicable: str
    zero_is_not_not_applicable: str
    absence_is_not_not_applicable: str
    missing_input_fail_closed: str
    malformed_input_fail_closed: str
    term_set_unresolved_does_not_decide_applicability: str
    unit_unresolved_does_not_decide_applicability: str
    rejected_applicability_inferences: str
    remaining_unresolved_semantics: str
    evidence_classification: str
    contradiction_state: str
    term_semantics_resolved_status: str
    unspecified_closed_status: str
    p01_applicability_contract_authority_effect: str
    provenance_digest: str

    def __post_init__(self) -> None:
        _validate_p01_applicability_contract_v1(self)

    def to_canonical_dict(self) -> dict[str, str]:
        values = {
            "p01_applicability_contract_id": self.p01_applicability_contract_id,
            "p01_applicability_contract_version": self.p01_applicability_contract_version,
            "parent_p01_term_set_and_unit_class_contract_schema_class": (
                self.parent_p01_term_set_and_unit_class_contract_schema_class
            ),
            "parent_p01_term_contract_schema_class": (self.parent_p01_term_contract_schema_class),
            "target_semantic_dimension_id": self.target_semantic_dimension_id,
            "policy_id": self.policy_id,
            "term_id": self.term_id,
            "p01_applicability_status": self.p01_applicability_status,
            "p01_applicability_resolved_status": self.p01_applicability_resolved_status,
            "p01_applicability_rule": self.p01_applicability_rule,
            "p01_applicability_adjudication": self.p01_applicability_adjudication,
            "typed_applicability_state": self.typed_applicability_state,
            "unknown_is_not_not_applicable": self.unknown_is_not_not_applicable,
            "zero_is_not_not_applicable": self.zero_is_not_not_applicable,
            "absence_is_not_not_applicable": self.absence_is_not_not_applicable,
            "missing_input_fail_closed": self.missing_input_fail_closed,
            "malformed_input_fail_closed": self.malformed_input_fail_closed,
            "term_set_unresolved_does_not_decide_applicability": (
                self.term_set_unresolved_does_not_decide_applicability
            ),
            "unit_unresolved_does_not_decide_applicability": (
                self.unit_unresolved_does_not_decide_applicability
            ),
            "rejected_applicability_inferences": self.rejected_applicability_inferences,
            "remaining_unresolved_semantics": self.remaining_unresolved_semantics,
            "evidence_classification": self.evidence_classification,
            "contradiction_state": self.contradiction_state,
            "term_semantics_resolved_status": self.term_semantics_resolved_status,
            "unspecified_closed_status": self.unspecified_closed_status,
            "p01_applicability_contract_authority_effect": (
                self.p01_applicability_contract_authority_effect
            ),
            "provenance_digest": self.provenance_digest,
        }
        return {key: values[key] for key in P01_APPLICABILITY_PROVENANCE_REQUIRED_FIELDS}


def _validate_p01_applicability_contract_v1(contract: P01ApplicabilityContractV1) -> None:
    if P01_APPLICABILITY_CONTRACT_SCHEMA_PRESENT is not True:
        raise P01ApplicabilityContractError("P01_APPLICABILITY_CONTRACT_SCHEMA_PRESENT_REQUIRED")
    if P01_APPLICABILITY_CONTRACT_RUNTIME_INSTANCE_PRESENT is True:
        raise P01ApplicabilityContractError("P01_RUNTIME_INSTANCE_FORBIDDEN")
    if P01_APPLICABILITY_RESOLVED is True:
        raise P01ApplicabilityContractError("P01_APPLICABILITY_RESOLVED_PIN_FORBIDDEN")
    if P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_SCHEMA_PRESENT is not True:
        raise P01ApplicabilityContractError(
            "P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_SCHEMA_PRESENT_REQUIRED"
        )
    if P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_RUNTIME_INSTANCE_PRESENT is True:
        raise P01ApplicabilityContractError("P01_PARENT_TERM_SET_RUNTIME_INSTANCE_FORBIDDEN")
    if P01_TERM_CONTRACT_SCHEMA_PRESENT is not True:
        raise P01ApplicabilityContractError("P01_TERM_CONTRACT_SCHEMA_PRESENT_REQUIRED")
    if P01_TERM_CONTRACT_RUNTIME_INSTANCE_PRESENT is True:
        raise P01ApplicabilityContractError("P01_PARENT_RUNTIME_INSTANCE_FORBIDDEN")
    if P01_TERM_SEMANTICS_RESOLVED is True:
        raise P01ApplicabilityContractError("P01_TERM_SEMANTICS_RESOLVED_PIN_FORBIDDEN")
    if P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED is True:
        raise P01ApplicabilityContractError(
            "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED_PIN_FORBIDDEN"
        )
    if RECONSTRUCTION_ALGEBRA_COMPLETE is True:
        raise P01ApplicabilityContractError("P01_RECONSTRUCTION_ALGEBRA_COMPLETE_PIN_FORBIDDEN")
    if SOURCE_SELECTED is True or SOURCE_OBJECT_PRESENT is True:
        raise P01ApplicabilityContractError("P01_SOURCE_SELECTION_FORBIDDEN")
    contract_id = _require_non_empty_str(
        field="p01_applicability_contract_id", raw=contract.p01_applicability_contract_id
    )
    version = _require_non_empty_str(
        field="p01_applicability_contract_version",
        raw=contract.p01_applicability_contract_version,
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
        field="p01_applicability_status", raw=contract.p01_applicability_status
    )
    resolved = _require_non_empty_str(
        field="p01_applicability_resolved_status",
        raw=contract.p01_applicability_resolved_status,
    )
    rule = _require_non_empty_str(
        field="p01_applicability_rule", raw=contract.p01_applicability_rule
    )
    adjudication = _require_non_empty_str(
        field="p01_applicability_adjudication", raw=contract.p01_applicability_adjudication
    )
    typed_state = _require_non_empty_str(
        field="typed_applicability_state", raw=contract.typed_applicability_state
    )
    unknown_flag = _require_non_empty_str(
        field="unknown_is_not_not_applicable", raw=contract.unknown_is_not_not_applicable
    )
    zero_flag = _require_non_empty_str(
        field="zero_is_not_not_applicable", raw=contract.zero_is_not_not_applicable
    )
    absence_flag = _require_non_empty_str(
        field="absence_is_not_not_applicable", raw=contract.absence_is_not_not_applicable
    )
    missing_flag = _require_non_empty_str(
        field="missing_input_fail_closed", raw=contract.missing_input_fail_closed
    )
    malformed_flag = _require_non_empty_str(
        field="malformed_input_fail_closed", raw=contract.malformed_input_fail_closed
    )
    term_set_flag = _require_non_empty_str(
        field="term_set_unresolved_does_not_decide_applicability",
        raw=contract.term_set_unresolved_does_not_decide_applicability,
    )
    unit_flag = _require_non_empty_str(
        field="unit_unresolved_does_not_decide_applicability",
        raw=contract.unit_unresolved_does_not_decide_applicability,
    )
    rejected = _require_non_empty_str(
        field="rejected_applicability_inferences",
        raw=contract.rejected_applicability_inferences,
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
        field="p01_applicability_contract_authority_effect",
        raw=contract.p01_applicability_contract_authority_effect,
    )
    digest = _require_non_empty_str(field="provenance_digest", raw=contract.provenance_digest)
    if version != CONTRACT_VERSION:
        raise P01ApplicabilityContractError("P01_CONTRACT_VERSION_MISMATCH")
    if parent_term_set != PARENT_TERM_SET_CONTRACT_SCHEMA_CLASS:
        raise P01ApplicabilityContractError("P01_PARENT_TERM_SET_CONTRACT_REFERENCE_MISMATCH")
    if parent_term != PARENT_TERM_CONTRACT_SCHEMA_CLASS:
        raise P01ApplicabilityContractError("P01_PARENT_TERM_CONTRACT_REFERENCE_MISMATCH")
    if target != DIMENSION_ID:
        raise P01ApplicabilityContractError("P01_TARGET_DIMENSION_MISMATCH")
    if policy_id != POLICY_ID:
        raise P01ApplicabilityContractError("P01_POLICY_ID_MISMATCH")
    if term_id != TERM_ID:
        raise P01ApplicabilityContractError("P01_TERM_ID_MISMATCH")
    _reject_coerced_applicability(field="p01_applicability_status", raw=status)
    if status == TYPED_APPLICABILITY_STATE_APPLIES:
        raise P01ApplicabilityContractError("P01_APPLIES_UNPROVEN")
    if status == TYPED_APPLICABILITY_STATE_DOES_NOT_APPLY:
        raise P01ApplicabilityContractError("P01_UNKNOWN_APPLICABILITY_AUTO_NA_FORBIDDEN")
    if status != P01_APPLICABILITY_STATUS:
        raise P01ApplicabilityContractError("P01_APPLICABILITY_STATUS_MISMATCH")
    if resolved.lower() == "true":
        raise P01ApplicabilityContractError("P01_APPLICABILITY_RESOLVED_FORBIDDEN")
    if resolved != P01_APPLICABILITY_RESOLVED_STATUS:
        raise P01ApplicabilityContractError("P01_APPLICABILITY_RESOLVED_STATUS_MISMATCH")
    _reject_coerced_applicability(field="p01_applicability_rule", raw=rule)
    if rule != P01_APPLICABILITY_RULE:
        raise P01ApplicabilityContractError("P01_APPLICABILITY_RULE_MISMATCH")
    _reject_coerced_applicability(field="p01_applicability_adjudication", raw=adjudication)
    if adjudication != P01_APPLICABILITY_ADJUDICATION:
        raise P01ApplicabilityContractError("P01_APPLICABILITY_ADJUDICATION_MISMATCH")
    if typed_state == TYPED_APPLICABILITY_STATE_APPLIES:
        raise P01ApplicabilityContractError("P01_APPLIES_UNPROVEN")
    if typed_state == TYPED_APPLICABILITY_STATE_DOES_NOT_APPLY:
        raise P01ApplicabilityContractError("P01_UNKNOWN_APPLICABILITY_AUTO_NA_FORBIDDEN")
    if typed_state == INCLUSION_NOT_APPLICABLE:
        raise P01ApplicabilityContractError("P01_UNKNOWN_APPLICABILITY_AUTO_NA_FORBIDDEN")
    if typed_state != TYPED_APPLICABILITY_STATE:
        raise P01ApplicabilityContractError("P01_TYPED_APPLICABILITY_STATE_MISMATCH")
    if unknown_flag.lower() != "true" or unknown_flag != UNKNOWN_IS_NOT_NOT_APPLICABLE:
        raise P01ApplicabilityContractError("P01_UNKNOWN_IS_NOT_NOT_APPLICABLE_REQUIRED")
    if zero_flag.lower() != "true" or zero_flag != ZERO_IS_NOT_NOT_APPLICABLE:
        raise P01ApplicabilityContractError("P01_ZERO_IS_NOT_NOT_APPLICABLE_REQUIRED")
    if absence_flag.lower() != "true" or absence_flag != ABSENCE_IS_NOT_NOT_APPLICABLE:
        raise P01ApplicabilityContractError("P01_ABSENCE_IS_NOT_NOT_APPLICABLE_REQUIRED")
    if missing_flag.lower() != "true" or missing_flag != MISSING_INPUT_FAIL_CLOSED:
        raise P01ApplicabilityContractError("P01_MISSING_INPUT_FAIL_CLOSED_REQUIRED")
    if malformed_flag.lower() != "true" or malformed_flag != MALFORMED_INPUT_FAIL_CLOSED:
        raise P01ApplicabilityContractError("P01_MALFORMED_INPUT_FAIL_CLOSED_REQUIRED")
    if (
        term_set_flag.lower() != "true"
        or term_set_flag != TERM_SET_UNRESOLVED_DOES_NOT_DECIDE_APPLICABILITY
    ):
        raise P01ApplicabilityContractError("P01_TERM_SET_MUST_NOT_DECIDE_APPLICABILITY")
    if unit_flag.lower() != "true" or unit_flag != UNIT_UNRESOLVED_DOES_NOT_DECIDE_APPLICABILITY:
        raise P01ApplicabilityContractError("P01_UNIT_MUST_NOT_DECIDE_APPLICABILITY")
    if rejected != REJECTED_APPLICABILITY_INFERENCES:
        raise P01ApplicabilityContractError("P01_REJECTED_APPLICABILITY_INFERENCES_MISMATCH")
    if remaining != REMAINING_UNRESOLVED_SEMANTICS:
        raise P01ApplicabilityContractError("P01_REMAINING_UNRESOLVED_SEMANTICS_MISMATCH")
    if "P01_APPLICABILITY_UNSPECIFIED" not in remaining:
        raise P01ApplicabilityContractError("P01_APPLICABILITY_MUST_REMAIN_UNSPECIFIED")
    if evidence != EVIDENCE_CLASSIFICATION:
        raise P01ApplicabilityContractError("P01_EVIDENCE_CLASSIFICATION_MISMATCH")
    if contradiction != CONTRADICTION_NONE:
        raise P01ApplicabilityContractError("P01_CONTRADICTION_STATUS_MISMATCH")
    if semantics_resolved.lower() == "true":
        raise P01ApplicabilityContractError("P01_TERM_SEMANTICS_RESOLVED_FORBIDDEN")
    if semantics_resolved != TERM_SEMANTICS_RESOLVED_STATUS:
        raise P01ApplicabilityContractError("P01_TERM_SEMANTICS_RESOLVED_STATUS_MISMATCH")
    if closed.lower() == "true":
        raise P01ApplicabilityContractError(
            "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED_FORBIDDEN"
        )
    if closed != UNSPECIFIED_CLOSED_STATUS:
        raise P01ApplicabilityContractError("P01_UNSPECIFIED_CLOSED_STATUS_MISMATCH")
    if effect != P01_APPLICABILITY_CONTRACT_AUTHORITY_EFFECT or effect != AUTHORITY_EFFECT_NONE:
        raise P01ApplicabilityContractError("P01_AUTHORITY_EFFECT_MUST_REMAIN_NONE")
    if EARLIEST_UNRESOLVED_ALGEBRA_TERM != "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED":
        raise P01ApplicabilityContractError("P01_EARLIEST_ALGEBRA_TERM_DRIFT")
    if "U04_PENDING_ORDER_RESERVATION_INCLUSION_UNRESOLVED" not in UNRESOLVED_ALGEBRA_TERMS:
        raise P01ApplicabilityContractError("P01_U04_MUST_REMAIN_UNRESOLVED")
    if "U05_LIABILITY_INCLUSION_OR_VALUE_UNRESOLVED" not in UNRESOLVED_ALGEBRA_TERMS:
        raise P01ApplicabilityContractError("P01_U05_MUST_REMAIN_UNRESOLVED")
    if "U06_FEE_INCLUSION_UNRESOLVED" not in UNRESOLVED_ALGEBRA_TERMS:
        raise P01ApplicabilityContractError("P01_U06_MUST_REMAIN_UNRESOLVED")
    parent_term_contract = build_p01_haircut_reserve_depletion_term_contract_v1(
        p01_term_contract_id="P01_APPLICABILITY_PARENT_TERM_ALIGNMENT"
    )
    if parent_term_contract.applicability_state != P01_APPLICABILITY_STATUS:
        raise P01ApplicabilityContractError("P01_PARENT_APPLICABILITY_ALIGNMENT_MISMATCH")
    parent_term_set_contract = build_p01_term_set_and_unit_class_contract_v1(
        p01_term_set_and_unit_class_contract_id="P01_APPLICABILITY_PARENT_TERM_SET_ALIGNMENT"
    )
    if parent_term_set_contract.p01_term_set_resolved_status != "false":
        raise P01ApplicabilityContractError("P01_PARENT_TERM_SET_RESOLVED_ALIGNMENT")
    if parent_term_set_contract.p01_value_unit_class_resolved_status != "false":
        raise P01ApplicabilityContractError("P01_PARENT_UNIT_RESOLVED_ALIGNMENT")
    algebra = build_reconstruction_algebra_contract_v1(
        algebra_contract_id="P01_APPLICABILITY_ALGEBRA_ALIGNMENT"
    )
    p01_term = next(term for term in algebra.terms if term.term_id == TERM_ID)
    if p01_term.inclusion_state == INCLUSION_NOT_APPLICABLE:
        raise P01ApplicabilityContractError("P01_UNKNOWN_APPLICABILITY_AUTO_NA_FORBIDDEN")
    if algebra.algebra_completeness_status != "INCOMPLETE":
        raise P01ApplicabilityContractError("P01_ALGEBRA_COMPLETENESS_ALIGNMENT")
    canonical = contract.to_canonical_dict()
    expected_digest = compute_p01_applicability_provenance_digest_v1(canonical)
    if not _SHA256_HEX.fullmatch(digest):
        raise P01ApplicabilityContractError("P01_PROVENANCE_DIGEST_NOT_SHA256")
    if digest != expected_digest:
        raise P01ApplicabilityContractError("P01_PROVENANCE_DIGEST_MISMATCH")
    _ = contract_id


def build_p01_applicability_contract_v1(**fields: Any) -> P01ApplicabilityContractV1:
    """Construct the typed P01 applicability contract. Does not resolve P01."""

    payload = dict(fields)
    defaults = {
        "p01_applicability_contract_version": CONTRACT_VERSION,
        "parent_p01_term_set_and_unit_class_contract_schema_class": (
            PARENT_TERM_SET_CONTRACT_SCHEMA_CLASS
        ),
        "parent_p01_term_contract_schema_class": PARENT_TERM_CONTRACT_SCHEMA_CLASS,
        "target_semantic_dimension_id": DIMENSION_ID,
        "policy_id": POLICY_ID,
        "term_id": TERM_ID,
        "p01_applicability_status": P01_APPLICABILITY_STATUS,
        "p01_applicability_resolved_status": P01_APPLICABILITY_RESOLVED_STATUS,
        "p01_applicability_rule": P01_APPLICABILITY_RULE,
        "p01_applicability_adjudication": P01_APPLICABILITY_ADJUDICATION,
        "typed_applicability_state": TYPED_APPLICABILITY_STATE,
        "unknown_is_not_not_applicable": UNKNOWN_IS_NOT_NOT_APPLICABLE,
        "zero_is_not_not_applicable": ZERO_IS_NOT_NOT_APPLICABLE,
        "absence_is_not_not_applicable": ABSENCE_IS_NOT_NOT_APPLICABLE,
        "missing_input_fail_closed": MISSING_INPUT_FAIL_CLOSED,
        "malformed_input_fail_closed": MALFORMED_INPUT_FAIL_CLOSED,
        "term_set_unresolved_does_not_decide_applicability": (
            TERM_SET_UNRESOLVED_DOES_NOT_DECIDE_APPLICABILITY
        ),
        "unit_unresolved_does_not_decide_applicability": (
            UNIT_UNRESOLVED_DOES_NOT_DECIDE_APPLICABILITY
        ),
        "rejected_applicability_inferences": REJECTED_APPLICABILITY_INFERENCES,
        "remaining_unresolved_semantics": REMAINING_UNRESOLVED_SEMANTICS,
        "evidence_classification": EVIDENCE_CLASSIFICATION,
        "contradiction_state": CONTRADICTION_NONE,
        "term_semantics_resolved_status": TERM_SEMANTICS_RESOLVED_STATUS,
        "unspecified_closed_status": UNSPECIFIED_CLOSED_STATUS,
        "p01_applicability_contract_authority_effect": AUTHORITY_EFFECT_NONE,
    }
    for key, value in defaults.items():
        payload.setdefault(key, value)
    missing = [name for name in _VECTOR_FIELDS if name not in payload]
    if missing:
        raise P01ApplicabilityContractError("P01_FIELD_MISSING:" + ",".join(missing))
    attached = attach_p01_applicability_provenance_digest_v1(payload)
    return P01ApplicabilityContractV1(
        **{name: attached[name] for name in P01_APPLICABILITY_PROVENANCE_REQUIRED_FIELDS}
    )


def reject_p01_unknown_applicability_as_not_applicable_v1(*, applicability_status: str) -> None:
    """Unknown P01 applicability is not NOT_APPLICABLE."""

    _reject_coerced_applicability(field="p01_applicability_status", raw=applicability_status)
    if applicability_status in {
        INCLUSION_NOT_APPLICABLE,
        TYPED_APPLICABILITY_STATE_DOES_NOT_APPLY,
        TYPED_APPLICABILITY_STATE_APPLIES,
    }:
        raise P01ApplicabilityContractError("P01_UNKNOWN_APPLICABILITY_AUTO_NA_FORBIDDEN")
    raise P01ApplicabilityContractError("P01_APPLICABILITY_STATUS_MISMATCH")


def reject_p01_zero_or_absence_as_not_applicable_v1(*, applicability_status: str) -> None:
    """Zero or term absence is not P01 NOT_APPLICABLE."""

    _reject_coerced_applicability(field="p01_applicability_status", raw=applicability_status)
    raise P01ApplicabilityContractError("P01_APPLICABILITY_STATUS_MISMATCH")


def reject_p01_applicability_inferred_from_u04_u05_u06_or_venue_v1(
    *, applicability_rule: str
) -> None:
    """U04/U05/U06 or venue-raw state is not a P01 applicability rule."""

    _reject_coerced_applicability(field="p01_applicability_rule", raw=applicability_rule)
    raise P01ApplicabilityContractError("P01_APPLICABILITY_RULE_MISMATCH")
