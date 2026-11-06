"""P5.10B: close B2 mechanical provenance, B3 lifecycle durability, B4 canonical handoff."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

from trading.master_v2.deterministic_scope_event_generator_v1 import (
    SCOPE_EVENT_GENERATOR_POLICY_VERSION,
    ScopeEventEvidenceV1,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import ExistingPositionSide
from trading.master_v2.double_play_state import ScopeEvent, SideState
from trading.master_v2.integrated_offline_replay_p5_cz4_delegation_v1 import (
    P5_CZ4_DELEGATION_OWNER,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    StateSwitchEvidenceV1,
    _canonical_scope_event_to_scope_event,
    _compute_state_switch_digest,
    _derive_state_switch_id,
)
from trading.master_v2.naked_mv2_dp_regime_v1 import NakedRegimeV1

from src.ops.p5_10a_layered_tick_merge_epoch_orchestration_contract_v1.contract_v1 import (
    C4EntryExitSideStateEpochV1,
    LayeredEpochOrchestrationBindPrepRequestV1,
    SideStateEpochWriterV1,
    validate_layered_epoch_orchestration_bind_prep_v1,
)
from src.ops.p5_7_regime_sidestate_projection_mapping_contract_v1.contract_v1 import (
    RegimeSideStateProjectionInputV1,
    RegimeSideStateProjectionPhaseV1,
    project_regime_to_sidestate_v1,
)
from src.ops.p5_8b_regime_sidestate_projection_phase_authority_v1.contract_v1 import (
    RegimeSideStateProjectionLifecycleStateV1,
    mark_initial_regime_orientation_seed_consumed_v1,
    resolve_regime_sidestate_projection_phase_v1,
)
from src.ops.p5_9d_layered_mechanical_sidestate_fsm_contract_v1.contract_v1 import (
    CZ4_SYNTHETIC_NOOP_MATCHED_CONDITION,
    LayeredSideStateTransitionProvenanceSurfaceV1,
    MechanicalScopeEventProvenanceV1,
    MechanicalTransitionValidationResultV1,
    P57MechanicalFsmHandoffRequestV1,
    validate_layered_mechanical_transition_v1,
    validate_p5_7_to_mechanical_fsm_handoff_v1,
)

CONTRACT_OWNER = "ops.p5_10b_layered_epoch_remaining_authority_closure_v1.contract_v1"

AUTHORIZED_SCOPE_EVENT_PRODUCER_OWNER = "trading.master_v2.deterministic_scope_event_generator_v1"


class LayeredEpochHandoffFailureCodeV1(str, Enum):
    PHASE_RESOLUTION_FAILED = "phase_resolution_failed"
    P57_PROJECTION_FAILED = "p57_projection_failed"
    P57_TO_MECHANICAL_HANDOFF_FAILED = "p57_to_mechanical_handoff_failed"
    MECHANICAL_FSM_FAILED = "mechanical_fsm_failed"
    MECHANICAL_PROVENANCE_UNAUTHORIZED = "mechanical_provenance_unauthorized"
    SCOPE_EVENT_EVIDENCE_PRODUCER_UNKNOWN = "scope_event_evidence_producer_unknown"
    CANONICAL_WRITER_UNRESOLVED = "canonical_writer_unresolved"
    CANONICAL_NEXT_SIDESTATE_UNRESOLVED = "canonical_next_sidestate_unresolved"
    LEGACY_TRANSITION_PARALLEL_FORBIDDEN = "legacy_transition_parallel_forbidden"
    P510A_ORCHESTRATION_BIND_PREP_FAILED = "p510a_orchestration_bind_prep_failed"
    STATE_SWITCH_EVIDENCE_MATERIALIZATION_FAILED = "state_switch_evidence_materialization_failed"


@dataclass(frozen=True)
class MechanicalProvenanceClassificationResultV1:
    ok: bool
    provenance: MechanicalScopeEventProvenanceV1
    failure_codes: Tuple[str, ...]
    producer_owner: Optional[str]


@dataclass(frozen=True)
class LayeredEpochCanonicalHandoffRequestV1:
    trading_epoch: int
    instrument_id: str
    host_prior_side_state: SideState
    lifecycle: RegimeSideStateProjectionLifecycleStateV1
    venue_flat: bool
    existing_position_side: ExistingPositionSide
    switch_condition_met: bool
    regime_pre: NakedRegimeV1
    regime_post: NakedRegimeV1
    regime_pre_equals_post: bool
    scope_event_evidence: ScopeEventEvidenceV1
    scope_event: ScopeEvent
    mechanical_next_side_state: Optional[SideState]
    chop_scope_policy_blocked_transition: bool
    layered_bind_mode_active: bool
    legacy_transition_state_writer_would_run: bool
    transition_allowed: bool
    transition_reason_code: str


@dataclass(frozen=True)
class LayeredEpochCanonicalHandoffResultV1:
    ok: bool
    failure_codes: Tuple[str, ...]
    phase: RegimeSideStateProjectionPhaseV1 | None
    lifecycle_after: RegimeSideStateProjectionLifecycleStateV1 | None
    p57_projected_side_state: SideState | None
    canonical_next_side_state: SideState | None
    epoch_writer: SideStateEpochWriterV1 | None
    regime_bound_write_asserted: bool
    mechanical_write_asserted: bool
    mechanical_fsm_result: MechanicalTransitionValidationResultV1 | None
    provenance_surface: LayeredSideStateTransitionProvenanceSurfaceV1 | None
    state_switch_evidence: StateSwitchEvidenceV1 | None


def map_scope_event_evidence_to_scope_event_v1(
    evidence: ScopeEventEvidenceV1,
) -> ScopeEvent:
    """Map deterministic generator evidence to SideState ScopeEvent (CANONICAL_AUTHORITY)."""
    return _canonical_scope_event_to_scope_event(
        evidence.event_type,
        matched_conditions=tuple(evidence.matched_conditions),
    )


def classify_mechanical_scope_event_provenance_from_evidence_v1(
    evidence: ScopeEventEvidenceV1,
) -> MechanicalProvenanceClassificationResultV1:
    """B2: producer → ScopeEvent provenance; CZ-4 synthetic NOOP is never completion authority."""
    if CZ4_SYNTHETIC_NOOP_MATCHED_CONDITION in tuple(evidence.matched_conditions):
        return MechanicalProvenanceClassificationResultV1(
            ok=True,
            provenance=MechanicalScopeEventProvenanceV1.CZ4_SYNTHETIC_NOOP,
            failure_codes=(),
            producer_owner=P5_CZ4_DELEGATION_OWNER,
        )
    binding = evidence.semantic_binding
    if binding is None:
        return MechanicalProvenanceClassificationResultV1(
            ok=False,
            provenance=MechanicalScopeEventProvenanceV1.UNSPECIFIED,
            failure_codes=(
                LayeredEpochHandoffFailureCodeV1.SCOPE_EVENT_EVIDENCE_PRODUCER_UNKNOWN.value,
            ),
            producer_owner=None,
        )
    policy_version = str(getattr(binding, "generator_policy_version", "") or "").strip()
    if not policy_version:
        return MechanicalProvenanceClassificationResultV1(
            ok=False,
            provenance=MechanicalScopeEventProvenanceV1.UNSPECIFIED,
            failure_codes=(
                LayeredEpochHandoffFailureCodeV1.SCOPE_EVENT_EVIDENCE_PRODUCER_UNKNOWN.value,
            ),
            producer_owner=None,
        )
    if policy_version != SCOPE_EVENT_GENERATOR_POLICY_VERSION:
        return MechanicalProvenanceClassificationResultV1(
            ok=False,
            provenance=MechanicalScopeEventProvenanceV1.UNSPECIFIED,
            failure_codes=(
                LayeredEpochHandoffFailureCodeV1.MECHANICAL_PROVENANCE_UNAUTHORIZED.value,
            ),
            producer_owner=None,
        )
    return MechanicalProvenanceClassificationResultV1(
        ok=True,
        provenance=MechanicalScopeEventProvenanceV1.LEGACY_DETERMINISTIC_SCOPE_EVENT_GENERATOR,
        failure_codes=(),
        producer_owner=AUTHORIZED_SCOPE_EVENT_PRODUCER_OWNER,
    )


def validate_layered_mechanical_completion_provenance_chain_v1(
    *,
    evidence: ScopeEventEvidenceV1,
    scope_event: ScopeEvent,
    prior_side_state: SideState,
    next_side_state: SideState,
    chop_scope_policy_blocked_transition: bool = False,
) -> MechanicalTransitionValidationResultV1:
    """B2: prove producer → provenance → P5.9D FSM for mechanical rows (incl. MECH_T8–T14)."""
    classification = classify_mechanical_scope_event_provenance_from_evidence_v1(evidence)
    if not classification.ok:
        return MechanicalTransitionValidationResultV1(
            ok=False,
            mechanical_row_id=None,
            forbidden_legacy_row_id=None,
            failure_codes=classification.failure_codes,
            provenance_surface=None,
        )
    mapped = map_scope_event_evidence_to_scope_event_v1(evidence)
    if mapped is not scope_event:
        return MechanicalTransitionValidationResultV1(
            ok=False,
            mechanical_row_id=None,
            forbidden_legacy_row_id=None,
            failure_codes=("scope_event_evidence_transport_mismatch",),
            provenance_surface=None,
        )
    return validate_layered_mechanical_transition_v1(
        prior_side_state=prior_side_state,
        scope_event=scope_event,
        next_side_state=next_side_state,
        scope_event_provenance=classification.provenance,
        chop_scope_policy_blocked_transition=chop_scope_policy_blocked_transition,
    )


def materialize_state_switch_evidence_v1_from_layered_handoff_v1(
    *,
    instrument_id: str,
    trading_epoch: int,
    previous_side_state: SideState,
    next_side_state: SideState,
    scope_event: ScopeEvent,
    scope_event_id: str,
    transition_allowed: bool,
    transition_reason_code: str,
) -> StateSwitchEvidenceV1:
    """B4: StateSwitchEvidenceV1 from canonical layered handoff (not legacy transition_state)."""
    state_switch_id = _derive_state_switch_id(instrument_id, trading_epoch, scope_event_id)
    switch_digest = _compute_state_switch_digest(
        state_switch_id=state_switch_id,
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        previous_side_state=previous_side_state.value,
        next_side_state=next_side_state.value,
        scope_event_type=scope_event.value,
        transition_allowed=transition_allowed,
        transition_reason_code=transition_reason_code,
    )
    return StateSwitchEvidenceV1(
        state_switch_id=state_switch_id,
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        previous_side_state=previous_side_state.value,
        next_side_state=next_side_state.value,
        scope_event_type=scope_event.value,
        transition_allowed=transition_allowed,
        transition_reason_code=transition_reason_code,
        semantic_digest=switch_digest,
    )


def _fail_handoff(
    *codes: LayeredEpochHandoffFailureCodeV1 | str,
) -> LayeredEpochCanonicalHandoffResultV1:
    normalized = tuple(dict.fromkeys(c.value if hasattr(c, "value") else str(c) for c in codes))
    return LayeredEpochCanonicalHandoffResultV1(
        ok=False,
        failure_codes=normalized,
        phase=None,
        lifecycle_after=None,
        p57_projected_side_state=None,
        canonical_next_side_state=None,
        epoch_writer=None,
        regime_bound_write_asserted=False,
        mechanical_write_asserted=False,
        mechanical_fsm_result=None,
        provenance_surface=None,
        state_switch_evidence=None,
    )


def execute_layered_epoch_canonical_sidestate_handoff_v1(
    request: LayeredEpochCanonicalHandoffRequestV1,
) -> LayeredEpochCanonicalHandoffResultV1:
    """B4 end-to-end: P5.8B → P5.7 → P5.9D → canonical_next_side_state → StateSwitchEvidenceV1."""
    if request.layered_bind_mode_active and request.legacy_transition_state_writer_would_run:
        return _fail_handoff(LayeredEpochHandoffFailureCodeV1.LEGACY_TRANSITION_PARALLEL_FORBIDDEN)

    phase_result = resolve_regime_sidestate_projection_phase_v1(
        lifecycle=request.lifecycle,
        instrument_id=request.instrument_id,
        prior_side_state=request.host_prior_side_state,
        venue_flat=request.venue_flat,
        existing_position_side=request.existing_position_side,
        switch_condition_met=request.switch_condition_met,
        regime_pre_equals_post=request.regime_pre_equals_post,
    )
    if not phase_result.ok or phase_result.phase is None:
        return _fail_handoff(LayeredEpochHandoffFailureCodeV1.PHASE_RESOLUTION_FAILED)

    p57 = project_regime_to_sidestate_v1(
        RegimeSideStateProjectionInputV1(
            regime_pre=request.regime_pre,
            regime_post=request.regime_post,
            switch_condition_met=request.switch_condition_met,
            prior_side_state=request.host_prior_side_state,
            phase=phase_result.phase,
            venue_flat=request.venue_flat,
            existing_position_side=request.existing_position_side,
        )
    )
    if not p57.ok or p57.projected_side_state is None:
        return _fail_handoff(LayeredEpochHandoffFailureCodeV1.P57_PROJECTION_FAILED)

    handoff = validate_p5_7_to_mechanical_fsm_handoff_v1(
        P57MechanicalFsmHandoffRequestV1(
            p5_7_projected_side_state=p57.projected_side_state,
            mechanical_fsm_input_prior_side_state=p57.projected_side_state,
        )
    )
    if not handoff.ok:
        return _fail_handoff(LayeredEpochHandoffFailureCodeV1.P57_TO_MECHANICAL_HANDOFF_FAILED)

    lifecycle_after = phase_result.lifecycle_after or request.lifecycle
    if phase_result.phase is RegimeSideStateProjectionPhaseV1.INITIAL_SEED:
        lifecycle_after = mark_initial_regime_orientation_seed_consumed_v1(lifecycle_after)

    mechanical_result: MechanicalTransitionValidationResultV1 | None = None
    provenance_surface = handoff.provenance_surface

    regime_bound_write = p57.projected_side_state is not request.host_prior_side_state
    mechanical_write = False
    canonical_next = p57.projected_side_state
    epoch_writer = SideStateEpochWriterV1.HOLD_NO_MUTATION

    if request.mechanical_next_side_state is not None:
        mechanical_result = validate_layered_mechanical_completion_provenance_chain_v1(
            evidence=request.scope_event_evidence,
            scope_event=request.scope_event,
            prior_side_state=p57.projected_side_state,
            next_side_state=request.mechanical_next_side_state,
            chop_scope_policy_blocked_transition=request.chop_scope_policy_blocked_transition,
        )
        if not mechanical_result.ok:
            return LayeredEpochCanonicalHandoffResultV1(
                ok=False,
                failure_codes=(LayeredEpochHandoffFailureCodeV1.MECHANICAL_FSM_FAILED.value,),
                phase=phase_result.phase,
                lifecycle_after=lifecycle_after,
                p57_projected_side_state=p57.projected_side_state,
                canonical_next_side_state=None,
                epoch_writer=None,
                regime_bound_write_asserted=regime_bound_write,
                mechanical_write_asserted=False,
                mechanical_fsm_result=mechanical_result,
                provenance_surface=mechanical_result.provenance_surface,
                state_switch_evidence=None,
            )
        mechanical_side_changed = request.mechanical_next_side_state is not p57.projected_side_state
        if mechanical_side_changed:
            mechanical_write = True
            canonical_next = request.mechanical_next_side_state
            provenance_surface = mechanical_result.provenance_surface
            epoch_writer = SideStateEpochWriterV1.MECHANICAL_FSM
        elif regime_bound_write:
            epoch_writer = SideStateEpochWriterV1.REGIME_BOUND_P57
        else:
            epoch_writer = SideStateEpochWriterV1.HOLD_NO_MUTATION
    elif regime_bound_write:
        epoch_writer = SideStateEpochWriterV1.REGIME_BOUND_P57
    else:
        epoch_writer = SideStateEpochWriterV1.HOLD_NO_MUTATION

    if regime_bound_write and mechanical_write:
        return _fail_handoff(LayeredEpochHandoffFailureCodeV1.CANONICAL_WRITER_UNRESOLVED)

    if canonical_next is None:
        return _fail_handoff(LayeredEpochHandoffFailureCodeV1.CANONICAL_NEXT_SIDESTATE_UNRESOLVED)

    reason_code = (
        provenance_surface.reason_code
        if provenance_surface is not None
        else "layered_epoch_hold_no_mutation"
    )
    state_switch = materialize_state_switch_evidence_v1_from_layered_handoff_v1(
        instrument_id=request.instrument_id,
        trading_epoch=request.trading_epoch,
        previous_side_state=request.host_prior_side_state,
        next_side_state=canonical_next,
        scope_event=request.scope_event,
        scope_event_id=request.scope_event_evidence.scope_event_id,
        transition_allowed=request.transition_allowed,
        transition_reason_code=reason_code,
    )
    if state_switch.next_side_state != canonical_next.value:
        return _fail_handoff(
            LayeredEpochHandoffFailureCodeV1.STATE_SWITCH_EVIDENCE_MATERIALIZATION_FAILED
        )

    orchestration = validate_layered_epoch_orchestration_bind_prep_v1(
        LayeredEpochOrchestrationBindPrepRequestV1(
            trading_epoch=request.trading_epoch,
            prior_side_state=request.host_prior_side_state,
            canonical_next_side_state=canonical_next,
            c4_entry_exit_sidestate_epoch=C4EntryExitSideStateEpochV1.POST_CANONICAL_NEXT_SIDE_STATE,
            c4_consumes_side_state=canonical_next,
            entry_exit_consumes_side_state=canonical_next,
            regime_bound_write_asserted=regime_bound_write,
            mechanical_write_asserted=mechanical_write,
            legacy_transition_state_writer_would_run=(
                request.legacy_transition_state_writer_would_run
            ),
            layered_bind_mode_active=request.layered_bind_mode_active,
            b2_scope_event_provenance_closed=True,
            b3_lifecycle_persistence_closed=True,
            b4_p57_state_switch_evidence_closed=True,
        )
    )
    if not orchestration.ok:
        return LayeredEpochCanonicalHandoffResultV1(
            ok=False,
            failure_codes=(
                LayeredEpochHandoffFailureCodeV1.P510A_ORCHESTRATION_BIND_PREP_FAILED.value,
                *orchestration.failure_codes,
            ),
            phase=phase_result.phase,
            lifecycle_after=lifecycle_after,
            p57_projected_side_state=p57.projected_side_state,
            canonical_next_side_state=canonical_next,
            epoch_writer=epoch_writer,
            regime_bound_write_asserted=regime_bound_write,
            mechanical_write_asserted=mechanical_write,
            mechanical_fsm_result=mechanical_result,
            provenance_surface=provenance_surface,
            state_switch_evidence=state_switch,
        )

    return LayeredEpochCanonicalHandoffResultV1(
        ok=True,
        failure_codes=(),
        phase=phase_result.phase,
        lifecycle_after=lifecycle_after,
        p57_projected_side_state=p57.projected_side_state,
        canonical_next_side_state=canonical_next,
        epoch_writer=epoch_writer,
        regime_bound_write_asserted=regime_bound_write,
        mechanical_write_asserted=mechanical_write,
        mechanical_fsm_result=mechanical_result,
        provenance_surface=provenance_surface,
        state_switch_evidence=state_switch,
    )


def state_switch_evidence_digest_parity_check_v1(
    evidence: StateSwitchEvidenceV1,
) -> bool:
    """Verify semantic_digest matches integrated replay digest algorithm."""
    expected = _compute_state_switch_digest(
        state_switch_id=evidence.state_switch_id,
        instrument_id=evidence.instrument_id,
        trading_epoch=evidence.trading_epoch,
        previous_side_state=evidence.previous_side_state,
        next_side_state=evidence.next_side_state,
        scope_event_type=evidence.scope_event_type,
        transition_allowed=evidence.transition_allowed,
        transition_reason_code=evidence.transition_reason_code,
    )
    return evidence.semantic_digest == expected


__all__ = [
    "AUTHORIZED_SCOPE_EVENT_PRODUCER_OWNER",
    "CONTRACT_OWNER",
    "LayeredEpochCanonicalHandoffRequestV1",
    "LayeredEpochCanonicalHandoffResultV1",
    "LayeredEpochHandoffFailureCodeV1",
    "MechanicalProvenanceClassificationResultV1",
    "classify_mechanical_scope_event_provenance_from_evidence_v1",
    "execute_layered_epoch_canonical_sidestate_handoff_v1",
    "map_scope_event_evidence_to_scope_event_v1",
    "materialize_state_switch_evidence_v1_from_layered_handoff_v1",
    "state_switch_evidence_digest_parity_check_v1",
    "validate_layered_mechanical_completion_provenance_chain_v1",
]
