# src/trading/master_v2/canonical_market_context_v1.py
"""
Pure Canonical Market Context v1: data-only futures market context contract.

Bound to Master V2 / Double Play futures input infrastructure via shared
``FuturesMarketType`` and narrow adapter helpers. No I/O, runtime, adapter,
order, or execution authority.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Optional, Tuple

from trading.master_v2.double_play_futures_input import (
    FuturesInputSnapshot,
    FuturesMarketType,
)

CANONICAL_MARKET_CONTEXT_LAYER_VERSION = "v1"
FEATURE_CONTRACT_VERSION = "canonical_market_context_feature_contract_v1"
PRIMARY_DECISION_PRICE = "VENUE_MARK_PRICE"

_FORBIDDEN_INSTRUMENT_KINDS = frozenset(
    {"spot", "synthetic_spot", "synthetic-spot", "syntheticspot"}
)
_SPREAD_TOLERANCE = 1e-9
_ISO8601_UTC_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(\+00:00|Z)$")


class BarFinalityStatus(str, Enum):
    FINALIZED = "finalized"
    UNFINALIZED = "unfinalized"
    UNKNOWN = "unknown"


class WarmupStatus(str, Enum):
    WARMUP_REQUIRED = "warmup_required"
    WARMUP_COMPLETE = "warmup_complete"
    WARMUP_INVALID = "warmup_invalid"


class DataIntegrityStatus(str, Enum):
    TRUSTED = "trusted"
    UNTRUSTED = "untrusted"
    UNKNOWN = "unknown"
    INVALID = "invalid"


class ClockTrustStatus(str, Enum):
    TRUSTED = "trusted"
    UNTRUSTED = "untrusted"
    UNKNOWN = "unknown"
    INVALID = "invalid"


_TRUSTED_DATA_INTEGRITY = frozenset({DataIntegrityStatus.TRUSTED})
_TRUSTED_CLOCK_TRUST = frozenset({ClockTrustStatus.TRUSTED})


class CanonicalMarketContextBlockReason(str, Enum):
    INSTRUMENT_KIND_FORBIDDEN = "instrument_kind_forbidden"
    INSTRUMENT_KIND_UNKNOWN = "instrument_kind_unknown"
    INSTRUMENT_ID_INVALID = "instrument_id_invalid"
    TRADING_EPOCH_INVALID = "trading_epoch_invalid"
    MARKET_EVENT_TIME_INVALID = "market_event_time_invalid"
    DECISION_TIME_INVALID = "decision_time_invalid"
    DECISION_TIME_BEFORE_MARKET_EVENT = "decision_time_before_market_event"
    BAR_INTERVAL_INVALID = "bar_interval_invalid"
    BAR_FINALITY_UNKNOWN = "bar_finality_unknown"
    BAR_UNFINALIZED = "bar_unfinalized"
    MARK_PRICE_INVALID = "mark_price_invalid"
    INDEX_PRICE_INVALID = "index_price_invalid"
    BEST_BID_INVALID = "best_bid_invalid"
    BEST_ASK_INVALID = "best_ask_invalid"
    SPREAD_INCONSISTENT = "spread_inconsistent"
    SPREAD_INVALID = "spread_invalid"
    VOLUME_INVALID = "volume_invalid"
    OPEN_INTEREST_INVALID = "open_interest_invalid"
    FUNDING_RATE_INVALID = "funding_rate_invalid"
    VOLATILITY_ESTIMATE_INVALID = "volatility_estimate_invalid"
    FEATURE_CONTRACT_VERSION_INVALID = "feature_contract_version_invalid"
    DATA_INTEGRITY_UNTRUSTED = "data_integrity_untrusted"
    DATA_INTEGRITY_UNKNOWN = "data_integrity_unknown"
    CLOCK_TRUST_UNTRUSTED = "clock_trust_untrusted"
    CLOCK_TRUST_UNKNOWN = "clock_trust_unknown"
    WARMUP_REQUIRED = "warmup_required"
    WARMUP_INVALID = "warmup_invalid"
    OUT_OF_ORDER_MARKET_EVENT = "out_of_order_market_event"
    FUTURES_INPUT_INSTRUMENT_MISMATCH = "futures_input_instrument_mismatch"
    FUTURES_INPUT_MARKET_TYPE_MISMATCH = "futures_input_market_type_mismatch"


class CanonicalMarketContextBindingOutcome(str, Enum):
    ACCEPTED = "accepted"
    DUPLICATE_IDEMPOTENT = "duplicate_idempotent"
    BLOCKED = "blocked"


def futures_market_type_to_canonical(market_type: FuturesMarketType) -> FuturesMarketType:
    """Narrow reuse bridge: canonical context uses the same futures market type enum."""
    return market_type


def canonical_market_type_allowed(market_type: FuturesMarketType) -> bool:
    return market_type in (
        FuturesMarketType.FUTURES,
        FuturesMarketType.PERPETUAL,
        FuturesMarketType.SWAP,
    )


def _normalize_feature_set(features: Mapping[str, float]) -> Tuple[Tuple[str, float], ...]:
    return tuple(sorted((str(k), float(v)) for k, v in features.items()))


@dataclass(frozen=True)
class CanonicalMarketContextV1:
    context_id: str
    instrument_id: str
    market_type: FuturesMarketType
    trading_epoch: int
    market_event_time: str
    decision_time: str
    bar_interval: str
    bar_finality_status: BarFinalityStatus
    mark_price: float
    index_price: float
    best_bid: float
    best_ask: float
    spread: float
    volume: float
    open_interest: float
    funding_rate: float
    volatility_estimate: float
    trend_feature_set: Mapping[str, float]
    momentum_feature_set: Mapping[str, float]
    liquidity_feature_set: Mapping[str, float]
    market_structure_feature_set: Mapping[str, float]
    data_integrity_status: DataIntegrityStatus
    clock_trust_status: ClockTrustStatus
    warmup_status: WarmupStatus
    feature_contract_version: str = FEATURE_CONTRACT_VERSION
    input_digest: str = ""

    def __post_init__(self) -> None:
        if self.input_digest and not _valid_sha256_hex(self.input_digest):
            msg = "input_digest must be empty or a 64-char lowercase sha256 hex"
            raise ValueError(msg)


@dataclass(frozen=True)
class CanonicalMarketContextEligibilityV1:
    """Non-authority eligibility labels for downstream scope/trading gates."""

    binding_outcome: CanonicalMarketContextBindingOutcome
    decision_price_source: str
    primary_decision_price: float
    trading_decision_allowed: bool
    scope_confirmation_allowed: bool
    new_directional_exposure_allowed: bool
    observation_and_reconciliation_only: bool
    block_reasons: Tuple[CanonicalMarketContextBlockReason, ...]
    is_authority: bool = False
    is_signal: bool = False
    execution_eligible: bool = False
    live_authorization: bool = False


@dataclass(frozen=True)
class CanonicalMarketContextBindingStateV1:
    """Immutable idempotence and ordering state for sequential event binding."""

    last_market_event_time: Optional[str] = None
    seen_context_ids: Tuple[str, ...] = ()
    last_input_digest: Optional[str] = None


@dataclass(frozen=True)
class CanonicalMarketContextBindingResultV1:
    context: Optional[CanonicalMarketContextV1]
    eligibility: CanonicalMarketContextEligibilityV1
    next_state: CanonicalMarketContextBindingStateV1
    validation_errors: Tuple[str, ...] = ()


def _valid_sha256_hex(value: str) -> bool:
    return bool(re.fullmatch(r"[0-9a-f]{64}", value))


def _parse_utc_instant(value: str) -> Optional[str]:
    if not isinstance(value, str) or not value.strip():
        return None
    stripped = value.strip()
    if not _ISO8601_UTC_PATTERN.match(stripped):
        return None
    return stripped


def _instrument_id_valid(instrument_id: str) -> bool:
    if not isinstance(instrument_id, str):
        return False
    stripped = instrument_id.strip()
    if not stripped or len(stripped) > 256:
        return False
    lowered = stripped.lower()
    for forbidden in _FORBIDDEN_INSTRUMENT_KINDS:
        if forbidden in lowered:
            return False
    return True


def _positive_finite(value: object) -> bool:
    return isinstance(value, (int, float)) and float(value) > 0.0


def _non_negative_finite(value: object) -> bool:
    return isinstance(value, (int, float)) and float(value) >= 0.0


def _spread_matches_bid_ask(spread: float, best_bid: float, best_ask: float) -> bool:
    if best_ask < best_bid:
        return False
    expected = best_ask - best_bid
    return abs(spread - expected) <= _SPREAD_TOLERANCE


def validate_canonical_market_context_fields(
    context: CanonicalMarketContextV1,
) -> Tuple[CanonicalMarketContextBlockReason, ...]:
    blocks: list[CanonicalMarketContextBlockReason] = []

    if not context.context_id or not str(context.context_id).strip():
        blocks.append(CanonicalMarketContextBlockReason.INSTRUMENT_ID_INVALID)

    if not _instrument_id_valid(context.instrument_id):
        blocks.append(CanonicalMarketContextBlockReason.INSTRUMENT_ID_INVALID)

    if context.market_type is FuturesMarketType.UNKNOWN:
        blocks.append(CanonicalMarketContextBlockReason.INSTRUMENT_KIND_UNKNOWN)
    elif not canonical_market_type_allowed(context.market_type):
        blocks.append(CanonicalMarketContextBlockReason.INSTRUMENT_KIND_FORBIDDEN)

    if not isinstance(context.trading_epoch, int) or context.trading_epoch < 0:
        blocks.append(CanonicalMarketContextBlockReason.TRADING_EPOCH_INVALID)

    market_event_time = _parse_utc_instant(context.market_event_time)
    if market_event_time is None:
        blocks.append(CanonicalMarketContextBlockReason.MARKET_EVENT_TIME_INVALID)

    decision_time = _parse_utc_instant(context.decision_time)
    if decision_time is None:
        blocks.append(CanonicalMarketContextBlockReason.DECISION_TIME_INVALID)
    elif market_event_time is not None and decision_time < market_event_time:
        blocks.append(CanonicalMarketContextBlockReason.DECISION_TIME_BEFORE_MARKET_EVENT)

    if not context.bar_interval or not str(context.bar_interval).strip():
        blocks.append(CanonicalMarketContextBlockReason.BAR_INTERVAL_INVALID)

    if context.bar_finality_status is BarFinalityStatus.UNKNOWN:
        blocks.append(CanonicalMarketContextBlockReason.BAR_FINALITY_UNKNOWN)
    elif context.bar_finality_status is BarFinalityStatus.UNFINALIZED:
        blocks.append(CanonicalMarketContextBlockReason.BAR_UNFINALIZED)

    if not _positive_finite(context.mark_price):
        blocks.append(CanonicalMarketContextBlockReason.MARK_PRICE_INVALID)
    if not _positive_finite(context.index_price):
        blocks.append(CanonicalMarketContextBlockReason.INDEX_PRICE_INVALID)
    if not _positive_finite(context.best_bid):
        blocks.append(CanonicalMarketContextBlockReason.BEST_BID_INVALID)
    if not _positive_finite(context.best_ask):
        blocks.append(CanonicalMarketContextBlockReason.BEST_ASK_INVALID)
    if not _non_negative_finite(context.spread):
        blocks.append(CanonicalMarketContextBlockReason.SPREAD_INVALID)
    elif _positive_finite(context.best_bid) and _positive_finite(context.best_ask):
        if not _spread_matches_bid_ask(context.spread, context.best_bid, context.best_ask):
            blocks.append(CanonicalMarketContextBlockReason.SPREAD_INCONSISTENT)

    if not _non_negative_finite(context.volume):
        blocks.append(CanonicalMarketContextBlockReason.VOLUME_INVALID)
    if not _non_negative_finite(context.open_interest):
        blocks.append(CanonicalMarketContextBlockReason.OPEN_INTEREST_INVALID)
    if not isinstance(context.funding_rate, (int, float)):
        blocks.append(CanonicalMarketContextBlockReason.FUNDING_RATE_INVALID)
    if not _non_negative_finite(context.volatility_estimate):
        blocks.append(CanonicalMarketContextBlockReason.VOLATILITY_ESTIMATE_INVALID)

    if (
        not context.feature_contract_version
        or context.feature_contract_version != FEATURE_CONTRACT_VERSION
    ):
        blocks.append(CanonicalMarketContextBlockReason.FEATURE_CONTRACT_VERSION_INVALID)

    if context.data_integrity_status in (
        DataIntegrityStatus.UNTRUSTED,
        DataIntegrityStatus.INVALID,
    ):
        blocks.append(CanonicalMarketContextBlockReason.DATA_INTEGRITY_UNTRUSTED)
    elif context.data_integrity_status is DataIntegrityStatus.UNKNOWN:
        blocks.append(CanonicalMarketContextBlockReason.DATA_INTEGRITY_UNKNOWN)

    if context.clock_trust_status in (ClockTrustStatus.UNTRUSTED, ClockTrustStatus.INVALID):
        blocks.append(CanonicalMarketContextBlockReason.CLOCK_TRUST_UNTRUSTED)
    elif context.clock_trust_status is ClockTrustStatus.UNKNOWN:
        blocks.append(CanonicalMarketContextBlockReason.CLOCK_TRUST_UNKNOWN)

    if context.warmup_status is WarmupStatus.WARMUP_REQUIRED:
        blocks.append(CanonicalMarketContextBlockReason.WARMUP_REQUIRED)
    elif context.warmup_status is WarmupStatus.WARMUP_INVALID:
        blocks.append(CanonicalMarketContextBlockReason.WARMUP_INVALID)

    return tuple(dict.fromkeys(blocks))


def serialize_canonical_market_context_canonical(context: CanonicalMarketContextV1) -> str:
    """Deterministic JSON serialization for digest (excludes input_digest field)."""
    payload = {
        "bar_finality_status": context.bar_finality_status.value,
        "bar_interval": context.bar_interval,
        "best_ask": context.best_ask,
        "best_bid": context.best_bid,
        "clock_trust_status": context.clock_trust_status.value,
        "context_id": context.context_id,
        "data_integrity_status": context.data_integrity_status.value,
        "decision_time": context.decision_time,
        "feature_contract_version": context.feature_contract_version,
        "funding_rate": context.funding_rate,
        "index_price": context.index_price,
        "instrument_id": context.instrument_id,
        "layer_version": CANONICAL_MARKET_CONTEXT_LAYER_VERSION,
        "liquidity_feature_set": list(_normalize_feature_set(context.liquidity_feature_set)),
        "mark_price": context.mark_price,
        "market_event_time": context.market_event_time,
        "market_structure_feature_set": list(
            _normalize_feature_set(context.market_structure_feature_set)
        ),
        "market_type": context.market_type.value,
        "momentum_feature_set": list(_normalize_feature_set(context.momentum_feature_set)),
        "open_interest": context.open_interest,
        "primary_decision_price_source": PRIMARY_DECISION_PRICE,
        "spread": context.spread,
        "trading_epoch": context.trading_epoch,
        "trend_feature_set": list(_normalize_feature_set(context.trend_feature_set)),
        "volatility_estimate": context.volatility_estimate,
        "volume": context.volume,
        "warmup_status": context.warmup_status.value,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_canonical_market_context_input_digest(context: CanonicalMarketContextV1) -> str:
    """Deterministic digest over normalized decision-relevant inputs."""
    canonical = serialize_canonical_market_context_canonical(context)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def with_computed_input_digest(context: CanonicalMarketContextV1) -> CanonicalMarketContextV1:
    digest = compute_canonical_market_context_input_digest(context)
    return CanonicalMarketContextV1(
        context_id=context.context_id,
        instrument_id=context.instrument_id,
        market_type=context.market_type,
        trading_epoch=context.trading_epoch,
        market_event_time=context.market_event_time,
        decision_time=context.decision_time,
        bar_interval=context.bar_interval,
        bar_finality_status=context.bar_finality_status,
        mark_price=context.mark_price,
        index_price=context.index_price,
        best_bid=context.best_bid,
        best_ask=context.best_ask,
        spread=context.spread,
        volume=context.volume,
        open_interest=context.open_interest,
        funding_rate=context.funding_rate,
        volatility_estimate=context.volatility_estimate,
        trend_feature_set=context.trend_feature_set,
        momentum_feature_set=context.momentum_feature_set,
        liquidity_feature_set=context.liquidity_feature_set,
        market_structure_feature_set=context.market_structure_feature_set,
        data_integrity_status=context.data_integrity_status,
        clock_trust_status=context.clock_trust_status,
        warmup_status=context.warmup_status,
        feature_contract_version=context.feature_contract_version,
        input_digest=digest,
    )


def _warmup_blocks_directional_and_scope(
    warmup_status: WarmupStatus,
) -> bool:
    return warmup_status in (WarmupStatus.WARMUP_REQUIRED, WarmupStatus.WARMUP_INVALID)


def evaluate_canonical_market_context_eligibility(
    context: CanonicalMarketContextV1,
    *,
    binding_outcome: CanonicalMarketContextBindingOutcome = CanonicalMarketContextBindingOutcome.ACCEPTED,
    extra_blocks: Tuple[CanonicalMarketContextBlockReason, ...] = (),
) -> CanonicalMarketContextEligibilityV1:
    """Evaluate non-authority eligibility from a validated canonical market context."""
    field_blocks = validate_canonical_market_context_fields(context)
    all_blocks = tuple(dict.fromkeys((*field_blocks, *extra_blocks)))

    trusted_integrity = context.data_integrity_status in _TRUSTED_DATA_INTEGRITY
    trusted_clock = context.clock_trust_status in _TRUSTED_CLOCK_TRUST
    finalized_bar = context.bar_finality_status is BarFinalityStatus.FINALIZED
    warmup_ok = context.warmup_status is WarmupStatus.WARMUP_COMPLETE

    base_ok = (
        binding_outcome
        in (
            CanonicalMarketContextBindingOutcome.ACCEPTED,
            CanonicalMarketContextBindingOutcome.DUPLICATE_IDEMPOTENT,
        )
        and not all_blocks
    )

    trading_allowed = (
        base_ok and finalized_bar and trusted_integrity and trusted_clock and warmup_ok
    )
    scope_allowed = trading_allowed
    directional_allowed = trading_allowed
    observation_only = _warmup_blocks_directional_and_scope(context.warmup_status) or bool(
        all_blocks
    )

    if binding_outcome is CanonicalMarketContextBindingOutcome.BLOCKED:
        trading_allowed = False
        scope_allowed = False
        directional_allowed = False
        observation_only = True

    return CanonicalMarketContextEligibilityV1(
        binding_outcome=binding_outcome,
        decision_price_source=PRIMARY_DECISION_PRICE,
        primary_decision_price=context.mark_price,
        trading_decision_allowed=trading_allowed,
        scope_confirmation_allowed=scope_allowed,
        new_directional_exposure_allowed=directional_allowed,
        observation_and_reconciliation_only=observation_only,
        block_reasons=all_blocks,
        is_authority=False,
        is_signal=False,
        execution_eligible=False,
        live_authorization=False,
    )


def validate_futures_input_snapshot_binding(
    context: CanonicalMarketContextV1,
    snapshot: FuturesInputSnapshot,
) -> Tuple[CanonicalMarketContextBlockReason, ...]:
    """Narrow adapter: ensure canonical context aligns with futures input snapshot identity."""
    blocks: list[CanonicalMarketContextBlockReason] = []
    if snapshot.candidate.instrument_id != context.instrument_id:
        blocks.append(CanonicalMarketContextBlockReason.FUTURES_INPUT_INSTRUMENT_MISMATCH)
    if snapshot.candidate.market_type != context.market_type:
        blocks.append(CanonicalMarketContextBlockReason.FUTURES_INPUT_MARKET_TYPE_MISMATCH)
    return tuple(blocks)


def bind_canonical_market_context_event(
    context: CanonicalMarketContextV1,
    state: CanonicalMarketContextBindingStateV1,
    *,
    futures_input_snapshot: Optional[FuturesInputSnapshot] = None,
) -> CanonicalMarketContextBindingResultV1:
    """
    Bind one canonical market context event with fail-closed ordering and idempotence.

    Duplicate ``context_id`` returns idempotent eligibility without mutating ordering state.
    Out-of-order ``market_event_time`` is blocked fail-closed.
    """
    extra_blocks: list[CanonicalMarketContextBlockReason] = []
    validation_errors: list[str] = []

    market_event_time = _parse_utc_instant(context.market_event_time)
    if market_event_time is None:
        validation_errors.append("market_event_time must be canonical UTC ISO8601")

    if context.context_id in state.seen_context_ids:
        bound = with_computed_input_digest(context)
        eligibility = evaluate_canonical_market_context_eligibility(
            bound,
            binding_outcome=CanonicalMarketContextBindingOutcome.DUPLICATE_IDEMPOTENT,
        )
        return CanonicalMarketContextBindingResultV1(
            context=bound,
            eligibility=eligibility,
            next_state=state,
            validation_errors=tuple(validation_errors),
        )

    if (
        state.last_market_event_time is not None
        and market_event_time is not None
        and market_event_time < state.last_market_event_time
    ):
        extra_blocks.append(CanonicalMarketContextBlockReason.OUT_OF_ORDER_MARKET_EVENT)

    if futures_input_snapshot is not None:
        extra_blocks.extend(
            validate_futures_input_snapshot_binding(context, futures_input_snapshot)
        )

    bound = with_computed_input_digest(context)
    outcome = (
        CanonicalMarketContextBindingOutcome.BLOCKED
        if extra_blocks or validate_canonical_market_context_fields(bound)
        else CanonicalMarketContextBindingOutcome.ACCEPTED
    )
    eligibility = evaluate_canonical_market_context_eligibility(
        bound,
        binding_outcome=outcome,
        extra_blocks=tuple(extra_blocks),
    )

    if outcome is CanonicalMarketContextBindingOutcome.ACCEPTED and market_event_time is not None:
        next_state = CanonicalMarketContextBindingStateV1(
            last_market_event_time=market_event_time,
            seen_context_ids=state.seen_context_ids + (context.context_id,),
            last_input_digest=bound.input_digest,
        )
    else:
        next_state = state

    return CanonicalMarketContextBindingResultV1(
        context=bound,
        eligibility=eligibility,
        next_state=next_state,
        validation_errors=tuple(validation_errors),
    )
