# Cross-Sectional Funding Rate Dual-Leg Spread v1 — Binding Ratification Prep

---
scope: governance, documentation-only, non-authorizing
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

> **Non-authorizing:** Ratifiziert ausschließlich versionierte offline-only Research-Bindings für `cross_sectional_funding_rate_dual_leg_spread&#47;v1` nach terminaler PR4925-Negative-Evidence und Material-Scope-Definition. Keine Economic Evaluation. Keine Runtime-Authority.

## A. Verdict

| Feld | Wert |
|---|---|
| `VERDICT` | `SCOPE_BINDING_RATIFICATION_PREP_COMPLETE_NOT_EVALUATED` |
| `RECOMMENDED_SCOPE_ID` | `CROSS_SECTIONAL_FUNDING_RATE_DUAL_LEG_SPREAD_V1_OFFLINE_ECONOMIC_EVALUATION_RATIFICATION_PREP` |
| `STRATEGY_ID` | `cross_sectional_funding_rate_dual_leg_spread` |
| `STRATEGY_VERSION` | `v1` |
| `GO_TOKEN` | `GO_CROSS_SECTIONAL_FUNDING_RATE_DUAL_LEG_SPREAD_V1_BINDING_RATIFICATION_NO_EVAL_NO_RUNTIME_AUTHORITY_V0` |
| `PARENT_SCOPE_DEFINITION_BUNDLE` | `post_pr4925_new_material_cross_sectional_funding_rate_dual_leg_spread_v1_scope_definition_20260706T134500Z` |
| `PARENT_PR4925_NEGATIVE_TERMINALIZATION` | `pr4925_cross_sectional_funding_rate_delta_momentum_v0_negative_evidence_terminalization_20260706T134445Z` |
| `MATERIAL_DIFFERENCE_PASS` | `true` |
| `FUTURES_ONLY_PASS` | `true` |
| `REUSE_FIRST_PASS` | `true` |
| `BINDING_RATIFIED` | `true` |
| `EVALUATION_INFRASTRUCTURE_READY` | `false` |
| `ECONOMIC_EVALUATION_EXECUTED` | `false` |
| `PROMOTION_ADMISSIBLE` | `false` |
| `RUNTIME_REWIRE_ADMISSIBLE` | `false` |
| `CORE_MUTATION_REQUIRED` | `false` |

## B. Material Difference Basis vs PR4925

| PR4925 `cross_sectional_funding_rate_delta_momentum&#47;v0` | Dual-leg spread v1 |
|---|---|
| Funding-rate **delta** extremum ranking | Funding-rate **level** spread |
| `funding_delta_extremes_single_leg_rotation_v0` | `funding_level_spread_dual_leg_simultaneous_v1` |
| `dual_leg_simultaneous_forbidden=true` | `dual_leg_simultaneous_required=true` |
| Single-slot rotation (1 leg/epoch) | Simultaneous long-min + short-max book |

## C. Required Bindings (All Ratified)

| Dimension | Owner |
|---|---|
| strategy_id / strategy_version | `cross_sectional_funding_rate_dual_leg_spread` / `v1` |
| parameter_binding | `config/research/cross_sectional_funding_rate_dual_leg_spread_v1_versioned_research_binding_v0.json` |
| dataset_binding | `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1` / `extended_chronological_with_funding_v1` |
| period_binding | `pit_cross_sectional_research_chronological_holdout_v1` |
| instrument_binding | `pit_okx_linear_usdt_non_bitcoin_perpetual_universe_manifest_v1` |
| fee/slippage/funding/execution | `backtest_fee_taker_symmetric_v0`, `backtest_slippage_symmetric_v0`, `backtest_funding_perpetual_interval_v1`, `backtest_execution_v0` |
| economic_policy_binding | `economic_validity_policy_v1`, `policy_lowering_forbidden=true` |
| materialization script | `scripts/ops/materialize_cross_sectional_funding_rate_dual_leg_spread_v1_scope_definition_and_binding_ratification_v0.py` |

## D. Terminal Exclusions

Unchanged retry forbidden for: `cross_sectional_funding_rate_delta_momentum&#47;v0` (PR4925), `cross_sectional_funding_rate_carry&#47;v0`, `cross_sectional_relative_strength&#47;v0`, v1/v2 fleet, STEP29M/30A surfaces.

## E. Allowed After Separate Execution GO

- Offline backtest, walk-forward, Monte Carlo, stress, parameter sensitivity (requires future runner/harness implementation)
- EconomicViabilityEvidenceV1 materialization

## F. Forbidden

- Economic evaluation in this ratification pass
- Promotion, runtime rewire, shadow/paper/testnet/live
- Core system / canonical trading logic mutation
- Threshold lowering, parameter optimization, PR4925 unchanged retry

## G. Next Step

```
SEPARATE_GO_REQUIRED_FOR_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_NO_RUNTIME_AUTHORITY_V0
```
