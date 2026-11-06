"""Market truth projection from okx_selected_instrument_ohlcv_readmodel.v1 only."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping


def _parse_bar_time_unix(bar: Mapping[str, Any]) -> int | None:
    ms_raw = bar.get("provider_ts_ms")
    if ms_raw is not None:
        try:
            return int(int(str(ms_raw)) / 1000)
        except ValueError:
            pass
    ts_raw = bar.get("ts")
    if isinstance(ts_raw, str) and ts_raw.strip():
        text = ts_raw.strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(text)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return int(dt.timestamp())
        except ValueError:
            return None
    return None


def project_market_state_from_ohlcv_doc(
    ohlcv: Mapping[str, Any] | None,
    *,
    refresh_meta: Mapping[str, Any] | None,
    observed_at: str,
) -> dict[str, Any]:
    """Map CURRENT OHLCV readmodel document to canonical MarketState (no fabrication)."""
    if ohlcv is None:
        return {
            "instrument": None,
            "okx_inst_id": None,
            "last_price": None,
            "candle_series": [],
            "interval": None,
            "market_timestamp": None,
            "market_observed_at": observed_at,
            "market_freshness": "UNKNOWN",
            "connection_status": "MISSING_SOURCE",
            "refresh_status": None if refresh_meta is None else refresh_meta.get("status"),
            "source_producer": "okx_selected_instrument_ohlcv_readmodel.v1",
            "classification": "UNKNOWN_CURRENT",
        }

    inst = str(ohlcv.get("instrument_id") or "") or None
    okx_inst = str(ohlcv.get("provider_instrument_id") or "") or None
    bars_in = ohlcv.get("bars")
    series: list[dict[str, Any]] = []
    if isinstance(bars_in, list):
        for raw in bars_in:
            if not isinstance(raw, Mapping):
                continue
            t = _parse_bar_time_unix(raw)
            if t is None:
                continue
            try:
                series.append(
                    {
                        "time": t,
                        "open": float(raw.get("open")),
                        "high": float(raw.get("high")),
                        "low": float(raw.get("low")),
                        "close": float(raw.get("close")),
                    }
                )
            except (TypeError, ValueError):
                continue

    last_price = None
    if series:
        last_price = series[-1]["close"]
    live_mark = ohlcv.get("live_mark_price")
    if isinstance(live_mark, Mapping):
        lp = live_mark.get("price") or live_mark.get("mark_px")
        if lp is not None:
            try:
                last_price = float(lp)
            except (TypeError, ValueError):
                pass

    freshness = str(ohlcv.get("freshness_state") or "UNKNOWN").upper()
    if bool(ohlcv.get("is_stale")):
        freshness = "STALE"

    connection = "HEALTHY"
    if freshness == "STALE":
        connection = "STALE"
    elif not series:
        connection = "DEGRADED"

    return {
        "instrument": inst,
        "okx_inst_id": okx_inst,
        "last_price": last_price,
        "candle_series": series,
        "interval": ohlcv.get("interval"),
        "market_timestamp": ohlcv.get("last_timestamp") or ohlcv.get("captured_at"),
        "market_observed_at": observed_at,
        "market_freshness": freshness,
        "connection_status": connection,
        "refresh_status": None if refresh_meta is None else refresh_meta.get("status"),
        "source_producer": "okx_selected_instrument_ohlcv_readmodel.v1",
        "classification": "PROVEN_CURRENT" if okx_inst and series else "UNKNOWN_CURRENT",
    }
