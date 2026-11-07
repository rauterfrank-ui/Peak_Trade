"""Market truth projection from okx_selected_instrument_ohlcv_readmodel.v1 only."""

from __future__ import annotations

from datetime import datetime, timezone
import math
from typing import Any, Mapping

from src.ops.okx_captured_at_freshness_policy_v1 import (
    classify_freshness_v1,
    load_freshness_policy_v1,
)


def _positive_price(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        price = float(value)
    except (TypeError, ValueError):
        return None
    return price if math.isfinite(price) and price > 0 else None


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
            "last_price_kind": "UNAVAILABLE",
            "last_price_freshness": "UNKNOWN",
            "last_price_timestamp": None,
            "live_mark_price": None,
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
    # The original producer emits a decimal string, independently of positions.
    # Preserve the older object shape as an input compatibility surface only.
    if isinstance(live_mark, Mapping):
        live_mark = (
            live_mark.get("price")
            if live_mark.get("price") is not None
            else live_mark.get("mark_px")
        )
    mark_price = _positive_price(live_mark)
    mark_captured = ohlcv.get("live_mark_captured_at")
    mark_event = ohlcv.get("live_mark_provider_ts")
    mark_freshness = "UNKNOWN"
    if mark_price is not None and mark_captured:
        try:
            verdict, _, _ = classify_freshness_v1(
                reference_at=mark_captured,
                as_of=observed_at,
                source_type="reference_mark_price",
                policy=load_freshness_policy_v1(),
            )
            mark_freshness = verdict.upper()
        except (ValueError, TypeError, AttributeError, OverflowError):
            mark_freshness = "UNKNOWN"
    if mark_price is not None:
        last_price = mark_price

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
        "last_price_kind": "MARK_PRICE"
        if mark_price is not None
        else ("CANDLE_CLOSE" if series else "UNAVAILABLE"),
        "last_price_freshness": mark_freshness if mark_price is not None else freshness,
        "last_price_timestamp": (mark_event or mark_captured)
        if mark_price is not None
        else ohlcv.get("last_timestamp"),
        "live_mark_price": mark_price,
        "live_mark_captured_at": mark_captured,
        "live_mark_provider_ts": mark_event,
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
