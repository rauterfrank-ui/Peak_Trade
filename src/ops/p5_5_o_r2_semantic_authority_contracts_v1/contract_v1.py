"""Fail-closed O-R2 semantic authority contracts for future layered cutover (no activation)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Tuple

from src.ops.p5_2_productive_cycle_seam_invoke_and_authority_bind_v1.contract_v1 import (
    ProductiveDecisionAuthorityModeV1,
    SideStateSeedClassV1,
    classify_side_state_seed_v1,
)
from src.ops.p5_5_o_r2_semantic_authority_contracts_v1.constants_v1 import (
    SIDESTATE_CUTOVER_MODEL,
)


class OR2AuthorityFailureCodeV1(str, Enum):
    SIDESTATE_CUTOVER_MODEL_MISMATCH = "sidestate_cutover_model_mismatch"
    LAYERED_COMPETING_SIDESTATE_BULL_BEAR_WRITER_FORBIDDEN = (
        "layered_competing_sidestate_bull_bear_writer_forbidden"
    )
    IMPLICIT_BULL_TO_LONG_ACTIVE_FORBIDDEN = "implicit_bull_to_long_active_forbidden"
    IMPLICIT_BEAR_TO_SHORT_ACTIVE_FORBIDDEN = "implicit_bear_to_short_active_forbidden"
    VENUE_CANNOT_CLAIM_CORE_REGIME_AUTHORITY = "venue_cannot_claim_core_regime_authority"
    CURSOR_CANNOT_CLAIM_CORE_REGIME_AUTHORITY = "cursor_cannot_claim_core_regime_authority"
    LEGACY_FALLBACK_ON_MISSING_CORE_FORBIDDEN = "legacy_fallback_on_missing_core_forbidden"
    SIDESTATE_BACKFLOW_TO_CORE_FORBIDDEN = "sidestate_backflow_to_core_forbidden"
    ACTIVE_FROM_REGIME_ALONE_FORBIDDEN = "active_from_regime_alone_forbidden"
    TOTAL_REGIME_SIDESTATE_BIJECTION_FORBIDDEN = "total_regime_sidestate_bijection_forbidden"
    PROJECTION_REQUIRED_BUT_NOT_AUTHORIZED = "projection_required_but_not_authorized"
    LEGACY_CANONICAL_DISTANCES_AS_D_T_FORBIDDEN = (
        "legacy_canonical_distances_as_d_t_authority_forbidden"
    )
    MISSING_AUTHORIZED_D_T_FAIL_CLOSED = "missing_authorized_d_t_fail_closed"
    DUAL_LEGACY_SCOPE_CM_WRITER_WITH_LAYERED_SEAL_FORBIDDEN = (
        "dual_legacy_scope_cm_writer_with_layered_seal_forbidden"
    )
    EXPLICIT_DT_PROPOSAL_PROMOTED_TO_NUMERIC_AUTHORITY_FORBIDDEN = (
        "explicit_dt_proposal_promoted_to_numeric_authority_forbidden"
    )


@dataclass(frozen=True)
class OR2AuthorityValidationResultV1:
    ok: bool
    failure_codes: Tuple[str, ...]


@dataclass(frozen=True)
class OR2LayeredAuthorityBindRequestV1:
    """Validate O-R2 rules for a future layered-mode bind/cutover configuration."""

    sidestate_cutover_model: str
    decision_authority_mode: ProductiveDecisionAuthorityModeV1
    competing_sidestate_bull_bear_decision_writer_would_run: bool
    implicit_bull_to_long_active_mapping: bool
    implicit_bear_to_short_active_mapping: bool
    venue_claims_core_regime_authority: bool
    cursor_claims_core_regime_authority: bool
    from_venue_position: bool
    from_cursor_restore: bool
    legacy_fallback_on_missing_core: bool
    sidestate_backflow_to_core: bool
    active_side_state_derived_from_regime_only: bool
    total_regime_sidestate_bijection_claimed: bool
    sidestate_projection_required_for_cycle: bool
    sidestate_projection_authorized_and_implemented: bool
    legacy_canonical_distances_as_d_t_authority: bool
    authorized_proposed_d_t_present: bool
    legacy_scope_or_cm_writer_would_run_with_valid_layered_seal: bool
    explicit_dt_proposal_promoted_to_numeric_authority: bool


def _fail(*codes: OR2AuthorityFailureCodeV1) -> OR2AuthorityValidationResultV1:
    return OR2AuthorityValidationResultV1(
        ok=False,
        failure_codes=tuple(dict.fromkeys(c.value for c in codes)),
    )


def _ok() -> OR2AuthorityValidationResultV1:
    return OR2AuthorityValidationResultV1(ok=True, failure_codes=())


def validate_host_seed_boundary_v1(
    *,
    from_venue_position: bool,
    from_cursor_restore: bool,
    claims_core_regime_authority: bool,
    legacy_fallback_on_missing_core: bool,
) -> OR2AuthorityValidationResultV1:
    """Venue/cursor are observation/recovery; never core regime writers; no legacy fallback."""
    failures: list[OR2AuthorityFailureCodeV1] = []
    if legacy_fallback_on_missing_core:
        failures.append(OR2AuthorityFailureCodeV1.LEGACY_FALLBACK_ON_MISSING_CORE_FORBIDDEN)
    seed = classify_side_state_seed_v1(
        from_venue_position=from_venue_position,
        from_cursor_restore=from_cursor_restore,
        claims_core_regime_authority=claims_core_regime_authority,
    )
    if seed is SideStateSeedClassV1.CORE_REGIME_AUTHORITY_CLAIM:
        if from_venue_position:
            failures.append(OR2AuthorityFailureCodeV1.VENUE_CANNOT_CLAIM_CORE_REGIME_AUTHORITY)
        if from_cursor_restore:
            failures.append(OR2AuthorityFailureCodeV1.CURSOR_CANNOT_CLAIM_CORE_REGIME_AUTHORITY)
        if not from_venue_position and not from_cursor_restore:
            failures.append(OR2AuthorityFailureCodeV1.VENUE_CANNOT_CLAIM_CORE_REGIME_AUTHORITY)
    if failures:
        return OR2AuthorityValidationResultV1(
            ok=False,
            failure_codes=tuple(dict.fromkeys(c.value for c in failures)),
        )
    return _ok()


def validate_sidestate_projection_boundary_v1(
    *,
    sidestate_backflow_to_core: bool,
    active_from_regime_only: bool,
    total_bijection_claimed: bool,
    projection_required: bool,
    projection_authorized_and_implemented: bool,
) -> OR2AuthorityValidationResultV1:
    """Projection may read core/occupancy; must not write core; unmapped => fail-closed."""
    failures: list[OR2AuthorityFailureCodeV1] = []
    if sidestate_backflow_to_core:
        failures.append(OR2AuthorityFailureCodeV1.SIDESTATE_BACKFLOW_TO_CORE_FORBIDDEN)
    if active_from_regime_only:
        failures.append(OR2AuthorityFailureCodeV1.ACTIVE_FROM_REGIME_ALONE_FORBIDDEN)
    if total_bijection_claimed:
        failures.append(OR2AuthorityFailureCodeV1.TOTAL_REGIME_SIDESTATE_BIJECTION_FORBIDDEN)
    if projection_required and not projection_authorized_and_implemented:
        failures.append(OR2AuthorityFailureCodeV1.PROJECTION_REQUIRED_BUT_NOT_AUTHORIZED)
    if failures:
        return OR2AuthorityValidationResultV1(
            ok=False,
            failure_codes=tuple(dict.fromkeys(c.value for c in failures)),
        )
    return _ok()


def validate_d_t_authority_gate_v1(
    *,
    legacy_canonical_distances_as_d_t_authority: bool,
    authorized_proposed_d_t_present: bool,
    explicit_dt_proposal_promoted_to_numeric_authority: bool,
    layered_mode_active: bool,
) -> OR2AuthorityValidationResultV1:
    """Layered D_t from authorized proposal/transport only; legacy distances forbidden."""
    failures: list[OR2AuthorityFailureCodeV1] = []
    if explicit_dt_proposal_promoted_to_numeric_authority:
        failures.append(
            OR2AuthorityFailureCodeV1.EXPLICIT_DT_PROPOSAL_PROMOTED_TO_NUMERIC_AUTHORITY_FORBIDDEN
        )
    if layered_mode_active and legacy_canonical_distances_as_d_t_authority:
        failures.append(OR2AuthorityFailureCodeV1.LEGACY_CANONICAL_DISTANCES_AS_D_T_FORBIDDEN)
    if layered_mode_active and not authorized_proposed_d_t_present:
        failures.append(OR2AuthorityFailureCodeV1.MISSING_AUTHORIZED_D_T_FAIL_CLOSED)
    if failures:
        return OR2AuthorityValidationResultV1(
            ok=False,
            failure_codes=tuple(dict.fromkeys(c.value for c in failures)),
        )
    return _ok()


def validate_o_r2_layered_authority_bind_v1(
    request: OR2LayeredAuthorityBindRequestV1,
) -> OR2AuthorityValidationResultV1:
    """O-R2: L1-L10 sole Bull/Bear authority in layered mode; SideState subordinated only."""
    if request.sidestate_cutover_model != SIDESTATE_CUTOVER_MODEL:
        return _fail(OR2AuthorityFailureCodeV1.SIDESTATE_CUTOVER_MODEL_MISMATCH)

    failures: list[OR2AuthorityFailureCodeV1] = []

    if request.implicit_bull_to_long_active_mapping:
        failures.append(OR2AuthorityFailureCodeV1.IMPLICIT_BULL_TO_LONG_ACTIVE_FORBIDDEN)
    if request.implicit_bear_to_short_active_mapping:
        failures.append(OR2AuthorityFailureCodeV1.IMPLICIT_BEAR_TO_SHORT_ACTIVE_FORBIDDEN)

    layered = (
        request.decision_authority_mode
        is ProductiveDecisionAuthorityModeV1.LAYERED_CORE_SEAL_DELEGATED
    )

    if layered and request.competing_sidestate_bull_bear_decision_writer_would_run:
        failures.append(
            OR2AuthorityFailureCodeV1.LAYERED_COMPETING_SIDESTATE_BULL_BEAR_WRITER_FORBIDDEN
        )

    if layered and request.legacy_scope_or_cm_writer_would_run_with_valid_layered_seal:
        failures.append(
            OR2AuthorityFailureCodeV1.DUAL_LEGACY_SCOPE_CM_WRITER_WITH_LAYERED_SEAL_FORBIDDEN
        )

    host = validate_host_seed_boundary_v1(
        from_venue_position=request.from_venue_position,
        from_cursor_restore=request.from_cursor_restore,
        claims_core_regime_authority=(
            request.venue_claims_core_regime_authority
            or request.cursor_claims_core_regime_authority
        ),
        legacy_fallback_on_missing_core=request.legacy_fallback_on_missing_core,
    )
    failures.extend(OR2AuthorityFailureCodeV1(c) for c in host.failure_codes)

    if request.venue_claims_core_regime_authority:
        failures.append(OR2AuthorityFailureCodeV1.VENUE_CANNOT_CLAIM_CORE_REGIME_AUTHORITY)
    if request.cursor_claims_core_regime_authority:
        failures.append(OR2AuthorityFailureCodeV1.CURSOR_CANNOT_CLAIM_CORE_REGIME_AUTHORITY)

    proj = validate_sidestate_projection_boundary_v1(
        sidestate_backflow_to_core=request.sidestate_backflow_to_core,
        active_from_regime_only=request.active_side_state_derived_from_regime_only,
        total_bijection_claimed=request.total_regime_sidestate_bijection_claimed,
        projection_required=(layered and request.sidestate_projection_required_for_cycle),
        projection_authorized_and_implemented=(
            request.sidestate_projection_authorized_and_implemented
        ),
    )
    failures.extend(OR2AuthorityFailureCodeV1(c) for c in proj.failure_codes)

    dt = validate_d_t_authority_gate_v1(
        legacy_canonical_distances_as_d_t_authority=(
            request.legacy_canonical_distances_as_d_t_authority
        ),
        authorized_proposed_d_t_present=request.authorized_proposed_d_t_present,
        explicit_dt_proposal_promoted_to_numeric_authority=(
            request.explicit_dt_proposal_promoted_to_numeric_authority
        ),
        layered_mode_active=layered,
    )
    failures.extend(OR2AuthorityFailureCodeV1(c) for c in dt.failure_codes)

    if failures:
        return OR2AuthorityValidationResultV1(
            ok=False,
            failure_codes=tuple(dict.fromkeys(c.value for c in failures)),
        )
    return _ok()


def validate_legacy_mode_preserves_transition_state_authority_v1(
    *,
    decision_authority_mode: ProductiveDecisionAuthorityModeV1,
    legacy_transition_state_is_canonical_sm_writer: bool,
) -> OR2AuthorityValidationResultV1:
    """Legacy mode: transition_state remains canonical SideState/Switch writer (unchanged)."""
    if (
        decision_authority_mode
        is ProductiveDecisionAuthorityModeV1.LEGACY_DOUBLE_PLAY_INTEGRATED_REPLAY
        and not legacy_transition_state_is_canonical_sm_writer
    ):
        return _fail(
            OR2AuthorityFailureCodeV1.LAYERED_COMPETING_SIDESTATE_BULL_BEAR_WRITER_FORBIDDEN
        )
    return _ok()


__all__ = [
    "OR2AuthorityFailureCodeV1",
    "OR2AuthorityValidationResultV1",
    "OR2LayeredAuthorityBindRequestV1",
    "validate_d_t_authority_gate_v1",
    "validate_host_seed_boundary_v1",
    "validate_legacy_mode_preserves_transition_state_authority_v1",
    "validate_o_r2_layered_authority_bind_v1",
    "validate_sidestate_projection_boundary_v1",
]
