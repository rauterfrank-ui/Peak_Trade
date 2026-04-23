# src/trading/master_v2/decision_packet_snapshot_v1.py
from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, cast

from .decision_packet_v1 import (
    DoubleplayResolutionHandoffV1,
    MasterV2DecisionPacketV1,
    RiskExposureCapHandoffV1,
    SafetyKillSwitchHandoffV1,
    ScopeCapitalEnvelopeHandoffV1,
    UniverseSelectionHandoffV1,
    validate_master_v2_decision_packet_v1,
)
from .staged_execution_enablement_v1 import (
    ExecutionStageV1,
    StagedExecutionEnablementInputV1,
)

DECISION_PACKET_SNAPSHOT_LAYER_VERSION = "v1"
_SNAP_VERSION_KEY = "snapshot_layer_version"


def _staged_in(d: Mapping[str, Any]) -> StagedExecutionEnablementInputV1:
    return StagedExecutionEnablementInputV1(
        current_stage=ExecutionStageV1(d["current_stage"]),
        requested_stage=ExecutionStageV1(d["requested_stage"]),
        safety_decision_allowed=bool(d["safety_decision_allowed"]),
        live_authority_acknowledged=bool(d.get("live_authority_acknowledged", False)),
    )


def _staged_out(s: StagedExecutionEnablementInputV1) -> Dict[str, Any]:
    return {
        "current_stage": s.current_stage.value,
        "requested_stage": s.requested_stage.value,
        "safety_decision_allowed": s.safety_decision_allowed,
        "live_authority_acknowledged": s.live_authority_acknowledged,
    }


def _uni_in(d: Optional[Mapping[str, Any]]) -> Optional[UniverseSelectionHandoffV1]:
    if d is None:
        return None
    return UniverseSelectionHandoffV1(
        layer_version=d["layer_version"],
        symbols=tuple(d.get("symbols", ())),
    )


def _uni_out(h: Optional[UniverseSelectionHandoffV1]) -> Optional[Dict[str, Any]]:
    if h is None:
        return None
    return {
        "layer_version": h.layer_version,
        "symbols": list(h.symbols),
    }


def _dp_in(d: Optional[Mapping[str, Any]]) -> Optional[DoubleplayResolutionHandoffV1]:
    if d is None:
        return None
    return DoubleplayResolutionHandoffV1(
        layer_version=d["layer_version"],
        resolution=str(d.get("resolution", "")),
    )


def _dp_out(h: Optional[DoubleplayResolutionHandoffV1]) -> Optional[Dict[str, Any]]:
    if h is None:
        return None
    return {"layer_version": h.layer_version, "resolution": h.resolution}


def _scope_in(d: Optional[Mapping[str, Any]]) -> Optional[ScopeCapitalEnvelopeHandoffV1]:
    if d is None:
        return None
    return ScopeCapitalEnvelopeHandoffV1(
        layer_version=d["layer_version"],
        within_envelope=bool(d.get("within_envelope", True)),
    )


def _scope_out(h: Optional[ScopeCapitalEnvelopeHandoffV1]) -> Optional[Dict[str, Any]]:
    if h is None:
        return None
    return {"layer_version": h.layer_version, "within_envelope": h.within_envelope}


def _risk_in(d: Optional[Mapping[str, Any]]) -> Optional[RiskExposureCapHandoffV1]:
    if d is None:
        return None
    return RiskExposureCapHandoffV1(
        layer_version=d["layer_version"],
        cap_satisfied=bool(d.get("cap_satisfied", True)),
    )


def _risk_out(h: Optional[RiskExposureCapHandoffV1]) -> Optional[Dict[str, Any]]:
    if h is None:
        return None
    return {"layer_version": h.layer_version, "cap_satisfied": h.cap_satisfied}


def _safety_in(d: Optional[Mapping[str, Any]]) -> Optional[SafetyKillSwitchHandoffV1]:
    if d is None:
        return None
    return SafetyKillSwitchHandoffV1(
        layer_version=d["layer_version"],
        safety_decision_allowed=bool(d.get("safety_decision_allowed", False)),
    )


def _safety_out(h: Optional[SafetyKillSwitchHandoffV1]) -> Optional[Dict[str, Any]]:
    if h is None:
        return None
    return {
        "layer_version": h.layer_version,
        "safety_decision_allowed": h.safety_decision_allowed,
    }


def decision_packet_to_snapshot_v1(
    p: MasterV2DecisionPacketV1, *, require_consistent_packet: bool = True
) -> Dict[str, Any]:
    if require_consistent_packet:
        v = validate_master_v2_decision_packet_v1(p)
        if not v.ok:
            raise ValueError("packet does not validate; snapshot refused")
    return {
        _SNAP_VERSION_KEY: DECISION_PACKET_SNAPSHOT_LAYER_VERSION,
        "layer_version": p.layer_version,
        "correlation_id": p.correlation_id,
        "staged": _staged_out(p.staged),
        "universe": _uni_out(p.universe),
        "doubleplay": _dp_out(p.doubleplay),
        "scope_envelope": _scope_out(p.scope_envelope),
        "risk_cap": _risk_out(p.risk_cap),
        "safety": _safety_out(p.safety),
    }


def decision_packet_from_snapshot_v1(
    snapshot: Mapping[str, Any],
) -> MasterV2DecisionPacketV1:
    d = {k: v for k, v in snapshot.items() if k != _SNAP_VERSION_KEY}
    u = d.get("universe")
    p = d.get("doubleplay")
    se = d.get("scope_envelope")
    r = d.get("risk_cap")
    sa = d.get("safety")
    return MasterV2DecisionPacketV1(
        layer_version=str(d["layer_version"]),
        correlation_id=str(d["correlation_id"]),
        staged=_staged_in(cast(Mapping[str, Any], d["staged"])),
        universe=_uni_in(cast(Optional[Mapping[str, Any]], u)),
        doubleplay=_dp_in(cast(Optional[Mapping[str, Any]], p)),
        scope_envelope=_scope_in(cast(Optional[Mapping[str, Any]], se)),
        risk_cap=_risk_in(cast(Optional[Mapping[str, Any]], r)),
        safety=_safety_in(cast(Optional[Mapping[str, Any]], sa)),
    )


def validate_decision_packet_snapshot_v1(snapshot: Mapping[str, Any]) -> None:
    if _SNAP_VERSION_KEY not in snapshot:
        raise ValueError("missing snapshot version")
    if snapshot[_SNAP_VERSION_KEY] != DECISION_PACKET_SNAPSHOT_LAYER_VERSION:
        raise ValueError("snapshot version mismatch")
    p = decision_packet_from_snapshot_v1(dict(snapshot))
    v = validate_master_v2_decision_packet_v1(p)
    if not v.ok:
        raise ValueError("snapshot does not re-validate", list(v.reason_codes))
