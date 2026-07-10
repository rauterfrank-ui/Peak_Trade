# El Karoui Vol Model v1 — Repaired Binding Inconclusive Baseline Evidence and Unchanged Retry Block

---
docs_token: DOCS_TOKEN_EL_KAROUI_VOL_MODEL_V1_REPAIRED_BINDING_INCONCLUSIVE_BASELINE_EVIDENCE_AND_UNCHANGED_RETRY_BLOCK_V0
STATUS: REPAIRED_BINDING_INCONCLUSIVE_BASELINE_EVIDENCE_REGISTRATION_COMPLETE
scope: governance, documentation-only, non-authorizing
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

> **Non-authorizing:** Registriert die post-repair manifest-verifizierte Offline-Baseline-Reevaluation (`20260710T135114Z`) als `INCONCLUSIVE` für das reparierte Binding `el_karoui_vol_model&#47;v1`, erhält prior blocked evaluation und Repair-PR-#5089-Linie, und blockiert Unchanged-Binding-Retry ohne Economic Reevaluation oder Runtime-Authority.

## A. Zweck

Nach Abschluss von PR #5089 (Sizing-Config-Digest-Repair) und der einmaligen post-repair Reevaluation wird das reparierte Binding `2ba82dd9…` als `TERMINAL_INCONCLUSIVE_INSUFFICIENT_SAMPLE` registriert. Die authoritative Baseline-Entscheidung bleibt `INCONCLUSIVE` (nicht `TERMINAL_NEGATIVE`). Unchanged-Binding-Retry, Parameter-Relaxation und Policy-Rescue sind blockiert. Weitere Forschung erfordert einen neuen distinct scope oder eine neue evidence class.

## B. Scope

| Feld | Wert |
|---|---|
| `PROCESS_CLASSIFICATION` | `BOUNDED_FUTURES_ONLY_REPAIRED_BINDING_INCONCLUSIVE_BASELINE_EVIDENCE_AND_UNCHANGED_RETRY_BLOCK_V0` |
| `GO_TOKEN` | `GO_PERSIST_EL_KAROUI_VOL_MODEL_V1_REPAIRED_BINDING_INCONCLUSIVE_BASELINE_EVIDENCE_AND_BLOCK_UNCHANGED_RETRY_V0` |
| `STRATEGY_ID` | `el_karoui_vol_model` |
| `STRATEGY_VERSION` | `v1` |
| `RESEARCH_SCOPE` | `el_karoui_vol_model&#47;v1` |
| `BINDING_CLASSIFICATION` | `SAME_SEMANTIC_BINDING_NEW_CRYPTOGRAPHIC_IDENTITY` |
| `PRE_MERGE_ORIGIN_MAIN` | `5177b8af165cdce94a6589b9e5fa099fc5f9f3cc` |
| `offline_only` | `true` |
| `non_authorizing` | `true` |

Ausgeschlossen: Economic-Reevaluation, Backtest-Retry, Walk-Forward, Monte-Carlo, Stress, Parameteränderung, Threshold-Lowering, Promotion, Runtime, Shadow, Paper, Testnet, Scheduler, Orders, Credentials, Arming, Live.

## C. Evidence Bundle Referenzen

| Feld | Wert |
|---|---|
| `CANONICAL_EVALUATION_BUNDLE` | `/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/el_karoui_vol_model_v1_bound_offline_economic_baseline_evaluation_v0_20260710T135114Z` |
| `CANONICAL_MANIFEST_DIGEST` | `11de71c7b7c19e90700c358ae88d3b049b75679fecfc2736ab52df1d759ac941` |
| `PRIOR_BLOCKED_EVALUATION_BUNDLE` | `/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/el_karoui_vol_model_v1_bound_offline_economic_baseline_evaluation_v0_20260710T130747Z` |
| `REPAIR_CLOSEOUT_DIR` | `/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/pr5089_merge_closeout_el_karoui_vol_model_v1_sizing_config_digest_same_semantic_binding_new_cryptographic_identity_repair_v0_20260710T134808Z` |
| `MANIFEST_VERIFY_RC` | `0` |
| `Governance config ref` | `config/research/el_karoui_vol_model_v1_repaired_binding_inconclusive_baseline_evidence_and_unchanged_retry_block_v0.json` |

