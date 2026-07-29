"""Versioned simulated portfolio / economics model for Paper-Shadow Observation.

Pure offline model. Never submits orders or mutates broker state.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from decimal import Decimal
from typing import Any, Mapping, Optional

PORTFOLIO_ECONOMICS_MODEL_ID = "ops.integrated_paper_shadow_observation_portfolio_economics_v1"
PORTFOLIO_ECONOMICS_MODEL_VERSION = "v1"
PORTFOLIO_ECONOMICS_SCHEMA_ID = PORTFOLIO_ECONOMICS_MODEL_ID

_ZERO = Decimal("0")


class PortfolioEconomicsModelError(ValueError):
    """Fail-closed portfolio economics error."""


@dataclass(frozen=True)
class PortfolioEconomicsModelParamsV1:
    model_id: str = PORTFOLIO_ECONOMICS_MODEL_ID
    model_version: str = PORTFOLIO_ECONOMICS_MODEL_VERSION
    fee_rate_bps: Decimal = Decimal("2.0")  # 2 bps taker-like default
    slippage_bps: Decimal = Decimal("1.0")
    funding_rate_per_interval: Decimal = Decimal("0")
    initial_equity: Decimal = Decimal("100000")
    max_leverage: Decimal = Decimal("1")

    def digest(self) -> str:
        payload = (
            f"{self.model_id}|{self.model_version}|fee={self.fee_rate_bps}|"
            f"slip={self.slippage_bps}|fund={self.funding_rate_per_interval}|"
            f"eq={self.initial_equity}|lev={self.max_leverage}"
        )
        # Deterministic lightweight digest without importing hashlib at module import cost.
        import hashlib

        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass
class SimulatedPositionV1:
    instrument_id: str
    quantity: Decimal = _ZERO
    avg_entry_price: Decimal = _ZERO
    realized_pnl: Decimal = _ZERO
    unrealized_pnl: Decimal = _ZERO


@dataclass
class SimulatedPortfolioStateV1:
    equity: Decimal
    cash: Decimal
    positions: dict[str, SimulatedPositionV1] = field(default_factory=dict)
    cumulative_fees: Decimal = _ZERO
    cumulative_slippage: Decimal = _ZERO
    cumulative_funding: Decimal = _ZERO
    realized_pnl: Decimal = _ZERO
    unrealized_pnl: Decimal = _ZERO
    turnover_notional: Decimal = _ZERO
    fill_count: int = 0
    intended_action_count: int = 0
    peak_equity: Decimal = _ZERO
    max_drawdown: Decimal = _ZERO

    def to_dict(self) -> dict[str, Any]:
        return {
            "equity": str(self.equity),
            "cash": str(self.cash),
            "cumulative_fees": str(self.cumulative_fees),
            "cumulative_slippage": str(self.cumulative_slippage),
            "cumulative_funding": str(self.cumulative_funding),
            "realized_pnl": str(self.realized_pnl),
            "unrealized_pnl": str(self.unrealized_pnl),
            "turnover_notional": str(self.turnover_notional),
            "fill_count": self.fill_count,
            "intended_action_count": self.intended_action_count,
            "peak_equity": str(self.peak_equity),
            "max_drawdown": str(self.max_drawdown),
            "positions": {
                k: {
                    "instrument_id": v.instrument_id,
                    "quantity": str(v.quantity),
                    "avg_entry_price": str(v.avg_entry_price),
                    "realized_pnl": str(v.realized_pnl),
                    "unrealized_pnl": str(v.unrealized_pnl),
                }
                for k, v in sorted(self.positions.items())
            },
        }


@dataclass(frozen=True)
class SimulatedFillV1:
    instrument_id: str
    side: str  # BUY|SELL|FLAT
    quantity: Decimal
    mark_price: Decimal
    fill_price: Decimal
    fee: Decimal
    slippage_cost: Decimal
    notional: Decimal


@dataclass(frozen=True)
class EconomicMetricsSnapshotV1:
    fees: Decimal
    slippage: Decimal
    funding: Decimal
    turnover: Decimal
    exposure: Decimal
    drawdown: Decimal
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    equity: Decimal
    fill_count: int
    hit_rate: Decimal
    profit_factor: Decimal

    def to_dict(self) -> dict[str, Any]:
        return {k: (str(v) if isinstance(v, Decimal) else v) for k, v in asdict(self).items()}


class SimulatedPortfolioEconomicsModelV1:
    """Canonical producer for simulated fill/fee/slippage/PnL/funding."""

    def __init__(self, params: PortfolioEconomicsModelParamsV1 | None = None) -> None:
        self.params = params or PortfolioEconomicsModelParamsV1()
        if self.params.max_leverage <= 0:
            raise PortfolioEconomicsModelError("MAX_LEVERAGE_MUST_BE_POSITIVE")
        if self.params.initial_equity <= 0:
            raise PortfolioEconomicsModelError("INITIAL_EQUITY_MUST_BE_POSITIVE")
        self.state = SimulatedPortfolioStateV1(
            equity=self.params.initial_equity,
            cash=self.params.initial_equity,
            peak_equity=self.params.initial_equity,
        )
        self._wins = 0
        self._losses = 0
        self._gross_profit = _ZERO
        self._gross_loss = _ZERO

    @property
    def model_id(self) -> str:
        return PORTFOLIO_ECONOMICS_MODEL_ID

    @property
    def model_version(self) -> str:
        return PORTFOLIO_ECONOMICS_MODEL_VERSION

    def model_digest(self) -> str:
        return self.params.digest()

    def apply_intended_action(
        self,
        *,
        instrument_id: str,
        side: str,
        quantity: Decimal,
        mark_price: Decimal,
    ) -> Optional[SimulatedFillV1]:
        """Apply a simulated intended action. Never emits broker writes."""
        side_u = str(side or "").strip().upper()
        if side_u in {"", "HOLD", "NONE", "FLAT"}:
            self.state.intended_action_count += 1
            self._mark_to_market(instrument_id=instrument_id, mark_price=mark_price)
            return None
        if side_u not in {"BUY", "SELL"}:
            raise PortfolioEconomicsModelError(f"INVALID_SIDE:{side_u}")
        if quantity <= 0:
            raise PortfolioEconomicsModelError("QUANTITY_MUST_BE_POSITIVE")
        if mark_price <= 0:
            raise PortfolioEconomicsModelError("MARK_PRICE_MUST_BE_POSITIVE")

        slip_mult = self.params.slippage_bps / Decimal("10000")
        fill_price = (
            mark_price * (Decimal("1") + slip_mult)
            if side_u == "BUY"
            else mark_price * (Decimal("1") - slip_mult)
        )
        notional = (quantity * fill_price).copy_abs()
        fee = notional * (self.params.fee_rate_bps / Decimal("10000"))
        slippage_cost = (fill_price - mark_price).copy_abs() * quantity
        fill = SimulatedFillV1(
            instrument_id=instrument_id,
            side=side_u,
            quantity=quantity,
            mark_price=mark_price,
            fill_price=fill_price,
            fee=fee,
            slippage_cost=slippage_cost,
            notional=notional,
        )
        self._apply_fill(fill)
        self.state.intended_action_count += 1
        self.state.fill_count += 1
        self.state.cumulative_fees += fee
        self.state.cumulative_slippage += slippage_cost
        self.state.turnover_notional += notional
        self._apply_funding(instrument_id=instrument_id, mark_price=mark_price)
        self._mark_to_market(instrument_id=instrument_id, mark_price=mark_price)
        self._update_equity_drawdown()
        return fill

    def economic_metrics(self) -> EconomicMetricsSnapshotV1:
        exposure = sum(
            (p.quantity * p.avg_entry_price).copy_abs() for p in self.state.positions.values()
        )
        hit_rate = (
            Decimal(self._wins) / Decimal(self._wins + self._losses)
            if (self._wins + self._losses) > 0
            else _ZERO
        )
        profit_factor = (
            self._gross_profit / self._gross_loss if self._gross_loss > 0 else Decimal("0")
        )
        return EconomicMetricsSnapshotV1(
            fees=self.state.cumulative_fees,
            slippage=self.state.cumulative_slippage,
            funding=self.state.cumulative_funding,
            turnover=self.state.turnover_notional,
            exposure=exposure,
            drawdown=self.state.max_drawdown,
            realized_pnl=self.state.realized_pnl,
            unrealized_pnl=self.state.unrealized_pnl,
            equity=self.state.equity,
            fill_count=self.state.fill_count,
            hit_rate=hit_rate,
            profit_factor=profit_factor,
        )

    def snapshot(self) -> Mapping[str, Any]:
        return {
            "model_id": self.model_id,
            "model_version": self.model_version,
            "model_digest": self.model_digest(),
            "params": {
                "fee_rate_bps": str(self.params.fee_rate_bps),
                "slippage_bps": str(self.params.slippage_bps),
                "funding_rate_per_interval": str(self.params.funding_rate_per_interval),
                "initial_equity": str(self.params.initial_equity),
                "max_leverage": str(self.params.max_leverage),
            },
            "state": self.state.to_dict(),
            "economic_metrics": self.economic_metrics().to_dict(),
            "broker_writes": False,
            "orders_submitted": False,
        }

    def _apply_fill(self, fill: SimulatedFillV1) -> None:
        pos = self.state.positions.get(fill.instrument_id) or SimulatedPositionV1(
            instrument_id=fill.instrument_id
        )
        signed_qty = fill.quantity if fill.side == "BUY" else -fill.quantity
        new_qty = pos.quantity + signed_qty
        if (
            pos.quantity == 0
            or (pos.quantity > 0 and signed_qty > 0)
            or (pos.quantity < 0 and signed_qty < 0)
        ):
            # Increasing / opening
            total_cost = (
                pos.avg_entry_price * pos.quantity.copy_abs() + fill.fill_price * fill.quantity
            )
            pos.avg_entry_price = total_cost / new_qty.copy_abs() if new_qty != 0 else _ZERO
            pos.quantity = new_qty
        else:
            # Reducing / closing
            closed = min(pos.quantity.copy_abs(), fill.quantity)
            pnl = (
                (fill.fill_price - pos.avg_entry_price) * closed
                if pos.quantity > 0
                else (pos.avg_entry_price - fill.fill_price) * closed
            )
            pos.realized_pnl += pnl
            self.state.realized_pnl += pnl
            if pnl >= 0:
                self._wins += 1
                self._gross_profit += pnl
            else:
                self._losses += 1
                self._gross_loss += pnl.copy_abs()
            pos.quantity = new_qty
            if pos.quantity == 0:
                pos.avg_entry_price = _ZERO
        self.state.cash -= fill.fee
        if fill.side == "BUY":
            self.state.cash -= fill.notional
        else:
            self.state.cash += fill.notional
        self.state.positions[fill.instrument_id] = pos

    def _apply_funding(self, *, instrument_id: str, mark_price: Decimal) -> None:
        pos = self.state.positions.get(instrument_id)
        if pos is None or pos.quantity == 0:
            return
        notional = pos.quantity.copy_abs() * mark_price
        funding = notional * self.params.funding_rate_per_interval
        # Longs pay positive funding by convention here.
        signed = funding if pos.quantity > 0 else -funding
        self.state.cumulative_funding += signed
        self.state.cash -= signed

    def _mark_to_market(self, *, instrument_id: str, mark_price: Decimal) -> None:
        pos = self.state.positions.get(instrument_id)
        if pos is not None and pos.quantity != 0 and mark_price > 0:
            if pos.quantity > 0:
                pos.unrealized_pnl = pos.quantity * (mark_price - pos.avg_entry_price)
            else:
                pos.unrealized_pnl = (-pos.quantity) * (pos.avg_entry_price - mark_price)
        self.state.unrealized_pnl = sum(
            (p.unrealized_pnl for p in self.state.positions.values()),
            _ZERO,
        )

    def _update_equity_drawdown(self) -> None:
        self.state.equity = self.state.cash + self.state.unrealized_pnl
        if self.state.equity > self.state.peak_equity:
            self.state.peak_equity = self.state.equity
        dd = (
            (self.state.peak_equity - self.state.equity) / self.state.peak_equity
            if self.state.peak_equity > 0
            else _ZERO
        )
        if dd > self.state.max_drawdown:
            self.state.max_drawdown = dd
