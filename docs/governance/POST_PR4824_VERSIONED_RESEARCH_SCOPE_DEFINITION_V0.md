# Post-PR4824 Versioned Research Scope Definition v0

---
docs_token: DOCS_TOKEN_POST_PR4824_VERSIONED_RESEARCH_SCOPE_DEFINITION_V0
STATUS: VERSIONED_RESEARCH_SCOPE_DEFINITION
scope: governance, documentation-only, non-authorizing
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

> **Non-authorizing:** Dieses Dokument ratifiziert die versionierte Research-Scope-Definition nach PR #4824. Es ersetzt **keine** authoritative Registry, Contract- oder Evidence-Owner. Keine Runtime-, Order-, Promotion- oder Evaluation-Execution-Authority.

## A. Scope Verdict

| Feld | Wert |
|---|---|
| `VERDICT` | `POST_PR4824_VERSIONED_RESEARCH_SCOPE_DEFINITION_RATIFIED` |
| `PROCESS_CLASSIFICATION` | `BOUNDED_VERSIONED_RESEARCH_SCOPE_DEFINITION_V0` |
| `SCOPE_CLASSIFICATION` | `GOVERNANCE_ONLY_RESEARCH_SCOPE_DEFINITION` |
| `BASELINE_ORIGIN_MAIN` | `2ee068f058d265d6cf7e973bb10b103f450d5a2c` |
| `PR4824_MERGE_COMMIT` | `2ee068f058d265d6cf7e973bb10b103f450d5a2c` |
| `FUTURES_ONLY` | `true` |
| `BITCOIN_DIRECTION_ALLOWED` | `false` |
| `SPOT_ALLOWED` | `false` |
| `SYNTHETIC_SPOT_ALLOWED` | `false` |
| `LIVE_AUTHORIZED` | `false` |
| `RUNTIME_REWIRE_ADMISSIBLE` | `false` |
| `ECONOMIC_EVALUATION_AUTHORIZED` | `false` |
| `EVALUATION_EXECUTED_THIS_SCOPE` | `false` |
| `CORE_SYSTEM_MUTATION_ALLOWED` | `false` |
| `CANONICAL_TRADING_LOGIC_MUTATION_ALLOWED` | `false` |
| `MASTER_V2_MUTATION_ALLOWED` | `false` |
| `DOUBLE_PLAY_MUTATION_ALLOWED` | `false` |
| `RISK_SIZING_MUTATION_ALLOWED` | `false` |
| `SAFETY_RUNTIME_MUTATION_ALLOWED` | `false` |
| `FINAL_RESEARCH_FLEET_STATUS` | `BINDINGS_REQUIRED_BEFORE_EVALUATION` |
| `FINAL_RESEARCH_FLEET` | `trend_following,bollinger_bands,momentum_1h` |
| `FAILED_BINDINGS_ARE_NEGATIVE_EVIDENCE` | `true` |
| `FAILED_BINDINGS_MAY_NOT_BE_RETRIED_UNCHANGED` | `true` |
| `POLICY_CHANGE_DOES_NOT_CHANGE_HISTORICAL_EVIDENCE` | `true` |
| `UNMODIFIED_RE_EXECUTION_ADMISSIBLE` | `false` |
| `runtime_effect` | `NONE` |
| `promotion_effect` | `NONE` |
| `rewire_effect` | `NONE` |
| `evaluation_executed` | `false` |

**Authoritative owners (reuse, nicht ersetzen):**

