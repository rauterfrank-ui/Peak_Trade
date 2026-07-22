---
docs_token: DOCS_TOKEN_BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_HOLDOUT_PREREGISTERED_MEASUREMENT_V1
STATUS: HOLDOUT_EVALUATION_EXECUTED_TERMINAL
scope: research, offline-only, non-authorizing
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

# Bollinger/MR midband exit reentry-cooldown — Holdout evaluation v1

`HOLDOUT_EVALUATION_EXECUTED_TERMINAL` — independently versioned holdout evaluation
executed once and terminated as `FAIL` / `NET_PROFIT_FACTOR_NOT_IMPROVED`.

## Binding

- Hypothesis: `BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_NON_BITCOIN_PERPETUALS_HOLDOUT_V1`
- Predecessor: `BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V8`
- V8 digest (immutable): `610460038f56bddda426f4169876a4ead00c186d1601256174033b4e4fca0a0c`
- Holdout result class: `FAIL`
- Holdout reason: `NET_PROFIT_FACTOR_NOT_IMPROVED`
- Holdout run count: `1`
- Holdout run limit: `1`
- Primary metrics produced: `true`
- Frozen preregistration digest: `a0658fe3fb883939ed2a2de2c426f2e4edf21eeeb91d1b902d45b4d05a38fd1d`
- Frozen holdout split digest: `e29eeb4e9d264e1529a0c7419d707ce84df7919ee6ed95a833612fca46a7184d`
- Evidence: `docs/evidence/evaluate_bollinger_mr_midband_exit_reentry_cooldown_holdout_v1/`

## Gates

- `PROMOTION_ELIGIBLE=false`
- Economic offline gate unchanged/closed
- No runtime / shadow / paper / testnet / live / orders
- Retry / restart / post-result tuning: forbidden
- V8 reopen/rerun: forbidden
- Second holdout run: forbidden

## Next step

`REVIEW_TERMINAL_HOLDOUT_FAIL_NO_RETRY`
