"""Bounded testnet producer fetch is not a current operative venue surface."""

from __future__ import annotations

import pytest

from src.exchange.operative_venue_boundary_v1 import NoncanonicalVenueRejectedError
from src.ops.bounded_testnet_runtime_market_observation_producer_v0 import (
    fetch_bounded_testnet_pf_ethusd_ticker_tick_v0,
    validate_testnet_public_ticker_request_url,
)


def test_fetch_current_operative_use_rejected() -> None:
    with pytest.raises(NoncanonicalVenueRejectedError):
        fetch_bounded_testnet_pf_ethusd_ticker_tick_v0(
            source_run_id="r",
            tick_index=0,
            sequence=0,
            fetcher=lambda url, timeout_seconds: (200, b"{}"),
        )


def test_canonical_url_validator_rejects_noncanonical_host() -> None:
    from src.ops.bounded_testnet_runtime_market_observation_producer_v0 import (
        RuntimeMarketObservationFailureClass,
    )

    assert (
        validate_testnet_public_ticker_request_url("http://example.invalid")
        == RuntimeMarketObservationFailureClass.TESTNET_HOST_NOT_ALLOWED
    )
