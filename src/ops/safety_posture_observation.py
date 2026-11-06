"""
Conservative safety / gating posture **observation** for the Ops Cockpit payload.

Uses only caller-supplied cockpit rollups (``policy_state``, ``guard_state``, ``incident_state``,
etc.). **Observation only** — not approval, not unlock, not broker or exchange truth.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional

READER_SCHEMA_VERSION = "safety_posture_observation/v0"

_STATUS_BLOCKING = "blocking"
_STATUS_DEGRADED = "degraded"
_STATUS_CAUTION = "caution"
_STATUS_NOMINAL = "nominal"
_STATUS_UNKNOWN = "unknown"


def _as_dict(value: Any) -> Optional[Dict[str, Any]]:
    if value is None:
        return None
    if isinstance(value, dict):
        return dict(value)
    return None


def _boolish(value: Any) -> Optional[bool]:
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    if isinstance(value, (int, float)):
        if value == 0:
            return False
        if value == 1:
            return True
        return None
    if isinstance(value, str):
        lower = value.strip().lower()
        if lower in ("true", "1", "yes"):
            return True
        if lower in ("false", "0", "no"):
            return False
    return None


def build_safety_posture_observation(
    *,
    policy_state: Mapping[str, Any],
    guard_state: Mapping[str, Any],
    incident_state: Mapping[str, Any],
    operator_state: Mapping[str, Any],
    system_state: Mapping[str, Any],
    stale_state: Optional[Mapping[str, Any]] = None,
    dependencies_state: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Roll up a single **observation** status from existing cockpit payload fields.

    Missing or ambiguous inputs map to ``status`` ``unknown`` with a defensive ``observation_reason``.
    """
    ps = _as_dict(policy_state)
    gs = _as_dict(guard_state)
    inc = _as_dict(incident_state)
    op = _as_dict(operator_state)
    sys_s = _as_dict(system_state)
    st = _as_dict(stale_state) if stale_state is not None else None
    dep = _as_dict(dependencies_state) if dependencies_state is not None else None

    consistency_notes: List[str] = []
    contributing: List[str] = []

    if ps is None or gs is None or inc is None or op is None or sys_s is None:
        return {
            "status": _STATUS_UNKNOWN,
            "summary": "Insufficient structured payload objects for posture observation (read-only).",
            "data_source": "cockpit_payload_aggregate",
            "provenance": {
                "builder": "build_safety_posture_observation",
                "reader_schema_version": READER_SCHEMA_VERSION,
            },
            "observation_reason": "missing_required_state_dict",
            "consistency_notes": [],
            "contributing_signals": [],
            "reader_schema_version": READER_SCHEMA_VERSION,
        }

    ks_ps = bool(ps.get("kill_switch_active"))
    ks_inc = bool(inc.get("kill_switch_active"))
    ks_op = bool(op.get("kill_switch_active"))
    if ks_ps != ks_inc or ks_ps != ks_op:
        consistency_notes.append(
            "kill_switch_active differs across policy/incident/operator snapshots; "
            "treating as active if any is true (observation only)."
        )
    kill_switch_active = ks_ps or ks_inc or ks_op
    if kill_switch_active:
        contributing.append("policy_state.kill_switch_active")
        contributing.append("incident_state.kill_switch_active")

    blocked = bool(ps.get("blocked"))
    if blocked:
        contributing.append("policy_state.blocked")

    entry_perm = inc.get("entry_permitted")
    ep = _boolish(entry_perm)
    if entry_perm is not None and ep is None:
        consistency_notes.append(
            "entry_permitted present but not interpretable as boolean (observation only)."
        )
    elif ep is not None and ep != (not blocked):
        consistency_notes.append(
            "entry_permitted does not match policy_state.blocked (observation only)."
        )

    inc_degraded = bool(inc.get("degraded"))
    if inc_degraded:
        contributing.append("incident_state.degraded")

    stale_summary = str(st.get("summary", "unknown") or "unknown") if st else "unknown"
    if stale_summary == "stale":
        contributing.append("stale_state.summary")

    dep_summary = str(dep.get("summary", "unknown") or "unknown") if dep else "unknown"
    if dep_summary == "degraded":
        contributing.append("dependencies_state.summary")

    incident_stop = bool(inc.get("incident_stop_invoked"))
    if incident_stop:
        contributing.append("incident_state.incident_stop_invoked")

    req_att = bool(inc.get("requires_operator_attention"))
    if req_att:
        contributing.append("incident_state.requires_operator_attention")

    gating_mirror = str(sys_s.get("gating_posture_observation", "") or "")
    pol_summary = str(ps.get("summary", "") or "")
    if gating_mirror and pol_summary and gating_mirror != pol_summary:
        consistency_notes.append(
            "system_state.gating_posture_observation does not match policy_state.summary "
            "at aggregate time (observation only)."
        )

    # Priority: blocking > degraded > caution > nominal
    status: str
    summary: str
    observation_reason: Optional[str] = None

    if kill_switch_active or blocked:
        status = _STATUS_BLOCKING
        summary = (
            "Policy and incident rollups indicate a blocked or kill-switch-active posture "
            "(cockpit observation only; not an approval or unlock)."
        )
    elif inc_degraded or stale_summary == "stale" or dep_summary == "degraded":
        status = _STATUS_DEGRADED
        summary = (
            "Incident, stale, or dependency rollups indicate a degraded observation posture "
            "(read-only aggregate; not broker truth)."
        )
    elif incident_stop:
        status = _STATUS_CAUTION
        summary = (
            "Incident stop signal is present in the payload rollups "
            "(observation only; verify authoritative controls outside this page)."
        )
    elif req_att:
        status = _STATUS_CAUTION
        summary = (
            "Operator attention is flagged in incident rollups "
            "(observation only; not a go/no-go approval)."
        )
    else:
        status = _STATUS_NOMINAL
        summary = (
            "No blocking, degraded, or stop signals in this aggregate snapshot "
            "(observation only; not an all-clear or live permission)."
        )

    if not contributing and status == _STATUS_NOMINAL:
        contributing.extend(
            [
                "policy_state.summary",
                "guard_state.deny_by_default",
                "incident_state.summary",
            ]
        )

    out: Dict[str, Any] = {
        "status": status,
        "summary": summary,
        "data_source": "cockpit_payload_aggregate",
        "provenance": {
            "builder": "build_safety_posture_observation",
            "reader_schema_version": READER_SCHEMA_VERSION,
        },
        "observation_reason": observation_reason,
        "consistency_notes": consistency_notes,
        "contributing_signals": sorted(set(contributing)),
        "reader_schema_version": READER_SCHEMA_VERSION,
    }
    return out
