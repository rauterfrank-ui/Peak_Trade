"""Fail-closed authority-bind contracts for future productive L1–L10 seam invoke."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

from trading.master_v2.double_play_state import SideState
from trading.master_v2.layered_core_authority_seal_v1 import LayeredCoreAuthoritySealV1

from src.ops.p5_2_productive_cycle_seam_invoke_and_authority_bind_v1.constants_v1 import (
    PRODUCTIVE_CYCLE_LAYERED_CORE_BIND_ENABLED,
    REGIME_SIDESTATE_MAPPING_CONTRACT_AUTHORIZED,
)


class ProductiveDecisionAuthorityModeV1(str, Enum):
    LEGACY_DOUBLE_PLAY_INTEGRATED_REPLAY = "legacy_double_play_integrated_replay"
    LAYERED_CORE_SEAL_DELEGATED = "layered_core_seal_delegated"


class SideStateSeedClassV1(str, Enum):
    """I-06: how pre-replay SideState was sourced."""

    NONE = "none"
    OBSERVATION_OCCUPANCY_INPUT = "observation_occupancy_input"
    CORE_REGIME_AUTHORITY_CLAIM = "core_regime_authority_claim"


class AuthorityBindFailureCodeV1(str, Enum):
    PRODUCTIVE_LAYERED_CORE_BIND_DISABLED = "productive_layered_core_bind_disabled"
    DUAL_DECISION_AUTHORITY_WRITERS_FORBIDDEN = "dual_decision_authority_writers_forbidden"
    LAYERED_CORE_REQUIRES_VALID_SEAL = "layered_core_requires_valid_seal"
    LEGACY_PATH_FORBIDS_SEAL_DELEGATION = "legacy_path_forbids_seal_delegation"
    REGIME_SIDESTATE_MAPPING_NOT_AUTHORIZED = "regime_sidestate_mapping_not_authorized"
    VENUE_CURSOR_CANNOT_CLAIM_CORE_REGIME_AUTHORITY = (
        "venue_cursor_cannot_claim_core_regime_authority"
    )
    LEGACY_SCOPE_WRITER_FORBIDDEN_IN_LAYERED_MODE = "legacy_scope_writer_forbidden_in_layered_mode"
    LEGACY_ANCHOR_WRITER_FORBIDDEN_IN_LAYERED_MODE = (
        "legacy_anchor_writer_forbidden_in_layered_mode"
    )
    LEGACY_SWITCH_WRITER_FORBIDDEN_IN_LAYERED_MODE = (
        "legacy_switch_writer_forbidden_in_layered_mode"
    )
    LEGACY_DISTANCES_D_T_AUTHORITY_FORBIDDEN_IN_LAYERED_MODE = (
        "legacy_distances_d_t_authority_forbidden_in_layered_mode"
    )
    MISSING_CORE_STATE_LEGACY_FALLBACK_FORBIDDEN = "missing_core_state_legacy_fallback_forbidden"
    CZ4_REQUIRES_VALID_SEAL = "cz4_requires_valid_seal"


@dataclass(frozen=True)
class ProductiveCycleAuthorityBindRequestV1:
    """Request to validate a productive-cycle authority configuration (bind prep)."""

    productive_layered_core_bind_requested: bool
    decision_authority_mode: ProductiveDecisionAuthorityModeV1
    seal_present: bool
    seal_validation_ok: bool
    cz4_delegation_intended: bool
    legacy_scope_writer_would_run: bool
    legacy_transition_writer_would_run: bool
    legacy_dynamic_boundary_writer_would_run: bool
    legacy_canonical_distances_as_d_t_authority: bool
    side_state_seed_class: SideStateSeedClassV1
    fallback_to_legacy_on_missing_core: bool


@dataclass(frozen=True)
class AuthorityBindValidationResultV1:
    ok: bool
    failure_codes: Tuple[str, ...]


def classify_side_state_seed_v1(
    *,
    from_venue_position: bool,
    from_cursor_restore: bool,
    claims_core_regime_authority: bool,
) -> SideStateSeedClassV1:
    if claims_core_regime_authority:
        return SideStateSeedClassV1.CORE_REGIME_AUTHORITY_CLAIM
    if from_venue_position or from_cursor_restore:
        return SideStateSeedClassV1.OBSERVATION_OCCUPANCY_INPUT
    return SideStateSeedClassV1.NONE


def _fail(*codes: AuthorityBindFailureCodeV1) -> AuthorityBindValidationResultV1:
    return AuthorityBindValidationResultV1(ok=False, failure_codes=tuple(c.value for c in codes))


def _ok() -> AuthorityBindValidationResultV1:
    return AuthorityBindValidationResultV1(ok=True, failure_codes=())


def validate_productive_cycle_authority_bind_v1(
    request: ProductiveCycleAuthorityBindRequestV1,
) -> AuthorityBindValidationResultV1:
    """Validate productive-cycle bind intent. Default install: bind disabled → legacy only."""
    failures: list[AuthorityBindFailureCodeV1] = []

    if (
        request.productive_layered_core_bind_requested
        and not PRODUCTIVE_CYCLE_LAYERED_CORE_BIND_ENABLED
    ):
        failures.append(AuthorityBindFailureCodeV1.PRODUCTIVE_LAYERED_CORE_BIND_DISABLED)

    if request.fallback_to_legacy_on_missing_core:
        failures.append(AuthorityBindFailureCodeV1.MISSING_CORE_STATE_LEGACY_FALLBACK_FORBIDDEN)

    if request.side_state_seed_class is SideStateSeedClassV1.CORE_REGIME_AUTHORITY_CLAIM:
        failures.append(AuthorityBindFailureCodeV1.VENUE_CURSOR_CANNOT_CLAIM_CORE_REGIME_AUTHORITY)

    layered = (
        request.decision_authority_mode
        is ProductiveDecisionAuthorityModeV1.LAYERED_CORE_SEAL_DELEGATED
    )
    legacy = (
        request.decision_authority_mode
        is ProductiveDecisionAuthorityModeV1.LEGACY_DOUBLE_PLAY_INTEGRATED_REPLAY
    )

    legacy_writers_active = (
        request.legacy_scope_writer_would_run
        or request.legacy_transition_writer_would_run
        or request.legacy_dynamic_boundary_writer_would_run
    )

    if layered and legacy_writers_active:
        failures.append(AuthorityBindFailureCodeV1.DUAL_DECISION_AUTHORITY_WRITERS_FORBIDDEN)

    if layered:
        if not request.seal_present or not request.seal_validation_ok:
            failures.append(AuthorityBindFailureCodeV1.LAYERED_CORE_REQUIRES_VALID_SEAL)
        if request.legacy_scope_writer_would_run:
            failures.append(
                AuthorityBindFailureCodeV1.LEGACY_SCOPE_WRITER_FORBIDDEN_IN_LAYERED_MODE
            )
        if request.legacy_dynamic_boundary_writer_would_run:
            failures.append(
                AuthorityBindFailureCodeV1.LEGACY_ANCHOR_WRITER_FORBIDDEN_IN_LAYERED_MODE
            )
        if request.legacy_transition_writer_would_run:
            failures.append(
                AuthorityBindFailureCodeV1.LEGACY_SWITCH_WRITER_FORBIDDEN_IN_LAYERED_MODE
            )
        if request.legacy_canonical_distances_as_d_t_authority:
            failures.append(
                AuthorityBindFailureCodeV1.LEGACY_DISTANCES_D_T_AUTHORITY_FORBIDDEN_IN_LAYERED_MODE
            )

    if legacy and request.cz4_delegation_intended:
        failures.append(AuthorityBindFailureCodeV1.LEGACY_PATH_FORBIDS_SEAL_DELEGATION)

    if (
        legacy
        and request.seal_present
        and request.seal_validation_ok
        and request.cz4_delegation_intended
    ):
        failures.append(AuthorityBindFailureCodeV1.DUAL_DECISION_AUTHORITY_WRITERS_FORBIDDEN)

    if failures:
        return AuthorityBindValidationResultV1(
            ok=False,
            failure_codes=tuple(dict.fromkeys(c.value for c in failures)),
        )
    return _ok()


def validate_cz4_delegation_authority_bind_v1(
    *,
    seal: Optional[LayeredCoreAuthoritySealV1],
    side_state: SideState,
) -> AuthorityBindValidationResultV1:
    """I-05: CZ-4 requires seal; regime switch without mapping contract → fail-closed."""
    _ = side_state  # reserved for future mapping contract; no implicit conversion today
    if seal is None:
        return _fail(AuthorityBindFailureCodeV1.CZ4_REQUIRES_VALID_SEAL)

    if not REGIME_SIDESTATE_MAPPING_CONTRACT_AUTHORIZED:
        if seal.switch_condition_met and seal.regime_pre != seal.regime_post:
            return _fail(AuthorityBindFailureCodeV1.REGIME_SIDESTATE_MAPPING_NOT_AUTHORIZED)

    return _ok()


__all__ = [
    "AuthorityBindFailureCodeV1",
    "AuthorityBindValidationResultV1",
    "ProductiveCycleAuthorityBindRequestV1",
    "ProductiveDecisionAuthorityModeV1",
    "SideStateSeedClassV1",
    "classify_side_state_seed_v1",
    "validate_cz4_delegation_authority_bind_v1",
    "validate_productive_cycle_authority_bind_v1",
]
