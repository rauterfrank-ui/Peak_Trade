"""Presenter for Market Dashboard Landscape V2 — display formatting only.

No decision, risk, sizing, scope, Double Play, or Safety authority logic.
"""

from __future__ import annotations

from typing import Any, Mapping

from .availability import Availability
from .contracts import _ProjectionBase
from .page_aggregate import MarketDashboardPageSnapshotV1
from .serialization import serialize_projection

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

_NOT_BOUND_VIEW: dict[str, Any] = {
    "availability": Availability.NOT_BOUND.value,
    "availability_label": AVAILABILITY_LABELS[Availability.NOT_BOUND],
}


def _display_value(raw: Any, availability: Availability) -> str:
    if availability is not Availability.AVAILABLE or raw is None:
        return AVAILABILITY_LABELS[availability]
    return str(raw)


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


def present_market_landscape_v2(page: MarketDashboardPageSnapshotV1) -> dict[str, Any]:
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
    if chart_availability is Availability.AVAILABLE:
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
    if page.universe_ranking.availability is Availability.AVAILABLE:
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
        else _display_value(
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
            "venue": _display_value(
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
        "source_health": {
            "availability": health.availability.value,
            "slot_availability": {
                slot: state.value for slot, state in sorted(health.slot_availability.items())
            },
            "incomplete_slots": list(health.incomplete_slots),
            "provenance": health.provenance.to_json_dict(),
            "freshness": health.freshness.to_json_dict(),
        },
        "chart": {
            "availability": chart_availability.value,
            "availability_label": AVAILABILITY_LABELS[chart_availability],
            "bound": chart_availability is Availability.AVAILABLE,
            "message": chart_message,
            "ohlcv": None,
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
