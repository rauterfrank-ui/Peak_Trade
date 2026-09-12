"""Typed P01 haircut/reserve/depletion term contract.

Encodes only Owner-ratified and algebra-proven P01 facts. Does not specify
the P01 member term set, unit class, numeric value, or productive
reconstruction. Schema presence is not P01 semantic resolution.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Mapping

from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    GOVERNED_PRODUCER_CREATED,
    INTERNAL_RECONSTRUCTION_PROVEN,
    INTERNAL_RECONSTRUCTION_RUNTIME_INSTANCE_PRESENT,
    LIVE_RESTART_RECONSTRUCTED,
    P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED,
    P01_PROVENANCE_REQUIRED_FIELDS,
    P01_TERM_CONTRACT_AUTHORITY_EFFECT,
    P01_TERM_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_TERM_CONTRACT_SCHEMA_PRESENT,
    P01_TERM_SEMANTICS_RESOLVED,
    RECONCILIATION_CONTRACT_CREATED,
    RECONSTRUCTION_ALGEBRA_COMPLETE,
    RECONSTRUCTION_ALGEBRA_SCHEMA_PRESENT,
    SOURCE_OBJECT_PRESENT,
    SOURCE_SELECTED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.reconstruction_algebra_contract_v1 import (
    CONTRADICTION_NONE,
    CURRENCY_DOMAIN_UNSPECIFIED,
    CURRENCY_DOMAIN_USDC,
    DIMENSION_ID,
    EARLIEST_UNRESOLVED_ALGEBRA_TERM,
    EMBEDDED_NO,
    EMBEDDED_NOT_APPLICABLE,
    EMBEDDED_UNRESOLVED,
    INCLUSION_NOT_APPLICABLE,
    INCLUSION_NOT_IN_BASE,
    INCLUSION_UNRESOLVED,
    NUMERIC_MALFORMED,
    NUMERIC_MISSING,
    NUMERIC_NOT_COMPUTED,
    NUMERIC_PRESENT_ZERO,
    P01_HAIRCUTS_RESERVE_DEPLETION,
    ROLE_ADDITIVE,
    ROLE_REDUCTION_ONLY_UNSPECIFIED,
    ROLE_SUBTRACTIVE,
    SCHEMA_CLASS as ALGEBRA_SCHEMA_CLASS,
    SIGN_ADD,
    SIGN_REDUCTION_ONLY,
    TERM_FEE,
    TERM_LIABILITY,
    TERM_P01_HAIRCUT_RESERVE_DEPLETION,
    TERM_PENDING_ORDER_RESERVATION,
    TERM_SET_UNSPECIFIED,
    UNRESOLVED_ALGEBRA_TERMS,
    build_reconstruction_algebra_contract_v1,
)

SCHEMA_CLASS = "P01_HAIRCUT_RESERVE_DEPLETION_TERM_CONTRACT_V1"
P01_TERM_CONTRACT_VERSION = "v1"
POLICY_ID = "P01"
TERM_ID = TERM_P01_HAIRCUT_RESERVE_DEPLETION
SEMANTIC_CLASS = "HAIRCUT_RESERVE_DEPLETION_FAMILY"
ALGEBRAIC_ROLE = ROLE_REDUCTION_ONLY_UNSPECIFIED
ECONOMIC_MEANING = (
    "HAIRCUT_RESERVE_AND_DEPLETION_REDUCTION_ONLY;"
    "EACH_TERM_NON_NEGATIVE;"
    "MUST_NOT_INCREASE_EQUITY;"
    "UNSPECIFIED_OR_UNCLEAR_FAIL_CLOSED;"
    "ZERO_ONLY_BY_EXPLICIT_NORMATIVE_POLICY;"
    "NO_VENUE_RAW_HAIRCUTS;"
    "NO_C01_C21_ELEVATION"
)
VALUE_UNIT_CLASS = "UNSPECIFIED"
CURRENCY_VALUATION_DOMAIN = "PARENT_DIMENSION_SETTLEMENT_USDC_P01_UNIT_CLASS_UNSPECIFIED"
APPLICABILITY_STATE = "UNSPECIFIED_FAIL_CLOSED"
PROVENANCE_REQUIREMENTS = (
    "NO_VENUE_RAW_HAIRCUTS;"
    "NO_C01_C21_ELEVATION;"
    "NO_FORBIDDEN_FIELD_FALLBACK;"
    "P01_NUMERIC_VALUE_PROVENANCE_UNSPECIFIED"
)
ORIGIN_CLASS = "POLICY_DEFINED_OPERATOR_UNSPECIFIED_TERM_SET_AND_VALUE"
INCLUSION_STATE = INCLUSION_UNRESOLVED
EMBEDDED_STATE = EMBEDDED_UNRESOLVED
OVERLAP_STATE = (
    "U06_ACCRUED_FEES_DISTINCT;"
    "FUTURE_FEES_MAY_BE_P01_RESERVE;"
    "U04_U05_EQUIVALENCE_UNPROVEN;"
    "UNKNOWN_OVERLAP_FAIL_CLOSED"
)
DOUBLE_COUNTING_GUARD = "P01_REDUCTION_ONCE_UNKNOWN_OVERLAP_FAIL_CLOSED"
SIGN_CONSTRAINTS = "NON_NEGATIVE_REDUCTION_ONLY_MUST_NOT_INCREASE_EQUITY"
NEGATIVE_ALLOWED = "false"
ZERO_VALIDITY_SEMANTICS = "PRESENT_ZERO_ONLY_BY_EXPLICIT_NORMATIVE_POLICY_MISSING_IS_NOT_ZERO"
FRESHNESS_EPOCH_REQUIREMENTS = (
    "U09_FRESH_GET_PER_PRETRADE_DECISION;P01_MEMBER_FRESHNESS_INHERITANCE_UNPROVEN"
)
COMPLETENESS_RESOLUTION_STATE = "UNRESOLVED"
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
EVIDENCE_CLASSIFICATION = (
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_T_P01_REDUCTION_ONLY_UNSPECIFIED_FAIL_CLOSED;"
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_AA_ALGEBRA_P01_REDUCTION_ONLY_UNSPECIFIED;"
    "FORENSIC_EVIDENCE=U06_FUTURE_FEES_MAY_EXIST_ONLY_AS_SEPARATE_P01_RESERVE_TERM;"
    "HISTORICAL_STATE=11_2_1_N_HAIRCUTS_RESERVE_DEPLETION_FROZEN_PENDING_OWNER_POLICY_SUPERSEDED;"
    "STRUCTURAL_REUSE_ONLY=RECONSTRUCTION_ALGEBRA_CONTRACT_V1;"
    "NAVIGATION=MAP_OF_TRUTH_NON_SSOT;"
    "REJECTED=VENUE_RAW_HAIRCUTS_C01_C21_AVAILEQ_TOTALEQ_EQ_ADJEQ_AVAILBAL_CASHBAL_FROZENBAL;"
    "UNRESOLVED=TERM_SET_UNIT_CLASS_APPLICABILITY_BASE_INCLUSION_U04_U05_OVERLAP_VALUE_PROVENANCE"
)
AUTHORITY_EFFECT_NONE = "NONE"
NUMERIC_STATE = NUMERIC_NOT_COMPUTED
_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")
_FORBIDDEN_FALLBACK_MARKERS: tuple[str, ...] = ("|", " or ", ",", ";")
_FORBIDDEN_VENUE_FIELD_MARKERS: tuple[str, ...] = (
    "details.availeq",
    "availeq",
    "totaleq",
    "adjeq",
    "availbal",
    "cashbal",
    "frozenbal",
    "isoeq",
    "ordfrozen",
)
_BARE_FORBIDDEN_TOKENS: tuple[str, ...] = ("eq", "upl")
_FORBIDDEN_OBJECT_TOKENS: tuple[str, ...] = (
    "accountingportfoliostatev1",
    "ledgersnapshot",
    "equitybyccy",
    "simulatedportfoliostatev1",
    "fundingaccountbalanceobservationv1",
    "freshavailablemarginobservationv1",
    "balancesnapshot",
    "start_balance",
)
_P01_VECTOR_FIELDS: tuple[str, ...] = tuple(
    name for name in P01_PROVENANCE_REQUIRED_FIELDS if name != "provenance_digest"
)


class P01HaircutReserveDepletionTermContractError(ValueError):
    """Fail-closed P01 haircut/reserve/depletion term contract violation."""


def _fold(value: str) -> str:
    return str(value or "").strip().lower().replace("_", "").replace("-", "")


def _require_non_empty_str(*, field: str, raw: Any) -> str:
    if raw is None:
        raise P01HaircutReserveDepletionTermContractError(f"P01_FIELD_MISSING:{field}")
    if not isinstance(raw, str):
        raise P01HaircutReserveDepletionTermContractError(f"P01_FIELD_NOT_STRING:{field}")
    text = raw.strip()
    if text == "" or text != raw:
        raise P01HaircutReserveDepletionTermContractError(f"P01_FIELD_MISSING:{field}")
    return text


def _reject_fallback_chain(*, field: str, raw: str) -> None:
    lowered = raw.lower()
    for marker in _FORBIDDEN_FALLBACK_MARKERS:
        if marker in lowered and field in {
            "p01_term_contract_id",
            "policy_id",
            "term_id",
            "algebra_contract_schema_class",
            "target_semantic_dimension_id",
        }:
            raise P01HaircutReserveDepletionTermContractError(
                f"P01_FALLBACK_CHAIN_FORBIDDEN:{field}"
            )


def _token_is_forbidden(raw: str) -> bool:
    folded = _fold(raw)
    if not folded:
        return False
    if folded in _BARE_FORBIDDEN_TOKENS:
        return True
    if any(marker in folded for marker in _FORBIDDEN_VENUE_FIELD_MARKERS):
        return True
    return any(token in folded for token in _FORBIDDEN_OBJECT_TOKENS)


def _reject_forbidden_authority_token(*, field: str, raw: str) -> None:
    if _token_is_forbidden(raw):
        raise P01HaircutReserveDepletionTermContractError(f"P01_FORBIDDEN_AUTHORITY_FIELD:{field}")


def _sha256_hex(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _canonical_json(payload: Mapping[str, str]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_p01_term_provenance_digest_v1(canonical: Mapping[str, str]) -> str:
    payload = {
        key: canonical[key] for key in P01_PROVENANCE_REQUIRED_FIELDS if key != "provenance_digest"
    }
    return _sha256_hex(_canonical_json(payload))


def attach_p01_term_provenance_digest_v1(fields: Mapping[str, Any]) -> dict[str, Any]:
    """Attach the deterministic digest. Does not reconstruct or bind."""

    canonical: dict[str, str] = {}
    for canonical_name in P01_PROVENANCE_REQUIRED_FIELDS:
        if canonical_name == "provenance_digest":
            continue
        if canonical_name not in fields:
            raise P01HaircutReserveDepletionTermContractError(f"P01_FIELD_MISSING:{canonical_name}")
        raw = fields[canonical_name]
        canonical[canonical_name] = "" if raw is None else str(raw)
    attached = dict(fields)
    attached["provenance_digest"] = compute_p01_term_provenance_digest_v1(canonical)
    return attached


def _policy_pins() -> Mapping[str, Any]:
    from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
        P01_HAIRCUTS_RESERVE_DEPLETION as PIN_P01,
        P01_MAY_INCREASE_EQUITY,
        P01_ZERO_ONLY_BY_EXPLICIT_POLICY,
        U04_PENDING_ORDER_RESERVATIONS,
        U05_LIABILITIES_BORROWINGS,
        U06_FEES,
        USD_EQUALS_USDC,
    )

    return {
        "P01_HAIRCUTS_RESERVE_DEPLETION": PIN_P01,
        "P01_MAY_INCREASE_EQUITY": P01_MAY_INCREASE_EQUITY,
        "P01_ZERO_ONLY_BY_EXPLICIT_POLICY": P01_ZERO_ONLY_BY_EXPLICIT_POLICY,
        "U04_PENDING_ORDER_RESERVATIONS": U04_PENDING_ORDER_RESERVATIONS,
        "U05_LIABILITIES_BORROWINGS": U05_LIABILITIES_BORROWINGS,
        "U06_FEES": U06_FEES,
        "USD_EQUALS_USDC": USD_EQUALS_USDC,
    }


@dataclass(frozen=True)
class P01HaircutReserveDepletionTermContractV1:
    """Typed immutable P01 term contract. Schema only. Not a numeric instance."""

    p01_term_contract_id: str
    p01_term_contract_version: str
    algebra_contract_schema_class: str
    target_semantic_dimension_id: str
    policy_id: str
    term_id: str
    semantic_class: str
    algebraic_role: str
    economic_meaning: str
    value_unit_class: str
    currency_valuation_domain: str
    applicability_state: str
    provenance_requirements: str
    origin_class: str
    inclusion_state: str
    embedded_state: str
    overlap_state: str
    double_counting_guard: str
    sign_constraints: str
    negative_allowed: str
    zero_validity_semantics: str
    freshness_epoch_requirements: str
    completeness_resolution_state: str
    term_semantics_resolved_status: str
    unspecified_closed_status: str
    remaining_unresolved_semantics: str
    evidence_classification: str
    contradiction_state: str
    p01_term_contract_authority_effect: str
    numeric_state: str
    provenance_digest: str

    def __post_init__(self) -> None:
        _validate_p01_term_contract_v1(self)

    def to_canonical_dict(self) -> dict[str, str]:
        values = {
            "p01_term_contract_id": self.p01_term_contract_id,
            "p01_term_contract_version": self.p01_term_contract_version,
            "algebra_contract_schema_class": self.algebra_contract_schema_class,
            "target_semantic_dimension_id": self.target_semantic_dimension_id,
            "policy_id": self.policy_id,
            "term_id": self.term_id,
            "semantic_class": self.semantic_class,
            "algebraic_role": self.algebraic_role,
            "economic_meaning": self.economic_meaning,
            "value_unit_class": self.value_unit_class,
            "currency_valuation_domain": self.currency_valuation_domain,
            "applicability_state": self.applicability_state,
            "provenance_requirements": self.provenance_requirements,
            "origin_class": self.origin_class,
            "inclusion_state": self.inclusion_state,
            "embedded_state": self.embedded_state,
            "overlap_state": self.overlap_state,
            "double_counting_guard": self.double_counting_guard,
            "sign_constraints": self.sign_constraints,
            "negative_allowed": self.negative_allowed,
            "zero_validity_semantics": self.zero_validity_semantics,
            "freshness_epoch_requirements": self.freshness_epoch_requirements,
            "completeness_resolution_state": self.completeness_resolution_state,
            "term_semantics_resolved_status": self.term_semantics_resolved_status,
            "unspecified_closed_status": self.unspecified_closed_status,
            "remaining_unresolved_semantics": self.remaining_unresolved_semantics,
            "evidence_classification": self.evidence_classification,
            "contradiction_state": self.contradiction_state,
            "p01_term_contract_authority_effect": self.p01_term_contract_authority_effect,
            "numeric_state": self.numeric_state,
            "provenance_digest": self.provenance_digest,
        }
        return {key: values[key] for key in P01_PROVENANCE_REQUIRED_FIELDS}


def _validate_p01_term_contract_v1(contract: P01HaircutReserveDepletionTermContractV1) -> None:
    if P01_TERM_CONTRACT_SCHEMA_PRESENT is not True:
        raise P01HaircutReserveDepletionTermContractError(
            "P01_TERM_CONTRACT_SCHEMA_PRESENT_REQUIRED"
        )
    if P01_TERM_CONTRACT_RUNTIME_INSTANCE_PRESENT is True:
        raise P01HaircutReserveDepletionTermContractError("P01_RUNTIME_INSTANCE_FORBIDDEN")
    if P01_TERM_SEMANTICS_RESOLVED is True:
        raise P01HaircutReserveDepletionTermContractError(
            "P01_TERM_SEMANTICS_RESOLVED_PIN_FORBIDDEN"
        )
    if P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED is True:
        raise P01HaircutReserveDepletionTermContractError(
            "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED_PIN_FORBIDDEN"
        )
    if RECONSTRUCTION_ALGEBRA_SCHEMA_PRESENT is not True:
        raise P01HaircutReserveDepletionTermContractError(
            "P01_RECONSTRUCTION_ALGEBRA_SCHEMA_PRESENT_REQUIRED"
        )
    if RECONSTRUCTION_ALGEBRA_COMPLETE is True:
        raise P01HaircutReserveDepletionTermContractError(
            "P01_RECONSTRUCTION_ALGEBRA_COMPLETE_PIN_FORBIDDEN"
        )
    if INTERNAL_RECONSTRUCTION_RUNTIME_INSTANCE_PRESENT is True:
        raise P01HaircutReserveDepletionTermContractError(
            "P01_INTERNAL_RECONSTRUCTION_RUNTIME_INSTANCE_FORBIDDEN"
        )
    if INTERNAL_RECONSTRUCTION_PROVEN is True:
        raise P01HaircutReserveDepletionTermContractError(
            "P01_INTERNAL_RECONSTRUCTION_PROVEN_PIN_FORBIDDEN"
        )
    if SOURCE_SELECTED is True or SOURCE_OBJECT_PRESENT is True:
        raise P01HaircutReserveDepletionTermContractError("P01_SOURCE_SELECTION_FORBIDDEN")
    if GOVERNED_PRODUCER_CREATED is True:
        raise P01HaircutReserveDepletionTermContractError("P01_GOVERNED_PRODUCER_CREATED_FORBIDDEN")
    if RECONCILIATION_CONTRACT_CREATED is True:
        raise P01HaircutReserveDepletionTermContractError(
            "P01_RECONCILIATION_CONTRACT_CREATED_FORBIDDEN"
        )
    if LIVE_RESTART_RECONSTRUCTED is True:
        raise P01HaircutReserveDepletionTermContractError(
            "P01_LIVE_RESTART_RECONSTRUCTED_FORBIDDEN"
        )
    contract_id = _require_non_empty_str(
        field="p01_term_contract_id", raw=contract.p01_term_contract_id
    )
    version = _require_non_empty_str(
        field="p01_term_contract_version", raw=contract.p01_term_contract_version
    )
    algebra_ref = _require_non_empty_str(
        field="algebra_contract_schema_class", raw=contract.algebra_contract_schema_class
    )
    target = _require_non_empty_str(
        field="target_semantic_dimension_id", raw=contract.target_semantic_dimension_id
    )
    policy_id = _require_non_empty_str(field="policy_id", raw=contract.policy_id)
    term_id = _require_non_empty_str(field="term_id", raw=contract.term_id)
    semantic_class = _require_non_empty_str(field="semantic_class", raw=contract.semantic_class)
    algebraic_role = _require_non_empty_str(field="algebraic_role", raw=contract.algebraic_role)
    economic_meaning = _require_non_empty_str(
        field="economic_meaning", raw=contract.economic_meaning
    )
    value_unit = _require_non_empty_str(field="value_unit_class", raw=contract.value_unit_class)
    currency_domain = _require_non_empty_str(
        field="currency_valuation_domain", raw=contract.currency_valuation_domain
    )
    applicability = _require_non_empty_str(
        field="applicability_state", raw=contract.applicability_state
    )
    provenance = _require_non_empty_str(
        field="provenance_requirements", raw=contract.provenance_requirements
    )
    origin = _require_non_empty_str(field="origin_class", raw=contract.origin_class)
    inclusion = _require_non_empty_str(field="inclusion_state", raw=contract.inclusion_state)
    embedded = _require_non_empty_str(field="embedded_state", raw=contract.embedded_state)
    overlap = _require_non_empty_str(field="overlap_state", raw=contract.overlap_state)
    guard = _require_non_empty_str(
        field="double_counting_guard", raw=contract.double_counting_guard
    )
    sign = _require_non_empty_str(field="sign_constraints", raw=contract.sign_constraints)
    negative = _require_non_empty_str(field="negative_allowed", raw=contract.negative_allowed)
    zero = _require_non_empty_str(
        field="zero_validity_semantics", raw=contract.zero_validity_semantics
    )
    freshness = _require_non_empty_str(
        field="freshness_epoch_requirements", raw=contract.freshness_epoch_requirements
    )
    completeness = _require_non_empty_str(
        field="completeness_resolution_state", raw=contract.completeness_resolution_state
    )
    resolved = _require_non_empty_str(
        field="term_semantics_resolved_status", raw=contract.term_semantics_resolved_status
    )
    closed = _require_non_empty_str(
        field="unspecified_closed_status", raw=contract.unspecified_closed_status
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
    effect = _require_non_empty_str(
        field="p01_term_contract_authority_effect",
        raw=contract.p01_term_contract_authority_effect,
    )
    numeric = _require_non_empty_str(field="numeric_state", raw=contract.numeric_state)
    digest = _require_non_empty_str(field="provenance_digest", raw=contract.provenance_digest)
    if version != P01_TERM_CONTRACT_VERSION:
        raise P01HaircutReserveDepletionTermContractError("P01_CONTRACT_VERSION_MISMATCH")
    if algebra_ref != ALGEBRA_SCHEMA_CLASS:
        raise P01HaircutReserveDepletionTermContractError("P01_ALGEBRA_CONTRACT_REFERENCE_MISMATCH")
    if target != DIMENSION_ID:
        raise P01HaircutReserveDepletionTermContractError("P01_TARGET_DIMENSION_MISMATCH")
    if policy_id != POLICY_ID:
        raise P01HaircutReserveDepletionTermContractError("P01_POLICY_ID_MISMATCH")
    if term_id != TERM_ID:
        raise P01HaircutReserveDepletionTermContractError("P01_TERM_ID_MISMATCH")
    if semantic_class != SEMANTIC_CLASS:
        raise P01HaircutReserveDepletionTermContractError("P01_SEMANTIC_CLASS_MISMATCH")
    if algebraic_role == ROLE_SUBTRACTIVE:
        raise P01HaircutReserveDepletionTermContractError("P01_INDEPENDENT_SUBTRACTIVE_UNPROVEN")
    if algebraic_role == ROLE_ADDITIVE:
        raise P01HaircutReserveDepletionTermContractError("P01_MAY_INCREASE_EQUITY_FORBIDDEN")
    if algebraic_role != ALGEBRAIC_ROLE:
        raise P01HaircutReserveDepletionTermContractError("P01_ALGEBRAIC_ROLE_MISMATCH")
    if economic_meaning != ECONOMIC_MEANING:
        raise P01HaircutReserveDepletionTermContractError("P01_ECONOMIC_MEANING_MISMATCH")
    if value_unit == CURRENCY_DOMAIN_USDC or value_unit.lower() == "currency":
        raise P01HaircutReserveDepletionTermContractError("P01_UNIT_INFERRED_CURRENCY_FORBIDDEN")
    if value_unit != VALUE_UNIT_CLASS:
        raise P01HaircutReserveDepletionTermContractError("P01_VALUE_UNIT_CLASS_MISMATCH")
    if currency_domain == CURRENCY_DOMAIN_USDC:
        raise P01HaircutReserveDepletionTermContractError("P01_UNIT_INFERRED_CURRENCY_FORBIDDEN")
    if currency_domain != CURRENCY_VALUATION_DOMAIN:
        raise P01HaircutReserveDepletionTermContractError("P01_CURRENCY_DOMAIN_MISMATCH")
    if applicability in {"NOT_APPLICABLE", INCLUSION_NOT_APPLICABLE}:
        raise P01HaircutReserveDepletionTermContractError(
            "P01_UNKNOWN_APPLICABILITY_AUTO_NA_FORBIDDEN"
        )
    if applicability != APPLICABILITY_STATE:
        raise P01HaircutReserveDepletionTermContractError("P01_APPLICABILITY_MISMATCH")
    if provenance != PROVENANCE_REQUIREMENTS:
        raise P01HaircutReserveDepletionTermContractError("P01_PROVENANCE_REQUIREMENTS_MISMATCH")
    if origin != ORIGIN_CLASS:
        raise P01HaircutReserveDepletionTermContractError("P01_ORIGIN_CLASS_MISMATCH")
    if inclusion == INCLUSION_NOT_IN_BASE:
        raise P01HaircutReserveDepletionTermContractError("P01_BASE_EXCLUSION_UNPROVEN")
    if inclusion == INCLUSION_NOT_APPLICABLE:
        raise P01HaircutReserveDepletionTermContractError(
            "P01_UNKNOWN_APPLICABILITY_AUTO_NA_FORBIDDEN"
        )
    if inclusion != INCLUSION_STATE:
        raise P01HaircutReserveDepletionTermContractError("P01_INCLUSION_STATE_MISMATCH")
    if embedded == EMBEDDED_NO:
        raise P01HaircutReserveDepletionTermContractError("P01_NON_EMBEDDING_UNPROVEN")
    if embedded == EMBEDDED_NOT_APPLICABLE:
        raise P01HaircutReserveDepletionTermContractError(
            "P01_UNKNOWN_APPLICABILITY_AUTO_NA_FORBIDDEN"
        )
    if embedded != EMBEDDED_STATE:
        raise P01HaircutReserveDepletionTermContractError("P01_EMBEDDED_STATE_MISMATCH")
    if "safe" in _fold(overlap) or overlap in {"SAFE", "NO_OVERLAP", "NONE"}:
        raise P01HaircutReserveDepletionTermContractError("P01_UNKNOWN_OVERLAP_AUTO_SAFE_FORBIDDEN")
    if overlap != OVERLAP_STATE:
        raise P01HaircutReserveDepletionTermContractError("P01_OVERLAP_STATE_MISMATCH")
    if "safe" in _fold(guard):
        raise P01HaircutReserveDepletionTermContractError("P01_UNKNOWN_OVERLAP_AUTO_SAFE_FORBIDDEN")
    if guard != DOUBLE_COUNTING_GUARD:
        raise P01HaircutReserveDepletionTermContractError("P01_DOUBLE_COUNTING_GUARD_MISMATCH")
    if sign == SIGN_ADD or sign == "MAY_INCREASE_EQUITY":
        raise P01HaircutReserveDepletionTermContractError("P01_MAY_INCREASE_EQUITY_FORBIDDEN")
    if sign != SIGN_CONSTRAINTS:
        raise P01HaircutReserveDepletionTermContractError("P01_SIGN_CONSTRAINTS_MISMATCH")
    if negative.lower() in {"true", "yes", "allowed"}:
        raise P01HaircutReserveDepletionTermContractError("P01_NEGATIVE_FORBIDDEN")
    if negative != NEGATIVE_ALLOWED:
        raise P01HaircutReserveDepletionTermContractError("P01_NEGATIVE_ALLOWED_MISMATCH")
    if zero != ZERO_VALIDITY_SEMANTICS:
        raise P01HaircutReserveDepletionTermContractError("P01_ZERO_VALIDITY_MISMATCH")
    if freshness != FRESHNESS_EPOCH_REQUIREMENTS:
        raise P01HaircutReserveDepletionTermContractError("P01_FRESHNESS_EPOCH_MISMATCH")
    if completeness != COMPLETENESS_RESOLUTION_STATE:
        raise P01HaircutReserveDepletionTermContractError("P01_COMPLETENESS_RESOLUTION_MISMATCH")
    if resolved.lower() == "true":
        raise P01HaircutReserveDepletionTermContractError("P01_TERM_SEMANTICS_RESOLVED_FORBIDDEN")
    if resolved != TERM_SEMANTICS_RESOLVED_STATUS:
        raise P01HaircutReserveDepletionTermContractError(
            "P01_TERM_SEMANTICS_RESOLVED_STATUS_MISMATCH"
        )
    if closed.lower() == "true":
        raise P01HaircutReserveDepletionTermContractError(
            "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED_FORBIDDEN"
        )
    if closed != UNSPECIFIED_CLOSED_STATUS:
        raise P01HaircutReserveDepletionTermContractError("P01_UNSPECIFIED_CLOSED_STATUS_MISMATCH")
    if remaining != REMAINING_UNRESOLVED_SEMANTICS:
        raise P01HaircutReserveDepletionTermContractError(
            "P01_REMAINING_UNRESOLVED_SEMANTICS_MISMATCH"
        )
    if evidence != EVIDENCE_CLASSIFICATION:
        raise P01HaircutReserveDepletionTermContractError("P01_EVIDENCE_CLASSIFICATION_MISMATCH")
    if contradiction != CONTRADICTION_NONE:
        raise P01HaircutReserveDepletionTermContractError("P01_CONTRADICTION_STATUS_MISMATCH")
    if effect != P01_TERM_CONTRACT_AUTHORITY_EFFECT or effect != AUTHORITY_EFFECT_NONE:
        raise P01HaircutReserveDepletionTermContractError("P01_AUTHORITY_EFFECT_MUST_REMAIN_NONE")
    if numeric == NUMERIC_MISSING:
        raise P01HaircutReserveDepletionTermContractError(
            "P01_MISSING_VALUE_ZERO_COERCION_FORBIDDEN"
        )
    if numeric == NUMERIC_MALFORMED:
        raise P01HaircutReserveDepletionTermContractError(
            "P01_MALFORMED_VALUE_ZERO_COERCION_FORBIDDEN"
        )
    if numeric == NUMERIC_PRESENT_ZERO:
        raise P01HaircutReserveDepletionTermContractError(
            "P01_ZERO_WITHOUT_EXPLICIT_POLICY_FORBIDDEN"
        )
    if numeric != NUMERIC_STATE:
        raise P01HaircutReserveDepletionTermContractError("P01_NUMERIC_STATE_MISMATCH")
    pins = _policy_pins()
    if pins["P01_HAIRCUTS_RESERVE_DEPLETION"] != P01_HAIRCUTS_RESERVE_DEPLETION:
        raise P01HaircutReserveDepletionTermContractError("P01_CANONICAL_PIN_DRIFT")
    if pins["P01_MAY_INCREASE_EQUITY"] is True:
        raise P01HaircutReserveDepletionTermContractError("P01_MAY_INCREASE_EQUITY_FORBIDDEN")
    if pins["P01_ZERO_ONLY_BY_EXPLICIT_POLICY"] is not True:
        raise P01HaircutReserveDepletionTermContractError(
            "P01_ZERO_ONLY_BY_EXPLICIT_POLICY_REQUIRED"
        )
    if pins["USD_EQUALS_USDC"] is True:
        raise P01HaircutReserveDepletionTermContractError("P01_USD_EQUALS_USDC_PIN")
    if pins["U06_FEES"] != "ACCRUED_ONCE_FUTURE_NOT_IN_U06":
        raise P01HaircutReserveDepletionTermContractError("P01_U06_DISTINCTNESS_PIN_DRIFT")
    if "U04_PENDING_ORDER_RESERVATION_INCLUSION_UNRESOLVED" not in UNRESOLVED_ALGEBRA_TERMS:
        raise P01HaircutReserveDepletionTermContractError("P01_U04_MUST_REMAIN_UNRESOLVED")
    if "U05_LIABILITY_INCLUSION_OR_VALUE_UNRESOLVED" not in UNRESOLVED_ALGEBRA_TERMS:
        raise P01HaircutReserveDepletionTermContractError("P01_U05_MUST_REMAIN_UNRESOLVED")
    if "U06_FEE_INCLUSION_UNRESOLVED" not in UNRESOLVED_ALGEBRA_TERMS:
        raise P01HaircutReserveDepletionTermContractError("P01_U06_MUST_REMAIN_UNRESOLVED")
    if EARLIEST_UNRESOLVED_ALGEBRA_TERM != "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED":
        raise P01HaircutReserveDepletionTermContractError("P01_EARLIEST_ALGEBRA_TERM_DRIFT")
    _reject_fallback_chain(field="p01_term_contract_id", raw=contract_id)
    _reject_forbidden_authority_token(field="p01_term_contract_id", raw=contract_id)
    _reject_forbidden_authority_token(field="term_id", raw=term_id)
    _reject_forbidden_authority_token(field="semantic_class", raw=semantic_class)
    algebra = build_reconstruction_algebra_contract_v1(
        algebra_contract_id="P01_TERM_CONTRACT_ALGEBRA_ALIGNMENT"
    )
    p01_term = next(term for term in algebra.terms if term.term_id == TERM_ID)
    if p01_term.algebraic_role != ROLE_REDUCTION_ONLY_UNSPECIFIED:
        raise P01HaircutReserveDepletionTermContractError("P01_ALGEBRA_ROLE_ALIGNMENT_MISMATCH")
    if p01_term.sign_semantics != SIGN_REDUCTION_ONLY:
        raise P01HaircutReserveDepletionTermContractError("P01_ALGEBRA_SIGN_ALIGNMENT_MISMATCH")
    if p01_term.inclusion_state != INCLUSION_UNRESOLVED:
        raise P01HaircutReserveDepletionTermContractError(
            "P01_ALGEBRA_INCLUSION_ALIGNMENT_MISMATCH"
        )
    if p01_term.embedded_term_state != EMBEDDED_UNRESOLVED:
        raise P01HaircutReserveDepletionTermContractError("P01_ALGEBRA_EMBEDDED_ALIGNMENT_MISMATCH")
    if p01_term.currency_unit_domain != CURRENCY_DOMAIN_UNSPECIFIED:
        raise P01HaircutReserveDepletionTermContractError("P01_ALGEBRA_UNIT_ALIGNMENT_MISMATCH")
    if p01_term.term_set_status != TERM_SET_UNSPECIFIED:
        raise P01HaircutReserveDepletionTermContractError("P01_ALGEBRA_TERM_SET_ALIGNMENT_MISMATCH")
    if algebra.algebra_completeness_status != "INCOMPLETE":
        raise P01HaircutReserveDepletionTermContractError("P01_ALGEBRA_COMPLETENESS_ALIGNMENT")
    u04 = next(term for term in algebra.terms if term.term_id == TERM_PENDING_ORDER_RESERVATION)
    u05 = next(term for term in algebra.terms if term.term_id == TERM_LIABILITY)
    u06 = next(term for term in algebra.terms if term.term_id == TERM_FEE)
    if u04.inclusion_state != INCLUSION_UNRESOLVED:
        raise P01HaircutReserveDepletionTermContractError("P01_U04_INCLUSION_MUTATION_FORBIDDEN")
    if u05.inclusion_state != INCLUSION_UNRESOLVED:
        raise P01HaircutReserveDepletionTermContractError("P01_U05_INCLUSION_MUTATION_FORBIDDEN")
    if u06.inclusion_state != INCLUSION_UNRESOLVED:
        raise P01HaircutReserveDepletionTermContractError("P01_U06_INCLUSION_MUTATION_FORBIDDEN")
    canonical = contract.to_canonical_dict()
    expected_digest = compute_p01_term_provenance_digest_v1(canonical)
    if not _SHA256_HEX.fullmatch(digest):
        raise P01HaircutReserveDepletionTermContractError("P01_PROVENANCE_DIGEST_NOT_SHA256")
    if digest != expected_digest:
        raise P01HaircutReserveDepletionTermContractError("P01_PROVENANCE_DIGEST_MISMATCH")
    _ = (pins["U04_PENDING_ORDER_RESERVATIONS"], pins["U05_LIABILITIES_BORROWINGS"])


def build_p01_haircut_reserve_depletion_term_contract_v1(
    **fields: Any,
) -> P01HaircutReserveDepletionTermContractV1:
    """Construct the typed P01 term contract. Does not reconstruct equity."""

    payload = dict(fields)
    if "p01_term_contract_version" not in payload:
        payload["p01_term_contract_version"] = P01_TERM_CONTRACT_VERSION
    if "algebra_contract_schema_class" not in payload:
        payload["algebra_contract_schema_class"] = ALGEBRA_SCHEMA_CLASS
    if "target_semantic_dimension_id" not in payload:
        payload["target_semantic_dimension_id"] = DIMENSION_ID
    if "policy_id" not in payload:
        payload["policy_id"] = POLICY_ID
    if "term_id" not in payload:
        payload["term_id"] = TERM_ID
    if "semantic_class" not in payload:
        payload["semantic_class"] = SEMANTIC_CLASS
    if "algebraic_role" not in payload:
        payload["algebraic_role"] = ALGEBRAIC_ROLE
    if "economic_meaning" not in payload:
        payload["economic_meaning"] = ECONOMIC_MEANING
    if "value_unit_class" not in payload:
        payload["value_unit_class"] = VALUE_UNIT_CLASS
    if "currency_valuation_domain" not in payload:
        payload["currency_valuation_domain"] = CURRENCY_VALUATION_DOMAIN
    if "applicability_state" not in payload:
        payload["applicability_state"] = APPLICABILITY_STATE
    if "provenance_requirements" not in payload:
        payload["provenance_requirements"] = PROVENANCE_REQUIREMENTS
    if "origin_class" not in payload:
        payload["origin_class"] = ORIGIN_CLASS
    if "inclusion_state" not in payload:
        payload["inclusion_state"] = INCLUSION_STATE
    if "embedded_state" not in payload:
        payload["embedded_state"] = EMBEDDED_STATE
    if "overlap_state" not in payload:
        payload["overlap_state"] = OVERLAP_STATE
    if "double_counting_guard" not in payload:
        payload["double_counting_guard"] = DOUBLE_COUNTING_GUARD
    if "sign_constraints" not in payload:
        payload["sign_constraints"] = SIGN_CONSTRAINTS
    if "negative_allowed" not in payload:
        payload["negative_allowed"] = NEGATIVE_ALLOWED
    if "zero_validity_semantics" not in payload:
        payload["zero_validity_semantics"] = ZERO_VALIDITY_SEMANTICS
    if "freshness_epoch_requirements" not in payload:
        payload["freshness_epoch_requirements"] = FRESHNESS_EPOCH_REQUIREMENTS
    if "completeness_resolution_state" not in payload:
        payload["completeness_resolution_state"] = COMPLETENESS_RESOLUTION_STATE
    if "term_semantics_resolved_status" not in payload:
        payload["term_semantics_resolved_status"] = TERM_SEMANTICS_RESOLVED_STATUS
    if "unspecified_closed_status" not in payload:
        payload["unspecified_closed_status"] = UNSPECIFIED_CLOSED_STATUS
    if "remaining_unresolved_semantics" not in payload:
        payload["remaining_unresolved_semantics"] = REMAINING_UNRESOLVED_SEMANTICS
    if "evidence_classification" not in payload:
        payload["evidence_classification"] = EVIDENCE_CLASSIFICATION
    if "contradiction_state" not in payload:
        payload["contradiction_state"] = CONTRADICTION_NONE
    if "p01_term_contract_authority_effect" not in payload:
        payload["p01_term_contract_authority_effect"] = AUTHORITY_EFFECT_NONE
    if "numeric_state" not in payload:
        payload["numeric_state"] = NUMERIC_STATE
    missing = [name for name in _P01_VECTOR_FIELDS if name not in payload]
    if missing:
        raise P01HaircutReserveDepletionTermContractError("P01_FIELD_MISSING:" + ",".join(missing))
    attached = attach_p01_term_provenance_digest_v1(payload)
    return P01HaircutReserveDepletionTermContractV1(
        **{name: attached[name] for name in P01_PROVENANCE_REQUIRED_FIELDS}
    )


def reject_p01_independent_subtractive_assumption_v1() -> None:
    """Independent subtractive participation remains unproven for P01."""

    raise P01HaircutReserveDepletionTermContractError("P01_INDEPENDENT_SUBTRACTIVE_UNPROVEN")


def reject_p01_missing_or_malformed_zero_coercion_v1(*, numeric_state: str) -> None:
    """Missing or malformed P01 is not zero."""

    if numeric_state == NUMERIC_MISSING:
        raise P01HaircutReserveDepletionTermContractError(
            "P01_MISSING_VALUE_ZERO_COERCION_FORBIDDEN"
        )
    if numeric_state == NUMERIC_MALFORMED:
        raise P01HaircutReserveDepletionTermContractError(
            "P01_MALFORMED_VALUE_ZERO_COERCION_FORBIDDEN"
        )
    raise P01HaircutReserveDepletionTermContractError("P01_NUMERIC_STATE_MISMATCH")


def prove_p01_present_zero_distinct_from_missing_v1() -> tuple[str, str]:
    """PRESENT_ZERO remains a distinct state from missing. Canonical P01 is not zero."""

    return NUMERIC_PRESENT_ZERO, NUMERIC_MISSING


def prove_p01_does_not_resolve_u04_u05_u06_v1() -> tuple[str, str, str]:
    """Resolving a P01 schema does not resolve U04/U05/U06."""

    return (
        "U04_PENDING_ORDER_RESERVATION_INCLUSION_UNRESOLVED",
        "U05_LIABILITY_INCLUSION_OR_VALUE_UNRESOLVED",
        "U06_FEE_INCLUSION_UNRESOLVED",
    )
