# Cross-Sectional Open Interest Level Rank v0 Versioned Hypothesis Binding v0

## Scope classification

`BOUNDED_FUTURES_ONLY_VERSIONED_HYPOTHESIS_BINDING_V0`

Research-only binding for `cross_sectional_open_interest_level_rank/v0` (`RESEARCH_SCOPE=cross_sectional_open_interest_level_rank/v0`). Binds a distinct
point-in-time open-interest level ranking hypothesis before any economic evaluation.

## Operator GO

`GO_CROSS_SECTIONAL_OPEN_INTEREST_LEVEL_RANK_V0_VERSIONED_HYPOTHESIS_BINDING_IMPLEMENTATION_V0`

## Non-authorizing constraints

- No economic evaluation
- No backtest, walk-forward, Monte Carlo, or stress execution
- No runtime, scheduler, orders, credentials, or authority effect
- No reuse of prior delta-rank binding unchanged
- No threshold relaxation or policy rescue

## Material difference from prior scope

| Field | Prior (`cross_sectional_open_interest_delta_rank&#47;v0`) | New (`cross_sectional_open_interest_level_rank&#47;v0`) |
|---|---|---|
| Feature | `delta_or_change_in_open_interest` | `point_in_time_open_interest_level` |
| Ranking input | OI delta over lookback K | Lagged OI level |
| Mechanism | Positioning change extremes | Positioning crowding level extremes |
| Selection mode | `open_interest_delta_rank_extremes_single_leg_rotation_v0` | `open_interest_level_extremes_single_leg_rotation_v0` |

## Canonical owners

| Surface | Owner |
|---|---|
| Hypothesis binding | `src/research/cross_sectional_open_interest_level_rank_v0_versioned_hypothesis_binding_v0.py` |
| PIT semantics | `src/research/cross_sectional_open_interest_level_rank_v0_pit_semantics_contract_v0.py` |
| Scoring | `src/research/cross_sectional_open_interest_level_rank_scoring_v0.py` |
| Dataset panel | `okx_self_accumulated_forward_open_interest_bound_panel_dataset_materialization.v0` |
| Config | `config/research/cross_sectional_open_interest_level_rank_v0_versioned_hypothesis_binding_v0.json` |
| Materializer | `scripts/research/materialize_cross_sectional_open_interest_level_rank_v0_versioned_hypothesis_binding_v0.py` |
| Evaluation infrastructure | `src/research/cross_sectional_open_interest_level_rank_v0_offline_economic_evaluation_execution_v0.py` |
| Ops runner | `scripts/ops/run_cross_sectional_open_interest_level_rank_v0_offline_economic_evaluation_execution_v0.py` |

## Canonical entry point

`run_full_offline_economic_evaluation_v0` in
`src/research/cross_sectional_open_interest_level_rank_v0_offline_economic_evaluation_execution_v0.py`

Infrastructure-only in this slice. No economic evaluation executed.

## Provenance references

- Prior terminal baseline: inconclusive baseline evidence bundle (integrity RC=1 preserved)
- Superseding integrity attestation: PR #5121 attestation config
- Provisional Rank-1 source: downstream distinct-hypothesis ranking evidence

## Next recommended scope

`CROSS_SECTIONAL_OPEN_INTEREST_LEVEL_RANK_V0_OFFLINE_ECONOMIC_EVALUATION_REEVALUATION_V0`

Requires separate operator GO after infrastructure merge. Economic evaluation not executed in infrastructure scope.
