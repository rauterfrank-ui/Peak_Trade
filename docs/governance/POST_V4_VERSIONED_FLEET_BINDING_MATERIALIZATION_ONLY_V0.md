# Post-v4 Versioned Fleet Binding Materialization Only v0

---
docs_token: DOCS_TOKEN_POST_V4_VERSIONED_FLEET_BINDING_MATERIALIZATION_ONLY_V0
STATUS: BINDINGS_MATERIALIZED_NOT_EVALUATED
scope: research, offline-only, non-authorizing
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

> **Non-authorizing:** Materialisiert ausschließlich versionierte Fleet-Bindings nach PR4902 post-v4 Hypothesis- und Binding-Definition-Ratifikation. Keine Offline-Economic-Evaluation, kein Backtest/WF/MC/Stress, kein v4 Same-Binding-Retry, keine Runtime-Authority.

## A. Verdict

| Feld | Wert |
|---|---|
| `VERDICT` | `BINDINGS_MATERIALIZED_NOT_EVALUATED` |
| `PROCESS_CLASSIFICATION` | `POST_V4_VERSIONED_FLEET_BINDING_MATERIALIZATION_ONLY_V0` |
| `SCOPE_CLASSIFICATION` | `VERSIONED_FLEET_BINDING_MATERIALIZATION_ONLY_NO_EVALUATION_NO_RUNTIME_AUTHORITY` |
| `GO_TOKEN` | `GO_OPERATOR_RATIFY_POST_V4_VERSIONED_FLEET_BINDING_MATERIALIZATION_ONLY_V0` |
| `GO_TOKEN_CONSUMPTION` | `CONSUME_ONCE_FOR_THIS_SCOPE_BINDING_MATERIALIZATION_ONLY` |
| `BASE_HEAD` | `c534b0eafc53b38c046bc99e823eb8318a43da7f` |
| `PARENT_PR` | `4902` |
| `PARENT_CLOSEOUT_DIR` | `/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/implementation/post_v4_new_hypothesis_and_versioned_fleet_binding_ratification_scope_merge_closeout_20260706T034102Z` |
| `PARENT_CLOSEOUT_MANIFEST_VERIFY_RC` | `0` |
| `HYPOTHESIS_ID` | `post_v4_sparse_signal_failure_recovery_futures_fleet_hypothesis_v0` |
| `HYPOTHESIS_STATUS` | `RATIFIED_FOR_BINDING_DEFINITION_ONLY` |
| `MATERIALIZATION_STATUS` | `BINDING_MATERIALIZATION_ONLY` |
| `FINAL_RESEARCH_FLEET` | `trend_following,bollinger_bands,momentum_1h` |
| `STRATEGY_VERSION_MATERIALIZED` | `post_v4_hypothesis_v0` |
| `BLOCKED_STRATEGY_VERSION` | `v4` |
| `BLOCKED_BINDING_CLASS` | `SPARSE_SIGNAL_ZERO_TRADE_RESEARCH_V0` |
| `EVALUATION_STATUS` | `NOT_EVALUATED` |
| `EVALUATION_AUTHORIZED` | `false` |
| `ECONOMIC_EVALUATION_AUTHORIZED` | `false` |
| `BACKTEST_AUTHORIZED` | `false` |
| `WALK_FORWARD_AUTHORIZED` | `false` |
| `MONTE_CARLO_AUTHORIZED` | `false` |
| `STRESS_AUTHORIZED` | `false` |
| `RUNTIME_AUTHORITY` | `NONE` |
| `RUNTIME_AUTHORITY_CREATED` | `false` |
| `PROMOTION_AUTHORIZED` | `false` |
| `SHADOW_AUTHORIZED` | `false` |
| `PAPER_AUTHORIZED` | `false` |
| `TESTNET_AUTHORIZED` | `false` |
| `LIVE_AUTHORIZED` | `false` |
| `FUTURES_ONLY` | `true` |
| `REQUIRED_NEXT_GO_FOR_OFFLINE_EVALUATION` | `GO_OPERATOR_RATIFY_POST_V4_VERSIONED_FLEET_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_SCOPE_V0` |
| `runtime_effect` | `NONE` |
| `authority_effect` | `NONE` |
| `trading_effect` | `NONE` |

