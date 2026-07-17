"""Optional read-only source loading for Market Dashboard product surface (PR-F).

Loads env-gated OHLCV/ranking readmodels and optional review-evidence JSON for
decision / Double Play / execution / economic / diagnostics. Does not call
replay, composition, current-state snapshots, or dummy OHLCV builders.
Safety/Authority stays unbound unless a consolidated mapping is explicitly
supplied (no invented TriStates).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
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
ENV_REVIEW_EVIDENCE_ROOT = "PEAK_TRADE_MARKET_DASHBOARD_REVIEW_EVIDENCE_ROOT"
DEFAULT_RANKING_STAGE = "universe"
DEFAULT_REVIEW_VENUE = "binance_usdm_futures"

_DECISION_FILE = "canonical_decision.json"
_DOUBLE_PLAY_FILE = "double_play.json"
_EXECUTION_FILE = "execution.json"
_ECONOMIC_FILE = "economic.json"
_DIAGNOSTICS_FILE = "diagnostics.json"
_MANIFEST_FILE = "manifest.json"


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
    canonical_decision_source: Mapping[str, Any] | None
    decision_effective_at: datetime | None
    decision_evidence_reference: str | None
    decision_evidence_status: str | None
    double_play_composition: Mapping[str, Any] | None
    double_play_bull_assessment: Mapping[str, Any] | None
    double_play_bear_assessment: Mapping[str, Any] | None
    double_play_effective_at: datetime | None
    double_play_evidence_reference: str | None
    safety_authority_source: Mapping[str, Any] | None
    execution_source: Mapping[str, Any] | None
    execution_effective_at: datetime | None
    execution_operating_mode: str
    execution_evidence_reference: str | None
    economic_source: Mapping[str, Any] | None
    economic_effective_at: datetime | None
    economic_evidence_reference: str | None
    diagnostics_source: Mapping[str, Any] | None
    diagnostics_effective_at: datetime | None
    diagnostics_bundle_reference: str | None
    loader_notes: tuple[str, ...]


def _parse_iso_datetime(raw: Any) -> datetime | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    text = raw.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


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


def _review_evidence_root_or_none() -> Path | None:
    raw = (os.environ.get(ENV_REVIEW_EVIDENCE_ROOT) or "").strip()
    if not raw:
        return None
    path = Path(raw).expanduser()
    if not path.is_absolute():
        # Relative paths resolve from process CWD (review harness sets repo root).
        path = path.resolve()
    if not path.is_dir():
        return None
    return path


def _load_json_mapping(path: Path) -> Mapping[str, Any] | None:
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(payload, Mapping):
        return None
    return payload


def _load_review_evidence_bundle(
    root: Path,
) -> tuple[
    Mapping[str, Any] | None,
    datetime | None,
    str | None,
    str | None,
    Mapping[str, Any] | None,
    Mapping[str, Any] | None,
    Mapping[str, Any] | None,
    datetime | None,
    str | None,
    Mapping[str, Any] | None,
    datetime | None,
    str,
    str | None,
    Mapping[str, Any] | None,
    datetime | None,
    str | None,
    Mapping[str, Any] | None,
    datetime | None,
    str | None,
    list[str],
]:
    """Load review evidence JSON files. Malformed files stay unbound (fail-closed)."""

    notes: list[str] = []
    decision = _load_json_mapping(root / _DECISION_FILE)
    decision_effective: datetime | None = None
    decision_ref: str | None = None
    decision_status: str | None = None
    if decision is None:
        notes.append("decision_evidence_absent_or_malformed")
    else:
        decision_effective = _parse_iso_datetime(decision.get("effective_at"))
        decision_ref = f"review_evidence:{root.name}/{_DECISION_FILE}"
        status = decision.get("evidence_status")
        decision_status = status.strip() if isinstance(status, str) and status.strip() else None
        notes.append("decision_evidence_loaded")

    dp_payload = _load_json_mapping(root / _DOUBLE_PLAY_FILE)
    composition: Mapping[str, Any] | None = None
    bull: Mapping[str, Any] | None = None
    bear: Mapping[str, Any] | None = None
    dp_effective: datetime | None = None
    dp_ref: str | None = None
    if dp_payload is None:
        notes.append("double_play_evidence_absent_or_malformed")
    else:
        raw_comp = dp_payload.get("composition")
        raw_bull = dp_payload.get("bull_assessment")
        raw_bear = dp_payload.get("bear_assessment")
        if (
            isinstance(raw_comp, Mapping)
            and isinstance(raw_bull, Mapping)
            and isinstance(raw_bear, Mapping)
        ):
            composition = raw_comp
            bull = raw_bull
            bear = raw_bear
            dp_effective = _parse_iso_datetime(dp_payload.get("effective_at"))
            dp_ref = f"review_evidence:{root.name}/{_DOUBLE_PLAY_FILE}"
            notes.append("double_play_evidence_loaded")
        else:
            notes.append("double_play_evidence_malformed_structure")

    execution = _load_json_mapping(root / _EXECUTION_FILE)
    exec_effective: datetime | None = None
    exec_mode = "OFFLINE"
    exec_ref: str | None = None
    if execution is None:
        notes.append("execution_evidence_absent_or_malformed")
    else:
        exec_effective = _parse_iso_datetime(execution.get("effective_at"))
        mode = execution.get("operating_mode")
        if isinstance(mode, str) and mode.strip():
            exec_mode = mode.strip()
        exec_ref = f"review_evidence:{root.name}/{_EXECUTION_FILE}"
        notes.append("execution_evidence_loaded")

    economic = _load_json_mapping(root / _ECONOMIC_FILE)
    econ_effective: datetime | None = None
    econ_ref: str | None = None
    if economic is None:
        notes.append("economic_evidence_absent_or_malformed")
    else:
        econ_effective = _parse_iso_datetime(economic.get("effective_at"))
        econ_ref = f"review_evidence:{root.name}/{_ECONOMIC_FILE}"
        notes.append("economic_evidence_loaded")

    diagnostics = _load_json_mapping(root / _DIAGNOSTICS_FILE)
    diag_effective: datetime | None = None
    diag_ref: str | None = None
    if diagnostics is None:
        notes.append("diagnostics_evidence_absent_or_malformed")
    else:
        diag_effective = _parse_iso_datetime(diagnostics.get("effective_at"))
        diag_ref = f"review_evidence:{root.name}/{_DIAGNOSTICS_FILE}"
        notes.append("diagnostics_evidence_loaded")

    manifest = _load_json_mapping(root / _MANIFEST_FILE)
    if manifest is not None:
        notes.append("review_evidence_manifest_present")
    else:
        notes.append("review_evidence_manifest_absent")

    # Safety remains unbound: no consolidated canonical producer in review bundle.
    notes.append("safety_authority_not_bound_no_consolidated_producer")

    return (
        decision,
        decision_effective,
        decision_ref,
        decision_status,
        composition,
        bull,
        bear,
        dp_effective,
        dp_ref,
        execution,
        exec_effective,
        exec_mode,
        exec_ref,
        economic,
        econ_effective,
        econ_ref,
        diagnostics,
        diag_effective,
        diag_ref,
        notes,
    )


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

    market_source: Mapping[str, Any] | None = None
    chart_bars: tuple[Mapping[str, Any], ...] = ()
    if ohlcv is not None and instrument_id and venue:
        market_source = ohlcv
        chart_bars = _extract_chart_bars(ohlcv, instrument_id=instrument_id)
        notes.append("market_bound")
    else:
        notes.append("market_unbound")

    decision: Mapping[str, Any] | None = None
    decision_effective: datetime | None = None
    decision_ref: str | None = None
    decision_status: str | None = None
    composition: Mapping[str, Any] | None = None
    bull: Mapping[str, Any] | None = None
    bear: Mapping[str, Any] | None = None
    dp_effective: datetime | None = None
    dp_ref: str | None = None
    execution: Mapping[str, Any] | None = None
    exec_effective: datetime | None = None
    exec_mode = "OFFLINE"
    exec_ref: str | None = None
    economic: Mapping[str, Any] | None = None
    econ_effective: datetime | None = None
    econ_ref: str | None = None
    diagnostics: Mapping[str, Any] | None = None
    diag_effective: datetime | None = None
    diag_ref: str | None = None

    evidence_root = _review_evidence_root_or_none()
    if evidence_root is None:
        raw = (os.environ.get(ENV_REVIEW_EVIDENCE_ROOT) or "").strip()
        if raw:
            notes.append(f"{ENV_REVIEW_EVIDENCE_ROOT} unreadable:{raw}")
        else:
            notes.append(f"{ENV_REVIEW_EVIDENCE_ROOT} unset")
    else:
        (
            decision,
            decision_effective,
            decision_ref,
            decision_status,
            composition,
            bull,
            bear,
            dp_effective,
            dp_ref,
            execution,
            exec_effective,
            exec_mode,
            exec_ref,
            economic,
            econ_effective,
            econ_ref,
            diagnostics,
            diag_effective,
            diag_ref,
            evidence_notes,
        ) = _load_review_evidence_bundle(evidence_root)
        notes.extend(evidence_notes)

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
        canonical_decision_source=decision,
        decision_effective_at=decision_effective,
        decision_evidence_reference=decision_ref,
        decision_evidence_status=decision_status,
        double_play_composition=composition,
        double_play_bull_assessment=bull,
        double_play_bear_assessment=bear,
        double_play_effective_at=dp_effective,
        double_play_evidence_reference=dp_ref,
        safety_authority_source=None,
        execution_source=execution,
        execution_effective_at=exec_effective,
        execution_operating_mode=exec_mode,
        execution_evidence_reference=exec_ref,
        economic_source=economic,
        economic_effective_at=econ_effective,
        economic_evidence_reference=econ_ref,
        diagnostics_source=diagnostics,
        diagnostics_effective_at=diag_effective,
        diagnostics_bundle_reference=diag_ref,
        loader_notes=tuple(notes),
    )


__all__ = [
    "DEFAULT_RANKING_STAGE",
    "DEFAULT_REVIEW_VENUE",
    "ENV_REVIEW_EVIDENCE_ROOT",
    "ENV_VENUE",
    "LoadedMarketDashboardSourcesV1",
    "load_market_dashboard_readonly_sources_v1",
]
