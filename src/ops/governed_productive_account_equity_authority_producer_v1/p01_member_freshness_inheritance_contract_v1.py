"""Typed P01 member freshness inheritance adjudication.

Encodes the forensic result that canonical evidence does not prove a
P01 freshness dimension, member-to-P01 inheritance rule, or U09
freshness authority for P01. Unproven freshness is not freshness
authorization. Schema presence is not a timestamp. This slice does not
copy U09, invent aggregation, or complete reconstruction algebra.

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
    P01_APPLICABILITY_RESOLVED,
    P01_EMBEDDED_STATE_RESOLVED,
    P01_EMBEDDING_STATE_CONTRACT_AUTHORITY_EFFECT,
    P01_EQUITY_BASE_INCLUSION_CONTRACT_AUTHORITY_EFFECT,
    P01_EQUITY_BASE_INCLUSION_RESOLVED,
    P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED,
    P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_AUTHORITY_EFFECT,
    P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_SCHEMA_PRESENT,
    P01_MEMBER_FRESHNESS_INHERITANCE_REQUIRED_FIELDS,
    P01_MEMBER_FRESHNESS_INHERITANCE_RESOLVED,
    P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_AUTHORITY_EFFECT,
    P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_SCHEMA_PRESENT,
    P01_NUMERIC_VALUE_PROVENANCE_RESOLVED,
    P01_OVERLAP_WITH_U04_U05_CONTRACT_AUTHORITY_EFFECT,
    P01_TERM_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_TERM_SEMANTICS_RESOLVED,
    P01_TERM_SET_RESOLVED,
    P01_U04_OVERLAP_RESOLVED,
    P01_U05_OVERLAP_RESOLVED,
    P01_VALUE_UNIT_CLASS_RESOLVED,
    RECONSTRUCTION_ALGEBRA_COMPLETE,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_haircut_reserve_depletion_term_contract_v1 import (
    FRESHNESS_EPOCH_REQUIREMENTS as PARENT_FRESHNESS_EPOCH_REQUIREMENTS,
    SCHEMA_CLASS as P01_TERM_SCHEMA_CLASS,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_numeric_value_provenance_contract_v1 import (
    P01_NUMERIC_VALUE_PROVENANCE_STATUS,
    P01_NUMERIC_VALUE_SOURCE,
    P01_NUMERIC_VALUE_TRANSFORMATION,
    REMAINING_UNRESOLVED_SEMANTICS as PARENT_REMAINING_UNRESOLVED_SEMANTICS,
    SCHEMA_CLASS as P01_NUMERIC_PROVENANCE_SCHEMA_CLASS,
    TIME_SEMANTICS_STATE as PARENT_TIME_SEMANTICS_STATE,
    build_p01_numeric_value_provenance_contract_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.reconstruction_algebra_contract_v1 import (
    CONTRADICTION_NONE,
    DIMENSION_ID,
    TERM_P01_HAIRCUT_RESERVE_DEPLETION,
    U09_FRESHNESS_CLASS,
)

SCHEMA_CLASS = "P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_V1"
CONTRACT_VERSION = "v1"
POLICY_ID = "P01"
TERM_ID = TERM_P01_HAIRCUT_RESERVE_DEPLETION
PARENT_NUMERIC_PROVENANCE_CONTRACT_SCHEMA_CLASS = P01_NUMERIC_PROVENANCE_SCHEMA_CLASS
PARENT_TERM_CONTRACT_SCHEMA_CLASS = P01_TERM_SCHEMA_CLASS
P01_MEMBER_FRESHNESS_INHERITANCE_RESOLVED_STATUS = "false"
P01_MEMBER_FRESHNESS_STATUS = "UNPROVEN"
P01_MEMBER_FRESHNESS_RULE = "UNSPECIFIED"
P01_U09_FRESHNESS_RELATION = "UNSPECIFIED"
P01_FRESHNESS_DIMENSION_STATE = "UNPROVEN"
P01_TIMESTAMP_STATE = "UNSPECIFIED"
P01_LEVEL_FRESHNESS_METADATA_STATE = "UNPROVEN"
MEMBER_LEVEL_FRESHNESS_METADATA_STATE = "UNPROVEN"
INHERITANCE_RULE_STATE = "UNSPECIFIED"
U09_COMPARISON_EVIDENCE_ONLY = "true"
U09_IS_NOT_P01_FRESHNESS_AUTHORITY = "true"
P01_FRESHNESS_DOES_NOT_INHERIT_U09 = "true"
P01_FRESHNESS_NOT_EQUIVALENT_TO_U09 = "true"
UNKNOWN_IS_NOT_FRESHNESS_AUTHORITY = "true"
UNPROVEN_IS_NOT_FRESHNESS_AUTHORITY = "true"
UNSPECIFIED_IS_NOT_FRESHNESS_AUTHORITY = "true"
MISSING_INPUT_FAIL_CLOSED = "true"
MALFORMED_INPUT_FAIL_CLOSED = "true"
OLDEST_MEMBER_WINS_UNPROVEN = "true"
NEWEST_MEMBER_WINS_UNPROVEN = "true"
MIN_FRESHNESS_UNPROVEN = "true"
MAX_FRESHNESS_UNPROVEN = "true"
ALL_MEMBERS_SAME_EPOCH_UNPROVEN = "true"
WEIGHTED_COMPOSITE_UNPROVEN = "true"
SOURCE_SPECIFIC_FRESHNESS_UNPROVEN = "true"
INDEPENDENT_P01_TIMESTAMP_UNPROVEN = "true"
PRODUCER_TIMESTAMP_UNPROVEN = "true"
RECONSTRUCTION_EPOCH_UNPROVEN = "true"
VALUATION_EPOCH_UNPROVEN = "true"
ACCOUNTING_EPOCH_UNPROVEN = "true"
CURRENT_TIME_IS_NOT_P01_FRESHNESS = "true"
MISSING_FRESHNESS_IS_NOT_FRESH = "true"
STALE_P01_IS_NOT_ADMISSIBLE = "true"
UNPROVEN_CANNOT_AUTHORIZE_IGNORE = "true"
UNPROVEN_CANNOT_AUTHORIZE_FALLBACK = "true"
UNPROVEN_CANNOT_AUTHORIZE_STALE_FILTER = "true"
FALLBACK_FRESHNESS_STATE = "FORBIDDEN"
NUMERIC_PROVENANCE_UNSPECIFIED_DOES_NOT_DECIDE_FRESHNESS = "true"
TERM_SET_UNRESOLVED_DOES_NOT_DECIDE_FRESHNESS = "true"
AUTHORITY_EFFECT_NONE = "NONE"
TERM_SEMANTICS_RESOLVED_STATUS = "false"
UNSPECIFIED_CLOSED_STATUS = "false"
REMAINING_UNRESOLVED_SEMANTICS = PARENT_REMAINING_UNRESOLVED_SEMANTICS
REJECTED_FRESHNESS_INFERENCES = (
    "U09_IS_NOT_P01_FRESHNESS_AUTHORITY;"
    "P01_FRESHNESS_DOES_NOT_INHERIT_U09;"
    "P01_FRESHNESS_NOT_EQUIVALENT_TO_U09;"
    "OLDEST_MEMBER_WINS_UNPROVEN;"
    "NEWEST_MEMBER_WINS_UNPROVEN;"
    "MIN_FRESHNESS_UNPROVEN;"
    "MAX_FRESHNESS_UNPROVEN;"
    "ALL_MEMBERS_SAME_EPOCH_UNPROVEN;"
    "WEIGHTED_COMPOSITE_UNPROVEN;"
    "SOURCE_SPECIFIC_FRESHNESS_UNPROVEN;"
    "INDEPENDENT_P01_TIMESTAMP_UNPROVEN;"
    "PRODUCER_TIMESTAMP_UNPROVEN;"
    "RECONSTRUCTION_EPOCH_UNPROVEN;"
    "VALUATION_EPOCH_UNPROVEN;"
    "ACCOUNTING_EPOCH_UNPROVEN;"
    "CURRENT_TIME_IS_NOT_P01_FRESHNESS;"
    "MISSING_FRESHNESS_IS_NOT_FRESH;"
    "STALE_P01_IS_NOT_ADMISSIBLE;"
    "UNPROVEN_CANNOT_AUTHORIZE_IGNORE;"
    "UNPROVEN_CANNOT_AUTHORIZE_FALLBACK;"
    "UNPROVEN_CANNOT_COPY_U09_TTL;"
    "SHARED_EPOCH_IS_NOT_P01_MEMBER_FRESHNESS;"
    "DISTINCTNESS_IS_NOT_INHERITANCE;"
    "TERM_SET_UNRESOLVED_CANNOT_IDENTIFY_MEMBERS;"
    "UNSPECIFIED_NUMERIC_PROVENANCE_CANNOT_SUPPLY_TIMESTAMP"
)
EVIDENCE_CLASSIFICATION = (
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_AH_P01_MEMBER_FRESHNESS_INHERITANCE_UNPROVEN;"
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_AH_P01_MEMBER_FRESHNESS_DISTINCT_FROM_U09;"
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_T_U09_FRESH_GET_PER_PRETRADE_DECISION;"
    "CANONICAL_AUTHORITY=MASTER_RUNBOOK_11_2_1_AB_P01_FRESHNESS_EPOCH_REQUIREMENTS_UNPROVEN;"
    "FORENSIC_EVIDENCE=NO_P01_TIMESTAMP_NO_MEMBER_SET_NO_INHERITANCE_RULE;"
    "FORENSIC_EVIDENCE=P01_TERM_SET_UNSPECIFIED_CANNOT_IDENTIFY_MEMBERS;"
    "FORENSIC_EVIDENCE=P01_NUMERIC_VALUE_PROVENANCE_UNSPECIFIED_CANNOT_SUPPLY_SOURCE_TIME;"
    "HISTORICAL_STATE=U09_DECIDED_COMPARISON_EVIDENCE_ONLY;"
    "STRUCTURAL_REUSE_ONLY=P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_V1;"
    "NAVIGATION=MAP_OF_TRUTH_NON_SSOT;"
    "INTERPRETATION=NONE;"
    "HYPOTHESIS=NONE;"
    "REJECTED=U09_INHERITANCE_U09_EQUIVALENCE_OLDEST_NEWEST_MIN_MAX_NOW_IGNORE_FALLBACK;"
    "UNPROVEN=P01_MEMBER_FRESHNESS_INHERITANCE;"
    "UNSPECIFIED=P01_MEMBER_FRESHNESS_RULE_AND_U09_RELATION;"
    "UNRESOLVED=P01_TERM_SET_AND_NUMERIC_PROVENANCE_BLOCK_MEMBER_COMPOSITION;"
    "CONTRADICTORY=NONE"
)
CANDIDATE_FRESHNESS_RULES_CLASSIFICATION = (
    "CANDIDATE=OLDEST_MEMBER_WINS|CLASS=REJECTED|REASON=UNPROVEN;"
    "CANDIDATE=NEWEST_MEMBER_WINS|CLASS=REJECTED|REASON=UNPROVEN;"
    "CANDIDATE=MINIMUM_FRESHNESS|CLASS=REJECTED|REASON=UNPROVEN;"
    "CANDIDATE=MAXIMUM_FRESHNESS|CLASS=REJECTED|REASON=UNPROVEN;"
    "CANDIDATE=ALL_MEMBERS_SAME_EPOCH_REQUIRED|CLASS=REJECTED|REASON=UNPROVEN;"
    "CANDIDATE=WEIGHTED_COMPOSITE|CLASS=REJECTED|REASON=UNPROVEN;"
    "CANDIDATE=SOURCE_SPECIFIC|CLASS=REJECTED|REASON=UNPROVEN;"
    "CANDIDATE=INDEPENDENT_P01_TIMESTAMP|CLASS=REJECTED|REASON=UNPROVEN;"
    "CANDIDATE=PRODUCER_TIMESTAMP|CLASS=REJECTED|REASON=NO_PRODUCTIVE_PRODUCER;"
    "CANDIDATE=RECONSTRUCTION_EPOCH|CLASS=REJECTED|REASON=RECONSTRUCTION_UNPROVEN;"
    "CANDIDATE=VALUATION_EPOCH|CLASS=REJECTED|REASON=UNPROVEN;"
    "CANDIDATE=ACCOUNTING_EPOCH|CLASS=REJECTED|REASON=UNPROVEN;"
    "CANDIDATE=U09_FRESH_GET_PER_PRETRADE_DECISION|CLASS=CANONICAL_AUTHORITY|"
    "REASON=U09_SLOT_COMPARISON_EVIDENCE_NOT_P01_AUTHORITY;"
    "CANDIDATE=CURRENT_TIME|CLASS=REJECTED|REASON=NOT_P01_FRESHNESS;"
    "NO_WINNER_RATIFIED=true"
)
_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")
_INFERRED_RULE_TOKENS: tuple[str, ...] = (
    "oldestmember",
    "newestmember",
    "minfreshness",
    "maxfreshness",
    "minimumfreshness",
    "maximumfreshness",
    "allmemberssameepoch",
    "weightedcomposite",
    "sourcespecific",
    "independentp01timestamp",
    "producertimestamp",
    "reconstructionepoch",
    "valuationepoch",
    "accountingepoch",
    "currenttime",
    "wallclock",
    "utcnow",
    "now",
    "inheritsu09",
    "u09freshness",
    "equivalenttou09",
    "copyu09",
    "copyttl",
    "ignorefreshness",
    "staleadmissible",
    "missingisfresh",
    "fallback",
    "resolved",
)
_VECTOR_FIELDS: tuple[str, ...] = tuple(
    name for name in P01_MEMBER_FRESHNESS_INHERITANCE_REQUIRED_FIELDS if name != "provenance_digest"
)


class P01MemberFreshnessInheritanceContractError(ValueError):
    """Fail-closed P01 member freshness inheritance contract violation."""


def _fold(value: str) -> str:
    return str(value or "").strip().lower().replace("_", "").replace("-", "").replace(".", "")


def _require_non_empty_str(*, field: str, raw: Any) -> str:
    if raw is None:
        raise P01MemberFreshnessInheritanceContractError(f"P01_FIELD_MISSING:{field}")
    if isinstance(raw, bool) or not isinstance(raw, str):
        raise P01MemberFreshnessInheritanceContractError(f"P01_FIELD_NOT_STRING:{field}")
    text = raw.strip()
    if text == "" or text != raw:
        raise P01MemberFreshnessInheritanceContractError(f"P01_FIELD_MISSING:{field}")
    return text


def _sha256_hex(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _canonical_json(payload: Mapping[str, str]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_p01_member_freshness_inheritance_digest_v1(canonical: Mapping[str, str]) -> str:
    payload = {
        key: canonical[key]
        for key in P01_MEMBER_FRESHNESS_INHERITANCE_REQUIRED_FIELDS
        if key != "provenance_digest"
    }
    return _sha256_hex(_canonical_json(payload))


def attach_p01_member_freshness_inheritance_digest_v1(
    fields: Mapping[str, Any],
) -> dict[str, Any]:
    canonical: dict[str, str] = {}
    for canonical_name in P01_MEMBER_FRESHNESS_INHERITANCE_REQUIRED_FIELDS:
        if canonical_name == "provenance_digest":
            continue
        if canonical_name not in fields:
            raise P01MemberFreshnessInheritanceContractError(f"P01_FIELD_MISSING:{canonical_name}")
        raw = fields[canonical_name]
        canonical[canonical_name] = "" if raw is None else str(raw)
    attached = dict(fields)
    attached["provenance_digest"] = compute_p01_member_freshness_inheritance_digest_v1(canonical)
    return attached


def _reject_coerced_rule(*, field: str, raw: str) -> None:
    folded = _fold(raw)
    _ = field
    if folded in _INFERRED_RULE_TOKENS:
        raise P01MemberFreshnessInheritanceContractError("P01_FRESHNESS_RULE_INFERRED_FORBIDDEN")
    if any(len(token) > 3 and token in folded for token in _INFERRED_RULE_TOKENS):
        raise P01MemberFreshnessInheritanceContractError("P01_FRESHNESS_RULE_INFERRED_FORBIDDEN")
    if folded == "u09":
        raise P01MemberFreshnessInheritanceContractError("P01_FRESHNESS_RULE_INFERRED_FORBIDDEN")


@dataclass(frozen=True)
class P01MemberFreshnessInheritanceContractV1:
    """Typed immutable P01 freshness adjudication. Not a timestamp instance."""

    p01_member_freshness_inheritance_contract_id: str
    p01_member_freshness_inheritance_contract_version: str
    parent_p01_numeric_value_provenance_contract_schema_class: str
    parent_p01_term_contract_schema_class: str
    target_semantic_dimension_id: str
    policy_id: str
    term_id: str
    p01_member_freshness_inheritance_resolved_status: str
    p01_member_freshness_status: str
    p01_member_freshness_rule: str
    p01_u09_freshness_relation: str
    p01_freshness_dimension_state: str
    p01_timestamp_state: str
    p01_level_freshness_metadata_state: str
    member_level_freshness_metadata_state: str
    inheritance_rule_state: str
    u09_comparison_evidence_only: str
    u09_is_not_p01_freshness_authority: str
    p01_freshness_does_not_inherit_u09: str
    p01_freshness_not_equivalent_to_u09: str
    unknown_is_not_freshness_authority: str
    unproven_is_not_freshness_authority: str
    unspecified_is_not_freshness_authority: str
    missing_input_fail_closed: str
    malformed_input_fail_closed: str
    oldest_member_wins_unproven: str
    newest_member_wins_unproven: str
    min_freshness_unproven: str
    max_freshness_unproven: str
    all_members_same_epoch_unproven: str
    weighted_composite_unproven: str
    source_specific_freshness_unproven: str
    independent_p01_timestamp_unproven: str
    producer_timestamp_unproven: str
    reconstruction_epoch_unproven: str
    valuation_epoch_unproven: str
    accounting_epoch_unproven: str
    current_time_is_not_p01_freshness: str
    missing_freshness_is_not_fresh: str
    stale_p01_is_not_admissible: str
    unproven_cannot_authorize_ignore: str
    unproven_cannot_authorize_fallback: str
    unproven_cannot_authorize_stale_filter: str
    fallback_freshness_state: str
    numeric_provenance_unspecified_does_not_decide_freshness: str
    term_set_unresolved_does_not_decide_freshness: str
    parent_time_semantics_state: str
    parent_freshness_epoch_requirements: str
    u09_freshness_class_comparison: str
    rejected_freshness_inferences: str
    remaining_unresolved_semantics: str
    evidence_classification: str
    candidate_freshness_rules_classification: str
    contradiction_state: str
    term_semantics_resolved_status: str
    unspecified_closed_status: str
    p01_member_freshness_inheritance_contract_authority_effect: str
    provenance_digest: str

    def __post_init__(self) -> None:
        _validate_p01_member_freshness_inheritance_contract_v1(self)

    def to_canonical_dict(self) -> dict[str, str]:
        values = {
            "p01_member_freshness_inheritance_contract_id": (
                self.p01_member_freshness_inheritance_contract_id
            ),
            "p01_member_freshness_inheritance_contract_version": (
                self.p01_member_freshness_inheritance_contract_version
            ),
            "parent_p01_numeric_value_provenance_contract_schema_class": (
                self.parent_p01_numeric_value_provenance_contract_schema_class
            ),
            "parent_p01_term_contract_schema_class": self.parent_p01_term_contract_schema_class,
            "target_semantic_dimension_id": self.target_semantic_dimension_id,
            "policy_id": self.policy_id,
            "term_id": self.term_id,
            "p01_member_freshness_inheritance_resolved_status": (
                self.p01_member_freshness_inheritance_resolved_status
            ),
            "p01_member_freshness_status": self.p01_member_freshness_status,
            "p01_member_freshness_rule": self.p01_member_freshness_rule,
            "p01_u09_freshness_relation": self.p01_u09_freshness_relation,
            "p01_freshness_dimension_state": self.p01_freshness_dimension_state,
            "p01_timestamp_state": self.p01_timestamp_state,
            "p01_level_freshness_metadata_state": self.p01_level_freshness_metadata_state,
            "member_level_freshness_metadata_state": self.member_level_freshness_metadata_state,
            "inheritance_rule_state": self.inheritance_rule_state,
            "u09_comparison_evidence_only": self.u09_comparison_evidence_only,
            "u09_is_not_p01_freshness_authority": self.u09_is_not_p01_freshness_authority,
            "p01_freshness_does_not_inherit_u09": self.p01_freshness_does_not_inherit_u09,
            "p01_freshness_not_equivalent_to_u09": self.p01_freshness_not_equivalent_to_u09,
            "unknown_is_not_freshness_authority": self.unknown_is_not_freshness_authority,
            "unproven_is_not_freshness_authority": self.unproven_is_not_freshness_authority,
            "unspecified_is_not_freshness_authority": self.unspecified_is_not_freshness_authority,
            "missing_input_fail_closed": self.missing_input_fail_closed,
            "malformed_input_fail_closed": self.malformed_input_fail_closed,
            "oldest_member_wins_unproven": self.oldest_member_wins_unproven,
            "newest_member_wins_unproven": self.newest_member_wins_unproven,
            "min_freshness_unproven": self.min_freshness_unproven,
            "max_freshness_unproven": self.max_freshness_unproven,
            "all_members_same_epoch_unproven": self.all_members_same_epoch_unproven,
            "weighted_composite_unproven": self.weighted_composite_unproven,
            "source_specific_freshness_unproven": self.source_specific_freshness_unproven,
            "independent_p01_timestamp_unproven": self.independent_p01_timestamp_unproven,
            "producer_timestamp_unproven": self.producer_timestamp_unproven,
            "reconstruction_epoch_unproven": self.reconstruction_epoch_unproven,
            "valuation_epoch_unproven": self.valuation_epoch_unproven,
            "accounting_epoch_unproven": self.accounting_epoch_unproven,
            "current_time_is_not_p01_freshness": self.current_time_is_not_p01_freshness,
            "missing_freshness_is_not_fresh": self.missing_freshness_is_not_fresh,
            "stale_p01_is_not_admissible": self.stale_p01_is_not_admissible,
            "unproven_cannot_authorize_ignore": self.unproven_cannot_authorize_ignore,
            "unproven_cannot_authorize_fallback": self.unproven_cannot_authorize_fallback,
            "unproven_cannot_authorize_stale_filter": self.unproven_cannot_authorize_stale_filter,
            "fallback_freshness_state": self.fallback_freshness_state,
            "numeric_provenance_unspecified_does_not_decide_freshness": (
                self.numeric_provenance_unspecified_does_not_decide_freshness
            ),
            "term_set_unresolved_does_not_decide_freshness": (
                self.term_set_unresolved_does_not_decide_freshness
            ),
            "parent_time_semantics_state": self.parent_time_semantics_state,
            "parent_freshness_epoch_requirements": self.parent_freshness_epoch_requirements,
            "u09_freshness_class_comparison": self.u09_freshness_class_comparison,
            "rejected_freshness_inferences": self.rejected_freshness_inferences,
            "remaining_unresolved_semantics": self.remaining_unresolved_semantics,
            "evidence_classification": self.evidence_classification,
            "candidate_freshness_rules_classification": (
                self.candidate_freshness_rules_classification
            ),
            "contradiction_state": self.contradiction_state,
            "term_semantics_resolved_status": self.term_semantics_resolved_status,
            "unspecified_closed_status": self.unspecified_closed_status,
            "p01_member_freshness_inheritance_contract_authority_effect": (
                self.p01_member_freshness_inheritance_contract_authority_effect
            ),
            "provenance_digest": self.provenance_digest,
        }
        return {key: values[key] for key in P01_MEMBER_FRESHNESS_INHERITANCE_REQUIRED_FIELDS}


def _require_true_pin(*, field: str, raw: str, expected: str, error: str) -> None:
    if raw.lower() != "true" or raw != expected:
        raise P01MemberFreshnessInheritanceContractError(error)
    _ = field


def _validate_p01_member_freshness_inheritance_contract_v1(
    contract: P01MemberFreshnessInheritanceContractV1,
) -> None:
    if P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_SCHEMA_PRESENT is not True:
        raise P01MemberFreshnessInheritanceContractError(
            "P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_SCHEMA_PRESENT_REQUIRED"
        )
    if P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_RUNTIME_INSTANCE_PRESENT is True:
        raise P01MemberFreshnessInheritanceContractError("P01_RUNTIME_INSTANCE_FORBIDDEN")
    if P01_MEMBER_FRESHNESS_INHERITANCE_RESOLVED is True:
        raise P01MemberFreshnessInheritanceContractError(
            "P01_MEMBER_FRESHNESS_INHERITANCE_RESOLVED_PIN_FORBIDDEN"
        )
    if P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_SCHEMA_PRESENT is not True:
        raise P01MemberFreshnessInheritanceContractError(
            "P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_SCHEMA_PRESENT_REQUIRED"
        )
    if P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_RUNTIME_INSTANCE_PRESENT is True:
        raise P01MemberFreshnessInheritanceContractError(
            "P01_PARENT_NUMERIC_PROVENANCE_RUNTIME_INSTANCE_FORBIDDEN"
        )
    if P01_NUMERIC_VALUE_PROVENANCE_RESOLVED is True:
        raise P01MemberFreshnessInheritanceContractError(
            "P01_NUMERIC_VALUE_PROVENANCE_RESOLVED_PIN_FORBIDDEN"
        )
    if P01_NUMERIC_VALUE_PROVENANCE_STATUS != "UNSPECIFIED":
        raise P01MemberFreshnessInheritanceContractError(
            "P01_NUMERIC_VALUE_PROVENANCE_STATUS_MISMATCH"
        )
    if P01_NUMERIC_VALUE_SOURCE != "UNSPECIFIED":
        raise P01MemberFreshnessInheritanceContractError("P01_NUMERIC_VALUE_SOURCE_MISMATCH")
    if P01_NUMERIC_VALUE_TRANSFORMATION != "UNSPECIFIED":
        raise P01MemberFreshnessInheritanceContractError(
            "P01_NUMERIC_VALUE_TRANSFORMATION_MISMATCH"
        )
    if P01_TERM_CONTRACT_RUNTIME_INSTANCE_PRESENT is True:
        raise P01MemberFreshnessInheritanceContractError(
            "P01_PARENT_TERM_RUNTIME_INSTANCE_FORBIDDEN"
        )
    if P01_TERM_SET_RESOLVED is True:
        raise P01MemberFreshnessInheritanceContractError("P01_TERM_SET_RESOLVED_PIN_FORBIDDEN")
    if P01_VALUE_UNIT_CLASS_RESOLVED is True:
        raise P01MemberFreshnessInheritanceContractError(
            "P01_VALUE_UNIT_CLASS_RESOLVED_PIN_FORBIDDEN"
        )
    if P01_APPLICABILITY_RESOLVED is True:
        raise P01MemberFreshnessInheritanceContractError("P01_APPLICABILITY_RESOLVED_PIN_FORBIDDEN")
    if P01_EQUITY_BASE_INCLUSION_RESOLVED is True:
        raise P01MemberFreshnessInheritanceContractError(
            "P01_EQUITY_BASE_INCLUSION_RESOLVED_PIN_FORBIDDEN"
        )
    if P01_EMBEDDED_STATE_RESOLVED is True:
        raise P01MemberFreshnessInheritanceContractError(
            "P01_EMBEDDED_STATE_RESOLVED_PIN_FORBIDDEN"
        )
    if P01_U04_OVERLAP_RESOLVED is True:
        raise P01MemberFreshnessInheritanceContractError("P01_U04_OVERLAP_RESOLVED_PIN_FORBIDDEN")
    if P01_U05_OVERLAP_RESOLVED is True:
        raise P01MemberFreshnessInheritanceContractError("P01_U05_OVERLAP_RESOLVED_PIN_FORBIDDEN")
    if P01_TERM_SEMANTICS_RESOLVED is True:
        raise P01MemberFreshnessInheritanceContractError(
            "P01_TERM_SEMANTICS_RESOLVED_PIN_FORBIDDEN"
        )
    if P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED is True:
        raise P01MemberFreshnessInheritanceContractError(
            "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED_PIN_FORBIDDEN"
        )
    if RECONSTRUCTION_ALGEBRA_COMPLETE is True:
        raise P01MemberFreshnessInheritanceContractError(
            "P01_RECONSTRUCTION_ALGEBRA_COMPLETE_PIN_FORBIDDEN"
        )
    if P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_AUTHORITY_EFFECT != AUTHORITY_EFFECT_NONE:
        raise P01MemberFreshnessInheritanceContractError(
            "P01_PARENT_AUTHORITY_EFFECT_MUST_REMAIN_NONE"
        )
    if P01_OVERLAP_WITH_U04_U05_CONTRACT_AUTHORITY_EFFECT != AUTHORITY_EFFECT_NONE:
        raise P01MemberFreshnessInheritanceContractError(
            "P01_PARENT_AUTHORITY_EFFECT_MUST_REMAIN_NONE"
        )
    if P01_EMBEDDING_STATE_CONTRACT_AUTHORITY_EFFECT != AUTHORITY_EFFECT_NONE:
        raise P01MemberFreshnessInheritanceContractError(
            "P01_PARENT_AUTHORITY_EFFECT_MUST_REMAIN_NONE"
        )
    if P01_EQUITY_BASE_INCLUSION_CONTRACT_AUTHORITY_EFFECT != AUTHORITY_EFFECT_NONE:
        raise P01MemberFreshnessInheritanceContractError(
            "P01_PARENT_AUTHORITY_EFFECT_MUST_REMAIN_NONE"
        )
    if P01_APPLICABILITY_CONTRACT_AUTHORITY_EFFECT != AUTHORITY_EFFECT_NONE:
        raise P01MemberFreshnessInheritanceContractError(
            "P01_PARENT_AUTHORITY_EFFECT_MUST_REMAIN_NONE"
        )

    for field in _VECTOR_FIELDS:
        raw = getattr(contract, field)
        _require_non_empty_str(field=field, raw=raw)
    digest = _require_non_empty_str(field="provenance_digest", raw=contract.provenance_digest)
    if _SHA256_HEX.fullmatch(digest) is None:
        raise P01MemberFreshnessInheritanceContractError("P01_PROVENANCE_DIGEST_MALFORMED")
    expected_digest = compute_p01_member_freshness_inheritance_digest_v1(
        {key: getattr(contract, key) for key in _VECTOR_FIELDS}
    )
    if digest != expected_digest:
        raise P01MemberFreshnessInheritanceContractError("P01_PROVENANCE_DIGEST_MISMATCH")

    resolved = contract.p01_member_freshness_inheritance_resolved_status
    if resolved.lower() == "true" or resolved != P01_MEMBER_FRESHNESS_INHERITANCE_RESOLVED_STATUS:
        raise P01MemberFreshnessInheritanceContractError(
            "P01_MEMBER_FRESHNESS_INHERITANCE_RESOLVED_FORBIDDEN"
        )
    if contract.p01_member_freshness_status != P01_MEMBER_FRESHNESS_STATUS:
        raise P01MemberFreshnessInheritanceContractError("P01_MEMBER_FRESHNESS_STATUS_MISMATCH")
    if contract.p01_member_freshness_rule != P01_MEMBER_FRESHNESS_RULE:
        raise P01MemberFreshnessInheritanceContractError("P01_MEMBER_FRESHNESS_RULE_MISMATCH")
    if contract.p01_u09_freshness_relation != P01_U09_FRESHNESS_RELATION:
        raise P01MemberFreshnessInheritanceContractError("P01_U09_FRESHNESS_RELATION_MISMATCH")
    if contract.p01_u09_freshness_relation in {"INHERITS", "EQUIVALENT"}:
        raise P01MemberFreshnessInheritanceContractError("P01_U09_FRESHNESS_RELATION_FORBIDDEN")
    _reject_coerced_rule(
        field="p01_member_freshness_rule",
        raw=contract.p01_member_freshness_rule,
    )
    _reject_coerced_rule(
        field="p01_u09_freshness_relation",
        raw=contract.p01_u09_freshness_relation,
    )
    if contract.parent_time_semantics_state != PARENT_TIME_SEMANTICS_STATE:
        raise P01MemberFreshnessInheritanceContractError("P01_TIME_SEMANTICS_STATE_MISMATCH")
    if contract.parent_time_semantics_state != "P01_MEMBER_FRESHNESS_INHERITANCE_UNPROVEN":
        raise P01MemberFreshnessInheritanceContractError("P01_TIME_SEMANTICS_STATE_MISMATCH")
    if contract.parent_freshness_epoch_requirements != PARENT_FRESHNESS_EPOCH_REQUIREMENTS:
        raise P01MemberFreshnessInheritanceContractError(
            "P01_FRESHNESS_EPOCH_REQUIREMENTS_MISMATCH"
        )
    if "P01_MEMBER_FRESHNESS_INHERITANCE_UNPROVEN" not in PARENT_FRESHNESS_EPOCH_REQUIREMENTS:
        raise P01MemberFreshnessInheritanceContractError(
            "P01_MEMBER_FRESHNESS_INHERITANCE_UNPROVEN_PIN_MISSING"
        )
    if contract.u09_freshness_class_comparison != U09_FRESHNESS_CLASS:
        raise P01MemberFreshnessInheritanceContractError("P01_U09_COMPARISON_CLASS_MISMATCH")
    if contract.remaining_unresolved_semantics != REMAINING_UNRESOLVED_SEMANTICS:
        raise P01MemberFreshnessInheritanceContractError(
            "P01_REMAINING_UNRESOLVED_SEMANTICS_MISMATCH"
        )
    if "P01_NUMERIC_VALUE_PROVENANCE_UNSPECIFIED" not in contract.remaining_unresolved_semantics:
        raise P01MemberFreshnessInheritanceContractError(
            "P01_NUMERIC_VALUE_PROVENANCE_MUST_REMAIN_UNSPECIFIED"
        )
    if contract.p01_member_freshness_inheritance_contract_authority_effect != AUTHORITY_EFFECT_NONE:
        raise P01MemberFreshnessInheritanceContractError("P01_AUTHORITY_EFFECT_MUST_REMAIN_NONE")
    if contract.fallback_freshness_state != FALLBACK_FRESHNESS_STATE:
        raise P01MemberFreshnessInheritanceContractError(
            "P01_FALLBACK_FRESHNESS_MUST_REMAIN_FORBIDDEN"
        )
    for field, expected, error in (
        (
            "u09_comparison_evidence_only",
            U09_COMPARISON_EVIDENCE_ONLY,
            "P01_U09_COMPARISON_ONLY_REQUIRED",
        ),
        (
            "u09_is_not_p01_freshness_authority",
            U09_IS_NOT_P01_FRESHNESS_AUTHORITY,
            "P01_U09_IS_NOT_P01_FRESHNESS_AUTHORITY_REQUIRED",
        ),
        (
            "p01_freshness_does_not_inherit_u09",
            P01_FRESHNESS_DOES_NOT_INHERIT_U09,
            "P01_FRESHNESS_DOES_NOT_INHERIT_U09_REQUIRED",
        ),
        (
            "p01_freshness_not_equivalent_to_u09",
            P01_FRESHNESS_NOT_EQUIVALENT_TO_U09,
            "P01_FRESHNESS_NOT_EQUIVALENT_TO_U09_REQUIRED",
        ),
        (
            "unknown_is_not_freshness_authority",
            UNKNOWN_IS_NOT_FRESHNESS_AUTHORITY,
            "P01_UNKNOWN_IS_NOT_FRESHNESS_AUTHORITY_REQUIRED",
        ),
        (
            "unproven_is_not_freshness_authority",
            UNPROVEN_IS_NOT_FRESHNESS_AUTHORITY,
            "P01_UNPROVEN_IS_NOT_FRESHNESS_AUTHORITY_REQUIRED",
        ),
        (
            "unspecified_is_not_freshness_authority",
            UNSPECIFIED_IS_NOT_FRESHNESS_AUTHORITY,
            "P01_UNSPECIFIED_IS_NOT_FRESHNESS_AUTHORITY_REQUIRED",
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
        (
            "oldest_member_wins_unproven",
            OLDEST_MEMBER_WINS_UNPROVEN,
            "P01_OLDEST_MEMBER_UNPROVEN_REQUIRED",
        ),
        (
            "newest_member_wins_unproven",
            NEWEST_MEMBER_WINS_UNPROVEN,
            "P01_NEWEST_MEMBER_UNPROVEN_REQUIRED",
        ),
        ("min_freshness_unproven", MIN_FRESHNESS_UNPROVEN, "P01_MIN_FRESHNESS_UNPROVEN_REQUIRED"),
        ("max_freshness_unproven", MAX_FRESHNESS_UNPROVEN, "P01_MAX_FRESHNESS_UNPROVEN_REQUIRED"),
        (
            "current_time_is_not_p01_freshness",
            CURRENT_TIME_IS_NOT_P01_FRESHNESS,
            "P01_CURRENT_TIME_IS_NOT_FRESHNESS_REQUIRED",
        ),
        (
            "missing_freshness_is_not_fresh",
            MISSING_FRESHNESS_IS_NOT_FRESH,
            "P01_MISSING_FRESHNESS_IS_NOT_FRESH_REQUIRED",
        ),
        (
            "stale_p01_is_not_admissible",
            STALE_P01_IS_NOT_ADMISSIBLE,
            "P01_STALE_NOT_ADMISSIBLE_REQUIRED",
        ),
        (
            "unproven_cannot_authorize_ignore",
            UNPROVEN_CANNOT_AUTHORIZE_IGNORE,
            "P01_UNPROVEN_CANNOT_AUTHORIZE_IGNORE_REQUIRED",
        ),
        (
            "unproven_cannot_authorize_fallback",
            UNPROVEN_CANNOT_AUTHORIZE_FALLBACK,
            "P01_UNPROVEN_CANNOT_AUTHORIZE_FALLBACK_REQUIRED",
        ),
        (
            "unproven_cannot_authorize_stale_filter",
            UNPROVEN_CANNOT_AUTHORIZE_STALE_FILTER,
            "P01_UNPROVEN_CANNOT_AUTHORIZE_STALE_FILTER_REQUIRED",
        ),
        (
            "numeric_provenance_unspecified_does_not_decide_freshness",
            NUMERIC_PROVENANCE_UNSPECIFIED_DOES_NOT_DECIDE_FRESHNESS,
            "P01_NUMERIC_PROVENANCE_DOES_NOT_DECIDE_FRESHNESS_REQUIRED",
        ),
        (
            "term_set_unresolved_does_not_decide_freshness",
            TERM_SET_UNRESOLVED_DOES_NOT_DECIDE_FRESHNESS,
            "P01_TERM_SET_UNRESOLVED_DOES_NOT_DECIDE_FRESHNESS_REQUIRED",
        ),
    ):
        _require_true_pin(field=field, raw=getattr(contract, field), expected=expected, error=error)
    if contract.term_semantics_resolved_status != TERM_SEMANTICS_RESOLVED_STATUS:
        raise P01MemberFreshnessInheritanceContractError(
            "P01_TERM_SEMANTICS_RESOLVED_STATUS_MISMATCH"
        )
    if contract.unspecified_closed_status != UNSPECIFIED_CLOSED_STATUS:
        raise P01MemberFreshnessInheritanceContractError("P01_UNSPECIFIED_CLOSED_STATUS_MISMATCH")
    if contract.contradiction_state != CONTRADICTION_NONE:
        raise P01MemberFreshnessInheritanceContractError("P01_CONTRADICTION_STATE_MISMATCH")
    if contract.rejected_freshness_inferences != REJECTED_FRESHNESS_INFERENCES:
        raise P01MemberFreshnessInheritanceContractError(
            "P01_REJECTED_FRESHNESS_INFERENCES_MISMATCH"
        )
    if contract.evidence_classification != EVIDENCE_CLASSIFICATION:
        raise P01MemberFreshnessInheritanceContractError("P01_EVIDENCE_CLASSIFICATION_MISMATCH")
    if (
        contract.candidate_freshness_rules_classification
        != CANDIDATE_FRESHNESS_RULES_CLASSIFICATION
    ):
        raise P01MemberFreshnessInheritanceContractError(
            "P01_CANDIDATE_FRESHNESS_RULES_CLASSIFICATION_MISMATCH"
        )


def build_p01_member_freshness_inheritance_contract_v1(
    *,
    p01_member_freshness_inheritance_contract_id: str,
    **overrides: Any,
) -> P01MemberFreshnessInheritanceContractV1:
    parent = build_p01_numeric_value_provenance_contract_v1(
        p01_numeric_value_provenance_contract_id="SYNTHETIC_P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_ID"
    )
    if parent.time_semantics_state != PARENT_TIME_SEMANTICS_STATE:
        raise P01MemberFreshnessInheritanceContractError("P01_TIME_SEMANTICS_STATE_MISMATCH")
    payload: dict[str, Any] = dict(overrides)
    defaults: dict[str, str] = {
        "p01_member_freshness_inheritance_contract_id": (
            p01_member_freshness_inheritance_contract_id
        ),
        "p01_member_freshness_inheritance_contract_version": CONTRACT_VERSION,
        "parent_p01_numeric_value_provenance_contract_schema_class": (
            PARENT_NUMERIC_PROVENANCE_CONTRACT_SCHEMA_CLASS
        ),
        "parent_p01_term_contract_schema_class": PARENT_TERM_CONTRACT_SCHEMA_CLASS,
        "target_semantic_dimension_id": DIMENSION_ID,
        "policy_id": POLICY_ID,
        "term_id": TERM_ID,
        "p01_member_freshness_inheritance_resolved_status": (
            P01_MEMBER_FRESHNESS_INHERITANCE_RESOLVED_STATUS
        ),
        "p01_member_freshness_status": P01_MEMBER_FRESHNESS_STATUS,
        "p01_member_freshness_rule": P01_MEMBER_FRESHNESS_RULE,
        "p01_u09_freshness_relation": P01_U09_FRESHNESS_RELATION,
        "p01_freshness_dimension_state": P01_FRESHNESS_DIMENSION_STATE,
        "p01_timestamp_state": P01_TIMESTAMP_STATE,
        "p01_level_freshness_metadata_state": P01_LEVEL_FRESHNESS_METADATA_STATE,
        "member_level_freshness_metadata_state": MEMBER_LEVEL_FRESHNESS_METADATA_STATE,
        "inheritance_rule_state": INHERITANCE_RULE_STATE,
        "u09_comparison_evidence_only": U09_COMPARISON_EVIDENCE_ONLY,
        "u09_is_not_p01_freshness_authority": U09_IS_NOT_P01_FRESHNESS_AUTHORITY,
        "p01_freshness_does_not_inherit_u09": P01_FRESHNESS_DOES_NOT_INHERIT_U09,
        "p01_freshness_not_equivalent_to_u09": P01_FRESHNESS_NOT_EQUIVALENT_TO_U09,
        "unknown_is_not_freshness_authority": UNKNOWN_IS_NOT_FRESHNESS_AUTHORITY,
        "unproven_is_not_freshness_authority": UNPROVEN_IS_NOT_FRESHNESS_AUTHORITY,
        "unspecified_is_not_freshness_authority": UNSPECIFIED_IS_NOT_FRESHNESS_AUTHORITY,
        "missing_input_fail_closed": MISSING_INPUT_FAIL_CLOSED,
        "malformed_input_fail_closed": MALFORMED_INPUT_FAIL_CLOSED,
        "oldest_member_wins_unproven": OLDEST_MEMBER_WINS_UNPROVEN,
        "newest_member_wins_unproven": NEWEST_MEMBER_WINS_UNPROVEN,
        "min_freshness_unproven": MIN_FRESHNESS_UNPROVEN,
        "max_freshness_unproven": MAX_FRESHNESS_UNPROVEN,
        "all_members_same_epoch_unproven": ALL_MEMBERS_SAME_EPOCH_UNPROVEN,
        "weighted_composite_unproven": WEIGHTED_COMPOSITE_UNPROVEN,
        "source_specific_freshness_unproven": SOURCE_SPECIFIC_FRESHNESS_UNPROVEN,
        "independent_p01_timestamp_unproven": INDEPENDENT_P01_TIMESTAMP_UNPROVEN,
        "producer_timestamp_unproven": PRODUCER_TIMESTAMP_UNPROVEN,
        "reconstruction_epoch_unproven": RECONSTRUCTION_EPOCH_UNPROVEN,
        "valuation_epoch_unproven": VALUATION_EPOCH_UNPROVEN,
        "accounting_epoch_unproven": ACCOUNTING_EPOCH_UNPROVEN,
        "current_time_is_not_p01_freshness": CURRENT_TIME_IS_NOT_P01_FRESHNESS,
        "missing_freshness_is_not_fresh": MISSING_FRESHNESS_IS_NOT_FRESH,
        "stale_p01_is_not_admissible": STALE_P01_IS_NOT_ADMISSIBLE,
        "unproven_cannot_authorize_ignore": UNPROVEN_CANNOT_AUTHORIZE_IGNORE,
        "unproven_cannot_authorize_fallback": UNPROVEN_CANNOT_AUTHORIZE_FALLBACK,
        "unproven_cannot_authorize_stale_filter": UNPROVEN_CANNOT_AUTHORIZE_STALE_FILTER,
        "fallback_freshness_state": FALLBACK_FRESHNESS_STATE,
        "numeric_provenance_unspecified_does_not_decide_freshness": (
            NUMERIC_PROVENANCE_UNSPECIFIED_DOES_NOT_DECIDE_FRESHNESS
        ),
        "term_set_unresolved_does_not_decide_freshness": (
            TERM_SET_UNRESOLVED_DOES_NOT_DECIDE_FRESHNESS
        ),
        "parent_time_semantics_state": PARENT_TIME_SEMANTICS_STATE,
        "parent_freshness_epoch_requirements": PARENT_FRESHNESS_EPOCH_REQUIREMENTS,
        "u09_freshness_class_comparison": U09_FRESHNESS_CLASS,
        "rejected_freshness_inferences": REJECTED_FRESHNESS_INFERENCES,
        "remaining_unresolved_semantics": REMAINING_UNRESOLVED_SEMANTICS,
        "evidence_classification": EVIDENCE_CLASSIFICATION,
        "candidate_freshness_rules_classification": CANDIDATE_FRESHNESS_RULES_CLASSIFICATION,
        "contradiction_state": CONTRADICTION_NONE,
        "term_semantics_resolved_status": TERM_SEMANTICS_RESOLVED_STATUS,
        "unspecified_closed_status": UNSPECIFIED_CLOSED_STATUS,
        "p01_member_freshness_inheritance_contract_authority_effect": AUTHORITY_EFFECT_NONE,
    }
    for key, value in defaults.items():
        payload.setdefault(key, value)
    missing = [name for name in _VECTOR_FIELDS if name not in payload]
    if missing:
        raise P01MemberFreshnessInheritanceContractError("P01_FIELD_MISSING:" + ",".join(missing))
    attached = attach_p01_member_freshness_inheritance_digest_v1(payload)
    return P01MemberFreshnessInheritanceContractV1(
        **{name: attached[name] for name in P01_MEMBER_FRESHNESS_INHERITANCE_REQUIRED_FIELDS}
    )


def reject_p01_unproven_freshness_as_authority_v1(*, freshness_status: str) -> None:
    """Unproven or unspecified freshness is not a P01 freshness authority."""

    _reject_coerced_rule(field="p01_member_freshness_status", raw=freshness_status)
    raise P01MemberFreshnessInheritanceContractError("P01_UNPROVEN_FRESHNESS_AUTHORITY_FORBIDDEN")


def reject_p01_u09_freshness_as_p01_authority_v1(*, freshness_rule: str) -> None:
    """U09 freshness is comparison evidence only, not P01 freshness authority."""

    _reject_coerced_rule(field="p01_member_freshness_rule", raw=freshness_rule)
    raise P01MemberFreshnessInheritanceContractError("P01_U09_FRESHNESS_AUTHORITY_FORBIDDEN")


def reject_p01_member_aggregation_rule_v1(*, freshness_rule: str) -> None:
    """Oldest/newest/min/max aggregation is not a ratified P01 freshness rule."""

    _reject_coerced_rule(field="p01_member_freshness_rule", raw=freshness_rule)
    raise P01MemberFreshnessInheritanceContractError("P01_FRESHNESS_RULE_INFERRED_FORBIDDEN")


def reject_p01_current_time_as_freshness_v1(*, freshness_rule: str) -> None:
    """Wall-clock now is not a P01 freshness value."""

    _reject_coerced_rule(field="p01_member_freshness_rule", raw=freshness_rule)
    raise P01MemberFreshnessInheritanceContractError("P01_CURRENT_TIME_FRESHNESS_FORBIDDEN")


def reject_p01_missing_freshness_as_fresh_v1(*, freshness_state: str) -> None:
    """Missing freshness is not fresh."""

    _reject_coerced_rule(field="p01_member_freshness_status", raw=freshness_state)
    raise P01MemberFreshnessInheritanceContractError("P01_MISSING_FRESHNESS_IS_NOT_FRESH")


def reject_p01_stale_as_admissible_v1(*, freshness_state: str) -> None:
    """Stale P01 is not admissible."""

    _reject_coerced_rule(field="p01_member_freshness_status", raw=freshness_state)
    raise P01MemberFreshnessInheritanceContractError("P01_STALE_FRESHNESS_ADMISSION_FORBIDDEN")


def reject_p01_unproven_freshness_as_ignore_v1(*, requested_action: str) -> None:
    """Unproven freshness cannot authorize ignore, fallback, or stale filtering."""

    _reject_coerced_rule(field="requested_action", raw=requested_action)
    raise P01MemberFreshnessInheritanceContractError("P01_UNPROVEN_FRESHNESS_IGNORE_FORBIDDEN")
