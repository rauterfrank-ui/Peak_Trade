"""P5.2 productive-cycle authority bind contract (disabled by default)."""

from __future__ import annotations

from pathlib import Path

from trading.master_v2.double_play_state import SideState
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    run_integrated_offline_trading_logic_replay_v1,
)
from trading.master_v2.layered_core_authority_seal_v1 import build_layered_core_authority_seal_v1
from trading.master_v2.naked_mv2_dp_regime_v1 import NakedRegimeV1

from src.ops.p5_2_productive_cycle_seam_invoke_and_authority_bind_v1 import (
    AUTHORITY_CUTOVER_OCCURRED,
    EXTERNAL_EFFECT_AUTHORIZED,
    FINAL_D_T_FORMULA_SELECTED,
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    P4_PRODUCTIVE_BINDING,
    P5_AUTHORITY_CUTOVER_AUTHORIZED,
    PRODUCTIVE_CYCLE_LAYERED_CORE_BIND_ENABLED,
    PRODUCTIVE_DECISION_PATH_CUTOVER_ENABLED,
    REGIME_SIDESTATE_MAPPING_CONTRACT_AUTHORIZED,
    AuthorityBindFailureCodeV1,
    ProductiveCycleAuthorityBindRequestV1,
    ProductiveDecisionAuthorityModeV1,
    SideStateSeedClassV1,
    classify_side_state_seed_v1,
    validate_cz4_delegation_authority_bind_v1,
    validate_productive_cycle_authority_bind_v1,
)

from tests.trading.master_v2.test_integrated_replay_p5_cz4_delegated_seal_v1 import (
    _existing_scope,
    _valid_seal,
)
from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import (
    _INSTRUMENT,
    _replay_input,
)

_CYCLE_SOURCE = (
    Path(__file__).resolve().parents[2]
    / "src/ops/full_core_live_path_composition_root_v1/current_productive_master_v2_runtime_cycle_v1.py"
)


def test_guard_constants_unchanged() -> None:
    assert P5_AUTHORITY_CUTOVER_AUTHORIZED is False
    assert PRODUCTIVE_DECISION_PATH_CUTOVER_ENABLED is False
    assert P4_PRODUCTIVE_BINDING is False
    assert AUTHORITY_CUTOVER_OCCURRED is False
    assert PRODUCTIVE_CYCLE_LAYERED_CORE_BIND_ENABLED is False
    assert REGIME_SIDESTATE_MAPPING_CONTRACT_AUTHORIZED is False
    assert FINAL_D_T_FORMULA_SELECTED is False
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert MAX_POSITIONS_EFFECTIVE == 1
    assert EXTERNAL_EFFECT_AUTHORIZED is False


def test_productive_bind_disabled_by_default_rejects_layered_request() -> None:
    req = ProductiveCycleAuthorityBindRequestV1(
        productive_layered_core_bind_requested=True,
        decision_authority_mode=ProductiveDecisionAuthorityModeV1.LAYERED_CORE_SEAL_DELEGATED,
        seal_present=True,
        seal_validation_ok=True,
        cz4_delegation_intended=True,
        legacy_scope_writer_would_run=False,
        legacy_transition_writer_would_run=False,
        legacy_dynamic_boundary_writer_would_run=False,
        legacy_canonical_distances_as_d_t_authority=False,
        side_state_seed_class=SideStateSeedClassV1.OBSERVATION_OCCUPANCY_INPUT,
        fallback_to_legacy_on_missing_core=False,
    )
    result = validate_productive_cycle_authority_bind_v1(req)
    assert result.ok is False
    assert (
        AuthorityBindFailureCodeV1.PRODUCTIVE_LAYERED_CORE_BIND_DISABLED.value
        in result.failure_codes
    )


def test_dual_writer_rejection_layered_plus_legacy_scope() -> None:
    req = ProductiveCycleAuthorityBindRequestV1(
        productive_layered_core_bind_requested=False,
        decision_authority_mode=ProductiveDecisionAuthorityModeV1.LAYERED_CORE_SEAL_DELEGATED,
        seal_present=True,
        seal_validation_ok=True,
        cz4_delegation_intended=True,
        legacy_scope_writer_would_run=True,
        legacy_transition_writer_would_run=False,
        legacy_dynamic_boundary_writer_would_run=False,
        legacy_canonical_distances_as_d_t_authority=False,
        side_state_seed_class=SideStateSeedClassV1.NONE,
        fallback_to_legacy_on_missing_core=False,
    )
    result = validate_productive_cycle_authority_bind_v1(req)
    assert result.ok is False
    assert (
        AuthorityBindFailureCodeV1.DUAL_DECISION_AUTHORITY_WRITERS_FORBIDDEN.value
        in result.failure_codes
    )
    assert (
        AuthorityBindFailureCodeV1.LEGACY_SCOPE_WRITER_FORBIDDEN_IN_LAYERED_MODE.value
        in result.failure_codes
    )


def test_competing_r_t_and_d_t_rejection_in_layered_mode() -> None:
    req = ProductiveCycleAuthorityBindRequestV1(
        productive_layered_core_bind_requested=False,
        decision_authority_mode=ProductiveDecisionAuthorityModeV1.LAYERED_CORE_SEAL_DELEGATED,
        seal_present=True,
        seal_validation_ok=True,
        cz4_delegation_intended=True,
        legacy_scope_writer_would_run=False,
        legacy_transition_writer_would_run=False,
        legacy_dynamic_boundary_writer_would_run=True,
        legacy_canonical_distances_as_d_t_authority=True,
        side_state_seed_class=SideStateSeedClassV1.NONE,
        fallback_to_legacy_on_missing_core=False,
    )
    result = validate_productive_cycle_authority_bind_v1(req)
    assert result.ok is False
    assert (
        AuthorityBindFailureCodeV1.LEGACY_ANCHOR_WRITER_FORBIDDEN_IN_LAYERED_MODE.value
        in result.failure_codes
    )
    assert (
        AuthorityBindFailureCodeV1.LEGACY_DISTANCES_D_T_AUTHORITY_FORBIDDEN_IN_LAYERED_MODE.value
        in result.failure_codes
    )


