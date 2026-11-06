"""Layered post-projection mechanical SideState FSM contract (validator only; no wiring).

Rows are derived from ``trading.master_v2.double_play_state.transition_state`` behavior
as adjudicated in P5.9C. UNKNOWN rows (e.g. CHOP_GUARD_BLOCK clear) are not allowlisted.
Does not invoke ``transition_state`` or modify productive replay.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

from trading.master_v2.double_play_state import (
    LONG_ARMED_POLICY_STATES,
    SHORT_ARMED_POLICY_STATES,
    ScopeEvent,
    SideState,
)
from trading.master_v2.naked_mv2_dp_regime_v1 import NakedRegimeV1

CONTRACT_OWNER = "ops.p5_9d_layered_mechanical_sidestate_fsm_contract_v1.contract_v1"

# CZ-4 delegated replay synthetic NOOP marker (integrated_offline_replay_p5_cz4_delegation_v1).
CZ4_SYNTHETIC_NOOP_MATCHED_CONDITION = "p5_cz4_delegated_noop"


class MechanicalScopeEventProvenanceV1(str, Enum):
    """Scope-event source for mechanical SideState completion (bind prep)."""

    LEGACY_DETERMINISTIC_SCOPE_EVENT_GENERATOR = "legacy_deterministic_scope_event_generator"
    CZ4_SYNTHETIC_NOOP = "cz4_synthetic_noop"
    UNSPECIFIED = "unspecified"


class SideStateAuthorityDomainV1(str, Enum):
    REGIME_BOUND = "regime_bound"
    MECHANICAL = "mechanical"


class MechanicalFsmFailureCodeV1(str, Enum):
    FORBIDDEN_REGIME_BOUND_LEGACY_ROW = "forbidden_regime_bound_legacy_row"
    MECHANICAL_ROW_NOT_AUTHORIZED = "mechanical_row_not_authorized"
    MECHANICAL_ROW_UNKNOWN = "mechanical_row_unknown"
    MECHANICAL_COMPLETION_SCOPE_PROVENANCE_REQUIRED = (
        "mechanical_completion_scope_provenance_required"
    )
    MECHANICAL_COMPLETION_CZ4_NOOP_FORBIDDEN = "mechanical_completion_cz4_noop_forbidden"
    COMPETING_REGIME_AND_MECHANICAL_WRITER = "competing_regime_and_mechanical_writer"
    P5_7_HANDOFF_PRIOR_MISMATCH = "p5_7_handoff_prior_mismatch"
    REGIME_BOUND_ACTIVE_FROM_REGIME_FORBIDDEN = "regime_bound_active_from_regime_forbidden"
    MECHANICAL_REGIME_INFERENCE_FORBIDDEN = "mechanical_regime_inference_forbidden"
    SIDESTATE_TO_REGIME_BACKFLOW_FORBIDDEN = "sidestate_to_regime_backflow_forbidden"


class ForbiddenRegimeBoundLegacyRowV1(str, Enum):
    """Legacy ``transition_state`` rows that must not run in layered mode (P5.9C)."""

    T15_NEUTRAL_UPSCOPE_TO_LONG_ARMED_NEUTRAL_START = (
        "t15_neutral_observe_upscope_to_long_armed_neutral_start"
    )
    T16_NEUTRAL_DOWNSCOPE_TO_SHORT_ARMED_NEUTRAL_START = (
        "t16_neutral_observe_downscope_to_short_armed_neutral_start"
    )
    T7_LONG_ACTIVE_DOWNSCOPE_TO_SWITCH_LONG_TO_SHORT_PENDING = (
        "t7_long_active_downscope_to_switch_long_to_short_pending"
    )
    T11_SHORT_ACTIVE_DOWNSCOPE_TO_SWITCH_SHORT_TO_LONG_PENDING = (
        "t11_short_active_downscope_to_switch_short_to_long_pending"
    )


class AuthorizedMechanicalRowV1(str, Enum):
    """Repo-belegbare mechanical rows (side-changing or explicit hold)."""

    MECH_T1_KILL_ALL = "mech_t1_kill_all"
    MECH_T3_SCOPE_UNKNOWN_HOLD = "mech_t3_scope_unknown_hold"
    MECH_T4_CHOP_DETECTED_HOLD = "mech_t4_chop_detected_hold"
    MECH_T6_CHOP_POLICY_BLOCK_HOLD = "mech_t6_chop_policy_block_hold"
    MECH_T8_SWITCH_LONG_PENDING_TO_LONG_BLOCKED = "mech_t8_switch_long_pending_to_long_blocked"
    MECH_T9_LONG_BLOCKED_TO_SHORT_ARMED_SWITCH_TERMINAL = (
        "mech_t9_long_blocked_to_short_armed_switch_terminal"
    )
    MECH_T10_SHORT_ARMED_TO_SHORT_ACTIVE = "mech_t10_short_armed_to_short_active"
    MECH_T12_SWITCH_SHORT_PENDING_TO_SHORT_BLOCKED = (
        "mech_t12_switch_short_pending_to_short_blocked"
    )
    MECH_T13_SHORT_BLOCKED_TO_LONG_ARMED_SWITCH_TERMINAL = (
        "mech_t13_short_blocked_to_long_armed_switch_terminal"
    )
    MECH_T14_LONG_ARMED_TO_LONG_ACTIVE = "mech_t14_long_armed_to_long_active"
    MECH_T17_CANDIDATE_ACK = "mech_t17_candidate_ack"
    MECH_T18_NOOP_HOLD = "mech_t18_noop_hold"


MECHANICAL_COMPLETION_ROW_IDS: frozenset[AuthorizedMechanicalRowV1] = frozenset(
    {
        AuthorizedMechanicalRowV1.MECH_T8_SWITCH_LONG_PENDING_TO_LONG_BLOCKED,
        AuthorizedMechanicalRowV1.MECH_T9_LONG_BLOCKED_TO_SHORT_ARMED_SWITCH_TERMINAL,
        AuthorizedMechanicalRowV1.MECH_T10_SHORT_ARMED_TO_SHORT_ACTIVE,
        AuthorizedMechanicalRowV1.MECH_T12_SWITCH_SHORT_PENDING_TO_SHORT_BLOCKED,
        AuthorizedMechanicalRowV1.MECH_T13_SHORT_BLOCKED_TO_LONG_ARMED_SWITCH_TERMINAL,
        AuthorizedMechanicalRowV1.MECH_T14_LONG_ARMED_TO_LONG_ACTIVE,
    }
)


@dataclass(frozen=True)
class LayeredSideStateTransitionProvenanceSurfaceV1:
    """Reason/provenance surface for future ``StateSwitchEvidence`` bind."""

    contract_owner: str
    authority_domain: SideStateAuthorityDomainV1
    mechanical_row_id: Optional[str]
    reason_code: str
    scope_event_provenance: Optional[str]


@dataclass(frozen=True)
class MechanicalTransitionValidationResultV1:
    ok: bool
    mechanical_row_id: Optional[AuthorizedMechanicalRowV1]
    forbidden_legacy_row_id: Optional[ForbiddenRegimeBoundLegacyRowV1]
    failure_codes: Tuple[str, ...]
    provenance_surface: Optional[LayeredSideStateTransitionProvenanceSurfaceV1]


@dataclass(frozen=True)
class LayeredSidestateEpochWriteRequestV1:
    trading_epoch: int
    regime_bound_write_asserted: bool
    mechanical_write_asserted: bool


@dataclass(frozen=True)
class P57MechanicalFsmHandoffRequestV1:
    p5_7_projected_side_state: SideState
    mechanical_fsm_input_prior_side_state: SideState


def _fail_mechanical(
    *codes: MechanicalFsmFailureCodeV1,
    forbidden: ForbiddenRegimeBoundLegacyRowV1 | None = None,
) -> MechanicalTransitionValidationResultV1:
    return MechanicalTransitionValidationResultV1(
        ok=False,
        mechanical_row_id=None,
        forbidden_legacy_row_id=forbidden,
        failure_codes=tuple(dict.fromkeys(c.value for c in codes)),
        provenance_surface=None,
    )


def _ok_mechanical(
    row: AuthorizedMechanicalRowV1,
    *,
    reason_code: str,
    scope_provenance: MechanicalScopeEventProvenanceV1 | None,
) -> MechanicalTransitionValidationResultV1:
    return MechanicalTransitionValidationResultV1(
        ok=True,
        mechanical_row_id=row,
        forbidden_legacy_row_id=None,
        failure_codes=(),
        provenance_surface=LayeredSideStateTransitionProvenanceSurfaceV1(
            contract_owner=CONTRACT_OWNER,
            authority_domain=SideStateAuthorityDomainV1.MECHANICAL,
            mechanical_row_id=row.value,
            reason_code=reason_code,
            scope_event_provenance=(None if scope_provenance is None else scope_provenance.value),
        ),
    )


def classify_forbidden_regime_bound_legacy_row_v1(
    *,
    prior_side_state: SideState,
    scope_event: ScopeEvent,
    next_side_state: SideState,
) -> Optional[ForbiddenRegimeBoundLegacyRowV1]:
    if (
        prior_side_state is SideState.NEUTRAL_OBSERVE
        and scope_event is ScopeEvent.UPSCOPE_CONFIRMED
        and next_side_state is SideState.LONG_ARMED_NEUTRAL_START
    ):
        return ForbiddenRegimeBoundLegacyRowV1.T15_NEUTRAL_UPSCOPE_TO_LONG_ARMED_NEUTRAL_START
    if (
        prior_side_state is SideState.NEUTRAL_OBSERVE
        and scope_event is ScopeEvent.DOWNSCOPE_CONFIRMED
        and next_side_state is SideState.SHORT_ARMED_NEUTRAL_START
    ):
        return ForbiddenRegimeBoundLegacyRowV1.T16_NEUTRAL_DOWNSCOPE_TO_SHORT_ARMED_NEUTRAL_START
    if (
        prior_side_state is SideState.LONG_ACTIVE
        and scope_event is ScopeEvent.DOWNSCOPE_CONFIRMED
        and next_side_state is SideState.SWITCH_LONG_TO_SHORT_PENDING
    ):
        return (
            ForbiddenRegimeBoundLegacyRowV1.T7_LONG_ACTIVE_DOWNSCOPE_TO_SWITCH_LONG_TO_SHORT_PENDING
        )
    if (
        prior_side_state is SideState.SHORT_ACTIVE
        and scope_event is ScopeEvent.DOWNSCOPE_CONFIRMED
        and next_side_state is SideState.SWITCH_SHORT_TO_LONG_PENDING
    ):
        return ForbiddenRegimeBoundLegacyRowV1.T11_SHORT_ACTIVE_DOWNSCOPE_TO_SWITCH_SHORT_TO_LONG_PENDING
    return None


def validate_forbidden_regime_bound_legacy_row_v1(
    *,
    prior_side_state: SideState,
    scope_event: ScopeEvent,
    next_side_state: SideState,
) -> MechanicalTransitionValidationResultV1:
    forbidden = classify_forbidden_regime_bound_legacy_row_v1(
        prior_side_state=prior_side_state,
        scope_event=scope_event,
        next_side_state=next_side_state,
    )
    if forbidden is not None:
        return _fail_mechanical(
            MechanicalFsmFailureCodeV1.FORBIDDEN_REGIME_BOUND_LEGACY_ROW,
            forbidden=forbidden,
        )
    return MechanicalTransitionValidationResultV1(
        ok=True,
        mechanical_row_id=None,
        forbidden_legacy_row_id=None,
        failure_codes=(),
        provenance_surface=None,
    )


def classify_authorized_mechanical_row_v1(
    *,
    prior_side_state: SideState,
    scope_event: ScopeEvent,
    next_side_state: SideState,
    chop_scope_policy_blocked_transition: bool = False,
) -> Optional[AuthorizedMechanicalRowV1]:
    if (
        scope_event is ScopeEvent.KILL_ALL_REQUIRED
        and next_side_state is SideState.KILL_ALL
        and prior_side_state is not SideState.KILL_ALL
    ):
        return AuthorizedMechanicalRowV1.MECH_T1_KILL_ALL
    if scope_event is ScopeEvent.SCOPE_UNKNOWN and next_side_state is prior_side_state:
        return AuthorizedMechanicalRowV1.MECH_T3_SCOPE_UNKNOWN_HOLD
    if scope_event is ScopeEvent.CHOP_DETECTED and next_side_state is prior_side_state:
        return AuthorizedMechanicalRowV1.MECH_T4_CHOP_DETECTED_HOLD
    if (
        chop_scope_policy_blocked_transition
        and scope_event in (ScopeEvent.DOWNSCOPE_CONFIRMED, ScopeEvent.UPSCOPE_CONFIRMED)
        and next_side_state is prior_side_state
    ):
        return AuthorizedMechanicalRowV1.MECH_T6_CHOP_POLICY_BLOCK_HOLD
    if (
        prior_side_state is SideState.SWITCH_LONG_TO_SHORT_PENDING
        and scope_event is ScopeEvent.DOWNSCOPE_CONFIRMED
        and next_side_state is SideState.LONG_BLOCKED
    ):
        return AuthorizedMechanicalRowV1.MECH_T8_SWITCH_LONG_PENDING_TO_LONG_BLOCKED
    if (
        prior_side_state is SideState.LONG_BLOCKED
        and scope_event is ScopeEvent.DOWNSCOPE_CONFIRMED
        and next_side_state is SideState.SHORT_ARMED_SWITCH_TERMINAL
    ):
        return AuthorizedMechanicalRowV1.MECH_T9_LONG_BLOCKED_TO_SHORT_ARMED_SWITCH_TERMINAL
    if (
        prior_side_state in SHORT_ARMED_POLICY_STATES
        and scope_event is ScopeEvent.DOWNSCOPE_CONFIRMED
        and next_side_state is SideState.SHORT_ACTIVE
    ):
        return AuthorizedMechanicalRowV1.MECH_T10_SHORT_ARMED_TO_SHORT_ACTIVE
    if (
        prior_side_state is SideState.SWITCH_SHORT_TO_LONG_PENDING
        and scope_event is ScopeEvent.DOWNSCOPE_CONFIRMED
        and next_side_state is SideState.SHORT_BLOCKED
    ):
        return AuthorizedMechanicalRowV1.MECH_T12_SWITCH_SHORT_PENDING_TO_SHORT_BLOCKED
    if (
        prior_side_state is SideState.SHORT_BLOCKED
        and scope_event is ScopeEvent.DOWNSCOPE_CONFIRMED
        and next_side_state is SideState.LONG_ARMED_SWITCH_TERMINAL
    ):
        return AuthorizedMechanicalRowV1.MECH_T13_SHORT_BLOCKED_TO_LONG_ARMED_SWITCH_TERMINAL
    if (
        prior_side_state in LONG_ARMED_POLICY_STATES
        and scope_event is ScopeEvent.UPSCOPE_CONFIRMED
        and next_side_state is SideState.LONG_ACTIVE
    ):
        return AuthorizedMechanicalRowV1.MECH_T14_LONG_ARMED_TO_LONG_ACTIVE
    if (
        scope_event
        in (
            ScopeEvent.DOWNSCOPE_CANDIDATE,
            ScopeEvent.UPSCOPE_CANDIDATE,
        )
        and next_side_state is prior_side_state
    ):
        return AuthorizedMechanicalRowV1.MECH_T17_CANDIDATE_ACK
    if scope_event is ScopeEvent.NOOP and next_side_state is prior_side_state:
        return AuthorizedMechanicalRowV1.MECH_T18_NOOP_HOLD
    return None


def resolve_mechanical_scope_event_provenance_v1(
    *,
    legacy_deterministic_generator_evidence: bool,
    cz4_delegated_noop_matched: bool,
) -> MechanicalScopeEventProvenanceV1:
    if cz4_delegated_noop_matched:
        return MechanicalScopeEventProvenanceV1.CZ4_SYNTHETIC_NOOP
    if legacy_deterministic_generator_evidence:
        return MechanicalScopeEventProvenanceV1.LEGACY_DETERMINISTIC_SCOPE_EVENT_GENERATOR
    return MechanicalScopeEventProvenanceV1.UNSPECIFIED


def validate_mechanical_scope_provenance_for_side_change_v1(
    *,
    provenance: MechanicalScopeEventProvenanceV1,
    mechanical_row_id: AuthorizedMechanicalRowV1,
) -> MechanicalTransitionValidationResultV1:
    if mechanical_row_id in MECHANICAL_COMPLETION_ROW_IDS:
        if (
            provenance
            is not MechanicalScopeEventProvenanceV1.LEGACY_DETERMINISTIC_SCOPE_EVENT_GENERATOR
        ):
            codes: list[MechanicalFsmFailureCodeV1] = [
                MechanicalFsmFailureCodeV1.MECHANICAL_COMPLETION_SCOPE_PROVENANCE_REQUIRED,
            ]
            if provenance is MechanicalScopeEventProvenanceV1.CZ4_SYNTHETIC_NOOP:
                codes.append(MechanicalFsmFailureCodeV1.MECHANICAL_COMPLETION_CZ4_NOOP_FORBIDDEN)
            return _fail_mechanical(*codes)
    elif provenance is MechanicalScopeEventProvenanceV1.UNSPECIFIED:
        return _fail_mechanical(
            MechanicalFsmFailureCodeV1.MECHANICAL_COMPLETION_SCOPE_PROVENANCE_REQUIRED,
        )
    if provenance is MechanicalScopeEventProvenanceV1.CZ4_SYNTHETIC_NOOP:
        return _fail_mechanical(
            MechanicalFsmFailureCodeV1.MECHANICAL_COMPLETION_CZ4_NOOP_FORBIDDEN,
        )
    return MechanicalTransitionValidationResultV1(
        ok=True,
        mechanical_row_id=mechanical_row_id,
        forbidden_legacy_row_id=None,
        failure_codes=(),
        provenance_surface=None,
    )


def validate_layered_mechanical_transition_v1(
    *,
    prior_side_state: SideState,
    scope_event: ScopeEvent,
    next_side_state: SideState,
    scope_event_provenance: MechanicalScopeEventProvenanceV1,
    chop_scope_policy_blocked_transition: bool = False,
) -> MechanicalTransitionValidationResultV1:
    """Fail-closed validator for a single mechanical transition attempt (bind prep)."""
    forbidden_check = validate_forbidden_regime_bound_legacy_row_v1(
        prior_side_state=prior_side_state,
        scope_event=scope_event,
        next_side_state=next_side_state,
    )
    if not forbidden_check.ok:
        return forbidden_check

    row = classify_authorized_mechanical_row_v1(
        prior_side_state=prior_side_state,
        scope_event=scope_event,
        next_side_state=next_side_state,
        chop_scope_policy_blocked_transition=chop_scope_policy_blocked_transition,
    )
    if row is None:
        if prior_side_state is SideState.CHOP_GUARD_BLOCK:
            return _fail_mechanical(MechanicalFsmFailureCodeV1.MECHANICAL_ROW_UNKNOWN)
        return _fail_mechanical(
            MechanicalFsmFailureCodeV1.MECHANICAL_ROW_NOT_AUTHORIZED,
            MechanicalFsmFailureCodeV1.MECHANICAL_ROW_UNKNOWN,
        )

    side_changed = next_side_state is not prior_side_state
    if side_changed:
        prov_check = validate_mechanical_scope_provenance_for_side_change_v1(
            provenance=scope_event_provenance,
            mechanical_row_id=row,
        )
        if not prov_check.ok:
            return prov_check

    reason = f"layered_mechanical_{row.value}"
    return _ok_mechanical(
        row,
        reason_code=reason,
        scope_provenance=scope_event_provenance,
    )


def validate_single_writer_per_trading_epoch_v1(
    request: LayeredSidestateEpochWriteRequestV1,
) -> MechanicalTransitionValidationResultV1:
    if request.regime_bound_write_asserted and request.mechanical_write_asserted:
        return _fail_mechanical(
            MechanicalFsmFailureCodeV1.COMPETING_REGIME_AND_MECHANICAL_WRITER,
        )
    return MechanicalTransitionValidationResultV1(
        ok=True,
        mechanical_row_id=None,
        forbidden_legacy_row_id=None,
        failure_codes=(),
        provenance_surface=None,
    )


def validate_p5_7_to_mechanical_fsm_handoff_v1(
    request: P57MechanicalFsmHandoffRequestV1,
) -> MechanicalTransitionValidationResultV1:
    if request.mechanical_fsm_input_prior_side_state is not request.p5_7_projected_side_state:
        return _fail_mechanical(MechanicalFsmFailureCodeV1.P5_7_HANDOFF_PRIOR_MISMATCH)
    return MechanicalTransitionValidationResultV1(
        ok=True,
        mechanical_row_id=None,
        forbidden_legacy_row_id=None,
        failure_codes=(),
        provenance_surface=LayeredSideStateTransitionProvenanceSurfaceV1(
            contract_owner=CONTRACT_OWNER,
            authority_domain=SideStateAuthorityDomainV1.REGIME_BOUND,
            mechanical_row_id=None,
            reason_code="p5_7_regime_bound_projection_handoff",
            scope_event_provenance=None,
        ),
    )


def validate_regime_bound_projection_no_active_v1(
    projected_side_state: SideState,
) -> MechanicalTransitionValidationResultV1:
    if projected_side_state in (SideState.LONG_ACTIVE, SideState.SHORT_ACTIVE):
        return _fail_mechanical(
            MechanicalFsmFailureCodeV1.REGIME_BOUND_ACTIVE_FROM_REGIME_FORBIDDEN,
        )
    return MechanicalTransitionValidationResultV1(
        ok=True,
        mechanical_row_id=None,
        forbidden_legacy_row_id=None,
        failure_codes=(),
        provenance_surface=None,
    )


def validate_mechanical_does_not_infer_regime_v1(
    *,
    inferred_regime: NakedRegimeV1 | None,
) -> MechanicalTransitionValidationResultV1:
    if inferred_regime is not None:
        return _fail_mechanical(
            MechanicalFsmFailureCodeV1.MECHANICAL_REGIME_INFERENCE_FORBIDDEN,
            MechanicalFsmFailureCodeV1.SIDESTATE_TO_REGIME_BACKFLOW_FORBIDDEN,
        )
    return MechanicalTransitionValidationResultV1(
        ok=True,
        mechanical_row_id=None,
        forbidden_legacy_row_id=None,
        failure_codes=(),
        provenance_surface=None,
    )


def all_forbidden_regime_bound_legacy_rows_v1() -> Tuple[ForbiddenRegimeBoundLegacyRowV1, ...]:
    return tuple(ForbiddenRegimeBoundLegacyRowV1)


def all_authorized_mechanical_rows_v1() -> Tuple[AuthorizedMechanicalRowV1, ...]:
    return tuple(AuthorizedMechanicalRowV1)


__all__ = [
    "CONTRACT_OWNER",
    "CZ4_SYNTHETIC_NOOP_MATCHED_CONDITION",
    "AuthorizedMechanicalRowV1",
    "ForbiddenRegimeBoundLegacyRowV1",
    "LayeredSideStateTransitionProvenanceSurfaceV1",
    "LayeredSidestateEpochWriteRequestV1",
    "MechanicalFsmFailureCodeV1",
    "MechanicalScopeEventProvenanceV1",
    "MechanicalTransitionValidationResultV1",
    "MECHANICAL_COMPLETION_ROW_IDS",
    "P57MechanicalFsmHandoffRequestV1",
    "SideStateAuthorityDomainV1",
    "all_authorized_mechanical_rows_v1",
    "all_forbidden_regime_bound_legacy_rows_v1",
    "classify_authorized_mechanical_row_v1",
    "classify_forbidden_regime_bound_legacy_row_v1",
    "resolve_mechanical_scope_event_provenance_v1",
    "validate_forbidden_regime_bound_legacy_row_v1",
    "validate_layered_mechanical_transition_v1",
    "validate_mechanical_does_not_infer_regime_v1",
    "validate_mechanical_scope_provenance_for_side_change_v1",
    "validate_p5_7_to_mechanical_fsm_handoff_v1",
    "validate_regime_bound_projection_no_active_v1",
    "validate_single_writer_per_trading_epoch_v1",
]
