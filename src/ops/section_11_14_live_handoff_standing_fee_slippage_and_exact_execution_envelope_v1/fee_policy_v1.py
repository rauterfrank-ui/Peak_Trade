"""Standing trading-fee policy for the §11.14 exact-single LIMIT fill.

Binds the source, sign convention, and conservative single-fill algebra.
Does not treat historical BTC rates, research backtest fees, round-trip
FEE_RESERVE, or expiry delivery as this fill's expected trading fee.
Does not POST.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_CEILING, Decimal, InvalidOperation
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INST_FAMILY,
    DEFAULT_INST_TYPE,
    DEFAULT_INSTRUMENT_ID,
)
from src.ops.section_11_14_live_handoff_standing_fee_slippage_and_exact_execution_envelope_v1.constants_v1 import (
    CONSERVATIVE_FEE_QUANTIZE_EXPONENT,
    EXACT_OKX_FEE_FORMULA_STATUS,
    FEE_CURRENCY_REQUIRED,
    FEE_FIELD_DELIVERY,
    FEE_FIELD_MAKER_GENERIC,
    FEE_FIELD_MAKER_USDC,
    FEE_FIELD_TAKER_GENERIC,
    FEE_FIELD_TAKER_USDC,
    FEE_QUANTIZE_ROLE,
    FEE_RATE_UNIT,
    FEE_SIGN_DEBIT_IS_NEGATIVE,
    FEE_SOURCE_ENDPOINT,
    HISTORICAL_BTC_FAMILY,
    HISTORICAL_FEE_RATES_ARE_NOT_CURRENT,
    MAKER_TAKER_ASSUMPTION,
    NOTIONAL_ALGEBRA,
    NOTIONAL_ALGEBRA_ROLE,
    PATH_ACCOUNT_TRADE_FEE,
    ROUND_TRIP_FEE_RESERVE_IS_NOT_THIS_FILL,
    SINGLE_FILL_FEE_AMOUNT_ALGEBRA,
    SINGLE_FILL_FEE_RATE_ALGEBRA,
    TRADE_FEE_INST_TYPE,
)

QUANTIZE_EXP = Decimal("1e" + str(CONSERVATIVE_FEE_QUANTIZE_EXPONENT))


class StandingFeePolicyError(RuntimeError):
    """Fail-closed standing fee-policy violation."""


def trade_fee_query_path_v1(
    *,
    inst_type: str = DEFAULT_INST_TYPE,
    inst_family: str = DEFAULT_INST_FAMILY,
) -> str:
    family = str(inst_family or "").strip()
    itype = str(inst_type or "").strip().upper()
    if not family:
        raise StandingFeePolicyError("INST_FAMILY_REQUIRED")
    if itype != TRADE_FEE_INST_TYPE:
        raise StandingFeePolicyError(f"INST_TYPE_NOT_FUTURES:{itype}")
    if family == HISTORICAL_BTC_FAMILY:
        raise StandingFeePolicyError("HISTORICAL_BTC_FAMILY_IS_NOT_CURRENT_SUI_AUTHORITY")
    if family != DEFAULT_INST_FAMILY:
        raise StandingFeePolicyError(f"INST_FAMILY_NOT_BOUND_SUI:{family}")
    return f"{PATH_ACCOUNT_TRADE_FEE}?instType={itype}&instFamily={family}"


def _dec(raw: Any, *, field: str) -> Decimal:
    text = str(raw if raw is not None else "").strip()
    if not text:
        raise StandingFeePolicyError(f"FEE_FIELD_MISSING:{field}")
    try:
        value = Decimal(text)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise StandingFeePolicyError(f"FEE_FIELD_UNPARSEABLE:{field}") from exc
    if not value.is_finite():
        raise StandingFeePolicyError(f"FEE_FIELD_NON_FINITE:{field}")
    return value


def debit_rate_from_venue_raw_v1(raw: Decimal) -> Decimal:
    """Venue negative rate is an account debit. Rebate cannot reduce worst-case debit below 0."""
    if raw < 0:
        return -raw
    return Decimal("0")


def _pick_rate(*, row: Mapping[str, Any], generic: str, usdc: str) -> tuple[Decimal, str]:
    generic_raw = str(row.get(generic) or "").strip()
    usdc_raw = str(row.get(usdc) or "").strip()
    if generic_raw:
        return _dec(generic_raw, field=generic), generic
    if usdc_raw:
        return _dec(usdc_raw, field=usdc), usdc
    raise StandingFeePolicyError(f"FEE_RATE_UNKNOWN:{generic}|{usdc}")


def conservative_quantize_fee_amount_v1(amount: Decimal) -> Decimal:
    if amount < 0:
        raise StandingFeePolicyError("FEE_AMOUNT_SIGN_INVALID")
    return amount.quantize(QUANTIZE_EXP, rounding=ROUND_CEILING)


@dataclass(frozen=True)
class StandingFeePolicyV1:
    policy_bound: bool
    source_endpoint: str
    query_path: str
    inst_type: str
    inst_family: str
    instrument_id: str
    taker_raw: str
    maker_raw: str
    taker_field: str
    maker_field: str
    taker_debit: str
    maker_debit: str
    conservative_rate: str
    rate_unit: str
    fee_ccy: str
    delivery_raw: str
    delivery_role: str
    maker_taker_assumption: str
    notional_algebra: str
    amount_algebra: str
    exact_okx_formula_status: str
    historical_rates_used: bool
    round_trip_reserve_used: bool
    freshness: str
    deny_reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "POLICY_BOUND": self.policy_bound,
            "SOURCE_ENDPOINT": self.source_endpoint,
            "QUERY_PATH": self.query_path,
            "INST_TYPE": self.inst_type,
            "INST_FAMILY": self.inst_family,
            "INSTRUMENT_ID": self.instrument_id,
            "TAKER_RAW": self.taker_raw,
            "MAKER_RAW": self.maker_raw,
            "TAKER_FIELD": self.taker_field,
            "MAKER_FIELD": self.maker_field,
            "TAKER_DEBIT": self.taker_debit,
            "MAKER_DEBIT": self.maker_debit,
            "CONSERVATIVE_RATE": self.conservative_rate,
            "RATE_UNIT": self.rate_unit,
            "FEE_CCY": self.fee_ccy,
            "DELIVERY_RAW": self.delivery_raw,
            "DELIVERY_ROLE": self.delivery_role,
            "MAKER_TAKER_ASSUMPTION": self.maker_taker_assumption,
            "NOTIONAL_ALGEBRA": self.notional_algebra,
            "AMOUNT_ALGEBRA": self.amount_algebra,
            "EXACT_OKX_FEE_FORMULA_STATUS": self.exact_okx_formula_status,
            "HISTORICAL_RATES_USED": self.historical_rates_used,
            "ROUND_TRIP_RESERVE_USED": self.round_trip_reserve_used,
            "FRESHNESS": self.freshness,
            "DENY_REASON": self.deny_reason,
            "SIGN_CONVENTION": "VENUE_NEGATIVE_IS_DEBIT" if FEE_SIGN_DEBIT_IS_NEGATIVE else "",
        }


def bind_standing_fee_policy_from_trade_fee_payload_v1(
    *,
    payload: Mapping[str, Any] | None,
    instrument_id: str = DEFAULT_INSTRUMENT_ID,
    inst_type: str = DEFAULT_INST_TYPE,
    inst_family: str = DEFAULT_INST_FAMILY,
    historical_reuse: bool = False,
    freshness: str = "CURRENT_GET",
) -> StandingFeePolicyV1:
    query = trade_fee_query_path_v1(inst_type=inst_type, inst_family=inst_family)
    iid = str(instrument_id or "").strip()
    if iid != DEFAULT_INSTRUMENT_ID:
        raise StandingFeePolicyError(f"INSTRUMENT_NOT_BOUND:{iid}")
    if historical_reuse:
        raise StandingFeePolicyError("HISTORICAL_FEE_EVIDENCE_MUST_NOT_BE_CURRENT")
    if payload is None:
        raise StandingFeePolicyError("TRADE_FEE_PAYLOAD_MISSING")
    if str(payload.get("code") or "") != "0":
        raise StandingFeePolicyError("TRADE_FEE_PAYLOAD_NOT_OK")
    data = payload.get("data")
    if not isinstance(data, list) or not data:
        raise StandingFeePolicyError("TRADE_FEE_DATA_MISSING")
    row = None
    for item in data:
        if not isinstance(item, Mapping):
            continue
        family = str(item.get("instFamily") or inst_family).strip()
        itype = str(item.get("instType") or inst_type).strip().upper()
        if family == HISTORICAL_BTC_FAMILY:
            raise StandingFeePolicyError("HISTORICAL_BTC_FAMILY_ROW_REJECTED")
        if family == inst_family and itype == str(inst_type).upper():
            row = item
            break
    if row is None:
        if len(data) == 1 and isinstance(data[0], Mapping):
            row = data[0]
            family = str(row.get("instFamily") or "").strip()
            if family == HISTORICAL_BTC_FAMILY:
                raise StandingFeePolicyError("HISTORICAL_BTC_FAMILY_ROW_REJECTED")
            if family and family != inst_family:
                raise StandingFeePolicyError(f"TRADE_FEE_FAMILY_MISMATCH:{family}")
        else:
            raise StandingFeePolicyError("TRADE_FEE_ROW_NOT_FOUND")
    taker, taker_field = _pick_rate(
        row=row, generic=FEE_FIELD_TAKER_GENERIC, usdc=FEE_FIELD_TAKER_USDC
    )
    maker, maker_field = _pick_rate(
        row=row, generic=FEE_FIELD_MAKER_GENERIC, usdc=FEE_FIELD_MAKER_USDC
    )
    taker_debit = debit_rate_from_venue_raw_v1(taker)
    maker_debit = debit_rate_from_venue_raw_v1(maker)
    conservative = taker_debit if taker_debit >= maker_debit else maker_debit
    if conservative <= 0:
        raise StandingFeePolicyError("CONSERVATIVE_FEE_RATE_NON_POSITIVE")
    delivery_raw = str(row.get(FEE_FIELD_DELIVERY) or "").strip()
    return StandingFeePolicyV1(
        policy_bound=True,
        source_endpoint=FEE_SOURCE_ENDPOINT,
        query_path=query,
        inst_type=str(inst_type).upper(),
        inst_family=str(inst_family),
        instrument_id=iid,
        taker_raw=format(taker, "f"),
        maker_raw=format(maker, "f"),
        taker_field=taker_field,
        maker_field=maker_field,
        taker_debit=format(taker_debit, "f"),
        maker_debit=format(maker_debit, "f"),
        conservative_rate=format(conservative, "f"),
        rate_unit=FEE_RATE_UNIT,
        fee_ccy=FEE_CURRENCY_REQUIRED,
        delivery_raw=delivery_raw or "UNKNOWN",
        delivery_role="NOT_PART_OF_ENTRY_FILL",
        maker_taker_assumption=MAKER_TAKER_ASSUMPTION,
        notional_algebra=NOTIONAL_ALGEBRA,
        amount_algebra=SINGLE_FILL_FEE_AMOUNT_ALGEBRA,
        exact_okx_formula_status=EXACT_OKX_FEE_FORMULA_STATUS,
        historical_rates_used=not HISTORICAL_FEE_RATES_ARE_NOT_CURRENT,
        round_trip_reserve_used=not ROUND_TRIP_FEE_RESERVE_IS_NOT_THIS_FILL,
        freshness=freshness,
        deny_reason="",
    )


def compute_expected_fee_amount_v1(
    *,
    conservative_rate: str,
    qty: str,
    ct_val: str,
    worst_fill_px: str,
    fee_ccy: str = FEE_CURRENCY_REQUIRED,
    notional_ccy: str = FEE_CURRENCY_REQUIRED,
) -> dict[str, str]:
    if str(fee_ccy or "").strip() != FEE_CURRENCY_REQUIRED:
        raise StandingFeePolicyError(f"FEE_CURRENCY_MISMATCH:{fee_ccy}")
    if str(notional_ccy or "").strip() != FEE_CURRENCY_REQUIRED:
        raise StandingFeePolicyError(f"NOTIONAL_CURRENCY_MISMATCH:{notional_ccy}")
    rate = _dec(conservative_rate, field="conservative_rate")
    if rate <= 0:
        raise StandingFeePolicyError("CONSERVATIVE_FEE_RATE_NON_POSITIVE")
    q = _dec(qty, field="qty")
    ct = _dec(ct_val, field="ctVal")
    px = _dec(worst_fill_px, field="worst_fill_px")
    notional = q * ct * px
    if notional <= 0:
        raise StandingFeePolicyError("NOTIONAL_NON_POSITIVE")
    raw_amount = rate * notional
    quantized = conservative_quantize_fee_amount_v1(raw_amount)
    return {
        "GROSS_NOTIONAL": format(notional, "f"),
        "FEE_AMOUNT_EXACT": format(raw_amount, "f"),
        "FEE_AMOUNT_CONSERVATIVE": format(quantized, "f"),
        "FEE_CCY": FEE_CURRENCY_REQUIRED,
        "NOTIONAL_ALGEBRA_ROLE": NOTIONAL_ALGEBRA_ROLE,
        "QUANTIZE_ROLE": FEE_QUANTIZE_ROLE,
        "RATE": format(rate, "f"),
    }
