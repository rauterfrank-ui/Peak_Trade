# Cross-Sectional Open Interest Z-Score Reversion v0 Versioned Hypothesis Binding v0

## Scope classification

`BOUNDED_FUTURES_ONLY_VERSIONED_HYPOTHESIS_BINDING_V0`

Research-only binding for `cross_sectional_open_interest_zscore_reversion&#47;v0` (`RESEARCH_SCOPE=cross_sectional_open_interest_zscore_reversion&#47;v0`). Binds a distinct cross-sectional open-interest z-score mean-reversion hypothesis before any economic evaluation.

RESEARCH_SCOPE: cross_sectional_open_interest_zscore_reversion&#47;v0

## Operator GO

`GO_CROSS_SECTIONAL_OPEN_INTEREST_ZSCORE_REVERSION_V0_VERSIONED_HYPOTHESIS_BINDING_IMPLEMENTATION_V0`

## Non-authorizing constraints

- No economic evaluation
- No backtest, walk-forward, Monte Carlo, or stress execution
- No runtime, scheduler, orders, credentials, or authority effect
- No reuse of prior level-rank or delta-rank bindings unchanged
- No threshold relaxation or policy rescue
- Zero panel dispersion fails closed to FLAT

## Material difference from prior scopes

| Field | Prior level-rank | Prior delta-rank | New (z-score reversion) |
|---|---|---|---|
| Feature | `point_in_time_open_interest_level` | `delta_or_change_in_open_interest` | `cross_sectional_open_interest_zscore_at_lagged_observation` |
| Ranking input | Lagged OI level | OI delta over lookback K | Population cross-sectional z-score at lag |
| Mechanism | Positioning crowding level extremes | Positioning change extremes | Crowding z-score mean-reversion extremes |
| Selection mode | `open_interest_level_extremes_single_leg_rotation_v0` | `open_interest_delta_rank_extremes_single_leg_rotation_v0` | `open_interest_zscore_reversion_extremes_single_leg_rotation_v0` |

## Canonical owners

| Surface | Owner |
|---|---|
| Hypothesis binding | `src/research/cross_sectional_open_interest_zscore_reversion_v0_versioned_hypothesis_binding_v0.py` |
| PIT semantics | `src/research/cross_sectional_open_interest_zscore_reversion_v0_pit_semantics_contract_v0.py` |
| Scoring | `src/research/cross_sectional_open_interest_zscore_reversion_scoring_v0.py` |
| Orchestrator | `src/research/cross_sectional_open_interest_zscore_reversion_single_slot_research_orchestrator_v0.py` |
| Dataset panel | `okx_self_accumulated_forward_open_interest_bound_panel_dataset_materialization.v0` |
| Config | `config/research/cross_sectional_open_interest_zscore_reversion_v0_versioned_hypothesis_binding_v0.json` |
| Materializer | `scripts/research/materialize_cross_sectional_open_interest_zscore_reversion_v0_versioned_hypothesis_binding_v0.py` |

## Provenance references

- Source evidence: terminal classification bundle `20260712T135127Z`
- Prior level-rank terminal baseline preserved
- Prior delta-rank inconclusive baseline preserved
- Superseding integrity attestation: PR #5121 attestation config

## Next recommended scope

`CROSS_SECTIONAL_OPEN_INTEREST_ZSCORE_REVERSION_V0_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0`

Requires separate operator GO after infrastructure merge. Economic evaluation not executed in infrastructure scope.
