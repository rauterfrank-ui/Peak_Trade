"""P5.10A layered tick-merge epoch orchestration contract (no productive wiring)."""

from __future__ import annotations

from pathlib import Path

import pytest

from trading.master_v2.double_play_state import SideState

from src.ops.p5_10a_layered_tick_merge_epoch_orchestration_contract_v1 import (
    CANONICAL_LAYERED_EPOCH_STEP_ORDER,
    C4EntryExitSideStateEpochV1,
    EpochOrchestrationFailureCodeV1,
    ExternalEpochClosureIdV1,
    LAYERED_TICK_MERGE_EPOCH_ORCHESTRATION_CONTRACT_V1_DEFINED,
    LayeredEpochOrchestrationBindPrepRequestV1,
    LayeredEpochSideStateIdentityV1,
    LayeredTradingEpochStepV1,
    PRODUCTIVE_CYCLE_LAYERED_CORE_BIND_ENABLED,
    REGIME_SIDESTATE_MAPPING_CONTRACT_AUTHORIZED,
    validate_c4_entry_exit_epoch_boundary_v1,
    validate_deterministic_epoch_step_order_v1,
    validate_exactly_one_layered_sidestate_writer_v1,
    validate_explicit_prior_next_identity_v1,
    validate_layered_epoch_activation_readiness_v1,
    validate_layered_epoch_orchestration_bind_prep_v1,
    validate_no_parallel_legacy_transition_writer_v1,
)

_REPO = Path(__file__).resolve().parents[2]
_CYCLE_SOURCE = (
    _REPO
    / "src/ops/full_core_live_path_composition_root_v1/current_productive_master_v2_runtime_cycle_v1.py"
)
_REPLAY_SOURCE = _REPO / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
_TRANSITION_STATE_SOURCE = _REPO / "src/trading/master_v2/double_play_state.py"


def _bind_prep(
    *,
    prior: SideState = SideState.NEUTRAL_OBSERVE,
    nxt: SideState = SideState.LONG_ARMED_NEUTRAL_START,
    regime_write: bool = True,
    mechanical_write: bool = False,
    legacy_transition: bool = False,
    layered_mode: bool = True,
) -> LayeredEpochOrchestrationBindPrepRequestV1:
    return LayeredEpochOrchestrationBindPrepRequestV1(
        trading_epoch=1,
        prior_side_state=prior,
        canonical_next_side_state=nxt,
        c4_entry_exit_sidestate_epoch=C4EntryExitSideStateEpochV1.POST_CANONICAL_NEXT_SIDE_STATE,
        c4_consumes_side_state=nxt,
        entry_exit_consumes_side_state=nxt,
        regime_bound_write_asserted=regime_write,
        mechanical_write_asserted=mechanical_write,
        legacy_transition_state_writer_would_run=legacy_transition,
        layered_bind_mode_active=layered_mode,
        b2_scope_event_provenance_closed=False,
        b3_lifecycle_persistence_closed=False,
        b4_p57_state_switch_evidence_closed=False,
    )


def test_contract_flags_and_external_closure_ids() -> None:
    assert LAYERED_TICK_MERGE_EPOCH_ORCHESTRATION_CONTRACT_V1_DEFINED is True
    assert REGIME_SIDESTATE_MAPPING_CONTRACT_AUTHORIZED is True
    assert PRODUCTIVE_CYCLE_LAYERED_CORE_BIND_ENABLED is True
    assert ExternalEpochClosureIdV1.B2_SCOPE_EVENT_PROVENANCE.value == "b2_scope_event_provenance"
    assert (
        ExternalEpochClosureIdV1.B3_P58B_LIFECYCLE_PERSISTENCE.value
        == "b3_p58b_lifecycle_persistence"
    )
    assert (
        ExternalEpochClosureIdV1.B4_P57_TO_STATE_SWITCH_EVIDENCE.value
        == "b4_p57_to_state_switch_evidence"
    )


