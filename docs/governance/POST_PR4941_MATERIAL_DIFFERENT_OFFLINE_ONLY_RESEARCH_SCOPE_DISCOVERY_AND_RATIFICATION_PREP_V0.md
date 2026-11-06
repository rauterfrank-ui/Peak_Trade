# Post-PR4941 Material-Different Offline-Only Research Scope Discovery and Ratification Prep v0

---
docs_token: DOCS_TOKEN_POST_PR4941_MATERIAL_DIFFERENT_OFFLINE_ONLY_RESEARCH_SCOPE_DISCOVERY_AND_RATIFICATION_PREP_V0
STATUS: SCOPE_DISCOVERY_AND_RATIFICATION_PREP_COMPLETE
scope: governance, documentation-only, non-authorizing
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

> **Non-authorizing:** Discovery und Ratifikation-Vorbereitung für genau einen material-differenten offline-only Research-Scope nach manifest-verifizierter PR4939/PR4940 Terminal-Negative-Evidence. Keine Economic Evaluation. Keine Binding-Ratifikation in diesem Scope. Kein Same-Binding-Retry, keine Parameterrettung, keine Runtime-Authority. Market-Airport ausgeschlossen.

## A. Verdict

| Feld | Wert |
|---|---|
| `VERDICT` | `SCOPE_DISCOVERY_AND_RATIFICATION_PREP_COMPLETE` |
| `PROCESS_CLASSIFICATION` | `MATERIAL_DIFFERENT_OFFLINE_ONLY_RESEARCH_SCOPE_DISCOVERY_AND_RATIFICATION_PREP` |
| `SCOPE_CLASSIFICATION` | `PR4941_MATERIAL_DIFFERENT_OFFLINE_ONLY_RESEARCH_SCOPE_DISCOVERY_AND_RATIFICATION_PREP_NO_EVAL_NO_RUNTIME_AUTHORITY_V0` |
| `OPERATOR_GO` | `GO_PR4941_MATERIAL_DIFFERENT_OFFLINE_ONLY_RESEARCH_SCOPE_DISCOVERY_AND_RATIFICATION_PREP_NO_EVAL_NO_RUNTIME_AUTHORITY_V0` |
| `GO_TOKEN_CONSUMPTION` | `CONSUMED_ONCE_FOR_DISCOVERY_AND_RATIFICATION_PREP_ONLY` |
| `CURRENT_BASELINE_PR` | `4941` |
| `BASE_HEAD` | `f75e32a19f6708c8be1ab313636a1f0047e6cab1` |
| `PARENT_PR4939_CLOSEOUT_DIR` | `/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/pr4939_final_research_fleet_negative_evidence_terminalization_merge_closeout_20260706T181802Z` |
| `PARENT_PR4939_CLOSEOUT_MANIFEST_VERIFY_RC` | `0` |
| `PARENT_PR4940_CLOSEOUT_DIR` | `/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/pr4940_final_fleet_terminalization_and_next_material_research_boundary_merge_closeout_20260706T182841Z` |
| `PARENT_PR4940_CLOSEOUT_MANIFEST_VERIFY_RC` | `0` |
| `EVIDENCE_CLASS_ID` | `POST_PR4941_MATERIAL_DIFFERENT_OFFLINE_ONLY_RESEARCH_SCOPE_DISCOVERY_AND_RATIFICATION_PREP_V0` |
| `SCOPE_ID` | `POST_PR4941_MATERIAL_DIFFERENT_OFFLINE_ONLY_RESEARCH_SCOPE_DISCOVERY_AND_RATIFICATION_PREP_V0` |
| `FINAL_RESEARCH_FLEET` | `trend_following,bollinger_bands,momentum_1h` |
| `FINAL_RESEARCH_FLEET_STATUS` | `NEGATIVE_EVIDENCE_TERMINAL_FOR_UNCHANGED_BINDINGS` |
| `AGGREGATE_FLEET_VERDICT` | `FLEET_ECONOMIC_VALIDITY_FAIL` |
| `ECONOMIC_VALIDITY_OFFLINE_GATE_PASS` | `false` |
| `NEGATIVE_EVIDENCE_TERMINAL_FOR_UNCHANGED_BINDINGS` | `true` |
| `SELECTED_NEXT_SCOPE_BOUNDARY` | `cross_sectional_realized_volatility_rank_rotation&#47;v0` |
| `SELECTED_STRATEGY_ID` | `cross_sectional_realized_volatility_rank_rotation` |
| `SELECTED_STRATEGY_VERSION` | `v0` |
| `MATERIAL_DIFFERENCE_AXES` | `signal_family,target_phenomenon,data_feature_class,portfolio_aggregation,entry_exit_hypothesis,universe_ranking` |
| `REUSE_FIRST_DECISION` | `REUSE_PIT_CROSS_SECTIONAL_PANEL_DATASET_AND_RELATIVE_STRENGTH_RANKING_SEMANTICS_PATTERN_WITH_NARROW_REALIZED_VOL_FEATURE_ADAPTER_ONLY` |
| `FUTURES_ONLY` | `true` |
| `BITCOIN_DIRECTION_ALLOWED` | `false` |
| `MARKET_AIRPORT_EXCLUDED` | `true` |
| `SCOPE_DISCOVERY_AND_RATIFICATION_PREP_ONLY` | `true` |
| `RATIFICATION_PREP_ONLY` | `true` |
| `EVALUATION_EXECUTED` | `false` |
| `ECONOMIC_EVALUATION_AUTHORIZED` | `false` |
| `RUNTIME_AUTHORITY_TOUCHED` | `false` |
| `PROMOTION_GRANTED` | `false` |
| `UNCHANGED_RETRY_ALLOWED` | `false` |
| `REQUIRED_NEXT_GO_FOR_SCOPE_RATIFICATION` | `GO_RATIFY_CROSS_SECTIONAL_REALIZED_VOLATILITY_RANK_ROTATION_V0_RESEARCH_SCOPE_NO_EVAL_NO_RUNTIME_AUTHORITY_V0` |
| `runtime_effect` | `NONE` |
| `authority_effect` | `NONE` |
| `economic_evaluation_effect` | `NONE` |
| `trading_effect` | `NONE` |

