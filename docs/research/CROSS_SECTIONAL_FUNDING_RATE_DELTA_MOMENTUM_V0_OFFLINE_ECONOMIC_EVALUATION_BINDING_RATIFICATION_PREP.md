# Cross-Sectional Funding Rate Delta Momentum v0 — Binding Ratification Prep

---
scope: governance, documentation-only, non-authorizing
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

> **Non-authorizing:** Ratifiziert ausschließlich versionierte offline-only Research-Bindings für `cross_sectional_funding_rate_delta_momentum&#47;v0` nach v2-Fleet-Terminalisierung und Discovery-Bundle. Keine Economic Evaluation. Keine Runtime-Authority.

## A. Verdict

| Feld | Wert |
|---|---|
| `VERDICT` | `SCOPE_BINDING_RATIFICATION_PREP_COMPLETE_NOT_EVALUATED` |
| `RECOMMENDED_SCOPE_ID` | `CROSS_SECTIONAL_FUNDING_RATE_DELTA_MOMENTUM_V0_OFFLINE_ECONOMIC_EVALUATION_RATIFICATION_PREP` |
| `STRATEGY_ID` | `cross_sectional_funding_rate_delta_momentum` |
| `STRATEGY_VERSION` | `v0` |
| `GO_TOKEN` | `GO_RATIFY_CROSS_SECTIONAL_FUNDING_RATE_DELTA_MOMENTUM_V0_VERSIONED_OFFLINE_RESEARCH_BINDINGS_NO_EVAL_NO_RUNTIME_AUTHORITY_V0` |
| `PARENT_DISCOVERY_BUNDLE` | `new_versioned_offline_research_scope_discovery_material_difference_required_20260706T131920Z` |
| `PARENT_TERMINALIZATION_BUNDLE` | `v2_fleet_terminalization_and_next_research_scope_boundary_20260706T131703Z` |
| `MATERIAL_DIFFERENCE_PASS` | `true` |
| `FUTURES_ONLY_PASS` | `true` |
| `REUSE_FIRST_PASS` | `true` |
| `EVALUATION_READY` | `true` |
| `ECONOMIC_EVALUATION_EXECUTED` | `false` |
| `PROMOTION_ADMISSIBLE` | `false` |
| `RUNTIME_REWIRE_ADMISSIBLE` | `false` |
| `CORE_MUTATION_REQUIRED` | `false` |

## B. Material Difference Basis

Nach terminaler v2-Fleet (`trend_following&#47;v2`, `bollinger_bands&#47;v2`, `momentum_1h&#47;v2` = ROBUSTNESS_FAILED) ist dieser Scope der einzige admissible Discovery-Kandidat mit:

- **Anderer Signal-Semantik:** Funding-Rate-**Delta**-Ranking über Panel, nicht Single-Instrument-Preis-Signal
- **Anderem Universe-Modell:** Cross-sectional Panel-Rotation (118 Members), nicht narrow ETH-PERP Fleet-Binding
- **Eigenen Digests:** `config_digest`, `data_digest`, `implementation_digest` distinct von failed v2

## C. Required Bindings (All Ratified)

| Dimension | Owner |
|---|---|
| strategy_id / strategy_version | `cross_sectional_funding_rate_delta_momentum` / `v0` |
| parameter_binding | `config/research/cross_sectional_funding_rate_delta_momentum_v0_versioned_research_binding_v0.json` |
| dataset_binding | `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1` / `extended_chronological_with_funding_v1` |
| period_binding | `pit_cross_sectional_research_chronological_holdout_v1` |
| instrument_binding | `pit_okx_linear_usdt_non_bitcoin_perpetual_universe_manifest_v1` |
| fee/slippage/funding/execution | `backtest_fee_taker_symmetric_v0`, `backtest_slippage_symmetric_v0`, `backtest_funding_perpetual_interval_v1`, `backtest_execution_v0` |
| economic_policy_binding | `economic_validity_policy_v1`, `policy_lowering_forbidden=true` |
| runner_binding | `scripts/ops/run_cross_sectional_funding_rate_delta_momentum_v0_offline_economic_evaluation_execution_v0.py` |
| harness_binding | `src/research/cross_sectional_funding_rate_delta_momentum_v0_offline_economic_evaluation_execution_v0.py` |

## D. Terminal Exclusions

Unchanged retry forbidden for: v2 fleet, v1 fleet, `cross_sectional_relative_strength&#47;v0`, `cross_sectional_funding_rate_carry&#47;v0`, STEP29M/30A surfaces, composite breakout line.

## E. Allowed After Separate Execution GO

- Offline backtest, walk-forward, Monte Carlo, stress, parameter sensitivity (cost grid only)
- EconomicViabilityEvidenceV1 materialization

## F. Forbidden

- Economic evaluation in this ratification pass
- Promotion, runtime rewire, shadow/paper/testnet/live
- Core system / canonical trading logic mutation
- Threshold lowering, parameter optimization, unchanged retry

## G. Next Step

```
SEPARATE_GO_REQUIRED_FOR_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_NO_RUNTIME_AUTHORITY_V0
```
