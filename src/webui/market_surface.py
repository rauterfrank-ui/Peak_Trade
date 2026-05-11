# src/webui/market_surface.py
"""
Read-only Market Surface v0 — öffentliche OHLCV + minimale Chart-UI.

- GET /market — HTML (Close-Line-Chart, Chart.js)
- GET /api/market/ohlcv — JSON (OHLCV-Bars)

GET /market embeds offline Market Depth read-model state SSR-only via
``market_depth_json_payload_v0`` (no in-page Depth JSON route, no fetch).

Keine Orders, kein OPS-Cockpit-Bezug. Dummy-Quelle für Offline/CI; Kraken über fetch_ohlcv_df.
"""

from __future__ import annotations

import importlib.util
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Literal

import pandas as pd
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .market_depth_runtime_v0 import market_depth_json_payload_v0

logger = logging.getLogger(__name__)

# Aligniert mit scripts/_shared_forward_args.OHLCV_TIMEFRAME_CHOICES / Kraken-ccxt-Übliches
MARKET_TIMEFRAMES: tuple[str, ...] = ("1m", "5m", "15m", "1h", "4h", "1d")
MAX_OHLCV_LIMIT = 720
MARKET_DEPTH_SSR_TOP_LEVELS = 8
DEFAULT_SYMBOL = "BTC/USD"
DEFAULT_TIMEFRAME = "1h"
DEFAULT_LIMIT = 120

_dummy_loader_mod: Any = None


def _get_shared_ohlcv_loader():
    """Lädt scripts/_shared_ohlcv_loader.py dynamisch (scripts ist kein Package)."""
    global _dummy_loader_mod
    if _dummy_loader_mod is not None:
        return _dummy_loader_mod
    root = Path(__file__).resolve().parents[2]
    path = root / "scripts" / "_shared_ohlcv_loader.py"
    if not path.is_file():
        raise RuntimeError(f"Erwartet: {path}")
    spec = importlib.util.spec_from_file_location("peak_trade_shared_ohlcv_loader", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Konnte _shared_ohlcv_loader nicht laden")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _dummy_loader_mod = mod
    return mod


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_source(raw: str) -> Literal["kraken", "dummy"]:
    key = (raw or "dummy").strip().lower()
    if key not in ("kraken", "dummy"):
        raise HTTPException(
            status_code=422,
            detail=f"source muss 'kraken' oder 'dummy' sein, nicht {raw!r}",
        )
    return key  # type: ignore[return-value]


def load_ohlcv_dataframe(
    *,
    symbol: str,
    timeframe: str,
    limit: int,
    source: Literal["kraken", "dummy"],
) -> tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Liefert OHLCV-DataFrame (DatetimeIndex UTC) und Meta-Hinweise.

    Dummy: load_dummy_ohlcv — synthetische 1h-Bars (timeframe-Query wird nur dokumentiert).
    Kraken: fetch_ohlcv_df — öffentliche REST-OHLCV.
    """
    meta: Dict[str, Any] = {}
    if source == "dummy":
        mod = _get_shared_ohlcv_loader()
        df = mod.load_dummy_ohlcv(symbol, n_bars=limit)
        meta["note"] = (
            "dummy: synthetische 1h-Bars; Parameter timeframe betrifft die Serie nicht "
            "(nur Kraken-Pfad nutzt timeframe)."
        )
        return df, meta

    from src.core.errors import CacheError, ProviderError
    from src.data.kraken import fetch_ohlcv_df

    try:
        df = fetch_ohlcv_df(
            symbol=symbol,
            timeframe=timeframe,
            limit=min(limit, MAX_OHLCV_LIMIT),
            use_cache=True,
        )
    except ProviderError as e:
        logger.warning("Kraken ProviderError: %s", e)
        raise HTTPException(status_code=503, detail=str(e)) from e
    except CacheError as e:
        logger.warning("Kraken CacheError: %s", e)
        raise HTTPException(status_code=503, detail=str(e)) from e

    return df, meta


def _sanitize_depth_level_item(item: object) -> Dict[str, str] | None:
    """Normalize a bid/ask level for template display only (strings, JSON-safe subset)."""

    if not isinstance(item, dict):
        return None

    raw_price = item.get("price")
    raw_size = item.get("size")
    if raw_price is None and raw_size is None:
        return None

    price = str(raw_price).strip()
    size = str(raw_size).strip()
    row: Dict[str, str] = {"price": price, "size": size}
    if "notional" in item and item["notional"] is not None:
        row["notional"] = str(item["notional"]).strip()
    return row


def _top_depth_level_rows(
    depth_obj: Any, *, limit: int
) -> tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    """Return sanitized top-N bids/asks from offline depth envelope (deterministic slicing only)."""

    if not isinstance(depth_obj, dict) or limit <= 0:
        return [], []

    bids_out: List[Dict[str, str]] = []
    asks_out: List[Dict[str, str]] = []

    raw_bids = depth_obj.get("bids")
    if isinstance(raw_bids, list):
        for it in raw_bids:
            if len(bids_out) >= limit:
                break
            row = _sanitize_depth_level_item(it)
            if row is not None and (row["price"] or row["size"]):
                bids_out.append(row)

    raw_asks = depth_obj.get("asks")
    if isinstance(raw_asks, list):
        for it in raw_asks:
            if len(asks_out) >= limit:
                break
            row = _sanitize_depth_level_item(it)
            if row is not None and (row["price"] or row["size"]):
                asks_out.append(row)

    return bids_out, asks_out


def dataframe_to_bars(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Serialisiert DataFrame mit open/high/low/close/volume in JSON-Bar-Objekte."""
    bars: List[Dict[str, Any]] = []
    for ts, row in df.iterrows():
        t_iso = pd.Timestamp(ts).isoformat()
        bars.append(
            {
                "ts": t_iso,
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["volume"]),
            }
        )
    return bars


