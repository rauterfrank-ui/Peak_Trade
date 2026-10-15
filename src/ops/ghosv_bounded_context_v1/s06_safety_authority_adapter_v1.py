"""S06 — disabled existing safety authority adapter (contract only)."""

from __future__ import annotations

from typing import Optional, Sequence

from src.ops.ghosv_bounded_context_v1.constants_v1 import (
    ADAPTER_MODE,
    SAFETY_ESCALATION_ENABLED,
)
from src.ops.ghosv_bounded_context_v1.types_v1 import (
    GhosvCriticalIncidentV1,
    GhosvSafetyAdapterDecisionV1,
)

ADAPTER_CONTRACT = "ghosv_existing_safety_authority_adapter.v1"
PLANNED_HANDOFF = (
    "KillSwitch.trigger+StatePersistence+FILEGATE (PROPOSED_ONLY; not invoked when disabled)"
)


class GhosvSafetyAdapterActivationForbiddenError(RuntimeError):
    pass


def evaluate_safety_authority_adapter_v1(
    incidents: Sequence[GhosvCriticalIncidentV1],
    *,
    safety_escalation_enabled: Optional[bool] = None,
    adapter_mode: Optional[str] = None,
    stub_accept: bool = False,
) -> GhosvSafetyAdapterDecisionV1:
    enabled = (
        SAFETY_ESCALATION_ENABLED
        if safety_escalation_enabled is None
        else safety_escalation_enabled
    )
    mode = ADAPTER_MODE if adapter_mode is None else adapter_mode
    reasons: list[str] = []
    if enabled is True and mode != "STUB_TEST":
        raise GhosvSafetyAdapterActivationForbiddenError("PRODUCTIVE_SAFETY_ESCALATION_FORBIDDEN")
    delivery = False
    accepted = False
    side_effects = False
    if incidents and mode == "STUB_TEST" and stub_accept:
        delivery = True
        accepted = True
        reasons.append("STUB_SIMULATED_HANDOFF_ONLY")
    elif incidents:
        reasons.append("ADAPTER_DISABLED_NO_DELIVERY")
    else:
        reasons.append("NO_INCIDENT")
    return GhosvSafetyAdapterDecisionV1(
        adapter_mode=mode,
        safety_escalation_enabled=enabled is True,
        incident_accepted=accepted,
        delivery_attempted=delivery,
        productive_side_effects=side_effects,
        reason_codes=tuple(reasons),
        planned_handoff=PLANNED_HANDOFF,
    )
