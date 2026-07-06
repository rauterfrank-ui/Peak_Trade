# Cross-Sectional Funding Rate Rank-Delta v0 — Binding Ratification Prep

---
scope: governance, documentation-only, non-authorizing
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

> **Non-authorizing:** Ratifiziert ausschließlich versionierte offline-only Research-Bindings für `cross_sectional_funding_rate_rank_delta&#47;v0` nach terminaler dual_leg_spread/v1-Negative-Evidence und Material-Scope-Definition. Keine Economic Evaluation. Keine Runtime-Authority.

## A. Verdict

| Feld | Wert |
|---|---|
| `VERDICT` | `SCOPE_BINDING_RATIFICATION_PREP_COMPLETE_NOT_EVALUATED` |
| `RECOMMENDED_SCOPE_ID` | `CROSS_SECTIONAL_FUNDING_RATE_RANK_DELTA_V0_OFFLINE_ECONOMIC_EVALUATION_RATIFICATION_PREP` |
| `STRATEGY_ID` | `cross_sectional_funding_rate_rank_delta` |
| `STRATEGY_VERSION` | `v0` |
| `GO_TOKEN` | `GO_CROSS_SECTIONAL_FUNDING_RATE_RANK_DELTA_V0_BINDING_RATIFICATION_NO_EVAL_NO_RUNTIME_AUTHORITY_V0` |
| `PARENT_TERMINAL_SCOPE_BUNDLE` | `dual_leg_spread_v1_terminal_negative_evidence_and_next_material_scope_20260706T145350Z` |
| `MATERIAL_DIFFERENCE_PASS` | `true` |
| `FUTURES_ONLY_PASS` | `true` |
| `REUSE_FIRST_PASS` | `true` |
| `BINDING_RATIFIED` | `true` |
| `EVALUATION_INFRASTRUCTURE_READY` | `false` |
| `ECONOMIC_EVALUATION_EXECUTED` | `false` |
| `PROMOTION_ADMISSIBLE` | `false` |
| `RUNTIME_REWIRE_ADMISSIBLE` | `false` |
| `CORE_MUTATION_REQUIRED` | `false` |

## B. Material Difference Basis

| Terminal Surface | Rank-Delta v0 |
|---|---|
| dual_leg_spread/v1 level spread dual-leg | cross-sectional **rank migration** single-slot |
| delta_momentum/v0 absolute funding delta | **rank_delta** = rank(t) - rank(t-K) |
| carry/v0 level extremum | rank dynamics, not static level |

## C. Required Bindings (All Ratified)

| Dimension | Owner |
|---|---|
| strategy_id / strategy_version | `cross_sectional_funding_rate_rank_delta` / `v0` |
| parameter_binding | `config/research/cross_sectional_funding_rate_rank_delta_v0_versioned_research_binding_v0.json` |
| dataset_binding | `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1` / `extended_chronological_with_funding_v1` |
| period_binding | `pit_cross_sectional_research_chronological_holdout_v1` |
| instrument_binding | `pit_okx_linear_usdt_non_bitcoin_perpetual_universe_manifest_v1` |
| fee/slippage/funding/execution | `backtest_fee_taker_symmetric_v0`, `backtest_slippage_symmetric_v0`, `backtest_funding_perpetual_interval_v1`, `backtest_execution_v0` |
| economic_policy_binding | `economic_validity_policy_v1`, `policy_lowering_forbidden=true` |
| materialization script | `scripts/ops/materialize_cross_sectional_funding_rate_rank_delta_v0_scope_definition_and_binding_ratification_v0.py` |

## D. Terminal Exclusions

Unchanged retry forbidden for: `cross_sectional_funding_rate_dual_leg_spread&#47;v1`, `cross_sectional_funding_rate_delta_momentum&#47;v0`, `cross_sectional_funding_rate_carry&#47;v0`, `cross_sectional_relative_strength&#47;v0`, v1/v2 fleet, STEP29M/30A surfaces.

## E. Allowed After Separate Execution GO

- Offline backtest, walk-forward, Monte Carlo, stress, parameter sensitivity (requires future runner/harness implementation)
- EconomicViabilityEvidenceV1 materialization

## F. Forbidden

- Economic evaluation in this ratification pass
- Promotion, runtime rewire, shadow/paper/testnet/live
- Core system / canonical trading logic mutation
- Threshold lowering, parameter optimization, unchanged retry of terminal bindings

## G. Next Step

```
SEPARATE_GO_REQUIRED_FOR_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_NO_RUNTIME_AUTHORITY_V0
```
