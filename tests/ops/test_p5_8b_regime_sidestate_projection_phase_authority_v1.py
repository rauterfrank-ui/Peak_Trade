"""P5.8B RegimeSideStateProjectionPhase authority (persisted lifecycle; no CZ-4 wire)."""

from __future__ import annotations

import pytest

from trading.master_v2.deterministic_scope_event_generator_v1 import ScopeDirectionState
from trading.master_v2.double_play_entry_exit_policy_v0 import ExistingPositionSide
from trading.master_v2.double_play_state import SideState
from trading.master_v2.naked_mv2_dp_regime_v1 import NakedRegimeV1

from src.ops.p5_2_productive_cycle_seam_invoke_and_authority_bind_v1.constants_v1 import (
    REGIME_SIDESTATE_MAPPING_CONTRACT_AUTHORIZED,
)
from src.ops.p5_5_o_r2_semantic_authority_contracts_v1.constants_v1 import (
    P5_AUTHORITY_CUTOVER_AUTHORIZED,
    PRODUCTIVE_CYCLE_LAYERED_CORE_BIND_ENABLED,
)
from src.ops.p5_7_regime_sidestate_projection_mapping_contract_v1 import (
    RegimeSideStateProjectionInputV1,
    RegimeSideStateProjectionPhaseV1,
    project_regime_to_sidestate_v1,
    regime_to_scope_direction_v1,
    validate_no_sidestate_to_regime_backflow_v1,
)
from src.ops.p5_8b_regime_sidestate_projection_phase_authority_v1 import (
    PHASE_AUTHORITY_CONTRACT_V1_DEFINED,
    PHASE_AUTHORITY_VARIANT,
    PhaseAuthorityFailureCodeV1,
    fresh_regime_sidestate_projection_lifecycle_v1,
    lifecycle_to_dict_v1,
    mark_initial_regime_orientation_seed_consumed_v1,
    parse_lifecycle_v1,
    resolve_regime_sidestate_projection_phase_v1,
)

_INSTRUMENT = "ETH-PERP"


def _resolve(**overrides: object):
    lifecycle = overrides.pop(
        "lifecycle", fresh_regime_sidestate_projection_lifecycle_v1(instrument_id=_INSTRUMENT)
    )
    base = dict(
        lifecycle=lifecycle,
        instrument_id=_INSTRUMENT,
        prior_side_state=SideState.NEUTRAL_OBSERVE,
        venue_flat=True,
        existing_position_side=ExistingPositionSide.NONE,
        switch_condition_met=False,
        regime_pre_equals_post=True,
    )
    base.update(overrides)
    return resolve_regime_sidestate_projection_phase_v1(**base)  # type: ignore[arg-type]


def test_guard_constants_unchanged() -> None:
    assert PHASE_AUTHORITY_CONTRACT_V1_DEFINED is True
    assert PHASE_AUTHORITY_VARIANT == "PERSISTED_STATE_REQUIRED"
    assert REGIME_SIDESTATE_MAPPING_CONTRACT_AUTHORIZED is True
    assert PRODUCTIVE_CYCLE_LAYERED_CORE_BIND_ENABLED is True
    assert P5_AUTHORITY_CUTOVER_AUTHORIZED is False


def test_fresh_flat_neutral_initial_seed() -> None:
    result = _resolve()
    assert result.ok is True
    assert result.phase is RegimeSideStateProjectionPhaseV1.INITIAL_SEED


def test_seed_exactly_once_then_mechanical_step() -> None:
    lifecycle = fresh_regime_sidestate_projection_lifecycle_v1(instrument_id=_INSTRUMENT)
    first = _resolve(lifecycle=lifecycle)
    assert first.phase is RegimeSideStateProjectionPhaseV1.INITIAL_SEED
    consumed = mark_initial_regime_orientation_seed_consumed_v1(lifecycle)
    second = _resolve(
        lifecycle=consumed,
        prior_side_state=SideState.LONG_ARMED_NEUTRAL_START,
    )
    assert second.ok is True
    assert second.phase is RegimeSideStateProjectionPhaseV1.MECHANICAL_STEP


