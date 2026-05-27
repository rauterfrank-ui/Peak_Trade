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
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Literal

import pandas as pd
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .market_depth_runtime_v0 import market_depth_json_payload_v0
from .market_ranking_funnel_runtime_v0 import build_market_ranking_funnel_display_context

logger = logging.getLogger(__name__)

# Aligniert mit scripts/_shared_forward_args.OHLCV_TIMEFRAME_CHOICES (übliche Timeframes)
MARKET_TIMEFRAMES: tuple[str, ...] = ("1m", "5m", "15m", "1h", "4h", "1d")
MAX_OHLCV_LIMIT = 720
MARKET_DEPTH_SSR_TOP_LEVELS = 8
DEFAULT_SYMBOL = "BTC/USD"
DEFAULT_TIMEFRAME = "1h"
DEFAULT_LIMIT = 120

MARKET_RUN_PROJECTION_ENABLED_ENV = "PEAK_TRADE_MARKET_RUN_PROJECTION_ENABLED"
MARKET_RUN_PROJECTION_PAYLOAD_JSON_ENV = "PEAK_TRADE_MARKET_RUN_PROJECTION_PAYLOAD_JSON"
PROJECTION_PAYLOAD_SCHEMA_V0 = "peak_trade.post_closeout_projection_payload.v0"
REGISTRY_V1_SCHEMA = "peak_trade.generic_evidence_run_registry.v1"

RUN_PROJECTION_REGISTRY_FIELDS: tuple[str, ...] = (
    "run_id",
    "lane_id",
    "runtime_host",
    "runtime_backend",
    "runtime_mode",
    "evidence_root_type",
    "evidence_transport",
    "evidence_status",
    "review_verdict",
    "manifest_verified",
    "archive_path",
    "market_dashboard_projection",
)

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


def _sanitize_depth_bundle_provenance(display_envelope: Dict[str, Any]) -> Dict[str, Any]:
    """Extract already-present Depth JSON envelope provenance fields for SSR templates only."""

    ga = display_envelope.get("generated_at_iso")
    depth_generated_at_iso = ""
    if ga is not None:
        depth_generated_at_iso = str(ga).strip()
        if len(depth_generated_at_iso) > 200:
            depth_generated_at_iso = f"{depth_generated_at_iso[:197]}..."

    stale_raw = display_envelope.get("stale")
    depth_stale = stale_raw is True

    sr = display_envelope.get("stale_reason")
    depth_stale_reason = ""
    if sr is not None:
        depth_stale_reason = str(sr).strip()
        if len(depth_stale_reason) > 500:
            depth_stale_reason = f"{depth_stale_reason[:497]}..."

    bs = display_envelope.get("source")
    depth_bundle_source = ""
    if bs is not None:
        depth_bundle_source = str(bs).strip()
        if len(depth_bundle_source) > 80:
            depth_bundle_source = f"{depth_bundle_source[:77]}..."

    has_depth_bundle_provenance = bool(
        depth_generated_at_iso or depth_bundle_source or depth_stale_reason or stale_raw is not None
    )

    return {
        "depth_generated_at_iso": depth_generated_at_iso,
        "depth_stale": depth_stale,
        "depth_stale_reason": depth_stale_reason,
        "depth_bundle_source": depth_bundle_source,
        "has_depth_bundle_provenance": has_depth_bundle_provenance,
    }


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


def _market_run_projection_env_enabled() -> bool:
    return (os.getenv(MARKET_RUN_PROJECTION_ENABLED_ENV) or "").strip() == "1"