## D. Inconclusive Baseline Verdict

| Feld | Wert |
|---|---|
| `VERDICT` | `PASS` |
| `BASELINE_VERDICT` | `INCONCLUSIVE` |
| `TERMINAL_ECONOMIC_DECISION` | `INCONCLUSIVE` |
| `TERMINAL_STATUS` | `TERMINAL_INCONCLUSIVE_INSUFFICIENT_SAMPLE` |
| `TERMINAL_FAILURE_CLASS` | `INCONCLUSIVE_BASELINE_INSUFFICIENT_TRADE_SAMPLE` |
| `PRIMARY_CAUSE_CLASS` | `INSUFFICIENT_TRADE_SAMPLE_AFTER_REPAIRED_BINDING_REEVALUATION` |
| `ACCOUNTING_RECONCILIATION_PASS` | `true` |
| `GROSS_RETURN` | `-0.0186` |
| `NET_RETURN` | `-0.0186` |
| `PROFIT_FACTOR` | `0.249` |
| `SHARPE` | `-0.198` |
| `MAX_DRAWDOWN` | `-0.0248` |
| `TRADE_COUNT` | `6` |
| `POLICY_MINIMUM_TRADE_COUNT` | `50` |
| `SAMPLE_SUFFICIENCY_STATUS` | `INSUFFICIENT_TRADE_SAMPLE` |
| `ECONOMIC_VALIDITY_OFFLINE_GATE_PASS` | `false` |
| `TERMINAL_NEGATIVE_EVIDENCE_FOR_UNCHANGED_BINDING` | `false` |
| `TERMINAL_INCONCLUSIVE_EVIDENCE_FOR_UNCHANGED_BINDING` | `true` |
| `UNCHANGED_RETRY_ALLOWED` | `false` |
| `PROMOTION_ADMISSIBLE` | `false` |
| `RUNTIME_REWIRE_ADMISSIBLE` | `false` |
| `PARAMETER_RELAXATION_AUTHORIZED` | `false` |
| `POLICY_RESCUE_ALLOWED` | `false` |
| `NEW_DISTINCT_RESEARCH_SCOPE_OR_NEW_EVIDENCE_CLASS_REQUIRED` | `true` |

## E. Cryptographic Identity Relation

| Feld | Alt | Neu |
|---|---|---|
| `BINDING_DIGEST` | `223845f2047779218390fc245c3f2ebb04631bb068139e3d40731781906d099b` | `2ba82dd901c940a5d41d2aabd3ddeb693dbbf7cdd1f0308275d11b6df4d988b3` |
| `CONFIG_DIGEST` | `1b45ed11abdc5310f14a160200a63bb488c55d9677cd6caec0aa4bb202969d61` | `5d0afaed79c84a34bc0e92fc04c150dca1c0b828af4ee44b37384d0cd5943afc` |
| `SIZING_CONFIG_DIGEST` | `d49d85ede512dda6d3200dbf9a50d306a423de4279767d228d20d28d88975dd8` | `dd9152621c58c1ed283c7b42601d66cf4fdcd1bb009f439d8583ebef64dc4516` |

Semantische Binding-Identität unverändert; kryptographische Identität durch PR #5089 geändert.

## F. Runtime / Authority

| Feld | Wert |
|---|---|
| `RUNTIME_EFFECT` | `NONE` |
| `AUTHORITY_EFFECT` | `NONE` |
| `NEXT_CANONICAL_STEP` | `NEW_DISTINCT_RESEARCH_SCOPE_OR_NEW_EVIDENCE_CLASS_REQUIRED` |
