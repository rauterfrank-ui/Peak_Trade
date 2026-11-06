"""MARKET_CONTEXT_V1 — compositional typed non-price context for MI/Learning (AUTHORITY=NONE).

Not a second market truth; references governed canonical fact/adapters only.
Does not grant trading, selection, promotion, risk, sizing, or external effect.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Final, Mapping, Sequence

from src.learning.deterministic_decision_outcome_v0.common_v0 import (
    require_event_time_utc,
    require_mapping,
    require_record_id,
)
from src.learning.deterministic_decision_outcome_v0.serialization_v0 import (
    compute_content_hash_v0,
    is_valid_sha256_hex_v0,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.constants_v1 import (
    STACK_DOMAIN,
)

SCHEMA_VERSION: Final[str] = "market_context_v1"
MARKET_CONTEXT_AUTHORITY: Final[str] = "NONE"
CONTRACT_ID: Final[str] = "normative_non_price_market_context_v1"
N_BARS_BACKBONE_TOKEN: Final[str] = "N_BARS_REALIZED_OUTCOME_BACKBONE_UNCHANGED"

CONTEXT_FAMILY_SLOT_SCHEMA: Final[str] = "context_family_slot_v1"
MICROSTRUCTURE_KIND_PROXY_OHLCV: Final[str] = "PROXY_OHLCV"
MICROSTRUCTURE_KIND_TRUE_L2: Final[str] = "TRUE_L2"
CROSS_MARKET_CONTEXT_ONLY: Final[str] = "CONTEXT_ONLY"

_TOP_LEVEL_KEYS: Final[frozenset[str]] = frozenset(
    {
        "schema_version",
        "contract_id",
        "context_id",
        "observed_at",
        "instrument_ref",
        "information_set_ref",
        "price_state_ref",
        "flow_state_ref",
        "liquidity_microstructure_state_ref",
        "derivatives_state_ref",
        "volatility_state_ref",
        "cross_market_state_ref",
        "quality_state_ref",
        "provenance_refs",
        "feature_versions",
        "market_context_authority",
        "n_bars_backbone_semantics",
        "content_digest",
    }
)

_FAMILY_FIELDS: Final[tuple[str, ...]] = (
    "price_state_ref",
    "flow_state_ref",
    "liquidity_microstructure_state_ref",
    "derivatives_state_ref",
    "volatility_state_ref",
    "cross_market_state_ref",
    "quality_state_ref",
)


class ContextFamilyPresence(str, Enum):
    PRESENT = "PRESENT"
    MISSING = "MISSING"


class MarketContextValidationError(ValueError):
    """Fail-closed MARKET_CONTEXT_V1 validation."""


def _parse_utc(value: str) -> datetime:
    text = require_event_time_utc(value, "utc")
    return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc)


def derive_context_id_v1(*, identity_body: Mapping[str, Any]) -> str:
    digest = compute_content_hash_v0(dict(identity_body))
    return f"mi.market_context.{digest[:48]}"


def derive_information_set_ref_v1(*, identity_body: Mapping[str, Any]) -> str:
    digest = compute_content_hash_v0(dict(identity_body))
    return f"mi.info_set.{digest[:48]}"


def _validate_feature_versions(raw: Any) -> Mapping[str, str]:
    if not isinstance(raw, Mapping):
        raise MarketContextValidationError("FEATURE_VERSIONS_INVALID")
    out: dict[str, str] = {}
    for key, value in raw.items():
        if not isinstance(key, str) or not key.strip():
            raise MarketContextValidationError("FEATURE_VERSION_KEY_INVALID")
        if not isinstance(value, str) or not value.strip():
            raise MarketContextValidationError("FEATURE_VERSION_VALUE_INVALID")
        out[key] = value.strip()
    if not out:
        raise MarketContextValidationError("FEATURE_VERSIONS_EMPTY")
    return MappingProxyType(out)


def _validate_provenance_refs(raw: Any) -> tuple[str, ...]:
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        raise MarketContextValidationError("PROVENANCE_REFS_INVALID")
    refs = tuple(require_record_id(item, "provenance_refs[]") for item in raw)
    if not refs:
        raise MarketContextValidationError("PROVENANCE_REFS_EMPTY")
    return refs


def _validate_context_family_slot(
    raw: Any,
    *,
    field_name: str,
    observed_at: datetime,
) -> MappingProxyType[str, Any]:
    slot = require_mapping(raw, field_name)
    if slot.get("schema_version") != CONTEXT_FAMILY_SLOT_SCHEMA:
        raise MarketContextValidationError(f"{field_name}_SCHEMA_MISMATCH")
    presence = slot.get("presence")
    if presence not in {ContextFamilyPresence.PRESENT.value, ContextFamilyPresence.MISSING.value}:
        raise MarketContextValidationError(f"{field_name}_PRESENCE_INVALID")

    ownership = slot.get("producer_ownership")
    if ownership in ("UNKNOWN", "MIXED"):
        raise MarketContextValidationError(f"{field_name}_OWNERSHIP_FAIL_CLOSED")

    if presence == ContextFamilyPresence.MISSING.value:
        if slot.get("state_ref") is not None:
            raise MarketContextValidationError(f"{field_name}_MISSING_MUST_NOT_HAVE_STATE_REF")
        if slot.get("pit_observed_at_utc") is not None:
            raise MarketContextValidationError(f"{field_name}_MISSING_MUST_NOT_HAVE_PIT_TIME")
        missing_reason = slot.get("missing_reason")
        if not isinstance(missing_reason, str) or not missing_reason.strip():
            raise MarketContextValidationError(f"{field_name}_MISSING_REASON_REQUIRED")
        return MappingProxyType(
            {
                "schema_version": CONTEXT_FAMILY_SLOT_SCHEMA,
                "presence": ContextFamilyPresence.MISSING.value,
                "state_ref": None,
                "missing_reason": missing_reason.strip(),
                "producer_owner": slot.get("producer_owner"),
                "producer_ownership": ownership,
            }
        )

    state_ref = require_record_id(slot.get("state_ref"), f"{field_name}.state_ref")
    pit = require_event_time_utc(
        slot.get("pit_observed_at_utc"), f"{field_name}.pit_observed_at_utc"
    )
    pit_dt = _parse_utc(pit)
    if pit_dt > observed_at:
        raise MarketContextValidationError(f"{field_name}_PIT_LOOKAHEAD_FORBIDDEN")

    producer_owner = slot.get("producer_owner")
    if not isinstance(producer_owner, str) or not producer_owner.strip():
        raise MarketContextValidationError(f"{field_name}_PRODUCER_OWNER_REQUIRED")

    normalized: dict[str, Any] = {
        "schema_version": CONTEXT_FAMILY_SLOT_SCHEMA,
        "presence": ContextFamilyPresence.PRESENT.value,
        "state_ref": state_ref,
        "pit_observed_at_utc": pit,
        "producer_owner": producer_owner.strip(),
        "producer_ownership": ownership,
        "feature_version": slot.get("feature_version"),
    }

    if field_name == "liquidity_microstructure_state_ref":
        kind = slot.get("microstructure_kind")
        if kind not in (MICROSTRUCTURE_KIND_PROXY_OHLCV, MICROSTRUCTURE_KIND_TRUE_L2):
            raise MarketContextValidationError("MICROSTRUCTURE_KIND_INVALID_OR_COLLAPSED")
        if slot.get("microstructure_kind_collapsed") is True:
            raise MarketContextValidationError("MICROSTRUCTURE_PROXY_L2_COLLAPSE_FORBIDDEN")
        normalized["microstructure_kind"] = kind

    if field_name == "cross_market_state_ref":
        if slot.get("cross_market_authority") != CROSS_MARKET_CONTEXT_ONLY:
            raise MarketContextValidationError("CROSS_MARKET_MUST_BE_CONTEXT_ONLY")
        if slot.get("rerank_authorized") is True or slot.get("reselect_authorized") is True:
            raise MarketContextValidationError("CROSS_MARKET_RERANK_RESELECT_FORBIDDEN")
        normalized["cross_market_authority"] = CROSS_MARKET_CONTEXT_ONLY

    return MappingProxyType(normalized)


def build_market_context_v1(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    raw = require_mapping(payload, "market_context")
    missing = _TOP_LEVEL_KEYS - frozenset(raw.keys())
    if missing:
        raise MarketContextValidationError("MARKET_CONTEXT_FIELDS_MISSING")
    if raw.get("schema_version") != SCHEMA_VERSION:
        raise MarketContextValidationError("MARKET_CONTEXT_SCHEMA_MISMATCH")
    if raw.get("contract_id") != CONTRACT_ID:
        raise MarketContextValidationError("MARKET_CONTEXT_CONTRACT_ID_MISMATCH")
    if raw.get("market_context_authority") != MARKET_CONTEXT_AUTHORITY:
        raise MarketContextValidationError("MARKET_CONTEXT_AUTHORITY_MUST_BE_NONE")
    if raw.get("n_bars_backbone_semantics") != N_BARS_BACKBONE_TOKEN:
        raise MarketContextValidationError("N_BARS_BACKBONE_SEMANTICS_REQUIRED")

    observed_at = require_event_time_utc(raw.get("observed_at"), "observed_at")
    observed_dt = _parse_utc(observed_at)
    instrument_ref = require_record_id(raw.get("instrument_ref"), "instrument_ref")
    information_set_ref = require_record_id(raw.get("information_set_ref"), "information_set_ref")

    family_slots: dict[str, Any] = {}
    for field in _FAMILY_FIELDS:
        family_slots[field] = dict(
            _validate_context_family_slot(
                raw.get(field),
                field_name=field,
                observed_at=observed_dt,
            )
        )

    provenance_refs = _validate_provenance_refs(raw.get("provenance_refs"))
    feature_versions = _validate_feature_versions(raw.get("feature_versions"))

    identity_body = {
        "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        "observed_at": observed_at,
        "instrument_ref": instrument_ref,
        "information_set_ref": information_set_ref,
        **{field: family_slots[field] for field in _FAMILY_FIELDS},
        "provenance_refs": provenance_refs,
        "feature_versions": dict(feature_versions),
    }
    expected_id = derive_context_id_v1(identity_body=identity_body)
    if raw.get("context_id") != expected_id:
        raise MarketContextValidationError("MARKET_CONTEXT_ID_MISMATCH")

    digest = compute_content_hash_v0(identity_body)
    if raw.get("content_digest") != digest:
        raise MarketContextValidationError("MARKET_CONTEXT_CONTENT_DIGEST_MISMATCH")
    if not is_valid_sha256_hex_v0(str(raw.get("content_digest"))):
        raise MarketContextValidationError("MARKET_CONTEXT_CONTENT_DIGEST_INVALID")

    body = {
        "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        "domain": STACK_DOMAIN,
        "context_id": expected_id,
        "observed_at": observed_at,
        "instrument_ref": instrument_ref,
        "information_set_ref": information_set_ref,
        **family_slots,
        "provenance_refs": list(provenance_refs),
        "feature_versions": dict(feature_versions),
        "market_context_authority": MARKET_CONTEXT_AUTHORITY,
        "n_bars_backbone_semantics": N_BARS_BACKBONE_TOKEN,
        "content_digest": digest,
    }
    return MappingProxyType(body)


def validate_market_context_v1(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    return build_market_context_v1(payload)


def serialize_market_context_canonical_v1(record: Mapping[str, Any]) -> str:
    """Deterministic JSON serialization for replay/persistence contracts."""
    import json

    validated = validate_market_context_v1(record)
    canonical = {key: validated[key] for key in sorted(validated.keys())}
    return json.dumps(canonical, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True)
class GovernedMarketContextInputsV1:
    observed_at: str
    instrument_ref: str
    information_set_identity_body: Mapping[str, Any]
    provenance_refs: Sequence[str]
    feature_versions: Mapping[str, str]
    price_state: Mapping[str, Any] | None = None
    flow_state: Mapping[str, Any] | None = None
    liquidity_microstructure_state: Mapping[str, Any] | None = None
    derivatives_state: Mapping[str, Any] | None = None
    volatility_state: Mapping[str, Any] | None = None
    cross_market_state: Mapping[str, Any] | None = None
    quality_state: Mapping[str, Any] | None = None


def _missing_slot(*, missing_reason: str, producer_owner: str | None = None) -> dict[str, Any]:
    return {
        "schema_version": CONTEXT_FAMILY_SLOT_SCHEMA,
        "presence": ContextFamilyPresence.MISSING.value,
        "state_ref": None,
        "missing_reason": missing_reason,
        "producer_owner": producer_owner,
        "producer_ownership": "GOVERNED_MISSING",
    }


def _present_slot(slot: Mapping[str, Any]) -> dict[str, Any]:
    body = dict(slot)
    body.setdefault("schema_version", CONTEXT_FAMILY_SLOT_SCHEMA)
    body["presence"] = ContextFamilyPresence.PRESENT.value
    return body


def compose_market_context_v1_from_governed_inputs(
    inputs: GovernedMarketContextInputsV1,
) -> MappingProxyType[str, Any]:
    """Compose MARKET_CONTEXT_V1 from explicitly supplied governed slots only."""
    information_set_ref = derive_information_set_ref_v1(
        identity_body=inputs.information_set_identity_body
    )
    family_builders = (
        ("price_state_ref", inputs.price_state, "NO_GOVERNED_PRICE_FACT_REF_SUPPLIED"),
        ("flow_state_ref", inputs.flow_state, "NO_GOVERNED_FLOW_FACT_REF_SUPPLIED"),
        (
            "liquidity_microstructure_state_ref",
            inputs.liquidity_microstructure_state,
            "NO_GOVERNED_MICROSTRUCTURE_FACT_REF_SUPPLIED",
        ),
        (
            "derivatives_state_ref",
            inputs.derivatives_state,
            "NO_GOVERNED_DERIVATIVES_FACT_REF_SUPPLIED",
        ),
        (
            "volatility_state_ref",
            inputs.volatility_state,
            "NO_GOVERNED_VOLATILITY_FACT_REF_SUPPLIED",
        ),
        (
            "cross_market_state_ref",
            inputs.cross_market_state,
            "NO_GOVERNED_CROSS_MARKET_FACT_REF_SUPPLIED",
        ),
        ("quality_state_ref", inputs.quality_state, "NO_GOVERNED_QUALITY_FACT_REF_SUPPLIED"),
    )
    family_slots: dict[str, Any] = {}
    for field_name, supplied, missing_reason in family_builders:
        if supplied is None:
            family_slots[field_name] = _missing_slot(missing_reason=missing_reason)
        else:
            family_slots[field_name] = _present_slot(supplied)

    identity_body = {
        "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        "observed_at": inputs.observed_at,
        "instrument_ref": inputs.instrument_ref,
        "information_set_ref": information_set_ref,
        **family_slots,
        "provenance_refs": tuple(
            require_record_id(item, "provenance_refs[]") for item in inputs.provenance_refs
        ),
        "feature_versions": dict(inputs.feature_versions),
    }
    digest = compute_content_hash_v0(identity_body)
    payload = {
        **identity_body,
        "context_id": derive_context_id_v1(identity_body=identity_body),
        "provenance_refs": list(identity_body["provenance_refs"]),
        "market_context_authority": MARKET_CONTEXT_AUTHORITY,
        "n_bars_backbone_semantics": N_BARS_BACKBONE_TOKEN,
        "content_digest": digest,
    }
    return validate_market_context_v1(payload)
