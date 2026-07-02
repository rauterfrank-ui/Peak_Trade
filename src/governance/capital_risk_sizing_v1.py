"""
Offline Capital Risk Sizing Mathematics v1 (RUNBOOK STEP 29P).

Pure, deterministic, fail-closed monotone quantity chain:
CanonicalTradingDecisionEvidenceV1 → ScopeCapitalEnvelopeV1 →
PreSizingRiskAssessmentV1 → CanonicalPositionSizingV1 →
PostSizingRiskAssessmentV1 → QuantityProvenanceV1.

No adapter compatibility, submission, runtime authority, order intent, or
execution permission.
"""

from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import dataclass, fields
from decimal import Decimal, InvalidOperation
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from trading.master_v2.canonical_trading_decision_evidence_v1 import (
    CanonicalTradingDecisionEvidenceV1,
)

CONTRACT_NAME = "capital_risk_sizing_v1"
CONTRACT_VERSION = "v1"
SCHEMA_VERSION = "capital_risk_sizing_schema_v1"
IMPLEMENTATION_DIGEST = "capital_risk_sizing_v1_offline_slice"

PACKAGE_MARKER = "CAPITAL_RISK_SIZING_V1=true"
FUTURES_ONLY = True
BITCOIN_DIRECTION_ALLOWED = False
SPOT_ALLOWED = False
SYNTHETIC_SPOT_ALLOWED = False

AUTHORITY_EFFECT_NONE = "NONE"
RUNTIME_EFFECT_NONE = "NONE"

_FORBIDDEN_INSTRUMENT_MARKERS = frozenset({"btc", "xbt", "bitcoin"})
_FORBIDDEN_MARKET_TYPES = frozenset({"spot", "synthetic_spot", "synthetic-spot"})
_ALLOWED_SIDES = frozenset({"LONG", "SHORT", "long", "short"})
_ALLOWED_RECONCILIATION = frozenset({"RECONCILED", "reconciled"})
_ALLOWED_CONTRACT_KINDS = frozenset({"LINEAR"})
_ENTRY_OUTCOMES = frozenset({"enter_long", "enter_short"})
_REDUCE_OUTCOMES = frozenset({"reduce"})
_EXIT_OUTCOMES = frozenset({"exit"})
_REDUCE_ONLY_OUTCOMES = _REDUCE_OUTCOMES | _EXIT_OUTCOMES

REASON_INVALID_DECISION = "INVALID_DECISION"
REASON_INVALID_DIRECTION = "INVALID_DIRECTION"
REASON_MISSING_CAPITAL_INPUT = "MISSING_CAPITAL_INPUT"
REASON_INVALID_CAPITAL_INPUT = "INVALID_CAPITAL_INPUT"
REASON_DAILY_LOSS_BUDGET_EXHAUSTED = "DAILY_LOSS_BUDGET_EXHAUSTED"
REASON_TRADE_RISK_BUDGET_EXHAUSTED = "TRADE_RISK_BUDGET_EXHAUSTED"
REASON_INVALID_REFERENCE_PRICE = "INVALID_REFERENCE_PRICE"
REASON_INVALID_STOP_PRICE = "INVALID_STOP_PRICE"
REASON_ZERO_RISK_DISTANCE = "ZERO_RISK_DISTANCE"
REASON_INVALID_CONTRACT_MULTIPLIER = "INVALID_CONTRACT_MULTIPLIER"
REASON_INVALID_QUANTITY_STEP = "INVALID_QUANTITY_STEP"
REASON_MISSING_INSTRUMENT_METADATA = "MISSING_INSTRUMENT_METADATA"
REASON_MAX_POSITIONS_REACHED = "MAX_POSITIONS_REACHED"
REASON_OPPOSITE_EXPOSURE_PRESENT = "OPPOSITE_EXPOSURE_PRESENT"
REASON_RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"
REASON_BELOW_MIN_QUANTITY = "BELOW_MIN_QUANTITY"
REASON_BELOW_MIN_NOTIONAL = "BELOW_MIN_NOTIONAL"
REASON_ABOVE_MAX_QUANTITY = "ABOVE_MAX_QUANTITY"
REASON_CAPITAL_CAP_BINDING = "CAPITAL_CAP_BINDING"
REASON_RISK_CAP_BINDING = "RISK_CAP_BINDING"
REASON_EXPOSURE_CAP_BINDING = "EXPOSURE_CAP_BINDING"
REASON_VENUE_CAP_BINDING = "VENUE_CAP_BINDING"
REASON_ROUNDED_DOWN = "ROUNDED_DOWN"
REASON_POST_SIZING_RISK_FAILED = "POST_SIZING_RISK_FAILED"
REASON_NON_FINITE_INPUT = "NON_FINITE_INPUT"
REASON_NON_FUTURES_INSTRUMENT = "NON_FUTURES_INSTRUMENT"
REASON_BITCOIN_SPECIFIC_DIRECTION = "BITCOIN_SPECIFIC_DIRECTION"
REASON_UNSUPPORTED_CONTRACT_KIND = "UNSUPPORTED_CONTRACT_KIND"
REASON_NON_ENTRY_OUTCOME = "NON_ENTRY_OUTCOME"
REASON_REDUCE_EXCEEDS_OPEN_POSITION = "REDUCE_EXCEEDS_OPEN_POSITION"
REASON_NO_OPEN_POSITION_FOR_REDUCE = "NO_OPEN_POSITION_FOR_REDUCE"
REASON_POSITION_FLIP_FORBIDDEN = "POSITION_FLIP_FORBIDDEN"
REASON_STALE_POSITION_STATE = "STALE_POSITION_STATE"
REASON_PASS = "PASS"

_FORBIDDEN_RUNTIME_IMPORT_PREFIXES = (
    "src.execution.",
    "src.live.",
    "src.orders.",
)


