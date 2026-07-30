"""Normalized public market data carrying canonical + venue identities."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Optional

from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.mark_price_contract_v1 import (
    PublicMarkPriceV1,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.ticker_semantics_v1 import (
    PublicTickerSemanticsV1,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.venue_instrument_mapping_v1 import (
    VenueInstrumentMappingV1,
)


@dataclass(frozen=True)
class NormalizedPublicMarketDataV1:
    canonical_instrument_id: str
    venue_instrument_id: str
    venue: str
    mark_px: float
    event_ts_unix: float
    receive_ts_unix: float
    mark_price_endpoint: str
    mark_price_field: str
    mapping_digest: str
    mapping_version: str
    last: Optional[float] = None
    bid_px: Optional[float] = None
    ask_px: Optional[float] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def authority_instrument_id(self) -> str:
        """Downstream portfolio/strategy authority remains canonical."""
        return self.canonical_instrument_id


def build_normalized_public_market_data_v1(
    *,
    mapping: VenueInstrumentMappingV1,
    mark: PublicMarkPriceV1,
    ticker: Optional[PublicTickerSemanticsV1] = None,
) -> NormalizedPublicMarketDataV1:
    if mapping.venue_instrument_id != mark.venue_instrument_id:
        raise ValueError("MAPPING_MARK_VENUE_ID_MISMATCH")
    if ticker is not None and ticker.venue_instrument_id != mapping.venue_instrument_id:
        raise ValueError("MAPPING_TICKER_VENUE_ID_MISMATCH")
    return NormalizedPublicMarketDataV1(
        canonical_instrument_id=mapping.canonical_instrument_id,
        venue_instrument_id=mapping.venue_instrument_id,
        venue=mapping.venue,
        mark_px=mark.mark_px,
        event_ts_unix=mark.event_ts_unix,
        receive_ts_unix=mark.receive_ts_unix,
        mark_price_endpoint=mark.endpoint,
        mark_price_field=mark.field,
        mapping_digest=mapping.mapping_digest,
        mapping_version=mapping.mapping_version,
        last=None if ticker is None else ticker.last,
        bid_px=None if ticker is None else ticker.bid_px,
        ask_px=None if ticker is None else ticker.ask_px,
    )


def dual_identity_provenance_v1(
    *,
    mapping: VenueInstrumentMappingV1,
    extra: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    payload = {
        "canonical_instrument_id": mapping.canonical_instrument_id,
        "venue_instrument_id": mapping.venue_instrument_id,
        "venue": mapping.venue,
        "mapping_source": mapping.mapping_source,
        "mapping_version": mapping.mapping_version,
        "mapping_digest": mapping.mapping_digest,
        "instrument_authority": "canonical_instrument_id",
        "transport_identity": "venue_instrument_id",
    }
    if extra:
        payload.update(dict(extra))
    return payload
