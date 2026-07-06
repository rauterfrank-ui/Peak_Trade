# Post-PR4920 New Versioned Research Scope Definition v0

---
docs_token: DOCS_TOKEN_POST_PR4920_NEW_VERSIONED_RESEARCH_SCOPE_DEFINITION_V0
STATUS: SCOPE_DEFINED_NOT_EXECUTED
scope: governance, documentation-only, non-authorizing
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

> **Non-authorizing:** Definiert ausschließlich den nächsten admissiblen versionierten Research-Scope nach manifest-verifizierter PR4920 Failure-Decomposition (`FLEET_ECONOMIC_VALIDITY_FAIL`, alle v1-Bindings terminal `ROBUSTNESS_FAILED`). Keine Economic Evaluation. Keine Binding-Ratifikation in diesem Scope. Kein Same-Binding-Retry, keine Parameterrettung, keine Runtime-Authority. Scope-Definition ≠ Binding-Ratifikation ≠ Evaluation-Autorisierung.

## A. Verdict

| Feld | Wert |
|---|---|
| `VERDICT` | `SCOPE_DEFINED_NOT_EXECUTED` |
| `PROCESS_CLASSIFICATION` | `POST_PR4920_NEW_VERSIONED_RESEARCH_SCOPE_DEFINITION_ONLY_V0` |
| `SCOPE_CLASSIFICATION` | `POST_PR4920_NEW_VERSIONED_RESEARCH_SCOPE_FROM_FAILURE_DECOMPOSITION_DEFINITION_ONLY_V0` |
| `SELECTED_CLASS` | `D` |
| `ADMISSIBLE_SCOPE_CLASS` | `D_NEW_VERSIONED_RESEARCH_SCOPE_WITH_FULL_BINDINGS` |
| `OPERATOR_GO` | `GO_DEFINE_POST_PR4920_NEW_VERSIONED_RESEARCH_SCOPE_FROM_FAILURE_DECOMPOSITION_V0` |
| `GO_TOKEN_CONSUMPTION` | `CONSUMED_ONCE_FOR_SCOPE_DEFINITION_ONLY` |
| `CURRENT_BASELINE_PR` | `4920` |
| `CURRENT_BASELINE_HEAD` | `aa53ee580257b8d937a19c5172e98b7d16544221` |
| `PARENT_DECOMPOSITION_EVIDENCE_CLASS_ID` | `POST_PR4920_FAILURE_DECOMPOSITION_FOLLOWUP_EXECUTION_OFFLINE_ONLY_V0` |
| `PARENT_DECOMPOSITION_EVIDENCE_REF` | `/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/implementation/post_pr4920_failure_decomposition_followup_execution_offline_only_20260706T080836Z` |
| `PARENT_DECOMPOSITION_MANIFEST_VERIFY_RC` | `0` |
| `PARENT_CLOSEOUT_DIR` | `/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/implementation/pr4920_post_pr4919_terminal_final_fleet_failure_decomposition_followup_scope_merge_closeout_20260706T080500Z` |
| `PARENT_CLOSEOUT_MANIFEST_VERIFY_RC` | `0` |
| `EVIDENCE_CLASS_ID` | `POST_PR4920_NEW_VERSIONED_RESEARCH_SCOPE_DEFINITION_V0` |
| `SCOPE_ID` | `POST_PR4920_NEW_VERSIONED_RESEARCH_SCOPE_DEFINITION_V0` |
| `SCOPE_DEFINITION_ONLY` | `true` |
| `RESEARCH_HYPOTHESIS` | `POST_PR4920_FAILURE_DECOMPOSITION_REQUIRES_NEW_VERSIONED_BINDINGS_NOT_UNCHANGED_V1_RETRY_OR_NEAR_DUPLICATE_ARCHETYPE` |
| `FINAL_RESEARCH_FLEET` | `trend_following,bollinger_bands,momentum_1h` |
| `FINAL_RESEARCH_FLEET_STATUS` | `NEW_VERSIONED_BINDINGS_REQUIRED_BEFORE_ANY_OFFLINE_EVALUATION` |
| `STRATEGY_VERSION` | `v2_required` |
| `FLEET_VERDICT` | `FLEET_ECONOMIC_VALIDITY_FAIL` |
| `FLEET_STATUS` | `FAIL` |
| `ECONOMIC_VALIDITY_OFFLINE_GATE_PASS` | `false` |
| `PROMOTION_ADMISSIBLE` | `false` |
| `RUNTIME_REWIRE_ADMISSIBLE` | `false` |
| `RETRY_AUTHORIZED` | `false` |
| `FAILED_BINDINGS_EXCLUDED` | `true` |
| `TERMINAL_NEGATIVE_EVIDENCE_UNCHANGED` | `true` |
| `FAILED_EVIDENCE_IS_TERMINAL` | `true` |
| `NEW_CANDIDATE_RATIFIED` | `false` |
| `NEW_CANDIDATES_RATIFIED` | `false` |
| `PROMOTION_AUTHORITY` | `false` |
| `PROMOTION_ELIGIBLE` | `false` |
| `ECONOMIC_EVALUATION_AUTHORIZED` | `false` |
| `ECONOMIC_EVALUATION_EXECUTED` | `false` |
| `BACKTEST_EXECUTED` | `false` |
| `EVALUATION_EXECUTION_IN_THIS_SCOPE` | `false` |
| `RUNTIME_AUTHORITY` | `NONE` |
| `SHADOW_AUTHORIZED` | `false` |
| `PAPER_AUTHORIZED` | `false` |
| `TESTNET_AUTHORIZED` | `false` |
| `LIVE_AUTHORIZED` | `false` |
| `NO_ORDER_AUTHORITY` | `true` |
| `ORDERS_ALLOWED` | `false` |
| `FUTURES_ONLY` | `true` |
| `FAILED_BINDINGS_RETRY_ALLOWED` | `false` |
| `UNCHANGED_RETRY_ALLOWED` | `false` |
| `SAME_BINDING_RETRY_ALLOWED` | `false` |
| `PARAMETER_RESCUE_ALLOWED` | `false` |
| `PARAMETER_OPTIMIZATION_ALLOWED` | `false` |
| `THRESHOLD_LOWERING_ALLOWED` | `false` |
| `NEAR_DUPLICATE_BREAKOUT_MEAN_REVERSION_RETRY_ALLOWED` | `false` |
| `CORE_SYSTEM_MUTATION_ALLOWED` | `false` |
| `CANONICAL_TRADING_LOGIC_MUTATION_ALLOWED` | `false` |
| `MASTER_V2_MUTATION_ALLOWED` | `false` |
| `DOUBLE_PLAY_MUTATION_ALLOWED` | `false` |
| `RISK_SIZING_MUTATION_ALLOWED` | `false` |
| `SAFETY_RUNTIME_MUTATION_ALLOWED` | `false` |
| `REQUIRED_FUTURE_OPERATOR_GO` | `true` |
| `REQUIRED_NEXT_GO_FOR_BINDING_RATIFICATION` | `GO_POST_PR4920_VERSIONED_FLEET_BINDING_RATIFICATION_V0` |
| `REQUIRED_NEXT_GO_FOR_OFFLINE_EVALUATION` | `GO_POST_PR4920_OFFLINE_ECONOMIC_EVALUATION_V0` |
| `NEXT_STEP` | `SEPARATE_OPERATOR_GO_REQUIRED_FOR_VERSIONED_BINDINGS_OR_OFFLINE_EVALUATION` |
| `runtime_effect` | `NONE` |
| `authority_effect` | `NONE` |
| `economic_evaluation_effect` | `NONE` |
| `trading_effect` | `NONE` |

