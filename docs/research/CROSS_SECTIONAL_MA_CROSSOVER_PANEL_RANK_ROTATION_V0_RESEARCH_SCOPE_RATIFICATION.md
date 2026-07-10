# Cross-Sectional MA-Crossover Panel Rank Rotation v0 — Research Scope Ratification

---
scope: governance, documentation-only, non-authorizing
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

> **Non-authorizing:** Ratifiziert ausschließlich die versionierte offline-only Research-Scope-Definition für `cross_sectional_ma_crossover_panel_rank_rotation&#47;v0` unter Wiederverwendung der unveränderten kanonischen `ma_crossover&#47;v1`-Signal- und Parameterlogik in einer neuen Cross-Sectional-Panel-Kompositionsgeometrie. Keine Versioned-Binding-Ratifikation. Keine Dataset-Materialization. Keine Economic Evaluation. Keine Runtime-Authority.

## A. Verdict

| Feld | Wert |
|---|---|
| `VERDICT` | `RESEARCH_SCOPE_DEFINITION_RATIFIED_NOT_EVALUATED_NOT_BINDING_RATIFIED` |
| `RECOMMENDED_SCOPE_ID` | `CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_RESEARCH_SCOPE_RATIFICATION` |
| `STRATEGY_ID` | `cross_sectional_ma_crossover_panel_rank_rotation` |
| `STRATEGY_VERSION` | `v0` |
| `UNDERLYING_SIGNAL_BINDING` | `ma_crossover&#47;v1@inst-eth-usdt-perp` |
| `GO_TOKEN` | `GO_RATIFY_CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_RESEARCH_SCOPE_NO_EVAL_NO_RUNTIME_AUTHORITY_V1` |
| `SINGLE_INSTRUMENT_EVIDENCE` | `TERMINAL_NEGATIVE` |
| `PANEL_ARCHETYPE_EVIDENCE` | `NOT_PREVIOUSLY_EXECUTED` |
| `MATERIAL_DIFFERENCE_CONFIRMED` | `true` |
| `SIGNAL_FAMILY_MATERIAL_DIFFERENCE` | `false` |
| `FUTURES_ONLY_PASS` | `true` |
| `REUSE_FIRST_PASS` | `true` |
| `RESEARCH_SCOPE_DEFINITION_RATIFIED` | `true` |
| `RESEARCH_SCOPE_RATIFIED` | `true` |
| `BINDING_RATIFIED` | `false` |
| `DATASET_MATERIALIZED` | `false` |
| `EVALUATION_INFRASTRUCTURE_READY` | `false` |
| `ECONOMIC_EVALUATION_EXECUTED` | `false` |
| `PROMOTION_GRANTED` | `false` |
| `RUNTIME_AUTHORITY_TOUCHED` | `false` |
| `UNCHANGED_SINGLE_INSTRUMENT_RETRY_BLOCKED` | `true` |

## B. Material Difference Basis

| Achse | Single-Instrument Terminal | Panel Rank Rotation v0 |
|---|---|---|
| Portfolio aggregation | direct single-slot on `inst-eth-usdt-perp` | per-instrument MA-crossover score, cross-sectional rank, top-1 rotation |
| Universe | ETH-only | lifecycle-admissible OKX non-Bitcoin perpetual panel |
| Dataset | `inst-eth-usdt-perp` 1m bars | new PIT OKX PT1H lifecycle panel |
| Evaluation geometry | direct single-instrument backtest | multi-instrument rank rotation |
| Signal family | `ma_crossover&#47;v1` | **same underlying signal reused — not a new signal family** |

## C. Explicit Non-Claims

| Claim | Status |
|---|---|
| Signal untested | **false** — single-instrument evaluation executed and terminal negative |
| No prior single-instrument evaluation | **false** |
| New signal family | **false** |
| Terminal single-instrument evidence superseded | **false** |
| Dataset change alone sufficient | **false** |

## D. Scope Boundary

| Dimension | Status |
|---|---|
| Research scope definition | **Ratified in this pass** |
| Versioned binding ratification | **Not authorized — separate future GO** |
| Dataset materialization | **Not authorized — Phase 3 requires separate GO** |
| Economic evaluation | **Not authorized** |
| Runtime authority | **Not touched** |
| Promotion | **Not granted** |

## E. Panel Contract (Scope-Defined, Not Ratified)

