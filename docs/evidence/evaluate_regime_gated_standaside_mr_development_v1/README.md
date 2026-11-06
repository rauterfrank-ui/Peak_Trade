# Evaluate regime-gated standaside MR — DEVELOPMENT v1

```text
SLICE=EVALUATE_REGIME_GATED_STANDASIDE_MR_DEVELOPMENT_V1
BASE_SHA=08474655be46b178c9f0113766cfbb67fab448be
BRANCH=research/evaluate-regime-gated-standaside-mr-development-v1
CLASS=DEVELOPMENT_EVALUATION_EVIDENCE_ONLY
HYPOTHESIS=REGIME_GATED_STANDASIDE_MEAN_REVERSION_NON_BITCOIN_PERPETUALS_V1
DATASET=pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1
DATASET_CLASS=DEVELOPMENT_ONLY
CONFIG_ID=bollinger_bands_v2_full_canonical_system_economic_binding_v1
SEED=20220601
EVALUATION_RUN_COUNT=1
BACKTEST_EXECUTED=true
HOLDOUT_ACCESSED=false
SEALED_HOLDOUT_CONTENT_INSPECTED=false
RESULT_CLASS=FAIL
PROMOTION_ELIGIBLE=false
RUNTIME=false
ORDERS=false
```

## Verdict

Preregistered DEVELOPMENT evaluation on the sealed independent panel
`final_development_confirmation` segment only.

**RESULT_CLASS=FAIL** — treatment did not strictly reduce turnover or cost drag versus
baseline (`PASS_REQUIRES_NOT_MET`). Metrics for baseline and treatment are identical
because ~98% of decision-segment bars classified `RANGE_BOUND` under the frozen
close-path formulas, and all 51 entries already occurred inside `RANGE_BOUND`
(stand-aside gate never blocked an observed entry).

## Key metrics (shared book, decision segment)

| Field | Baseline | Treatment |
|---|---:|---:|
| Trade count | 51 | 51 |
| Gross PnL | 27.83 | 27.83 |
| Net PnL (closed-trade sum) | -274.69 | -274.69 |
| Fees | 201.68 | 201.68 |
| Slippage | 100.84 | 100.84 |
| Cost drag | 302.52 | 302.52 |
| Net return (shared equity) | 0.002575 | 0.002575 |
| Sharpe | 0.542 | 0.542 |
| Max drawdown | -0.007132 | -0.007132 |
| Profit factor | 0.895 | 0.895 |
| Win rate | 0.078 | 0.078 |
| Turnover | 51 | 51 |

## Acceptance (locked contract)

- `trade_count_treatment >= 50` → true
- `max_drawdown_treatment >= max_drawdown_baseline` → true (equal)
- `turnover_treatment < turnover_baseline` → **false** (equal)
- `cost_drag_treatment < cost_drag_baseline` → **false** (equal)
- `net_return_treatment >= baseline - 0.005` → true

## Command

```bash
PYTHONPATH=src:. python3 scripts/research/run_evaluate_regime_gated_standaside_mr_development_v1.py \
  --output-dir docs/evidence/evaluate_regime_gated_standaside_mr_development_v1
```

## Safety

- Holdout not accessed / not inspected
- No productive trading-logic / authority / risk / sizing / execution mutation
- Gate applied as research-only signal mask over unchanged bollinger chain
- `PROMOTION_ELIGIBLE=false`, economic offline gate unchanged/closed
- No runtime / shadow / testnet / live / orders
