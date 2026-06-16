# src/webui/market_surface.py
"""
Read-only Market Surface v0 — öffentliche OHLCV + minimale Chart-UI.

- GET /market — HTML (Close-Line-Chart, Chart.js)
- GET /api/market/ohlcv — JSON (OHLCV-Bars)

GET /market embeds offline Market Depth read-model state SSR-only via
``market_depth_json_payload_v0`` (no in-page Depth JSON route, no fetch).

GET /market may embed env-gated Tape readmodel SSR via
``build_market_tape_display_context`` (offline fixture bundle only, default off).

Keine Orders, kein OPS-Cockpit-Bezug. Kanonischer Default ist futures-first (SSR, fail-closed).
Legacy Spot/Synthetic nur explizit via ``source=kraken`` oder ``source=dummy`` mit explizitem Symbol.
"""

from __future__ import annotations

import functools
import importlib.util
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Literal, Optional
from urllib.parse import quote, urlencode

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
from .market_futures_ohlcv_runtime_v0 import (
    build_market_futures_ohlcv_display_context,
    resolve_futures_ohlcv_series_for_symbol,
)
from .market_instrument_eligibility_v0 import (
    CANONICAL_EXCLUSION_OWNER,
    is_bitcoin_underlying,
    is_eligible_market_dashboard_instrument,
)
from .workflow_dashboard_runtime_v1 import build_workflow_dashboard_display_context

logger = logging.getLogger(__name__)

# Aligniert mit scripts/_shared_forward_args.OHLCV_TIMEFRAME_CHOICES (übliche Timeframes)
MARKET_TIMEFRAMES: tuple[str, ...] = ("1m", "5m", "15m", "1h", "4h", "1d")
MAX_OHLCV_LIMIT = 720
MARKET_DEPTH_SSR_TOP_LEVELS = 8
MARKET_TAPE_SSR_TOP_TRADES = 5
DEFAULT_SYMBOL = ""
DEFAULT_TIMEFRAME = "1d"
DEFAULT_LIMIT = 120
MarketSource = Literal["futures", "kraken", "dummy"]
DEFAULT_SOURCE: MarketSource = "futures"
FORBIDDEN_IMPLICIT_SPOT_DEFAULT_SYMBOL = "BTC/EUR"
LEGACY_DEMO_SOURCES: tuple[str, ...] = ("kraken", "dummy")
DEFAULT_TOP_N = 20
ALLOWED_TOP_N_VALUES: tuple[int, ...] = (20, 50)
PAGE_TITLE = "Peak Trade Market Dashboard"

CANONICAL_MARKET_ROUTE = "/market"
CANONICAL_MARKET_ROUTE_OWNER = "src/webui/market_surface.py"
CANONICAL_MARKET_VIEWMODEL_OWNER = "src/webui/market_surface.py"
CANONICAL_MARKET_TEMPLATE_OWNER = "templates/peak_trade_dashboard/market_v0.html"
CANONICAL_FUTURES_UNIVERSE_OWNER = "src/webui/market_ranking_funnel_runtime_v0.py"
CANONICAL_FUTURES_RANKING_OWNER = "src/webui/market_ranking_funnel_runtime_v0.py"
CANONICAL_TOP_N_OWNER = "src/webui/market_surface.py"
CANONICAL_F5_METADATA_OWNER = "src/webui/futures_read_only_market_dashboard_runtime_v0.py"
CANONICAL_SELECTED_INSTRUMENT_OWNER = "src/webui/market_surface.py"
CANONICAL_FUTURES_OHLCV_OWNER = "src/webui/market_futures_ohlcv_runtime_v0.py"
CANONICAL_CHART_OWNER = "templates/peak_trade_dashboard/partials/market_primary_close_chart_v1.html"
CANONICAL_INSTRUMENT_EXCLUSION_OWNER = CANONICAL_EXCLUSION_OWNER
CANONICAL_MATRIX_TEMPLATE_OWNER = (
    "templates/peak_trade_dashboard/partials/market_governed_top20_primary_v1.html"
)
CANONICAL_RANKING_FUNNEL_OWNER = "src/webui/market_ranking_funnel_runtime_v0.py"
CANONICAL_ELIGIBILITY_OWNER = "src/webui/market_instrument_eligibility_v0.py"
CANONICAL_STYLE_OWNER = CANONICAL_MATRIX_TEMPLATE_OWNER
CANONICAL_URL_BUILDER_OWNER = "src/webui/market_surface.py"
CANONICAL_FILTER_OWNER = "src/webui/market_surface.py"
CANONICAL_SORT_OWNER = "src/webui/market_surface.py"
CANONICAL_CLIENT_INTERACTION_OWNER = CANONICAL_MATRIX_TEMPLATE_OWNER
CANONICAL_WORKSPACE_TEMPLATE_OWNER = (
    "templates/peak_trade_dashboard/partials/market_primary_operator_hero_v1.html"
)
CANONICAL_HERO_TEMPLATE_OWNER = CANONICAL_WORKSPACE_TEMPLATE_OWNER
CANONICAL_VOLUME_OWNER = CANONICAL_CHART_OWNER
CANONICAL_RANKING_CONTEXT_OWNER = "src/webui/market_surface.py"
CANONICAL_CONTRACT_METADATA_OWNER = CANONICAL_F5_METADATA_OWNER
CANONICAL_FRESHNESS_OWNER = CANONICAL_FUTURES_OHLCV_OWNER

MATRIX_ROW_SCHEMA: tuple[str, ...] = (
    "rank",
    "symbol",
    "score_display",
    "eligibility_status",
    "f5_status",
    "last_price_display",
    "change_display",
    "volume_display",
    "freshness_display",
    "data_source",
    "data_status",
)
AVAILABLE_SORT_FIELDS: tuple[str, ...] = (
    "rank",
    "symbol",
    "score",
    "f5_status",
    "last_price",
    "change",
    "volume",
)
AVAILABLE_FILTER_FIELDS: tuple[str, ...] = ("symbol", "f5_status", "freshness")
ALLOWED_FRESHNESS_FILTER_VALUES: frozenset[str] = frozenset({"fresh", "stale"})
MATRIX_VIEW_QUERY_PARAM_NAMES: tuple[str, ...] = (
    "matrix_filter_symbol",
    "matrix_filter_f5_status",
    "matrix_filter_freshness",
    "matrix_sort_field",
    "matrix_sort_direction",
)

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
    fixed = (os.environ.get("PEAK_TRADE_FIXED_GENERATED_AT_UTC") or "").strip()
    if fixed:
        return fixed
    return datetime.now(timezone.utc).isoformat()


def _pin_market_page_display_timestamps(dp_display: Dict[str, Any]) -> None:
    """Pin SSR display timestamps when tests set PEAK_TRADE_FIXED_GENERATED_AT_UTC."""
    fixed = (os.environ.get("PEAK_TRADE_FIXED_GENERATED_AT_UTC") or "").strip()
    if not fixed:
        return
    meta = dp_display.get("display_snapshot_meta")
    if not isinstance(meta, dict):
        return
    text = fixed[:-1] + "+00:00" if fixed.endswith("Z") else fixed
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    meta["assembled_at_iso"] = (
        dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    )


def _normalize_source(raw: str | None) -> MarketSource:
    key = (raw or DEFAULT_SOURCE).strip().lower()
    if key not in ("futures", "kraken", "dummy"):
        raise HTTPException(
            status_code=422,
            detail=f"source muss 'futures', 'kraken' oder 'dummy' sein, nicht {raw!r}",
        )
    return key  # type: ignore[return-value]


def _normalize_request_symbol(symbol: str | None) -> str:
    return (symbol or "").strip()


def _is_forbidden_implicit_spot_symbol(symbol: str) -> bool:
    normalized = symbol.strip().upper().replace(" ", "")
    return normalized in {"BTC/EUR", "BTCEUR"}


