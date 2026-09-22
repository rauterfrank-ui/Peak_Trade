"""P5.5 O-R2 semantic authority contracts (no cutover activation)."""

from __future__ import annotations

from pathlib import Path

from trading.master_v2.double_play_sole_authority_quarantine_v1 import (
    CANONICAL_BULL_BEAR_STATE_OWNER,
    CANONICAL_SWITCH_AUTHORITY,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    run_integrated_offline_trading_logic_replay_v1,
)

from src.ops.p5_2_productive_cycle_seam_invoke_and_authority_bind_v1.contract_v1 import (
    ProductiveDecisionAuthorityModeV1,
)
from src.ops.p5_5_o_r2_semantic_authority_contracts_v1 import (
    AUTHORITY_CUTOVER,
    AUTHORITY_CUTOVER_OCCURRED,
    BEAR_TO_SHORT_ACTIVE_IMPLICIT_MAPPING,
    BULL_TO_LONG_ACTIVE_IMPLICIT_MAPPING,
    D_T_FORMULA_SELECTED,
    EXTERNAL_EFFECT_AUTHORIZED,
    FINAL_D_T_FORMULA_SELECTED,
    FULL_CORE_FIRST_TRADING_DECISION_CONSUMER,
    L1_L10_BULL_BEAR_DECISION_AUTHORITY,
    LEGACY_TRANSITION_STATE_AUTHORITY,
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    NUMERIC_FORMULA_AUTHORITY,
    OPTIMIZER_PRODUCTIVE_AUTHORITY,
    OR2AuthorityFailureCodeV1,
    P4_PRODUCTIVE_BINDING,
    P5_AUTHORITY_CUTOVER_AUTHORIZED,
    PRODUCTIVE_BIND_ENABLE,
    PRODUCTIVE_CYCLE_LAYERED_CORE_BIND_ENABLED,
    PRODUCTIVE_DECISION_PATH_CUTOVER_ENABLED,
    REGIME_SIDESTATE_MAPPING_CONTRACT_AUTHORIZED,
    SIDESTATE_AS_COMPETING_BULL_BEAR_AUTHORITY,
    SIDESTATE_CUTOVER_MODEL,
    SIDESTATE_DOWNSTREAM_PROJECTION_LIFECYCLE_OCCUPANCY_ROLE,
    VENUE_POSITION_OCCUPANCY_TRUTH,
    OR2LayeredAuthorityBindRequestV1,
    validate_d_t_authority_gate_v1,
    validate_host_seed_boundary_v1,
    validate_legacy_mode_preserves_transition_state_authority_v1,
    validate_o_r2_layered_authority_bind_v1,
    validate_sidestate_projection_boundary_v1,
)
from src.ops.productive_decision_host_active_archive_three_family_binding_v1.constants_v1 import (
    PRODUCTIVE_HOST_SYMBOL,
)

from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import (
    _replay_input,
)

_REPO = Path(__file__).resolve().parents[2]
_CYCLE_SOURCE = (
    _REPO
    / "src/ops/full_core_live_path_composition_root_v1/current_productive_master_v2_runtime_cycle_v1.py"
)


def _layered_request(**overrides: object) -> OR2LayeredAuthorityBindRequestV1:
    base = dict(
        sidestate_cutover_model=SIDESTATE_CUTOVER_MODEL,
        decision_authority_mode=ProductiveDecisionAuthorityModeV1.LAYERED_CORE_SEAL_DELEGATED,
        competing_sidestate_bull_bear_decision_writer_would_run=False,
        implicit_bull_to_long_active_mapping=False,
        implicit_bear_to_short_active_mapping=False,
        venue_claims_core_regime_authority=False,
        cursor_claims_core_regime_authority=False,
        from_venue_position=False,
        from_cursor_restore=False,
        legacy_fallback_on_missing_core=False,
        sidestate_backflow_to_core=False,
        active_side_state_derived_from_regime_only=False,
        total_regime_sidestate_bijection_claimed=False,
        sidestate_projection_required_for_cycle=True,
        sidestate_projection_authorized_and_implemented=True,
        legacy_canonical_distances_as_d_t_authority=False,
        authorized_proposed_d_t_present=True,
        legacy_scope_or_cm_writer_would_run_with_valid_layered_seal=False,
        explicit_dt_proposal_promoted_to_numeric_authority=False,
    )
    base.update(overrides)
    return OR2LayeredAuthorityBindRequestV1(**base)  # type: ignore[arg-type]