**Authoritative owners (reuse, nicht ersetzen):**

- Scope config: `config/research/post_pr4941_material_different_offline_only_research_scope_discovery_and_ratification_prep_v0.json`
- Materialization owner: `scripts/research/post_pr4941_material_different_offline_only_research_scope_discovery_and_ratification_prep_v0.py`
- Validation owner: `src/research/post_pr4941_material_different_offline_only_research_scope_discovery_and_ratification_prep_v0.py`
- Parent PR4940 boundary: `docs/governance/POST_PR4939_FINAL_RESEARCH_FLEET_NEGATIVE_EVIDENCE_TERMINALIZATION_AND_NEXT_MATERIAL_RESEARCH_BOUNDARY_V0.md`
- Progress registry: `docs/governance/PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md`

## B. Excluded Failed Bindings (bindend)

| Binding | Terminal Verdict | Retry Allowed |
|---|---|---|
| `trend_following&#47;v1` | `FAIL` | `false` |
| `bollinger_bands&#47;v1` | `FAIL` | `false` |
| `momentum_1h&#47;v1` | `FAIL` | `false` |

Keine unveränderten Final-Fleet-Binding-Reexecutions. Keine Threshold-Lowering. Keine Parameter-Drift-Retries.

## C. Candidate Family Inventory

| Candidate Family | Disposition | Exclusion / Selection Rationale |
|---|---|---|
| `trend_following&#47;v1` | `EXCLUDED_TERMINAL` | unchanged final fleet binding terminal FAIL |
| `bollinger_bands&#47;v1` | `EXCLUDED_TERMINAL` | unchanged final fleet binding terminal FAIL |
| `momentum_1h&#47;v1` | `EXCLUDED_TERMINAL` | unchanged final fleet binding terminal FAIL |
| `cross_sectional_funding_rate_score_family` | `EXCLUDED_TERMINAL` | fleet `COMPLETE_NO_PASS`, score family exhausted |
| `cross_sectional_relative_strength&#47;v0` | `EXCLUDED_TERMINAL` | price-return rank axis terminal `COMPLETE_FAIL` |
| `okx_full_panel_cross_sectional_ranking_archetype` | `EXCLUDED_TERMINAL` | ranking archetype terminal negative evidence |
| `v2_fleet_archetype_retries` | `EXCLUDED_NEAR_DUPLICATE` | near-duplicate of failed v1 trend/mr/momentum |
| `panel_skewness_reversion` | `EXCLUDED_NEAR_DUPLICATE` | same panel mean-reversion higher-moment family |
| `cross_sectional_funding_rate_regime_transition_filter` | `EXCLUDED_NEAR_DUPLICATE` | near-duplicate persistence reversal filter |
| `cross_sectional_realized_volatility_rank_rotation&#47;v0` | `SELECTED_RECOMMENDED` | material-different volatility-rank axis, reuse-first compatible |

