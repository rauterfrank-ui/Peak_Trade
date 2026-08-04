"""Presenter for Market Dashboard Landscape V2 — display formatting only.

No decision, risk, sizing, scope, Double Play, or Safety authority logic.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from .availability import Availability
from .contracts import _ProjectionBase
from .page_aggregate import MarketDashboardPageSnapshotV1
from .serialization import serialize_projection
from .source_health import DashboardSourceHealthSnapshotV1

# Presentation-only poll contract; server owns refresh cadence/materialization.
OHLCV_POLL_PATH = "/api/market/landscape/ohlcv"
OHLCV_BROWSER_PAYLOAD_SCHEMA = "market_landscape_ohlcv_browser_payload.v1"
# Must stay equal to DEFAULT_DASHBOARD_OHLCV_POLL_INTERVAL_SECONDS in
# src.ops.okx_selected_instrument_ohlcv_readmodel_v1 (contract-tested).
# Landscape package must not import ops owners (architecture guard).
OHLCV_POLL_INTERVAL_SECONDS = 1


def _ohlcv_poll_interval_seconds() -> int:
    """Presentation mirror of the canonical OKX OHLCV poll cadence."""
    return int(OHLCV_POLL_INTERVAL_SECONDS)


AVAILABILITY_LABELS: Mapping[Availability, str] = {
    Availability.AVAILABLE: "AVAILABLE",
    Availability.NOT_BOUND: "NOT_BOUND",
    Availability.MISSING_SOURCE: "MISSING_SOURCE",
    Availability.STALE: "STALE",
    Availability.INVALID: "INVALID",
}

# Phase-2 vocabulary; SCHEMA_MISMATCH / INVALID_PROVENANCE surface as
# INVALID availability with an explicit reason code when producers bind later.
MISSING_STATE_REASON_HINTS = (
    "SCHEMA_MISMATCH",
    "INVALID_PROVENANCE",
)

# Presentation labels only — no authority / ownership semantics.
_SOURCE_SLOT_LABELS: Mapping[str, str] = {
    "market_instrument": "Market",
    "universe_ranking": "Universe",
    "dynamic_scope": "Scope",
    "regime_bull_bear_switch": "Regime/Bull-Bear/Switch",
    "canonical_decision": "Decision",
    "double_play": "Double Play",
    "risk_sizing_capital": "Risk",
    "safety_authority": "Safety",
    "execution_reconciliation": "Execution",
    "economic_summary": "Economic",
    "autonomy_stage": "Autonomy",
    "diagnostics_summary": "Diagnostics",
}

_FRESHNESS_UNAVAILABLE = "FRESHNESS_UNAVAILABLE"

_NOT_BOUND_VIEW: dict[str, Any] = {
    "availability": Availability.NOT_BOUND.value,
    "availability_label": AVAILABILITY_LABELS[Availability.NOT_BOUND],
}


def _display_value(raw: Any, availability: Availability) -> str:
    if availability is not Availability.AVAILABLE or raw is None:
        return AVAILABILITY_LABELS[availability]
    return str(raw)


def _identity_fact_display(raw: Any, availability: Availability) -> str:
    """Retain selected-instrument / venue identity for AVAILABLE and STALE."""
    if availability in (Availability.AVAILABLE, Availability.STALE) and raw is not None:
        return str(raw)
    return AVAILABILITY_LABELS[availability]


def _venue_display(raw: Any, availability: Availability) -> str:
    """Project venue label from canonical readmodel value; never invent a venue."""
    if availability not in (Availability.AVAILABLE, Availability.STALE) or raw is None:
        return AVAILABILITY_LABELS[availability]
    text = str(raw).strip()
    if not text:
        return AVAILABILITY_LABELS[availability]
    lowered = text.lower()
    if lowered == "okx" or lowered.startswith("okx_"):
        return "OKX"
    return text


def _finite_ohlc_float(raw: Any) -> float | None:
    """Coerce canonical decimal/string OHLC to a finite browser float; never invent."""
    if raw is None:
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if value != value or value in (float("inf"), float("-inf")):
        return None
    return value


def classify_volume_bar_direction_v1(*, open_v: float, close_v: float) -> str:
    """Candle-direction class for volume bars — not buy/sell volume semantics."""
    if close_v > open_v:
        return "up"
    if close_v < open_v:
        return "down"
    return "neutral"


def usable_volume_value_v1(raw: Any) -> float | None:
    """Accept finite non-negative volume only; never invent zeros for missing/invalid."""
    value = _finite_ohlc_float(raw)
    if value is None or value < 0:
        return None
    return value


def resolve_volume_panel_state_v1(
    *,
    browser_payload: Mapping[str, Any] | None,
    ohlcv_payload: Mapping[str, Any] | None = None,
) -> tuple[str, str]:
    """Honest volume-panel availability from existing OHLCV payload facts only."""
    source = ohlcv_payload if isinstance(ohlcv_payload, Mapping) else None
    payload = browser_payload if isinstance(browser_payload, Mapping) else None
    if payload is None and source is None:
        return (
            "MISSING_SOURCE",
            "Volume MISSING_SOURCE — no OHLCV volume field in existing payload.",
        )
    if payload is None:
        return (
            "NOT_BOUND",
            "Volume NOT_BOUND — OHLCV present but not browser-serializable for volume.",
        )
    bars = payload.get("bars")
    if not isinstance(bars, list) or not bars:
        return (
            "MISSING_SOURCE",
            "Volume MISSING_SOURCE — empty OHLCV series; no fabricated volume bars.",
        )
    usable = 0
    missing = 0
    invalid = 0
    for row in bars:
        if not isinstance(row, Mapping):
            invalid += 1
            continue
        raw = row.get("volume")
        if raw is None or raw == "":
            missing += 1
            continue
        if usable_volume_value_v1(raw) is None:
            invalid += 1
            continue
        usable += 1
    if usable == 0 and missing == len(bars):
        return (
            "MISSING_SOURCE",
            "Volume MISSING_SOURCE — volume field absent on all bars.",
        )
    if usable == 0:
        return (
            "NOT_BOUND",
            "Volume NOT_BOUND — volume present but not usable in presentation binding.",
        )
    freshness_raw = ""
    if isinstance(source, Mapping):
        freshness_raw = str(source.get("freshness_state") or "")
    if not freshness_raw:
        freshness_raw = str(payload.get("freshness_state") or "")
    is_stale = False
    if isinstance(source, Mapping):
        is_stale = bool(source.get("is_stale"))
    if not is_stale:
        is_stale = bool(payload.get("is_stale"))
    if freshness_raw.lower() == "stale" or is_stale:
        return (
            "STALE",
            "Volume STALE — canonical OHLCV freshness reports stale; bars retained.",
        )
    return (
        "AVAILABLE",
        "Volume bound to authentic OHLCV bar volume (contracts); not buy/sell delta.",
    )


def serialize_ohlcv_browser_payload_v1(
    ohlcv_readmodel: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    """Build browser-consumable OHLCV payload with finite numeric OHLC values.

    Source bars may store OHLC as decimal strings (canonical readmodel). This
    projection never fabricates candles; missing/non-finite values fail closed.

    Identity domains (local browser payload only):
    - candle_series_digest: authentic timestamp + O/H/L/C/V (+ confirm)
    - metadata_digest: captured_at / freshness / mark provenance clocks
    - live_mark_price: distinct OKX mark fact — never mutates candle close/geometry
    """
    if not isinstance(ohlcv_readmodel, Mapping):
        return None
    bars_raw = ohlcv_readmodel.get("bars")
    if not isinstance(bars_raw, list) or not bars_raw:
        return None
    live_mark = _finite_ohlc_float(ohlcv_readmodel.get("live_mark_price"))
    bars: list[dict[str, Any]] = []
    for row in bars_raw:
        if not isinstance(row, Mapping):
            return None
        ts = row.get("ts")
        if not isinstance(ts, str) or not ts.strip():
            return None
        open_v = _finite_ohlc_float(row.get("open"))
        high_v = _finite_ohlc_float(row.get("high"))
        low_v = _finite_ohlc_float(row.get("low"))
        close_v = _finite_ohlc_float(row.get("close"))
        volume_v = _finite_ohlc_float(row.get("volume"))
        if None in (open_v, high_v, low_v, close_v, volume_v):
            return None
        assert open_v is not None and high_v is not None
        assert low_v is not None and close_v is not None and volume_v is not None
        confirm_raw = row.get("confirm")
        if confirm_raw is None:
            confirm = True
        elif isinstance(confirm_raw, bool):
            confirm = confirm_raw
        else:
            confirm = str(confirm_raw) in {"1", "true", "True"}
        # Geometry uses authentic OHLCV only — mark never overwrites close/high/low.
        bars.append(
            {
                "ts": ts.strip(),
                "open": open_v,
                "high": high_v,
                "low": low_v,
                "close": close_v,
                "volume": volume_v,
                "display_close": close_v,
                "display_high": high_v,
                "display_low": low_v,
                "confirm": confirm,
                "provisional": not confirm,
            }
        )
    venue_raw = ohlcv_readmodel.get("venue")
    venue_display = None
    if isinstance(venue_raw, str) and venue_raw.strip():
        venue_display = _venue_display(venue_raw, Availability.AVAILABLE)
    candle_series_source = {
        "instrument_id": ohlcv_readmodel.get("instrument_id"),
        "venue": venue_display or venue_raw,
        "interval": ohlcv_readmodel.get("interval"),
        "bars": [
            {
                "ts": b["ts"],
                "open": b["open"],
                "high": b["high"],
                "low": b["low"],
                "close": b["close"],
                "volume": b["volume"],
                "confirm": b["confirm"],
            }
            for b in bars
        ],
    }
    candle_series_digest = hashlib.sha256(
        json.dumps(candle_series_source, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    metadata_source = {
        "captured_at": ohlcv_readmodel.get("captured_at"),
        "effective_at": ohlcv_readmodel.get("effective_at"),
        "candle_captured_at": ohlcv_readmodel.get("candle_captured_at")
        or ohlcv_readmodel.get("captured_at"),
        "freshness_state": ohlcv_readmodel.get("freshness_state"),
        "is_stale": bool(ohlcv_readmodel.get("is_stale")),
        "live_mark_price": live_mark,
        "live_mark_provider_ts": ohlcv_readmodel.get("live_mark_provider_ts"),
        "live_mark_captured_at": ohlcv_readmodel.get("live_mark_captured_at"),
        "gap_count": ohlcv_readmodel.get("gap_count"),
        "last_closed_timestamp": ohlcv_readmodel.get("last_closed_timestamp"),
        "ohlcv_revision_kind": ohlcv_readmodel.get("ohlcv_revision_kind"),
    }
    metadata_digest = hashlib.sha256(
        json.dumps(metadata_source, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    # Backward-compatible aliases: chart_digest == candle geometry only.
    chart_digest = candle_series_digest
    payload_digest = hashlib.sha256(
        json.dumps(
            {**candle_series_source, **metadata_source},
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return {
        "schema_name": OHLCV_BROWSER_PAYLOAD_SCHEMA,
        "schema_version": 1,
        "instrument_id": ohlcv_readmodel.get("instrument_id"),
        "venue": venue_display or venue_raw,
        "interval": ohlcv_readmodel.get("interval"),
        "bar_count": len(bars),
        "first_timestamp": bars[0]["ts"],
        "last_timestamp": bars[-1]["ts"],
        "last_closed_timestamp": ohlcv_readmodel.get("last_closed_timestamp"),
        "captured_at": ohlcv_readmodel.get("captured_at"),
        "effective_at": ohlcv_readmodel.get("effective_at"),
        "freshness_state": ohlcv_readmodel.get("freshness_state"),
        "is_stale": bool(ohlcv_readmodel.get("is_stale")),
        "gap_count": ohlcv_readmodel.get("gap_count"),
        "live_mark_price": live_mark,
        "live_mark_provider_ts": ohlcv_readmodel.get("live_mark_provider_ts"),
        "live_mark_captured_at": ohlcv_readmodel.get("live_mark_captured_at"),
        "live_price_kind": ohlcv_readmodel.get("live_price_kind") or "mark",
        "live_mark_projection": ohlcv_readmodel.get("live_mark_projection"),
        "candle_endpoint": ohlcv_readmodel.get("candle_endpoint"),
        "trades_endpoint": ohlcv_readmodel.get("trades_endpoint"),
        "open_candle_live_source": ohlcv_readmodel.get("open_candle_live_source"),
        "open_candle_bootstrap_source": ohlcv_readmodel.get("open_candle_bootstrap_source"),
        "candle_captured_at": ohlcv_readmodel.get("candle_captured_at")
        or ohlcv_readmodel.get("captured_at"),
        "trades_captured_at": ohlcv_readmodel.get("trades_captured_at"),
        "ohlcv_revision_kind": ohlcv_readmodel.get("ohlcv_revision_kind"),
        "trade_revision_kind": ohlcv_readmodel.get("trade_revision_kind"),
        "candle_revision_kind": ohlcv_readmodel.get("candle_revision_kind"),
        "raw_capture_digest": ohlcv_readmodel.get("raw_capture_digest"),
        "trades_raw_capture_digest": ohlcv_readmodel.get("trades_raw_capture_digest"),
        "candle_series_digest": candle_series_digest,
        "metadata_digest": metadata_digest,
        "chart_digest": chart_digest,
        "payload_digest": payload_digest,
        "close_source_semantics": "okx_market_candles_close_plus_public_trades",
        "volume_source_semantics": "okx_market_candles_vol_contracts_plus_trade_sz",
        "mark_source_semantics": "okx_public_mark_price_markPx_metadata_only",
        "bars": bars,
    }


def _lifecycle_fact_display(raw: Any, availability: Availability) -> str:
    """Retain producer lifecycle facts for AVAILABLE and STALE; never invent."""
    if availability in (Availability.AVAILABLE, Availability.STALE) and raw is not None:
        return str(raw)
    return AVAILABILITY_LABELS[availability]


def _slot_view(snap: _ProjectionBase) -> dict[str, Any]:
    payload = serialize_projection(snap)
    availability = snap.availability
    return {
        "availability": availability.value,
        "availability_label": AVAILABILITY_LABELS[availability],
        "is_available": availability is Availability.AVAILABLE,
        "is_stale": availability is Availability.STALE,
        "reason_codes": list(getattr(snap, "reason_codes", ()) or ()),
        "blockers": list(getattr(snap, "blockers", ()) or ()),
        "provenance": payload.get("provenance"),
        "freshness": payload.get("freshness"),
        "schema_id": snap.schema_id,
        "schema_version": snap.schema_version,
        "fields": {
            key: value
            for key, value in payload.items()
            if key
            not in {
                "schema_id",
                "schema_version",
                "availability",
                "provenance",
                "freshness",
            }
        },
    }


def _safety_strip_display(page: MarketDashboardPageSnapshotV1) -> str:
    """Format KillSwitch state + veto from exact projected fields only."""
    snap = page.safety_authority
    if snap.availability not in (Availability.AVAILABLE, Availability.STALE):
        return AVAILABILITY_LABELS[snap.availability]
    parts: list[str] = []
    if snap.kill_switch_state is not None:
        parts.append(str(snap.kill_switch_state))
    if snap.veto_active is not None:
        parts.append(f"veto={snap.veto_active}")
    if not parts:
        return AVAILABILITY_LABELS[snap.availability]
    return " · ".join(parts)


def _economic_status_display(page: MarketDashboardPageSnapshotV1) -> str:
    """Format economic viability status from exact projected fields only."""
    snap = page.economic_summary
    if snap.availability not in (Availability.AVAILABLE, Availability.STALE):
        return AVAILABILITY_LABELS[snap.availability]
    if snap.economic_viability_status is not None:
        return str(snap.economic_viability_status)
    return AVAILABILITY_LABELS[snap.availability]


def _metric_field_display(
    metric: Mapping[str, Any] | None,
    *,
    availability: Availability,
) -> str:
    """Present an already-projected MetricFieldV1 mapping exactly (no recomputation)."""
    if availability not in (Availability.AVAILABLE, Availability.STALE):
        return AVAILABILITY_LABELS[availability]
    if metric is None:
        return "—"
    if not isinstance(metric, Mapping):
        return "—"
    if metric.get("value") is not None:
        return str(metric["value"])
    semantic = metric.get("semantic")
    reason = metric.get("reason_code")
    if semantic is not None and reason is not None:
        return f"{semantic}:{reason}"
    if semantic is not None:
        return str(semantic)
    if reason is not None:
        return str(reason)
    return "—"


def _scalar_field_display(
    value: Any,
    *,
    availability: Availability,
) -> str:
    """Present an already-projected scalar exactly; absent stays em-dash."""
    if availability not in (Availability.AVAILABLE, Availability.STALE):
        return AVAILABILITY_LABELS[availability]
    if value is None:
        return "—"
    return str(value)


def _economic_ops_display(page: MarketDashboardPageSnapshotV1) -> dict[str, str]:
    """Format Economic evidence-only ops-band facts from projected fields only.

    Never recomputes metrics, never maps promotion_economic_gate_v1, never invents
    Development/Holdout/Sealed lifecycle labels.
    """
    snap = page.economic_summary
    availability = snap.availability
    status_display = _economic_status_display(page)
    # Unavailable projections: one canonical status on summary/status; detail
    # fields stay em-dash (no repeated MISSING_SOURCE badges). Reasons preserved.
    if availability not in (Availability.AVAILABLE, Availability.STALE) or (
        snap.economic_viability_status is None
    ):
        label = AVAILABILITY_LABELS[availability]
        reasons = ", ".join(str(code) for code in snap.reason_codes) if snap.reason_codes else "—"
        return {
            "summary_display": status_display if status_display else label,
            "status_display": status_display if status_display else label,
            "validity_display": "—",
            "policy_threshold_display": "—",
            "profit_factor_display": "—",
            "net_return_display": "—",
            "max_drawdown_display": "—",
            "funding_drag_display": "—",
            "trade_count_display": "—",
            "evidence_ref_display": "—",
            "evidence_digest_display": "—",
            "reasons_display": reasons,
            "classification_display": "EVIDENCE_ONLY",
        }

    validity = (
        str(snap.economic_validity_proven) if snap.economic_validity_proven is not None else "—"
    )
    policy_threshold = _scalar_field_display(
        snap.policy_threshold_status, availability=availability
    )
    evidence_ref = _scalar_field_display(snap.evidence_ref, availability=availability)
    evidence_digest = "—"
    if snap.provenance is not None and snap.provenance.evidence_digest is not None:
        evidence_digest = str(snap.provenance.evidence_digest)
    elif snap.manifest_digest is not None:
        evidence_digest = str(snap.manifest_digest)
    reasons = ", ".join(str(code) for code in snap.reason_codes) if snap.reason_codes else "—"
    return {
        "summary_display": status_display,
        "status_display": status_display,
        "validity_display": validity,
        "policy_threshold_display": policy_threshold,
        "profit_factor_display": _metric_field_display(
            snap.profit_factor, availability=availability
        ),
        "net_return_display": _metric_field_display(snap.net_return, availability=availability),
        "max_drawdown_display": _metric_field_display(snap.max_drawdown, availability=availability),
        "funding_drag_display": _metric_field_display(snap.funding_drag, availability=availability),
        "trade_count_display": _metric_field_display(snap.trade_count, availability=availability),
        "evidence_ref_display": evidence_ref,
        "evidence_digest_display": evidence_digest,
        "reasons_display": reasons,
        "classification_display": "EVIDENCE_ONLY",
    }


def _diagnostics_ops_display(page: MarketDashboardPageSnapshotV1) -> dict[str, str]:
    """Present diagnostics as ratified NOT_BOUND / NON_AUTHORITATIVE / UNRESOLVED.

    Does not infer health from logs, tests, source-health, or economic evidence.
    """
    snap = page.diagnostics_summary
    availability = snap.availability
    availability_label = AVAILABILITY_LABELS[availability]
    # OPTION_A closeout: slot remains unbound; never promote availability to healthy.
    status = (
        Availability.NOT_BOUND.value
        if availability is Availability.NOT_BOUND
        else availability_label
    )
    return {
        "summary_display": status,
        "status_display": status,
        "authority_display": "NON_AUTHORITATIVE",
        "owner_display": "UNRESOLVED",
        "availability": availability.value,
        "availability_label": availability_label,
        "classification_display": "NON_AUTHORITATIVE",
    }


def _governance_ops_display(page: MarketDashboardPageSnapshotV1) -> dict[str, str]:
    """Present governance/autonomy locks without binding or evaluating gates.

    autonomy_stage / promotion / activation remain NOT_BOUND (OPTION_D).
    Runtime bridge is the separate shell constant BOUND_NOT_ACTIVATED.
    OPERATOR_GO_REQUIRED comes from existing product/shell live-lock metadata.
    """
    autonomy = page.autonomy_stage
    autonomy_availability = autonomy.availability
    autonomy_stage_display = (
        Availability.NOT_BOUND.value
        if autonomy_availability is Availability.NOT_BOUND
        else AVAILABILITY_LABELS[autonomy_availability]
    )
    # Never treat shell runtime bridge as autonomy-stage source or ACTIVE runtime.
    runtime_bridge = str(page.runtime_bridge_display)
    operator_go_required = True  # LIVE_AUTHORIZED=false shell metadata
    return {
        "summary_display": f"{autonomy_stage_display} · {runtime_bridge}",
        "autonomy_stage_display": autonomy_stage_display,
        "promotion_eligibility_display": Availability.NOT_BOUND.value,
        "activation_eligibility_display": Availability.NOT_BOUND.value,
        "runtime_bridge_display": runtime_bridge,
        "runtime_bridge_class": str(page.shell_authority_class),
        "operator_go_required_display": "true" if operator_go_required else "false",
        "operator_go_required": operator_go_required,
        "lock_classification_display": "INTENTIONAL_LOCK",
        "availability": autonomy_availability.value,
        "availability_label": AVAILABILITY_LABELS[autonomy_availability],
    }


def _risk_ops_display(page: MarketDashboardPageSnapshotV1) -> dict[str, str]:
    """Format Risk/Sizing/Capital operative-band facts from projected fields only."""
    snap = page.risk_sizing_capital
    if snap.availability not in (Availability.AVAILABLE, Availability.STALE):
        label = AVAILABILITY_LABELS[snap.availability]
        # Capability 7 / TASK_1: one status on summary; detail cells stay em-dash.
        return {
            "summary_display": label,
            "risk_status_display": "—",
            "sizing_status_display": "—",
            "capital_status_display": "—",
            "quantity_display": "—",
            "reasons_display": (
                ", ".join(str(code) for code in snap.reason_codes) if snap.reason_codes else "—"
            ),
        }
    quantity_display = "—"
    if snap.availability is Availability.AVAILABLE and snap.quantity is not None:
        quantity_display = str(snap.quantity)
    reasons = ", ".join(str(code) for code in snap.reason_codes) if snap.reason_codes else "—"
    risk_status = (
        str(snap.risk_status)
        if snap.risk_status is not None
        else AVAILABILITY_LABELS[snap.availability]
    )
    sizing_status = (
        str(snap.sizing_status)
        if snap.sizing_status is not None
        else AVAILABILITY_LABELS[snap.availability]
    )
    capital_status = (
        str(snap.capital_status)
        if snap.capital_status is not None
        else AVAILABILITY_LABELS[snap.availability]
    )
    return {
        "summary_display": f"{risk_status} · {sizing_status} · {capital_status}",
        "risk_status_display": risk_status,
        "sizing_status_display": sizing_status,
        "capital_status_display": capital_status,
        "quantity_display": quantity_display,
        "reasons_display": reasons,
    }


def _execution_ops_display(page: MarketDashboardPageSnapshotV1) -> dict[str, str]:
    """Format Execution/Reconciliation operative-band facts from projected fields only."""
    snap = page.execution_reconciliation
    if snap.availability not in (Availability.AVAILABLE, Availability.STALE):
        label = AVAILABILITY_LABELS[snap.availability]
        # Capability 7 / TASK_1: one status on summary; detail cells stay em-dash.
        return {
            "summary_display": label,
            "execution_status_display": "—",
            "reconciliation_status_display": "—",
            "order_intent_ref_display": "—",
            "reasons_display": (
                ", ".join(str(code) for code in snap.reason_codes) if snap.reason_codes else "—"
            ),
        }
    execution_status = (
        str(snap.execution_status)
        if snap.execution_status is not None
        else AVAILABILITY_LABELS[snap.availability]
    )
    reconciliation_status = (
        str(snap.reconciliation_status) if snap.reconciliation_status is not None else "—"
    )
    order_intent_ref = str(snap.order_intent_ref) if snap.order_intent_ref is not None else "—"
    reasons = ", ".join(str(code) for code in snap.reason_codes) if snap.reason_codes else "—"
    summary_parts = [execution_status]
    if snap.reconciliation_status is not None:
        summary_parts.append(str(snap.reconciliation_status))
    return {
        "summary_display": " · ".join(summary_parts),
        "execution_status_display": execution_status,
        "reconciliation_status_display": reconciliation_status,
        "order_intent_ref_display": order_intent_ref,
        "reasons_display": reasons,
    }


def _format_freshness_display(freshness: Mapping[str, Any] | None) -> str:
    """Format canonical freshness for display; never invent timestamps or health."""
    if not isinstance(freshness, Mapping):
        return _FRESHNESS_UNAVAILABLE
    observed = freshness.get("observed_at")
    if observed is None or not str(observed).strip():
        return _FRESHNESS_UNAVAILABLE
    return str(observed)


def _source_line_display(*, availability: str, freshness_display: str) -> str:
    return f"{availability} · {freshness_display}"


def _present_source_health_compact(
    *,
    health: DashboardSourceHealthSnapshotV1,
    slot_views: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Compact Context-rail projection from existing Source Health + slot freshness."""
    freshness = health.freshness.to_json_dict()
    freshness_display = _format_freshness_display(freshness)
    availability = health.availability.value
    sources: list[dict[str, Any]] = []
    for slot, state in sorted(health.slot_availability.items()):
        view = slot_views.get(slot) or {}
        slot_availability = str(view.get("availability") or state.value)
        slot_freshness_display = _format_freshness_display(
            view.get("freshness") if isinstance(view.get("freshness"), Mapping) else None
        )
        sources.append(
            {
                "slot": slot,
                "label": _SOURCE_SLOT_LABELS.get(slot, slot),
                "availability": slot_availability,
                "freshness_display": slot_freshness_display,
                "line_display": _source_line_display(
                    availability=slot_availability,
                    freshness_display=slot_freshness_display,
                ),
                "is_stale": bool(
                    isinstance(view.get("freshness"), Mapping)
                    and view.get("freshness", {}).get("is_stale") is True
                ),
            }
        )
    return {
        "availability": availability,
        "availability_label": AVAILABILITY_LABELS[health.availability],
        "slot_availability": {
            slot: state.value for slot, state in sorted(health.slot_availability.items())
        },
        "incomplete_slots": list(health.incomplete_slots),
        "provenance": health.provenance.to_json_dict(),
        "freshness": freshness,
        "freshness_display": freshness_display,
        "summary_display": _source_line_display(
            availability=availability,
            freshness_display=freshness_display,
        ),
        "sources": sources,
    }


