# Evaluate MA trend-alignment MR eligibility — DEVELOPMENT v1

```text
SLICE=EVALUATE_MA_TREND_ALIGNMENT_MR_ELIGIBILITY_DEVELOPMENT_V1
BASE_SHA=a9982dfa76bd536841e8b8bed3dde991c1059cf2
BRANCH=research/evaluate-ma-trend-alignment-mr-entry-eligibility-development-v1
CLASS=DEVELOPMENT_EVALUATION_EVIDENCE_ONLY
HYPOTHESIS=MA_TREND_ALIGNMENT_MR_ENTRY_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1
DATASET=pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1
DATASET_CLASS=DEVELOPMENT_ONLY
CONFIG_ID=bollinger_bands_v2_full_canonical_system_economic_binding_v1
SEED=20220601
EVALUATION_RUN_COUNT=1
BACKTEST_EXECUTED=true
HOLDOUT_ACCESSED=false
SEALED_HOLDOUT_CONTENT_INSPECTED=false
ENTRY_ELIGIBILITY_DIVERGENCE=true
entries_blocked_by_gate=174
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
`entries_blocked_by_gate=174` across 34/46 instruments), but treatment failed the
locked economic criteria (profit factor not improved versus control), even though
net return and max drawdown both improved.

The side-aware eligibility gate (long admitted iff `close > SMA(50)`; short
admitted iff `close < SMA(50)`) is applied **post-map** on Master-V2 position
signals (research-local mask only); no productive trading-logic / authority
mutation.

## Key metrics (shared book, decision segment)

| Field | Baseline (control) | Treatment |
|---|---:|---:|
| Trade count | 138 | 121 |
| Long trades | 14 | 14 |
| Short trades | 124 | 107 |
| Gross PnL | 2194.88 | 1767.98 |
| Net PnL (closed-trade sum) | 1387.91 | 1055.64 |
| Fees | 537.98 | 474.90 |
| Slippage | 268.99 | 237.45 |
| Cost drag | 806.97 | 712.34 |
| Net return (shared equity) | 0.0020535965964010305 | 0.0022948591561742226 |
| Sharpe | 0.2530807283316113 | 0.32225051477281347 |
| Max drawdown | -0.015346201605060377 | -0.012639254998926298 |
| Profit factor | 1.210315325090541 | 1.181544162653302 |
| Win rate | 0.13043478260869565 | 0.12396694214876033 |
| Turnover | 138.0 | 121.0 |
| Entries blocked by gate | 0 | 174 |

## Acceptance (locked contract)

- `entry_eligibility_divergence_observed` → **True**
- `trade_count_treatment_ge_minimum` (≥50) → True
- `trade_count_treatment_ge_control_floor` → True
- `profit_factor_treatment_gt_control` → **False**
- `net_return_treatment_gt_control` → True
- `max_drawdown_treatment_ge_control` → True
- `cost_drag_fully_included` → True

Joint PASS requires ALL checks True; `profit_factor_treatment_gt_control=False`
alone forces `RESULT_CLASS=FAIL` (reason `NET_PROFIT_FACTOR_NOT_IMPROVED`).

## Command

```bash
PYTHONPATH=src:. python3 scripts/research/run_evaluate_ma_trend_alignment_mr_eligibility_development_v1.py \
  --output-dir docs/evidence/evaluate_ma_trend_alignment_mr_eligibility_development_v1
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