def normalize_top_n(raw: int | str | None) -> int:
    """Fail-closed: unknown or disallowed values normalize to canonical Top 20."""
    if raw is None or raw == "":
        return DEFAULT_TOP_N
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return DEFAULT_TOP_N
    if value not in ALLOWED_TOP_N_VALUES:
        return DEFAULT_TOP_N
    return value


@dataclass(frozen=True)
class MarketViewQueryExtras:
    """Optional matrix view-only query state preserved across Top-N navigation."""

    matrix_filter_symbol: str = ""
    matrix_filter_f5_status: str = ""
    matrix_filter_freshness: str = ""
    matrix_sort_field: str = ""
    matrix_sort_direction: str = ""


def _sanitize_matrix_filter_symbol(raw: str | None) -> str:
    return (raw or "").strip()[:64]


def _sanitize_matrix_filter_f5_status(raw: str | None) -> str:
    return (raw or "").strip()[:64]


def _sanitize_matrix_filter_freshness(raw: str | None) -> str:
    value = (raw or "").strip().lower()
    return value if value in ALLOWED_FRESHNESS_FILTER_VALUES else ""


def _sanitize_matrix_sort_field(raw: str | None) -> str:
    value = (raw or "").strip()
    return value if value in AVAILABLE_SORT_FIELDS else ""


def _sanitize_matrix_sort_direction(raw: str | None) -> str:
    value = (raw or "").strip().lower()
    return value if value in {"asc", "desc"} else ""


def build_market_view_query_extras(
    *,
    matrix_filter_symbol: str | None = None,
    matrix_filter_f5_status: str | None = None,
    matrix_filter_freshness: str | None = None,
    matrix_sort_field: str | None = None,
    matrix_sort_direction: str | None = None,
) -> MarketViewQueryExtras:
    return MarketViewQueryExtras(
        matrix_filter_symbol=_sanitize_matrix_filter_symbol(matrix_filter_symbol),
        matrix_filter_f5_status=_sanitize_matrix_filter_f5_status(matrix_filter_f5_status),
        matrix_filter_freshness=_sanitize_matrix_filter_freshness(matrix_filter_freshness),
        matrix_sort_field=_sanitize_matrix_sort_field(matrix_sort_field),
        matrix_sort_direction=_sanitize_matrix_sort_direction(matrix_sort_direction),
    )


def _market_query_params(
    *,
    source: str,
    symbol: str,
    timeframe: str,
    limit: int,
    top_n: int,
    extras: MarketViewQueryExtras | None = None,
    include_default_top_n: bool = False,
) -> list[tuple[str, str]]:
    params: list[tuple[str, str]] = [("source", source)]
    if symbol:
        params.append(("symbol", symbol))
    params.extend([("timeframe", timeframe), ("limit", str(limit))])
    if include_default_top_n or top_n != DEFAULT_TOP_N:
        params.append(("top_n", str(top_n)))
    if extras is not None:
        if extras.matrix_filter_symbol:
            params.append(("matrix_filter_symbol", extras.matrix_filter_symbol))
        if extras.matrix_filter_f5_status:
            params.append(("matrix_filter_f5_status", extras.matrix_filter_f5_status))
        if extras.matrix_filter_freshness:
            params.append(("matrix_filter_freshness", extras.matrix_filter_freshness))
        if extras.matrix_sort_field:
            params.append(("matrix_sort_field", extras.matrix_sort_field))
        if extras.matrix_sort_direction:
            params.append(("matrix_sort_direction", extras.matrix_sort_direction))
    return params


def build_market_canonical_href(
    *,
    source: str,
    symbol: str,
    timeframe: str,
    limit: int,
    top_n: int = DEFAULT_TOP_N,
    extras: MarketViewQueryExtras | None = None,
    include_default_top_n: bool = False,
) -> str:
    """Deterministic absolute GET /market href (single canonical route)."""
    params = _market_query_params(
        source=source,
        symbol=symbol,
        timeframe=timeframe,
        limit=limit,
        top_n=top_n,
        extras=extras,
        include_default_top_n=include_default_top_n,
    )
    return f"{CANONICAL_MARKET_ROUTE}?{urlencode(params)}"


def _merge_market_view_extras(
    base: MarketViewQueryExtras | None,
    *,
    matrix_filter_symbol: str | None = None,
    matrix_filter_f5_status: str | None = None,
    matrix_filter_freshness: str | None = None,
    matrix_sort_field: str | None = None,
    matrix_sort_direction: str | None = None,
    clear_filters: bool = False,
    clear_sort: bool = False,
) -> MarketViewQueryExtras:
    current = base or MarketViewQueryExtras()
    if clear_filters:
        return MarketViewQueryExtras(
            matrix_sort_field="" if clear_sort else current.matrix_sort_field,
            matrix_sort_direction="" if clear_sort else current.matrix_sort_direction,
        )
    if clear_sort:
        return MarketViewQueryExtras(
            matrix_filter_symbol=current.matrix_filter_symbol,
            matrix_filter_f5_status=current.matrix_filter_f5_status,
            matrix_filter_freshness=current.matrix_filter_freshness,
        )
    return MarketViewQueryExtras(
        matrix_filter_symbol=(
            matrix_filter_symbol
            if matrix_filter_symbol is not None
            else current.matrix_filter_symbol
        ),
        matrix_filter_f5_status=(
            matrix_filter_f5_status
            if matrix_filter_f5_status is not None
            else current.matrix_filter_f5_status
        ),
        matrix_filter_freshness=(
            matrix_filter_freshness
            if matrix_filter_freshness is not None
            else current.matrix_filter_freshness
        ),
        matrix_sort_field=(
            matrix_sort_field if matrix_sort_field is not None else current.matrix_sort_field
        ),
        matrix_sort_direction=(
            matrix_sort_direction
            if matrix_sort_direction is not None
            else current.matrix_sort_direction
        ),
    )


def normalize_matrix_view_extras(
    extras: MarketViewQueryExtras | None,
    *,
    allowed_f5_statuses: tuple[str, ...] | list[str] = (),
) -> MarketViewQueryExtras:
    """Fail-closed normalization for matrix view-only query state."""
    base = extras or MarketViewQueryExtras()
    f5 = base.matrix_filter_f5_status
    if f5 and allowed_f5_statuses and f5 not in allowed_f5_statuses:
        f5 = ""
    sort_field = base.matrix_sort_field
    if sort_field and sort_field not in AVAILABLE_SORT_FIELDS:
        sort_field = ""
    sort_direction = base.matrix_sort_direction
    if sort_direction and sort_direction not in {"asc", "desc"}:
        sort_direction = ""
    if sort_field and not sort_direction:
        sort_direction = "asc" if sort_field == "rank" else "desc"
    if sort_direction and not sort_field:
        sort_direction = ""
    return MarketViewQueryExtras(
        matrix_filter_symbol=_sanitize_matrix_filter_symbol(base.matrix_filter_symbol),
        matrix_filter_f5_status=f5,
        matrix_filter_freshness=_sanitize_matrix_filter_freshness(base.matrix_filter_freshness),
        matrix_sort_field=sort_field,
        matrix_sort_direction=sort_direction,
    )


def resolve_matrix_sort_state(extras: MarketViewQueryExtras) -> tuple[str, str, bool]:
    """Return active sort field, direction, and whether sort params were explicit."""
    explicit = bool(extras.matrix_sort_field or extras.matrix_sort_direction)
    field = extras.matrix_sort_field or "rank"
    if field not in AVAILABLE_SORT_FIELDS:
        field = "rank"
        explicit = False
    direction = extras.matrix_sort_direction or ("asc" if field == "rank" else "desc")
    if direction not in {"asc", "desc"}:
        direction = "asc" if field == "rank" else "desc"
        explicit = False
    return field, direction, explicit


