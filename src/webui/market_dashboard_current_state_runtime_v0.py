"""SSR display context for STEP29M current-state panel on GET /market (always on, view-only)."""

from __future__ import annotations

from typing import Any

from .market_dashboard_current_state_snapshot_v0 import (
    SNAPSHOT_OWNER,
    market_dashboard_current_state_snapshot_v0,
)


def build_market_dashboard_current_state_display_context() -> dict[str, Any]:
    """Build template context from the canonical snapshot owner (no duplicate SSOT)."""

    snapshot = market_dashboard_current_state_snapshot_v0()
    system = snapshot["current_system_state"]
    governance = snapshot["governance_and_safety"]
    evidence = snapshot["pr_and_evidence_status"]
    provenance = snapshot["provenance"]

    return {
        "section_visible": True,
        "display_status": "current",
        "view_only": True,
        "controls_allowed": False,
        "snapshot_owner": SNAPSHOT_OWNER,
        "snapshot_version": snapshot["snapshot_version"],
        "provenance": provenance,
        "system": system,
        "technical_completion": snapshot["technical_completion"],
        "economic_result": snapshot["economic_result"],
        "current_research": snapshot["current_research"],
        "parity_surfaces_completed": snapshot["parity_surfaces_completed"],
        "blocked_main_gates": snapshot["blocked_main_gates"],
        "strategy_fleet": snapshot["strategy_fleet"],
        "ma_crossover_fixed_config": snapshot["ma_crossover_fixed_config"],
        "next_parity_slice": snapshot["next_parity_slice"],
        "documented_only_later_path": snapshot["documented_only_later_path"],
        "governance_and_safety": governance,
        "pr_and_evidence_status": evidence,
        "evidence_integrity_secondary": {
            "ratification_bundle_manifest_verify_rc": evidence["ratification_evidence"][
                "MANIFEST_VERIFY_RC"
            ],
            "ratification_bundle_integrity_note": evidence["ratification_evidence"][
                "integrity_note"
            ],
            "secondary_surface_only": True,
            "dominant_alarm_forbidden": True,
        },
        "historical_semantics_suppressed": snapshot["historical_semantics_suppressed"],
        "runtime_effect": False,
        "order_effect": False,
        "productive_runner_invocations_allowed": 0,
    }
