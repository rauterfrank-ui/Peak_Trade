# Volatility decay breakout v1 — DEVELOPMENT evaluation entry point

## Status

`CORRECTIVE_MEASUREMENT_REEVALUATION_EXECUTED_FAIL_CLOSED_UNPAIRABLE_ENTRY_NO_EXIT`

Executable development-evaluation path and panel execution boundary are present.
The single authorized development evaluate attempt fail-closed during productive
PnL/metrics materialization with `UNEXPECTED:OverflowError:(34, 'Result too large')`
under an invalid instrument-count-scaled portfolio measurement.
Durable development run slot consumed (`DEVELOPMENT_RUN_COUNT=1`, `RUNNER_START_COUNT=1`).
No development retry.

A separate bounded corrective measurement reevaluation executed once after
measurement repair merge `00a820f080973600378c3c2d5513905ee07217e9`
(`PORTFOLIO_AGGREGATION_ID=RESEARCH_EQUAL_WEIGHT_NORMALIZED_SLEEVE_COMBINE_V1`)
and fail-closed with
`UNEXPECTED:ValueError:UNPAIRABLE_ENTRY_NO_EXIT:okx:linear_perpetual:DOGE:USDT:USDT:perp:10574`.
Corrective slot consumed (`CORRECTIVE_MEASUREMENT_REEVALUATION_COUNT=1/1`).
Development counters preserved at `1`. No corrective retry.
New evidence under
`docs/evidence/evaluate_volatility_decay_breakout_corrective_measurement_reevaluation_v1/`
(prior development evidence preserved unmodified; supersession audited).

## Owner

`VOLATILITY_DECAY_BREAKOUT_V1_DEVELOPMENT_EVALUATION_ENTRY_POINT_V1`

## Canonical entry point

`scripts/research/run_evaluate_volatility_decay_breakout_development_v1.py`

### Corrective CLI (executed; slot consumed; no retry)

```bash
python3 scripts/research/run_evaluate_volatility_decay_breakout_development_v1.py \
  --mode corrective-reevaluate \
  --authorize-corrective-measurement-reevaluation \
  VOLATILITY_DECAY_BREAKOUT_CORRECTIVE_MEASUREMENT_REEVALUATION_V1
```

## Bindings

- Strategy identity: `VOLATILITY_DECAY_BREAKOUT_V1`
- Previous strategy: `VOLATILITY_EXPANSION_PERSISTENCE_V1`
- Baseline: `UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1`
- Program: `VOLATILITY_REGIME_RESEARCH_PROGRAM_V1`
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1`
- Measurement contract digest:
  `2d0922f0bf4a2082a032320f1a03316012682ea4021a1677e30c481fa620590c`
- Productive PnL evaluator (reused):
  `src/research/volatility_compression_breakout_v1_development_evaluation_v1/productive_exit_pnl_evaluator_v1.py`
- Portfolio aggregation:
  `RESEARCH_EQUAL_WEIGHT_NORMALIZED_SLEEVE_COMBINE_V1`
- Terminal development evidence (superseded measurement; preserved):
  `docs/evidence/evaluate_volatility_decay_breakout_development_v1/summary.json`
- Terminal corrective evidence (FAIL_CLOSED_UNPAIRABLE_ENTRY_NO_EXIT):
  `docs/evidence/evaluate_volatility_decay_breakout_corrective_measurement_reevaluation_v1/summary.json`

## Next step

`NO_RETRY_CORRECTIVE_SLOT_CONSUMED_FAIL_CLOSED_UNPAIRABLE_ENTRY_NO_EXIT_REQUIRES_NEW_SEPARATE_OPERATOR_GO`

## Explicitly false

- `LIVE_AUTHORIZED=false`
- `ORDERS=false`
- `SHADOW=false`
- `TESTNET=false`
- `HOLDOUT_ACCESS=false`
- `RETRY_FORBIDDEN=true` (development and corrective retry)
- `DEVELOPMENT_RUN_COUNT=1` (preserved across corrective execution)
- `CORRECTIVE_MEASUREMENT_REEVALUATION_COUNT=1` (slot consumed; no retry)

---
docs_token: DOCS_TOKEN_VOLATILITY_DECAY_BREAKOUT_V1_DEVELOPMENT_EVALUATION_ENTRY_POINT_V1
STATUS: CORRECTIVE_MEASUREMENT_REEVALUATION_EXECUTED_FAIL_CLOSED_UNPAIRABLE_ENTRY_NO_EXIT
scope: research, offline-only, corrective-measurement-reevaluation-terminal
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---
