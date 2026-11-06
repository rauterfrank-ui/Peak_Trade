# P26 — Execution Integration v1

## Objective
Integrate deterministic execution (P23/P24) into the backtest loop end-to-end:
Orders → Fills → Accounting (cash/positions/fees) → PnL snapshots.

## Design
### Adapter
- `ExecutionAdapterV1` bridges existing backtest order objects to P24 `ExecutionModelV2`.
- Input per bar: `MarketSnapshot` (OHLCV) + list of open orders + config.
- Output: list of `Fill` records (deterministic ordering).

### Invariants
- Determinism: stable ordering of fills; stable rounding; no RNG.
- Fill bounds: `0 <= filled_qty_total <= order.qty`.
- Fee application: per fill; never double-counted.
- PnL accounting: realized/unrealized consistent with fills and mark price.

## Evidence
- Contract tests for determinism and accounting.
