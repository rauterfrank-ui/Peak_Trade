"""
Top-level **safety_state** projection for the Ops Cockpit payload (vNext read-model name).

Bundles **only** already-built cockpit objects — ``safety_posture_observation``,
``incident_safety_observation``, and a small scalar subset of ``incident_state`` — into one
top-level key for spec alignment with ``OPS_SUITE_DASHBOARD_VNEXT_SPEC`` (*Data Model
Expectations*). **Does not** recompute gating logic; **does not** add broker or unlock semantics.

**Observation / projection only** — not approval, not incident resolution, not an all-clear.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

READER_SCHEMA_VERSION = "safety_state/v0"


def _as_dict(value: Any) -> Optional[Dict[str, Any]]:
    if value is None:
        return None
    if isinstance(value, dict):
        return dict(value)
    return None


def build_safety_state(
    *,
    safety_posture_observation: Mapping[str, Any],
    incident_state: Mapping[str, Any],
    incident_safety_observation: Mapping[str, Any],
) -> Dict[str, Any]:
    """
    Project a read-only **safety_state** object from existing payload sections (no new I/O).
    """
    spo = _as_dict(safety_posture_observation)
    inc = _as_dict(incident_state)
    iso = _as_dict(incident_safety_observation)

    if spo is None or inc is None or iso is None:
        return {
            "summary": (
                "Insufficient structured objects for safety_state projection (read-only); "
                "see individual safety_posture_observation, incident_state, incident_safety_observation."
            ),
            "data_source": "cockpit_payload_aggregate",
            "reader_schema_version": READER_SCHEMA_VERSION,
            "provenance": {
                "builder": "build_safety_state",
                "observation_reason": "missing_required_projection_inputs",
            },
        }

    posture_status = str(spo.get("status", "unknown") or "unknown")
    iso_status = str(iso.get("status", "unknown") or "unknown")

    incident_signal_subset = {
        "status": str(inc.get("status", "unknown") or "unknown"),
        "summary": str(inc.get("summary", "unknown") or "unknown"),
        "kill_switch_active": bool(inc.get("kill_switch_active")),
        "blocked": bool(inc.get("blocked")),
        "degraded": bool(inc.get("degraded")),
        "requires_operator_attention": bool(inc.get("requires_operator_attention")),
    }

    summary = (
        "Read-only safety projection: links holistic gating posture, incident/safety observation, "
        "and incident rollups already in the payload — not approval, not unlock, not broker truth."
    )

    return {
        "summary": summary,
        "data_source": "cockpit_payload_aggregate",
        "reader_schema_version": READER_SCHEMA_VERSION,
        "provenance": {
            "builder": "build_safety_state",
            "upstream_aggregates": [
                "safety_posture_observation",
                "incident_safety_observation",
                "incident_state",
            ],
        },
        "posture_observation": {
            "status": posture_status,
            "reader_schema_version": str(spo.get("reader_schema_version", "") or ""),
        },
        "incident_safety_observation": {
            "status": iso_status,
            "reader_schema_version": str(iso.get("reader_schema_version", "") or ""),
        },
        "incident_signal_subset": incident_signal_subset,
    }
