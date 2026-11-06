"""Staleness acceptance authority for bounded Run-001 public MD path."""

from __future__ import annotations

import pytest

from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.constants_v1 import (
    DEFAULT_MAX_STALE_SECONDS,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.error_classes_v1 import (
    MarketDataBindingErrorV1,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.mark_price_contract_v1 import (
    parse_public_mark_price_response_v1,
)


def _payload(ts_ms: int) -> dict:
    return {
        "code": "0",
        "data": [{"instId": "ETH-USD-SWAP", "markPx": "3500", "ts": str(ts_ms)}],
    }


def test_six_seconds_stale_rejected_at_authoritative_threshold() -> None:
    receive = 1_700_000_010.0
    event_ms = int((receive - 6.0) * 1000)
    with pytest.raises(MarketDataBindingErrorV1, match="MARKET_DATA_STALE"):
        parse_public_mark_price_response_v1(
            _payload(event_ms),
            expected_venue_instrument_id="ETH-USD-SWAP",
            receive_ts_unix=receive,
            max_stale_seconds=float(DEFAULT_MAX_STALE_SECONDS),
        )


def test_four_seconds_stale_accepted() -> None:
    receive = 1_700_000_010.0
    event_ms = int((receive - 4.0) * 1000)
    parsed = parse_public_mark_price_response_v1(
        _payload(event_ms),
        expected_venue_instrument_id="ETH-USD-SWAP",
        receive_ts_unix=receive,
        max_stale_seconds=float(DEFAULT_MAX_STALE_SECONDS),
    )
    assert parsed.mark_px == 3500.0
