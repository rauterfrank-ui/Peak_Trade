"""Market Futures OHLCV runtime resolution (env + offline bundle), SSR-only."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .market_futures_ohlcv_readmodel_v0 import (
    MarketFuturesOhlcvReadmodelError,
    build_market_futures_ohlcv_readmodel,
)
from .market_futures_ohlcv_readmodel_v0.builder import READMODEL_ID

ENV_ENABLED = "PEAK_TRADE_MARKET_FUTURES_OHLCV_ENABLED"
ENV_BUNDLE_ROOT = "PEAK_TRADE_MARKET_FUTURES_OHLCV_BUNDLE_ROOT"


def enabled_explicitly_on() -> bool:
    raw = os.environ.get(ENV_ENABLED)
    return raw is not None and raw.strip() == "1"


def resolved_bundle_root_or_none() -> Path | None:
    raw = os.environ.get(ENV_BUNDLE_ROOT)
    if raw is None or not str(raw).strip():
        return None
    path = Path(raw).expanduser()
    try:
        path = path.resolve(strict=True)
    except OSError:
        return None
    if not path.is_dir():
        return None
    return path


def _base_context(*, gate_enabled: bool, display_status: str) -> dict[str, Any]:
    return {
        "gate_enabled": gate_enabled,
        "display_status": display_status,
        "readmodel_id": READMODEL_ID,
        "non_authorizing": True,
        "stale": True,
        "stale_reason": "",
        "source": "",
        "generated_at_iso": "",
        "series": {},
    }


def build_market_futures_ohlcv_display_context() -> dict[str, Any]:
    """SSR-only futures OHLCV readmodel context for GET /market (fail closed by default)."""
    if not enabled_explicitly_on():
        ctx = _base_context(gate_enabled=False, display_status="disabled")
        ctx["stale_reason"] = "source_disabled"
        return ctx

    bundle_root = resolved_bundle_root_or_none()
    if bundle_root is None:
        ctx = _base_context(gate_enabled=True, display_status="unconfigured")
        ctx["stale_reason"] = "bundle_root_unconfigured"
        return ctx

    try:
        readmodel = build_market_futures_ohlcv_readmodel(bundle_root)
    except MarketFuturesOhlcvReadmodelError:
        ctx = _base_context(gate_enabled=True, display_status="builder_error")
        ctx["stale_reason"] = "bundle_build_failed"
        return ctx

    series = readmodel.get("series") or {}
    has_series = bool(series)
    display_status = "ready" if has_series else "empty"

    return {
        "gate_enabled": True,
        "display_status": display_status,
        "readmodel_id": str(readmodel.get("readmodel_id", READMODEL_ID)),
        "non_authorizing": bool(readmodel.get("non_authorizing") is True),
        "stale": bool(readmodel.get("stale") is True),
        "stale_reason": str(readmodel.get("stale_reason") or ""),
        "source": str(readmodel.get("source", "")),
        "generated_at_iso": str(readmodel.get("generated_at_iso", "")),
        "series": series,
    }


def resolve_futures_ohlcv_series_for_symbol(
    *,
    futures_ohlcv: dict[str, Any],
    symbol: str,
    timeframe: str,
    limit: int,
) -> tuple[list[dict[str, Any]], str, bool]:
    """Return (bars, unavailable_reason, data_unavailable) for a governed futures symbol."""
    if futures_ohlcv.get("display_status") == "builder_error":
        return [], "futures_ohlcv_malformed", True
    if not futures_ohlcv.get("gate_enabled"):
        return [], "futures_ohlcv_unavailable", True
    if futures_ohlcv.get("display_status") == "unconfigured":
        return [], "futures_ohlcv_unconfigured", True

    series_map = futures_ohlcv.get("series")
    if not isinstance(series_map, dict):
        return [], "futures_ohlcv_unavailable", True

    series = series_map.get(symbol)
    if not isinstance(series, dict):
        return [], "futures_ohlcv_symbol_missing", True

    if futures_ohlcv.get("stale") is True:
        return [], "futures_ohlcv_stale", True

    series_timeframe = str(series.get("timeframe") or "").strip()
    if series_timeframe and series_timeframe != timeframe:
        return [], "futures_ohlcv_timeframe_mismatch", True

    bars_raw = series.get("bars")
    if not isinstance(bars_raw, list) or not bars_raw:
        return [], "futures_ohlcv_empty", True

    bars = bars_raw[-limit:] if limit > 0 else []
    return bars, "", False
