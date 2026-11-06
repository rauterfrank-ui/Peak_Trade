# Trend-Following v2 — Offline Economic Evaluation Authorization v0

---
docs_token: DOCS_TOKEN_TREND_FOLLOWING_V2_OFFLINE_ECONOMIC_EVALUATION_AUTHORIZATION_V0
STATUS: AUTHORIZATION_RATIFICATION_COMPLETE
scope: research, offline-only, non-authorizing
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

> **Non-authorizing:** Ratifiziert die versionierte Research-Binding für `trend_following&#47;v2` und autorisiert ausschließlich eine spätere, separat zu startende Offline-Economic-Evaluation. Keine Evaluation, kein Backtest, kein Walk-Forward, kein Monte-Carlo, kein Stress, keine Promotion, kein Runtime-Rewire.

## A. Verdict

| Feld | Wert |
|---|---|
| `VERDICT` | `AUTHORIZATION_RATIFICATION_COMPLETE` |
| `PROCESS_CLASSIFICATION` | `TREND_FOLLOWING_V2_OFFLINE_ECONOMIC_EVALUATION_AUTHORIZATION_RATIFICATION_V0` |
| `SCOPE_CLASSIFICATION` | `BOUNDED_FUTURES_ONLY_OFFLINE_ECONOMIC_EVALUATION_AUTHORIZATION_RATIFICATION_V0` |
| `GO_TOKEN` | `GO_TREND_FOLLOWING_V2_OFFLINE_ECONOMIC_EVALUATION_AUTHORIZATION_V0` |
| `RESEARCH_SCOPE` | `trend_following&#47;v2` |
| `STRATEGY_ARCHETYPE` | `TREND_CONTINUATION_V2` |
| `EXCLUDED_FAILED_BINDING` | `trend_following&#47;v1` |
| `BINDING_DIGEST` | `9c624a22506c905261e58c117923ea4c0f570968d54ddf5e91f2c56f88b0d966` |
| `DATASET_DIGEST` | `0083e0502a05667f5b0ca31d374b3bef066f65aacfdb05ee020490cc1f15c638` |
| `RATIFICATION_DIGEST` | `59a2cee7dee1cd2f84454c25dfff35f1e28d96ec2d915fd5c44cb4e78706907f` |
| `ECONOMIC_EVALUATION_AUTHORIZED_FOR_SEPARATE_EXECUTION` | `true` |
| `ECONOMIC_EVALUATION_EXECUTED` | `false` |
| `NEXT_RECOMMENDED_SCOPE` | `TREND_FOLLOWING_V2_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0` |
| `NEXT_OPERATOR_GO` | `GO_TREND_FOLLOWING_V2_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0` |
| `runtime_effect` | `NONE` |
| `authority_effect` | `NONE` |

## B. Kanonische Owner

| Surface | Owner |
|---|---|
| Versioned binding | `src/research/trend_following_v2_versioned_research_binding_v0.py` |
| Authorization ratification | `src/research/trend_following_v2_offline_economic_evaluation_authorization_ratification_v0.py` |
| Materializer | `scripts/research/materialize_trend_following_v2_offline_economic_evaluation_authorization_ratification_v0.py` |
| Binding config | `config/research/trend_following_v2_versioned_research_binding_v0.json` |
| Authorization config | `config/research/trend_following_v2_offline_economic_evaluation_authorization_ratification_v0.json` |
| Contract tests | `tests/research/test_trend_following_v2_offline_economic_evaluation_authorization_ratification_v0_contract.py` |

## C. Source Evidence

| Feld | Wert |
|---|---|
| `DISCOVERY_EVIDENCE_DIR` | `/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/new_distinct_research_scope_discovery_v0_20260715T104548Z` |
| `PAIRWISE_TERMINAL_EVIDENCE_DIR` | `/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/cross_sectional_futures_pairwise_lead_lag_spillover_v1_terminal_negative_evidence_registration_v0_20260715T104146Z` |

## D. Material Difference

| Achse | Baseline terminal | `trend_following&#47;v2` |
|---|---|---|
| Signal family | Pairwise dyadic spillover graph | TREND_CONTINUATION_V2 single-slot trend continuation |
| Failed binding replaced | `cross_sectional_futures_pairwise_lead_lag_spillover&#47;v1` | `trend_following&#47;v1` |
| Instrument geometry | Cross-sectional pairwise rotation | Panel-sequential signal-density research |
| Dataset | PIT OHLCV cross-sectional research panel | Extended chronological PT1H panel with funding |

## E. Authority Boundary

Binding-Ratifikation und Authorization ≠ Evaluation-Ausführung.

| Pfad | Status |
|---|---|
| Versioned binding ratification | `ALLOWED` (this scope only) |
| Offline economic evaluation authorization | `ALLOWED_FOR_SEPARATE_EXECUTION_ONLY` |
| Economic evaluation / Backtest | `BLOCKED` |
| Walk-Forward / Monte-Carlo / Stress | `BLOCKED` |
| v1 / pairwise unchanged binding retry | `BLOCKED` |
| Parameter optimization / Threshold lowering | `BLOCKED` |
| Runtime / Shadow / Paper / Testnet / Live | `BLOCKED` |

**Keine Offline-Economic-Evaluation in diesem Scope.**

**Binding-Materialisierung ≠ Evaluation-Autorisierung der Ausführung.**

**FAILED_V1_BINDINGS_EXCLUDED=true**

**SEPARATE_OPERATOR_GO_REQUIRED_FOR_OFFLINE_ECONOMIC_EVALUATION_EXECUTION**
