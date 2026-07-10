# Peak Trade — Implementierungsvertrag für Cursor

**Rolle:** Kurze repo-seitige Navigations- und Ausführungsanweisung.  
**Authority:** Keine zweite Trading-, Safety-, Risk-, Sizing-, Economic- oder Runtime-SSOT.

```text
CANONICAL_RUNBOOK_PATH=docs/governance/Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.10_IMPLEMENTATION_CONTRACT.md
THIS_DOCUMENT_IS_NOT_A_SECOND_SSOT=true
THIS_DOCUMENT_MAY_NOT_OVERRIDE_CANONICAL_RUNBOOK=true
CURSOR_MUST_READ_CANONICAL_RUNBOOK_FIRST=true
```

**Kanonischer Parent:** [`Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.10_IMPLEMENTATION_CONTRACT.md`](Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.10_IMPLEMENTATION_CONTRACT.md)

## 1. Unveränderliche Grenzen

```text
FUTURES_ONLY=true
BITCOIN_DIRECTION_ALLOWED=false
SPOT_ALLOWED=false
SYNTHETIC_SPOT_ALLOWED=false
LIVE_AUTHORIZED=false
ORDERS_ALLOWED=false
SCHEDULER_RUNTIME_ALLOWED=false
NO_CORE_TRADING_LOGIC_CHANGE_WITHOUT_EXPLICIT_SCOPE=true
NO_MASTER_V2_CHANGE_WITHOUT_EXPLICIT_SCOPE=true
NO_DOUBLE_PLAY_CHANGE_WITHOUT_EXPLICIT_SCOPE=true
NO_RISK_SIZING_SEMANTIC_CHANGE_WITHOUT_EXPLICIT_SCOPE=true
NO_SAFETY_KILLSWITCH_RECONCILIATION_CHANGE_WITHOUT_EXPLICIT_SCOPE=true
NO_POLICY_RESCUE=true
```

## 2. Keine Vermutungen

```text
NO_GUESSING_ABOUT_REPO_OWNERS=true
NO_GUESSING_ABOUT_DIGEST_PAYLOADS=true
NO_GUESSING_ABOUT_BINDING_IDENTITY=true
NO_GUESSING_ABOUT_RUNNER_REQUIREMENT=true
NO_GUESSING_ABOUT_SUPERSESSION=true
```

Unklarheit bedeutet:

```text
READ_ONLY_DISCOVERY
→ KNOWN / UNKNOWN / BLOCKER report
→ NO MUTATION until resolved
```

## 3. Pflichtreihenfolge vor Implementierung

```text
1. current state und origin/main abgleichen
2. Source-MANIFESTE mit RC=0 verifizieren
3. kanonische Owner inventarisieren
4. authored / observed / derived Felder klassifizieren
5. Digest-Inputs, Excludes, Serialisierung und Hash-Owner belegen
6. transitive Digest-Abhängigkeiten darstellen
7. semantische und kryptografische Binding-Identität getrennt bestimmen
8. Supersession-/Repair-Modus belegen
9. kanonischen Runner oder Entry Point bestimmen
10. kleinsten zulässigen Slice implementieren
11. fokussierte Proof-Matrix ausführen
12. Durable Evidence + MANIFEST.sha256 RC=0
13. genau einen PR öffnen
```

## 4. Reuse-First

```text
REUSE_AS_IS
→ REUSE_WITH_NARROW_ADAPTER
→ REWIRE_EXISTING_COMPONENT
→ CONSOLIDATE_TO_EXISTING_OWNER
→ NEW_IMPLEMENTATION_JUSTIFIED
```

Kein paralleler Digest-, Binder-, Materializer-, Runner-, Registry- oder Evidence-Owner ohne belegte Notwendigkeit.

## 5. Digest- und Binding-Regeln

Für jeden Digest dokumentieren:

```text
canonical_owner
canonical_input_payload
included_fields
excluded_fields
serialization
normalization
hash_algorithm
transitive_dependencies
consumers
```

```text
DERIVED_DIGESTS_MUST_USE_CANONICAL_OWNER=true
SELF_REFERENCE_ALLOWED=false
MANUAL_HASH_REIMPLEMENTATION_ALLOWED=false
REPEATED_COMPUTATION_IDENTICAL=true
TRANSITIVE_DIGEST_UPDATE_COMPLETE=true
UNEXPLAINED_DIGEST_CHANGE_ALLOWED=false
```

Binding immer zweistufig berichten:

```text
SEMANTIC_BINDING_IDENTITY
CRYPTOGRAPHIC_BINDING_IDENTITY
```

```text
old_binding_digest != new_binding_digest
→ CRYPTOGRAPHIC_BINDING_IDENTITY_CHANGED=true
```

