"""
Incident / dependency **safety observation** aggregate for the Ops Cockpit payload.

Uses only caller-supplied rollups: ``incident_state``, ``dependencies_state``, and optional
``policy_state`` / ``operator_state`` for **consistency notes** (not new authority).

**Observation only** — not incident resolution, not approval, not unlock, not broker truth,
**not** an all-clear. This is narrower than ``build_safety_posture_observation`` (which rolls up
overall gating posture); use that object for the holistic safety/gating snapshot.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional

READER_SCHEMA_VERSION = "incident_safety_observation/v0"

_STATUS_CAUTION = "caution"
_STATUS_DEGRADED = "degraded"
_STATUS_NOMINAL = "nominal"
_STATUS_UNKNOWN = "unknown"


def _as_dict(value: Any) -> Optional[Dict[str, Any]]:
    if value is None:
        return None
    if isinstance(value, dict):
        return dict(value)
    return None


def _norm(value: Any) -> str:
    return str(value or "").strip().lower()


def build_incident_safety_observation(
    *,
    incident_state: Mapping[str, Any],
    dependencies_state: Mapping[str, Any],
    policy_state: Optional[Mapping[str, Any]] = None,
    operator_state: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Roll up incident and dependency **observation** signals already present in the cockpit payload.
    """
    inc = _as_dict(incident_state)
    dep = _as_dict(dependencies_state)
    ps = _as_dict(policy_state) if policy_state is not None else None
    op = _as_dict(operator_state) if operator_state is not None else None

    consistency_notes: List[str] = []
    contributing: List[str] = []

    if inc is None or dep is None:
        return {
            "status": _STATUS_UNKNOWN,
            "summary": "Insufficient structured payload objects for incident/safety observation (read-only).",
            "data_source": "cockpit_payload_aggregate",
            "provenance": {
                "builder": "build_incident_safety_observation",
                "reader_schema_version": READER_SCHEMA_VERSION,
            },
            "observation_reason": "missing_required_state_dict",
            "consistency_notes": [],
            "contributing_signals": [],
            "reader_schema_version": READER_SCHEMA_VERSION,
        }

    dep_summary = _norm(dep.get("summary"))
    tel = _norm(dep.get("telemetry"))
    degraded_list = dep.get("degraded")
    dep_degraded_nonempty = isinstance(degraded_list, list) and len(degraded_list) > 0

    inc_summary = _norm(inc.get("summary"))
    inc_status = _norm(inc.get("status"))
    ks = bool(inc.get("kill_switch_active"))
    inc_deg = bool(inc.get("degraded"))
    stop = bool(inc.get("incident_stop_invoked"))
    req_att = bool(inc.get("requires_operator_attention"))
    op_auth = _norm(inc.get("operator_authoritative_state"))

    degraded = (
        ks
        or inc_status == "blocked"
        or inc_summary == "blocked"
        or inc_deg
        or stop
        or dep_summary in ("degraded", "stale")
        or tel == "critical"
        or dep_degraded_nonempty
    )

    caution = (
        (tel == "warn" or dep_summary == "partial")
        or (req_att and not degraded)
        or (inc_summary == "degraded" and not inc_deg)
        or (op_auth in ("blocked", "kill_switch_active", "degraded") and inc_summary == "normal")
    )

    if ps is not None:
        pol_blocked = bool(ps.get("blocked"))
        entry = inc.get("entry_permitted")
        if isinstance(entry, bool) and pol_blocked != (not entry):
            consistency_notes.append(
                "policy_state.blocked does not align with incident_state.entry_permitted "
                "(observation only; enforcement is outside this aggregate)."
            )
    if ps is not None and op is not None:
        pol_b = bool(ps.get("blocked"))
        op_b = bool(op.get("blocked"))
        if pol_b != op_b:
            consistency_notes.append(
                "policy_state.blocked differs from operator_state.blocked in this snapshot "
                "(observation only)."
            )

    status: str
    summary: str
    observation_reason: Optional[str] = None

    if degraded:
        status = _STATUS_DEGRADED
        summary = (
            "Incident and dependency rollups show elevated signals in this snapshot "
            "(read-only; not resolution, not an all-clear, not live incident truth)."
        )
        if ks:
            contributing.append("incident_state.kill_switch_active")
        if inc_status == "blocked" or inc_summary == "blocked":
            contributing.append("incident_state.status_or_summary")
        if inc_deg:
            contributing.append("incident_state.degraded")
        if stop:
            contributing.append("incident_state.incident_stop_invoked")
        if dep_summary in ("degraded", "stale") or dep_degraded_nonempty:
            contributing.append("dependencies_state.summary_or_degraded")
        if tel == "critical":
            contributing.append("dependencies_state.telemetry")
    elif caution:
        status = _STATUS_CAUTION
        summary = (
            "Partial incident or dependency signals warrant extra operator attention in this "
            "aggregate (observation only; not a go/no-go approval — see also "
            "safety_posture_observation for overall gating posture)."
        )
        if tel == "warn":
            contributing.append("dependencies_state.telemetry")
        if dep_summary == "partial":
            contributing.append("dependencies_state.summary")
        if req_att:
            contributing.append("incident_state.requires_operator_attention")
        if inc_summary == "degraded" and not inc_deg:
            contributing.append("incident_state.summary")
        if op_auth:
            contributing.append("incident_state.operator_authoritative_state")
    else:
        status = _STATUS_NOMINAL
        summary = (
            "No elevated incident or dependency degradation flags in this aggregate snapshot "
            "(observation only; not an all-clear against external or exchange state). "
            "Overall gating posture remains in safety_posture_observation."
        )
        contributing.extend(
            [
                "incident_state.summary",
                "dependencies_state.summary",
            ]
        )

    out: Dict[str, Any] = {
        "status": status,
        "summary": summary,
        "data_source": "cockpit_payload_aggregate",
        "provenance": {
            "builder": "build_incident_safety_observation",
            "reader_schema_version": READER_SCHEMA_VERSION,
        },
        "observation_reason": observation_reason,
        "consistency_notes": consistency_notes,
        "contributing_signals": sorted(set(contributing)),
        "reader_schema_version": READER_SCHEMA_VERSION,
    }
    return out
