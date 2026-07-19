# Portfolio aggregation audit — post-#5348

## Method used in prior export

Each of the 118 instruments was backtested independently with
`initial_cash = 10000.0`.

Prior panel `NET_RETURN=0.5066899689424893` was
computed as the **sum of per-instrument `total_return` values**.

## Capital double-counting

`CAPITAL_DOUBLE_COUNTING=true`.

Summing independent returns implicitly treats each instrument's full initial
capital as additive portfolio capital without a shared equity curve:

- prior sum-of-returns: `0.5066899689424893`
- equal-capital panel proxy `sum(net_pnl)&#47;(N*10000)`: `0.004293982787648256`

These differ by ~0.502396.

## Equity reconciliation

`EQUITY_RECONCILIATION=FAIL` — there is **no** single portfolio equity series.
Therefore panel Sharpe / portfolio max-drawdown / portfolio net-return cannot be
sourced from one canonical equity ledger.

## Corrected aggregation (reporting only)

| Field | Value |
|------|------:|
| gross_pnl (sum trades) | 5066.899689424941 |
| net_pnl (sum trades) | 5066.899689424941 |
| equal-capital panel return | 0.004293982787648256 |
| profit_factor (trade gross) | 1.22955031589784 |
| sharpe corrected | NOT_AVAILABLE |
| portfolio equity | NOT_AVAILABLE |

## First-loss boundary

`NET_RETURN_SUM_OF_INSTRUMENT_RETURNS` in audit harness `_aggregate_rows`.