def _matrix_row_matches_view_filters(row: dict[str, Any], extras: MarketViewQueryExtras) -> bool:
    sym_q = extras.matrix_filter_symbol.strip().upper()
    if sym_q and sym_q not in str(row.get("symbol") or "").upper():
        return False
    f5 = extras.matrix_filter_f5_status
    if f5 and str(row.get("f5_status") or "") != f5:
        return False
    freshness = extras.matrix_filter_freshness
    if freshness and str(row.get("freshness_filter") or "") != freshness:
        return False
    return True


def _matrix_row_sort_key(row: dict[str, Any], field: str) -> tuple[int, Any]:
    if field == "symbol":
        return (0, str(row.get("symbol") or "").lower())
    if field == "f5_status":
        return (0, str(row.get("f5_status") or "").lower())
    attr = {
        "rank": "rank_sort",
        "score": "score_sort",
        "last_price": "last_price_sort",
        "change": "change_sort",
        "volume": "volume_sort",
    }.get(field, "rank_sort")
    value = row.get(attr)
    if value is None:
        return (1, "")
    if isinstance(value, (int, float)):
        return (0, value)
    return (0, str(value).lower())


def sort_matrix_rows(
    rows: list[dict[str, Any]],
    *,
    field: str,
    direction: str,
) -> list[dict[str, Any]]:
    dir_mult = -1 if direction == "desc" else 1

    def _cmp(a: dict[str, Any], b: dict[str, Any]) -> int:
        ak = _matrix_row_sort_key(a, field)
        bk = _matrix_row_sort_key(b, field)
        if ak[0] != bk[0]:
            return ak[0] - bk[0]
        if ak[1] == bk[1]:
            ar = _matrix_row_sort_key(a, "rank")
            br = _matrix_row_sort_key(b, "rank")
            if ar[1] == br[1]:
                return 0
            if ar[1] == "":
                return 1
            if br[1] == "":
                return -1
            return (ar[1] > br[1]) - (ar[1] < br[1])
        if ak[1] < bk[1]:
            return -1 * dir_mult
        return 1 * dir_mult

    return sorted(rows, key=functools.cmp_to_key(_cmp))


def apply_matrix_view_state(
    rows: list[dict[str, Any]],
    extras: MarketViewQueryExtras | None,
    *,
    allowed_f5_statuses: tuple[str, ...] | list[str],
) -> tuple[list[dict[str, Any]], MarketViewQueryExtras, str, str, bool]:
    normalized = normalize_matrix_view_extras(extras, allowed_f5_statuses=allowed_f5_statuses)
    filtered = [row for row in rows if _matrix_row_matches_view_filters(row, normalized)]
    sort_field, sort_direction, explicit_sort = resolve_matrix_sort_state(normalized)
    if explicit_sort:
        filtered = sort_matrix_rows(filtered, field=sort_field, direction=sort_direction)
    no_results = len(filtered) == 0 and len(rows) > 0
    return filtered, normalized, sort_field, sort_direction, no_results


def build_market_matrix_view_href(
    *,
    source: str,
    symbol: str,
    timeframe: str,
    limit: int,
    top_n: int = DEFAULT_TOP_N,
    extras: MarketViewQueryExtras | None = None,
    matrix_filter_symbol: str | None = None,
    matrix_filter_f5_status: str | None = None,
    matrix_filter_freshness: str | None = None,
    matrix_sort_field: str | None = None,
    matrix_sort_direction: str | None = None,
    clear_filters: bool = False,
    clear_sort: bool = False,
    include_default_top_n: bool = False,
) -> str:
    merged = _merge_market_view_extras(
        extras,
        matrix_filter_symbol=matrix_filter_symbol,
        matrix_filter_f5_status=matrix_filter_f5_status,
        matrix_filter_freshness=matrix_filter_freshness,
        matrix_sort_field=matrix_sort_field,
        matrix_sort_direction=matrix_sort_direction,
        clear_filters=clear_filters,
        clear_sort=clear_sort,
    )
    return build_market_canonical_href(
        source=source,
        symbol=symbol,
        timeframe=timeframe,
        limit=limit,
        top_n=top_n,
        extras=merged,
        include_default_top_n=include_default_top_n,
    )


def build_market_matrix_sort_toggle_href(
    *,
    field: str,
    source: str,
    symbol: str,
    timeframe: str,
    limit: int,
    top_n: int,
    extras: MarketViewQueryExtras | None,
    active_sort_field: str,
    active_sort_direction: str,
) -> str:
    if field not in AVAILABLE_SORT_FIELDS:
        field = "rank"
    if field == active_sort_field:
        next_direction = "desc" if active_sort_direction == "asc" else "asc"
    else:
        next_direction = "asc" if field == "rank" else "desc"
    return build_market_matrix_view_href(
        source=source,
        symbol=symbol,
        timeframe=timeframe,
        limit=limit,
        top_n=top_n,
        extras=extras,
        matrix_sort_field=field,
        matrix_sort_direction=next_direction,
    )


def build_market_matrix_reset_filters_href(
    *,
    source: str,
    symbol: str,
    timeframe: str,
    limit: int,
    top_n: int,
    extras: MarketViewQueryExtras | None,
) -> str:
    return build_market_matrix_view_href(
        source=source,
        symbol=symbol,
        timeframe=timeframe,
        limit=limit,
        top_n=top_n,
        extras=extras,
        clear_filters=True,
    )


def build_market_matrix_reset_sort_href(
    *,
    source: str,
    symbol: str,
    timeframe: str,
    limit: int,
    top_n: int,
    extras: MarketViewQueryExtras | None,
) -> str:
    return build_market_matrix_view_href(
        source=source,
        symbol=symbol,
        timeframe=timeframe,
        limit=limit,
        top_n=top_n,
        extras=extras,
        clear_sort=True,
    )


def build_market_matrix_control_hrefs(
    *,
    source: str,
    symbol: str,
    timeframe: str,
    limit: int,
    top_n: int,
    extras: MarketViewQueryExtras,
    active_sort_field: str,
    active_sort_direction: str,
    f5_filter_values: list[str],
) -> dict[str, Any]:
    return {
        "reset_filters": build_market_matrix_reset_filters_href(
            source=source,
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
            top_n=top_n,
            extras=extras,
        ),
        "reset_sort": build_market_matrix_reset_sort_href(
            source=source,
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
            top_n=top_n,
            extras=extras,
        ),
        "sort": {
            field: build_market_matrix_sort_toggle_href(
                field=field,
                source=source,
                symbol=symbol,
                timeframe=timeframe,
                limit=limit,
                top_n=top_n,
                extras=extras,
                active_sort_field=active_sort_field,
                active_sort_direction=active_sort_direction,
            )
            for field in AVAILABLE_SORT_FIELDS
        },
        "f5_status": {
            "all": build_market_matrix_view_href(
                source=source,
                symbol=symbol,
                timeframe=timeframe,
                limit=limit,
                top_n=top_n,
                extras=extras,
                matrix_filter_f5_status="",
            ),
            **{
                status: build_market_matrix_view_href(
                    source=source,
                    symbol=symbol,
                    timeframe=timeframe,
                    limit=limit,
                    top_n=top_n,
                    extras=extras,
                    matrix_filter_f5_status=status,
                )
                for status in f5_filter_values
            },
        },
        "freshness": {
            "all": build_market_matrix_view_href(
                source=source,
                symbol=symbol,
                timeframe=timeframe,
                limit=limit,
                top_n=top_n,
                extras=extras,
                matrix_filter_freshness="",
            ),
            "fresh": build_market_matrix_view_href(
                source=source,
                symbol=symbol,
                timeframe=timeframe,
                limit=limit,
                top_n=top_n,
                extras=extras,
                matrix_filter_freshness="fresh",
            ),
            "stale": build_market_matrix_view_href(
                source=source,
                symbol=symbol,
                timeframe=timeframe,
                limit=limit,
                top_n=top_n,
                extras=extras,
                matrix_filter_freshness="stale",
            ),
        },
        "filter_form_action": CANONICAL_MARKET_ROUTE,
        "filter_form_fields": _market_query_params(
            source=source,
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
            top_n=top_n,
            extras=extras,
            include_default_top_n=top_n != DEFAULT_TOP_N,
        ),
    }


