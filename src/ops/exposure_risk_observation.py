"""
Exposure / risk **observation** aggregate for the Ops Cockpit payload.

Uses only caller-supplied cockpit rollups (``exposure_state``, ``transfer_ambiguity_state``,
``stale_state``, ``guard_state`` treasury mirror). **Observation only** — not approval, not unlock,
not broker truth, **not** a position or risk gate clearance.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional

READER_SCHEMA_VERSION = "exposure_risk_observation/v0"

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


def build_exposure_risk_observation(
    *,
    exposure_state: Mapping[str, Any],
    transfer_ambiguity_state: Mapping[str, Any],
    stale_state: Mapping[str, Any],
    guard_state: Mapping[str, Any],
) -> Dict[str, Any]:
    """
    Roll up a single **observation** status from existing exposure/risk-related payload fields.
    """
    exp = _as_dict(exposure_state)
    ta = _as_dict(transfer_ambiguity_state)
    st = _as_dict(stale_state)
    gd = _as_dict(guard_state)
    consistency_notes: List[str] = []
    contributing: List[str] = []

    if exp is None or ta is None or st is None or gd is None:
        return {
            "status": _STATUS_UNKNOWN,
            "summary": "Insufficient structured payload objects for exposure/risk observation (read-only).",
            "data_source": "cockpit_payload_aggregate",
            "provenance": {
                "builder": "build_exposure_risk_observation",
                "reader_schema_version": READER_SCHEMA_VERSION,
            },
            "observation_reason": "missing_required_state_dict",
            "consistency_notes": [],
            "contributing_signals": [],
            "reader_schema_version": READER_SCHEMA_VERSION,
        }

    g_treas = _norm(gd.get("treasury_separation"))
    e_treas = _norm(exp.get("treasury_separation"))
    if g_treas and e_treas and g_treas != e_treas:
        consistency_notes.append(
            "treasury_separation differs between guard_state and exposure_state (observation only)."
        )

    risk = _norm(exp.get("risk_status"))
    ta_status = _norm(ta.get("status"))
    exp_sum = _norm(exp.get("summary"))
    data_src = str(exp.get("data_source") or "")
    stale_flag = exp.get("stale")
    stale_exp = _norm(st.get("exposure"))
    op_hint = bool(ta.get("operator_attention_hint"))

    degraded = (
        risk == "critical" or ta_status == "warning" or stale_flag is True or stale_exp == "stale"
    )

    empty_local_exposure_surface = (
        exp_sum == "no_live_context" and risk == "unknown" and stale_flag is not True
    )

    caution = (
        risk == "warn"
        or op_hint
        or (ta_status == "unknown" and not empty_local_exposure_surface)
        or (exp_sum == "unknown" and data_src == "live_runs")
    )

    status: str
    summary: str
    observation_reason: Optional[str] = None

    if degraded:
        status = _STATUS_DEGRADED
        summary = (
            "Exposure, stale, or transfer/treasury ambiguity rollups indicate an elevated "
            "observation posture in this snapshot (read-only; not broker truth or risk approval)."
        )
        if risk == "critical":
            contributing.append("exposure_state.risk_status")
        if ta_status == "warning":
            contributing.append("transfer_ambiguity_state.status")
        if stale_flag is True:
            contributing.append("exposure_state.stale")
        if stale_exp == "stale":
            contributing.append("stale_state.exposure")
    elif empty_local_exposure_surface and not op_hint:
        status = _STATUS_NOMINAL
        summary = (
            "Default local exposure surface with no elevated risk signals in this aggregate "
            "(observation only; not an all-clear against external or exchange state)."
        )
        contributing.extend(
            [
                "exposure_state.summary",
                "transfer_ambiguity_state.status",
            ]
        )
    elif caution:
        status = _STATUS_CAUTION
        summary = (
            "Partial coverage, warnings, or operator hints in exposure and treasury rollups "
            "(observation only; not a position or limit approval)."
        )
        if risk == "warn":
            contributing.append("exposure_state.risk_status")
        if op_hint:
            contributing.append("transfer_ambiguity_state.operator_attention_hint")
        if ta_status == "unknown":
            contributing.append("transfer_ambiguity_state.status")
        if exp_sum == "unknown" and data_src == "live_runs":
            contributing.append("exposure_state.summary")
    else:
        status = _STATUS_NOMINAL
        summary = (
            "Exposure and treasury rollups show no elevated observation signals in this snapshot "
            "(observation only; not live net exposure truth)."
        )
        contributing.extend(
            [
                "exposure_state.risk_status",
                "exposure_state.treasury_separation",
                "transfer_ambiguity_state.status",
            ]
        )

    out: Dict[str, Any] = {
        "status": status,
        "summary": summary,
        "data_source": "cockpit_payload_aggregate",
        "provenance": {
            "builder": "build_exposure_risk_observation",
            "reader_schema_version": READER_SCHEMA_VERSION,
        },
        "observation_reason": observation_reason,
        "consistency_notes": consistency_notes,
        "contributing_signals": sorted(set(contributing)),
        "reader_schema_version": READER_SCHEMA_VERSION,
    }
    return out
