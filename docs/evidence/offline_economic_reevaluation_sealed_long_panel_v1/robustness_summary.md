# Robustness summary — post-#5348 economic reevaluation

## Scope

- Config: `bollinger_bands_v2_full_canonical_system_economic_binding_v1`
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_chrono_3y_v1` (65 instruments)
- Period: `2023-08-16T05:55:00Z..2024-09-01T00:00:00Z` (max local PIT coverage; **no longer chronological panel**)
- Seed: `42`
- Chain: `run_mv2_research_backtest_wiring_v1` → integrated offline replay → `transition_state`

## Dataset blocker

`None`

Cross-sectional expansion: prior post-#5346 sample used 4 instruments; this run uses
the full binding panel (65).

## Baseline

| Metric | Value |
|--------|------:|
| Total trades | 303 |
| LONG | 15 |
| SHORT | 288 |
| Traded instruments | 60 |
| Gross PnL | -228.94997421043914 |
| Net PnL | -256.73280650393065 |
| Net return | -0.02567328065039287 |
| Fees | 18.521888195661013 |
| Slippage drag | 9.260944097830507 |
| Cost drag | 27.782832293491524 |
| Profit factor | 0.0 |
| Sharpe | -9.27064192702636 |
| Max drawdown | -0.025673280650392916 |
| Win rate | 0.0 |
| Avg hold (h) | 171.52440638065636 |
| Stop triggers | 303 |

## Walk-forward

Verdict: **FAIL**

Folds use the existing runtime training/validation/OOS calendar windows.

## Stress

Verdict: **FAIL**

Modelled fee/slip roundtrip-bps drag on the baseline panel net return (sealed cost
binding does not honor cfg fee/slip overrides). Live stop-pct re-runs are
`NOT_AVAILABLE` (`sizing_config_digest_mismatch`).

## Leave-one-out

LOO rows: 60 (one per traded instrument). Used diagnostically for
cross-sectional concentration; not a promotion input.

## Classification

- ECONOMIC_CLASS=`FAIL_ECONOMIC`
- STATUS=`PASS`
- RATIONALE=`net_return=-0.02567328065039287;sealed_long_panel_bound`
- ECONOMIC_GATE_OPENED=`false`
- PROMOTION_ELIGIBLE=`false`
- Reproducibility identical (`okx:linear_perpetual:1INCH:USDT:USDT:perp`): `True`
- entry_side_other_total=`0` (expect 0 / NONE)
