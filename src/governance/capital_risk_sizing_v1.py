"""
Offline Capital Risk Sizing Mathematics v1 (RUNBOOK STEP 29P).

Pure, deterministic, fail-closed monotone quantity chain:
canonical trading decision → scope capital envelope → pre-sizing risk →
canonical position sizing → instrument constraint normalization →
post-sizing risk → quantity provenance.

No adapter compatibility, submission, runtime authority, order intent, or
execution permission.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Any, Mapping, Optional

CONTRACT_NAME = "capital_risk_sizing_v1"
CONTRACT_VERSION = "v1"
SCHEMA_VERSION = "capital_risk_sizing_schema_v1"
IMPLEMENTATION_DIGEST = "capital_risk_sizing_v1_offline_slice"

PACKAGE_MARKER = "CAPITAL_RISK_SIZING_V1=true"
FUTURES_ONLY = True
BITCOIN_DIRECTION_ALLOWED = False
SPOT_ALLOWED = False

AUTHORITY_EFFECT_NONE = "NONE"
RUNTIME_EFFECT_NONE = "NONE"

_FORBIDDEN_INSTRUMENT_MARKERS = frozenset({"btc", "xbt", "bitcoin"})
_FORBIDDEN_MARKET_TYPES = frozenset({"spot", "synthetic_spot", "synthetic-spot"})
_ALLOWED_SIDES = frozenset({"LONG", "SHORT"})
_ALLOWED_RECONCILIATION = frozenset({"RECONCILED"})
_ALLOWED_CONTRACT_KINDS = frozenset({"LINEAR"})

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
REASON_PASS = "PASS"


class SelectedSide(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"


class FuturesContractKind(str, Enum):
    LINEAR = "LINEAR"
    INVERSE = "INVERSE"


class PreSizingRiskOutcome(str, Enum):
    PASS = "PASS"
    REDUCE_CAP = "REDUCE_CAP"
    BLOCK = "BLOCK"


class PostSizingRiskOutcome(str, Enum):
    PASS = "PASS"
    REDUCED = "REDUCED"
    BLOCKED = "BLOCKED"


class CapitalRiskSizingOutcome(str, Enum):
    PASS = "PASS"
    BLOCKED = "BLOCKED"


class BindingCapKind(str, Enum):
    RISK = "RISK"
    CAPITAL = "CAPITAL"
    EXPOSURE = "EXPOSURE"
    VENUE = "VENUE"
    CONFIGURED = "CONFIGURED"


@dataclass(frozen=True)
class InstrumentQuantityConstraintsV1:
    instrument_id: str
    market_type: str
    contract_kind: str
    contract_multiplier: Decimal
    quantity_step: Decimal
    minimum_quantity: Decimal
    maximum_quantity: Optional[Decimal]
    minimum_notional: Optional[Decimal]
    instrument_metadata_version: str
    price_precision: Optional[int] = None


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


@dataclass(frozen=True)
class CapitalEnvelopeV1:
    scope_capital_limit: Decimal
    account_equity: Decimal
    total_capital_limit: Decimal
    within_envelope: bool
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class PreSizingRiskResultV1:
    outcome: PreSizingRiskOutcome
    effective_trade_risk_budget: Decimal
    effective_scope_capital_limit: Decimal
    effective_total_capital_limit: Decimal
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class CanonicalSizingResultV1:
    risk_per_unit: Decimal
    raw_risk_quantity: Decimal
    capital_quantity_cap: Decimal
    exposure_quantity_cap: Decimal
    candidate_quantity: Decimal
    binding_cap: BindingCapKind
    applied_caps: tuple[tuple[str, Decimal], ...]


@dataclass(frozen=True)
class QuantityProvenanceV1:
    input_candidate_quantity: Decimal
    applied_upper_caps: tuple[tuple[str, Decimal], ...]
    binding_cap: str
    risk_per_unit: Decimal
    pre_round_quantity: Decimal
    quantity_step: Decimal
    rounded_quantity: Decimal
    final_quantity: Decimal
    projected_stop_loss: Decimal
    projected_notional: Decimal
    projected_exposure: Decimal
    projected_margin: Optional[Decimal]
    policy_version: str
    instrument_metadata_ref: str
    decision_ref: str
    reason_codes: tuple[str, ...]
    config_digest: str
    implementation_digest: str
    input_digest: str
    output_digest: str
    execution_eligible: bool = False
    adapter_compatible: bool = False
    order_intent_bound: bool = False
    authority_effect: str = AUTHORITY_EFFECT_NONE
    runtime_effect: str = RUNTIME_EFFECT_NONE


@dataclass(frozen=True)
class PostSizingRiskResultV1:
    outcome: PostSizingRiskOutcome
    projected_stop_loss: Decimal
    projected_notional: Decimal
    projected_exposure: Decimal
    projected_daily_loss_impact: Decimal
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class CapitalRiskSizingDecisionV1:
    outcome: CapitalRiskSizingOutcome
    final_quantity: Decimal
    selected_side: str
    capital_envelope: CapitalEnvelopeV1
    pre_sizing_risk: PreSizingRiskResultV1
    canonical_sizing: Optional[CanonicalSizingResultV1]
    post_sizing_risk: Optional[PostSizingRiskResultV1]
    quantity_provenance: Optional[QuantityProvenanceV1]
    reason_codes: tuple[str, ...]
    execution_eligible: bool = False
    adapter_compatible: bool = False
    order_intent_bound: bool = False
    authority_effect: str = AUTHORITY_EFFECT_NONE
    runtime_effect: str = RUNTIME_EFFECT_NONE


def _sha256_hex(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


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


def _decimal_finite_non_negative(value: Optional[Decimal]) -> bool:
    if value is None:
        return False
    try:
        return value.is_finite() and value >= 0
    except (InvalidOperation, AttributeError):
        return False


def _floor_to_quantity_step(quantity: Decimal, step: Decimal) -> Decimal:
    if step <= 0:
        return Decimal("0")
    return (quantity // step) * step


def _effective_risk_distance(
    *,
    selected_side: str,
    reference_price: Decimal,
    protective_stop_price: Optional[Decimal],
    stop_distance: Optional[Decimal],
) -> tuple[Optional[Decimal], tuple[str, ...]]:
    reasons: list[str] = []
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

    if selected_side == SelectedSide.LONG.value and protective_stop_price >= reference_price:
        reasons.append(REASON_INVALID_STOP_PRICE)
        return None, tuple(reasons)
    if selected_side == SelectedSide.SHORT.value and protective_stop_price <= reference_price:
        reasons.append(REASON_INVALID_STOP_PRICE)
        return None, tuple(reasons)

    return distance, tuple(reasons)


def _linear_effective_notional_per_unit(
    reference_price: Decimal, contract_multiplier: Decimal
) -> Decimal:
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


def _blocked_decision(
    *,
    inp: CapitalRiskSizingInputV1,
    reason_codes: tuple[str, ...],
    capital_envelope: Optional[CapitalEnvelopeV1] = None,
    pre_sizing: Optional[PreSizingRiskResultV1] = None,
) -> CapitalRiskSizingDecisionV1:
    envelope = capital_envelope or CapitalEnvelopeV1(
        scope_capital_limit=inp.scope_capital_limit,
        account_equity=inp.account_equity,
        total_capital_limit=inp.total_capital_limit,
        within_envelope=False,
        reason_codes=reason_codes,
    )
    pre = pre_sizing or PreSizingRiskResultV1(
        outcome=PreSizingRiskOutcome.BLOCK,
        effective_trade_risk_budget=Decimal("0"),
        effective_scope_capital_limit=inp.scope_capital_limit,
        effective_total_capital_limit=inp.total_capital_limit,
        reason_codes=reason_codes,
    )
    return CapitalRiskSizingDecisionV1(
        outcome=CapitalRiskSizingOutcome.BLOCKED,
        final_quantity=Decimal("0"),
        selected_side=inp.selected_side,
        capital_envelope=envelope,
        pre_sizing_risk=pre,
        canonical_sizing=None,
        post_sizing_risk=None,
        quantity_provenance=None,
        reason_codes=reason_codes,
    )


def _validate_required_inputs(inp: CapitalRiskSizingInputV1) -> tuple[str, ...]:
    reasons: list[str] = []

    if not inp.decision_id:
        reasons.append(REASON_INVALID_DECISION)

    if inp.selected_side not in _ALLOWED_SIDES:
        reasons.append(REASON_INVALID_DIRECTION)

    if inp.reconciliation_status not in _ALLOWED_RECONCILIATION:
        reasons.append(REASON_RECONCILIATION_REQUIRED)

    instrument = inp.instrument
    if instrument is None or not instrument.instrument_metadata_version:
        reasons.append(REASON_MISSING_INSTRUMENT_METADATA)

    market_type = (instrument.market_type if instrument else "").lower()
    if market_type in _FORBIDDEN_MARKET_TYPES or market_type != "futures":
        reasons.append(REASON_NON_FUTURES_INSTRUMENT)

    instrument_lower = inp.instrument_id.lower()
    if any(marker in instrument_lower for marker in _FORBIDDEN_INSTRUMENT_MARKERS):
        reasons.append(REASON_BITCOIN_SPECIFIC_DIRECTION)

    if instrument.contract_kind not in _ALLOWED_CONTRACT_KINDS:
        reasons.append(REASON_UNSUPPORTED_CONTRACT_KIND)

    required_financial = (
        ("account_equity", inp.account_equity),
        ("scope_capital_limit", inp.scope_capital_limit),
        ("per_trade_risk_limit", inp.per_trade_risk_limit),
        ("total_capital_limit", inp.total_capital_limit),
        ("daily_loss_remaining_budget", inp.daily_loss_remaining_budget),
        ("current_reconciled_exposure", inp.current_reconciled_exposure),
        ("reference_price", inp.reference_price),
    )
    for _name, value in required_financial:
        if value is None:
            reasons.append(REASON_MISSING_CAPITAL_INPUT)
            continue
        if not value.is_finite():
            reasons.append(REASON_NON_FINITE_INPUT)
            continue
        if value < 0:
            reasons.append(REASON_INVALID_CAPITAL_INPUT)

    if not _decimal_finite_positive(inp.reference_price):
        reasons.append(REASON_INVALID_REFERENCE_PRICE)

    if not _decimal_finite_positive(instrument.contract_multiplier):
        reasons.append(REASON_INVALID_CONTRACT_MULTIPLIER)

    if not _decimal_finite_positive(instrument.quantity_step):
        reasons.append(REASON_INVALID_QUANTITY_STEP)

    if not _decimal_finite_positive(instrument.minimum_quantity):
        reasons.append(REASON_MISSING_INSTRUMENT_METADATA)

    if instrument.maximum_quantity is not None and instrument.maximum_quantity <= 0:
        reasons.append(REASON_INVALID_CAPITAL_INPUT)

    if inp.account_equity <= 0 or inp.scope_capital_limit <= 0 or inp.total_capital_limit <= 0:
        reasons.append(REASON_INVALID_CAPITAL_INPUT)

    if inp.daily_loss_remaining_budget <= 0:
        reasons.append(REASON_DAILY_LOSS_BUDGET_EXHAUSTED)

    if inp.per_trade_risk_limit <= 0:
        reasons.append(REASON_TRADE_RISK_BUDGET_EXHAUSTED)

    if inp.maximum_positions <= 0:
        reasons.append(REASON_INVALID_CAPITAL_INPUT)

    if inp.current_open_positions_count >= inp.maximum_positions:
        reasons.append(REASON_MAX_POSITIONS_REACHED)

    if (
        inp.current_open_side is not None
        and inp.current_open_side in _ALLOWED_SIDES
        and inp.current_reconciled_exposure > 0
        and inp.current_open_side != inp.selected_side
    ):
        reasons.append(REASON_OPPOSITE_EXPOSURE_PRESENT)

    if inp.config_digest == "" or inp.input_digest == "" or inp.policy_version == "":
        reasons.append(REASON_MISSING_CAPITAL_INPUT)

    return tuple(dict.fromkeys(reasons))


def _build_capital_envelope(inp: CapitalRiskSizingInputV1) -> CapitalEnvelopeV1:
    within = (
        inp.scope_capital_limit <= inp.total_capital_limit
        and inp.account_equity <= inp.total_capital_limit
        and inp.scope_capital_limit > 0
    )
    reasons: list[str] = []
    if not within:
        reasons.append(REASON_INVALID_CAPITAL_INPUT)
    return CapitalEnvelopeV1(
        scope_capital_limit=inp.scope_capital_limit,
        account_equity=inp.account_equity,
        total_capital_limit=inp.total_capital_limit,
        within_envelope=within,
        reason_codes=tuple(reasons),
    )


def _evaluate_pre_sizing_risk(
    inp: CapitalRiskSizingInputV1,
    envelope: CapitalEnvelopeV1,
) -> PreSizingRiskResultV1:
    reasons: list[str] = list(envelope.reason_codes)
    outcome = PreSizingRiskOutcome.PASS

    effective_trade_budget = min(inp.per_trade_risk_limit, inp.daily_loss_remaining_budget)
    if effective_trade_budget <= 0:
        reasons.append(REASON_TRADE_RISK_BUDGET_EXHAUSTED)
        return PreSizingRiskResultV1(
            outcome=PreSizingRiskOutcome.BLOCK,
            effective_trade_risk_budget=Decimal("0"),
            effective_scope_capital_limit=inp.scope_capital_limit,
            effective_total_capital_limit=inp.total_capital_limit,
            reason_codes=tuple(dict.fromkeys(reasons)),
        )

    if effective_trade_budget < inp.per_trade_risk_limit:
        outcome = PreSizingRiskOutcome.REDUCE_CAP
        reasons.append(REASON_DAILY_LOSS_BUDGET_EXHAUSTED)

    effective_scope = min(inp.scope_capital_limit, inp.account_equity)
    if effective_scope < inp.scope_capital_limit:
        outcome = PreSizingRiskOutcome.REDUCE_CAP

    return PreSizingRiskResultV1(
        outcome=outcome,
        effective_trade_risk_budget=effective_trade_budget,
        effective_scope_capital_limit=effective_scope,
        effective_total_capital_limit=inp.total_capital_limit,
        reason_codes=tuple(dict.fromkeys(reasons)),
    )


def _select_binding_cap(caps: list[tuple[BindingCapKind, Decimal]]) -> BindingCapKind:
    minimum = min(caps, key=lambda item: item[1])
    return minimum[0]


def evaluate_capital_risk_sizing_v1(inp: CapitalRiskSizingInputV1) -> CapitalRiskSizingDecisionV1:
    """Evaluate the offline capital/risk/sizing quantity chain."""

    validation_reasons = _validate_required_inputs(inp)
    if validation_reasons:
        return _blocked_decision(inp=inp, reason_codes=validation_reasons)

    instrument = inp.instrument
    risk_distance, stop_reasons = _effective_risk_distance(
        selected_side=inp.selected_side,
        reference_price=inp.reference_price,
        protective_stop_price=inp.protective_stop_price,
        stop_distance=inp.stop_distance,
    )
    if risk_distance is None:
        return _blocked_decision(inp=inp, reason_codes=stop_reasons)

    envelope = _build_capital_envelope(inp)
    if not envelope.within_envelope:
        return _blocked_decision(
            inp=inp,
            reason_codes=envelope.reason_codes,
            capital_envelope=envelope,
        )

    pre_sizing = _evaluate_pre_sizing_risk(inp, envelope)
    if pre_sizing.outcome is PreSizingRiskOutcome.BLOCK:
        return _blocked_decision(
            inp=inp,
            reason_codes=pre_sizing.reason_codes,
            capital_envelope=envelope,
            pre_sizing=pre_sizing,
        )

    multiplier = instrument.contract_multiplier
    risk_per_unit = risk_distance * multiplier
    if risk_per_unit <= 0:
        return _blocked_decision(
            inp=inp,
            reason_codes=(REASON_ZERO_RISK_DISTANCE,),
            capital_envelope=envelope,
            pre_sizing=pre_sizing,
        )

    notional_per_unit = _linear_effective_notional_per_unit(inp.reference_price, multiplier)
    if notional_per_unit <= 0:
        return _blocked_decision(
            inp=inp,
            reason_codes=(REASON_INVALID_REFERENCE_PRICE,),
            capital_envelope=envelope,
            pre_sizing=pre_sizing,
        )

    raw_risk_quantity = pre_sizing.effective_trade_risk_budget / risk_per_unit
    capital_quantity_cap = pre_sizing.effective_scope_capital_limit / notional_per_unit
    remaining_exposure_capacity = max(
        inp.total_capital_limit - inp.current_reconciled_exposure,
        Decimal("0"),
    )
    exposure_quantity_cap = remaining_exposure_capacity / notional_per_unit

    cap_entries: list[tuple[BindingCapKind, Decimal, str]] = [
        (BindingCapKind.RISK, raw_risk_quantity, REASON_RISK_CAP_BINDING),
        (BindingCapKind.CAPITAL, capital_quantity_cap, REASON_CAPITAL_CAP_BINDING),
        (BindingCapKind.EXPOSURE, exposure_quantity_cap, REASON_EXPOSURE_CAP_BINDING),
    ]

    if inp.configured_quantity_cap is not None:
        if inp.configured_quantity_cap.is_finite() and inp.configured_quantity_cap > 0:
            cap_entries.append(
                (BindingCapKind.VENUE, inp.configured_quantity_cap, REASON_VENUE_CAP_BINDING)
            )

    if instrument.maximum_quantity is not None and instrument.maximum_quantity > 0:
        cap_entries.append(
            (BindingCapKind.CONFIGURED, instrument.maximum_quantity, REASON_ABOVE_MAX_QUANTITY)
        )

    candidate_quantity = min(entry[1] for entry in cap_entries)
    binding_cap = _select_binding_cap([(kind, qty) for kind, qty, _ in cap_entries])

    applied_caps = tuple((kind.value, qty) for kind, qty, _ in cap_entries)
    canonical_sizing = CanonicalSizingResultV1(
        risk_per_unit=risk_per_unit,
        raw_risk_quantity=raw_risk_quantity,
        capital_quantity_cap=capital_quantity_cap,
        exposure_quantity_cap=exposure_quantity_cap,
        candidate_quantity=candidate_quantity,
        binding_cap=binding_cap,
        applied_caps=applied_caps,
    )

    rounded_quantity = _floor_to_quantity_step(candidate_quantity, instrument.quantity_step)
    round_reasons: list[str] = []
    if rounded_quantity < candidate_quantity:
        round_reasons.append(REASON_ROUNDED_DOWN)

    if rounded_quantity < instrument.minimum_quantity:
        reasons = tuple(dict.fromkeys((*round_reasons, REASON_BELOW_MIN_QUANTITY)))
        return _blocked_decision(
            inp=inp,
            reason_codes=reasons,
            capital_envelope=envelope,
            pre_sizing=pre_sizing,
        )

    projected_notional = _linear_projected_notional(
        inp.reference_price, multiplier, rounded_quantity
    )
    if instrument.minimum_notional is not None and projected_notional < instrument.minimum_notional:
        reasons = tuple(dict.fromkeys((*round_reasons, REASON_BELOW_MIN_NOTIONAL)))
        return _blocked_decision(
            inp=inp,
            reason_codes=reasons,
            capital_envelope=envelope,
            pre_sizing=pre_sizing,
        )

    if instrument.maximum_quantity is not None and rounded_quantity > instrument.maximum_quantity:
        reasons = tuple(dict.fromkeys((*round_reasons, REASON_ABOVE_MAX_QUANTITY)))
        return _blocked_decision(
            inp=inp,
            reason_codes=reasons,
            capital_envelope=envelope,
            pre_sizing=pre_sizing,
        )

    projected_stop_loss = _linear_projected_stop_loss(risk_distance, multiplier, rounded_quantity)
    projected_exposure = inp.current_reconciled_exposure + projected_notional
    projected_daily_loss_impact = projected_stop_loss

    post_reasons: list[str] = list(round_reasons)
    post_outcome = PostSizingRiskOutcome.PASS

    if projected_stop_loss > pre_sizing.effective_trade_risk_budget:
        post_reasons.append(REASON_POST_SIZING_RISK_FAILED)
        return _blocked_decision(
            inp=inp,
            reason_codes=tuple(dict.fromkeys(post_reasons)),
            capital_envelope=envelope,
            pre_sizing=pre_sizing,
        )

    if projected_notional > pre_sizing.effective_scope_capital_limit:
        post_reasons.append(REASON_POST_SIZING_RISK_FAILED)
        return _blocked_decision(
            inp=inp,
            reason_codes=tuple(dict.fromkeys(post_reasons)),
            capital_envelope=envelope,
            pre_sizing=pre_sizing,
        )

    if projected_exposure > inp.total_capital_limit:
        post_reasons.append(REASON_POST_SIZING_RISK_FAILED)
        return _blocked_decision(
            inp=inp,
            reason_codes=tuple(dict.fromkeys(post_reasons)),
            capital_envelope=envelope,
            pre_sizing=pre_sizing,
        )

    if projected_daily_loss_impact > inp.daily_loss_remaining_budget:
        post_reasons.append(REASON_POST_SIZING_RISK_FAILED)
        return _blocked_decision(
            inp=inp,
            reason_codes=tuple(dict.fromkeys(post_reasons)),
            capital_envelope=envelope,
            pre_sizing=pre_sizing,
        )

    if rounded_quantity < candidate_quantity and post_outcome is PostSizingRiskOutcome.PASS:
        post_outcome = PostSizingRiskOutcome.REDUCED

    projected_margin: Optional[Decimal] = None
    if inp.leverage_ceiling is not None and inp.leverage_ceiling > 0:
        projected_margin = projected_notional / inp.leverage_ceiling

    post_sizing = PostSizingRiskResultV1(
        outcome=post_outcome,
        projected_stop_loss=projected_stop_loss,
        projected_notional=projected_notional,
        projected_exposure=projected_exposure,
        projected_daily_loss_impact=projected_daily_loss_impact,
        reason_codes=tuple(dict.fromkeys(post_reasons)) or (REASON_PASS,),
    )

    provenance_payload = {
        field.name: getattr(post_sizing, field.name)
        for field in fields(PostSizingRiskResultV1)
        if field.name != "reason_codes"
    }
    provenance_payload.update(
        {
            "decision_id": inp.decision_id,
            "instrument_id": inp.instrument_id,
            "selected_side": inp.selected_side,
            "candidate_quantity": str(candidate_quantity),
            "rounded_quantity": str(rounded_quantity),
            "binding_cap": binding_cap.value,
        }
    )
    output_digest = _sha256_hex(provenance_payload)

    quantity_provenance = QuantityProvenanceV1(
        input_candidate_quantity=candidate_quantity,
        applied_upper_caps=applied_caps,
        binding_cap=binding_cap.value,
        risk_per_unit=risk_per_unit,
        pre_round_quantity=candidate_quantity,
        quantity_step=instrument.quantity_step,
        rounded_quantity=rounded_quantity,
        final_quantity=rounded_quantity,
        projected_stop_loss=projected_stop_loss,
        projected_notional=projected_notional,
        projected_exposure=projected_exposure,
        projected_margin=projected_margin,
        policy_version=inp.policy_version,
        instrument_metadata_ref=instrument.instrument_metadata_version,
        decision_ref=inp.decision_id,
        reason_codes=post_sizing.reason_codes,
        config_digest=inp.config_digest,
        implementation_digest=IMPLEMENTATION_DIGEST,
        input_digest=inp.input_digest,
        output_digest=output_digest,
    )

    final_reasons = tuple(dict.fromkeys((*post_sizing.reason_codes, REASON_PASS)))

    return CapitalRiskSizingDecisionV1(
        outcome=CapitalRiskSizingOutcome.PASS,
        final_quantity=rounded_quantity,
        selected_side=inp.selected_side,
        capital_envelope=envelope,
        pre_sizing_risk=pre_sizing,
        canonical_sizing=canonical_sizing,
        post_sizing_risk=post_sizing,
        quantity_provenance=quantity_provenance,
        reason_codes=final_reasons,
    )


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
            "rounding_must_not_increase_risk": True,
            "risk_layer_can_only_reduce_or_block": True,
            "sizing_layer_cannot_select_direction": True,
            "no_implicit_capital_default": True,
            "no_implicit_leverage_default": True,
            "execution_eligible": False,
            "adapter_compatible": False,
            "order_intent_bound": False,
            "authority_effect": AUTHORITY_EFFECT_NONE,
            "runtime_effect": RUNTIME_EFFECT_NONE,
        },
        "quantity_chain": [
            "canonical_trading_decision",
            "scope_capital_envelope",
            "pre_sizing_risk",
            "canonical_position_sizing",
            "instrument_constraint_normalization",
            "post_sizing_risk",
            "quantity_provenance",
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
                REASON_PASS,
            }
        ),
    }
