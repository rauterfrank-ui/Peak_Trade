# Evaluate RSI-exhaustion MR eligibility — DEVELOPMENT v1

```text
SLICE=EVALUATE_RSI_EXHAUSTION_MR_ELIGIBILITY_DEVELOPMENT_V1
BASE_SHA=c3b00fffa7735b809970177ef0e4a3238981f863
BRANCH=research/evaluate-rsi-exhaustion-mr-entry-eligibility-development-v1
CLASS=DEVELOPMENT_EVALUATION_EVIDENCE_ONLY
HYPOTHESIS=RSI_EXHAUSTION_MR_ENTRY_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1
DATASET=pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1
DATASET_CLASS=DEVELOPMENT_ONLY
CONFIG_ID=bollinger_bands_v2_full_canonical_system_economic_binding_v1
SEED=20220601
EVALUATION_RUN_COUNT=1
BACKTEST_EXECUTED=true
HOLDOUT_ACCESSED=false
SEALED_HOLDOUT_CONTENT_INSPECTED=false
ENTRY_ELIGIBILITY_DIVERGENCE=true
entries_blocked_by_gate=268
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
`entries_blocked_by_gate=268`), but treatment failed the locked economic
criteria (profit factor and net return not improved).

The eligibility gate is applied **post-map** on Master-V2 position signals
(research-local mask only); no productive trading-logic / authority mutation.

## Key metrics (shared book, decision segment)

| Field | Baseline | Treatment |
|---|---:|---:|
| Trade count | 126 | 128 |
| Gross PnL | 742.53 | -1294.52 |
| Net PnL (closed-trade sum) | 3.53 | -2048.24 |
| Fees | 492.66 | 502.48 |
| Slippage | 246.33 | 251.24 |
| Cost drag | 739.00 | 753.72 |
| Net return (shared equity) | -0.0005840594533342847 | -0.004446146508991444 |
| Sharpe | -0.07171982687728654 | -0.8994602577012483 |
| Max drawdown | -0.014172438505512036 | -0.01414317291244879 |
| Profit factor | 1.0005657702862698 | 0.6851388521496325 |
| Win rate | 0.10317460317460317 | 0.078125 |
| Turnover | 126.0 | 128.0 |
| Entries blocked by gate | 0 | 268 |

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
PYTHONPATH=src:. python3 scripts/research/run_evaluate_rsi_exhaustion_mr_eligibility_development_v1.py \
  --output-dir docs/evidence/evaluate_rsi_exhaustion_mr_eligibility_development_v1
```

## Safety

- Holdout not accessed / not inspected
- No productive trading-logic / authority / risk / sizing / execution mutation
- Gate applied as research-only post-map mask over unchanged bollinger/MV2 chain
- `PROMOTION_ELIGIBLE=false`, economic offline gate unchanged/closed
- No runtime / shadow / testnet / live / orders
