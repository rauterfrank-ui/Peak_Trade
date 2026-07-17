"""Presentation-only Market Dashboard page context (PR-D).

Maps ``MarketDashboardPageSnapshotV1`` to a deterministic template view model.
No producer I/O, no domain imports, no decision/authority inference.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Mapping, Sequence

from src.webui.market_dashboard_readmodels_v1.aggregate import MarketDashboardPageSnapshotV1
from src.webui.market_dashboard_readmodels_v1.contracts import (
    CanonicalDecisionSummaryV1,
    DashboardFreshnessSnapshotV1,
    DiagnosticsSummarySnapshotV1,
    DoublePlayDecisionSnapshotV1,
    EconomicSummarySnapshotV1,
    ExecutionStateSnapshotV1,
    MarketInstrumentSnapshotV1,
    MarketRankingSnapshotV1,
    SafetyAuthoritySnapshotV1,
    UnavailableSnapshotV1,
)
from src.webui.market_dashboard_readmodels_v1.provenance import DashboardSnapshotProvenanceV1

PRESENTER_OWNER = (
    "src.webui.market_dashboard_product_surface_v1.presenter.build_market_dashboard_page_context_v1"
)

_AVAILABILITY_LABELS = {
    "AVAILABLE": "AVAILABLE",
    "UNAVAILABLE": "UNAVAILABLE",
    "NOT_BOUND": "NOT BOUND",
    "MISSING_SOURCE": "SOURCE MISSING",
    "STALE": "STALE",
    "MALFORMED_SOURCE": "MALFORMED SOURCE",
}

_UNSUPPORTED_SAFETY_CLAIMS = (
    "execution allowed",
    "execution safe",
    "risk passed",
    "kill switch inactive",
    "authority granted",
)


def _enum_value(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, Enum):
        return str(value.value)
    return str(value)


def _availability_label(state: str | None) -> str:
    if not state:
        return "UNAVAILABLE"
    return _AVAILABILITY_LABELS.get(state, state.replace("_", " "))


def _fmt_ts(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.isoformat(timespec="seconds") + "Z"
    return value.isoformat(timespec="seconds")


def _fmt_number(value: float | None, *, digits: int = 4) -> str | None:
    if value is None:
        return None
    return f"{value:.{digits}f}"


def _fmt_pct(value: float | None) -> str | None:
    if value is None:
        return None
    return f"{value * 100:.2f}%"


def _provenance_rows(provenance: DashboardSnapshotProvenanceV1 | None) -> list[dict[str, str]]:
    if provenance is None:
        return []
    rows: list[dict[str, str]] = []
    mapping = {
        "schema_id": provenance.schema_id,
        "producer_module": provenance.producer_module,
        "producer_version": provenance.producer_version,
        "generated_at": _fmt_ts(provenance.generated_at),
        "effective_at": _fmt_ts(provenance.effective_at),
        "source_kind": _enum_value(provenance.source_kind),
        "freshness_state": _enum_value(provenance.freshness_state),
        "source_reference": provenance.source_reference,
        "evidence_digest": provenance.evidence_digest,
    }
    for key, raw in mapping.items():
        if raw is None or raw == "":
            continue
        rows.append({"key": key, "value": str(raw)})
    return rows


def _unavailable_view(section: UnavailableSnapshotV1) -> dict[str, Any]:
    state = _enum_value(section.availability_state) or "UNAVAILABLE"
    return {
        "available": False,
        "availability_state": state,
        "availability_label": _availability_label(state),
        "reason_code": section.reason_code,
        "detail": section.detail,
        "expected_source": section.expected_source,
        "generated_at": _fmt_ts(section.generated_at),
        "source_reference": section.source_reference,
        "provenance_rows": _provenance_rows(section.provenance),
        "display_severity": "critical" if state in {"MALFORMED_SOURCE", "STALE"} else "warning",
    }


@dataclass(frozen=True)
class ChartBarViewV1:
    ts: str | None
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None


@dataclass(frozen=True)
class MarketDashboardPageContextV1:
    """Typed presentation view model for the product template."""

    page_title: str
    read_only_label: str
    product_surface_id: str
    generated_at: str | None
    header: dict[str, Any]
    market_workspace: dict[str, Any]
    decision: dict[str, Any]
    double_play: dict[str, Any]
    ranking: dict[str, Any]
    economic: dict[str, Any]
    diagnostics: dict[str, Any]
    execution: dict[str, Any]
    safety_authority: dict[str, Any]
    freshness: dict[str, Any]
    engineering: dict[str, Any]
    chart_bars: tuple[ChartBarViewV1, ...] = ()
    flags: dict[str, Any] = field(default_factory=dict)

    def to_template_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        return payload


def _build_market_workspace(
    market: MarketInstrumentSnapshotV1 | UnavailableSnapshotV1,
    *,
    chart_bars: Sequence[Mapping[str, Any]] | None,
) -> dict[str, Any]:
    if isinstance(market, UnavailableSnapshotV1):
        view = _unavailable_view(market)
        view.update(
            {
                "instrument_id": None,
                "venue": None,
                "last_price": None,
                "last_price_display": None,
                "change_abs_display": None,
                "change_pct_display": None,
                "volume_display": None,
                "ohlcv": None,
                "freshness_state": None,
                "chart_available": False,
                "chart_status": "unavailable",
                "chart_status_label": view["availability_label"],
            }
        )
        return view

    bars_view: list[dict[str, Any]] = []
    if chart_bars:
        for bar in chart_bars:
            if not isinstance(bar, Mapping):
                continue
            try:
                bars_view.append(
                    {
                        "ts": str(bar.get("ts") or bar.get("timestamp") or "") or None,
                        "open": float(bar["open"]),
                        "high": float(bar["high"]),
                        "low": float(bar["low"]),
                        "close": float(bar["close"]),
                        "volume": (
                            None if bar.get("volume") is None else float(bar["volume"])  # type: ignore[arg-type]
                        ),
                    }
                )
            except (KeyError, TypeError, ValueError):
                continue

    chart_available = len(bars_view) > 0
    freshness = _enum_value(market.freshness_state)
    chart_status = "ready" if chart_available else "unavailable"
    if freshness == "STALE":
        chart_status = "stale"

    ohlcv = None
    if market.ohlcv is not None:
        ohlcv = {
            "open": _fmt_number(market.ohlcv.open),
            "high": _fmt_number(market.ohlcv.high),
            "low": _fmt_number(market.ohlcv.low),
            "close": _fmt_number(market.ohlcv.close),
            "volume": _fmt_number(market.ohlcv.volume) if market.ohlcv.volume is not None else None,
        }

    # Display-only change from already-loaded OHLCV bars when producer omits change.
    change_abs = market.change_abs
    change_pct = market.change_pct
    if change_abs is None and change_pct is None and len(bars_view) >= 2:
        first_close = bars_view[0]["close"]
        last_close = bars_view[-1]["close"]
        if isinstance(first_close, (int, float)) and isinstance(last_close, (int, float)):
            if first_close != 0:
                change_abs = float(last_close) - float(first_close)
                change_pct = change_abs / float(first_close)

    last_volume = None
    if bars_view and bars_view[-1].get("volume") is not None:
        last_volume = bars_view[-1]["volume"]
    volume_value = market.volume if market.volume is not None else last_volume

    return {
        "available": True,
        "availability_state": "AVAILABLE",
        "availability_label": "AVAILABLE",
        "instrument_id": market.instrument_id,
        "venue": market.venue,
        "last_price": market.last_price,
        "last_price_display": _fmt_number(market.last_price),
        "mark_price_display": _fmt_number(market.mark_price),
        "change_abs_display": _fmt_number(change_abs),
        "change_pct_display": _fmt_pct(change_pct),
        "volume_display": _fmt_number(volume_value, digits=2),
        "bar_count": len(bars_view),
        "ohlcv": ohlcv,
        "freshness_state": freshness,
        "effective_at": _fmt_ts(market.effective_at),
        "market_series_reference": market.market_series_reference,
        "provenance_rows": _provenance_rows(market.provenance),
        "chart_available": chart_available,
        "chart_status": chart_status,
        "chart_status_label": (
            "STALE"
            if chart_status == "stale"
            else ("AVAILABLE" if chart_available else "UNAVAILABLE")
        ),
        "chart_bars": bars_view,
        "display_severity": "ok" if chart_available and chart_status != "stale" else "warning",
    }


def _build_decision(decision: CanonicalDecisionSummaryV1 | UnavailableSnapshotV1) -> dict[str, Any]:
    if isinstance(decision, UnavailableSnapshotV1):
        view = _unavailable_view(decision)
        view.update(
            {
                "decision_status": None,
                "direction": None,
                "evidence_status": None,
                "reason_codes": [],
                "blockers": [],
                "confidence_display": None,
            }
        )
        return view
    return {
        "available": True,
        "availability_state": "AVAILABLE",
        "availability_label": "AVAILABLE",
        "decision_status": _enum_value(decision.decision_status),
        "direction": _enum_value(decision.direction),
        "evidence_status": decision.evidence_status,
        "reason_codes": list(decision.reason_codes),
        "blockers": list(decision.blockers),
        "confidence_display": _fmt_number(decision.confidence, digits=3),
        "effective_at": _fmt_ts(decision.effective_at),
        "evidence_digest": decision.evidence_digest,
        "evidence_reference": decision.evidence_reference,
        "provenance_rows": _provenance_rows(decision.provenance),
        "display_severity": "ok",
    }


def _build_double_play(
    double_play: DoublePlayDecisionSnapshotV1 | UnavailableSnapshotV1,
) -> dict[str, Any]:
    if isinstance(double_play, UnavailableSnapshotV1):
        return _unavailable_view(double_play)
    bull = double_play.bull_assessment
    bear = double_play.bear_assessment
    return {
        "available": True,
        "availability_state": "AVAILABLE",
        "availability_label": "AVAILABLE",
        "composition_result": double_play.composition_result,
        "arbitration_status": double_play.arbitration_status,
        "blockers": list(double_play.blockers),
        "bull_status": bull.status if bull else None,
        "bear_status": bear.status if bear else None,
        "bull_score_display": _fmt_number(bull.score, digits=3) if bull else None,
        "bear_score_display": _fmt_number(bear.score, digits=3) if bear else None,
        "effective_at": _fmt_ts(double_play.effective_at),
        "provenance_rows": _provenance_rows(double_play.provenance),
        "display_severity": "ok",
    }


def _build_ranking(ranking: MarketRankingSnapshotV1 | UnavailableSnapshotV1) -> dict[str, Any]:
    if isinstance(ranking, UnavailableSnapshotV1):
        view = _unavailable_view(ranking)
        view["items"] = []
        view["selected_instrument_id"] = None
        return view
    items = [
        {
            "instrument_id": item.instrument_id,
            "rank": item.rank,
            "score_display": _fmt_number(item.score, digits=3),
            "eligibility_status": _enum_value(item.eligibility_status),
            "reason_codes": list(item.reason_codes),
            "selected": item.instrument_id == ranking.selected_instrument_id,
        }
        for item in ranking.ranked_items[:20]
    ]
    return {
        "available": True,
        "availability_state": "AVAILABLE",
        "availability_label": "AVAILABLE",
        "selected_instrument_id": ranking.selected_instrument_id,
        "items": items,
        "effective_at": _fmt_ts(ranking.effective_at),
        "provenance_rows": _provenance_rows(ranking.provenance),
        "display_severity": "ok",
    }


def _build_economic(
    economic: EconomicSummarySnapshotV1 | UnavailableSnapshotV1,
) -> dict[str, Any]:
    if isinstance(economic, UnavailableSnapshotV1):
        return _unavailable_view(economic)
    return {
        "available": True,
        "availability_state": "AVAILABLE",
        "availability_label": "AVAILABLE",
        "economic_gate_status": _enum_value(economic.economic_gate_status),
        "authoritative_gate": economic.authoritative_gate,
        "profit_factor_display": _fmt_number(economic.profit_factor),
        "expectancy_display": _fmt_number(economic.expectancy),
        "drawdown_display": _fmt_number(economic.drawdown),
        "sample_size_display": (
            None if economic.sample_size is None else str(economic.sample_size)
        ),
        "gross_return_display": _fmt_number(economic.gross_return),
        "net_return_display": _fmt_number(economic.net_return),
        "effective_at": _fmt_ts(economic.effective_at),
        "provenance_rows": _provenance_rows(economic.provenance),
        "display_severity": "ok",
    }


def _build_diagnostics(
    diagnostics: DiagnosticsSummarySnapshotV1 | UnavailableSnapshotV1,
) -> dict[str, Any]:
    if isinstance(diagnostics, UnavailableSnapshotV1):
        view = _unavailable_view(diagnostics)
        view["diagnostic_only"] = True
        view["non_authority_marker"] = "DIAGNOSTIC ONLY"
        return view
    return {
        "available": True,
        "availability_state": "AVAILABLE",
        "availability_label": "AVAILABLE",
        "diagnostic_only": True,
        "non_authority_marker": "DIAGNOSTIC ONLY",
        "non_authoritative": diagnostics.non_authoritative,
        "diagnostic_statuses": list(diagnostics.diagnostic_statuses),
        "bundle_digest": diagnostics.bundle_digest,
        "bundle_reference": diagnostics.bundle_reference,
        "effective_at": _fmt_ts(diagnostics.effective_at),
        "provenance_rows": _provenance_rows(diagnostics.provenance),
        "display_severity": "info",
    }


def _build_execution(
    execution: ExecutionStateSnapshotV1 | UnavailableSnapshotV1,
) -> dict[str, Any]:
    if isinstance(execution, UnavailableSnapshotV1):
        return _unavailable_view(execution)
    return {
        "available": True,
        "availability_state": "AVAILABLE",
        "availability_label": "AVAILABLE",
        "operating_mode": _enum_value(execution.operating_mode),
        "intent_state": execution.intent_state,
        "reconciliation_state": execution.reconciliation_state,
        "fill_state": execution.fill_state,
        "unknown_outcome_state": execution.unknown_outcome_state,
        "effective_at": _fmt_ts(execution.effective_at),
        "provenance_rows": _provenance_rows(execution.provenance),
        "display_severity": "ok",
    }


def _build_safety(
    safety: SafetyAuthoritySnapshotV1 | UnavailableSnapshotV1,
) -> dict[str, Any]:
    if isinstance(safety, UnavailableSnapshotV1):
        view = _unavailable_view(safety)
        view["safety_authority_state"] = view["availability_state"]
        view["compact_label"] = view["availability_label"]
        view["unsupported_claims_forbidden"] = True
        view["claims_blocked"] = list(_UNSUPPORTED_SAFETY_CLAIMS)
        return view
    return {
        "available": True,
        "availability_state": "AVAILABLE",
        "availability_label": "AVAILABLE",
        "safety_authority_state": "AVAILABLE",
        "compact_label": _enum_value(safety.authority_classification),
        "authority_classification": _enum_value(safety.authority_classification),
        "kill_switch_state": _enum_value(safety.kill_switch_state),
        "risk_gate_state": _enum_value(safety.risk_gate_state),
        "execution_permission_state": _enum_value(safety.execution_permission_state),
        "fail_closed_reason_codes": list(safety.fail_closed_reason_codes),
        "effective_at": _fmt_ts(safety.effective_at),
        "provenance_rows": _provenance_rows(safety.provenance),
        "unsupported_claims_forbidden": True,
        "claims_blocked": list(_UNSUPPORTED_SAFETY_CLAIMS),
        "display_severity": "ok",
    }


def _build_freshness(
    freshness: DashboardFreshnessSnapshotV1 | UnavailableSnapshotV1,
) -> dict[str, Any]:
    if isinstance(freshness, UnavailableSnapshotV1):
        return _unavailable_view(freshness)
    entries = [
        {
            "source_key": entry.source_key,
            "freshness_state": _enum_value(entry.freshness_state),
            "stale": entry.stale,
            "missing": entry.missing,
            "age_seconds_display": (
                None if entry.source_age_seconds is None else f"{entry.source_age_seconds:.0f}s"
            ),
        }
        for entry in freshness.source_entries
    ]
    states = {entry["freshness_state"] for entry in entries}
    if "STALE" in states:
        aggregate = "STALE"
    elif states and states <= {"MISSING", "UNKNOWN"}:
        aggregate = "MISSING"
    elif "FRESH" in states:
        aggregate = "FRESH"
    else:
        aggregate = "UNKNOWN"
    return {
        "available": True,
        "availability_state": "AVAILABLE",
        "availability_label": _availability_label(aggregate),
        "aggregate_freshness_state": aggregate,
        "entries": entries,
        "page_generated_at": _fmt_ts(freshness.page_generated_at),
        "provenance_rows": _provenance_rows(freshness.provenance),
        "display_severity": "warning" if aggregate == "STALE" else "ok",
    }


def _build_engineering(snapshot: MarketDashboardPageSnapshotV1) -> dict[str, Any]:
    sections = (
        ("market", snapshot.market),
        ("ranking", snapshot.ranking),
        ("decision", snapshot.decision),
        ("double_play", snapshot.double_play),
        ("safety_authority", snapshot.safety_authority),
        ("execution", snapshot.execution),
        ("economic", snapshot.economic),
        ("diagnostics", snapshot.diagnostics),
        ("freshness", snapshot.freshness),
    )
    rows: list[dict[str, str]] = [
        {"key": "page_schema_id", "value": snapshot.schema_id},
        {"key": "page_schema_version", "value": str(snapshot.schema_version)},
        {"key": "page_generated_at", "value": _fmt_ts(snapshot.generated_at) or ""},
    ]
    missing_reasons: list[dict[str, str]] = []
    for name, section in sections:
        if isinstance(section, UnavailableSnapshotV1):
            missing_reasons.append(
                {
                    "section": name,
                    "availability_state": _enum_value(section.availability_state) or "",
                    "reason_code": section.reason_code,
                    "expected_source": section.expected_source,
                }
            )
            continue
        provenance = getattr(section, "provenance", None)
        if isinstance(provenance, DashboardSnapshotProvenanceV1):
            rows.append(
                {
                    "key": f"{name}.producer_module",
                    "value": provenance.producer_module,
                }
            )
            if provenance.producer_version:
                rows.append(
                    {
                        "key": f"{name}.producer_version",
                        "value": provenance.producer_version,
                    }
                )
            if provenance.source_reference:
                rows.append(
                    {
                        "key": f"{name}.source_reference",
                        "value": provenance.source_reference,
                    }
                )
            if provenance.evidence_digest:
                rows.append(
                    {
                        "key": f"{name}.evidence_digest",
                        "value": provenance.evidence_digest,
                    }
                )
            rows.append(
                {
                    "key": f"{name}.freshness_state",
                    "value": _enum_value(provenance.freshness_state) or "",
                }
            )
    return {
        "rows": rows,
        "missing_source_reasons": missing_reasons,
        "disclosure_label": "Engineering / Provenance",
    }


def _build_header(
    *,
    market_workspace: dict[str, Any],
    freshness: dict[str, Any],
    safety: dict[str, Any],
) -> dict[str, Any]:
    instrument = market_workspace.get("instrument_id") or "SOURCE MISSING"
    venue = market_workspace.get("venue") or "SOURCE MISSING"
    return {
        "title": "Market Dashboard",
        "instrument_id": instrument,
        "venue": venue,
        "aggregate_freshness_label": freshness.get("availability_label") or "UNAVAILABLE",
        "read_only_label": "READ ONLY",
        "safety_authority_label": safety.get("compact_label") or "NOT BOUND",
        "safety_authority_state": safety.get("safety_authority_state") or "NOT_BOUND",
    }


def build_market_dashboard_page_context_v1(
    snapshot: MarketDashboardPageSnapshotV1,
    *,
    chart_bars: Sequence[Mapping[str, Any]] | None = None,
) -> MarketDashboardPageContextV1:
    """Pure presenter: snapshot (+ optional display-only chart bars) → page context."""

    if not isinstance(snapshot, MarketDashboardPageSnapshotV1):
        raise TypeError("snapshot must be MarketDashboardPageSnapshotV1")

    market_workspace = _build_market_workspace(snapshot.market, chart_bars=chart_bars)
    decision = _build_decision(snapshot.decision)
    double_play = _build_double_play(snapshot.double_play)
    ranking = _build_ranking(snapshot.ranking)
    economic = _build_economic(snapshot.economic)
    diagnostics = _build_diagnostics(snapshot.diagnostics)
    execution = _build_execution(snapshot.execution)
    safety_authority = _build_safety(snapshot.safety_authority)
    freshness = _build_freshness(snapshot.freshness)
    engineering = _build_engineering(snapshot)
    header = _build_header(
        market_workspace=market_workspace,
        freshness=freshness,
        safety=safety_authority,
    )

    chart_bar_models = tuple(
        ChartBarViewV1(
            ts=bar.get("ts"),
            open=float(bar["open"]),
            high=float(bar["high"]),
            low=float(bar["low"]),
            close=float(bar["close"]),
            volume=bar.get("volume"),
        )
        for bar in market_workspace.get("chart_bars") or []
    )

    return MarketDashboardPageContextV1(
        page_title="Market Dashboard",
        read_only_label="READ ONLY",
        product_surface_id="market_dashboard_product_surface_v1",
        generated_at=_fmt_ts(snapshot.generated_at),
        header=header,
        market_workspace=market_workspace,
        decision=decision,
        double_play=double_play,
        ranking=ranking,
        economic=economic,
        diagnostics=diagnostics,
        execution=execution,
        safety_authority=safety_authority,
        freshness=freshness,
        engineering=engineering,
        chart_bars=chart_bar_models,
        flags={
            "product_gate_pass": False,
            "technical_browser_only": True,
            "no_order_controls": True,
            "safety_authority_not_bound": (
                safety_authority.get("safety_authority_state") == "NOT_BOUND"
            ),
        },
    )


__all__ = [
    "ChartBarViewV1",
    "MarketDashboardPageContextV1",
    "PRESENTER_OWNER",
    "build_market_dashboard_page_context_v1",
]