def _is_eligible_ranking_row(row: dict[str, Any]) -> bool:
    sym = str(row.get("symbol") or "").strip()
    return bool(sym) and is_eligible_market_dashboard_instrument(sym)


def collect_governed_futures_symbols(ranking_funnel: Dict[str, Any]) -> set[str]:
    symbols: set[str] = set()
    stages = ranking_funnel.get("stages") if isinstance(ranking_funnel.get("stages"), dict) else {}
    for stage_key in ("universe", "shortlist", "selected"):
        for row in stages.get(stage_key) or []:
            if not isinstance(row, dict):
                continue
            sym = str(row.get("symbol") or "").strip()
            if sym and is_eligible_market_dashboard_instrument(sym):
                symbols.add(sym)
    return symbols


def is_valid_governed_futures_symbol(symbol: str, ranking_funnel: Dict[str, Any]) -> bool:
    sym = symbol.strip()
    if not sym or _is_forbidden_implicit_spot_symbol(sym):
        return False
    if is_bitcoin_underlying(sym):
        return False
    return sym in collect_governed_futures_symbols(ranking_funnel)


def resolve_selected_futures_symbol_from_ranking_funnel(
    ranking_funnel: Dict[str, Any],
) -> str:
    """Display-only: first eligible governed ranking row from selected → shortlist → universe."""
    stages = ranking_funnel.get("stages") if isinstance(ranking_funnel.get("stages"), dict) else {}
    for stage_key in ("selected", "shortlist", "universe"):
        for row in stages.get(stage_key) or []:
            if not isinstance(row, dict):
                continue
            sym = str(row.get("symbol") or "").strip()
            if sym and is_eligible_market_dashboard_instrument(sym):
                return sym
    return ""


def build_futures_first_empty_payload(
    *,
    symbol: str,
    timeframe: str,
    limit: int,
    unavailable_reason: str,
) -> Dict[str, Any]:
    """Fail-closed futures SSR payload — no spot OHLCV, no synthetic fallback."""
    return {
        "generated_at_utc": _utc_now_iso(),
        "source": "futures",
        "symbol": symbol,
        "timeframe": timeframe,
        "limit_requested": limit,
        "bars_returned": 0,
        "meta": {
            "unavailable": True,
            "reason": unavailable_reason,
            "source_mode": "futures_read_only_ssr",
            "futures_empty_state": True,
            "fail_closed": True,
        },
        "bars": [],
    }


def resolve_market_page_data(
    *,
    symbol: str | None,
    timeframe: str,
    limit: int,
    source: str | None,
    top_n: int = DEFAULT_TOP_N,
) -> tuple[str, MarketSource, Dict[str, Any], bool]:
    """Resolve canonical GET /market request state (futures-first, no implicit spot fallback)."""
    _ = top_n  # display-only; governed list sizing uses template context
    src = _normalize_source(source)
    sym = _normalize_request_symbol(symbol)

    if src == "futures":
        ranking_funnel = build_market_ranking_funnel_display_context()
        if sym and not is_valid_governed_futures_symbol(sym, ranking_funnel):
            payload = build_futures_first_empty_payload(
                symbol=sym,
                timeframe=timeframe,
                limit=limit,
                unavailable_reason="futures_symbol_not_in_governed_universe",
            )
            return sym, src, payload, True
        if not sym:
            sym = resolve_selected_futures_symbol_from_ranking_funnel(ranking_funnel)
        if not sym:
            payload = build_futures_first_empty_payload(
                symbol="",
                timeframe=timeframe,
                limit=limit,
                unavailable_reason="futures_snapshot_unavailable",
            )
            return "", src, payload, True

        futures_ohlcv = build_market_futures_ohlcv_display_context()
        bars, reason, unavailable = resolve_futures_ohlcv_series_for_symbol(
            futures_ohlcv=futures_ohlcv,
            symbol=sym,
            timeframe=timeframe,
            limit=limit,
        )
        if not unavailable:
            payload = {
                "generated_at_utc": str(futures_ohlcv.get("generated_at_iso") or _utc_now_iso()),
                "source": "futures",
                "symbol": sym,
                "timeframe": timeframe,
                "limit_requested": limit,
                "bars_returned": len(bars),
                "meta": {
                    "source_mode": "futures_read_only_ssr",
                    "futures_ohlcv_readmodel_id": futures_ohlcv.get("readmodel_id"),
                    "data_source": futures_ohlcv.get("source"),
                    "freshness": futures_ohlcv.get("generated_at_iso"),
                    "fail_closed": False,
                },
                "bars": bars,
            }
            return sym, src, payload, False

        payload = build_futures_first_empty_payload(
            symbol=sym,
            timeframe=timeframe,
            limit=limit,
            unavailable_reason=reason or "futures_ohlcv_not_wired",
        )
        return sym, src, payload, True

    if not sym:
        payload = build_futures_first_empty_payload(
            symbol="",
            timeframe=timeframe,
            limit=limit,
            unavailable_reason="legacy_source_requires_explicit_symbol",
        )
        return "", src, payload, True

    if is_bitcoin_underlying(sym):
        payload = build_futures_first_empty_payload(
            symbol=sym,
            timeframe=timeframe,
            limit=limit,
            unavailable_reason="bitcoin_instrument_excluded",
        )
        return sym, src, payload, True

    payload, data_unavailable = build_market_payload_for_page(
        symbol=sym,
        timeframe=timeframe,
        limit=limit,
        source=src,
    )
    return sym, src, payload, data_unavailable


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


def build_market_top_n_toggle_href(
    *,
    top_n: int,
    symbol: str,
    source: str,
    timeframe: str,
    limit: int,
    extras: MarketViewQueryExtras | None = None,
) -> str:
    """Display-only Top-N toggle link preserving current instrument and matrix view state."""
    return build_market_canonical_href(
        source=source,
        symbol=symbol,
        timeframe=timeframe,
        limit=limit,
        top_n=top_n,
        extras=extras,
        include_default_top_n=True,
    )


def build_market_symbol_nav_href(
    *,
    symbol: str,
    source: str,
    timeframe: str,
    limit: int,
    top_n: int = DEFAULT_TOP_N,
    extras: MarketViewQueryExtras | None = None,
) -> str:
    """Display-only GET /market query link for a ranking row symbol (no selector authority)."""
    return build_market_canonical_href(
        source=source,
        symbol=symbol,
        timeframe=timeframe,
        limit=limit,
        top_n=top_n,
        extras=extras,
        include_default_top_n=False,
    )


def _format_ranking_score_display(row: dict[str, Any]) -> str:
    if "display_score" not in row:
        return "unavailable"
    score = row.get("display_score")
    if score is None or isinstance(score, bool):
        return "unavailable"
    try:
        return f"{float(score):.4f}".rstrip("0").rstrip(".")
    except (TypeError, ValueError):
        return "unavailable"


def _parse_ranking_score_sort_value(row: dict[str, Any]) -> float | None:
    if "display_score" not in row:
        return None
    score = row.get("display_score")
    if score is None or isinstance(score, bool):
        return None
    try:
        return float(score)
    except (TypeError, ValueError):
        return None