def test_o_r2_owner_tokens_and_guard_constants() -> None:
    assert SIDESTATE_CUTOVER_MODEL == "O-R2"
    assert L1_L10_BULL_BEAR_DECISION_AUTHORITY == "SOLE"
    assert SIDESTATE_AS_COMPETING_BULL_BEAR_AUTHORITY == "FORBIDDEN_IN_LAYERED_MODE"
    assert SIDESTATE_DOWNSTREAM_PROJECTION_LIFECYCLE_OCCUPANCY_ROLE == "PRESERVED"
    assert VENUE_POSITION_OCCUPANCY_TRUTH == "PRESERVED"
    assert BULL_TO_LONG_ACTIVE_IMPLICIT_MAPPING == "FORBIDDEN"
    assert BEAR_TO_SHORT_ACTIVE_IMPLICIT_MAPPING == "FORBIDDEN"
    assert LEGACY_TRANSITION_STATE_AUTHORITY == "PRESERVED_UNTIL_EXPLICIT_CUTOVER"
    assert D_T_FORMULA_SELECTED is False
    assert FINAL_D_T_FORMULA_SELECTED is False
    assert PRODUCTIVE_BIND_ENABLE is False
    assert AUTHORITY_CUTOVER is False
    assert PRODUCTIVE_CYCLE_LAYERED_CORE_BIND_ENABLED is True
    assert P5_AUTHORITY_CUTOVER_AUTHORIZED is False
    assert PRODUCTIVE_DECISION_PATH_CUTOVER_ENABLED is False
    assert P4_PRODUCTIVE_BINDING is False
    assert REGIME_SIDESTATE_MAPPING_CONTRACT_AUTHORIZED is False
    assert NUMERIC_FORMULA_AUTHORITY == "NONE"
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert MAX_POSITIONS_EFFECTIVE == 1
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert OPTIMIZER_PRODUCTIVE_AUTHORITY == "NONE"
    assert AUTHORITY_CUTOVER_OCCURRED is False


def test_legacy_mode_preserves_transition_state_authority() -> None:
    ok = validate_legacy_mode_preserves_transition_state_authority_v1(
        decision_authority_mode=(
            ProductiveDecisionAuthorityModeV1.LEGACY_DOUBLE_PLAY_INTEGRATED_REPLAY
        ),
        legacy_transition_state_is_canonical_sm_writer=True,
    )
    assert ok.ok is True
    assert CANONICAL_BULL_BEAR_STATE_OWNER.endswith("transition_state")
    assert CANONICAL_SWITCH_AUTHORITY.endswith("transition_state")


def test_layered_mode_rejects_competing_sidestate_decision_writer() -> None:
    result = validate_o_r2_layered_authority_bind_v1(
        _layered_request(competing_sidestate_bull_bear_decision_writer_would_run=True)
    )
    assert result.ok is False
    assert (
        OR2AuthorityFailureCodeV1.LAYERED_COMPETING_SIDESTATE_BULL_BEAR_WRITER_FORBIDDEN.value
        in result.failure_codes
    )


def test_implicit_bull_to_long_active_rejected() -> None:
    result = validate_o_r2_layered_authority_bind_v1(
        _layered_request(implicit_bull_to_long_active_mapping=True)
    )
    assert result.ok is False
    assert (
        OR2AuthorityFailureCodeV1.IMPLICIT_BULL_TO_LONG_ACTIVE_FORBIDDEN.value
        in result.failure_codes
    )


def test_implicit_bear_to_short_active_rejected() -> None:
    result = validate_o_r2_layered_authority_bind_v1(
        _layered_request(implicit_bear_to_short_active_mapping=True)
    )
    assert result.ok is False
    assert (
        OR2AuthorityFailureCodeV1.IMPLICIT_BEAR_TO_SHORT_ACTIVE_FORBIDDEN.value
        in result.failure_codes
    )


def test_venue_active_cannot_claim_core_regime_authority() -> None:
    result = validate_host_seed_boundary_v1(
        from_venue_position=True,
        from_cursor_restore=False,
        claims_core_regime_authority=True,
        legacy_fallback_on_missing_core=False,
    )
    assert result.ok is False
    assert (
        OR2AuthorityFailureCodeV1.VENUE_CANNOT_CLAIM_CORE_REGIME_AUTHORITY.value
        in result.failure_codes
    )


def test_cursor_sidestate_cannot_claim_core_regime_authority() -> None:
    result = validate_host_seed_boundary_v1(
        from_venue_position=False,
        from_cursor_restore=True,
        claims_core_regime_authority=True,
        legacy_fallback_on_missing_core=False,
    )
    assert result.ok is False
    assert (
        OR2AuthorityFailureCodeV1.CURSOR_CANNOT_CLAIM_CORE_REGIME_AUTHORITY.value
        in result.failure_codes
    )