| Feld | Wert |
|---|---|
| `UNIVERSE_POLICY` | `pit_okx_linear_usdt_non_bitcoin_perpetual_cross_sectional_universe&#47;v1` |
| `LIFECYCLE_POLICY` | `okx_production_instrument_lifecycle_historical_as_of_fail_closed.v1` |
| `PANEL_ID` | `pit_okx_linear_usdt_non_bitcoin_pt1h_panel` |
| `DATASET_SCHEMA` | `pit_okx_pt1h_panel_ohlcv_dataset_manifest_v1` |
| `BAR_INTERVAL` | `PT1H` |
| `MIN_INSTRUMENTS` | `5` |
| `SELECTION_POLICY` | `TOP1_BY_CANONICAL_MA_CROSSOVER_SCORE` |
| `MAX_ACTIVE_INSTRUMENTS` | `1` |
| `ROTATION_REQUIRES_RECONCILED_FLAT` | `true` |

## F. Signal and Parameter Contract

| Feld | Wert |
|---|---|
| `REUSE_EXISTING_MA_CROSSOVER_V1_SIGNAL_LOGIC` | `true` |
| `FAST_WINDOW` | `20` |
| `SLOW_WINDOW` | `50` |
| `PRICE_COL` | `close` |
| `SIGNAL_LOGIC_CHANGE_ALLOWED` | `false` |
| `PARAMETER_OPTIMIZATION_ALLOWED` | `false` |
| `THRESHOLD_RELAXATION_ALLOWED` | `false` |
| `POLICY_RESCUE_ALLOWED` | `false` |

## G. Phase 3 Precondition (Register Only)

| Feld | Wert |
|---|---|
| `PHASE3_GO_TOKEN_TO_REGISTER_ONLY` | `GO_BOUNDED_OKX_PRODUCTION_LIFECYCLE_SOURCE_REGISTRATION_AND_PT1H_PANEL_OHLCV_INGEST_V0` |
| `NEXT_ACTION` | `PHASE3_DATASET_MATERIALIZATION_REQUIRES_SEPARATE_GO` |

## H. Contract Flags

```
NEXT_SCOPE_REQUIRES_SEPARATE_EVALUATION_GO=true
EVALUATION_EXECUTED=false
DATASET_MATERIALIZED=false
RUNTIME_AUTHORITY_TOUCHED=false
PROMOTION_GRANTED=false
UNCHANGED_SINGLE_INSTRUMENT_RETRY_BLOCKED=true
CORE_SYSTEM_MUTATION_ALLOWED=false
CANONICAL_TRADING_LOGIC_MUTATION_ALLOWED=false
NO_ORDERS=true
NO_CREDENTIALS=true
NO_SCHEDULER=true
NO_SHADOW=true
NO_PAPER=true
NO_TESTNET=true
NO_LIVE=true
```

## I. Authoritative Evidence References

| Bundle | Role |
|---|---|
| `planning&#47;cross_sectional_multi_instrument_futures_panel_scope_discovery_and_ratification_prep_v0_20260710T085834Z` | Phase 1 discovery |
| `planning&#47;cross_sectional_ma_crossover_panel_scope_discovery_contradiction_adjudication_and_corrected_ratification_prep_v0_20260710T090302Z` | Adjudication and corrected prep |
| `economic_evaluation&#47;bounded_step29m_ma_crossover_v1_post_binding_fix_economic_evaluation_recovery_single_run_v0_20260702T012057Z` | Terminal single-instrument evaluation |
| `economic_evaluation&#47;bounded_step29m_ma_crossover_v1_economic_policy_fail_closeout_and_candidate_decision_read_only_v0_20260702T012719Z` | Terminal single-instrument closeout |

## J. Config References

| Artifact | Path |
|---|---|
| Scope ratification | `config&#47;research&#47;cross_sectional_ma_crossover_panel_rank_rotation_v0_research_scope_ratification_v1.json` |
| Panel binding | `config&#47;research&#47;cross_sectional_ma_crossover_panel_rank_rotation_v0_panel_universe_dataset_binding_v0.json` |
| Material difference | `config&#47;research&#47;cross_sectional_ma_crossover_panel_rank_rotation_v0_material_difference_and_non_claim_contract_v0.json` |
| Unchanged retry block | `config&#47;research&#47;cross_sectional_ma_crossover_panel_rank_rotation_v0_unchanged_retry_and_near_duplicate_block_v0.json` |
| Phase 3 precondition | `config&#47;research&#47;cross_sectional_ma_crossover_panel_rank_rotation_v0_phase3_precondition_contract_v0.json` |
