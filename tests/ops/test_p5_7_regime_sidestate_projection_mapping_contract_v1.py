"""P5.7 regime→SideState projection mapping contract (no productive wiring)."""

from __future__ import annotations

from pathlib import Path

import pytest

from trading.master_v2.deterministic_scope_event_generator_v1 import ScopeDirectionState
from trading.master_v2.double_play_entry_exit_policy_v0 import ExistingPositionSide
from trading.master_v2.double_play_state import SideState
from trading.master_v2.naked_mv2_dp_regime_v1 import NakedRegimeV1

from src.ops.p5_2_productive_cycle_seam_invoke_and_authority_bind_v1.constants_v1 import (
    REGIME_SIDESTATE_MAPPING_CONTRACT_AUTHORIZED,
)
from src.ops.p5_7_regime_sidestate_projection_mapping_contract_v1 import (
    AUTHORITY_CUTOVER_OCCURRED,
    CONTRACT_VERSION,
    MAPPING_CONTRACT_V1_DEFINED,
    P5_AUTHORITY_CUTOVER_AUTHORIZED,
    PRODUCTIVE_CYCLE_LAYERED_CORE_BIND_ENABLED,
    RegimeSideStateProjectionFailureCodeV1,
    RegimeSideStateProjectionInputV1,
    RegimeSideStateProjectionPhaseV1,
    all_naked_regime_domain_v1,
    all_sidestate_domain_v1,
    project_regime_to_sidestate_v1,
    regime_to_scope_direction_v1,
    validate_no_sidestate_to_regime_backflow_v1,
)

_REPO = Path(__file__).resolve().parents[2]
_CYCLE_SOURCE = (
    _REPO
    / "src/ops/full_core_live_path_composition_root_v1/current_productive_master_v2_runtime_cycle_v1.py"
)


def _inp(**overrides: object) -> RegimeSideStateProjectionInputV1:
    base = dict(
        regime_pre=NakedRegimeV1.BULL,
        regime_post=NakedRegimeV1.BULL,
        switch_condition_met=False,
        prior_side_state=SideState.NEUTRAL_OBSERVE,
        phase=RegimeSideStateProjectionPhaseV1.MECHANICAL_STEP,
        venue_flat=True,
        existing_position_side=ExistingPositionSide.NONE,
    )
    base.update(overrides)
    return RegimeSideStateProjectionInputV1(**base)  # type: ignore[arg-type]


def test_guard_constants_unchanged() -> None:
    assert CONTRACT_VERSION == "regime_sidestate_projection_mapping.v1"
    assert MAPPING_CONTRACT_V1_DEFINED is True
    assert REGIME_SIDESTATE_MAPPING_CONTRACT_AUTHORIZED is True
    assert PRODUCTIVE_CYCLE_LAYERED_CORE_BIND_ENABLED is True
    assert P5_AUTHORITY_CUTOVER_AUTHORIZED is False
    assert AUTHORITY_CUTOVER_OCCURRED is False


def test_full_sidestate_and_regime_domains() -> None:
    assert all_naked_regime_domain_v1() == (NakedRegimeV1.BULL, NakedRegimeV1.BEAR)
    assert len(all_sidestate_domain_v1()) == len(SideState)
    assert set(all_sidestate_domain_v1()) == set(SideState)


def test_regime_orientation_symmetry_matches_l9_rule() -> None:
    assert regime_to_scope_direction_v1(NakedRegimeV1.BULL) is ScopeDirectionState.LONG
    assert regime_to_scope_direction_v1(NakedRegimeV1.BEAR) is ScopeDirectionState.SHORT


def test_no_switch_preserves_prior_sidestate() -> None:
    result = project_regime_to_sidestate_v1(
        _inp(prior_side_state=SideState.LONG_ARMED_NEUTRAL_START)
    )
    assert result.ok is True
    assert result.projected_side_state is SideState.LONG_ARMED_NEUTRAL_START


def test_initial_flat_seed_armed_neutral_start_not_active() -> None:
    result = project_regime_to_sidestate_v1(
        _inp(
            regime_pre=NakedRegimeV1.BEAR,
            regime_post=NakedRegimeV1.BEAR,
            phase=RegimeSideStateProjectionPhaseV1.INITIAL_SEED,
        )
    )
    assert result.ok is True
    assert result.projected_side_state is SideState.SHORT_ARMED_NEUTRAL_START


