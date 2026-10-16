"""Fail-closed stubs after presentation infrastructure retirement."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def build_presentation_retired_cockpit_payload_v1(*, repo_root: Path) -> dict[str, Any]:
    """Minimal cockpit-shaped payload: explicit NO_TRADE / blocked (presentation UI retired)."""
    _ = repo_root
    return {
        "presentation_ops_cockpit_retired": True,
        "policy_state": {
            "enabled": False,
            "armed": False,
            "dry_run": True,
            "confirm_token_required": True,
            "kill_switch_active": True,
            "blocked": True,
            "action": "NO_TRADE",
        },
        "incident_state": {"requires_operator_attention": True},
        "exposure_state": {
            "caps_configured": [
                {
                    "cap_id": "presentation_retired_bounded_placeholder_v1",
                    "configured": True,
                    "authority_effect": "NONE",
                }
            ],
        },
        "guard_state": {"treasury_separation": "enforced"},
        "stale_state": {"summary": "ok"},
        "evidence_state": {"summary": "ok"},
        "dependencies_state": {"summary": "ok"},
        "human_supervision_state": {"status": "operator_supervised"},
        "treasury_state": {"separation_explicit": True},
        "runtime_state": {"presentation_http_retired": True},
    }