## D. Selected Next Scope Boundary (exactly one)

| Feld | Wert |
|---|---|
| `SELECTED_NEXT_SCOPE_BOUNDARY` | `cross_sectional_realized_volatility_rank_rotation&#47;v0` |
| `RESEARCH_HYPOTHESIS` | `NON_BITCOIN_PERPETUAL_PANEL_REALIZED_VOLATILITY_DISPERSION_SUPPORTS_CROSS_SECTIONAL_LOW_VOL_LONG_HIGH_VOL_SHORT_ROTATION_EDGE` |
| `SIGNAL_FAMILY` | `realized_volatility_rank` |
| `TARGET_PHENOMENON` | `volatility_dispersion_rotation` |
| `DATA_FEATURE_CLASS` | `panel_ohlcv_derived_realized_volatility` |
| `AGGREGATION_MECHANISM` | `cross_sectional_rank_single_slot_rotation` |
| `ENTRY_EXIT_HYPOTHESIS` | `long_lowest_realized_vol_short_highest_realized_vol` |
| `UNIVERSE_RANKING` | `pit_okx_linear_usdt_non_bitcoin_perpetual_panel` |

## E. Material Difference Matrix

| Axis | Failed Final Fleet / Prior Families | Selected Scope |
|---|---|---|
| Signal family | price trend, mean-reversion bands, price momentum, funding scores, price-return rank | realized volatility rank |
| Target phenomenon | directional edge on single slot or funding score | volatility dispersion rotation |
| Data feature class | OHLCV trend/band/momentum; funding panel scores | panel OHLCV-derived realized vol |
| Aggregation | single-slot ETH narrow adapter or funding cross-section | cross-sectional vol rank rotation |
| Entry/exit | trend/band/momentum thresholds; funding z-scores | low-vol long / high-vol short rank selection |
| Regime filter | persistence/reversal filter (terminal) | none — not filter-overlay near-duplicate |

Material difference confirmed. Economic gates and safety boundaries are not weakened.

## F. Reuse-First Decision

| Surface | Reuse Owner |
|---|---|
| Panel dataset | `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1` |
| Ranking semantics pattern | `config/research/cross_sectional_relative_strength_non_bitcoin_perpetuals_v0_ranking_semantics_binding_v0.json` |
| Scope ratification pattern | `cross_sectional_funding_rate_*_research_scope_ratification_v0` family |
| Offline evaluation infra pattern | `cross_sectional_relative_strength_v0_offline_economic_evaluation_execution_v0` |
| Narrow adapter need | realized-vol feature computation from panel OHLCV only — no core/runtime mutation |
| Manifest verify | `scripts/ops/primary_evidence_retention_v0.py` |

Keine Core-System-, Master-V2-, Double-Play-, Risk-/Sizing-, Safety-Runtime- oder Market-Airport-Mutation.

## G. Authority Boundary

Scope-Discovery/Ratifikation-Prep ≠ Binding-Ratifikation ≠ Evaluation-Autorisierung.

| Boundary | Value |
|---|---|
| `SCOPE_DISCOVERY_AND_RATIFICATION_PREP_ONLY` | `true` |
| `OFFLINE_ONLY` | `true` |
| `EVALUATION_EXECUTED` | `false` |
| `RUNTIME_AUTHORITY_TOUCHED` | `false` |
| `PROMOTION_GRANTED` | `false` |
| `UNCHANGED_RETRY_ALLOWED` | `false` |
| `MARKET_AIRPORT_EXCLUDED` | `true` |
