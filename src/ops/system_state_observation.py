"""
System / environment **observation** aggregate for the Ops Cockpit payload.

Uses only ``system_state`` rollups already in the cockpit build, with an optional **consistency
check** against ``policy_state.summary`` when ``policy_state`` is supplied (same mirror rule as
``safety_posture_observation``). This is **not** service health or evidence freshness (see
``health_drift_observation``), not holistic gating (see ``safety_posture_observation``), and not
policy outcome / go–no-go (see ``policy_go_no_go_observation``).

**Observation only** — not approval, not unlock, not broker or exchange truth, not an environment
runtime guarantee.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional

READER_SCHEMA_VERSION = "system_state_observation/v0"

_KNOWN_CONFIG_LOAD = frozenset({"not_loaded", "loaded", "unavailable"})

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


def build_system_state_observation(
    *,
    system_state: Optional[Mapping[str, Any]],
    policy_state: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Roll up a **system / environment** observation from cockpit ``system_state`` (read-only).
    """
    sys_s = _as_dict(system_state)
    ps = _as_dict(policy_state) if policy_state is not None else None

    consistency_notes: List[str] = []
    contributing: List[str] = []

    if sys_s is None:
        return {
            "status": _STATUS_UNKNOWN,
            "summary": "Insufficient structured system_state object for system/environment observation (read-only).",
            "data_source": "cockpit_payload_aggregate",
            "provenance": {
                "builder": "build_system_state_observation",
                "reader_schema_version": READER_SCHEMA_VERSION,
            },
            "observation_reason": "missing_system_state_dict",
            "consistency_notes": [],
            "contributing_signals": [],
            "reader_schema_version": READER_SCHEMA_VERSION,
        }

    cfg = _norm(sys_s.get("config_load_status"))
    env = _norm(sys_s.get("environment"))
    mode = str(sys_s.get("mode") or "").strip()
    exec_m = str(sys_s.get("execution_model") or "").strip()
    gating_mirror = str(sys_s.get("gating_posture_observation") or "").strip()
    pol_summary = str(ps.get("summary") or "").strip() if ps is not None else ""

    if cfg:
        contributing.append("system_state.config_load_status")
    if env:
        contributing.append("system_state.environment")
    if mode:
        contributing.append("system_state.mode")
    if exec_m:
        contributing.append("system_state.execution_model")

    if (
        ps is not None
        and gating_mirror
        and pol_summary
        and _norm(gating_mirror) != _norm(pol_summary)
    ):
        consistency_notes.append(
            "system_state.gating_posture_observation does not match policy_state.summary at "
            "aggregate time (observation only; go/no-go lens: policy_go_no_go_observation; "
            "holistic gating: safety_posture_observation)."
        )

    gating_mismatch_only = len(consistency_notes) == 1 and any(
        "gating_posture_observation does not match" in n for n in consistency_notes
    )

    status: str
    summary: str
    observation_reason: Optional[str] = None

    if cfg and cfg not in _KNOWN_CONFIG_LOAD:
        status = _STATUS_CAUTION
        summary = (
            "system_state.config_load_status uses an unexpected label in this aggregate "
            "(read-only; not broker truth)."
        )
        observation_reason = "unexpected_config_load_status"
    elif cfg == "unavailable":
        status = _STATUS_DEGRADED
        summary = (
            "Config load failed in this snapshot; system/environment labels may be incomplete "
            "(read-only; not a broker guarantee, not an approval)."
        )
        observation_reason = "config_load_unavailable"
    elif cfg == "not_loaded":
        status = _STATUS_CAUTION
        summary = (
            "Config was not loaded for environment observation in this aggregate "
            "(read-only; trading environment remains unknown here — not exchange truth)."
        )
        observation_reason = "config_not_loaded"
    elif env in ("", "unknown"):
        status = _STATUS_CAUTION
        summary = (
            "Trading environment label is unknown in this aggregate while other system fields are "
            "present (observation only; not a runtime environment guarantee)."
        )
        observation_reason = "environment_unknown"
    elif not mode or not exec_m:
        status = _STATUS_CAUTION
        summary = (
            "system_state.mode or system_state.execution_model is missing in this aggregate "
            "(observation only)."
        )
        observation_reason = "missing_mode_or_execution_model"
    elif gating_mismatch_only:
        status = _STATUS_CAUTION
        summary = (
            "System mirror fields disagree with policy summary in this snapshot "
            "(read-only; verify authoritative controls outside this page)."
        )
        observation_reason = "gating_mirror_mismatch"
    else:
        status = _STATUS_NOMINAL
        summary = (
            "System and environment rollups in this aggregate are internally consistent for the "
            "cockpit snapshot (read-only; not broker truth, not compliance clearance)."
        )

    bp = sys_s.get("bounded_pilot_mode")
    if bp is True:
        consistency_notes.append(
            "bounded_pilot_mode is true in system_state when config loaded (observation only; "
            "policy/go-no-go: policy_go_no_go_observation)."
        )

    out: Dict[str, Any] = {
        "status": status,
        "summary": summary,
        "data_source": "cockpit_payload_aggregate",
        "provenance": {
            "builder": "build_system_state_observation",
            "reader_schema_version": READER_SCHEMA_VERSION,
        },
        "observation_reason": observation_reason,
        "consistency_notes": consistency_notes,
        "contributing_signals": sorted(set(contributing)),
        "reader_schema_version": READER_SCHEMA_VERSION,
    }
    return out
