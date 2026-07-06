# Post-PR4904 v4 Fleet Robustness Failure Decomposition v0

---
docs_token: DOCS_TOKEN_POST_PR4904_V4_FLEET_ROBUSTNESS_FAILURE_DECOMPOSITION_V0
STATUS: FAILURE_DECOMPOSITION_EXECUTION_COMPLETE_V0
scope: research, offline-only, non-authorizing
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

> **Non-authorizing:** Führt die bounded Class-E read-only/offline Failure-Decomposition über terminale PR4904 post-v4 fleet evaluation evidence aus. Keine Economic Evaluation, kein Same-Binding-Retry, keine Parameterrettung, kein Runtime-Rewire, keine Trading-Authority.

## A. Verdict

| Feld | Wert |
|---|---|
| `VERDICT` | `POST_PR4904_V4_FLEET_ROBUSTNESS_FAILURE_DECOMPOSITION_EVIDENCE_EXECUTION_COMPLETE_V0` |
| `PROCESS_CLASSIFICATION` | `POST_PR4904_V4_FLEET_ROBUSTNESS_FAILURE_DECOMPOSITION_EVIDENCE_EXECUTION_V0` |
| `SCOPE_CLASSIFICATION` | `READ_ONLY_FAILURE_DECOMPOSITION_EVIDENCE_EXECUTION_AFTER_POST_V4_FLEET_ECONOMIC_VALIDITY_FAIL_V0` |
| `EVIDENCE_CLASS_ID` | `POST_PR4904_V4_FLEET_ROBUSTNESS_FAILURE_DECOMPOSITION_EVIDENCE_EXECUTION_V0` |
| `EXECUTION_ID` | `POST_PR4904_V4_FLEET_ROBUSTNESS_FAILURE_DECOMPOSITION_EVIDENCE_EXECUTION_V0` |
| `SCOPE_ID` | `post_pr4904_v4_fleet_robustness_failure_decomposition_v0` |
| `SELECTED_CLASS` | `E` |
| `GO_TOKEN` | `GO_POST_PR4904_V4_FLEET_ROBUSTNESS_FAILURE_DECOMPOSITION_EVIDENCE_EXECUTION_V0` |
| `GO_TOKEN_CONSUMED` | `true` |
| `EXECUTION_STATUS` | `FAILURE_DECOMPOSITION_EXECUTION_COMPLETE_V0` |
| `CURRENT_BASELINE_PR` | `4904` |
| `CURRENT_BASELINE_HEAD` | `442c05688cfd1dcc28ebfcfdb13fd853dc16f8aa` |
| `PARENT_EVALUATION_EVIDENCE_REF` | `/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/implementation/post_v4_versioned_fleet_offline_economic_evaluation_execution_v0_20260706T040339Z` |
| `PARENT_EVALUATION_MANIFEST_VERIFY_RC` | `0` |
| `PARENT_CLOSEOUT_EVIDENCE_REF` | `/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/implementation/pr4904_squash_merge_closeout_20260706T041915Z` |
| `PARENT_CLOSEOUT_MANIFEST_VERIFY_RC` | `0` |
| `STRATEGY_VERSION` | `post_v4_hypothesis_v0` |
| `FLEET_VERDICT` | `FLEET_ECONOMIC_VALIDITY_FAIL` |
| `AGGREGATE_STATUS` | `FLEET_ECONOMIC_VALIDITY_FAIL` |
| `FLEET_STATUS` | `FAIL` |
| `ECONOMIC_VALIDITY_OFFLINE_GATE_PASS` | `false` |
| `TERMINAL_NEGATIVE_EVIDENCE_UNCHANGED` | `true` |
| `HISTORICAL_NEGATIVE_EVIDENCE_MUTATED` | `false` |
| `NEW_CANDIDATES_RATIFIED` | `false` |
| `PROMOTION_AUTHORITY` | `false` |
| `PROMOTION_ELIGIBLE` | `false` |
| `RUNTIME_REWIRE_ADMISSIBLE` | `false` |
| `SAME_BINDING_RETRY_ALLOWED` | `false` |
| `IMMUTABLE_BINDING_RETRY_ALLOWED` | `false` |
| `FAILED_BINDINGS_RETRY_ALLOWED` | `false` |
| `PARAMETER_RESCUE_ALLOWED` | `false` |
| `THRESHOLD_LOWERING_ALLOWED` | `false` |
| `RUNTIME_AUTHORITY` | `NONE` |
| `RUNTIME_AUTHORITY_CREATED` | `false` |
| `AUTHORITY_EFFECT` | `NONE` |
| `RUNTIME_EFFECT` | `NONE` |
| `TRADING_EFFECT` | `NONE` |
| `LIVE_AUTHORIZED` | `false` |
| `SHADOW_AUTHORIZED` | `false` |
| `PAPER_AUTHORIZED` | `false` |
| `TESTNET_AUTHORIZED` | `false` |
| `ORDERS_ALLOWED` | `false` |
| `FUTURES_ONLY` | `true` |
| `BITCOIN_DIRECTION_ALLOWED` | `false` |

