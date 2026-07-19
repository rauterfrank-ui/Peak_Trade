# Robustness summary — post-#5348 economic reevaluation

## Scope

- Config: `bollinger_bands_v2_full_canonical_system_economic_binding_v1`
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1` (118 instruments)
- Period: `2024-05-01T00:00:00Z..2024-09-01T00:00:00Z` (max local PIT coverage; **no longer chronological panel**)
- Seed: `42`
- Chain: `run_mv2_research_backtest_wiring_v1` → integrated offline replay → `transition_state`

## Dataset blocker

`NO_LONGER_CHRONOLOGICAL_PIT_OKX_LINEAR_USDT_NON_BTC_DATASET_THAN_2024-05-01..2024-09-01; max local coverage equals prior sample period; cross-sectional expansion to full 118-member panel used instead`

Cross-sectional expansion: prior post-#5346 sample used 4 instruments; this run uses
the full binding panel (118).

## Baseline

| Metric | Value |
|--------|------:|
| Total trades | 464 |
| LONG | 69 |
| SHORT | 395 |
| Traded instruments | 115 |
| Gross PnL | 5066.899689424928 |
| Net PnL | 5066.899689424928 |
| Net return | 0.5066899689424893 |
| Fees | 0.0 |
| Slippage drag | 4640.0 |
| Cost drag | 0.0 |
| Profit factor | 1.2782631983779025 |
| Sharpe | 0.040885256927793066 |
| Max drawdown | -0.0770688760257639 |
| Win rate | 0.051520834322429536 |
| Avg hold (h) | 247.42446941095278 |
| Stop triggers | 447 |

## Walk-forward

Verdict: **INCONCLUSIVE**

Folds use the existing runtime training/validation/OOS calendar windows.

## Stress

Verdict: **INCONCLUSIVE**

Modelled fee/slip roundtrip-bps drag on the baseline panel net return (sealed cost
binding does not honor cfg fee/slip overrides). Live stop-pct re-runs are
`NOT_AVAILABLE` (`sizing_config_digest_mismatch`).

## Leave-one-out

LOO rows: 115 (one per traded instrument). Used diagnostically for
cross-sectional concentration; not a promotion input.

## Classification

- ECONOMIC_CLASS=`INCONCLUSIVE_UNSTABLE`
- STATUS=`PARTIAL`
- RATIONALE=`unstable_splits_or_stress;NO_LONGER_CHRONOLOGICAL_PIT_OKX_LINEAR_USDT_NON_BTC_DATASET_THAN_2024-05-01..2024-09-01`
- ECONOMIC_GATE_OPENED=`false`
- PROMOTION_ELIGIBLE=`false`
- Reproducibility identical (`okx:linear_perpetual:1INCH:USDT:USDT:perp`): `True`
- entry_side_other_total=`0` (expect 0 / NONE)
