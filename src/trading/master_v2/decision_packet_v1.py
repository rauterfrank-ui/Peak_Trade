# src/trading/master_v2/decision_packet_v1.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from .staged_execution_enablement_v1 import (
    ExecutionStageV1,
    StagedExecutionEnablementInputV1,
)

MASTER_V2_DECISION_PACKET_LAYER_VERSION = "v1"


@dataclass(frozen=True)
class UniverseSelectionHandoffV1:
    layer_version: str
    symbols: Tuple[str, ...] = ()


@dataclass(frozen=True)
class DoubleplayResolutionHandoffV1:
    layer_version: str
    resolution: str = "ok"


@dataclass(frozen=True)
class ScopeCapitalEnvelopeHandoffV1:
    layer_version: str
    within_envelope: bool = True


@dataclass(frozen=True)
class RiskExposureCapHandoffV1:
    layer_version: str
    cap_satisfied: bool


@dataclass(frozen=True)
class SafetyKillSwitchHandoffV1:
    layer_version: str
    safety_decision_allowed: bool


@dataclass(frozen=True)
class MasterV2DecisionPacketV1:
    layer_version: str
    correlation_id: str
    staged: StagedExecutionEnablementInputV1
    universe: Optional[UniverseSelectionHandoffV1] = None
    doubleplay: Optional[DoubleplayResolutionHandoffV1] = None
    scope_envelope: Optional[ScopeCapitalEnvelopeHandoffV1] = None
    risk_cap: Optional[RiskExposureCapHandoffV1] = None
    safety: Optional[SafetyKillSwitchHandoffV1] = None


@dataclass(frozen=True)
class MasterV2DecisionPacketValidationV1:
    ok: bool
    reason_codes: Tuple[str, ...] = ()


def build_master_v2_decision_packet_v1(
    correlation_id: str,
    staged: StagedExecutionEnablementInputV1,
    *,
    universe: Optional[UniverseSelectionHandoffV1] = None,
    doubleplay: Optional[DoubleplayResolutionHandoffV1] = None,
    scope_envelope: Optional[ScopeCapitalEnvelopeHandoffV1] = None,
    risk_cap: Optional[RiskExposureCapHandoffV1] = None,
    safety: Optional[SafetyKillSwitchHandoffV1] = None,
) -> MasterV2DecisionPacketV1:
    if safety is None:
        safety = SafetyKillSwitchHandoffV1(
            layer_version=MASTER_V2_DECISION_PACKET_LAYER_VERSION,
            safety_decision_allowed=staged.safety_decision_allowed,
        )
    return MasterV2DecisionPacketV1(
        layer_version=MASTER_V2_DECISION_PACKET_LAYER_VERSION,
        correlation_id=correlation_id,
        staged=staged,
        universe=universe,
        doubleplay=doubleplay,
        scope_envelope=scope_envelope,
        risk_cap=risk_cap,
        safety=safety,
    )


def _check_safety_mismatch(
    p: MasterV2DecisionPacketV1,
) -> List[str]:
    if p.safety is None:
        return []
    if p.safety.safety_decision_allowed != p.staged.safety_decision_allowed:
        return ["SAFETY_HANDOFF_STAGED_INPUT_MISMATCH"]
    return []


def _check_risk_cap(
    p: MasterV2DecisionPacketV1,
) -> List[str]:
    if p.risk_cap is None:
        return []
    if not p.risk_cap.cap_satisfied and p.staged.safety_decision_allowed:
        return ["RISK_CAP_BLOCKED_BUT_ENABLEMENT_ALLOWED"]
    return []


def _check_live_auth(
    p: MasterV2DecisionPacketV1,
) -> List[str]:
    s = p.staged
    if (
        s.current_stage is ExecutionStageV1.LIVE_GATED
        and s.requested_stage is ExecutionStageV1.LIVE_AUTHORIZED
        and not s.live_authority_acknowledged
    ):
        return ["LIVE_AUTH_ACK_REQUIRED"]
    return []


def validate_master_v2_decision_packet_v1(
    p: MasterV2DecisionPacketV1,
) -> MasterV2DecisionPacketValidationV1:
    reasons: List[str] = []
    reasons += _check_safety_mismatch(p)
    reasons += _check_risk_cap(p)
    reasons += _check_live_auth(p)
    return MasterV2DecisionPacketValidationV1(ok=len(reasons) == 0, reason_codes=tuple(reasons))
