"""Shadow readiness matrix evaluator (post-enablement reproof helper)."""

from __future__ import annotations

from typing import Any

from src.ops.canonical_shadow_runtime_enablement_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
)


def evaluate_shadow_readiness_dimensions_v1(
    *,
    bridge_activated: bool,
) -> dict[str, Any]:
    """Re-classify readiness dimensions after canonical runtime implementation."""
    dims: list[dict[str, str]] = [
        {
            "NAME": "CONFIG_READY",
            "STATUS": "PROVEN_NOT_READY",
            "NOTE": "247 preflight still BLOCKED",
        },
        {"NAME": "MARKET_DATA_READY", "STATUS": "PROVEN_READY", "NOTE": "unchanged"},
        {"NAME": "SELECTION_READY", "STATUS": "PROVEN_READY", "NOTE": "unchanged"},
        {"NAME": "DECISION_READY", "STATUS": "PROVEN_READY", "NOTE": "unchanged"},
        {"NAME": "CAPITAL_READY", "STATUS": "PROVEN_READY", "NOTE": "unchanged"},
        {"NAME": "RISK_READY", "STATUS": "PROVEN_READY", "NOTE": "unchanged"},
        {"NAME": "CRS_READY", "STATUS": "PROVEN_READY", "NOTE": "unchanged"},
        {"NAME": "SIZING_READY", "STATUS": "PROVEN_READY", "NOTE": "unchanged"},
        {"NAME": "INTENT_READY", "STATUS": "PROVEN_READY", "NOTE": "unchanged"},
        {"NAME": "ADMISSION_READY", "STATUS": "PROVEN_READY", "NOTE": "unchanged"},
        {
            "NAME": "EXECUTION_SIMULATION_READY",
            "STATUS": "PROVEN_READY" if bridge_activated else "PROVEN_NOT_READY",
            "NOTE": "SimulatedExecutionPort sink; requires bridge ACTIVATED",
        },
        {
            "NAME": "POSITION_STATE_READY",
            "STATUS": "PROVEN_READY" if bridge_activated else "UNKNOWN_CURRENT",
            "NOTE": "Canonical accounting via simulated port when activated",
        },
        {
            "NAME": "RECONCILIATION_READY",
            "STATUS": "PROVEN_NOT_READY",
            "NOTE": "Venue reconciliation not in scope for offline shadow sink",
        },
        {
            "NAME": "ACCOUNTING_READY",
            "STATUS": "PROVEN_READY" if bridge_activated else "PROVEN_NOT_READY",
            "NOTE": "apply_intended_action_via_canonical_accounting_v1",
        },
        {"NAME": "OBSERVABILITY_READY", "STATUS": "PROVEN_READY", "NOTE": "evidence dict emitted"},
        {"NAME": "AUDIT_READY", "STATUS": "PROVEN_READY", "NOTE": "unchanged"},
        {
            "NAME": "RESTART_RECOVERY_READY",
            "STATUS": "PROVEN_NOT_READY",
            "NOTE": "Bounded offline cycle only; wallclock restart not proven",
        },
        {
            "NAME": "KILL_SWITCH_READY",
            "STATUS": "PROVEN_NOT_READY",
            "NOTE": "Fail-closed bridge deactivation; dedicated kill wiring not proven",
        },
        {
            "NAME": "SAFETY_READY",
            "STATUS": "PROVEN_READY",
            "NOTE": f"POST_ALLOWED={POST_ALLOWED}; EXTERNAL_EFFECT={EXTERNAL_EFFECT_AUTHORIZED}",
        },
    ]
    unknown = sum(1 for d in dims if d["STATUS"] == "UNKNOWN_CURRENT")
    blockers = [d["NAME"] for d in dims if d["STATUS"] == "PROVEN_NOT_READY"]
    ready = unknown == 0 and not blockers
    return {"DIMENSIONS": dims, "SHADOW_READY": ready}
