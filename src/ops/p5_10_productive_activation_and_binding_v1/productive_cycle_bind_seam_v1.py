"""Productive cycle bind seam: P5 seam seal + CZ-4 replay + P5.10B canonical handoff."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Optional, Sequence, Tuple

from trading.market_state.distinct_market_observation_acceptor_v1 import ObservationCandidateV1
from trading.market_state.observation_identity_v1 import InstrumentObservationKeyV1
from trading.master_v2.deterministic_scope_event_generator_v1 import ScopeEventEvidenceV1
from trading.master_v2.double_play_entry_exit_policy_v0 import ExistingPositionSide
from trading.master_v2.double_play_state import ScopeEvent, SideState
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    IntegratedOfflineReplayInputV1,
    IntegratedOfflineReplayIntermediateV1,
    IntegratedOfflineReplayResultV1,
)
from trading.master_v2.layered_core_authority_seal_v1 import (
    LayeredCoreAuthoritySealV1,
    validate_layered_core_authority_seal_v1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.contracts_v1 import (
    SelectedFutureInputV1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.durable_state_v1 import (
    NakedLayeredCoreDurableStateError,
    restore_episode_from_store_v1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.orchestrator_v1 import (
    MechanicalStepSpecV1,
)
from trading.master_v2.naked_mv2_dp_regime_v1 import NakedRegimeV1

from src.ops.decision_config_ownership_and_consumer_closure_v1.canonical_values_v1 import (
    CANONICAL_UP_DISTANCE,
)
from src.ops.p5_10_productive_activation_and_binding_v1.constants_v1 import (
    PRODUCTIVE_BIND_SEAM_OWNER,
    PRODUCTIVE_CYCLE_LAYERED_CORE_BIND_ENABLED,
)
from src.ops.p5_10b_layered_epoch_remaining_authority_closure_v1.contract_v1 import (
    LayeredEpochCanonicalHandoffRequestV1,
    execute_layered_epoch_canonical_sidestate_handoff_v1,
    map_scope_event_evidence_to_scope_event_v1,
)
from src.ops.p5_2_productive_cycle_seam_invoke_and_authority_bind_v1.contract_v1 import (
    ProductiveCycleAuthorityBindRequestV1,
    ProductiveDecisionAuthorityModeV1,
    SideStateSeedClassV1,
    classify_side_state_seed_v1,
    validate_productive_cycle_authority_bind_v1,
)
from src.ops.p5_8b_regime_sidestate_projection_phase_authority_v1.contract_v1 import (
    fresh_regime_sidestate_projection_lifecycle_v1,
)
from src.ops.p5_8b_regime_sidestate_projection_phase_authority_v1.persistence_v1 import (
    RegimeSidestateProjectionLifecyclePersistBindingV1,
    RegimeSidestateProjectionLifecyclePersistenceError,
    atomic_persist_regime_sidestate_projection_lifecycle_v1,
    restore_regime_sidestate_projection_lifecycle_v1,
)
from src.ops.p5_productive_layered_core_authority_seam_v1.seam_v1 import (
    run_p5_layered_core_authority_seam_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from src.ops.stateful_confirmation_and_c1_productive_binding_v1.constants_v1 import (
    DEFAULT_VENUE,
)


class ProductiveLayeredCoreBindSeamError(ValueError):
    """Fail-closed productive P5.10 bind violation."""


@dataclass(frozen=True)
class ProductiveLayeredCoreBindCarryV1:
    bind_active: bool
    failure_codes: Tuple[str, ...]
    seal: Optional[LayeredCoreAuthoritySealV1]
    lifecycle_binding: Optional[RegimeSidestateProjectionLifecyclePersistBindingV1]
    cz4_delegation_suppressed_legacy_writers: bool
    sole_handoff_owner: str


def _fail_carry(*codes: str) -> ProductiveLayeredCoreBindCarryV1:
    normalized = tuple(dict.fromkeys(str(c) for c in codes if str(c).strip()))
    return ProductiveLayeredCoreBindCarryV1(
        bind_active=False,
        failure_codes=normalized,
        seal=None,
        lifecycle_binding=None,
        cz4_delegation_suppressed_legacy_writers=False,
        sole_handoff_owner=PRODUCTIVE_BIND_SEAM_OWNER,
    )


def _inactive_carry() -> ProductiveLayeredCoreBindCarryV1:
    return ProductiveLayeredCoreBindCarryV1(
        bind_active=False,
        failure_codes=(),
        seal=None,
        lifecycle_binding=None,
        cz4_delegation_suppressed_legacy_writers=False,
        sole_handoff_owner=PRODUCTIVE_BIND_SEAM_OWNER,
    )


def _observation_candidates_from_closes_v1(
    *,
    instrument_key: InstrumentObservationKeyV1,
    closes: Sequence[float],
    event_ts_unix: float,
) -> Tuple[ObservationCandidateV1, ...]:
    if len(closes) < 2:
        return ()
    t0 = float(event_ts_unix) - 60.0
    t1 = float(event_ts_unix)
    return (
        ObservationCandidateV1(
            venue=instrument_key.venue,
            canonical_instrument_id=instrument_key.canonical_instrument_id,
            venue_instrument_id=instrument_key.venue_instrument_id,
            venue_event_time=t0,
            mark_price=float(closes[-2]),
        ),
        ObservationCandidateV1(
            venue=instrument_key.venue,
            canonical_instrument_id=instrument_key.canonical_instrument_id,
            venue_instrument_id=instrument_key.venue_instrument_id,
            venue_event_time=t1,
            mark_price=float(closes[-1]),
        ),
    )


def _resolve_lifecycle_v1(
    *,
    store_root: Path,
    instrument_id: str,
    episode_snapshot_id: str,
) -> Tuple[object, RegimeSidestateProjectionLifecyclePersistBindingV1]:
    binding = RegimeSidestateProjectionLifecyclePersistBindingV1(
        instrument_id=instrument_id,
        layered_episode_snapshot_id=episode_snapshot_id,
    )
    try:
        lifecycle = restore_regime_sidestate_projection_lifecycle_v1(store_root, binding=binding)
        return lifecycle, binding
    except RegimeSidestateProjectionLifecyclePersistenceError:
        lifecycle = fresh_regime_sidestate_projection_lifecycle_v1(instrument_id=instrument_id)
        return lifecycle, binding


def prepare_productive_layered_core_replay_bind_v1(
    *,
    productive_layered_core_bind_requested: bool,
    layered_core_store_root: Path | None,
    bound_instrument: BoundInstrumentV1,
    replay_input: IntegratedOfflineReplayInputV1,
    mark_price_m_t: float,
    finalized_closes: Sequence[float],
    last_finalized_event_ts_unix: float,
    venue_flat: bool,
    existing_position_side: ExistingPositionSide,
    side_state_from_cursor_restore: bool,
    side_state_from_venue_position: bool,
    existing_scope_present: bool,
) -> Tuple[IntegratedOfflineReplayInputV1, ProductiveLayeredCoreBindCarryV1]:
    """Attach layered-core seal for CZ-4 delegation when bind is requested and enabled."""
    if not productive_layered_core_bind_requested:
        return replay_input, _inactive_carry()

    if not PRODUCTIVE_CYCLE_LAYERED_CORE_BIND_ENABLED:
        return replay_input, _fail_carry("productive_layered_core_bind_disabled")

    if layered_core_store_root is None:
        return replay_input, _fail_carry("layered_core_store_root_required")

    if not existing_scope_present:
        return replay_input, _fail_carry("layered_bind_requires_existing_scope_carrier")

    instrument_id = str(bound_instrument.instrument_id or "").strip()
    venue_native_id = str(bound_instrument.venue_native_id or "").strip() or instrument_id
    instrument_key = InstrumentObservationKeyV1(
        venue=DEFAULT_VENUE,
        canonical_instrument_id=instrument_id,
        venue_instrument_id=venue_native_id,
    )
    store_root = Path(layered_core_store_root)

    seed_class = classify_side_state_seed_v1(
        from_venue_position=side_state_from_venue_position,
        from_cursor_restore=side_state_from_cursor_restore,
        claims_core_regime_authority=False,
    )
    if seed_class is SideStateSeedClassV1.CORE_REGIME_AUTHORITY_CLAIM:
        return replay_input, _fail_carry("venue_cursor_cannot_claim_core_regime_authority")

    mechanical_step = MechanicalStepSpecV1(
        mark_price_m_t=float(mark_price_m_t),
        proposed_d_t=float(CANONICAL_UP_DISTANCE),
    )
    selected = SelectedFutureInputV1(
        instrument_id=instrument_id,
        instrument_key=instrument_key,
    )
    observations = _observation_candidates_from_closes_v1(
        instrument_key=instrument_key,
        closes=finalized_closes,
        event_ts_unix=last_finalized_event_ts_unix,
    )
    restore_existing = True
    try:
        restore_episode_from_store_v1(store_root, expected_instrument_id=instrument_id)
    except NakedLayeredCoreDurableStateError:
        restore_existing = False
        if not observations:
            return replay_input, _fail_carry("layered_core_initialization_observations_required")

    seam = run_p5_layered_core_authority_seam_v1(
        store_root=store_root,
        selected=selected,
        mark_price_m_t=float(mark_price_m_t),
        mechanical_step=mechanical_step if restore_existing else None,
        restore_existing=restore_existing,
        initialization_observations=observations if not restore_existing else None,
    )
    if not seam.ok or seam.seal is None:
        return replay_input, _fail_carry(*(seam.failure_codes or ("p5_seam_failed",)))

    seal_validation = validate_layered_core_authority_seal_v1(
        seam.seal, instrument_id=instrument_id
    )
    if not seal_validation.ok:
        return replay_input, _fail_carry(*seal_validation.failure_codes)

    post_seal_bind = validate_productive_cycle_authority_bind_v1(
        ProductiveCycleAuthorityBindRequestV1(
            productive_layered_core_bind_requested=True,
            decision_authority_mode=ProductiveDecisionAuthorityModeV1.LAYERED_CORE_SEAL_DELEGATED,
            seal_present=True,
            seal_validation_ok=True,
            cz4_delegation_intended=True,
            legacy_scope_writer_would_run=False,
            legacy_transition_writer_would_run=False,
            legacy_dynamic_boundary_writer_would_run=False,
            legacy_canonical_distances_as_d_t_authority=False,
            side_state_seed_class=seed_class,
            fallback_to_legacy_on_missing_core=False,
        )
    )
    if not post_seal_bind.ok:
        return replay_input, _fail_carry(*post_seal_bind.failure_codes)

    bound_input = replace(replay_input, layered_core_authority_seal=seam.seal)
    lifecycle_binding = RegimeSidestateProjectionLifecyclePersistBindingV1(
        instrument_id=instrument_id,
        layered_episode_snapshot_id=str(seam.seal.episode_snapshot_id),
    )
    return (
        bound_input,
        ProductiveLayeredCoreBindCarryV1(
            bind_active=True,
            failure_codes=(),
            seal=seam.seal,
            lifecycle_binding=lifecycle_binding,
            cz4_delegation_suppressed_legacy_writers=True,
            sole_handoff_owner=PRODUCTIVE_BIND_SEAM_OWNER,
        ),
    )


def _mapped_scope_event_v1(evidence: ScopeEventEvidenceV1) -> ScopeEvent:
    return map_scope_event_evidence_to_scope_event_v1(evidence)


def finalize_productive_layered_core_replay_bind_v1(
    *,
    replay: IntegratedOfflineReplayResultV1,
    carry: ProductiveLayeredCoreBindCarryV1,
    layered_core_store_root: Path | None,
    host_prior_side_state: SideState,
    trading_epoch: int,
    instrument_id: str,
    venue_flat: bool,
    existing_position_side: ExistingPositionSide,
) -> IntegratedOfflineReplayResultV1:
    """Apply P5.10B canonical sidestate handoff (POST_CANONICAL_NEXT_SIDE_STATE)."""
    if not carry.bind_active or carry.seal is None:
        return replay
    if replay.intermediate is None or not replay.replay_pass:
        return replay

    seal = carry.seal
    regime_pre = NakedRegimeV1(str(seal.regime_pre))
    regime_post = NakedRegimeV1(str(seal.regime_post))
    regime_pre_equals_post = regime_pre == regime_post

    store_root = Path(layered_core_store_root) if layered_core_store_root is not None else None
    if store_root is None or carry.lifecycle_binding is None:
        return replace(
            replay,
            replay_pass=False,
            fail_reasons=tuple(
                dict.fromkeys((*replay.fail_reasons, "layered_bind_finalize_store_required"))
            ),
        )

    lifecycle, binding = _resolve_lifecycle_v1(
        store_root=store_root,
        instrument_id=instrument_id,
        episode_snapshot_id=str(seal.episode_snapshot_id),
    )

    intermediate = replay.intermediate
    scope_evidence = intermediate.scope_event
    scope_event = _mapped_scope_event_v1(scope_evidence)
    transition = intermediate.transition_decision
    transition_allowed = bool(transition.allowed) if transition is not None else False
    transition_reason = (
        str(transition.reason_code)
        if transition is not None
        else "layered_bind_no_transition_decision"
    )

    handoff = execute_layered_epoch_canonical_sidestate_handoff_v1(
        LayeredEpochCanonicalHandoffRequestV1(
            trading_epoch=int(trading_epoch),
            instrument_id=instrument_id,
            host_prior_side_state=host_prior_side_state,
            lifecycle=lifecycle,
            venue_flat=bool(venue_flat),
            existing_position_side=existing_position_side,
            switch_condition_met=bool(seal.switch_condition_met),
            regime_pre=regime_pre,
            regime_post=regime_post,
            regime_pre_equals_post=regime_pre_equals_post,
            scope_event_evidence=scope_evidence,
            scope_event=scope_event,
            mechanical_next_side_state=None,
            chop_scope_policy_blocked_transition=False,
            layered_bind_mode_active=True,
            legacy_transition_state_writer_would_run=False,
            transition_allowed=transition_allowed,
            transition_reason_code=transition_reason,
        )
    )
    if not handoff.ok or handoff.state_switch_evidence is None:
        reasons = handoff.failure_codes or ("layered_epoch_handoff_failed",)
        return replace(
            replay,
            replay_pass=False,
            fail_reasons=tuple(dict.fromkeys((*replay.fail_reasons, *reasons))),
        )

    patched_intermediate = replace(
        intermediate,
        state_switch=handoff.state_switch_evidence,
    )
    if handoff.lifecycle_after is not None:
        try:
            atomic_persist_regime_sidestate_projection_lifecycle_v1(
                store_root,
                lifecycle=handoff.lifecycle_after,
                binding=binding,
            )
        except RegimeSidestateProjectionLifecyclePersistenceError as exc:
            return replace(
                replay,
                replay_pass=False,
                fail_reasons=tuple(
                    dict.fromkeys((*replay.fail_reasons, f"lifecycle_persist_fail_closed:{exc}"))
                ),
            )

    return replace(replay, intermediate=patched_intermediate)


__all__ = [
    "ProductiveLayeredCoreBindCarryV1",
    "ProductiveLayeredCoreBindSeamError",
    "finalize_productive_layered_core_replay_bind_v1",
    "prepare_productive_layered_core_replay_bind_v1",
]
