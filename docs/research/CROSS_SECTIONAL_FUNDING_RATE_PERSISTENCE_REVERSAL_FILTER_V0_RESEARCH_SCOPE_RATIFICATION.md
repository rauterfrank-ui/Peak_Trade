# Cross-Sectional Funding Rate Persistence Reversal Filter v0 — Research Scope Ratification

---
scope: governance, documentation-only, non-authorizing
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

> **Non-authorizing:** Ratifiziert ausschließlich die versionierte offline-only Research-Scope-Definition für `cross_sectional_funding_rate_persistence_reversal_filter&#47;v0` nach terminaler rank_delta/v0-Negative-Evidence. Keine Versioned-Binding-Ratifikation. Keine Economic Evaluation. Keine Runtime-Authority.

## A. Verdict

| Feld | Wert |
|---|---|
| `VERDICT` | `RESEARCH_SCOPE_DEFINITION_RATIFIED_NOT_EVALUATED_NOT_BINDING_RATIFIED` |
| `RECOMMENDED_SCOPE_ID` | `CROSS_SECTIONAL_FUNDING_RATE_PERSISTENCE_REVERSAL_FILTER_V0_RESEARCH_SCOPE_RATIFICATION` |
| `STRATEGY_ID` | `cross_sectional_funding_rate_persistence_reversal_filter` |
| `STRATEGY_VERSION` | `v0` |
| `GO_TOKEN` | `GO_RATIFY_CROSS_SECTIONAL_FUNDING_RATE_PERSISTENCE_REVERSAL_FILTER_V0_SCOPE_ONLY_NO_EVAL_NO_RUNTIME_AUTHORITY_V0` |
| `PARENT_TERMINAL_SCOPE_BUNDLE` | `rank_delta_v0_terminal_negative_evidence_and_next_scope_boundary_20260706T154311Z` |
| `TERMINALIZED_PARENT_STRATEGY` | `cross_sectional_funding_rate_rank_delta&#47;v0` |
| `MATERIAL_DIFFERENCE_PASS` | `true` |
| `FUTURES_ONLY_PASS` | `true` |
| `REUSE_FIRST_PASS` | `true` |
| `RESEARCH_SCOPE_DEFINITION_RATIFIED` | `true` |
| `BINDING_RATIFIED` | `false` |
| `EVALUATION_INFRASTRUCTURE_READY` | `false` |
| `ECONOMIC_EVALUATION_EXECUTED` | `false` |
| `PROMOTION_GRANTED` | `false` |
| `RUNTIME_AUTHORITY_TOUCHED` | `false` |
| `UNCHANGED_RETRY_ALLOWED` | `false` |
| `CORE_MUTATION_REQUIRED` | `false` |

## B. Material Difference Basis

| Terminal Surface | Persistence Reversal Filter v0 |
|---|---|
| rank_delta/v0 rank migration (FAIL) | **persistence duration + decay stability + reversal-risk gate** |
| dual_leg_spread/v1 level spread | single-slot persistence filter, no dual-leg |
| delta_momentum/v0 absolute delta | multi-epoch persistence, not rate delta |
| carry/v0 level extremum | persistence dynamics with explicit crowding filter |

## C. Scope Boundary

| Dimension | Status |
|---|---|
| Research scope definition | **Ratified in this pass** |
| Versioned binding ratification | **Not authorized — separate future GO** |
| Economic evaluation | **Not authorized** |
| Runtime authority | **Not touched** |
| Promotion | **Not granted** |

## D. Terminal Exclusions

Unchanged retry forbidden for: `cross_sectional_funding_rate_rank_delta&#47;v0` (terminal FAIL), `cross_sectional_funding_rate_dual_leg_spread&#47;v1`, `cross_sectional_funding_rate_delta_momentum&#47;v0`, `cross_sectional_funding_rate_carry&#47;v0`, `cross_sectional_relative_strength&#47;v0`, v1/v2 fleet, STEP29M/30A surfaces.

## E. Contract Flags

```
NEXT_SCOPE_REQUIRES_SEPARATE_EVALUATION_GO=true
EVALUATION_EXECUTED=false
RUNTIME_AUTHORITY_TOUCHED=false
PROMOTION_GRANTED=false
UNCHANGED_RETRY_ALLOWED=false
CORE_SYSTEM_MUTATION_ALLOWED=false
CANONICAL_TRADING_LOGIC_MUTATION_ALLOWED=false
MASTER_V2_MUTATION_ALLOWED=false
DOUBLE_PLAY_MUTATION_ALLOWED=false
RISK_SIZING_MUTATION_ALLOWED=false
SAFETY_RUNTIME_MUTATION_ALLOWED=false
NO_ORDERS=true
NO_CREDENTIALS=true
NO_SCHEDULER=true
NO_SHADOW=true
NO_PAPER=true
NO_TESTNET=true
NO_LIVE=true
```

## F. Forbidden in This Scope

- Economic evaluation, backtest, walk-forward, Monte Carlo, stress, parameter search
- Versioned binding ratification or binding completion
- Promotion, runtime rewire, shadow/paper/testnet/live
- Core system / canonical trading logic mutation
- Threshold lowering, parameter optimization, unchanged retry of terminal bindings

## G. Next Step

```
NEXT_STEP=SEPARATE_GO_REQUIRED_FOR_OFFLINE_ECONOMIC_EVALUATION_NO_RUNTIME_AUTHORITY
```

Separates Operator-GO erforderlich für versionierte Binding-Ratifikation und anschließende offline Economic Evaluation.