def test_legacy_path_forbids_seal_delegation() -> None:
    req = ProductiveCycleAuthorityBindRequestV1(
        productive_layered_core_bind_requested=False,
        decision_authority_mode=ProductiveDecisionAuthorityModeV1.LEGACY_DOUBLE_PLAY_INTEGRATED_REPLAY,
        seal_present=False,
        seal_validation_ok=False,
        cz4_delegation_intended=True,
        legacy_scope_writer_would_run=True,
        legacy_transition_writer_would_run=True,
        legacy_dynamic_boundary_writer_would_run=True,
        legacy_canonical_distances_as_d_t_authority=True,
        side_state_seed_class=SideStateSeedClassV1.OBSERVATION_OCCUPANCY_INPUT,
        fallback_to_legacy_on_missing_core=False,
    )
    result = validate_productive_cycle_authority_bind_v1(req)
    assert result.ok is False
    assert (
        AuthorityBindFailureCodeV1.LEGACY_PATH_FORBIDS_SEAL_DELEGATION.value in result.failure_codes
    )


def test_missing_core_legacy_fallback_forbidden() -> None:
    req = ProductiveCycleAuthorityBindRequestV1(
        productive_layered_core_bind_requested=False,
        decision_authority_mode=ProductiveDecisionAuthorityModeV1.LAYERED_CORE_SEAL_DELEGATED,
        seal_present=False,
        seal_validation_ok=False,
        cz4_delegation_intended=False,
        legacy_scope_writer_would_run=False,
        legacy_transition_writer_would_run=False,
        legacy_dynamic_boundary_writer_would_run=False,
        legacy_canonical_distances_as_d_t_authority=False,
        side_state_seed_class=SideStateSeedClassV1.NONE,
        fallback_to_legacy_on_missing_core=True,
    )
    result = validate_productive_cycle_authority_bind_v1(req)
    assert result.ok is False
    assert (
        AuthorityBindFailureCodeV1.MISSING_CORE_STATE_LEGACY_FALLBACK_FORBIDDEN.value
        in result.failure_codes
    )


def test_venue_cursor_seed_classification_and_core_claim_rejection() -> None:
    assert (
        classify_side_state_seed_v1(
            from_venue_position=True,
            from_cursor_restore=False,
            claims_core_regime_authority=False,
        )
        is SideStateSeedClassV1.OBSERVATION_OCCUPANCY_INPUT
    )
    req = ProductiveCycleAuthorityBindRequestV1(
        productive_layered_core_bind_requested=False,
        decision_authority_mode=ProductiveDecisionAuthorityModeV1.LEGACY_DOUBLE_PLAY_INTEGRATED_REPLAY,
        seal_present=False,
        seal_validation_ok=False,
        cz4_delegation_intended=False,
        legacy_scope_writer_would_run=True,
        legacy_transition_writer_would_run=True,
        legacy_dynamic_boundary_writer_would_run=True,
        legacy_canonical_distances_as_d_t_authority=False,
        side_state_seed_class=SideStateSeedClassV1.CORE_REGIME_AUTHORITY_CLAIM,
        fallback_to_legacy_on_missing_core=False,
    )
    result = validate_productive_cycle_authority_bind_v1(req)
    assert result.ok is False
    assert (
        AuthorityBindFailureCodeV1.VENUE_CURSOR_CANNOT_CLAIM_CORE_REGIME_AUTHORITY.value
        in result.failure_codes
    )


def test_regime_sidestate_ambiguity_rejects_cz4_without_mapping_contract() -> None:
    seal = build_layered_core_authority_seal_v1(
        seal_id="switch-seal",
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
    bind = validate_cz4_delegation_authority_bind_v1(seal=seal, side_state=SideState.LONG_ARMED)
    assert bind.ok is False
    assert (
        AuthorityBindFailureCodeV1.REGIME_SIDESTATE_MAPPING_NOT_AUTHORIZED.value
        in bind.failure_codes
    )


def test_cz4_replay_fail_closed_on_regime_switch_without_mapping() -> None:
    seal = build_layered_core_authority_seal_v1(
        seal_id="switch-seal-replay",
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
    inp = _replay_input(existing_scope=_existing_scope(), layered_core_authority_seal=seal)
    result = run_integrated_offline_trading_logic_replay_v1(inp)
    assert result.replay_pass is False
    assert (
        AuthorityBindFailureCodeV1.REGIME_SIDESTATE_MAPPING_NOT_AUTHORIZED.value
        in result.fail_reasons
    )


def test_cz4_no_switch_seal_still_delegates() -> None:
    seal = _valid_seal()
    inp = _replay_input(existing_scope=_existing_scope(), layered_core_authority_seal=seal)
    result = run_integrated_offline_trading_logic_replay_v1(inp)
    assert result.evidence is not None


def test_current_productive_cycle_unchanged_no_seam_invoke() -> None:
    text = _CYCLE_SOURCE.read_text(encoding="utf-8")
    assert "run_p5_layered_core_authority_seam_v1" not in text
    assert "p5_2_productive_cycle_seam_invoke_and_authority_bind_v1" not in text


def test_baseline_replay_without_seal_unchanged() -> None:
    baseline = run_integrated_offline_trading_logic_replay_v1(_replay_input())
    assert baseline.evidence is not None
