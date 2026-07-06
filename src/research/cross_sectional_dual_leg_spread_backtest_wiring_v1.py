"""Dual-leg spread panel backtest wiring for cross-sectional funding-rate dual-leg spread v1.

Simultaneous long-low / short-high dollar-neutral book with bound conservative costs.
Research-only; no runtime, order, or authority effect.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import pandas as pd

from src.backtest.stats import compute_backtest_stats
from src.research.cross_sectional_funding_rate_dual_leg_spread_research_orchestrator_v1 import (
    DualLegOrchestratorRunResultV1,
)
from src.research.cross_sectional_trade_record_schema_v0 import (
    CANONICAL_PNL_FIELD,
    PNL_UNIT,
    compute_roundtrip_net_pnl_v0,
    normalize_trades_for_stats_v0,
)
from src.research.cross_sectional_funding_rate_dual_leg_spread_v1_versioned_research_binding_v0 import (
    EFFECTIVE_ENTRY_COST_BPS,
    EFFECTIVE_EXIT_COST_BPS,
    ROUNDTRIP_COST_BPS,
)
from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import InstrumentPanelSeriesV1

PACKAGE_MARKER = "CROSS_SECTIONAL_DUAL_LEG_SPREAD_BACKTEST_WIRING_V1=true"
WIRING_VERSION = "cross_sectional_dual_leg_spread_backtest_wiring.v1"


@dataclass(frozen=True)
class DualLegSpreadBacktestResultV1:
    wiring_version: str
    initial_cash: float
    final_equity: float
    gross_return: float
    net_return: float
    trade_count: int
    turnover: float
    fee_drag: float
    slippage_impact: float
    roundtrip_cost_bps: float
    equity_curve: pd.Series
    trades: pd.DataFrame
    stats: dict[str, float]
    authority_effect: str
    long_contribution: float | None = None
    short_contribution: float | None = None


def _close_price_at_epoch(
    panel_series: Sequence[InstrumentPanelSeriesV1],
    instrument_id: str,
    epoch_index: int,
) -> float | None:
    for series in panel_series:
        if series.instrument_id != instrument_id:
            continue
        if epoch_index < 0 or epoch_index >= len(series.bars):
            return None
        try:
            return float(series.bars[epoch_index].close)
        except (TypeError, ValueError):
            return None
    return None


def _cost_fraction(bps: float) -> float:
    return bps / 10_000.0


def _close_leg(
    *,
    side: str,
    instrument_id: str,
    entry_price: float,
    entry_ts: str,
    equity_at_entry: float,
    exit_price: float,
    exit_ts: str,
    equity: float,
    exit_bps: float,
    fee_bps: float,
    entry_bps: float,
    slip_bps: float,
    trades: list[dict[str, Any]],
    total_fee_drag: list[float],
    total_slippage: list[float],
) -> float:
    direction = 1.0 if side == "LONG" else "SHORT"
    gross_pnl_frac = direction * ((exit_price / entry_price) - 1.0)
    equity_before_exit = equity
    exit_cost = equity_before_exit * _cost_fraction(exit_bps)
    gross_pnl_abs, net_pnl = compute_roundtrip_net_pnl_v0(
        equity_at_entry=equity_at_entry,
        equity_before_exit=equity_before_exit,
        gross_pnl_frac=gross_pnl_frac,
        exit_cost=exit_cost,
    )
    new_equity = equity_before_exit * (1.0 + gross_pnl_frac) - exit_cost
    total_fee_drag[0] += exit_cost * (fee_bps / entry_bps if entry_bps else 0.5)
    total_slippage[0] += exit_cost * (slip_bps / entry_bps if entry_bps else 0.5)
    trades.append(
        {
            "entry_time": entry_ts,
            "exit_time": exit_ts,
            "instrument_id": instrument_id,
            "side": side,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "gross_pnl_frac": gross_pnl_frac,
            "gross_pnl": gross_pnl_abs,
            "entry_cost": 0.0,
            "exit_cost": exit_cost,
            CANONICAL_PNL_FIELD: net_pnl,
            "pnl_unit": PNL_UNIT,
        }
    )
    return new_equity


def run_dual_leg_spread_panel_backtest_v1(
    orchestrator_result: DualLegOrchestratorRunResultV1,
    panel_series: Sequence[InstrumentPanelSeriesV1],
    *,
    cost_execution_binding: Mapping[str, Any],
    initial_cash: float = 10_000.0,
) -> DualLegSpreadBacktestResultV1:
    """Simulate simultaneous dual-leg spread backtest with bound conservative costs."""
    fee_binding = cost_execution_binding.get("fee_model_binding", {})
    slip_binding = cost_execution_binding.get("slippage_model_binding", {})
    exec_binding = cost_execution_binding.get("execution_model_binding", {})

    fee_bps = float(fee_binding.get("fee_bps_per_side", 0.0))
    slip_bps = float(slip_binding.get("slippage_bps_per_side", 0.0))
    entry_bps = float(exec_binding.get("effective_entry_cost_bps", EFFECTIVE_ENTRY_COST_BPS))
    exit_bps = float(exec_binding.get("effective_exit_cost_bps", EFFECTIVE_EXIT_COST_BPS))
    roundtrip_bps = float(exec_binding.get("roundtrip_cost_bps", ROUNDTRIP_COST_BPS))

    if fee_bps <= 0 or slip_bps <= 0 or entry_bps <= 0 or exit_bps <= 0:
        raise ValueError("implicit_zero_cost_forbidden")

    equity = initial_cash
    equity_points: list[tuple[str, float]] = []
    trades: list[dict[str, Any]] = []
    total_fee_drag = [0.0]
    total_slippage = [0.0]
    rebalance_count = 0

    prev_active = False
    prev_long: str | None = None
    prev_short: str | None = None
    long_entry_price: float | None = None
    short_entry_price: float | None = None
    long_entry_ts: str | None = None
    short_entry_ts: str | None = None
    long_equity_at_entry: float | None = None
    short_equity_at_entry: float | None = None
    leg_allocation = initial_cash / 2.0

    long_pnl_total = 0.0
    short_pnl_total = 0.0

    for epoch in orchestrator_result.epochs:
        ts = epoch.timestamp_utc
        sel = epoch.selection
        active = sel.active
        long_id = sel.long_instrument_id
        short_id = sel.short_instrument_id

        legs_changed = prev_active and (
            not active or long_id != prev_long or short_id != prev_short
        )
        if legs_changed:
            if prev_long and long_entry_price is not None and long_equity_at_entry is not None:
                exit_px = _close_price_at_epoch(panel_series, prev_long, epoch.epoch_index)
                if exit_px is not None:
                    before = equity
                    equity = _close_leg(
                        side="LONG",
                        instrument_id=prev_long,
                        entry_price=long_entry_price,
                        entry_ts=long_entry_ts or ts,
                        equity_at_entry=long_equity_at_entry,
                        exit_price=exit_px,
                        exit_ts=ts,
                        equity=equity,
                        exit_bps=exit_bps,
                        fee_bps=fee_bps,
                        entry_bps=entry_bps,
                        slip_bps=slip_bps,
                        trades=trades,
                        total_fee_drag=total_fee_drag,
                        total_slippage=total_slippage,
                    )
                    long_pnl_total += equity - before
            if prev_short and short_entry_price is not None and short_equity_at_entry is not None:
                exit_px = _close_price_at_epoch(panel_series, prev_short, epoch.epoch_index)
                if exit_px is not None:
                    before = equity
                    equity = _close_leg(
                        side="SHORT",
                        instrument_id=prev_short,
                        entry_price=short_entry_price,
                        entry_ts=short_entry_ts or ts,
                        equity_at_entry=short_equity_at_entry,
                        exit_price=exit_px,
                        exit_ts=ts,
                        equity=equity,
                        exit_bps=exit_bps,
                        fee_bps=fee_bps,
                        entry_bps=entry_bps,
                        slip_bps=slip_bps,
                        trades=trades,
                        total_fee_drag=total_fee_drag,
                        total_slippage=total_slippage,
                    )
                    short_pnl_total += equity - before
            long_entry_price = None
            short_entry_price = None
            long_entry_ts = None
            short_entry_ts = None
            long_equity_at_entry = None
            short_equity_at_entry = None
            rebalance_count += 1

        if active and long_id and short_id:
            opening = not prev_active or long_id != prev_long or short_id != prev_short
            if opening:
                long_px = _close_price_at_epoch(panel_series, long_id, epoch.epoch_index)
                short_px = _close_price_at_epoch(panel_series, short_id, epoch.epoch_index)
                if long_px is not None:
                    entry_cost = leg_allocation * _cost_fraction(entry_bps)
                    equity -= entry_cost
                    total_fee_drag[0] += entry_cost * (fee_bps / entry_bps if entry_bps else 0.5)
                    total_slippage[0] += entry_cost * (slip_bps / entry_bps if entry_bps else 0.5)
                    long_entry_price = long_px
                    long_entry_ts = ts
                    long_equity_at_entry = leg_allocation
                if short_px is not None:
                    entry_cost = leg_allocation * _cost_fraction(entry_bps)
                    equity -= entry_cost
                    total_fee_drag[0] += entry_cost * (fee_bps / entry_bps if entry_bps else 0.5)
                    total_slippage[0] += entry_cost * (slip_bps / entry_bps if entry_bps else 0.5)
                    short_entry_price = short_px
                    short_entry_ts = ts
                    short_equity_at_entry = leg_allocation

        prev_active = active
        prev_long = long_id if active else None
        prev_short = short_id if active else None
        equity_points.append((ts, equity))

    if not equity_points:
        equity_curve = pd.Series([initial_cash], index=pd.DatetimeIndex(["1970-01-01T00:00:00Z"]))
    else:
        index = pd.to_datetime([item[0] for item in equity_points], utc=True)
        equity_curve = pd.Series([item[1] for item in equity_points], index=index)

    trades_df = pd.DataFrame(trades)
    trade_records = (
        normalize_trades_for_stats_v0(trades_df.to_dict(orient="records"))
        if not trades_df.empty
        else []
    )
    stats = compute_backtest_stats(
        trades=trade_records,
        equity_curve=equity_curve,
    )
    gross_return = float(stats.get("total_return", 0.0))
    net_return = (equity / initial_cash) - 1.0 if initial_cash else 0.0

    total_abs = abs(long_pnl_total) + abs(short_pnl_total)
    long_contrib = (long_pnl_total / total_abs) if total_abs > 0 else None
    short_contrib = (short_pnl_total / total_abs) if total_abs > 0 else None

    return DualLegSpreadBacktestResultV1(
        wiring_version=WIRING_VERSION,
        initial_cash=initial_cash,
        final_equity=equity,
        gross_return=gross_return,
        net_return=net_return,
        trade_count=len(trades),
        turnover=float(rebalance_count),
        fee_drag=total_fee_drag[0],
        slippage_impact=total_slippage[0],
        roundtrip_cost_bps=roundtrip_bps,
        equity_curve=equity_curve,
        trades=trades_df,
        stats=stats,
        authority_effect="NONE",
        long_contribution=long_contrib,
        short_contribution=short_contrib,
    )
