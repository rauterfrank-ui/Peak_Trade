"""P5.9D layered mechanical SideState FSM contract (no productive wiring)."""

from __future__ import annotations

from pathlib import Path

import pytest

from trading.master_v2.double_play_entry_exit_policy_v0 import ExistingPositionSide
from trading.master_v2.double_play_state import ScopeEvent, SideState
from trading.master_v2.naked_mv2_dp_regime_v1 import NakedRegimeV1

from src.ops.p5_2_productive_cycle_seam_invoke_and_authority_bind_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    FINAL_D_T_FORMULA_SELECTED,
    PRODUCTIVE_CYCLE_LAYERED_CORE_BIND_ENABLED,
    REGIME_SIDESTATE_MAPPING_CONTRACT_AUTHORIZED,
)
from src.ops.p5_7_regime_sidestate_projection_mapping_contract_v1 import (
    RegimeSideStateProjectionInputV1,
    RegimeSideStateProjectionPhaseV1,
    project_regime_to_sidestate_v1,
)
from src.ops.p5_9d_layered_mechanical_sidestate_fsm_contract_v1 import (
    AuthorizedMechanicalRowV1,
    CZ4_SYNTHETIC_NOOP_MATCHED_CONDITION,
    ForbiddenRegimeBoundLegacyRowV1,
    LAYERED_MECHANICAL_FSM_CONTRACT_V1_DEFINED,
    LayeredSidestateEpochWriteRequestV1,
    MECHANICAL_COMPLETION_ROW_IDS,
    MechanicalFsmFailureCodeV1,
    MechanicalScopeEventProvenanceV1,
    P57MechanicalFsmHandoffRequestV1,
    all_authorized_mechanical_rows_v1,
    all_forbidden_regime_bound_legacy_rows_v1,
    resolve_mechanical_scope_event_provenance_v1,
    validate_layered_mechanical_transition_v1,
    validate_mechanical_does_not_infer_regime_v1,
    validate_p5_7_to_mechanical_fsm_handoff_v1,
    validate_regime_bound_projection_no_active_v1,
    validate_single_writer_per_trading_epoch_v1,
)

_REPO = Path(__file__).resolve().parents[2]
_CYCLE_SOURCE = (
    _REPO
    / "src/ops/full_core_live_path_composition_root_v1/current_productive_master_v2_runtime_cycle_v1.py"
)
_TRANSITION_STATE_SOURCE = _REPO / "src/trading/master_v2/double_play_state.py"
_LEGACY = MechanicalScopeEventProvenanceV1.LEGACY_DETERMINISTIC_SCOPE_EVENT_GENERATOR
_CZ4 = MechanicalScopeEventProvenanceV1.CZ4_SYNTHETIC_NOOP


def test_guard_constants_unchanged() -> None:
    assert LAYERED_MECHANICAL_FSM_CONTRACT_V1_DEFINED is True
    assert REGIME_SIDESTATE_MAPPING_CONTRACT_AUTHORIZED is True
    assert PRODUCTIVE_CYCLE_LAYERED_CORE_BIND_ENABLED is True
    assert FINAL_D_T_FORMULA_SELECTED is False
    assert EXTERNAL_EFFECT_AUTHORIZED is False


@pytest.mark.parametrize(
    ("prior", "event", "next_side", "forbidden_id"),
    [
        (
            SideState.NEUTRAL_OBSERVE,
            ScopeEvent.UPSCOPE_CONFIRMED,
            SideState.LONG_ARMED_NEUTRAL_START,
            ForbiddenRegimeBoundLegacyRowV1.T15_NEUTRAL_UPSCOPE_TO_LONG_ARMED_NEUTRAL_START,
        ),
        (
            SideState.NEUTRAL_OBSERVE,
            ScopeEvent.DOWNSCOPE_CONFIRMED,
            SideState.SHORT_ARMED_NEUTRAL_START,
            ForbiddenRegimeBoundLegacyRowV1.T16_NEUTRAL_DOWNSCOPE_TO_SHORT_ARMED_NEUTRAL_START,
        ),
        (
            SideState.LONG_ACTIVE,
            ScopeEvent.DOWNSCOPE_CONFIRMED,
            SideState.SWITCH_LONG_TO_SHORT_PENDING,
            ForbiddenRegimeBoundLegacyRowV1.T7_LONG_ACTIVE_DOWNSCOPE_TO_SWITCH_LONG_TO_SHORT_PENDING,
        ),
        (
            SideState.SHORT_ACTIVE,
            ScopeEvent.DOWNSCOPE_CONFIRMED,
            SideState.SWITCH_SHORT_TO_LONG_PENDING,
            ForbiddenRegimeBoundLegacyRowV1.T11_SHORT_ACTIVE_DOWNSCOPE_TO_SWITCH_SHORT_TO_LONG_PENDING,
        ),
    ],
)
def test_forbidden_legacy_rows_fail_closed(
    prior: SideState,
    event: ScopeEvent,
    next_side: SideState,
    forbidden_id: ForbiddenRegimeBoundLegacyRowV1,
) -> None:
    result = validate_layered_mechanical_transition_v1(
        prior_side_state=prior,
        scope_event=event,
        next_side_state=next_side,
        scope_event_provenance=_LEGACY,
    )
    assert result.ok is False
    assert (
        MechanicalFsmFailureCodeV1.FORBIDDEN_REGIME_BOUND_LEGACY_ROW.value in result.failure_codes
    )
    assert result.forbidden_legacy_row_id is forbidden_id


