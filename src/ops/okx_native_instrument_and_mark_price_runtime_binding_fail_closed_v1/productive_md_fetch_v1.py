"""Productive public MD fetch: mapping → instruments → mark-price → normalize."""

from __future__ import annotations

from typing import Any, Callable, Mapping, Optional, Protocol

from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.constants_v1 import (
    CANONICAL_INSTRUMENT_ID,
    MARK_PRICE_ENDPOINT,
    MARK_PRICE_INST_TYPE,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.error_classes_v1 import (
    MarketDataBindingErrorV1,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.i17_shadow_instrument_v1 import (
    ETH_I17,
    SOPH_I17,
    RANKED_SWAP_SCOPES,
    I17ShadowInstrumentV1,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.mark_price_contract_v1 import (
    parse_public_mark_price_response_v1,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.normalized_market_data_v1 import (
    NormalizedPublicMarketDataV1,
    build_normalized_public_market_data_v1,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.public_instruments_validation_v1 import (
    extract_instruments_data_array_v1,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.ticker_semantics_v1 import (
    parse_public_ticker_semantics_v1,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.venue_instrument_mapping_v1 import (
    VenueInstrumentMappingV1,
    resolve_okx_venue_instrument_mapping_v1,
)


class PublicMdTransportProtocolV1(Protocol):
    def fetch_instruments(self, *, venue_instrument_id: str, inst_type: str = ...) -> Any: ...

    def fetch_mark_price(self, *, venue_instrument_id: str, inst_type: str = ...) -> Any: ...

    def fetch_ticker(self, *, venue_instrument_id: str) -> Any: ...


def resolve_mapping_with_transport_inventory_v1(
    *,
    transport: PublicMdTransportProtocolV1,
    canonical_instrument_id: str = CANONICAL_INSTRUMENT_ID,
    instruments_payload: Optional[Mapping[str, Any]] = None,
    i17_scope: I17ShadowInstrumentV1 | None = None,
) -> VenueInstrumentMappingV1:
    if i17_scope is not None and (
        i17_scope not in (ETH_I17, SOPH_I17, *RANKED_SWAP_SCOPES)
        or canonical_instrument_id != i17_scope.canonical_id
    ):
        raise MarketDataBindingErrorV1(
            "CANONICAL_INSTRUMENT_MAPPING_MISSING", canonical_instrument_id
        )
    if instruments_payload is None:
        # Need venue id from authority first for targeted instruments query.
        # Seed inventory query uses authority instrument id without treating it as
        # a transport default for market data — mapping still validates inventory.
        from src.ops.bounded_futures_testnet_venue_binding_v0 import (
            default_okx_europe_xperp_production_binding,
        )

        seed_id = (
            i17_scope.native_id
            if i17_scope is not None
            else str(default_okx_europe_xperp_production_binding().instrument_id)
        )
        fetch = transport.fetch_instruments(
            venue_instrument_id=seed_id,
            inst_type=i17_scope.instrument_type if i17_scope else MARK_PRICE_INST_TYPE,
        )
        instruments_payload = fetch.payload
    inventory = extract_instruments_data_array_v1(instruments_payload)
    return resolve_okx_venue_instrument_mapping_v1(
        canonical_instrument_id=canonical_instrument_id,
        instruments_inventory=inventory,
        i17_scope=i17_scope,
    )


def fetch_normalized_public_market_data_v1(
    *,
    transport: PublicMdTransportProtocolV1,
    mapping: VenueInstrumentMappingV1,
    receive_ts_unix: float | Callable[[], float],
    max_stale_seconds: float,
    include_ticker: bool = True,
) -> NormalizedPublicMarketDataV1:
    """Fetch markPx via mark-price contract using venue_instrument_id only."""
    if mapping.canonical_instrument_id == mapping.venue_instrument_id:
        # Equality of strings is allowed; transport must still use venue field.
        pass
    try:
        mark_fetch = transport.fetch_mark_price(
            venue_instrument_id=mapping.venue_instrument_id,
            inst_type=mapping.instrument_type,
        )
    except Exception as exc:  # noqa: BLE001
        raise MarketDataBindingErrorV1("TRANSPORT_FAILURE", str(exc)) from exc

    if mapping.instrument_type == "SWAP":
        rows = mark_fetch.payload.get("data")
        if (
            not isinstance(rows, list)
            or len(rows) != 1
            or not isinstance(rows[0], Mapping)
            or rows[0].get("instType") != "SWAP"
        ):
            raise MarketDataBindingErrorV1(
                "VENUE_INSTRUMENT_RESPONSE_MISMATCH", mapping.venue_instrument_id
            )
    mark = parse_public_mark_price_response_v1(
        mark_fetch.payload,
        expected_venue_instrument_id=mapping.venue_instrument_id,
        receive_ts_unix=receive_ts_unix() if callable(receive_ts_unix) else receive_ts_unix,
        max_stale_seconds=max_stale_seconds,
    )

    ticker = None
    if include_ticker:
        try:
            ticker_fetch = transport.fetch_ticker(venue_instrument_id=mapping.venue_instrument_id)
            ticker = parse_public_ticker_semantics_v1(
                ticker_fetch.payload,
                expected_venue_instrument_id=mapping.venue_instrument_id,
            )
        except MarketDataBindingErrorV1:
            raise
        except Exception as exc:  # noqa: BLE001
            raise MarketDataBindingErrorV1("TRANSPORT_FAILURE", str(exc)) from exc

    assert mark.endpoint == MARK_PRICE_ENDPOINT
    return build_normalized_public_market_data_v1(mapping=mapping, mark=mark, ticker=ticker)
