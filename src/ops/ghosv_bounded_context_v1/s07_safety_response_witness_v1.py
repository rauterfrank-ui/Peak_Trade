"""S07 — read-only safety response witness."""

from __future__ import annotations

from typing import Mapping, Optional, Sequence

from src.ops.ghosv_bounded_context_v1.types_v1 import (
    GhosvCriticalIncidentV1,
    GhosvSafetyAdapterDecisionV1,
    GhosvSafetyResponseWitnessV1,
)


def witness_safety_response_v1(
    *,
    incidents: Sequence[GhosvCriticalIncidentV1],
    adapter: GhosvSafetyAdapterDecisionV1,
    external_observations: Optional[Mapping[str, bool]] = None,
) -> GhosvSafetyResponseWitnessV1:
    obs = dict(external_observations or {})
    incident_id = incidents[0].incident_id if incidents else ""
    created = len(incidents) > 0
    delivery = adapter.delivery_attempted
    accepted = adapter.incident_accepted
    persisted = bool(obs.get("safety_state_persisted", False))
    admission_denied = bool(obs.get("admission_denied", False))
    cancel_req = bool(obs.get("venue_cancel_requested", False))
    cancel_ack = bool(obs.get("venue_cancel_acknowledged", False))
    order_closed = bool(obs.get("venue_order_closed", False))
    fill_executed = bool(obs.get("fill_already_executed", False))
    unknown = not any(
        [persisted, admission_denied, cancel_req, cancel_ack, order_closed, fill_executed]
    ) and (created and not delivery)
    notes: list[str] = []
    if created and not admission_denied:
        notes.append("INCIDENT_CREATED_NOT_EQUAL_TRADE_STOPPED")
    if admission_denied and not cancel_req:
        notes.append("ADMISSION_DENIED_NOT_EQUAL_OPEN_ORDER_CANCELLED")
    if adapter.productive_side_effects:
        notes.append("UNEXPECTED_PRODUCTIVE_SIDE_EFFECT")
    return GhosvSafetyResponseWitnessV1(
        incident_id=incident_id,
        incident_created=created,
        incident_delivery_attempted=delivery,
        incident_accepted=accepted,
        safety_state_persisted=persisted,
        admission_denied=admission_denied,
        venue_cancel_requested=cancel_req,
        venue_cancel_acknowledged=cancel_ack,
        venue_order_closed=order_closed,
        fill_already_executed=fill_executed,
        unknown=unknown,
        notes=tuple(notes),
    )
