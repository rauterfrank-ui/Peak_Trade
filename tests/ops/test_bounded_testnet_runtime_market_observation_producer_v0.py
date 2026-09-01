"""Bounded testnet producer fetch is OKX EEA public-ticker only (fake-fetcher tests)."""

from __future__ import annotations

from datetime import datetime, timezone

from src.ops.bounded_testnet_runtime_market_observation_producer_v0 import (
    fetch_bounded_testnet_pf_ethusd_ticker_tick_v0,
    validate_testnet_public_ticker_request_url,
    RuntimeMarketObservationFailureClass,
    CANONICAL_TESTNET_BASE_URL,
    BoundedTestnetRuntimeClockV0,
)


def test_fetch_okx_eea_ticker_with_fake_payload() -> None:
    body = (
        b'{"code":"0","data":[{"instId":"ETH-USD_UM_XPERP-310404",'
        b'"markPx":"3500.0","last":"3499.5","idxPx":"3500.1","ts":"1785442987000"}]}'
    )
    clock = BoundedTestnetRuntimeClockV0(_now=datetime.fromtimestamp(1785442987, tz=timezone.utc))
    result = fetch_bounded_testnet_pf_ethusd_ticker_tick_v0(
        source_run_id="r",
        tick_index=0,
        sequence=0,
        fetcher=lambda url, timeout_seconds: (200, body),
        testnet_base_url=CANONICAL_TESTNET_BASE_URL,
        clock=clock,
    )
    assert result.success is True


def test_canonical_url_validator_rejects_noncanonical_host() -> None:
    assert (
        validate_testnet_public_ticker_request_url("http://example.invalid")
        == RuntimeMarketObservationFailureClass.TESTNET_HOST_NOT_ALLOWED
    )
