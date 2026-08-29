# src/trading/master_v2/decision_packet_from_integrated_replay_v1.py
"""Derive Decision Packet handoff from Integrated Replay compute evidence.

INTEGRATED_REPLAY = COMPUTE OWNER
DECISION_PACKET   = HANDOFF / EVIDENCE only

Does not recompute Master-V2 / Double-Play decisions.
"""

from __future__ import annotations

from typing import Optional

from trading.master_v2.decision_packet_v1 import (
    MASTER_V2_DECISION_PACKET_LAYER_VERSION,
    DoubleplayResolutionHandoffV1,
    MasterV2DecisionPacketV1,
    RiskExposureCapHandoffV1,
    SafetyKillSwitchHandoffV1,
    ScopeCapitalEnvelopeHandoffV1,
    UniverseSelectionHandoffV1,
    build_master_v2_decision_packet_v1,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER,
    IntegratedOfflineReplayResultV1,
)
from trading.master_v2.staged_execution_enablement_v1 import StagedExecutionEnablementInputV1

DECISION_PACKET_FROM_INTEGRATED_REPLAY_LAYER_VERSION = "v1"
DECISION_PACKET_FROM_INTEGRATED_REPLAY_OWNER = (
    "trading.master_v2.decision_packet_from_integrated_replay_v1"
)

SOURCE_ROLE_DERIVED_FROM_INTEGRATED_REPLAY = "DERIVED_FROM_INTEGRATED_REPLAY"
SOURCE_ROLE_LEGACY_HANDOFF_UNPROVEN = "LEGACY_HANDOFF_UNPROVEN"
DECISION_PACKET_ROLE_HANDOFF_EVIDENCE_ONLY = "HANDOFF_EVIDENCE_ONLY"

REASON_PACKET_WITHOUT_CANONICAL_REPLAY_EVIDENCE = "packet_without_canonical_replay_evidence"
REASON_PACKET_INDEPENDENT_RECOMPUTE = "decision_packet_independent_recompute"


class DecisionPacketWithoutCanonicalReplayEvidenceError(ValueError):
    """Raised when a packet claims Double-Play compute without Integrated Replay evidence."""


def derive_doubleplay_handoff_from_integrated_replay_v1(
    result: IntegratedOfflineReplayResultV1,
) -> DoubleplayResolutionHandoffV1:
    evidence = result.evidence
    if evidence is None or not evidence.decision_id or not evidence.replay_id:
        raise DecisionPacketWithoutCanonicalReplayEvidenceError(
            REASON_PACKET_WITHOUT_CANONICAL_REPLAY_EVIDENCE
        )
    if result.compute_owner != INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER:
        raise DecisionPacketWithoutCanonicalReplayEvidenceError(REASON_PACKET_INDEPENDENT_RECOMPUTE)
    resolution = "ok" if result.replay_pass else "blocked"
    return DoubleplayResolutionHandoffV1(
        layer_version=MASTER_V2_DECISION_PACKET_LAYER_VERSION,
        resolution=resolution,
        source_role=SOURCE_ROLE_DERIVED_FROM_INTEGRATED_REPLAY,
        compute_owner=INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER,
        derived_from_replay_id=evidence.replay_id,
        derived_from_evidence_decision_id=evidence.decision_id,
        composition_result_ref=evidence.composition_result_ref,
        selected_side=evidence.selected_side,
    )


def require_canonical_derived_doubleplay_handoff_v1(
    handoff: Optional[DoubleplayResolutionHandoffV1],
) -> DoubleplayResolutionHandoffV1:
    if handoff is None:
        raise DecisionPacketWithoutCanonicalReplayEvidenceError(
            REASON_PACKET_WITHOUT_CANONICAL_REPLAY_EVIDENCE
        )
    if handoff.source_role != SOURCE_ROLE_DERIVED_FROM_INTEGRATED_REPLAY:
        raise DecisionPacketWithoutCanonicalReplayEvidenceError(
            REASON_PACKET_WITHOUT_CANONICAL_REPLAY_EVIDENCE
        )
    if handoff.compute_owner != INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER:
        raise DecisionPacketWithoutCanonicalReplayEvidenceError(REASON_PACKET_INDEPENDENT_RECOMPUTE)
    if not handoff.derived_from_replay_id or not handoff.derived_from_evidence_decision_id:
        raise DecisionPacketWithoutCanonicalReplayEvidenceError(
            REASON_PACKET_WITHOUT_CANONICAL_REPLAY_EVIDENCE
        )
    return handoff


def build_master_v2_decision_packet_from_integrated_replay_v1(
    correlation_id: str,
    staged: StagedExecutionEnablementInputV1,
    result: IntegratedOfflineReplayResultV1,
    *,
    universe: Optional[UniverseSelectionHandoffV1] = None,
    scope_envelope: Optional[ScopeCapitalEnvelopeHandoffV1] = None,
    risk_cap: Optional[RiskExposureCapHandoffV1] = None,
    safety: Optional[SafetyKillSwitchHandoffV1] = None,
) -> MasterV2DecisionPacketV1:
    doubleplay = derive_doubleplay_handoff_from_integrated_replay_v1(result)
    return build_master_v2_decision_packet_v1(
        correlation_id,
        staged,
        universe=universe,
        doubleplay=doubleplay,
        scope_envelope=scope_envelope,
        risk_cap=risk_cap,
        safety=safety,
    )