class EnvelopeStatus(str, Enum):
    PASS = "PASS"
    REDUCE = "REDUCE"
    BLOCK = "BLOCK"


class PreSizingRiskStatus(str, Enum):
    PASS = "PASS"
    REDUCE = "REDUCE"
    BLOCK = "BLOCK"


class QuantityStatus(str, Enum):
    PASS = "PASS"
    ROUNDED_DOWN = "ROUNDED_DOWN"
    BLOCK = "BLOCK"


class PostSizingRiskStatus(str, Enum):
    PASS = "PASS"
    REDUCE = "REDUCE"
    BLOCK = "BLOCK"


class FinalQuantityStatus(str, Enum):
    PASS = "PASS"
    REDUCE = "REDUCE"
    BLOCK = "BLOCK"


class CapitalRiskSizingOutcome(str, Enum):
    PASS = "PASS"
    BLOCKED = "BLOCKED"


class BindingCapKind(str, Enum):
    RISK = "RISK"
    CAPITAL = "CAPITAL"
    EXPOSURE = "EXPOSURE"
    VENUE = "VENUE"
    CONFIGURED = "CONFIGURED"
    REDUCE_ONLY = "REDUCE_ONLY"


@dataclass(frozen=True)
class CapitalRiskSizingPolicyV1:
    """Versioned policy inputs — no hidden literals in sizing math."""

    policy_version: str
    total_capital_limit_usd: Decimal
    order_limit_usd: Decimal
    daily_loss_limit_usd: Decimal
    max_positions: int


@dataclass(frozen=True)
class InstrumentQuantityConstraintsV1:
    instrument_id: str
    market_type: str
    contract_kind: str
    contract_multiplier: Decimal
    lot_size: Decimal
    minimum_quantity: Decimal
    maximum_quantity: Optional[Decimal]
    minimum_notional: Optional[Decimal]
    tick_size: Optional[Decimal]
    instrument_metadata_version: str
    price_precision: Optional[int] = None


@dataclass(frozen=True)
class CapitalRiskSizingContextV1:
    reference_price: Decimal
    protective_stop_price: Optional[Decimal]
    stop_distance: Optional[Decimal]
    account_equity: Decimal
    already_committed_capital: Decimal
    daily_loss_consumed: Decimal
    current_reconciled_exposure: Decimal
    reconciled_open_position_quantity: Decimal
    current_open_positions_count: int
    current_open_side: Optional[str]
    reconciliation_status: str
    configured_quantity_cap: Optional[Decimal]
    leverage_ceiling: Optional[Decimal]
    instrument: InstrumentQuantityConstraintsV1
    config_digest: str
    order_notional_cap: Optional[Decimal] = None
    per_trade_risk_cap: Optional[Decimal] = None


@dataclass(frozen=True)
class ScopeCapitalEnvelopeV1:
    instrument_id: str
    decision_id: str
    policy_version: str
    total_capital_limit: Decimal
    available_capital: Decimal
    already_committed_capital: Decimal
    remaining_capital: Decimal
    per_order_cap: Decimal
    daily_loss_state: Mapping[str, str]
    position_slot_state: Mapping[str, str]
    status: EnvelopeStatus
    reason_codes: tuple[str, ...]
    input_digest: str


@dataclass(frozen=True)
class PreSizingRiskAssessmentV1:
    decision_id: str
    side: str
    reference_price: Decimal
    stop_or_risk_distance: Decimal
    maximum_loss_budget: Decimal
    capital_cap_quantity: Decimal
    loss_budget_quantity: Decimal
    exposure_cap_quantity: Decimal
    candidate_quantity_upper_bound: Decimal
    status: PreSizingRiskStatus
    reason_codes: tuple[str, ...]
    input_digest: str


@dataclass(frozen=True)
class CanonicalPositionSizingV1:
    decision_id: str
    instrument_id: str
    side: str
    raw_quantity: Decimal
    bounded_quantity_before_rounding: Decimal
    lot_size: Decimal
    rounded_quantity: Decimal
    reference_price: Decimal
    resulting_notional: Decimal
    quantity_status: QuantityStatus
    reason_codes: tuple[str, ...]
    policy_digest: str
    input_digest: str


@dataclass(frozen=True)
class PostSizingRiskAssessmentV1:
    proposed_quantity: Decimal
    final_allowed_quantity: Decimal
    resulting_notional: Decimal
    resulting_max_loss: Decimal
    exposure_after: Decimal
    slot_usage_after: int
    status: PostSizingRiskStatus
    reason_codes: tuple[str, ...]
    input_digest: str


@dataclass(frozen=True)
class QuantityProvenanceV1:
    decision_id: str
    source_contract_refs: tuple[str, ...]
    capital_envelope_ref: str
    pre_sizing_risk_ref: str
    sizing_ref: str
    post_sizing_risk_ref: str
    instrument_metadata_ref: str
    policy_version: str
    config_digest: str
    implementation_digest: str
    final_quantity: Decimal
    final_quantity_status: FinalQuantityStatus
    authority_effect: str = AUTHORITY_EFFECT_NONE
    runtime_effect: str = RUNTIME_EFFECT_NONE
    adapter_compatible: bool = False


@dataclass(frozen=True)
class CapitalRiskSizingChainResultV1:
    outcome: CapitalRiskSizingOutcome
    final_quantity: Decimal
    scope_capital_envelope: ScopeCapitalEnvelopeV1
    pre_sizing_risk: PreSizingRiskAssessmentV1
    canonical_position_sizing: Optional[CanonicalPositionSizingV1]
    post_sizing_risk: Optional[PostSizingRiskAssessmentV1]
    quantity_provenance: Optional[QuantityProvenanceV1]
    reason_codes: tuple[str, ...]
    authority_effect: str = AUTHORITY_EFFECT_NONE
    runtime_effect: str = RUNTIME_EFFECT_NONE
    adapter_compatible: bool = False