Der Begriff `same binding` ist nur ohne Zusatz zulässig, wenn semantische und kryptografische Identität unverändert sind.

## 6. Materializer-/Binder-Vertrag

```text
canonical source
→ materializer
→ materialized artifact
→ real binder/validator
→ PASS
```

Pflicht:

```text
MATERIALIZER_USES_CANONICAL_DIGEST_OWNERS=true
ROUNDTRIP_MATERIALIZER_TO_BINDER_PASS=true
DETERMINISTIC_MATERIALIZATION=true
SECOND_MATERIALIZATION_DIFF_EMPTY=true
```

Nur statische JSON-Gleichheitsprüfungen reichen nicht aus.

## 7. Repair und Reevaluation trennen

```text
failed evaluation
→ read-only defect classification
→ separate repair PR
→ repair merge-closeout
→ new explicit operator GO
→ separate reevaluation
```

```text
REPAIR_GO_DOES_NOT_AUTHORIZE_REEVALUATION=true
NO_ECONOMIC_EVALUATION_IN_REPAIR_PR_BY_DEFAULT=true
RUNTIME_EFFECT=NONE
AUTHORITY_EFFECT=NONE
```

Ein Repair muss den kanonischen Owner beheben; nicht nur das erzeugte Config-Artefakt, wenn der Generator fehlerhaft ist.

## 8. Runner-/Entry-Point-Regel

Vor Evaluation genau eine belegte Entscheidung:

```text
REUSE_EXISTING_GENERIC_RUNNER
REUSE_EXISTING_DIRECT_INVOCATION
REUSE_EXISTING_STRATEGY_SPECIFIC_RUNNER
ADD_THIN_CANONICAL_ADAPTER
RUNNER_NOT_REQUIRED_BY_REPO_CONTRACT
UNKNOWN_RUNNER_CONTRACT
```

`RUNNER_REQUIRED=false` ist nur zulässig, wenn ein konkreter alternativer Entry Point benannt oder repo-seitig belegt ist, dass kein Runner erforderlich ist.

Ein dünner Adapter darf nur Config referenzieren, Gates durchreichen und den bestehenden Owner aufrufen. Keine Strategy-, Sizing-, Cost-, Digest-, Dataset- oder Universe-Logik duplizieren.

## 9. Pflicht-Testmatrix

```text
wrong_or_stale_digest_rejected
correct_digest_accepted_by_real_binder
canonical_digest_owner_used
materializer_to_binder_roundtrip_pass
repeated_materialization_deterministic
semantic_payload_unchanged_when_claimed
dataset_and_universe_unchanged_when_claimed
strategy_parameters_unchanged_when_claimed
transitive_digest_chain_complete
old_evidence_preserved
no_runtime_effect
no_authority_effect
```

Jede Aussage markieren:

```text
DIRECTLY_PROVEN
INDIRECTLY_PROVEN
NOT_PROVEN
NOT_APPLICABLE_WITH_REASON
```

Materielle Merge-Aussagen müssen direkt bewiesen sein.

## 10. Final-Report-Wahrheit

Pflichtfelder:

```text
ROOT_CAUSE_CONFIRMED
CANONICAL_OWNER
OLD_AND_NEW_COMPONENT_DIGESTS
OLD_AND_NEW_BINDING_DIGEST
SEMANTIC_BINDING_FIELDS_CHANGED
CRYPTOGRAPHIC_BINDING_IDENTITY_CHANGED
BINDING_CLASSIFICATION
SUPERSESSION_MODE
ROUNDTRIP_PASS
DETERMINISTIC_MATERIALIZATION
RUNNER_REQUIRED
RUNNER_ACTION
CANONICAL_ENTRY_POINT
ECONOMIC_EVALUATION_EXECUTED
RUNTIME_EFFECT
AUTHORITY_EFFECT
UNRESOLVED_UNKNOWNS
```

Widerspruch im Report blockiert den Merge.

## 11. Evidence

Mindestens:

```text
owner_inventory.json
reuse_decision.json
field_classification.json
digest_contracts.json
digest_dependency_graph.json
before_after_field_diff.json
semantic_identity_comparison.json
cryptographic_identity_comparison.json
materializer_roundtrip.txt
deterministic_materialization.txt
runner_decision.json
test_assertion_matrix.json
final_report.txt
MANIFEST.sha256
```

## 12. Repo-Integration

Vor Ablage dieser Datei prüfen, ob bereits ein näherer kanonischer Governance-/Implementation-Contract-Owner existiert. Dann diesen erweitern, statt eine Parallel-SSOT anzulegen.

Diese Kurzdatei navigiert. Das vollständige Runbook entscheidet.