def build_market_depth_display_context() -> Dict[str, Any]:
    """SSR-only snapshot for templates: tuple from helper, unchanged semantics."""

    top_limit = MARKET_DEPTH_SSR_TOP_LEVELS

    depth_http_status, depth_payload = market_depth_json_payload_v0()
    readmodel_id = str(depth_payload.get("readmodel_id", ""))

    top_bids: List[Dict[str, str]] = []
    top_asks: List[Dict[str, str]] = []
    summary_line = ""

    if depth_http_status == 200:
        display_status = "ok"
        depth_obj = depth_payload.get("depth") or {}
        levels = (
            depth_obj.get("levels_returned")
            if isinstance(depth_obj.get("levels_returned"), dict)
            else {}
        )
        bids_n = levels.get("bids", "—")
        asks_n = levels.get("asks", "—")
        sym = depth_payload.get("symbol", "")
        summary_line = f"{sym} — bids {bids_n}, asks {asks_n} (offline bundle, read-only display)"
        if isinstance(depth_obj, dict):
            top_bids, top_asks = _top_depth_level_rows(depth_obj, limit=top_limit)
    else:
        display_status = str(depth_payload.get("runtime_source_status", "unavailable"))
        warnings = depth_payload.get("warnings")
        if isinstance(warnings, list) and warnings:
            summary_line = str(warnings[0])
        else:
            summary_line = str(depth_payload.get("stale_reason", display_status))

    has_depth_levels = len(top_bids) > 0 or len(top_asks) > 0

    return {
        "depth_http_status": depth_http_status,
        "display_status": display_status,
        "readmodel_id": readmodel_id,
        "summary_line": summary_line,
        "top_bids": top_bids,
        "top_asks": top_asks,
        "top_levels_limit": top_limit,
        "has_depth_levels": has_depth_levels,
    }


def build_market_payload(
    *,
    symbol: str,
    timeframe: str,
    limit: int,
    source: Literal["kraken", "dummy"],
) -> Dict[str, Any]:
    df, meta = load_ohlcv_dataframe(symbol=symbol, timeframe=timeframe, limit=limit, source=source)
    bars = dataframe_to_bars(df)
    return {
        "generated_at_utc": _utc_now_iso(),
        "source": source,
        "symbol": symbol,
        "timeframe": timeframe,
        "limit_requested": limit,
        "bars_returned": len(bars),
        "meta": meta,
        "bars": bars,
    }


def create_market_router(
    templates: Jinja2Templates,
    get_project_status: Callable[[], Dict[str, Any]],
) -> APIRouter:
    router = APIRouter(tags=["market-readonly"])

    @router.get("/api/market/ohlcv")
    async def api_market_ohlcv(
        symbol: str = Query(DEFAULT_SYMBOL, description="Trading-Paar, z.B. BTC/USD"),
        timeframe: str = Query(
            DEFAULT_TIMEFRAME,
            description="Timeframe (Kraken); Dummy ignoriert (synthetisch 1h)",
        ),
        limit: int = Query(
            DEFAULT_LIMIT,
            ge=1,
            le=MAX_OHLCV_LIMIT,
            description="Anzahl Bars (max 720)",
        ),
        source: str = Query(
            "dummy",
            description="dummy = offline synthetisch; kraken = öffentliche OHLCV",
        ),
    ) -> Dict[str, Any]:
        if timeframe not in MARKET_TIMEFRAMES:
            raise HTTPException(
                status_code=422,
                detail=f"timeframe muss einer von {list(MARKET_TIMEFRAMES)} sein, nicht {timeframe!r}",
            )
        src = _normalize_source(source)
        return build_market_payload(symbol=symbol, timeframe=timeframe, limit=limit, source=src)

    @router.get("/market", response_class=HTMLResponse)
    async def market_v0_page(
        request: Request,
        symbol: str = Query(DEFAULT_SYMBOL),
        timeframe: str = Query(DEFAULT_TIMEFRAME),
        limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_OHLCV_LIMIT),
        source: str = Query("dummy"),
    ) -> Any:
        if timeframe not in MARKET_TIMEFRAMES:
            raise HTTPException(
                status_code=422,
                detail=f"timeframe muss einer von {list(MARKET_TIMEFRAMES)} sein, nicht {timeframe!r}",
            )
        src = _normalize_source(source)
        payload = build_market_payload(symbol=symbol, timeframe=timeframe, limit=limit, source=src)
        proj_status = get_project_status()
        market_depth = build_market_depth_display_context()
        return templates.TemplateResponse(
            request,
            "market_v0.html",
            {
                "status": proj_status,
                "payload": payload,
                "market_depth": market_depth,
                "query": {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "limit": limit,
                    "source": src,
                },
            },
        )

    return router