**Authoritative owners (reuse, nicht ersetzen):**

- Decomposition config: `config/research/post_pr4904_v4_fleet_robustness_failure_decomposition_v0.json`
- Parent evaluation governance: `docs/governance/POST_V4_VERSIONED_FLEET_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_SCOPE_V0.md`
- Parent evaluation config: `config/research/post_v4_versioned_fleet_offline_economic_evaluation_execution_scope_v0.json`
- Progress registry: `docs/governance/PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md`

## B. Candidate Failure Decomposition (actual evidence only)

| Kandidat | Verdict | Trades | Net Return | Sharpe | Profit Factor | Max Drawdown |
|---|---|---:|---:|---:|---:|---:|
| `trend_following/post_v4_hypothesis_v0` | `ROBUSTNESS_FAILED` | 219 | -0.002398 | -0.132 | 0.951 | -0.009945 |
| `bollinger_bands/post_v4_hypothesis_v0` | `ROBUSTNESS_FAILED` | 0 | 0.0 | 0.0 | 0.0 | 0.0 |
| `momentum_1h/post_v4_hypothesis_v0` | `ROBUSTNESS_FAILED` | 2 | -0.001889 | -0.457 | 0.285 | -0.002638 |

**Per-candidate failure classification:**

| Kandidat | Terminal Negative | Dominante Failure-Klassen | Retry Allowed |
|---|---|---|---|
| `trend_following` | `true` | `NEGATIVE_NET_EDGE`, `PROFIT_FACTOR_BELOW_THRESHOLD`, `MONTE_CARLO_NEGATIVE_MEDIAN_RETURN`, `STRESS_SCENARIO_TAIL_FAILURE`, `ROBUSTNESS_FAILED` | `false` |
| `bollinger_bands` | `true` | `SPARSE_SIGNAL_UNDERPOWERING`, `PROFIT_FACTOR_BELOW_THRESHOLD`, `ROBUSTNESS_FAILED` | `false` |
| `momentum_1h` | `true` | `NEGATIVE_NET_EDGE`, `PROFIT_FACTOR_BELOW_THRESHOLD`, `SPARSE_SIGNAL_UNDERPOWERING`, `ROBUSTNESS_FAILED` | `false` |

## C. Decomposition Axis Summary

Read-only mapping aus PR4904 post-v4 evaluation bundle und PR4904 merge closeout:

