"""Simulated fill model (fee/slippage) — no portfolio authority."""

from __future__ import annotations

import hashlib
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Optional

from src.ops.productive_futures_accounting_runtime_binding_v1.constants_v1 import (
    DEFAULT_FEE_RATE_BPS,
    DEFAULT_SLIPPAGE_BPS,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.models_v1 import (
    ContractMetadataV1,
    SimulatedFillInputV1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.reason_codes_v1 import (
    AccountingFailureCodeV1,
)


class FillModelError(ValueError):
    """Fail-closed fill model error."""

    def __init__(self, code: AccountingFailureCodeV1, detail: str = "") -> None:
        self.code = code
        super().__init__(f"{code.value}:{detail}" if detail else code.value)


def _to_decimal(name: str, value: Decimal | str | int | float) -> Decimal:
    d = value if isinstance(value, Decimal) else Decimal(str(value))
    if not d.is_finite():
        raise FillModelError(
            AccountingFailureCodeV1.NON_REPRESENTABLE_QUANTITY, f"{name}_not_finite"
        )
    return d


def build_simulated_fill_v1(
    *,
    fill_id: str,
    instrument_id: str,
    side: str,
    quantity: Decimal | str | int | float,
    mark_price: Decimal | str | int | float | None,
    contract: ContractMetadataV1,
    fee_rate_bps: Decimal | str = DEFAULT_FEE_RATE_BPS,
    slippage_bps: Decimal | str = DEFAULT_SLIPPAGE_BPS,
    reduce_only: bool = False,
    event_time_unix: Optional[float] = None,
) -> SimulatedFillInputV1:
    """Build a deterministic simulated fill. Does not mutate portfolio/accounting state."""
    if not str(fill_id or "").strip():
        raise FillModelError(AccountingFailureCodeV1.MISSING_FILL_ID)
    side_u = str(side or "").strip().upper()
    if side_u not in {"BUY", "SELL"}:
        raise FillModelError(AccountingFailureCodeV1.INVALID_SIDE, side_u)
    if mark_price is None:
        raise FillModelError(AccountingFailureCodeV1.MISSING_MARK_PRICE)
    qty = _to_decimal("quantity", quantity)
    mark = _to_decimal("mark_price", mark_price)
    if qty == 0:
        raise FillModelError(AccountingFailureCodeV1.ZERO_QUANTITY)
    if qty < 0:
        raise FillModelError(AccountingFailureCodeV1.NEGATIVE_QUANTITY)
    if mark <= 0:
        raise FillModelError(AccountingFailureCodeV1.INVALID_MARK_PRICE)

    # Deterministic quantity representability vs min_qty / lot step.
    min_qty = contract.min_qty
    steps = (qty / min_qty).to_integral_value(rounding=ROUND_HALF_EVEN)
    quantized = steps * min_qty
    if quantized != qty:
        raise FillModelError(
            AccountingFailureCodeV1.NON_REPRESENTABLE_QUANTITY,
            f"qty={qty} min_qty={min_qty}",
        )

    fee_bps = _to_decimal("fee_rate_bps", fee_rate_bps)
    slip_bps = _to_decimal("slippage_bps", slippage_bps)
    if fee_bps < 0 or slip_bps < 0:
        raise FillModelError(AccountingFailureCodeV1.KERNEL_VALIDATION_FAILED, "negative_bps")

    slip_mult = slip_bps / Decimal("10000")
    raw_fill = (
        mark * (Decimal("1") + slip_mult) if side_u == "BUY" else mark * (Decimal("1") - slip_mult)
    )
    fill_price = raw_fill.quantize(contract.tick_size, rounding=ROUND_HALF_EVEN)
    if fill_price <= 0:
        raise FillModelError(AccountingFailureCodeV1.INVALID_MARK_PRICE, "fill_price")

    notional = (qty * fill_price * contract.contract_size).copy_abs()
    fee = (notional * fee_bps / Decimal("10000")).quantize(
        Decimal("0.00000001"), rounding=ROUND_HALF_EVEN
    )
    slippage_cost = ((fill_price - mark).copy_abs() * qty * contract.contract_size).quantize(
        Decimal("0.00000001"), rounding=ROUND_HALF_EVEN
    )
    return SimulatedFillInputV1(
        fill_id=str(fill_id),
        instrument_id=str(instrument_id),
        side=side_u,
        quantity=qty,
        mark_price=mark,
        fill_price=fill_price,
        fee=fee,
        slippage_cost=slippage_cost,
        notional=notional,
        reduce_only=bool(reduce_only),
        event_time_unix=event_time_unix,
    )


def deterministic_fill_id_v1(
    *,
    session_id: str,
    cycle_index: int,
    instrument_id: str,
    side: str,
    quantity: str,
    mark_price: str,
) -> str:
    payload = f"{session_id}|{cycle_index}|{instrument_id}|{side}|{quantity}|{mark_price}"
    return "fill_" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]
