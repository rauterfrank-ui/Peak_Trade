# Post-PR4921 Versioned Research Bindings (No Eval) v0

---
docs_token: DOCS_TOKEN_POST_PR4921_VERSIONED_RESEARCH_BINDINGS_NO_EVAL_V0
STATUS: BINDINGS_MATERIALIZED_NOT_EVALUATED
scope: research, offline-only, non-authorizing
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

> **Non-authorizing:** Materialisiert ausschließlich versionierte Research-Bindings nach PR4921 Scope-Definition (PR4920 Failure-Decomposition Follow-up). Keine Offline-Economic-Evaluation, kein Backtest/WF/MC/Stress, kein v1 Same-Binding-Retry, keine Runtime-Authority. Binding-Materialisierung ≠ Evaluation-Autorisierung.

## A. Verdict

| Feld | Wert |
|---|---|
| `VERDICT` | `BINDINGS_MATERIALIZED_NOT_EVALUATED` |
| `PROCESS_CLASSIFICATION` | `POST_PR4921_VERSIONED_RESEARCH_BINDINGS_MATERIALIZATION_NO_EVAL_V0` |
| `SCOPE_CLASSIFICATION` | `BINDING_MATERIALIZATION_ONLY_NO_EVAL_NO_RUNTIME_AUTHORITY_V0` |
| `GO_TOKEN` | `GO_MATERIALIZE_POST_PR4921_VERSIONED_RESEARCH_BINDINGS_NO_EVAL_V0` |
| `GO_TOKEN_CONSUMPTION` | `CONSUMED_ONCE_FOR_BINDING_MATERIALIZATION_ONLY` |
| `BASE_HEAD` | `dc6229ed32a57af4b9f3cd1f3d969cf499b6ebc5` |
| `PARENT_PR` | `4921` |
| `PARENT_SCOPE_ID` | `POST_PR4920_NEW_VERSIONED_RESEARCH_SCOPE_DEFINITION_V0` |
| `PARENT_CLOSEOUT_DIR` | `/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/implementation/post_pr4920_new_versioned_research_scope_definition_merge_closeout_20260706T081927Z` |
| `PARENT_CLOSEOUT_MANIFEST_VERIFY_RC` | `0` |
| `BINDING_MATERIALIZATION_ONLY` | `true` |
| `BINDING_MATERIALIZATION_STATUS` | `BINDINGS_MATERIALIZED_NOT_EVALUATED` |
| `FAILED_V1_BINDINGS_EXCLUDED` | `true` |
| `EXCLUDED_FAILED_V1_BINDINGS` | `trend_following&#47;v1,bollinger_bands&#47;v1,momentum_1h&#47;v1` |
| `STRATEGY_VERSION_MATERIALIZED` | `v2` |
| `EVALUATION_AUTHORIZED` | `false` |
| `ECONOMIC_EVALUATION_AUTHORIZED` | `false` |
| `BACKTEST_EXECUTION_AUTHORIZED` | `false` |
| `WALK_FORWARD_EXECUTION_AUTHORIZED` | `false` |
| `MONTE_CARLO_EXECUTION_AUTHORIZED` | `false` |
| `STRESS_EXECUTION_AUTHORIZED` | `false` |
| `PARAMETER_OPTIMIZATION_AUTHORIZED` | `false` |
| `THRESHOLD_LOWERING_AUTHORIZED` | `false` |
| `RETRY_AUTHORIZED` | `false` |
| `PROMOTION_ADMISSIBLE` | `false` |
| `RUNTIME_REWIRE_ADMISSIBLE` | `false` |
| `RUNTIME_AUTHORITY` | `NONE` |
| `ORDERS_ALLOWED` | `false` |
| `LIVE_AUTHORIZED` | `false` |
| `SHADOW_AUTHORIZED` | `false` |
| `PAPER_AUTHORIZED` | `false` |
| `TESTNET_AUTHORIZED` | `false` |
| `NEXT_STEP` | `SEPARATE_OPERATOR_GO_REQUIRED_FOR_OFFLINE_ECONOMIC_EVALUATION_EXECUTION` |
| `runtime_effect` | `NONE` |
| `authority_effect` | `NONE` |
| `trading_effect` | `NONE` |

