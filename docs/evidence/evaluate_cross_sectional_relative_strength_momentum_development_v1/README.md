# Evaluate CS RS momentum development v1 — terminal FAIL_CLOSED

```text
SLICE=EVALUATE_CROSS_SECTIONAL_RELATIVE_STRENGTH_MOMENTUM_DEVELOPMENT_V1
BASE_SHA=e7963fe3071c9942a58fce0e2f4b7394a75715f2
STRATEGY_ID=CROSS_SECTIONAL_RELATIVE_STRENGTH_MOMENTUM_V1
DATASET=pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1
STATUS=FAIL_CLOSED
REASON=UNEXPECTED:ValueError:ALIGNMENT_GAP:okx:linear_perpetual:1INCH:USDT:USDT:perp
EVALUATION_EXECUTED=false
RUNNER_STARTED=true
CLI_REPORTED_RUNNER_STARTED=false
RUN_BUDGET_CONSUMED=true
EVALUATION_RUN_COUNT=1
RUNNER_START_COUNT=1
HOLDOUT_ACCESSED=false
RETRY_FORBIDDEN=true
PREREGISTERED_GATES=NOT_EVALUATED
```

## Exact command (single authorized attempt; budget consumed)

```bash
python3 scripts/research/run_evaluate_cross_sectional_relative_strength_momentum_development_v1.py \
  --mode evaluate \
  --authorize-single-development-evaluation CROSS_SECTIONAL_RELATIVE_STRENGTH_MOMENTUM_NON_BITCOIN_PERPETUALS_V1
```

Panel load failed with `ALIGNMENT_GAP` before economic metrics. No retry.