# Legacy input adapter for regression compatibility
@dataclass(frozen=True)
class CapitalRiskSizingInputV1:
    decision_id: str
    instrument_id: str
    selected_side: str
    reference_price: Decimal
    protective_stop_price: Optional[Decimal]
    stop_distance: Optional[Decimal]
    account_equity: Decimal
    scope_capital_limit: Decimal
    per_trade_risk_limit: Decimal
    total_capital_limit: Decimal
    daily_loss_remaining_budget: Decimal
    current_reconciled_exposure: Decimal
    maximum_positions: int
    current_open_positions_count: int
    current_open_side: Optional[str]
    configured_quantity_cap: Optional[Decimal]
    leverage_ceiling: Optional[Decimal]
    reconciliation_status: str
    policy_version: str
    config_digest: str
    input_digest: str
    instrument: InstrumentQuantityConstraintsV1
    decision_outcome: str = "enter_long"
    already_committed_capital: Decimal = Decimal("0")
    reconciled_open_position_quantity: Decimal = Decimal("0")
    daily_loss_consumed: Decimal = Decimal("0")


@dataclass(frozen=True)
class CapitalRiskSizingDecisionV1:
    outcome: CapitalRiskSizingOutcome
    final_quantity: Decimal
    selected_side: str
    scope_capital_envelope: ScopeCapitalEnvelopeV1
    pre_sizing_risk: PreSizingRiskAssessmentV1
    canonical_position_sizing: Optional[CanonicalPositionSizingV1]
    post_sizing_risk: Optional[PostSizingRiskAssessmentV1]
    quantity_provenance: Optional[QuantityProvenanceV1]
    reason_codes: tuple[str, ...]
    authority_effect: str = AUTHORITY_EFFECT_NONE
    runtime_effect: str = RUNTIME_EFFECT_NONE
    adapter_compatible: bool = False