def _open_candle_projection_is_valid(
    browser_payload: Mapping[str, Any] | None,
    ohlcv_payload: Mapping[str, Any] | None,
) -> bool:
    """Open tip must be authentic, provisional (confirm=false), and source-bound."""
    source = ohlcv_payload or {}
    live_source = source.get("open_candle_live_source")
    if not isinstance(live_source, str) or not live_source.strip():
        return False
    if source.get("trades_endpoint") in (None, "") and source.get("candle_endpoint") in (
        None,
        "",
    ):
        return False
    bars = None
    if browser_payload is not None:
        bars = browser_payload.get("bars")
    if not isinstance(bars, list) or not bars:
        bars = source.get("bars")
    if not isinstance(bars, list) or not bars:
        return False
    tip = bars[-1]
    if not isinstance(tip, Mapping):
        return False
    confirm_raw = tip.get("confirm")
    if confirm_raw is None:
        confirm = True
    elif isinstance(confirm_raw, bool):
        confirm = confirm_raw
    else:
        confirm = str(confirm_raw) in {"1", "true", "True"}
    provisional = tip.get("provisional")
    if provisional is None:
        provisional = not confirm
    return (not confirm) and bool(provisional)


def _ohlcv_source_feed_is_live(
    *,
    browser_payload: Mapping[str, Any] | None,
    ohlcv_payload: Mapping[str, Any] | None,
    chart_availability: Availability,
) -> bool:
    """HEALTHY feed only when authentic open-candle intrabar evidence is AVAILABLE.

    Mark-price / captured_at / freshness cosmetics alone must never claim HEALTHY.
    CAPABILITY_O5: LIVE_DATA is an alias of HEALTHY (pre-O5 chrome).
    """
    if browser_payload is None or chart_availability is not Availability.AVAILABLE:
        return False
    source = ohlcv_payload or {}
    if bool(source.get("is_stale")) or str(source.get("freshness_state") or "").lower() == "stale":
        return False
    candle_cap = source.get("candle_captured_at") or source.get("captured_at")
    if not isinstance(candle_cap, str) or not candle_cap.strip():
        return False
    if source.get("candle_endpoint") in (None, "") and not source.get("bars"):
        return False
    return _open_candle_projection_is_valid(browser_payload, ohlcv_payload)