def _derive_governed_matrix_row_ohlcv_fields(
    *,
    futures_ohlcv: Dict[str, Any],
    symbol: str,
    timeframe: str,
    limit: int,
) -> dict[str, Any]:
    """Display-only OHLCV fields for a governed matrix row (no new scoring)."""
    bars, reason, unavailable = resolve_futures_ohlcv_series_for_symbol(
        futures_ohlcv=futures_ohlcv,
        symbol=symbol,
        timeframe=timeframe,
        limit=limit,
    )
    if unavailable or not bars:
        return {
            "last_price_display": "—",
            "last_price_sort": None,
            "change_display": "—",
            "change_sort": None,
            "volume_display": "—",
            "volume_sort": None,
            "ohlcv_status": reason or "unavailable",
        }

    last_bar = bars[-1] if isinstance(bars[-1], dict) else {}
    prev_bar = bars[-2] if len(bars) >= 2 and isinstance(bars[-2], dict) else {}

    def _fval(row: dict[str, Any], key: str) -> float | None:
        raw = row.get(key)
        if raw is None:
            return None
        try:
            return float(raw)
        except (TypeError, ValueError):
            return None

    last_close = _fval(last_bar, "close")
    prev_close = _fval(prev_bar, "close")
    last_volume = _fval(last_bar, "volume")
    change_pct: float | None = None
    if last_close is not None and prev_close is not None and prev_close != 0:
        change_pct = ((last_close - prev_close) / prev_close) * 100.0

    return {
        "last_price_display": _format_display_price(last_close) if last_close is not None else "—",
        "last_price_sort": last_close,
        "change_display": f"{change_pct:.4f}%" if change_pct is not None else "—",
        "change_sort": change_pct,
        "volume_display": _format_display_price(last_volume) if last_volume is not None else "—",
        "volume_sort": last_volume,
        "ohlcv_status": "ready",
    }


def _enrich_ranking_row_for_watchlist(
    row: dict[str, Any],
    *,
    selected_symbol: str,
    source: str,
    timeframe: str,
    limit: int,
    top_n: int = DEFAULT_TOP_N,
    extras: MarketViewQueryExtras | None = None,
) -> dict[str, Any]:
    row_symbol = str(row.get("symbol") or "")
    is_selected = _normalize_symbol_for_match(row_symbol) == _normalize_symbol_for_match(
        selected_symbol
    )
    return {
        **row,
        "is_selected": is_selected,
        "score_display": _format_ranking_score_display(row),
        "market_nav_href": build_market_symbol_nav_href(
            symbol=row_symbol,
            source=source,
            timeframe=timeframe,
            limit=limit,
            top_n=top_n,
            extras=extras,
        ),
    }


def _ranking_funnel_snapshot_status(ranking_funnel: Dict[str, Any]) -> str:
    """Canonical governed snapshot read status for futures-first default wiring."""
    display = str(ranking_funnel.get("display_status") or "disabled")
    if display == "disabled":
        return "disabled"
    if display == "unconfigured":
        return "unconfigured"
    if display == "builder_error":
        return "malformed"
    if ranking_funnel.get("stale") is True:
        return "stale"
    if display == "ready" and ranking_funnel.get("has_rows"):
        return "ready"
    if display == "empty":
        return "empty"
    return display


def build_market_governed_top20_display_context(
    *,
    ranking_funnel: Dict[str, Any],
    f5_dashboard: Dict[str, Any],
    futures_ohlcv: Dict[str, Any] | None = None,
    selected_symbol: str = "",
    source: str = DEFAULT_SOURCE,
    timeframe: str = DEFAULT_TIMEFRAME,
    limit: int = DEFAULT_LIMIT,
    top_n: int = DEFAULT_TOP_N,
    extras: MarketViewQueryExtras | None = None,
) -> Dict[str, Any]:
    """Primary governed Top-N visual matrix + F5 metadata for futures-first GET /market (view-only)."""
    snapshot_status = _ranking_funnel_snapshot_status(ranking_funnel)
    stages = ranking_funnel.get("stages") if isinstance(ranking_funnel.get("stages"), dict) else {}
    selected_rows = [
        row
        for row in (stages.get("selected") or [])
        if isinstance(row, dict) and _is_eligible_ranking_row(row)
    ]
    visible_rows = selected_rows[:top_n]

    f5_gate_enabled = bool(f5_dashboard.get("gate_enabled"))
    f5_display_status = str(f5_dashboard.get("display_status") or "disabled")
    f5_overall_status = str(f5_dashboard.get("overall_status") or "futures_metadata_missing")
    if not f5_gate_enabled:
        f5_row_status = "unavailable"
    elif f5_display_status == "builder_error":
        f5_row_status = "malformed"
    elif f5_display_status in ("unconfigured", "disabled"):
        f5_row_status = "unavailable"
    else:
        f5_row_status = f5_overall_status

    freshness_display = str(ranking_funnel.get("generated_at_iso") or "").strip() or "unavailable"
    data_source = str(ranking_funnel.get("source") or "").strip() or "unavailable"
    snapshot_stale = ranking_funnel.get("stale") is True

    ohlcv_ctx = futures_ohlcv if isinstance(futures_ohlcv, dict) else {}
    rows: list[dict[str, Any]] = []
    for row in visible_rows:
        row_symbol = str(row.get("symbol") or "")
        is_selected = _normalize_symbol_for_match(row_symbol) == _normalize_symbol_for_match(
            selected_symbol
        )
        ohlcv_fields = _derive_governed_matrix_row_ohlcv_fields(
            futures_ohlcv=ohlcv_ctx,
            symbol=row_symbol,
            timeframe=timeframe,
            limit=limit,
        )
        row_rank = row.get("rank")
        try:
            rank_sort = int(row_rank) if row_rank is not None else None
        except (TypeError, ValueError):
            rank_sort = None
        if snapshot_stale:
            row_data_status = "stale"
        elif snapshot_status == "malformed":
            row_data_status = "malformed"
        elif ohlcv_fields["ohlcv_status"] == "ready":
            row_data_status = "ready"
        else:
            row_data_status = "partial"
        rows.append(
            {
                "rank": row_rank,
                "rank_sort": rank_sort,
                "symbol": row_symbol,
                "score_display": _format_ranking_score_display(row),
                "score_sort": _parse_ranking_score_sort_value(row),
                "eligibility_status": "selected",
                "f5_status": f5_row_status,
                "last_price_display": ohlcv_fields["last_price_display"],
                "last_price_sort": ohlcv_fields["last_price_sort"],
                "change_display": ohlcv_fields["change_display"],
                "change_sort": ohlcv_fields["change_sort"],
                "volume_display": ohlcv_fields["volume_display"],
                "volume_sort": ohlcv_fields["volume_sort"],
                "freshness_display": freshness_display,
                "freshness_filter": "stale" if snapshot_stale else "fresh",
                "data_source": data_source,
                "data_status": row_data_status,
                "stale": snapshot_stale,
                "is_selected": is_selected,
                "market_nav_href": build_market_symbol_nav_href(
                    symbol=row_symbol,
                    source=source,
                    timeframe=timeframe,
                    limit=limit,
                    top_n=top_n,
                    extras=extras,
                ),
            }
        )

    snapshot_available = snapshot_status in ("ready", "stale")
    f5_filter_values = sorted({str(r["f5_status"]) for r in rows})
    producer_rows = rows
    display_rows, resolved_extras, active_sort_field, active_sort_direction, filter_no_results = (
        apply_matrix_view_state(
            rows,
            extras,
            allowed_f5_statuses=f5_filter_values,
        )
    )
    matrix_control_hrefs = build_market_matrix_control_hrefs(
        source=source,
        symbol=selected_symbol,
        timeframe=timeframe,
        limit=limit,
        top_n=top_n,
        extras=resolved_extras,
        active_sort_field=active_sort_field,
        active_sort_direction=active_sort_direction,
        f5_filter_values=f5_filter_values,
    )
    return {
        "section_visible": True,
        "snapshot_available": snapshot_available,
        "snapshot_status": snapshot_status,
        "display_status": "ready" if snapshot_available else snapshot_status,
        "rows": display_rows,
        "producer_rows": producer_rows,
        "row_count": len(producer_rows),
        "visible_row_count": len(display_rows),
        "filter_no_results": filter_no_results,
        "top_n": top_n,
        "top_n_default": DEFAULT_TOP_N,
        "top_n_selectable": True,
        "selected_symbol": selected_symbol,
        "data_source": data_source,
        "generated_at_iso": freshness_display,
        "stale": snapshot_stale,
        "stale_reason": str(ranking_funnel.get("stale_reason") or ""),
        "gate_enabled": bool(ranking_funnel.get("gate_enabled")),
        "f5_display_status": f5_display_status,
        "f5_overall_status": f5_overall_status,
        "f5_gate_enabled": f5_gate_enabled,
        "f5_filter_values": f5_filter_values,
        "unavailable_message": "Futures data unavailable",
        "view_only": True,
        "read_only": True,
        "matrix_row_schema": MATRIX_ROW_SCHEMA,
        "available_sort_fields": AVAILABLE_SORT_FIELDS,
        "available_filter_fields": AVAILABLE_FILTER_FIELDS,
        "default_sort_field": "rank",
        "default_sort_direction": "asc",
        "active_sort_field": active_sort_field,
        "active_sort_direction": active_sort_direction,
        "resolved_matrix_view_query": resolved_extras,
        "matrix_control_hrefs": matrix_control_hrefs,
    }


