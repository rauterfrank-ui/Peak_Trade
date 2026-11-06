"""Deterministic fail-closed exact-single-fill execution envelope. No wire send."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INST_FAMILY,
    DEFAULT_INST_TYPE,
    DEFAULT_INSTRUMENT_ID,
    DEFAULT_ORDER_TYPE,
    DEFAULT_SIDE,
    DEFAULT_TD_MODE,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.venue_contract_count_v1 import (
    SUI_OPERATIVE_ORDER_SZ,
    SUI_OPERATIVE_ORDER_SZ_UNIT,
    assert_venue_contract_count_admissible_v1,
    canary_venue_contract_count_v1,
)
from src.ops.section_11_14_live_handoff_standing_fee_slippage_and_exact_execution_envelope_v1.constants_v1 import (
    ENVELOPE_VERSION,
    SCHEMA_VERSION,
)
from src.ops.section_11_14_live_handoff_standing_fee_slippage_and_exact_execution_envelope_v1.fee_policy_v1 import (
    StandingFeePolicyError,
    StandingFeePolicyV1,
    compute_expected_fee_amount_v1,
)
from src.ops.section_11_14_live_handoff_standing_fee_slippage_and_exact_execution_envelope_v1.slippage_policy_v1 import (
    StandingSlippagePolicyError,
    StandingSlippagePolicyV1,
    bind_standing_limit_slippage_policy_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANARY_AUTHORIZED,
    LIVE_ARMED,
    LIVE_ENABLED,
    POST_ALLOWED,
    SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED,
)


class ExactExecutionEnvelopeError(RuntimeError):
    """Fail-closed exact execution envelope violation."""


def _dec(raw: Any, *, field: str) -> Decimal:
    text = str(raw if raw is not None else "").strip()
    if not text or text == "UNKNOWN":
        raise ExactExecutionEnvelopeError(f"ENVELOPE_INPUT_UNKNOWN:{field}")
    try:
        value = Decimal(text)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ExactExecutionEnvelopeError(f"ENVELOPE_INPUT_UNPARSEABLE:{field}") from exc
    if not value.is_finite():
        raise ExactExecutionEnvelopeError(f"ENVELOPE_INPUT_NON_FINITE:{field}")
    return value


def _require_pass(predicates: Mapping[str, Mapping[str, Any]], name: str) -> None:
    status = str((predicates.get(name) or {}).get("status") or "")
    if status != "PASS":
        raise ExactExecutionEnvelopeError(f"PREDICATE_NOT_PASS:{name}:{status or 'MISSING'}")


def _allow_pass_or_not_observed(predicates: Mapping[str, Mapping[str, Any]], name: str) -> None:
    status = str((predicates.get(name) or {}).get("status") or "")
    if status not in {"PASS", "NOT_OBSERVED"}:
        raise ExactExecutionEnvelopeError(f"PREDICATE_NOT_ADMISSIBLE:{name}:{status or 'MISSING'}")


@dataclass(frozen=True)
class ExactExecutionEnvelopeV1:
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return dict(self.payload)


def build_exact_execution_envelope_v1(
    *,
    instrument_id: str,
    side: str,
    order_type: str,
    td_mode: str,
    pos_mode: str,
    leverage: str,
    qty: str,
    qty_unit: str,
    min_sz: str,
    lot_sz: str,
    tick_sz: str,
    ct_val: str,
    ct_val_ccy: str,
    settle_ccy: str,
    reference_price: str,
    limit_price: str,
    buy_lmt: str,
    sell_lmt: str,
    max_buy: str,
    available_margin: str,
    available_margin_ccy: str,
    instrument_state: str,
    account_mode: str,
    fee_policy: StandingFeePolicyV1,
    predicates: Mapping[str, Mapping[str, Any]] | None = None,
    owner_execution_authorized: bool = False,
) -> ExactExecutionEnvelopeV1:
    if LIVE_ENABLED or LIVE_ARMED or CANARY_AUTHORIZED or POST_ALLOWED:
        raise ExactExecutionEnvelopeError("STANDING_LIVE_FLAG_MUST_REMAIN_FALSE")
    if SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED:
        raise ExactExecutionEnvelopeError("RUNTIME_EXECUTION_MUST_REMAIN_FALSE")
    if owner_execution_authorized:
        raise ExactExecutionEnvelopeError("OWNER_EXECUTION_AUTHORIZED_MUST_REMAIN_FALSE")
    iid = str(instrument_id or "").strip()
    if iid != DEFAULT_INSTRUMENT_ID:
        raise ExactExecutionEnvelopeError(f"WRONG_INSTRUMENT:{iid}")
    if str(side or "").upper() != DEFAULT_SIDE:
        raise ExactExecutionEnvelopeError(f"WRONG_SIDE:{side}")
    if str(order_type or "").upper() != DEFAULT_ORDER_TYPE:
        raise ExactExecutionEnvelopeError(f"WRONG_ORDER_TYPE:{order_type}")
    if str(td_mode or "").strip() != DEFAULT_TD_MODE:
        raise ExactExecutionEnvelopeError(f"WRONG_TD_MODE:{td_mode}")
    if str(pos_mode or "").strip() != "net_mode":
        raise ExactExecutionEnvelopeError(f"WRONG_POS_MODE:{pos_mode}")
    if str(instrument_state or "").strip() != "live":
        raise ExactExecutionEnvelopeError(f"INSTRUMENT_NOT_LIVE:{instrument_state}")
    if str(account_mode or "").strip() != "2":
        raise ExactExecutionEnvelopeError(f"WRONG_ACCOUNT_MODE:{account_mode}")
    if str(qty_unit or "").strip() != SUI_OPERATIVE_ORDER_SZ_UNIT:
        raise ExactExecutionEnvelopeError(f"WRONG_QTY_UNIT:{qty_unit}")
    if str(settle_ccy or "").strip() != "USDC":
        raise ExactExecutionEnvelopeError(f"SETTLE_CCY_MISMATCH:{settle_ccy}")
    if str(available_margin_ccy or "").strip() != "USDC":
        raise ExactExecutionEnvelopeError(f"MARGIN_CCY_MISMATCH:{available_margin_ccy}")
    if str(ct_val_ccy or "").strip() not in {"SUI", "USDC", ""}:
        raise ExactExecutionEnvelopeError(f"CTVAL_CCY_UNEXPECTED:{ct_val_ccy}")
    typed_qty = canary_venue_contract_count_v1()
    if str(qty).strip() != typed_qty or typed_qty != SUI_OPERATIVE_ORDER_SZ:
        raise ExactExecutionEnvelopeError(f"QTY_NOT_BOUND_OPERATIVE:{qty}")
    try:
        assert_venue_contract_count_admissible_v1(
            venue_contract_count=typed_qty,
            instrument_min_sz=min_sz,
            instrument_lot_sz=lot_sz,
        )
    except Exception as exc:  # noqa: BLE001
        raise ExactExecutionEnvelopeError(f"QTY_NOT_VENUE_ADMISSIBLE:{exc}") from exc
    px = _dec(limit_price, field="limit_price")
    buy = _dec(buy_lmt, field="buyLmt")
    _dec(sell_lmt, field="sellLmt")
    if px > buy:
        raise ExactExecutionEnvelopeError("PRICE_OUTSIDE_BAND")
    max_buy_d = _dec(max_buy, field="maxBuy")
    qty_d = _dec(typed_qty, field="qty")
    if qty_d > max_buy_d:
        raise ExactExecutionEnvelopeError("QTY_ABOVE_MAX_AVAILABLE")
    avail = _dec(available_margin, field="available_margin")
    if avail <= 0:
        raise ExactExecutionEnvelopeError("AVAILABLE_MARGIN_NON_POSITIVE")
    if not fee_policy.policy_bound:
        raise ExactExecutionEnvelopeError("FEE_POLICY_NOT_BOUND")
    if fee_policy.instrument_id != iid:
        raise ExactExecutionEnvelopeError("FEE_POLICY_INSTRUMENT_MISMATCH")
    if fee_policy.inst_family != DEFAULT_INST_FAMILY:
        raise ExactExecutionEnvelopeError("FEE_POLICY_FAMILY_MISMATCH")
    if fee_policy.inst_type != DEFAULT_INST_TYPE:
        raise ExactExecutionEnvelopeError("FEE_POLICY_INST_TYPE_MISMATCH")
    try:
        slippage = bind_standing_limit_slippage_policy_v1(
            side=side,
            reference_price=reference_price,
            limit_price=limit_price,
            tick_sz=tick_sz,
        )
    except StandingSlippagePolicyError as exc:
        raise ExactExecutionEnvelopeError(f"SLIPPAGE_POLICY:{exc}") from exc
    try:
        fee_amt = compute_expected_fee_amount_v1(
            conservative_rate=fee_policy.conservative_rate,
            qty=typed_qty,
            ct_val=ct_val,
            worst_fill_px=slippage.worst_fill_price,
            fee_ccy=fee_policy.fee_ccy,
            notional_ccy="USDC",
        )
    except StandingFeePolicyError as exc:
        raise ExactExecutionEnvelopeError(f"EXPECTED_FEE:{exc}") from exc
    worst_cost = _dec(fee_amt["FEE_AMOUNT_CONSERVATIVE"], field="fee") + _dec(
        fee_amt["GROSS_NOTIONAL"], field="notional"
    )
    # Margin sufficiency uses venue max-size as oracle, not invented IM algebra.
    margin_sufficiency = qty_d <= max_buy_d and avail > Decimal("0")
    if not margin_sufficiency:
        raise ExactExecutionEnvelopeError("MARGIN_SUFFICIENCY_UNPROVEN")
    if predicates:
        for name in (
            "INSTRUMENT_STATE_CURRENT",
            "ACCOUNT_MODE_CURRENT",
            "POSITION_MODE_CURRENT",
            "LEVERAGE_CURRENT",
            "PRICE_BAND_CURRENT",
            "PRICE_SOURCE_CURRENT",
            "EXACT_PRICE_SEMANTICS_BOUND",
            "AVAILABLE_MARGIN_CURRENT",
            "MAX_AVAILABLE_MAX_SIZE_CURRENT",
        ):
            _require_pass(predicates, name)
        _allow_pass_or_not_observed(predicates, "MARGIN_MODE_CURRENT")
        _allow_pass_or_not_observed(predicates, "EXPECTED_PRE_EXISTING_POSITION")
    payload = {
        "SCHEMA_VERSION": SCHEMA_VERSION,
        "ENVELOPE_VERSION": ENVELOPE_VERSION,
        "INSTRUMENT_ID": iid,
        "INST_TYPE": DEFAULT_INST_TYPE,
        "INST_FAMILY": DEFAULT_INST_FAMILY,
        "SIDE": DEFAULT_SIDE,
        "ORDER_TYPE": DEFAULT_ORDER_TYPE,
        "TD_MODE": DEFAULT_TD_MODE,
        "POS_MODE": "net_mode",
        "POS_SIDE": "OMITTED_NET_MODE",
        "LEVERAGE": str(leverage),
        "ORDER_QTY": typed_qty,
        "ORDER_QTY_UNIT": SUI_OPERATIVE_ORDER_SZ_UNIT,
        "MIN_SZ": str(min_sz),
        "LOT_SZ": str(lot_sz),
        "TICK_SZ": str(tick_sz),
        "CT_VAL": str(ct_val),
        "CT_VAL_CCY": str(ct_val_ccy),
        "SETTLE_CCY": "USDC",
        "REFERENCE_PRICE": str(reference_price),
        "LIMIT_PRICE": str(limit_price),
        "BUY_LMT": str(buy_lmt),
        "SELL_LMT": str(sell_lmt),
        "MAX_BUY": str(max_buy),
        "AVAILABLE_MARGIN": str(available_margin),
        "AVAILABLE_MARGIN_CCY": "USDC",
        "INSTRUMENT_STATE": "live",
        "ACCOUNT_MODE": "2",
        "WORST_FILL_PRICE": slippage.worst_fill_price,
        "SLIPPAGE_ABS": slippage.slippage_abs,
        "SLIPPAGE_FRAC": slippage.slippage_frac,
        "SLIPPAGE_POLICY_ID": slippage.policy_id,
        "GROSS_NOTIONAL": fee_amt["GROSS_NOTIONAL"],
        "WORST_CASE_NOTIONAL": fee_amt["GROSS_NOTIONAL"],
        "EXPECTED_FEE_RATE": fee_policy.conservative_rate,
        "EXPECTED_FEE_AMOUNT": fee_amt["FEE_AMOUNT_CONSERVATIVE"],
        "EXPECTED_FEE_AMOUNT_EXACT": fee_amt["FEE_AMOUNT_EXACT"],
        "EXPECTED_FEE_CCY": "USDC",
        "WORST_CASE_COST": format(worst_cost, "f"),
        "WORST_CASE_COST_UNIT": "USDC_INTERNAL_NOTIONAL_PLUS_FEE_NOT_OEM_IM",
        "FEE_POLICY": fee_policy.to_dict(),
        "SLIPPAGE_POLICY": slippage.to_dict(),
        "MARGIN_SUFFICIENCY_PROVEN": True,
        "MARGIN_SUFFICIENCY_ORACLE": "VENUE_MAX_SIZE_AND_AVAILABLE_MARGIN_OBSERVED_NOT_INVENTED_IM",
        "STOP_SEMANTICS": "SEPARATE_FLATTEN_PATH_NOT_PART_OF_ENTRY_FILL",
        "EXACT_EXECUTION_ENVELOPE_COMPLETE": True,
        "TECHNICAL_EXECUTION_READY": True,
        "OWNER_EXECUTION_AUTHORIZED": False,
        "LIVE_EXECUTION_AUTHORIZED": False,
        "LIVE_ENABLED": False,
        "LIVE_ARMED": False,
        "CANARY_AUTHORIZED": False,
        "POST_ALLOWED": False,
        "SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED": False,
        "LIVE_SUBMIT_EXECUTED": False,
        "WIRE_SEND_EXECUTED": False,
        "CLORDID_STATUS": "UNKNOWN_REQUIRES_FUTURE_EXECUTION_OWNER_GO",
    }
    return ExactExecutionEnvelopeV1(payload=payload)
