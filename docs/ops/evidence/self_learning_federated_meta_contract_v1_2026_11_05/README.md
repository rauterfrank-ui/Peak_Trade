---
docs_token: DOCS_TOKEN_SELF_LEARNING_FEDERATED_META_CONTRACT_V1
status: supplemental_source_review
runtime_authorization_effect: NONE
---

# Selbstlernendes Universum: föderierter Meta-Rückweg und Versionsvertrag

Quellstand: `732601aeacca7b87ff3df2e0373f180f8de50081`.
Diese ergänzende Quellenanalyse ändert keine Implementierung oder Konfiguration.
Das [Master-Runbook](../../../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) bleibt maßgeblich.

## Eigene Variante des Rückwegs

Der bestehende [föderierte M5–M8-Vertrag](../../specs/M5_M8_BOUNDED_META_RETURN_AND_REPLAY_COMPLETION_NORMATIVE_V1.md)
beschreibt Evidence-Rückgabe und Offline-Replay. Der konkrete Zyklus erzeugt selbst den Join,
projiziert M6-Meta-Evidence und validiert M7-Feedback. Die Auswahl einer Searchmethode muss
ausdrücklich fail-closed bleiben. Der Multi-Cycle-Runner übernimmt vorgegebene M5-Evidence
pro Zyklus und trägt voriges Feedback in die nächste Evidence-Ausgabe weiter.

Das ist ein anderer Consumerpfad als native numerische Forschung mit tatsächlichem
Phase11-Analyzer und anschließender Search. M6-Muster-/Digestprojektion und weitergetragenes
Feedback beweisen hier keine neue Kandidatenmessung. Surface-, Plane- und Experimentidentität
sind getrennt; aus dieser Föderation entsteht keine Gleichsetzung mit N5-Slots.
Andere Governed-Continuations werden durch diese Aussage nicht pauschal klassifiziert.

## Ergänzender Befund zum erwarteten Schema

Der föderierte M6-Request deklariert `expected_optimization_evidence_schema_version`.
Sein Ingest-Funktionskörper liest dieses Feld nicht. Erwartete Join- und Meta-Versionen
werden hingegen gelesen; der nichtföderierte Ingest prüft auch die erwartete Optimization-Version.
Die Nichtverwendung im föderierten Funktionskörper wurde zusätzlich statisch per AST geprüft.

Die tatsächliche Payload wird trotzdem durch den föderierten M5-Validator und dessen
Basisschemavalidierung geprüft. Es wird deshalb kein Durchlass beliebiger alter Payloads behauptet.
Der konkrete lokale M8-Caller verwendet Defaults und erstellt den Join unmittelbar vorher.
Ein abweichender vom Caller verlangter Vertrag erhält im föderierten M6-Ingest jedoch keinen
eigenen Versionsvergleich. Diese Requestsemantik ist für eine spätere Ergänzung aufzulösen.

## Prüfgrenze

Fünf konkrete Kriterien sind definiert, aber nicht ausgeführt. Es gab keinen neuen Zyklus-,
Analyzer- oder Negativtestlauf. Die bestehenden Autoritätsgrenzen bleiben erhalten.
[Befunde und exakte Quellenbindungen](findings.json), [Manifest](manifest.json).
