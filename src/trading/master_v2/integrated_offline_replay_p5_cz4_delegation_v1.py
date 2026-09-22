"""P5.1 CZ-4 delegated replay: skip integrated I-1..I-3 writers when seal is valid."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional, Tuple

if TYPE_CHECKING:
    from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
        IntegratedOfflineReplayInputV1,
        StateSwitchEvidenceV1,
    )

from trading.master_v2.canonical_scope_initialization_v1 import (
    CanonicalScopeInitializationResultV1,
    CanonicalScopeLifecycleState,
)
from trading.master_v2.deterministic_scope_event_generator_v1 import (
    CanonicalScopeEventType,
    EvaluatedThresholdsV1,
    ScopeConfirmationStateV1,
    ScopeEventEvidenceV1,
    ScopeEventSemanticBindingV1,
    with_computed_scope_event_digest,
)
from trading.master_v2.double_play_state import (
    RuntimeScopeState,
    ScopeEvent,
    SideState,
    TransitionDecision,
)
from trading.master_v2.layered_core_authority_seal_v1 import (
    LayeredCoreAuthoritySealV1,
    validate_layered_core_authority_seal_v1,
)

P5_CZ4_DELEGATION_REASON = "P5_CZ4_DELEGATED_EXTERNAL_LAYERED_CORE_AUTHORITY"
P5_CZ4_DELEGATION_OWNER = "trading.master_v2.integrated_offline_replay_p5_cz4_delegation_v1"


@dataclass(frozen=True)
class P5Cz4DelegatedReplayContextV1:
    scope_init: CanonicalScopeInitializationResultV1
    current_scope: object
    scope_event: ScopeEventEvidenceV1
    mapped_event: ScopeEvent
    scope_event_ref: object
    scope_chop_policy_active: bool
    runtime_scope_pre: RuntimeScopeState
    runtime_scope_after: RuntimeScopeState
    next_side_state: SideState
    transition: TransitionDecision
    state_switch: Any


def _synthetic_noop_scope_event_v1(
    inp: IntegratedOfflineReplayInputV1,  # noqa: F821
    *,
    seal: LayeredCoreAuthoritySealV1,
) -> ScopeEventEvidenceV1:
    from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
        _derive_state_switch_id,
    )

    current_scope = inp.existing_scope
    assert current_scope is not None
    confirmation = inp.scope_confirmation_state
    trailing = float(seal.r_t) if seal.r_t > 0 else float(current_scope.trailing_anchor)
    thresholds = EvaluatedThresholdsV1(
        up_candidate_threshold=float(seal.d_t),
        downscope_candidate_threshold=float(seal.d_t),
        adverse_exit_threshold=float(inp.adverse_exit_distance),
        reversal_candidate_threshold=float(inp.reversal_distance),
    )
    binding = ScopeEventSemanticBindingV1(
        market_context_digest=inp.canonical_market_context.input_digest or "",
        current_direction_state=inp.scope_direction_state,
        current_price=float(inp.current_price),
        trailing_anchor=trailing,
        up_distance=float(seal.d_t),
        adverse_exit_distance=float(inp.adverse_exit_distance),
        reversal_distance=float(inp.reversal_distance),
        confirmation_epochs=int(inp.confirmation_epochs),
        cooldown_active=bool(inp.scope_cooldown_state.active),
        cooldown_remaining_epochs=int(inp.scope_cooldown_state.remaining_epochs),
        generator_policy_version=inp.policies.scope_event_generator.policy_version,
    )
    scope_event_id = _derive_state_switch_id(
        inp.instrument_id,
        inp.trading_epoch,
        f"p5-delegated-{seal.seal_id}",
    )
    raw = ScopeEventEvidenceV1(
        scope_event_id=scope_event_id,
        instrument_id=inp.instrument_id,
        trading_epoch=inp.trading_epoch,
        event_type=CanonicalScopeEventType.NOOP,
        previous_confirmation_state=confirmation,
        next_confirmation_state=confirmation,
        candidate_count_before=int(confirmation.candidate_count),
        candidate_count_after=int(confirmation.candidate_count),
        evaluated_thresholds=thresholds,
        matched_conditions=("p5_cz4_delegated_noop",),
        blocked_reasons=(),
        current_scope_ref=current_scope,
        next_scope_effective_epoch=None,
        semantic_binding=binding,
        semantic_digest="",
    )
    digest = hashlib.sha256(
        f"{scope_event_id}:{seal.seal_digest}:{CanonicalScopeEventType.NOOP.value}".encode()
    ).hexdigest()
    with_digest = ScopeEventEvidenceV1(
        scope_event_id=raw.scope_event_id,
        instrument_id=raw.instrument_id,
        trading_epoch=raw.trading_epoch,
        event_type=raw.event_type,
        previous_confirmation_state=raw.previous_confirmation_state,
        next_confirmation_state=raw.next_confirmation_state,
        candidate_count_before=raw.candidate_count_before,
        candidate_count_after=raw.candidate_count_after,
        evaluated_thresholds=raw.evaluated_thresholds,
        matched_conditions=raw.matched_conditions,
        blocked_reasons=raw.blocked_reasons,
        current_scope_ref=raw.current_scope_ref,
        next_scope_effective_epoch=raw.next_scope_effective_epoch,
        semantic_binding=raw.semantic_binding,
        semantic_digest=digest,
    )
    return with_computed_scope_event_digest(with_digest)


def try_build_p5_cz4_delegated_replay_context_v1(
    inp: IntegratedOfflineReplayInputV1,  # type: ignore[name-defined]
) -> Tuple[Optional[P5Cz4DelegatedReplayContextV1], Tuple[str, ...]]:
    from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
        StateSwitchEvidenceV1,
        _canonical_scope_event_to_scope_event,
        _compute_state_switch_digest,
        _derive_state_switch_id,
        _scope_event_ref_from_evidence,
    )

    seal = inp.layered_core_authority_seal
    validation = validate_layered_core_authority_seal_v1(
        seal,
        instrument_id=inp.instrument_id,
    )
    if not validation.ok:
        return None, validation.failure_codes

    assert seal is not None

    from src.ops.p5_2_productive_cycle_seam_invoke_and_authority_bind_v1.contract_v1 import (
        validate_cz4_delegation_authority_bind_v1,
    )

    bind = validate_cz4_delegation_authority_bind_v1(seal=seal, side_state=inp.side_state)
    if not bind.ok:
        return None, bind.failure_codes
    if inp.existing_scope is None:
        return None, ("p5_delegation_requires_existing_scope_carrier",)

    current_scope = inp.existing_scope
    scope_init = CanonicalScopeInitializationResultV1(
        scope=current_scope,
        lifecycle_state=CanonicalScopeLifecycleState.SCOPE_VALID,
        block_reasons=(),
        scope_event_generated=False,
        is_authority=False,
        is_signal=False,
        execution_eligible=False,
        live_authorization=False,
        order_effect=False,
        runtime_effect=False,
    )

    scope_event = _synthetic_noop_scope_event_v1(inp, seal=seal)
    mapped_event = _canonical_scope_event_to_scope_event(
        scope_event.event_type,
        matched_conditions=tuple(scope_event.matched_conditions),
    )
    scope_event_ref = _scope_event_ref_from_evidence(scope_event)

    runtime_pre = inp.runtime_scope_state
    if runtime_pre is None:
        runtime_pre = RuntimeScopeState(
            anchor_price=float(seal.r_t),
            now_tick=int(inp.now_tick),
        )
    runtime_after = runtime_pre
    next_side_state = inp.side_state
    transition = TransitionDecision(False, P5_CZ4_DELEGATION_REASON)

    state_switch_id = _derive_state_switch_id(
        inp.instrument_id,
        inp.trading_epoch,
        scope_event.scope_event_id,
    )
    switch_digest = _compute_state_switch_digest(
        state_switch_id=state_switch_id,
        instrument_id=inp.instrument_id,
        trading_epoch=inp.trading_epoch,
        previous_side_state=inp.side_state.value,
        next_side_state=next_side_state.value,
        scope_event_type=scope_event.event_type.value,
        transition_allowed=transition.allowed,
        transition_reason_code=transition.reason_code,
    )
    state_switch = StateSwitchEvidenceV1(
        state_switch_id=state_switch_id,
        instrument_id=inp.instrument_id,
        trading_epoch=inp.trading_epoch,
        previous_side_state=inp.side_state.value,
        next_side_state=next_side_state.value,
        scope_event_type=scope_event.event_type.value,
        transition_allowed=transition.allowed,
        transition_reason_code=transition.reason_code,
        semantic_digest=switch_digest,
    )

    return (
        P5Cz4DelegatedReplayContextV1(
            scope_init=scope_init,
            current_scope=current_scope,
            scope_event=scope_event,
            mapped_event=mapped_event,
            scope_event_ref=scope_event_ref,
            scope_chop_policy_active=bool(runtime_pre.chop_latched),
            runtime_scope_pre=runtime_pre,
            runtime_scope_after=runtime_after,
            next_side_state=next_side_state,
            transition=transition,
            state_switch=state_switch,
        ),
        (),
    )


__all__ = [
    "P5_CZ4_DELEGATION_OWNER",
    "P5_CZ4_DELEGATION_REASON",
    "P5Cz4DelegatedReplayContextV1",
    "try_build_p5_cz4_delegated_replay_context_v1",
]
