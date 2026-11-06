# Bollinger/MR midband exit-efficiency — preregistered hypothesis and measurement v3

---
docs_token: DOCS_TOKEN_BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_PREREGISTERED_HYPOTHESIS_MEASUREMENT_V3
STATUS: DEFINITION_ONLY_PREREGISTERED
scope: research, offline-only, non-authorizing, definition-only
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

> **Non-authorizing:** Definition-only preregistration of one DEVELOPMENT_ONLY exit-efficiency
> hypothesis with identical measurement definition to V2&#47;V1. V3 is **not** a rerun of V2
> or V1. V2 remains terminal `INCONCLUSIVE_INFRASTRUCTURE_FAILURE` with run count 1
> (`PREMEASUREMENT_GATE_FALSE_POSITIVE_ZERO_OR_SENTINEL`; no panel backtest; no economic
> metrics). V1 remains terminal and unchanged. No evaluation, no holdout access, no
> Economic&#47;Promotion gate open, no Master-V2 &#47; Double-Play &#47; risk &#47; sizing &#47;
> execution mutation.

## Status

`DEFINITION_ONLY_PREREGISTERED` — hypothesis and measurement contract preregistered;
`EVALUATION_RUN_COUNT=0`; `EVALUATION_STARTED=false`; `EVALUATION_COMPLETED=false`;
`RESULT_CLASS=NOT_EVALUATED`; `ECONOMIC_VERDICT=NOT_EVALUATED`; no evaluation executed.

## Binding

- Hypothesis: `BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V3`
- Contract: `bollinger_mr_midband_exit_efficiency_preregistered_economic_hypothesis_measurement_contract.v3`
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1` (`DEVELOPMENT_ONLY`)
- `DEVELOPMENT_ONLY=true`
- `HOLDOUT_ALLOWED=false`
- Multiple-testing budget: `1`
- Authorized later development evaluation runs: `1` (one-shot; separate Operator-GO)
- Holdout: `offline_economic_reevaluation_sealed_long_panel_v1` opaque exclusion only
- Baseline: `bollinger_bands_v2_full_canonical_system_economic_binding_v1` (immutable)
- Parent diagnostic: `bollinger_mr_economic_failure_decomposition_development_v1`
  (`DIAGNOSTIC_CLASS=COSTS_DESTROY_MARGINAL_EDGE`, `EXIT_LEAKAGE_MATERIAL=true`)
- Treatment: `POST_ENTRY_EXIT_EFFICIENCY_MECHANISM` (not implemented in this slice)
- Primary decision metric: `NET_PROFIT_FACTOR` (joint PASS requires all locked companions)
- Observability (mandatory for any future evaluation): `EVALUATION_RUNNER_LIFECYCLE_OBSERVABILITY_V1`
- Falsy-zero hygiene (mandatory for any future evaluation):
  `PANEL_RUNNER_FALSY_ZERO_PREMEASUREMENT_HYGIENE` (already merged; does not authorize V2 rerun)

## Predecessor V2 (read-only; terminal; not rerun)

- Hypothesis: `BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V2`
- Terminal: `INCONCLUSIVE_INFRASTRUCTURE_FAILURE`
- `EVALUATION_RUN_COUNT=1`; `RERUN_ALLOWED=false`
- Root cause: `PREMEASUREMENT_GATE_FALSE_POSITIVE_ZERO_OR_SENTINEL`
- Panel backtest executed: `false`
- Economic metrics produced: `false`
- No V2 result, partial measurement, checkpoint, or economic claim is transferred into V3
- V3 is a new independently preregistered measurement authority after the merged
  panel_runner falsy-zero hygiene correction — **not** a V2 rerun

## Predecessor V1 lineage (read-only)

- Hypothesis: `BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V1`
- Remains terminal `INCONCLUSIVE_INFRASTRUCTURE_FAILURE` with run count 1
- Unchanged by this V3 definition-only slice

## Why V3 is a new independent evaluation authority

The V2 sole authorized development evaluation slot was consumed by an infrastructure
premeasurement abort. Under the one-run-only contract, that slot cannot be reused.
V3 therefore introduces a new hypothesis ID with identical economic&#47;definition
semantics and binds the already-merged falsy-zero runner correction as a required
infrastructure prerequisite for any future separately authorized evaluation.

## Research question (exact; identical to V2&#47;V1)

`Given COSTS_DESTROY_MARGINAL_EDGE on the sealed DEVELOPMENT_ONLY Bollinger&#47;MR baseline (marginal gross PF~1.01, all-SHORT book), does a cost-structure or holding&#47;exit-efficiency change class exist that preserves gross edge without retuning terminal entry-eligibility parameters or reopening exhausted filter families?`

