---
docs_token: DOCS_TOKEN_BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_PREREGISTERED_HYPOTHESIS_MEASUREMENT_V5
artifact: bollinger_mr_midband_exit_efficiency_preregistered_hypothesis_measurement_v5
---

# Bollinger&#47;MR midband exit-efficiency — preregistered hypothesis measurement V5

## Status

`DEFINITION_ONLY_PREREGISTERED` — no evaluation authorized or executed in this slice.
`EVALUATION_RUN_COUNT=0` &#47; `RUN_LIMIT=1`.

## Identity

- Hypothesis: `BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V5`
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1`
- Dataset class: `DEVELOPMENT_ONLY`
- Contract: `config&#47;research&#47;bollinger_mr_midband_exit_efficiency_preregistered_economic_hypothesis_measurement_contract_v5.json`
- Digest: `b85903ebc76d1fefdb576075e88a1b72d9abb852ad4da5f1f8c5bc9c0bd21b2e`
- Evidence: `docs&#47;evidence&#47;preregister_bollinger_mr_midband_exit_efficiency_hypothesis_v5&#47;`

## Scope

Preserves the V4 economic hypothesis, baseline&#47;treatment arms, metrics, acceptance
criteria, universe, costs, sizing, and evaluation semantics.
V5 delta is infrastructure &#47; measurement-lifecycle only:

- Generic process-lifecycle observability (`BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_PROCESS_LIFECYCLE_CHECKPOINT_V5`)
- Monotonic lifecycle state machine
- Atomic checkpoint persistence (temp-file + fsync&#47;replace via canonical helper)
- Read-only recovery inspection
- Dead process before lifecycle-terminal => `INFRASTRUCTURE_FAILURE`
- Partial metrics remain non-authoritative
- Checkpoints never authorize automatic rerun or another run slot
- Import&#47;validation of the definition cannot start the runner

## Mandatory bindings

- Observability: `EVALUATION_RUNNER_LIFECYCLE_OBSERVABILITY_V1`
- Lifecycle checkpoint: `BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_PROCESS_LIFECYCLE_CHECKPOINT_V5`
- Falsy-zero hygiene: `PANEL_RUNNER_FALSY_ZERO_PREMEASUREMENT_HYGIENE`
- Binding fix: `MV2_WIRING_MOD_CAPTURE_ALIAS_OPEN_SIDE_BINDING_FIX`
- Primary decision metric: `NET_RETURN_AFTER_COSTS`

## Predecessor V4 (read-only; terminal; not rerun)

- Hypothesis: `BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V4`
- Terminal: `DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL&#47;INFRASTRUCTURE_FAILURE`
- Diagnostic: `PROCESS_DIED_INCOMPLETE_PANEL_RUN_NO_LIFECYCLE_TERMINAL`
- `EVALUATION_RUN_COUNT=1`; `RERUN_ALLOWED=false`
- Baseline members completed `1&#47;46`; treatment `0&#47;46`; no economic closeout
- No V4 result, partial measurement, checkpoint, or economic claim is transferred into V5
- V4 must not be reinterpreted as economic PASS or FAIL

## Terminal classifications authorized

- `PASS`
- `FAIL`
- `INVALID_MEASUREMENT_BINDING_MISSING`
- `INVALID_MEASUREMENT_IDENTICAL_EFFECTIVE_CONFIGS`
- `INVALID_MEASUREMENT_NO_EXIT_OBSERVABILITY`
- `INFRASTRUCTURE_FAILURE`

## Promotion

Explicitly not authorized by this preregistration. Economic offline gate remains closed.

## Explicit non-actions

No evaluation in this slice. No panel&#47;holdout access. No V4&#47;V3&#47;V2&#47;V1 rerun.
No runtime&#47;orders. No productive Master-V2 &#47; Double-Play &#47; risk &#47; sizing &#47; execution mutation.
No automatic rerun from checkpoints. No V6 auto-create.
