# Robustness summary — post-#5348 economic reevaluation

## Integrity override (fail-closed)

Prior baseline exports are **INVALID_ECONOMIC_MEASUREMENT**. Configured
`fee_bps=10` / `slippage_bps=5` are **NOT_APPLIED** in the roundtrip ledger
(`entry_cost=exit_cost=fee_drag=0`, `pnl==gross_pnl`, `COST_DRAG=0`). Prior panel
`NET_RETURN≈0.507` summed 118 independent instrument returns (capital
double-counting). Corrected equal-capital proxy: `sum(net_pnl)&#47;(118*10000)`.

See `metrics_integrity_verdict.md`, `cost_reconciliation.json`,
`portfolio_aggregation_audit.md`.

## Scope

- Config: `bollinger_bands_v2_full_canonical_system_economic_binding_v1`
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1` (118 instruments)
- Period: `2024-05-01T00:00:00Z..2024-09-01T00:00:00Z` (max local PIT coverage; **no longer chronological panel**)
- Seed: `42`
- Chain: `run_mv2_research_backtest_wiring_v1` → integrated offline replay → `transition_state`

## Dataset blocker

`NO_LONGER_CHRONOLOGICAL_PIT_OKX_LINEAR_USDT_NON_BTC_DATASET_THAN_2024-05-01..2024-09-01; max local coverage equals prior sample period; cross-sectional expansion to full 118-member panel used instead`

## Corrected baseline (measurement-invalid; forensic)

| Metric | Value |
|--------|------:|
| Total trades | 464 |
| LONG | 69 |
| SHORT | 395 |
| Traded instruments | 115 |
| Gross PnL | 5066.899689424941 |
| Fees | 0.0 |
| Slippage | 0.0 |
| Net PnL | 5066.899689424941 |
| Cost drag | 0.0 |
| Cost application | NOT_APPLIED |
| Net return (corrected equal-capital proxy) | 0.004293982787648256 |
| Net return (prior INVALID sum of instrument returns) | 0.5066899689424893 |
| Profit factor (pooled trade gross) | 1.22955031589784 |
| Sharpe | NOT_AVAILABLE |
| Sharpe (prior INVALID cross-section) | 0.040885256927793066 |
| Max drawdown | NOT_AVAILABLE |
| Max DD (prior worst instrument) | -0.0770688760257639 |
| Win rate | 0.051520834322429536 |
| Avg hold (h) | 247.42446941095278 |
| Stop triggers | 447 |
| Economic class | INVALID_ECONOMIC_MEASUREMENT |
| Economic measurement valid | false |

## Walk-forward / stress / LOO

Prior walk-forward / stress / LOO artifacts remain on disk for forensic
comparison only. They inherit the same cost-application and aggregation defects
and must **not** be treated as valid economic robustness evidence.

## Safety

`ECONOMIC_GATE_OPENED=false`, `PROMOTION_ELIGIBLE=false`.
