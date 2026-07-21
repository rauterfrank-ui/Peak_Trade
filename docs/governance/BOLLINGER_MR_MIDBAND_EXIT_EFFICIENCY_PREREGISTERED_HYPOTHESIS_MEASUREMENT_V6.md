---
docs_token: DOCS_TOKEN_BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_PREREGISTERED_HYPOTHESIS_MEASUREMENT_V6
artifact: bollinger_mr_midband_exit_efficiency_preregistered_hypothesis_measurement_v6
---

# Bollinger&#47;MR midband exit-efficiency — preregistered hypothesis measurement V6

## Status

`DEFINITION_ONLY_PREREGISTERED` — no evaluation authorized or executed in this slice.
`EVALUATION_RUN_COUNT=0` &#47; `RUN_LIMIT=1`.

## Identity

- Hypothesis: `BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V6`
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1`
- Dataset class: `DEVELOPMENT_ONLY`
- Contract: `config&#47;research&#47;bollinger_mr_midband_exit_efficiency_preregistered_economic_hypothesis_measurement_contract_v6.json`
- Digest: `9ddcd32d78b3b3f60c168321404b2270a770409d46a3bff036f7dbc5eefd8fa5`
- Evidence: `docs&#47;evidence&#47;preregister_bollinger_mr_midband_exit_efficiency_hypothesis_v6&#47;`

## Economic change versus V5

V5 preserved the pure side-aware midband-cross exit
(`canonical_bollinger_side_aware_middle_band_exit_v1`) and added lifecycle
observability only. V6 changes the economic exit treatment:

- Mechanism: `canonical_bollinger_side_aware_middle_band_exit_with_frozen_max_holding_horizon_v1`
- Composite triggers: midband-cross OR hard max-holding-horizon at sealed
  `splits.max_holding_horizon_hours=48` (PT1H => 48 bars), whichever first
- Stop-loss remains active if hit first
- Not derived from V5 partial metrics

## Scope preserved

Baseline&#47;control arm, universe, costs (1.0x), sizing, risk, execution, Double-Play
authority, measurement-validity gates, and one-run lifecycle constraints remain
as lineage-frozen. V6 reuses
`BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_PROCESS_LIFECYCLE_CHECKPOINT_V5`.

## Predecessor V5 (read-only; terminal; not rerun)

- Hypothesis: `BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V5`
- Terminal: `DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL&#47;INFRASTRUCTURE_FAILURE`
- Diagnostic: `PROCESS_DIED_INCOMPLETE_PANEL_RUN_NO_LIFECYCLE_TERMINAL`
- `EVALUATION_RUN_COUNT=1`; `RERUN_ALLOWED=false`
- Baseline members completed `3&#47;46`; treatment `0&#47;46`; no economic closeout
- Partial metrics non-authoritative; not transferred into V6

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

No evaluation in this slice. No panel&#47;holdout access. No V5&#47;V4&#47;V3&#47;V2&#47;V1 rerun.
No runtime&#47;orders. No productive Master-V2 &#47; Double-Play &#47; risk &#47; sizing &#47; execution mutation.
No automatic rerun from checkpoints. No V7 auto-create.
