# Evaluate ADX range-admission MR eligibility — DEVELOPMENT v1

```text
SLICE=EVALUATE_ADX_RANGE_ADMISSION_MR_ELIGIBILITY_DEVELOPMENT_V1
BASE_SHA=974126ec84a18658cd5dfc7f95fe31a04fe3e7b6
BRANCH=research/evaluate-adx-range-admission-mr-eligibility-development-v1
CLASS=DEVELOPMENT_EVALUATION_EVIDENCE_ONLY
HYPOTHESIS=ADX_RANGE_ADMISSION_MR_ENTRY_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1
DATASET=pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1
DATASET_CLASS=DEVELOPMENT_ONLY
CONFIG_ID=bollinger_bands_v2_full_canonical_system_economic_binding_v1
SEED=20220601
EVALUATION_RUN_COUNT=1
BACKTEST_EXECUTED=true
HOLDOUT_ACCESSED=false
SEALED_HOLDOUT_CONTENT_INSPECTED=false
ENTRY_ELIGIBILITY_DIVERGENCE=true
entries_blocked_by_gate=260
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
`entries_blocked_by_gate=260`), but treatment failed the locked economic
criteria (profit factor and net return not improved).

The eligibility gate is applied **post-map** on Master-V2 position signals
(research-local mask only); no productive trading-logic / authority mutation.

## Key metrics (shared book, decision segment)

| Field | Baseline | Treatment |
|---|---:|---:|
| Trade count | 117 | 110 |
| Gross PnL | -890.35 | -1221.73 |
| Net PnL (closed-trade sum) | -1579.49 | -1870.14 |
| Fees | 459.43 | 432.27 |
| Slippage | 229.71 | 216.14 |
| Cost drag | 689.14 | 648.41 |
| Net return (shared equity) | -0.0035966843294545914 | -0.004187424636777681 |
| Sharpe | -0.6894122039695529 | -1.0453422995487085 |
| Max drawdown | -0.013820156962916736 | -0.012086056217016994 |
| Profit factor | 0.7324360833782796 | 0.6601913977187674 |
| Win rate | 0.08547008547008547 | 0.09090909090909091 |
| Turnover | 117.0 | 110.0 |
| Entries blocked by gate | 0 | 260 |

## Acceptance (locked contract)

- `entry_eligibility_divergence_observed` → **True**
- `trade_count_treatment_ge_minimum` (≥50) → True
- `trade_count_treatment_ge_control_floor` → True
- `profit_factor_treatment_gt_control` → **False**
- `net_return_treatment_gt_control` → **False**
- `max_drawdown_treatment_ge_control` → True
- `cost_drag_fully_included` → True

## Command

```bash
PYTHONPATH=src:. python3 scripts/research/run_evaluate_adx_range_admission_mr_eligibility_development_v1.py \
  --output-dir docs/evidence/evaluate_adx_range_admission_mr_eligibility_development_v1
```

## Safety

- Holdout not accessed / not inspected
- No productive trading-logic / authority / risk / sizing / execution mutation
- Gate applied as research-only post-map mask over unchanged bollinger/MV2 chain
- `PROMOTION_ELIGIBLE=false`, economic offline gate unchanged/closed
- No runtime / shadow / testnet / live / orders
