"""V03/V04 consumer-only Source Health slot matrix and presentation projection fidelity.

Aggregation/display only — never loads archives, never writes readmodels, never
recomputes domain freshness beyond bound slot snapshots.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .availability import Availability
from .source_health import DashboardSourceHealthSnapshotV1

CAPABILITY_ID = "LANDSCAPE_SOURCE_HEALTH_AND_PROJECTION_FRESHNESS_FIDELITY_V1"
FRESHNESS_UNAVAILABLE = "FRESHNESS_UNAVAILABLE"

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

_AVAILABILITY_LABELS: Mapping[Availability, str] = {
    Availability.AVAILABLE: "AVAILABLE",
    Availability.NOT_BOUND: "NOT_BOUND",
    Availability.MISSING_SOURCE: "MISSING_SOURCE",
    Availability.STALE: "STALE",
    Availability.INVALID: "INVALID",
}


@dataclass(frozen=True)
class PresentationProjectionFamilyV1:
    """Catalog entry for durable presentation-projection autobind families (display only)."""

    family_id: str
    schema_name: str
    slot: str


PRESENTATION_PROJECTION_FAMILIES_V1: tuple[PresentationProjectionFamilyV1, ...] = tuple(
    sorted(
        (
            PresentationProjectionFamilyV1(
                family_id="bull_bear_regime_presentation_projection",
                schema_name="bull_bear_regime_presentation_projection.v1",
                slot="regime_bull_bear_switch",
            ),
            PresentationProjectionFamilyV1(
                family_id="canonical_decision_presentation_projection",
                schema_name="canonical_decision_presentation_projection.v1",
                slot="canonical_decision",
            ),
            PresentationProjectionFamilyV1(
                family_id="double_play_presentation_projection",
                schema_name="double_play_presentation_projection.v1",
                slot="double_play",
            ),
            PresentationProjectionFamilyV1(
                family_id="dynamic_scope_presentation_projection",
                schema_name="dynamic_scope_presentation_projection.v1",
                slot="dynamic_scope",
            ),
            PresentationProjectionFamilyV1(
                family_id="economic_summary_presentation_projection",
                schema_name="economic_summary_presentation_projection.v1",
                slot="economic_summary",
            ),
            PresentationProjectionFamilyV1(
                family_id="execution_reconciliation_presentation_projection",
                schema_name="execution_reconciliation_presentation_projection.v1",
                slot="execution_reconciliation",
            ),
            PresentationProjectionFamilyV1(
                family_id="risk_sizing_capital_presentation_projection",
                schema_name="risk_sizing_capital_presentation_projection.v1",
                slot="risk_sizing_capital",
            ),
            PresentationProjectionFamilyV1(
                family_id="safety_authority_presentation_projection",
                schema_name="safety_authority_presentation_projection.v1",
                slot="safety_authority",
            ),
        ),
        key=lambda entry: entry.family_id,
    )
)


def format_freshness_display_v1(freshness: Mapping[str, Any] | None) -> str:
    """Format canonical freshness for display; never invent timestamps."""
    if not isinstance(freshness, Mapping):
        return FRESHNESS_UNAVAILABLE
    observed = freshness.get("observed_at")
    if observed is None or not str(observed).strip():
        return FRESHNESS_UNAVAILABLE
    return str(observed)


def source_line_display_v1(*, availability: str, freshness_display: str) -> str:
    return f"{availability} · {freshness_display}"


def presentation_presence_from_availability_v1(availability: str) -> str:
    """Map bound Landscape slot availability to presentation presence vocabulary."""
    if availability in ("AVAILABLE", "STALE"):
        return "PRESENT"
    if availability == "MISSING_SOURCE":
        return "ABSENT"
    if availability == "NOT_BOUND":
        return "NOT_BOUND"
    if availability == "INVALID":
        return "INVALID"
    return "UNKNOWN"


def _provenance_fields(view: Mapping[str, Any]) -> tuple[str | None, str | None]:
    provenance = view.get("provenance")
    if not isinstance(provenance, Mapping):
        return None, None
    source_kind = provenance.get("source_kind")
    source_reference = provenance.get("source_reference")
    kind = None if source_kind is None else str(source_kind)
    ref = None if source_reference is None else str(source_reference)
    return kind, ref


def _freshness_meta(view: Mapping[str, Any]) -> tuple[bool, str | None]:
    freshness = view.get("freshness")
    if not isinstance(freshness, Mapping):
        return False, None
    is_stale = freshness.get("is_stale") is True
    stale_reason = freshness.get("stale_reason")
    reason = None if stale_reason is None else str(stale_reason)
    return is_stale, reason


def build_source_health_slot_matrix_v1(
    *,
    health: DashboardSourceHealthSnapshotV1,
    slot_views: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """V03: compact slot matrix from Source Health aggregation + bound slot views."""
    rows: list[dict[str, Any]] = []
    for slot, state in sorted(health.slot_availability.items()):
        view = slot_views.get(slot) or {}
        slot_availability = str(view.get("availability") or state.value)
        freshness_raw = (
            view.get("freshness") if isinstance(view.get("freshness"), Mapping) else None
        )
        freshness_display = format_freshness_display_v1(freshness_raw)
        is_stale, stale_reason = _freshness_meta(view)
        source_kind, source_reference = _provenance_fields(view)
        rows.append(
            {
                "slot": slot,
                "label": _SOURCE_SLOT_LABELS.get(slot, slot),
                "availability": slot_availability,
                "availability_label": (
                    _AVAILABILITY_LABELS[Availability(slot_availability)]
                    if slot_availability in {a.value for a in Availability}
                    else slot_availability
                ),
                "freshness_display": freshness_display,
                "is_stale": is_stale,
                "stale_reason": stale_reason,
                "source_kind": source_kind,
                "source_reference": source_reference,
                "line_display": source_line_display_v1(
                    availability=slot_availability,
                    freshness_display=freshness_display,
                ),
            }
        )
    return rows


def build_presentation_projection_presence_matrix_v1(
    slot_views: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """V04: presence/freshness for durable presentation projection families only."""
    families: list[dict[str, Any]] = []
    for family in PRESENTATION_PROJECTION_FAMILIES_V1:
        view = slot_views.get(family.slot) or {}
        availability = str(view.get("availability") or Availability.NOT_BOUND.value)
        presence = presentation_presence_from_availability_v1(availability)
        freshness_raw = (
            view.get("freshness") if isinstance(view.get("freshness"), Mapping) else None
        )
        freshness_display = format_freshness_display_v1(freshness_raw)
        is_stale, stale_reason = _freshness_meta(view)
        source_kind, source_reference = _provenance_fields(view)
        families.append(
            {
                "family_id": family.family_id,
                "schema_name": family.schema_name,
                "slot": family.slot,
                "slot_label": _SOURCE_SLOT_LABELS.get(family.slot, family.slot),
                "presence": presence,
                "availability": availability,
                "freshness_display": freshness_display,
                "is_stale": is_stale,
                "stale_reason": stale_reason,
                "source_kind": source_kind,
                "source_reference": source_reference,
                "line_display": source_line_display_v1(
                    availability=presence,
                    freshness_display=freshness_display,
                ),
            }
        )
    return {
        "capability_id": CAPABILITY_ID,
        "consumer_role": "read_only_consumer",
        "authority": "NONE",
        "family_count": len(families),
        "families": families,
    }


def build_source_health_presentation_v1(
    *,
    health: DashboardSourceHealthSnapshotV1,
    slot_views: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Combined V03 source-health presentation payload for SSR."""
    freshness = health.freshness.to_json_dict()
    freshness_display = format_freshness_display_v1(freshness)
    availability = health.availability.value
    sources = build_source_health_slot_matrix_v1(health=health, slot_views=slot_views)
    return {
        "availability": availability,
        "availability_label": _AVAILABILITY_LABELS[health.availability],
        "slot_availability": {
            slot: state.value for slot, state in sorted(health.slot_availability.items())
        },
        "incomplete_slots": list(health.incomplete_slots),
        "provenance": health.provenance.to_json_dict(),
        "freshness": freshness,
        "freshness_display": freshness_display,
        "summary_display": source_line_display_v1(
            availability=availability,
            freshness_display=freshness_display,
        ),
        "sources": sources,
        "slot_matrix": sources,
    }
