# src/trading/master_v2/deterministic_scope_event_generator_v1.py
"""
Pure Deterministic Scope Event Generator v1: data-only scope event evidence.

Consumes immutable canonical market context bindings, current scope snapshots,
confirmation/cooldown state, and explicit scope-event policy. Produces
fachliche scope-event evidence only — no runtime, authority, order, or position
effects.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Optional, Tuple

from trading.master_v2.canonical_market_context_v1 import (
    BarFinalityStatus,
    ClockTrustStatus,
    DataIntegrityStatus,
)
from trading.master_v2.canonical_scope_initialization_v1 import (
    CanonicalScopeLifecycleState,
    CanonicalScopeSnapshotV1,
)
from trading.master_v2.double_play_state import ActiveSide, ScopeEvent

DETERMINISTIC_SCOPE_EVENT_GENERATOR_LAYER_VERSION = "v1"
SCOPE_EVENT_GENERATOR_POLICY_VERSION = "deterministic_scope_event_generator_policy_v1"
CHOP_POLICY_STATUS = "NOT_BOUND"

_AUTHORITY_EFFECT_NONE = "NONE"
_RUNTIME_EFFECT_NONE = "NONE"
_ORDER_EFFECT_NONE = "NONE"
_POSITION_EFFECT_NONE = "NONE"


class ScopeDirectionState(str, Enum):
    LONG = "long"
    SHORT = "short"


class ScopeCandidateKind(str, Enum):
    UPSCOPE = "upscope"
    DOWNSCOPE = "downscope"
    ADVERSE_EXIT = "adverse_exit"


class CanonicalScopeEventType(str, Enum):
    """Canonical scope-event taxonomy; reuses ``ScopeEvent`` values where bound."""

    NOOP = ScopeEvent.NOOP.value
    UPSCOPE_CANDIDATE = ScopeEvent.UPSCOPE_CANDIDATE.value
    UPSCOPE_CONFIRMED = ScopeEvent.UPSCOPE_CONFIRMED.value
    DOWNSCOPE_CANDIDATE = ScopeEvent.DOWNSCOPE_CANDIDATE.value
    DOWNSCOPE_CONFIRMED = ScopeEvent.DOWNSCOPE_CONFIRMED.value
    CHOP_DETECTED = ScopeEvent.CHOP_DETECTED.value
    ADVERSE_EXIT_CANDIDATE = "adverse_exit_candidate"
    SCOPE_BLOCKED = "scope_blocked"


class ScopeEventBlockReason(str, Enum):
    POLICY_UP_DISTANCE_INVALID = "policy_up_distance_invalid"
    POLICY_ADVERSE_DISTANCE_INVALID = "policy_adverse_distance_invalid"
    POLICY_REVERSAL_DISTANCE_INVALID = "policy_reversal_distance_invalid"
    POLICY_ADVERSE_EXCEEDS_REVERSAL = "policy_adverse_exceeds_reversal"
    POLICY_HARD_MAX_SCOPE_EXCEEDED = "policy_hard_max_scope_exceeded"
    POLICY_HARD_MAX_ADVERSE_EXCEEDED = "policy_hard_max_adverse_exceeded"
    POLICY_HARD_MAX_REVERSAL_EXCEEDED = "policy_hard_max_reversal_exceeded"
    POLICY_CONFIRMATION_EPOCHS_INVALID = "policy_confirmation_epochs_invalid"
    POLICY_VERSION_INVALID = "policy_version_invalid"
    REFERENCE_PRICE_NON_POSITIVE = "reference_price_non_positive"
    CURRENT_PRICE_NON_POSITIVE = "current_price_non_positive"
    TRAILING_ANCHOR_NON_POSITIVE = "trailing_anchor_non_positive"
    BAR_UNFINALIZED = "bar_unfinalized"
    DATA_INTEGRITY_UNTRUSTED = "data_integrity_untrusted"
    DATA_INTEGRITY_UNKNOWN = "data_integrity_unknown"
    CLOCK_TRUST_UNTRUSTED = "clock_trust_untrusted"
    CLOCK_TRUST_UNKNOWN = "clock_trust_unknown"
    SCOPE_UNINITIALIZED = "scope_uninitialized"
    SCOPE_WARMING_UP = "scope_warming_up"
    SCOPE_STALE = "scope_stale"
    SCOPE_INVALID = "scope_invalid"
    TRADING_EPOCH_OUT_OF_ORDER = "trading_epoch_out_of_order"
    TRADING_EPOCH_SKIPPED = "trading_epoch_skipped"
    COOLDOWN_ACTIVE = "cooldown_active"
    INSTRUMENT_KIND_FORBIDDEN = "instrument_kind_forbidden"


@dataclass(frozen=True)
class ScopeEventGeneratorPolicyV1:
    hard_max_scope_distance: float
    hard_max_adverse_distance: float
    hard_max_reversal_distance: float
    policy_version: str = SCOPE_EVENT_GENERATOR_POLICY_VERSION


@dataclass(frozen=True)
class ScopeCooldownStateV1:
    active: bool
    remaining_epochs: int
    policy_version: str


@dataclass(frozen=True)
class ScopeConfirmationStateV1:
    candidate_kind: Optional[ScopeCandidateKind]
    candidate_count: int
    last_evaluated_trading_epoch: int


@dataclass(frozen=True)
class ScopeEventGeneratorInputV1:
    instrument_id: str
    trading_epoch: int
    market_context_id: str
    market_context_digest: str
    current_scope: CanonicalScopeSnapshotV1
    current_direction_state: ScopeDirectionState
    reference_price: float
    current_price: float
    trailing_anchor: float
    up_distance: float
    adverse_exit_distance: float
    reversal_distance: float
    confirmation_epochs: int
    confirmation_state: ScopeConfirmationStateV1
    cooldown_state: ScopeCooldownStateV1
    cooldown_remaining_epochs: int
    data_integrity_status: DataIntegrityStatus
    clock_trust_status: ClockTrustStatus
    bar_finality_status: BarFinalityStatus
    policy_version: str


@dataclass(frozen=True)
class EvaluatedThresholdsV1:
    up_candidate_threshold: float
    downscope_candidate_threshold: float
    adverse_exit_threshold: float
    reversal_candidate_threshold: float


@dataclass(frozen=True)
class ScopeEventSemanticBindingV1:
    market_context_digest: str
    current_direction_state: ScopeDirectionState
    current_price: float
    trailing_anchor: float
    up_distance: float
    adverse_exit_distance: float
    reversal_distance: float
    confirmation_epochs: int
    cooldown_active: bool
    cooldown_remaining_epochs: int
    generator_policy_version: str


@dataclass(frozen=True)
class ScopeEventEvidenceV1:
    scope_event_id: str
    instrument_id: str
    trading_epoch: int
    event_type: CanonicalScopeEventType
    previous_confirmation_state: ScopeConfirmationStateV1
    next_confirmation_state: ScopeConfirmationStateV1
    candidate_count_before: int
    candidate_count_after: int
    evaluated_thresholds: EvaluatedThresholdsV1
    matched_conditions: Tuple[str, ...]
    blocked_reasons: Tuple[str, ...]
    current_scope_ref: CanonicalScopeSnapshotV1
    next_scope_effective_epoch: Optional[int]
    semantic_binding: ScopeEventSemanticBindingV1
    semantic_digest: str
    authority_effect: str = _AUTHORITY_EFFECT_NONE
    runtime_effect: str = _RUNTIME_EFFECT_NONE
    order_effect: str = _ORDER_EFFECT_NONE
    position_effect: str = _POSITION_EFFECT_NONE

    def __post_init__(self) -> None:
        if self.semantic_digest and not _valid_sha256_hex(self.semantic_digest):
            msg = "semantic_digest must be empty or a 64-char lowercase sha256 hex"
            raise ValueError(msg)


_FORBIDDEN_INSTRUMENT_SUBSTRINGS = frozenset({"btc", "xbt", "bitcoin", "spot", "synthetic_spot"})


def _valid_sha256_hex(value: str) -> bool:
    return bool(re.fullmatch(r"[0-9a-f]{64}", value))


def _positive_finite(value: object) -> bool:
    return isinstance(value, (int, float)) and float(value) > 0.0


def _positive_int(value: object) -> bool:
    return isinstance(value, int) and value > 0


def _instrument_id_allowed(instrument_id: str) -> bool:
    lowered = instrument_id.lower()
    return not any(token in lowered for token in _FORBIDDEN_INSTRUMENT_SUBSTRINGS)


def _sorted_reason_values(reasons: Tuple[ScopeEventBlockReason, ...]) -> Tuple[str, ...]:
    return tuple(sorted(r.value for r in reasons))


def validate_scope_event_generator_policy(
    policy: ScopeEventGeneratorPolicyV1,
    *,
    up_distance: float,
    adverse_exit_distance: float,
    reversal_distance: float,
    confirmation_epochs: int,
    policy_version: str,
) -> Tuple[ScopeEventBlockReason, ...]:
    blocks: list[ScopeEventBlockReason] = []
    if not _positive_finite(policy.hard_max_scope_distance):
        blocks.append(ScopeEventBlockReason.POLICY_HARD_MAX_SCOPE_EXCEEDED)
    if not _positive_finite(policy.hard_max_adverse_distance):
        blocks.append(ScopeEventBlockReason.POLICY_HARD_MAX_ADVERSE_EXCEEDED)
    if not _positive_finite(policy.hard_max_reversal_distance):
        blocks.append(ScopeEventBlockReason.POLICY_HARD_MAX_REVERSAL_EXCEEDED)
    if not policy.policy_version or policy.policy_version != SCOPE_EVENT_GENERATOR_POLICY_VERSION:
        blocks.append(ScopeEventBlockReason.POLICY_VERSION_INVALID)
    if policy_version != SCOPE_EVENT_GENERATOR_POLICY_VERSION:
        blocks.append(ScopeEventBlockReason.POLICY_VERSION_INVALID)
    if not _positive_finite(up_distance):
        blocks.append(ScopeEventBlockReason.POLICY_UP_DISTANCE_INVALID)
    elif up_distance > policy.hard_max_scope_distance:
        blocks.append(ScopeEventBlockReason.POLICY_HARD_MAX_SCOPE_EXCEEDED)
    if not _positive_finite(adverse_exit_distance):
        blocks.append(ScopeEventBlockReason.POLICY_ADVERSE_DISTANCE_INVALID)
    elif adverse_exit_distance > policy.hard_max_adverse_distance:
        blocks.append(ScopeEventBlockReason.POLICY_HARD_MAX_ADVERSE_EXCEEDED)
    if not _positive_finite(reversal_distance):
        blocks.append(ScopeEventBlockReason.POLICY_REVERSAL_DISTANCE_INVALID)
    elif reversal_distance > policy.hard_max_reversal_distance:
        blocks.append(ScopeEventBlockReason.POLICY_HARD_MAX_REVERSAL_EXCEEDED)
    if adverse_exit_distance > reversal_distance:
        blocks.append(ScopeEventBlockReason.POLICY_ADVERSE_EXCEEDS_REVERSAL)
    if not _positive_int(confirmation_epochs):
        blocks.append(ScopeEventBlockReason.POLICY_CONFIRMATION_EPOCHS_INVALID)
    return tuple(dict.fromkeys(blocks))


def _collect_input_gate_blocks(
    inp: ScopeEventGeneratorInputV1,
) -> Tuple[ScopeEventBlockReason, ...]:
    blocks: list[ScopeEventBlockReason] = []
    if not _instrument_id_allowed(inp.instrument_id):
        blocks.append(ScopeEventBlockReason.INSTRUMENT_KIND_FORBIDDEN)
    if not _positive_finite(inp.reference_price):
        blocks.append(ScopeEventBlockReason.REFERENCE_PRICE_NON_POSITIVE)
    if not _positive_finite(inp.current_price):
        blocks.append(ScopeEventBlockReason.CURRENT_PRICE_NON_POSITIVE)
    if not _positive_finite(inp.trailing_anchor):
        blocks.append(ScopeEventBlockReason.TRAILING_ANCHOR_NON_POSITIVE)
    if inp.bar_finality_status is not BarFinalityStatus.FINALIZED:
        blocks.append(ScopeEventBlockReason.BAR_UNFINALIZED)
    if inp.data_integrity_status in (DataIntegrityStatus.UNTRUSTED, DataIntegrityStatus.INVALID):
        blocks.append(ScopeEventBlockReason.DATA_INTEGRITY_UNTRUSTED)
    elif inp.data_integrity_status is DataIntegrityStatus.UNKNOWN:
        blocks.append(ScopeEventBlockReason.DATA_INTEGRITY_UNKNOWN)
    if inp.clock_trust_status in (ClockTrustStatus.UNTRUSTED, ClockTrustStatus.INVALID):
        blocks.append(ScopeEventBlockReason.CLOCK_TRUST_UNTRUSTED)
    elif inp.clock_trust_status is ClockTrustStatus.UNKNOWN:
        blocks.append(ScopeEventBlockReason.CLOCK_TRUST_UNKNOWN)
    lifecycle = inp.current_scope.lifecycle_state
    if lifecycle is CanonicalScopeLifecycleState.SCOPE_UNINITIALIZED:
        blocks.append(ScopeEventBlockReason.SCOPE_UNINITIALIZED)
    elif lifecycle is CanonicalScopeLifecycleState.SCOPE_WARMING_UP:
        blocks.append(ScopeEventBlockReason.SCOPE_WARMING_UP)
    elif lifecycle is CanonicalScopeLifecycleState.SCOPE_STALE:
        blocks.append(ScopeEventBlockReason.SCOPE_STALE)
    elif lifecycle is CanonicalScopeLifecycleState.SCOPE_INVALID:
        blocks.append(ScopeEventBlockReason.SCOPE_INVALID)
    return tuple(dict.fromkeys(blocks))


def active_side_from_direction(direction: ScopeDirectionState) -> ActiveSide:
    if direction is ScopeDirectionState.LONG:
        return ActiveSide.LONG
    return ActiveSide.SHORT


def compute_evaluated_thresholds(
    *,
    direction: ScopeDirectionState,
    trailing_anchor: float,
    up_distance: float,
    adverse_exit_distance: float,
    reversal_distance: float,
) -> EvaluatedThresholdsV1:
    anchor = float(trailing_anchor)
    up = float(up_distance)
    adverse = float(adverse_exit_distance)
    reversal = float(reversal_distance)
    if direction is ScopeDirectionState.LONG:
        return EvaluatedThresholdsV1(
            up_candidate_threshold=anchor + up,
            downscope_candidate_threshold=anchor - up,
            adverse_exit_threshold=anchor - adverse,
            reversal_candidate_threshold=anchor - reversal,
        )
    return EvaluatedThresholdsV1(
        up_candidate_threshold=anchor - up,
        downscope_candidate_threshold=anchor + up,
        adverse_exit_threshold=anchor + adverse,
        reversal_candidate_threshold=anchor + reversal,
    )


def mirror_price_for_short(price: float, reference: float) -> float:
    """Structural mirror: reflect price around reference for long/short symmetry tests."""
    return (2.0 * reference) - price


def _matched_directional_conditions(
    *,
    direction: ScopeDirectionState,
    current_price: float,
    thresholds: EvaluatedThresholdsV1,
) -> Tuple[ScopeCandidateKind, ...]:
    price = float(current_price)
    matched: list[ScopeCandidateKind] = []
    if direction is ScopeDirectionState.LONG:
        if price >= thresholds.up_candidate_threshold:
            matched.append(ScopeCandidateKind.UPSCOPE)
        if price <= thresholds.downscope_candidate_threshold:
            matched.append(ScopeCandidateKind.DOWNSCOPE)
        if price <= thresholds.adverse_exit_threshold:
            matched.append(ScopeCandidateKind.ADVERSE_EXIT)
    else:
        if price <= thresholds.up_candidate_threshold:
            matched.append(ScopeCandidateKind.UPSCOPE)
        if price >= thresholds.downscope_candidate_threshold:
            matched.append(ScopeCandidateKind.DOWNSCOPE)
        if price >= thresholds.adverse_exit_threshold:
            matched.append(ScopeCandidateKind.ADVERSE_EXIT)
    return tuple(matched)


def _candidate_kind_to_matched_condition(kind: ScopeCandidateKind) -> str:
    return kind.value


def _resolve_epoch_semantics(
    *,
    trading_epoch: int,
    last_evaluated_trading_epoch: int,
) -> Tuple[str, Optional[ScopeEventBlockReason]]:
    if last_evaluated_trading_epoch < 0:
        return "first", None
    if trading_epoch == last_evaluated_trading_epoch:
        return "duplicate", None
    if trading_epoch == last_evaluated_trading_epoch + 1:
        return "consecutive", None
    if trading_epoch < last_evaluated_trading_epoch:
        return "out_of_order", ScopeEventBlockReason.TRADING_EPOCH_OUT_OF_ORDER
    return "skipped", None


def _reset_confirmation_state(last_epoch: int) -> ScopeConfirmationStateV1:
    return ScopeConfirmationStateV1(
        candidate_kind=None,
        candidate_count=0,
        last_evaluated_trading_epoch=last_epoch,
    )


def _advance_confirmation_state(
    *,
    previous: ScopeConfirmationStateV1,
    trading_epoch: int,
    selected_kind: Optional[ScopeCandidateKind],
    confirmation_epochs: int,
    epoch_mode: str,
) -> ScopeConfirmationStateV1:
    if epoch_mode == "out_of_order":
        return _reset_confirmation_state(trading_epoch)
    if epoch_mode == "duplicate":
        return previous
    if selected_kind is None:
        return ScopeConfirmationStateV1(
            candidate_kind=None,
            candidate_count=0,
            last_evaluated_trading_epoch=trading_epoch,
        )
    if epoch_mode == "skipped":
        return ScopeConfirmationStateV1(
            candidate_kind=selected_kind,
            candidate_count=1,
            last_evaluated_trading_epoch=trading_epoch,
        )
    if previous.candidate_kind != selected_kind:
        return ScopeConfirmationStateV1(
            candidate_kind=selected_kind,
            candidate_count=1,
            last_evaluated_trading_epoch=trading_epoch,
        )
    next_count = previous.candidate_count + 1 if epoch_mode == "consecutive" else 1
    return ScopeConfirmationStateV1(
        candidate_kind=selected_kind,
        candidate_count=next_count,
        last_evaluated_trading_epoch=trading_epoch,
    )


def _event_type_for_kind(
    kind: ScopeCandidateKind,
    *,
    confirmed: bool,
) -> CanonicalScopeEventType:
    if kind is ScopeCandidateKind.ADVERSE_EXIT:
        return CanonicalScopeEventType.ADVERSE_EXIT_CANDIDATE
    if kind is ScopeCandidateKind.UPSCOPE:
        return (
            CanonicalScopeEventType.UPSCOPE_CONFIRMED
            if confirmed
            else CanonicalScopeEventType.UPSCOPE_CANDIDATE
        )
    return (
        CanonicalScopeEventType.DOWNSCOPE_CONFIRMED
        if confirmed
        else CanonicalScopeEventType.DOWNSCOPE_CANDIDATE
    )


def _select_directional_kind(
    matched: Tuple[ScopeCandidateKind, ...],
) -> Optional[ScopeCandidateKind]:
    if ScopeCandidateKind.ADVERSE_EXIT in matched:
        return ScopeCandidateKind.ADVERSE_EXIT
    if ScopeCandidateKind.DOWNSCOPE in matched and ScopeCandidateKind.UPSCOPE in matched:
        return None
    if ScopeCandidateKind.DOWNSCOPE in matched:
        return ScopeCandidateKind.DOWNSCOPE
    if ScopeCandidateKind.UPSCOPE in matched:
        return ScopeCandidateKind.UPSCOPE
    return None


def _derive_scope_event_id(instrument_id: str, trading_epoch: int, event_type: str) -> str:
    return f"scope-event-{instrument_id}-epoch{trading_epoch}-{event_type}"


def _semantic_binding_from_input(
    inp: ScopeEventGeneratorInputV1,
    policy: ScopeEventGeneratorPolicyV1,
) -> ScopeEventSemanticBindingV1:
    return ScopeEventSemanticBindingV1(
        market_context_digest=inp.market_context_digest,
        current_direction_state=inp.current_direction_state,
        current_price=float(inp.current_price),
        trailing_anchor=float(inp.trailing_anchor),
        up_distance=float(inp.up_distance),
        adverse_exit_distance=float(inp.adverse_exit_distance),
        reversal_distance=float(inp.reversal_distance),
        confirmation_epochs=int(inp.confirmation_epochs),
        cooldown_active=bool(inp.cooldown_state.active),
        cooldown_remaining_epochs=int(inp.cooldown_remaining_epochs),
        generator_policy_version=policy.policy_version,
    )


def serialize_scope_event_evidence_canonical(evidence: ScopeEventEvidenceV1) -> str:
    binding = evidence.semantic_binding
    payload = {
        "adverse_exit_distance": binding.adverse_exit_distance,
        "authority_effect": evidence.authority_effect,
        "blocked_reasons": sorted(evidence.blocked_reasons),
        "candidate_count_after": evidence.candidate_count_after,
        "candidate_count_before": evidence.candidate_count_before,
        "confirmation_epochs": binding.confirmation_epochs,
        "cooldown_active": binding.cooldown_active,
        "cooldown_remaining_epochs": binding.cooldown_remaining_epochs,
        "current_direction_state": binding.current_direction_state.value,
        "current_price": binding.current_price,
        "current_scope_digest": evidence.current_scope_ref.semantic_digest,
        "current_scope_id": evidence.current_scope_ref.scope_id,
        "current_scope_lifecycle": evidence.current_scope_ref.lifecycle_state.value,
        "evaluated_thresholds": {
            "adverse_exit_threshold": evidence.evaluated_thresholds.adverse_exit_threshold,
            "downscope_candidate_threshold": evidence.evaluated_thresholds.downscope_candidate_threshold,
            "reversal_candidate_threshold": evidence.evaluated_thresholds.reversal_candidate_threshold,
            "up_candidate_threshold": evidence.evaluated_thresholds.up_candidate_threshold,
        },
        "event_type": evidence.event_type.value,
        "generator_policy_version": binding.generator_policy_version,
        "instrument_id": evidence.instrument_id,
        "layer_version": DETERMINISTIC_SCOPE_EVENT_GENERATOR_LAYER_VERSION,
        "market_context_digest": binding.market_context_digest,
        "matched_conditions": sorted(evidence.matched_conditions),
        "next_confirmation_state": {
            "candidate_count": evidence.next_confirmation_state.candidate_count,
            "candidate_kind": (
                evidence.next_confirmation_state.candidate_kind.value
                if evidence.next_confirmation_state.candidate_kind
                else None
            ),
            "last_evaluated_trading_epoch": evidence.next_confirmation_state.last_evaluated_trading_epoch,
        },
        "next_scope_effective_epoch": evidence.next_scope_effective_epoch,
        "order_effect": evidence.order_effect,
        "policy_version": evidence.current_scope_ref.policy_version,
        "position_effect": evidence.position_effect,
        "previous_confirmation_state": {
            "candidate_count": evidence.previous_confirmation_state.candidate_count,
            "candidate_kind": (
                evidence.previous_confirmation_state.candidate_kind.value
                if evidence.previous_confirmation_state.candidate_kind
                else None
            ),
            "last_evaluated_trading_epoch": evidence.previous_confirmation_state.last_evaluated_trading_epoch,
        },
        "reversal_distance": binding.reversal_distance,
        "runtime_effect": evidence.runtime_effect,
        "scope_event_id": evidence.scope_event_id,
        "trading_epoch": evidence.trading_epoch,
        "trailing_anchor": binding.trailing_anchor,
        "up_distance": binding.up_distance,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_scope_event_semantic_digest(evidence: ScopeEventEvidenceV1) -> str:
    canonical = serialize_scope_event_evidence_canonical(evidence)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def with_computed_scope_event_digest(evidence: ScopeEventEvidenceV1) -> ScopeEventEvidenceV1:
    digest = compute_scope_event_semantic_digest(evidence)
    return ScopeEventEvidenceV1(
        scope_event_id=evidence.scope_event_id,
        instrument_id=evidence.instrument_id,
        trading_epoch=evidence.trading_epoch,
        event_type=evidence.event_type,
        previous_confirmation_state=evidence.previous_confirmation_state,
        next_confirmation_state=evidence.next_confirmation_state,
        candidate_count_before=evidence.candidate_count_before,
        candidate_count_after=evidence.candidate_count_after,
        evaluated_thresholds=evidence.evaluated_thresholds,
        matched_conditions=evidence.matched_conditions,
        blocked_reasons=evidence.blocked_reasons,
        current_scope_ref=evidence.current_scope_ref,
        next_scope_effective_epoch=evidence.next_scope_effective_epoch,
        semantic_binding=evidence.semantic_binding,
        semantic_digest=digest,
    )


def _finalize_evidence(
    inp: ScopeEventGeneratorInputV1,
    policy: ScopeEventGeneratorPolicyV1,
    *,
    scope_event_id: str,
    event_type: CanonicalScopeEventType,
    previous_confirmation_state: ScopeConfirmationStateV1,
    next_confirmation_state: ScopeConfirmationStateV1,
    candidate_count_before: int,
    candidate_count_after: int,
    thresholds: EvaluatedThresholdsV1,
    matched_conditions: Tuple[str, ...],
    blocked_reasons: Tuple[str, ...],
    next_scope_effective_epoch: Optional[int],
) -> ScopeEventEvidenceV1:
    evidence = ScopeEventEvidenceV1(
        scope_event_id=scope_event_id,
        instrument_id=inp.instrument_id,
        trading_epoch=inp.trading_epoch,
        event_type=event_type,
        previous_confirmation_state=previous_confirmation_state,
        next_confirmation_state=next_confirmation_state,
        candidate_count_before=candidate_count_before,
        candidate_count_after=candidate_count_after,
        evaluated_thresholds=thresholds,
        matched_conditions=matched_conditions,
        blocked_reasons=blocked_reasons,
        current_scope_ref=inp.current_scope,
        next_scope_effective_epoch=next_scope_effective_epoch,
        semantic_binding=_semantic_binding_from_input(inp, policy),
        semantic_digest="",
    )
    return with_computed_scope_event_digest(evidence)


def _build_blocked_evidence(
    inp: ScopeEventGeneratorInputV1,
    policy: ScopeEventGeneratorPolicyV1,
    *,
    thresholds: EvaluatedThresholdsV1,
    blocked_reasons: Tuple[ScopeEventBlockReason, ...],
    matched_conditions: Tuple[str, ...] = (),
    previous_state: Optional[ScopeConfirmationStateV1] = None,
) -> ScopeEventEvidenceV1:
    prev = previous_state or inp.confirmation_state
    next_state = _reset_confirmation_state(inp.trading_epoch)
    reasons = _sorted_reason_values(blocked_reasons)
    return _finalize_evidence(
        inp,
        policy,
        scope_event_id=_derive_scope_event_id(
            inp.instrument_id,
            inp.trading_epoch,
            CanonicalScopeEventType.SCOPE_BLOCKED.value,
        ),
        event_type=CanonicalScopeEventType.SCOPE_BLOCKED,
        previous_confirmation_state=prev,
        next_confirmation_state=next_state,
        candidate_count_before=prev.candidate_count,
        candidate_count_after=0,
        thresholds=thresholds,
        matched_conditions=matched_conditions,
        blocked_reasons=reasons,
        next_scope_effective_epoch=None,
    )


def generate_deterministic_scope_event(
    inp: ScopeEventGeneratorInputV1,
    policy: ScopeEventGeneratorPolicyV1,
) -> ScopeEventEvidenceV1:
    """
    Deterministic scope-event evidence generator.

    Fail-closed on untrusted/unfinalized inputs, invalid lifecycle, invalid policy,
    epoch ordering violations, and active cooldown (for new confirmations).
    Never mutates ``inp.current_scope`` in place.
    """
    thresholds = compute_evaluated_thresholds(
        direction=inp.current_direction_state,
        trailing_anchor=inp.trailing_anchor,
        up_distance=inp.up_distance,
        adverse_exit_distance=inp.adverse_exit_distance,
        reversal_distance=inp.reversal_distance,
    )

    policy_blocks = validate_scope_event_generator_policy(
        policy,
        up_distance=inp.up_distance,
        adverse_exit_distance=inp.adverse_exit_distance,
        reversal_distance=inp.reversal_distance,
        confirmation_epochs=inp.confirmation_epochs,
        policy_version=inp.policy_version,
    )
    if policy_blocks:
        return _build_blocked_evidence(
            inp, policy, thresholds=thresholds, blocked_reasons=policy_blocks
        )

    gate_blocks = _collect_input_gate_blocks(inp)
    if gate_blocks:
        return _build_blocked_evidence(
            inp, policy, thresholds=thresholds, blocked_reasons=gate_blocks
        )

    epoch_mode, epoch_block = _resolve_epoch_semantics(
        trading_epoch=inp.trading_epoch,
        last_evaluated_trading_epoch=inp.confirmation_state.last_evaluated_trading_epoch,
    )
    if epoch_block is not None:
        return _build_blocked_evidence(
            inp,
            policy,
            thresholds=thresholds,
            blocked_reasons=(epoch_block,),
        )

    if epoch_mode == "duplicate":
        prior = inp.confirmation_state
        matched = _matched_directional_conditions(
            direction=inp.current_direction_state,
            current_price=inp.current_price,
            thresholds=thresholds,
        )
        selected = _select_directional_kind(matched)
        confirmed = (
            selected is not None
            and prior.candidate_kind == selected
            and prior.candidate_count >= inp.confirmation_epochs
            and selected is not ScopeCandidateKind.ADVERSE_EXIT
        )
        event_type = (
            _event_type_for_kind(selected, confirmed=confirmed)
            if selected is not None
            else CanonicalScopeEventType.NOOP
        )
        next_epoch = inp.trading_epoch + 1 if confirmed else None
        return _finalize_evidence(
            inp,
            policy,
            scope_event_id=_derive_scope_event_id(
                inp.instrument_id, inp.trading_epoch, event_type.value
            ),
            event_type=event_type,
            previous_confirmation_state=prior,
            next_confirmation_state=prior,
            candidate_count_before=prior.candidate_count,
            candidate_count_after=prior.candidate_count,
            thresholds=thresholds,
            matched_conditions=tuple(_candidate_kind_to_matched_condition(k) for k in matched),
            blocked_reasons=(),
            next_scope_effective_epoch=next_epoch,
        )

    matched = _matched_directional_conditions(
        direction=inp.current_direction_state,
        current_price=inp.current_price,
        thresholds=thresholds,
    )
    matched_conditions = tuple(_candidate_kind_to_matched_condition(k) for k in matched)
    selected_kind = _select_directional_kind(matched)

    prev_state = inp.confirmation_state
    if epoch_mode == "skipped":
        prev_state = ScopeConfirmationStateV1(
            candidate_kind=None,
            candidate_count=0,
            last_evaluated_trading_epoch=inp.confirmation_state.last_evaluated_trading_epoch,
        )

    cooldown_blocks: Tuple[ScopeEventBlockReason, ...] = ()
    if inp.cooldown_state.active and inp.cooldown_remaining_epochs > 0:
        cooldown_blocks = (ScopeEventBlockReason.COOLDOWN_ACTIVE,)

    if cooldown_blocks and selected_kind not in (ScopeCandidateKind.ADVERSE_EXIT, None):
        return _build_blocked_evidence(
            inp,
            policy,
            thresholds=thresholds,
            blocked_reasons=cooldown_blocks,
            matched_conditions=matched_conditions,
            previous_state=prev_state,
        )

    next_state = _advance_confirmation_state(
        previous=prev_state,
        trading_epoch=inp.trading_epoch,
        selected_kind=selected_kind,
        confirmation_epochs=inp.confirmation_epochs,
        epoch_mode=epoch_mode,
    )

    if selected_kind is ScopeCandidateKind.ADVERSE_EXIT:
        event_type = CanonicalScopeEventType.ADVERSE_EXIT_CANDIDATE
        next_scope_epoch = None
    elif selected_kind is None:
        event_type = CanonicalScopeEventType.NOOP
        next_scope_epoch = None
    else:
        confirmed = next_state.candidate_count >= inp.confirmation_epochs
        if cooldown_blocks and confirmed:
            return _build_blocked_evidence(
                inp,
                policy,
                thresholds=thresholds,
                blocked_reasons=cooldown_blocks,
                matched_conditions=matched_conditions,
                previous_state=prev_state,
            )
        event_type = _event_type_for_kind(selected_kind, confirmed=confirmed)
        next_scope_epoch = inp.trading_epoch + 1 if confirmed else None

    return _finalize_evidence(
        inp,
        policy,
        scope_event_id=_derive_scope_event_id(
            inp.instrument_id, inp.trading_epoch, event_type.value
        ),
        event_type=event_type,
        previous_confirmation_state=prev_state,
        next_confirmation_state=next_state,
        candidate_count_before=prev_state.candidate_count,
        candidate_count_after=next_state.candidate_count,
        thresholds=thresholds,
        matched_conditions=matched_conditions,
        blocked_reasons=_sorted_reason_values(cooldown_blocks),
        next_scope_effective_epoch=next_scope_epoch,
    )
