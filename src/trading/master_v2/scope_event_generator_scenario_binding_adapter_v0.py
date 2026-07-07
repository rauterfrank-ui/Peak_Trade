# src/trading/master_v2/scope_event_generator_scenario_binding_adapter_v0.py
"""
Scenario replay adapter: binds offline Double Play scenario ticks to the canonical
``deterministic_scope_event_generator_v1.generate_deterministic_scope_event`` owner
and derives ``scope_adverse_exit_signal`` for the entry-exit policy chain.

Wiring-only parity slice (Surface B) — no runtime authority, no trading semantic extension.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Tuple

from trading.master_v2.canonical_market_context_v1 import (
    BarFinalityStatus,
    ClockTrustStatus,
    DataIntegrityStatus,
)
from trading.master_v2.canonical_scope_initialization_v1 import (
    CanonicalScopeLifecycleState,
    CanonicalScopeSnapshotV1,
    SCOPE_INITIALIZATION_POLICY_VERSION,
    with_computed_semantic_digest,
)
from trading.master_v2.deterministic_scope_event_generator_v1 import (
    CanonicalScopeEventType,
    DETERMINISTIC_SCOPE_EVENT_GENERATOR_LAYER_VERSION,
    SCOPE_EVENT_GENERATOR_POLICY_VERSION,
    ScopeCandidateKind,
    ScopeConfirmationStateV1,
    ScopeCooldownStateV1,
    ScopeDirectionState,
    ScopeEventEvidenceV1,
    ScopeEventGeneratorInputV1,
    ScopeEventGeneratorPolicyV1,
    generate_deterministic_scope_event,
    with_computed_scope_event_digest,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import PolicySignalV0
from trading.master_v2.double_play_state import ActiveSide, DynamicScopeRules, RuntimeScopeState

SCOPE_EVENT_GENERATOR_SCENARIO_BINDING_ADAPTER_LAYER_VERSION = "v0"
SCOPE_EVENT_GENERATOR_SCENARIO_BINDING_ADAPTER_OWNER = (
    "trading.master_v2.scope_event_generator_scenario_binding_adapter_v0"
)
CANONICAL_SCOPE_EVENT_GENERATOR_OWNER = "trading.master_v2.deterministic_scope_event_generator_v1"

SCOPE_EVENT_EFFECT_BOUND_OFFLINE = "BOUND_OFFLINE"
SCOPE_EVENT_EFFECT_NONE = "NONE"

RUNTIME_AUTHORITY_EFFECT_NONE = "NONE"
ORDER_EFFECT_NONE = "NONE"

_DEFAULT_GENERATOR_POLICY = ScopeEventGeneratorPolicyV1(
    hard_max_scope_distance=1000.0,
    hard_max_adverse_distance=500.0,
    hard_max_reversal_distance=800.0,
    policy_version=SCOPE_EVENT_GENERATOR_POLICY_VERSION,
)
_DEFAULT_COOLDOWN = ScopeCooldownStateV1(
    active=False,
    remaining_epochs=0,
    policy_version=SCOPE_EVENT_GENERATOR_POLICY_VERSION,
)
_CONTEXT_DIGEST_PLACEHOLDER = "c" * 64


@dataclass(frozen=True)
class ScenarioScopeEventContextV0:
    """Explicit offline scenario scope-event context — never inferred from tick shortcuts."""

    instrument_id: str
    trading_epoch: int
    context_reference: str
    current_price: float
    scope_state: RuntimeScopeState
    rules: DynamicScopeRules
    active_side: ActiveSide
    confirmation_state: ScopeConfirmationStateV1
    safety_decision_allowed: bool = True
    data_integrity_status: DataIntegrityStatus | None = None
    clock_trust_status: ClockTrustStatus | None = None
    bar_finality_status: BarFinalityStatus | None = None
    scope_lifecycle_state: CanonicalScopeLifecycleState | None = None
    up_distance: float | None = None
    adverse_exit_distance: float | None = None
    reversal_distance: float | None = None
    confirmation_epochs: int = 2


@dataclass(frozen=True)
class ScenarioScopeEventBindingResultV0:
    scope_event_evidence: ScopeEventEvidenceV1
    scope_adverse_exit_signal: PolicySignalV0
    next_confirmation_state: ScopeConfirmationStateV1
    scope_event_ref: str
    scope_event_effect: str
    runtime_authority_effect: str = RUNTIME_AUTHORITY_EFFECT_NONE
    order_effect: str = ORDER_EFFECT_NONE


def active_side_to_scope_direction_v0(active: ActiveSide) -> ScopeDirectionState:
    if active is ActiveSide.SHORT:
        return ScopeDirectionState.SHORT
    return ScopeDirectionState.LONG


def _resolve_trust_gates_v0(
    ctx: ScenarioScopeEventContextV0,
) -> tuple[DataIntegrityStatus, ClockTrustStatus, BarFinalityStatus, CanonicalScopeLifecycleState]:
    if not ctx.safety_decision_allowed:
        return (
            DataIntegrityStatus.UNTRUSTED,
            ClockTrustStatus.UNTRUSTED,
            BarFinalityStatus.UNFINALIZED,
            CanonicalScopeLifecycleState.SCOPE_INVALID,
        )
    return (
        ctx.data_integrity_status or DataIntegrityStatus.TRUSTED,
        ctx.clock_trust_status or ClockTrustStatus.TRUSTED,
        ctx.bar_finality_status or BarFinalityStatus.FINALIZED,
        ctx.scope_lifecycle_state or CanonicalScopeLifecycleState.SCOPE_VALID,
    )


def _distance_triplet_from_scope_v0(
    *,
    scope_state: RuntimeScopeState,
    rules: DynamicScopeRules,
    up_distance: float | None,
    adverse_exit_distance: float | None,
    reversal_distance: float | None,
) -> tuple[float, float, float]:
    if (
        up_distance is not None
        and adverse_exit_distance is not None
        and reversal_distance is not None
    ):
        return float(up_distance), float(adverse_exit_distance), float(reversal_distance)
    band = max(
        float(scope_state.current_hysteresis_band),
        float(rules.min_band_width),
        1.0,
    )
    up = band
    adverse = band * 0.8
    reversal = band * 2.0
    return up, adverse, reversal


def build_scenario_canonical_scope_snapshot_v0(
    *,
    instrument_id: str,
    trading_epoch: int,
    scope_state: RuntimeScopeState,
    rules: DynamicScopeRules,
    mark_price: float,
    lifecycle_state: CanonicalScopeLifecycleState,
) -> CanonicalScopeSnapshotV1:
    anchor = float(scope_state.anchor_price) if scope_state.anchor_price > 0 else float(mark_price)
    band = max(float(scope_state.current_hysteresis_band), float(rules.min_band_width), 1.0)
    half = band / 2.0
    raw = CanonicalScopeSnapshotV1(
        scope_id=f"scope-{instrument_id}-epoch{trading_epoch}-scenario",
        instrument_id=instrument_id,
        initialized_at_trading_epoch=max(0, trading_epoch - 1),
        source_market_context_id=f"ctx-{instrument_id}-epoch{trading_epoch}",
        source_input_digest=_CONTEXT_DIGEST_PLACEHOLDER,
        lifecycle_state=lifecycle_state,
        reference_price=anchor,
        volatility_estimate=float(rules.volatility_estimate),
        initial_volatility_distance=band,
        scope_band=band,
        neutral_upper_boundary=anchor + half,
        neutral_lower_boundary=max(anchor - half, 0.01),
        trailing_anchor=anchor,
        min_scope_band=float(rules.min_band_width),
        max_scope_band=float(rules.max_band_width),
        policy_version=SCOPE_INITIALIZATION_POLICY_VERSION,
        semantic_digest="",
        reason_codes=(),
    )
    return with_computed_semantic_digest(raw)


def build_scenario_scope_generator_input_v0(
    ctx: ScenarioScopeEventContextV0,
    *,
    policy: ScopeEventGeneratorPolicyV1 | None = None,
) -> ScopeEventGeneratorInputV1:
    data_integrity, clock_trust, bar_finality, lifecycle = _resolve_trust_gates_v0(ctx)
    up_distance, adverse_exit_distance, reversal_distance = _distance_triplet_from_scope_v0(
        scope_state=ctx.scope_state,
        rules=ctx.rules,
        up_distance=ctx.up_distance,
        adverse_exit_distance=ctx.adverse_exit_distance,
        reversal_distance=ctx.reversal_distance,
    )
    scope_snapshot = build_scenario_canonical_scope_snapshot_v0(
        instrument_id=ctx.instrument_id,
        trading_epoch=ctx.trading_epoch,
        scope_state=ctx.scope_state,
        rules=ctx.rules,
        mark_price=ctx.current_price,
        lifecycle_state=lifecycle,
    )
    anchor = float(scope_snapshot.trailing_anchor)
    return ScopeEventGeneratorInputV1(
        instrument_id=ctx.instrument_id,
        trading_epoch=ctx.trading_epoch,
        market_context_id=f"ctx-{ctx.instrument_id}-epoch{ctx.trading_epoch}",
        market_context_digest=_CONTEXT_DIGEST_PLACEHOLDER,
        current_scope=scope_snapshot,
        current_direction_state=active_side_to_scope_direction_v0(ctx.active_side),
        reference_price=anchor,
        current_price=float(ctx.current_price),
        trailing_anchor=anchor,
        up_distance=up_distance,
        adverse_exit_distance=adverse_exit_distance,
        reversal_distance=reversal_distance,
        confirmation_epochs=int(ctx.confirmation_epochs),
        confirmation_state=ctx.confirmation_state,
        cooldown_state=_DEFAULT_COOLDOWN,
        cooldown_remaining_epochs=0,
        data_integrity_status=data_integrity,
        clock_trust_status=clock_trust,
        bar_finality_status=bar_finality,
        policy_version=(policy or _DEFAULT_GENERATOR_POLICY).policy_version,
    )


def derive_scope_adverse_exit_signal_v0(
    evidence: ScopeEventEvidenceV1,
) -> PolicySignalV0:
    """Adverse-exit signal from canonical generator evidence only — no legacy shortcuts."""
    if evidence.blocked_reasons:
        return PolicySignalV0(triggered=False, reason_code="scope_event_blocked")
    if evidence.event_type is CanonicalScopeEventType.ADVERSE_EXIT_CANDIDATE:
        return PolicySignalV0(triggered=True, reason_code="adverse_scope_exit_candidate")
    if ScopeCandidateKind.ADVERSE_EXIT.value in evidence.matched_conditions:
        return PolicySignalV0(triggered=True, reason_code="adverse_scope_exit_matched")
    return PolicySignalV0(triggered=False, reason_code="no_adverse_scope_exit")


def _derive_scope_event_ref(
    *,
    instrument_id: str,
    trading_epoch: int,
    scope_event_id: str,
) -> str:
    material = f"{instrument_id}|{trading_epoch}|{scope_event_id}"
    return f"scope-event-binding-{hashlib.sha256(material.encode('utf-8')).hexdigest()[:24]}"


def evaluate_scenario_scope_event_v0(
    ctx: ScenarioScopeEventContextV0,
    *,
    policy: ScopeEventGeneratorPolicyV1 | None = None,
) -> ScenarioScopeEventBindingResultV0:
    """Evaluate one scenario tick through canonical ``generate_deterministic_scope_event`` only."""
    generator_policy = policy or _DEFAULT_GENERATOR_POLICY
    generator_input = build_scenario_scope_generator_input_v0(ctx, policy=generator_policy)
    evidence = with_computed_scope_event_digest(
        generate_deterministic_scope_event(generator_input, generator_policy)
    )
    adverse_signal = derive_scope_adverse_exit_signal_v0(evidence)
    scope_event_ref = _derive_scope_event_ref(
        instrument_id=ctx.instrument_id,
        trading_epoch=ctx.trading_epoch,
        scope_event_id=evidence.scope_event_id,
    )
    return ScenarioScopeEventBindingResultV0(
        scope_event_evidence=evidence,
        scope_adverse_exit_signal=adverse_signal,
        next_confirmation_state=evidence.next_confirmation_state,
        scope_event_ref=scope_event_ref,
        scope_event_effect=SCOPE_EVENT_EFFECT_BOUND_OFFLINE,
    )


def scope_event_binding_non_authority_boundary_ok_v0(
    binding: ScenarioScopeEventBindingResultV0,
) -> bool:
    evidence = binding.scope_event_evidence
    if binding.runtime_authority_effect != RUNTIME_AUTHORITY_EFFECT_NONE:
        return False
    if binding.order_effect != ORDER_EFFECT_NONE:
        return False
    if evidence.authority_effect != RUNTIME_AUTHORITY_EFFECT_NONE:
        return False
    if evidence.runtime_effect != RUNTIME_AUTHORITY_EFFECT_NONE:
        return False
    if evidence.order_effect != ORDER_EFFECT_NONE:
        return False
    if binding.scope_event_effect not in {
        SCOPE_EVENT_EFFECT_NONE,
        SCOPE_EVENT_EFFECT_BOUND_OFFLINE,
    }:
        return False
    if (
        binding.scope_event_effect == SCOPE_EVENT_EFFECT_BOUND_OFFLINE
        and not binding.scope_event_ref
    ):
        return False
    return True


def system_economic_evidence_admissible_v0(
    binding: ScenarioScopeEventBindingResultV0,
) -> bool:
    return False


def scope_event_parity_adverse_signal_aligned_v0(
    *,
    integrated_triggered: bool,
    integrated_reason: str,
    scenario_binding: ScenarioScopeEventBindingResultV0,
) -> bool:
    scenario = scenario_binding.scope_adverse_exit_signal
    return integrated_triggered == scenario.triggered and integrated_reason == scenario.reason_code
