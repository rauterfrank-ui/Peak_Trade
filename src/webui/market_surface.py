# src/webui/market_surface.py
"""
Read-only Market Surface v0 — öffentliche OHLCV + minimale Chart-UI.

- GET /market — HTML (Close-Line-Chart, Chart.js)
- GET /api/market/ohlcv — JSON (OHLCV-Bars)

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

logger = logging.getLogger(__name__)

# Aligniert mit scripts/_shared_forward_args.OHLCV_TIMEFRAME_CHOICES / Kraken-ccxt-Übliches
MARKET_TIMEFRAMES: tuple[str, ...] = ("1m", "5m", "15m", "1h", "4h", "1d")
MAX_OHLCV_LIMIT = 720
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
        return templates.TemplateResponse(
            request,
            "market_v0.html",
            {
                "status": proj_status,
                "payload": payload,
                "query": {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "limit": limit,
                    "source": src,
                },
            },
        )

    return router
