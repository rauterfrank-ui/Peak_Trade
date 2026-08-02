"""Productive accounting engine — reuses canonical futures_accounting kernel only."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Any, Mapping, Optional

from src.execution.paper.futures_accounting import (
    FuturesInstrumentSpec,
    FuturesMarginSpec,
    FuturesPosition,
    FuturesSide,
    build_futures_paper_accounting_snapshot_v0,
    notional_value,
    reduce_position,
    unrealized_pnl,
    validate_futures_accounting_inputs,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.constants_v1 import (
    CANONICAL_KERNEL_OWNER,
    DEFAULT_INITIAL_EQUITY,
    SINGLE_WRITER_IDENTITY,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.models_v1 import (
    AccountingApplyResultV1,
    AccountingPortfolioStateV1,
    AccountingPositionStateV1,
    AccountingRiskStateV1,
    ContractMetadataV1,
    SimulatedFillInputV1,
    sha256_hex,
    canonical_json_dumps,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.reason_codes_v1 import (
    AccountingFailureCodeV1,
    AccountingSuccessCodeV1,
)


class AccountingEngineError(RuntimeError):
    """Fail-closed productive accounting error."""

    def __init__(self, code: AccountingFailureCodeV1, detail: str = "") -> None:
        self.code = code
        super().__init__(f"{code.value}:{detail}" if detail else code.value)


def _to_decimal(name: str, value: Decimal | str | int | float) -> Decimal:
    d = value if isinstance(value, Decimal) else Decimal(str(value))
    if not d.is_finite():
        raise AccountingEngineError(
            AccountingFailureCodeV1.NON_REPRESENTABLE_QUANTITY, f"{name}_not_finite"
        )
    return d


def validate_contract_metadata_v1(contract: ContractMetadataV1) -> None:
    try:
        instrument = FuturesInstrumentSpec(
            symbol=contract.symbol,
            contract_size=contract.contract_size,
            tick_size=contract.tick_size,
            min_qty=contract.min_qty,
            quote_currency=contract.quote_currency,
        )
        margin = FuturesMarginSpec(
            initial_margin_rate=contract.initial_margin_rate,
            maintenance_margin_rate=contract.maintenance_margin_rate,
            max_leverage=contract.max_leverage,
        )
        validate_futures_accounting_inputs(instrument=instrument, margin=margin)
    except Exception as exc:  # noqa: BLE001
        raise AccountingEngineError(
            AccountingFailureCodeV1.INVALID_CONTRACT_METADATA, str(exc)
        ) from exc


def _instrument(contract: ContractMetadataV1) -> FuturesInstrumentSpec:
    return FuturesInstrumentSpec(
        symbol=contract.symbol,
        contract_size=contract.contract_size,
        tick_size=contract.tick_size,
        min_qty=contract.min_qty,
        quote_currency=contract.quote_currency,
    )


def _margin(contract: ContractMetadataV1) -> FuturesMarginSpec:
    return FuturesMarginSpec(
        initial_margin_rate=contract.initial_margin_rate,
        maintenance_margin_rate=contract.maintenance_margin_rate,
        max_leverage=contract.max_leverage,
    )


def _side_from_buy_sell(side: str) -> FuturesSide:
    side_u = str(side).upper()
    if side_u == "BUY":
        return FuturesSide.LONG
    if side_u == "SELL":
        return FuturesSide.SHORT
    raise AccountingEngineError(AccountingFailureCodeV1.INVALID_SIDE, side_u)


@dataclass
class ProductiveFuturesAccountingSessionV1:
    """Single-writer in-memory accounting session backed by futures_accounting kernel."""

    contract: ContractMetadataV1
    initial_equity: Decimal = field(default_factory=lambda: Decimal(DEFAULT_INITIAL_EQUITY))
    writer_identity: str = SINGLE_WRITER_IDENTITY
    position: Optional[FuturesPosition] = None
    cumulative_fees: Decimal = field(default_factory=lambda: Decimal("0"))
    cumulative_slippage: Decimal = field(default_factory=lambda: Decimal("0"))
    realized_pnl: Decimal = field(default_factory=lambda: Decimal("0"))
    last_mark: Optional[Decimal] = None
    applied_fill_results: dict[str, AccountingApplyResultV1] = field(default_factory=dict)
    fill_order: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        validate_contract_metadata_v1(self.contract)
        self.initial_equity = _to_decimal("initial_equity", self.initial_equity)

    @property
    def kernel_owner(self) -> str:
        return CANONICAL_KERNEL_OWNER

    def portfolio_state(self) -> AccountingPortfolioStateV1:
        positions: list[AccountingPositionStateV1] = []
        unreal = Decimal("0")
        if self.position is not None and self.position.qty > 0:
            mark = self.last_mark if self.last_mark is not None else self.position.mark_price
            upnl = unrealized_pnl(
                side=self.position.side,
                entry_price=self.position.entry_price,
                mark_price=mark,
                qty=self.position.qty,
                contract_size=self.contract.contract_size,
            )
            unreal = upnl
            positions.append(
                AccountingPositionStateV1(
                    symbol=self.position.symbol,
                    side=self.position.side.value,
                    quantity=self.position.qty,
                    entry_price=self.position.entry_price,
                    mark_price=mark,
                    realized_pnl=self.position.realized_pnl,
                    unrealized_pnl=upnl,
                    fees_paid=self.position.fees_paid,
                    funding_pnl=self.position.funding_pnl,
                )
            )
        equity = (
            self.initial_equity
            + self.realized_pnl
            + unreal
            - self.cumulative_fees
            - self.cumulative_slippage
        )
        return AccountingPortfolioStateV1(
            equity=equity.quantize(Decimal("0.00000001"), rounding=ROUND_HALF_EVEN),
            initial_equity=self.initial_equity,
            realized_pnl=self.realized_pnl,
            unrealized_pnl=unreal,
            cumulative_fees=self.cumulative_fees,
            cumulative_slippage=self.cumulative_slippage,
            positions=tuple(positions),
            fill_count=len(self.fill_order),
            applied_fill_ids=tuple(self.fill_order),
        )

    def risk_state(self, *, mark_price: Optional[Decimal] = None) -> AccountingRiskStateV1:
        mark = mark_price if mark_price is not None else self.last_mark
        if mark is None or mark <= 0:
            if self.position is None or self.position.qty <= 0:
                return AccountingRiskStateV1(
                    notional=Decimal("0"),
                    initial_margin_required=Decimal("0"),
                    maintenance_margin_required=Decimal("0"),
                    liquidation_proximity=None,
                    mark_price=Decimal("0"),
                    contract_size=self.contract.contract_size,
                )
            raise AccountingEngineError(AccountingFailureCodeV1.MISSING_MARK_PRICE)
        if self.position is None or self.position.qty <= 0:
            return AccountingRiskStateV1(
                notional=Decimal("0"),
                initial_margin_required=Decimal("0"),
                maintenance_margin_required=Decimal("0"),
                liquidation_proximity=None,
                mark_price=mark,
                contract_size=self.contract.contract_size,
            )
        snap = build_futures_paper_accounting_snapshot_v0(
            instrument=_instrument(self.contract),
            margin=_margin(self.contract),
            position=self.position,
            mark_price=mark,
            equity=self.portfolio_state().equity,
        )
        return AccountingRiskStateV1(
            notional=snap.notional,
            initial_margin_required=snap.initial_margin_required,
            maintenance_margin_required=snap.maintenance_margin_required,
            liquidation_proximity=(
                None if snap.liquidation_proximity is None else snap.liquidation_proximity.value
            ),
            mark_price=mark,
            contract_size=self.contract.contract_size,
        )

    def mark_to_market(self, mark_price: Decimal | str | int | float) -> AccountingApplyResultV1:
        mark = _to_decimal("mark_price", mark_price)
        if mark <= 0:
            raise AccountingEngineError(AccountingFailureCodeV1.INVALID_MARK_PRICE)
        self.last_mark = mark
        if self.position is not None and self.position.qty > 0:
            self.position = FuturesPosition(
                symbol=self.position.symbol,
                side=self.position.side,
                qty=self.position.qty,
                entry_price=self.position.entry_price,
                mark_price=mark,
                realized_pnl=self.position.realized_pnl,
                funding_pnl=self.position.funding_pnl,
                fees_paid=self.position.fees_paid,
            )
        portfolio = self.portfolio_state()
        risk = self.risk_state(mark_price=mark)
        out = {
            "action": AccountingSuccessCodeV1.MARK_TO_MARKET.value,
            "portfolio": portfolio.to_dict(),
            "risk": risk.to_dict(),
        }
        return AccountingApplyResultV1(
            ok=True,
            action_code=AccountingSuccessCodeV1.MARK_TO_MARKET.value,
            fill_input_digest="",
            accounting_output_digest=sha256_hex(canonical_json_dumps(out)),
            portfolio_state=portfolio,
            risk_state=risk,
            notes=("KERNEL_UNREALIZED_PNL",),
        )

    def apply_fill(self, fill: SimulatedFillInputV1) -> AccountingApplyResultV1:
        """Apply fill through canonical kernel semantics. Idempotent by fill_id."""
        if fill.fill_id in self.applied_fill_results:
            prior = self.applied_fill_results[fill.fill_id]
            return AccountingApplyResultV1(
                ok=prior.ok,
                action_code=AccountingSuccessCodeV1.IDEMPOTENT_REPLAY.value,
                fill_input_digest=prior.fill_input_digest,
                accounting_output_digest=prior.accounting_output_digest,
                portfolio_state=self.portfolio_state(),
                risk_state=self.risk_state(
                    mark_price=fill.mark_price if fill.mark_price > 0 else self.last_mark
                ),
                idempotent_replay=True,
                notes=("IDEMPOTENT_FILL_REPLAY",),
            )

        validate_contract_metadata_v1(self.contract)
        if fill.instrument_id != self.contract.symbol and fill.instrument_id not in {
            self.contract.symbol,
        }:
            # Allow venue-native id equality only; productive single-future uses one symbol.
            if self.position is not None and fill.instrument_id != self.position.symbol:
                raise AccountingEngineError(
                    AccountingFailureCodeV1.PORTFOLIO_STATE_CONTRADICTION,
                    "instrument_mismatch",
                )

        if fill.mark_price is None:
            raise AccountingEngineError(AccountingFailureCodeV1.MISSING_MARK_PRICE)
        mark = _to_decimal("mark_price", fill.mark_price)
        if mark <= 0:
            raise AccountingEngineError(AccountingFailureCodeV1.INVALID_MARK_PRICE)
        qty = _to_decimal("quantity", fill.quantity)
        if qty == 0:
            raise AccountingEngineError(AccountingFailureCodeV1.ZERO_QUANTITY)
        if qty < 0:
            raise AccountingEngineError(AccountingFailureCodeV1.NEGATIVE_QUANTITY)

        fill_price = _to_decimal("fill_price", fill.fill_price)
        fee = _to_decimal("fee", fill.fee)
        slip = _to_decimal("slippage_cost", fill.slippage_cost)
        intended_side = _side_from_buy_sell(fill.side)

        open_qty = Decimal("0") if self.position is None else self.position.qty
        open_side = None if self.position is None or open_qty <= 0 else self.position.side

        is_reduce = open_side is not None and (
            (open_side == FuturesSide.LONG and intended_side == FuturesSide.SHORT)
            or (open_side == FuturesSide.SHORT and intended_side == FuturesSide.LONG)
        )
        is_increase_or_open = not is_reduce

        if fill.reduce_only and is_increase_or_open:
            raise AccountingEngineError(AccountingFailureCodeV1.REDUCE_ONLY_VIOLATION)

        if is_reduce and open_side is not None:
            if qty > open_qty:
                raise AccountingEngineError(
                    AccountingFailureCodeV1.OVER_REDUCE, f"{qty}>{open_qty}"
                )
            # Exact close or partial reduce via kernel.
            assert self.position is not None
            before_realized = self.position.realized_pnl
            try:
                new_pos = reduce_position(
                    self.position,
                    contract_size=self.contract.contract_size,
                    close_qty=qty,
                    close_price=fill_price,
                    fee_quote=fee,
                )
            except ValueError as exc:
                raise AccountingEngineError(
                    AccountingFailureCodeV1.KERNEL_VALIDATION_FAILED, str(exc)
                ) from exc
            realized_delta = new_pos.realized_pnl - before_realized
            self.realized_pnl += realized_delta
            self.cumulative_fees += fee
            self.cumulative_slippage += slip
            self.last_mark = mark
            if new_pos.qty == 0:
                self.position = None
                action = (
                    AccountingSuccessCodeV1.LONG_CLOSE
                    if open_side == FuturesSide.LONG
                    else AccountingSuccessCodeV1.SHORT_CLOSE
                )
            else:
                self.position = FuturesPosition(
                    symbol=new_pos.symbol,
                    side=new_pos.side,
                    qty=new_pos.qty,
                    entry_price=new_pos.entry_price,
                    mark_price=mark,
                    realized_pnl=new_pos.realized_pnl,
                    funding_pnl=new_pos.funding_pnl,
                    fees_paid=new_pos.fees_paid,
                )
                action = (
                    AccountingSuccessCodeV1.LONG_REDUCE
                    if open_side == FuturesSide.LONG
                    else AccountingSuccessCodeV1.SHORT_REDUCE
                )
        else:
            # Open or same-side increase — flip across zero is forbidden.
            if open_side is not None and open_side != intended_side:
                raise AccountingEngineError(AccountingFailureCodeV1.POSITION_FLIP_BLOCKED)
            if open_side is None:
                try:
                    pos = FuturesPosition(
                        symbol=self.contract.symbol,
                        side=intended_side,
                        qty=qty,
                        entry_price=fill_price,
                        mark_price=mark,
                        realized_pnl=Decimal("0"),
                        funding_pnl=Decimal("0"),
                        fees_paid=fee,
                    )
                    validate_futures_accounting_inputs(
                        instrument=_instrument(self.contract),
                        margin=_margin(self.contract),
                        position=pos,
                    )
                except Exception as exc:  # noqa: BLE001
                    raise AccountingEngineError(
                        AccountingFailureCodeV1.KERNEL_VALIDATION_FAILED, str(exc)
                    ) from exc
                self.position = pos
                self.cumulative_fees += fee
                self.cumulative_slippage += slip
                self.last_mark = mark
                action = (
                    AccountingSuccessCodeV1.LONG_OPEN
                    if intended_side == FuturesSide.LONG
                    else AccountingSuccessCodeV1.SHORT_OPEN
                )
            else:
                assert self.position is not None
                new_qty = open_qty + qty
                new_entry = ((self.position.entry_price * open_qty) + (fill_price * qty)) / new_qty
                new_entry = new_entry.quantize(self.contract.tick_size, rounding=ROUND_HALF_EVEN)
                pos = FuturesPosition(
                    symbol=self.position.symbol,
                    side=intended_side,
                    qty=new_qty,
                    entry_price=new_entry,
                    mark_price=mark,
                    realized_pnl=self.position.realized_pnl,
                    funding_pnl=self.position.funding_pnl,
                    fees_paid=self.position.fees_paid + fee,
                )
                try:
                    validate_futures_accounting_inputs(
                        instrument=_instrument(self.contract),
                        margin=_margin(self.contract),
                        position=pos,
                    )
                    # Prove notional path uses contract multiplier.
                    _ = notional_value(
                        mark_price=mark,
                        qty=new_qty,
                        contract_size=self.contract.contract_size,
                    )
                except Exception as exc:  # noqa: BLE001
                    raise AccountingEngineError(
                        AccountingFailureCodeV1.KERNEL_VALIDATION_FAILED, str(exc)
                    ) from exc
                self.position = pos
                self.cumulative_fees += fee
                self.cumulative_slippage += slip
                self.last_mark = mark
                action = (
                    AccountingSuccessCodeV1.LONG_INCREASE
                    if intended_side == FuturesSide.LONG
                    else AccountingSuccessCodeV1.SHORT_INCREASE
                )

        portfolio = self.portfolio_state()
        risk = self.risk_state(mark_price=mark)
        out_payload = {
            "action": action.value,
            "fill": fill.to_dict(),
            "portfolio": portfolio.to_dict(),
            "risk": risk.to_dict(),
            "kernel_owner": CANONICAL_KERNEL_OWNER,
        }
        result = AccountingApplyResultV1(
            ok=True,
            action_code=action.value,
            fill_input_digest=fill.digest(),
            accounting_output_digest=sha256_hex(canonical_json_dumps(out_payload)),
            portfolio_state=portfolio,
            risk_state=risk,
            notes=("CANONICAL_KERNEL_APPLIED",),
        )
        self.applied_fill_results[fill.fill_id] = result
        self.fill_order.append(fill.fill_id)
        return result

    def to_durable_dict(self) -> dict[str, Any]:
        return {
            "contract": self.contract.to_dict(),
            "initial_equity": str(self.initial_equity),
            "writer_identity": self.writer_identity,
            "cumulative_fees": str(self.cumulative_fees),
            "cumulative_slippage": str(self.cumulative_slippage),
            "realized_pnl": str(self.realized_pnl),
            "last_mark": None if self.last_mark is None else str(self.last_mark),
            "fill_order": list(self.fill_order),
            "applied_fill_results": {k: v.to_dict() for k, v in self.applied_fill_results.items()},
            "position": None
            if self.position is None
            else {
                "symbol": self.position.symbol,
                "side": self.position.side.value,
                "qty": str(self.position.qty),
                "entry_price": str(self.position.entry_price),
                "mark_price": str(self.position.mark_price),
                "realized_pnl": str(self.position.realized_pnl),
                "funding_pnl": str(self.position.funding_pnl),
                "fees_paid": str(self.position.fees_paid),
            },
            "portfolio_state": self.portfolio_state().to_dict(),
            "risk_state": self.risk_state().to_dict(),
            "kernel_owner": CANONICAL_KERNEL_OWNER,
        }

    @classmethod
    def from_durable_dict(cls, payload: Mapping[str, Any]) -> ProductiveFuturesAccountingSessionV1:
        c = payload.get("contract") or {}
        contract = ContractMetadataV1(
            symbol=str(c["symbol"]),
            contract_size=Decimal(str(c["contract_size"])),
            tick_size=Decimal(str(c["tick_size"])),
            min_qty=Decimal(str(c["min_qty"])),
            quote_currency=str(c["quote_currency"]),
            initial_margin_rate=Decimal(str(c["initial_margin_rate"])),
            maintenance_margin_rate=Decimal(str(c["maintenance_margin_rate"])),
            max_leverage=Decimal(str(c["max_leverage"])),
        )
        session = cls(
            contract=contract,
            initial_equity=Decimal(str(payload.get("initial_equity") or DEFAULT_INITIAL_EQUITY)),
            writer_identity=str(payload.get("writer_identity") or SINGLE_WRITER_IDENTITY),
        )
        session.cumulative_fees = Decimal(str(payload.get("cumulative_fees") or "0"))
        session.cumulative_slippage = Decimal(str(payload.get("cumulative_slippage") or "0"))
        session.realized_pnl = Decimal(str(payload.get("realized_pnl") or "0"))
        lm = payload.get("last_mark")
        session.last_mark = None if lm is None else Decimal(str(lm))
        session.fill_order = [str(x) for x in (payload.get("fill_order") or [])]
        pos = payload.get("position")
        if pos:
            session.position = FuturesPosition(
                symbol=str(pos["symbol"]),
                side=FuturesSide(str(pos["side"])),
                qty=Decimal(str(pos["qty"])),
                entry_price=Decimal(str(pos["entry_price"])),
                mark_price=Decimal(str(pos["mark_price"])),
                realized_pnl=Decimal(str(pos["realized_pnl"])),
                funding_pnl=Decimal(str(pos.get("funding_pnl") or "0")),
                fees_paid=Decimal(str(pos.get("fees_paid") or "0")),
            )
        # Rebuild idempotency map from durable results (portfolio refreshed live).
        for fid, raw in (payload.get("applied_fill_results") or {}).items():
            session.applied_fill_results[str(fid)] = AccountingApplyResultV1(
                ok=bool(raw.get("ok", True)),
                action_code=str(
                    raw.get("action_code") or AccountingSuccessCodeV1.IDEMPOTENT_REPLAY.value
                ),
                fill_input_digest=str(raw.get("fill_input_digest") or ""),
                accounting_output_digest=str(raw.get("accounting_output_digest") or ""),
                portfolio_state=session.portfolio_state(),
                risk_state=session.risk_state(),
                idempotent_replay=True,
                failure_code=raw.get("failure_code"),
                notes=tuple(raw.get("notes") or ("RELOADED",)),
            )
        return session