**Authoritative owners (reuse, nicht ersetzen):**

- Scope config: `config/research/post_pr4920_new_versioned_research_scope_definition_v0.json`
- Parent decomposition bundle: `post_pr4920_failure_decomposition_followup_execution_offline_only_20260706T080836Z`
- Parent scope config (PR4919): `config/research/post_pr4919_terminal_final_fleet_failure_decomposition_followup_scope_v0.json`
- Parent scope doc (PR4919): `docs/governance/POST_PR4919_TERMINAL_FINAL_FLEET_FAILURE_DECOMPOSITION_FOLLOWUP_SCOPE_V0.md`
- Progress registry: `docs/governance/PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md`

## B. Excluded Failed v1 Bindings (bindend, nicht retry-fähig)

| Binding | Failure Summary | Classified Verdict | Retry Allowed |
|---|---|---|---|
| `trend_following&#47;v1` | terminal negative edge, MC/Stress failed | `ROBUSTNESS_FAILED` | `false` |
| `bollinger_bands&#47;v1` | zero-trade degeneration, no edge | `ROBUSTNESS_FAILED` | `false` |
| `momentum_1h&#47;v1` | sparse signal, single-trade dominance, terminal negative | `ROBUSTNESS_FAILED` | `false` |

Keine unveränderten v1-Binding-Reexecutions. Keine Threshold-Lowering zur Trade-Generierung. Keine Near-Duplicate-Breakout-/Mean-Reversion-Umgehung.

