---
docs_token: DOCS_TOKEN_BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_HOLDOUT_PREREGISTERED_MEASUREMENT_V1
STATUS: DEFINITION_ONLY_HOLDOUT_PREREGISTERED
scope: research, offline-only, non-authorizing
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

# Bollinger/MR midband exit reentry-cooldown — Holdout confirmation preregistration v1

Definition-only holdout confirmation successor for frozen Exit Efficiency V8.

- Hypothesis: `BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_NON_BITCOIN_PERPETUALS_HOLDOUT_V1`
- Predecessor: `BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V8`
- V8 digest (immutable): `610460038f56bddda426f4169876a4ead00c186d1601256174033b4e4fca0a0c`
- Holdout preregistration digest: `a0658fe3fb883939ed2a2de2c426f2e4edf21eeeb91d1b902d45b4d05a38fd1d`
- Mechanism identical to V8; parameters frozen; no retune
- Holdout run count: `0&#47;1`; execution unauthorized until separate Operator GO
- V8 identity remains `holdout_allowed=false` (not reopened/reused/rerun)

## Explicit non-actions

No holdout data access in this slice. No runner. No V8 reopen/rerun.
No economic-gate open. No promotion/runtime/orders. No Master-V2/Double-Play mutation.

## Next

`REVIEW_AND_MERGE_DEFINITION_ONLY_HOLDOUT_PREREGISTRATION_THEN_SEPARATE_OPERATOR_GO_FOR_EXACTLY_ONE_HOLDOUT_RUN`
