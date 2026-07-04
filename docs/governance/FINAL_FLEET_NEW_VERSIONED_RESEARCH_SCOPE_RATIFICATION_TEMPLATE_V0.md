# Final Fleet New Versioned Research Scope — Ratification Template v0

---
docs_token: DOCS_TOKEN_FINAL_FLEET_NEW_VERSIONED_RESEARCH_SCOPE_RATIFICATION_TEMPLATE_V0
STATUS: RATIFICATION_TEMPLATE
scope: governance, documentation-only, non-authorizing
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

> **Non-authorizing:** Maschinenlesbare Operator-Ratifikationsvorlage für einen admissiblen neuen versionierten Research-Scope nach PR #4829. Keine Evaluation-Execution, keine Runtime-Authority, keine Ratifikation simuliert, keine Binding-Werte vorbefüllt.

## A. Verdict

| Feld | Wert |
|---|---|
| `VERDICT` | `NEW_VERSIONED_RESEARCH_SCOPE_RATIFICATION_TEMPLATE_READY_V0` |
| `PROCESS_CLASSIFICATION` | `FINAL_FLEET_NEW_VERSIONED_RESEARCH_SCOPE_RATIFICATION_TEMPLATE_V0` |
| `SCOPE_CLASSIFICATION` | `GOVERNANCE_ONLY_RATIFICATION_TEMPLATE_NO_EXECUTION` |
| `CURRENT_HEAD_BINDING` | `5d79b85800e39d345f185f224d68dab2d38d2066` |
| `PR4829_MERGE_COMMIT` | `5d79b85800e39d345f185f224d68dab2d38d2066` |
| `RATIFICATION_STATUS` | `NOT_RATIFIED` |
| `OFFLINE_EVALUATION_ALLOWED` | `false` |
| `UNMODIFIED_STEP31F_REEXECUTION_ALLOWED` | `false` |
| `NEW_VERSIONED_RESEARCH_SCOPE_REQUIRED` | `true` |
| `NEW_VERSIONED_EVIDENCE_CLASS_REQUIRED` | `false` |
| `FUTURES_ONLY` | `true` |
| `BITCOIN_DIRECTION_ALLOWED` | `false` |
| `REALISTIC_COST_MODEL_REQUIRED` | `true` |
| `VERSIONED_BINDING_REQUIRED` | `true` |
| `REPRODUCIBLE_EVIDENCE_REQUIRED` | `true` |
| `MANIFEST_VERIFIED_EVIDENCE_REQUIRED` | `true` |
| `FAIL_CLOSED_REQUIRED` | `true` |
| `CORE_SYSTEM_MUTATION_ALLOWED` | `false` |
| `CANONICAL_TRADING_LOGIC_MUTATION_ALLOWED` | `false` |
| `MASTER_V2_MUTATION_ALLOWED` | `false` |
| `DOUBLE_PLAY_MUTATION_ALLOWED` | `false` |
| `RISK_SIZING_MUTATION_ALLOWED` | `false` |
| `SAFETY_RUNTIME_MUTATION_ALLOWED` | `false` |
| `RUNTIME_REWIRE_ALLOWED` | `false` |
| `SHADOW_ALLOWED` | `false` |
| `PAPER_ALLOWED` | `false` |
| `TESTNET_ALLOWED` | `false` |
| `SCHEDULER_ALLOWED` | `false` |
| `ADAPTER_SUBMISSION_ALLOWED` | `false` |
| `ORDERS_ALLOWED` | `false` |
| `CREDENTIALS_ALLOWED` | `false` |
| `ARMING_ALLOWED` | `false` |
| `CANARY_ALLOWED` | `false` |
| `LIVE_ALLOWED` | `false` |
| `EVALUATION_EXECUTED_THIS_SCOPE` | `false` |
| `runtime_effect` | `NONE` |

**Authoritative owners (reuse, nicht ersetzen):**

- Progress registry: `docs/governance/PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md`
- Operator decision packet: `docs/governance/FINAL_FLEET_OPERATOR_DECISION_PACKET_FOR_BLOCKED_REEXECUTION_V0.md`
- Post-PR4827 readiness: `docs/governance/POST_PR4827_OPERATOR_DECISION_READINESS_UNMODIFIED_BINDING_REEXECUTION_BLOCKED_V0.md`
- Execution owner rebind: `docs/governance/FINAL_FLEET_OFFLINE_EVAL_EXECUTION_OWNER_REBIND_AND_RETRY_GOVERNANCE_V0.md`
- Execution owner: `src/research/final_research_fleet_offline_economic_evaluation_execution_v0.py`
- Fleet binding completion: `config/research/final_research_fleet_versioned_binding_completion_v0.json`

## B. Admissibility Matrix

