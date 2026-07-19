# Portfolio aggregation audit — measurement repair

## Model

`RESEARCH_EQUAL_WEIGHT_NORMALIZED_SLEEVE_COMBINE_V1` (research measurement only;
not runtime / sizing / risk authority).

## Shared capital

| Field | Value |
|---|---:|
| initial_capital (shared) | 10000 |
| sleeve_initial_cash | 10000 |
| instruments N | 118 |
| CRS scale | 1/118 |
| capital_double_counting | false |

## Construction

1. Run each instrument sleeve independently (canonical MV2 wiring, seed 42).
2. Normalize each sleeve equity to 1.0 at t0.
3. Equal-weight combine → multiply by shared `initial_capital`.
4. `NET_RETURN = final_equity &#47; initial_capital - 1`.
5. Sharpe / MaxDD from the shared hourly portfolio equity only.
6. PnL/fee/slippage/exposure reports apply CRS scale so shared capital is counted once.

## Prior invalid aggregation (superseded)

- Sum of independent instrument `total_return`s (`≈0.507`) — INVALID.
- Cross-sectional Sharpe `mean(r_i)&#47;std(r_i)` — INVALID.
- Equal-capital proxy alone without portfolio equity path — SUPERSEDED.

## Current reconciliation

| Check | Result |
|---|---|
| equity_reconciliation | PASS |
| final_equity vs initial + scaled net_pnl | aligned under CRS |
| peak_gross_exposure | scaled concurrent notionals |