@pytest.mark.parametrize(
    ("pre", "post", "prior", "expected"),
    [
        (
            NakedRegimeV1.BULL,
            NakedRegimeV1.BEAR,
            SideState.LONG_ACTIVE,
            SideState.SWITCH_LONG_TO_SHORT_PENDING,
        ),
        (
            NakedRegimeV1.BEAR,
            NakedRegimeV1.BULL,
            SideState.SHORT_ACTIVE,
            SideState.SWITCH_SHORT_TO_LONG_PENDING,
        ),
    ],
)
def test_switch_pending_symmetry(
    pre: NakedRegimeV1,
    post: NakedRegimeV1,
    prior: SideState,
    expected: SideState,
) -> None:
    result = project_regime_to_sidestate_v1(
        _inp(
            regime_pre=pre,
            regime_post=post,
            switch_condition_met=True,
            prior_side_state=prior,
            venue_flat=False,
            existing_position_side=(
                ExistingPositionSide.LONG
                if prior is SideState.LONG_ACTIVE
                else ExistingPositionSide.SHORT
            ),
        )
    )
    assert result.ok is True
    assert result.projected_side_state is expected


def test_flat_switch_uses_armed_neutral_start() -> None:
    result = project_regime_to_sidestate_v1(
        _inp(
            regime_pre=NakedRegimeV1.BULL,
            regime_post=NakedRegimeV1.BEAR,
            switch_condition_met=True,
            prior_side_state=SideState.LONG_ARMED_NEUTRAL_START,
        )
    )
    assert result.ok is True
    assert result.projected_side_state is SideState.SHORT_ARMED_NEUTRAL_START


def test_seal_switch_flag_inconsistent_rejected() -> None:
    result = project_regime_to_sidestate_v1(
        _inp(
            regime_pre=NakedRegimeV1.BULL,
            regime_post=NakedRegimeV1.BEAR,
            switch_condition_met=False,
        )
    )
    assert result.ok is False
    assert (
        RegimeSideStateProjectionFailureCodeV1.SEAL_SWITCH_FLAG_INCONSISTENT.value
        in result.failure_codes
    )


def test_occupancy_flat_contradiction_rejected() -> None:
    result = project_regime_to_sidestate_v1(
        _inp(
            venue_flat=True,
            existing_position_side=ExistingPositionSide.LONG,
        )
    )
    assert result.ok is False
    assert (
        RegimeSideStateProjectionFailureCodeV1.OCCUPANCY_CONTRADICTS_VENUE_FLAT.value
        in result.failure_codes
    )


def test_active_from_regime_alone_forbidden_on_flat_switch() -> None:
    result = project_regime_to_sidestate_v1(
        _inp(
            regime_pre=NakedRegimeV1.BULL,
            regime_post=NakedRegimeV1.BULL,
            switch_condition_met=False,
            prior_side_state=SideState.NEUTRAL_OBSERVE,
            phase=RegimeSideStateProjectionPhaseV1.MECHANICAL_STEP,
        )
    )
    assert result.ok is True
    assert result.projected_side_state is SideState.NEUTRAL_OBSERVE


def test_no_sidestate_to_regime_backflow() -> None:
    ok = validate_no_sidestate_to_regime_backflow_v1(
        side_state=SideState.LONG_ACTIVE,
        inferred_regime=None,
    )
    assert ok.ok is True
    bad = validate_no_sidestate_to_regime_backflow_v1(
        side_state=SideState.LONG_ACTIVE,
        inferred_regime=NakedRegimeV1.BULL,
    )
    assert bad.ok is False
    assert (
        RegimeSideStateProjectionFailureCodeV1.SIDESTATE_TO_REGIME_BACKFLOW_FORBIDDEN.value
        in bad.failure_codes
    )


def test_legacy_productive_cycle_unchanged() -> None:
    text = _CYCLE_SOURCE.read_text(encoding="utf-8")
    assert "p5_7_regime_sidestate_projection_mapping_contract_v1" not in text
    assert "run_p5_layered_core_authority_seam_v1" not in text


def test_cz4_switch_delegation_allowed_when_mapping_authorized() -> None:
    from src.ops.p5_2_productive_cycle_seam_invoke_and_authority_bind_v1.contract_v1 import (
        validate_cz4_delegation_authority_bind_v1,
    )
    from trading.master_v2.layered_core_authority_seal_v1 import (
        build_layered_core_authority_seal_v1,
    )

    seal = build_layered_core_authority_seal_v1(
        seal_id="p57-switch-authorized",
        instrument_id="ETH-PERP",
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


def test_mapping_domain_matrix_no_switch_stable_armed_states() -> None:
    for prior in (
        SideState.LONG_ARMED,
        SideState.SHORT_ARMED,
        SideState.LONG_BLOCKED,
        SideState.SHORT_BLOCKED,
    ):
        result = project_regime_to_sidestate_v1(_inp(prior_side_state=prior))
        assert result.ok is True
        assert result.projected_side_state is prior
