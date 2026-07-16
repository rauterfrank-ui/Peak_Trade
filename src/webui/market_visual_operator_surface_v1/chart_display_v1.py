"""Phase 3 Market Chart display adapter (presentation-only).

Formats chart meta, window links, gap markers, and overlay states from existing
canonical OHLCV/payload contexts. No trading/decision/risk semantics and no new
market-data producers.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode

_UNAVAILABLE = "unavailable"
_SUPPORTED_WINDOWS: tuple[int | str, ...] = (50, 120, 250, "ALL")
_TIMEFRAME_SECONDS: dict[str, int] = {
    "1m": 60,
    "5m": 300,
    "15m": 900,
    "1h": 3600,
    "4h": 14400,
    "1d": 86400,
}


def _text(value: Any, *, default: str = _UNAVAILABLE) -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _parse_ts(raw: Any) -> datetime | None:
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        return None


def _detect_gap_indices(bars: list[dict[str, Any]], timeframe: str) -> list[int]:
    """Return bar indices that begin after an explicit missing interval.

    Gaps are detected from real timestamps only. Missing bars are never invented.
    """
    step = _TIMEFRAME_SECONDS.get(timeframe)
    if not step or len(bars) < 2:
        return []
    expected = timedelta(seconds=step)
    # Allow small clock skew; flag only clear multi-interval holes.
    threshold = expected * 1.5
    gaps: list[int] = []
    prev = _parse_ts(bars[0].get("ts"))
    for idx in range(1, len(bars)):
        cur = _parse_ts(bars[idx].get("ts"))
        if prev is None or cur is None:
            prev = cur
            continue
        if cur - prev > threshold:
            gaps.append(idx)
        prev = cur
    return gaps


def _window_href(
    *,
    symbol: str,
    source: str,
    timeframe: str,
    top_n: int,
    window: int | str,
    max_limit: int,
) -> str:
    limit = max_limit if window == "ALL" else int(window)
    params = [
        ("source", source or "futures"),
        ("timeframe", timeframe or "1h"),
        ("limit", str(limit)),
        ("top_n", str(top_n or 20)),
    ]
    if symbol:
        params.insert(1, ("symbol", symbol))
    return "/market?" + urlencode(params)


def _classify_source(source: str) -> str:
    text = (source or "").strip().lower()
    if not text or text == _UNAVAILABLE:
        return "UNAVAILABLE"
    if text.startswith("fixture:") or "complete_minimal" in text or text.startswith("test_"):
        return "TEST_FIXTURE"
    if text.startswith("historical_panel_offline:"):
        return "CANONICAL_LOCAL_READ_ONLY_BUNDLE"
    return "UNKNOWN"


def _freshness_state(freshness: str) -> str:
    dt = _parse_ts(freshness)
    if dt is None:
        return "UNAVAILABLE" if freshness in ("", _UNAVAILABLE) else "INVALID"
    now = datetime.now(timezone.utc)
    if dt > now + timedelta(minutes=5):
        return "INVALID_FUTURE"
    return "OK"


def build_chart_display_v1(
    *,
    payload: dict[str, Any] | None = None,
    primary_values: dict[str, Any] | None = None,
    selected_instrument_workspace: dict[str, Any] | None = None,
    futures_ohlcv: dict[str, Any] | None = None,
    query: dict[str, Any] | None = None,
    max_ohlcv_limit: int = 720,
    default_visible_bars: int = 120,
) -> dict[str, Any]:
    """Build Phase-3 chart presentation VM from existing contexts only."""
    payload = payload if isinstance(payload, dict) else {}
    primary = primary_values if isinstance(primary_values, dict) else {}
    workspace = (
        selected_instrument_workspace if isinstance(selected_instrument_workspace, dict) else {}
    )
    futures = futures_ohlcv if isinstance(futures_ohlcv, dict) else {}
    query = query if isinstance(query, dict) else {}
    meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}

    bars_raw = payload.get("bars") if isinstance(payload.get("bars"), list) else []
    bars = [b for b in bars_raw if isinstance(b, dict)]
    bars_returned = int(payload.get("bars_returned") or len(bars) or 0)
    timeframe = _text(
        primary.get("timeframe") or query.get("timeframe") or payload.get("timeframe")
    )
    symbol = _text(primary.get("symbol") or payload.get("symbol") or query.get("symbol"))
    source = _text(
        meta.get("data_source") or futures.get("source") or payload.get("source"),
        default="unavailable",
    )
    source_class = _classify_source(source)
    freshness = _text(
        primary.get("generated_at_utc")
        or meta.get("freshness")
        or futures.get("generated_at_iso")
        or payload.get("generated_at_utc")
    )
    freshness_state = _freshness_state(freshness)
    ohlcv_status = _text(workspace.get("ohlcv_status"), default="unavailable")
    if bars_returned == 0 and ohlcv_status in (_UNAVAILABLE, "ready"):
        ohlcv_status = "empty" if payload.get("bars_returned") == 0 else ohlcv_status

    limit_requested = int(
        query.get("limit") or payload.get("limit_requested") or default_visible_bars
    )
    active_window: int | str
    if limit_requested >= max_ohlcv_limit:
        active_window = "ALL"
    elif limit_requested in (50, 120, 250):
        active_window = limit_requested
    else:
        active_window = limit_requested

    top_n = int(query.get("top_n") or 20)
    window_controls = []
    for window in _SUPPORTED_WINDOWS:
        href = _window_href(
            symbol=symbol if symbol != _UNAVAILABLE else "",
            source=_text(query.get("source") or payload.get("source"), default="futures"),
            timeframe=timeframe if timeframe != _UNAVAILABLE else "1h",
            top_n=top_n,
            window=window,
            max_limit=max_ohlcv_limit,
        )
        window_controls.append(
            {
                "label": str(window),
                "href": href,
                "active": active_window == window
                or (window == "ALL" and active_window == "ALL")
                or (window != "ALL" and active_window == window),
                "supported": True,
            }
        )

    gap_indices = _detect_gap_indices(bars, timeframe if timeframe != _UNAVAILABLE else "")
    gap_count = len(gap_indices)

    stale = ohlcv_status == "stale" or bool(futures.get("stale") is True)
    missing = ohlcv_status in ("missing", "empty", "unavailable") and bars_returned == 0
    malformed = ohlcv_status == "malformed"

    overlay_state = "none"
    if stale:
        overlay_state = "stale"
    elif freshness_state == "INVALID_FUTURE":
        overlay_state = "missing"
    elif malformed:
        overlay_state = "malformed"
    elif missing:
        overlay_state = "missing"

    canonical_real = (
        source_class == "CANONICAL_LOCAL_READ_ONLY_BUNDLE"
        and bars_returned > 0
        and freshness_state != "INVALID_FUTURE"
    )

    last_bar = bars[-1] if bars else {}
    return {
        "section_visible": True,
        "phase": "PHASE_3",
        "read_only": True,
        "render_mode": "SSR_SVG",
        "chart_library": "SSR_SVG",
        "selected_symbol": symbol,
        "timeframe": timeframe,
        "source": source,
        "source_class": source_class,
        "freshness": freshness,
        "freshness_state": freshness_state,
        "timezone": "UTC",
        "timezone_visible": True,
        "bar_count": bars_returned,
        "limit_requested": limit_requested,
        "default_visible_bars": default_visible_bars,
        "active_window": str(active_window),
        "window_controls": window_controls,
        "supported_windows": ["50", "120", "250", "ALL"],
        "ohlcv_status": ohlcv_status,
        "overlay_state": overlay_state,
        "stale": stale,
        "missing": missing,
        "malformed": malformed,
        "has_real_bars": bars_returned > 0 and source_class != "TEST_FIXTURE",
        "gap_indices": gap_indices,
        "gap_count": gap_count,
        "gap_rendering_policy": "EXPLICIT",
        "no_visual_interpolation": True,
        "candle_chart_real_data": canonical_real,
        "volume_real_data": canonical_real,
        "selected_instrument_sync": symbol != _UNAVAILABLE
        and symbol == _text(payload.get("symbol"), default=symbol),
        "last_ohlc": {
            "open": _text(last_bar.get("open"), default="—"),
            "high": _text(last_bar.get("high"), default="—"),
            "low": _text(last_bar.get("low"), default="—"),
            "close": _text(last_bar.get("close"), default="—"),
            "volume": _text(last_bar.get("volume"), default="—"),
            "ts": _text(last_bar.get("ts")),
        },
        "price_precision_source_bound": False,
        "price_precision_note": "display heuristic from range; tick_size not instrument-bound in chart SVG",
        "contracts": {
            "DEFAULT_VISIBLE_BARS": default_visible_bars,
            "SUPPORTED_CHART_WINDOWS": "50,120,250,ALL",
            "GAP_RENDERING_POLICY": "EXPLICIT",
            "NO_VISUAL_INTERPOLATION_OF_MISSING_BARS": True,
            "STALE_DATA_OVERLAY_REQUIRED": True,
            "TIMEZONE_VISIBLE": True,
            "SOURCE_CLASS_REQUIRED_FOR_REAL_DATA": "CANONICAL_LOCAL_READ_ONLY_BUNDLE",
        },
    }


__all__ = ["build_chart_display_v1"]
