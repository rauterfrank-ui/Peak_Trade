# Cross-Sectional MA-Crossover Panel Rank-Rotation v0 — Terminal Negative Evidence and Supersession Registration

---
docs_token: DOCS_TOKEN_CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_TERMINAL_NEGATIVE_ECONOMIC_EVIDENCE_AND_SUPERSESSION_REGISTRATION_V0
STATUS: TERMINAL_NEGATIVE_EVIDENCE_AND_SUPERSESSION_REGISTRATION_COMPLETE
scope: governance, documentation-only, non-authorizing
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

> **Non-authorizing:** Registriert die korrigierte manifest-verifizierte Offline-Economic-Evidence (`20260710T101815Z`) als kanonisches Ergebnis für `cross_sectional_ma_crossover_panel_rank_rotation&#47;v0`, superseded die accounting-incomplete Original-Evaluation (`20260710T101306Z`), und blockiert Same-Binding-Retry. Keine Economic-Reevaluation, keine Promotion, kein Runtime-Rewire.

## A. Zweck

PR #5080 korrigierte die End-of-Window-Accounting-Reconciliation (force-close policy). Diese Registrierung ratifiziert die korrigierte Evaluation als kanonische terminal-negative Evidence und verzeichnet die Original-Evaluation als superseded wegen accounting incompleteness.

## B. Scope

| Feld | Wert |
|---|---|
| `PROCESS_CLASSIFICATION` | `CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_TERMINAL_NEGATIVE_ECONOMIC_EVIDENCE_AND_SUPERSESSION_REGISTRATION_V0` |
| `GO_TOKEN` | `GO_RATIFY_CORRECTED_TERMINAL_NEGATIVE_EVIDENCE_AND_SUPERSESSION_REGISTRATION_V0` |
| `STRATEGY_ID` | `cross_sectional_ma_crossover_panel_rank_rotation` |
| `STRATEGY_VERSION` | `v0` |
| `RESEARCH_SCOPE` | `cross_sectional_ma_crossover_panel_rank_rotation&#47;v0` |
| `PRE_MERGE_ORIGIN_MAIN` | `8ea5670cda60f9eb3656ef1aa483ed6f823457b5` |
| `SOURCE_PR` | `5080` |
| `SOURCE_MERGE_COMMIT` | `48dd6e367f9e61361861b6d8a0d250def424f222` |
| `offline_only` | `true` |
| `non_authorizing` | `true` |

Ausgeschlossen: Economic-Reevaluation, Backtest-Retry, Walk-Forward-Retry, Monte-Carlo-Retry, Stress-Retry, Parameteränderung, Threshold-Lowering, Promotion, Runtime, Shadow, Paper, Testnet, Scheduler, Orders, Credentials, Arming, Live.

## C. Evidence Bundle Referenzen

| Feld | Wert |
|---|---|
| `CANONICAL_EVALUATION_BUNDLE` | `/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/cross_sectional_ma_crossover_panel_rank_rotation_v0_offline_economic_evaluation_20260710T101815Z` |
| `CANONICAL_MANIFEST_DIGEST` | `3a132a93e01a209c3d0c58f5573d0e04ab588ba563048d58419c03450b1b609c` |
| `SUPERSEDED_EVALUATION_BUNDLE` | `/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/cross_sectional_ma_crossover_panel_rank_rotation_v0_offline_economic_evaluation_20260710T101306Z` |
| `SUPERSEDED_MANIFEST_DIGEST` | `1366b57fb19f0b8ea90f37b1ae2111a1b7599eeefa2728fd04650c60162b36f6` |
| `PR5080_CLOSEOUT_DIR` | `/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/pr5080_merge_closeout_cs_ma_crossover_panel_rank_rotation_v0_accounting_reconciliation_20260710T102332Z` |
| `MANIFEST_VERIFY_RC` | `0` |
| `Governance config ref` | `config/research/cross_sectional_ma_crossover_panel_rank_rotation_v0_terminal_negative_economic_evidence_and_supersession_registration_v0.json` |

## D. Supersession und Accounting

| Feld | Wert |
|---|---|
| `SUPERSESSION_REASON` | `ORIGINAL_EVALUATION_ACCOUNTING_INCOMPLETE_OPEN_END_OF_WINDOW_POSITION_AND_WRONG_RECONCILIATION_IDENTITY` |
| `ACCOUNTING_RECONCILIATION_PASS` | `true` |
| `ACCOUNTING_FAILURE_CLASS` | `FORCED_END_OF_WINDOW_LIQUIDATION` |
| `ACCOUNTING_ROOT_CAUSE` | `open_position_at_window_end_without_force_close_trade_ledger_entry;wrong_reconciliation_identity` |
| `END_OF_WINDOW_POLICY` | `force_close_at_window_end_inclusive_v0` |
| `TRADING_LOGIC_CHANGED` | `false` |
| `BINDING_CHANGED` | `false` |
| `DATASET_CHANGED` | `false` |
| `COST_POLICY_CHANGED` | `false` |

## E. Verdict und zentrale Metriken (korrigiert, kanonisch)

| Feld | Wert |
|---|---|
| `VERDICT` | `PASS` |
| `BASELINE_VERDICT` | `FAIL` |
| `TERMINAL_ECONOMIC_DECISION` | `FAIL` |
| `TERMINAL_FAILURE_CLASS` | `NEGATIVE_ECONOMIC_BASELINE_AND_INSUFFICIENT_TRADE_SAMPLE` |
| `EVALUATION_EXECUTED` | `true` |
| `ECONOMIC_VALIDITY_OFFLINE_GATE_PASS` | `false` |
| `PROMOTION_GRANTED` | `false` |
| `RUNTIME_AUTHORITY_TOUCHED` | `false` |
| `UNCHANGED_RETRY_ALLOWED` | `false` |
| `RETRY_ALLOWED_SAME_BINDING` | `false` |
| `TERMINAL_NEGATIVE_EVIDENCE_FOR_UNCHANGED_BINDING` | `true` |
| `net_return` | `-0.152906` |
| `trade_count` | `4` |
| `sample_sufficiency_status` | `INSUFFICIENT_TRADE_SAMPLE` |
| `walk_forward_status` | `NOT_EXECUTED_BASELINE_NEGATIVE` |
| `monte_carlo_status` | `NOT_EXECUTED_BASELINE_NEGATIVE` |
| `stress_status` | `NOT_EXECUTED_BASELINE_NEGATIVE` |

## F. Binding Digests (unverändert)

| Feld | Wert |
|---|---|
| `BINDING_DIGEST` | `89f80951dd71e43168b9b37b0d6f04d57ba7ca025fcd4923c9901d0f244f43e6` |
| `CONFIG_DIGEST` | `eaca6226b6e040580227c8380c86a3aaa4f3e3bdad9292b37d9cbef736405141` |
| `DATA_DIGEST` | `b0eb7802c269bcab987d2025fe1e960b83079d5ac5f305799e0867661d42f2e0` |
| `UNIVERSE_DIGEST` | `ccc36aa52d9df3aa2067fbc0a75aea6ae33a458583ec8a15b08d69f54b8b9a8b` |

## G. Nächster kanonischer Schritt

`NEXT_CANONICAL_STEP=NEW_RATIFIED_RESEARCH_SCOPE_OR_NEW_EVIDENCE_CLASS_REQUIRED`

`authority_effect=NONE` · `runtime_effect=NONE`
