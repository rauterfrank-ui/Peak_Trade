"""Typed internal reconstruction contract schema.

Schema/contract only. Target dimension naming is not reconstruction proof.
Not a producer. Not a numeric equity calculation. Not a runtime value
binding. Not a LIVE_ACCOUNT_BOUND join. Construction of a schema instance
is not a productive reconstruction runtime instance.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping, Sequence, Tuple

from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    EQUITY_DIMENSION_BOUND,
    GOVERNED_PRODUCER_CREATED,
    INCLUSION_PROVEN,
    INTERNAL_RECONSTRUCTION_AUTHORITY_EFFECT,
    INTERNAL_RECONSTRUCTION_CREATED,
    INTERNAL_RECONSTRUCTION_PROVEN,
    INTERNAL_RECONSTRUCTION_RUNTIME_INSTANCE_PRESENT,
    INTERNAL_RECONSTRUCTION_SCHEMA_PRESENT,
    LIVE_RESTART_RECONSTRUCTED,
    MAPPED_TO_RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING,
    RECONCILIATION_CONTRACT_CREATED,
    RECONSTRUCTION_ALGEBRA_COMPLETE,
    RECONSTRUCTION_ALGEBRA_SCHEMA_PRESENT,
    RECONSTRUCTION_PROVENANCE_REQUIRED_FIELDS,
    SEMANTIC_MAPPING_PROVEN,
    SOURCE_OBJECT_PRESENT,
    SOURCE_SELECTED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.venue_witness_observation_v1 import (
    PRESENCE_EMPTY,
    PRESENCE_MALFORMED,
    PRESENCE_MISSING,
    PRESENCE_NONZERO,
    PRESENCE_ZERO,
)

SCHEMA_CLASS = "INTERNAL_RECONSTRUCTION_CONTRACT_V1"
DIMENSION_ID = "RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING"
RECONSTRUCTION_SEMANTIC_CLASS = "COMPOSITIONAL_INTERNAL_RECONSTRUCTION_V1"
RECONSTRUCTION_SEMANTIC_CLASS_VERSION = "v1"
REQUIRED_SETTLEMENT_CURRENCY = "USDC"
OBSERVATION_VS_AUTHORITY_CLASS_OBSERVATION = "OBSERVATION"
OBSERVATION_VS_AUTHORITY_CLASS_AUTHORITY = "AUTHORITY"
RECONSTRUCTION_ELIGIBILITY_INELIGIBLE = "INELIGIBLE"
RECONSTRUCTION_ELIGIBILITY_ELIGIBLE = "ELIGIBLE"
RECONSTRUCTION_PROVEN_STATUS_UNPROVEN = "UNPROVEN"
RECONSTRUCTION_PROVEN_STATUS_PROVEN = "PROVEN"
RECONSTRUCTED_VALUE_STATE_NOT_COMPUTED = "NOT_COMPUTED"
RECONSTRUCTED_VALUE_STATE_COMPUTED = "COMPUTED"
ALGEBRA_STATUS_INCOMPLETE = "INCOMPLETE"
ALGEBRA_STATUS_COMPLETE = "COMPLETE"
ALGEBRA_REPRESENTATION = (
    "U02_U03_IN_EQUITY_BASE_ONLY_NO_SEPARATE_ADDEND;"
    "P01_REDUCTION_ONLY;"
    "U04_HOLD_ONCE;"
    "U05_LIABILITY_ONCE;"
    "U06_FEE_ONCE;"
    "ALGEBRA_COMPLETE=false"
)
COMPONENT_COMPLETENESS_INCOMPLETE = "INCOMPLETE"
COMPONENT_COMPLETENESS_UNPROVEN = "UNPROVEN"
COMPONENT_COMPLETENESS_COMPLETE = "COMPLETE"
COMPONENT_REQUIRED = "COMPONENT_REQUIRED"
COMPONENT_NOT_APPLICABLE = "COMPONENT_NOT_APPLICABLE"
COMPONENT_PRESENT = "COMPONENT_PRESENT"
COMPONENT_MISSING = "COMPONENT_MISSING"
COMPONENT_MALFORMED = "COMPONENT_MALFORMED"
COMPONENT_STALE = "COMPONENT_STALE"
COMPONENT_CONTRADICTORY = "COMPONENT_CONTRADICTORY"
PRESENCE_NOT_APPLICABLE = "NOT_APPLICABLE"
INCLUSION_IN_BASE_UNKNOWN = "UNKNOWN"
INCLUSION_IN_BASE = "IN_BASE"
INCLUSION_NOT_IN_BASE = "NOT_IN_BASE"
INCLUSION_SEPARATE_ADDEND_FORBIDDEN = "SEPARATE_ADDEND_FORBIDDEN"
INCLUSION_NOT_APPLICABLE = "NOT_APPLICABLE"
SAME_EPOCH_UNPROVEN = "SAME_EPOCH_UNPROVEN"
SAME_EPOCH_MISMATCH = "SAME_EPOCH_MISMATCH"
SAME_EPOCH_PROVEN = "SAME_EPOCH_PROVEN"
RESTART_UNPROVEN = "RESTART_UNPROVEN"
RESTART_INVALIDATED = "RESTART_INVALIDATED"
RESTART_CLEAR = "RESTART_CLEAR"
RESTART_PROVENANCE_UNBOUND = "UNBOUND"
RESTART_PROVENANCE_PRE_RESTART = "PRE_RESTART"
RESTART_PROVENANCE_POST_RESTART = "POST_RESTART"
FRESHNESS_UNPROVEN = "UNPROVEN"
FRESHNESS_STALE = "STALE"
FRESHNESS_EXPLICIT_TIMESTAMPS_NOT_COMPONENT_TTL = "EXPLICIT_TIMESTAMPS_NOT_COMPONENT_TTL_POLICY"
FRESHNESS_PROVEN = "PROVEN"
CONTRADICTION_NONE = "NO_CONTRADICTION"
CONTRADICTION_PRESENT = "CONTRADICTION_PRESENT"
COMPONENT_EQUITY_BASE = "EQUITY_BASE"
COMPONENT_REALIZED_PNL = "REALIZED_PNL"
COMPONENT_UNREALIZED_PNL_MTM = "UNREALIZED_PNL_MTM"
COMPONENT_PENDING_ORDER_RESERVATION = "PENDING_ORDER_RESERVATION"
COMPONENT_LIABILITY = "LIABILITY"
COMPONENT_FEE = "FEE"
COMPONENT_P01_HAIRCUT_RESERVE_DEPLETION = "P01_HAIRCUT_RESERVE_DEPLETION"
COMPONENT_SLIPPAGE = "SLIPPAGE"
REQUIRED_COMPONENT_CLASSES: Tuple[str, ...] = (
    COMPONENT_EQUITY_BASE,
    COMPONENT_REALIZED_PNL,
    COMPONENT_UNREALIZED_PNL_MTM,
    COMPONENT_PENDING_ORDER_RESERVATION,
    COMPONENT_LIABILITY,
    COMPONENT_FEE,
    COMPONENT_P01_HAIRCUT_RESERVE_DEPLETION,
)
NOT_APPLICABLE_COMPONENT_CLASSES: Tuple[str, ...] = (COMPONENT_SLIPPAGE,)
KNOWN_COMPONENT_CLASSES: Tuple[str, ...] = (
    REQUIRED_COMPONENT_CLASSES + NOT_APPLICABLE_COMPONENT_CLASSES
)
COMPONENT_TERM_VECTOR = (
    "P01_HAIRCUT_RESERVE_DEPLETION,"
    "U02_REALIZED_UNREALIZED_IN_EQUITY_BASE_ONLY_NO_SEPARATE_ADDEND,"
    "U03_OPEN_POSITION_MTM_IN_EQUITY_BASE,"
    "U04_PENDING_ORDER_RESERVATION,"
    "U05_LIABILITY,"
    "U06_FEE"
)
NO_SEPARATE_ADDEND_CLASSES: Tuple[str, ...] = (
    COMPONENT_REALIZED_PNL,
    COMPONENT_UNREALIZED_PNL_MTM,
)
COMPONENT_REQUIREMENT_STATES: Tuple[str, ...] = (
    COMPONENT_REQUIRED,
    COMPONENT_NOT_APPLICABLE,
)
COMPONENT_STATES: Tuple[str, ...] = (
    COMPONENT_PRESENT,
    COMPONENT_MISSING,
    COMPONENT_MALFORMED,
    COMPONENT_STALE,
    COMPONENT_CONTRADICTORY,
    COMPONENT_NOT_APPLICABLE,
)
PRESENCE_STATES: Tuple[str, ...] = (
    PRESENCE_MISSING,
    PRESENCE_EMPTY,
    PRESENCE_ZERO,
    PRESENCE_NONZERO,
    PRESENCE_MALFORMED,
    PRESENCE_NOT_APPLICABLE,
)
INCLUSION_IN_BASE_STATES: Tuple[str, ...] = (
    INCLUSION_IN_BASE_UNKNOWN,
    INCLUSION_IN_BASE,
    INCLUSION_NOT_IN_BASE,
    INCLUSION_SEPARATE_ADDEND_FORBIDDEN,
    INCLUSION_NOT_APPLICABLE,
)
INVALID_REQUIRED_COMPONENT_STATES: Tuple[str, ...] = (
    COMPONENT_MISSING,
    COMPONENT_MALFORMED,
    COMPONENT_STALE,
    COMPONENT_CONTRADICTORY,
)
UNPROVEN_FRESHNESS_STATES: Tuple[str, ...] = (
    FRESHNESS_UNPROVEN,
    FRESHNESS_STALE,
    FRESHNESS_EXPLICIT_TIMESTAMPS_NOT_COMPONENT_TTL,
)
_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")
_SCIENTIFIC_NOTATION = re.compile(r"^[+-]?(?:\d+\.?\d*|\.\d+)[eE][+-]?\d+$")
_FORBIDDEN_FALLBACK_MARKERS: Tuple[str, ...] = ("|", " or ", ",", ";")
_FORBIDDEN_VENUE_FIELD_MARKERS: Tuple[str, ...] = (
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
_BARE_FORBIDDEN_TOKENS: Tuple[str, ...] = ("eq", "upl")
_FORBIDDEN_OBJECT_TOKENS: Tuple[str, ...] = (
    "accountingportfoliostatev1",
    "ledgersnapshot",
    "equitybyccy",
    "simulatedportfoliostatev1",
)
_COMPONENT_VECTOR_FIELDS: Tuple[str, ...] = (
    "component_semantic_class",
    "component_requirement_status",
    "component_state",
    "presence_state",
    "component_value_representation",
    "component_currency",
    "component_unit",
    "valuation_mark_ref",
    "provenance_ref",
    "observed_at_as_of",
    "inclusion_in_equity_base_status",
)
_IDENTITY_SEMANTICS_FIELDS: Tuple[str, ...] = (
    "target_semantic_dimension_id",
    "reconstruction_semantic_class",
    "reconstruction_eligibility",
    "reconstruction_proven_status",
    "reconstructed_value_state",
    "reconstruction_algebra_status",
    "internal_reconstruction_authority_effect",
    "observation_vs_authority_class",
)


class InternalReconstructionContractError(ValueError):
    """Fail-closed internal reconstruction contract violation."""


def _fold(value: str) -> str:
    return str(value or "").strip().lower().replace("_", "").replace("-", "")


def _require_non_empty_str(*, field: str, raw: Any) -> str:
    if raw is None:
        raise InternalReconstructionContractError(f"INTERNAL_RECONSTRUCTION_FIELD_MISSING:{field}")
    if not isinstance(raw, str):
        raise InternalReconstructionContractError(
            f"INTERNAL_RECONSTRUCTION_FIELD_NOT_STRING:{field}"
        )
    text = raw.strip()
    if text == "" or text != raw:
        raise InternalReconstructionContractError(f"INTERNAL_RECONSTRUCTION_FIELD_MISSING:{field}")
    return text


def _require_str_allow_empty(*, field: str, raw: Any) -> str:
    if raw is None:
        raise InternalReconstructionContractError(f"INTERNAL_RECONSTRUCTION_FIELD_MISSING:{field}")
    if not isinstance(raw, str):
        raise InternalReconstructionContractError(
            f"INTERNAL_RECONSTRUCTION_FIELD_NOT_STRING:{field}"
        )
    if raw.strip() != raw:
        raise InternalReconstructionContractError(
            f"INTERNAL_RECONSTRUCTION_FIELD_NOT_EXACT:{field}"
        )
    return raw


def _reject_fallback_chain(*, field: str, raw: str) -> None:
    lowered = raw.lower()
    for marker in _FORBIDDEN_FALLBACK_MARKERS:
        if marker in lowered:
            raise InternalReconstructionContractError(
                f"INTERNAL_RECONSTRUCTION_FALLBACK_CHAIN_FORBIDDEN:{field}"
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
        raise InternalReconstructionContractError(
            f"INTERNAL_RECONSTRUCTION_FORBIDDEN_AUTHORITY_FIELD:{field}"
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


def encode_inclusion_vector_v1(components: Sequence["ReconstructionComponentV1"]) -> str:
    payload = [component.to_canonical_dict() for component in components]
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_internal_reconstruction_provenance_digest_v1(
    canonical: Mapping[str, str],
) -> str:
    payload = {
        key: canonical[key]
        for key in RECONSTRUCTION_PROVENANCE_REQUIRED_FIELDS
        if key != "provenance_digest"
    }
    return _sha256_hex(_canonical_json(payload))


def attach_internal_reconstruction_provenance_digest_v1(
    fields: Mapping[str, Any],
) -> dict[str, Any]:
    """Attach the deterministic digest. Does not reconstruct, map, or select."""

    canonical: dict[str, str] = {}
    for canonical_name in RECONSTRUCTION_PROVENANCE_REQUIRED_FIELDS:
        if canonical_name == "provenance_digest":
            continue
        if canonical_name not in fields:
            raise InternalReconstructionContractError(
                f"INTERNAL_RECONSTRUCTION_FIELD_MISSING:{canonical_name}"
            )
        raw = fields[canonical_name]
        canonical[canonical_name] = "" if raw is None else str(raw)
    attached = dict(fields)
    attached["provenance_digest"] = compute_internal_reconstruction_provenance_digest_v1(canonical)
    return attached


@dataclass(frozen=True)
class ReconstructionComponentV1:
    """Typed reconstruction component slot. Not a numeric equity term mint."""

    component_semantic_class: str
    component_requirement_status: str
    component_state: str
    presence_state: str
    component_value_representation: str
    component_currency: str
    component_unit: str
    valuation_mark_ref: str
    provenance_ref: str
    observed_at_as_of: str
    inclusion_in_equity_base_status: str

    def __post_init__(self) -> None:
        _validate_reconstruction_component_v1(self)

    def to_canonical_dict(self) -> dict[str, str]:
        return {
            "component_semantic_class": self.component_semantic_class,
            "component_requirement_status": self.component_requirement_status,
            "component_state": self.component_state,
            "presence_state": self.presence_state,
            "component_value_representation": self.component_value_representation,
            "component_currency": self.component_currency,
            "component_unit": self.component_unit,
            "valuation_mark_ref": self.valuation_mark_ref,
            "provenance_ref": self.provenance_ref,
            "observed_at_as_of": self.observed_at_as_of,
            "inclusion_in_equity_base_status": self.inclusion_in_equity_base_status,
        }


def build_reconstruction_component_v1(
    **fields: str,
) -> ReconstructionComponentV1:
    missing = [name for name in _COMPONENT_VECTOR_FIELDS if name not in fields]
    if missing:
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_COMPONENT_FIELD_MISSING:" + ",".join(missing)
        )
    extra = [name for name in fields if name not in _COMPONENT_VECTOR_FIELDS]
    if extra:
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_COMPONENT_FIELD_UNKNOWN:" + ",".join(sorted(extra))
        )
    return ReconstructionComponentV1(**{name: fields[name] for name in _COMPONENT_VECTOR_FIELDS})


def _validate_presence_state(*, presence_state: str, raw_value: str) -> None:
    parsed = _parse_simple_decimal(raw_value)
    if presence_state in {PRESENCE_MISSING, PRESENCE_EMPTY, PRESENCE_NOT_APPLICABLE}:
        if raw_value != "":
            raise InternalReconstructionContractError(
                f"INTERNAL_RECONSTRUCTION_EMPTY_PRESENCE_MUST_HAVE_EMPTY_RAW:{presence_state}"
            )
        return
    if presence_state == PRESENCE_ZERO:
        if parsed is None or parsed != Decimal("0"):
            raise InternalReconstructionContractError(
                "INTERNAL_RECONSTRUCTION_PRESENT_ZERO_REQUIRES_ZERO_DECIMAL"
            )
        return
    if presence_state == PRESENCE_NONZERO:
        if parsed is None or parsed == Decimal("0"):
            raise InternalReconstructionContractError(
                "INTERNAL_RECONSTRUCTION_PRESENT_NONZERO_REQUIRES_NONZERO_DECIMAL"
            )
        return
    if presence_state == PRESENCE_MALFORMED:
        if raw_value == "" or parsed is not None:
            raise InternalReconstructionContractError(
                "INTERNAL_RECONSTRUCTION_MALFORMED_REQUIRES_NON_DECIMAL_RAW"
            )
        return
    raise InternalReconstructionContractError(
        f"INTERNAL_RECONSTRUCTION_PRESENCE_STATE_UNKNOWN:{presence_state}"
    )


def _validate_reconstruction_component_v1(component: ReconstructionComponentV1) -> None:
    component_class = _require_non_empty_str(
        field="component_semantic_class", raw=component.component_semantic_class
    )
    if component_class not in KNOWN_COMPONENT_CLASSES:
        raise InternalReconstructionContractError(
            f"INTERNAL_RECONSTRUCTION_COMPONENT_CLASS_UNKNOWN:{component_class}"
        )
    requirement = _require_non_empty_str(
        field="component_requirement_status", raw=component.component_requirement_status
    )
    if requirement not in COMPONENT_REQUIREMENT_STATES:
        raise InternalReconstructionContractError(
            f"INTERNAL_RECONSTRUCTION_COMPONENT_REQUIREMENT_UNKNOWN:{requirement}"
        )
    expected_requirement = (
        COMPONENT_NOT_APPLICABLE
        if component_class in NOT_APPLICABLE_COMPONENT_CLASSES
        else COMPONENT_REQUIRED
    )
    if requirement != expected_requirement:
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_COMPONENT_REQUIREMENT_MISMATCH:"
            f"{component_class}:{requirement}"
        )
    state = _require_non_empty_str(field="component_state", raw=component.component_state)
    if state not in COMPONENT_STATES:
        raise InternalReconstructionContractError(
            f"INTERNAL_RECONSTRUCTION_COMPONENT_STATE_UNKNOWN:{state}"
        )
    presence = _require_non_empty_str(field="presence_state", raw=component.presence_state)
    if presence not in PRESENCE_STATES:
        raise InternalReconstructionContractError(
            f"INTERNAL_RECONSTRUCTION_COMPONENT_PRESENCE_UNKNOWN:{presence}"
        )
    raw_value = _require_str_allow_empty(
        field="component_value_representation",
        raw=component.component_value_representation,
    )
    _validate_presence_state(presence_state=presence, raw_value=raw_value)
    inclusion = _require_non_empty_str(
        field="inclusion_in_equity_base_status",
        raw=component.inclusion_in_equity_base_status,
    )
    if inclusion not in INCLUSION_IN_BASE_STATES:
        raise InternalReconstructionContractError(
            f"INTERNAL_RECONSTRUCTION_INCLUSION_IN_BASE_UNKNOWN:{inclusion}"
        )
    if requirement == COMPONENT_NOT_APPLICABLE:
        if state != COMPONENT_NOT_APPLICABLE or presence != PRESENCE_NOT_APPLICABLE:
            raise InternalReconstructionContractError(
                "INTERNAL_RECONSTRUCTION_NOT_APPLICABLE_COMPONENT_STATE_MISMATCH"
            )
        if inclusion != INCLUSION_NOT_APPLICABLE:
            raise InternalReconstructionContractError(
                "INTERNAL_RECONSTRUCTION_NOT_APPLICABLE_INCLUSION_MISMATCH"
            )
    elif state == COMPONENT_MISSING and presence not in {
        PRESENCE_MISSING,
        PRESENCE_EMPTY,
    }:
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_MISSING_COMPONENT_PRESENCE_MISMATCH"
        )
    elif state == COMPONENT_MALFORMED and presence != PRESENCE_MALFORMED:
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_MALFORMED_COMPONENT_PRESENCE_MISMATCH"
        )
    elif state == COMPONENT_PRESENT and presence not in {PRESENCE_ZERO, PRESENCE_NONZERO}:
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_PRESENT_COMPONENT_PRESENCE_MISMATCH"
        )
    elif state == COMPONENT_STALE and presence not in {PRESENCE_ZERO, PRESENCE_NONZERO}:
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_STALE_COMPONENT_PRESENCE_MISMATCH"
        )
    elif state == COMPONENT_NOT_APPLICABLE:
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_REQUIRED_COMPONENT_NOT_APPLICABLE_FORBIDDEN"
        )
    if presence == PRESENCE_MISSING and raw_value == "0":
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_MISSING_COMPONENT_ZERO_COERCION_FORBIDDEN"
        )
    if presence == PRESENCE_MALFORMED and _parse_simple_decimal(raw_value) == Decimal("0"):
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_MALFORMED_COMPONENT_ZERO_COERCION_FORBIDDEN"
        )
    currency = _require_non_empty_str(field="component_currency", raw=component.component_currency)
    _reject_fallback_chain(field="component_currency", raw=currency)
    if currency == "USD":
        raise InternalReconstructionContractError("INTERNAL_RECONSTRUCTION_USD_IS_NOT_USDC")
    _require_non_empty_str(field="component_unit", raw=component.component_unit)
    valuation_mark_ref = _require_str_allow_empty(
        field="valuation_mark_ref", raw=component.valuation_mark_ref
    )
    provenance_ref = _require_str_allow_empty(field="provenance_ref", raw=component.provenance_ref)
    observed_at = _require_str_allow_empty(
        field="observed_at_as_of", raw=component.observed_at_as_of
    )
    if (
        component_class in NO_SEPARATE_ADDEND_CLASSES
        and inclusion == INCLUSION_SEPARATE_ADDEND_FORBIDDEN
    ):
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_SEPARATE_ADDEND_FORBIDDEN"
        )
    if state == COMPONENT_MISSING:
        if provenance_ref != "":
            raise InternalReconstructionContractError(
                "INTERNAL_RECONSTRUCTION_MISSING_COMPONENT_MUST_NOT_CARRY_PROVENANCE"
            )
        if observed_at != "":
            raise InternalReconstructionContractError(
                "INTERNAL_RECONSTRUCTION_MISSING_COMPONENT_MUST_NOT_CARRY_TIMESTAMP"
            )
    if state == COMPONENT_STALE and observed_at == "":
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_STALE_COMPONENT_REQUIRES_TIMESTAMP_EVIDENCE"
        )
    if component_class == COMPONENT_UNREALIZED_PNL_MTM and state == COMPONENT_PRESENT:
        if valuation_mark_ref == "":
            raise InternalReconstructionContractError(
                "INTERNAL_RECONSTRUCTION_MTM_PRESENT_REQUIRES_MARK_REF"
            )
    _reject_forbidden_authority_token(field="component_semantic_class", raw=component_class)
    _reject_forbidden_authority_token(field="provenance_ref", raw=provenance_ref)
    _reject_forbidden_authority_token(field="valuation_mark_ref", raw=valuation_mark_ref)


def _validate_component_set(
    components: Tuple[ReconstructionComponentV1, ...],
) -> None:
    if not components:
        raise InternalReconstructionContractError("INTERNAL_RECONSTRUCTION_COMPONENT_SET_EMPTY")
    classes = tuple(component.component_semantic_class for component in components)
    if len(set(classes)) != len(classes):
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_COMPONENT_CLASS_DUPLICATE"
        )
    if tuple(sorted(classes)) != classes:
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_COMPONENT_SET_NOT_SORTED"
        )
    missing_required = [name for name in REQUIRED_COMPONENT_CLASSES if name not in classes]
    if missing_required:
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_REQUIRED_COMPONENT_SLOT_MISSING:" + ",".join(missing_required)
        )
    missing_optional_slots = [
        name for name in NOT_APPLICABLE_COMPONENT_CLASSES if name not in classes
    ]
    if missing_optional_slots:
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_NOT_APPLICABLE_COMPONENT_SLOT_OMITTED:"
            + ",".join(missing_optional_slots)
        )
    unknown = [name for name in classes if name not in KNOWN_COMPONENT_CLASSES]
    if unknown:
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_COMPONENT_CLASS_UNKNOWN:" + ",".join(unknown)
        )


@dataclass(frozen=True)
class InternalReconstructionContractV1:
    """Typed immutable internal reconstruction contract. Schema only."""

    reconstruction_id: str
    source_normalization_adjudication_id: str
    bound_account_identity: str
    bound_venue_identity: str
    rest_host: str
    bound_td_mode: str
    account_mode: str
    currency_domain: str
    reconstruction_epoch: str
    target_semantic_dimension_id: str
    reconstruction_semantic_class: str
    reconstruction_semantic_class_version: str
    inclusion_vector: str
    component_term_vector: str
    component_completeness: str
    reconstruction_algebra_status: str
    reconstruction_algebra_representation: str
    reconstructed_value_state: str
    reconstructed_value_representation: str
    contradiction_status: str
    same_epoch_status: str
    freshness_status: str
    freshness_evidence_ref: str
    restart_invalidation_status: str
    restart_provenance_class: str
    reconstruction_eligibility: str
    reconstruction_proven_status: str
    observation_vs_authority_class: str
    internal_reconstruction_authority_effect: str
    provenance_digest: str
    components: Tuple[ReconstructionComponentV1, ...]

    def __post_init__(self) -> None:
        _validate_internal_reconstruction_contract_v1(self)

    def to_canonical_dict(self) -> dict[str, str]:
        values = {
            "reconstruction_id": self.reconstruction_id,
            "source_normalization_adjudication_id": (self.source_normalization_adjudication_id),
            "bound_account_identity": self.bound_account_identity,
            "bound_venue_identity": self.bound_venue_identity,
            "rest_host": self.rest_host,
            "bound_td_mode": self.bound_td_mode,
            "account_mode": self.account_mode,
            "currency_domain": self.currency_domain,
            "reconstruction_epoch": self.reconstruction_epoch,
            "target_semantic_dimension_id": self.target_semantic_dimension_id,
            "reconstruction_semantic_class": self.reconstruction_semantic_class,
            "reconstruction_semantic_class_version": (self.reconstruction_semantic_class_version),
            "inclusion_vector": self.inclusion_vector,
            "component_term_vector": self.component_term_vector,
            "component_completeness": self.component_completeness,
            "reconstruction_algebra_status": self.reconstruction_algebra_status,
            "reconstruction_algebra_representation": (self.reconstruction_algebra_representation),
            "reconstructed_value_state": self.reconstructed_value_state,
            "reconstructed_value_representation": self.reconstructed_value_representation,
            "contradiction_status": self.contradiction_status,
            "same_epoch_status": self.same_epoch_status,
            "freshness_status": self.freshness_status,
            "freshness_evidence_ref": self.freshness_evidence_ref,
            "restart_invalidation_status": self.restart_invalidation_status,
            "restart_provenance_class": self.restart_provenance_class,
            "reconstruction_eligibility": self.reconstruction_eligibility,
            "reconstruction_proven_status": self.reconstruction_proven_status,
            "observation_vs_authority_class": self.observation_vs_authority_class,
            "internal_reconstruction_authority_effect": (
                self.internal_reconstruction_authority_effect
            ),
            "provenance_digest": self.provenance_digest,
        }
        return {key: values[key] for key in RECONSTRUCTION_PROVENANCE_REQUIRED_FIELDS}


def _required_fail_closed_reasons(
    *,
    components: Tuple[ReconstructionComponentV1, ...],
    contradiction_status: str,
    same_epoch_status: str,
    freshness_status: str,
    restart_invalidation_status: str,
    algebra_status: str,
) -> Tuple[str, ...]:
    reasons: list[str] = []
    for component in components:
        if component.component_requirement_status != COMPONENT_REQUIRED:
            continue
        if component.component_state == COMPONENT_MISSING:
            reasons.append("REQUIRED_COMPONENT_MISSING")
            if component.presence_state == PRESENCE_EMPTY:
                reasons.append("REQUIRED_COMPONENT_EMPTY")
        if component.component_state == COMPONENT_MALFORMED:
            reasons.append("REQUIRED_COMPONENT_MALFORMED")
        if component.component_state == COMPONENT_STALE:
            reasons.append("REQUIRED_COMPONENT_STALE")
        if component.component_state == COMPONENT_CONTRADICTORY:
            reasons.append("REQUIRED_COMPONENT_CONTRADICTORY")
        if component.inclusion_in_equity_base_status == INCLUSION_IN_BASE_UNKNOWN:
            reasons.append("REQUIRED_COMPONENT_INCLUSION_UNKNOWN")
        if component.component_state == COMPONENT_PRESENT and (
            component.provenance_ref == "" or component.observed_at_as_of == ""
        ):
            reasons.append("REQUIRED_COMPONENT_PROVENANCE_INSUFFICIENT")
    if contradiction_status == CONTRADICTION_PRESENT:
        reasons.append("CONTRADICTION_PRESENT")
    if same_epoch_status in {SAME_EPOCH_UNPROVEN, SAME_EPOCH_MISMATCH}:
        reasons.append("SAME_EPOCH_UNPROVEN")
    if freshness_status in UNPROVEN_FRESHNESS_STATES:
        reasons.append("FRESHNESS_UNPROVEN")
    if restart_invalidation_status in {RESTART_UNPROVEN, RESTART_INVALIDATED}:
        reasons.append("RESTART_INVALIDATED_OR_UNPROVEN")
    if algebra_status != ALGEBRA_STATUS_COMPLETE:
        reasons.append("RECONSTRUCTION_ALGEBRA_INCOMPLETE")
    return tuple(sorted(set(reasons)))


def _validate_internal_reconstruction_contract_v1(
    contract: InternalReconstructionContractV1,
) -> None:
    if INTERNAL_RECONSTRUCTION_SCHEMA_PRESENT is not True:
        raise InternalReconstructionContractError("INTERNAL_RECONSTRUCTION_SCHEMA_PRESENT_REQUIRED")
    if INTERNAL_RECONSTRUCTION_RUNTIME_INSTANCE_PRESENT is True:
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_RUNTIME_INSTANCE_FORBIDDEN"
        )
    if INTERNAL_RECONSTRUCTION_CREATED is True:
        raise InternalReconstructionContractError("INTERNAL_RECONSTRUCTION_CREATED_FORBIDDEN")
    if INTERNAL_RECONSTRUCTION_PROVEN is True:
        raise InternalReconstructionContractError("INTERNAL_RECONSTRUCTION_PROVEN_PIN_FORBIDDEN")
    if RECONSTRUCTION_ALGEBRA_SCHEMA_PRESENT is not True:
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_ALGEBRA_SCHEMA_PRESENT_REQUIRED"
        )
    if RECONSTRUCTION_ALGEBRA_COMPLETE is True:
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_ALGEBRA_COMPLETE_FORBIDDEN"
        )
    if SOURCE_SELECTED is True:
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_SOURCE_SELECTED_FORBIDDEN"
        )
    if SOURCE_OBJECT_PRESENT is True:
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_SOURCE_OBJECT_PRESENT_FORBIDDEN"
        )
    if GOVERNED_PRODUCER_CREATED is True:
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_GOVERNED_PRODUCER_CREATED_FORBIDDEN"
        )
    if RECONCILIATION_CONTRACT_CREATED is True:
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_RECONCILIATION_CONTRACT_CREATED_FORBIDDEN"
        )
    if SEMANTIC_MAPPING_PROVEN is True or INCLUSION_PROVEN is True:
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_MAPPING_OR_INCLUSION_PROVEN_FORBIDDEN"
        )
    if EQUITY_DIMENSION_BOUND is True:
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_EQUITY_DIMENSION_BOUND_FORBIDDEN"
        )
    if MAPPED_TO_RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING is True:
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_TARGET_DIMENSION_MAPPING_FORBIDDEN"
        )
    if LIVE_RESTART_RECONSTRUCTED is True:
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_LIVE_RESTART_RECONSTRUCTED_FORBIDDEN"
        )
    reconstruction_id = _require_non_empty_str(
        field="reconstruction_id", raw=contract.reconstruction_id
    )
    source_adjudication_id = _require_non_empty_str(
        field="source_normalization_adjudication_id",
        raw=contract.source_normalization_adjudication_id,
    )
    bound_account = _require_non_empty_str(
        field="bound_account_identity", raw=contract.bound_account_identity
    )
    bound_venue = _require_non_empty_str(
        field="bound_venue_identity", raw=contract.bound_venue_identity
    )
    rest_host = _require_non_empty_str(field="rest_host", raw=contract.rest_host)
    bound_td_mode = _require_non_empty_str(field="bound_td_mode", raw=contract.bound_td_mode)
    account_mode = _require_non_empty_str(field="account_mode", raw=contract.account_mode)
    currency_domain = _require_non_empty_str(field="currency_domain", raw=contract.currency_domain)
    reconstruction_epoch = _require_non_empty_str(
        field="reconstruction_epoch", raw=contract.reconstruction_epoch
    )
    target_dimension = _require_non_empty_str(
        field="target_semantic_dimension_id", raw=contract.target_semantic_dimension_id
    )
    semantic_class = _require_non_empty_str(
        field="reconstruction_semantic_class",
        raw=contract.reconstruction_semantic_class,
    )
    semantic_version = _require_non_empty_str(
        field="reconstruction_semantic_class_version",
        raw=contract.reconstruction_semantic_class_version,
    )
    inclusion_vector = _require_non_empty_str(
        field="inclusion_vector", raw=contract.inclusion_vector
    )
    component_term_vector = _require_non_empty_str(
        field="component_term_vector", raw=contract.component_term_vector
    )
    completeness = _require_non_empty_str(
        field="component_completeness", raw=contract.component_completeness
    )
    algebra_status = _require_non_empty_str(
        field="reconstruction_algebra_status",
        raw=contract.reconstruction_algebra_status,
    )
    algebra_representation = _require_non_empty_str(
        field="reconstruction_algebra_representation",
        raw=contract.reconstruction_algebra_representation,
    )
    reconstructed_value_state = _require_non_empty_str(
        field="reconstructed_value_state", raw=contract.reconstructed_value_state
    )
    reconstructed_value = _require_str_allow_empty(
        field="reconstructed_value_representation",
        raw=contract.reconstructed_value_representation,
    )
    contradiction_status = _require_non_empty_str(
        field="contradiction_status", raw=contract.contradiction_status
    )
    same_epoch_status = _require_non_empty_str(
        field="same_epoch_status", raw=contract.same_epoch_status
    )
    freshness_status = _require_non_empty_str(
        field="freshness_status", raw=contract.freshness_status
    )
    freshness_ref = _require_non_empty_str(
        field="freshness_evidence_ref", raw=contract.freshness_evidence_ref
    )
    restart_status = _require_non_empty_str(
        field="restart_invalidation_status", raw=contract.restart_invalidation_status
    )
    restart_provenance = _require_non_empty_str(
        field="restart_provenance_class", raw=contract.restart_provenance_class
    )
    eligibility = _require_non_empty_str(
        field="reconstruction_eligibility", raw=contract.reconstruction_eligibility
    )
    proven_status = _require_non_empty_str(
        field="reconstruction_proven_status", raw=contract.reconstruction_proven_status
    )
    observation_class = _require_non_empty_str(
        field="observation_vs_authority_class",
        raw=contract.observation_vs_authority_class,
    )
    effect = _require_non_empty_str(
        field="internal_reconstruction_authority_effect",
        raw=contract.internal_reconstruction_authority_effect,
    )
    digest = _require_non_empty_str(field="provenance_digest", raw=contract.provenance_digest)
    if not isinstance(contract.components, tuple) or not contract.components:
        raise InternalReconstructionContractError("INTERNAL_RECONSTRUCTION_COMPONENTS_REQUIRED")
    if any(
        not isinstance(component, ReconstructionComponentV1) for component in contract.components
    ):
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_COMPONENTS_MUST_BE_TYPED"
        )
    _validate_component_set(contract.components)
    expected_vector = encode_inclusion_vector_v1(contract.components)
    if inclusion_vector != expected_vector:
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_INCLUSION_VECTOR_MISMATCH"
        )
    if component_term_vector != COMPONENT_TERM_VECTOR:
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_COMPONENT_TERM_VECTOR_MISMATCH"
        )
    for field, raw in (
        ("reconstruction_id", reconstruction_id),
        ("source_normalization_adjudication_id", source_adjudication_id),
        ("bound_account_identity", bound_account),
        ("bound_venue_identity", bound_venue),
        ("rest_host", rest_host),
        ("bound_td_mode", bound_td_mode),
        ("reconstruction_epoch", reconstruction_epoch),
        ("freshness_evidence_ref", freshness_ref),
    ):
        _reject_fallback_chain(field=field, raw=raw)
        _reject_forbidden_authority_token(field=field, raw=raw)
    if account_mode not in {"UNPROVEN", "cross", "isolated"}:
        raise InternalReconstructionContractError(
            f"INTERNAL_RECONSTRUCTION_ACCOUNT_MODE_UNKNOWN:{account_mode}"
        )
    if currency_domain != REQUIRED_SETTLEMENT_CURRENCY:
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_CURRENCY_DOMAIN_MUST_BE_USDC"
        )
    if target_dimension != DIMENSION_ID:
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_TARGET_DIMENSION_MISMATCH"
        )
    if semantic_class != RECONSTRUCTION_SEMANTIC_CLASS:
        raise InternalReconstructionContractError("INTERNAL_RECONSTRUCTION_SEMANTIC_CLASS_MISMATCH")
    if semantic_version != RECONSTRUCTION_SEMANTIC_CLASS_VERSION:
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_SEMANTIC_CLASS_VERSION_MISMATCH"
        )
    if completeness == COMPONENT_COMPLETENESS_COMPLETE:
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_COMPONENT_COMPLETENESS_COMPLETE_FORBIDDEN"
        )
    if completeness not in {
        COMPONENT_COMPLETENESS_INCOMPLETE,
        COMPONENT_COMPLETENESS_UNPROVEN,
    }:
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_COMPONENT_COMPLETENESS_MUST_REMAIN_UNPROVEN_OR_INCOMPLETE"
        )
    if algebra_status == ALGEBRA_STATUS_COMPLETE:
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_ALGEBRA_COMPLETE_STATUS_FORBIDDEN"
        )
    if algebra_status != ALGEBRA_STATUS_INCOMPLETE:
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_ALGEBRA_STATUS_MUST_REMAIN_INCOMPLETE"
        )
    if algebra_representation != ALGEBRA_REPRESENTATION:
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_ALGEBRA_REPRESENTATION_MISMATCH"
        )
    if reconstructed_value_state != RECONSTRUCTED_VALUE_STATE_NOT_COMPUTED:
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_VALUE_STATE_MUST_REMAIN_NOT_COMPUTED"
        )
    if reconstructed_value_state == RECONSTRUCTED_VALUE_STATE_COMPUTED:
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_VALUE_COMPUTED_FORBIDDEN"
        )
    if reconstructed_value != "":
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_VALUE_REPRESENTATION_MUST_REMAIN_EMPTY"
        )
    if contradiction_status not in {CONTRADICTION_NONE, CONTRADICTION_PRESENT}:
        raise InternalReconstructionContractError(
            f"INTERNAL_RECONSTRUCTION_CONTRADICTION_STATUS_UNKNOWN:{contradiction_status}"
        )
    if same_epoch_status == SAME_EPOCH_PROVEN:
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_SAME_EPOCH_PROVEN_FORBIDDEN"
        )
    if same_epoch_status not in {SAME_EPOCH_UNPROVEN, SAME_EPOCH_MISMATCH}:
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_SAME_EPOCH_STATUS_MUST_REMAIN_UNPROVEN_OR_MISMATCH"
        )
    if freshness_status not in UNPROVEN_FRESHNESS_STATES:
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_FRESHNESS_STATUS_MUST_REMAIN_UNPROVEN"
        )
    if freshness_status == FRESHNESS_PROVEN:
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_FRESHNESS_PROVEN_FORBIDDEN"
        )
    if restart_status == RESTART_CLEAR:
        raise InternalReconstructionContractError("INTERNAL_RECONSTRUCTION_RESTART_CLEAR_FORBIDDEN")
    if restart_status not in {RESTART_UNPROVEN, RESTART_INVALIDATED}:
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_RESTART_STATUS_MUST_REMAIN_UNPROVEN_OR_INVALIDATED"
        )
    if restart_provenance not in {
        RESTART_PROVENANCE_UNBOUND,
        RESTART_PROVENANCE_PRE_RESTART,
        RESTART_PROVENANCE_POST_RESTART,
    }:
        raise InternalReconstructionContractError(
            f"INTERNAL_RECONSTRUCTION_RESTART_PROVENANCE_UNKNOWN:{restart_provenance}"
        )
    if eligibility == RECONSTRUCTION_ELIGIBILITY_ELIGIBLE:
        raise InternalReconstructionContractError("INTERNAL_RECONSTRUCTION_ELIGIBLE_FORBIDDEN")
    if eligibility != RECONSTRUCTION_ELIGIBILITY_INELIGIBLE:
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_ELIGIBILITY_MUST_REMAIN_INELIGIBLE"
        )
    if proven_status == RECONSTRUCTION_PROVEN_STATUS_PROVEN:
        raise InternalReconstructionContractError("INTERNAL_RECONSTRUCTION_PROVEN_FORBIDDEN")
    if proven_status != RECONSTRUCTION_PROVEN_STATUS_UNPROVEN:
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_PROVEN_STATUS_MUST_REMAIN_UNPROVEN"
        )
    if observation_class != OBSERVATION_VS_AUTHORITY_CLASS_OBSERVATION:
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_OBSERVATION_VS_AUTHORITY_MUST_REMAIN_OBSERVATION"
        )
    if observation_class == OBSERVATION_VS_AUTHORITY_CLASS_AUTHORITY:
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_AUTHORITY_CLASS_FORBIDDEN"
        )
    if effect != INTERNAL_RECONSTRUCTION_AUTHORITY_EFFECT or effect != "NONE":
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_AUTHORITY_EFFECT_MUST_REMAIN_NONE"
        )
    fail_closed_reasons = _required_fail_closed_reasons(
        components=contract.components,
        contradiction_status=contradiction_status,
        same_epoch_status=same_epoch_status,
        freshness_status=freshness_status,
        restart_invalidation_status=restart_status,
        algebra_status=algebra_status,
    )
    if not fail_closed_reasons:
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_FAIL_CLOSED_REASONS_REQUIRED"
        )
    if completeness == COMPONENT_COMPLETENESS_INCOMPLETE and not fail_closed_reasons:
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_INCOMPLETE_REQUIRES_FAIL_CLOSED_REASON"
        )
    identity_fields = {
        "reconstruction_id": reconstruction_id,
        "source_normalization_adjudication_id": source_adjudication_id,
        "bound_account_identity": bound_account,
        "target_semantic_dimension_id": target_dimension,
        "reconstruction_semantic_class": semantic_class,
        "reconstruction_eligibility": eligibility,
        "reconstruction_proven_status": proven_status,
        "reconstructed_value_state": reconstructed_value_state,
        "reconstruction_algebra_status": algebra_status,
        "internal_reconstruction_authority_effect": effect,
        "observation_vs_authority_class": observation_class,
    }
    for field in _IDENTITY_SEMANTICS_FIELDS:
        _reject_forbidden_authority_token(field=field, raw=identity_fields[field])
    canonical = contract.to_canonical_dict()
    expected_digest = compute_internal_reconstruction_provenance_digest_v1(canonical)
    if not _SHA256_HEX.fullmatch(digest):
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_PROVENANCE_DIGEST_NOT_SHA256"
        )
    if digest != expected_digest:
        raise InternalReconstructionContractError(
            "INTERNAL_RECONSTRUCTION_PROVENANCE_DIGEST_MISMATCH"
        )


def build_internal_reconstruction_contract_v1(
    **fields: Any,
) -> InternalReconstructionContractV1:
    """Construct the typed reconstruction contract. Does not reconstruct equity."""

    components_raw = fields.get("components")
    if not isinstance(components_raw, tuple) or not components_raw:
        raise InternalReconstructionContractError("INTERNAL_RECONSTRUCTION_COMPONENTS_REQUIRED")
    components: list[ReconstructionComponentV1] = []
    for item in components_raw:
        if isinstance(item, ReconstructionComponentV1):
            components.append(item)
        elif isinstance(item, Mapping):
            components.append(build_reconstruction_component_v1(**dict(item)))
        else:
            raise InternalReconstructionContractError(
                "INTERNAL_RECONSTRUCTION_COMPONENTS_MUST_BE_TYPED"
            )
    typed_components = tuple(components)
    payload = dict(fields)
    components_for_vector = typed_components
    payload["components"] = typed_components
    if "inclusion_vector" not in payload:
        payload["inclusion_vector"] = encode_inclusion_vector_v1(components_for_vector)
    attached = attach_internal_reconstruction_provenance_digest_v1(
        {key: value for key, value in payload.items() if key != "components"}
    )
    attached["components"] = typed_components
    return InternalReconstructionContractV1(
        reconstruction_id=attached["reconstruction_id"],
        source_normalization_adjudication_id=attached["source_normalization_adjudication_id"],
        bound_account_identity=attached["bound_account_identity"],
        bound_venue_identity=attached["bound_venue_identity"],
        rest_host=attached["rest_host"],
        bound_td_mode=attached["bound_td_mode"],
        account_mode=attached["account_mode"],
        currency_domain=attached["currency_domain"],
        reconstruction_epoch=attached["reconstruction_epoch"],
        target_semantic_dimension_id=attached["target_semantic_dimension_id"],
        reconstruction_semantic_class=attached["reconstruction_semantic_class"],
        reconstruction_semantic_class_version=attached["reconstruction_semantic_class_version"],
        inclusion_vector=attached["inclusion_vector"],
        component_term_vector=attached["component_term_vector"],
        component_completeness=attached["component_completeness"],
        reconstruction_algebra_status=attached["reconstruction_algebra_status"],
        reconstruction_algebra_representation=attached["reconstruction_algebra_representation"],
        reconstructed_value_state=attached["reconstructed_value_state"],
        reconstructed_value_representation=attached["reconstructed_value_representation"],
        contradiction_status=attached["contradiction_status"],
        same_epoch_status=attached["same_epoch_status"],
        freshness_status=attached["freshness_status"],
        freshness_evidence_ref=attached["freshness_evidence_ref"],
        restart_invalidation_status=attached["restart_invalidation_status"],
        restart_provenance_class=attached["restart_provenance_class"],
        reconstruction_eligibility=attached["reconstruction_eligibility"],
        reconstruction_proven_status=attached["reconstruction_proven_status"],
        observation_vs_authority_class=attached["observation_vs_authority_class"],
        internal_reconstruction_authority_effect=attached[
            "internal_reconstruction_authority_effect"
        ],
        provenance_digest=attached["provenance_digest"],
        components=typed_components,
    )