| Achse | Fleet-level Ergebnis |
|---|---|
| `net_edge_after_costs` | `MIXED_TERMINAL_NEGATIVE` (trend/momentum negative; bollinger flat zero) |
| `profit_factor` | `TERMINAL_NEGATIVE` (alle Kandidaten profit factor &lt; 1 oder 0) |
| `max_drawdown_tail_loss` | `MIXED_TERMINAL_NEGATIVE` (trend tail risk via MC p5/stress) |
| `walk_forward_stability` | `INCONCLUSIVE_OR_REFUTED` (mixed OOS windows) |
| `monte_carlo_robustness` | `MIXED_TERMINAL_NEGATIVE` (trend negative median/p5) |
| `stress_robustness` | `MIXED_TERMINAL_NEGATIVE` (trend crash/gap scenarios) |
| `parameter_sensitivity` | `REFUTED` (`parameter_robustness_policy_pass=true` für alle Kandidaten) |
| `trade_count_sample_adequacy` | `MIXED_TERMINAL_NEGATIVE` (bollinger 0 trades; momentum 2 trades) |
| `long_short_contribution` | `MISSING_EVIDENCE` |
| `regime_breakdown` | `INCONCLUSIVE_OR_REFUTED` (WF mixed positive/negative OOS) |
| `fee_slippage_funding_drag` | `INCONCLUSIVE_OR_REFUTED` (implicit gross&gt;net where available) |
| `dominance_concentration` | `MIXED_TERMINAL_NEGATIVE` (single stress scenario dominance bei trend) |
| `evidence_admissibility` | `INCONCLUSIVE_OR_REFUTED` (parent manifests RC=0) |
| `fleet_contribution_failure` | `TERMINAL_NEGATIVE` (fleet 0/3 PASS) |

## D. Inconclusive vs Terminal Negative vs Missing Evidence

| Klassifikation | Bedeutung in diesem Scope |
|---|---|
| `TERMINAL_NEGATIVE` | Bestätigte Failure-Klasse aus persistierter post-v4-Evidence; unverändert bindend |
| `REFUTED` | Hypothese durch Evidence widerlegt; kein Retry-Pfad |
| `INCONCLUSIVE_EVIDENCE` | Teilweise Evidenz, keine admissible Promotion-/Retry-Schlussfolgerung |
| `MISSING_EVIDENCE` | Feld/Artefakt nicht materialisiert; keine Improvisation |

## E. Authority Boundary

| Feld | Wert |
|---|---|
| `ECONOMIC_EVALUATION_AUTHORIZED` | `false` |
| `economic_evaluation_executed` | `false` |
| `backtest_executed` | `false` |
| `walk_forward_run_executed` | `false` |
| `monte_carlo_run_executed` | `false` |
| `stress_run_executed` | `false` |
| `NO_PROMOTION_CLAIM` | `true` |
| `NO_UNCHANGED_BINDING_RETRY` | `ACTIVE` |
| `NO_FAILED_BINDING_RETRY` | `ACTIVE` |
| `NO_PARAMETER_RESCUE` | `ACTIVE` |
| `NO_THRESHOLD_LOWERING` | `ACTIVE` |
| `NO_RESULT_RESCUE` | `ACTIVE` |
| `NO_NEW_CANDIDATE` | `ACTIVE` |

## F. Output Bundle Artifacts

| Artefakt | Zweck |
|---|---|
| `FAILURE_DECOMPOSITION_SUMMARY.md` | Human-readable summary |
| `FAILURE_DECOMPOSITION.json` | Machine-readable full decomposition |
| `CANDIDATE_FAILURE_MATRIX.tsv` | Per-candidate dimension matrix |
| `AGGREGATE_FAILURE_MATRIX.tsv` | Fleet-level dimension matrix |
| `INPUT_POINTERS.json` | Parent bundle pointers and manifest status |
| `MANIFEST.sha256` | Durable evidence integrity |

## G. Next Step

| Feld | Wert |
|---|---|
| `NEXT_CANONICAL_STEP` | `GO_OPERATOR_RATIFY_NEXT_NEW_VERSIONED_RESEARCH_SCOPE_OR_NEW_EVIDENCE_CLASS_DEFINITION_ONLY_V0` |
| `NEXT_ADMISSIBLE_GO` | `GO_OPERATOR_RATIFY_NEXT_NEW_VERSIONED_RESEARCH_SCOPE_OR_NEW_EVIDENCE_CLASS_DEFINITION_ONLY_V0` |

Kein automatischer Folgeschritt. Operator-GO erforderlich für neue versioned research scope oder evidence class definition.