def test_deterministic_epoch_ordering_is_fixed_and_monotonic() -> None:
    assert len(CANONICAL_LAYERED_EPOCH_STEP_ORDER) == 8
    assert (
        CANONICAL_LAYERED_EPOCH_STEP_ORDER[0]
        is LayeredTradingEpochStepV1.PRIOR_PERSISTED_STATE_LOAD
    )
    assert (
        CANONICAL_LAYERED_EPOCH_STEP_ORDER[5] is LayeredTradingEpochStepV1.CANONICAL_NEXT_SIDE_STATE
    )
    assert (
        CANONICAL_LAYERED_EPOCH_STEP_ORDER[6]
        is LayeredTradingEpochStepV1.C4_AND_ENTRY_EXIT_CONSUMPTION
    )
    ok = validate_deterministic_epoch_step_order_v1(CANONICAL_LAYERED_EPOCH_STEP_ORDER)
    assert ok.ok is True
    bad = validate_deterministic_epoch_step_order_v1(
        (
            LayeredTradingEpochStepV1.C4_AND_ENTRY_EXIT_CONSUMPTION,
            LayeredTradingEpochStepV1.CANONICAL_NEXT_SIDE_STATE,
        )
    )
    assert bad.ok is False
    assert EpochOrchestrationFailureCodeV1.EPOCH_STEP_ORDER_DRIFT.value in bad.failure_codes


def test_explicit_prior_and_next_identity() -> None:
    identity = LayeredEpochSideStateIdentityV1(
        trading_epoch=2,
        prior_side_state=SideState.SHORT_ACTIVE,
        canonical_next_side_state=SideState.SHORT_ACTIVE,
    )
    assert validate_explicit_prior_next_identity_v1(identity).ok is True


def test_exactly_one_sidestate_writer_rejects_dual_regime_and_mechanical() -> None:
    ok = validate_exactly_one_layered_sidestate_writer_v1(
        regime_bound_write_asserted=True,
        mechanical_write_asserted=False,
    )
    assert ok.ok is True
    bad = validate_exactly_one_layered_sidestate_writer_v1(
        regime_bound_write_asserted=True,
        mechanical_write_asserted=True,
    )
    assert bad.ok is False
    assert (
        EpochOrchestrationFailureCodeV1.DUAL_SIDESTATE_WRITER_FORBIDDEN.value in bad.failure_codes
    )


def test_parallel_legacy_transition_and_layered_mode_rejected() -> None:
    bad = validate_no_parallel_legacy_transition_writer_v1(
        layered_bind_mode_active=True,
        legacy_transition_state_writer_would_run=True,
        layered_sidestate_writer_asserted=True,
    )
    assert bad.ok is False
    assert (
        EpochOrchestrationFailureCodeV1.LEGACY_TRANSITION_PARALLEL_LAYERED_WRITER_FORBIDDEN.value
        in bad.failure_codes
    )
    ok = validate_no_parallel_legacy_transition_writer_v1(
        layered_bind_mode_active=False,
        legacy_transition_state_writer_would_run=True,
        layered_sidestate_writer_asserted=False,
    )
    assert ok.ok is True


@pytest.mark.parametrize(
    "epoch_kind",
    [
        C4EntryExitSideStateEpochV1.UNSPECIFIED,
        C4EntryExitSideStateEpochV1.LEGACY_INTEGRATED_REPLAY_PRE_STATE_SWITCH,
    ],
)
def test_c4_entry_exit_boundary_fail_closed_without_post_canonical(
    epoch_kind: C4EntryExitSideStateEpochV1,
) -> None:
    result = validate_c4_entry_exit_epoch_boundary_v1(
        c4_entry_exit_sidestate_epoch=epoch_kind,
        canonical_next_side_state=SideState.LONG_ACTIVE,
        c4_consumes_side_state=SideState.LONG_ACTIVE,
        entry_exit_consumes_side_state=SideState.LONG_ACTIVE,
    )
    assert result.ok is False


