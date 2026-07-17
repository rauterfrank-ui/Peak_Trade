"""Optional read-only source loading for Market Dashboard product surface (PR-D).

Loads only env-gated OHLCV/ranking readmodels already produced offline.
Does not call replay, Double-Play composition, current-state snapshots,
static fixtures, or dummy OHLCV builders.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from src.webui.market_futures_ohlcv_readmodel_v0 import (
    MarketFuturesOhlcvReadmodelError,
    build_market_futures_ohlcv_readmodel,
)
from src.webui.market_futures_ohlcv_runtime_v0 import (
    ENV_BUNDLE_ROOT as OHLCV_ENV_BUNDLE_ROOT,
    ENV_ENABLED as OHLCV_ENV_ENABLED,
    enabled_explicitly_on as ohlcv_enabled_explicitly_on,
    resolved_bundle_root_or_none as ohlcv_resolved_bundle_root_or_none,
)
from src.webui.market_ranking_funnel_readmodel_v0 import (
    MarketRankingFunnelReadmodelError,
    build_market_ranking_funnel_readmodel,
)
from src.webui.market_ranking_funnel_runtime_v0 import (
    ENV_BUNDLE_ROOT as RANKING_ENV_BUNDLE_ROOT,
    ENV_ENABLED as RANKING_ENV_ENABLED,
    enabled_explicitly_on as ranking_enabled_explicitly_on,
    resolved_bundle_root_or_none as ranking_resolved_bundle_root_or_none,
)

ENV_VENUE = "PEAK_TRADE_MARKET_DASHBOARD_VENUE"
DEFAULT_RANKING_STAGE = "universe"


@dataclass(frozen=True)
class LoadedMarketDashboardSourcesV1:
    """Raw optional sources for page aggregate + display-only chart bars."""

    generated_at: datetime
    market_ohlcv_source: Mapping[str, Any] | None
    instrument_id: str
    venue: str
    ranking_source: Mapping[str, Any] | None
    ranking_stage: str
    chart_bars: tuple[Mapping[str, Any], ...]
    market_source_reference: str | None
    ranking_source_reference: str | None
    loader_notes: tuple[str, ...]


def _selected_instrument_from_ranking(ranking: Mapping[str, Any] | None) -> str | None:
    if ranking is None:
        return None
    stages = ranking.get("stages")
    if not isinstance(stages, Mapping):
        return None
    selected = stages.get("selected")
    if not isinstance(selected, list) or not selected:
        return None
    first = selected[0]
    if not isinstance(first, Mapping):
        return None
    symbol = first.get("symbol")
    if isinstance(symbol, str) and symbol.strip():
        return symbol.strip()
    return None


def _try_load_ohlcv_readmodel() -> tuple[Mapping[str, Any] | None, str | None, str]:
    if not ohlcv_enabled_explicitly_on():
        return None, None, f"{OHLCV_ENV_ENABLED}!=1"
    root = ohlcv_resolved_bundle_root_or_none()
    if root is None:
        return None, None, f"{OHLCV_ENV_BUNDLE_ROOT} unconfigured"
    try:
        readmodel = build_market_futures_ohlcv_readmodel(root)
    except MarketFuturesOhlcvReadmodelError as exc:
        return None, None, f"ohlcv_bundle_error:{exc}"
    if not isinstance(readmodel, Mapping):
        return None, None, "ohlcv_readmodel_type_invalid"
    ref = f"env_bundle:{root.name}"
    return readmodel, ref, "ohlcv_loaded"


def _try_load_ranking_readmodel() -> tuple[Mapping[str, Any] | None, str | None, str]:
    if not ranking_enabled_explicitly_on():
        return None, None, f"{RANKING_ENV_ENABLED}!=1"
    root = ranking_resolved_bundle_root_or_none()
    if root is None:
        return None, None, f"{RANKING_ENV_BUNDLE_ROOT} unconfigured"
    try:
        readmodel = build_market_ranking_funnel_readmodel(root)
    except MarketRankingFunnelReadmodelError as exc:
        return None, None, f"ranking_bundle_error:{exc}"
    if not isinstance(readmodel, Mapping):
        return None, None, "ranking_readmodel_type_invalid"
    ref = f"env_bundle:{root.name}"
    return readmodel, ref, "ranking_loaded"


def _extract_chart_bars(
    ohlcv: Mapping[str, Any] | None, *, instrument_id: str
) -> tuple[Mapping[str, Any], ...]:
    if ohlcv is None or not instrument_id:
        return ()
    series = ohlcv.get("series")
    if not isinstance(series, Mapping):
        return ()
    instrument_series = series.get(instrument_id)
    if not isinstance(instrument_series, Mapping):
        return ()
    bars = instrument_series.get("bars")
    if not isinstance(bars, list) or not bars:
        return ()
    out: list[Mapping[str, Any]] = []
    for bar in bars:
        if isinstance(bar, Mapping):
            out.append(bar)
    return tuple(out)


def load_market_dashboard_readonly_sources_v1(
    *,
    generated_at: datetime | None = None,
) -> LoadedMarketDashboardSourcesV1:
    """Fail-closed optional source load for the productive /market route."""

    now = generated_at or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    notes: list[str] = []
    ranking, ranking_ref, ranking_note = _try_load_ranking_readmodel()
    notes.append(ranking_note)
    ohlcv, ohlcv_ref, ohlcv_note = _try_load_ohlcv_readmodel()
    notes.append(ohlcv_note)

    venue = (os.environ.get(ENV_VENUE) or "").strip()
    if not venue:
        notes.append(f"{ENV_VENUE} unset")

    instrument_id = _selected_instrument_from_ranking(ranking) or ""
    if not instrument_id:
        notes.append("selected_instrument_absent")

    # Market adapter requires explicit venue + instrument; otherwise leave unbound.
    market_source: Mapping[str, Any] | None = None
    chart_bars: tuple[Mapping[str, Any], ...] = ()
    if ohlcv is not None and instrument_id and venue:
        market_source = ohlcv
        chart_bars = _extract_chart_bars(ohlcv, instrument_id=instrument_id)
        notes.append("market_bound")
    else:
        notes.append("market_unbound")

    return LoadedMarketDashboardSourcesV1(
        generated_at=now,
        market_ohlcv_source=market_source,
        instrument_id=instrument_id,
        venue=venue,
        ranking_source=ranking,
        ranking_stage=DEFAULT_RANKING_STAGE,
        chart_bars=chart_bars,
        market_source_reference=ohlcv_ref if market_source is not None else None,
        ranking_source_reference=ranking_ref,
        loader_notes=tuple(notes),
    )


__all__ = [
    "DEFAULT_RANKING_STAGE",
    "ENV_VENUE",
    "LoadedMarketDashboardSourcesV1",
    "load_market_dashboard_readonly_sources_v1",
]
