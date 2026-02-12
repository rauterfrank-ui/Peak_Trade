"""P32 — Backtest report v1 composition primitive."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from src.backtest.p29.accounting_v2 import PositionCashStateV2, apply_fills_v2
from src.backtest.p30.equity_curve_v1 import equity_curve_v1
from src.backtest.p31.metrics_v1 import summary_kpis
from src.execution.p26.adapter import ExecutionAdapterV1, FillRecord
from src.execution.p24.execution_model_v2 import MarketSnapshot


def _to_snapshot(bar: Any, bar_ts: str) -> MarketSnapshot:
    """Convert bar-like object to P24 MarketSnapshot."""
    return MarketSnapshot(
        ts=bar_ts,
        open=float(getattr(bar, "open", 0.0)),
        high=float(getattr(bar, "high", 0.0)),
        low=float(getattr(bar, "low", 0.0)),
        close=float(getattr(bar, "close", 0.0)),
        volume=float(getattr(bar, "volume", 0.0)),
    )


@dataclass(frozen=True)
class BacktestReportV1:
    fills: list[FillRecord]
    state: PositionCashStateV2
    equity: list[float]
    metrics: dict[str, float | int]


def run_backtest_report_v1(
    *,
    bars: Sequence[Any],
    orders_by_bar: Sequence[Sequence[Any]],
    adapter: ExecutionAdapterV1,
    initial_state: PositionCashStateV2,
    initial_equity: float,
    symbol: str,
) -> BacktestReportV1:
    """Run a deterministic backtest slice and return report (fills, state, equity, metrics)."""
    if len(orders_by_bar) != len(bars):
        raise ValueError("orders_by_bar must have same length as bars")

    fills_all: list[FillRecord] = []
    fills_by_idx: list[list[FillRecord]] = []
    state = initial_state

    for i, (bar, orders) in enumerate(zip(bars, orders_by_bar)):
        snapshot = _to_snapshot(bar, bar_ts=f"bar_{i}")
        fills = list(adapter.execute_bar(snapshot=snapshot, orders=list(orders)))
        fills_by_idx.append(fills)
        if fills:
            state = apply_fills_v2(state=state, fills=fills)
            fills_all.extend(fills)

    prices = [float(getattr(b, "close", getattr(b, "price", 0.0))) for b in bars]
    rows = equity_curve_v1(
        prices=prices,
        fills_by_idx=fills_by_idx,
        initial_cash=float(initial_equity),
        symbol=symbol,
    )
    equity_points = [float(initial_equity)] + [float(r.equity) for r in rows]

    metrics = summary_kpis(equity_points)
    metrics_int = {k: int(v) if k == "n_steps" else v for k, v in metrics.items()}

    return BacktestReportV1(
        fills=fills_all,
        state=state,
        equity=equity_points,
        metrics=metrics_int,
    )
