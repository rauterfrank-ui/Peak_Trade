"""Typed venue-witness normalization/inclusion adjudication contract.

Schema/contract only. Observation is not authority. Inclusion eligibility
is not source selection. A requested target dimension is not a proven
mapping. Not a producer. Not a runtime value binding. Not a
LIVE_ACCOUNT_BOUND join. Construction of a schema instance is not a
productive normalization runtime instance.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping, Tuple

from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    EQUITY_DIMENSION_BOUND,
    FIELD_TO_DIMENSION_MAPPING_PRESENT,
    FIELD_TO_DIMENSION_MAPPING_SCHEMA_PRESENT,
    GOVERNED_PRODUCER_CREATED,
    INCLUSION_PROVEN,
    INTERNAL_RECONSTRUCTION_CREATED,
    MAPPED_TO_RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING,
    NORMALIZATION_AUTHORITY_EFFECT,
    NORMALIZATION_PROVENANCE_REQUIRED_FIELDS,
    NORMALIZATION_RUNTIME_INSTANCE_PRESENT,
    NORMALIZATION_SCHEMA_PRESENT,
    SEMANTIC_MAPPING_PROVEN,
    SOURCE_OBJECT_PRESENT,
    SOURCE_SELECTED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.venue_witness_observation_v1 import (
    OBSERVATION_SEMANTIC_CLASS,
    PRESENCE_EMPTY,
    PRESENCE_MALFORMED,
    PRESENCE_MISSING,
    PRESENCE_NONZERO,
    PRESENCE_STATES,
    PRESENCE_ZERO,
)

SCHEMA_CLASS = "NORMALIZATION_INCLUSION_ADJUDICATION_V1"
DIMENSION_ID = "RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING"
MAPPING_STATUS_UNBOUND = "UNBOUND"
OBSERVATION_PARTICIPATION_STATE_OBSERVED = "OBSERVED"
NORMALIZABLE_STATUS_NORMALIZABLE = "NORMALIZABLE"
NORMALIZABLE_STATUS_NOT_NORMALIZABLE = "NOT_NORMALIZABLE"
SEMANTIC_MAPPING_STATUS_UNBOUND = "UNBOUND"
SEMANTIC_MAPPING_STATUS_MAPPED = "SEMANTICALLY_MAPPED"
INCLUSION_STATUS_EXCLUDED = "EXCLUDED"
INCLUSION_STATUS_UNPROVEN = "INCLUSION_UNPROVEN"
INCLUSION_STATUS_INCLUDED = "INCLUDED"
SOURCE_SELECTION_STATUS_NOT_SELECTED = "NOT_SELECTED"
SOURCE_SELECTION_STATUS_SELECTED = "SELECTED"
OBSERVATION_VS_AUTHORITY_CLASS_OBSERVATION = "OBSERVATION"
OBSERVATION_VS_AUTHORITY_CLASS_AUTHORITY = "AUTHORITY"
COMPATIBILITY_COMPATIBLE = "COMPATIBLE"
COMPATIBILITY_INCOMPATIBLE = "INCOMPATIBLE"
COMPATIBILITY_UNPROVEN = "UNPROVEN"
COMPATIBILITY_UNSUPPORTED = "UNSUPPORTED"
FRESHNESS_UNPROVEN = "UNPROVEN"
FRESHNESS_STALE = "STALE"
FRESHNESS_WITNESS_TIMESTAMPS_NOT_TTL_POLICY = "EXPLICIT_TIMESTAMPS_NOT_WITNESS_TTL_POLICY"
FRESHNESS_PROVEN = "PROVEN"
PROVENANCE_PRESENT = "PROVENANCE_PRESENT"
PROVENANCE_ABSENT = "ABSENT"
AMBIGUITY_NONE = "NO_AMBIGUITY"
AMBIGUITY_UNRESOLVED = "UNRESOLVED"
CONTRADICTION_NONE = "NO_CONTRADICTION"
CONTRADICTION_PRESENT = "CONTRADICTION_PRESENT"
PROVEN_STATUS_UNPROVEN = "UNPROVEN"
PROVEN_STATUS_PROVEN = "PROVEN"
EXCLUSION_NONE = "NONE"
EXCLUSION_MISSING_VALUE = "EXCLUSION_MISSING_VALUE"
EXCLUSION_EMPTY_VALUE = "EXCLUSION_EMPTY_VALUE"
EXCLUSION_MALFORMED_VALUE = "EXCLUSION_MALFORMED_VALUE"
EXCLUSION_UNSUPPORTED_SEMANTIC_CLASS = "EXCLUSION_UNSUPPORTED_SEMANTIC_CLASS"
EXCLUSION_INCOMPATIBLE_ACCOUNT_SCOPE = "EXCLUSION_INCOMPATIBLE_ACCOUNT_SCOPE"
EXCLUSION_INCOMPATIBLE_CURRENCY_DOMAIN = "EXCLUSION_INCOMPATIBLE_CURRENCY_DOMAIN"
EXCLUSION_UNSUPPORTED_UNIT = "EXCLUSION_UNSUPPORTED_UNIT"
EXCLUSION_STALE_OR_UNPROVEN_FRESHNESS = "EXCLUSION_STALE_OR_UNPROVEN_FRESHNESS"
EXCLUSION_ABSENT_PROVENANCE = "EXCLUSION_ABSENT_PROVENANCE"
EXCLUSION_UNRESOLVED_AMBIGUITY = "EXCLUSION_UNRESOLVED_AMBIGUITY"
EXCLUSION_CONTRADICTION = "EXCLUSION_CONTRADICTION"
EXCLUSION_UNSUPPORTED_RAW_FIELD_MAPPING = "EXCLUSION_UNSUPPORTED_RAW_FIELD_MAPPING"
EXCLUSION_INSUFFICIENT_EVIDENCE = "EXCLUSION_INSUFFICIENT_EVIDENCE"
KNOWN_EXCLUSION_CODES: Tuple[str, ...] = (
    EXCLUSION_MISSING_VALUE,
    EXCLUSION_EMPTY_VALUE,
    EXCLUSION_MALFORMED_VALUE,
    EXCLUSION_UNSUPPORTED_SEMANTIC_CLASS,
    EXCLUSION_INCOMPATIBLE_ACCOUNT_SCOPE,
    EXCLUSION_INCOMPATIBLE_CURRENCY_DOMAIN,
    EXCLUSION_UNSUPPORTED_UNIT,
    EXCLUSION_STALE_OR_UNPROVEN_FRESHNESS,
    EXCLUSION_ABSENT_PROVENANCE,
    EXCLUSION_UNRESOLVED_AMBIGUITY,
    EXCLUSION_CONTRADICTION,
    EXCLUSION_UNSUPPORTED_RAW_FIELD_MAPPING,
    EXCLUSION_INSUFFICIENT_EVIDENCE,
)
ZERO_COLLAPSE_EXCLUSION_CODES: Tuple[str, ...] = (
    EXCLUSION_MISSING_VALUE,
    EXCLUSION_EMPTY_VALUE,
    EXCLUSION_MALFORMED_VALUE,
)
UNPROVEN_FRESHNESS_STATES: Tuple[str, ...] = (
    FRESHNESS_UNPROVEN,
    FRESHNESS_STALE,
    FRESHNESS_WITNESS_TIMESTAMPS_NOT_TTL_POLICY,
)
_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")
_SCIENTIFIC_NOTATION = re.compile(r"^[+-]?(?:\d+\.?\d*|\.\d+)[eE][+-]?\d+$")
_FORBIDDEN_FALLBACK_MARKERS: Tuple[str, ...] = ("|", " or ", ",", ";")
_IDENTITY_SEMANTICS_FIELDS: Tuple[str, ...] = (
    "observation_semantic_class",
    "observation_participation_state",
    "normalizable_status",
    "semantic_mapping_status",
    "inclusion_status",
    "source_selection_status",
    "observation_vs_authority_class",
    "normalization_authority_effect",
    "field_to_dimension_mapping_status",
    "semantic_mapping_proven_status",
    "inclusion_proven_status",
    "source_selected_status",
)


class NormalizationInclusionAdjudicationContractError(ValueError):
    """Fail-closed normalization/inclusion adjudication contract violation."""


def _fold(value: str) -> str:
    return str(value or "").strip().lower().replace("_", "").replace("-", "")


def _require_non_empty_str(*, field: str, raw: Any) -> str:
    if raw is None:
        raise NormalizationInclusionAdjudicationContractError(
            f"NORMALIZATION_INCLUSION_FIELD_MISSING:{field}"
        )
    if not isinstance(raw, str):
        raise NormalizationInclusionAdjudicationContractError(
            f"NORMALIZATION_INCLUSION_FIELD_NOT_STRING:{field}"
        )
    text = raw.strip()
    if text == "" or text != raw:
        raise NormalizationInclusionAdjudicationContractError(
            f"NORMALIZATION_INCLUSION_FIELD_MISSING:{field}"
        )
    return text


def _require_str_allow_empty(*, field: str, raw: Any) -> str:
    if raw is None:
        raise NormalizationInclusionAdjudicationContractError(
            f"NORMALIZATION_INCLUSION_FIELD_MISSING:{field}"
        )
    if not isinstance(raw, str):
        raise NormalizationInclusionAdjudicationContractError(
            f"NORMALIZATION_INCLUSION_FIELD_NOT_STRING:{field}"
        )
    if raw.strip() != raw:
        raise NormalizationInclusionAdjudicationContractError(
            f"NORMALIZATION_INCLUSION_FIELD_NOT_EXACT:{field}"
        )
    return raw


def _reject_fallback_chain(*, field: str, raw: str) -> None:
    lowered = raw.lower()
    for marker in _FORBIDDEN_FALLBACK_MARKERS:
        if marker in lowered:
            raise NormalizationInclusionAdjudicationContractError(
                f"NORMALIZATION_INCLUSION_FALLBACK_CHAIN_FORBIDDEN:{field}"
            )


def _parse_simple_decimal(raw: str) -> Decimal | None:
    if raw == "" or _SCIENTIFIC_NOTATION.fullmatch(raw):
        return None
    lowered = raw.lower()
    if lowered in {"nan", "inf", "+inf", "-inf", "infinity", "+infinity", "-infinity"}:
        return None
    try:
        value = Decimal(raw)
    except (InvalidOperation, ValueError):
        return None
    if not value.is_finite():
        return None
    return value


def _sha256_hex(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _canonical_json(payload: Mapping[str, str]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def parse_exclusion_reason_codes_v1(raw: str) -> Tuple[str, ...]:
    text = _require_non_empty_str(field="exclusion_reason_codes", raw=raw)
    if text == EXCLUSION_NONE:
        return ()
    codes = tuple(part.strip() for part in text.split(",") if part.strip())
    if not codes:
        raise NormalizationInclusionAdjudicationContractError(
            "NORMALIZATION_INCLUSION_EXCLUSION_REASON_CODES_EMPTY"
        )
    unknown = [code for code in codes if code not in KNOWN_EXCLUSION_CODES]
    if unknown:
        raise NormalizationInclusionAdjudicationContractError(
            "NORMALIZATION_INCLUSION_EXCLUSION_REASON_UNKNOWN:" + ",".join(unknown)
        )
    if tuple(sorted(codes)) != codes:
        raise NormalizationInclusionAdjudicationContractError(
            "NORMALIZATION_INCLUSION_EXCLUSION_REASON_CODES_NOT_SORTED"
        )
    if len(set(codes)) != len(codes):
        raise NormalizationInclusionAdjudicationContractError(
            "NORMALIZATION_INCLUSION_EXCLUSION_REASON_CODES_DUPLICATE"
        )
    return codes


def encode_exclusion_reason_codes_v1(codes: Tuple[str, ...]) -> str:
    if not codes:
        return EXCLUSION_NONE
    ordered = tuple(sorted(codes))
    return ",".join(ordered)


def compute_normalization_inclusion_provenance_digest_v1(
    canonical: Mapping[str, str],
) -> str:
    payload = {
        key: canonical[key]
        for key in NORMALIZATION_PROVENANCE_REQUIRED_FIELDS
        if key != "provenance_digest"
    }
    return _sha256_hex(_canonical_json(payload))


def attach_normalization_inclusion_provenance_digest_v1(
    fields: Mapping[str, Any],
) -> dict[str, Any]:
    """Attach the deterministic digest. Does not mint, map, or select."""

    canonical: dict[str, str] = {}
    for canonical_name in NORMALIZATION_PROVENANCE_REQUIRED_FIELDS:
        if canonical_name == "provenance_digest":
            continue
        if canonical_name not in fields:
            raise NormalizationInclusionAdjudicationContractError(
                f"NORMALIZATION_INCLUSION_FIELD_MISSING:{canonical_name}"
            )
        raw = fields[canonical_name]
        canonical[canonical_name] = "" if raw is None else str(raw)
    attached = dict(fields)
    attached["provenance_digest"] = compute_normalization_inclusion_provenance_digest_v1(canonical)
    return attached


@dataclass(frozen=True)
class NormalizationInclusionAdjudicationV1:
    """Typed immutable normalization/inclusion adjudication. Schema only."""

    adjudication_id: str
    source_witness_id: str
    bound_account_identity: str
    bound_venue_identity: str
    rest_host: str
    bound_td_mode: str
    account_mode: str
    currency_domain: str
    decision_epoch: str
    raw_field_path: str
    observation_semantic_class: str
    raw_value_representation: str
    presence_state: str
    requested_target_dimension_id: str
    field_to_dimension_mapping_status: str
    observation_participation_state: str
    normalizable_status: str
    semantic_mapping_status: str
    inclusion_status: str
    source_selection_status: str
    observation_vs_authority_class: str
    normalization_authority_effect: str
    exclusion_reason_codes: str
    account_scope_compatibility_status: str
    currency_domain_compatibility_status: str
    unit_compatibility_status: str
    freshness_evidence_status: str
    freshness_evidence_ref: str
    provenance_status: str
    ambiguity_status: str
    contradiction_status: str
    semantic_mapping_proven_status: str
    inclusion_proven_status: str
    source_selected_status: str
    provenance_digest: str

    def __post_init__(self) -> None:
        _validate_normalization_inclusion_adjudication_v1(self)

    def to_canonical_dict(self) -> dict[str, str]:
        values = {
            "adjudication_id": self.adjudication_id,
            "source_witness_id": self.source_witness_id,
            "bound_account_identity": self.bound_account_identity,
            "bound_venue_identity": self.bound_venue_identity,
            "rest_host": self.rest_host,
            "bound_td_mode": self.bound_td_mode,
            "account_mode": self.account_mode,
            "currency_domain": self.currency_domain,
            "decision_epoch": self.decision_epoch,
            "raw_field_path": self.raw_field_path,
            "observation_semantic_class": self.observation_semantic_class,
            "raw_value_representation": self.raw_value_representation,
            "presence_state": self.presence_state,
            "requested_target_dimension_id": self.requested_target_dimension_id,
            "field_to_dimension_mapping_status": self.field_to_dimension_mapping_status,
            "observation_participation_state": self.observation_participation_state,
            "normalizable_status": self.normalizable_status,
            "semantic_mapping_status": self.semantic_mapping_status,
            "inclusion_status": self.inclusion_status,
            "source_selection_status": self.source_selection_status,
            "observation_vs_authority_class": self.observation_vs_authority_class,
            "normalization_authority_effect": self.normalization_authority_effect,
            "exclusion_reason_codes": self.exclusion_reason_codes,
            "account_scope_compatibility_status": self.account_scope_compatibility_status,
            "currency_domain_compatibility_status": self.currency_domain_compatibility_status,
            "unit_compatibility_status": self.unit_compatibility_status,
            "freshness_evidence_status": self.freshness_evidence_status,
            "freshness_evidence_ref": self.freshness_evidence_ref,
            "provenance_status": self.provenance_status,
            "ambiguity_status": self.ambiguity_status,
            "contradiction_status": self.contradiction_status,
            "semantic_mapping_proven_status": self.semantic_mapping_proven_status,
            "inclusion_proven_status": self.inclusion_proven_status,
            "source_selected_status": self.source_selected_status,
            "provenance_digest": self.provenance_digest,
        }
        return {key: values[key] for key in NORMALIZATION_PROVENANCE_REQUIRED_FIELDS}


def _validate_presence_state(*, presence_state: str, raw_value: str) -> None:
    parsed = _parse_simple_decimal(raw_value)
    if presence_state == PRESENCE_MISSING:
        if raw_value != "":
            raise NormalizationInclusionAdjudicationContractError(
                "NORMALIZATION_INCLUSION_MISSING_MUST_HAVE_EMPTY_RAW"
            )
        return
    if presence_state == PRESENCE_EMPTY:
        if raw_value != "":
            raise NormalizationInclusionAdjudicationContractError(
                "NORMALIZATION_INCLUSION_EMPTY_MUST_HAVE_EMPTY_RAW"
            )
        return
    if presence_state == PRESENCE_ZERO:
        if parsed is None or parsed != Decimal("0"):
            raise NormalizationInclusionAdjudicationContractError(
                "NORMALIZATION_INCLUSION_PRESENT_ZERO_REQUIRES_ZERO_DECIMAL"
            )
        return
    if presence_state == PRESENCE_NONZERO:
        if parsed is None or parsed == Decimal("0"):
            raise NormalizationInclusionAdjudicationContractError(
                "NORMALIZATION_INCLUSION_PRESENT_NONZERO_REQUIRES_NONZERO_DECIMAL"
            )
        return
    if presence_state == PRESENCE_MALFORMED:
        if raw_value == "" or parsed is not None:
            raise NormalizationInclusionAdjudicationContractError(
                "NORMALIZATION_INCLUSION_MALFORMED_REQUIRES_NON_DECIMAL_RAW"
            )
        return
    raise NormalizationInclusionAdjudicationContractError(
        f"NORMALIZATION_INCLUSION_PRESENCE_STATE_UNKNOWN:{presence_state}"
    )


def _required_exclusion_codes(
    *,
    presence_state: str,
    observation_semantic_class: str,
    account_scope_status: str,
    currency_status: str,
    unit_status: str,
    freshness_status: str,
    provenance_status: str,
    ambiguity_status: str,
    contradiction_status: str,
    mapping_status: str,
    account_scope_unproven: bool,
    currency_unproven: bool,
    unit_unproven: bool,
) -> Tuple[str, ...]:
    codes: list[str] = []
    if presence_state == PRESENCE_MISSING:
        codes.append(EXCLUSION_MISSING_VALUE)
    if presence_state == PRESENCE_EMPTY:
        codes.append(EXCLUSION_EMPTY_VALUE)
    if presence_state == PRESENCE_MALFORMED:
        codes.append(EXCLUSION_MALFORMED_VALUE)
    if observation_semantic_class != OBSERVATION_SEMANTIC_CLASS:
        codes.append(EXCLUSION_UNSUPPORTED_SEMANTIC_CLASS)
    if account_scope_status == COMPATIBILITY_INCOMPATIBLE:
        codes.append(EXCLUSION_INCOMPATIBLE_ACCOUNT_SCOPE)
    if currency_status == COMPATIBILITY_INCOMPATIBLE:
        codes.append(EXCLUSION_INCOMPATIBLE_CURRENCY_DOMAIN)
    if unit_status in {COMPATIBILITY_INCOMPATIBLE, COMPATIBILITY_UNSUPPORTED}:
        codes.append(EXCLUSION_UNSUPPORTED_UNIT)
    if freshness_status in UNPROVEN_FRESHNESS_STATES:
        codes.append(EXCLUSION_STALE_OR_UNPROVEN_FRESHNESS)
    if provenance_status == PROVENANCE_ABSENT:
        codes.append(EXCLUSION_ABSENT_PROVENANCE)
    if ambiguity_status == AMBIGUITY_UNRESOLVED:
        codes.append(EXCLUSION_UNRESOLVED_AMBIGUITY)
    if contradiction_status == CONTRADICTION_PRESENT:
        codes.append(EXCLUSION_CONTRADICTION)
    if mapping_status == MAPPING_STATUS_UNBOUND:
        codes.append(EXCLUSION_UNSUPPORTED_RAW_FIELD_MAPPING)
    if account_scope_unproven or currency_unproven or unit_unproven:
        codes.append(EXCLUSION_INSUFFICIENT_EVIDENCE)
    return tuple(sorted(set(codes)))


def _validate_normalization_inclusion_adjudication_v1(
    adjudication: NormalizationInclusionAdjudicationV1,
) -> None:
    if NORMALIZATION_SCHEMA_PRESENT is not True:
        raise NormalizationInclusionAdjudicationContractError(
            "NORMALIZATION_INCLUSION_SCHEMA_PRESENT_REQUIRED"
        )
    if NORMALIZATION_RUNTIME_INSTANCE_PRESENT is True:
        raise NormalizationInclusionAdjudicationContractError(
            "NORMALIZATION_INCLUSION_RUNTIME_INSTANCE_FORBIDDEN"
        )
    if FIELD_TO_DIMENSION_MAPPING_SCHEMA_PRESENT is not True:
        raise NormalizationInclusionAdjudicationContractError(
            "NORMALIZATION_INCLUSION_MAPPING_SCHEMA_PRESENT_REQUIRED"
        )
    if FIELD_TO_DIMENSION_MAPPING_PRESENT is True:
        raise NormalizationInclusionAdjudicationContractError(
            "NORMALIZATION_INCLUSION_FIELD_TO_DIMENSION_MAPPING_FORBIDDEN"
        )
    if SEMANTIC_MAPPING_PROVEN is True:
        raise NormalizationInclusionAdjudicationContractError(
            "NORMALIZATION_INCLUSION_SEMANTIC_MAPPING_PROVEN_FORBIDDEN"
        )
    if INCLUSION_PROVEN is True:
        raise NormalizationInclusionAdjudicationContractError(
            "NORMALIZATION_INCLUSION_INCLUSION_PROVEN_FORBIDDEN"
        )
    if SOURCE_OBJECT_PRESENT is True:
        raise NormalizationInclusionAdjudicationContractError(
            "NORMALIZATION_INCLUSION_RUNTIME_SOURCE_OBJECT_FORBIDDEN"
        )
    if SOURCE_SELECTED is True:
        raise NormalizationInclusionAdjudicationContractError(
            "NORMALIZATION_INCLUSION_SOURCE_SELECTION_FORBIDDEN"
        )
    if GOVERNED_PRODUCER_CREATED is True:
        raise NormalizationInclusionAdjudicationContractError(
            "NORMALIZATION_INCLUSION_PRODUCER_MUST_REMAIN_ABSENT"
        )
    if INTERNAL_RECONSTRUCTION_CREATED is True:
        raise NormalizationInclusionAdjudicationContractError(
            "NORMALIZATION_INCLUSION_INTERNAL_RECONSTRUCTION_FORBIDDEN"
        )
    if EQUITY_DIMENSION_BOUND is True:
        raise NormalizationInclusionAdjudicationContractError(
            "NORMALIZATION_INCLUSION_EQUITY_DIMENSION_BOUND_FORBIDDEN"
        )
    if MAPPED_TO_RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING is True:
        raise NormalizationInclusionAdjudicationContractError(
            "NORMALIZATION_INCLUSION_MAPPING_FORBIDDEN"
        )

    _require_non_empty_str(field="adjudication_id", raw=adjudication.adjudication_id)
    _require_non_empty_str(field="source_witness_id", raw=adjudication.source_witness_id)
    _require_non_empty_str(field="bound_account_identity", raw=adjudication.bound_account_identity)
    _require_non_empty_str(field="bound_venue_identity", raw=adjudication.bound_venue_identity)
    _require_non_empty_str(field="rest_host", raw=adjudication.rest_host)
    _require_non_empty_str(field="bound_td_mode", raw=adjudication.bound_td_mode)
    _require_non_empty_str(field="account_mode", raw=adjudication.account_mode)
    currency = _require_non_empty_str(field="currency_domain", raw=adjudication.currency_domain)
    if _fold(currency) == "usdusdc" or currency == "USD=USDC":
        raise NormalizationInclusionAdjudicationContractError(
            "NORMALIZATION_INCLUSION_USD_USDC_EQUIVALENCE_FORBIDDEN"
        )
    _require_non_empty_str(field="decision_epoch", raw=adjudication.decision_epoch)
    raw_field_path = _require_non_empty_str(field="raw_field_path", raw=adjudication.raw_field_path)
    _reject_fallback_chain(field="raw_field_path", raw=raw_field_path)
    semantic = _require_non_empty_str(
        field="observation_semantic_class", raw=adjudication.observation_semantic_class
    )
    if semantic != OBSERVATION_SEMANTIC_CLASS:
        raise NormalizationInclusionAdjudicationContractError(
            "NORMALIZATION_INCLUSION_SEMANTIC_CLASS_NOT_RAW_VENUE_OBSERVATION"
        )
    if _fold(semantic) == _fold(DIMENSION_ID):
        raise NormalizationInclusionAdjudicationContractError(
            "NORMALIZATION_INCLUSION_OBSERVATION_CLASS_MUST_NOT_CLAIM_EQUITY_DIMENSION"
        )
    raw_value = _require_str_allow_empty(
        field="raw_value_representation", raw=adjudication.raw_value_representation
    )
    presence = _require_non_empty_str(field="presence_state", raw=adjudication.presence_state)
    if presence not in PRESENCE_STATES:
        raise NormalizationInclusionAdjudicationContractError(
            f"NORMALIZATION_INCLUSION_PRESENCE_STATE_UNKNOWN:{presence}"
        )
    _validate_presence_state(presence_state=presence, raw_value=raw_value)
    requested = _require_non_empty_str(
        field="requested_target_dimension_id",
        raw=adjudication.requested_target_dimension_id,
    )
    if requested != DIMENSION_ID:
        raise NormalizationInclusionAdjudicationContractError(
            "NORMALIZATION_INCLUSION_REQUESTED_TARGET_DIMENSION_UNKNOWN"
        )
    mapping_status = _require_non_empty_str(
        field="field_to_dimension_mapping_status",
        raw=adjudication.field_to_dimension_mapping_status,
    )
    if mapping_status != MAPPING_STATUS_UNBOUND:
        raise NormalizationInclusionAdjudicationContractError(
            "NORMALIZATION_INCLUSION_FIELD_TO_DIMENSION_MAPPING_STATUS_MUST_REMAIN_UNBOUND"
        )
    observed = _require_non_empty_str(
        field="observation_participation_state",
        raw=adjudication.observation_participation_state,
    )
    if observed != OBSERVATION_PARTICIPATION_STATE_OBSERVED:
        raise NormalizationInclusionAdjudicationContractError(
            "NORMALIZATION_INCLUSION_OBSERVATION_PARTICIPATION_STATE_MUST_BE_OBSERVED"
        )
    normalizable = _require_non_empty_str(
        field="normalizable_status", raw=adjudication.normalizable_status
    )
    if normalizable not in {
        NORMALIZABLE_STATUS_NORMALIZABLE,
        NORMALIZABLE_STATUS_NOT_NORMALIZABLE,
    }:
        raise NormalizationInclusionAdjudicationContractError(
            f"NORMALIZATION_INCLUSION_NORMALIZABLE_STATUS_UNKNOWN:{normalizable}"
        )
    if presence in {PRESENCE_MISSING, PRESENCE_EMPTY, PRESENCE_MALFORMED}:
        if normalizable != NORMALIZABLE_STATUS_NOT_NORMALIZABLE:
            raise NormalizationInclusionAdjudicationContractError(
                "NORMALIZATION_INCLUSION_MISSING_EMPTY_MALFORMED_NOT_NORMALIZABLE"
            )
    if presence in {PRESENCE_ZERO, PRESENCE_NONZERO}:
        if normalizable not in {
            NORMALIZABLE_STATUS_NORMALIZABLE,
            NORMALIZABLE_STATUS_NOT_NORMALIZABLE,
        }:
            raise NormalizationInclusionAdjudicationContractError(
                "NORMALIZATION_INCLUSION_PRESENT_VALUE_NORMALIZABLE_STATUS_UNKNOWN"
            )
    if observed == normalizable:
        raise NormalizationInclusionAdjudicationContractError(
            "NORMALIZATION_INCLUSION_OBSERVED_MUST_NOT_EQUAL_NORMALIZABLE"
        )
    semantic_mapping = _require_non_empty_str(
        field="semantic_mapping_status", raw=adjudication.semantic_mapping_status
    )
    if semantic_mapping == SEMANTIC_MAPPING_STATUS_MAPPED:
        raise NormalizationInclusionAdjudicationContractError(
            "NORMALIZATION_INCLUSION_SEMANTICALLY_MAPPED_FORBIDDEN"
        )
    if semantic_mapping != SEMANTIC_MAPPING_STATUS_UNBOUND:
        raise NormalizationInclusionAdjudicationContractError(
            "NORMALIZATION_INCLUSION_SEMANTIC_MAPPING_STATUS_MUST_REMAIN_UNBOUND"
        )
    if normalizable == semantic_mapping:
        raise NormalizationInclusionAdjudicationContractError(
            "NORMALIZATION_INCLUSION_NORMALIZABLE_MUST_NOT_EQUAL_SEMANTICALLY_MAPPED"
        )
    inclusion = _require_non_empty_str(field="inclusion_status", raw=adjudication.inclusion_status)
    if inclusion == INCLUSION_STATUS_INCLUDED:
        raise NormalizationInclusionAdjudicationContractError(
            "NORMALIZATION_INCLUSION_INCLUDED_FORBIDDEN"
        )
    if inclusion not in {INCLUSION_STATUS_EXCLUDED, INCLUSION_STATUS_UNPROVEN}:
        raise NormalizationInclusionAdjudicationContractError(
            f"NORMALIZATION_INCLUSION_INCLUSION_STATUS_UNKNOWN:{inclusion}"
        )
    if semantic_mapping == inclusion:
        raise NormalizationInclusionAdjudicationContractError(
            "NORMALIZATION_INCLUSION_SEMANTICALLY_MAPPED_MUST_NOT_EQUAL_INCLUDED"
        )
    source_selection = _require_non_empty_str(
        field="source_selection_status", raw=adjudication.source_selection_status
    )
    if source_selection == SOURCE_SELECTION_STATUS_SELECTED:
        raise NormalizationInclusionAdjudicationContractError(
            "NORMALIZATION_INCLUSION_SELECTED_FORBIDDEN"
        )
    if source_selection != SOURCE_SELECTION_STATUS_NOT_SELECTED:
        raise NormalizationInclusionAdjudicationContractError(
            "NORMALIZATION_INCLUSION_SOURCE_SELECTION_STATUS_MUST_REMAIN_NOT_SELECTED"
        )
    if inclusion == source_selection:
        raise NormalizationInclusionAdjudicationContractError(
            "NORMALIZATION_INCLUSION_INCLUDED_MUST_NOT_EQUAL_SELECTED"
        )
    authority_class = _require_non_empty_str(
        field="observation_vs_authority_class",
        raw=adjudication.observation_vs_authority_class,
    )
    if authority_class == OBSERVATION_VS_AUTHORITY_CLASS_AUTHORITY:
        raise NormalizationInclusionAdjudicationContractError(
            "NORMALIZATION_INCLUSION_AUTHORITY_CLASS_FORBIDDEN"
        )
    if authority_class != OBSERVATION_VS_AUTHORITY_CLASS_OBSERVATION:
        raise NormalizationInclusionAdjudicationContractError(
            "NORMALIZATION_INCLUSION_OBSERVATION_VS_AUTHORITY_CLASS_UNKNOWN"
        )
    if source_selection == authority_class:
        raise NormalizationInclusionAdjudicationContractError(
            "NORMALIZATION_INCLUSION_SELECTED_MUST_NOT_EQUAL_AUTHORITATIVE"
        )
    effect = _require_non_empty_str(
        field="normalization_authority_effect",
        raw=adjudication.normalization_authority_effect,
    )
    if effect != NORMALIZATION_AUTHORITY_EFFECT:
        raise NormalizationInclusionAdjudicationContractError(
            "NORMALIZATION_INCLUSION_AUTHORITY_EFFECT_MUST_BE_NONE"
        )
    account_scope = _require_non_empty_str(
        field="account_scope_compatibility_status",
        raw=adjudication.account_scope_compatibility_status,
    )
    if account_scope not in {
        COMPATIBILITY_COMPATIBLE,
        COMPATIBILITY_INCOMPATIBLE,
        COMPATIBILITY_UNPROVEN,
    }:
        raise NormalizationInclusionAdjudicationContractError(
            f"NORMALIZATION_INCLUSION_ACCOUNT_SCOPE_STATUS_UNKNOWN:{account_scope}"
        )
    currency_status = _require_non_empty_str(
        field="currency_domain_compatibility_status",
        raw=adjudication.currency_domain_compatibility_status,
    )
    if currency_status not in {
        COMPATIBILITY_COMPATIBLE,
        COMPATIBILITY_INCOMPATIBLE,
        COMPATIBILITY_UNPROVEN,
    }:
        raise NormalizationInclusionAdjudicationContractError(
            f"NORMALIZATION_INCLUSION_CURRENCY_DOMAIN_STATUS_UNKNOWN:{currency_status}"
        )
    if _fold(currency) != "usdc" and currency_status == COMPATIBILITY_COMPATIBLE:
        raise NormalizationInclusionAdjudicationContractError(
            "NORMALIZATION_INCLUSION_NON_USDC_CANNOT_BE_CURRENCY_COMPATIBLE"
        )
    unit_status = _require_non_empty_str(
        field="unit_compatibility_status", raw=adjudication.unit_compatibility_status
    )
    if unit_status not in {
        COMPATIBILITY_COMPATIBLE,
        COMPATIBILITY_INCOMPATIBLE,
        COMPATIBILITY_UNPROVEN,
        COMPATIBILITY_UNSUPPORTED,
    }:
        raise NormalizationInclusionAdjudicationContractError(
            f"NORMALIZATION_INCLUSION_UNIT_STATUS_UNKNOWN:{unit_status}"
        )
    freshness = _require_non_empty_str(
        field="freshness_evidence_status", raw=adjudication.freshness_evidence_status
    )
    if freshness == FRESHNESS_PROVEN:
        raise NormalizationInclusionAdjudicationContractError(
            "NORMALIZATION_INCLUSION_FRESHNESS_PROVEN_FORBIDDEN"
        )
    if freshness not in UNPROVEN_FRESHNESS_STATES:
        raise NormalizationInclusionAdjudicationContractError(
            f"NORMALIZATION_INCLUSION_FRESHNESS_STATUS_UNKNOWN:{freshness}"
        )
    _require_non_empty_str(field="freshness_evidence_ref", raw=adjudication.freshness_evidence_ref)
    provenance_status = _require_non_empty_str(
        field="provenance_status", raw=adjudication.provenance_status
    )
    if provenance_status not in {PROVENANCE_PRESENT, PROVENANCE_ABSENT}:
        raise NormalizationInclusionAdjudicationContractError(
            f"NORMALIZATION_INCLUSION_PROVENANCE_STATUS_UNKNOWN:{provenance_status}"
        )
    ambiguity = _require_non_empty_str(field="ambiguity_status", raw=adjudication.ambiguity_status)
    if ambiguity not in {AMBIGUITY_NONE, AMBIGUITY_UNRESOLVED}:
        raise NormalizationInclusionAdjudicationContractError(
            f"NORMALIZATION_INCLUSION_AMBIGUITY_STATUS_UNKNOWN:{ambiguity}"
        )
    contradiction = _require_non_empty_str(
        field="contradiction_status", raw=adjudication.contradiction_status
    )
    if contradiction not in {CONTRADICTION_NONE, CONTRADICTION_PRESENT}:
        raise NormalizationInclusionAdjudicationContractError(
            f"NORMALIZATION_INCLUSION_CONTRADICTION_STATUS_UNKNOWN:{contradiction}"
        )
    mapping_proven_status = _require_non_empty_str(
        field="semantic_mapping_proven_status",
        raw=adjudication.semantic_mapping_proven_status,
    )
    if mapping_proven_status != PROVEN_STATUS_UNPROVEN:
        raise NormalizationInclusionAdjudicationContractError(
            "NORMALIZATION_INCLUSION_SEMANTIC_MAPPING_PROVEN_STATUS_MUST_REMAIN_UNPROVEN"
        )
    inclusion_proven_status = _require_non_empty_str(
        field="inclusion_proven_status", raw=adjudication.inclusion_proven_status
    )
    if inclusion_proven_status != PROVEN_STATUS_UNPROVEN:
        raise NormalizationInclusionAdjudicationContractError(
            "NORMALIZATION_INCLUSION_INCLUSION_PROVEN_STATUS_MUST_REMAIN_UNPROVEN"
        )
    source_selected_status = _require_non_empty_str(
        field="source_selected_status", raw=adjudication.source_selected_status
    )
    if source_selected_status != SOURCE_SELECTION_STATUS_NOT_SELECTED:
        raise NormalizationInclusionAdjudicationContractError(
            "NORMALIZATION_INCLUSION_SOURCE_SELECTED_STATUS_MUST_REMAIN_NOT_SELECTED"
        )
    declared_codes = parse_exclusion_reason_codes_v1(adjudication.exclusion_reason_codes)
    if presence in {PRESENCE_ZERO, PRESENCE_NONZERO}:
        collapsed = [code for code in declared_codes if code in ZERO_COLLAPSE_EXCLUSION_CODES]
        if collapsed:
            raise NormalizationInclusionAdjudicationContractError(
                "NORMALIZATION_INCLUSION_PRESENT_VALUE_MUST_NOT_COLLAPSE_TO_MISSING_EMPTY_MALFORMED"
            )
    required = _required_exclusion_codes(
        presence_state=presence,
        observation_semantic_class=semantic,
        account_scope_status=account_scope,
        currency_status=currency_status,
        unit_status=unit_status,
        freshness_status=freshness,
        provenance_status=provenance_status,
        ambiguity_status=ambiguity,
        contradiction_status=contradiction,
        mapping_status=mapping_status,
        account_scope_unproven=account_scope == COMPATIBILITY_UNPROVEN,
        currency_unproven=currency_status == COMPATIBILITY_UNPROVEN,
        unit_unproven=unit_status == COMPATIBILITY_UNPROVEN,
    )
    if tuple(sorted(declared_codes)) != required:
        raise NormalizationInclusionAdjudicationContractError(
            "NORMALIZATION_INCLUSION_EXCLUSION_REASON_CODES_MISMATCH"
        )
    if required:
        if inclusion != INCLUSION_STATUS_EXCLUDED:
            raise NormalizationInclusionAdjudicationContractError(
                "NORMALIZATION_INCLUSION_EXCLUSION_REASONS_REQUIRE_EXCLUDED"
            )
    elif inclusion == INCLUSION_STATUS_EXCLUDED:
        raise NormalizationInclusionAdjudicationContractError(
            "NORMALIZATION_INCLUSION_EXCLUDED_REQUIRES_EXCLUSION_REASONS"
        )
    for field in _IDENTITY_SEMANTICS_FIELDS:
        if field == "requested_target_dimension_id":
            continue
        if _fold(str(getattr(adjudication, field))) == _fold(DIMENSION_ID):
            raise NormalizationInclusionAdjudicationContractError(
                f"NORMALIZATION_INCLUSION_MUST_NOT_CLAIM_EQUITY_DIMENSION:{field}"
            )
    canonical = adjudication.to_canonical_dict()
    expected_digest = compute_normalization_inclusion_provenance_digest_v1(canonical)
    digest = _require_non_empty_str(field="provenance_digest", raw=adjudication.provenance_digest)
    if _SHA256_HEX.fullmatch(digest) is None:
        raise NormalizationInclusionAdjudicationContractError(
            "NORMALIZATION_INCLUSION_PROVENANCE_DIGEST_NOT_SHA256"
        )
    if digest != expected_digest:
        raise NormalizationInclusionAdjudicationContractError(
            "NORMALIZATION_INCLUSION_PROVENANCE_DIGEST_MISMATCH"
        )


def build_normalization_inclusion_adjudication_v1(
    **fields: Any,
) -> NormalizationInclusionAdjudicationV1:
    """Fail-closed schema constructor. Explicit fields only. Not a mint."""

    normalized: dict[str, Any] = {}
    for canonical in NORMALIZATION_PROVENANCE_REQUIRED_FIELDS:
        if canonical not in fields:
            raise NormalizationInclusionAdjudicationContractError(
                f"NORMALIZATION_INCLUSION_FIELD_MISSING:{canonical}"
            )
        normalized[canonical] = fields[canonical]
    unexpected = set(fields) - set(NORMALIZATION_PROVENANCE_REQUIRED_FIELDS)
    if unexpected:
        raise NormalizationInclusionAdjudicationContractError(
            "NORMALIZATION_INCLUSION_UNEXPECTED_FIELD:" + ",".join(sorted(unexpected))
        )
    return NormalizationInclusionAdjudicationV1(**normalized)
