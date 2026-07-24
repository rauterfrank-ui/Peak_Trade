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


def _ohlcv_poll_interval_seconds() -> int:
    """Reuse canonical OKX OHLCV poll cadence; presentation never invents a second owner."""
    from src.ops.okx_selected_instrument_ohlcv_readmodel_v1 import (
        DEFAULT_DASHBOARD_OHLCV_POLL_INTERVAL_SECONDS,
    )

    return int(DEFAULT_DASHBOARD_OHLCV_POLL_INTERVAL_SECONDS)


def serialize_ohlcv_browser_payload_v1(
    ohlcv_readmodel: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    """Build browser-consumable OHLCV payload with finite numeric OHLC values.

    Source bars may store OHLC as decimal strings (canonical readmodel). This
    projection never fabricates candles; missing/non-finite values fail closed.
    """
    if not isinstance(ohlcv_readmodel, Mapping):
        return None
    bars_raw = ohlcv_readmodel.get("bars")
    if not isinstance(bars_raw, list) or not bars_raw:
        return None
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
        if None in (open_v, high_v, low_v, close_v):
            return None
        assert open_v is not None and high_v is not None
        assert low_v is not None and close_v is not None
        confirm_raw = row.get("confirm")
        if confirm_raw is None:
            confirm = True
        elif isinstance(confirm_raw, bool):
            confirm = confirm_raw
        else:
            confirm = str(confirm_raw) in {"1", "true", "True"}
        bars.append(
            {
                "ts": ts.strip(),
                "open": open_v,
                "high": high_v,
                "low": low_v,
                "close": close_v,
                "confirm": confirm,
                "provisional": not confirm,
            }
        )
    venue_raw = ohlcv_readmodel.get("venue")
    venue_display = None
    if isinstance(venue_raw, str) and venue_raw.strip():
        venue_display = _venue_display(venue_raw, Availability.AVAILABLE)
    digest_source = {
        "instrument_id": ohlcv_readmodel.get("instrument_id"),
        "venue": venue_display or venue_raw,
        "interval": ohlcv_readmodel.get("interval"),
        "last_closed_timestamp": ohlcv_readmodel.get("last_closed_timestamp"),
        "captured_at": ohlcv_readmodel.get("captured_at"),
        "bars": [
            {
                "ts": b["ts"],
                "open": b["open"],
                "high": b["high"],
                "low": b["low"],
                "close": b["close"],
                "confirm": b["confirm"],
            }
            for b in bars
        ],
    }
    payload_digest = hashlib.sha256(
        json.dumps(digest_source, sort_keys=True, separators=(",", ":")).encode("utf-8")
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
        "payload_digest": payload_digest,
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


def present_market_landscape_v2(
    page: MarketDashboardPageSnapshotV1,
    *,
    ohlcv_readmodel: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Format page snapshot for SSR template context (presentation only)."""
    market = _slot_view(page.market_instrument)
    universe = _slot_view(page.universe_ranking)
    scope = _slot_view(page.dynamic_scope)
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

    return {
        "page_schema_id": page.schema_id,
        "generated_at": page.generated_at.isoformat().replace("+00:00", "Z"),
        "git_sha": page.git_sha,
        "runtime_bridge_display": page.runtime_bridge_display,
        "shell_authority_class": page.shell_authority_class,
        "consumer_role": "read_only_consumer",
        "phase": "PHASE_4_6B_ECONOMIC_EVIDENCE_EXPLICIT_INJECTION_BINDING",
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
        "regime": dict(_NOT_BOUND_VIEW),
        "bull_bear": dict(_NOT_BOUND_VIEW),
        "switch": dict(_NOT_BOUND_VIEW),
        "decision": decision,
        "double_play": double_play,
        "risk": risk,
        "safety": safety,
        "execution": execution,
        "economic": {
            **economic,
            "status_display": economic_status_display,
        },
        "autonomy": autonomy,
        "diagnostics": diagnostics,
        "source_health": _present_source_health_compact(
            health=health,
            slot_views={
                "market_instrument": market,
                "universe_ranking": universe,
                "dynamic_scope": scope,
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
            "captured_at": (browser_payload or ohlcv_payload or {}).get("captured_at"),
            "effective_at": (browser_payload or ohlcv_payload or {}).get("effective_at"),
            "payload_digest": (browser_payload or {}).get("payload_digest"),
            "is_stale": bool((ohlcv_payload or {}).get("is_stale")),
            "poll_path": OHLCV_POLL_PATH,
            "poll_interval_seconds": _ohlcv_poll_interval_seconds(),
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
            "phase_4_3a_bound_slots": [
                "canonical_decision",
            ],
            "phase_4_3b_bound_slots": [
                "double_play",
            ],
            "phase_4_4a_bound_slots": [
                "safety_authority",
            ],
            "phase_4_6b_bound_slots": [
                "economic_summary",
            ],
            "slots": {
                "market_instrument": market,
                "universe_ranking": universe,
                "dynamic_scope": scope,
                "canonical_decision": decision,
                "double_play": double_play,
                "risk_sizing_capital": risk,
                "safety_authority": safety,
                "execution_reconciliation": execution,
                "economic_summary": {
                    **economic,
                    "status_display": economic_status_display,
                },
                "autonomy_stage": autonomy,
                "diagnostics_summary": diagnostics,
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
            "phase_4_1_binding_active": True,
            "phase_4_2_binding_active": True,
            "phase_4_3a_binding_active": True,
            "phase_4_3b_binding_active": True,
            "phase_4_4a_binding_active": True,
            "phase_4_6b_binding_active": True,
            "phase_4_full_pass": False,
            "phase_4_authorized": True,
            "operator_skeleton_approval": "PENDING",
        },
    }