## C. Candidate Archetype Requirements (v2, nicht autorisiert)

| Archetype | Parent Strategy | Replaces Binding | Derived Failure Class |
|---|---|---|---|
| `TREND_CONTINUATION_V2` | `trend_following` | `trend_following&#47;v1` | `MONTE_CARLO_STRESS_WEAKNESS_CLASS` |
| `MEAN_REVERSION_BANDS_V2` | `bollinger_bands` | `bollinger_bands&#47;v1` | `FEATURE_EDGE_FAILURE_CLASS` |
| `MOMENTUM_HORIZON_V2` | `momentum_1h` | `momentum_1h&#47;v1` | `SPARSE_SIGNAL_UNDERPOWERING` |

Diese Archetypen definieren Anforderungen für spätere versionierte Bindings — **keine** Economic Viability-Behauptung, **keine** Runtime-Eligibility.

## D. Required Bindings Before Any Evaluation

Bevor irgendeine spätere offline Economic Evaluation zulässig ist, müssen pro Kandidat versioniert und dauerhaft gebunden werden:

| Binding-Feld | Pflicht pro Kandidat |
|---|---|
| `strategy_id` | `true` |
| `strategy_version` | `true` |
| `parameter_binding` | `true` |
| `dataset_binding` | `true` |
| `period_binding` | `true` |
| `instrument_binding` | `true` |
| `fee_model_binding` | `true` |
| `slippage_model_binding` | `true` |
| `funding_model_binding` | `true` |
| `execution_model_binding` | `true` |
| `economic_policy_binding` | `true` |
| `implementation_digest` | `true` |
| `config_digest` | `true` |
| `data_digest` | `true` |

Fleet-weite Paritätsregeln: identische Economic Policies und vergleichbare Kosten-, Execution-, Dataset- und Periodenbindungen über alle drei Kandidaten.

## E. Admissibility Filters and Rejection Criteria

**Admissibility filters (bindend):**

- `EXCLUDE_UNCHANGED_V1_FAILED_BINDING` — strategy_id/strategy_version darf keinem excluded_failed_binding entsprechen
- `REQUIRE_NEW_VERSIONED_BINDING` — strategy_version > v1 oder neu ratifizierter versionierter Alias mit vollem Binding-Digest-Set
- `REQUIRE_MIN_TRADE_COUNT_EVIDENCE_PLAN` — Binding muss Minimum-Trade-Count-Evidence-Plan deklarieren
- `REQUIRE_ROBUSTNESS_EVIDENCE_PLAN` — Binding muss Walk-Forward-, Monte-Carlo- und Stress-Evidence-Plan deklarieren
- `REQUIRE_FLEET_PARITY` — fleet-weite identische Economic Policy und Kostenbindungen
- `NO_NEAR_DUPLICATE_ARCHETYPE` — kein Near-Duplicate-Breakout-/Mean-Reversion-Workaround

**Explicit rejection criteria (automatisch abgelehnt):**