def _pointer_basename(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    try:
        return Path(text).name
    except (TypeError, ValueError):
        return "configured"


def _truncate_display(value: object, *, max_len: int = 120) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if len(text) > max_len:
        return f"{text[: max_len - 3]}..."
    return text


def _load_projection_payload_json(path: Path) -> tuple[Dict[str, Any] | None, str | None]:
    if not path.is_file():
        return None, "payload_missing"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None, "payload_malformed"
    if not isinstance(payload, dict):
        return None, "payload_invalid_shape"
    return payload, None


def _load_registry_v1_json(path: Path) -> tuple[Dict[str, Any] | None, str | None]:
    if not path.is_file():
        return None, "registry_missing"
    try:
        registry = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None, "registry_malformed"
    if not isinstance(registry, dict):
        return None, "registry_invalid_shape"
    if registry.get("schema") != REGISTRY_V1_SCHEMA:
        return None, "registry_schema_unsupported"
    return registry, None


def _select_registry_run(registry: Dict[str, Any], run_id: str | None) -> Dict[str, Any] | None:
    runs = registry.get("runs")
    if not isinstance(runs, list) or not runs:
        return None
    if run_id:
        for row in runs:
            if isinstance(row, dict) and row.get("run_id") == run_id:
                return row
        return None
    first = runs[0]
    return first if isinstance(first, dict) else None


def _registry_run_projection_subset(run: Dict[str, Any]) -> Dict[str, Any]:
    subset: Dict[str, Any] = {}
    for key in RUN_PROJECTION_REGISTRY_FIELDS:
        if key not in run:
            continue
        value = run.get(key)
        if key == "archive_path" and value is not None:
            subset[key] = _pointer_basename(value)
        else:
            subset[key] = value
    return subset


def build_market_run_projection_display_context() -> Dict[str, Any]:
    """SSR-only post-closeout registry projection panel for GET /market (env-gated, read-only)."""

    base: Dict[str, Any] = {
        "section_visible": False,
        "gate_enabled": False,
        "projection_ready": False,
        "projection_blocked_reason": "",
        "manifest_verify_rc": "",
        "closeout_accepted": False,
        "primary_evidence_finalized": False,
        "repo_commit": "",
        "s3_export_status": "",
        "download_verify_rc": "",
        "run_id": "",
        "payload_generated_at_utc": "",
        "dashboard_projection_allowed": False,
        "registry_configured_label": "",
        "closeout_configured_label": "",
        "registry_generated_at_utc": "",
        "registry_verdict": "",
        "registry_run_count": 0,
        "registry_run": {},
        "status": "disabled",
    }

    if not _market_run_projection_env_enabled():
        return base

    base["gate_enabled"] = True
    payload_path_raw = (os.getenv(MARKET_RUN_PROJECTION_PAYLOAD_JSON_ENV) or "").strip()
    if not payload_path_raw:
        base["status"] = "unconfigured"
        return base

    payload_path = Path(payload_path_raw).expanduser()
    payload, load_err = _load_projection_payload_json(payload_path)
    if load_err or payload is None:
        base["section_visible"] = True
        base["status"] = load_err or "payload_malformed"
        base["projection_blocked_reason"] = load_err or "payload_malformed"
        return base

    if payload.get("schema_version") != PROJECTION_PAYLOAD_SCHEMA_V0:
        base["section_visible"] = True
        base["status"] = "payload_schema_unsupported"
        base["projection_blocked_reason"] = "payload_schema_unsupported"
        return base

    base["section_visible"] = True
    base["status"] = "loaded"
    base["run_id"] = _truncate_display(payload.get("run_id"))
    base["payload_generated_at_utc"] = _truncate_display(payload.get("generated_at_utc"))
    base["projection_ready"] = payload.get("projection_ready") is True
    blocked = payload.get("projection_blocked_reason")
    base["projection_blocked_reason"] = _truncate_display(blocked) if blocked else ""
    manifest_rc = payload.get("manifest_verify_rc")
    base["manifest_verify_rc"] = "" if manifest_rc is None else _truncate_display(manifest_rc)
    base["closeout_accepted"] = payload.get("closeout_accepted") is True
    base["primary_evidence_finalized"] = payload.get("primary_evidence_finalized") is True
    base["repo_commit"] = _truncate_display(payload.get("repo_commit"), max_len=40)
    base["s3_export_status"] = _truncate_display(payload.get("s3_export_status"), max_len=40)
    download_rc = payload.get("download_verify_rc")
    base["download_verify_rc"] = "" if download_rc is None else _truncate_display(download_rc)

    base["registry_configured_label"] = _pointer_basename(payload.get("registry_pointer"))
    base["closeout_configured_label"] = _pointer_basename(payload.get("closeout_pointer"))

    consumers = payload.get("consumers")
    if isinstance(consumers, dict):
        base["dashboard_projection_allowed"] = (
            consumers.get("market_dashboard_projection_allowed") is True
        )

    if not base["projection_ready"]:
        base["status"] = "blocked"
        return base

    if not base["dashboard_projection_allowed"]:
        base["projection_ready"] = False
        base["status"] = "consumer_not_allowed"
        base["projection_blocked_reason"] = base["projection_blocked_reason"] or (
            "market_dashboard_projection_not_allowed"
        )
        return base

    registry_pointer = payload.get("registry_pointer")
    if not registry_pointer:
        base["status"] = "registry_pointer_missing"
        base["projection_blocked_reason"] = "registry_pointer_missing"
        base["projection_ready"] = False
        return base

    registry_path = Path(str(registry_pointer)).expanduser()
    registry, reg_err = _load_registry_v1_json(registry_path)
    if reg_err or registry is None:
        base["status"] = reg_err or "registry_unavailable"
        base["projection_blocked_reason"] = reg_err or "registry_unavailable"
        base["projection_ready"] = False
        return base

    base["registry_generated_at_utc"] = _truncate_display(registry.get("generated_at_utc"))
    base["registry_verdict"] = _truncate_display(registry.get("verdict"), max_len=80)
    runs = registry.get("runs")
    base["registry_run_count"] = len(runs) if isinstance(runs, list) else 0

    run = _select_registry_run(registry, payload.get("run_id"))
    if run is None:
        base["status"] = "registry_run_not_found"
        base["projection_blocked_reason"] = "registry_run_not_found"
        base["projection_ready"] = False
        return base

    base["registry_run"] = _registry_run_projection_subset(run)
    base["status"] = "ready"
    return base


def build_market_depth_display_context() -> Dict[str, Any]:
    """SSR-only snapshot for templates: tuple from helper, unchanged semantics."""

    top_limit = MARKET_DEPTH_SSR_TOP_LEVELS

    depth_http_status, depth_payload = market_depth_json_payload_v0()
    readmodel_id = str(depth_payload.get("readmodel_id", ""))

    provenance_ctx = _sanitize_depth_bundle_provenance(depth_payload)

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
        **provenance_ctx,
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
        run_projection = build_market_run_projection_display_context()
        ranking_funnel = build_market_ranking_funnel_display_context()
        return templates.TemplateResponse(
            request,
            "market_v0.html",
            {
                "status": proj_status,
                "payload": payload,
                "market_depth": market_depth,
                "run_projection": run_projection,
                "ranking_funnel": ranking_funnel,
                "query": {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "limit": limit,
                    "source": src,
                },
            },
        )

    return router
