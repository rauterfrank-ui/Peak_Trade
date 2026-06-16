"""Offline read-only Market Futures OHLCV readmodel v0 builder."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

READMODEL_ID = "market_futures_ohlcv_readmodel.v0"
FORBIDDEN_BAR_FIELDS = {
    "order_id",
    "side",
    "quantity",
    "leverage",
    "approval",
    "approved",
    "live_authorized",
    "strategy_activation",
}


class MarketFuturesOhlcvReadmodelError(ValueError):
    """Raised when the futures OHLCV readmodel payload is invalid."""


def _as_mapping(value: Any, *, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise MarketFuturesOhlcvReadmodelError(f"{field} must be an object")
    return value


def _as_bool(value: Any, *, field: str) -> bool:
    if not isinstance(value, bool):
        raise MarketFuturesOhlcvReadmodelError(f"{field} must be a boolean")
    return value


def _as_string(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MarketFuturesOhlcvReadmodelError(f"{field} must be a non-empty string")
    return value


def _as_optional_string(value: Any, *, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise MarketFuturesOhlcvReadmodelError(f"{field} must be a string or null")
    return value


def _as_float(value: Any, *, field: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise MarketFuturesOhlcvReadmodelError(f"{field} must be numeric")
    return float(value)


def _normalize_bar(bar: Any, *, index: int) -> dict[str, Any]:
    bar_map = _as_mapping(bar, field=f"bars[{index}]")
    forbidden = sorted(FORBIDDEN_BAR_FIELDS.intersection(bar_map))
    if forbidden:
        raise MarketFuturesOhlcvReadmodelError(
            f"bars[{index}] contains forbidden fields: {', '.join(forbidden)}"
        )
    return {
        "ts": _as_string(bar_map.get("ts"), field=f"bars[{index}].ts"),
        "open": _as_float(bar_map.get("open"), field=f"bars[{index}].open"),
        "high": _as_float(bar_map.get("high"), field=f"bars[{index}].high"),
        "low": _as_float(bar_map.get("low"), field=f"bars[{index}].low"),
        "close": _as_float(bar_map.get("close"), field=f"bars[{index}].close"),
        "volume": _as_float(bar_map.get("volume"), field=f"bars[{index}].volume"),
    }


def _normalize_series(value: Any, *, symbol: str) -> dict[str, Any]:
    series_map = _as_mapping(value, field=f"series.{symbol}")
    bars_raw = series_map.get("bars")
    if not isinstance(bars_raw, list):
        raise MarketFuturesOhlcvReadmodelError(f"series.{symbol}.bars must be a list")
    bars = [_normalize_bar(bar, index=index) for index, bar in enumerate(bars_raw)]
    timeframe = _as_string(series_map.get("timeframe"), field=f"series.{symbol}.timeframe")
    return {"timeframe": timeframe, "bars": bars}


def build_market_futures_ohlcv_readmodel(bundle_root: str | Path) -> dict[str, Any]:
    """Build a deterministic, read-only futures OHLCV readmodel from an offline bundle."""
    root = Path(bundle_root)
    payload_path = root / "futures_ohlcv.json"
    if not payload_path.is_file():
        raise MarketFuturesOhlcvReadmodelError(f"missing futures OHLCV payload: {payload_path}")

    try:
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise MarketFuturesOhlcvReadmodelError(f"invalid JSON: {exc}") from exc

    payload_map = _as_mapping(payload, field="payload")
    readmodel_id = _as_string(payload_map.get("readmodel_id"), field="readmodel_id")
    if readmodel_id != READMODEL_ID:
        raise MarketFuturesOhlcvReadmodelError(f"readmodel_id must be {READMODEL_ID!r}")

    non_authorizing = _as_bool(payload_map.get("non_authorizing"), field="non_authorizing")
    if not non_authorizing:
        raise MarketFuturesOhlcvReadmodelError("non_authorizing must be true")

    series_raw = _as_mapping(payload_map.get("series"), field="series")
    normalized_series = {
        symbol: _normalize_series(series_raw[symbol], symbol=symbol)
        for symbol in sorted(series_raw)
    }

    return {
        "readmodel_id": readmodel_id,
        "generated_at_iso": _as_string(
            payload_map.get("generated_at_iso"),
            field="generated_at_iso",
        ),
        "source": _as_string(payload_map.get("source"), field="source"),
        "stale": _as_bool(payload_map.get("stale"), field="stale"),
        "stale_reason": _as_optional_string(
            payload_map.get("stale_reason"),
            field="stale_reason",
        ),
        "non_authorizing": non_authorizing,
        "series": normalized_series,
    }
