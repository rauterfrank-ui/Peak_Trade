"""§11.13.5.Z2F bind uninstantiated B08 term instances and FX / rounding.

CONTRACT / GOVERNANCE only. Adjudicates already-ratified Z2E terms against
canonical evidence. Does not invent OKX fee truth, a monetary base, USD/USDC
conversion, USDC rounding, COVER_USDC, or a numeric funding amount. Does not
authorize Live, Testnet, orders, funding, GET, scaling, or Multi-Future.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    AUTHORIZATION_SCOPE,
    LIVE_AUTHORIZED,
    MINIMUM_RATIFIED_NOTIONAL_ONLY,
    TESTNET_AUTHORIZED,
    assert_live_canary_instrument_binding_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.exact_formula_body_v1 import (
    API_DELIVERY_0_0003_STATUS,
    B08_EXACT_FORMULA_BODY_KIND,
    B08_EXACT_FORMULA_BODY_STATUS,
    DELIVERY_COVER_INTERNAL_STATUS,
    EXACT_OKX_FEE_FORMULA_STATUS,
    FEE_RESERVE_RATES_STATUS,
    MM_LIQ_BUFFER_STATUS,
    NUMERIC_FUNDING_AMOUNT,
    SLIPPAGE_RESERVE_STATUS,
    SUM_INTERNAL_NUMERIC_STATUS,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.expiry_fee_economic_uncertainty_bound_v1 import (
    PEAK_TRADE_EXPIRY_RESERVE_RATE,
    PEAK_TRADE_EXPIRY_RESERVE_RATE_IS_OKX_FEE_TRUTH,
    PEAK_TRADE_EXPIRY_RESERVE_RATE_SOURCE,
    PROVEN_NORMAL_EXPIRY_RATE,
    QTY_LIMIT,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.position_value_fx_rounding_chain_v1 import (
    COVER_USDC_STATUS,
    EXCHANGE_TRUTH_CHANGED,
    MULTI_FUTURE_AUTHORIZED,
    OKX_POSITION_VALUE_ALGEBRA_STATUS,
    PEAK_TRADE_INTERNAL_POSITION_VALUE_IS_OKX_POSITION_VALUE,
    ROUNDING_APPLIED,
    RULE_FX,
    RULE_FX_STATUS,
    RULE_ROUNDING,
    RULE_ROUNDING_STATUS,
    SCALING_AUTHORIZED,
    TICK_SZ_IS_NOT_USDC_PRECISION,
    USD_USDC_CONVERSION_APPLIED,
    USD_USDC_PARITY_ASSUMED,
    USDC_PRECISION_STATUS,
)

KIND_PROVEN = "PROVEN"
KIND_INTERNAL_POLICY = "INTERNAL_POLICY"
KIND_UNPROVEN = "UNPROVEN"

QTY_TERM_STATUS = "PROVEN"
QTY_TERM_KIND = KIND_PROVEN
QTY_BOUND_VALUE = "1"
QTY_ROLE = "CANARY_SCOPE_QTY_ONE_NO_SCALING"

CTVAL_TERM_STATUS = "PROVEN"
CTVAL_TERM_KIND = KIND_PROVEN
CTVAL_BOUND_VALUE = "0.0001"
CTVAL_BOUND_CCY = "BTC"
CTVAL_ROLE = "CANONICAL_INSTRUMENT_METADATA_NOT_OKX_DELIVERY_POSITION_VALUE_OPERAND"
CTVAL_DELIVERY_FEE_OPERAND_STATUS = "UNPROVEN"

MARKPX_TERM_STATUS = "UNINSTANTIATED"
MARKPX_TERM_KIND = KIND_UNPROVEN
MARKPX_ROLE = "RUNTIME_TERM_NOT_CURRENT_VALUE"
MARKPX_CURRENT_VALUE = "UNINSTANTIATED"
HISTORICAL_L_PACK_MARKPX = "63043.7"
HISTORICAL_S_PACK_MARKPX = "62986.2"
HISTORICAL_MARKPX_IS_NOT_CURRENT = True
NO_LIVE_MARKPX_GET_THIS_STEP = True

MONETARY_BASE_STATUS = "UNPROVEN"
MONETARY_BASE_KIND = KIND_UNPROVEN

FX_STATUS = "UNPROVEN"
FX_KIND = KIND_UNPROVEN
FX_APPLIED = USD_USDC_CONVERSION_APPLIED
NORMATIVE_USD_USDC_CONVERSION_DEFINED_FOR_EXPIRY_COVER = False

ROUNDING_STATUS = "UNPROVEN"
ROUNDING_KIND = KIND_UNPROVEN
ROUNDING_PRECISION_STATUS = "UNPROVEN"
ROUNDING_DECIMAL_PLACES_STATUS = "UNPROVEN"
ROUNDING_TICK_LOT_DERIVED_STATUS = "UNPROVEN"
ROUNDING_CEIL_FLOOR_NEAREST_STATUS = "UNPROVEN"
ROUNDING_CURRENCY_PRECISION_STATUS = USDC_PRECISION_STATUS

NORMAL_EXPIRY_RATE_0_0001_STATUS = "PROVEN_APPLICABILITY_NON_OPERATIVE"
CONSERVATIVE_RATE_0_0003_STATUS = "INTERNAL_CONSERVATIVE_POLICY_NOT_EXCHANGE_TRUTH"
CONSERVATIVE_RATE_KIND = KIND_INTERNAL_POLICY

FEE_RESERVE_RATES_INSTANCE_STATUS = FEE_RESERVE_RATES_STATUS
SLIPPAGE_RESERVE_INSTANCE_STATUS = SLIPPAGE_RESERVE_STATUS
MM_LIQ_BUFFER_INSTANCE_STATUS = MM_LIQ_BUFFER_STATUS
DELIVERY_COVER_INTERNAL_INSTANCE_STATUS = DELIVERY_COVER_INTERNAL_STATUS
SUM_INTERNAL_NUMERIC_INSTANCE_STATUS = SUM_INTERNAL_NUMERIC_STATUS
NUMERIC_FUNDING_AMOUNT_PRODUCED = False
MINIMUM_EXPOSURE_ONLY = True
CANONICAL_CTVAL = Decimal("0.0001")


class FormulaTermInstanceBindingError(RuntimeError):
    """Fail-closed B08 term-instance / FX / rounding adjudication violation."""


@dataclass(frozen=True)
class QtyOneFormulaTermInstanceBindingV1:
    qty_term_status: str
    qty_term_kind: str
    qty_bound_value: str
    ctval_term_status: str
    ctval_term_kind: str
    ctval_bound_value: str
    ctval_bound_ccy: str
    ctval_role: str
    ctval_delivery_fee_operand_status: str
    markpx_term_status: str
    markpx_term_kind: str
    markpx_role: str
    markpx_current_value: str
    historical_markpx_is_not_current: bool
    no_live_markpx_get_this_step: bool
    monetary_base_status: str
    monetary_base_kind: str
    fx_status: str
    fx_kind: str
    fx_applied: bool
    rule_fx: str
    rule_fx_status: str
    usd_usdc_parity_assumed: bool
    usd_usdc_conversion_applied: bool
    normative_usd_usdc_conversion_defined_for_expiry_cover: bool
    rounding_status: str
    rounding_kind: str
    rounding_applied: bool
    rule_rounding: str
    rule_rounding_status: str
    rounding_precision_status: str
    rounding_decimal_places_status: str
    rounding_tick_lot_derived_status: str
    rounding_ceil_floor_nearest_status: str
    rounding_currency_precision_status: str
    tick_sz_is_not_usdc_precision: bool
    normal_expiry_rate_0_0001_status: str
    proven_normal_expiry_rate: str
    conservative_rate_0_0003_status: str
    conservative_rate_kind: str
    conservative_reserve_rate: str
    conservative_reserve_rate_is_okx_fee_truth: bool
    conservative_reserve_rate_source: str
    exact_okx_fee_formula_status: str
    position_value_algebra_status: str
    b08_internal_algebra_status: str
    b08_exact_formula_body_kind: str
    api_delivery_0_0003_status: str
    fee_reserve_rates_instance_status: str
    delivery_cover_internal_instance_status: str
    slippage_reserve_instance_status: str
    mm_liq_buffer_instance_status: str
    sum_internal_numeric_instance_status: str
    cover_usdc_status: str
    numeric_funding_amount: str
    numeric_funding_amount_produced: bool
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
            "QTY_TERM_STATUS": self.qty_term_status,
            "QTY_TERM_KIND": self.qty_term_kind,
            "QTY_BOUND_VALUE": self.qty_bound_value,
            "CTVAL_TERM_STATUS": self.ctval_term_status,
            "CTVAL_TERM_KIND": self.ctval_term_kind,
            "CTVAL_BOUND_VALUE": self.ctval_bound_value,
            "CTVAL_BOUND_CCY": self.ctval_bound_ccy,
            "CTVAL_ROLE": self.ctval_role,
            "CTVAL_DELIVERY_FEE_OPERAND_STATUS": self.ctval_delivery_fee_operand_status,
            "MARKPX_TERM_STATUS": self.markpx_term_status,
            "MARKPX_TERM_KIND": self.markpx_term_kind,
            "MARKPX_ROLE": self.markpx_role,
            "MARKPX_CURRENT_VALUE": self.markpx_current_value,
            "HISTORICAL_MARKPX_IS_NOT_CURRENT": self.historical_markpx_is_not_current,
            "NO_LIVE_MARKPX_GET_THIS_STEP": self.no_live_markpx_get_this_step,
            "MONETARY_BASE_STATUS": self.monetary_base_status,
            "MONETARY_BASE_KIND": self.monetary_base_kind,
            "FX_STATUS": self.fx_status,
            "FX_KIND": self.fx_kind,
            "FX_APPLIED": self.fx_applied,
            "RULE_FX": self.rule_fx,
            "RULE_FX_STATUS": self.rule_fx_status,
            "USD_USDC_PARITY_ASSUMED": self.usd_usdc_parity_assumed,
            "USD_USDC_CONVERSION_APPLIED": self.usd_usdc_conversion_applied,
            "NORMATIVE_USD_USDC_CONVERSION_DEFINED_FOR_EXPIRY_COVER": (
                self.normative_usd_usdc_conversion_defined_for_expiry_cover
            ),
            "ROUNDING_STATUS": self.rounding_status,
            "ROUNDING_KIND": self.rounding_kind,
            "ROUNDING_APPLIED": self.rounding_applied,
            "RULE_ROUNDING": self.rule_rounding,
            "RULE_ROUNDING_STATUS": self.rule_rounding_status,
            "ROUNDING_PRECISION_STATUS": self.rounding_precision_status,
            "ROUNDING_DECIMAL_PLACES_STATUS": self.rounding_decimal_places_status,
            "ROUNDING_TICK_LOT_DERIVED_STATUS": self.rounding_tick_lot_derived_status,
            "ROUNDING_CEIL_FLOOR_NEAREST_STATUS": self.rounding_ceil_floor_nearest_status,
            "ROUNDING_CURRENCY_PRECISION_STATUS": self.rounding_currency_precision_status,
            "TICK_SZ_IS_NOT_USDC_PRECISION": self.tick_sz_is_not_usdc_precision,
            "NORMAL_EXPIRY_RATE_0_0001_STATUS": self.normal_expiry_rate_0_0001_status,
            "PROVEN_NORMAL_EXPIRY_RATE": self.proven_normal_expiry_rate,
            "CONSERVATIVE_RATE_0_0003_STATUS": self.conservative_rate_0_0003_status,
            "CONSERVATIVE_RATE_KIND": self.conservative_rate_kind,
            "PEAK_TRADE_EXPIRY_RESERVE_RATE": self.conservative_reserve_rate,
            "PEAK_TRADE_EXPIRY_RESERVE_RATE_IS_OKX_FEE_TRUTH": (
                self.conservative_reserve_rate_is_okx_fee_truth
            ),
            "PEAK_TRADE_EXPIRY_RESERVE_RATE_SOURCE": (self.conservative_reserve_rate_source),
            "EXACT_OKX_FEE_FORMULA_STATUS": self.exact_okx_fee_formula_status,
            "POSITION_VALUE_ALGEBRA_STATUS": self.position_value_algebra_status,
            "B08_INTERNAL_ALGEBRA_STATUS": self.b08_internal_algebra_status,
            "B08_EXACT_FORMULA_BODY_KIND": self.b08_exact_formula_body_kind,
            "API_DELIVERY_0_0003_STATUS": self.api_delivery_0_0003_status,
            "FEE_RESERVE_RATES_INSTANCE_STATUS": self.fee_reserve_rates_instance_status,
            "DELIVERY_COVER_INTERNAL_INSTANCE_STATUS": (
                self.delivery_cover_internal_instance_status
            ),
            "SLIPPAGE_RESERVE_INSTANCE_STATUS": self.slippage_reserve_instance_status,
            "MM_LIQ_BUFFER_INSTANCE_STATUS": self.mm_liq_buffer_instance_status,
            "SUM_INTERNAL_NUMERIC_INSTANCE_STATUS": self.sum_internal_numeric_instance_status,
            "COVER_USDC_STATUS": self.cover_usdc_status,
            "NUMERIC_FUNDING_AMOUNT": self.numeric_funding_amount,
            "NUMERIC_FUNDING_AMOUNT_PRODUCED": self.numeric_funding_amount_produced,
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
        raise FormulaTermInstanceBindingError(f"MISSING_PROVEN_LOCAL_QUANTITY:{field}")
    try:
        value = Decimal(text)
    except (InvalidOperation, TypeError) as exc:
        raise FormulaTermInstanceBindingError(f"MISSING_PROVEN_LOCAL_QUANTITY:{field}") from exc
    if value <= 0:
        raise FormulaTermInstanceBindingError(f"MISSING_PROVEN_LOCAL_QUANTITY:{field}")
    return value


def bind_qty_one_uninstantiated_formula_term_instances_v1(
    *,
    quantity: str | None,
    instrument_ct_val: str | None,
    instrument_id: str | None,
    authorization_scope: str | None,
    instrument_min_sz: str | None = "1",
    current_mark_px: str | None = None,
    freeze_historical_mark_px_as_current: bool = False,
    execute_live_mark_px_get: bool = False,
    multi_future_requested: bool = False,
    claim_okx_position_value: bool = False,
    apply_usd_usdc_conversion: bool = False,
    assume_usd_equals_usdc: bool = False,
    apply_rounding: bool = False,
    invent_rounding_precision: bool = False,
    treat_tick_sz_as_usdc_precision: bool = False,
    claim_0003_is_okx_fee_truth: bool = False,
    reset_conservative_rate_to_0001: bool = False,
    consume_0001_as_operative_fee_input: bool = False,
    instantiate_cover_usdc: bool = False,
    invent_monetary_base: bool = False,
    freeze_section_w_fee_rates: bool = False,
    instantiate_slippage: bool = False,
    instantiate_mm_liq: bool = False,
    produce_numeric_funding_amount: bool = False,
) -> QtyOneFormulaTermInstanceBindingV1:
    """Bind proven qty/ctVal instances and leave COVER_USDC uninstantiated.

    markPx remains a runtime term. Historical L/S-pack prices are not current.
    FX and rounding remain UNPROVEN Exchange Truth. No conversion or rounding
    step is applied. No numeric funding amount is produced.
    """

    if claim_0003_is_okx_fee_truth or PEAK_TRADE_EXPIRY_RESERVE_RATE_IS_OKX_FEE_TRUTH:
        raise FormulaTermInstanceBindingError("PEAK_TRADE_EXPIRY_RESERVE_RATE_IS_NOT_OKX_FEE_TRUTH")
    if reset_conservative_rate_to_0001:
        raise FormulaTermInstanceBindingError("CONSERVATIVE_RATE_0_0003_REMAINS_INTERNAL_POLICY")
    if consume_0001_as_operative_fee_input:
        raise FormulaTermInstanceBindingError("PROVEN_NORMAL_EXPIRY_RATE_IS_NON_OPERATIVE")
    if invent_monetary_base:
        raise FormulaTermInstanceBindingError("MONETARY_BASE_REMAINS_UNPROVEN")
    if claim_okx_position_value or PEAK_TRADE_INTERNAL_POSITION_VALUE_IS_OKX_POSITION_VALUE:
        raise FormulaTermInstanceBindingError("OKX_POSITION_VALUE_ALGEBRA_REMAINS_UNPROVEN")
    if (
        apply_usd_usdc_conversion
        or assume_usd_equals_usdc
        or USD_USDC_PARITY_ASSUMED
        or USD_USDC_CONVERSION_APPLIED
        or NORMATIVE_USD_USDC_CONVERSION_DEFINED_FOR_EXPIRY_COVER
    ):
        raise FormulaTermInstanceBindingError("USD_USDC_CONVERSION_UNPROVEN")
    if (
        apply_rounding
        or invent_rounding_precision
        or treat_tick_sz_as_usdc_precision
        or ROUNDING_APPLIED
        or not TICK_SZ_IS_NOT_USDC_PRECISION
    ):
        raise FormulaTermInstanceBindingError("USDC_ROUNDING_PRECISION_UNPROVEN")
    if instantiate_cover_usdc:
        raise FormulaTermInstanceBindingError("COVER_USDC_REMAINS_UNINSTANTIATED")
    if freeze_section_w_fee_rates:
        raise FormulaTermInstanceBindingError("SECTION_W_FEE_RATES_NOT_FROZEN")
    if instantiate_slippage:
        raise FormulaTermInstanceBindingError("SLIPPAGE_RESERVE_UNINSTANTIATED")
    if instantiate_mm_liq:
        raise FormulaTermInstanceBindingError("MM_LIQ_BUFFER_UNINSTANTIATED")
    if produce_numeric_funding_amount or NUMERIC_FUNDING_AMOUNT_PRODUCED:
        raise FormulaTermInstanceBindingError("NUMERIC_FUNDING_AMOUNT_REMAINS_UNPROVEN")
    if freeze_historical_mark_px_as_current:
        raise FormulaTermInstanceBindingError("HISTORICAL_MARKPX_IS_NOT_CURRENT")
    if execute_live_mark_px_get:
        raise FormulaTermInstanceBindingError("LIVE_MARKPX_GET_NOT_AUTHORIZED")
    current_px = str(current_mark_px or "").strip()
    if current_px:
        raise FormulaTermInstanceBindingError("MARKPX_CURRENT_VALUE_REMAINS_UNINSTANTIATED")

    scope = str(authorization_scope or "").strip()
    if not scope:
        raise FormulaTermInstanceBindingError("MISSING_PROVEN_LOCAL_QUANTITY:authorization_scope")
    if scope != AUTHORIZATION_SCOPE:
        raise FormulaTermInstanceBindingError(f"SCOPE_NOT_MINIMUM_EXPOSURE_CANARY:{scope}")

    iid = str(instrument_id or "").strip()
    if not iid:
        raise FormulaTermInstanceBindingError("MISSING_PROVEN_LOCAL_QUANTITY:instrument_id")
    assert_live_canary_instrument_binding_v1(instrument_id=iid)

    if multi_future_requested or not MINIMUM_RATIFIED_NOTIONAL_ONLY:
        raise FormulaTermInstanceBindingError("MULTI_FUTURE_NOT_AUTHORIZED")

    qty = _require_positive_decimal(quantity, field="quantity")
    min_sz = _require_positive_decimal(instrument_min_sz, field="instrument_min_sz")
    if qty != QTY_LIMIT or qty != min_sz:
        raise FormulaTermInstanceBindingError("QTY_NOT_MINIMUM_EXPOSURE_CANARY_LIMIT")

    ct_val = _require_positive_decimal(instrument_ct_val, field="instrument_ct_val")
    if ct_val != CANONICAL_CTVAL:
        raise FormulaTermInstanceBindingError("CTVAL_NOT_CANONICAL_INSTRUMENT_METADATA")

    return QtyOneFormulaTermInstanceBindingV1(
        qty_term_status=QTY_TERM_STATUS,
        qty_term_kind=QTY_TERM_KIND,
        qty_bound_value=QTY_BOUND_VALUE,
        ctval_term_status=CTVAL_TERM_STATUS,
        ctval_term_kind=CTVAL_TERM_KIND,
        ctval_bound_value=CTVAL_BOUND_VALUE,
        ctval_bound_ccy=CTVAL_BOUND_CCY,
        ctval_role=CTVAL_ROLE,
        ctval_delivery_fee_operand_status=CTVAL_DELIVERY_FEE_OPERAND_STATUS,
        markpx_term_status=MARKPX_TERM_STATUS,
        markpx_term_kind=MARKPX_TERM_KIND,
        markpx_role=MARKPX_ROLE,
        markpx_current_value=MARKPX_CURRENT_VALUE,
        historical_markpx_is_not_current=HISTORICAL_MARKPX_IS_NOT_CURRENT,
        no_live_markpx_get_this_step=NO_LIVE_MARKPX_GET_THIS_STEP,
        monetary_base_status=MONETARY_BASE_STATUS,
        monetary_base_kind=MONETARY_BASE_KIND,
        fx_status=FX_STATUS,
        fx_kind=FX_KIND,
        fx_applied=FX_APPLIED,
        rule_fx=RULE_FX,
        rule_fx_status=RULE_FX_STATUS,
        usd_usdc_parity_assumed=USD_USDC_PARITY_ASSUMED,
        usd_usdc_conversion_applied=USD_USDC_CONVERSION_APPLIED,
        normative_usd_usdc_conversion_defined_for_expiry_cover=(
            NORMATIVE_USD_USDC_CONVERSION_DEFINED_FOR_EXPIRY_COVER
        ),
        rounding_status=ROUNDING_STATUS,
        rounding_kind=ROUNDING_KIND,
        rounding_applied=ROUNDING_APPLIED,
        rule_rounding=RULE_ROUNDING,
        rule_rounding_status=RULE_ROUNDING_STATUS,
        rounding_precision_status=ROUNDING_PRECISION_STATUS,
        rounding_decimal_places_status=ROUNDING_DECIMAL_PLACES_STATUS,
        rounding_tick_lot_derived_status=ROUNDING_TICK_LOT_DERIVED_STATUS,
        rounding_ceil_floor_nearest_status=ROUNDING_CEIL_FLOOR_NEAREST_STATUS,
        rounding_currency_precision_status=ROUNDING_CURRENCY_PRECISION_STATUS,
        tick_sz_is_not_usdc_precision=TICK_SZ_IS_NOT_USDC_PRECISION,
        normal_expiry_rate_0_0001_status=NORMAL_EXPIRY_RATE_0_0001_STATUS,
        proven_normal_expiry_rate=format(PROVEN_NORMAL_EXPIRY_RATE, "f"),
        conservative_rate_0_0003_status=CONSERVATIVE_RATE_0_0003_STATUS,
        conservative_rate_kind=CONSERVATIVE_RATE_KIND,
        conservative_reserve_rate=format(PEAK_TRADE_EXPIRY_RESERVE_RATE, "f"),
        conservative_reserve_rate_is_okx_fee_truth=(
            PEAK_TRADE_EXPIRY_RESERVE_RATE_IS_OKX_FEE_TRUTH
        ),
        conservative_reserve_rate_source=PEAK_TRADE_EXPIRY_RESERVE_RATE_SOURCE,
        exact_okx_fee_formula_status=EXACT_OKX_FEE_FORMULA_STATUS,
        position_value_algebra_status=OKX_POSITION_VALUE_ALGEBRA_STATUS,
        b08_internal_algebra_status=B08_EXACT_FORMULA_BODY_STATUS,
        b08_exact_formula_body_kind=B08_EXACT_FORMULA_BODY_KIND,
        api_delivery_0_0003_status=API_DELIVERY_0_0003_STATUS,
        fee_reserve_rates_instance_status=FEE_RESERVE_RATES_INSTANCE_STATUS,
        delivery_cover_internal_instance_status=DELIVERY_COVER_INTERNAL_INSTANCE_STATUS,
        slippage_reserve_instance_status=SLIPPAGE_RESERVE_INSTANCE_STATUS,
        mm_liq_buffer_instance_status=MM_LIQ_BUFFER_INSTANCE_STATUS,
        sum_internal_numeric_instance_status=SUM_INTERNAL_NUMERIC_INSTANCE_STATUS,
        cover_usdc_status=COVER_USDC_STATUS,
        numeric_funding_amount=NUMERIC_FUNDING_AMOUNT,
        numeric_funding_amount_produced=NUMERIC_FUNDING_AMOUNT_PRODUCED,
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


__all__ = (
    "B08_EXACT_FORMULA_BODY_KIND",
    "B08_EXACT_FORMULA_BODY_STATUS",
    "CANONICAL_CTVAL",
    "CONSERVATIVE_RATE_0_0003_STATUS",
    "CONSERVATIVE_RATE_KIND",
    "COVER_USDC_STATUS",
    "CTVAL_BOUND_CCY",
    "CTVAL_BOUND_VALUE",
    "CTVAL_DELIVERY_FEE_OPERAND_STATUS",
    "CTVAL_ROLE",
    "CTVAL_TERM_KIND",
    "CTVAL_TERM_STATUS",
    "EXACT_OKX_FEE_FORMULA_STATUS",
    "EXCHANGE_TRUTH_CHANGED",
    "FX_KIND",
    "FX_STATUS",
    "FormulaTermInstanceBindingError",
    "HISTORICAL_L_PACK_MARKPX",
    "HISTORICAL_S_PACK_MARKPX",
    "KIND_INTERNAL_POLICY",
    "KIND_PROVEN",
    "KIND_UNPROVEN",
    "MARKPX_CURRENT_VALUE",
    "MARKPX_ROLE",
    "MARKPX_TERM_KIND",
    "MARKPX_TERM_STATUS",
    "MONETARY_BASE_KIND",
    "MONETARY_BASE_STATUS",
    "NORMAL_EXPIRY_RATE_0_0001_STATUS",
    "NUMERIC_FUNDING_AMOUNT",
    "NUMERIC_FUNDING_AMOUNT_PRODUCED",
    "OKX_POSITION_VALUE_ALGEBRA_STATUS",
    "QTY_BOUND_VALUE",
    "QTY_LIMIT",
    "QTY_TERM_KIND",
    "QTY_TERM_STATUS",
    "QtyOneFormulaTermInstanceBindingV1",
    "ROUNDING_KIND",
    "ROUNDING_STATUS",
    "RULE_FX",
    "RULE_FX_STATUS",
    "RULE_ROUNDING",
    "RULE_ROUNDING_STATUS",
    "bind_qty_one_uninstantiated_formula_term_instances_v1",
)
