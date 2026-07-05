# Final Research Fleet New Evidence Class Scope v0

---
docs_token: DOCS_TOKEN_FINAL_RESEARCH_FLEET_NEW_EVIDENCE_CLASS_SCOPE_V0
STATUS: NEW_EVIDENCE_CLASS_SCOPE_DEFINED
scope: governance, documentation-only, non-authorizing
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

> **Non-authorizing:** Definiert einen admissiblen neuen versionierten Research-/Evidence-Class-Scope für die Final Research Fleet nach Fail-Closed-Blockade der unveränderten STEP31F-Re-Execution. Keine Offline-Evaluation-Execution, keine Runtime-Authority, keine Policy-Exception.

## A. Verdict

| Feld | Wert |
|---|---|
| `VERDICT` | `NEW_EVIDENCE_CLASS_SCOPE_DEFINED` |
| `PROCESS_CLASSIFICATION` | `BOUNDED_FINAL_RESEARCH_FLEET_NEW_EVIDENCE_CLASS_SCOPE_DEFINITION_V0` |
| `SCOPE_CLASSIFICATION` | `GOVERNANCE_ONLY_NEW_EVIDENCE_CLASS_SCOPE_DEFINITION_NO_EXECUTION` |
| `GO_TOKEN` | `GO_BOUNDED_FINAL_RESEARCH_FLEET_NEW_EVIDENCE_CLASS_SCOPE_DEFINITION_PR_V0` |
| `GO_TOKEN_CONSUMED` | `false` (Scope-Definition only; consumed at PR merge by operator workflow) |
| `BINDING_READY` | `true` |
| `BINDING_SPEC_STATUS` | `NEW_EVIDENCE_CLASS_SCOPE_DEFINED` |
| `EVIDENCE_CLASS` | `NEW_VERSIONED_RESEARCH_SCOPE_NOT_UNCHANGED_RETRY` |
| `EVIDENCE_CLASS_ID` | `FINAL_RESEARCH_FLEET_OKX_FULL_PANEL_NEW_EVIDENCE_CLASS_V0` |
| `FINAL_RESEARCH_FLEET` | `trend_following,bollinger_bands,momentum_1h` |
| `PREVIOUS_COMPLETION_DIGEST` | `161d834e5153df78a0013b6e55c4c8bd4788c775811e3678f025104a307d78f1` |
| `PREVIOUS_COMPLETION_STATUS` | `TERMINAL_FAILED_OR_ROBUSTNESS_FAILED` |
| `NEW_BINDING_COMPLETION_DIGEST` | `c5e3b5fe6b688b49dbd2b210fd63bdea79201d64820591f87091b4e20689a9dd` |
| `RETRY_UNCHANGED_BINDING_ALLOWED` | `false` |
| `POLICY_EXCEPTION_ALLOWED` | `false` |
| `CLASS_D_OWNER_MIXING` | `false` |
| `CANDIDATE_RATIFIED` | `false` |
| `ECONOMIC_EVALUATION_AUTHORIZED` | `false` |
| `EVALUATION_EXECUTED_THIS_SCOPE` | `false` |
| `RUNTIME_AUTHORITY` | `false` |
| `runtime_effect` | `NONE` |
| `authority_effect` | `NONE` |

**Authoritative owners (reuse, nicht ersetzen):**

- Scope config: `config/research/final_research_fleet_new_evidence_class_scope_v0.json`
- New binding completion (reuse): `config/research/final_research_fleet_okx_full_panel_versioned_binding_completion_v0.json`
- New offline scope ratification (reuse): `config/research/final_research_fleet_okx_full_panel_offline_economic_evaluation_scope_ratification_v0.json`
- Materialization/execution owner (reuse): `src/research/final_research_fleet_okx_full_panel_versioned_binding_and_offline_economic_evaluation_v0.py`
- Execution runner (reuse): `scripts/ops/run_final_research_fleet_okx_full_panel_versioned_binding_and_offline_economic_evaluation_v0.py`
- Blocked historical completion: `config/research/final_research_fleet_versioned_binding_completion_v0.json`
- Progress registry: `docs/governance/PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md`

## B. Fail-Closed Blocker Addressed

| Blocker | Resolution |
|---|---|
| `UNMODIFIED_BINDING_RETRY_BLOCKED` | Neuer `completion_digest=c5e3b5fe…` ≠ historisch `161d834e…` |
| `NEW_EVIDENCE_CLASS_REQUIRED_FOR_REEXECUTION` | Neue Evidence-Class `FINAL_RESEARCH_FLEET_OKX_FULL_PANEL_NEW_EVIDENCE_CLASS_V0` |
| `GO_TOKEN_NOT_REGISTERED` (Execution) | Separates Execution-GO dokumentiert; Scope-Definition ändert alte Token-Liste nicht |
| `ORIGIN_MAIN_SHA_MISMATCH` (STEP31F runner) | Neuer Scope nutzt OKX-full-panel Owner, nicht STEP31F-Retry-Pfad |
| Policy-Exception | **Nicht verwendet** |

## C. Substantielle Binding-Deltas (vs. STEP31F)

| Dimension | STEP31F (blocked) | New Evidence Class (admissible) |
|---|---|---|
| `dataset_binding` | `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1` | `okx_full_panel_historical_funding_archive_v0` |
| `data_digest` | `815b3316…` | `0bfa4df4…` |
| `period_binding` | `2024-05-25..2024-06-01` | `2024-05-01..2024-09-01` |
| `instrument_binding` | 6 instruments, cross-sectional manifest | 118 instruments, lifecycle admissible panel |
| `evidence_class_binding` | `step31f_pit_cross_sectional_v0` | `FINAL_RESEARCH_FLEET_OKX_FULL_PANEL_NEW_EVIDENCE_CLASS_V0` |
| `implementation_digest` | `0c6a4ec7…` | `7c8dc31d…` |
| `parameter_binding` | unchanged | unchanged (not sole novelty) |
| Cost stack | unchanged | unchanged (not sole novelty) |

## D. Excluded Paths

| Pfad | Status |
|---|---|
| Unveränderte STEP31F-Completion `161d834e…` | `BLOCKED` |
| Class-D owner mixing | `BLOCKED` |
| Exit-Companion redesign | `BLOCKED` (remains `PARKED_COUNTS_ONLY_FAILED`) |
| Policy threshold lowering | `BLOCKED` |
| Parameter optimization | `BLOCKED` |

## E. Safe Next Action

```text
NEXT_ACTION=REQUEST_OPERATOR_GO_FOR_BOUNDED_NEW_EVIDENCE_CLASS_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0
```

Separate Operator-Ratifikation und Execution-GO erforderlich. Keine Evaluation in diesem Scope.