def build_market_ranking_watchlist_display_context(
    *,
    ranking_funnel: Dict[str, Any],
    operator_overview: Dict[str, Any],
    selected_symbol: str,
    source: str,
    timeframe: str,
    limit: int,
    top_n: int = DEFAULT_TOP_N,
    extras: MarketViewQueryExtras | None = None,
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
                top_n=top_n,
                extras=extras,
            )
            for row in (stages.get(stage_key) or [])
            if isinstance(row, dict) and _is_eligible_ranking_row(row)
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
            top_n=top_n,
            extras=extras,
        )
        for row in raw_rows
        if isinstance(row, dict) and _is_eligible_ranking_row(row)
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
    source: MarketSource,
    payload: Dict[str, Any],
    market_depth: Dict[str, Any],
) -> Dict[str, Any]:
    """Display-only instrument header context for GET /market (no selector authority)."""

    if source == "dummy":
        source_mode = "dummy_offline_synthetic"
    elif source == "kraken":
        source_mode = "kraken_public_ohlcv"
    else:
        source_mode = "futures_read_only_ssr"

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
    source: MarketSource,
    payload: Dict[str, Any],
    market_depth: Dict[str, Any],
) -> Dict[str, Any]:
    """Display-only futures metrics strip for GET /market (derived from bars/depth, no signals)."""

    if source == "dummy":
        source_mode = "dummy_offline_synthetic"
    elif source == "kraken":
        source_mode = "kraken_public_ohlcv"
    else:
        source_mode = "futures_read_only_ssr"

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
            if isinstance(row, dict) and _is_eligible_ranking_row(row):
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
    source: MarketSource,
    payload: Dict[str, Any],
    data_unavailable: bool,
) -> Dict[str, Any]:
    """Above-the-fold operator market values (display-only, derived from embedded bars)."""

    if source == "dummy":
        source_kind = "dummy-offline-synthetic"
        source_mode = "dummy_offline_synthetic"
    elif source == "kraken":
        source_kind = "kraken-public"
        source_mode = "kraken_public_ohlcv"
    else:
        source_kind = "futures-read-only-ssr"
        source_mode = "futures_read_only_ssr"

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


def _f5_section_field_value(section: Dict[str, Any], field: str) -> str:
    rows = section.get("rows") if isinstance(section.get("rows"), list) else []
    for row in rows:
        if not isinstance(row, dict) or str(row.get("field") or "") != field:
            continue
        if str(row.get("display_status") or "") == "missing":
            return "unavailable"
        value = str(row.get("value") or "").strip()
        return value if value and value != "missing" else "unavailable"
    return "unavailable"


def _f5_operator_status_display(raw_status: str) -> tuple[str, str]:
    """Map internal F5 tokens to operator-readable (category, label) pairs."""
    status = str(raw_status or "unavailable").strip().lower()
    if status in ("unavailable", "disabled", "unconfigured"):
        return "missing", "Unavailable"
    if status == "malformed":
        return "missing", "Malformed"
    if status == "ready":
        return "ready", "Ready"
    category_by_status: dict[str, str] = {
        "futures_metadata_partial": "partial",
        "futures_metadata_missing": "missing",
        "provenance_missing": "missing",
        "provenance_partial": "partial",
        "backtest_realism_incomplete": "incomplete",
        "risk_safety_incomplete": "incomplete",
        "metadata_label_only": "partial",
        "testnet_candidate_only": "partial",
        "unsupported_for_live": "incomplete",
    }
    label_by_status: dict[str, str] = {
        "futures_metadata_partial": "Partial metadata",
        "futures_metadata_missing": "Metadata missing",
        "provenance_missing": "Provenance missing",
        "provenance_partial": "Provenance partial",
        "backtest_realism_incomplete": "Realism incomplete",
        "risk_safety_incomplete": "Risk/safety incomplete",
        "metadata_label_only": "Metadata label only",
        "testnet_candidate_only": "Testnet candidate",
        "unsupported_for_live": "Unsupported for live",
    }
    category = category_by_status.get(status, "partial")
    label = label_by_status.get(status, status.replace("_", " ").title())
    return category, label


def _build_workspace_visual_summary(
    payload: Dict[str, Any],
    *,
    ranking_rank: Any,
    data_quality: str,
    freshness_stale: bool,
) -> dict[str, Any]:
    """Descriptive chart/ranking summary derived from already-resolved SSR values."""
    bars = payload.get("bars") if isinstance(payload.get("bars"), list) else []
    visible = [bar for bar in bars if isinstance(bar, dict)]
    if not visible:
        return {
            "implemented": False,
            "visible_bar_count": 0,
            "up_bar_count": 0,
            "down_bar_count": 0,
            "total_volume_display": "unavailable",
            "close_range_position_display": "unavailable",
            "ranking_position_display": "unavailable",
            "freshness_quality_display": "unavailable",
        }

    up_bar_count = 0
    lows: list[float] = []
    highs: list[float] = []
    total_volume = 0.0
    for bar in visible:
        try:
            o = float(bar.get("open"))
            c = float(bar.get("close"))
            lo = float(bar.get("low"))
            hi = float(bar.get("high"))
        except (TypeError, ValueError):
            continue
        if c >= o:
            up_bar_count += 1
        lows.append(lo)
        highs.append(hi)
        raw_volume = bar.get("volume")
        if raw_volume is not None:
            try:
                total_volume += max(0.0, float(raw_volume))
            except (TypeError, ValueError):
                pass

    down_bar_count = len(visible) - up_bar_count
    range_low = min(lows) if lows else None
    range_high = max(highs) if highs else None
    last_close = None
    try:
        last_close = float(visible[-1].get("close"))
    except (TypeError, ValueError):
        last_close = None

    close_range_position_display = "unavailable"
    if (
        last_close is not None
        and range_low is not None
        and range_high is not None
        and range_high > range_low
    ):
        position_pct = ((last_close - range_low) / (range_high - range_low)) * 100.0
        close_range_position_display = f"{position_pct:.1f}% of visible range"

    ranking_position_display = str(ranking_rank) if ranking_rank is not None else "unavailable"
    if freshness_stale or data_quality == "stale":
        freshness_quality_display = "stale"
    else:
        freshness_quality_display = str(data_quality or "unavailable")

    return {
        "implemented": True,
        "visible_bar_count": len(visible),
        "up_bar_count": up_bar_count,
        "down_bar_count": down_bar_count,
        "total_volume_display": _format_display_price(total_volume),
        "close_range_position_display": close_range_position_display,
        "ranking_position_display": ranking_position_display,
        "freshness_quality_display": freshness_quality_display,
    }


