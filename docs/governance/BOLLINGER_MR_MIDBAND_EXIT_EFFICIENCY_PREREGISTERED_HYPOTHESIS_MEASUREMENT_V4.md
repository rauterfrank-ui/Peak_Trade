# Bollinger/MR midband exit-efficiency — preregistered hypothesis and measurement v4

---
docs_token: DOCS_TOKEN_BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_PREREGISTERED_HYPOTHESIS_MEASUREMENT_V4
STATUS: DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL/INFRASTRUCTURE_FAILURE
scope: research, offline-only, non-authorizing, terminal-closeout
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

> **Non-authorizing:** Definition-only preregistration of one DEVELOPMENT_ONLY exit-efficiency
> hypothesis after terminal V3 `FAIL`. V4 is **not** a rerun of V3, V2, or V1. V3 remains
> terminal `FAIL` with run count 1 (`identical_arms_no_exit_divergence`; open_side unbound;
> `exit_bars_observed=0`). V2&#47;V1 remain terminal and unchanged. V4 presupposes the merged
> MV2 wiring_mod capture-alias open_side binding fix on main (PR #5398 &#47; `364f51b6`).
> No evaluation, no holdout access, no Economic&#47;Promotion gate open, no Master-V2 &#47;
> Double-Play &#47; risk &#47; sizing &#47; execution mutation.

## Status

`DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL&#47;INFRASTRUCTURE_FAILURE` — sole authorized
development evaluation slot consumed (`EVALUATION_RUN_COUNT=1`);
`EVALUATION_STARTED=true`; `EVALUATION_COMPLETED=false`;
`RESULT_CLASS=INFRASTRUCTURE_FAILURE`; `ECONOMIC_VERDICT=NOT_EVALUATED`;
`RERUN_ALLOWED=false`. Evidence:
`docs&#47;evidence&#47;evaluate_bollinger_mr_midband_exit_efficiency_development_v4&#47;`.

## Binding

- Hypothesis: `BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V4`
- Contract: `bollinger_mr_midband_exit_efficiency_preregistered_economic_hypothesis_measurement_contract.v4`
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1` (`DEVELOPMENT_ONLY`)
- `DEVELOPMENT_ONLY=true`
- `HOLDOUT_ALLOWED=false`
- Multiple-testing budget: `1`
- Authorized later development evaluation runs: `1` (one-shot; separate Operator-GO)
- Holdout: `offline_economic_reevaluation_sealed_long_panel_v1` opaque exclusion only
- Baseline: `bollinger_bands_v2_full_canonical_system_economic_binding_v1` (immutable)
- Treatment: `POST_ENTRY_EXIT_EFFICIENCY_MECHANISM` (not implemented in this slice)
- Primary decision metric: `NET_RETURN_AFTER_COSTS` (joint PASS requires measurement-validity
  gates first, then locked economic companions)
- Observability (mandatory): `EVALUATION_RUNNER_LIFECYCLE_OBSERVABILITY_V1`
- Falsy-zero hygiene (mandatory): `PANEL_RUNNER_FALSY_ZERO_PREMEASUREMENT_HYGIENE`
- Binding fix (mandatory): `MV2_WIRING_MOD_CAPTURE_ALIAS_OPEN_SIDE_BINDING_FIX`

## Measurement-validity prerequisites (fail-closed before real panel run)

1. Effective baseline&#47;treatment config digests must differ
   (`INVALID_MEASUREMENT_IDENTICAL_EFFECTIVE_CONFIGS` otherwise)
2. `open_side` must be bound in the per-bar exit-decision input via
   `wiring_mod.capture_backtest_engine_position_feedback_v1`
   (`INVALID_MEASUREMENT_BINDING_MISSING` otherwise)
3. `exit_bars_observed > 0` for at least one admissible synthetic contract case
   (`INVALID_MEASUREMENT_NO_EXIT_OBSERVABILITY` otherwise)
4. Baseline&#47;treatment must synthetically diverge at the exit-decision boundary
   (`INVALID_MEASUREMENT_BINDING_MISSING` otherwise)

## Predecessor V3 (read-only; terminal; not rerun)

- Hypothesis: `BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V3`
- Terminal: `FAIL` &#47; `identical_arms_no_exit_divergence`
- `EVALUATION_RUN_COUNT=1`; `RERUN_ALLOWED=false`
- Root cause class: measurement binding collapse
  (`FEEDBACK_MOD_ONLY_PATCH_LEFT_WIRING_MOD_FROM_IMPORT_ALIAS_UNBOUND`)
- No V3 result, partial measurement, checkpoint, or economic claim is transferred into V4

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

No evaluation in this slice. No panel&#47;holdout access. No V3&#47;V2&#47;V1 rerun. No runtime&#47;orders.
No productive Master-V2 &#47; Double-Play &#47; risk &#47; sizing &#47; execution mutation.
