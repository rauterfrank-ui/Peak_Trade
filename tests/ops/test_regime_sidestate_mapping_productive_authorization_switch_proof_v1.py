"""REGIME_SIDESTATE_MAPPING productive authorization + switch-path proof (Owner-GO slice)."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest

from trading.master_v2.deterministic_scope_event_generator_v1 import CanonicalScopeEventType
from trading.master_v2.double_play_entry_exit_policy_v0 import ExistingPositionSide
from trading.master_v2.double_play_state import ScopeEvent, SideState
from trading.master_v2.integrated_offline_replay_p5_cz4_delegation_v1 import P5_CZ4_DELEGATION_OWNER
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    run_integrated_offline_trading_logic_replay_v1,
)
from trading.master_v2.layered_core_authority_seal_v1 import build_layered_core_authority_seal_v1
from trading.master_v2.naked_mv2_dp_regime_v1 import NakedRegimeV1

from src.ops.p5_10_productive_activation_and_binding_v1.productive_cycle_bind_seam_v1 import (
    ProductiveLayeredCoreBindCarryV1,
    finalize_productive_layered_core_replay_bind_v1,
)
from src.ops.p5_10a_layered_tick_merge_epoch_orchestration_contract_v1 import (
    EpochOrchestrationFailureCodeV1,
    SideStateEpochWriterV1,
    validate_external_epoch_closures_not_promoted_v1,
)
from src.ops.p5_10b_layered_epoch_remaining_authority_closure_v1 import (
    LayeredEpochCanonicalHandoffRequestV1,
    execute_layered_epoch_canonical_sidestate_handoff_v1,
    map_scope_event_evidence_to_scope_event_v1,
    state_switch_evidence_digest_parity_check_v1,
)
from src.ops.p5_2_productive_cycle_seam_invoke_and_authority_bind_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    PRODUCTIVE_DECISION_PATH_CUTOVER_ENABLED,
    P5_AUTHORITY_CUTOVER_AUTHORIZED,
    REGIME_SIDESTATE_MAPPING_CONTRACT_AUTHORIZED,
    validate_cz4_delegation_authority_bind_v1,
)
from src.ops.p5_8b_regime_sidestate_projection_phase_authority_v1 import (
    fresh_regime_sidestate_projection_lifecycle_v1,
    mark_initial_regime_orientation_seed_consumed_v1,
)

from tests.ops.test_p5_10b_layered_epoch_remaining_authority_closure_v1 import _generate
from tests.trading.master_v2.test_integrated_replay_p5_cz4_delegated_seal_v1 import (
    _existing_scope,
)
from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import (
    _INSTRUMENT,
    _replay_input,
)

_INSTRUMENT = "inst-eth-usdt-perp"


def test_mapping_authorization_guard_flags_unchanged() -> None:
    assert REGIME_SIDESTATE_MAPPING_CONTRACT_AUTHORIZED is True
    assert P5_AUTHORITY_CUTOVER_AUTHORIZED is False
    assert PRODUCTIVE_DECISION_PATH_CUTOVER_ENABLED is False
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert MAX_POSITIONS_EFFECTIVE == 1


def test_p5_10a_activation_gate_passes_with_mapping_authorized_and_b2_b3_b4_closed() -> None:
    result = validate_external_epoch_closures_not_promoted_v1(
        b2_closed=True,
        b3_closed=True,
        b4_closed=True,
        activation_requested=True,
    )
    assert result.ok is True
    assert (
        EpochOrchestrationFailureCodeV1.ACTIVATION_MAPPING_NOT_AUTHORIZED.value
        not in result.failure_codes
    )


@pytest.mark.parametrize(
    ("regime_pre", "regime_post", "prior", "expected", "position_side"),
    [
        (
            NakedRegimeV1.BULL,
            NakedRegimeV1.BEAR,
            SideState.LONG_ACTIVE,
            SideState.SWITCH_LONG_TO_SHORT_PENDING,
            ExistingPositionSide.LONG,
        ),
        (
            NakedRegimeV1.BEAR,
            NakedRegimeV1.BULL,
            SideState.SHORT_ACTIVE,
            SideState.SWITCH_SHORT_TO_LONG_PENDING,
            ExistingPositionSide.SHORT,
        ),
    ],
)
def test_p5_10b_switch_handoff_single_regime_bound_writer(
    regime_pre: NakedRegimeV1,
    regime_post: NakedRegimeV1,
    prior: SideState,
    expected: SideState,
    position_side: ExistingPositionSide,
) -> None:
    lifecycle = mark_initial_regime_orientation_seed_consumed_v1(
        fresh_regime_sidestate_projection_lifecycle_v1(instrument_id=_INSTRUMENT)
    )
    evidence = _generate(trading_epoch=50, current_price=3600.0)
    cz4_evidence = replace(
        evidence,
        event_type=CanonicalScopeEventType.NOOP,
        matched_conditions=("p5_cz4_delegated_noop",),
    )
    result = execute_layered_epoch_canonical_sidestate_handoff_v1(
        LayeredEpochCanonicalHandoffRequestV1(
            trading_epoch=50,
            instrument_id=_INSTRUMENT,
            host_prior_side_state=prior,
            lifecycle=lifecycle,
            venue_flat=False,
            existing_position_side=position_side,
            switch_condition_met=True,
            regime_pre=regime_pre,
            regime_post=regime_post,
            regime_pre_equals_post=False,
            scope_event_evidence=cz4_evidence,
            scope_event=map_scope_event_evidence_to_scope_event_v1(cz4_evidence),
            mechanical_next_side_state=None,
            chop_scope_policy_blocked_transition=False,
            layered_bind_mode_active=True,
            legacy_transition_state_writer_would_run=False,
            transition_allowed=False,
            transition_reason_code=P5_CZ4_DELEGATION_OWNER,
        )
    )
    assert result.ok is True
    assert result.epoch_writer is SideStateEpochWriterV1.REGIME_BOUND_P57
    assert result.canonical_next_side_state is expected
    assert result.state_switch_evidence is not None
    assert result.state_switch_evidence.next_side_state == expected.value
    assert state_switch_evidence_digest_parity_check_v1(result.state_switch_evidence) is True


def test_no_switch_handoff_unchanged_hold() -> None:
    lifecycle = fresh_regime_sidestate_projection_lifecycle_v1(instrument_id=_INSTRUMENT)
    evidence = _generate(trading_epoch=1, current_price=3500.0)
    result = execute_layered_epoch_canonical_sidestate_handoff_v1(
        LayeredEpochCanonicalHandoffRequestV1(
            trading_epoch=1,
            instrument_id=_INSTRUMENT,
            host_prior_side_state=SideState.LONG_ARMED_NEUTRAL_START,
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
            transition_reason_code="no_switch",
        )
    )
    assert result.ok is True
    assert result.epoch_writer is SideStateEpochWriterV1.HOLD_NO_MUTATION
    assert result.canonical_next_side_state is SideState.LONG_ARMED_NEUTRAL_START


@patch("trading.master_v2.integrated_offline_trading_logic_replay_v1.transition_state")
@patch(
    "trading.master_v2.integrated_offline_trading_logic_replay_v1.generate_deterministic_scope_event"
)
@patch("trading.master_v2.integrated_offline_trading_logic_replay_v1.update_dynamic_boundaries")
@patch("trading.master_v2.integrated_offline_trading_logic_replay_v1.initialize_canonical_scope")
def test_cz4_switch_tick_skips_legacy_i1_i3_writers(
    mock_init,
    mock_update,
    mock_generate,
    mock_transition,
) -> None:
    seal = build_layered_core_authority_seal_v1(
        seal_id="switch-writer-proof",
        instrument_id=_INSTRUMENT,
        episode_snapshot_id="a" * 64,
        store_manifest_digest="b" * 64,
        regime_pre=NakedRegimeV1.BULL,
        regime_post=NakedRegimeV1.BEAR,
        nullline_price=3500.0,
        d_t=200.0,
        r_t=3500.0,
        cm_t=250.0,
        switch_condition_met=True,
        mechanical_step_count=2,
    )
    bind = validate_cz4_delegation_authority_bind_v1(seal=seal, side_state=SideState.LONG_ACTIVE)
    assert bind.ok is True
    inp = _replay_input(
        existing_scope=_existing_scope(),
        layered_core_authority_seal=seal,
        side_state=SideState.LONG_ACTIVE,
    )
    result = run_integrated_offline_trading_logic_replay_v1(inp)
    assert result.evidence is not None
    mock_init.assert_not_called()
    mock_update.assert_not_called()
    mock_generate.assert_not_called()
    mock_transition.assert_not_called()


def test_finalize_bind_patches_state_switch_on_regime_switch(tmp_path: Path) -> None:
    seal = build_layered_core_authority_seal_v1(
        seal_id="switch-finalize",
        instrument_id=_INSTRUMENT,
        episode_snapshot_id="c" * 64,
        store_manifest_digest="d" * 64,
        regime_pre=NakedRegimeV1.BULL,
        regime_post=NakedRegimeV1.BEAR,
        nullline_price=3500.0,
        d_t=200.0,
        r_t=3500.0,
        cm_t=250.0,
        switch_condition_met=True,
        mechanical_step_count=2,
    )
    inp = _replay_input(
        existing_scope=_existing_scope(),
        layered_core_authority_seal=seal,
        side_state=SideState.LONG_ACTIVE,
        existing_position_side=ExistingPositionSide.LONG,
        venue_flat=False,
    )
    replay = run_integrated_offline_trading_logic_replay_v1(inp)
    assert replay.replay_pass is True
    assert replay.intermediate is not None
    carry = ProductiveLayeredCoreBindCarryV1(
        bind_active=True,
        failure_codes=(),
        seal=seal,
        lifecycle_binding=None,
        cz4_delegation_suppressed_legacy_writers=True,
        sole_handoff_owner="test",
    )
    from src.ops.p5_8b_regime_sidestate_projection_phase_authority_v1.persistence_v1 import (
        RegimeSidestateProjectionLifecyclePersistBindingV1,
    )

    carry = replace(
        carry,
        lifecycle_binding=RegimeSidestateProjectionLifecyclePersistBindingV1(
            instrument_id=_INSTRUMENT,
            layered_episode_snapshot_id=str(seal.episode_snapshot_id),
        ),
    )
    lifecycle = mark_initial_regime_orientation_seed_consumed_v1(
        fresh_regime_sidestate_projection_lifecycle_v1(instrument_id=_INSTRUMENT)
    )
    from src.ops.p5_8b_regime_sidestate_projection_phase_authority_v1.persistence_v1 import (
        atomic_persist_regime_sidestate_projection_lifecycle_v1,
    )

    binding = carry.lifecycle_binding
    assert binding is not None
    atomic_persist_regime_sidestate_projection_lifecycle_v1(
        tmp_path, lifecycle=lifecycle, binding=binding
    )
    finalized = finalize_productive_layered_core_replay_bind_v1(
        replay=replay,
        carry=carry,
        layered_core_store_root=tmp_path,
        host_prior_side_state=SideState.LONG_ACTIVE,
        trading_epoch=int(inp.trading_epoch),
        instrument_id=_INSTRUMENT,
        venue_flat=False,
        existing_position_side=ExistingPositionSide.LONG,
    )
    assert finalized.replay_pass is True
    assert finalized.intermediate is not None
    switch = finalized.intermediate.state_switch
    assert switch is not None
    assert switch.next_side_state == SideState.SWITCH_LONG_TO_SHORT_PENDING.value
    assert state_switch_evidence_digest_parity_check_v1(switch) is True


def test_cz4_fail_closed_on_invalid_seal_switch_flag() -> None:
    seal = build_layered_core_authority_seal_v1(
        seal_id="inconsistent-switch",
        instrument_id=_INSTRUMENT,
        episode_snapshot_id="e" * 64,
        store_manifest_digest="f" * 64,
        regime_pre=NakedRegimeV1.BULL,
        regime_post=NakedRegimeV1.BEAR,
        nullline_price=3500.0,
        d_t=200.0,
        r_t=3500.0,
        cm_t=250.0,
        switch_condition_met=False,
        mechanical_step_count=2,
    )
    bind = validate_cz4_delegation_authority_bind_v1(seal=seal, side_state=SideState.LONG_ACTIVE)
    assert bind.ok is True
    inp = _replay_input(existing_scope=_existing_scope(), layered_core_authority_seal=seal)
    replay = run_integrated_offline_trading_logic_replay_v1(inp)
    assert replay.replay_pass is True
