"""Single-slot panel backtest wiring for cross-sectional relative-strength v0.

Narrow adapter from orchestrator selection events to canonical backtest stats.
No duplicate strategy logic, cost model, or metrics stack.
Research-only; no runtime, order, or authority effect.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import pandas as pd

from src.backtest.stats import compute_backtest_stats
from src.research.cross_sectional_trade_record_schema_v0 import (
    CANONICAL_PNL_FIELD,
    PNL_UNIT,
    compute_roundtrip_net_pnl_v0,
    normalize_trades_for_stats_v0,
)
from src.research.cross_sectional_relative_strength_v0_versioned_research_binding_v0 import (
    EFFECTIVE_ENTRY_COST_BPS,
    EFFECTIVE_EXIT_COST_BPS,
    ROUNDTRIP_COST_BPS,
)
from src.research.cross_sectional_single_slot_research_orchestrator_v0 import (
    OrchestratorRunResultV0,
    SlotSide,
)
from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import InstrumentPanelSeriesV1

PACKAGE_MARKER = "CROSS_SECTIONAL_SINGLE_SLOT_BACKTEST_WIRING_V0=true"
WIRING_VERSION = "cross_sectional_single_slot_backtest_wiring.v0"
MAX_POSITIONS = 1


@dataclass(frozen=True)
class SingleSlotBacktestResultV0:
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


def run_single_slot_panel_backtest_v0(
    orchestrator_result: OrchestratorRunResultV0,
    panel_series: Sequence[InstrumentPanelSeriesV1],
    *,
    cost_execution_binding: Mapping[str, Any],
    initial_cash: float = 10_000.0,
) -> SingleSlotBacktestResultV0:
    """Simulate single-slot rotation backtest with bound conservative costs."""
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
    prev_side = SlotSide.FLAT
    prev_instrument: str | None = None
    entry_price: float | None = None
    entry_ts: str | None = None
    equity_at_entry: float | None = None
    entry_cost_recorded = 0.0
    total_fee_drag = 0.0
    total_slippage = 0.0
    rotation_count = 0

    for epoch in orchestrator_result.epochs:
        ts = epoch.timestamp_utc
        side = epoch.selection.slot_side
        instrument = epoch.selection.selected_instrument_id

        if prev_side != SlotSide.FLAT and (side != prev_side or instrument != prev_instrument):
            exit_price = _close_price_at_epoch(
                panel_series, prev_instrument or "", epoch.epoch_index
            )
            if exit_price is not None and entry_price is not None and prev_side != SlotSide.FLAT:
                if equity_at_entry is None:
                    raise ValueError("trade_close_without_equity_at_entry")
                direction = 1.0 if prev_side == SlotSide.LONG else -1.0
                gross_pnl_frac = direction * ((exit_price / entry_price) - 1.0)
                equity_before_exit = equity
                exit_cost = equity_before_exit * _cost_fraction(exit_bps)
                gross_pnl_abs, net_pnl = compute_roundtrip_net_pnl_v0(
                    equity_at_entry=equity_at_entry,
                    equity_before_exit=equity_before_exit,
                    gross_pnl_frac=gross_pnl_frac,
                    exit_cost=exit_cost,
                )
                equity = equity_before_exit * (1.0 + gross_pnl_frac) - exit_cost
                total_fee_drag += exit_cost * (fee_bps / entry_bps if entry_bps else 0.5)
                total_slippage += exit_cost * (slip_bps / entry_bps if entry_bps else 0.5)
                trades.append(
                    {
                        "entry_time": entry_ts,
                        "exit_time": ts,
                        "instrument_id": prev_instrument,
                        "side": prev_side.value,
                        "entry_price": entry_price,
                        "exit_price": exit_price,
                        "gross_pnl_frac": gross_pnl_frac,
                        "gross_pnl": gross_pnl_abs,
                        "entry_cost": entry_cost_recorded,
                        "exit_cost": exit_cost,
                        CANONICAL_PNL_FIELD: net_pnl,
                        "pnl_unit": PNL_UNIT,
                    }
                )
            entry_price = None
            entry_ts = None
            equity_at_entry = None
            entry_cost_recorded = 0.0
            rotation_count += 1

        if side != SlotSide.FLAT and instrument is not None:
            if prev_side == SlotSide.FLAT or instrument != prev_instrument or side != prev_side:
                px = _close_price_at_epoch(panel_series, instrument, epoch.epoch_index)
                if px is not None:
                    entry_cost = equity * _cost_fraction(entry_bps)
                    equity -= entry_cost
                    total_fee_drag += entry_cost * (fee_bps / entry_bps if entry_bps else 0.5)
                    total_slippage += entry_cost * (slip_bps / entry_bps if entry_bps else 0.5)
                    entry_price = px
                    entry_ts = ts
                    equity_at_entry = equity
                    entry_cost_recorded = entry_cost

        prev_side = side
        prev_instrument = instrument
        equity_points.append((ts, equity))

    if not equity_points:
        equity_curve = pd.Series([initial_cash], index=pd.DatetimeIndex(["1970-01-01T00:00:00Z"]))
    else:
        index = pd.to_datetime([ts for ts, _ in equity_points], utc=True)
        equity_curve = pd.Series([val for _, val in equity_points], index=index)

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

    return SingleSlotBacktestResultV0(
        wiring_version=WIRING_VERSION,
        initial_cash=initial_cash,
        final_equity=equity,
        gross_return=gross_return,
        net_return=net_return,
        trade_count=len(trades),
        turnover=float(rotation_count),
        fee_drag=total_fee_drag,
        slippage_impact=total_slippage,
        roundtrip_cost_bps=roundtrip_bps,
        equity_curve=equity_curve,
        trades=trades_df,
        stats=stats,
        authority_effect="NONE",
    )