def test_missing_core_legacy_fallback_rejected() -> None:
    result = validate_o_r2_layered_authority_bind_v1(
        _layered_request(legacy_fallback_on_missing_core=True)
    )
    assert result.ok is False
    assert (
        OR2AuthorityFailureCodeV1.LEGACY_FALLBACK_ON_MISSING_CORE_FORBIDDEN.value
        in result.failure_codes
    )


def test_sidestate_backflow_to_core_rejected() -> None:
    result = validate_sidestate_projection_boundary_v1(
        sidestate_backflow_to_core=True,
        active_from_regime_only=False,
        total_bijection_claimed=False,
        projection_required=False,
        projection_authorized_and_implemented=True,
    )
    assert result.ok is False
    assert (
        OR2AuthorityFailureCodeV1.SIDESTATE_BACKFLOW_TO_CORE_FORBIDDEN.value in result.failure_codes
    )


def test_missing_projection_fail_closed_in_layered_mode() -> None:
    result = validate_o_r2_layered_authority_bind_v1(
        _layered_request(
            sidestate_projection_required_for_cycle=True,
            sidestate_projection_authorized_and_implemented=False,
        )
    )
    assert result.ok is False
    assert (
        OR2AuthorityFailureCodeV1.PROJECTION_REQUIRED_BUT_NOT_AUTHORIZED.value
        in result.failure_codes
    )


def test_legacy_canonical_distances_as_d_t_rejected_in_layered_mode() -> None:
    result = validate_d_t_authority_gate_v1(
        legacy_canonical_distances_as_d_t_authority=True,
        authorized_proposed_d_t_present=True,
        explicit_dt_proposal_promoted_to_numeric_authority=False,
        layered_mode_active=True,
    )
    assert result.ok is False
    assert (
        OR2AuthorityFailureCodeV1.LEGACY_CANONICAL_DISTANCES_AS_D_T_FORBIDDEN.value
        in result.failure_codes
    )


def test_missing_authorized_d_t_fail_closed() -> None:
    result = validate_d_t_authority_gate_v1(
        legacy_canonical_distances_as_d_t_authority=False,
        authorized_proposed_d_t_present=False,
        explicit_dt_proposal_promoted_to_numeric_authority=False,
        layered_mode_active=True,
    )
    assert result.ok is False
    assert (
        OR2AuthorityFailureCodeV1.MISSING_AUTHORIZED_D_T_FAIL_CLOSED.value in result.failure_codes
    )


def test_dual_legacy_scope_cm_writer_with_layered_seal_rejected() -> None:
    result = validate_o_r2_layered_authority_bind_v1(
        _layered_request(legacy_scope_or_cm_writer_would_run_with_valid_layered_seal=True)
    )
    assert result.ok is False
    assert (
        OR2AuthorityFailureCodeV1.DUAL_LEGACY_SCOPE_CM_WRITER_WITH_LAYERED_SEAL_FORBIDDEN.value
        in result.failure_codes
    )


def test_r03_full_core_first_consumer_not_wallclock_bridge() -> None:
    cycle_text = _CYCLE_SOURCE.read_text(encoding="utf-8")
    assert f"def {FULL_CORE_FIRST_TRADING_DECISION_CONSUMER}" in cycle_text
    assert "run_bridge_cycle_v1" not in cycle_text
    assert FULL_CORE_FIRST_TRADING_DECISION_CONSUMER in cycle_text
    assert PRODUCTIVE_HOST_SYMBOL == "run_bridge_cycle_v1"
    assert FULL_CORE_FIRST_TRADING_DECISION_CONSUMER != PRODUCTIVE_HOST_SYMBOL


def test_current_productive_path_unchanged_no_seam_invoke() -> None:
    text = _CYCLE_SOURCE.read_text(encoding="utf-8")
    assert "run_p5_layered_core_authority_seam_v1" not in text
    assert "p5_5_o_r2_semantic_authority_contracts_v1" not in text
    assert "p5_2_productive_cycle_seam_invoke_and_authority_bind_v1" not in text


def test_baseline_replay_without_seal_unchanged() -> None:
    baseline = run_integrated_offline_trading_logic_replay_v1(_replay_input())
    assert baseline.evidence is not None


def test_layered_minimal_valid_o_r2_bind_request_passes() -> None:
    result = validate_o_r2_layered_authority_bind_v1(_layered_request())
    assert result.ok is True
    assert result.failure_codes == ()
