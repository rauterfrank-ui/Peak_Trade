"""Typed Trading-Account venue-witness observation contract.

Schema/contract only. Observation is not authority. Not a source mapping.
Not a producer. Not a runtime value binding. Not a LIVE_ACCOUNT_BOUND join.
Construction of a schema instance is not source selection and is not a
productive runtime witness instance.

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
    GOVERNED_PRODUCER_CREATED,
    MAPPED_TO_RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING,
    OBSERVATION_AUTHORITY_EFFECT,
    SOURCE_OBJECT_PRESENT,
    SOURCE_SELECTED,
    VENUE_WITNESS_RUNTIME_INSTANCE_PRESENT,
    VENUE_WITNESS_SCHEMA_PRESENT,
    VENUE_WITNESS_SELECTED,
    WITNESS_PROVENANCE_REQUIRED_FIELDS,
)

SCHEMA_CLASS = "VENUE_WITNESS_OBSERVATION_V1"
DIMENSION_ID = "RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING"
OBSERVATION_SEMANTIC_CLASS = "RAW_VENUE_OBSERVATION"
OBSERVATION_VS_AUTHORITY_CLASS_OBSERVATION = "OBSERVATION"
OBSERVATION_VS_AUTHORITY_CLASS_AUTHORITY = "AUTHORITY"
EQUITY_DIMENSION_BOUND_STATUS_UNBOUND = "UNBOUND"
MAPPING_STATUS_UNBOUND = "UNBOUND"
FRESHNESS_EVIDENCE_STATUS = "EXPLICIT_TIMESTAMPS_NOT_WITNESS_TTL_POLICY"
CLOCK_SOURCE_STATUS_UNBOUND = "UNBOUND"
METHOD_GET = "GET"
PRESENCE_MISSING = "MISSING"
PRESENCE_EMPTY = "EMPTY"
PRESENCE_ZERO = "PRESENT_ZERO"
PRESENCE_NONZERO = "PRESENT_NONZERO"
PRESENCE_MALFORMED = "MALFORMED"
PRESENCE_STATES: Tuple[str, ...] = (
    PRESENCE_MISSING,
    PRESENCE_EMPTY,
    PRESENCE_ZERO,
    PRESENCE_NONZERO,
    PRESENCE_MALFORMED,
)
RAW_PAYLOAD_RETAINED = "RAW_PAYLOAD_RETAINED"
PAYLOAD_DIGEST_ONLY = "PAYLOAD_DIGEST_ONLY"
RAW_PAYLOAD_STATES: Tuple[str, ...] = (
    RAW_PAYLOAD_RETAINED,
    PAYLOAD_DIGEST_ONLY,
)
CANONICAL_OBSERVED_AT_AS_OF = "observed_at/as_of"
PYTHON_OBSERVED_AT_AS_OF = "observed_at_as_of"
CANONICAL_TO_PYTHON_FIELD: Mapping[str, str] = {
    CANONICAL_OBSERVED_AT_AS_OF: PYTHON_OBSERVED_AT_AS_OF,
}
_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")
_SCIENTIFIC_NOTATION = re.compile(r"^[+-]?(?:\d+\.?\d*|\.\d+)[eE][+-]?\d+$")
_ISO_Z = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")
_PROVIDER_MS = re.compile(r"^[1-9]\d{0,17}$")
_FORBIDDEN_FALLBACK_MARKERS: Tuple[str, ...] = ("|", " or ", ",", ";")
_FORBIDDEN_HEADER_MARKERS: Tuple[str, ...] = (
    "authorization",
    "ok-access",
    "cookie",
    "api-key",
    "secret",
    "sign",
    "passphrase",
)
_IDENTITY_SEMANTICS_FIELDS: Tuple[str, ...] = (
    "observation_semantic_class",
    "observation_vs_authority_class",
    "observation_authority_effect",
    "equity_dimension_bound_status",
    "mapping_status",
    "freshness_evidence_status",
    "clock_source_status",
)


class VenueWitnessObservationContractError(ValueError):
    """Fail-closed venue-witness observation contract violation."""


def _fold(value: str) -> str:
    return str(value or "").strip().lower().replace("_", "").replace("-", "")


def _python_field_name(canonical: str) -> str:
    return CANONICAL_TO_PYTHON_FIELD.get(canonical, canonical)


def _require_non_empty_str(*, field: str, raw: Any) -> str:
    if raw is None:
        raise VenueWitnessObservationContractError(
            f"VENUE_WITNESS_OBSERVATION_FIELD_MISSING:{field}"
        )
    if not isinstance(raw, str):
        raise VenueWitnessObservationContractError(
            f"VENUE_WITNESS_OBSERVATION_FIELD_NOT_STRING:{field}"
        )
    text = raw.strip()
    if text == "" or text != raw:
        raise VenueWitnessObservationContractError(
            f"VENUE_WITNESS_OBSERVATION_FIELD_MISSING:{field}"
        )
    return text


def _require_str_allow_empty(*, field: str, raw: Any) -> str:
    if raw is None:
        raise VenueWitnessObservationContractError(
            f"VENUE_WITNESS_OBSERVATION_FIELD_MISSING:{field}"
        )
    if not isinstance(raw, str):
        raise VenueWitnessObservationContractError(
            f"VENUE_WITNESS_OBSERVATION_FIELD_NOT_STRING:{field}"
        )
    if raw.strip() != raw:
        raise VenueWitnessObservationContractError(
            f"VENUE_WITNESS_OBSERVATION_FIELD_NOT_EXACT:{field}"
        )
    return raw


def _require_iso_z(*, field: str, raw: Any) -> str:
    text = _require_non_empty_str(field=field, raw=raw)
    if _ISO_Z.fullmatch(text) is None:
        raise VenueWitnessObservationContractError(
            f"VENUE_WITNESS_OBSERVATION_TIMESTAMP_NOT_ISO_Z:{field}"
        )
    return text


def _reject_secret_text(*, field: str, raw: str) -> None:
    folded = raw.lower()
    for marker in _FORBIDDEN_HEADER_MARKERS:
        if marker in folded:
            raise VenueWitnessObservationContractError(
                f"VENUE_WITNESS_OBSERVATION_SECRET_TEXT_FORBIDDEN:{field}"
            )


def _reject_fallback_chain(*, field: str, raw: str) -> None:
    lowered = raw.lower()
    for marker in _FORBIDDEN_FALLBACK_MARKERS:
        if marker in lowered:
            raise VenueWitnessObservationContractError(
                f"VENUE_WITNESS_OBSERVATION_FALLBACK_CHAIN_FORBIDDEN:{field}"
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


def compute_venue_witness_provenance_digest_v1(canonical: Mapping[str, str]) -> str:
    payload = {
        key: canonical[key]
        for key in WITNESS_PROVENANCE_REQUIRED_FIELDS
        if key != "provenance_digest"
    }
    return _sha256_hex(_canonical_json(payload))


def attach_venue_witness_provenance_digest_v1(fields: Mapping[str, Any]) -> dict[str, Any]:
    """Attach the deterministic digest. Does not mint or map."""

    canonical: dict[str, str] = {}
    for canonical_name in WITNESS_PROVENANCE_REQUIRED_FIELDS:
        if canonical_name == "provenance_digest":
            continue
        python_name = _python_field_name(canonical_name)
        if canonical_name in fields:
            raw = fields[canonical_name]
        elif python_name in fields:
            raw = fields[python_name]
        else:
            raise VenueWitnessObservationContractError(
                f"VENUE_WITNESS_OBSERVATION_FIELD_MISSING:{canonical_name}"
            )
        canonical[canonical_name] = "" if raw is None else str(raw)
    attached = dict(fields)
    attached["provenance_digest"] = compute_venue_witness_provenance_digest_v1(canonical)
    return attached


@dataclass(frozen=True)
class TradingAccountVenueWitnessObservationV1:
    """Typed immutable Trading-Account venue witness. Observation only."""

    witness_id: str
    bound_account_identity: str
    bound_venue_identity: str
    rest_host: str
    bound_td_mode: str
    account_mode: str
    currency_domain: str
    endpoint: str
    method: str
    request_identity: str
    decision_epoch: str
    observed_at_as_of: str
    response_received_at: str
    provider_timestamp: str
    raw_field_path: str
    observation_semantic_class: str
    raw_value_representation: str
    presence_state: str
    raw_payload_state: str
    payload_digest: str
    raw_payload: str
    request_provenance: str
    response_provenance: str
    observation_vs_authority_class: str
    observation_authority_effect: str
    equity_dimension_bound_status: str
    mapping_status: str
    freshness_evidence_status: str
    clock_source_status: str
    provenance_digest: str

    def __post_init__(self) -> None:
        _validate_trading_account_venue_witness_observation_v1(self)

    def to_canonical_dict(self) -> dict[str, str]:
        values = {
            "witness_id": self.witness_id,
            "bound_account_identity": self.bound_account_identity,
            "bound_venue_identity": self.bound_venue_identity,
            "rest_host": self.rest_host,
            "bound_td_mode": self.bound_td_mode,
            "account_mode": self.account_mode,
            "currency_domain": self.currency_domain,
            "endpoint": self.endpoint,
            "method": self.method,
            "request_identity": self.request_identity,
            "decision_epoch": self.decision_epoch,
            CANONICAL_OBSERVED_AT_AS_OF: self.observed_at_as_of,
            "response_received_at": self.response_received_at,
            "provider_timestamp": self.provider_timestamp,
            "raw_field_path": self.raw_field_path,
            "observation_semantic_class": self.observation_semantic_class,
            "raw_value_representation": self.raw_value_representation,
            "presence_state": self.presence_state,
            "raw_payload_state": self.raw_payload_state,
            "payload_digest": self.payload_digest,
            "raw_payload": self.raw_payload,
            "request_provenance": self.request_provenance,
            "response_provenance": self.response_provenance,
            "observation_vs_authority_class": self.observation_vs_authority_class,
            "observation_authority_effect": self.observation_authority_effect,
            "equity_dimension_bound_status": self.equity_dimension_bound_status,
            "mapping_status": self.mapping_status,
            "freshness_evidence_status": self.freshness_evidence_status,
            "clock_source_status": self.clock_source_status,
            "provenance_digest": self.provenance_digest,
        }
        return {key: values[key] for key in WITNESS_PROVENANCE_REQUIRED_FIELDS}


def _validate_presence_state(*, presence_state: str, raw_value: str) -> None:
    parsed = _parse_simple_decimal(raw_value)
    if presence_state == PRESENCE_MISSING:
        if raw_value != "":
            raise VenueWitnessObservationContractError(
                "VENUE_WITNESS_OBSERVATION_MISSING_MUST_HAVE_EMPTY_RAW"
            )
        return
    if presence_state == PRESENCE_EMPTY:
        if raw_value != "":
            raise VenueWitnessObservationContractError(
                "VENUE_WITNESS_OBSERVATION_EMPTY_MUST_HAVE_EMPTY_RAW"
            )
        return
    if presence_state == PRESENCE_ZERO:
        if parsed is None or parsed != Decimal("0"):
            raise VenueWitnessObservationContractError(
                "VENUE_WITNESS_OBSERVATION_PRESENT_ZERO_REQUIRES_ZERO_DECIMAL"
            )
        return
    if presence_state == PRESENCE_NONZERO:
        if parsed is None or parsed == Decimal("0"):
            raise VenueWitnessObservationContractError(
                "VENUE_WITNESS_OBSERVATION_PRESENT_NONZERO_REQUIRES_NONZERO_DECIMAL"
            )
        return
    if presence_state == PRESENCE_MALFORMED:
        if raw_value == "" or parsed is not None:
            raise VenueWitnessObservationContractError(
                "VENUE_WITNESS_OBSERVATION_MALFORMED_REQUIRES_NON_DECIMAL_RAW"
            )
        return
    raise VenueWitnessObservationContractError(
        f"VENUE_WITNESS_OBSERVATION_PRESENCE_STATE_UNKNOWN:{presence_state}"
    )


def _validate_trading_account_venue_witness_observation_v1(
    witness: TradingAccountVenueWitnessObservationV1,
) -> None:
    if VENUE_WITNESS_SCHEMA_PRESENT is not True:
        raise VenueWitnessObservationContractError(
            "VENUE_WITNESS_OBSERVATION_SCHEMA_PRESENT_REQUIRED"
        )
    if VENUE_WITNESS_RUNTIME_INSTANCE_PRESENT is True:
        raise VenueWitnessObservationContractError(
            "VENUE_WITNESS_OBSERVATION_RUNTIME_INSTANCE_FORBIDDEN"
        )
    if VENUE_WITNESS_SELECTED is True:
        raise VenueWitnessObservationContractError("VENUE_WITNESS_OBSERVATION_SELECTION_FORBIDDEN")
    if SOURCE_OBJECT_PRESENT is True:
        raise VenueWitnessObservationContractError(
            "VENUE_WITNESS_OBSERVATION_RUNTIME_SOURCE_OBJECT_FORBIDDEN"
        )
    if SOURCE_SELECTED is True:
        raise VenueWitnessObservationContractError(
            "VENUE_WITNESS_OBSERVATION_SOURCE_SELECTION_FORBIDDEN"
        )
    if GOVERNED_PRODUCER_CREATED is True:
        raise VenueWitnessObservationContractError(
            "VENUE_WITNESS_OBSERVATION_PRODUCER_MUST_REMAIN_ABSENT"
        )
    if EQUITY_DIMENSION_BOUND is True:
        raise VenueWitnessObservationContractError(
            "VENUE_WITNESS_OBSERVATION_EQUITY_DIMENSION_BOUND_FORBIDDEN"
        )
    if MAPPED_TO_RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING is True:
        raise VenueWitnessObservationContractError("VENUE_WITNESS_OBSERVATION_MAPPING_FORBIDDEN")

    _require_non_empty_str(field="witness_id", raw=witness.witness_id)
    _require_non_empty_str(field="bound_account_identity", raw=witness.bound_account_identity)
    _require_non_empty_str(field="bound_venue_identity", raw=witness.bound_venue_identity)
    _require_non_empty_str(field="rest_host", raw=witness.rest_host)
    _require_non_empty_str(field="bound_td_mode", raw=witness.bound_td_mode)
    _require_non_empty_str(field="account_mode", raw=witness.account_mode)
    currency = _require_non_empty_str(field="currency_domain", raw=witness.currency_domain)
    if _fold(currency) == "usdusdc" or currency == "USD=USDC":
        raise VenueWitnessObservationContractError(
            "VENUE_WITNESS_OBSERVATION_USD_USDC_EQUIVALENCE_FORBIDDEN"
        )
    _require_non_empty_str(field="endpoint", raw=witness.endpoint)
    method = _require_non_empty_str(field="method", raw=witness.method)
    if method != METHOD_GET:
        raise VenueWitnessObservationContractError(
            f"VENUE_WITNESS_OBSERVATION_METHOD_NOT_GET:{method}"
        )
    _require_non_empty_str(field="request_identity", raw=witness.request_identity)
    _require_non_empty_str(field="decision_epoch", raw=witness.decision_epoch)
    _require_iso_z(field=CANONICAL_OBSERVED_AT_AS_OF, raw=witness.observed_at_as_of)
    _require_iso_z(field="response_received_at", raw=witness.response_received_at)
    provider = _require_str_allow_empty(field="provider_timestamp", raw=witness.provider_timestamp)
    if (
        provider != ""
        and _ISO_Z.fullmatch(provider) is None
        and _PROVIDER_MS.fullmatch(provider) is None
    ):
        raise VenueWitnessObservationContractError(
            "VENUE_WITNESS_OBSERVATION_PROVIDER_TIMESTAMP_NOT_EVIDENCE"
        )
    raw_field_path = _require_non_empty_str(field="raw_field_path", raw=witness.raw_field_path)
    _reject_fallback_chain(field="raw_field_path", raw=raw_field_path)
    semantic = _require_non_empty_str(
        field="observation_semantic_class", raw=witness.observation_semantic_class
    )
    if semantic != OBSERVATION_SEMANTIC_CLASS:
        raise VenueWitnessObservationContractError(
            "VENUE_WITNESS_OBSERVATION_SEMANTIC_CLASS_NOT_RAW_VENUE_OBSERVATION"
        )
    if _fold(semantic) == _fold(DIMENSION_ID):
        raise VenueWitnessObservationContractError(
            "VENUE_WITNESS_OBSERVATION_MUST_NOT_CLAIM_EQUITY_DIMENSION"
        )
    raw_value = _require_str_allow_empty(
        field="raw_value_representation", raw=witness.raw_value_representation
    )
    presence = _require_non_empty_str(field="presence_state", raw=witness.presence_state)
    if presence not in PRESENCE_STATES:
        raise VenueWitnessObservationContractError(
            f"VENUE_WITNESS_OBSERVATION_PRESENCE_STATE_UNKNOWN:{presence}"
        )
    _validate_presence_state(presence_state=presence, raw_value=raw_value)
    payload_state = _require_non_empty_str(field="raw_payload_state", raw=witness.raw_payload_state)
    if payload_state not in RAW_PAYLOAD_STATES:
        raise VenueWitnessObservationContractError(
            f"VENUE_WITNESS_OBSERVATION_RAW_PAYLOAD_STATE_UNKNOWN:{payload_state}"
        )
    payload_digest = _require_non_empty_str(field="payload_digest", raw=witness.payload_digest)
    if _SHA256_HEX.fullmatch(payload_digest) is None:
        raise VenueWitnessObservationContractError(
            "VENUE_WITNESS_OBSERVATION_PAYLOAD_DIGEST_NOT_SHA256"
        )
    raw_payload = _require_str_allow_empty(field="raw_payload", raw=witness.raw_payload)
    _reject_secret_text(field="raw_payload", raw=raw_payload)
    if payload_state == RAW_PAYLOAD_RETAINED:
        if raw_payload == "":
            raise VenueWitnessObservationContractError(
                "VENUE_WITNESS_OBSERVATION_RAW_PAYLOAD_RETAINED_REQUIRES_PAYLOAD"
            )
        if _sha256_hex(raw_payload) != payload_digest:
            raise VenueWitnessObservationContractError(
                "VENUE_WITNESS_OBSERVATION_PAYLOAD_DIGEST_MISMATCH"
            )
    else:
        if raw_payload != "":
            raise VenueWitnessObservationContractError(
                "VENUE_WITNESS_OBSERVATION_DIGEST_ONLY_CANNOT_CLAIM_RAW_PAYLOAD"
            )
    request_provenance = _require_non_empty_str(
        field="request_provenance", raw=witness.request_provenance
    )
    response_provenance = _require_non_empty_str(
        field="response_provenance", raw=witness.response_provenance
    )
    _reject_secret_text(field="request_provenance", raw=request_provenance)
    _reject_secret_text(field="response_provenance", raw=response_provenance)
    authority_class = _require_non_empty_str(
        field="observation_vs_authority_class",
        raw=witness.observation_vs_authority_class,
    )
    if authority_class == OBSERVATION_VS_AUTHORITY_CLASS_AUTHORITY:
        raise VenueWitnessObservationContractError(
            "VENUE_WITNESS_OBSERVATION_AUTHORITY_CLASS_FORBIDDEN"
        )
    if authority_class != OBSERVATION_VS_AUTHORITY_CLASS_OBSERVATION:
        raise VenueWitnessObservationContractError(
            "VENUE_WITNESS_OBSERVATION_OBSERVATION_VS_AUTHORITY_CLASS_UNKNOWN"
        )
    effect = _require_non_empty_str(
        field="observation_authority_effect",
        raw=witness.observation_authority_effect,
    )
    if effect != OBSERVATION_AUTHORITY_EFFECT:
        raise VenueWitnessObservationContractError(
            "VENUE_WITNESS_OBSERVATION_AUTHORITY_EFFECT_MUST_BE_NONE"
        )
    bound_status = _require_non_empty_str(
        field="equity_dimension_bound_status",
        raw=witness.equity_dimension_bound_status,
    )
    if bound_status != EQUITY_DIMENSION_BOUND_STATUS_UNBOUND:
        raise VenueWitnessObservationContractError(
            "VENUE_WITNESS_OBSERVATION_EQUITY_DIMENSION_BOUND_STATUS_MUST_REMAIN_UNBOUND"
        )
    mapping_status = _require_non_empty_str(field="mapping_status", raw=witness.mapping_status)
    if mapping_status != MAPPING_STATUS_UNBOUND:
        raise VenueWitnessObservationContractError(
            "VENUE_WITNESS_OBSERVATION_MAPPING_STATUS_MUST_REMAIN_UNBOUND"
        )
    freshness = _require_non_empty_str(
        field="freshness_evidence_status", raw=witness.freshness_evidence_status
    )
    if freshness != FRESHNESS_EVIDENCE_STATUS:
        raise VenueWitnessObservationContractError(
            "VENUE_WITNESS_OBSERVATION_FRESHNESS_POLICY_MUST_REMAIN_UNBOUND"
        )
    clock = _require_non_empty_str(field="clock_source_status", raw=witness.clock_source_status)
    if clock != CLOCK_SOURCE_STATUS_UNBOUND:
        raise VenueWitnessObservationContractError(
            "VENUE_WITNESS_OBSERVATION_CLOCK_SOURCE_MUST_REMAIN_UNBOUND"
        )
    for field in _IDENTITY_SEMANTICS_FIELDS:
        if _fold(str(getattr(witness, field))) == _fold(DIMENSION_ID):
            raise VenueWitnessObservationContractError(
                f"VENUE_WITNESS_OBSERVATION_MUST_NOT_CLAIM_EQUITY_DIMENSION:{field}"
            )
    canonical = witness.to_canonical_dict()
    expected_digest = compute_venue_witness_provenance_digest_v1(canonical)
    digest = _require_non_empty_str(field="provenance_digest", raw=witness.provenance_digest)
    if digest != expected_digest:
        raise VenueWitnessObservationContractError(
            "VENUE_WITNESS_OBSERVATION_PROVENANCE_DIGEST_MISMATCH"
        )


def build_trading_account_venue_witness_observation_v1(
    **fields: Any,
) -> TradingAccountVenueWitnessObservationV1:
    """Fail-closed schema constructor. Explicit fields only. Not a mint."""

    normalized: dict[str, Any] = {}
    for canonical in WITNESS_PROVENANCE_REQUIRED_FIELDS:
        python_name = _python_field_name(canonical)
        if canonical in fields:
            raw = fields[canonical]
        elif python_name in fields:
            raw = fields[python_name]
        else:
            raise VenueWitnessObservationContractError(
                f"VENUE_WITNESS_OBSERVATION_FIELD_MISSING:{canonical}"
            )
        normalized[python_name] = raw
    unexpected = (
        set(fields)
        - set(WITNESS_PROVENANCE_REQUIRED_FIELDS)
        - set(CANONICAL_TO_PYTHON_FIELD.values())
    )
    if unexpected:
        raise VenueWitnessObservationContractError(
            "VENUE_WITNESS_OBSERVATION_UNEXPECTED_FIELD:" + ",".join(sorted(unexpected))
        )
    return TradingAccountVenueWitnessObservationV1(**normalized)
