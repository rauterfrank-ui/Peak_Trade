"""Order-Capability side/price/quantity rules contract (v1).

Pure offline evaluation of side, limit_price, quantity, tick/step alignment,
notional bounds, and order-field policy. Does not authorize network, secrets,
cancel, flatten, live, preflight lift, or execute.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Any

PACKAGE_MARKER = "ORDER_CAPABILITY_SIDE_PRICE_QTY_RULES_CONTRACT_V1=true"
SCHEMA_VERSION = "order_capability_side_price_qty_rules_result.v1"

DEFAULT_MAX_NOTIONAL_EUR = Decimal("10.0")
DEFAULT_MAX_LOSS_CAP_EUR = Decimal("1.0")

ALLOWED_SIDES = frozenset({"buy", "sell"})
ALLOWED_ENVIRONMENTS = frozenset(
    {
        "kraken_futures_demo",
        "demo",
        "testnet",
        "demo_testnet_only",
    }
)
FORBIDDEN_ENVIRONMENT_MARKERS = frozenset(
    {
        "live",
        "prod",
        "production",
        "mainnet",
    }
)
DEFAULT_ALLOWED_TIME_IN_FORCE = frozenset({"gtc", "ioc"})
FORBIDDEN_SERIALIZATION_KEYS = frozenset(
    {
        "api_key",
        "api_secret",
        "secret",
        "password",
        "token",
        "credential",
        "credentials",
        "private_key",
    }
)

REASON_MISSING_INSTRUMENT_RULES = "MISSING_INSTRUMENT_RULES"
REASON_LIVE_ENVIRONMENT_REJECTED = "LIVE_ENVIRONMENT_REJECTED"
REASON_UNSUPPORTED_SIDE = "UNSUPPORTED_SIDE"
REASON_SIDE_POLICY_MISMATCH = "SIDE_POLICY_MISMATCH"
REASON_MISSING_LIMIT_PRICE = "MISSING_LIMIT_PRICE"
REASON_NON_FINITE_LIMIT_PRICE = "NON_FINITE_LIMIT_PRICE"
REASON_LIMIT_PRICE_NOT_POSITIVE = "LIMIT_PRICE_NOT_POSITIVE"
REASON_PRICE_TICK_MISMATCH = "PRICE_TICK_MISMATCH"
REASON_PRICE_OUT_OF_POLICY_BOUNDS = "PRICE_OUT_OF_POLICY_BOUNDS"
REASON_MISSING_QUANTITY = "MISSING_QUANTITY"
REASON_NON_FINITE_QUANTITY = "NON_FINITE_QUANTITY"
REASON_QUANTITY_NOT_POSITIVE = "QUANTITY_NOT_POSITIVE"
REASON_QUANTITY_STEP_MISMATCH = "QUANTITY_STEP_MISMATCH"
REASON_QUANTITY_BELOW_MIN = "QUANTITY_BELOW_MIN"
REASON_QUANTITY_ABOVE_MAX = "QUANTITY_ABOVE_MAX"
REASON_NOTIONAL_ABOVE_MAX = "NOTIONAL_ABOVE_MAX"
REASON_LOSS_CAP_REFERENCE_MISSING = "LOSS_CAP_REFERENCE_MISSING"
REASON_UNSUPPORTED_REDUCE_ONLY = "UNSUPPORTED_REDUCE_ONLY"
REASON_UNSUPPORTED_POST_ONLY = "UNSUPPORTED_POST_ONLY"
REASON_UNSUPPORTED_TIME_IN_FORCE = "UNSUPPORTED_TIME_IN_FORCE"
REASON_MISSING_CORRELATION = "MISSING_CORRELATION"
REASON_UNSAFE_AUTHORITY_FLAGS = "UNSAFE_AUTHORITY_FLAGS"
REASON_EXECUTION_FIELDS_NOT_DRY_ONLY = "EXECUTION_FIELDS_NOT_DRY_ONLY"

_SIDE_ALIASES = {
    "buy": "buy",
    "sell": "sell",
    "long": "buy",
    "short": "sell",
}


class SidePriceQtyRulesError(ValueError):
    """Fail-closed side/price/qty rules evaluation or validation error."""


class SidePriceQtyVerdictKind(str, Enum):
    VALID_FOR_DRY_ORDER_CAPABILITY_PAYLOAD_ONLY = "VALID_FOR_DRY_ORDER_CAPABILITY_PAYLOAD_ONLY"
    FAIL_CLOSED = "FAIL_CLOSED"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class OrderCapabilityInstrumentRulesSummary:
    instrument: str
    price_tick: Decimal
    quantity_step: Decimal
    min_quantity: Decimal
    max_quantity: Decimal
    metadata_source: str
    metadata_verified_offline: bool


@dataclass(frozen=True)
class OrderCapabilitySidePriceQtyPolicy:
    allowed_sides: frozenset[str] = ALLOWED_SIDES
    allow_long_short_aliases: bool = False
    allowed_time_in_force: frozenset[str] = DEFAULT_ALLOWED_TIME_IN_FORCE
    reduce_only_supported: bool = False
    post_only_supported: bool = False
    require_explicit_loss_cap_reference: bool = True
    max_notional_eur: Decimal = DEFAULT_MAX_NOTIONAL_EUR
    max_loss_cap_eur: Decimal = DEFAULT_MAX_LOSS_CAP_EUR
    optional_min_limit_price: Decimal | None = None
    optional_max_limit_price: Decimal | None = None
    allowed_environments: frozenset[str] = ALLOWED_ENVIRONMENTS
    forbidden_environment_markers: frozenset[str] = FORBIDDEN_ENVIRONMENT_MARKERS


@dataclass(frozen=True)
class OrderCapabilitySidePriceQtyInput:
    instrument_rules: OrderCapabilityInstrumentRulesSummary
    policy: OrderCapabilitySidePriceQtyPolicy
    environment: str
    side: str
    limit_price: float | Decimal | None
    quantity: float | Decimal | None
    time_in_force: str
    post_only: bool
    reduce_only: bool
    max_notional_eur: float | Decimal
    max_loss_cap_eur: float | Decimal
    evidence_correlation_id: str
    execute_authorized: bool = False
    cancel_authorized: bool = False
    flatten_authorized: bool = False


@dataclass(frozen=True)
class OrderCapabilitySidePriceQtyVerdict:
    verdict: SidePriceQtyVerdictKind
    reason_codes: tuple[str, ...]
    normalized_side: str | None
    computed_notional_eur: Decimal | None
    side_price_qty_rules_satisfied: bool
    safety_flags: dict[str, bool]


def default_order_capability_side_price_qty_policy() -> OrderCapabilitySidePriceQtyPolicy:
    return OrderCapabilitySidePriceQtyPolicy()


def _normalize(text: str) -> str:
    return " ".join(text.strip().lower().split())


def _to_decimal(value: float | Decimal | str | int) -> Decimal:
    return Decimal(str(value))


def _is_finite_number(value: float | Decimal | None) -> bool:
    if value is None:
        return False
    if isinstance(value, Decimal):
        return not value.is_nan() and not value.is_infinite()
    return math.isfinite(float(value))


def _decimal_aligned(value: Decimal, step: Decimal) -> bool:
    if step <= 0:
        return False
    remainder = value % step
    return remainder == 0


def _blocked_safety_flags(*, satisfied: bool) -> dict[str, bool]:
    return {
        "side_price_qty_rules_satisfied": satisfied,
        "no_network_performed": True,
        "no_secret_read": True,
        "order_submission_executed": False,
        "cancel_executed": False,
        "trade_position_mutation_executed": False,
        "execute_authorized": False,
        "cancel_authorized": False,
        "flatten_authorized": False,
        "preflight_remains_blocked": True,
        "live_ready": False,
        "dashboard_truth_granted": False,
        "no_authority_change": True,
    }


def _fail_verdict(
    reason_codes: list[str],
    *,
    normalized_side: str | None = None,
    computed_notional_eur: Decimal | None = None,
) -> OrderCapabilitySidePriceQtyVerdict:
    return OrderCapabilitySidePriceQtyVerdict(
        verdict=SidePriceQtyVerdictKind.FAIL_CLOSED,
        reason_codes=tuple(reason_codes),
        normalized_side=normalized_side,
        computed_notional_eur=computed_notional_eur,
        side_price_qty_rules_satisfied=False,
        safety_flags=_blocked_safety_flags(satisfied=False),
    )


def _validate_instrument_rules(
    rules: OrderCapabilityInstrumentRulesSummary,
) -> list[str]:
    reasons: list[str] = []
    if not rules.instrument.strip():
        reasons.append(REASON_MISSING_INSTRUMENT_RULES)
    if not rules.metadata_verified_offline:
        reasons.append(REASON_MISSING_INSTRUMENT_RULES)
    if not rules.metadata_source.strip():
        reasons.append(REASON_MISSING_INSTRUMENT_RULES)
    try:
        if rules.price_tick <= 0 or rules.quantity_step <= 0:
            reasons.append(REASON_MISSING_INSTRUMENT_RULES)
        if rules.min_quantity <= 0 or rules.max_quantity <= 0:
            reasons.append(REASON_MISSING_INSTRUMENT_RULES)
        if rules.max_quantity < rules.min_quantity:
            reasons.append(REASON_MISSING_INSTRUMENT_RULES)
    except Exception:
        reasons.append(REASON_MISSING_INSTRUMENT_RULES)
    return reasons


def _environment_forbidden(environment: str, policy: OrderCapabilitySidePriceQtyPolicy) -> bool:
    normalized = _normalize(environment)
    if not normalized:
        return True
    for marker in policy.forbidden_environment_markers:
        if marker in normalized:
            return True
    return normalized not in policy.allowed_environments


def _normalize_side(
    side: str, policy: OrderCapabilitySidePriceQtyPolicy
) -> tuple[str | None, str | None]:
    """Return (normalized_side, reason_code_if_any)."""
    normalized = _normalize(side)
    if not normalized:
        return None, REASON_UNSUPPORTED_SIDE
    if normalized in {"buy", "sell"}:
        canonical = normalized
    elif policy.allow_long_short_aliases and normalized in {"long", "short"}:
        canonical = _SIDE_ALIASES[normalized]
    else:
        return None, REASON_UNSUPPORTED_SIDE
    if canonical not in policy.allowed_sides:
        return None, REASON_SIDE_POLICY_MISMATCH
    return canonical, None


def evaluate_order_capability_side_price_qty_rules(
    input: OrderCapabilitySidePriceQtyInput,
) -> OrderCapabilitySidePriceQtyVerdict:
    reasons: list[str] = []
    policy = input.policy

    reasons.extend(_validate_instrument_rules(input.instrument_rules))
    if _environment_forbidden(input.environment, policy):
        reasons.append(REASON_LIVE_ENVIRONMENT_REJECTED)

    if input.execute_authorized or input.cancel_authorized or input.flatten_authorized:
        reasons.append(REASON_UNSAFE_AUTHORITY_FLAGS)
        reasons.append(REASON_EXECUTION_FIELDS_NOT_DRY_ONLY)

    normalized_side, side_reason = _normalize_side(input.side, policy)
    if side_reason:
        reasons.append(side_reason)

    if input.limit_price is None:
        reasons.append(REASON_MISSING_LIMIT_PRICE)
    elif not _is_finite_number(input.limit_price):
        reasons.append(REASON_NON_FINITE_LIMIT_PRICE)
    else:
        price_dec = _to_decimal(input.limit_price)
        if price_dec <= 0:
            reasons.append(REASON_LIMIT_PRICE_NOT_POSITIVE)
        else:
            if not _decimal_aligned(price_dec, input.instrument_rules.price_tick):
                reasons.append(REASON_PRICE_TICK_MISMATCH)
            if (
                policy.optional_min_limit_price is not None
                and price_dec < policy.optional_min_limit_price
            ):
                reasons.append(REASON_PRICE_OUT_OF_POLICY_BOUNDS)
            if (
                policy.optional_max_limit_price is not None
                and price_dec > policy.optional_max_limit_price
            ):
                reasons.append(REASON_PRICE_OUT_OF_POLICY_BOUNDS)

    if input.quantity is None:
        reasons.append(REASON_MISSING_QUANTITY)
    elif not _is_finite_number(input.quantity):
        reasons.append(REASON_NON_FINITE_QUANTITY)
    else:
        qty_dec = _to_decimal(input.quantity)
        if qty_dec <= 0:
            reasons.append(REASON_QUANTITY_NOT_POSITIVE)
        else:
            if not _decimal_aligned(qty_dec, input.instrument_rules.quantity_step):
                reasons.append(REASON_QUANTITY_STEP_MISMATCH)
            if qty_dec < input.instrument_rules.min_quantity:
                reasons.append(REASON_QUANTITY_BELOW_MIN)
            if qty_dec > input.instrument_rules.max_quantity:
                reasons.append(REASON_QUANTITY_ABOVE_MAX)

    computed_notional: Decimal | None = None
    if (
        input.limit_price is not None
        and input.quantity is not None
        and _is_finite_number(input.limit_price)
        and _is_finite_number(input.quantity)
    ):
        price_dec = _to_decimal(input.limit_price)
        qty_dec = _to_decimal(input.quantity)
        if price_dec > 0 and qty_dec > 0:
            computed_notional = price_dec * qty_dec
            input_max_notional = _to_decimal(input.max_notional_eur)
            effective_cap = min(policy.max_notional_eur, input_max_notional)
            if computed_notional > effective_cap:
                reasons.append(REASON_NOTIONAL_ABOVE_MAX)

    if policy.require_explicit_loss_cap_reference:
        loss_cap = _to_decimal(input.max_loss_cap_eur)
        if loss_cap <= 0:
            reasons.append(REASON_LOSS_CAP_REFERENCE_MISSING)
        else:
            notional_cap = _to_decimal(input.max_notional_eur)
            if loss_cap > notional_cap:
                reasons.append(REASON_LOSS_CAP_REFERENCE_MISSING)

    if input.reduce_only and not policy.reduce_only_supported:
        reasons.append(REASON_UNSUPPORTED_REDUCE_ONLY)
    if input.post_only and not policy.post_only_supported:
        reasons.append(REASON_UNSUPPORTED_POST_ONLY)

    tif_normalized = _normalize(input.time_in_force)
    if not tif_normalized or tif_normalized not in policy.allowed_time_in_force:
        reasons.append(REASON_UNSUPPORTED_TIME_IN_FORCE)

    if not input.evidence_correlation_id.strip():
        reasons.append(REASON_MISSING_CORRELATION)

    if reasons:
        return _fail_verdict(
            reasons,
            normalized_side=normalized_side,
            computed_notional_eur=computed_notional,
        )

    return OrderCapabilitySidePriceQtyVerdict(
        verdict=SidePriceQtyVerdictKind.VALID_FOR_DRY_ORDER_CAPABILITY_PAYLOAD_ONLY,
        reason_codes=(),
        normalized_side=normalized_side,
        computed_notional_eur=computed_notional,
        side_price_qty_rules_satisfied=True,
        safety_flags=_blocked_safety_flags(satisfied=True),
    )


def serialize_order_capability_side_price_qty_verdict(
    verdict: OrderCapabilitySidePriceQtyVerdict,
) -> dict[str, Any]:
    validate_order_capability_side_price_qty_verdict(verdict)
    notional_value: float | None = None
    if verdict.computed_notional_eur is not None:
        notional_value = float(verdict.computed_notional_eur)
    data: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "contract_marker": PACKAGE_MARKER,
        "verdict": verdict.verdict.value,
        "reason_codes": list(verdict.reason_codes),
        "normalized_side": verdict.normalized_side,
        "computed_notional_eur": notional_value,
        "side_price_qty_rules_satisfied": verdict.side_price_qty_rules_satisfied,
        "safety_flags": dict(verdict.safety_flags),
    }
    for key in data:
        if key.lower() in FORBIDDEN_SERIALIZATION_KEYS:
            raise SidePriceQtyRulesError(
                f"serialized verdict must not include forbidden key {key!r}"
            )
    for key in verdict.safety_flags:
        if key.lower() in FORBIDDEN_SERIALIZATION_KEYS:
            raise SidePriceQtyRulesError(
                f"safety flag key must not be forbidden serialization key {key!r}"
            )
    return data


def validate_order_capability_side_price_qty_verdict(
    verdict: OrderCapabilitySidePriceQtyVerdict,
) -> None:
    expected_blocked = _blocked_safety_flags(satisfied=verdict.side_price_qty_rules_satisfied)
    for key, expected in expected_blocked.items():
        actual = verdict.safety_flags.get(key)
        if actual is not expected:
            raise SidePriceQtyRulesError(
                f"safety flag {key!r} must be {expected!r}, got {actual!r}"
            )
    if verdict.verdict == SidePriceQtyVerdictKind.VALID_FOR_DRY_ORDER_CAPABILITY_PAYLOAD_ONLY:
        if verdict.reason_codes:
            raise SidePriceQtyRulesError("VALID verdict must have empty reason_codes")
        if not verdict.side_price_qty_rules_satisfied:
            raise SidePriceQtyRulesError(
                "VALID verdict requires side_price_qty_rules_satisfied=true"
            )
        if verdict.normalized_side not in ALLOWED_SIDES:
            raise SidePriceQtyRulesError("VALID verdict requires normalized buy/sell side")
    else:
        if verdict.side_price_qty_rules_satisfied:
            raise SidePriceQtyRulesError(
                "non-VALID verdict requires side_price_qty_rules_satisfied=false"
            )
        if not verdict.reason_codes:
            raise SidePriceQtyRulesError("non-VALID verdict requires non-empty reason_codes")


def map_side_price_qty_verdict_to_payload_builder_flag(
    verdict: OrderCapabilitySidePriceQtyVerdict,
) -> bool:
    return (
        verdict.verdict == SidePriceQtyVerdictKind.VALID_FOR_DRY_ORDER_CAPABILITY_PAYLOAD_ONLY
        and verdict.side_price_qty_rules_satisfied
    )
