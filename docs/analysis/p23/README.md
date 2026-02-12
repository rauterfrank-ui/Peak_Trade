# P23 — Backtest Execution Realism v1

This phase introduces a deterministic execution layer for backtests:
- explicit fills
- explicit fees + slippage
- explicit stop handling

Design goals:
- deterministic, config-driven
- testable edge cases
- no live trading enablement

## Architecture

### Interfaces (v1)

**Order** (from `src.execution.contracts`):
- `order_type`: market, limit, stop (stop_market)
- `side`: BUY, SELL
- `quantity`, `price` (for limit/stop), `time_in_force`

**Fill** (from `src.execution.contracts`):
- `price`, `quantity`, `fee`, `filled_at`
- `metadata` may include `slippage_bps`, `reason`

**ExecutionModelV1**:
- `apply(order, market_snapshot, ts) -> list[Fill]`
- Input: Order + OHLCV bar (open, high, low, close, volume) or mid price
- Output: 0 or more Fills (deterministic)

### Fill Rules (deterministic)

| Order Type   | Condition                         | Fill Price                         |
|--------------|-----------------------------------|------------------------------------|
| MARKET       | always                            | mid ± slippage (BUY: higher, SELL: lower) |
| LIMIT        | price crosses limit in bar        | at limit (or better) ± slippage     |
| STOP_MARKET  | price crosses stop in bar         | after trigger: market fill ± slippage |

### Config Schema (Pydantic)

```yaml
# config/execution/p23_execution.yaml
execution_model_p23:
  enabled: true
  fees:
    maker_bps: 5
    taker_bps: 10
  slippage:
    model: bps
    bps: 5
  stops:
    stop_market_enabled: true
```

Defaults: `maker_bps=5`, `taker_bps=10`, `slippage_bps=5`, `stop_market_enabled=true`.

### Integration Points

- `src&#47;backtest&#47;engine.py` — `_run_with_execution_pipeline` uses `PaperOrderExecutor` with `fee_bps` and `slippage_bps`
- `src&#47;execution&#47;venue_adapters&#47;fill_models.py` — existing `ImmediateFillModel`, `FixedFeeModel`, `FixedSlippageModel`
- P23 adds `ExecutionModelV1` in `src&#47;execution&#47;p23&#47;` as a configurable, deterministic layer that can be plugged into backtest execution

### Invariants

1. **Determinism**: Same (order, market_snapshot, config, seed) → same fills
2. **Fees**: Always applied to fill notional (qty × price)
3. **Slippage**: Applied in unfavorable direction
4. **Stops**: Stop triggers when bar crosses stop price; fill at next-available price (deterministic)

### Path References (encoded for docs gates)

- `out&#47;ops&#47;p23_*` — P23 ops output
- `tests&#47;p23&#47;` — P23 unit tests
- `src&#47;execution&#47;p23&#47;` — P23 execution module
