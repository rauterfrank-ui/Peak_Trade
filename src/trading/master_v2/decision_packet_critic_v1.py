# src/trading/master_v2/decision_packet_critic_v1.py
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List

from .decision_packet_v1 import MasterV2DecisionPacketV1, validate_master_v2_decision_packet_v1
from .staged_execution_enablement_v1 import ExecutionStageV1

DECISION_PACKET_CRITIC_LAYER_VERSION = "v1"


class CriticFindingSeverityV1(str, Enum):
    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True)
class DecisionPacketCriticFindingV1:
    code: str
    message: str
    severity: CriticFindingSeverityV1


@dataclass
class DecisionPacketCriticReportV1:
    layer_version: str
    findings: List[DecisionPacketCriticFindingV1] = field(default_factory=list)

    @property
    def has_error_findings(self) -> bool:
        return any(f.severity is CriticFindingSeverityV1.ERROR for f in self.findings)


def _optional_layer_warnings(p: MasterV2DecisionPacketV1) -> List[DecisionPacketCriticFindingV1]:
    s = p.staged
    if (
        s.current_stage is not ExecutionStageV1.TESTNET
        or s.requested_stage is not ExecutionStageV1.LIVE_GATED
    ):
        return []
    missing = []
    if p.universe is None:
        missing.append("universe")
    if p.doubleplay is None:
        missing.append("doubleplay")
    if p.scope_envelope is None:
        missing.append("scope_envelope")
    if p.risk_cap is None:
        missing.append("risk_cap")
    if not missing:
        return []
    return [
        DecisionPacketCriticFindingV1(
            code="LAYER_MISSING_OPTIONAL",
            message="optional handoffs missing: " + ",".join(missing),
            severity=CriticFindingSeverityV1.WARNING,
        )
    ]


def critique_master_v2_decision_packet_v1(
    p: MasterV2DecisionPacketV1,
) -> DecisionPacketCriticReportV1:
    v = validate_master_v2_decision_packet_v1(p)
    fs: List[DecisionPacketCriticFindingV1] = []

    if "SAFETY_HANDOFF_STAGED_INPUT_MISMATCH" in v.reason_codes:
        fs.append(
            DecisionPacketCriticFindingV1(
                code="SAFETY_ENABLEMENT_MISMATCH",
                message="safety handoff widerspricht dem staged safety_decision_allowed",
                severity=CriticFindingSeverityV1.ERROR,
            )
        )
    if "RISK_CAP_BLOCKED_BUT_ENABLEMENT_ALLOWED" in v.reason_codes:
        fs.append(
            DecisionPacketCriticFindingV1(
                code="BLOCKED_BUT_ENABLEMENT_ALLOWED",
                message="risiko cap nicht erfuellt, enablement indiziert erlaubte progression",
                severity=CriticFindingSeverityV1.ERROR,
            )
        )
    if "LIVE_AUTH_ACK_REQUIRED" in v.reason_codes:
        fs.append(
            DecisionPacketCriticFindingV1(
                code="LIVE_AUTH_ACK_MISSING",
                message="wechsel zu live_authorized benoetigt live_authority_acknowledged",
                severity=CriticFindingSeverityV1.ERROR,
            )
        )

    if v.ok:
        fs.extend(_optional_layer_warnings(p))

    return DecisionPacketCriticReportV1(
        layer_version=DECISION_PACKET_CRITIC_LAYER_VERSION, findings=fs
    )