Scope selected: `EXIT_EFFICIENCY_ONLY` (not cost-structure weakening; not SHORT-side filter; not entry-eligibility reopen).

## Exit mechanism (ex ante, deterministic; identical to V2&#47;V1)

Canonical side-aware Bollinger middle-band mean-reversion exit from immutable baseline
binding parameters (`bb_period=20`, `bb_std=2.0`, exit level = middle band):

- LONG open: EXIT iff `close[t-1] < middle[t-1]` AND `close[t] >= middle[t]`
- SHORT open: EXIT iff `close[t-1] > middle[t-1]` AND `close[t] <= middle[t]`
- Stop-loss remains active if hit first
- Fail-closed if state &#47; bar-index &#47; digest binding missing
- No future MFE; no lookahead; no entry&#47;side&#47;instrument authority

`EXIT_DIVERGENCE_REQUIRED=true` — absence ⇒ `RESULT_CLASS=FAIL`.

## Pass criteria (frozen before any run; identical to V2&#47;V1)

PASS requires all of:

- `net_profit_factor_treatment > control`
- `net_pnl_treatment > control` and `net_return_treatment > control`
- MFE capture ratio improved
- MFE-to-exit leakage reduced
- improvement not solely explained by reduced trade count or artificially lower turnover
- no new instrument concentration
- canonical cost multiplier exactly `1.0` (never below)

## Lifecycle contract (one-run-only)

- Runner start must persist `EVALUATION_STARTED=true` and increment run count `0→1`
- Terminal state must be persisted before process exit
- No rerun after runner start &#47; after run count equals 1
- Infrastructure failure (`INCONCLUSIVE_INFRASTRUCTURE_FAILURE`, economic verdict
  `NOT_EVALUATED`) is distinct from economic `FAIL` &#47; `PASS`
- No auto-resume; no auto-rerun on infrastructure failure

## Observability and hygiene bindings (mandatory)

Future evaluation must bind:

1. `EVALUATION_RUNNER_LIFECYCLE_OBSERVABILITY_V1` with durable diagnostics for phase,
   last confirmed member, heartbeat&#47;progress, exit code, signal, exception class +
   truncated traceback, and atomic lifecycle checkpoint
2. `PANEL_RUNNER_FALSY_ZERO_PREMEASUREMENT_HYGIENE` — runner must not treat legitimate
   `evaluation_run_count=0` as missing via Python falsy-zero (`x or -1`)

Incomplete execution ends fail-closed as `INCONCLUSIVE_INFRASTRUCTURE_FAILURE`.

## Terminal states

- `DEFINITION_ONLY_PREREGISTERED` (current)
- `DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL&#47;PASS`
- `DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL&#47;FAIL`
- `DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL&#47;INCONCLUSIVE_INFRASTRUCTURE_FAILURE`

Maximum one development evaluation run under this hypothesis ID.

## Gates

- `PROMOTION_ELIGIBLE=false`
- Economic offline gate unchanged&#47;closed
- On FAIL: retuning forbidden; holdout forbidden
- No runtime &#47; shadow &#47; testnet &#47; live &#47; orders
- `PRODUCTIVE_TRADING_LOGIC_CHANGED=false`
- `PRODUCTION_STRATEGY_SEMANTICS_CHANGED=false`
- `DOUBLE_PLAY_AUTHORITY_CHANGED=false`
- `RISK_SIZING_EXECUTION_SEMANTICS_CHANGED=false`

## Next step

Review and merge this definition-only V3 PR. Any development evaluation requires a
separate Operator-GO. Do not rerun V1 or V2. Do not create V4 in this slice.
