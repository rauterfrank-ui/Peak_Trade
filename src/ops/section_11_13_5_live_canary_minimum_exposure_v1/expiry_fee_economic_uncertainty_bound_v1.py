"""§11.13.5.Z2C/Z2I expiry-fee bound.

PROVENANCE != ADJUDICATION.

The numeric ``0.0003`` is a verified first-party OKX EEA production API
artifact (``GET /api/v5/account/trade-fee`` field ``delivery``). It is
not Peak_Trade-generated and not Owner-generated.

§11.13.5.Z2I owner-ratifies the *semantic/operative use* of that verified
field as Peak_Trade's single expiry-settlement rate. This does not invent
a later OKX support confirmation of field semantics, does not rewrite
sealed evidence, and does not authorize Live, Testnet, orders, funding,
scaling, or Multi-Future.

``PEAK_TRADE_EXPIRY_RESERVE_RATE=0.0003`` historically began as a
Peak_Trade-internal policy constant. That history remains; it is now
policy reuse of the same verified API numeric, not a second rate.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    AUTHORIZATION_SCOPE,
    DEFAULT_INSTRUMENT_ID,
    LIVE_AUTHORIZED,
    MINIMUM_RATIFIED_NOTIONAL_ONLY,
    TESTNET_AUTHORIZED,
    assert_live_canary_instrument_binding_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.exposure_v1 import (
    derive_min_executable_notional_v1,
)

# Historical Z2B support rate. Superseded for current operative use.
PROVEN_NORMAL_EXPIRY_RATE = Decimal("0.0001")
SUPPORT_RATE_0_0001_STATUS = "HISTORICAL_SUPERSEDED"
SUPPORT_TICKET_7823581_STATUS = "HISTORICAL_SUPERSEDED_FOR_RATE_ADJUDICATION"
SUPPORT_RATE_0_0001_CAN_BLOCK_CURRENT_RATE = False
SUPPORT_DEPENDENCY_FOR_EXPIRY_RATE = False
EXPIRY_RATE_REOPEN_REQUIRED = False

DELIVERY_RATE_VALUE = Decimal("0.0003")
DELIVERY_RATE_VALUE_PROVENANCE = "VERIFIED_FIRST_PARTY_OKX_API_ARTIFACT"
DELIVERY_RATE_SOURCE = "OKX_EEA_PRODUCTION_API"
DELIVERY_RATE_ENDPOINT = "/api/v5/account/trade-fee"
DELIVERY_RATE_FIELD = "delivery"
DELIVERY_RATE_ARTIFACT_VERIFIED = True
DELIVERY_RATE_PEAK_TRADE_GENERATED = False
DELIVERY_RATE_OWNER_GENERATED = False

CANONICAL_EXPIRY_SETTLEMENT_RATE = Decimal("0.0003")
CANONICAL_EXPIRY_SETTLEMENT_RATE_PERCENT = "0.03%"
EXPIRY_SETTLEMENT_RATE = Decimal("0.0003")
EXPIRY_SETTLEMENT_RATE_PERCENT = "0.03%"
EXPIRY_SETTLEMENT_RATE_VALUE_PROVENANCE = "VERIFIED_FIRST_PARTY_OKX_API_ARTIFACT"
EXPIRY_SETTLEMENT_RATE_SOURCE_FIELD = "delivery"
EXPIRY_SETTLEMENT_RATE_SOURCE_VALUE = "0.0003"
EXPIRY_SETTLEMENT_RATE_ADJUDICATION = "OWNER_RATIFIED_FROM_VERIFIED_FIRST_PARTY_OKX_DELIVERY_FIELD"
OPERATIVE_EXPIRY_SETTLEMENT_RATE = Decimal("0.0003")
OPERATIVE_EXPIRY_SETTLEMENT_RATE_PERCENT = "0.03%"
OPERATIVE_EXPIRY_FEE_RATE = "0.0003"
SINGLE_CURRENT_RATE_TRUTH = True
PR_5960_SEMANTICS_STATUS = "HISTORICAL_SUPERSEDED"
DELIVERY_RATE_OPERATIVE_VALUE = "0.0003"
EXPIRY_SETTLEMENT_RATE_AUTHORITY = "EXCHANGE_OBSERVED_OWNER_RATIFIED_OPERATIVE_TRUTH"
EXPIRY_SETTLEMENT_RATE_API_SOURCE = "OKX_ACCOUNT_TRADE_FEE_DELIVERY"
EXPIRY_SETTLEMENT_RATE_API_FIELD = "delivery"
EXPIRY_SETTLEMENT_RATE_API_VALUE = "0.0003"
CANONICAL_RATE_STATUS = "OWNER_RATIFIED_OPERATIVE"
CANONICAL_RATE_SOURCE = "OKX_TRADE_FEE_API_FIELD_DELIVERY"
CANONICAL_RATE_PROVENANCE = "VERIFIED_FIRST_PARTY_OKX_API_ARTIFACT"
RATE_STATUS = "RESOLVED"
RATE_ADJUDICATION_CLOSED = True
EXPIRY_RATE_GATE = "PASS"
EXPIRY_RATE_BLOCKER = False
EXPIRY_RATE_SUPPORT_DEPENDENCY = False
SUPPORT_REQUIRED_FOR_RATE_DECISION = False
API_DELIVERY_0003_BLOCKS_OPERATION = False
PROVEN_FIRST_PARTY_RATE_CONTRADICTION_BLOCKING = False

API_DELIVERY_0_0003_STATUS = "VERIFIED_FIRST_PARTY_VALUE_OWNER_RATIFIED_OPERATIVE_ADJUDICATION"
# False: do not invent an OKX support confirmation of field semantics.
PEAK_TRADE_EXPIRY_RESERVE_RATE_IS_OKX_FEE_TRUTH = False

PEAK_TRADE_EXPIRY_RESERVE_RATE = Decimal("0.0003")
PEAK_TRADE_EXPIRY_RESERVE_RATE_SOURCE = "PEAK_TRADE_POLICY_REUSE_OF_SAME_NUMERIC_VALUE"
PEAK_TRADE_EXPIRY_RESERVE_RATE_HISTORICAL_SOURCE = "CONSERVATIVE_INTERNAL_POLICY"
RESERVE_RATE_ROLE = "PEAK_TRADE_POLICY_REUSE_OF_VERIFIED_API_DELIVERY_NUMERIC"
ABSOLUTE_BOUND_DERIVATION = "PEAK_TRADE_EXPIRY_RESERVE_RATE * PEAK_TRADE_INTERNAL_NOTIONAL_ENVELOPE"
ABSOLUTE_BOUND_USES_UNPROVEN_EXCHANGE_FORMULA = False
PEAK_TRADE_INTERNAL_NOTIONAL_ENVELOPE_FORM = "qty * ctVal * markPx"
PEAK_TRADE_INTERNAL_NOTIONAL_ENVELOPE_ROLE = (
    "BOUND_PEAK_TRADE_INTERNAL_NOTIONAL_ENVELOPE_NOT_OEM_OKX_MONETARY_BASE"
)
OEM_FEE_MONETARY_BASE_STATUS = "BOUND_PEAK_TRADE_INTERNAL_NOTIONAL_ENVELOPE"
MONETARY_BASE_STATUS = "BOUND_PEAK_TRADE_INTERNAL_NOTIONAL_ENVELOPE"
OEM_OKX_MONETARY_BASE_IDENTITY_STATUS = "UNPROVEN"
ACTUAL_EXPIRY_FEE_AMOUNT_STATUS = "COMPUTED_FROM_VERIFIED_API_RATE_AND_INTERNAL_ENVELOPE"
PEAK_TRADE_INTERNAL_NOTIONAL_UNIT = "PEAK_TRADE_INTERNAL_NOTIONAL_UNIT"
QTY_LIMIT = Decimal("1")
MINIMUM_EXPOSURE_ONLY = True
SCALING_AUTHORIZED = False
MULTI_FUTURE_AUTHORIZED = False
POST_SETTLEMENT_RECONCILIATION_REQUIRED = True
OBSERVED_FEE_MUST_NOT_REWRITE_NORMATIVE_TRUTH = True
UNKNOWN_EXACT_EXPIRY_FEE_EXCEPTION_SCOPE = (
    "QTY_1_MINIMUM_EXPOSURE_CANARY_SINGLE_SELECTED_FUTURE_ONLY"
)

REQUIRED_PROVEN_LOCAL_QUANTITIES: tuple[str, ...] = (
    "quantity",
    "instrument_ct_val",
    "reference_price",
    "instrument_id",
    "authorization_scope",
)


class ExpiryFeeEconomicUncertaintyBoundError(RuntimeError):
    """Fail-closed internal conservative-bound / reconciliation violation."""


def assert_canonical_expiry_settlement_rate_v1() -> None:
    """Fail closed unless the single verified API rate is the operative rate."""

    if DELIVERY_RATE_PEAK_TRADE_GENERATED or DELIVERY_RATE_OWNER_GENERATED:
        raise ExpiryFeeEconomicUncertaintyBoundError(
            "DELIVERY_RATE_VALUE_IS_NOT_PEAK_TRADE_OR_OWNER_GENERATED"
        )
    if DELIVERY_RATE_VALUE_PROVENANCE != "VERIFIED_FIRST_PARTY_OKX_API_ARTIFACT":
        raise ExpiryFeeEconomicUncertaintyBoundError(
            "DELIVERY_RATE_VALUE_PROVENANCE_MISSING_OR_INVALID"
        )
    if not DELIVERY_RATE_ARTIFACT_VERIFIED:
        raise ExpiryFeeEconomicUncertaintyBoundError("DELIVERY_RATE_ARTIFACT_NOT_VERIFIED")
    if EXPIRY_SETTLEMENT_RATE != Decimal("0.0003"):
        raise ExpiryFeeEconomicUncertaintyBoundError(
            "CANONICAL_EXPIRY_SETTLEMENT_RATE_MISSING_OR_INVALID"
        )
    if EXPIRY_SETTLEMENT_RATE_PERCENT != "0.03%":
        raise ExpiryFeeEconomicUncertaintyBoundError(
            "CANONICAL_EXPIRY_SETTLEMENT_RATE_PERCENT_MISSING_OR_INVALID"
        )
    if OPERATIVE_EXPIRY_FEE_RATE in {"", "NONE", "0.0001"}:
        raise ExpiryFeeEconomicUncertaintyBoundError(
            "CANONICAL_EXPIRY_SETTLEMENT_RATE_MISSING_OR_INVALID"
        )
    if OPERATIVE_EXPIRY_FEE_RATE != "0.0003":
        raise ExpiryFeeEconomicUncertaintyBoundError(
            "CANONICAL_EXPIRY_SETTLEMENT_RATE_MISSING_OR_INVALID"
        )
    if OPERATIVE_EXPIRY_SETTLEMENT_RATE != Decimal("0.0003"):
        raise ExpiryFeeEconomicUncertaintyBoundError(
            "CANONICAL_EXPIRY_SETTLEMENT_RATE_MISSING_OR_INVALID"
        )
    if not SINGLE_CURRENT_RATE_TRUTH:
        raise ExpiryFeeEconomicUncertaintyBoundError("ACTIVE_EXPIRY_RATE_CONFLICT")
    if PR_5960_SEMANTICS_STATUS != "HISTORICAL_SUPERSEDED":
        raise ExpiryFeeEconomicUncertaintyBoundError("ACTIVE_EXPIRY_RATE_CONFLICT")
    if PEAK_TRADE_EXPIRY_RESERVE_RATE != EXPIRY_SETTLEMENT_RATE:
        raise ExpiryFeeEconomicUncertaintyBoundError("ACTIVE_EXPIRY_RATE_CONFLICT")
    if SUPPORT_RATE_0_0001_CAN_BLOCK_CURRENT_RATE or EXPIRY_RATE_BLOCKER:
        raise ExpiryFeeEconomicUncertaintyBoundError("HISTORICAL_SUPPORT_RATE_MUST_NOT_BLOCK")
    if EXPIRY_RATE_GATE != "PASS":
        raise ExpiryFeeEconomicUncertaintyBoundError("EXPIRY_RATE_GATE_MUST_PASS")


@dataclass(frozen=True)
class InternalExpiryFeeEconomicUncertaintyBoundV1:
    bound_status: str
    absolute_economic_uncertainty_bound: str
    bound_unit: str
    reserve_rate: str
    reserve_rate_role: str
    reserve_rate_is_okx_fee_truth: bool
    proven_normal_expiry_rate: str
    oem_fee_monetary_base_status: str
    actual_expiry_fee_amount_status: str
    operative_expiry_fee_rate: str
    internal_notional_envelope: str
    internal_notional_envelope_role: str
    derivation: str
    uses_unproven_exchange_formula: bool
    quantity: str
    qty_limit: str
    instrument_id: str
    authorization_scope: str
    minimum_exposure_only: bool
    scaling_authorized: bool
    multi_future_authorized: bool
    live_authorized: bool
    testnet_authorized: bool
    order_effect: str
    funding_executed: bool
    post_settlement_reconciliation_required: bool
    observed_fee_can_rewrite_normative_truth: bool
    unknown_exact_expiry_fee_exception_scope: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "BOUND_STATUS": self.bound_status,
            "ABSOLUTE_ECONOMIC_UNCERTAINTY_BOUND": self.absolute_economic_uncertainty_bound,
            "BOUND_UNIT": self.bound_unit,
            "PEAK_TRADE_EXPIRY_RESERVE_RATE": self.reserve_rate,
            "RESERVE_RATE_ROLE": self.reserve_rate_role,
            "PEAK_TRADE_EXPIRY_RESERVE_RATE_IS_OKX_FEE_TRUTH": (self.reserve_rate_is_okx_fee_truth),
            "PROVEN_NORMAL_EXPIRY_RATE": self.proven_normal_expiry_rate,
            "OEM_FEE_MONETARY_BASE_STATUS": self.oem_fee_monetary_base_status,
            "ACTUAL_EXPIRY_FEE_AMOUNT_STATUS": self.actual_expiry_fee_amount_status,
            "OPERATIVE_EXPIRY_FEE_RATE": self.operative_expiry_fee_rate,
            "PEAK_TRADE_INTERNAL_NOTIONAL_ENVELOPE": self.internal_notional_envelope,
            "PEAK_TRADE_INTERNAL_NOTIONAL_ENVELOPE_ROLE": (self.internal_notional_envelope_role),
            "ABSOLUTE_BOUND_DERIVATION": self.derivation,
            "ABSOLUTE_BOUND_USES_UNPROVEN_EXCHANGE_FORMULA": (self.uses_unproven_exchange_formula),
            "QUANTITY": self.quantity,
            "QTY_LIMIT": self.qty_limit,
            "INSTRUMENT_ID": self.instrument_id,
            "AUTHORIZATION_SCOPE": self.authorization_scope,
            "MINIMUM_EXPOSURE_ONLY": self.minimum_exposure_only,
            "SCALING_AUTHORIZED": self.scaling_authorized,
            "MULTI_FUTURE_AUTHORIZED": self.multi_future_authorized,
            "LIVE_AUTHORIZED": self.live_authorized,
            "TESTNET_AUTHORIZED": self.testnet_authorized,
            "ORDER_EFFECT": self.order_effect,
            "FUNDING_EXECUTED": self.funding_executed,
            "POST_SETTLEMENT_RECONCILIATION_REQUIRED": (
                self.post_settlement_reconciliation_required
            ),
            "OBSERVED_FEE_CAN_REWRITE_NORMATIVE_TRUTH": (
                self.observed_fee_can_rewrite_normative_truth
            ),
            "UNKNOWN_EXACT_EXPIRY_FEE_EXCEPTION_SCOPE": (
                self.unknown_exact_expiry_fee_exception_scope
            ),
        }


@dataclass(frozen=True)
class ObservedExpiryFeeReconciliationV1:
    reconciliation_status: str
    fail_closed: bool
    scaling_blocked: bool
    further_canary_requires_review: bool
    observed_fee_amount: str
    bound_amount: str
    observed_fee_rewrote_normative_truth: bool
    proven_normal_expiry_rate: str
    oem_fee_monetary_base_status: str
    actual_expiry_fee_amount_status: str
    operative_expiry_fee_rate: str
    live_authorized: bool
    testnet_authorized: bool
    order_effect: str
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "RECONCILIATION_STATUS": self.reconciliation_status,
            "FAIL_CLOSED": self.fail_closed,
            "SCALING_BLOCKED": self.scaling_blocked,
            "FURTHER_CANARY_REQUIRES_REVIEW": self.further_canary_requires_review,
            "OBSERVED_FEE_AMOUNT": self.observed_fee_amount,
            "BOUND_AMOUNT": self.bound_amount,
            "OBSERVED_FEE_REWROTE_NORMATIVE_TRUTH": (self.observed_fee_rewrote_normative_truth),
            "PROVEN_NORMAL_EXPIRY_RATE": self.proven_normal_expiry_rate,
            "OEM_FEE_MONETARY_BASE_STATUS": self.oem_fee_monetary_base_status,
            "ACTUAL_EXPIRY_FEE_AMOUNT_STATUS": self.actual_expiry_fee_amount_status,
            "OPERATIVE_EXPIRY_FEE_RATE": self.operative_expiry_fee_rate,
            "LIVE_AUTHORIZED": self.live_authorized,
            "TESTNET_AUTHORIZED": self.testnet_authorized,
            "ORDER_EFFECT": self.order_effect,
            "REASONS": list(self.reasons),
        }


def _require_positive_decimal(raw: str | None, *, field: str) -> Decimal:
    text = str(raw or "").strip()
    if not text:
        raise ExpiryFeeEconomicUncertaintyBoundError(f"MISSING_PROVEN_LOCAL_QUANTITY:{field}")
    try:
        value = Decimal(text)
    except (InvalidOperation, TypeError) as exc:
        raise ExpiryFeeEconomicUncertaintyBoundError(
            f"MISSING_PROVEN_LOCAL_QUANTITY:{field}"
        ) from exc
    if value <= 0:
        raise ExpiryFeeEconomicUncertaintyBoundError(f"MISSING_PROVEN_LOCAL_QUANTITY:{field}")
    return value


def evaluate_internal_expiry_fee_economic_uncertainty_bound_v1(
    *,
    quantity: str | None,
    instrument_ct_val: str | None,
    reference_price: str | None,
    instrument_id: str | None,
    authorization_scope: str | None,
    instrument_min_sz: str | None = "1",
    multi_future_requested: bool = False,
) -> InternalExpiryFeeEconomicUncertaintyBoundV1:
    """Form the qty=1 bound from the verified API rate, or fail closed.

    Reuses the existing Peak_Trade notional envelope
    ``qty * ctVal * markPx`` already used by §11.13.5.U ``FEE_RESERVE``.
    That envelope is a bound Peak_Trade implementation input, not an OEM
    OKX monetary-base identity. The rate itself cannot be reset to NONE
    by that OEM-identity question.
    """

    assert_canonical_expiry_settlement_rate_v1()

    scope = str(authorization_scope or "").strip()
    if not scope:
        raise ExpiryFeeEconomicUncertaintyBoundError(
            "MISSING_PROVEN_LOCAL_QUANTITY:authorization_scope"
        )
    if scope != AUTHORIZATION_SCOPE:
        raise ExpiryFeeEconomicUncertaintyBoundError(f"SCOPE_NOT_MINIMUM_EXPOSURE_CANARY:{scope}")

    iid = str(instrument_id or "").strip()
    if not iid:
        raise ExpiryFeeEconomicUncertaintyBoundError("MISSING_PROVEN_LOCAL_QUANTITY:instrument_id")
    assert_live_canary_instrument_binding_v1(instrument_id=iid)

    if multi_future_requested or not MINIMUM_RATIFIED_NOTIONAL_ONLY:
        raise ExpiryFeeEconomicUncertaintyBoundError("MULTI_FUTURE_NOT_AUTHORIZED")

    qty = _require_positive_decimal(quantity, field="quantity")
    min_sz = _require_positive_decimal(instrument_min_sz, field="instrument_min_sz")
    if qty != QTY_LIMIT or qty != min_sz:
        raise ExpiryFeeEconomicUncertaintyBoundError("QTY_NOT_MINIMUM_EXPOSURE_CANARY_LIMIT")

    _require_positive_decimal(instrument_ct_val, field="instrument_ct_val")
    _require_positive_decimal(reference_price, field="reference_price")

    envelope = Decimal(
        derive_min_executable_notional_v1(
            quantity=str(quantity),
            reference_price=str(reference_price),
            instrument_ct_val=str(instrument_ct_val),
        )
    )
    bound = PEAK_TRADE_EXPIRY_RESERVE_RATE * envelope
    if bound <= 0:
        raise ExpiryFeeEconomicUncertaintyBoundError("MISSING_PROVEN_LOCAL_QUANTITY:absolute_bound")

    return InternalExpiryFeeEconomicUncertaintyBoundV1(
        bound_status="INTERNAL_CONSERVATIVE_ABSOLUTE_BOUND_PRESENT",
        absolute_economic_uncertainty_bound=format(bound, "f"),
        bound_unit=PEAK_TRADE_INTERNAL_NOTIONAL_UNIT,
        reserve_rate=format(PEAK_TRADE_EXPIRY_RESERVE_RATE, "f"),
        reserve_rate_role=RESERVE_RATE_ROLE,
        reserve_rate_is_okx_fee_truth=PEAK_TRADE_EXPIRY_RESERVE_RATE_IS_OKX_FEE_TRUTH,
        proven_normal_expiry_rate=format(PROVEN_NORMAL_EXPIRY_RATE, "f"),
        oem_fee_monetary_base_status=OEM_FEE_MONETARY_BASE_STATUS,
        actual_expiry_fee_amount_status=ACTUAL_EXPIRY_FEE_AMOUNT_STATUS,
        operative_expiry_fee_rate=OPERATIVE_EXPIRY_FEE_RATE,
        internal_notional_envelope=format(envelope, "f"),
        internal_notional_envelope_role=PEAK_TRADE_INTERNAL_NOTIONAL_ENVELOPE_ROLE,
        derivation=ABSOLUTE_BOUND_DERIVATION,
        uses_unproven_exchange_formula=ABSOLUTE_BOUND_USES_UNPROVEN_EXCHANGE_FORMULA,
        quantity=format(qty, "f"),
        qty_limit=format(QTY_LIMIT, "f"),
        instrument_id=iid,
        authorization_scope=scope,
        minimum_exposure_only=MINIMUM_EXPOSURE_ONLY,
        scaling_authorized=SCALING_AUTHORIZED,
        multi_future_authorized=MULTI_FUTURE_AUTHORIZED,
        live_authorized=LIVE_AUTHORIZED,
        testnet_authorized=TESTNET_AUTHORIZED,
        order_effect="NONE",
        funding_executed=False,
        post_settlement_reconciliation_required=POST_SETTLEMENT_RECONCILIATION_REQUIRED,
        observed_fee_can_rewrite_normative_truth=False,
        unknown_exact_expiry_fee_exception_scope=UNKNOWN_EXACT_EXPIRY_FEE_EXCEPTION_SCOPE,
    )


def reconcile_observed_expiry_fee_against_internal_bound_v1(
    *,
    bound: InternalExpiryFeeEconomicUncertaintyBoundV1 | Mapping[str, Any],
    observed_fee_amount: str | None,
    observed_fee_unit: str | None,
) -> ObservedExpiryFeeReconciliationV1:
    """Compare an observed OKX debit with the internal bound.

    Observed amounts are evidence only. They must not rewrite Exchange Truth.
    Unit mismatch with unproven FX fails closed.
    """

    payload = (
        bound.to_dict()
        if isinstance(bound, InternalExpiryFeeEconomicUncertaintyBoundV1)
        else dict(bound)
    )
    bound_amount_raw = str(payload.get("ABSOLUTE_ECONOMIC_UNCERTAINTY_BOUND") or "").strip()
    bound_unit = str(payload.get("BOUND_UNIT") or "").strip()
    if not bound_amount_raw or not bound_unit:
        raise ExpiryFeeEconomicUncertaintyBoundError("MISSING_PROVEN_LOCAL_QUANTITY:absolute_bound")

    observed_raw = str(observed_fee_amount or "").strip()
    if not observed_raw:
        raise ExpiryFeeEconomicUncertaintyBoundError(
            "MISSING_PROVEN_LOCAL_QUANTITY:observed_fee_amount"
        )
    try:
        observed = Decimal(observed_raw)
        bound_amount = Decimal(bound_amount_raw)
    except (InvalidOperation, TypeError) as exc:
        raise ExpiryFeeEconomicUncertaintyBoundError(
            "MISSING_PROVEN_LOCAL_QUANTITY:observed_fee_amount"
        ) from exc
    if observed < 0 or bound_amount <= 0:
        raise ExpiryFeeEconomicUncertaintyBoundError(
            "MISSING_PROVEN_LOCAL_QUANTITY:observed_fee_amount"
        )

    observed_unit = str(observed_fee_unit or "").strip()
    if not observed_unit:
        raise ExpiryFeeEconomicUncertaintyBoundError(
            "MISSING_PROVEN_LOCAL_QUANTITY:observed_fee_unit"
        )
    if observed_unit != bound_unit:
        raise ExpiryFeeEconomicUncertaintyBoundError("UNIT_MISMATCH_FX_UNPROVEN")

    reasons: list[str] = [
        "OBSERVED_FEE_IS_EVIDENCE_ONLY",
        "OBSERVED_FEE_MUST_NOT_REWRITE_NORMATIVE_TRUTH",
        f"OEM_FEE_MONETARY_BASE_STATUS={OEM_FEE_MONETARY_BASE_STATUS}",
        f"OEM_OKX_MONETARY_BASE_IDENTITY_STATUS={OEM_OKX_MONETARY_BASE_IDENTITY_STATUS}",
        f"ACTUAL_EXPIRY_FEE_AMOUNT_STATUS={ACTUAL_EXPIRY_FEE_AMOUNT_STATUS}",
        f"OPERATIVE_EXPIRY_FEE_RATE={OPERATIVE_EXPIRY_FEE_RATE}",
        "LIVE_AUTHORIZED=false",
        "SCALING_AUTHORIZED=false",
    ]
    exceeded = observed > bound_amount
    if exceeded:
        reasons.append("OBSERVED_FEE_EXCEEDS_INTERNAL_CONSERVATIVE_BOUND")
        status = "FAIL_CLOSED_BOUND_EXCEEDED_REVIEW_REQUIRED"
    else:
        reasons.append("OBSERVED_FEE_WITHIN_INTERNAL_CONSERVATIVE_BOUND")
        status = "RECONCILIATION_PASS_NORMATIVE_TRUTH_UNCHANGED"

    return ObservedExpiryFeeReconciliationV1(
        reconciliation_status=status,
        fail_closed=exceeded,
        scaling_blocked=True,
        further_canary_requires_review=exceeded,
        observed_fee_amount=format(observed, "f"),
        bound_amount=format(bound_amount, "f"),
        observed_fee_rewrote_normative_truth=False,
        proven_normal_expiry_rate=format(PROVEN_NORMAL_EXPIRY_RATE, "f"),
        oem_fee_monetary_base_status=OEM_FEE_MONETARY_BASE_STATUS,
        actual_expiry_fee_amount_status=ACTUAL_EXPIRY_FEE_AMOUNT_STATUS,
        operative_expiry_fee_rate=OPERATIVE_EXPIRY_FEE_RATE,
        live_authorized=False,
        testnet_authorized=False,
        order_effect="NONE",
        reasons=tuple(reasons),
    )