@pytest.mark.parametrize(
    ("prior", "event", "next_side", "row_id"),
    [
        (
            SideState.LONG_ARMED_NEUTRAL_START,
            ScopeEvent.UPSCOPE_CONFIRMED,
            SideState.LONG_ACTIVE,
            AuthorizedMechanicalRowV1.MECH_T14_LONG_ARMED_TO_LONG_ACTIVE,
        ),
        (
            SideState.SWITCH_LONG_TO_SHORT_PENDING,
            ScopeEvent.DOWNSCOPE_CONFIRMED,
            SideState.LONG_BLOCKED,
            AuthorizedMechanicalRowV1.MECH_T8_SWITCH_LONG_PENDING_TO_LONG_BLOCKED,
        ),
        (
            SideState.SHORT_ARMED_NEUTRAL_START,
            ScopeEvent.DOWNSCOPE_CONFIRMED,
            SideState.SHORT_ACTIVE,
            AuthorizedMechanicalRowV1.MECH_T10_SHORT_ARMED_TO_SHORT_ACTIVE,
        ),
    ],
)
def test_authorized_mechanical_completion_rows(
    prior: SideState,
    event: ScopeEvent,
    next_side: SideState,
    row_id: AuthorizedMechanicalRowV1,
) -> None:
    result = validate_layered_mechanical_transition_v1(
        prior_side_state=prior,
        scope_event=event,
        next_side_state=next_side,
        scope_event_provenance=_LEGACY,
    )
    assert result.ok is True
    assert result.mechanical_row_id is row_id
    assert row_id in MECHANICAL_COMPLETION_ROW_IDS


def test_unknown_row_rejected() -> None:
    result = validate_layered_mechanical_transition_v1(
        prior_side_state=SideState.CHOP_GUARD_BLOCK,
        scope_event=ScopeEvent.NOOP,
        next_side_state=SideState.NEUTRAL_OBSERVE,
        scope_event_provenance=_LEGACY,
    )
    assert result.ok is False
    assert MechanicalFsmFailureCodeV1.MECHANICAL_ROW_UNKNOWN.value in result.failure_codes


def test_unclassified_transition_rejected() -> None:
    result = validate_layered_mechanical_transition_v1(
        prior_side_state=SideState.LONG_ACTIVE,
        scope_event=ScopeEvent.NOOP,
        next_side_state=SideState.SHORT_ACTIVE,
        scope_event_provenance=_LEGACY,
    )
    assert result.ok is False
    assert MechanicalFsmFailureCodeV1.MECHANICAL_ROW_NOT_AUTHORIZED.value in result.failure_codes


def test_competing_regime_and_mechanical_writer_rejected() -> None:
    result = validate_single_writer_per_trading_epoch_v1(
        LayeredSidestateEpochWriteRequestV1(
            trading_epoch=1,
            regime_bound_write_asserted=True,
            mechanical_write_asserted=True,
        )
    )
    assert result.ok is False
    assert (
        MechanicalFsmFailureCodeV1.COMPETING_REGIME_AND_MECHANICAL_WRITER.value
        in result.failure_codes
    )


def test_mechanical_cannot_infer_regime() -> None:
    bad = validate_mechanical_does_not_infer_regime_v1(inferred_regime=NakedRegimeV1.BULL)
    assert bad.ok is False
    assert (
        MechanicalFsmFailureCodeV1.MECHANICAL_REGIME_INFERENCE_FORBIDDEN.value in bad.failure_codes
    )
    ok = validate_mechanical_does_not_infer_regime_v1(inferred_regime=None)
    assert ok.ok is True


