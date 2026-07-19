# Metrics definitions — post-#5348 integrity audit

## Scope

Audit of exported panel metrics from
`docs/evidence/canonical_economic_reevaluation_post_5348_v1` against the
canonical offline roundtrip ledger produced by
`run_mv2_research_backtest_wiring_v1` (seed 42).

## Per-metric contract

| Metric | Formula | Unit | Aggregation | Denominator | Annualization | Parallel instruments | Open positions | Ledger source |
|--------|---------|------|-------------|-------------|---------------|----------------------|----------------|---------------|
| gross_pnl | Σ trade.gross_pnl | currency | panel sum of trades | n/a | none | sum across independent instrument runs | closed roundtrips only in trades table | trade.gross_pnl |
| fees | Σ (entry_cost+exit_cost) else Σ fee | currency | panel sum | n/a | none | sum | closed only | entry_cost/exit_cost/fee |
| slippage | separable slippage fields (none observed) | currency | panel sum | n/a | none | sum | closed only | **not present** / 0 |
| net_pnl | Σ trade.pnl | currency | panel sum | n/a | none | sum | closed only | trade.pnl |
| cost_drag | gross_pnl − net_pnl | currency | panel | n/a | none | derived | closed only | identity |
| equity | per-instrument equity_curve | currency | **no portfolio curve** | initial 10000/instrument | n/a | independent | MTM while open | BacktestResult.equity_curve |
| net_return (prior export) | Σ instrument total_return | return | **INVALID sum** | each instrument 10000 | none | **double-counts capital** | uses closed stats total_return | stats/metrics total_return |
| net_return (corrected) | Σ net_pnl / (N × 10000) | return | equal-capital panel proxy | N×10000 | none | equal capital assumed | closed pnl only | derived |
| profit_factor | Σ gross_wins / \|Σ gross_losses\| | ratio | trade gross legs | n/a | none | pooled trades | closed only | trade.gross_pnl |
| sharpe (prior export) | mean(r_i)/std(r_i) over instruments | ratio | cross-section | instrument returns | **none / not TS** | cross-section | n/a | instrument net_return |
| sharpe (corrected) | NOT_AVAILABLE | n/a | requires portfolio equity TS | n/a | n/a | n/a | n/a | none |
| max_drawdown (prior) | min_i DD_i | return | worst instrument | per-instrument equity | none | not portfolio DD | per curve | metrics max_drawdown |

## Configured costs

- `fee_bps=10.0`, `slippage_bps=5.0`, `stop_pct=0.025`
- Bound break-even roundtrip = 30 bps when costs are applied
- Observed ledger: fees=0, slippage=0, cost_drag=0, fill at bar close

## Validity

`ECONOMIC_MEASUREMENT_VALID=false` because costs are **NOT_APPLIED** in the
roundtrip ledger and the prior panel return/Sharpe aggregation is invalid.
