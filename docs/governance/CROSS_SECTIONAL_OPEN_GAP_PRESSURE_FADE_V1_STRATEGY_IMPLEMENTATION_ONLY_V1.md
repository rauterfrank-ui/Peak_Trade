# Cross-sectional open-gap pressure fade v1 — strategy implementation only

## Status

`STRATEGY_IMPLEMENTATION_PRESENT` under operator GO
`GO_CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_V1_STRATEGY_IMPLEMENTATION_ONLY_V1`
(PR #5495 MERGED).

Post-merge terminal truth (PR #5496): one bounded DEVELOPMENT evaluation executed
with `DEVELOPMENT_FAIL`. Development run count is 1; run slot consumed.
Evaluation unauthorized for further runs; retry forbidden.

## Binding

- Capability PR: `#5495` MERGED
- Hypothesis: `CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_NON_BITCOIN_PERPETUALS_V1`
- Strategy identity: `CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_V1`
- Signal family: `CROSS_SECTIONAL_OPEN_GAP_PRESSURE`
- Directional form: `D_MUTUALLY_EXCLUSIVE_DIRECTIONAL_SELECTION`
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1`
- Implementation binding: `config&#47;research&#47;cross_sectional_open_gap_pressure_fade_v1_strategy_implementation_binding_v1.json`
- Score: `src&#47;research&#47;cross_sectional_open_gap_pressure_fade_v1_score_v1.py`
- Selection: `src&#47;research&#47;cross_sectional_open_gap_pressure_fade_v1_selection_v1.py`
- Development evidence: `docs&#47;evidence&#47;evaluate_cross_sectional_open_gap_pressure_fade_development_v1&#47;`

## Semantics

- `gap_b=log(open_b&#47;close_{b-1})`; `score_i=-mean(gap)` over frozen lookback
- `single_top1_by_score_desc` + `symmetric_top1_sign`
- Frozen: `lookback_N=30`, `rebalance_interval_bars=5`, `signal_lag_bars=1`,
  `min_eligible_members_for_rank=5`, `n=1`
- Fail-closed: non-finite&#47;non-positive prior close ineligible; `score==0` ineligible;
  eligible &lt; 5 → no selection
- Fade: gap-down → positive score → LONG; gap-up → negative score → SHORT
- Rank intent only; Double-Play remains sole directional transition authority
- Not a CLV pressure retry; no shared CLV utility; no values 36&#47;6

## Terminal markers after PR #5496

- `DEVELOPMENT_RUN_COUNT=1`
- `DEVELOPMENT_VERDICT=DEVELOPMENT_FAIL`
- `DEVELOPMENT_SLOT_CONSUMED=true`
- `EVALUATION_AUTHORIZED=false`
- `RETRY_AUTHORIZED=false`
- `HOLDOUT_ACCESSED=false` / `SEALED_ACCESSED=false`
- `PROMOTION_ELIGIBLE=false`
- `ECONOMIC_VALIDITY_OFFLINE_GATE_PASS=false`

## Explicit non-actions

No further evaluation, runner reuse, holdout access, promotion, runtime,
Master V2 mutation, Double-Play authority change, parameter optimization,
CSRHR continue&#47;reuse&#47;mutation, path-efficiency retry, CLV pressure retry,
or Open Gap as next implementation candidate.

## Next step

`NEW_DISTINCT_RESEARCH_PROGRAM_OR_FULL_CANONICAL_SYSTEM_BINDING_OR_OTHER_EVIDENCE_CLASS_REQUIRES_OPERATOR_RATIFICATION`

Not `EXPLICIT_DEVELOPMENT_EVALUATION_GO`. No new research program selected here.

---
docs_token: DOCS_TOKEN_CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_V1_STRATEGY_IMPLEMENTATION_ONLY_V1
STATUS: STRATEGY_IMPLEMENTATION_PRESENT
scope: research, offline-only, non-authorizing, strategy-implementation
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---
