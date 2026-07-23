"""Presenter for Market Dashboard Landscape V2 — display formatting only.

No decision, risk, sizing, scope, or Double Play authority logic.
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


def _display_value(raw: Any, availability: Availability) -> str:
    if availability is not Availability.AVAILABLE or raw is None:
        return AVAILABILITY_LABELS[availability]
    return str(raw)


def _slot_view(snap: _ProjectionBase) -> dict[str, Any]:
    payload = serialize_projection(snap)
    availability = snap.availability
    return {
        "availability": availability.value,
        "availability_label": AVAILABILITY_LABELS[availability],
        "is_available": availability is Availability.AVAILABLE,
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
    return {
        "page_schema_id": page.schema_id,
        "generated_at": page.generated_at.isoformat().replace("+00:00", "Z"),
        "git_sha": page.git_sha,
        "runtime_bridge_display": page.runtime_bridge_display,
        "shell_authority_class": page.shell_authority_class,
        "consumer_role": "read_only_consumer",
        "phase": "PHASE_3_LANDSCAPE_SHELL",
        "global_strip": {
            "instrument": _display_value(
                page.market_instrument.instrument_id, page.market_instrument.availability
            ),
            "venue": _display_value(
                page.market_instrument.venue, page.market_instrument.availability
            ),
            "scope": _display_value(
                page.dynamic_scope.scope_state, page.dynamic_scope.availability
            ),
            "regime": AVAILABILITY_LABELS[page.dynamic_scope.availability],
            "runtime_state": page.runtime_bridge_display,
            "runtime_state_class": page.shell_authority_class,
            "freshness": health.freshness.to_json_dict(),
            "safety_status": _display_value(
                page.safety_authority.kill_switch_state, page.safety_authority.availability
            ),
            "source_health": health.availability.value,
        },
        "market": market,
        "universe": universe,
        "scope": scope,
        "decision": decision,
        "double_play": double_play,
        "risk": risk,
        "safety": safety,
        "execution": execution,
        "economic": economic,
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
            "message": (
                "Primary chart bound to market read-model."
                if chart_availability is Availability.AVAILABLE
                else "Primary chart NOT_BOUND — no OHLCV fabricated for Landscape shell."
            ),
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
            "slots": {
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
            "phase_4_authorized": False,
            "operator_skeleton_approval": "PENDING",
        },
    }
