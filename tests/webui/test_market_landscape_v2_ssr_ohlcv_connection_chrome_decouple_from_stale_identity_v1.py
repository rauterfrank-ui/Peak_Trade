"""SSR OHLCV connection chrome must not inherit instrument-identity STALE.

Capability:
MARKET_LANDSCAPE_V2_SSR_OHLCV_CONNECTION_CHROME_DECOUPLE_FROM_STALE_IDENTITY_V1

Presentation-only: identity freshness and OHLCV/O5 connection state stay separate.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from src.webui.market_dashboard_landscape_v2 import (
    Availability,
    MarketDashboardReadServiceV1,
    present_market_landscape_v2,
)
from src.webui.market_dashboard_landscape_v2.presenter import (
    _chart_availability_for_ohlcv,
    _ohlcv_data_connection_state,
    serialize_ohlcv_browser_payload_v1,
)
from src.webui.market_dashboard_landscape_v2.projections import (
    project_market_instrument_snapshot_v1,
)

STAMP = datetime(2026, 8, 4, 15, 0, 0, tzinfo=timezone.utc)
INSTRUMENT = "ETH-USDT-SWAP"


def _stale_instrument() -> Any:
    return project_market_instrument_snapshot_v1(
        instrument_id=INSTRUMENT,
        venue="okx",
        market_type="perpetual",
        mark_price=None,
        reason_codes=("PRODUCER_DATA_STALE",),
        generated_at=STAMP,
        effective_at=STAMP,
        source_reference="test://stale_instrument",
        availability=Availability.STALE,
        is_stale=True,
        stale_reason="PRODUCER_DATA_STALE",
    )


def _fresh_instrument() -> Any:
    return project_market_instrument_snapshot_v1(
        instrument_id=INSTRUMENT,
        venue="okx",
        market_type="perpetual",
        mark_price=None,
        reason_codes=(),
        generated_at=STAMP,
        effective_at=STAMP,
        source_reference="test://fresh_instrument",
        availability=Availability.AVAILABLE,
        is_stale=False,
    )


def _ohlcv(
    *,
    freshness_state: str = "fresh",
    is_stale: bool = False,
    live: bool = False,
) -> dict[str, Any]:
    tip_confirm = False if live else True
    payload: dict[str, Any] = {
        "schema_name": "okx_selected_instrument_ohlcv_readmodel.v1",
        "schema_version": 1,
        "venue": "okx",
        "instrument_id": INSTRUMENT,
        "interval": "PT1M",
        "captured_at": "2026-08-04T15:00:00Z",
        "candle_captured_at": "2026-08-04T15:00:00Z",
        "effective_at": "2026-08-04T15:00:00Z",
        "freshness_state": freshness_state,
        "is_stale": is_stale,
        "bar_count": 2,
        "bars": [
            {
                "ts": "2026-08-04T14:58:00Z",
                "open": "100",
                "high": "101",
                "low": "99",
                "close": "100.5",
                "volume": "10",
                "confirm": True,
            },
            {
                "ts": "2026-08-04T14:59:00Z",
                "open": "100.5",
                "high": "102",
                "low": "100",
                "close": "101",
                "volume": "12",
                "confirm": tip_confirm,
            },
        ],
    }
    if live:
        payload["open_candle_live_source"] = "okx_public_trades_into_pt1m_v1"
        payload["candle_endpoint"] = "https://www.okx.com/api/v5/market/candles"
        payload["trades_endpoint"] = "https://www.okx.com/api/v5/market/trades"
    return payload


def _page(*, instrument: Any) -> Any:
    return MarketDashboardReadServiceV1().load_page_snapshot(
        generated_at=STAMP,
        git_sha=None,
        slot_overrides={"market_instrument": instrument},
    )


def test_chart_availability_helper_is_ohlcv_only() -> None:
    assert _chart_availability_for_ohlcv(None) is Availability.MISSING_SOURCE
    assert _chart_availability_for_ohlcv({}) is Availability.MISSING_SOURCE
    assert _chart_availability_for_ohlcv(_ohlcv()) is Availability.AVAILABLE
    assert (
        _chart_availability_for_ohlcv(_ohlcv(freshness_state="stale", is_stale=True))
        is Availability.STALE
    )


def test_case1_instrument_stale_ohlcv_fresh_o5_healthy_connection_not_stale() -> None:
    """Instrument STALE + OHLCV fresh/AVAILABLE + O5 HEALTHY → connection HEALTHY."""
    ohlcv = _ohlcv(live=True)
    page = _page(instrument=_stale_instrument())
    ctx = present_market_landscape_v2(
        page,
        ohlcv_readmodel=ohlcv,
        adapted_ohlcv_connection_state="HEALTHY",
    )
    assert ctx["market"]["availability"] == "STALE"
    assert ctx["market"]["is_stale"] is True
    assert ctx["chart"]["availability"] == "AVAILABLE"
    assert ctx["chart"]["data_connection_state"] == "HEALTHY"
    assert ctx["chart"]["data_connection_state"] != "STALE"


def test_case2_instrument_fresh_ohlcv_stale_connection_stale() -> None:
    ohlcv = _ohlcv(freshness_state="stale", is_stale=True)
    page = _page(instrument=_fresh_instrument())
    ctx = present_market_landscape_v2(
        page,
        ohlcv_readmodel=ohlcv,
        adapted_ohlcv_connection_state="STALE",
    )
    assert ctx["market"]["availability"] == "AVAILABLE"
    assert ctx["chart"]["availability"] == "STALE"
    assert ctx["chart"]["data_connection_state"] == "STALE"


def test_case3_instrument_stale_ohlcv_missing_connection_missing_source() -> None:
    page = _page(instrument=_stale_instrument())
    ctx = present_market_landscape_v2(page, ohlcv_readmodel=None)
    assert ctx["market"]["availability"] == "STALE"
    assert ctx["chart"]["availability"] == "MISSING_SOURCE"
    assert ctx["chart"]["data_connection_state"] == "MISSING_SOURCE"


def test_case4_instrument_stale_ohlcv_unhealthy_stays_honest() -> None:
    ohlcv = _ohlcv(freshness_state="stale", is_stale=True)
    page = _page(instrument=_stale_instrument())
    ctx = present_market_landscape_v2(
        page,
        ohlcv_readmodel=ohlcv,
        adapted_ohlcv_connection_state="STALE",
    )
    assert ctx["market"]["availability"] == "STALE"
    assert ctx["chart"]["availability"] == "STALE"
    assert ctx["chart"]["data_connection_state"] == "STALE"


def test_case5_no_ohlcv_o5_evidence_never_invents_healthy() -> None:
    page = _page(instrument=_stale_instrument())
    ctx = present_market_landscape_v2(
        page,
        ohlcv_readmodel=None,
        adapted_ohlcv_connection_state="HEALTHY",
    )
    assert ctx["chart"]["data_connection_state"] != "HEALTHY"
    assert ctx["chart"]["data_connection_state"] == "MISSING_SOURCE"

    assert (
        _ohlcv_data_connection_state(
            browser_payload=None,
            ohlcv_payload=None,
            chart_availability=Availability.MISSING_SOURCE,
            adapted_connection_state="HEALTHY",
        )
        == "MISSING_SOURCE"
    )


def test_shell_ssr_path_decouples_identity_stale_from_ohlcv_connection() -> None:
    """Shell SSR O5 availability input must come from OHLCV, not instrument STALE."""
    from src.webui.market_dashboard_landscape_shell_router_v2 import (
        _chart_availability_for_ohlcv,
    )
    from src.ops.canonical_read_model_and_market_dashboard_rebuild_v1.ohlcv_adapter_v1 import (
        adapt_derived_ohlcv_payload_to_o5_read_model_v1,
    )

    ohlcv = _ohlcv(live=True)
    # Identity STALE must not be passed into O5 adaptation for connection chrome.
    chart_availability = _chart_availability_for_ohlcv(ohlcv)
    assert chart_availability is Availability.AVAILABLE
    o5 = adapt_derived_ohlcv_payload_to_o5_read_model_v1(
        ohlcv,
        projection_time_unix=STAMP.timestamp(),
        availability=chart_availability.value,
    )
    assert o5["connection_state"] == "HEALTHY"
    browser = serialize_ohlcv_browser_payload_v1(ohlcv)
    assert (
        _ohlcv_data_connection_state(
            browser_payload=browser,
            ohlcv_payload=ohlcv,
            chart_availability=chart_availability,
            adapted_connection_state=str(o5["connection_state"]),
        )
        == "HEALTHY"
    )
    # Contrast: legacy bug path would have forced STALE via instrument availability.
    assert (
        _ohlcv_data_connection_state(
            browser_payload=browser,
            ohlcv_payload=ohlcv,
            chart_availability=Availability.STALE,
            adapted_connection_state="HEALTHY",
        )
        == "STALE"
    )
