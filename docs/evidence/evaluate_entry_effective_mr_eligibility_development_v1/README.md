# Evaluate entry-effective MR eligibility — DEVELOPMENT v1

```text
SLICE=EVALUATE_ENTRY_EFFECTIVE_MR_ELIGIBILITY_DEVELOPMENT_V1
BASE_SHA=8ddf8e2c0b9c6b8413f5211e9c0dffd827bbebaa
BRANCH=research/evaluate-entry-effective-mr-eligibility-development-v1
CLASS=DEVELOPMENT_EVALUATION_EVIDENCE_ONLY
HYPOTHESIS=ENTRY_EFFECTIVE_MR_ELIGIBILITY_MEAN_REVERSION_NON_BITCOIN_PERPETUALS_V1
DATASET=pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1
DATASET_CLASS=DEVELOPMENT_ONLY
CONFIG_ID=bollinger_bands_v2_full_canonical_system_economic_binding_v1
SEED=20220601
EVALUATION_RUN_COUNT=1
BACKTEST_EXECUTED=true
HOLDOUT_ACCESSED=false
SEALED_HOLDOUT_CONTENT_INSPECTED=false
ENTRY_ELIGIBILITY_DIVERGENCE=true
entries_blocked_by_gate=310
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
`entries_blocked_by_gate=310`), but treatment failed the locked economic
criteria (profit factor and net return not improved; max drawdown worsened).

The eligibility gate is applied **post-map** on Master-V2 position signals
(research-local mask only); no productive trading-logic / authority mutation.

## Key metrics (shared book, decision segment)

| Field | Baseline | Treatment |
|---|---:|---:|
| Trade count | 81 | 98 |
| Gross PnL | 1678.68 | -884.27 |
| Net PnL (closed-trade sum) | 1204.62 | -1460.89 |
| Fees | 316.04 | 384.41 |
| Slippage | 158.02 | 192.21 |
| Cost drag | 474.06 | 576.62 |
| Net return (shared equity) | 0.002824876 | -0.003422356 |
| Sharpe | 0.481152 | -0.908032 |
| Max drawdown | -0.009251 | -0.010859 |
| Profit factor | 1.313174 | 0.700731 |
| Win rate | 0.135802 | 0.091837 |
| Turnover | 81 | 98 |
| Entries blocked by gate | 0 | 310 |

## Acceptance (locked contract)

- `entry_eligibility_divergence_observed` → **true**
- `trade_count_treatment_ge_minimum` (≥50) → true
- `trade_count_treatment_ge_control_floor` → true
- `profit_factor_treatment_gt_control` → **false**
- `net_return_treatment_gt_control` → **false**
- `max_drawdown_treatment_ge_control` → **false**
- `cost_drag_fully_included` → true

## Command

```bash
PYTHONPATH=src:. python3 scripts/research/run_evaluate_entry_effective_mr_eligibility_development_v1.py \
  --output-dir docs/evidence/evaluate_entry_effective_mr_eligibility_development_v1
```

## Safety

- Holdout not accessed / not inspected
- No productive trading-logic / authority / risk / sizing / execution mutation
- Gate applied as research-only post-map mask over unchanged bollinger/MV2 chain
- `PROMOTION_ELIGIBLE=false`, economic offline gate unchanged/closed
- No runtime / shadow / testnet / live / orders
