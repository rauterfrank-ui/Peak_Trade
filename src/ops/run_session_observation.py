"""
Run / session **observation** aggregate for the Ops Cockpit payload.

Uses only caller-supplied cockpit rollups (``run_state``, ``session_end_mismatch_state``,
``stale_state``, optional ``operator_state``). **Observation only** — not approval, not unlock,
not broker truth, not a guarantee that a session is safe to continue.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional

READER_SCHEMA_VERSION = "run_session_observation/v0"

_STATUS_ATTENTION = "attention"
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


def _run_freshness_degraded(run_state: Mapping[str, Any]) -> bool:
    fs = str(run_state.get("freshness_status", "") or "").lower()
    return fs in ("warn", "critical")


def build_run_session_observation(
    *,
    run_state: Mapping[str, Any],
    session_end_mismatch_state: Mapping[str, Any],
    stale_state: Optional[Mapping[str, Any]] = None,
    operator_state: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Roll up a single **observation** status from existing run/session-related payload fields.
    """
    rs = _as_dict(run_state)
    sem = _as_dict(session_end_mismatch_state)
    st = _as_dict(stale_state) if stale_state is not None else None
    op = _as_dict(operator_state) if operator_state is not None else None

    consistency_notes: List[str] = []
    contributing: List[str] = []

    if rs is None or sem is None:
        return {
            "status": _STATUS_UNKNOWN,
            "summary": "Insufficient structured payload objects for run/session observation (read-only).",
            "data_source": "cockpit_payload_aggregate",
            "provenance": {
                "builder": "build_run_session_observation",
                "reader_schema_version": READER_SCHEMA_VERSION,
            },
            "observation_reason": "missing_required_state_dict",
            "consistency_notes": [],
            "contributing_signals": [],
            "reader_schema_version": READER_SCHEMA_VERSION,
        }

    session_active = bool(rs.get("session_active"))
    sem_status = str(sem.get("status", "") or "").lower()
    blocked_next = bool(sem.get("blocked_next_session"))

    if session_active:
        contributing.append("run_state.session_active")
    contributing.append("run_state.status")
    contributing.append("session_end_mismatch_state.status")

    stale_summary = str(st.get("summary", "unknown") or "unknown") if st else "unknown"
    if stale_summary == "stale":
        contributing.append("stale_state.summary")

    if op is not None and session_active and bool(op.get("blocked")):
        consistency_notes.append(
            "run_state reports session activity while operator_state is blocked "
            "(observation only; not an enforcement decision)."
        )

    status: str
    summary: str
    observation_reason: Optional[str] = None

    if sem_status == "mismatch_signal" or blocked_next:
        status = _STATUS_ATTENTION
        summary = (
            "Session-end mismatch or next-session hint in local rollups suggests operator review "
            "of registry and run artifacts (observation only; not broker truth or unlock)."
        )
        if sem_status == "mismatch_signal":
            contributing.append("session_end_mismatch_state.mismatch_signal")
        if blocked_next:
            contributing.append("session_end_mismatch_state.blocked_next_session")
    elif sem_status == "ambiguous":
        status = _STATUS_CAUTION
        summary = (
            "Session-end alignment is ambiguous in local cross-checks "
            "(read-only aggregate; verify outside this page if needed)."
        )
        contributing.append("session_end_mismatch_state.ambiguous")
    elif stale_summary == "stale" or _run_freshness_degraded(rs):
        status = _STATUS_DEGRADED
        summary = (
            "Stale or freshness rollups indicate degraded run/session observation posture "
            "(not live connectivity or exchange session state)."
        )
        if _run_freshness_degraded(rs):
            contributing.append("run_state.freshness_status")
    elif sem_status in ("unknown", "no_signal") and session_active:
        status = _STATUS_CAUTION
        summary = (
            "Active session signal in run_state while session-end observation is limited "
            "(no_signal or unknown); not an all-clear (observation only)."
        )
        contributing.append("session_end_mismatch_state.limited_while_active")
    else:
        status = _STATUS_NOMINAL
        summary = (
            "Run and session rollups show no elevated mismatch or stale signals in this snapshot "
            "(observation only; not a session guarantee or approval)."
        )

    if not contributing and status == _STATUS_NOMINAL:
        contributing.extend(
            [
                "run_state.last_run_status",
                "session_end_mismatch_state.summary",
            ]
        )

    out: Dict[str, Any] = {
        "status": status,
        "summary": summary,
        "data_source": "cockpit_payload_aggregate",
        "provenance": {
            "builder": "build_run_session_observation",
            "reader_schema_version": READER_SCHEMA_VERSION,
        },
        "observation_reason": observation_reason,
        "consistency_notes": consistency_notes,
        "contributing_signals": sorted(set(contributing)),
        "reader_schema_version": READER_SCHEMA_VERSION,
    }
    return out
