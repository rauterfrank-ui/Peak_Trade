# Cross-sectional relative-strength momentum v1 — DEVELOPMENT evaluation entry point

## Status

`ENTRY_POINT_MATERIALIZED_EVALUATION_UNAUTHORIZED`

Infrastructure-only. Canonical CLI&#47;owner&#47;binding&#47;guards&#47;evidence surface are
materialized. No development evaluation executed. Run counts remain `0`.

## Owner

`CROSS_SECTIONAL_RELATIVE_STRENGTH_MOMENTUM_V1_DEVELOPMENT_EVALUATION_ENTRY_POINT_V1`

## Canonical entry point

`scripts&#47;research&#47;run_evaluate_cross_sectional_relative_strength_momentum_development_v1.py`

Default mode: `preflight` (no panel open, no runner start, no slot claim).

Evaluate mode remains fail-closed while
`development_evaluation_authorized=false` on the measurement contract &#47; program.

## Bindings

- Strategy identity: `CROSS_SECTIONAL_RELATIVE_STRENGTH_MOMENTUM_V1`
- Signal family: `CROSS_SECTIONAL_MOMENTUM`
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1`
  (`DEVELOPMENT_ONLY`)
- Measurement contract digest (frozen):
  `1d7f855027df438629765566cb559310820ab6699b6351bddc1577b1f731c158`
- Entry-point binding:
  `config&#47;research&#47;cross_sectional_relative_strength_momentum_v1_development_evaluation_entry_point_binding_v1.json`
- Lifecycle authority:
  `config&#47;research&#47;material_different_cross_sectional_momentum_hypothesis_backlog_v1.json`

## Reused canonical owners (no second metrics truth)

- Score&#47;selection: already-merged CS RS momentum v1 modules
- Backtest&#47;PnL metrics: `src.research.cross_sectional_single_slot_backtest_wiring_v0`
- Stats: `src.backtest.stats`
- Economic validity policy: `src.backtest.economic_validity_policy_v1`

## Time-segment &#47; sample guards (preregistered, unchanged)

- `TIME_SEGMENT_DEFINITION_ID=CHRONOLOGICAL_EQUAL_DURATION_QUARTERS_V1`
- Exactly 4 chronological equal-duration quarters; remainder to earliest segments
- Valid rebalance observations = evaluable rebalance timestamps only (not trades&#47;bars&#47;instruments)
- `minimum_rebalance_observations=30`
- `minimum_passing_segments=2` &#47; `time_segment_robustness_pass_ratio=0.5`

## Explicit non-actions in this slice

No evaluation run, no holdout access, no retry, no threshold change, no result
calibration, no Master-V2&#47;Double-Play&#47;risk&#47;sizing&#47;execution&#47;runtime activation,
economic&#47;promotion gates remain closed.

## Next step

`AWAIT_SEPARATE_OPERATOR_GO_FOR_BOUNDED_DEVELOPMENT_EVALUATION_EXECUTION`

---
docs_token: DOCS_TOKEN_CROSS_SECTIONAL_RELATIVE_STRENGTH_MOMENTUM_V1_DEVELOPMENT_EVALUATION_ENTRY_POINT_V1
STATUS: ENTRY_POINT_MATERIALIZED_EVALUATION_UNAUTHORIZED
scope: research, offline-only, non-authorizing, evaluation-entry-point-infrastructure
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---
