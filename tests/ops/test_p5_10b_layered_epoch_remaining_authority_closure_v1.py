"""P5.10B B2+B3+B4 layered epoch remaining authority closure (no productive wiring)."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from trading.master_v2.deterministic_scope_event_generator_v1 import CanonicalScopeEventType
from trading.master_v2.double_play_entry_exit_policy_v0 import ExistingPositionSide
from trading.master_v2.double_play_state import ScopeEvent, SideState
from trading.master_v2.integrated_offline_replay_p5_cz4_delegation_v1 import P5_CZ4_DELEGATION_OWNER
from trading.master_v2.naked_mv2_dp_regime_v1 import NakedRegimeV1

from src.ops.p5_10a_layered_tick_merge_epoch_orchestration_contract_v1 import (
    SideStateEpochWriterV1,
)
from src.ops.p5_10b_layered_epoch_remaining_authority_closure_v1 import (
    map_scope_event_evidence_to_scope_event_v1,
    AUTHORIZED_SCOPE_EVENT_PRODUCER_OWNER,
    B2_CONTRACT_CLOSED,
    B3_CONTRACT_CLOSED,
    B4_CONTRACT_CLOSED,
    EXTERNAL_EFFECT_AUTHORIZED,
    LAYERED_EPOCH_REMAINING_AUTHORITY_CLOSURE_V1_DEFINED,
    LayeredEpochCanonicalHandoffRequestV1,
    LayeredEpochHandoffFailureCodeV1,
    MECHANICAL_PROVENANCE_AUTHORIZED,
    P5_10_ACTIVATION_READINESS,
    PRODUCTIVE_CYCLE_LAYERED_CORE_BIND_ENABLED,
    classify_mechanical_scope_event_provenance_from_evidence_v1,
    execute_layered_epoch_canonical_sidestate_handoff_v1,
    materialize_state_switch_evidence_v1_from_layered_handoff_v1,
    state_switch_evidence_digest_parity_check_v1,
    validate_layered_mechanical_completion_provenance_chain_v1,
)
from src.ops.p5_8b_regime_sidestate_projection_phase_authority_v1 import (
    LIFECYCLE_PERSISTENCE_OWNER,
    RegimeSidestateProjectionLifecyclePersistBindingV1,
    atomic_persist_regime_sidestate_projection_lifecycle_v1,
    fresh_regime_sidestate_projection_lifecycle_v1,
    mark_initial_regime_orientation_seed_consumed_v1,
    restore_regime_sidestate_projection_lifecycle_v1,
    roundtrip_regime_sidestate_projection_lifecycle_v1,
)
from src.ops.p5_9d_layered_mechanical_sidestate_fsm_contract_v1 import (
    CZ4_SYNTHETIC_NOOP_MATCHED_CONDITION as P59D_CZ4_MARKER,
    MechanicalFsmFailureCodeV1,
    MechanicalScopeEventProvenanceV1,
)

from tests.trading.master_v2.test_deterministic_scope_event_generator_v1 import _generate

_REPO = Path(__file__).resolve().parents[2]
_CYCLE_SOURCE = (
    _REPO
    / "src/ops/full_core_live_path_composition_root_v1/current_productive_master_v2_runtime_cycle_v1.py"
)
_REPLAY_SOURCE = _REPO / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
_INSTRUMENT = "inst-eth-usdt-perp"
_SNAPSHOT_ID = "episode-snapshot-test-001"


def test_closure_constants_and_guards() -> None:
    assert LAYERED_EPOCH_REMAINING_AUTHORITY_CLOSURE_V1_DEFINED is True
    assert B2_CONTRACT_CLOSED is True
    assert B3_CONTRACT_CLOSED is True
    assert B4_CONTRACT_CLOSED is True
    assert MECHANICAL_PROVENANCE_AUTHORIZED is True
    assert P5_10_ACTIVATION_READINESS == "READY"
    assert PRODUCTIVE_CYCLE_LAYERED_CORE_BIND_ENABLED is True
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert P59D_CZ4_MARKER == "p5_cz4_delegated_noop"


def test_b3_lifecycle_persistence_owner_and_restart_parity(tmp_path: Path) -> None:
    assert LIFECYCLE_PERSISTENCE_OWNER.endswith("persistence_v1")
    lifecycle = fresh_regime_sidestate_projection_lifecycle_v1(instrument_id=_INSTRUMENT)
    binding = RegimeSidestateProjectionLifecyclePersistBindingV1(
        instrument_id=_INSTRUMENT,
        layered_episode_snapshot_id=_SNAPSHOT_ID,
    )
    roundtrip = roundtrip_regime_sidestate_projection_lifecycle_v1(
        lifecycle=lifecycle,
        binding=binding,
    )
    assert roundtrip == lifecycle
    atomic_persist_regime_sidestate_projection_lifecycle_v1(
        tmp_path,
        lifecycle=mark_initial_regime_orientation_seed_consumed_v1(lifecycle),
        binding=binding,
    )
    restored = restore_regime_sidestate_projection_lifecycle_v1(tmp_path, binding=binding)
    assert restored.initial_regime_orientation_seed_consumed is True


def test_b3_restore_rejects_snapshot_binding_mismatch(tmp_path: Path) -> None:
    lifecycle = fresh_regime_sidestate_projection_lifecycle_v1(instrument_id=_INSTRUMENT)
    binding = RegimeSidestateProjectionLifecyclePersistBindingV1(
        instrument_id=_INSTRUMENT,
        layered_episode_snapshot_id=_SNAPSHOT_ID,
    )
    atomic_persist_regime_sidestate_projection_lifecycle_v1(
        tmp_path,
        lifecycle=lifecycle,
        binding=binding,
    )
    wrong_binding = RegimeSidestateProjectionLifecyclePersistBindingV1(
        instrument_id=_INSTRUMENT,
        layered_episode_snapshot_id="other-snapshot",
    )
    with pytest.raises(Exception, match="snapshot_binding_mismatch"):
        restore_regime_sidestate_projection_lifecycle_v1(tmp_path, binding=wrong_binding)


def test_b2_provenance_chain_accepts_deterministic_generator_for_mech_t14() -> None:
    first = _generate(trading_epoch=43, current_price=3605.0)
    evidence = _generate(
        trading_epoch=44,
        current_price=3610.0,
        confirmation_state=first.next_confirmation_state,
    )
    assert evidence.event_type is CanonicalScopeEventType.UPSCOPE_CONFIRMED
    classification = classify_mechanical_scope_event_provenance_from_evidence_v1(evidence)
    assert classification.ok is True
    assert (
        classification.provenance
        is MechanicalScopeEventProvenanceV1.LEGACY_DETERMINISTIC_SCOPE_EVENT_GENERATOR
    )
    assert classification.producer_owner == AUTHORIZED_SCOPE_EVENT_PRODUCER_OWNER
    result = validate_layered_mechanical_completion_provenance_chain_v1(
        evidence=evidence,
        scope_event=ScopeEvent.UPSCOPE_CONFIRMED,
        prior_side_state=SideState.LONG_ARMED_NEUTRAL_START,
        next_side_state=SideState.LONG_ACTIVE,
    )
    assert result.ok is True


def test_b2_cz4_synthetic_noop_rejects_completion() -> None:
    first = _generate(trading_epoch=43, current_price=3605.0)
    evidence = _generate(
        trading_epoch=44,
        current_price=3610.0,
        confirmation_state=first.next_confirmation_state,
    )
    assert evidence.event_type is CanonicalScopeEventType.UPSCOPE_CONFIRMED
    cz4 = replace(
        evidence,
        matched_conditions=(P59D_CZ4_MARKER,),
    )
    classification = classify_mechanical_scope_event_provenance_from_evidence_v1(cz4)
    assert classification.provenance is MechanicalScopeEventProvenanceV1.CZ4_SYNTHETIC_NOOP
    assert classification.producer_owner == P5_CZ4_DELEGATION_OWNER
    mapped = map_scope_event_evidence_to_scope_event_v1(cz4)
    result = validate_layered_mechanical_completion_provenance_chain_v1(
        evidence=cz4,
        scope_event=mapped,
        prior_side_state=SideState.LONG_ARMED_NEUTRAL_START,
        next_side_state=SideState.LONG_ACTIVE,
    )
    assert result.ok is False
    assert (
        MechanicalFsmFailureCodeV1.MECHANICAL_COMPLETION_CZ4_NOOP_FORBIDDEN.value
        in result.failure_codes
    )


def test_b4_initial_seed_regime_bound_handoff_end_to_end() -> None:
    lifecycle = fresh_regime_sidestate_projection_lifecycle_v1(instrument_id=_INSTRUMENT)
    evidence = _generate(trading_epoch=1, current_price=3500.0)
    result = execute_layered_epoch_canonical_sidestate_handoff_v1(
        LayeredEpochCanonicalHandoffRequestV1(
            trading_epoch=1,
            instrument_id=_INSTRUMENT,
            host_prior_side_state=SideState.NEUTRAL_OBSERVE,
            lifecycle=lifecycle,
            venue_flat=True,
            existing_position_side=ExistingPositionSide.NONE,
            switch_condition_met=False,
            regime_pre=NakedRegimeV1.BULL,
            regime_post=NakedRegimeV1.BULL,
            regime_pre_equals_post=True,
            scope_event_evidence=evidence,
            scope_event=ScopeEvent.NOOP,
            mechanical_next_side_state=None,
            chop_scope_policy_blocked_transition=False,
            layered_bind_mode_active=True,
            legacy_transition_state_writer_would_run=False,
            transition_allowed=True,
            transition_reason_code="initial_seed",
        )
    )
    assert result.ok is True
    assert result.epoch_writer is SideStateEpochWriterV1.REGIME_BOUND_P57
    assert result.canonical_next_side_state is SideState.LONG_ARMED_NEUTRAL_START
    assert result.state_switch_evidence is not None
    assert state_switch_evidence_digest_parity_check_v1(result.state_switch_evidence) is True


def test_b4_mechanical_completion_handoff_single_writer() -> None:
    first = _generate(trading_epoch=43, current_price=3605.0)
    evidence = _generate(
        trading_epoch=44,
        current_price=3610.0,
        confirmation_state=first.next_confirmation_state,
    )
    lifecycle = mark_initial_regime_orientation_seed_consumed_v1(
        fresh_regime_sidestate_projection_lifecycle_v1(instrument_id=_INSTRUMENT)
    )
    result = execute_layered_epoch_canonical_sidestate_handoff_v1(
        LayeredEpochCanonicalHandoffRequestV1(
            trading_epoch=44,
            instrument_id=_INSTRUMENT,
            host_prior_side_state=SideState.LONG_ARMED_NEUTRAL_START,
            lifecycle=lifecycle,
            venue_flat=False,
            existing_position_side=ExistingPositionSide.LONG,
            switch_condition_met=False,
            regime_pre=NakedRegimeV1.BULL,
            regime_post=NakedRegimeV1.BULL,
            regime_pre_equals_post=True,
            scope_event_evidence=evidence,
            scope_event=ScopeEvent.UPSCOPE_CONFIRMED,
            mechanical_next_side_state=SideState.LONG_ACTIVE,
            chop_scope_policy_blocked_transition=False,
            layered_bind_mode_active=True,
            legacy_transition_state_writer_would_run=False,
            transition_allowed=True,
            transition_reason_code="layered_mechanical",
        )
    )
    assert result.ok is True
    assert result.mechanical_write_asserted is True
    assert result.regime_bound_write_asserted is False
    assert result.epoch_writer is SideStateEpochWriterV1.MECHANICAL_FSM
    assert result.canonical_next_side_state is SideState.LONG_ACTIVE
    assert result.state_switch_evidence is not None
    assert result.state_switch_evidence.next_side_state == SideState.LONG_ACTIVE.value


def test_b4_rejects_parallel_legacy_transition_writer() -> None:
    lifecycle = fresh_regime_sidestate_projection_lifecycle_v1(instrument_id=_INSTRUMENT)
    evidence = _generate(trading_epoch=1, current_price=3500.0)
    result = execute_layered_epoch_canonical_sidestate_handoff_v1(
        LayeredEpochCanonicalHandoffRequestV1(
            trading_epoch=1,
            instrument_id=_INSTRUMENT,
            host_prior_side_state=SideState.NEUTRAL_OBSERVE,
            lifecycle=lifecycle,
            venue_flat=True,
            existing_position_side=ExistingPositionSide.NONE,
            switch_condition_met=False,
            regime_pre=NakedRegimeV1.BULL,
            regime_post=NakedRegimeV1.BULL,
            regime_pre_equals_post=True,
            scope_event_evidence=evidence,
            scope_event=ScopeEvent.NOOP,
            mechanical_next_side_state=None,
            chop_scope_policy_blocked_transition=False,
            layered_bind_mode_active=True,
            legacy_transition_state_writer_would_run=True,
            transition_allowed=True,
            transition_reason_code="blocked",
        )
    )
    assert result.ok is False
    assert (
        LayeredEpochHandoffFailureCodeV1.LEGACY_TRANSITION_PARALLEL_FORBIDDEN.value
        in result.failure_codes
    )


def test_state_switch_materialization_matches_replay_digest() -> None:
    evidence = _generate(trading_epoch=5, current_price=3500.0)
    switch = materialize_state_switch_evidence_v1_from_layered_handoff_v1(
        instrument_id=_INSTRUMENT,
        trading_epoch=5,
        previous_side_state=SideState.LONG_ARMED_NEUTRAL_START,
        next_side_state=SideState.LONG_ACTIVE,
        scope_event=ScopeEvent.UPSCOPE_CONFIRMED,
        scope_event_id=evidence.scope_event_id,
        transition_allowed=True,
        transition_reason_code="test",
    )
    assert state_switch_evidence_digest_parity_check_v1(switch) is True


def test_productive_cycle_wires_p5_10_bind_seam_only() -> None:
    cycle = _CYCLE_SOURCE.read_text(encoding="utf-8")
    replay = _REPLAY_SOURCE.read_text(encoding="utf-8")
    assert "p5_10_productive_activation_and_binding_v1" in cycle
    assert "p5_10b_layered_epoch_remaining_authority_closure_v1" not in cycle
    assert "p5_10b_layered_epoch_remaining_authority_closure_v1" not in replay
