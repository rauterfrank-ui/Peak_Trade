"""§11.13.5.Z2D remaining UNPROVEN Position-Value / FX / Rounding chain.

INTERNAL_POLICY / CLASSIFICATION only. Does not invent an OKX PositionValue
formula, USD/USDC conversion, or USDC rounding precision. Does not authorize
Live, Testnet, orders, funding, scaling, or Multi-Future.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    AUTHORIZATION_SCOPE,
    DEFAULT_INSTRUMENT_ID,
    LIVE_AUTHORIZED,
    MINIMUM_RATIFIED_NOTIONAL_ONLY,
    SETTLEMENT_ACCOUNT_TRUTH,
    TESTNET_AUTHORIZED,
    assert_live_canary_instrument_binding_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.expiry_fee_economic_uncertainty_bound_v1 import (
    PEAK_TRADE_INTERNAL_NOTIONAL_ENVELOPE_FORM,
    PEAK_TRADE_INTERNAL_NOTIONAL_ENVELOPE_ROLE,
    PEAK_TRADE_INTERNAL_NOTIONAL_UNIT,
    QTY_LIMIT,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.exposure_v1 import (
    derive_min_executable_notional_v1,
)

# Exchange Truth. Related documented OKX formulas remain distinct objects and
# are not silently equated to X-Perp expiration-delivery PositionValue.
OKX_POSITION_VALUE_ALGEBRA_STATUS = "UNPROVEN"
OKX_POSITION_VALUE_ALGEBRA = "UNPROVEN"
LINEAR_VS_INVERSE_FOR_EXPIRATION_DELIVERY = "UNPROVEN"
SETTLEMENT_CURRENCY_OF_THE_FEE_USD_VS_USDC = "UNPROVEN"
CONTRACT_MULTIPLIER_FOR_THIS_INSTRUMENT = "UNPROVEN"
CONTRACT_SIZE_CTVAL_FOR_THIS_INSTRUMENT_IN_DELIVERY_FEE = "UNPROVEN"
PRICE_OPERAND_DELIVERYPX_VS_MARKPX_VS_FILL = "UNPROVEN"
ABSOLUTE_VALUE_CONVENTION = "UNPROVEN"
POSITION_SIGN_CONVENTION_FOR_FEE_MAGNITUDE = "UNPROVEN"
PEAK_TRADE_INTERNAL_POSITION_VALUE_IS_OKX_POSITION_VALUE = False
EXCHANGE_TRUTH_CHANGED = False

# Peak_Trade Internal Conservative Policy. Reuses the existing §11.13.5.U
# envelope already bound by Z2C. This is not a second formula.
PEAK_TRADE_U_NOTIONAL_FORM = PEAK_TRADE_INTERNAL_NOTIONAL_ENVELOPE_FORM
PEAK_TRADE_INTERNAL_POSITION_VALUE_ENVELOPE_ROLE = PEAK_TRADE_INTERNAL_NOTIONAL_ENVELOPE_ROLE
PUBLIC_SETTLE_CCY = "USD"
ACCOUNT_SETTLE_CCY = SETTLEMENT_ACCOUNT_TRUTH
RULE_FX = "FX-VENUE-CONVERT"
RULE_FX_STATUS = "UNPROVEN"
USD_AND_USDC_REMAIN_STRICTLY_DISTINCT_UNITS = True
USD_USDC_PARITY_ASSUMED = False
USD_USDC_CONVERSION_APPLIED = False
COVER_USDC_STATUS = "UNINSTANTIATED"
RULE_OUTPUT_UNIT = "FX-STATE-ALL-FINAL-FUNDS-IN-USDC"
RULE_ROUNDING = "RND-CEIL-VENUE-CCY-PRECISION-AFTER-COMPOSITION"
RULE_ROUNDING_STATUS = "UNPROVEN"
ROUNDING_APPLIED = False
USDC_PRECISION_STATUS = "UNPROVEN"
TICK_SZ_IS_NOT_USDC_PRECISION = True
MINIMUM_EXPOSURE_ONLY = True
SCALING_AUTHORIZED = False
MULTI_FUTURE_AUTHORIZED = False

REQUIRED_PROVEN_LOCAL_QUANTITIES: tuple[str, ...] = (
    "quantity",
    "instrument_ct_val",
    "reference_price",
    "instrument_id",
    "authorization_scope",
)


class PositionValueFxRoundingChainError(RuntimeError):
    """Fail-closed Position-Value / FX / Rounding chain violation."""


@dataclass(frozen=True)
class QtyOnePositionValueFxRoundingChainV1:
    chain_status: str
    okx_position_value_algebra_status: str
    peak_trade_internal_position_value_envelope: str
    peak_trade_internal_position_value_envelope_form: str
    peak_trade_internal_position_value_envelope_role: str
    peak_trade_internal_position_value_is_okx_position_value: bool
    envelope_unit: str
    public_settle_ccy: str
    account_settle_ccy: str
    rule_fx: str
    rule_fx_status: str
    usd_usdc_parity_assumed: bool
    usd_usdc_conversion_applied: bool
    cover_usdc_status: str
    rule_rounding: str
    rule_rounding_status: str
    rounding_applied: bool
    usdc_precision_status: str
    tick_sz_is_not_usdc_precision: bool
    exchange_truth_changed: bool
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

    def to_dict(self) -> dict[str, Any]:
        return {
            "CHAIN_STATUS": self.chain_status,
            "OKX_POSITION_VALUE_ALGEBRA_STATUS": self.okx_position_value_algebra_status,
            "PEAK_TRADE_INTERNAL_POSITION_VALUE_ENVELOPE": (
                self.peak_trade_internal_position_value_envelope
            ),
            "PEAK_TRADE_INTERNAL_POSITION_VALUE_ENVELOPE_FORM": (
                self.peak_trade_internal_position_value_envelope_form
            ),
            "PEAK_TRADE_INTERNAL_POSITION_VALUE_ENVELOPE_ROLE": (
                self.peak_trade_internal_position_value_envelope_role
            ),
            "PEAK_TRADE_INTERNAL_POSITION_VALUE_IS_OKX_POSITION_VALUE": (
                self.peak_trade_internal_position_value_is_okx_position_value
            ),
            "ENVELOPE_UNIT": self.envelope_unit,
            "PUBLIC_SETTLE_CCY": self.public_settle_ccy,
            "ACCOUNT_SETTLE_CCY": self.account_settle_ccy,
            "RULE_FX": self.rule_fx,
            "RULE_FX_STATUS": self.rule_fx_status,
            "USD_USDC_PARITY_ASSUMED": self.usd_usdc_parity_assumed,
            "USD_USDC_CONVERSION_APPLIED": self.usd_usdc_conversion_applied,
            "COVER_USDC_STATUS": self.cover_usdc_status,
            "RULE_ROUNDING": self.rule_rounding,
            "RULE_ROUNDING_STATUS": self.rule_rounding_status,
            "ROUNDING_APPLIED": self.rounding_applied,
            "USDC_PRECISION_STATUS": self.usdc_precision_status,
            "TICK_SZ_IS_NOT_USDC_PRECISION": self.tick_sz_is_not_usdc_precision,
            "EXCHANGE_TRUTH_CHANGED": self.exchange_truth_changed,
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
        }


def _require_positive_decimal(raw: str | None, *, field: str) -> Decimal:
    text = str(raw or "").strip()
    if not text:
        raise PositionValueFxRoundingChainError(f"MISSING_PROVEN_LOCAL_QUANTITY:{field}")
    try:
        value = Decimal(text)
    except (InvalidOperation, TypeError) as exc:
        raise PositionValueFxRoundingChainError(f"MISSING_PROVEN_LOCAL_QUANTITY:{field}") from exc
    if value <= 0:
        raise PositionValueFxRoundingChainError(f"MISSING_PROVEN_LOCAL_QUANTITY:{field}")
    return value


def classify_qty_one_position_value_fx_rounding_chain_v1(
    *,
    quantity: str | None,
    instrument_ct_val: str | None,
    reference_price: str | None,
    instrument_id: str | None,
    authorization_scope: str | None,
    instrument_min_sz: str | None = "1",
    instrument_tick_sz: str | None = None,
    multi_future_requested: bool = False,
    claim_okx_position_value: bool = False,
    apply_usd_usdc_conversion: bool = False,
    assume_usd_equals_usdc: bool = False,
    apply_rounding: bool = False,
    treat_tick_sz_as_usdc_precision: bool = False,
) -> QtyOnePositionValueFxRoundingChainV1:
    """Classify the remaining UNPROVEN chain and bind the qty=1 internal policy.

    Reuses the existing Peak_Trade notional envelope ``qty * ctVal * markPx``.
    That envelope is **not** an OKX expiration-delivery PositionValue.
    FX conversion and rounding are **not** applied.
    """

    if claim_okx_position_value:
        raise PositionValueFxRoundingChainError("OKX_POSITION_VALUE_ALGEBRA_REMAINS_UNPROVEN")
    if assume_usd_equals_usdc or apply_usd_usdc_conversion:
        raise PositionValueFxRoundingChainError("USD_USDC_CONVERSION_UNPROVEN")
    if apply_rounding or treat_tick_sz_as_usdc_precision:
        raise PositionValueFxRoundingChainError("USDC_ROUNDING_PRECISION_UNPROVEN")

    scope = str(authorization_scope or "").strip()
    if not scope:
        raise PositionValueFxRoundingChainError("MISSING_PROVEN_LOCAL_QUANTITY:authorization_scope")
    if scope != AUTHORIZATION_SCOPE:
        raise PositionValueFxRoundingChainError(f"SCOPE_NOT_MINIMUM_EXPOSURE_CANARY:{scope}")

    iid = str(instrument_id or "").strip()
    if not iid:
        raise PositionValueFxRoundingChainError("MISSING_PROVEN_LOCAL_QUANTITY:instrument_id")
    assert_live_canary_instrument_binding_v1(instrument_id=iid)
    if iid != DEFAULT_INSTRUMENT_ID:
        raise PositionValueFxRoundingChainError(f"INSTRUMENT_BINDING_MISMATCH:{iid}")

    if multi_future_requested or not MINIMUM_RATIFIED_NOTIONAL_ONLY:
        raise PositionValueFxRoundingChainError("MULTI_FUTURE_NOT_AUTHORIZED")

    qty = _require_positive_decimal(quantity, field="quantity")
    min_sz = _require_positive_decimal(instrument_min_sz, field="instrument_min_sz")
    if qty != QTY_LIMIT or qty != min_sz:
        raise PositionValueFxRoundingChainError("QTY_NOT_MINIMUM_EXPOSURE_CANARY_LIMIT")

    _require_positive_decimal(instrument_ct_val, field="instrument_ct_val")
    _require_positive_decimal(reference_price, field="reference_price")
    if instrument_tick_sz is not None and str(instrument_tick_sz).strip():
        _require_positive_decimal(instrument_tick_sz, field="instrument_tick_sz")

    envelope = Decimal(
        derive_min_executable_notional_v1(
            quantity=str(quantity),
            reference_price=str(reference_price),
            instrument_ct_val=str(instrument_ct_val),
        )
    )
    if envelope <= 0:
        raise PositionValueFxRoundingChainError("MISSING_PROVEN_LOCAL_QUANTITY:internal_envelope")

    return QtyOnePositionValueFxRoundingChainV1(
        chain_status=("INTERNAL_QTY1_CONSERVATIVE_POLICY_BOUND_EXCHANGE_TRUTH_UNPROVEN"),
        okx_position_value_algebra_status=OKX_POSITION_VALUE_ALGEBRA_STATUS,
        peak_trade_internal_position_value_envelope=format(envelope, "f"),
        peak_trade_internal_position_value_envelope_form=PEAK_TRADE_U_NOTIONAL_FORM,
        peak_trade_internal_position_value_envelope_role=(
            PEAK_TRADE_INTERNAL_POSITION_VALUE_ENVELOPE_ROLE
        ),
        peak_trade_internal_position_value_is_okx_position_value=(
            PEAK_TRADE_INTERNAL_POSITION_VALUE_IS_OKX_POSITION_VALUE
        ),
        envelope_unit=PEAK_TRADE_INTERNAL_NOTIONAL_UNIT,
        public_settle_ccy=PUBLIC_SETTLE_CCY,
        account_settle_ccy=ACCOUNT_SETTLE_CCY,
        rule_fx=RULE_FX,
        rule_fx_status=RULE_FX_STATUS,
        usd_usdc_parity_assumed=USD_USDC_PARITY_ASSUMED,
        usd_usdc_conversion_applied=USD_USDC_CONVERSION_APPLIED,
        cover_usdc_status=COVER_USDC_STATUS,
        rule_rounding=RULE_ROUNDING,
        rule_rounding_status=RULE_ROUNDING_STATUS,
        rounding_applied=ROUNDING_APPLIED,
        usdc_precision_status=USDC_PRECISION_STATUS,
        tick_sz_is_not_usdc_precision=TICK_SZ_IS_NOT_USDC_PRECISION,
        exchange_truth_changed=EXCHANGE_TRUTH_CHANGED,
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
    )