| Klasse | Pfad | Status |
|---|---|---|
| `A_UNMODIFIED_STEP31F_REEXECUTION` | `BLOCKED` | Unveränderte historische STEP31F-FAIL-Bindings (`completion_digest=161d834e…`) dürfen nicht erneut ausgeführt werden |
| `B_SAME_BINDINGS_NEW_SHA_ONLY` | `BLOCKED` | Gleiche Bindings mit neuem HEAD/SHA allein erzeugen keine admissible Evidence-Klasse |
| `C_GOVERNANCE_REWORDING_ONLY` | `BLOCKED` | Reine Governance-Umformulierung ohne neue versionierte Research-Frage oder Evidence-Klasse |
| `D_NEW_VERSIONED_RESEARCH_SCOPE_WITH_FULL_BINDINGS` | `OPERATOR_RATIFICATION_REQUIRED` | Neuer versionierter Research-Scope mit vollständigen Bindings und separater Operator-Ratifikation |
| `E_NEW_VERSIONED_EVIDENCE_CLASS_WITH_FULL_CONTRACT` | `OPERATOR_RATIFICATION_REQUIRED` | Neue versionierte Evidence-Klasse mit vollständigem Contract und separater Operator-Ratifikation |
| `F_EVALUATION_WITHOUT_RATIFICATION` | `BLOCKED` | Offline-Evaluation ohne vorherige Operator-Ratifikation eines admissiblen Scopes oder einer Evidence-Klasse |
| `G_RUNTIME_REWIRE` | `BLOCKED` | `RUNTIME_REWIRE_ADMISSIBLE=false`; `ECONOMIC_VALIDITY_OFFLINE_GATE_PASS=false` |

## C. Blocking Semantics

| Regel | Wert |
|---|---|
| `HISTORICAL_STEP31F_BINDING_COMPLETION_DIGEST` | `161d834e5153df78a0013b6e55c4c8bd4788c775811e3678f025104a307d78f1` |
| `HISTORICAL_STEP31F_STATUS` | `COMPLETE_ALL_FAIL` |
| `PR4829_CREATES_NEW_EXECUTION_EVIDENCE_CLASS` | `false` |
| `POLICY_CHANGE_DOES_NOT_CHANGE_HISTORICAL_EVIDENCE` | `true` |
| `GOVERNANCE_REFORMULATION_ALONE_ADMITS_EXECUTION` | `false` |
| `NEGATIVE_EVIDENCE_CAN_NOT_BE_RECLASSIFIED_BY_GOVERNANCE` | `true` |

## D. Ratification Input Matrix (Pflichtfelder, keine vorbefüllten Werte)

| INPUT_KEY | required_for | current_value | required_value_or_decision |
|---|---|---|---|
| `strategy_id` | Klasse D | `MISSING` | Operator-ratifizierte Strategy-ID für neuen Research-Scope |
| `strategy_version` | Klasse D | `MISSING` | Versionierte Strategy-Version |
| `parameter_binding` | Klasse D | `MISSING` | Versioniertes Parameter-Binding mit Digest |
| `dataset_binding` | Klasse D | `MISSING` | Versioniertes Dataset-Binding mit Digest |
| `period_binding` | Klasse D | `MISSING` | Versioniertes Perioden-Binding |
| `instrument_binding` | Klasse D | `MISSING` | Futures-only Instrument-Binding |
| `fee_model_binding` | Klasse D | `MISSING` | Realistisches Fee-Model-Binding |
| `slippage_model_binding` | Klasse D | `MISSING` | Realistisches Slippage-Model-Binding |
| `funding_model_binding` | Klasse D | `MISSING` | Realistisches Funding-Model-Binding |
| `execution_model_binding` | Klasse D | `MISSING` | Offline-only Execution-Model-Binding |
| `economic_policy_binding` | Klasse D | `MISSING` | Unveränderte Economic-Policy-Binding oder explizite neue Version |
| `implementation_digest` | Klasse D/E | `MISSING` | Reproduzierbarer Implementation-Digest |
| `config_digest` | Klasse D/E | `MISSING` | Reproduzierbarer Config-Digest |
| `data_digest` | Klasse D/E | `MISSING` | Reproduzierbarer Data-Digest |
| `evidence_class_id` | Klasse E | `MISSING` | Neue versionierte Evidence-Klassen-ID (optional für Klasse D) |
| `expected_output_contract` | Klasse D/E | `MISSING` | Maschinenlesbarer Output-Contract vor Evaluation |

## E. Required Operator Inputs For Any Future Execution

| INPUT_KEY | required_for | current_value | required_value_or_decision |
|---|---|---|---|
| `OPERATOR_GO_NEW_VERSIONED_RESEARCH_SCOPE` | Klasse D | `MISSING` | Benannter Hypothesis-Scope + versionierte Binding-Ratifikation + explizites Operator-GO |
| `OPERATOR_GO_NEW_VERSIONED_EVIDENCE_CLASS` | Klasse E | `MISSING` | Neue versionierte Evidence-Klasse + explizites Operator-GO ohne historische FAIL-Evidence zu überschreiben |
| `OPERATOR_GO_OFFLINE_ECONOMIC_EVALUATION_EXECUTION` | Offline Evaluation nach D oder E | `MISSING` | Separates Execution-GO nach Ratifikation; offline-only, futures-only, realistic-cost, manifest-verified |

## F. Safe Next Action

```text
NEXT_ACTION=OPERATOR_RATIFICATION_REQUIRED_FOR_NEW_VERSIONED_RESEARCH_SCOPE_OR_NEW_VERSIONED_EVIDENCE_CLASS_V0
```
