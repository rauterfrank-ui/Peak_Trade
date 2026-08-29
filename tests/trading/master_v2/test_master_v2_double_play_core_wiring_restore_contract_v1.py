"""Offline contract: restored Master-V2 / Double-Play core wiring (A01–A05).

REGISTRY → SUITABILITY SNAPSHOT → INTEGRATED REPLAY → COMPOSITION
→ CANONICAL DECISION EVIDENCE → DECISION PACKET DERIVATION

No network, no live/testnet/canary/orders, AUTH-001 remains undecided.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from src.ops.double_play.specialists import evaluate_double_play
from src.strategies.registry import build_registry_snapshot
from trading.master_v2.decision_packet_fixtures_v1 import sample_doubleplay_decision_v1
from trading.master_v2.decision_packet_from_integrated_replay_v1 import (
    SOURCE_ROLE_DERIVED_FROM_INTEGRATED_REPLAY,
    DecisionPacketWithoutCanonicalReplayEvidenceError,
    require_canonical_derived_doubleplay_handoff_v1,
)
from trading.master_v2.double_play_core_wiring_v1 import (
    assert_core_wiring_authority_invariants_v1,
    run_master_v2_double_play_core_wiring_v1,
)
from trading.master_v2.double_play_sole_authority_quarantine_v1 import (
    CANONICAL_BULL_BEAR_STATE_OWNER,
    CANONICAL_COMPOSITION_AUTHORITY,
    CANONICAL_OFFLINE_ORCHESTRATOR,
    LIVE_AUTHORIZED,
    OPS_SPECIALISTS_AUTHORITY_CLASS,
    ORDERS_ENABLED,
    SCENARIO_REPLAY_AUTHORITY_CLASS,
    CompetingAuthorityEscalationError,
    CompetingSideStateWriterError,
    assert_path_cannot_escalate_to_compute_owner_v1,
    assert_path_cannot_write_side_state_v1,
    build_double_play_sole_authority_status_fields_v1,
)
from trading.master_v2.evaluate_double_play_authority_boundary_v0 import (
    OFFLINE_SCENARIO_REPLAY_AUTHORITY,
    OFFLINE_SCENARIO_REPLAY_CALLABLE,
    OPS_EVALUATE_DOUBLE_PLAY_AUTHORITY,
    OPS_EVALUATE_DOUBLE_PLAY_CALLABLE,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER,
    run_integrated_offline_trading_logic_replay_v1,
)
from trading.master_v2.local_evaluator_v1 import evaluate_master_v2_local_flow_v1
from trading.master_v2.offline_double_play_scenario_replay_v0 import (
    OFFLINE_DOUBLE_PLAY_SCENARIO_REPLAY_AUTHORITY_CLASS,
    OFFLINE_DOUBLE_PLAY_SCENARIO_REPLAY_PATH_AUTHORITY,
)
from trading.master_v2.registry_suitability_snapshot_v1 import (
    METADATA_AUTHORIZATION_EFFECT,
    RegistrySuitabilitySnapshotError,
    build_registry_derived_suitability_snapshot_v1,
    finalize_registry_suitability_snapshot_v1,
)
from trading.master_v2.staged_execution_enablement_v1 import (
    ExecutionStageV1,
    StagedExecutionEnablementInputV1,
)
from trading.master_v2.strategy_identity_binding_v1 import (
    AUTH_001_CANONICAL_IDS,
    AUTH_001_POLICY_DECIDED,
    AUTH_001_RELATION_UNRESOLVED_DISTINCT_IDENTITIES,
    AUTH_001_RELATION_UNRESOLVED_DISTINCT_PEER,
    REASON_AMBIGUOUS_STRATEGY_BINDING,
    REASON_AUTH_001_UNRESOLVED_IDENTITY,
    REASON_DUPLICATE_REGISTRY_IDENTITY,
    REASON_EMPTY_ELIGIBLE_STRATEGY_SET,
    REASON_UNKNOWN_STRATEGY_ID,
    STRATEGY_IDENTITY_ENFORCEMENT_REGISTRY_DERIVED,
    StrategyIdentityBindingError,
    bind_requested_strategy_ids_v1,
    bind_strategy_identity_v1,
    collect_suitability_identity_failures_v1,
)
from trading.master_v2.suitability_binding_v1 import (
    SuitabilityStrategyEntryV1,
    SuitabilityStrategyRegistryV1,
)
from trading.master_v2.directional_assessment_v1 import DirectionalAssessmentSide
from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import (
    _replay_input,
)


def _disabled_entry(strategy_id: str) -> SuitabilityStrategyEntryV1:
    return SuitabilityStrategyEntryV1(
        strategy_id=strategy_id,
        supported_regime_ids=("*",),
        supported_sides=(DirectionalAssessmentSide.LONG, DirectionalAssessmentSide.SHORT),
        priority_rank=1,
        disabled=True,
    )


def _enabled_entry(strategy_id: str) -> SuitabilityStrategyEntryV1:
    return SuitabilityStrategyEntryV1(
        strategy_id=strategy_id,
        supported_regime_ids=("trending", "*"),
        supported_sides=(DirectionalAssessmentSide.LONG, DirectionalAssessmentSide.SHORT),
        priority_rank=1,
        disabled=False,
    )


def test_end_to_end_registry_suitability_integrated_replay_packet_wiring() -> None:
    snapshot_a = build_registry_derived_suitability_snapshot_v1()
    snapshot_b = build_registry_derived_suitability_snapshot_v1()
    assert snapshot_a.snapshot_digest == snapshot_b.snapshot_digest
    assert snapshot_a.strategy_ids_sorted == snapshot_b.strategy_ids_sorted
    assert snapshot_a.network_used is False
    assert snapshot_a.live_authorized is False
    assert snapshot_a.orders_allowed is False
    assert snapshot_a.runtime_promoted is False
    assert snapshot_a.auth_001_policy_decided is False
    assert AUTH_001_POLICY_DECIDED is False
    assert AUTH_001_CANONICAL_IDS.issubset(set(snapshot_a.strategy_ids_sorted))
    assert snapshot_a.auth_001_relation == AUTH_001_RELATION_UNRESOLVED_DISTINCT_IDENTITIES
    assert snapshot_a.metadata_authorization_effect == METADATA_AUTHORIZATION_EFFECT
    assert snapshot_a.production_or_live_ready_strategy_ids
    assert "ma_crossover" in snapshot_a.production_or_live_ready_strategy_ids

    result = run_master_v2_double_play_core_wiring_v1(_replay_input())
    assert_core_wiring_authority_invariants_v1(result)
    assert result.replay.compute_owner == INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER
    assert result.replay.compute_owner == CANONICAL_OFFLINE_ORCHESTRATOR
    assert result.replay.strategy_identity_enforcement == (
        STRATEGY_IDENTITY_ENFORCEMENT_REGISTRY_DERIVED
    )
    assert result.replay.consumed_strategy_ids == result.snapshot.strategy_ids_sorted
    assert result.replay.registry_snapshot_digest == result.snapshot.snapshot_digest
    assert result.replay.decision_packet_role == "HANDOFF_EVIDENCE_ONLY"
    assert result.replay.evidence.execution_eligible is False
    assert result.replay.evidence.order_effect == "NONE"
    assert result.replay.evidence.authority_effect == "NONE"
    assert result.replay.intermediate is not None
    assert result.replay.intermediate.composition_result is not None
    assert result.composition_confirm_authority == CANONICAL_COMPOSITION_AUTHORITY
    assert result.side_state_writer == CANONICAL_BULL_BEAR_STATE_OWNER
    assert CANONICAL_BULL_BEAR_STATE_OWNER.endswith("transition_state")
    assert result.doubleplay_handoff.source_role == SOURCE_ROLE_DERIVED_FROM_INTEGRATED_REPLAY
    assert result.doubleplay_handoff.compute_owner == INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER
    assert (
        result.doubleplay_handoff.derived_from_evidence_decision_id
        == result.replay.evidence.decision_id
    )
    assert (
        result.doubleplay_handoff.composition_result_ref
        == result.replay.evidence.composition_result_ref
    )
    require_canonical_derived_doubleplay_handoff_v1(result.packet.doubleplay)
    fields = build_double_play_sole_authority_status_fields_v1()
    assert fields["LIVE_AUTHORIZED"] == LIVE_AUTHORIZED == "false"
    assert fields["ORDERS_ENABLED"] == ORDERS_ENABLED == "false"


def test_explicit_canonical_auth_001_ids_bind_independently_without_collapse() -> None:
    ecm = bind_strategy_identity_v1("ecm_cycle")
    armstrong = bind_strategy_identity_v1("armstrong_cycle")
    assert ecm.canonical_strategy_id == "ecm_cycle"
    assert armstrong.canonical_strategy_id == "armstrong_cycle"
    assert ecm.canonical_strategy_id != armstrong.canonical_strategy_id
    assert ecm.auth_001_relation == AUTH_001_RELATION_UNRESOLVED_DISTINCT_PEER
    assert armstrong.auth_001_relation == AUTH_001_RELATION_UNRESOLVED_DISTINCT_PEER
    both = bind_requested_strategy_ids_v1(("ecm_cycle", "armstrong_cycle"))
    assert {item.canonical_strategy_id for item in both} == AUTH_001_CANONICAL_IDS


def test_unknown_strategy_id_fail_closed() -> None:
    with pytest.raises(StrategyIdentityBindingError, match=REASON_UNKNOWN_STRATEGY_ID):
        bind_strategy_identity_v1("definitely_not_a_strategy_xyz")
    with pytest.raises(RegistrySuitabilitySnapshotError, match=REASON_UNKNOWN_STRATEGY_ID):
        build_registry_derived_suitability_snapshot_v1(
            strategy_ids=("definitely_not_a_strategy_xyz",)
        )


def test_ambiguous_strategy_binding_fail_closed() -> None:
    for token in ("ecm", "armstrong", "ecm_or_armstrong", " armstrong_cycle"):
        with pytest.raises(StrategyIdentityBindingError, match=REASON_AMBIGUOUS_STRATEGY_BINDING):
            bind_strategy_identity_v1(token)


def test_auth_001_unresolved_relationship_fail_closed_on_collapse() -> None:
    with pytest.raises(StrategyIdentityBindingError, match=REASON_AUTH_001_UNRESOLVED_IDENTITY):
        bind_requested_strategy_ids_v1(
            ("ecm_cycle", "armstrong_cycle"),
            treat_as_equivalent=True,
        )


def test_duplicate_registry_identity_fail_closed() -> None:
    with pytest.raises(StrategyIdentityBindingError, match=REASON_DUPLICATE_REGISTRY_IDENTITY):
        bind_requested_strategy_ids_v1(("ma_crossover", "ma_crossover"))
    registry = SuitabilityStrategyRegistryV1(
        entries=(_enabled_entry("ma_crossover"), _enabled_entry("ma_crossover"))
    )
    reasons = collect_suitability_identity_failures_v1(registry)
    assert REASON_DUPLICATE_REGISTRY_IDENTITY in reasons


def test_empty_eligible_strategy_set_fail_closed() -> None:
    snapshot = build_registry_snapshot()
    registry = SuitabilityStrategyRegistryV1(entries=(_disabled_entry("ma_crossover"),))
    with pytest.raises(RegistrySuitabilitySnapshotError, match=REASON_EMPTY_ELIGIBLE_STRATEGY_SET):
        finalize_registry_suitability_snapshot_v1(
            registry,
            registry_snapshot=snapshot,
            consumed_strategy_ids=("ma_crossover",),
        )


def test_registry_derived_replay_rejects_unknown_identity() -> None:
    inp = replace(
        _replay_input(),
        strategy_registry=SuitabilityStrategyRegistryV1(
            entries=(_enabled_entry("definitely_not_a_strategy_xyz"),)
        ),
        strategy_identity_enforcement=STRATEGY_IDENTITY_ENFORCEMENT_REGISTRY_DERIVED,
    )
    result = run_integrated_offline_trading_logic_replay_v1(inp)
    assert result.replay_pass is False
    assert REASON_UNKNOWN_STRATEGY_ID in result.fail_reasons
    assert result.compute_owner == INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER


def test_packet_without_canonical_replay_evidence_fail_closed() -> None:
    with pytest.raises(
        DecisionPacketWithoutCanonicalReplayEvidenceError,
        match="packet_without_canonical_replay_evidence",
    ):
        require_canonical_derived_doubleplay_handoff_v1(sample_doubleplay_decision_v1())
    staged = StagedExecutionEnablementInputV1(
        current_stage=ExecutionStageV1.RESEARCH,
        requested_stage=ExecutionStageV1.BACKTEST,
        safety_decision_allowed=True,
        live_authority_acknowledged=False,
    )
    flow = evaluate_master_v2_local_flow_v1(
        "packet-without-replay",
        staged,
        doubleplay=sample_doubleplay_decision_v1(),
        require_canonical_derived_doubleplay_handoff=True,
    )
    assert flow.flow_ok is False
    assert flow.rejection_reason == "PACKET_WITHOUT_CANONICAL_REPLAY_EVIDENCE"


def test_subordinate_evaluator_cannot_escalate_to_compute_owner() -> None:
    with pytest.raises(CompetingAuthorityEscalationError):
        assert_path_cannot_escalate_to_compute_owner_v1(
            path_id=OFFLINE_SCENARIO_REPLAY_CALLABLE,
            claimed_role="COMPUTE_OWNER",
        )
    with pytest.raises(CompetingAuthorityEscalationError):
        evaluate_double_play(
            context={
                "double_play_enabled": True,
                "claimed_compute_role": "COMPUTE_OWNER",
            }
        )
    assert OPS_EVALUATE_DOUBLE_PLAY_AUTHORITY == "LEGACY_NON_AUTHORITATIVE"
    assert OFFLINE_SCENARIO_REPLAY_AUTHORITY == "LEGACY_NON_AUTHORITATIVE"
    assert OPS_SPECIALISTS_AUTHORITY_CLASS == "NON_AUTHORITATIVE"
    assert SCENARIO_REPLAY_AUTHORITY_CLASS == "SUBORDINATE"
    assert OFFLINE_DOUBLE_PLAY_SCENARIO_REPLAY_PATH_AUTHORITY == "LEGACY_NON_AUTHORITATIVE"
    assert OFFLINE_DOUBLE_PLAY_SCENARIO_REPLAY_AUTHORITY_CLASS == "SUBORDINATE"


def test_competing_side_state_writer_fail_closed() -> None:
    with pytest.raises(CompetingSideStateWriterError):
        assert_path_cannot_write_side_state_v1(
            path_id=OPS_EVALUATE_DOUBLE_PLAY_CALLABLE,
            claimed_may_write_side_state=True,
        )
    with pytest.raises(CompetingSideStateWriterError):
        evaluate_double_play(
            context={
                "double_play_enabled": True,
                "may_write_side_state": True,
            }
        )
    projection = evaluate_double_play(context={"double_play_enabled": True})
    assert projection.details["may_write_side_state"] == "false"
    assert projection.details["authority_class"] == OPS_SPECIALISTS_AUTHORITY_CLASS
    assert projection.details["path_authority"] == OPS_EVALUATE_DOUBLE_PLAY_AUTHORITY


def test_production_live_ready_metadata_does_not_authorize_trading() -> None:
    snapshot = build_registry_derived_suitability_snapshot_v1()
    assert snapshot.production_or_live_ready_strategy_ids
    assert snapshot.live_authorized is False
    assert snapshot.orders_allowed is False
    assert LIVE_AUTHORIZED == "false"
    assert ORDERS_ENABLED == "false"
    assert snapshot.metadata_authorization_effect == "NON_AUTHORIZING"
