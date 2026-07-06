# Cross-Sectional Funding Rate Dispersion Z-Score Reversion v0 — Research Scope Ratification

---
scope: governance, documentation-only, non-authorizing
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

> **Non-authorizing:** Ratifiziert ausschließlich die versionierte offline-only Research-Scope-Definition für `cross_sectional_funding_rate_dispersion_zscore_reversion/v0` nach terminaler persistence_reversal_filter/v0-Negative-Evidence. Keine Versioned-Binding-Ratifikation. Keine Economic Evaluation. Keine Runtime-Authority.

## A. Verdict

| Feld | Wert |
|---|---|
| `VERDICT` | `RESEARCH_SCOPE_DEFINITION_RATIFIED_NOT_EVALUATED_NOT_BINDING_RATIFIED` |
| `RECOMMENDED_SCOPE_ID` | `CROSS_SECTIONAL_FUNDING_RATE_DISPERSION_ZSCORE_REVERSION_V0_RESEARCH_SCOPE_RATIFICATION` |
| `STRATEGY_ID` | `cross_sectional_funding_rate_dispersion_zscore_reversion` |
| `STRATEGY_VERSION` | `v0` |
| `GO_TOKEN` | `GO_DEFINE_NEXT_MATERIAL_FUNDING_RATE_RESEARCH_HYPOTHESIS_SCOPE_AFTER_PERSISTENCE_REVERSAL_FILTER_V0_FAIL_NO_EVAL_NO_RUNTIME_AUTHORITY_V0` |
| `PARENT_TERMINAL_SCOPE_BUNDLE` | `pr4934_persistence_reversal_filter_v0_negative_evidence_merge_closeout_20260706T164420Z` |
| `TERMINALIZED_PARENT_STRATEGY` | `cross_sectional_funding_rate_persistence_reversal_filter/v0` |
| `TERMINALIZED_PARENT_BINDING_DIGEST` | `4355f213e0325c7e5ec87013693c91ea693b1bee5325959c1380888b7a31a533` |
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

## B. Hypothesis

When cross-sectional funding-rate **dispersion** across the panel exceeds a minimum threshold (panel disagreement regime), mean-revert the instrument with the largest **standardized deviation** from the panel mean funding rate (z-score extremum). Single-slot rotation selects the leg with larger |z-score| only when the dispersion gate passes.

## C. Material Difference Basis

| Terminal Surface | Dispersion Z-Score Reversion v0 |
|---|---|
| rank_delta/v0 rank migration (FAIL) | **panel dispersion gate + z-score**, not rank ordinal migration |
| dual_leg_spread/v1 level spread (FAIL) | **single-slot z-score**, no dual-leg simultaneous spread |
| persistence_reversal_filter/v0 (FAIL) | **dispersion regime + z-score**, not persistence/decay/reversal gate |
| delta_momentum/v0 absolute delta | level z-score vs rate-delta extremum |
| carry/v0 level extremum | dispersion-gated z-score vs static carry |

## D. Scope Boundary

| Dimension | Status |
|---|---|
| Research scope definition | **Ratified in this pass** |
| Versioned binding ratification | **Not authorized — separate future GO** |
| Economic evaluation | **Not authorized** |
| Runtime authority | **Not touched** |
| Promotion | **Not granted** |

## E. Terminal Exclusions

Unchanged retry forbidden for: `cross_sectional_funding_rate_persistence_reversal_filter/v0` (terminal FAIL, binding digest `4355f213…`), `cross_sectional_funding_rate_rank_delta/v0`, `cross_sectional_funding_rate_dual_leg_spread/v1`, `cross_sectional_funding_rate_delta_momentum/v0`, `cross_sectional_funding_rate_carry/v0`, `cross_sectional_relative_strength/v0`, v1/v2 fleet, STEP29M/30A surfaces.

## F. Contract Flags

```
NEXT_SCOPE_REQUIRES_SEPARATE_EVALUATION_GO=true
EVALUATION_EXECUTED=false
RUNTIME_AUTHORITY_TOUCHED=false
PROMOTION_GRANTED=false
UNCHANGED_RETRY_ALLOWED=false
TERMINALIZED_PARENT_BINDING_DIGEST_UNCHANGED_RETRY_FORBIDDEN=true
```

## G. Next Step

```
SEPARATE_GO_REQUIRED_FOR_VERSIONED_BINDING_RATIFICATION_AND_OFFLINE_ECONOMIC_EVALUATION_NO_RUNTIME_AUTHORITY_V0
```
