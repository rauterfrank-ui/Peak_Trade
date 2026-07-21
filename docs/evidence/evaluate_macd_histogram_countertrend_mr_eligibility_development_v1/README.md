# Evaluate MACD histogram-countertrend MR eligibility — DEVELOPMENT v1

```text
SLICE=EVALUATE_MACD_HISTOGRAM_COUNTERTREND_MR_ELIGIBILITY_DEVELOPMENT_V1
BASE_SHA=b05a10bca2d6c01f4378d55cf09edc8fb3aebc23
BRANCH=research/evaluate-macd-histogram-countertrend-mr-development-v1
CLASS=DEVELOPMENT_EVALUATION_EVIDENCE_ONLY
HYPOTHESIS=MACD_HISTOGRAM_COUNTERTREND_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1
DATASET=pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1
DATASET_CLASS=DEVELOPMENT_ONLY
CONFIG_ID=bollinger_bands_v2_full_canonical_system_economic_binding_v1
SEED=20220601
EVALUATION_RUN_COUNT=1
BACKTEST_EXECUTED=true
HOLDOUT_ACCESSED=false
SEALED_HOLDOUT_CONTENT_INSPECTED=false
ENTRY_ELIGIBILITY_DIVERGENCE=true
entries_blocked_by_gate=190
RESULT_CLASS=FAIL
PROMOTION_ELIGIBLE=false
RUNTIME=false
ORDERS=false
```

## Verdict

Preregistered DEVELOPMENT evaluation on the sealed independent panel
`final_development_confirmation` segment only.

**RESULT_CLASS=FAIL** — reason `NET_PROFIT_FACTOR_NOT_IMPROVED`. Entry-eligibility
divergence was observed (`ENTRY_ELIGIBILITY_DIVERGENCE=true`;
`entries_blocked_by_gate=190` across
39/46 instruments), but treatment failed the
locked economic criteria (profit factor not improved versus control). Net return and max
drawdown also failed their locked companion checks.

The side-aware eligibility gate (long admitted iff `histogram < 0`; short
admitted iff `histogram > 0`) is applied **post-map** on Master-V2 position
signals (research-local mask only); no productive trading-logic / authority
mutation.

## Key metrics (shared book, decision segment)

| Field | Baseline (control) | Treatment |
|---|---:|---:|
| Trade count | 100 | 110 |
| Long trades | 8 | 0 |
| Short trades | 92 | 110 |
| Gross PnL | 4667.374063181995 | 2068.4092736260345 |
| Net PnL (closed-trade sum) | 4081.853505175829 | 1422.8246679235895 |
| Fees | 390.3470386707774 | 430.38973713496273 |
| Slippage | 195.1735193353887 | 215.19486856748136 |
| Cost drag | 585.520558006166 | 645.5846057024442 |
| Net return (shared equity) | 0.008488326414724634 | 0.0028492927563554815 |
| Sharpe | 0.8814775984519235 | 0.4082855178008727 |
| Max drawdown | -0.011202514661665192 | -0.011614985468678424 |
| Profit factor | 1.8902386362662627 | 1.2720119459279058 |
| Win rate | 0.17 | 0.13636363636363635 |
| Turnover | 100.0 | 110.0 |
| Entries blocked by gate | 0 | 190 |

## Acceptance (locked contract)

- `entry_eligibility_divergence_observed` → **True**
- `trade_count_treatment_ge_minimum` (≥50) → True
- `trade_count_treatment_ge_control_floor` → True
- `profit_factor_treatment_gt_control` → **False**
- `net_return_treatment_gt_control` → **False**
- `max_drawdown_treatment_ge_control` → **False**
- `cost_drag_fully_included` → True

Joint PASS requires ALL checks True; `profit_factor_treatment_gt_control=False`
alone forces `RESULT_CLASS=FAIL` (reason `NET_PROFIT_FACTOR_NOT_IMPROVED`).

## Command

```bash
PYTHONPATH=src:. python3 scripts/research/run_evaluate_macd_histogram_countertrend_mr_eligibility_development_v1.py \
  --output-dir docs/evidence/evaluate_macd_histogram_countertrend_mr_eligibility_development_v1
```

## Safety

- Holdout not accessed / not inspected
- No productive trading-logic / authority / risk / sizing / execution mutation
- Gate applied as research-only post-map, side-aware signal override over the
  unchanged bollinger/MV2 chain
- `PROMOTION_ELIGIBLE=false`, economic offline gate unchanged/closed
- No runtime / shadow / testnet / live / orders
- Exactly one DEVELOPMENT evaluation run (baseline + treatment arms in this single
  run); no second run; no retuning
