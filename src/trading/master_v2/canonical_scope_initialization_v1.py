# src/trading/master_v2/canonical_scope_initialization_v1.py
"""
Pure Canonical Scope Initialization v1: data-only scope lifecycle and initialization.

Bound to ``canonical_market_context_v1`` and Master V2 dynamic-scope conventions.
No I/O, runtime, adapter, order, scope-event generation, or execution authority.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

from trading.master_v2.canonical_market_context_v1 import (
    BarFinalityStatus,
    CanonicalMarketContextV1,
    ClockTrustStatus,
    DataIntegrityStatus,
    WarmupStatus,
    canonical_market_type_allowed,
    validate_canonical_market_context_fields,
    with_computed_input_digest,
)

CANONICAL_SCOPE_INITIALIZATION_LAYER_VERSION = "v1"
SCOPE_INITIALIZATION_POLICY_VERSION = "canonical_scope_initialization_policy_v1"
_RECONCILED_STATUS = "RECONCILED"


class CanonicalScopeLifecycleState(str, Enum):
    SCOPE_UNINITIALIZED = "scope_uninitialized"
    SCOPE_WARMING_UP = "scope_warming_up"
    SCOPE_VALID = "scope_valid"
    SCOPE_STALE = "scope_stale"
    SCOPE_INVALID = "scope_invalid"


class CanonicalScopeBlockReason(str, Enum):
    SCOPE_ALREADY_INITIALIZED = "scope_already_initialized"
    REINITIALIZATION_OPEN_POSITION = "reinitialization_open_position"
    REINITIALIZATION_UNKNOWN_POSITION = "reinitialization_unknown_position"
    REINITIALIZATION_UNRESOLVED_INCREASE_ORDER = "reinitialization_unresolved_increase_order"
    REINITIALIZATION_UNRESOLVED_REDUCE_ORDER = "reinitialization_unresolved_reduce_order"
    REINITIALIZATION_SUBMISSION_UNKNOWN = "reinitialization_submission_unknown"
    REINITIALIZATION_NOT_RECONCILED = "reinitialization_not_reconciled"
    WARMUP_INCOMPLETE = "warmup_incomplete"
    WARMUP_INVALID = "warmup_invalid"
    BAR_UNFINALIZED = "bar_unfinalized"
    DATA_INTEGRITY_UNTRUSTED = "data_integrity_untrusted"
    DATA_INTEGRITY_UNKNOWN = "data_integrity_unknown"
    CLOCK_TRUST_UNTRUSTED = "clock_trust_untrusted"
    CLOCK_TRUST_UNKNOWN = "clock_trust_unknown"
    REQUIRED_WINDOW_INCOMPLETE = "required_window_incomplete"
    INSTRUMENT_METADATA_INVALID = "instrument_metadata_invalid"
    MARKET_CONTEXT_NOT_FINALIZED = "market_context_not_finalized"
    MARKET_CONTEXT_FIELD_INVALID = "market_context_field_invalid"
    INSTRUMENT_KIND_FORBIDDEN = "instrument_kind_forbidden"
    MARK_PRICE_NON_POSITIVE = "mark_price_non_positive"
    VOLATILITY_NEGATIVE = "volatility_negative"
    MIN_SCOPE_BAND_NON_POSITIVE = "min_scope_band_non_positive"
    MAX_SCOPE_BAND_LT_MIN = "max_scope_band_lt_min"
    SCOPE_CONTEXT_STALE = "scope_context_stale"


@dataclass(frozen=True)
class CanonicalScopeInitializationPolicyV1:
    """Explicit scope-band policy; no implicit defaults for safety-relevant bounds."""

    min_scope_band: float
    max_scope_band: float
    policy_version: str = SCOPE_INITIALIZATION_POLICY_VERSION


@dataclass(frozen=True)
class ScopeInitializationPrerequisitesV1:
    """Explicit offline prerequisites; caller must supply all gates."""

    required_window_complete: bool
    instrument_metadata_valid: bool
    finalized_market_context: bool


@dataclass(frozen=True)
class ScopeReinitializationGuardV1:
    """Offline reinitialization guard; no runtime access in this slice."""

    has_open_position: bool = False
    has_unknown_position: bool = False
    has_unresolved_increase_order: bool = False
    has_unresolved_reduce_order: bool = False
    has_submission_unknown: bool = False
    reconciliation_status: str = _RECONCILED_STATUS


@dataclass(frozen=True)
class CanonicalScopeSnapshotV1:
    scope_id: str
    instrument_id: str
    initialized_at_trading_epoch: int
    source_market_context_id: str
    source_input_digest: str
    lifecycle_state: CanonicalScopeLifecycleState
    reference_price: float
    volatility_estimate: float
    initial_volatility_distance: float
    scope_band: float
    neutral_upper_boundary: float
    neutral_lower_boundary: float
    trailing_anchor: float
    min_scope_band: float
    max_scope_band: float
    policy_version: str
    semantic_digest: str
    reason_codes: Tuple[str, ...]

    def __post_init__(self) -> None:
        if self.semantic_digest and not _valid_sha256_hex(self.semantic_digest):
            msg = "semantic_digest must be empty or a 64-char lowercase sha256 hex"
            raise ValueError(msg)


@dataclass(frozen=True)
class CanonicalScopeInitializationResultV1:
    scope: Optional[CanonicalScopeSnapshotV1]
    lifecycle_state: CanonicalScopeLifecycleState
    block_reasons: Tuple[CanonicalScopeBlockReason, ...]
    scope_event_generated: bool = False
    is_authority: bool = False
    is_signal: bool = False
    execution_eligible: bool = False
    live_authorization: bool = False
    order_effect: bool = False
    runtime_effect: bool = False


def _valid_sha256_hex(value: str) -> bool:
    return bool(re.fullmatch(r"[0-9a-f]{64}", value))


def _positive_finite(value: object) -> bool:
    return isinstance(value, (int, float)) and float(value) > 0.0


def _non_negative_finite(value: object) -> bool:
    return isinstance(value, (int, float)) and float(value) >= 0.0


def validate_scope_initialization_policy(
    policy: CanonicalScopeInitializationPolicyV1,
) -> Tuple[CanonicalScopeBlockReason, ...]:
    blocks: list[CanonicalScopeBlockReason] = []
    if not _positive_finite(policy.min_scope_band):
        blocks.append(CanonicalScopeBlockReason.MIN_SCOPE_BAND_NON_POSITIVE)
    if not _positive_finite(policy.max_scope_band):
        blocks.append(CanonicalScopeBlockReason.MAX_SCOPE_BAND_LT_MIN)
    elif (
        CanonicalScopeBlockReason.MIN_SCOPE_BAND_NON_POSITIVE not in blocks
        and policy.max_scope_band < policy.min_scope_band
    ):
        blocks.append(CanonicalScopeBlockReason.MAX_SCOPE_BAND_LT_MIN)
    if not policy.policy_version or policy.policy_version != SCOPE_INITIALIZATION_POLICY_VERSION:
        blocks.append(CanonicalScopeBlockReason.MARKET_CONTEXT_FIELD_INVALID)
    return tuple(dict.fromkeys(blocks))


def clamp_scope_band(
    initial_volatility_distance: float,
    min_scope_band: float,
    max_scope_band: float,
) -> float:
    """Clamp volatility distance into [min_scope_band, max_scope_band]."""
    lo = float(min_scope_band)
    hi = float(max_scope_band)
    if hi < lo:
        return lo
    return max(lo, min(hi, float(initial_volatility_distance)))


def _derive_scope_id(instrument_id: str, trading_epoch: int, context_id: str) -> str:
    return f"scope-{instrument_id}-epoch{trading_epoch}-{context_id}"


def _sorted_reason_code_values(
    reasons: Tuple[CanonicalScopeBlockReason, ...],
) -> Tuple[str, ...]:
    return tuple(sorted(r.value for r in reasons))


def _reinitialization_guard_blocks(
    guard: ScopeReinitializationGuardV1,
) -> Tuple[CanonicalScopeBlockReason, ...]:
    blocks: list[CanonicalScopeBlockReason] = []
    if guard.has_open_position:
        blocks.append(CanonicalScopeBlockReason.REINITIALIZATION_OPEN_POSITION)
    if guard.has_unknown_position:
        blocks.append(CanonicalScopeBlockReason.REINITIALIZATION_UNKNOWN_POSITION)
    if guard.has_unresolved_increase_order:
        blocks.append(CanonicalScopeBlockReason.REINITIALIZATION_UNRESOLVED_INCREASE_ORDER)
    if guard.has_unresolved_reduce_order:
        blocks.append(CanonicalScopeBlockReason.REINITIALIZATION_UNRESOLVED_REDUCE_ORDER)
    if guard.has_submission_unknown:
        blocks.append(CanonicalScopeBlockReason.REINITIALIZATION_SUBMISSION_UNKNOWN)
    if guard.reconciliation_status != _RECONCILED_STATUS:
        blocks.append(CanonicalScopeBlockReason.REINITIALIZATION_NOT_RECONCILED)
    return tuple(blocks)


def _collect_prerequisite_blocks(
    context: CanonicalMarketContextV1,
    prerequisites: ScopeInitializationPrerequisitesV1,
) -> Tuple[CanonicalScopeBlockReason, ...]:
    blocks: list[CanonicalScopeBlockReason] = []

    if not canonical_market_type_allowed(context.market_type):
        blocks.append(CanonicalScopeBlockReason.INSTRUMENT_KIND_FORBIDDEN)

    context_field_blocks = validate_canonical_market_context_fields(context)
    if context_field_blocks:
        blocks.append(CanonicalScopeBlockReason.MARKET_CONTEXT_FIELD_INVALID)

    if context.warmup_status is WarmupStatus.WARMUP_INVALID:
        blocks.append(CanonicalScopeBlockReason.WARMUP_INVALID)
    elif context.warmup_status is WarmupStatus.WARMUP_REQUIRED:
        blocks.append(CanonicalScopeBlockReason.WARMUP_INCOMPLETE)

    if context.bar_finality_status is not BarFinalityStatus.FINALIZED:
        blocks.append(CanonicalScopeBlockReason.BAR_UNFINALIZED)

    if context.data_integrity_status in (
        DataIntegrityStatus.UNTRUSTED,
        DataIntegrityStatus.INVALID,
    ):
        blocks.append(CanonicalScopeBlockReason.DATA_INTEGRITY_UNTRUSTED)
    elif context.data_integrity_status is DataIntegrityStatus.UNKNOWN:
        blocks.append(CanonicalScopeBlockReason.DATA_INTEGRITY_UNKNOWN)

    if context.clock_trust_status in (ClockTrustStatus.UNTRUSTED, ClockTrustStatus.INVALID):
        blocks.append(CanonicalScopeBlockReason.CLOCK_TRUST_UNTRUSTED)
    elif context.clock_trust_status is ClockTrustStatus.UNKNOWN:
        blocks.append(CanonicalScopeBlockReason.CLOCK_TRUST_UNKNOWN)

    if not prerequisites.required_window_complete:
        blocks.append(CanonicalScopeBlockReason.REQUIRED_WINDOW_INCOMPLETE)
    if not prerequisites.instrument_metadata_valid:
        blocks.append(CanonicalScopeBlockReason.INSTRUMENT_METADATA_INVALID)
    if not prerequisites.finalized_market_context:
        blocks.append(CanonicalScopeBlockReason.MARKET_CONTEXT_NOT_FINALIZED)

    if not _positive_finite(context.mark_price):
        blocks.append(CanonicalScopeBlockReason.MARK_PRICE_NON_POSITIVE)
    if not _non_negative_finite(context.volatility_estimate):
        blocks.append(CanonicalScopeBlockReason.VOLATILITY_NEGATIVE)

    return tuple(dict.fromkeys(blocks))


def _is_warming_up_block(reason: CanonicalScopeBlockReason) -> bool:
    return reason in (
        CanonicalScopeBlockReason.WARMUP_INCOMPLETE,
        CanonicalScopeBlockReason.REQUIRED_WINDOW_INCOMPLETE,
    )


def _is_hard_invalid_block(reason: CanonicalScopeBlockReason) -> bool:
    return reason in (
        CanonicalScopeBlockReason.WARMUP_INVALID,
        CanonicalScopeBlockReason.MARK_PRICE_NON_POSITIVE,
        CanonicalScopeBlockReason.VOLATILITY_NEGATIVE,
        CanonicalScopeBlockReason.MIN_SCOPE_BAND_NON_POSITIVE,
        CanonicalScopeBlockReason.MAX_SCOPE_BAND_LT_MIN,
        CanonicalScopeBlockReason.INSTRUMENT_KIND_FORBIDDEN,
    )


def classify_scope_lifecycle_state(
    block_reasons: Tuple[CanonicalScopeBlockReason, ...],
) -> CanonicalScopeLifecycleState:
    if any(_is_hard_invalid_block(r) for r in block_reasons):
        return CanonicalScopeLifecycleState.SCOPE_INVALID
    if block_reasons and all(_is_warming_up_block(r) for r in block_reasons):
        return CanonicalScopeLifecycleState.SCOPE_WARMING_UP
    if any(_is_warming_up_block(r) for r in block_reasons):
        return CanonicalScopeLifecycleState.SCOPE_WARMING_UP
    if block_reasons:
        return CanonicalScopeLifecycleState.SCOPE_UNINITIALIZED
    return CanonicalScopeLifecycleState.SCOPE_VALID


def serialize_canonical_scope_canonical(scope: CanonicalScopeSnapshotV1) -> str:
    """Deterministic JSON serialization for semantic digest (excludes semantic_digest)."""
    payload = {
        "initialized_at_trading_epoch": scope.initialized_at_trading_epoch,
        "initial_volatility_distance": scope.initial_volatility_distance,
        "instrument_id": scope.instrument_id,
        "layer_version": CANONICAL_SCOPE_INITIALIZATION_LAYER_VERSION,
        "lifecycle_state": scope.lifecycle_state.value,
        "max_scope_band": scope.max_scope_band,
        "min_scope_band": scope.min_scope_band,
        "neutral_lower_boundary": scope.neutral_lower_boundary,
        "neutral_upper_boundary": scope.neutral_upper_boundary,
        "policy_version": scope.policy_version,
        "reason_codes": sorted(scope.reason_codes),
        "reference_price": scope.reference_price,
        "scope_band": scope.scope_band,
        "source_input_digest": scope.source_input_digest,
        "source_market_context_id": scope.source_market_context_id,
        "trailing_anchor": scope.trailing_anchor,
        "volatility_estimate": scope.volatility_estimate,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_canonical_scope_semantic_digest(scope: CanonicalScopeSnapshotV1) -> str:
    canonical = serialize_canonical_scope_canonical(scope)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def with_computed_semantic_digest(scope: CanonicalScopeSnapshotV1) -> CanonicalScopeSnapshotV1:
    digest = compute_canonical_scope_semantic_digest(scope)
    return CanonicalScopeSnapshotV1(
        scope_id=scope.scope_id,
        instrument_id=scope.instrument_id,
        initialized_at_trading_epoch=scope.initialized_at_trading_epoch,
        source_market_context_id=scope.source_market_context_id,
        source_input_digest=scope.source_input_digest,
        lifecycle_state=scope.lifecycle_state,
        reference_price=scope.reference_price,
        volatility_estimate=scope.volatility_estimate,
        initial_volatility_distance=scope.initial_volatility_distance,
        scope_band=scope.scope_band,
        neutral_upper_boundary=scope.neutral_upper_boundary,
        neutral_lower_boundary=scope.neutral_lower_boundary,
        trailing_anchor=scope.trailing_anchor,
        min_scope_band=scope.min_scope_band,
        max_scope_band=scope.max_scope_band,
        policy_version=scope.policy_version,
        semantic_digest=digest,
        reason_codes=scope.reason_codes,
    )


def _build_initialized_scope(
    context: CanonicalMarketContextV1,
    policy: CanonicalScopeInitializationPolicyV1,
    *,
    reason_codes: Tuple[str, ...] = (),
) -> CanonicalScopeSnapshotV1:
    bound_context = context if context.input_digest else with_computed_input_digest(context)
    reference_price = float(bound_context.mark_price)
    volatility_estimate = float(bound_context.volatility_estimate)
    initial_volatility_distance = volatility_estimate * reference_price
    scope_band = clamp_scope_band(
        initial_volatility_distance,
        policy.min_scope_band,
        policy.max_scope_band,
    )
    neutral_upper_boundary = reference_price + scope_band
    neutral_lower_boundary = reference_price - scope_band
    trailing_anchor = reference_price

    scope = CanonicalScopeSnapshotV1(
        scope_id=_derive_scope_id(
            bound_context.instrument_id,
            bound_context.trading_epoch,
            bound_context.context_id,
        ),
        instrument_id=bound_context.instrument_id,
        initialized_at_trading_epoch=bound_context.trading_epoch,
        source_market_context_id=bound_context.context_id,
        source_input_digest=bound_context.input_digest,
        lifecycle_state=CanonicalScopeLifecycleState.SCOPE_VALID,
        reference_price=reference_price,
        volatility_estimate=volatility_estimate,
        initial_volatility_distance=initial_volatility_distance,
        scope_band=scope_band,
        neutral_upper_boundary=neutral_upper_boundary,
        neutral_lower_boundary=neutral_lower_boundary,
        trailing_anchor=trailing_anchor,
        min_scope_band=policy.min_scope_band,
        max_scope_band=policy.max_scope_band,
        policy_version=policy.policy_version,
        semantic_digest="",
        reason_codes=reason_codes,
    )
    return with_computed_semantic_digest(scope)


def initialize_canonical_scope(
    market_context: CanonicalMarketContextV1,
    policy: CanonicalScopeInitializationPolicyV1,
    prerequisites: ScopeInitializationPrerequisitesV1,
    *,
    existing_scope: Optional[CanonicalScopeSnapshotV1] = None,
    reinitialization_guard: Optional[ScopeReinitializationGuardV1] = None,
) -> CanonicalScopeInitializationResultV1:
    """
    Initialize canonical scope from a finalized futures market context.

    Fail-closed: no implicit defaults, no authority/order/runtime effects,
    no scope-event generation.
    """
    blocks: list[CanonicalScopeBlockReason] = []

    policy_blocks = validate_scope_initialization_policy(policy)
    blocks.extend(policy_blocks)

    if existing_scope is not None:
        if existing_scope.lifecycle_state is CanonicalScopeLifecycleState.SCOPE_VALID:
            bound = (
                market_context
                if market_context.input_digest
                else with_computed_input_digest(market_context)
            )
            if (
                existing_scope.source_input_digest
                and bound.input_digest
                and existing_scope.source_input_digest != bound.input_digest
            ):
                return CanonicalScopeInitializationResultV1(
                    scope=existing_scope,
                    lifecycle_state=CanonicalScopeLifecycleState.SCOPE_STALE,
                    block_reasons=(CanonicalScopeBlockReason.SCOPE_CONTEXT_STALE,),
                )
            blocks.append(CanonicalScopeBlockReason.SCOPE_ALREADY_INITIALIZED)
            guard = reinitialization_guard or ScopeReinitializationGuardV1()
            blocks.extend(_reinitialization_guard_blocks(guard))

    prereq_blocks = _collect_prerequisite_blocks(market_context, prerequisites)
    blocks.extend(prereq_blocks)
    all_blocks = tuple(dict.fromkeys(blocks))

    lifecycle = classify_scope_lifecycle_state(all_blocks)

    if all_blocks:
        if (
            existing_scope is not None
            and existing_scope.lifecycle_state is CanonicalScopeLifecycleState.SCOPE_VALID
            and CanonicalScopeBlockReason.SCOPE_ALREADY_INITIALIZED in all_blocks
        ):
            return CanonicalScopeInitializationResultV1(
                scope=existing_scope,
                lifecycle_state=lifecycle,
                block_reasons=all_blocks,
            )
        return CanonicalScopeInitializationResultV1(
            scope=None,
            lifecycle_state=lifecycle,
            block_reasons=all_blocks,
        )

    scope = _build_initialized_scope(market_context, policy)
    return CanonicalScopeInitializationResultV1(
        scope=scope,
        lifecycle_state=CanonicalScopeLifecycleState.SCOPE_VALID,
        block_reasons=(),
    )
