"""Contract tests for instrument_id_canonicalization_v1."""

from __future__ import annotations

from dataclasses import asdict

import pytest

from src.research.instrument_id_canonicalization_v1 import (
    INSTRUMENT_ID_CANONICALIZATION_VERSION,
    InstrumentIdCanonicalizationErrorCode,
    InstrumentIdCanonicalizationInputV1,
    canonicalize_instrument_id_v1,
    validate_instrument_id_format_v1,
)


def _input(**overrides: object) -> InstrumentIdCanonicalizationInputV1:
    base = {
        "venue_id": "okx",
        "market_type": "futures",
        "contract_type": "linear_perpetual",
        "base_asset": "ETH",
        "quote_asset": "USDT",
        "settlement_asset": "USDT",
        "venue_symbol": "ETH-USDT-SWAP",
    }
    base.update(overrides)
    return InstrumentIdCanonicalizationInputV1(**base)


def test_valid_perpetual_id() -> None:
    result = canonicalize_instrument_id_v1(_input())
    assert result.success is True
    assert result.instrument_id == "okx:linear_perpetual:ETH:USDT:USDT:perp"
    assert validate_instrument_id_format_v1(result.instrument_id)


def test_valid_dated_future_id() -> None:
    result = canonicalize_instrument_id_v1(
        _input(
            contract_type="linear_dated_future",
            contract_expiry="20241227",
            venue_symbol="ETH-USDT-241227",
        )
    )
    assert result.success is True
    assert result.instrument_id == "okx:linear_dated_future:ETH:USDT:USDT:20241227"


def test_inverse_future_explicitly_typed() -> None:
    result = canonicalize_instrument_id_v1(
        _input(
            contract_type="inverse_perpetual",
            base_asset="ETH",
            quote_asset="USD",
            settlement_asset="ETH",
            venue_symbol="ETH-USD-SWAP",
        )
    )
    assert result.success is True
    assert result.instrument_id == "okx:inverse_perpetual:ETH:USD:ETH:perp"


def test_multiple_venues_remain_distinct() -> None:
    okx = canonicalize_instrument_id_v1(_input(venue_id="okx"))
    binance = canonicalize_instrument_id_v1(_input(venue_id="binance_usdm", venue_symbol="ETHUSDT"))
    assert okx.instrument_id != binance.instrument_id


def test_rename_with_stable_native_id_remains_identical() -> None:
    first = canonicalize_instrument_id_v1(
        _input(venue_symbol="ETH-USDT-SWAP", native_instrument_id="okx-perp-eth-usdt")
    )
    second = canonicalize_instrument_id_v1(
        _input(venue_symbol="ETHUSDTM", native_instrument_id="okx-perp-eth-usdt")
    )
    assert first.instrument_id == second.instrument_id


def test_missing_stable_native_id_blocks_dated_future() -> None:
    result = canonicalize_instrument_id_v1(
        _input(contract_type="linear_dated_future", venue_symbol="ETH-USDT-241227")
    )
    assert result.success is False
    assert (
        InstrumentIdCanonicalizationErrorCode.MISSING_STABLE_INSTRUMENT_IDENTIFIER.value
        in result.error_codes
    )


def test_spot_blocked() -> None:
    result = canonicalize_instrument_id_v1(_input(market_type="spot"))
    assert result.success is False
    assert InstrumentIdCanonicalizationErrorCode.SPOT_MARKET.value in result.error_codes


def test_synthetic_spot_blocked() -> None:
    result = canonicalize_instrument_id_v1(_input(market_type="synthetic_spot"))
    assert result.success is False
    assert InstrumentIdCanonicalizationErrorCode.SYNTHETIC_SPOT_MARKET.value in result.error_codes


@pytest.mark.parametrize("base_asset", ["BTC", "XBT", "WBTC"])
def test_bitcoin_aliases_blocked(base_asset: str) -> None:
    result = canonicalize_instrument_id_v1(_input(base_asset=base_asset))
    assert result.success is False
    assert (
        InstrumentIdCanonicalizationErrorCode.BITCOIN_DIRECTION_DISALLOWED.value
        in result.error_codes
    )


def test_unknown_version_blocked() -> None:
    result = canonicalize_instrument_id_v1(
        _input(canonicalization_version="instrument_id_canonicalization.v999")
    )
    assert result.success is False
    assert (
        InstrumentIdCanonicalizationErrorCode.UNSUPPORTED_CANONICALIZATION_VERSION.value
        in result.error_codes
    )


def test_deterministic_sortability() -> None:
    ids = sorted(
        canonicalize_instrument_id_v1(_input(base_asset=asset)).instrument_id
        for asset in ("SOL", "ETH", "AVAX", "LINK")
    )
    assert ids == sorted(ids)
    assert ids[0].startswith("okx:linear_perpetual:AVAX")


def test_mapping_input_round_trip() -> None:
    payload = asdict(_input())
    result = canonicalize_instrument_id_v1(payload)
    assert result.success is True
