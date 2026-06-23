"""Offline tests for bounded testnet runtime market observation producer v0."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import pytest

from src.ops.bounded_testnet_market_input_admission_wiring_v0 import (
    REPO_GROUNDED_ETH_PERP_SELECTED_FUTURE_ID,
    REPO_GROUNDED_ETH_PERP_VENUE_SYMBOL,
)
from src.ops.bounded_testnet_runtime_market_observation_producer_v0 import (
    CANONICAL_TESTNET_BASE_URL,
    CANONICAL_TICKER_ENDPOINT,
    BoundedTestnetRuntimeClockV0,
    RuntimeMarketObservationFailureClass,
    assemble_bounded_testnet_runtime_market_observation_v0,
    build_canonical_testnet_public_ticker_url,
    collect_bounded_testnet_runtime_market_observation_v0,
    fetch_bounded_testnet_pf_ethusd_ticker_tick_v0,
    validate_testnet_public_ticker_request_url,
)

_FIXED_NOW = datetime(2026, 6, 23, 12, 0, 0, tzinfo=timezone.utc)
_FIXED_CLOCK = BoundedTestnetRuntimeClockV0(_now=_FIXED_NOW)
_TICKER_TS = "2026-06-23T11:59:30Z"


def _tickers_body(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "result": "success",
        "tickers": [
            {
                "symbol": "PF_ETHUSD",
                "markPrice": 3500.0,
                "last": 3499.5,
                "indexPrice": 3500.1,
                "lastTime": _TICKER_TS,
            }
        ],
    }
    base.update(overrides)
    return base


class _FakeFetcher:
    def __init__(
        self, *, status: int = 200, body: bytes | None = None, exc: Exception | None = None
    ):
        self.status = status
        self.body = body if body is not None else json.dumps(_tickers_body()).encode("utf-8")
        self.exc = exc
        self.calls = 0

    def fetch(self, url: str, *, timeout_seconds: float) -> tuple[int, bytes]:
        self.calls += 1
        if self.exc is not None:
            raise self.exc
        assert url == build_canonical_testnet_public_ticker_url(CANONICAL_TESTNET_BASE_URL)
        return self.status, self.body


def test_valid_pf_ethusd_response_produces_canonical_observation() -> None:
    fetcher = _FakeFetcher()
    result = fetch_bounded_testnet_pf_ethusd_ticker_tick_v0(
        source_run_id="producer-test-run",
        tick_index=0,
        sequence=1,
        fetcher=fetcher,
        clock=_FIXED_CLOCK,
    )
    assert result.success is True
    assert result.failure_class is None
    assert result.tick is not None
    assert result.tick.mark_price == 3500.0
    assert result.fetch_count == 1
    observation, failure_class, _detail = assemble_bounded_testnet_runtime_market_observation_v0(
        tick_results=(result,),
        source_run_id="producer-test-run",
    )
    assert failure_class is None
    assert observation is not None
    assert observation.selected_future_id == REPO_GROUNDED_ETH_PERP_SELECTED_FUTURE_ID
    assert observation.venue_symbol == REPO_GROUNDED_ETH_PERP_VENUE_SYMBOL
    assert observation.synthetic_offline_fixture is False
    assert observation.mark_price_available is True
    assert observation.last_price_available is True
    assert observation.index_price_available is True


def test_instrument_and_venue_mapping_enforced() -> None:
    fetcher = _FakeFetcher()
    result = fetch_bounded_testnet_pf_ethusd_ticker_tick_v0(
        source_run_id="producer-test-run",
        tick_index=0,
        sequence=1,
        instrument="PF_XBTUSD",
        venue_symbol="PF_XBTUSD",
        fetcher=fetcher,
        clock=_FIXED_CLOCK,
    )
    assert result.success is False
    assert result.failure_class == RuntimeMarketObservationFailureClass.INSTRUMENT_MAPPING_MISMATCH


def test_http_503_fails_closed_without_retry() -> None:
    fetcher = _FakeFetcher(status=503, body=b"service unavailable")
    result = fetch_bounded_testnet_pf_ethusd_ticker_tick_v0(
        source_run_id="producer-test-run",
        tick_index=0,
        sequence=1,
        fetcher=fetcher,
        clock=_FIXED_CLOCK,
    )
    assert result.success is False
    assert result.failure_class == RuntimeMarketObservationFailureClass.HTTP_503_SERVICE_UNAVAILABLE
    assert fetcher.calls == 1


def test_network_exception_is_redacted() -> None:
    fetcher = _FakeFetcher(exc=OSError("secret-token connection refused"))
    result = fetch_bounded_testnet_pf_ethusd_ticker_tick_v0(
        source_run_id="producer-test-run",
        tick_index=0,
        sequence=1,
        fetcher=fetcher,
        clock=_FIXED_CLOCK,
    )
    assert result.success is False
    assert result.failure_class == RuntimeMarketObservationFailureClass.NETWORK_EXCEPTION_REDACTED
    assert "secret" not in (result.failure_detail or "")


def test_live_host_rejected() -> None:
    assert (
        validate_testnet_public_ticker_request_url("https://futures.kraken.com")
        == RuntimeMarketObservationFailureClass.TESTNET_HOST_NOT_ALLOWED
    )


def test_wrong_endpoint_rejected() -> None:
    assert (
        validate_testnet_public_ticker_request_url(
            CANONICAL_TESTNET_BASE_URL,
            endpoint_path="/derivatives/api/v3/instruments",
        )
        == RuntimeMarketObservationFailureClass.ENDPOINT_NOT_ALLOWED
    )


def test_pf_ethusd_missing_fails_closed() -> None:
    body = json.dumps(
        {"result": "success", "tickers": [{"symbol": "PF_XBTUSD", "markPrice": 1.0}]}
    ).encode()
    fetcher = _FakeFetcher(body=body)
    result = fetch_bounded_testnet_pf_ethusd_ticker_tick_v0(
        source_run_id="producer-test-run",
        tick_index=0,
        sequence=1,
        fetcher=fetcher,
        clock=_FIXED_CLOCK,
    )
    assert result.failure_class == RuntimeMarketObservationFailureClass.VENUE_SYMBOL_NOT_FOUND


def test_invalid_json_rejected() -> None:
    fetcher = _FakeFetcher(body=b"not-json")
    result = fetch_bounded_testnet_pf_ethusd_ticker_tick_v0(
        source_run_id="producer-test-run",
        tick_index=0,
        sequence=1,
        fetcher=fetcher,
        clock=_FIXED_CLOCK,
    )
    assert result.failure_class == RuntimeMarketObservationFailureClass.RESPONSE_NOT_JSON


def test_missing_mark_price_rejected() -> None:
    body = json.dumps(
        {
            "result": "success",
            "tickers": [{"symbol": "PF_ETHUSD", "lastTime": _TICKER_TS}],
        }
    ).encode()
    fetcher = _FakeFetcher(body=body)
    result = fetch_bounded_testnet_pf_ethusd_ticker_tick_v0(
        source_run_id="producer-test-run",
        tick_index=0,
        sequence=1,
        fetcher=fetcher,
        clock=_FIXED_CLOCK,
    )
    assert result.failure_class == RuntimeMarketObservationFailureClass.PRICE_FIELD_MISSING


def test_non_finite_price_rejected() -> None:
    body = json.dumps(
        {
            "result": "success",
            "tickers": [
                {
                    "symbol": "PF_ETHUSD",
                    "markPrice": "NaN",
                    "last": 1.0,
                    "indexPrice": 1.0,
                    "lastTime": _TICKER_TS,
                }
            ],
        }
    ).encode()
    fetcher = _FakeFetcher(body=body)
    result = fetch_bounded_testnet_pf_ethusd_ticker_tick_v0(
        source_run_id="producer-test-run",
        tick_index=0,
        sequence=1,
        fetcher=fetcher,
        clock=_FIXED_CLOCK,
    )
    assert result.failure_class == RuntimeMarketObservationFailureClass.PRICE_FIELD_NOT_FINITE


def test_stale_timestamp_rejected() -> None:
    body = json.dumps(
        _tickers_body(
            tickers=[
                {
                    "symbol": "PF_ETHUSD",
                    "markPrice": 3500.0,
                    "last": 3499.5,
                    "indexPrice": 3500.1,
                    "lastTime": "2026-06-23T10:00:00Z",
                }
            ]
        )
    ).encode()
    fetcher = _FakeFetcher(body=body)
    result = fetch_bounded_testnet_pf_ethusd_ticker_tick_v0(
        source_run_id="producer-test-run",
        tick_index=0,
        sequence=1,
        fetcher=fetcher,
        clock=_FIXED_CLOCK,
        max_staleness_seconds=60.0,
    )
    assert result.failure_class == RuntimeMarketObservationFailureClass.OBSERVATION_STALE


def test_collect_stops_on_first_failure_no_retry() -> None:
    fetcher = _FakeFetcher(status=503, body=b"")
    observation, failure_class, _detail = collect_bounded_testnet_runtime_market_observation_v0(
        testnet_base_url=CANONICAL_TESTNET_BASE_URL,
        source_run_id="producer-test-run",
        max_steps=3,
        fetcher=fetcher,
        clock=_FIXED_CLOCK,
    )
    assert observation is None
    assert failure_class == RuntimeMarketObservationFailureClass.HTTP_503_SERVICE_UNAVAILABLE
    assert fetcher.calls == 1


def test_endpoint_allowlist_is_canonical_ticker_path() -> None:
    assert CANONICAL_TICKER_ENDPOINT == "/derivatives/api/v3/tickers"