def _ohlcv_data_connection_state(
    *,
    browser_payload: Mapping[str, Any] | None,
    ohlcv_payload: Mapping[str, Any] | None,
    chart_availability: Availability,
    disconnected: bool = False,
    projection_time_unix: float | None = None,
    adapted_connection_state: str | None = None,
) -> str:
    """O5 connection vocabulary: HEALTHY/DEGRADED/STALE/DISCONNECTED/MISSING_SOURCE.

    Stale or disconnected cached data must never classify as HEALTHY.

    Age/freshness chrome is owned by the O5 ops adapter at the shell boundary.
    Landscape presentation accepts an optional adapted_connection_state and must
    not import ops owners (architecture guard: stdlib + relative only).
    """
    # Retained for call-site compatibility; age chrome arrives via adapted_connection_state.
    _ = projection_time_unix

    if chart_availability is Availability.MISSING_SOURCE:
        return "MISSING_SOURCE"
    if chart_availability in (Availability.INVALID, Availability.NOT_BOUND):
        return "MISSING_SOURCE"
    if disconnected:
        return "DISCONNECTED"
    if chart_availability is Availability.STALE:
        return "STALE"
    source = ohlcv_payload or {}
    if bool(source.get("is_stale")) or str(source.get("freshness_state") or "").lower() == "stale":
        return "STALE"

    if _ohlcv_source_feed_is_live(
        browser_payload=browser_payload,
        ohlcv_payload=ohlcv_payload,
        chart_availability=chart_availability,
    ):
        # Authentic open-candle evidence → HEALTHY (explicit stale/disconnected already excluded).
        return "HEALTHY"

    # Prefer O5-adapted chrome injected by the shell / producer boundary.
    if adapted_connection_state is not None:
        state = str(adapted_connection_state or "DEGRADED")
        # Source present without authentic live evidence must never invent HEALTHY.
        if state == "HEALTHY":
            return "DEGRADED"
        return state

    # Presentation without boundary injection: fail-closed, never invent HEALTHY.
    if ohlcv_payload is None:
        return "MISSING_SOURCE"
    return "DEGRADED"