def _find_governed_row_for_symbol(
    governed_top20: Dict[str, Any],
    symbol: str,
) -> dict[str, Any] | None:
    for key in ("producer_rows", "rows"):
        rows = governed_top20.get(key) if isinstance(governed_top20.get(key), list) else []
        normalized = _normalize_symbol_for_match(symbol)
        for row in rows:
            if not isinstance(row, dict):
                continue
            if _normalize_symbol_for_match(str(row.get("symbol") or "")) == normalized:
                return row
    return None


def _resolve_workspace_ohlcv_status(
    *,
    data_unavailable: bool,
    payload: Dict[str, Any],
    primary_values: Dict[str, Any],
    futures_ohlcv: Dict[str, Any],
) -> str:
    reason = str(primary_values.get("unavailable_reason") or "").strip()
    if reason == "futures_ohlcv_malformed":
        return "malformed"
    if reason == "futures_ohlcv_stale":
        return "stale"
    if data_unavailable:
        if reason in ("futures_ohlcv_empty", "futures_ohlcv_symbol_missing"):
            return "empty"
        return "unavailable"
    if int(payload.get("bars_returned") or 0) == 0:
        return "empty"
    if futures_ohlcv.get("display_status") == "builder_error":
        return "malformed"
    if futures_ohlcv.get("stale") is True:
        return "stale"
    return "ready"


def build_market_selected_instrument_workspace_display_context(
    *,
    symbol: str,
    source: MarketSource,
    primary_values: Dict[str, Any],
    governed_top20: Dict[str, Any],
    f5_dashboard: Dict[str, Any],
    futures_ohlcv: Dict[str, Any],
    payload: Dict[str, Any],
    data_unavailable: bool,
) -> Dict[str, Any]:
    """Single canonical selected-instrument workspace view-model (display-only, no recomputation)."""
    governed_row = _find_governed_row_for_symbol(governed_top20, symbol)
    ohlcv_status = _resolve_workspace_ohlcv_status(
        data_unavailable=data_unavailable,
        payload=payload,
        primary_values=primary_values,
        futures_ohlcv=futures_ohlcv,
    )
    volume_display = str(primary_values.get("last_volume_display") or "").strip()
    volume_status = "available" if volume_display and volume_display != "—" else "unavailable"

    ranking_rank = governed_row.get("rank") if governed_row else None
    ranking_score = (
        str(governed_row.get("score_display") or "unavailable") if governed_row else "unavailable"
    )
    ranking_eligibility = (
        str(governed_row.get("eligibility_status") or "unavailable")
        if governed_row
        else "unavailable"
    )
    ranking_f5_status = (
        str(governed_row.get("f5_status") or "unavailable") if governed_row else "unavailable"
    )
    ranking_data_status = (
        str(governed_row.get("data_status") or "unavailable") if governed_row else "unavailable"
    )

    f1 = f5_dashboard.get("f1") if isinstance(f5_dashboard.get("f1"), dict) else {}
    f2 = f5_dashboard.get("f2") if isinstance(f5_dashboard.get("f2"), dict) else {}
    f3 = f5_dashboard.get("f3") if isinstance(f5_dashboard.get("f3"), dict) else {}
    f4 = f5_dashboard.get("f4") if isinstance(f5_dashboard.get("f4"), dict) else {}

    contract_fields = {
        "contract_type": _f5_section_field_value(f1, "contract_type"),
        "base_currency": _f5_section_field_value(f1, "base_currency"),
        "quote_currency": _f5_section_field_value(f1, "quote_currency"),
        "tick_size": _f5_section_field_value(f1, "tick_size"),
        "lot_size": _f5_section_field_value(f1, "lot_size"),
        "contract_size": _f5_section_field_value(f1, "contract_size"),
        "perpetual": _f5_section_field_value(f1, "perpetual"),
        "exchange": _f5_section_field_value(f1, "exchange"),
    }
    contract_complete = all(v != "unavailable" for v in contract_fields.values())
    contract_unavailable_fields = [
        name.replace("_", " ").title()
        for name, value in contract_fields.items()
        if value == "unavailable"
    ]

    f5_gate = bool(f5_dashboard.get("gate_enabled"))
    f5_display = str(f5_dashboard.get("display_status") or "disabled")
    f5_cards: list[dict[str, str]] = []
    for card_id, section, label in (
        ("f1", f1, "F1 Instrument"),
        ("f2", f2, "F2 Provenance"),
        ("f3", f3, "F3 Realism"),
        ("f4", f4, "F4 Risk/Safety"),
    ):
        if not f5_gate:
            card_status = "unavailable"
        elif f5_display == "builder_error":
            card_status = "malformed"
        elif f5_display in ("unconfigured", "disabled"):
            card_status = "unavailable"
        else:
            card_status = str(section.get("status") or "unavailable")
        operator_category, operator_label = _f5_operator_status_display(card_status)
        f5_cards.append(
            {
                "id": card_id,
                "label": label,
                "status": card_status,
                "operator_category": operator_category,
                "operator_label": operator_label,
            }
        )

    meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
    freshness_source = (
        str(
            meta.get("data_source")
            or futures_ohlcv.get("source")
            or governed_top20.get("data_source")
            or ""
        ).strip()
        or "unavailable"
    )
    generated_at = (
        str(
            meta.get("freshness")
            or futures_ohlcv.get("generated_at_iso")
            or primary_values.get("generated_at_utc")
            or ""
        ).strip()
        or "unavailable"
    )
    snapshot_stale = bool(governed_top20.get("stale")) or bool(futures_ohlcv.get("stale"))
    stale_reason = str(
        governed_top20.get("stale_reason") or futures_ohlcv.get("stale_reason") or ""
    ).strip()

    if ohlcv_status == "malformed":
        data_quality = "malformed"
    elif ohlcv_status == "stale" or snapshot_stale:
        data_quality = "stale"
    elif ohlcv_status == "empty":
        data_quality = "empty"
    elif ohlcv_status == "ready":
        data_quality = "ready"
    else:
        data_quality = "partial"

    visual_summary = _build_workspace_visual_summary(
        payload,
        ranking_rank=ranking_rank,
        data_quality=data_quality,
        freshness_stale=snapshot_stale,
    )

    return {
        "workspace_visible": source == "futures",
        "symbol": symbol,
        "display_symbol": str(primary_values.get("symbol") or symbol or "unavailable"),
        "source": str(primary_values.get("source") or source),
        "source_mode": str(primary_values.get("source_mode") or ""),
        "timeframe": str(primary_values.get("timeframe") or ""),
        "selected_instrument": symbol,
        "ranking_rank": ranking_rank,
        "ranking_score_display": ranking_score,
        "ranking_eligibility_status": ranking_eligibility,
        "ranking_f5_status": ranking_f5_status,
        "ranking_data_status": ranking_data_status,
        "ranking_top_n": int(governed_top20.get("top_n") or DEFAULT_TOP_N),
        "ranking_in_universe": governed_row is not None,
        "last_price_display": (
            str(primary_values.get("last_close_display") or "unavailable")
            if primary_values.get("status") == "available"
            else "unavailable"
        ),
        "change_abs_display": str(primary_values.get("change_abs_display") or "unavailable"),
        "change_pct_display": str(primary_values.get("change_pct_display") or "unavailable"),
        "change_status": str(primary_values.get("change_status") or "unavailable"),
        "ohlcv_status": ohlcv_status,
        "bars_returned": int(
            primary_values.get("bars_returned") or payload.get("bars_returned") or 0
        ),
        "volume_display": volume_display if volume_status == "available" else "unavailable",
        "volume_status": volume_status,
        "freshness_source": freshness_source,
        "freshness_generated_at": generated_at,
        "freshness_stale": snapshot_stale,
        "freshness_stale_reason": stale_reason,
        "data_quality_status": data_quality,
        "f5_gate_enabled": f5_gate,
        "f5_display_status": f5_display,
        "f5_overall_status": str(f5_dashboard.get("overall_status") or "unavailable"),
        "f5_cards": f5_cards,
        "contract_metadata": contract_fields,
        "contract_metadata_complete": contract_complete,
        "contract_unavailable_fields": contract_unavailable_fields,
        "visual_summary": visual_summary,
        "view_only": True,
        "read_only": True,
    }


