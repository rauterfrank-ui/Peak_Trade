"""
Policy / go–no-go **observation** aggregate for the Ops Cockpit payload.

Uses only ``policy_state``, ``incident_state``, and ``operator_state`` rollups already present in the
cockpit build. This is the vNext **Go / No-Go** lens (policy outcome, blockers, escalation cues) —
**not** the holistic safety/gating posture (see ``safety_posture_observation``), not incident+deps
focus (see ``incident_safety_observation``), and **not** governance/AI boundary (see
``governance_boundary_observation``).

**Observation only** — not approval, not unlock, not broker truth, not a live operational go
decision, not a substitute for ``src/governance/go_no_go.py`` or external governance.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional

READER_SCHEMA_VERSION = "policy_go_no_go_observation/v0"

_STATUS_BLOCKING = "blocking"
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


def build_policy_go_no_go_observation(
    *,
    policy_state: Mapping[str, Any],
    incident_state: Mapping[str, Any],
    operator_state: Mapping[str, Any],
) -> Dict[str, Any]:
    """
    Roll up a **policy / go–no-go** observation from cockpit payload fields (read-only).
    """
    ps = _as_dict(policy_state)
    inc = _as_dict(incident_state)
    op = _as_dict(operator_state)

    consistency_notes: List[str] = []
    contributing: List[str] = []

    if ps is None or inc is None or op is None:
        return {
            "status": _STATUS_UNKNOWN,
            "summary": "Insufficient structured payload objects for policy/go-no-go observation (read-only).",
            "data_source": "cockpit_payload_aggregate",
            "provenance": {
                "builder": "build_policy_go_no_go_observation",
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
    kill_any = ks_ps or ks_inc or ks_op

    blocked = bool(ps.get("blocked"))
    action = _norm(ps.get("action"))
    pol_summary = _norm(ps.get("summary"))

    inc_deg = bool(inc.get("degraded"))
    req_att = bool(inc.get("requires_operator_attention"))
    inc_sum = _norm(inc.get("summary"))
    inc_stat = _norm(inc.get("status"))

    ep_raw = inc.get("entry_permitted")
    ep = _boolish(ep_raw)
    if ep_raw is not None and ep is None:
        consistency_notes.append(
            "entry_permitted present but not interpretable as boolean (observation only)."
        )
    elif ep is not None:
        expected = not blocked
        if ep != expected:
            consistency_notes.append(
                "entry_permitted does not align with policy_state.blocked in this snapshot "
                "(observation only; verify authoritative controls outside this page)."
            )

    if kill_any:
        contributing.append("policy_state.kill_switch_active")
        contributing.append("incident_state.kill_switch_active")
    if blocked:
        contributing.append("policy_state.blocked")
    if inc_deg:
        contributing.append("incident_state.degraded")
    if req_att:
        contributing.append("incident_state.requires_operator_attention")

    no_go_style = (
        kill_any
        or blocked
        or action in ("no_trade", "no-go", "no_go")
        or inc_stat in ("blocked",)
        or inc_sum in ("blocked",)
    )

    status: str
    summary: str
    observation_reason: Optional[str] = None

    if no_go_style:
        status = _STATUS_BLOCKING
        summary = (
            "Policy and incident rollups in this snapshot read as a no-go style posture "
            "(cockpit observation only; not a live go decision, not an approval or unlock)."
        )
    elif inc_deg:
        status = _STATUS_DEGRADED
        summary = (
            "Incident rollup flags degraded signals while policy fields are not in a blocked "
            "posture in this aggregate (read-only; not broker truth, not an all-clear)."
        )
    elif req_att:
        status = _STATUS_CAUTION
        summary = (
            "Operator attention is flagged in incident rollups for this go/no-go lens "
            "(observation only; holistic posture remains in safety_posture_observation)."
        )
    elif action and action not in ("trade_ready", "unknown") and "trade" not in action:
        status = _STATUS_CAUTION
        summary = (
            "policy_state.action uses an unexpected label in this snapshot "
            "(observation only; not a governance verdict)."
        )
        observation_reason = "unexpected_policy_action_label"
        contributing.append("policy_state.action")
    elif not action or action == "unknown":
        status = _STATUS_CAUTION
        summary = "policy_state.action is missing or unknown in this aggregate (observation only)."
        observation_reason = "ambiguous_policy_action"
    else:
        status = _STATUS_NOMINAL
        summary = (
            "Policy and incident rollups show no blockers in this aggregate for the go/no-go lens "
            "(read-only; not an approval, not live permission, not a substitute for external "
            "governance)."
        )
        contributing.extend(
            [
                "policy_state.action",
                "policy_state.blocked",
                "incident_state.summary",
            ]
        )

    if pol_summary and pol_summary not in ("blocked", "armed", "normal", "unknown", ""):
        consistency_notes.append(
            "policy_state.summary has a non-standard value in this snapshot (observation only)."
        )

    out: Dict[str, Any] = {
        "status": status,
        "summary": summary,
        "data_source": "cockpit_payload_aggregate",
        "provenance": {
            "builder": "build_policy_go_no_go_observation",
            "reader_schema_version": READER_SCHEMA_VERSION,
        },
        "observation_reason": observation_reason,
        "consistency_notes": consistency_notes,
        "contributing_signals": sorted(set(contributing)),
        "reader_schema_version": READER_SCHEMA_VERSION,
    }
    return out
