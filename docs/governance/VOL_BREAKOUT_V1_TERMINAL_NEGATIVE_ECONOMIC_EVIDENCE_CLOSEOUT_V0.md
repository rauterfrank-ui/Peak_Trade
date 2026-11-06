# Vol Breakout v1 Terminal Negative Economic Evidence Closeout v0

---
docs_token: DOCS_TOKEN_VOL_BREAKOUT_V1_TERMINAL_NEGATIVE_ECONOMIC_EVIDENCE_CLOSEOUT_V0
STATUS: TERMINAL_NEGATIVE_ECONOMIC_EVIDENCE_CLOSEOUT_COMPLETE
scope: governance, documentation-only, non-authorizing
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

> **Non-authorizing:** Terminale Governance-Bindung der vollständig ausgeführten Full-Canonical-Offline-Baseline-Economic-Evaluation (post PR #5074 sizing-config-digest binding repair) für `vol_breakout&#47;v1` auf `inst-eth-usdt-perp` unter unverändertem versioniertem Binding. Keine Promotion, keine Runtime, kein Same-Binding-Retry, kein Policy-Rescue.

## A. Verdict

| Feld | Wert |
|---|---|
| `VERDICT` | `VOL_BREAKOUT_V1_TERMINAL_NEGATIVE_ECONOMIC_EVIDENCE_CLOSEOUT_COMPLETE_V0` |
| `PROCESS_CLASSIFICATION` | `PERSIST_TERMINAL_NEGATIVE_EVIDENCE_NO_POLICY_RESCUE_AND_CLOSE_RESEARCH_GENERATION_V0` |
| `SCOPE_CLASSIFICATION` | `VOL_BREAKOUT_V1_TERMINAL_NEGATIVE_ECONOMIC_EVIDENCE_CLOSEOUT_V0` |
| `GO_TOKEN` | `GO_VOL_BREAKOUT_V1_TERMINAL_NEGATIVE_ECONOMIC_EVIDENCE_CLOSEOUT_V0` |
| `EVIDENCE_CLASS_ID` | `VOL_BREAKOUT_V1_FULL_CANONICAL_OFFLINE_BASELINE_ECONOMIC_EVALUATION_V0` |
| `BINDING` | `vol_breakout&#47;v1` |
| `INSTRUMENT` | `inst-eth-usdt-perp` |
| `BASELINE_HEAD` | `5a423b44645f5923985dd0eb660c55c1a065057b` |
| `BASELINE_PR` | `5074` |
| `BASELINE_VERDICT` | `FAIL` |
| `FAILURE_CLASS` | `NEGATIVE_ECONOMIC_BASELINE_AND_ROBUSTNESS_FAIL` |
| `BASELINE_EXECUTED` | `true` |
| `ECONOMIC_EVALUATION_EXECUTED` | `true` |
| `ECONOMIC_EVALUATION_RUN_COUNT` | `1` |
| `SUFFICIENT_TRADE_SAMPLE` | `true` |
| `FAILED_BINDING_REGISTERED` | `true` |
| `CURRENT_RESEARCH_GENERATION_CLOSED` | `true` |
| `UNCHANGED_RETRY_BLOCKED` | `true` |
| `ECONOMIC_VALIDITY_OFFLINE_GATE_PASS` | `false` |
| `RUNTIME_REWIRE_ADMISSIBLE` | `false` |
| `POLICY_RESCUE_ALLOWED` | `false` |
| `TRADING_LOGIC_CHANGED` | `false` |
| `RISK_SIZING_SEMANTICS_CHANGED` | `false` |

## B. Metrics Summary

| Feld | Wert |
|---|---|
| `TRADE_COUNT` | `151` |
| `GROSS_RETURN` | `-0.032304431618757914` |
| `NET_RETURN` | `-0.032304431618757914` |
| `NET_EXPECTANCY` | `-2.139366332368052` |
| `PROFIT_FACTOR` | `0.5860307052309081` |
| `SHARPE` | `-1.4172276457716613` |
| `MAX_DRAWDOWN` | `-0.03413022503905831` |
| `SAMPLE_SUFFICIENCY_STATUS` | `SUFFICIENT_TRADE_SAMPLE` |
| `WALK_FORWARD_STATUS` | `EXECUTED_FAIL` |
| `MONTE_CARLO_STATUS` | `EXECUTED_FAIL` |
| `STRESS_STATUS` | `EXECUTED_FAIL` |

## C. Failure Classification and Reason Codes

| Feld | Wert |
|---|---|
| `PRIMARY_FAILURE_CLASS` | `NEGATIVE_ECONOMIC_BASELINE_AND_ROBUSTNESS_FAIL` |
| `PRIMARY_FAILURE_CLASS_UNCHANGED` | `true` |
| `REASON_CODES` | `METRIC_MISSING:parameter_neighbor_degradation;METRIC_MISSING:single_regime_profit_contribution;MONTE_CARLO_FAILED;NET_EXPECTANCY_BELOW_THRESHOLD;OUT_OF_SAMPLE_FAILED;PROFIT_FACTOR_BELOW_THRESHOLD;STRESS_FAILED;WALK_FORWARD_FAILED` |
| `METRIC_MISSING_CLASSIFICATION` | `ADDITIONAL_EVIDENCE_ROBUSTNESS_DEFICIT` |
| `METRIC_MISSING_DOES_NOT_RECLASSIFY_BASELINE` | `true` |
| `METRIC_MISSING_DOES_NOT_WEAKEN_FAIL_VERDICT` | `true` |
| `INCONCLUSIVE_RECLASSIFICATION_BLOCKED` | `true` |

Die beiden `METRIC_MISSING`-Codes sind zusätzliche Evidence-/Robustness-Defizite. Sie schwächen das bereits negative Baseline-Verdict nicht ab und reklassifizieren es nicht nach `INCONCLUSIVE`.

## D. Binding Digests

| Feld | Wert |
|---|---|
| `SIZING_CONFIG_DIGEST_BOUND` | `8fcd7484cdc768869fad5b914a35764f09cf42b41b78330417402272c550844a` |
| `EVALUATION_CONFIG_DIGEST_BOUND` | `db7bf773de987afbb2643ff9b761760af6b286e5e864c39d3c8d908a59082b88` |
| `BINDING_SEMANTIC_DIGEST` | `1e307564aac982eade268413cad8f3d319b865e0b769b6bb2036c8a04cab735a` |
| `FULL_CANONICAL_CHAIN_WIRED` | `true` |
| `BACKTEST_RUNTIME_DECISION_PARITY_PASS` | `true` |
| `REALISTIC_COSTS_BOUND` | `true` |
| `ROUNDTRIP_COST_BPS` | `40.0` |

## E. Evidence References

| Feld | Wert |
|---|---|
| Economic evaluation bundle | `/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/economic/vol_breakout_v1_full_canonical_offline_baseline_economic_evaluation_v0_20260710T080040Z` |
| PR #5074 merge closeout bundle | `/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/pr5074_merge_closeout_vol_breakout_v1_sizing_config_digest_binding_fix_v0_20260710T075844Z` |
| `SOURCE_MANIFEST_VERIFY_RC` | `0` |
| `ECONOMIC_MANIFEST_VERIFY_RC` | `0` |
| Closeout config ref | `config/research/vol_breakout_v1_terminal_negative_economic_evidence_closeout_v0.json` |
| Versioned binding ref | `config/research/vol_breakout_v1_versioned_research_binding_v0.json` |

## F. Authority Matrix

| Authority | Status |
|---|---|
| `PROMOTION_ELIGIBLE` | false |
| `RUNTIME_REWIRE_ADMISSIBLE` | false |
| `RUNTIME_AUTHORITY` | false |
| `IMMUTABLE_BINDING_RETRY_ALLOWED` | false |
| `SAME_BINDING_RETRY_ALLOWED` | false |
| `POLICY_RESCUE_ALLOWED` | false |
| `FURTHER_ECONOMIC_EVALUATION` | false |
| `SHADOW` / `PAPER` / `TESTNET` / `LIVE` | false |

## G. Nächster kanonischer Schritt

`NEXT_CANONICAL_STEP=NEW_RATIFIED_RESEARCH_SCOPE_OR_NEW_EVIDENCE_CLASS_REQUIRED` (read-only; nicht in diesem Slice ausführen).

`NO_RUNTIME_OR_PROMOTION_ACTION=true`
