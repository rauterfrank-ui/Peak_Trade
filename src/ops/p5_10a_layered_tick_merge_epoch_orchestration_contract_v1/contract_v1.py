"""Layered trading epoch/tick merge orchestration (validator only; no productive wiring).

Orders existing P5 layered-core, P5.7, P5.8B, P5.9D, and CZ-4 bind-prep artifacts for one
trading epoch. Does not invoke seam, replay, transition_state, or activation gates.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Sequence, Tuple

from trading.master_v2.double_play_state import SideState

from src.ops.p5_10a_layered_tick_merge_epoch_orchestration_contract_v1.constants_v1 import (
    PRODUCTIVE_CYCLE_LAYERED_CORE_BIND_ENABLED,
    REGIME_SIDESTATE_MAPPING_CONTRACT_AUTHORIZED,
)
from src.ops.p5_9d_layered_mechanical_sidestate_fsm_contract_v1.contract_v1 import (
    LayeredSidestateEpochWriteRequestV1,
    validate_single_writer_per_trading_epoch_v1,
)

CONTRACT_OWNER = "ops.p5_10a_layered_tick_merge_epoch_orchestration_contract_v1.contract_v1"


class LayeredTradingEpochStepV1(str, Enum):
    """Deterministic orchestration order for one layered trading epoch (bind-prep)."""

    PRIOR_PERSISTED_STATE_LOAD = "prior_persisted_state_load"
    LAYERED_SEAM_AND_SEAL = "layered_seam_and_seal"
    LIFECYCLE_PHASE_RESOLUTION = "lifecycle_phase_resolution"
    REGIME_BOUND_P57_PROJECTION = "regime_bound_p57_projection"
    MECHANICAL_SIDESTATE_PHASE = "mechanical_sidestate_phase"
    CANONICAL_NEXT_SIDE_STATE = "canonical_next_side_state"
    C4_AND_ENTRY_EXIT_CONSUMPTION = "c4_and_entry_exit_consumption"
    DURABLE_CARRY_OUT = "durable_carry_out"


CANONICAL_LAYERED_EPOCH_STEP_ORDER: Tuple[LayeredTradingEpochStepV1, ...] = (
    LayeredTradingEpochStepV1.PRIOR_PERSISTED_STATE_LOAD,
    LayeredTradingEpochStepV1.LAYERED_SEAM_AND_SEAL,
    LayeredTradingEpochStepV1.LIFECYCLE_PHASE_RESOLUTION,
    LayeredTradingEpochStepV1.REGIME_BOUND_P57_PROJECTION,
    LayeredTradingEpochStepV1.MECHANICAL_SIDESTATE_PHASE,
    LayeredTradingEpochStepV1.CANONICAL_NEXT_SIDE_STATE,
    LayeredTradingEpochStepV1.C4_AND_ENTRY_EXIT_CONSUMPTION,
    LayeredTradingEpochStepV1.DURABLE_CARRY_OUT,
)


class C4EntryExitSideStateEpochV1(str, Enum):
    """Which SideState identity C4 / Entry-Exit consume within a layered epoch."""

    POST_CANONICAL_NEXT_SIDE_STATE = "post_canonical_next_side_state"
    UNSPECIFIED = "unspecified"
    LEGACY_INTEGRATED_REPLAY_PRE_STATE_SWITCH = (
        "legacy_integrated_replay_pre_state_switch_navigation_only"
    )


class SideStateEpochWriterV1(str, Enum):
    REGIME_BOUND_P57 = "regime_bound_p57"
    MECHANICAL_FSM = "mechanical_fsm"
    HOLD_NO_MUTATION = "hold_no_mutation"
    LEGACY_TRANSITION_STATE = "legacy_transition_state"


class ExternalEpochClosureIdV1(str, Enum):
    B2_SCOPE_EVENT_PROVENANCE = "b2_scope_event_provenance"
    B3_P58B_LIFECYCLE_PERSISTENCE = "b3_p58b_lifecycle_persistence"
    B4_P57_TO_STATE_SWITCH_EVIDENCE = "b4_p57_to_state_switch_evidence"


class EpochOrchestrationFailureCodeV1(str, Enum):
    EPOCH_STEP_ORDER_DRIFT = "epoch_step_order_drift"
    PRIOR_SIDESTATE_UNSPECIFIED = "prior_sidestate_unspecified"
    CANONICAL_NEXT_SIDESTATE_UNSPECIFIED = "canonical_next_sidestate_unspecified"
    PRIOR_NEXT_IDENTITY_MISMATCH = "prior_next_identity_mismatch"
    C4_ENTRY_EXIT_EPOCH_UNSPECIFIED = "c4_entry_exit_epoch_unspecified"
    C4_ENTRY_EXIT_EPOCH_NOT_POST_CANONICAL = "c4_entry_exit_epoch_not_post_canonical"
    C4_CONSUMES_DIFFERENT_SIDESTATE_THAN_CANONICAL = (
        "c4_consumes_different_sidestate_than_canonical"
    )
    ENTRY_EXIT_CONSUMES_DIFFERENT_SIDESTATE_THAN_CANONICAL = (
        "entry_exit_consumes_different_sidestate_than_canonical"
    )
    DUAL_SIDESTATE_WRITER_FORBIDDEN = "dual_sidestate_writer_forbidden"
    LEGACY_TRANSITION_PARALLEL_LAYERED_WRITER_FORBIDDEN = (
        "legacy_transition_parallel_layered_writer_forbidden"
    )
    LAYERED_WRITER_COUNT_NOT_EXACTLY_ONE = "layered_writer_count_not_exactly_one"
    ACTIVATION_MAPPING_NOT_AUTHORIZED = "activation_mapping_not_authorized"
    ACTIVATION_PRODUCTIVE_BIND_NOT_ENABLED = "activation_productive_bind_not_enabled"
    EXTERNAL_CLOSURE_B2_NOT_CLOSED = "external_closure_b2_not_closed"
    EXTERNAL_CLOSURE_B3_NOT_CLOSED = "external_closure_b3_not_closed"
    EXTERNAL_CLOSURE_B4_NOT_CLOSED = "external_closure_b4_not_closed"


@dataclass(frozen=True)
class LayeredEpochSideStateIdentityV1:
    """Explicit prior/next SideState for one trading epoch (bind-prep surface)."""

    trading_epoch: int
    prior_side_state: SideState
    canonical_next_side_state: SideState


@dataclass(frozen=True)
class LayeredEpochOrchestrationBindPrepRequestV1:
    """Declarative bind-prep snapshot for one layered epoch (no runtime invoke)."""

    trading_epoch: int
    prior_side_state: SideState
    canonical_next_side_state: SideState
    c4_entry_exit_sidestate_epoch: C4EntryExitSideStateEpochV1
    c4_consumes_side_state: Optional[SideState]
    entry_exit_consumes_side_state: Optional[SideState]
    regime_bound_write_asserted: bool
    mechanical_write_asserted: bool
    legacy_transition_state_writer_would_run: bool
    layered_bind_mode_active: bool
    b2_scope_event_provenance_closed: bool
    b3_lifecycle_persistence_closed: bool
    b4_p57_state_switch_evidence_closed: bool


@dataclass(frozen=True)
class EpochOrchestrationValidationResultV1:
    ok: bool
    failure_codes: Tuple[str, ...]


def canonical_layered_epoch_step_index_v1(step: LayeredTradingEpochStepV1) -> int:
    return CANONICAL_LAYERED_EPOCH_STEP_ORDER.index(step)


def validate_deterministic_epoch_step_order_v1(
    observed_steps: Sequence[LayeredTradingEpochStepV1],
) -> EpochOrchestrationValidationResultV1:
    """Observed step sequence must be a prefix of the canonical order (strictly increasing)."""
    if not observed_steps:
        return EpochOrchestrationValidationResultV1(ok=True, failure_codes=())
    last_idx = -1
    for step in observed_steps:
        idx = canonical_layered_epoch_step_index_v1(step)
        if idx <= last_idx:
            return EpochOrchestrationValidationResultV1(
                ok=False,
                failure_codes=(EpochOrchestrationFailureCodeV1.EPOCH_STEP_ORDER_DRIFT.value,),
            )
        last_idx = idx
    return EpochOrchestrationValidationResultV1(ok=True, failure_codes=())


def validate_explicit_prior_next_identity_v1(
    identity: LayeredEpochSideStateIdentityV1,
) -> EpochOrchestrationValidationResultV1:
    if identity.trading_epoch < 0:
        return EpochOrchestrationValidationResultV1(
            ok=False,
            failure_codes=(EpochOrchestrationFailureCodeV1.PRIOR_SIDESTATE_UNSPECIFIED.value,),
        )
    if not isinstance(identity.prior_side_state, SideState):
        return EpochOrchestrationValidationResultV1(
            ok=False,
            failure_codes=(EpochOrchestrationFailureCodeV1.PRIOR_SIDESTATE_UNSPECIFIED.value,),
        )
    if not isinstance(identity.canonical_next_side_state, SideState):
        return EpochOrchestrationValidationResultV1(
            ok=False,
            failure_codes=(
                EpochOrchestrationFailureCodeV1.CANONICAL_NEXT_SIDESTATE_UNSPECIFIED.value,
            ),
        )
    return EpochOrchestrationValidationResultV1(ok=True, failure_codes=())


def validate_exactly_one_layered_sidestate_writer_v1(
    *,
    regime_bound_write_asserted: bool,
    mechanical_write_asserted: bool,
) -> EpochOrchestrationValidationResultV1:
    single = validate_single_writer_per_trading_epoch_v1(
        LayeredSidestateEpochWriteRequestV1(
            trading_epoch=0,
            regime_bound_write_asserted=regime_bound_write_asserted,
            mechanical_write_asserted=mechanical_write_asserted,
        )
    )
    if not single.ok:
        return EpochOrchestrationValidationResultV1(
            ok=False,
            failure_codes=(EpochOrchestrationFailureCodeV1.DUAL_SIDESTATE_WRITER_FORBIDDEN.value,),
        )
    writer_count = int(regime_bound_write_asserted) + int(mechanical_write_asserted)
    if writer_count > 1:
        return EpochOrchestrationValidationResultV1(
            ok=False,
            failure_codes=(EpochOrchestrationFailureCodeV1.DUAL_SIDESTATE_WRITER_FORBIDDEN.value,),
        )
    return EpochOrchestrationValidationResultV1(ok=True, failure_codes=())


def validate_no_parallel_legacy_transition_writer_v1(
    *,
    layered_bind_mode_active: bool,
    legacy_transition_state_writer_would_run: bool,
    layered_sidestate_writer_asserted: bool,
) -> EpochOrchestrationValidationResultV1:
    if (
        layered_bind_mode_active
        and legacy_transition_state_writer_would_run
        and layered_sidestate_writer_asserted
    ):
        return EpochOrchestrationValidationResultV1(
            ok=False,
            failure_codes=(
                EpochOrchestrationFailureCodeV1.LEGACY_TRANSITION_PARALLEL_LAYERED_WRITER_FORBIDDEN.value,
            ),
        )
    if layered_bind_mode_active and legacy_transition_state_writer_would_run:
        return EpochOrchestrationValidationResultV1(
            ok=False,
            failure_codes=(
                EpochOrchestrationFailureCodeV1.LEGACY_TRANSITION_PARALLEL_LAYERED_WRITER_FORBIDDEN.value,
            ),
        )
    return EpochOrchestrationValidationResultV1(ok=True, failure_codes=())


def validate_c4_entry_exit_epoch_boundary_v1(
    *,
    c4_entry_exit_sidestate_epoch: C4EntryExitSideStateEpochV1,
    canonical_next_side_state: SideState,
    c4_consumes_side_state: Optional[SideState],
    entry_exit_consumes_side_state: Optional[SideState],
) -> EpochOrchestrationValidationResultV1:
    if c4_entry_exit_sidestate_epoch is C4EntryExitSideStateEpochV1.UNSPECIFIED:
        return EpochOrchestrationValidationResultV1(
            ok=False,
            failure_codes=(EpochOrchestrationFailureCodeV1.C4_ENTRY_EXIT_EPOCH_UNSPECIFIED.value,),
        )
    if (
        c4_entry_exit_sidestate_epoch
        is C4EntryExitSideStateEpochV1.LEGACY_INTEGRATED_REPLAY_PRE_STATE_SWITCH
    ):
        return EpochOrchestrationValidationResultV1(
            ok=False,
            failure_codes=(
                EpochOrchestrationFailureCodeV1.C4_ENTRY_EXIT_EPOCH_NOT_POST_CANONICAL.value,
            ),
        )
    if c4_consumes_side_state is None or entry_exit_consumes_side_state is None:
        return EpochOrchestrationValidationResultV1(
            ok=False,
            failure_codes=(EpochOrchestrationFailureCodeV1.C4_ENTRY_EXIT_EPOCH_UNSPECIFIED.value,),
        )
    failures: list[EpochOrchestrationFailureCodeV1] = []
    if c4_consumes_side_state is not canonical_next_side_state:
        failures.append(
            EpochOrchestrationFailureCodeV1.C4_CONSUMES_DIFFERENT_SIDESTATE_THAN_CANONICAL
        )
    if entry_exit_consumes_side_state is not canonical_next_side_state:
        failures.append(
            EpochOrchestrationFailureCodeV1.ENTRY_EXIT_CONSUMES_DIFFERENT_SIDESTATE_THAN_CANONICAL
        )
    if failures:
        return EpochOrchestrationValidationResultV1(
            ok=False,
            failure_codes=tuple(dict.fromkeys(c.value for c in failures)),
        )
    return EpochOrchestrationValidationResultV1(ok=True, failure_codes=())


def validate_external_epoch_closures_not_promoted_v1(
    *,
    b2_closed: bool,
    b3_closed: bool,
    b4_closed: bool,
    activation_requested: bool,
) -> EpochOrchestrationValidationResultV1:
    if not activation_requested:
        return EpochOrchestrationValidationResultV1(ok=True, failure_codes=())
    failures: list[EpochOrchestrationFailureCodeV1] = []
    if not b2_closed:
        failures.append(EpochOrchestrationFailureCodeV1.EXTERNAL_CLOSURE_B2_NOT_CLOSED)
    if not b3_closed:
        failures.append(EpochOrchestrationFailureCodeV1.EXTERNAL_CLOSURE_B3_NOT_CLOSED)
    if not b4_closed:
        failures.append(EpochOrchestrationFailureCodeV1.EXTERNAL_CLOSURE_B4_NOT_CLOSED)
    if not REGIME_SIDESTATE_MAPPING_CONTRACT_AUTHORIZED:
        failures.append(EpochOrchestrationFailureCodeV1.ACTIVATION_MAPPING_NOT_AUTHORIZED)
    if not PRODUCTIVE_CYCLE_LAYERED_CORE_BIND_ENABLED:
        failures.append(EpochOrchestrationFailureCodeV1.ACTIVATION_PRODUCTIVE_BIND_NOT_ENABLED)
    if failures:
        return EpochOrchestrationValidationResultV1(
            ok=False,
            failure_codes=tuple(dict.fromkeys(c.value for c in failures)),
        )
    return EpochOrchestrationValidationResultV1(ok=True, failure_codes=())


def _merge_failures(
    *results: EpochOrchestrationValidationResultV1,
) -> EpochOrchestrationValidationResultV1:
    codes: list[str] = []
    ok = True
    for r in results:
        if not r.ok:
            ok = False
            codes.extend(r.failure_codes)
    if ok:
        return EpochOrchestrationValidationResultV1(ok=True, failure_codes=())
    return EpochOrchestrationValidationResultV1(
        ok=False,
        failure_codes=tuple(dict.fromkeys(codes)),
    )


def validate_layered_epoch_orchestration_bind_prep_v1(
    request: LayeredEpochOrchestrationBindPrepRequestV1,
) -> EpochOrchestrationValidationResultV1:
    """Validate declarative layered epoch orchestration (contract-only; no wiring)."""
    identity = LayeredEpochSideStateIdentityV1(
        trading_epoch=request.trading_epoch,
        prior_side_state=request.prior_side_state,
        canonical_next_side_state=request.canonical_next_side_state,
    )
    layered_writer = request.regime_bound_write_asserted or request.mechanical_write_asserted
    return _merge_failures(
        validate_explicit_prior_next_identity_v1(identity),
        validate_exactly_one_layered_sidestate_writer_v1(
            regime_bound_write_asserted=request.regime_bound_write_asserted,
            mechanical_write_asserted=request.mechanical_write_asserted,
        ),
        validate_no_parallel_legacy_transition_writer_v1(
            layered_bind_mode_active=request.layered_bind_mode_active,
            legacy_transition_state_writer_would_run=(
                request.legacy_transition_state_writer_would_run
            ),
            layered_sidestate_writer_asserted=layered_writer,
        ),
        validate_c4_entry_exit_epoch_boundary_v1(
            c4_entry_exit_sidestate_epoch=request.c4_entry_exit_sidestate_epoch,
            canonical_next_side_state=request.canonical_next_side_state,
            c4_consumes_side_state=request.c4_consumes_side_state,
            entry_exit_consumes_side_state=request.entry_exit_consumes_side_state,
        ),
        validate_external_epoch_closures_not_promoted_v1(
            b2_closed=request.b2_scope_event_provenance_closed,
            b3_closed=request.b3_lifecycle_persistence_closed,
            b4_closed=request.b4_p57_state_switch_evidence_closed,
            activation_requested=False,
        ),
    )


def validate_layered_epoch_activation_readiness_v1(
    request: LayeredEpochOrchestrationBindPrepRequestV1,
) -> EpochOrchestrationValidationResultV1:
    """Activation remains fail-closed until B2/B3/B4 and bind flags are explicitly closed."""
    prep = validate_layered_epoch_orchestration_bind_prep_v1(request)
    if not prep.ok:
        return prep
    return validate_external_epoch_closures_not_promoted_v1(
        b2_closed=request.b2_scope_event_provenance_closed,
        b3_closed=request.b3_lifecycle_persistence_closed,
        b4_closed=request.b4_p57_state_switch_evidence_closed,
        activation_requested=True,
    )


__all__ = [
    "CANONICAL_LAYERED_EPOCH_STEP_ORDER",
    "C4EntryExitSideStateEpochV1",
    "CONTRACT_OWNER",
    "EpochOrchestrationFailureCodeV1",
    "EpochOrchestrationValidationResultV1",
    "ExternalEpochClosureIdV1",
    "LayeredEpochOrchestrationBindPrepRequestV1",
    "LayeredEpochSideStateIdentityV1",
    "LayeredTradingEpochStepV1",
    "SideStateEpochWriterV1",
    "canonical_layered_epoch_step_index_v1",
    "validate_c4_entry_exit_epoch_boundary_v1",
    "validate_deterministic_epoch_step_order_v1",
    "validate_exactly_one_layered_sidestate_writer_v1",
    "validate_explicit_prior_next_identity_v1",
    "validate_external_epoch_closures_not_promoted_v1",
    "validate_layered_epoch_activation_readiness_v1",
    "validate_layered_epoch_orchestration_bind_prep_v1",
    "validate_no_parallel_legacy_transition_writer_v1",
]