- Progress registry: `docs/governance/PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md`
- Operator decision packet (PR #4823): `docs/governance/POST_PR4823_OPERATOR_DECISION_PACKET_FOR_NEW_RESEARCH_SCOPE_DEFINITION_V0.md`
- Fleet binding completion: `config/research/final_research_fleet_versioned_binding_completion_v0.json`
- Offline evaluation scope ratification: `config/research/final_research_fleet_offline_economic_evaluation_scope_ratification_v0.json`
- Fleet ratification envelope: `config/research/final_research_fleet_v0_fleet_ratification_v0.json`

## B. Versioned Research Scope Definition

Der nächste **separat ausführbare** Research-/Evaluation-Scope ist nur zulässig, wenn pro Fleet-Kandidat dauerhaft und versioniert folgende Bindings ratifiziert sind:

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

### Fleet-Kandidaten

| Kandidat | Fleet-Mitglied |
|---|---|
| `trend_following` | `true` |
| `bollinger_bands` | `true` |
| `momentum_1h` | `true` |

### Fleet-weite Paritätsregeln

Für alle drei Fleet-Kandidaten (`trend_following`, `bollinger_bands`, `momentum_1h`) gelten **identische** Economic Policies und **vergleichbare** Kosten-, Execution-, Dataset- und Periodenbindungen. Folgende Aktionen sind **verboten**:

- Kandidatenspezifische Policy-Absenkung
- Threshold-Rettung
- Nachträgliche Ergebnisrettung
- Unveränderte Re-Execution gescheiterter Bindings (`UNMODIFIED_RE_EXECUTION_ADMISSIBLE=false`)
- Retry unveränderter Bindings (`FAILED_BINDINGS_MAY_NOT_BE_RETRIED_UNCHANGED=true`)

Historische negative Evidence (terminal FAIL 0/3 der Final Research Fleet) bleibt kanonisch und wird durch diese Scope-Definition **nicht** mutiert (`POLICY_CHANGE_DOES_NOT_CHANGE_HISTORICAL_EVIDENCE=true`).

## C. Explizit Ausgeschlossen (Dieser Scope)

```text
NO_CORE_SYSTEM_CHANGE
NO_CANONICAL_TRADING_LOGIC_CHANGE
NO_MASTER_V2_CHANGE
NO_DOUBLE_PLAY_CHANGE
NO_RISK_SIZING_CHANGE
NO_SAFETY_RUNTIME_CHANGE
NO_RUNTIME_REWIRE
NO_SHADOW
NO_PAPER
NO_TESTNET
NO_SCHEDULER
NO_ADAPTER_SUBMISSION
NO_ORDERS
NO_CREDENTIALS
NO_ARMING
NO_CANARY
NO_LIVE
NO_OFFLINE_EVALUATION_EXECUTION_THIS_SCOPE
NO_BACKTEST_EXECUTION_THIS_SCOPE
NO_WALK_FORWARD_EXECUTION_THIS_SCOPE
NO_MONTE_CARLO_EXECUTION_THIS_SCOPE
NO_STRESS_EXECUTION_THIS_SCOPE
NO_PARAMETER_SENSITIVITY_EXECUTION_THIS_SCOPE
```

| Ausführungsklasse | Autorisiert in diesem Scope |
|---|---|
| Offline Evaluation Execution | `false` |
| Backtest Execution | `false` |
| Walk-Forward Execution | `false` |
| Monte-Carlo Execution | `false` |
| Stress Execution | `false` |
| Parameter Sensitivity Execution | `false` |
| Runtime / Shadow / Paper / Testnet / Live | `false` |

## D. Safe Next Action

```text
SAFE_NEXT_ACTION=REQUEST_OPERATOR_GO_FOR_VERSIONED_FINAL_FLEET_BINDINGS_AND_BOUNDED_OFFLINE_ECONOMIC_EVALUATION_V0
```

- **Nicht** automatische Binding-Ratifikation oder Evaluation — erfordert separaten Operator-GO.
- **Nicht** unveränderte Final-Fleet-Re-Execution — governance-widersprüchlich zu terminal FAIL und Retry-Verbot.
- **Kein** Runtime-, Promotion- oder Rewire-Pfad aus dieser Scope-Definition allein.

**Minimaler admissibler Folgepfad (nur nach Operator-GO):**

1. Operator erteilt `GO_VERSIONED_FINAL_FLEET_BINDINGS_AND_BOUNDED_OFFLINE_ECONOMIC_EVALUATION_V0`.
2. Separater bounded PR: versionierte Final-Fleet-Binding-Ratifikation pro Kandidat (alle Pflicht-Bindings oben).
3. Operator bestätigt Fleet-weite Paritätsregeln und `CONFIRM_NO_RETRY_OF_FAILED_BINDINGS`.
4. Separates `OPERATOR_GO_OFFLINE_ECONOMIC_EVALUATION_EXECUTION` nur nach vollständiger Binding-Ratifikation.
