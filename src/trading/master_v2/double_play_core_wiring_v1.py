# src/trading/master_v2/double_play_core_wiring_v1.py
"""Restored current-system Master-V2 / Double-Play core wiring facade.

Registry → Suitability snapshot → Integrated Replay (compute owner)
→ Composition confirm / SideState sole writer → Decision Packet (derived handoff).

AUTH-001 is closed: ``AUTH_001_POLICY_DECIDED=true``. ``armstrong_cycle`` is not a
bindable active catalog identity. ``ecm_cycle`` remains legacy/deauthorized and
gains no productive, live, order, or promotion authority. Historical peer identities
must never collapse. Does not restore capital, live, or economic viability.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Optional

from trading.master_v2.decision_packet_from_integrated_replay_v1 import (
    DECISION_PACKET_ROLE_HANDOFF_EVIDENCE_ONLY,
    SOURCE_ROLE_DERIVED_FROM_INTEGRATED_REPLAY,
    build_master_v2_decision_packet_from_integrated_replay_v1,
    derive_doubleplay_handoff_from_integrated_replay_v1,
)
from trading.master_v2.decision_packet_v1 import (
    DoubleplayResolutionHandoffV1,
    MasterV2DecisionPacketV1,
)
from trading.master_v2.double_play_sole_authority_quarantine_v1 import (
    CANONICAL_BULL_BEAR_STATE_OWNER,
    CANONICAL_COMPOSITION_AUTHORITY,
    CANONICAL_OFFLINE_ORCHESTRATOR,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER,
    IntegratedOfflineReplayInputV1,
    IntegratedOfflineReplayResultV1,
    run_integrated_offline_trading_logic_replay_v1,
)
from trading.master_v2.registry_suitability_snapshot_v1 import (
    RegistryDerivedSuitabilitySnapshotV1,
    build_registry_derived_suitability_snapshot_v1,
)
from trading.master_v2.staged_execution_enablement_v1 import (
    ExecutionStageV1,
    StagedExecutionEnablementInputV1,
)
from trading.master_v2.strategy_identity_binding_v1 import (
    AUTH_001_POLICY_DECIDED,
    AUTH_001_RELATION_CLOSED_ARMSTRONG_RETIRED_ECM_LEGACY,
    AUTH_001_RELATION_UNRESOLVED_DISTINCT_IDENTITIES,
    AUTH_001_RETIRED_CATALOG_IDS,
    STRATEGY_IDENTITY_ENFORCEMENT_REGISTRY_DERIVED,
)

DOUBLE_PLAY_CORE_WIRING_LAYER_VERSION = "v1"
DOUBLE_PLAY_CORE_WIRING_OWNER = "trading.master_v2.double_play_core_wiring_v1"


@dataclass(frozen=True)
class MasterV2DoublePlayCoreWiringResultV1:
    snapshot: RegistryDerivedSuitabilitySnapshotV1
    replay: IntegratedOfflineReplayResultV1
    doubleplay_handoff: DoubleplayResolutionHandoffV1
    packet: MasterV2DecisionPacketV1
    compute_owner: str
    composition_confirm_authority: str
    side_state_writer: str
    decision_packet_role: str


def attach_registry_derived_suitability_snapshot_v1(
    inp: IntegratedOfflineReplayInputV1,
    snapshot: Optional[RegistryDerivedSuitabilitySnapshotV1] = None,
) -> tuple[IntegratedOfflineReplayInputV1, RegistryDerivedSuitabilitySnapshotV1]:
    snap = snapshot or build_registry_derived_suitability_snapshot_v1()
    wired = replace(
        inp,
        strategy_registry=snap.suitability_registry,
        strategy_identity_enforcement=STRATEGY_IDENTITY_ENFORCEMENT_REGISTRY_DERIVED,
        registry_snapshot_digest=snap.snapshot_digest,
    )
    return wired, snap


def run_master_v2_double_play_core_wiring_v1(
    inp: IntegratedOfflineReplayInputV1,
    *,
    snapshot: Optional[RegistryDerivedSuitabilitySnapshotV1] = None,
    correlation_id: str = "mv2-dp-core-wiring-v1",
) -> MasterV2DoublePlayCoreWiringResultV1:
    wired, snap = attach_registry_derived_suitability_snapshot_v1(inp, snapshot)
    replay = run_integrated_offline_trading_logic_replay_v1(wired)
    handoff = derive_doubleplay_handoff_from_integrated_replay_v1(replay)
    staged = StagedExecutionEnablementInputV1(
        current_stage=ExecutionStageV1.RESEARCH,
        requested_stage=ExecutionStageV1.BACKTEST,
        safety_decision_allowed=True,
        live_authority_acknowledged=False,
    )
    packet = build_master_v2_decision_packet_from_integrated_replay_v1(
        correlation_id,
        staged,
        replay,
    )
    return MasterV2DoublePlayCoreWiringResultV1(
        snapshot=snap,
        replay=replay,
        doubleplay_handoff=handoff,
        packet=packet,
        compute_owner=INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER,
        composition_confirm_authority=CANONICAL_COMPOSITION_AUTHORITY,
        side_state_writer=CANONICAL_BULL_BEAR_STATE_OWNER,
        decision_packet_role=DECISION_PACKET_ROLE_HANDOFF_EVIDENCE_ONLY,
    )


def assert_core_wiring_authority_invariants_v1(
    result: MasterV2DoublePlayCoreWiringResultV1,
) -> None:
    if result.compute_owner != CANONICAL_OFFLINE_ORCHESTRATOR:
        raise AssertionError("integrated_replay_not_compute_owner")
    if result.replay.compute_owner != INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER:
        raise AssertionError("integrated_replay_result_compute_owner_mismatch")
    if result.doubleplay_handoff.source_role != SOURCE_ROLE_DERIVED_FROM_INTEGRATED_REPLAY:
        raise AssertionError("decision_packet_not_derived_handoff")
    if result.composition_confirm_authority != CANONICAL_COMPOSITION_AUTHORITY:
        raise AssertionError("composition_confirm_authority_inverted")
    if result.side_state_writer != CANONICAL_BULL_BEAR_STATE_OWNER:
        raise AssertionError("side_state_writer_inverted")
    if result.packet.doubleplay is None:
        raise AssertionError("derived_doubleplay_handoff_missing")
    if result.snapshot.live_authorized or result.snapshot.orders_allowed:
        raise AssertionError("snapshot_inferred_trading_authorization")
    if result.snapshot.runtime_promoted:
        raise AssertionError("snapshot_inferred_runtime_promotion")
    if AUTH_001_POLICY_DECIDED is not True:
        raise AssertionError("auth_001_policy_must_remain_decided")
    if result.snapshot.auth_001_policy_decided is not True:
        raise AssertionError("auth_001_policy_must_remain_decided")
    retired_present = AUTH_001_RETIRED_CATALOG_IDS.intersection(
        result.snapshot.strategy_ids_sorted
    ) | AUTH_001_RETIRED_CATALOG_IDS.intersection(result.snapshot.eligible_strategy_ids_sorted)
    if retired_present:
        raise AssertionError("armstrong_cycle_must_not_be_bindable_active_catalog_identity")
    if AUTH_001_RETIRED_CATALOG_IDS.intersection(
        result.snapshot.production_or_live_ready_strategy_ids
    ):
        raise AssertionError("armstrong_cycle_must_not_gain_live_or_promotion_authority")
    if "ecm_cycle" in result.snapshot.production_or_live_ready_strategy_ids:
        raise AssertionError("ecm_cycle_must_not_gain_new_authority")
    if result.snapshot.auth_001_relation == AUTH_001_RELATION_UNRESOLVED_DISTINCT_IDENTITIES:
        raise AssertionError("auth_001_identities_must_not_collapse")
    if "ecm_cycle" in result.snapshot.strategy_ids_sorted:
        if (
            result.snapshot.auth_001_relation
            != AUTH_001_RELATION_CLOSED_ARMSTRONG_RETIRED_ECM_LEGACY
        ):
            raise AssertionError("auth_001_must_remain_closed_armstrong_retired_ecm_legacy")
