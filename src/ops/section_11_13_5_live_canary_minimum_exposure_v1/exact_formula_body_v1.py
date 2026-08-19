"""§11.13.5.Z2E Peak_Trade-internal qty=1 exact formula-body ratification.

INTERNAL_POLICY / FORMULA_BODY only. Does not invent OKX fee truth, a
monetary base, USD/USDC conversion, USDC rounding, or a numeric funding
amount. Does not authorize Live, Testnet, orders, funding, scaling, or
Multi-Future.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    LIVE_AUTHORIZED,
    TESTNET_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.expiry_fee_economic_uncertainty_bound_v1 import (
    API_DELIVERY_0_0003_STATUS,
    PEAK_TRADE_EXPIRY_RESERVE_RATE,
    PEAK_TRADE_EXPIRY_RESERVE_RATE_IS_OKX_FEE_TRUTH,
    PEAK_TRADE_EXPIRY_RESERVE_RATE_SOURCE,
    PEAK_TRADE_INTERNAL_NOTIONAL_ENVELOPE_FORM,
    PEAK_TRADE_INTERNAL_NOTIONAL_ENVELOPE_ROLE,
    PEAK_TRADE_INTERNAL_NOTIONAL_UNIT,
    PROVEN_NORMAL_EXPIRY_RATE,
    QTY_LIMIT,
    evaluate_internal_expiry_fee_economic_uncertainty_bound_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.position_value_fx_rounding_chain_v1 import (
    COVER_USDC_STATUS,
    EXCHANGE_TRUTH_CHANGED,
    MULTI_FUTURE_AUTHORIZED,
    OKX_POSITION_VALUE_ALGEBRA_STATUS,
    PEAK_TRADE_INTERNAL_POSITION_VALUE_IS_OKX_POSITION_VALUE,
    ROUNDING_APPLIED,
    SCALING_AUTHORIZED,
    USD_USDC_CONVERSION_APPLIED,
    classify_qty_one_position_value_fx_rounding_chain_v1,
)

B08_EXACT_FORMULA_BODY_KIND = (
    "INTERNAL_CONSERVATIVE_QTY1_COMPOSITION_NOT_EXCHANGE_TRUTH_NOT_COVER_USDC"
)
B08_EXACT_FORMULA_BODY_STATUS = "RATIFIED_INTERNAL_CONSERVATIVE_QTY1_NOT_COVER_USDC"
FORMULA_BODY_STATUS = "RATIFIED_INTERNAL_ALGEBRA_NUMERIC_SUM_UNINSTANTIATED"
OWNER_SUPPLIED_OPERATIONAL_FORMULA_BODY = B08_EXACT_FORMULA_BODY_KIND
NORMAL_EXPIRY_RATE_ROLE = "HISTORICAL_SUPERSEDED_NON_OPERATIVE"
MONETARY_BASE_STATUS = "BOUND_PEAK_TRADE_INTERNAL_NOTIONAL_ENVELOPE"
EXACT_OKX_FEE_FORMULA_STATUS = "UNPROVEN"
FEE_RESERVE_ALGEBRA = "2 * max(abs(taker), abs(maker)) * INTERNAL_NOTIONAL_ENVELOPE"
DELIVERY_COVER_INTERNAL_ALGEBRA = "0.0003 * INTERNAL_NOTIONAL_ENVELOPE"
SLIPPAGE_RESERVE_ALGEBRA = "2 * max(askPx - bidPx, tickSz) * ctVal * qty"
MM_LIQ_BUFFER_ALGEBRA = "INTERNAL_NOTIONAL_ENVELOPE * mmr_public_tier_qty_one"
SUM_INTERNAL_ALGEBRA = "FEE_RESERVE + DELIVERY_COVER_INTERNAL + SLIPPAGE_RESERVE + MM_LIQ_BUFFER"
FEE_RESERVE_RATES_STATUS = "SECTION_W_FRESH_GET_EVIDENCE_NOT_FROZEN_UNLESS_OWNER_EXPLICITLY_REBINDS"
DELIVERY_COVER_INTERNAL_STATUS = "ALREADY_BOUND_Z2C"
SLIPPAGE_RESERVE_STATUS = "UNINSTANTIATED_REQUIRES_FRESH_TICKER_GET"
MM_LIQ_BUFFER_STATUS = "UNINSTANTIATED_REQUIRES_PUBLIC_TIER_MMR_GET"
FX_STATUS = "UNINSTANTIATED_REQUIRES_PRODUCTIVE_USD_USDC_EVIDENCE"
ROUNDING_STATUS = "UNINSTANTIATED_REQUIRES_PRODUCTIVE_USDC_PRECISION_EVIDENCE"
SUM_INTERNAL_NUMERIC_STATUS = "UNINSTANTIATED"
NUMERIC_FUNDING_AMOUNT = "NONE"
IM_FRESH_ROLE = "MANDATORY_FLOOR_NOT_ADDITIVE_RESERVE_TERM"
VENUE_MIN_AVAIL_EQ_ROLE = "CONSTRAINT_AND_POSSIBLE_FLOOR_NEVER_ADDITIVE"
FUNDING_RATE_RESERVE = "EXCLUDED_UNRESOLVED_AND_NOT_USABLE"
OUTPUT_BEFORE_FX_AND_ROUNDING = "SUM_INTERNAL_IN_PEAK_TRADE_INTERNAL_NOTIONAL_UNIT"
MINIMUM_EXPOSURE_ONLY = True


class ExactFormulaBodyError(RuntimeError):
    """Fail-closed exact formula-body ratification / composition violation."""


@dataclass(frozen=True)
class QtyOneInternalExactFormulaBodyV1:
    formula_body_status: str
    formula_body_kind: str
    exchange_truth_changed: bool
    proven_normal_expiry_rate: str
    normal_expiry_rate_role: str
    conservative_reserve_rate: str
    conservative_reserve_rate_is_okx_fee_truth: bool
    conservative_reserve_rate_source: str
    monetary_base_status: str
    exact_okx_fee_formula_status: str
    api_delivery_0_0003_status: str
    position_value_algebra_status: str
    internal_notional_envelope: str
    internal_notional_envelope_form: str
    internal_notional_envelope_role: str
    internal_notional_is_okx_position_value: bool
    output_unit: str
    fee_reserve_algebra: str
    fee_reserve_rates_status: str
    delivery_cover_internal_algebra: str
    delivery_cover_internal_status: str
    delivery_cover_internal: str
    slippage_reserve_algebra: str
    slippage_reserve_status: str
    mm_liq_buffer_algebra: str
    mm_liq_buffer_status: str
    sum_internal_algebra: str
    sum_internal_numeric_status: str
    sum_internal_numeric: str
    im_fresh_role: str
    venue_min_avail_eq_role: str
    funding_rate_reserve: str
    fx_status: str
    rounding_status: str
    fx_applied: bool
    rounding_applied: bool
    cover_usdc_status: str
    numeric_funding_amount: str
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
            "B08_EXACT_FORMULA_BODY_STATUS": self.formula_body_status,
            "B08_EXACT_FORMULA_BODY_KIND": self.formula_body_kind,
            "EXCHANGE_TRUTH_CHANGED": self.exchange_truth_changed,
            "PROVEN_NORMAL_EXPIRY_RATE": self.proven_normal_expiry_rate,
            "NORMAL_EXPIRY_RATE_ROLE": self.normal_expiry_rate_role,
            "PEAK_TRADE_EXPIRY_RESERVE_RATE": self.conservative_reserve_rate,
            "PEAK_TRADE_EXPIRY_RESERVE_RATE_IS_OKX_FEE_TRUTH": (
                self.conservative_reserve_rate_is_okx_fee_truth
            ),
            "PEAK_TRADE_EXPIRY_RESERVE_RATE_SOURCE": (self.conservative_reserve_rate_source),
            "MONETARY_BASE_STATUS": self.monetary_base_status,
            "EXACT_OKX_FEE_FORMULA_STATUS": self.exact_okx_fee_formula_status,
            "API_DELIVERY_0_0003_STATUS": self.api_delivery_0_0003_status,
            "POSITION_VALUE_ALGEBRA_STATUS": self.position_value_algebra_status,
            "PEAK_TRADE_INTERNAL_NOTIONAL_ENVELOPE": self.internal_notional_envelope,
            "PEAK_TRADE_INTERNAL_NOTIONAL_ENVELOPE_FORM": (self.internal_notional_envelope_form),
            "PEAK_TRADE_INTERNAL_NOTIONAL_ENVELOPE_ROLE": (self.internal_notional_envelope_role),
            "PEAK_TRADE_INTERNAL_POSITION_VALUE_IS_OKX_POSITION_VALUE": (
                self.internal_notional_is_okx_position_value
            ),
            "OUTPUT_UNIT": self.output_unit,
            "FEE_RESERVE_ALGEBRA": self.fee_reserve_algebra,
            "FEE_RESERVE_RATES_STATUS": self.fee_reserve_rates_status,
            "DELIVERY_COVER_INTERNAL_ALGEBRA": self.delivery_cover_internal_algebra,
            "DELIVERY_COVER_INTERNAL_STATUS": self.delivery_cover_internal_status,
            "DELIVERY_COVER_INTERNAL": self.delivery_cover_internal,
            "SLIPPAGE_RESERVE_ALGEBRA": self.slippage_reserve_algebra,
            "SLIPPAGE_RESERVE_STATUS": self.slippage_reserve_status,
            "MM_LIQ_BUFFER_ALGEBRA": self.mm_liq_buffer_algebra,
            "MM_LIQ_BUFFER_STATUS": self.mm_liq_buffer_status,
            "SUM_INTERNAL_ALGEBRA": self.sum_internal_algebra,
            "SUM_INTERNAL_NUMERIC_STATUS": self.sum_internal_numeric_status,
            "SUM_INTERNAL_NUMERIC": self.sum_internal_numeric,
            "IM_FRESH_ROLE": self.im_fresh_role,
            "VENUE_MIN_AVAIL_EQ_ROLE": self.venue_min_avail_eq_role,
            "FUNDING_RATE_RESERVE": self.funding_rate_reserve,
            "FX_STATUS": self.fx_status,
            "ROUNDING_STATUS": self.rounding_status,
            "FX_APPLIED": self.fx_applied,
            "ROUNDING_APPLIED": self.rounding_applied,
            "COVER_USDC_STATUS": self.cover_usdc_status,
            "NUMERIC_FUNDING_AMOUNT": self.numeric_funding_amount,
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


def evaluate_qty_one_internal_exact_formula_body_v1(
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
    claim_0003_is_okx_fee_truth: bool = False,
    consume_0001_as_operative_fee_input: bool = False,
    label_output_usdc: bool = False,
    instantiate_cover_usdc: bool = False,
    add_im_fresh_to_sum: bool = False,
    add_venue_min_avail_eq_to_sum: bool = False,
    include_funding_rate_reserve: bool = False,
    freeze_section_w_fee_rates: bool = False,
    instantiate_slippage: bool = False,
    instantiate_mm_liq: bool = False,
    produce_numeric_funding_amount: bool = False,
) -> QtyOneInternalExactFormulaBodyV1:
    """Persist the ratified internal qty=1 formula body without funding math.

    Algebra is bound. Numeric SUM_INTERNAL, COVER_USDC, and funding amount
    remain uninstantiated. Delivery cover reuses the already-bound Z2C
    internal envelope and is not an OKX fee amount.
    """

    if claim_0003_is_okx_fee_truth or PEAK_TRADE_EXPIRY_RESERVE_RATE_IS_OKX_FEE_TRUTH:
        raise ExactFormulaBodyError("PEAK_TRADE_EXPIRY_RESERVE_RATE_IS_NOT_OKX_FEE_TRUTH")
    if consume_0001_as_operative_fee_input:
        raise ExactFormulaBodyError("HISTORICAL_SUPPORT_RATE_0_0001_IS_NOT_OPERATIVE")
    if label_output_usdc:
        raise ExactFormulaBodyError("OUTPUT_UNIT_IS_NOT_USDC")
    if instantiate_cover_usdc or apply_usd_usdc_conversion or apply_rounding:
        raise ExactFormulaBodyError("COVER_USDC_REMAINS_UNINSTANTIATED")
    if add_im_fresh_to_sum:
        raise ExactFormulaBodyError("IM_FRESH_IS_FLOOR_NOT_ADDITIVE_RESERVE_TERM")
    if add_venue_min_avail_eq_to_sum:
        raise ExactFormulaBodyError("VENUE_MIN_AVAIL_EQ_IS_CONSTRAINT_FLOOR_NOT_ADDITIVE")
    if include_funding_rate_reserve:
        raise ExactFormulaBodyError("FUNDING_RATE_RESERVE_REMAINS_EXCLUDED")
    if freeze_section_w_fee_rates:
        raise ExactFormulaBodyError("SECTION_W_FEE_RATES_NOT_FROZEN")
    if instantiate_slippage:
        raise ExactFormulaBodyError("SLIPPAGE_RESERVE_UNINSTANTIATED")
    if instantiate_mm_liq:
        raise ExactFormulaBodyError("MM_LIQ_BUFFER_UNINSTANTIATED")
    if produce_numeric_funding_amount:
        raise ExactFormulaBodyError("NUMERIC_FUNDING_AMOUNT_REMAINS_UNPROVEN")

    chain = classify_qty_one_position_value_fx_rounding_chain_v1(
        quantity=quantity,
        instrument_ct_val=instrument_ct_val,
        reference_price=reference_price,
        instrument_id=instrument_id,
        authorization_scope=authorization_scope,
        instrument_min_sz=instrument_min_sz,
        instrument_tick_sz=instrument_tick_sz,
        multi_future_requested=multi_future_requested,
        claim_okx_position_value=claim_okx_position_value,
        apply_usd_usdc_conversion=apply_usd_usdc_conversion,
        assume_usd_equals_usdc=assume_usd_equals_usdc,
        apply_rounding=apply_rounding,
        treat_tick_sz_as_usdc_precision=treat_tick_sz_as_usdc_precision,
    )
    bound = evaluate_internal_expiry_fee_economic_uncertainty_bound_v1(
        quantity=quantity,
        instrument_ct_val=instrument_ct_val,
        reference_price=reference_price,
        instrument_id=instrument_id,
        authorization_scope=authorization_scope,
        instrument_min_sz=instrument_min_sz,
        multi_future_requested=multi_future_requested,
    )
    if bound.bound_unit != PEAK_TRADE_INTERNAL_NOTIONAL_UNIT:
        raise ExactFormulaBodyError("OUTPUT_UNIT_IS_NOT_USDC")
    if chain.envelope_unit != PEAK_TRADE_INTERNAL_NOTIONAL_UNIT:
        raise ExactFormulaBodyError("OUTPUT_UNIT_IS_NOT_USDC")

    return QtyOneInternalExactFormulaBodyV1(
        formula_body_status=B08_EXACT_FORMULA_BODY_STATUS,
        formula_body_kind=B08_EXACT_FORMULA_BODY_KIND,
        exchange_truth_changed=EXCHANGE_TRUTH_CHANGED,
        proven_normal_expiry_rate=format(PROVEN_NORMAL_EXPIRY_RATE, "f"),
        normal_expiry_rate_role=NORMAL_EXPIRY_RATE_ROLE,
        conservative_reserve_rate=format(PEAK_TRADE_EXPIRY_RESERVE_RATE, "f"),
        conservative_reserve_rate_is_okx_fee_truth=(
            PEAK_TRADE_EXPIRY_RESERVE_RATE_IS_OKX_FEE_TRUTH
        ),
        conservative_reserve_rate_source=PEAK_TRADE_EXPIRY_RESERVE_RATE_SOURCE,
        monetary_base_status=MONETARY_BASE_STATUS,
        exact_okx_fee_formula_status=EXACT_OKX_FEE_FORMULA_STATUS,
        api_delivery_0_0003_status=API_DELIVERY_0_0003_STATUS,
        position_value_algebra_status=OKX_POSITION_VALUE_ALGEBRA_STATUS,
        internal_notional_envelope=chain.peak_trade_internal_position_value_envelope,
        internal_notional_envelope_form=PEAK_TRADE_INTERNAL_NOTIONAL_ENVELOPE_FORM,
        internal_notional_envelope_role=PEAK_TRADE_INTERNAL_NOTIONAL_ENVELOPE_ROLE,
        internal_notional_is_okx_position_value=(
            PEAK_TRADE_INTERNAL_POSITION_VALUE_IS_OKX_POSITION_VALUE
        ),
        output_unit=PEAK_TRADE_INTERNAL_NOTIONAL_UNIT,
        fee_reserve_algebra=FEE_RESERVE_ALGEBRA,
        fee_reserve_rates_status=FEE_RESERVE_RATES_STATUS,
        delivery_cover_internal_algebra=DELIVERY_COVER_INTERNAL_ALGEBRA,
        delivery_cover_internal_status=DELIVERY_COVER_INTERNAL_STATUS,
        delivery_cover_internal=bound.absolute_economic_uncertainty_bound,
        slippage_reserve_algebra=SLIPPAGE_RESERVE_ALGEBRA,
        slippage_reserve_status=SLIPPAGE_RESERVE_STATUS,
        mm_liq_buffer_algebra=MM_LIQ_BUFFER_ALGEBRA,
        mm_liq_buffer_status=MM_LIQ_BUFFER_STATUS,
        sum_internal_algebra=SUM_INTERNAL_ALGEBRA,
        sum_internal_numeric_status=SUM_INTERNAL_NUMERIC_STATUS,
        sum_internal_numeric="NONE",
        im_fresh_role=IM_FRESH_ROLE,
        venue_min_avail_eq_role=VENUE_MIN_AVAIL_EQ_ROLE,
        funding_rate_reserve=FUNDING_RATE_RESERVE,
        fx_status=FX_STATUS,
        rounding_status=ROUNDING_STATUS,
        fx_applied=USD_USDC_CONVERSION_APPLIED,
        rounding_applied=ROUNDING_APPLIED,
        cover_usdc_status=COVER_USDC_STATUS,
        numeric_funding_amount=NUMERIC_FUNDING_AMOUNT,
        quantity=chain.quantity,
        qty_limit=format(QTY_LIMIT, "f"),
        instrument_id=chain.instrument_id,
        authorization_scope=chain.authorization_scope,
        minimum_exposure_only=MINIMUM_EXPOSURE_ONLY,
        scaling_authorized=SCALING_AUTHORIZED,
        multi_future_authorized=MULTI_FUTURE_AUTHORIZED,
        live_authorized=LIVE_AUTHORIZED,
        testnet_authorized=TESTNET_AUTHORIZED,
        order_effect="NONE",
        funding_executed=False,
    )