def test_active_not_from_regime_bound_projection_validator() -> None:
    for active in (SideState.LONG_ACTIVE, SideState.SHORT_ACTIVE):
        result = validate_regime_bound_projection_no_active_v1(active)
        assert result.ok is False
        assert (
            MechanicalFsmFailureCodeV1.REGIME_BOUND_ACTIVE_FROM_REGIME_FORBIDDEN.value
            in result.failure_codes
        )


def test_p5_7_initial_seed_never_projects_active() -> None:
    proj = project_regime_to_sidestate_v1(
        RegimeSideStateProjectionInputV1(
            regime_pre=NakedRegimeV1.BULL,
            regime_post=NakedRegimeV1.BULL,
            switch_condition_met=False,
            prior_side_state=SideState.NEUTRAL_OBSERVE,
            phase=RegimeSideStateProjectionPhaseV1.INITIAL_SEED,
            venue_flat=True,
            existing_position_side=ExistingPositionSide.NONE,
        )
    )
    assert proj.ok is True
    assert proj.projected_side_state is not None
    assert validate_regime_bound_projection_no_active_v1(proj.projected_side_state).ok is True
    assert proj.projected_side_state not in (
        SideState.LONG_ACTIVE,
        SideState.SHORT_ACTIVE,
    )


def test_completion_requires_legacy_scope_provenance() -> None:
    result = validate_layered_mechanical_transition_v1(
        prior_side_state=SideState.LONG_ARMED,
        scope_event=ScopeEvent.UPSCOPE_CONFIRMED,
        next_side_state=SideState.LONG_ACTIVE,
        scope_event_provenance=MechanicalScopeEventProvenanceV1.UNSPECIFIED,
    )
    assert result.ok is False
    assert (
        MechanicalFsmFailureCodeV1.MECHANICAL_COMPLETION_SCOPE_PROVENANCE_REQUIRED.value
        in result.failure_codes
    )


def test_cz4_synthetic_noop_cannot_authorize_completion() -> None:
    assert (
        resolve_mechanical_scope_event_provenance_v1(
            legacy_deterministic_generator_evidence=False,
            cz4_delegated_noop_matched=True,
        )
        is _CZ4
    )
    result = validate_layered_mechanical_transition_v1(
        prior_side_state=SideState.LONG_ARMED_NEUTRAL_START,
        scope_event=ScopeEvent.UPSCOPE_CONFIRMED,
        next_side_state=SideState.LONG_ACTIVE,
        scope_event_provenance=_CZ4,
    )
    assert result.ok is False
    assert (
        MechanicalFsmFailureCodeV1.MECHANICAL_COMPLETION_CZ4_NOOP_FORBIDDEN.value
        in result.failure_codes
    )


def test_cz4_marker_matches_delegated_replay_contract() -> None:
    assert CZ4_SYNTHETIC_NOOP_MATCHED_CONDITION == "p5_cz4_delegated_noop"


def test_p5_7_handoff_requires_matching_prior() -> None:
    bad = validate_p5_7_to_mechanical_fsm_handoff_v1(
        P57MechanicalFsmHandoffRequestV1(
            p5_7_projected_side_state=SideState.LONG_ARMED_NEUTRAL_START,
            mechanical_fsm_input_prior_side_state=SideState.NEUTRAL_OBSERVE,
        )
    )
    assert bad.ok is False
    assert MechanicalFsmFailureCodeV1.P5_7_HANDOFF_PRIOR_MISMATCH.value in bad.failure_codes
    ok = validate_p5_7_to_mechanical_fsm_handoff_v1(
        P57MechanicalFsmHandoffRequestV1(
            p5_7_projected_side_state=SideState.SHORT_ARMED_NEUTRAL_START,
            mechanical_fsm_input_prior_side_state=SideState.SHORT_ARMED_NEUTRAL_START,
        )
    )
    assert ok.ok is True
    assert ok.provenance_surface is not None
    assert ok.provenance_surface.authority_domain.value == "regime_bound"


def test_legacy_productive_cycle_untouched() -> None:
    text = _CYCLE_SOURCE.read_text(encoding="utf-8")
    assert "p5_9d_layered_mechanical_sidestate_fsm_contract_v1" not in text


def test_transition_state_file_not_modified_in_this_wp() -> None:
    assert _TRANSITION_STATE_SOURCE.is_file()
    assert "p5_9d" not in _TRANSITION_STATE_SOURCE.read_text(encoding="utf-8")


def test_forbidden_and_mechanical_catalogs_complete() -> None:
    assert len(all_forbidden_regime_bound_legacy_rows_v1()) == 4
    assert len(all_authorized_mechanical_rows_v1()) == 12