def test_c4_entry_exit_must_match_canonical_next_side_state() -> None:
    canonical = SideState.LONG_ARMED
    ok = validate_c4_entry_exit_epoch_boundary_v1(
        c4_entry_exit_sidestate_epoch=C4EntryExitSideStateEpochV1.POST_CANONICAL_NEXT_SIDE_STATE,
        canonical_next_side_state=canonical,
        c4_consumes_side_state=canonical,
        entry_exit_consumes_side_state=canonical,
    )
    assert ok.ok is True
    drift = validate_c4_entry_exit_epoch_boundary_v1(
        c4_entry_exit_sidestate_epoch=C4EntryExitSideStateEpochV1.POST_CANONICAL_NEXT_SIDE_STATE,
        canonical_next_side_state=canonical,
        c4_consumes_side_state=SideState.SHORT_ACTIVE,
        entry_exit_consumes_side_state=canonical,
    )
    assert drift.ok is False
    assert (
        EpochOrchestrationFailureCodeV1.C4_CONSUMES_DIFFERENT_SIDESTATE_THAN_CANONICAL.value
        in drift.failure_codes
    )


def test_bind_prep_happy_path_post_canonical_c4_boundary() -> None:
    result = validate_layered_epoch_orchestration_bind_prep_v1(_bind_prep())
    assert result.ok is True


def test_activation_readiness_fail_closed_while_b2_b3_b4_open() -> None:
    result = validate_layered_epoch_activation_readiness_v1(_bind_prep())
    assert result.ok is False
    codes = set(result.failure_codes)
    assert EpochOrchestrationFailureCodeV1.EXTERNAL_CLOSURE_B2_NOT_CLOSED.value in codes
    assert EpochOrchestrationFailureCodeV1.EXTERNAL_CLOSURE_B3_NOT_CLOSED.value in codes
    assert EpochOrchestrationFailureCodeV1.EXTERNAL_CLOSURE_B4_NOT_CLOSED.value in codes
    assert EpochOrchestrationFailureCodeV1.ACTIVATION_MAPPING_NOT_AUTHORIZED.value not in codes
    assert EpochOrchestrationFailureCodeV1.ACTIVATION_PRODUCTIVE_BIND_NOT_ENABLED.value not in codes


def test_activation_readiness_passes_when_b2_b3_b4_closed_and_mapping_authorized() -> None:
    ready = LayeredEpochOrchestrationBindPrepRequestV1(
        trading_epoch=1,
        prior_side_state=SideState.NEUTRAL_OBSERVE,
        canonical_next_side_state=SideState.LONG_ARMED_NEUTRAL_START,
        c4_entry_exit_sidestate_epoch=C4EntryExitSideStateEpochV1.POST_CANONICAL_NEXT_SIDE_STATE,
        c4_consumes_side_state=SideState.LONG_ARMED_NEUTRAL_START,
        entry_exit_consumes_side_state=SideState.LONG_ARMED_NEUTRAL_START,
        regime_bound_write_asserted=True,
        mechanical_write_asserted=False,
        legacy_transition_state_writer_would_run=False,
        layered_bind_mode_active=True,
        b2_scope_event_provenance_closed=True,
        b3_lifecycle_persistence_closed=True,
        b4_p57_state_switch_evidence_closed=True,
    )
    result = validate_layered_epoch_activation_readiness_v1(ready)
    assert result.ok is True


def test_productive_cycle_wires_p5_10_bind_not_p5_10a_contract() -> None:
    cycle = _CYCLE_SOURCE.read_text(encoding="utf-8")
    replay = _REPLAY_SOURCE.read_text(encoding="utf-8")
    transition = _TRANSITION_STATE_SOURCE.read_text(encoding="utf-8")
    assert "p5_10_productive_activation_and_binding_v1" in cycle
    assert "p5_10a_layered_tick_merge_epoch_orchestration_contract_v1" not in cycle
    assert "p5_10a_layered_tick_merge_epoch_orchestration_contract_v1" not in replay
    assert "p5_10a" not in transition
