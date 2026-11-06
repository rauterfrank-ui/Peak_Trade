"""
Health / drift **observation** aggregate for the Ops Cockpit payload.

Uses only caller-supplied cockpit rollups (top-level truth/freshness/coverage, flags,
``evidence_state``, ``dependencies_state``, ``stale_state``, optional nested
``executive_summary`` for consistency notes). **Observation only** — not approval, not unlock,
not broker truth, **not** a live service health guarantee.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional

READER_SCHEMA_VERSION = "health_drift_observation/v0"

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


def _as_str_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x) for x in value]
    return []


def _norm_level(value: Any) -> str:
    return str(value or "").strip().lower()


def build_health_drift_observation(
    *,
    truth_status: str,
    freshness_status: str,
    source_coverage_status: str,
    critical_flags: Any,
    unknown_flags: Any,
    evidence_state: Mapping[str, Any],
    dependencies_state: Mapping[str, Any],
    stale_state: Mapping[str, Any],
    executive_summary: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Roll up a single **observation** status from existing health/drift-related payload fields.
    """
    ev = _as_dict(evidence_state)
    dep = _as_dict(dependencies_state)
    st = _as_dict(stale_state)
    consistency_notes: List[str] = []
    contributing: List[str] = []

    if ev is None or dep is None or st is None:
        return {
            "status": _STATUS_UNKNOWN,
            "summary": "Insufficient structured payload objects for health/drift observation (read-only).",
            "data_source": "cockpit_payload_aggregate",
            "provenance": {
                "builder": "build_health_drift_observation",
                "reader_schema_version": READER_SCHEMA_VERSION,
            },
            "observation_reason": "missing_required_state_dict",
            "consistency_notes": [],
            "contributing_signals": [],
            "reader_schema_version": READER_SCHEMA_VERSION,
        }

    ts = _norm_level(truth_status)
    fs = _norm_level(freshness_status)
    sc = _norm_level(source_coverage_status)
    crit = _as_str_list(critical_flags)
    unk = _as_str_list(unknown_flags)

    if executive_summary is not None and isinstance(executive_summary, dict):
        t_obj = executive_summary.get("truth_status")
        if isinstance(t_obj, dict):
            nested = _norm_level(t_obj.get("level"))
            if nested and nested != ts:
                consistency_notes.append(
                    "executive_summary.truth_status.level differs from top-level truth_status "
                    "(observation only)."
                )

    ev_sum = _norm_level(ev.get("summary"))
    ev_fs = _norm_level(ev.get("freshness_status"))
    audit = _norm_level(ev.get("audit_trail"))
    dep_sum = _norm_level(dep.get("summary"))
    tel = _norm_level(dep.get("telemetry"))
    stale_sum = _norm_level(st.get("summary"))

    degraded_hint = (
        ts == "critical"
        or fs == "critical"
        or sc == "critical"
        or stale_sum == "stale"
        or dep_sum == "degraded"
        or audit == "broken"
        or ev_fs == "critical"
    )
    caution_hint = (
        ts == "warn"
        or fs == "warn"
        or sc == "warn"
        or sc == "partial"
        or ev_sum in ("partial", "stale")
        or ev_fs == "warn"
        or audit == "degraded"
        or dep_sum == "partial"
        or tel in ("warn", "critical")
        or bool(crit)
        or bool(unk)
    )

    status: str
    summary: str
    observation_reason: Optional[str] = None

    if degraded_hint:
        status = _STATUS_DEGRADED
        summary = (
            "Truth, evidence, dependency, or stale rollups indicate a degraded drift posture "
            "in this snapshot (read-only aggregate; not live service health or broker truth)."
        )
        if ts == "critical":
            contributing.append("truth_status")
        if fs == "critical":
            contributing.append("freshness_status")
        if sc == "critical":
            contributing.append("source_coverage_status")
        if stale_sum == "stale":
            contributing.append("stale_state.summary")
        if dep_sum == "degraded":
            contributing.append("dependencies_state.summary")
        if audit == "broken":
            contributing.append("evidence_state.audit_trail")
        if ev_fs == "critical":
            contributing.append("evidence_state.freshness_status")
    elif caution_hint:
        status = _STATUS_CAUTION
        summary = (
            "Partial coverage, warnings, or flags in local rollups warrant attention "
            "(observation only; not an approval or all-clear)."
        )
        if ts == "warn":
            contributing.append("truth_status")
        if fs == "warn":
            contributing.append("freshness_status")
        if sc in ("warn", "partial"):
            contributing.append("source_coverage_status")
        if ev_sum in ("partial", "stale"):
            contributing.append("evidence_state.summary")
        if ev_fs == "warn":
            contributing.append("evidence_state.freshness_status")
        if audit == "degraded":
            contributing.append("evidence_state.audit_trail")
        if dep_sum == "partial":
            contributing.append("dependencies_state.summary")
        if tel in ("warn", "critical"):
            contributing.append("dependencies_state.telemetry")
        if crit:
            contributing.append("critical_flags")
        if unk:
            contributing.append("unknown_flags")
    else:
        status = _STATUS_NOMINAL
        summary = (
            "No elevated drift signals in this aggregate snapshot "
            "(observation only; not a health guarantee or live readiness proof)."
        )
        contributing.extend(
            [
                "truth_status",
                "freshness_status",
                "source_coverage_status",
                "evidence_state.summary",
            ]
        )

    out: Dict[str, Any] = {
        "status": status,
        "summary": summary,
        "data_source": "cockpit_payload_aggregate",
        "provenance": {
            "builder": "build_health_drift_observation",
            "reader_schema_version": READER_SCHEMA_VERSION,
        },
        "observation_reason": observation_reason,
        "consistency_notes": consistency_notes,
        "contributing_signals": sorted(set(contributing)) if contributing else [],
        "reader_schema_version": READER_SCHEMA_VERSION,
    }
    return out
