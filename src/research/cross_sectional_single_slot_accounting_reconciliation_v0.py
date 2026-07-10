"""Canonical accounting reconciliation for cross-sectional single-slot backtests v0.

Fail-closed reconciliation between equity change and closed-trade ledger totals.
Research-only; no runtime, order, or authority effect.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from src.research.cross_sectional_single_slot_backtest_wiring_v0 import (
    END_OF_WINDOW_POLICY,
)
from src.research.cross_sectional_trade_record_schema_v0 import CANONICAL_PNL_FIELD

PACKAGE_MARKER = "CROSS_SECTIONAL_SINGLE_SLOT_ACCOUNTING_RECONCILIATION_V0=true"
SCHEMA_VERSION = "cross_sectional_single_slot_accounting_reconciliation.v0"

DECIMAL_TOLERANCE_ABS = 0.01
DECIMAL_TOLERANCE_REL = 1e-9

FAILURE_OPEN_POSITION_ENTRY_COST_UNBOOKED = "OPEN_POSITION_ENTRY_COST_UNBOOKED"
FAILURE_FORCED_END_OF_WINDOW_LIQUIDATION_MISSING = "FORCED_END_OF_WINDOW_LIQUIDATION"
FAILURE_FEES_NOT_ALLOCATED = "FEES_NOT_ALLOCATED_TO_CLOSED_TRADES"
FAILURE_IMPLEMENTATION_DEFECT = "IMPLEMENTATION_DEFECT"


@dataclass(frozen=True)
class OpenPositionStateV0:
    had_open_position_at_window_end: bool
    instrument_id: str | None
    side: str | None
    entry_time: str | None
    entry_price: float | None
    entry_cost: float | None


@dataclass(frozen=True)
class AccountingReconciliationResultV0:
    reconciled: bool
    initial_cash: float
    final_equity: float
    equity_change: float
    realized_net_pnl_from_trades: float
    realized_gross_pnl: float
    fees_total: float
    slippage_impact: float
    spread_drag: float
    funding_drag: float
    accounting_delta: float
    tolerance_abs: float
    failure_class: str | None
    end_of_window_policy: str
    open_position_state: OpenPositionStateV0
    component_breakdown: dict[str, float]


def _trade_records(backtest: Any) -> list[dict[str, Any]]:
    if getattr(backtest, "trades", None) is None or backtest.trades.empty:
        return []
    return backtest.trades.to_dict(orient="records")


def detect_open_position_at_window_end(
    orchestrator_result: Any,
) -> OpenPositionStateV0:
    final_side = getattr(orchestrator_result, "final_slot_side", None)
    final_instrument = getattr(orchestrator_result, "final_instrument_id", None)
    side_value = final_side.value if final_side is not None else None
    had_open = side_value not in (None, "FLAT")
    return OpenPositionStateV0(
        had_open_position_at_window_end=had_open,
        instrument_id=final_instrument,
        side=side_value,
        entry_time=None,
        entry_price=None,
        entry_cost=None,
    )


def reconcile_single_slot_backtest_accounting_v0(
    backtest: Any,
    *,
    orchestrator_result: Any | None = None,
    funding_drag: float = 0.0,
    spread_drag: float = 0.0,
) -> AccountingReconciliationResultV0:
    """Reconcile equity change against closed-trade ledger totals."""
    initial = float(backtest.initial_cash)
    final_equity = float(backtest.final_equity)
    equity_change = final_equity - initial
    trades = _trade_records(backtest)

    realized_net = sum(float(row.get(CANONICAL_PNL_FIELD, 0.0)) for row in trades)
    realized_gross = sum(float(row.get("gross_pnl", 0.0)) for row in trades)
    entry_costs = sum(float(row.get("entry_cost", 0.0)) for row in trades)
    exit_costs = sum(float(row.get("exit_cost", 0.0)) for row in trades)
    fees_total = entry_costs + exit_costs

    open_state = (
        detect_open_position_at_window_end(orchestrator_result)
        if orchestrator_result is not None
        else OpenPositionStateV0(False, None, None, None, None, None)
    )

    ledger_implied_equity_change = realized_net - entry_costs
    gross_net_equity_change = realized_gross - entry_costs - exit_costs
    accounting_delta = equity_change - ledger_implied_equity_change
    gross_accounting_delta = equity_change - gross_net_equity_change
    tolerance_abs = max(DECIMAL_TOLERANCE_ABS, abs(equity_change) * DECIMAL_TOLERANCE_REL)

    failure_class: str | None = None
    if open_state.had_open_position_at_window_end:
        end_of_window_trades = [
            row for row in trades if row.get("close_reason") == "end_of_window_force_close"
        ]
        if not end_of_window_trades:
            failure_class = FAILURE_FORCED_END_OF_WINDOW_LIQUIDATION_MISSING
    if failure_class is None and abs(accounting_delta) > tolerance_abs:
        if abs(gross_accounting_delta) <= tolerance_abs:
            failure_class = FAILURE_FEES_NOT_ALLOCATED
        else:
            failure_class = FAILURE_IMPLEMENTATION_DEFECT

    reconciled = failure_class is None and abs(accounting_delta) <= tolerance_abs

    return AccountingReconciliationResultV0(
        reconciled=reconciled,
        initial_cash=initial,
        final_equity=final_equity,
        equity_change=equity_change,
        realized_net_pnl_from_trades=realized_net,
        realized_gross_pnl=realized_gross,
        fees_total=fees_total,
        slippage_impact=float(backtest.slippage_impact),
        spread_drag=spread_drag,
        funding_drag=funding_drag,
        accounting_delta=accounting_delta,
        tolerance_abs=tolerance_abs,
        failure_class=failure_class,
        end_of_window_policy=END_OF_WINDOW_POLICY,
        open_position_state=open_state,
        component_breakdown={
            "realized_net_pnl_from_trades": realized_net,
            "realized_gross_pnl": realized_gross,
            "entry_costs_total": entry_costs,
            "exit_costs_total": exit_costs,
            "fees_total": fees_total,
            "ledger_implied_equity_change": ledger_implied_equity_change,
            "gross_net_equity_change": gross_net_equity_change,
            "slippage_impact": float(backtest.slippage_impact),
            "spread_drag": spread_drag,
            "funding_drag": funding_drag,
            "accounting_delta": accounting_delta,
        },
    )


def accounting_reconciliation_to_dict(result: AccountingReconciliationResultV0) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "reconciled": result.reconciled,
        "initial_cash": result.initial_cash,
        "final_equity": result.final_equity,
        "equity_change": result.equity_change,
        "net_pnl_from_trades": result.realized_net_pnl_from_trades,
        "entry_costs_total": result.component_breakdown.get("entry_costs_total"),
        "exit_costs_total": result.component_breakdown.get("exit_costs_total"),
        "ledger_implied_equity_change": result.component_breakdown.get(
            "ledger_implied_equity_change"
        ),
        "realized_gross_pnl": result.realized_gross_pnl,
        "fee_drag": result.fees_total,
        "slippage_impact": result.slippage_impact,
        "spread_drag": result.spread_drag,
        "funding_drag": result.funding_drag,
        "accounting_delta": result.accounting_delta,
        "tolerance_abs": result.tolerance_abs,
        "failure_class": result.failure_class,
        "end_of_window_policy": result.end_of_window_policy,
        "open_position_at_window_end": result.open_position_state.had_open_position_at_window_end,
        "open_position_instrument_id": result.open_position_state.instrument_id,
        "open_position_side": result.open_position_state.side,
        "component_breakdown": dict(result.component_breakdown),
    }
