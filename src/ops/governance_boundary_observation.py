"""
Governance / AI boundary **observation** aggregate for the Ops Cockpit payload.

Uses ``ai_boundary_state`` and ``human_supervision_state`` rollups. Optional ``guard_state`` and
``evidence_state`` appear only in **consistency notes** — not a second safety gate (see
``safety_posture_observation``) and not an evidence verdict (see ``evidence_audit_observation``).

**Observation only** — not governance approval, not AI clearance, not supervision waiver, not unlock,
not broker truth.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Tuple

READER_SCHEMA_VERSION = "governance_boundary_observation/v0"

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


def _ai_keys() -> Tuple[str, ...]:
    return (
        "proposer_authority",
        "critic_authority",
        "provider_binding_authority",
        "execution_boundary",
        "closest_to_trade",
    )


_BAD_AI_VALUES = frozenset(
    {
        "execution_authority",
        "live_execution",
        "llm_final",
        "llm_final_trade",
    }
)


def build_governance_boundary_observation(
    *,
    ai_boundary_state: Mapping[str, Any],
    human_supervision_state: Mapping[str, Any],
    guard_state: Optional[Mapping[str, Any]] = None,
    evidence_state: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Roll up a **governance / AI boundary** observation from cockpit payload fields.
    """
    ai = _as_dict(ai_boundary_state)
    hs = _as_dict(human_supervision_state)
    gd = _as_dict(guard_state) if guard_state is not None else None
    ev = _as_dict(evidence_state) if evidence_state is not None else None

    consistency_notes: List[str] = []
    contributing: List[str] = []

    if ai is None or hs is None:
        return {
            "status": _STATUS_UNKNOWN,
            "summary": "Insufficient structured payload objects for governance/boundary observation (read-only).",
            "data_source": "cockpit_payload_aggregate",
            "provenance": {
                "builder": "build_governance_boundary_observation",
                "reader_schema_version": READER_SCHEMA_VERSION,
            },
            "observation_reason": "missing_required_state_dict",
            "consistency_notes": [],
            "contributing_signals": [],
            "reader_schema_version": READER_SCHEMA_VERSION,
        }

    if gd is not None and _norm(gd.get("deny_by_default")) not in ("", "active"):
        consistency_notes.append(
            "guard_state.deny_by_default is not active in this snapshot (observation only; "
            "holistic gating remains in safety_posture_observation)."
        )

    if ev is not None:
        es = _norm(ev.get("summary"))
        if es in ("stale", "partial"):
            consistency_notes.append(
                "evidence_state.summary is partial or stale while interpreting AI boundary labels "
                "(observation only; evidence focus remains in evidence_audit_observation)."
            )

    hs_status = _norm(hs.get("status"))
    hs_mode = _norm(hs.get("mode"))
    hs_sum = str(hs.get("summary") or "").strip()

    degraded = False
    for key in _ai_keys():
        val = _norm(ai.get(key))
        if val in _BAD_AI_VALUES:
            degraded = True
            contributing.append(f"ai_boundary_state.{key}")
    if hs_status in ("unsupervised", "not_supervised", "none"):
        degraded = True
        contributing.append("human_supervision_state.status")

    missing_ai = any(str(ai.get(k) or "").strip() == "" for k in _ai_keys())
    unknown_ai = any(_norm(ai.get(k)) == "unknown" for k in _ai_keys())
    missing_hs = not hs_sum

    caution = not degraded and (missing_ai or unknown_ai or missing_hs or hs_mode == "unknown")
    if not degraded and hs_status == "operator_supervised" and not _norm(hs.get("mode")):
        caution = True

    status: str
    summary: str
    observation_reason: Optional[str] = None

    if degraded:
        status = _STATUS_DEGRADED
        summary = (
            "AI boundary or supervision rollups show elevated signals in this snapshot "
            "(read-only; not governance approval, not an AI clearance, not a supervision waiver)."
        )
    elif caution:
        status = _STATUS_CAUTION
        summary = (
            "Partial or ambiguous AI boundary or supervision fields in this aggregate "
            "(observation only). Gating posture: safety_posture_observation; evidence trail: "
            "evidence_audit_observation — separate snapshots."
        )
        if missing_ai or unknown_ai:
            contributing.append("ai_boundary_state.*")
        if missing_hs or hs_mode == "unknown":
            contributing.append("human_supervision_state")
    else:
        status = _STATUS_NOMINAL
        summary = (
            "AI boundary and human supervision rollups present expected advisory/supervisory labels "
            "in this aggregate (read-only; not policy approval, not model certification)."
        )
        contributing.extend(
            [
                "ai_boundary_state.execution_boundary",
                "human_supervision_state.status",
            ]
        )

    out: Dict[str, Any] = {
        "status": status,
        "summary": summary,
        "data_source": "cockpit_payload_aggregate",
        "provenance": {
            "builder": "build_governance_boundary_observation",
            "reader_schema_version": READER_SCHEMA_VERSION,
        },
        "observation_reason": observation_reason,
        "consistency_notes": consistency_notes,
        "contributing_signals": sorted(set(contributing)),
        "reader_schema_version": READER_SCHEMA_VERSION,
    }
    return out
