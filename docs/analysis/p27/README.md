# P27 — Execution Integration v2 (Backtest loop wiring)

## Goal
Wire the existing backtest loop to route orders through:
Backtest → P26 ExecutionAdapterV1 → P24 ExecutionModelV2 → FillRecord
then apply fills to portfolio state (cash/positions), deterministically.

## Feature flag
- backtest.execution_mode = "p26_v1" (new)
- default remains existing execution path

## Determinism
Given identical:
- MarketSnapshot (bar OHLCV)
- order set for the bar
- Execution config (fees/slippage/stops)
the adapter must emit identical FillRecords and portfolio updates.

## Invariants
- 0 <= filled_qty <= order_qty
- fee/slippage applied per config
- no IO, no live trading
