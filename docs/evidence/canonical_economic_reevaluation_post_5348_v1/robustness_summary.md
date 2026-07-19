# Robustness summary — post-#5348 (measurement repaired)

## Measurement

- Cost application: `APPLIED` (fee_bps=10, slippage_bps=5 cash drag)
- Portfolio aggregation: `RESEARCH_EQUAL_WEIGHT_NORMALIZED_SLEEVE_COMBINE_V1`
- Shared initial capital: `10000`
- Ledger / equity reconciliation: `PASS` / `PASS`
- Economic measurement valid: `true`
- Economic class: `INCONCLUSIVE_UNSTABLE` (WF/stress; period blocker)

## Scope

- Config: `bollinger_bands_v2_full_canonical_system_economic_binding_v1`
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1` (118)
- Period: `2024-05-01T00:00:00Z..2024-09-01T00:00:00Z`
- Seed: `42`

## Baseline (shared book)

| Metric | Value |
|--------|------:|
| Total trades | 454 |
| LONG / SHORT | 69 / 385 |
| Gross PnL | 46.13329289862826 |
| Fees | 15.25295478732169 |
| Slippage | 7.626477393660845 |
| Net PnL | 23.253860717645743 |
| Cost drag | 22.87943218098253 |
| Final equity | 10023.253860717647 |
| Gross return | 0.004613329289862827 |
| Net return | 0.00232538607176469 |
| Profit factor (net) | 1.1135430312470467 |
| Sharpe | 0.1909766065222959 |
| Max drawdown | -0.020480218347394656 |
| Peak gross exposure | 1466.1642226234028 |

Trade count differs from the prior invalid zero-cost run (464) because applied
costs alter sleeve equity and subsequent sizing path-dependently.

## Walk-forward / stress

Remain `INCONCLUSIVE` (sign instability / modelled stress). Not promotion inputs.

## Safety

`ECONOMIC_GATE_OPENED=false`, `PROMOTION_ELIGIBLE=false`.
