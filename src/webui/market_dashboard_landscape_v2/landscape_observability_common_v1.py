"""Shared display helpers for Landscape consumer observability modules."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from .availability import Availability
from .contracts import _ProjectionBase
from .serialization import serialize_projection
from .source_health_projection_fidelity_v1 import format_freshness_display_v1

AVAILABILITY_LABELS: Mapping[Availability, str] = {
    Availability.AVAILABLE: "AVAILABLE",
    Availability.NOT_BOUND: "NOT_BOUND",
    Availability.MISSING_SOURCE: "MISSING_SOURCE",
    Availability.STALE: "STALE",
    Availability.INVALID: "INVALID",
}

# Existing universe-rail token for an optional projected field that is absent.
# Not a new Availability enum value and not a reconstructed domain fact.
OPTIONAL_FIELD_ABSENT_DISPLAY = "NOT_AVAILABLE"
_LEAKED_ABSENT_TOKENS = frozenset({"", "None", "null", "undefined"})


def fail_closed_component_display_v1(value: Any) -> str:
    """One already-projected component. Never emits None, null, or undefined."""
    if value is None:
        return OPTIONAL_FIELD_ABSENT_DISPLAY
    text = str(value).strip()
    if text in _LEAKED_ABSENT_TOKENS:
        return OPTIONAL_FIELD_ABSENT_DISPLAY
    return text


def fail_closed_scalar_display_v1(value: Any, *, availability: Availability) -> str:
    """Slot-aware scalar. Unavailable slots keep their availability label."""
    if availability not in (Availability.AVAILABLE, Availability.STALE):
        return AVAILABILITY_LABELS[availability]
    return fail_closed_component_display_v1(value)


def provenance_and_freshness_envelope_v1(snap: _ProjectionBase) -> dict[str, Any]:
    payload = serialize_projection(snap)
    provenance = payload.get("provenance")
    freshness = payload.get("freshness")
    prov = dict(provenance) if isinstance(provenance, Mapping) else {}
    fresh = dict(freshness) if isinstance(freshness, Mapping) else {}
    availability = snap.availability
    return {
        "schema_id": snap.schema_id,
        "availability": availability.value,
        "availability_label": AVAILABILITY_LABELS[availability],
        "is_available": availability is Availability.AVAILABLE,
        "is_stale": availability is Availability.STALE,
        "freshness": fresh,
        "freshness_display": format_freshness_display_v1(fresh),
        "is_stale_flag": fresh.get("is_stale") is True,
        "stale_reason": fresh.get("stale_reason"),
        "provenance": prov,
        "source_kind": prov.get("source_kind"),
        "source_reference": prov.get("source_reference"),
        "producer_module": prov.get("producer_module"),
        "provenance_generated_at": prov.get("generated_at"),
        "provenance_effective_at": prov.get("effective_at"),
        "evidence_digest": prov.get("evidence_digest"),
    }


def scalar_field_display_v1(value: Any, *, availability: Availability) -> str:
    return fail_closed_scalar_display_v1(value, availability=availability)


def reason_codes_display_v1(codes: Sequence[str], *, availability: Availability) -> str:
    if availability not in (Availability.AVAILABLE, Availability.STALE):
        label = AVAILABILITY_LABELS[availability]
        if codes:
            return f"{label} · {', '.join(str(c) for c in codes)}"
        return label
    if not codes:
        return OPTIONAL_FIELD_ABSENT_DISPLAY
    return ", ".join(str(c) for c in codes)


def metric_field_display_v1(
    metric: Mapping[str, Any] | None,
    *,
    availability: Availability,
) -> str:
    if availability not in (Availability.AVAILABLE, Availability.STALE):
        return AVAILABILITY_LABELS[availability]
    if metric is None or not isinstance(metric, Mapping):
        return OPTIONAL_FIELD_ABSENT_DISPLAY
    if metric.get("value") is not None:
        return fail_closed_component_display_v1(metric["value"])
    semantic = metric.get("semantic")
    reason = metric.get("reason_code")
    if semantic is not None and reason is not None:
        return f"{fail_closed_component_display_v1(semantic)}:{fail_closed_component_display_v1(reason)}"
    if semantic is not None:
        return fail_closed_component_display_v1(semantic)
    if reason is not None:
        return fail_closed_component_display_v1(reason)
    return OPTIONAL_FIELD_ABSENT_DISPLAY


def field_row_v1(*, field_id: str, label: str, display: str) -> dict[str, str]:
    return {"field_id": field_id, "label": label, "display": display}