def _regime_context_views(snap: Any) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Split RegimeBullBearSwitchSnapshot into three System Context views.

    Formatting only — never invents bullish/bearish/unchanged defaults.
    """
    availability = snap.availability
    label = AVAILABILITY_LABELS[availability]
    payload = serialize_projection(snap)
    base = {
        "availability": availability.value,
        "availability_label": label,
        "is_available": availability is Availability.AVAILABLE,
        "is_stale": availability is Availability.STALE,
        "reason_codes": list(getattr(snap, "reason_codes", ()) or ()),
        "provenance": payload.get("provenance"),
        "freshness": payload.get("freshness"),
        "schema_id": snap.schema_id,
        "schema_version": snap.schema_version,
    }
    if availability not in (Availability.AVAILABLE, Availability.STALE):
        empty = {**base, "value_display": label, "fields": {}}
        return empty, dict(empty), dict(empty)

    regime_display = str(snap.regime_id)
    if snap.regime_status is not None:
        regime_display = f"{snap.regime_id} ({snap.regime_status})"
    bull_bear_display = str(snap.side_state)
    switch_display = (
        f"{snap.previous_side_state}→{snap.next_side_state} "
        f"allowed={snap.transition_allowed} ({snap.transition_reason_code})"
    )
    regime = {
        **base,
        "value_display": regime_display,
        "fields": {
            "regime_id": snap.regime_id,
            "regime_status": snap.regime_status,
        },
    }
    bull_bear = {
        **base,
        "value_display": bull_bear_display,
        "fields": {"side_state": snap.side_state},
    }
    switch = {
        **base,
        "value_display": switch_display,
        "fields": {
            "previous_side_state": snap.previous_side_state,
            "next_side_state": snap.next_side_state,
            "scope_event_type": snap.scope_event_type,
            "transition_allowed": snap.transition_allowed,
            "transition_reason_code": snap.transition_reason_code,
        },
    }
    return regime, bull_bear, switch


def present_market_landscape_v2(
    page: MarketDashboardPageSnapshotV1,
    *,
    ohlcv_readmodel: Mapping[str, Any] | None = None,
    adapted_ohlcv_connection_state: str | None = None,
) -> dict[str, Any]:
    """Format page snapshot for SSR template context (presentation only).

    adapted_ohlcv_connection_state: optional O5 connection chrome from the shell
    boundary (ops adapter). Landscape must not import the ops owner itself.
    """
    market = _slot_view(page.market_instrument)
    universe = _slot_view(page.universe_ranking)
    scope = _slot_view(page.dynamic_scope)
    regime_view, bull_bear_view, switch_view = _regime_context_views(page.regime_bull_bear_switch)
    regime_bbs = _slot_view(page.regime_bull_bear_switch)
    decision = _slot_view(page.canonical_decision)
    double_play = _slot_view(page.double_play)
    risk = _slot_view(page.risk_sizing_capital)
    safety = _slot_view(page.safety_authority)
    execution = _slot_view(page.execution_reconciliation)
    economic = _slot_view(page.economic_summary)
    autonomy = _slot_view(page.autonomy_stage)
    diagnostics = _slot_view(page.diagnostics_summary)
    health = page.source_health

    chart_availability = page.market_instrument.availability
    ohlcv_bound = False
    ohlcv_payload: dict[str, Any] | None = None
    browser_payload = serialize_ohlcv_browser_payload_v1(ohlcv_readmodel)
    if isinstance(ohlcv_readmodel, Mapping) and ohlcv_readmodel.get("bar_count"):
        ohlcv_payload = dict(ohlcv_readmodel)
        freshness = str(ohlcv_readmodel.get("freshness_state") or "")
        if freshness == "stale":
            chart_availability = Availability.STALE
        elif chart_availability not in (Availability.AVAILABLE, Availability.STALE):
            chart_availability = Availability.AVAILABLE
        if browser_payload is None:
            ohlcv_bound = False
            chart_message = (
                "Primary chart OHLCV readmodel present but not browser-serializable "
                "(non-finite or invalid OHLC); no fabricated candles."
            )
        else:
            ohlcv_bound = True
            chart_message = (
                "Primary chart bound to materialized OKX OHLCV readmodel "
                f"(bars={browser_payload.get('bar_count')}, interval="
                f"{ohlcv_readmodel.get('interval')})."
            )
    elif chart_availability in (Availability.AVAILABLE, Availability.STALE):
        chart_message = (
            "Primary chart market instrument bound; OHLCV producer still unbound "
            "(no fabricated candles)."
        )
    elif chart_availability is Availability.MISSING_SOURCE:
        chart_message = (
            "Primary chart MISSING_SOURCE — market identity / OHLCV not persisted "
            "for dashboard; no OHLCV fabricated."
        )
    elif chart_availability is Availability.INVALID:
        chart_message = (
            "Primary chart INVALID — market producer output rejected; no OHLCV fabricated."
        )
    else:
        chart_message = "Primary chart NOT_BOUND — no OHLCV fabricated for Landscape shell."

    volume_panel_state, volume_panel_message = resolve_volume_panel_state_v1(
        browser_payload=browser_payload,
        ohlcv_payload=ohlcv_payload,
    )

    ranking_rows: list[dict[str, Any]] = []
    universe_rows: list[dict[str, Any]] = []
    selected_instrument_id = None
    membership_label = AVAILABILITY_LABELS[page.universe_ranking.availability]
    ranking_label = AVAILABILITY_LABELS[page.universe_ranking.availability]
    if page.universe_ranking.availability in (Availability.AVAILABLE, Availability.STALE):
        ranking_rows = [dict(row) for row in page.universe_ranking.ranking]
        universe_rows = [dict(row) for row in page.universe_ranking.universe]
        selected_instrument_id = page.universe_ranking.selected_instrument_id
        if not ranking_rows:
            ranking_label = "NOT_AVAILABLE"
        if selected_instrument_id and universe_rows:
            membership = {str(row.get("symbol")) for row in universe_rows}
            membership_label = (
                "IN_UNIVERSE" if selected_instrument_id in membership else "NOT_IN_UNIVERSE"
            )
        elif selected_instrument_id is None:
            membership_label = "NOT_AVAILABLE"
        elif not universe_rows:
            membership_label = "NOT_AVAILABLE"

    instrument_display = (
        selected_instrument_id
        if selected_instrument_id
        else _identity_fact_display(
            page.market_instrument.instrument_id, page.market_instrument.availability
        )
    )

    scope_lifecycle_display = _lifecycle_fact_display(
        page.dynamic_scope.scope_state, page.dynamic_scope.availability
    )
    current_scope_ref_display = _lifecycle_fact_display(
        page.dynamic_scope.current_scope_ref, page.dynamic_scope.availability
    )
    if page.dynamic_scope.availability in (Availability.AVAILABLE, Availability.STALE):
        if page.dynamic_scope.next_scope_ref is None:
            next_scope_ref_display = "—"
        else:
            next_scope_ref_display = str(page.dynamic_scope.next_scope_ref)
    else:
        next_scope_ref_display = AVAILABILITY_LABELS[page.dynamic_scope.availability]

    economic_status_display = _economic_status_display(page)
    economic_ops = _economic_ops_display(page)
    diagnostics_ops = _diagnostics_ops_display(page)
    governance_ops = _governance_ops_display(page)
    risk_ops = _risk_ops_display(page)
    execution_ops = _execution_ops_display(page)

    return {
        "page_schema_id": page.schema_id,
        "generated_at": page.generated_at.isoformat().replace("+00:00", "Z"),
        "git_sha": page.git_sha,
        "runtime_bridge_display": page.runtime_bridge_display,
        "shell_authority_class": page.shell_authority_class,
        "consumer_role": "read_only_consumer",
        "phase": "PHASE_5_CAPABILITY_7_PRODUCT_MATURITY_TECHNICAL",
        "global_strip": {
            # Compact ops summary only. Scope lifecycle + Regime primary in Context rail.
            # Do not expose availability under a Freshness label (Phase 5 PR1).
            "instrument": instrument_display,
            "venue": _venue_display(
                page.market_instrument.venue, page.market_instrument.availability
            ),
            "runtime_state": page.runtime_bridge_display,
            "runtime_state_class": page.shell_authority_class,
            "safety_status": _safety_strip_display(page),
        },
        "market": market,
        "universe": universe,
        "universe_ranking_rows": ranking_rows,
        "universe_membership_rows": universe_rows,
        "selected_instrument_id": selected_instrument_id,
        "universe_rail": {
            "watchlist_availability": page.universe_ranking.availability.value,
            "watchlist_label": AVAILABILITY_LABELS[page.universe_ranking.availability],
            # Membership of selected in projected universe rows — not a separate
            # eligibility producer / ranking recomputation.
            "membership_label": membership_label,
            "eligibility_label": membership_label,
            "rank_label": ranking_label,
            "selected_instrument_id": selected_instrument_id,
        },
        "scope": {
            **scope,
            "lifecycle_display": scope_lifecycle_display,
            "current_scope_ref_display": current_scope_ref_display,
            "next_scope_ref_display": next_scope_ref_display,
        },
        "regime": regime_view,
        "bull_bear": bull_bear_view,
        "switch": switch_view,
        "decision": decision,
        "double_play": double_play,
        "risk": {
            **risk,
            **risk_ops,
        },
        "safety": safety,
        "execution": {
            **execution,
            **execution_ops,
        },
        "economic": {
            **economic,
            **economic_ops,
            "status_display": economic_status_display,
        },
        "autonomy": {
            **autonomy,
            **governance_ops,
        },
        "diagnostics": {
            **diagnostics,
            **diagnostics_ops,
        },
        "governance": governance_ops,
        "source_health": _present_source_health_compact(
            health=health,
            slot_views={
                "market_instrument": market,
                "universe_ranking": universe,
                "dynamic_scope": scope,
                "regime_bull_bear_switch": regime_bbs,
                "canonical_decision": decision,
                "double_play": double_play,
                "risk_sizing_capital": risk,
                "safety_authority": safety,
                "execution_reconciliation": execution,
                "economic_summary": economic,
                "autonomy_stage": autonomy,
                "diagnostics_summary": diagnostics,
            },
        ),
        "chart": {
            "availability": chart_availability.value,
            "availability_label": AVAILABILITY_LABELS[chart_availability],
            "bound": bool(browser_payload)
            or ohlcv_bound
            or chart_availability in (Availability.AVAILABLE, Availability.STALE),
            "message": chart_message,
            "ohlcv": ohlcv_payload,
            "browser_payload": browser_payload,
            "has_browser_series": browser_payload is not None,
            "interval": (browser_payload or ohlcv_payload or {}).get("interval"),
            "bar_count": (browser_payload or ohlcv_payload or {}).get("bar_count"),
            "gap_count": (ohlcv_payload or {}).get("gap_count"),
            "freshness_state": (ohlcv_payload or {}).get("freshness_state"),
            "last_closed_timestamp": (ohlcv_payload or {}).get("last_closed_timestamp"),
            "first_timestamp": (browser_payload or {}).get("first_timestamp"),
            "last_timestamp": (browser_payload or {}).get("last_timestamp"),
            "captured_at": (browser_payload or ohlcv_payload or {}).get("candle_captured_at")
            or (browser_payload or ohlcv_payload or {}).get("captured_at"),
            "effective_at": (browser_payload or ohlcv_payload or {}).get("effective_at"),
            "payload_digest": (browser_payload or {}).get("payload_digest"),
            "chart_digest": (browser_payload or {}).get("chart_digest"),
            "candle_series_digest": (browser_payload or {}).get("candle_series_digest"),
            "metadata_digest": (browser_payload or {}).get("metadata_digest"),
            "live_mark_price": (browser_payload or {}).get("live_mark_price"),
            "live_price_kind": (browser_payload or {}).get("live_price_kind"),
            "ohlcv_revision_kind": (browser_payload or ohlcv_payload or {}).get(
                "ohlcv_revision_kind"
            ),
            "open_price": None
            if not browser_payload or not browser_payload.get("bars")
            else browser_payload["bars"][-1].get("open"),
            "high_price": None
            if not browser_payload or not browser_payload.get("bars")
            else browser_payload["bars"][-1].get("high"),
            "low_price": None
            if not browser_payload or not browser_payload.get("bars")
            else browser_payload["bars"][-1].get("low"),
            "close_price": None
            if not browser_payload or not browser_payload.get("bars")
            else browser_payload["bars"][-1].get("close"),
            "volume": None
            if not browser_payload or not browser_payload.get("bars")
            else browser_payload["bars"][-1].get("volume"),
            "volume_panel_state": volume_panel_state,
            "volume_panel_message": volume_panel_message,
            "is_stale": bool((ohlcv_payload or {}).get("is_stale")),
            "poll_path": OHLCV_POLL_PATH,
            "poll_interval_seconds": _ohlcv_poll_interval_seconds(),
            "data_connection_state": _ohlcv_data_connection_state(
                browser_payload=browser_payload,
                ohlcv_payload=ohlcv_payload,
                chart_availability=chart_availability,
                adapted_connection_state=adapted_ohlcv_connection_state,
            ),
        },
        "timeline": {
            "availability": Availability.NOT_BOUND.value,
            "availability_label": AVAILABILITY_LABELS[Availability.NOT_BOUND],
            "events": [],
            "message": "Event / Decision Timeline NOT_BOUND — no invented history.",
        },
        "engineering": {
            "label": "Engineering drawer — diagnostic / non-authoritative",
            "missing_state_hints": list(MISSING_STATE_REASON_HINTS),
            "phase_4_1_bound_slots": [
                "market_instrument",
                "universe_ranking",
            ],
            "phase_4_2_bound_slots": [
                "dynamic_scope",
            ],
            "phase_4_2b_bound_slots": [
                "regime_bull_bear_switch",
            ],
            "phase_4_3a_bound_slots": [
                "canonical_decision",
            ],
            "phase_4_3b_bound_slots": [
                "double_play",
            ],
            "phase_4_4a_bound_slots": [
                "safety_authority",
            ],
            "phase_4_4b_bound_slots": [
                "risk_sizing_capital",
            ],
            "phase_4_5_bound_slots": [
                "execution_reconciliation",
            ],
            "phase_4_6b_bound_slots": [
                "economic_summary",
            ],
            "slots": {
                "market_instrument": market,
                "universe_ranking": universe,
                "dynamic_scope": scope,
                "regime_bull_bear_switch": regime_bbs,
                "canonical_decision": decision,
                "double_play": double_play,
                "risk_sizing_capital": {
                    **risk,
                    **risk_ops,
                },
                "safety_authority": safety,
                "execution_reconciliation": {
                    **execution,
                    **execution_ops,
                },
                "economic_summary": {
                    **economic,
                    **economic_ops,
                    "status_display": economic_status_display,
                },
                "autonomy_stage": {
                    **autonomy,
                    **governance_ops,
                },
                "diagnostics_summary": {
                    **diagnostics,
                    **diagnostics_ops,
                },
            },
        },
        "product_flags": {
            "live_authorized": False,
            "orders": False,
            "shadow": False,
            "paper": False,
            "testnet": False,
            "scheduler": False,
            "write_endpoints": False,
            "dashboard_authority": False,
            "operator_go_required": True,
            "phase_4_1_binding_active": True,
            "phase_4_2_binding_active": True,
            "phase_4_2b_binding_active": True,
            "phase_4_3a_binding_active": True,
            "phase_4_3b_binding_active": True,
            "phase_4_4a_binding_active": True,
            "phase_4_4b_binding_active": True,
            "phase_4_5_binding_active": True,
            "phase_4_6b_binding_active": True,
            "capability_6_alt_a_closeout": True,
            "capability_7_product_maturity": True,
            "task1_visual_density": True,
            "phase_4_full_pass": False,
            "phase_4_authorized": True,
            "operator_skeleton_approval": "PENDING",
        },
    }