**Authoritative owners (reuse, nicht ersetzen):**

- Binding config: `config/research/post_pr4921_versioned_research_bindings_no_eval_v0.json`
- Parent scope config: `config/research/post_pr4920_new_versioned_research_scope_definition_v0.json`
- Parent scope doc: `docs/governance/POST_PR4920_NEW_VERSIONED_RESEARCH_SCOPE_DEFINITION_V0.md`
- Collector: `scripts/research/post_pr4921_versioned_research_bindings_no_eval_v0.py`

## B. Materialized Versioned Bindings

| Kandidat | Version | Archetype | Ersetzt | Status |
|---|---|---|---|---|
| `trend_following` | `v2` | `TREND_CONTINUATION_V2` | `trend_following&#47;v1` | `MATERIALIZED_NOT_EVALUATED` |
| `bollinger_bands` | `v2` | `MEAN_REVERSION_BANDS_V2` | `bollinger_bands&#47;v1` | `MATERIALIZED_NOT_EVALUATED` |
| `momentum_1h` | `v2` | `MOMENTUM_HORIZON_V2` | `momentum_1h&#47;v1` | `MATERIALIZED_NOT_EVALUATED` |

Jede Binding enthält: `parameter_binding`, `dataset_binding`, `period_binding`, `instrument_binding`, `fee_model_binding`, `slippage_model_binding`, `funding_model_binding`, `execution_model_binding`, `economic_policy_binding`, `implementation_digest_source`, `config_digest_source`, `data_digest_source`, sowie explizite Exclusion-Beziehung zu failed v1 Bindings.

## C. Shared Model Bindings (Fleet Parity)

| Binding | Wert |
|---|---|
| `dataset_binding` | `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1_extended_chronological_v1` |
| `period_binding` | `panel_calendar_2024-05-01_to_2024-09-01_utc_pt1h` |
| `instrument_binding` | `futures_only_okx_linear_usdt_non_bitcoin_panel_v1` |
| `fee_model_binding` | `backtest_fee_taker_symmetric_v0_realistic_costs` |
| `slippage_model_binding` | `backtest_slippage_conservative_half_spread_v0` |
| `funding_model_binding` | `backtest_funding_perpetual_interval_v1` |
| `execution_model_binding` | `backtest_execution_v0_offline_simulation_only` |
| `economic_policy_binding` | `economic_validity_policy_v1_unchanged_no_threshold_lowering` |

Fleet-weite Parität: identische Economic Policy und vergleichbare Kosten-, Execution-, Dataset- und Periodenbindungen über alle drei Kandidaten.

## D. Authority Boundary

Binding-Materialisierung ≠ Evaluation-Autorisierung. Keine Economic Evaluation. Kein v1 Same-Binding-Retry.

| Pfad | Status |
|---|---|
| Binding materialization | `ALLOWED` (this scope only) |
| Economic evaluation / Backtest | `BLOCKED` |
| Walk-Forward / Monte-Carlo / Stress | `BLOCKED` |
| v1 unmodified binding retry | `BLOCKED` |
| Parameter optimization / Threshold lowering | `BLOCKED` |
| Runtime / Shadow / Paper / Testnet / Live | `BLOCKED` |
| Orders / Adapter / Credentials / Arming | `BLOCKED` |
| `CREDENTIALS` | `FORBIDDEN` |
| `ARMING` | `FORBIDDEN` |

## E. Next Step

`SEPARATE_OPERATOR_GO_REQUIRED_FOR_OFFLINE_ECONOMIC_EVALUATION_EXECUTION`

Separater Operator GO erforderlich für offline Economic Evaluation Execution nach Binding-Materialisierung. Dieser Scope autorisiert weder Evaluation noch Runtime noch Promotion.