- `UNCHANGED_V1_BINDING_REEXECUTION`
- `ZERO_TRADE_DEGENERATION_WITHOUT_NEW_VERSIONED_BINDING`
- `SINGLE_TRADE_DOMINANCE_WITHOUT_MITIGATION_PLAN`
- `THRESHOLD_LOWERING_TO_GENERATE_TRADES`
- `PARAMETER_RESCUE_AFTER_KNOWN_NEGATIVE_EVIDENCE`
- `NEAR_DUPLICATE_BREAKOUT_MEAN_REVERSION_WORKAROUND`
- `PROMOTION_WITHOUT_OFFLINE_ECONOMIC_GATE_PASS`
- `RUNTIME_REWIRE_FROM_NEGATIVE_FLEET`

## F. Failure Taxonomy (from PR4920 Decomposition, read-only)

| Follow-up class | Fleet-level diagnosis | Non-admissible automatic action |
|---|---|---|
| Evidence adequacy gaps | `long_short_contribution`, `fee_slippage_funding_drag`, `dominance_concentration` teils `MISSING_EVIDENCE` oder `INCONCLUSIVE` | Automatische Evidence-Execution ohne Operator GO |
| Feature/edge failure class | Alle drei Kandidaten `ROBUSTNESS_FAILED`; `bollinger_bands&#47;v1` `ZERO_TRADE_DEGENERATION` | Unveränderte v1-Binding-Reexecution |
| Turnover/cost drag class | `trend_following&#47;v1` und `momentum_1h&#47;v1` negative net edge | Parameter-Optimierung oder Threshold-Lowering |
| Drawdown/tail-risk class | `trend_following&#47;v1` max drawdown -0.009945; Stress/MC failed | Policy-Threshold-Rescue |
| Regime instability class | Regime breakdown `MIXED_TERMINAL_NEGATIVE` | Same-binding retry |
| Walk-forward OOS instability | Walk-forward stability `TERMINAL_NEGATIVE` fleet-wide | Walk-forward rerun unveränderter v1 bindings |
| Monte Carlo/stress weakness | MC `MIXED_TERMINAL_NEGATIVE`; Stress `TERMINAL_NEGATIVE` | Monte Carlo/Stress execution in diesem Scope |
| Portfolio contribution weakness | Fleet contribution failure `TERMINAL_NEGATIVE` | Promotion oder Runtime-Rewire |

## G. Authority Boundary

Scope-Definition ≠ Binding-Ratifikation. Keine Economic Evaluation. Kein Same-Binding-Retry.

| Boundary | Value |
|---|---|
| `SCOPE_DEFINITION_ONLY` | `true` |
| `FAILED_BINDINGS_EXCLUDED` | `true` |
| `FAILED_BINDINGS_RETRY_ALLOWED` | `false` |
| `retry_unchanged_binding_allowed` | `false` |
| `NO_ORDER_AUTHORITY` | `true` |
| `RUNTIME` | `FORBIDDEN` |
| `SHADOW` | `FORBIDDEN` |
| `PAPER` | `FORBIDDEN` |
| `TESTNET` | `FORBIDDEN` |
| `SCHEDULER` | `FORBIDDEN` |
| `ORDERS` | `FORBIDDEN` |
| `CREDENTIALS` | `FORBIDDEN` |
| `ARMING` | `FORBIDDEN` |
| `LIVE` | `FORBIDDEN` |

## H. Next Step

`SEPARATE_OPERATOR_GO_REQUIRED_FOR_VERSIONED_BINDINGS_OR_OFFLINE_EVALUATION`

Ein separater Operator GO ist erforderlich für:

1. `GO_POST_PR4920_VERSIONED_FLEET_BINDING_RATIFICATION_V0` — Ratifikation neuer versionierter Bindings
2. `GO_POST_PR4920_OFFLINE_ECONOMIC_EVALUATION_V0` — offline Economic Evaluation nach Binding-Ratifikation

Dieser Scope autorisiert weder Evaluation noch Runtime noch Promotion.