def test_consumed_neutral_flat_fail_closed_no_repeat_seed() -> None:
    lifecycle = mark_initial_regime_orientation_seed_consumed_v1(
        fresh_regime_sidestate_projection_lifecycle_v1(instrument_id=_INSTRUMENT)
    )
    result = _resolve(lifecycle=lifecycle)
    assert result.ok is False
    assert (
        PhaseAuthorityFailureCodeV1.SEED_ALREADY_CONSUMED_NEUTRAL_OBSERVE.value
        in result.failure_codes
    )


def test_switch_independent_of_phase_resolution() -> None:
    lifecycle = fresh_regime_sidestate_projection_lifecycle_v1(instrument_id=_INSTRUMENT)
    result = _resolve(
        lifecycle=lifecycle,
        switch_condition_met=True,
        regime_pre_equals_post=False,
    )
    assert result.ok is True
    assert result.phase is RegimeSideStateProjectionPhaseV1.MECHANICAL_STEP
    proj = project_regime_to_sidestate_v1(
        RegimeSideStateProjectionInputV1(
            regime_pre=NakedRegimeV1.BULL,
            regime_post=NakedRegimeV1.BEAR,
            switch_condition_met=True,
            prior_side_state=SideState.LONG_ACTIVE,
            phase=RegimeSideStateProjectionPhaseV1.MECHANICAL_STEP,
            venue_flat=False,
            existing_position_side=ExistingPositionSide.LONG,
        )
    )
    assert proj.ok is True
    assert proj.projected_side_state is SideState.SWITCH_LONG_TO_SHORT_PENDING


def test_restore_lifecycle_roundtrip() -> None:
    lifecycle = mark_initial_regime_orientation_seed_consumed_v1(
        fresh_regime_sidestate_projection_lifecycle_v1(instrument_id=_INSTRUMENT)
    )
    payload = lifecycle_to_dict_v1(lifecycle)
    restored, failures = parse_lifecycle_v1(payload, expected_instrument_id=_INSTRUMENT)
    assert failures == ()
    assert restored == lifecycle
    result = _resolve(
        lifecycle=restored,
        prior_side_state=SideState.SHORT_ARMED_NEUTRAL_START,
    )
    assert result.phase is RegimeSideStateProjectionPhaseV1.MECHANICAL_STEP


def test_parse_lifecycle_schema_version_mismatch_fail_closed() -> None:
    lifecycle = fresh_regime_sidestate_projection_lifecycle_v1(instrument_id=_INSTRUMENT)
    payload = lifecycle_to_dict_v1(lifecycle)
    payload["schema_version"] = "v0"
    _, failures = parse_lifecycle_v1(payload)
    assert PhaseAuthorityFailureCodeV1.LIFECYCLE_SCHEMA_VERSION_MISMATCH.value in failures


def test_parse_lifecycle_missing_fail_closed() -> None:
    _, failures = parse_lifecycle_v1(None)
    assert PhaseAuthorityFailureCodeV1.LIFECYCLE_PAYLOAD_INVALID.value in failures