**Authoritative owners (reuse, nicht ersetzen):**

- Scope config: `config/research/post_v4_versioned_fleet_binding_materialization_only_v0.json`
- Parent PR4902 closeout: `/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/implementation/post_v4_new_hypothesis_and_versioned_fleet_binding_ratification_scope_merge_closeout_20260706T034102Z`
- Parent scope: `docs/governance/POST_V4_NEW_HYPOTHESIS_AND_VERSIONED_FLEET_BINDING_RATIFICATION_V0.md`
- Collector: `scripts/research/post_v4_versioned_fleet_binding_materialization_only_v0.py`
- Progress registry: `docs/governance/PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md`

## B. Materialized Fleet Bindings

| Kandidat | `strategy_version` | `candidate_binding_id` | `evaluation_status` | `runtime_status` |
|---|---|---|---|---|
| `trend_following` | `post_v4_hypothesis_v0` | `trend_following_post_v4_hypothesis_v0_binding_materialized` | `NOT_EVALUATED` | `NO_RUNTIME_AUTHORITY` |
| `bollinger_bands` | `post_v4_hypothesis_v0` | `bollinger_bands_post_v4_hypothesis_v0_binding_materialized` | `NOT_EVALUATED` | `NO_RUNTIME_AUTHORITY` |
| `momentum_1h` | `post_v4_hypothesis_v0` | `momentum_1h_post_v4_hypothesis_v0_binding_materialized` | `NOT_EVALUATED` | `NO_RUNTIME_AUTHORITY` |

**Shared model bindings:** canonical MV2 decision path reuse-first; realistic fee/slippage/funding; offline execution simulation only; unchanged post-v4 fleet economic policy; versioned futures dataset/period/instrument bindings required.

Binding-Materialisierung ≠ Evaluation-Autorisierung ≠ Runtime-Authority.

## C. Global Binding Policy (Fail-Closed)

| Policy | Wert |
|---|---|
| `futures_only` | `true` |
| `reuse_first` | `true` |
| `core_system_mutation_allowed` | `false` |
| `canonical_trading_logic_mutation_allowed` | `false` |
| `policy_threshold_lowering_allowed` | `false` |
| `failed_binding_retry_unchanged_allowed` | `false` |
| `candidate_specific_policy_relaxation_allowed` | `false` |

## D. Authority Boundary

| Pfad | Status |
|---|---|
| Binding materialization | `ALLOWED` (this scope only) |
| Economic evaluation / Backtest | `BLOCKED` |
| Walk-Forward / Monte-Carlo / Stress | `BLOCKED` |
| v4 unmodified binding retry | `BLOCKED` |
| Runtime / Shadow / Paper / Testnet / Live | `BLOCKED` |
| Orders / Adapter / Credentials / Arming | `BLOCKED` |

## E. Source Evidence Refs

| Quelle | Referenz | `MANIFEST_VERIFY_RC` |
|---|---|---|
| PR4902 scope merge closeout | `/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/implementation/post_v4_new_hypothesis_and_versioned_fleet_binding_ratification_scope_merge_closeout_20260706T034102Z` | `0` |
| Parent scope governance | `docs/governance/POST_V4_NEW_HYPOTHESIS_AND_VERSIONED_FLEET_BINDING_RATIFICATION_V0.md` | n/a (repo config) |

## F. Safe Next Action

```text
NEXT_ADMISSIBLE_STEP=REQUEST_OPERATOR_GO_FOR_POST_V4_VERSIONED_FLEET_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_SCOPE_V0
CURRENT_ADMISSIBLE_NEXT_SCOPE=POST_V4_VERSIONED_FLEET_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_SCOPE_V0
CURRENT_ADMISSIBLE_NEXT_SCOPE_GO_TOKEN=GO_OPERATOR_RATIFY_POST_V4_VERSIONED_FLEET_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_SCOPE_V0
NO_ECONOMIC_EVALUATION_WITHOUT_SEPARATE_OPERATOR_GO=true
NO_UNCHANGED_V4_BINDING_RETRY=true
```

Versionierte Fleet-Binding-Materialisierung ist abgeschlossen. Separates Operator-GO erforderlich für Offline-Economic-Evaluation-Execution.