def build_market_v0_page_template_context(
    *,
    get_project_status: Callable[[], Dict[str, Any]],
    symbol: str,
    timeframe: str,
    limit: int,
    source: MarketSource,
    payload: Dict[str, Any],
    data_unavailable: bool,
    top_n: int = DEFAULT_TOP_N,
    extras: MarketViewQueryExtras | None = None,
) -> Dict[str, Any]:
    """SSR template context for GET /market (display-only; always includes primary_values)."""

    primary_values = build_market_primary_values_display_context(
        symbol=symbol,
        timeframe=timeframe,
        limit=limit,
        source=source,
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
        source=source,
        timeframe=timeframe,
        limit=limit,
        top_n=top_n,
        extras=extras,
    )
    instrument_header = build_market_instrument_header_display_context(
        symbol=symbol,
        timeframe=timeframe,
        limit=limit,
        source=source,
        payload=payload,
        market_depth=market_depth,
    )
    futures_metrics_strip = build_market_futures_metrics_strip_display_context(
        source=source,
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
    _pin_market_page_display_timestamps(dp_display)
    f5_dashboard = build_futures_read_only_market_dashboard_display_context()
    futures_ohlcv = build_market_futures_ohlcv_display_context()
    governed_top20 = build_market_governed_top20_display_context(
        ranking_funnel=ranking_funnel,
        f5_dashboard=f5_dashboard,
        futures_ohlcv=futures_ohlcv,
        selected_symbol=symbol,
        source=source,
        timeframe=timeframe,
        limit=limit,
        top_n=top_n,
        extras=extras,
    )
    resolved_view_query = governed_top20.get("resolved_matrix_view_query")
    if not isinstance(resolved_view_query, MarketViewQueryExtras):
        resolved_view_query = extras or MarketViewQueryExtras()
    selected_instrument_workspace = build_market_selected_instrument_workspace_display_context(
        symbol=symbol,
        source=source,
        primary_values=primary_values,
        governed_top20=governed_top20,
        f5_dashboard=f5_dashboard,
        futures_ohlcv=futures_ohlcv,
        payload=payload,
        data_unavailable=data_unavailable,
    )
    encoded_symbol = quote(symbol, safe="")
    legacy_demo_href = (
        f"/market?source=dummy&symbol={quote('ETHUSDT', safe='')}"
        f"&timeframe={timeframe}&limit={limit}"
    )
    return {
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
        "futures_ohlcv": futures_ohlcv,
        "governed_top20": governed_top20,
        "selected_instrument_workspace": selected_instrument_workspace,
        "top_n": top_n,
        "top_n_toggle_hrefs": {
            20: build_market_top_n_toggle_href(
                top_n=20,
                symbol=symbol,
                source=source,
                timeframe=timeframe,
                limit=limit,
                extras=resolved_view_query,
            ),
            50: build_market_top_n_toggle_href(
                top_n=50,
                symbol=symbol,
                source=source,
                timeframe=timeframe,
                limit=limit,
                extras=resolved_view_query,
            ),
        },
        "double_play_json_url": "/api/master-v2/double-play/dashboard-display.json",
        "legacy_demo_href": legacy_demo_href,
        "futures_first": source == "futures",
        "page_title": PAGE_TITLE,
        "primary_values": primary_values,
        "data_unavailable": data_unavailable,
        "query": {
            "symbol": symbol,
            "timeframe": timeframe,
            "limit": limit,
            "source": source,
            "top_n": top_n,
            "matrix_filter_symbol": resolved_view_query.matrix_filter_symbol,
            "matrix_filter_f5_status": resolved_view_query.matrix_filter_f5_status,
            "matrix_filter_freshness": resolved_view_query.matrix_filter_freshness,
            "matrix_sort_field": resolved_view_query.matrix_sort_field,
            "matrix_sort_direction": resolved_view_query.matrix_sort_direction,
        },
        "matrix_view_query": resolved_view_query,
    }


def create_market_router(
    templates: Jinja2Templates,
    get_project_status: Callable[[], Dict[str, Any]],
) -> APIRouter:
    router = APIRouter(tags=["market-readonly"])

    @router.get("/api/market/ohlcv")
    async def api_market_ohlcv(
        symbol: str = Query("", description="Trading-Paar; bei Legacy-Quellen erforderlich"),
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
            description="futures = SSR-only (kein OHLCV); kraken/dummy = explizite Legacy-Quelle",
        ),
    ) -> Dict[str, Any]:
        if timeframe not in MARKET_TIMEFRAMES:
            raise HTTPException(
                status_code=422,
                detail=f"timeframe muss einer von {list(MARKET_TIMEFRAMES)} sein, nicht {timeframe!r}",
            )
        src = _normalize_source(source)
        if src == "futures":
            raise HTTPException(
                status_code=422,
                detail=(
                    "source=futures ist SSR-only auf GET /market; "
                    "für OHLCV-JSON source=kraken oder source=dummy mit explizitem symbol verwenden"
                ),
            )
        sym = _normalize_request_symbol(symbol)
        if not sym:
            raise HTTPException(
                status_code=422,
                detail="symbol ist für Legacy-OHLCV-Quellen erforderlich (kein impliziter Spot-Default)",
            )
        return build_market_payload(symbol=sym, timeframe=timeframe, limit=limit, source=src)

    @router.get("/market", response_class=HTMLResponse)
    async def market_v0_page(
        request: Request,
        symbol: str = Query(DEFAULT_SYMBOL),
        timeframe: str = Query(DEFAULT_TIMEFRAME),
        limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_OHLCV_LIMIT),
        source: str = Query(DEFAULT_SOURCE),
        top_n: Optional[str] = Query(None, description="Governed Top-N list size (20 or 50)"),
        matrix_filter_symbol: Optional[str] = Query(
            None, description="View-only matrix symbol filter"
        ),
        matrix_filter_f5_status: Optional[str] = Query(
            None, description="View-only matrix F5 status filter"
        ),
        matrix_filter_freshness: Optional[str] = Query(
            None, description="View-only matrix freshness filter"
        ),
        matrix_sort_field: Optional[str] = Query(None, description="View-only matrix sort field"),
        matrix_sort_direction: Optional[str] = Query(
            None, description="View-only matrix sort direction"
        ),
    ) -> Any:
        if timeframe not in MARKET_TIMEFRAMES:
            raise HTTPException(
                status_code=422,
                detail=f"timeframe muss einer von {list(MARKET_TIMEFRAMES)} sein, nicht {timeframe!r}",
            )
        normalized_top_n = normalize_top_n(top_n)
        view_extras = build_market_view_query_extras(
            matrix_filter_symbol=matrix_filter_symbol,
            matrix_filter_f5_status=matrix_filter_f5_status,
            matrix_filter_freshness=matrix_filter_freshness,
            matrix_sort_field=matrix_sort_field,
            matrix_sort_direction=matrix_sort_direction,
        )
        sym, src, payload, data_unavailable = resolve_market_page_data(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
            source=source,
            top_n=normalized_top_n,
        )
        return templates.TemplateResponse(
            request,
            "market_v0.html",
            build_market_v0_page_template_context(
                get_project_status=get_project_status,
                symbol=sym,
                timeframe=timeframe,
                limit=limit,
                source=src,
                payload=payload,
                data_unavailable=data_unavailable,
                top_n=normalized_top_n,
                extras=view_extras,
            ),
        )

    return router
