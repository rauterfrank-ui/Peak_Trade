# src/webui/market_surface.py
"""
Read-only Market Surface v0 — öffentliche OHLCV + minimale Chart-UI.

- GET /market — HTML (Close-Line-Chart, Chart.js)
- GET /api/market/ohlcv — JSON (OHLCV-Bars)

GET /market embeds offline Market Depth read-model state SSR-only via
``market_depth_json_payload_v0`` (no in-page Depth JSON route, no fetch).

GET /market may embed env-gated Tape readmodel SSR via
``build_market_tape_display_context`` (offline fixture bundle only, default off).

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
from urllib.parse import quote

import pandas as pd
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .last_paper_run_panel_runtime_v0 import build_last_paper_run_panel_display_context
from .market_active_paper_run_runtime_v0 import build_market_active_paper_run_display_context
from .market_depth_runtime_v0 import (
    depth_chart_enabled_explicitly_on,
    market_depth_json_payload_v0,
)
from .double_play_dashboard_display_json_route_v0 import build_static_dashboard_display_dict
from .futures_read_only_market_dashboard_runtime_v0 import (
    build_futures_read_only_market_dashboard_display_context,
)
from .market_ranking_funnel_runtime_v0 import build_market_ranking_funnel_display_context
from .market_tape_readmodel_v0.gate import (
    enabled_explicitly_on as _market_tape_enabled_explicitly_on,
    resolve_market_tape_readmodel_payload_v0,
)
from .workflow_dashboard_runtime_v1 import build_workflow_dashboard_display_context

logger = logging.getLogger(__name__)

# Aligniert mit scripts/_shared_forward_args.OHLCV_TIMEFRAME_CHOICES (übliche Timeframes)
MARKET_TIMEFRAMES: tuple[str, ...] = ("1m", "5m", "15m", "1h", "4h", "1d")
MAX_OHLCV_LIMIT = 720
MARKET_DEPTH_SSR_TOP_LEVELS = 8
MARKET_TAPE_SSR_TOP_TRADES = 5
DEFAULT_SYMBOL = "BTC/EUR"
DEFAULT_TIMEFRAME = "1d"
DEFAULT_LIMIT = 120
DEFAULT_SOURCE: Literal["kraken", "dummy"] = "kraken"
PAGE_TITLE = "Peak Trade Market Dashboard"

MARKET_SINGLE_PAGE_CONSOLIDATION_ENABLED_ENV = (
    "PEAK_TRADE_MARKET_SINGLE_PAGE_CONSOLIDATION_V1_ENABLED"
)

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
    key = (raw or DEFAULT_SOURCE).strip().lower()
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
    except (ProviderError, CacheError) as e:
        logger.warning("Kraken data error: %s", e)
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        logger.warning("Kraken unexpected load error: %s", e)
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


def _parse_depth_display_size(size_str: str) -> float:
    try:
        return float(str(size_str).replace(",", "").strip())
    except (ValueError, TypeError):
        return 0.0


def _cumulative_depth_chart_svg_paths(
    bid_rows: List[Dict[str, str]], ask_rows: List[Dict[str, str]]
) -> Dict[str, Any]:
    """Build stepped cumulative bid/ask SVG path data from offline Top-N rows only."""

    bid_cums: List[float] = []
    running = 0.0
    for row in bid_rows:
        running += _parse_depth_display_size(row.get("size", ""))
        bid_cums.append(running)

    ask_cums: List[float] = []
    running = 0.0
    for row in ask_rows:
        running += _parse_depth_display_size(row.get("size", ""))
        ask_cums.append(running)

    max_c = max(bid_cums + ask_cums) if (bid_cums or ask_cums) else 0.0
    if max_c <= 0:
        return {"bid_path_d": "", "ask_path_d": "", "has_svg_paths": False}

    baseline = 58.0
    height = 48.0
    center = 120.0
    left = 8.0
    right = 232.0

    def y_for(cum: float) -> float:
        return baseline - (cum / max_c) * height

    bid_path = ""
    if bid_cums:
        step = (center - left) / max(len(bid_cums), 1)
        parts = [f"M{center:.1f} {baseline:.1f}"]
        x_prev = center
        for i, cum in enumerate(bid_cums):
            y = y_for(cum)
            x = center - (i + 1) * step
            parts.append(f"L{x_prev:.1f} {y:.1f}")
            parts.append(f"L{x:.1f} {y:.1f}")
            x_prev = x
        parts.append(f"L{left:.1f} {baseline:.1f}")
        parts.append(f"L{center:.1f} {baseline:.1f} Z")
        bid_path = " ".join(parts)

    ask_path = ""
    if ask_cums:
        step = (right - center) / max(len(ask_cums), 1)
        parts = [f"M{center:.1f} {baseline:.1f}"]
        x_prev = center
        for i, cum in enumerate(ask_cums):
            y = y_for(cum)
            x = center + (i + 1) * step
            parts.append(f"L{x_prev:.1f} {y:.1f}")
            parts.append(f"L{x:.1f} {y:.1f}")
            x_prev = x
        parts.append(f"L{right:.1f} {baseline:.1f}")
        parts.append(f"L{center:.1f} {baseline:.1f} Z")
        ask_path = " ".join(parts)

    return {
        "bid_path_d": bid_path,
        "ask_path_d": ask_path,
        "has_svg_paths": bool(bid_path or ask_path),
    }


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


def _market_single_page_consolidation_enabled() -> bool:
    return (os.getenv(MARKET_SINGLE_PAGE_CONSOLIDATION_ENABLED_ENV) or "").strip() == "1"


def build_market_single_page_consolidation_display_context() -> Dict[str, Any]:
    """SSR gate for embedding observability view-only panels on GET /market (default off)."""

    base: Dict[str, Any] = {
        "section_visible": False,
        "gate_enabled": False,
    }
    if not _market_single_page_consolidation_enabled():
        return base
    base["gate_enabled"] = True
    base["section_visible"] = True
    return base


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


def build_market_tape_display_context() -> Dict[str, Any]:
    """SSR-only tape readmodel panel for GET /market (env-gated, read-only, default off)."""

    base: Dict[str, Any] = {
        "section_visible": False,
        "gate_enabled": False,
        "tape_ready": False,
        "readmodel_id": "",
        "display_status": "disabled",
        "summary_line": "",
        "symbol": "",
        "trade_count": 0,
        "top_trades": [],
        "generated_at_iso": "",
        "stale": True,
        "stale_reason": "",
    }

    if not _market_tape_enabled_explicitly_on():
        return base

    base["gate_enabled"] = True
    base["section_visible"] = True

    http_status, payload = resolve_market_tape_readmodel_payload_v0()
    base["readmodel_id"] = str(payload.get("readmodel_id", ""))
    base["generated_at_iso"] = _truncate_display(payload.get("generated_at_iso"))
    base["stale"] = payload.get("stale") is True
    stale_reason = payload.get("stale_reason")
    base["stale_reason"] = _truncate_display(stale_reason) if stale_reason else ""

    if http_status == 200:
        base["tape_ready"] = True
        base["display_status"] = "ok"
        base["symbol"] = _truncate_display(payload.get("symbol"))
        tape_obj = payload.get("tape")
        trades: List[Dict[str, str]] = []
        trade_count = 0
        if isinstance(tape_obj, dict):
            raw_trades = tape_obj.get("trades")
            if isinstance(raw_trades, list):
                trade_count = len(raw_trades)
                for row in raw_trades[:MARKET_TAPE_SSR_TOP_TRADES]:
                    if not isinstance(row, dict):
                        continue
                    trades.append(
                        {
                            "sequence": _truncate_display(row.get("sequence")),
                            "price": _truncate_display(row.get("price")),
                            "size": _truncate_display(row.get("size")),
                            "side": _truncate_display(row.get("side")),
                        }
                    )
        base["trade_count"] = trade_count
        base["top_trades"] = trades
        sym = base["symbol"]
        if sym:
            base["summary_line"] = (
                f"{sym} — {trade_count} trades (offline bundle, read-only display)"
            )
        else:
            base["summary_line"] = f"{trade_count} trades (offline bundle, read-only display)"
        return base

    base["display_status"] = str(payload.get("runtime_source_status", "unavailable"))
    warnings = payload.get("warnings")
    if isinstance(warnings, list) and warnings:
        base["summary_line"] = _truncate_display(warnings[0])
    else:
        base["summary_line"] = base["stale_reason"] or base["display_status"]
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

    chart_gate_enabled = depth_chart_enabled_explicitly_on()
    chart_cumulative_ready = chart_gate_enabled and depth_http_status == 200 and has_depth_levels
    chart_svg = (
        _cumulative_depth_chart_svg_paths(top_bids, top_asks)
        if chart_cumulative_ready
        else {"bid_path_d": "", "ask_path_d": "", "has_svg_paths": False}
    )

    return {
        "depth_http_status": depth_http_status,
        "display_status": display_status,
        "readmodel_id": readmodel_id,
        "summary_line": summary_line,
        "top_bids": top_bids,
        "top_asks": top_asks,
        "top_levels_limit": top_limit,
        "has_depth_levels": has_depth_levels,
        "chart_gate_enabled": chart_gate_enabled,
        "chart_cumulative_ready": chart_cumulative_ready,
        "chart_bid_path_d": chart_svg["bid_path_d"],
        "chart_ask_path_d": chart_svg["ask_path_d"],
        "chart_has_svg_paths": chart_svg["has_svg_paths"],
        **provenance_ctx,
    }


_RANKING_TABLE_STAGE_ORDER: tuple[str, ...] = ("universe", "shortlist", "selected")


def _normalize_symbol_for_match(symbol: str) -> str:
    normalized = symbol.upper().replace("/", "").replace("-", "")
    for suffix in ("USDT", "USD", "EUR", "GBP"):
        if normalized.endswith(suffix) and len(normalized) > len(suffix):
            return normalized[: -len(suffix)]
    return normalized


def build_market_symbol_nav_href(
    *,
    symbol: str,
    source: str,
    timeframe: str,
    limit: int,
) -> str:
    """Display-only GET /market query link for a ranking row symbol (no selector authority)."""
    from urllib.parse import quote

    return (
        f"/market?source={quote(source, safe='')}&symbol={quote(symbol, safe='')}"
        f"&timeframe={quote(timeframe, safe='')}&limit={limit}"
    )


def _enrich_ranking_row_for_watchlist(
    row: dict[str, Any],
    *,
    selected_symbol: str,
    source: str,
    timeframe: str,
    limit: int,
) -> dict[str, Any]:
    row_symbol = str(row.get("symbol") or "")
    is_selected = _normalize_symbol_for_match(row_symbol) == _normalize_symbol_for_match(
        selected_symbol
    )
    return {
        **row,
        "is_selected": is_selected,
        "market_nav_href": build_market_symbol_nav_href(
            symbol=row_symbol,
            source=source,
            timeframe=timeframe,
            limit=limit,
        ),
    }


def build_market_ranking_watchlist_display_context(
    *,
    ranking_funnel: Dict[str, Any],
    operator_overview: Dict[str, Any],
    selected_symbol: str,
    source: str,
    timeframe: str,
    limit: int,
) -> Dict[str, Any]:
    """Display-only watchlist/scanner funnel wiring for GET /market ranking SSR."""

    stages = ranking_funnel.get("stages") if isinstance(ranking_funnel.get("stages"), dict) else {}
    enriched_stages: dict[str, list[dict[str, Any]]] = {}
    for stage_key in _RANKING_TABLE_STAGE_ORDER:
        enriched_stages[stage_key] = [
            _enrich_ranking_row_for_watchlist(
                row,
                selected_symbol=selected_symbol,
                source=source,
                timeframe=timeframe,
                limit=limit,
            )
            for row in (stages.get(stage_key) or [])
            if isinstance(row, dict)
        ]

    table_rows = operator_overview.get("ranking_table_rows")
    raw_rows = table_rows if isinstance(table_rows, list) else []
    enriched_table_rows = [
        _enrich_ranking_row_for_watchlist(
            row,
            selected_symbol=selected_symbol,
            source=source,
            timeframe=timeframe,
            limit=limit,
        )
        for row in raw_rows
        if isinstance(row, dict)
    ]

    source_mode = str(operator_overview.get("ranking_source_mode") or "unavailable")
    rf_source = str(ranking_funnel.get("source") or "").strip()

    return {
        "selected_symbol": selected_symbol,
        "source_mode": source_mode,
        "ranking_funnel_source": rf_source,
        "display_status": str(ranking_funnel.get("display_status") or "disabled"),
        "stages": enriched_stages,
        "table_rows": enriched_table_rows,
        "table_count": len(enriched_table_rows),
        "has_selected_in_table": any(bool(r.get("is_selected")) for r in enriched_table_rows),
    }


def _format_display_price(value: float | None) -> str:
    if value is None:
        return ""
    text = f"{value:.8f}".rstrip("0").rstrip(".")
    return text or "0"


def build_market_instrument_header_display_context(
    *,
    symbol: str,
    timeframe: str,
    limit: int,
    source: Literal["kraken", "dummy"],
    payload: Dict[str, Any],
    market_depth: Dict[str, Any],
) -> Dict[str, Any]:
    """Display-only instrument header context for GET /market (no selector authority)."""

    if source == "dummy":
        source_mode = "dummy_offline_synthetic"
    elif source == "kraken":
        source_mode = "kraken_public_ohlcv"
    else:
        source_mode = "unavailable"

    bars = payload.get("bars") if isinstance(payload.get("bars"), list) else []
    last_close: float | None = None
    last_bar_ts = ""
    if bars:
        last_bar = bars[-1] if isinstance(bars[-1], dict) else {}
        raw_close = last_bar.get("close")
        if raw_close is not None:
            try:
                last_close = float(raw_close)
            except (TypeError, ValueError):
                last_close = None
        last_bar_ts = str(last_bar.get("ts") or "").strip()

    mid: float | None = None
    spread: float | None = None
    spread_source_mode = "unavailable"
    top_bids = (
        market_depth.get("top_bids") if isinstance(market_depth.get("top_bids"), list) else []
    )
    top_asks = (
        market_depth.get("top_asks") if isinstance(market_depth.get("top_asks"), list) else []
    )
    if market_depth.get("has_depth_levels") and top_bids and top_asks:
        try:
            best_bid = float(str(top_bids[0].get("price", "")).strip())
            best_ask = float(str(top_asks[0].get("price", "")).strip())
            mid = (best_bid + best_ask) / 2.0
            spread = best_ask - best_bid
            spread_source_mode = (
                "fixture_offline"
                if market_depth.get("display_status") == "ok"
                else str(market_depth.get("display_status") or "unavailable")
            )
        except (TypeError, ValueError, IndexError, AttributeError):
            mid = None
            spread = None

    encoded_symbol = symbol.replace("/", "%2F")
    double_play_href = (
        f"/market?source={source}&symbol={encoded_symbol}"
        f"&timeframe={timeframe}&limit={limit}#double-play"
    )

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "source_mode": source_mode,
        "snapshot_at_utc": str(payload.get("generated_at_utc") or "").strip(),
        "last_bar_ts": last_bar_ts,
        "last_close": last_close,
        "last_close_display": _format_display_price(last_close),
        "price_summary_status": "available" if last_close is not None else "unavailable",
        "mid": mid,
        "spread": spread,
        "mid_display": _format_display_price(mid),
        "spread_display": _format_display_price(spread),
        "spread_summary_status": "available" if spread is not None else "unavailable",
        "spread_source_mode": spread_source_mode,
        "data_authority": False,
        "trading_authority": False,
        "double_play_href": double_play_href,
    }


def build_market_futures_metrics_strip_display_context(
    *,
    source: Literal["kraken", "dummy"],
    payload: Dict[str, Any],
    market_depth: Dict[str, Any],
) -> Dict[str, Any]:
    """Display-only futures metrics strip for GET /market (derived from bars/depth, no signals)."""

    if source == "dummy":
        source_mode = "dummy_offline_synthetic"
    elif source == "kraken":
        source_mode = "kraken_public_ohlcv"
    else:
        source_mode = "unavailable"

    bars = payload.get("bars") if isinstance(payload.get("bars"), list) else []
    last_close: float | None = None
    volatility_proxy_display = ""
    volatility_status = "unavailable"
    volume_display = ""
    volume_status = "unavailable"

    if bars:
        last_bar = bars[-1] if isinstance(bars[-1], dict) else {}
        raw_close = last_bar.get("close")
        if raw_close is not None:
            try:
                last_close = float(raw_close)
            except (TypeError, ValueError):
                last_close = None

        if last_close is not None and last_close > 0:
            try:
                high = float(last_bar.get("high", 0))
                low = float(last_bar.get("low", 0))
                range_pct = ((high - low) / last_close) * 100.0
                volatility_proxy_display = f"{range_pct:.4f}% bar range"
                volatility_status = "available"
            except (TypeError, ValueError):
                pass

        raw_volume = last_bar.get("volume")
        if raw_volume is not None:
            try:
                volume_display = _format_display_price(float(raw_volume))
                volume_status = "available"
            except (TypeError, ValueError):
                pass

    mid: float | None = None
    spread: float | None = None
    spread_depth_status = "unavailable"
    depth_quality_display = ""
    spread_source_mode = "unavailable"
    top_bids = (
        market_depth.get("top_bids") if isinstance(market_depth.get("top_bids"), list) else []
    )
    top_asks = (
        market_depth.get("top_asks") if isinstance(market_depth.get("top_asks"), list) else []
    )
    if market_depth.get("has_depth_levels") and top_bids and top_asks:
        try:
            best_bid = float(str(top_bids[0].get("price", "")).strip())
            best_ask = float(str(top_asks[0].get("price", "")).strip())
            mid = (best_bid + best_ask) / 2.0
            spread = best_ask - best_bid
            spread_source_mode = (
                "fixture_offline"
                if market_depth.get("display_status") == "ok"
                else str(market_depth.get("display_status") or "unavailable")
            )
            level_count = len(top_bids) + len(top_asks)
            spread_bps = (spread / mid * 10000.0) if mid and mid > 0 else 0.0
            depth_quality_display = f"{level_count} top levels · {spread_bps:.2f} bps spread proxy"
            spread_depth_status = "available"
        except (TypeError, ValueError, IndexError, AttributeError):
            mid = None
            spread = None

    bars_returned = int(payload.get("bars_returned") or 0)
    depth_display = str(market_depth.get("display_status") or "unavailable")
    if bars_returned > 0 and spread_depth_status == "available":
        readiness_display = "bars+depth_ready"
    elif bars_returned > 0:
        readiness_display = "bars_ready"
    else:
        readiness_display = "bars_unavailable"

    return {
        "source_mode": source_mode,
        "last_close": last_close,
        "last_close_display": _format_display_price(last_close),
        "last_price_status": "available" if last_close is not None else "unavailable",
        "volatility_proxy_display": volatility_proxy_display,
        "volatility_status": volatility_status,
        "volume_display": volume_display,
        "volume_status": volume_status,
        "mid": mid,
        "spread": spread,
        "mid_display": _format_display_price(mid),
        "spread_display": _format_display_price(spread),
        "depth_quality_display": depth_quality_display,
        "spread_depth_status": spread_depth_status,
        "spread_source_mode": spread_source_mode,
        "depth_display_status": depth_display,
        "readiness_display": readiness_display,
        "data_authority": False,
        "trading_authority": False,
    }


def build_market_operator_overview_display_context(
    *,
    ranking_funnel: Dict[str, Any],
) -> Dict[str, Any]:
    """Display-only operator overview context for GET /market (no decision logic)."""

    dp_display = build_static_dashboard_display_dict()
    rows: list[dict[str, Any]] = []
    stages = ranking_funnel.get("stages") if isinstance(ranking_funnel.get("stages"), dict) else {}
    for stage_key in _RANKING_TABLE_STAGE_ORDER:
        for row in stages.get(stage_key) or []:
            if isinstance(row, dict):
                rows.append({**row, "stage": stage_key})

    if rows and ranking_funnel.get("gate_enabled"):
        source_mode = "existing_readmodel"
    elif rows:
        source_mode = "mixed"
    elif ranking_funnel.get("gate_enabled"):
        source_mode = "fixture_offline"
    else:
        source_mode = "fixture_offline"

    panels = {
        p.get("name"): p
        for p in (dp_display.get("panels") or [])
        if isinstance(p, dict) and p.get("name")
    }

    return {
        "dp_display": dp_display,
        "ranking_source_mode": source_mode,
        "ranking_table_rows": rows,
        "ranking_table_count": len(rows),
        "suitability_panel": panels.get("strategy_suitability") or {},
        "composition_panel": panels.get("composition") or {},
        "survival_panel": panels.get("survival_envelope") or {},
        "futures_input_panel": panels.get("futures_input") or {},
        "capital_ratchet_panel": panels.get("capital_slot_ratchet") or {},
        "capital_release_panel": panels.get("capital_slot_release") or {},
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


def build_market_payload_for_page(
    *,
    symbol: str,
    timeframe: str,
    limit: int,
    source: Literal["kraken", "dummy"],
) -> tuple[Dict[str, Any], bool]:
    """HTML page payload; Kraken failures render honest unavailable state (no 503 page)."""

    try:
        return build_market_payload(
            symbol=symbol, timeframe=timeframe, limit=limit, source=source
        ), False
    except HTTPException as exc:
        if exc.status_code != 503:
            raise
        detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        meta: Dict[str, Any] = {
            "unavailable": True,
            "reason": detail,
            "source_mode": (
                "kraken_public_ohlcv" if source == "kraken" else "dummy_offline_synthetic"
            ),
        }
        return (
            {
                "generated_at_utc": _utc_now_iso(),
                "source": source,
                "symbol": symbol,
                "timeframe": timeframe,
                "limit_requested": limit,
                "bars_returned": 0,
                "meta": meta,
                "bars": [],
            },
            True,
        )


def build_market_primary_values_display_context(
    *,
    symbol: str,
    timeframe: str,
    limit: int,
    source: Literal["kraken", "dummy"],
    payload: Dict[str, Any],
    data_unavailable: bool,
) -> Dict[str, Any]:
    """Above-the-fold operator market values (display-only, derived from embedded bars)."""

    if source == "dummy":
        source_kind = "dummy-offline-synthetic"
        source_mode = "dummy_offline_synthetic"
    else:
        source_kind = "kraken-public"
        source_mode = "kraken_public_ohlcv"

    bars = payload.get("bars") if isinstance(payload.get("bars"), list) else []
    last_bar = bars[-1] if bars and isinstance(bars[-1], dict) else {}
    prev_bar = bars[-2] if len(bars) >= 2 and isinstance(bars[-2], dict) else {}

    def _fval(row: Dict[str, Any], key: str) -> float | None:
        raw = row.get(key)
        if raw is None:
            return None
        try:
            return float(raw)
        except (TypeError, ValueError):
            return None

    last_close = _fval(last_bar, "close")
    last_open = _fval(last_bar, "open")
    last_high = _fval(last_bar, "high")
    last_low = _fval(last_bar, "low")
    last_volume = _fval(last_bar, "volume")
    prev_close = _fval(prev_bar, "close")

    change_abs: float | None = None
    change_pct: float | None = None
    if last_close is not None and prev_close is not None and prev_close != 0:
        change_abs = last_close - prev_close
        change_pct = (change_abs / prev_close) * 100.0

    status = "available" if last_close is not None and not data_unavailable else "unavailable"
    if data_unavailable and source == "kraken":
        status = "unavailable"

    meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
    unavailable_reason = str(meta.get("reason") or "").strip()

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "limit": limit,
        "source": source,
        "source_kind": source_kind,
        "source_mode": source_mode,
        "status": status,
        "data_unavailable": data_unavailable,
        "unavailable_reason": unavailable_reason,
        "generated_at_utc": str(payload.get("generated_at_utc") or "").strip(),
        "last_bar_ts": str(last_bar.get("ts") or "").strip(),
        "last_close": last_close,
        "last_close_display": _format_display_price(last_close),
        "last_open_display": _format_display_price(last_open),
        "last_high_display": _format_display_price(last_high),
        "last_low_display": _format_display_price(last_low),
        "last_volume_display": _format_display_price(last_volume),
        "change_abs_display": _format_display_price(change_abs),
        "change_pct_display": f"{change_pct:.4f}%" if change_pct is not None else "",
        "change_status": "available" if change_pct is not None else "unavailable",
        "bars_returned": int(payload.get("bars_returned") or 0),
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
            DEFAULT_SOURCE,
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
        source: str = Query(DEFAULT_SOURCE),
    ) -> Any:
        if timeframe not in MARKET_TIMEFRAMES:
            raise HTTPException(
                status_code=422,
                detail=f"timeframe muss einer von {list(MARKET_TIMEFRAMES)} sein, nicht {timeframe!r}",
            )
        src = _normalize_source(source)
        payload, data_unavailable = build_market_payload_for_page(
            symbol=symbol, timeframe=timeframe, limit=limit, source=src
        )
        primary_values = build_market_primary_values_display_context(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
            source=src,
            payload=payload,
            data_unavailable=data_unavailable,
        )
        proj_status = get_project_status()
        market_depth = build_market_depth_display_context()
        run_projection = build_market_run_projection_display_context()
        market_tape = build_market_tape_display_context()
        ranking_funnel = build_market_ranking_funnel_display_context()
        operator_overview = build_market_operator_overview_display_context(
            ranking_funnel=ranking_funnel,
        )
        ranking_watchlist = build_market_ranking_watchlist_display_context(
            ranking_funnel=ranking_funnel,
            operator_overview=operator_overview,
            selected_symbol=symbol,
            source=src,
            timeframe=timeframe,
            limit=limit,
        )
        instrument_header = build_market_instrument_header_display_context(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
            source=src,
            payload=payload,
            market_depth=market_depth,
        )
        futures_metrics_strip = build_market_futures_metrics_strip_display_context(
            source=src,
            payload=payload,
            market_depth=market_depth,
        )
        active_paper_run = build_market_active_paper_run_display_context()
        market_single_page_consolidation = build_market_single_page_consolidation_display_context()
        workflow_dashboard: Dict[str, Any] | None = None
        last_paper_run_panel: Dict[str, Any] | None = None
        if market_single_page_consolidation["section_visible"]:
            workflow_dashboard = build_workflow_dashboard_display_context()
            last_paper_run_panel = build_last_paper_run_panel_display_context()
        dp_display = build_static_dashboard_display_dict()
        f5_dashboard = build_futures_read_only_market_dashboard_display_context()
        encoded_symbol = quote(symbol, safe="")
        legacy_demo_href = (
            f"/market?source={src}&symbol={encoded_symbol}&timeframe={timeframe}&limit={limit}"
        )
        return templates.TemplateResponse(
            request,
            "market_v0.html",
            {
                "status": proj_status,
                "payload": payload,
                "market_depth": market_depth,
                "run_projection": run_projection,
                "market_tape": market_tape,
                "ranking_funnel": ranking_funnel,
                "ranking_watchlist": ranking_watchlist,
                "operator_overview": operator_overview,
                "instrument_header": instrument_header,
                "futures_metrics_strip": futures_metrics_strip,
                "active_paper_run": active_paper_run,
                "market_single_page_consolidation": market_single_page_consolidation,
                "workflow_dashboard": workflow_dashboard,
                "last_paper_run_panel": last_paper_run_panel,
                "dp_display": dp_display,
                "f5_dashboard": f5_dashboard,
                "double_play_json_url": "/api/master-v2/double-play/dashboard-display.json",
                "legacy_demo_href": legacy_demo_href,
                "page_title": PAGE_TITLE,
                "primary_values": primary_values,
                "data_unavailable": data_unavailable,
                "query": {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "limit": limit,
                    "source": src,
                },
            },
        )

    return router