def test_bull_bear_symmetry_initial_seed_projection() -> None:
    lifecycle = fresh_regime_sidestate_projection_lifecycle_v1(instrument_id=_INSTRUMENT)
    for regime in (NakedRegimeV1.BULL, NakedRegimeV1.BEAR):
        phase_res = _resolve(lifecycle=lifecycle)
        assert phase_res.phase is RegimeSideStateProjectionPhaseV1.INITIAL_SEED
        proj = project_regime_to_sidestate_v1(
            RegimeSideStateProjectionInputV1(
                regime_pre=regime,
                regime_post=regime,
                switch_condition_met=False,
                prior_side_state=SideState.NEUTRAL_OBSERVE,
                phase=phase_res.phase,
                venue_flat=True,
                existing_position_side=ExistingPositionSide.NONE,
            )
        )
        assert proj.ok is True
        expected = (
            SideState.LONG_ARMED_NEUTRAL_START
            if regime is NakedRegimeV1.BULL
            else SideState.SHORT_ARMED_NEUTRAL_START
        )
        assert proj.projected_side_state is expected
        assert regime_to_scope_direction_v1(regime) in (
            ScopeDirectionState.LONG,
            ScopeDirectionState.SHORT,
        )


def test_no_active_from_regime_on_initial_seed() -> None:
    lifecycle = fresh_regime_sidestate_projection_lifecycle_v1(instrument_id=_INSTRUMENT)
    phase_res = _resolve(lifecycle=lifecycle)
    proj = project_regime_to_sidestate_v1(
        RegimeSideStateProjectionInputV1(
            regime_pre=NakedRegimeV1.BULL,
            regime_post=NakedRegimeV1.BULL,
            switch_condition_met=False,
            prior_side_state=SideState.NEUTRAL_OBSERVE,
            phase=phase_res.phase,
            venue_flat=True,
            existing_position_side=ExistingPositionSide.NONE,
        )
    )
    assert proj.projected_side_state not in (
        SideState.LONG_ACTIVE,
        SideState.SHORT_ACTIVE,
    )


def test_no_sidestate_to_regime_backflow_unchanged() -> None:
    bad = validate_no_sidestate_to_regime_backflow_v1(
        side_state=SideState.LONG_ACTIVE,
        inferred_regime=NakedRegimeV1.BULL,
    )
    assert bad.ok is False


def test_occupied_venue_blocks_initial_seed_resolution() -> None:
    lifecycle = fresh_regime_sidestate_projection_lifecycle_v1(instrument_id=_INSTRUMENT)
    result = _resolve(
        lifecycle=lifecycle,
        venue_flat=False,
        existing_position_side=ExistingPositionSide.LONG,
        prior_side_state=SideState.LONG_ACTIVE,
    )
    assert result.phase is RegimeSideStateProjectionPhaseV1.MECHANICAL_STEP


def test_non_flat_neutral_with_unconsumed_lifecycle_fail_closed() -> None:
    lifecycle = fresh_regime_sidestate_projection_lifecycle_v1(instrument_id=_INSTRUMENT)
    result = _resolve(lifecycle=lifecycle, venue_flat=False)
    assert result.ok is False
    assert PhaseAuthorityFailureCodeV1.SEED_REQUIRES_FLAT_VENUE.value in result.failure_codes


def test_instrument_binding_mismatch_fail_closed() -> None:
    lifecycle = fresh_regime_sidestate_projection_lifecycle_v1(instrument_id="BTC-PERP")
    result = _resolve(lifecycle=lifecycle, instrument_id=_INSTRUMENT)
    assert result.ok is False
    assert PhaseAuthorityFailureCodeV1.LIFECYCLE_INSTRUMENT_MISMATCH.value in result.failure_codes


@pytest.mark.parametrize(
    "corrupt_key",
    ["schema_name", "instrument_id", "initial_regime_orientation_seed_consumed"],
)
def test_parse_lifecycle_corrupt_field_fail_closed(corrupt_key: str) -> None:
    lifecycle = fresh_regime_sidestate_projection_lifecycle_v1(instrument_id=_INSTRUMENT)
    payload = lifecycle_to_dict_v1(lifecycle)
    if corrupt_key == "schema_name":
        payload[corrupt_key] = "wrong"
    elif corrupt_key == "instrument_id":
        payload[corrupt_key] = ""
    else:
        payload[corrupt_key] = "not-a-bool"
    _, failures = parse_lifecycle_v1(payload)
    assert failures
