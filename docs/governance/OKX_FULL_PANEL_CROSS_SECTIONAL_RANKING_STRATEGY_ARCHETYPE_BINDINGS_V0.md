# OKX Full-Panel Cross-Sectional Ranking Strategy Archetype Bindings v0

---
docs_token: DOCS_TOKEN_OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_BINDINGS_V0
STATUS: VERSIONED_BINDINGS_MATERIALIZATION_COMPLETE
scope: governance, documentation-only, non-authorizing
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

> **Non-authorizing:** Materialisiert ausschließlich die versionierten Pflicht-Bindings für Evidence Class `OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_V0` nach Scope-Definition (PR #4849). Keine Offline-Economic-Evaluation, keine Runtime-Authority, keine Promotion, keine Kandidatenratifikation.

## A. Verdict

| Feld | Wert |
|---|---|
| `VERDICT` | `VERSIONED_BINDINGS_MATERIALIZATION_COMPLETE` |
| `PROCESS_CLASSIFICATION` | `OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_VERSIONED_BINDINGS_MATERIALIZATION_V0` |
| `SCOPE_CLASSIFICATION` | `GOVERNANCE_ONLY_VERSIONED_BINDING_MATERIALIZATION_NO_EXECUTION` |
| `GO_TOKEN` | `GO_OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_VERSIONED_BINDINGS_MATERIALIZATION_V0` |
| `GO_TOKEN_CONSUMED` | `false` (Binding-Materialization only; consumed at PR merge by operator workflow) |
| `PR4849_MERGED` | `true` |
| `PR4849_MERGE_COMMIT` | `f21aadc36c0ee3f5b697ef426da25db5104b9b90` |
| `SCOPE_DEFINED` | `true` |
| `BINDING_READY` | `true` |
| `BINDING_SPEC_STATUS` | `VERSIONED_BINDINGS_MATERIALIZED` |
| `BINDING_ID` | `OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_V0_BINDINGS_V0` |
| `EVIDENCE_CLASS_ID` | `OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_V0` |
| `STRATEGY_ARCHETYPE_ID` | `cross_sectional_ranking_selection` |
| `STRATEGY_ARCHETYPE_VERSION` | `v0` |
| `CANDIDATE_RATIFIED` | `false` |
| `ECONOMIC_EVALUATION_AUTHORIZED` | `false` |
| `EVALUATION_EXECUTED_THIS_SCOPE` | `false` |
| `FURTHER_ECONOMIC_EVALUATION_REQUIRES_SEPARATE_OPERATOR_GO` | `true` |
| `PROMOTION_AUTHORIZED` | `false` |
| `RUNTIME_REWIRE_ADMISSIBLE` | `false` |
| `RUNTIME_AUTHORITY` | `false` |
| `FUTURES_ONLY` | `true` |
| `BITCOIN_DIRECTION_ALLOWED` | `false` |
| `REQUIRES_FULL_PANEL_BINDING` | `true` |
| `NARROW_ADAPTER_ETH_ONLY_BINDING_DISALLOWED` | `true` |
| `authority_effect` | `false` |
| `runtime_effect` | `NONE` |

**Authoritative owners (reuse, nicht ersetzen):**

- Scope config: `config/research/okx_full_panel_cross_sectional_ranking_strategy_archetype_evidence_class_scope_v0.json`
- Bindings config: `config/research/okx_full_panel_cross_sectional_ranking_strategy_archetype_bindings_v0.json`
- Cross-sectional ranking semantics (reuse): `config/research/cross_sectional_relative_strength_non_bitcoin_perpetuals_v0_ranking_semantics_binding_v0.json`
- OKX full-panel dataset promotion registry (reuse): `config/research/okx_full_panel_dataset_promotion_registry_v0.json`
- Failed fleet scope (blocked, reuse): `config/research/final_research_fleet_new_evidence_class_scope_v0.json`
- Progress registry: `docs/governance/PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md`

## B. Materialisierte Pflicht-Bindings

| Binding-Dimension | Status | Wert / Referenz |
|---|---|---|
| `evidence_class_id` | `BOUND` | `OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_V0` |
| `strategy_archetype_id` | `BOUND` | `cross_sectional_ranking_selection` |
| `strategy_archetype_version` | `BOUND` | `v0` |
| `universe_binding` | `BOUND` | OKX lifecycle-admissible full panel, 118 instruments target, `futures_only=true` |
| `instrument_panel_binding` | `BOUND` | `lifecycle_admissible_complete_panel_v0`, true multi-instrument execution path |
| `dataset_binding` | `BOUND` | `okx_full_panel_historical_funding_archive_v0` v0, digest `0bfa4df4…` |
| `period_binding` | `BOUND` | Full Mai–Sep 2024 `2024-05-01..2024-09-01`, policy `okx_full_panel_cross_sectional_research_chronological_holdout_v0` |
| `training_period` | `BOUND` | `2024-05-21..2024-07-01` |
| `validation_period` | `BOUND` | `2024-07-01..2024-08-01` |
| `out_of_sample_period` | `BOUND` | `2024-08-01..2024-09-01` |
| `fee_model_binding` | `BOUND` | `backtest_fee_taker_symmetric_v0`, `fee_bps=10.0` (unchanged default) |
| `slippage_model_binding` | `BOUND` | `backtest_slippage_symmetric_v0`, `slippage_bps=5.0` (unchanged default) |
| `funding_model_binding` | `BOUND` | `backtest_funding_perpetual_interval_v1`, `bind=true` (unchanged default) |
| `execution_model_binding` | `BOUND` | `backtest_execution_v0`, `roundtrip_cost_bps=40.0` (unchanged default) |
| `economic_policy_binding` | `BOUND` | `economic_validity_policy_v1` (unchanged default) |
| `ranking_policy_binding` | `BOUND` | Reuse `cross_sectional_relative_strength_non_bitcoin_perpetuals_v0_ranking_semantics_binding_v0.json` |
| `selection_policy_binding` | `BOUND` | `single_top1_by_score_desc`, switch policy `flat_then_wait_one_epoch_then_enter` |
| `implementation_digest_policy` | `REQUIRED_BEFORE_EVALUATION_EXECUTION` | `MODULE_IMPLEMENTATION_REF_v0` |
| `config_digest_policy` | `REQUIRED_BEFORE_EVALUATION_EXECUTION` | `BINDING_CONFIG_CANONICAL_JSON_v0` |
| `data_digest_policy` | `BOUND` | `OKX_FULL_PANEL_DATASET_CONTENT_DIGEST_v0`, expected `0bfa4df4…` |
| `excluded_legacy_bindings` | `BOUND` | All Section C exclusions from scope config |
| `blocked_shortcuts` | `BOUND` | ETH-only narrow adapter, 7-day holdout narrowing, single-instrument evaluation blocked |

## C. Blockierte Shortcuts (Fail-Closed)

| Shortcut | Status |
|---|---|
| `NARROW_ADAPTER_INST_ETH_USDT_PERP` als Full-Panel-Evaluation | `BLOCKED` |
| `NARROW_ADAPTER_INST_ETH_USDT_PERP_ECONOMIC_RESEARCH_v1` als Full-Panel-Evaluation | `BLOCKED` |
| 7-Tage-Holdout `2024-05-25..2024-06-01` bei Full-Panel-Claim | `BLOCKED` |
| Period digest `950ac7f41d2eb3422cdbbd28a3ee5658a7a0a0ce5d6d55b9ddd3d387129fe5c5` (failed fleet 7-day slice) | `BLOCKED` |
| Retry `trend_following&#47;v1` | `BLOCKED` |
| Retry `bollinger_bands&#47;v1` | `BLOCKED` |
| Retry `momentum_1h&#47;v1` | `BLOCKED` |
| Retry digest `161d834e5153df78a0013b6e55c4c8bd4788c775811e3678f025104a307d78f1` (STEP31F) | `BLOCKED` |
| Retry digest `c5e3b5fe6b688b49dbd2b210fd63bdea79201d64820591f87091b4e20689a9dd` (failed fleet binding completion) | `BLOCKED` |
| Retry digest `64da0eae56a70ad0661398db14d712f6d58d6ea9f6ad0dbb73f3de2b01d11d67` (failed fleet scope) | `BLOCKED` |

## D. Safe Next Action

```text
NEXT_ACTION=NO_RUNTIME_OR_PROMOTION_ACTION
FUTURE_EVALUATION=REQUIRES_SEPARATE_OPERATOR_GO_AND_EVALUATION_EXECUTION_MATERIALIZATION
```

Keine Evaluation in diesem Scope. Nach Merge optional separate Offline-Evaluation nur mit explizitem Operator-GO, vollständiger Digest-Materialisierung und separatem Evaluation-Execution-Scope.
