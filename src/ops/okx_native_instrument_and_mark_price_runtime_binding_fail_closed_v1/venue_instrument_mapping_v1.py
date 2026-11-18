"""Canonical→venue instrument mapping via sole venue-binding authority."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from src.ops.bounded_futures_testnet_venue_binding_v0 import (
    PRODUCTION_INSTRUMENT_TYPE,
    PRODUCTION_RULE_TYPE,
    PRODUCTION_SETTLEMENT_ASSET,
    default_okx_europe_xperp_production_binding,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.constants_v1 import (
    AUTHORIZED_VENUE,
    MAPPING_SOURCE,
    VENUE_MAPPING_VERSION,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.error_classes_v1 import (
    MarketDataBindingErrorV1,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.i17_shadow_instrument_v1 import (
    SOPH_I17,
    I17ShadowInstrumentV1,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.public_instruments_validation_v1 import (
    validate_venue_instrument_in_public_inventory_v1,
)


@dataclass(frozen=True)
class VenueInstrumentMappingV1:
    canonical_instrument_id: str
    venue: str
    venue_instrument_id: str
    instrument_type: str
    contract_family: str
    settlement_currency: str
    mapping_source: str
    mapping_version: str
    mapping_digest: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _digest_mapping(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(dict(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def resolve_okx_venue_instrument_mapping_v1(
    *,
    canonical_instrument_id: str,
    venue: str = AUTHORIZED_VENUE,
    instruments_inventory: Sequence[Mapping[str, Any]],
    i17_scope: I17ShadowInstrumentV1 | None = None,
) -> VenueInstrumentMappingV1:
    """Resolve native OKX instId via the existing venue-binding authority only.

    Never invents a native ID. Never uses the Peak_Trade canonical constant as a
    transport default — the venue ID is taken from the binding authority and then
    validated against the public instruments inventory.
    """
    if venue != AUTHORIZED_VENUE:
        raise MarketDataBindingErrorV1("CANONICAL_INSTRUMENT_MAPPING_MISSING", f"venue={venue}")

    binding = default_okx_europe_xperp_production_binding()
    authority_instrument_id = str(binding.instrument_id or "").strip()
    if not authority_instrument_id:
        raise MarketDataBindingErrorV1(
            "CANONICAL_INSTRUMENT_MAPPING_MISSING", "binding_instrument_empty"
        )

    if i17_scope == SOPH_I17:
        if canonical_instrument_id != SOPH_I17.canonical_id:
            raise MarketDataBindingErrorV1(
                "CANONICAL_INSTRUMENT_MAPPING_MISSING", canonical_instrument_id
            )
        row = validate_venue_instrument_in_public_inventory_v1(
            venue_instrument_id=SOPH_I17.native_id,
            instruments_inventory=instruments_inventory,
            expected_inst_type="FUTURES",
        )
        if tuple(
            row.get(key)
            for key in (
                "instType",
                "instFamily",
                "uly",
                "ruleType",
                "ctType",
                "ctValCcy",
                "settleCcy",
            )
        ) != ("FUTURES", "SOPH-USD_UM_XPERP", "SOPH-USD", "xperp", "linear", "SOPH", "USD"):
            raise MarketDataBindingErrorV1("VENUE_INSTRUMENT_RESPONSE_MISMATCH", SOPH_I17.native_id)
        return _build_mapping(
            canonical_instrument_id=SOPH_I17.canonical_id,
            venue_instrument_id=SOPH_I17.native_id,
            mapping_source="I17_SHADOW_LANE_5_INSTRUMENT_SCOPE",
        )

    # The general mapping still comes from the venue-binding authority.
    if str(canonical_instrument_id).strip() != authority_instrument_id:
        raise MarketDataBindingErrorV1(
            "CANONICAL_INSTRUMENT_MAPPING_MISSING",
            str(canonical_instrument_id),
        )

    venue_instrument_id = authority_instrument_id
    validate_venue_instrument_in_public_inventory_v1(
        venue_instrument_id=venue_instrument_id,
        instruments_inventory=instruments_inventory,
        expected_inst_type=PRODUCTION_INSTRUMENT_TYPE,
    )

    return _build_mapping(
        canonical_instrument_id=str(canonical_instrument_id),
        venue_instrument_id=venue_instrument_id,
        mapping_source=MAPPING_SOURCE,
    )


def _build_mapping(*, canonical_instrument_id, venue_instrument_id, mapping_source):
    payload = {
        "canonical_instrument_id": canonical_instrument_id,
        "venue": AUTHORIZED_VENUE,
        "venue_instrument_id": venue_instrument_id,
        "instrument_type": PRODUCTION_INSTRUMENT_TYPE,
        "contract_family": PRODUCTION_RULE_TYPE,
        "settlement_currency": PRODUCTION_SETTLEMENT_ASSET,
        "mapping_source": mapping_source,
        "mapping_version": VENUE_MAPPING_VERSION,
    }
    return VenueInstrumentMappingV1(**payload, mapping_digest=_digest_mapping(payload))
