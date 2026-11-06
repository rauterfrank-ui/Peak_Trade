---
docs_token: DOCS_TOKEN_SELF_LEARNING_OFFLINE_REMEDIATION_CANDIDATES_V1
status: proposed_additions_from_executed_counterexamples
runtime_authorization_effect: NONE
---

# Konkrete Ergänzungskandidaten aus ausgeführten Gegenfällen

Grundlage sind die [ausgeführten Offline-Prüfungen](../self_learning_offline_functional_execution_v1_2026_11_05/README.md)
am eingefrorenen Quellstand `732601aeacca7b87ff3df2e0373f180f8de50081`.
Das [Master-Runbook](../../../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) bleibt maßgeblich.
Dies sind quellengebundene Ergänzungsvorschläge, keine neue Policy, Implementierung oder Aktivierung.

## Drei konkrete Ursachen und eine bedingte Erweiterung

1. Die beiden Candidate-Wiederholungsgegenfälle haben dieselbe Ursache: Das zweite Ergebnis
   wird verworfen. Ein stabiler Digest des ersten Candidate-Ergebnisses kann den zweiten
   Verdict und die vereinbarten Ergebnisfelder vor der Registrierung binden. Der bestehende
   Non-Determinism-Fehlerpfad ist wiederverwendbar; unveränderte Baseline-/Manifestprüfungen
   und vorhandene Corpus-/Meta-Bindungen sind zu erhalten.
2. Die föderierte erwartete Optimization-Schemaversion kann am Ingress entsprechend dem
   vorhandenen nichtföderierten Vertrag geprüft werden. Die tatsächliche Payload-Prüfung
   bleibt davon unabhängig und darf nicht entfallen.
3. Die native Session kennt die vorgeschlagene Experiment-ID vor der Messung. Dort gehört
   die Unterscheidung zwischen explizitem Archiv-Replay, neuer Identität und bereits belegter
   ID hin. Ein alter Archivdatensatz darf nicht als neue, zur aktuellen Search gehörende
   Ausführung ausgegeben werden. Ein Retest-Grund überschreibt weder die Identität noch
   unveränderlichen Memory-Inhalt. Der genaue nicht-ausführende Ergebnisvertrag ist vor einer
   Umsetzung festzulegen; eine willkürliche Seed-Änderung wäre keine Lösung.
4. Vollständige Domain-/Corpus-/Candidate-Erhaltung ist eine bedingte zusätzliche Anforderung.
   Wenn ein tatsächlicher Consumer sie benötigt, ist eine separat versionierte Ergebnisbindung
   ein konkreter Kandidat. Historische geschützte Digestdomänen werden dafür nicht still umdefiniert.
   Der aktuelle Fixture-Builder wird nicht pauschal zum Produktivdefekt erklärt.

## Vier verbleibende Vertragsgrenzen

Der Whole-System-Wrapper verwendet einen einzelnen injizierten Evaluator; ein erforderlicher
Verbundnachweis braucht einen eigenen tatsächlichen Consumer. Die kanonische GVEF-Registry
ist ausdrücklich in-memory; der numerische Archiv-Wiederanlauf ist ein anderer vorhandener
Owner und wurde erfolgreich geprüft. Der Default-Handoff ist absichtlich optional;
Envelope-Erzeugung ist keine externe Annahme oder Produktivfreigabe.

Eine späte Archivstörung lässt bestehende Phase2/3/7-Records erhalten. Die vorhandene
Teilpersistenzgrenze ist dokumentiert und wurde im temporären Offline-Fall reproduziert.
Vollständige spätere Recovery dürfte nur auf original gebundener Execution, Messreceipt
und unveränderlichen Ownerrecords aufbauen. Fehlende Loop-/Messwerte dürfen dafür nicht
neu erfunden oder ursprüngliche Records als Rollback gelöscht werden.

[Ergänzungsgruppen mit Quellen, Consumers und Abnahmekriterien](remediation_candidates.json).
[Manifest](manifest.json). Kein Vorschlag wurde angewendet oder als reparierter Stand getestet.
Die Freigabe zur Offline-Ausführung ändert den Implementierungs-Freeze nicht.
