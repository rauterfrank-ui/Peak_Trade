# OKX Full-Panel Cross-Sectional Ranking Strategy Archetype Evidence Class Scope v0

---
docs_token: DOCS_TOKEN_OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_EVIDENCE_CLASS_SCOPE_V0
STATUS: NEW_EVIDENCE_CLASS_SCOPE_DEFINED
scope: governance, documentation-only, non-authorizing
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

> **Non-authorizing:** Ratifiziert ausschließlich die neue Evidence-Class-Definition `OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_V0` und ihre Bindungsanforderungen nach terminal failed Final Research Fleet (PR #4846/#4847/#4848). Keine Offline-Economic-Evaluation, keine Runtime-Authority, keine Promotion, keine Kandidatenratifikation.

## A. Verdict

| Feld | Wert |
|---|---|
| `VERDICT` | `NEW_EVIDENCE_CLASS_SCOPE_DEFINED` |
| `PROCESS_CLASSIFICATION` | `OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_EVIDENCE_CLASS_SCOPE_DEFINITION_V0` |
| `SCOPE_CLASSIFICATION` | `GOVERNANCE_ONLY_NEW_EVIDENCE_CLASS_SCOPE_DEFINITION_NO_EXECUTION` |
| `GO_TOKEN` | `GO_OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_EVIDENCE_CLASS_SCOPE_DEFINITION_V0` |
| `GO_TOKEN_CONSUMED` | `false` (Scope-Definition only; consumed at PR merge by operator workflow) |
| `SCOPE_DEFINED` | `true` |
| `NEW_EVIDENCE_CLASS_RATIFIED_FOR_SCOPE_DEFINITION` | `true` |
| `BINDING_READY` | `false` (scope defined; versionierte Evaluation-Bindings noch nicht materialisiert) |
| `BINDING_SPEC_STATUS` | `NEW_EVIDENCE_CLASS_SCOPE_DEFINED` |
| `EVIDENCE_CLASS` | `OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_NOT_FAILED_FLEET_RETRY` |
| `EVIDENCE_CLASS_ID` | `OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_V0` |
| `STRATEGY_ARCHETYPE_ID` | `cross_sectional_ranking_selection` |
| `CANDIDATE_RATIFIED` | `false` |
| `ECONOMIC_EVALUATION_AUTHORIZED` | `false` |
| `EVALUATION_EXECUTED_THIS_SCOPE` | `false` |
| `ECONOMIC_VALIDITY_OFFLINE_GATE_PASS` | `false` |
| `PROMOTION_AUTHORIZED` | `false` |
| `RUNTIME_REWIRE_ADMISSIBLE` | `false` |
| `RUNTIME_AUTHORITY` | `false` |
| `FURTHER_SAME_BINDING_RETRY_ALLOWED` | `false` |
| `REQUIRES_SEPARATE_OPERATOR_GO_FOR_EVALUATION` | `true` |
| `REQUIRES_FULL_PANEL_BINDING` | `true` |
| `NARROW_ADAPTER_ETH_ONLY_BINDING_DISALLOWED_FOR_THIS_SCOPE` | `true` |
| `runtime_effect` | `NONE` |
| `authority_effect` | `NONE` |

**Authoritative owners (reuse, nicht ersetzen):**

- Scope config: `config/research/okx_full_panel_cross_sectional_ranking_strategy_archetype_evidence_class_scope_v0.json`
- Cross-sectional ranking semantics (reuse): `config/research/cross_sectional_relative_strength_non_bitcoin_perpetuals_v0_ranking_semantics_binding_v0.json`
- Cross-sectional research binding (reuse reference): `config/research/cross_sectional_relative_strength_v0_versioned_research_binding_v0.json`
- Failed fleet scope (blocked, reuse): `config/research/final_research_fleet_new_evidence_class_scope_v0.json`
- Failed fleet evaluation evidence: PR #4846 offline evaluation bundle
- Forensics source evidence: `final_research_fleet_post_failure_forensics_and_new_evidence_class_candidate_discovery_read_only_v0_20260705T011307Z`
- Progress registry: `docs/governance/PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md`

## B. Zentrale Hypothese

Ein cross-sectional Ranking-/Selection-Archetype über das echte OKX-Full-Panel kann andere Evidence liefern als die terminal failed Single-Instrument-/Narrow-Adapter-Fleet (`trend_following&#47;v1`, `bollinger_bands&#47;v1`, `momentum_1h&#47;v1`). Die neue Evidence Class ist nur zulässig, weil sie **Archetyp**, **Instrument-/Universe-Binding** und **Period-/Panel-Binding** ändert — nicht dieselbe failed Final-Fleet-Bindung wiederholt.

PR #4846 deklarierte OKX-Full-Panel-Metadaten (118 Instrumente, Mai–Sep 2024), führte aber alle drei Kandidaten über `NARROW_ADAPTER_INST_ETH_USDT_PERP` auf `ETH-USDT-SWAP` mit einem 7-Tage-Fenster (`2024-05-25..2024-06-01`) aus. Diese Scope-Definition schließt diesen Evaluationspfad explizit aus.

## C. Pflichtabgrenzung (Excluded Failed Bindings)

| Exclusion | Status |
|---|---|
| Retry `trend_following&#47;v1` | `BLOCKED` |
| Retry `bollinger_bands&#47;v1` | `BLOCKED` |
| Retry `momentum_1h&#47;v1` | `BLOCKED` |
| Retry digest `161d834e5153df78a0013b6e55c4c8bd4788c775811e3678f025104a307d78f1` (STEP31F) | `BLOCKED` |
| Retry digest `c5e3b5fe6b688b49dbd2b210fd63bdea79201d64820591f87091b4e20689a9dd` (failed fleet binding completion) | `BLOCKED` |
| Retry digest `64da0eae56a70ad0661398db14d712f6d58d6ea9f6ad0dbb73f3de2b01d11d67` (failed fleet scope) | `BLOCKED` |
| Evidence class `FINAL_RESEARCH_FLEET_OKX_FULL_PANEL_NEW_EVIDENCE_CLASS_V0` retry | `BLOCKED` |
| Parameter optimization | `BLOCKED` |
| Schwellenwertabsenkung | `BLOCKED` |
| Policy-Rettung / economic_validity_policy_v1 relaxation | `BLOCKED` |
| Reinterpretation `ROBUSTNESS_FAILED` als PASS | `BLOCKED` |
| `NARROW_ADAPTER_INST_ETH_USDT_PERP` als Full-Panel-Evaluation | `BLOCKED` |
| 7-Tage-Holdout-Verengung bei Full-Panel Mai–Sep 2024 Claim | `BLOCKED` |

## D. Substantielle Binding-Deltas (vs. failed Final Fleet)

| Dimension | Failed Final Fleet (PR #4846) | New Evidence Class (admissible scope) |
|---|---|---|
| `strategy_archetype_id` | single-instrument trend/momentum/mean-reversion fleet | cross-sectional ranking selection |
| `instrument_binding` | narrow adapter ETH-USDT-SWAP only | OKX full-panel lifecycle-admissible panel (118 instruments target) |
| `period_binding` | 7-day holdout slice `2024-05-25..2024-06-01` | full Mai–Sep 2024 coverage `2024-05-01..2024-09-01` (soweit archivierte Coverage) |
| `ranking_policy_binding` | not bound (fleet archetypes) | required before evaluation |
| `selection_policy_binding` | not bound | required before evaluation |
| `portfolio_construction_policy_binding` | not bound | required if offline portfolio evaluation |
| `evidence_class_binding` | `FINAL_RESEARCH_FLEET_OKX_FULL_PANEL_NEW_EVIDENCE_CLASS_V0` | `OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_V0` |

## E. Pflichtbindungen vor späterer Evaluation

Eine spätere Offline-Evaluation ist **erst nach separatem Operator-GO** zulässig und erfordert versionierte Bindung aller folgenden Dimensionen **vor** Execution:

| Binding-Dimension | Status in diesem Scope |
|---|---|
| `evidence_class_id` | `OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_V0` (defined) |
| `strategy_archetype_id` | `cross_sectional_ranking_selection` (defined; candidate strategy TBD) |
| `strategy_version` | `TBD_AT_BINDING_MATERIALIZATION` |
| `candidate_id` | `TBD_AT_BINDING_MATERIALIZATION` |
| OKX full-panel instrument universe binding | required before evaluation |
| instrument inclusion/exclusion rules | required before evaluation |
| dataset binding | `okx_full_panel_historical_funding_archive_v0` (target; verify at materialization) |
| period binding (Mai–Sep 2024 full coverage) | required before evaluation |
| timeframe binding | required before evaluation |
| ranking policy binding | required before evaluation |
| selection policy binding | required before evaluation |
| portfolio construction policy binding | required if offline portfolio evaluation |
| fee model binding | unchanged default unless separately ratified |
| slippage model binding | unchanged default unless separately ratified |
| funding model binding | unchanged default unless separately ratified |
| execution model binding | unchanged default unless separately ratified |
| economic policy binding | unchanged default unless separately ratified |
| `implementation_digest` | required before evaluation |
| `config_digest` | required before evaluation |
| `data_digest` | required before evaluation |
| `excluded_failed_bindings` | must include all blocked paths in Section C |
| no-runtime-authority statement | required; always true |

## F. Safe Next Action

```text
NEXT_ACTION=NO_RUNTIME_OR_PROMOTION_ACTION
FUTURE_EVALUATION=REQUIRES_SEPARATE_OPERATOR_GO_AND_VERSIONED_BINDING_MATERIALIZATION
```

Keine Evaluation in diesem Scope. Nach Merge/Closeout optional separate Offline-Evaluation nur mit explizitem Operator-GO und vollständiger Bindungsmaterialisierung.
