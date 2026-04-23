# src/trading/master_v2/decision_packet_fixtures_v1.py
from __future__ import annotations

from typing import Any, Dict

from .decision_packet_snapshot_v1 import decision_packet_to_snapshot_v1
from .decision_packet_v1 import (
    MASTER_V2_DECISION_PACKET_LAYER_VERSION,
    DoubleplayResolutionHandoffV1,
    MasterV2DecisionPacketV1,
    RiskExposureCapHandoffV1,
    SafetyKillSwitchHandoffV1,
    ScopeCapitalEnvelopeHandoffV1,
    UniverseSelectionHandoffV1,
    build_master_v2_decision_packet_v1,
    validate_master_v2_decision_packet_v1,
)
from .staged_execution_enablement_v1 import (
    ExecutionStageV1,
    StagedExecutionEnablementInputV1,
)

DECISION_PACKET_FIXTURES_LAYER_VERSION = "v1"


def sample_universe_selection_v1() -> UniverseSelectionHandoffV1:
    return UniverseSelectionHandoffV1(
        layer_version=MASTER_V2_DECISION_PACKET_LAYER_VERSION,
        symbols=("BTC/USD",),
    )


def sample_doubleplay_decision_v1() -> DoubleplayResolutionHandoffV1:
    return DoubleplayResolutionHandoffV1(
        layer_version=MASTER_V2_DECISION_PACKET_LAYER_VERSION,
        resolution="ok",
    )


def sample_scope_envelope_v1() -> ScopeCapitalEnvelopeHandoffV1:
    return ScopeCapitalEnvelopeHandoffV1(
        layer_version=MASTER_V2_DECISION_PACKET_LAYER_VERSION, within_envelope=True
    )


def sample_risk_caps_result_v1() -> RiskExposureCapHandoffV1:
    return RiskExposureCapHandoffV1(
        layer_version=MASTER_V2_DECISION_PACKET_LAYER_VERSION, cap_satisfied=True
    )


def sample_safety_decision_v1(
    safety_decision_allowed: bool = True,
) -> SafetyKillSwitchHandoffV1:
    return SafetyKillSwitchHandoffV1(
        layer_version=MASTER_V2_DECISION_PACKET_LAYER_VERSION,
        safety_decision_allowed=safety_decision_allowed,
    )


def sample_staged_execution_enablement_input_v1() -> StagedExecutionEnablementInputV1:
    return StagedExecutionEnablementInputV1(
        current_stage=ExecutionStageV1.RESEARCH,
        requested_stage=ExecutionStageV1.BACKTEST,
        safety_decision_allowed=True,
    )


def sample_staged_execution_enablement_decision_v1():
    from .staged_execution_enablement_v1 import evaluate_staged_execution_enablement_v1

    return evaluate_staged_execution_enablement_v1(sample_staged_execution_enablement_input_v1())


def sample_master_v2_decision_packet_v1() -> MasterV2DecisionPacketV1:
    inp = StagedExecutionEnablementInputV1(
        current_stage=ExecutionStageV1.TESTNET,
        requested_stage=ExecutionStageV1.BACKTEST,
        safety_decision_allowed=True,
    )
    return build_master_v2_decision_packet_v1(
        "fixture-packet-1",
        inp,
        universe=sample_universe_selection_v1(),
        doubleplay=sample_doubleplay_decision_v1(),
    )


def sample_decision_packet_snapshot_v1() -> Dict[str, Any]:
    p = sample_master_v2_decision_packet_v1()
    v = validate_master_v2_decision_packet_v1(p)
    if not v.ok:
        return {}
    return decision_packet_to_snapshot_v1(p, require_consistent_packet=True)