def _sha256_hex(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _contract_ref(prefix: str, digest: str) -> str:
    return f"{prefix}::{digest}"


def _normalize_side(side: str) -> str:
    return side.upper()


def _decimal_finite_positive(value: Optional[Decimal], *, allow_zero: bool = False) -> bool:
    if value is None:
        return False
    try:
        if not value.is_finite():
            return False
    except (InvalidOperation, AttributeError):
        return False
    if allow_zero:
        return value >= 0
    return value > 0


def _floor_to_lot(quantity: Decimal, lot_size: Decimal) -> Decimal:
    if lot_size <= 0:
        return Decimal("0")
    return (quantity // lot_size) * lot_size


def _effective_risk_distance(
    *,
    selected_side: str,
    reference_price: Decimal,
    protective_stop_price: Optional[Decimal],
    stop_distance: Optional[Decimal],
) -> tuple[Optional[Decimal], tuple[str, ...]]:
    reasons: list[str] = []
    side = _normalize_side(selected_side)
    if stop_distance is not None:
        if not _decimal_finite_positive(stop_distance):
            reasons.append(REASON_ZERO_RISK_DISTANCE)
            return None, tuple(reasons)
        return stop_distance, tuple(reasons)

    if protective_stop_price is None:
        reasons.append(REASON_INVALID_STOP_PRICE)
        return None, tuple(reasons)

    if not protective_stop_price.is_finite():
        reasons.append(REASON_INVALID_STOP_PRICE)
        return None, tuple(reasons)

    distance = abs(reference_price - protective_stop_price)
    if distance <= 0:
        reasons.append(REASON_ZERO_RISK_DISTANCE)
        return None, tuple(reasons)

    if side == "LONG" and protective_stop_price >= reference_price:
        reasons.append(REASON_INVALID_STOP_PRICE)
        return None, tuple(reasons)
    if side == "SHORT" and protective_stop_price <= reference_price:
        reasons.append(REASON_INVALID_STOP_PRICE)
        return None, tuple(reasons)

    return distance, tuple(reasons)


def _linear_notional_per_unit(reference_price: Decimal, contract_multiplier: Decimal) -> Decimal:
    return reference_price * contract_multiplier


def _linear_projected_stop_loss(
    risk_distance: Decimal,
    contract_multiplier: Decimal,
    quantity: Decimal,
) -> Decimal:
    return risk_distance * contract_multiplier * quantity


def _linear_projected_notional(
    reference_price: Decimal,
    contract_multiplier: Decimal,
    quantity: Decimal,
) -> Decimal:
    return reference_price * contract_multiplier * quantity


def _policy_digest(policy: CapitalRiskSizingPolicyV1) -> str:
    return _sha256_hex(
        {
            "policy_version": policy.policy_version,
            "total_capital_limit_usd": str(policy.total_capital_limit_usd),
            "order_limit_usd": str(policy.order_limit_usd),
            "daily_loss_limit_usd": str(policy.daily_loss_limit_usd),
            "max_positions": policy.max_positions,
        }
    )


def _is_entry_outcome(decision_outcome: str) -> bool:
    return decision_outcome.lower() in _ENTRY_OUTCOMES


def _is_reduce_only_outcome(decision_outcome: str) -> bool:
    return decision_outcome.lower() in _REDUCE_ONLY_OUTCOMES


def _outcome_side_consistent(decision_outcome: str, selected_side: str) -> bool:
    outcome = decision_outcome.lower()
    side = _normalize_side(selected_side)
    if outcome == "enter_long":
        return side == "LONG"
    if outcome == "enter_short":
        return side == "SHORT"
    return True


def _validate_context_and_evidence(
    evidence: CanonicalTradingDecisionEvidenceV1,
    context: CapitalRiskSizingContextV1,
    policy: CapitalRiskSizingPolicyV1,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if not evidence.decision_id:
        reasons.append(REASON_INVALID_DECISION)

    side = _normalize_side(evidence.selected_side)
    if side not in {"LONG", "SHORT"}:
        reasons.append(REASON_INVALID_DIRECTION)

    if context.reconciliation_status not in _ALLOWED_RECONCILIATION:
        reasons.append(REASON_RECONCILIATION_REQUIRED)

    instrument = context.instrument
    if not instrument.instrument_metadata_version:
        reasons.append(REASON_MISSING_INSTRUMENT_METADATA)

    market_type = instrument.market_type.lower()
    if market_type in _FORBIDDEN_MARKET_TYPES or market_type != "futures":
        reasons.append(REASON_NON_FUTURES_INSTRUMENT)

    instrument_lower = evidence.instrument_id.lower()
    if any(marker in instrument_lower for marker in _FORBIDDEN_INSTRUMENT_MARKERS):
        reasons.append(REASON_BITCOIN_SPECIFIC_DIRECTION)

    if instrument.contract_kind not in _ALLOWED_CONTRACT_KINDS:
        reasons.append(REASON_UNSUPPORTED_CONTRACT_KIND)

    financial_checks = (
        context.account_equity,
        context.already_committed_capital,
        context.current_reconciled_exposure,
        context.reconciled_open_position_quantity,
        context.reference_price,
        policy.total_capital_limit_usd,
        policy.order_limit_usd,
        policy.daily_loss_limit_usd,
    )
    for value in financial_checks:
        if value is None:
            reasons.append(REASON_MISSING_CAPITAL_INPUT)
        elif not value.is_finite():
            reasons.append(REASON_NON_FINITE_INPUT)
        elif value < 0:
            reasons.append(REASON_INVALID_CAPITAL_INPUT)

    if not _decimal_finite_positive(context.reference_price):
        reasons.append(REASON_INVALID_REFERENCE_PRICE)

    if not _decimal_finite_positive(instrument.contract_multiplier):
        reasons.append(REASON_INVALID_CONTRACT_MULTIPLIER)

    if not _decimal_finite_positive(instrument.lot_size):
        reasons.append(REASON_INVALID_QUANTITY_STEP)

    if not _decimal_finite_positive(instrument.minimum_quantity):
        reasons.append(REASON_MISSING_INSTRUMENT_METADATA)

    if context.account_equity <= 0 or policy.total_capital_limit_usd <= 0:
        reasons.append(REASON_INVALID_CAPITAL_INPUT)

    daily_remaining = policy.daily_loss_limit_usd - context.daily_loss_consumed
    if daily_remaining <= 0:
        reasons.append(REASON_DAILY_LOSS_BUDGET_EXHAUSTED)

    if policy.order_limit_usd <= 0:
        reasons.append(REASON_TRADE_RISK_BUDGET_EXHAUSTED)

    if policy.max_positions <= 0:
        reasons.append(REASON_INVALID_CAPITAL_INPUT)

    outcome = evidence.decision_outcome.lower()
    if outcome not in _ENTRY_OUTCOMES | _REDUCE_ONLY_OUTCOMES:
        reasons.append(REASON_NON_ENTRY_OUTCOME)

    if _is_entry_outcome(outcome):
        if context.current_open_positions_count >= policy.max_positions:
            reasons.append(REASON_MAX_POSITIONS_REACHED)
        if (
            context.current_open_side is not None
            and _normalize_side(context.current_open_side) in {"LONG", "SHORT"}
            and context.reconciled_open_position_quantity > 0
            and _normalize_side(context.current_open_side) != side
        ):
            reasons.append(REASON_OPPOSITE_EXPOSURE_PRESENT)
            reasons.append(REASON_POSITION_FLIP_FORBIDDEN)

    if _is_reduce_only_outcome(outcome):
        if context.reconciled_open_position_quantity <= 0:
            reasons.append(REASON_NO_OPEN_POSITION_FOR_REDUCE)
        if context.reconciliation_status.lower() not in {"reconciled"}:
            reasons.append(REASON_STALE_POSITION_STATE)

    if not _outcome_side_consistent(evidence.decision_outcome, evidence.selected_side):
        reasons.append(REASON_INVALID_DIRECTION)

    if context.config_digest == "" or evidence.input_digest == "" or policy.policy_version == "":
        reasons.append(REASON_MISSING_CAPITAL_INPUT)

    return tuple(dict.fromkeys(reasons))


def _build_scope_capital_envelope_v1(
    evidence: CanonicalTradingDecisionEvidenceV1,
    context: CapitalRiskSizingContextV1,
    policy: CapitalRiskSizingPolicyV1,
) -> ScopeCapitalEnvelopeV1:
    available = context.account_equity - context.already_committed_capital
    remaining = min(
        available,
        policy.total_capital_limit_usd - context.current_reconciled_exposure,
    )
    remaining = max(remaining, Decimal("0"))
    per_order = context.order_notional_cap or policy.order_limit_usd
    daily_remaining = max(policy.daily_loss_limit_usd - context.daily_loss_consumed, Decimal("0"))

    reasons: list[str] = []
    status = EnvelopeStatus.PASS
    if available <= 0 or remaining <= 0:
        status = EnvelopeStatus.BLOCK
        reasons.append(REASON_INVALID_CAPITAL_INPUT)
    elif remaining < per_order:
        status = EnvelopeStatus.REDUCE
    if daily_remaining <= 0:
        status = EnvelopeStatus.BLOCK
        reasons.append(REASON_DAILY_LOSS_BUDGET_EXHAUSTED)
    if context.current_open_positions_count >= policy.max_positions and _is_entry_outcome(
        evidence.decision_outcome
    ):
        status = EnvelopeStatus.BLOCK
        reasons.append(REASON_MAX_POSITIONS_REACHED)

    return ScopeCapitalEnvelopeV1(
        instrument_id=evidence.instrument_id,
        decision_id=evidence.decision_id,
        policy_version=policy.policy_version,
        total_capital_limit=policy.total_capital_limit_usd,
        available_capital=available,
        already_committed_capital=context.already_committed_capital,
        remaining_capital=remaining,
        per_order_cap=per_order,
        daily_loss_state={
            "limit_usd": str(policy.daily_loss_limit_usd),
            "consumed_usd": str(context.daily_loss_consumed),
            "remaining_usd": str(daily_remaining),
        },
        position_slot_state={
            "max_positions": str(policy.max_positions),
            "open_count": str(context.current_open_positions_count),
        },
        status=status,
        reason_codes=tuple(dict.fromkeys(reasons)),
        input_digest=evidence.input_digest,
    )


def _blocked_chain(
    *,
    evidence: CanonicalTradingDecisionEvidenceV1,
    context: CapitalRiskSizingContextV1,
    policy: CapitalRiskSizingPolicyV1,
    reason_codes: tuple[str, ...],
    envelope: Optional[ScopeCapitalEnvelopeV1] = None,
    pre_sizing: Optional[PreSizingRiskAssessmentV1] = None,
) -> CapitalRiskSizingChainResultV1:
    env = envelope or _build_scope_capital_envelope_v1(evidence, context, policy)
    side = _normalize_side(evidence.selected_side)
    pre = pre_sizing or PreSizingRiskAssessmentV1(
        decision_id=evidence.decision_id,
        side=side,
        reference_price=context.reference_price,
        stop_or_risk_distance=Decimal("0"),
        maximum_loss_budget=Decimal("0"),
        capital_cap_quantity=Decimal("0"),
        loss_budget_quantity=Decimal("0"),
        exposure_cap_quantity=Decimal("0"),
        candidate_quantity_upper_bound=Decimal("0"),
        status=PreSizingRiskStatus.BLOCK,
        reason_codes=reason_codes,
        input_digest=evidence.input_digest,
    )
    return CapitalRiskSizingChainResultV1(
        outcome=CapitalRiskSizingOutcome.BLOCKED,
        final_quantity=Decimal("0"),
        scope_capital_envelope=env,
        pre_sizing_risk=pre,
        canonical_position_sizing=None,
        post_sizing_risk=None,
        quantity_provenance=None,
        reason_codes=reason_codes,
    )


def evaluate_quantity_chain_v1(
    evidence: CanonicalTradingDecisionEvidenceV1,
    context: CapitalRiskSizingContextV1,
    policy: CapitalRiskSizingPolicyV1,
) -> CapitalRiskSizingChainResultV1:
    """Evaluate the offline capital/risk/sizing quantity chain from decision evidence."""

    validation = _validate_context_and_evidence(evidence, context, policy)
    if validation:
        return _blocked_chain(
            evidence=evidence,
            context=context,
            policy=policy,
            reason_codes=validation,
        )

    envelope = _build_scope_capital_envelope_v1(evidence, context, policy)
    if envelope.status is EnvelopeStatus.BLOCK:
        return _blocked_chain(
            evidence=evidence,
            context=context,
            policy=policy,
            reason_codes=envelope.reason_codes or (REASON_INVALID_CAPITAL_INPUT,),
            envelope=envelope,
        )

    side = _normalize_side(evidence.selected_side)
    instrument = context.instrument
    risk_distance, stop_reasons = _effective_risk_distance(
        selected_side=side,
        reference_price=context.reference_price,
        protective_stop_price=context.protective_stop_price,
        stop_distance=context.stop_distance,
    )
    if risk_distance is None:
        return _blocked_chain(
            evidence=evidence,
            context=context,
            policy=policy,
            reason_codes=stop_reasons,
            envelope=envelope,
        )

    daily_remaining = max(policy.daily_loss_limit_usd - context.daily_loss_consumed, Decimal("0"))
    per_trade_risk = context.per_trade_risk_cap or policy.order_limit_usd
    max_loss_budget = min(per_trade_risk, daily_remaining, envelope.remaining_capital)
    if max_loss_budget <= 0:
        return _blocked_chain(
            evidence=evidence,
            context=context,
            policy=policy,
            reason_codes=(REASON_TRADE_RISK_BUDGET_EXHAUSTED,),
            envelope=envelope,
        )

    multiplier = instrument.contract_multiplier
    risk_per_unit = risk_distance * multiplier
    notional_per_unit = _linear_notional_per_unit(context.reference_price, multiplier)
    if risk_per_unit <= 0 or notional_per_unit <= 0:
        return _blocked_chain(
            evidence=evidence,
            context=context,
            policy=policy,
            reason_codes=(REASON_ZERO_RISK_DISTANCE,),
            envelope=envelope,
        )

    loss_budget_quantity = max_loss_budget / risk_per_unit
    scope_capital_for_sizing = min(envelope.remaining_capital, envelope.per_order_cap)
    capital_cap_quantity = scope_capital_for_sizing / notional_per_unit
    exposure_capacity = max(
        policy.total_capital_limit_usd - context.current_reconciled_exposure,
        Decimal("0"),
    )
    exposure_cap_quantity = exposure_capacity / notional_per_unit

    cap_entries: list[tuple[BindingCapKind, Decimal]] = [
        (BindingCapKind.RISK, loss_budget_quantity),
        (BindingCapKind.CAPITAL, capital_cap_quantity),
        (BindingCapKind.EXPOSURE, exposure_cap_quantity),
    ]
    if context.configured_quantity_cap is not None and context.configured_quantity_cap > 0:
        cap_entries.append((BindingCapKind.VENUE, context.configured_quantity_cap))
    if instrument.maximum_quantity is not None and instrument.maximum_quantity > 0:
        cap_entries.append((BindingCapKind.CONFIGURED, instrument.maximum_quantity))

    candidate_upper = min(qty for _, qty in cap_entries)
    pre_status = PreSizingRiskStatus.PASS
    pre_reasons: list[str] = list(envelope.reason_codes)
    if envelope.status is EnvelopeStatus.REDUCE:
        pre_status = PreSizingRiskStatus.REDUCE
    if max_loss_budget < per_trade_risk:
        pre_status = PreSizingRiskStatus.REDUCE
        pre_reasons.append(REASON_DAILY_LOSS_BUDGET_EXHAUSTED)

    pre_sizing = PreSizingRiskAssessmentV1(
        decision_id=evidence.decision_id,
        side=side,
        reference_price=context.reference_price,
        stop_or_risk_distance=risk_distance,
        maximum_loss_budget=max_loss_budget,
        capital_cap_quantity=capital_cap_quantity,
        loss_budget_quantity=loss_budget_quantity,
        exposure_cap_quantity=exposure_cap_quantity,
        candidate_quantity_upper_bound=candidate_upper,
        status=pre_status,
        reason_codes=tuple(dict.fromkeys(pre_reasons)),
        input_digest=evidence.input_digest,
    )

    raw_quantity = candidate_upper
    bounded_before_rounding = candidate_upper
    rounded_quantity = _floor_to_lot(bounded_before_rounding, instrument.lot_size)
    sizing_reasons: list[str] = []
    quantity_status = QuantityStatus.PASS
    if rounded_quantity < bounded_before_rounding:
        quantity_status = QuantityStatus.ROUNDED_DOWN
        sizing_reasons.append(REASON_ROUNDED_DOWN)

    if _is_reduce_only_outcome(evidence.decision_outcome):
        open_qty = context.reconciled_open_position_quantity
        if rounded_quantity > open_qty:
            rounded_quantity = _floor_to_lot(open_qty, instrument.lot_size)
            sizing_reasons.append(REASON_REDUCE_EXCEEDS_OPEN_POSITION)
            quantity_status = QuantityStatus.ROUNDED_DOWN
        if rounded_quantity <= 0:
            return _blocked_chain(
                evidence=evidence,
                context=context,
                policy=policy,
                reason_codes=(REASON_NO_OPEN_POSITION_FOR_REDUCE,),
                envelope=envelope,
                pre_sizing=pre_sizing,
            )

    if rounded_quantity < instrument.minimum_quantity:
        return _blocked_chain(
            evidence=evidence,
            context=context,
            policy=policy,
            reason_codes=tuple(dict.fromkeys((*sizing_reasons, REASON_BELOW_MIN_QUANTITY))),
            envelope=envelope,
            pre_sizing=pre_sizing,
        )

    resulting_notional = _linear_projected_notional(
        context.reference_price, multiplier, rounded_quantity
    )
    if instrument.minimum_notional is not None and resulting_notional < instrument.minimum_notional:
        return _blocked_chain(
            evidence=evidence,
            context=context,
            policy=policy,
            reason_codes=tuple(dict.fromkeys((*sizing_reasons, REASON_BELOW_MIN_NOTIONAL))),
            envelope=envelope,
            pre_sizing=pre_sizing,
        )

    if instrument.maximum_quantity is not None and rounded_quantity > instrument.maximum_quantity:
        return _blocked_chain(
            evidence=evidence,
            context=context,
            policy=policy,
            reason_codes=tuple(dict.fromkeys((*sizing_reasons, REASON_ABOVE_MAX_QUANTITY))),
            envelope=envelope,
            pre_sizing=pre_sizing,
        )

    pol_digest = _policy_digest(policy)
    canonical_sizing = CanonicalPositionSizingV1(
        decision_id=evidence.decision_id,
        instrument_id=evidence.instrument_id,
        side=side,
        raw_quantity=raw_quantity,
        bounded_quantity_before_rounding=bounded_before_rounding,
        lot_size=instrument.lot_size,
        rounded_quantity=rounded_quantity,
        reference_price=context.reference_price,
        resulting_notional=resulting_notional,
        quantity_status=quantity_status,
        reason_codes=tuple(dict.fromkeys(sizing_reasons)) or (REASON_PASS,),
        policy_digest=pol_digest,
        input_digest=evidence.input_digest,
    )

    proposed_quantity = rounded_quantity
    final_allowed = proposed_quantity
    resulting_max_loss = _linear_projected_stop_loss(risk_distance, multiplier, final_allowed)
    exposure_after = context.current_reconciled_exposure + resulting_notional
    slot_after = context.current_open_positions_count
    if (
        _is_entry_outcome(evidence.decision_outcome)
        and context.reconciled_open_position_quantity <= 0
    ):
        slot_after = min(context.current_open_positions_count + 1, policy.max_positions)

    post_reasons: list[str] = list(sizing_reasons)
    post_status = PostSizingRiskStatus.PASS
    if quantity_status is QuantityStatus.ROUNDED_DOWN:
        post_status = PostSizingRiskStatus.REDUCE

    if resulting_max_loss > max_loss_budget:
        return _blocked_chain(
            evidence=evidence,
            context=context,
            policy=policy,
            reason_codes=tuple(dict.fromkeys((*post_reasons, REASON_POST_SIZING_RISK_FAILED))),
            envelope=envelope,
            pre_sizing=pre_sizing,
        )
    if resulting_notional > envelope.per_order_cap:
        return _blocked_chain(
            evidence=evidence,
            context=context,
            policy=policy,
            reason_codes=tuple(dict.fromkeys((*post_reasons, REASON_POST_SIZING_RISK_FAILED))),
            envelope=envelope,
            pre_sizing=pre_sizing,
        )
    if exposure_after > policy.total_capital_limit_usd:
        return _blocked_chain(
            evidence=evidence,
            context=context,
            policy=policy,
            reason_codes=tuple(dict.fromkeys((*post_reasons, REASON_POST_SIZING_RISK_FAILED))),
            envelope=envelope,
            pre_sizing=pre_sizing,
        )
    if resulting_max_loss > daily_remaining:
        return _blocked_chain(
            evidence=evidence,
            context=context,
            policy=policy,
            reason_codes=tuple(dict.fromkeys((*post_reasons, REASON_POST_SIZING_RISK_FAILED))),
            envelope=envelope,
            pre_sizing=pre_sizing,
        )

    post_sizing = PostSizingRiskAssessmentV1(
        proposed_quantity=proposed_quantity,
        final_allowed_quantity=final_allowed,
        resulting_notional=resulting_notional,
        resulting_max_loss=resulting_max_loss,
        exposure_after=exposure_after,
        slot_usage_after=slot_after,
        status=post_status,
        reason_codes=tuple(dict.fromkeys(post_reasons)) or (REASON_PASS,),
        input_digest=evidence.input_digest,
    )

    env_ref = _contract_ref(
        "ScopeCapitalEnvelopeV1", _sha256_hex({"decision_id": evidence.decision_id})
    )
    pre_ref = _contract_ref(
        "PreSizingRiskAssessmentV1", _sha256_hex({"bound": str(candidate_upper)})
    )
    sizing_ref = _contract_ref("CanonicalPositionSizingV1", pol_digest)
    post_ref = _contract_ref("PostSizingRiskAssessmentV1", _sha256_hex({"qty": str(final_allowed)}))

    final_status = FinalQuantityStatus.PASS
    if post_status is PostSizingRiskStatus.REDUCE:
        final_status = FinalQuantityStatus.REDUCE

    quantity_provenance = QuantityProvenanceV1(
        decision_id=evidence.decision_id,
        source_contract_refs=(
            "CanonicalTradingDecisionEvidenceV1",
            "CapitalRiskSizingContextV1",
            "CapitalRiskSizingPolicyV1",
        ),
        capital_envelope_ref=env_ref,
        pre_sizing_risk_ref=pre_ref,
        sizing_ref=sizing_ref,
        post_sizing_risk_ref=post_ref,
        instrument_metadata_ref=instrument.instrument_metadata_version,
        policy_version=policy.policy_version,
        config_digest=context.config_digest,
        implementation_digest=IMPLEMENTATION_DIGEST,
        final_quantity=final_allowed,
        final_quantity_status=final_status,
    )

    return CapitalRiskSizingChainResultV1(
        outcome=CapitalRiskSizingOutcome.PASS,
        final_quantity=final_allowed,
        scope_capital_envelope=envelope,
        pre_sizing_risk=pre_sizing,
        canonical_position_sizing=canonical_sizing,
        post_sizing_risk=post_sizing,
        quantity_provenance=quantity_provenance,
        reason_codes=tuple(dict.fromkeys((*post_sizing.reason_codes, REASON_PASS))),
    )


def evaluate_capital_risk_sizing_v1(inp: CapitalRiskSizingInputV1) -> CapitalRiskSizingDecisionV1:
    """Legacy adapter: evaluate chain from flat input bundle."""

    instrument = inp.instrument
    if not hasattr(instrument, "lot_size"):
        instrument = InstrumentQuantityConstraintsV1(
            instrument_id=instrument.instrument_id,
            market_type=instrument.market_type,
            contract_kind=instrument.contract_kind,
            contract_multiplier=instrument.contract_multiplier,
            lot_size=getattr(instrument, "quantity_step", instrument.lot_size),
            minimum_quantity=instrument.minimum_quantity,
            maximum_quantity=instrument.maximum_quantity,
            minimum_notional=instrument.minimum_notional,
            tick_size=getattr(instrument, "tick_size", None),
            instrument_metadata_version=instrument.instrument_metadata_version,
            price_precision=getattr(instrument, "price_precision", None),
        )

    policy = CapitalRiskSizingPolicyV1(
        policy_version=inp.policy_version,
        total_capital_limit_usd=inp.total_capital_limit,
        order_limit_usd=inp.per_trade_risk_limit,
        daily_loss_limit_usd=inp.daily_loss_remaining_budget + inp.daily_loss_consumed,
        max_positions=inp.maximum_positions,
    )
    evidence = CanonicalTradingDecisionEvidenceV1(
        decision_id=inp.decision_id,
        replay_id="legacy-replay",
        instrument_id=inp.instrument_id,
        trading_epoch=0,
        market_context_ref="legacy",
        scope_initialization_ref="legacy",
        scope_event_ref="legacy",
        bull_assessment_ref="legacy",
        bear_assessment_ref="legacy",
        state_switch_ref="legacy",
        bull_survival_ref="legacy",
        bear_survival_ref="legacy",
        bull_suitability_ref="legacy",
        bear_suitability_ref="legacy",
        composition_result_ref="legacy",
        entry_exit_policy_ref="legacy",
        current_scope_ref="legacy",
        next_scope_ref="legacy",
        previous_direction_state="neutral",
        next_direction_state="neutral",
        selected_side=inp.selected_side,
        selected_strategy_ref="legacy",
        decision_outcome=inp.decision_outcome,
        entry_or_exit_policy_ref="legacy",
        reason_codes=(),
        decision_precedence_trace=(),
        component_versions={},
        policy_versions={inp.policy_version: inp.policy_version},
        config_digest=inp.config_digest,
        implementation_digest=IMPLEMENTATION_DIGEST,
        input_digest=inp.input_digest,
        semantic_digest="",
    )
    context = CapitalRiskSizingContextV1(
        reference_price=inp.reference_price,
        protective_stop_price=inp.protective_stop_price,
        stop_distance=inp.stop_distance,
        account_equity=inp.account_equity,
        already_committed_capital=inp.already_committed_capital,
        daily_loss_consumed=inp.daily_loss_consumed,
        current_reconciled_exposure=inp.current_reconciled_exposure,
        reconciled_open_position_quantity=inp.reconciled_open_position_quantity,
        current_open_positions_count=inp.current_open_positions_count,
        current_open_side=inp.current_open_side,
        reconciliation_status=inp.reconciliation_status,
        configured_quantity_cap=inp.configured_quantity_cap,
        leverage_ceiling=inp.leverage_ceiling,
        instrument=instrument,
        config_digest=inp.config_digest,
        order_notional_cap=inp.scope_capital_limit,
        per_trade_risk_cap=inp.per_trade_risk_limit,
    )
    chain = evaluate_quantity_chain_v1(evidence, context, policy)
    return CapitalRiskSizingDecisionV1(
        outcome=chain.outcome,
        final_quantity=chain.final_quantity,
        selected_side=_normalize_side(inp.selected_side),
        scope_capital_envelope=chain.scope_capital_envelope,
        pre_sizing_risk=chain.pre_sizing_risk,
        canonical_position_sizing=chain.canonical_position_sizing,
        post_sizing_risk=chain.post_sizing_risk,
        quantity_provenance=chain.quantity_provenance,
        reason_codes=chain.reason_codes,
    )


def export_bypass_scan_v1(*, repo_root: Optional[Path] = None) -> dict[str, Any]:
    """Deterministic bypass guard export for STEP29P offline boundary."""

    root = repo_root or Path(__file__).resolve().parents[2]
    module_path = root / "src" / "governance" / "capital_risk_sizing_v1.py"
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    runtime_hits = [
        mod
        for mod in imported_modules
        if any(mod.startswith(prefix) for prefix in _FORBIDDEN_RUNTIME_IMPORT_PREFIXES)
    ]

    legacy_sizer = root / "src" / "risk" / "position_sizer.py"
    legacy_present = legacy_sizer.is_file()

    return {
        "DIRECT_DECISION_TO_QUANTITY_PATH_BLOCKED": True,
        "DIRECT_SIGNAL_TO_QUANTITY_PATH_BLOCKED": True,
        "IMPLICIT_DEFAULT_QUANTITY_BLOCKED": True,
        "RISK_INCREASING_ROUNDING_BLOCKED": True,
        "QUANTITY_WITHOUT_PROVENANCE_BLOCKED": True,
        "DIRECT_QUANTITY_TO_ADAPTER_PATH_BLOCKED": True,
        "CANONICAL_OWNER": "src.governance.capital_risk_sizing_v1",
        "LEGACY_POSITION_SIZER_PRESENT": legacy_present,
        "LEGACY_POSITION_SIZER_CLASSIFICATION": "DEPRECATE_LEGACY_PATH",
        "FORBIDDEN_RUNTIME_IMPORTS_IN_OWNER": runtime_hits,
        "AUTHORITY_EFFECT": AUTHORITY_EFFECT_NONE,
        "RUNTIME_EFFECT": RUNTIME_EFFECT_NONE,
        "ADAPTER_COMPATIBLE": False,
    }


def capital_risk_sizing_schema_v1() -> dict[str, Any]:
    """Return the offline contract schema and invariants."""

    return {
        "contract_name": CONTRACT_NAME,
        "contract_version": CONTRACT_VERSION,
        "schema_version": SCHEMA_VERSION,
        "package_marker": PACKAGE_MARKER,
        "implementation_digest": IMPLEMENTATION_DIGEST,
        "invariants": {
            "futures_only": FUTURES_ONLY,
            "bitcoin_direction_allowed": BITCOIN_DIRECTION_ALLOWED,
            "spot_allowed": SPOT_ALLOWED,
            "synthetic_spot_allowed": SYNTHETIC_SPOT_ALLOWED,
            "rounding_must_not_increase_risk": True,
            "risk_layer_can_only_reduce_or_block": True,
            "no_implicit_capital_default": True,
            "no_implicit_leverage_default": True,
            "adapter_compatible": False,
            "authority_effect": AUTHORITY_EFFECT_NONE,
            "runtime_effect": RUNTIME_EFFECT_NONE,
        },
        "quantity_chain": [
            "CanonicalTradingDecisionEvidenceV1",
            "ScopeCapitalEnvelopeV1",
            "PreSizingRiskAssessmentV1",
            "CanonicalPositionSizingV1",
            "PostSizingRiskAssessmentV1",
            "QuantityProvenanceV1",
        ],
        "reason_codes": sorted(
            {
                REASON_INVALID_DECISION,
                REASON_INVALID_DIRECTION,
                REASON_MISSING_CAPITAL_INPUT,
                REASON_INVALID_CAPITAL_INPUT,
                REASON_DAILY_LOSS_BUDGET_EXHAUSTED,
                REASON_TRADE_RISK_BUDGET_EXHAUSTED,
                REASON_INVALID_REFERENCE_PRICE,
                REASON_INVALID_STOP_PRICE,
                REASON_ZERO_RISK_DISTANCE,
                REASON_INVALID_CONTRACT_MULTIPLIER,
                REASON_INVALID_QUANTITY_STEP,
                REASON_MISSING_INSTRUMENT_METADATA,
                REASON_MAX_POSITIONS_REACHED,
                REASON_OPPOSITE_EXPOSURE_PRESENT,
                REASON_RECONCILIATION_REQUIRED,
                REASON_BELOW_MIN_QUANTITY,
                REASON_BELOW_MIN_NOTIONAL,
                REASON_ABOVE_MAX_QUANTITY,
                REASON_CAPITAL_CAP_BINDING,
                REASON_RISK_CAP_BINDING,
                REASON_EXPOSURE_CAP_BINDING,
                REASON_VENUE_CAP_BINDING,
                REASON_ROUNDED_DOWN,
                REASON_POST_SIZING_RISK_FAILED,
                REASON_NON_FINITE_INPUT,
                REASON_NON_FUTURES_INSTRUMENT,
                REASON_BITCOIN_SPECIFIC_DIRECTION,
                REASON_UNSUPPORTED_CONTRACT_KIND,
                REASON_NON_ENTRY_OUTCOME,
                REASON_REDUCE_EXCEEDS_OPEN_POSITION,
                REASON_NO_OPEN_POSITION_FOR_REDUCE,
                REASON_POSITION_FLIP_FORBIDDEN,
                REASON_STALE_POSITION_STATE,
                REASON_PASS,
            }
        ),
    }
