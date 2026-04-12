"""
Evidence / audit **observation** aggregate for the Ops Cockpit payload.

Uses **primarily** ``evidence_state`` rollups already in the cockpit payload. Optional
``truth_status``, ``freshness_status``, and nested ``executive_summary`` fragments are used only for
**consistency notes**, not to re-score service health — that remains ``health_drift_observation``.

**Observation only** — not audit clearance, not compliance pass/fail, not approval, not unlock,
not broker truth, **not** a substitute for governance review.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional

READER_SCHEMA_VERSION = "evidence_audit_observation/v0"

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


def build_evidence_audit_observation(
    *,
    evidence_state: Mapping[str, Any],
    truth_status: Optional[str] = None,
    freshness_status: Optional[str] = None,
    executive_summary: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Roll up an **evidence/audit** observation from ``evidence_state`` only for status selection.

    Cross-field hints appear in ``consistency_notes``; they do not replace
    ``build_health_drift_observation``.
    """
    ev = _as_dict(evidence_state)
    consistency_notes: List[str] = []
    contributing: List[str] = []

    if ev is None:
        return {
            "status": _STATUS_UNKNOWN,
            "summary": "Insufficient structured evidence_state for evidence/audit observation (read-only).",
            "data_source": "cockpit_payload_aggregate",
            "provenance": {
                "builder": "build_evidence_audit_observation",
                "reader_schema_version": READER_SCHEMA_VERSION,
            },
            "observation_reason": "missing_required_state_dict",
            "consistency_notes": [],
            "contributing_signals": [],
            "reader_schema_version": READER_SCHEMA_VERSION,
        }

    s_sum = _norm(ev.get("summary"))
    s_fs = _norm(ev.get("freshness_status"))
    audit = _norm(ev.get("audit_trail"))
    tel_ev = _norm(ev.get("telemetry_evidence")) if "telemetry_evidence" in ev else ""

    sf_raw = ev.get("source_freshness")
    stale_dominant = False
    if isinstance(sf_raw, dict):
        try:
            fr = int(sf_raw.get("fresh") or 0)
            st = int(sf_raw.get("stale") or 0)
            stale_dominant = st > fr and st > 0
        except (TypeError, ValueError):
            pass

    ts_top = _norm(truth_status) if truth_status is not None else ""
    fs_top = _norm(freshness_status) if freshness_status is not None else ""
    if fs_top and s_fs and fs_top != s_fs:
        consistency_notes.append(
            "Top-level freshness_status differs from evidence_state.freshness_status in this snapshot "
            "(observation only; health/drift rollup remains in health_drift_observation)."
        )

    if executive_summary is not None and isinstance(executive_summary, dict):
        t_obj = executive_summary.get("truth_status")
        if isinstance(t_obj, dict):
            nested = _norm(t_obj.get("level"))
            if nested and ts_top and nested != ts_top:
                consistency_notes.append(
                    "executive_summary.truth_status.level differs from top-level truth_status "
                    "(observation only)."
                )

    degraded = audit == "broken" or s_fs == "critical" or s_sum == "stale"
    caution = not degraded and (
        audit == "degraded"
        or s_fs == "warn"
        or s_sum in ("partial", "unknown")
        or tel_ev in ("warn", "critical")
        or stale_dominant
    )

    status: str
    summary: str
    observation_reason: Optional[str] = None

    if degraded:
        status = _STATUS_DEGRADED
        summary = (
            "Evidence and audit-trail rollups in this snapshot show elevated signals "
            "(read-only; not audit clearance, not compliance pass/fail, not live evidence truth)."
        )
        if audit == "broken":
            contributing.append("evidence_state.audit_trail")
        if s_fs == "critical":
            contributing.append("evidence_state.freshness_status")
        if s_sum == "stale":
            contributing.append("evidence_state.summary")
    elif caution:
        status = _STATUS_CAUTION
        summary = (
            "Partial or warning-level evidence/audit signals in this aggregate "
            "(observation only). For service/drift posture, see health_drift_observation — "
            "not a duplicate verdict."
        )
        if audit == "degraded":
            contributing.append("evidence_state.audit_trail")
        if s_fs == "warn":
            contributing.append("evidence_state.freshness_status")
        if s_sum in ("partial", "unknown"):
            contributing.append("evidence_state.summary")
        if tel_ev:
            contributing.append("evidence_state.telemetry_evidence")
        if stale_dominant:
            contributing.append("evidence_state.source_freshness")
    else:
        status = _STATUS_NOMINAL
        summary = (
            "Evidence and audit rollups show no elevated observation flags in this aggregate "
            "(read-only; not an all-clear against external obligations). "
            "Health/drift remains scoped to health_drift_observation."
        )
        contributing.extend(
            [
                "evidence_state.summary",
                "evidence_state.audit_trail",
                "evidence_state.freshness_status",
            ]
        )

    out: Dict[str, Any] = {
        "status": status,
        "summary": summary,
        "data_source": "cockpit_payload_aggregate",
        "provenance": {
            "builder": "build_evidence_audit_observation",
            "reader_schema_version": READER_SCHEMA_VERSION,
        },
        "observation_reason": observation_reason,
        "consistency_notes": consistency_notes,
        "contributing_signals": sorted(set(contributing)),
        "reader_schema_version": READER_SCHEMA_VERSION,
    }
    return out
