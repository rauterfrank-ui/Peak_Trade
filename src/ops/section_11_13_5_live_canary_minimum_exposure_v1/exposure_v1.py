"""Exposure / instrument binding helpers for §11.13.5 canary."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    DEFAULT_ORDER_TYPE,
    DEFAULT_SIDE,
    DEFAULT_TD_MODE,
    MINIMUM_RATIFIED_NOTIONAL_ONLY,
    ORDER_COUNT_LIMIT,
    POSITION_COUNT_LIMIT,
)


class LiveCanaryExposureError(RuntimeError):
    """Fail-closed exposure/instrument binding violation."""


@dataclass(frozen=True)
class CanaryExposureBindingV1:
    venue: str
    account_scope: str
    instrument_id: str
    side: str
    order_type: str
    td_mode: str
    instrument_min_sz: str
    instrument_lot_sz: str
    instrument_ct_val: str
    instrument_tick_sz: str
    quantity: str
    reference_price: str
    min_executable_notional: str
    max_notional: str
    position_count_limit: int = POSITION_COUNT_LIMIT
    order_count_limit: int = ORDER_COUNT_LIMIT
    minimum_ratified_notional_only: bool = MINIMUM_RATIFIED_NOTIONAL_ONLY

    def to_dict(self) -> dict[str, Any]:
        return {
            "venue": self.venue,
            "account_scope": self.account_scope,
            "instrument_id": self.instrument_id,
            "side": self.side,
            "order_type": self.order_type,
            "td_mode": self.td_mode,
            "instrument_min_sz": self.instrument_min_sz,
            "instrument_lot_sz": self.instrument_lot_sz,
            "instrument_ct_val": self.instrument_ct_val,
            "instrument_tick_sz": self.instrument_tick_sz,
            "quantity": self.quantity,
            "reference_price": self.reference_price,
            "min_executable_notional": self.min_executable_notional,
            "max_notional": self.max_notional,
            "position_count_limit": self.position_count_limit,
            "order_count_limit": self.order_count_limit,
            "minimum_ratified_notional_only": self.minimum_ratified_notional_only,
        }


def _dec(raw: str, *, field: str) -> Decimal:
    try:
        value = Decimal(str(raw))
    except (InvalidOperation, TypeError) as exc:
        raise LiveCanaryExposureError(f"INVALID_DECIMAL:{field}") from exc
    if value <= 0:
        raise LiveCanaryExposureError(f"NON_POSITIVE:{field}")
    return value


def derive_min_executable_notional_v1(
    *,
    quantity: str,
    reference_price: str,
    instrument_ct_val: str,
) -> str:
    """Notional ≈ qty * ctVal * price (OKX contract units; XPERP integer sz)."""
    qty = _dec(quantity, field="quantity")
    px = _dec(reference_price, field="reference_price")
    ct = _dec(instrument_ct_val, field="instrument_ct_val")
    return format(qty * ct * px, "f")


def build_canary_exposure_binding_v1(
    *,
    venue: str,
    account_scope: str,
    instrument_id: str = DEFAULT_INSTRUMENT_ID,
    side: str = DEFAULT_SIDE,
    order_type: str = DEFAULT_ORDER_TYPE,
    td_mode: str = DEFAULT_TD_MODE,
    instrument_min_sz: str,
    instrument_lot_sz: str,
    instrument_ct_val: str,
    instrument_tick_sz: str,
    quantity: str | None = None,
    reference_price: str,
    max_notional: str | None = None,
) -> CanaryExposureBindingV1:
    if str(order_type).upper() != "LIMIT":
        raise LiveCanaryExposureError("ONLY_LIMIT_ORDER_TYPE_ALLOWED")
    if str(side).upper() not in {"BUY", "SELL"}:
        raise LiveCanaryExposureError("SIDE_INVALID")
    min_sz = _dec(instrument_min_sz, field="instrument_min_sz")
    lot = _dec(instrument_lot_sz, field="instrument_lot_sz")
    if min_sz != min_sz.to_integral_value():
        raise LiveCanaryExposureError("INTEGER_CONTRACT_REQUIRED:instrument_min_sz")
    if lot != lot.to_integral_value():
        raise LiveCanaryExposureError("INTEGER_CONTRACT_REQUIRED:instrument_lot_sz")
    qty_raw = instrument_min_sz if quantity is None else quantity
    qty = _dec(qty_raw, field="quantity")
    if qty < min_sz:
        raise LiveCanaryExposureError("QUANTITY_BELOW_MIN_SZ")
    if (qty % lot) != 0:
        raise LiveCanaryExposureError("QUANTITY_NOT_MULTIPLE_OF_LOT_SZ")
    if qty != min_sz:
        raise LiveCanaryExposureError("MINIMUM_EXPOSURE_REQUIRES_MIN_SZ_QUANTITY")

    min_notional = derive_min_executable_notional_v1(
        quantity=str(qty_raw),
        reference_price=reference_price,
        instrument_ct_val=instrument_ct_val,
    )
    max_n = min_notional if max_notional is None else str(max_notional)
    if max_n != min_notional:
        raise LiveCanaryExposureError("MAX_NOTIONAL_MUST_EQUAL_MIN_EXECUTABLE")

    return CanaryExposureBindingV1(
        venue=str(venue),
        account_scope=str(account_scope),
        instrument_id=str(instrument_id or DEFAULT_INSTRUMENT_ID),
        side=str(side).upper(),
        order_type="LIMIT",
        td_mode=str(td_mode or DEFAULT_TD_MODE),
        instrument_min_sz=str(instrument_min_sz),
        instrument_lot_sz=str(instrument_lot_sz),
        instrument_ct_val=str(instrument_ct_val),
        instrument_tick_sz=str(instrument_tick_sz),
        quantity=str(qty_raw),
        reference_price=str(reference_price),
        min_executable_notional=min_notional,
        max_notional=max_n,
    )


def exposure_above_minimum_bound_v1(
    *,
    quantity: str,
    instrument_min_sz: str,
    max_notional: str,
    min_executable_notional: str,
) -> bool:
    try:
        return _dec(quantity, field="quantity") > _dec(instrument_min_sz, field="min_sz") or _dec(
            max_notional, field="max_notional"
        ) > _dec(min_executable_notional, field="min_notional")
    except LiveCanaryExposureError:
        return True


def require_instrument_metadata_fields_v1(payload: Mapping[str, Any]) -> None:
    for key in (
        "instrument_min_sz",
        "instrument_lot_sz",
        "instrument_ct_val",
        "instrument_tick_sz",
    ):
        if not str(payload.get(key) or "").strip():
            raise LiveCanaryExposureError(f"INSTRUMENT_METADATA_REQUIRED:{key}")
