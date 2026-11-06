---
docs_token: DOCS_TOKEN_SELF_LEARNING_OFFLINE_FUNCTIONAL_EXECUTION_V1
status: executed_offline_evidence_with_open_criteria
runtime_authorization_effect: NONE
---

# Selbstlernendes Universum: ausgeführte Offline-Funktionsprüfung

Datum: 05.11.2026. Quellstand `732601aeacca7b87ff3df2e0373f180f8de50081`,
Ausführungs-HEAD `1660a02faabf5dc3e7eb24ee652c192f55313f72` mit ausschließlich ergänzender
Dokumentation gegenüber dem Freeze. Das [Master-Runbook](../../../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md)
bleibt maßgeblich. Der Owner hat die Offline-Ausführung ausdrücklich freigegeben;
die bestehende Implementierung und Konfiguration wurden nicht verändert.

## Ausgeführt

96 vorhandene Tests bestanden. Alle 29 ausgewählten Funktionskriterien wurden mit gezielten
Offline-Probes beziehungsweise exakt gebundenen bestandenen Tests geprüft.
Der erste Probe-Lauf enthielt drei Fehler im zusätzlichen Prüfskript: einen falschen bestehenden
Testnamen und zwei falsche API-Zugriffe im Prüfskript. Diese sind korrigiert; ausschließlich
die drei betroffenen Probes wurden wiederholt. Die 26 unveränderten Probe-Funktionen wurden
über unveränderte ASTs und denselben Produktquellstand wiederverwendet. Insgesamt gab es
128 pytest-Testfallausführungen, nicht 128 verschiedene erfolgreich erfüllte Funktionsanforderungen.

## Ergebnis der 29 Kriterien

- 12 Kriterien erfüllt;
- 5 fachliche Prüfgrenzen bestätigt;
- 4 konkrete Lücken reproduziert;
- 4 weitere Grenzen unter ausdrücklich genannten Bedingungen reproduziert;
- 1 Anforderung und 3 teilweise geprüfte Vertragsanforderungen weiterhin offen.

Die vier konkreten Gegenfälle: Ein zweiter Candidate-FAIL beziehungsweise geänderte zweite
Candidate-Ergebnisse bleiben im Runner unberücksichtigt; eine gleiche Experimentidentität
mit neuer Zeit kann erst nach erneuter Messung am Memory-Konflikt scheitern; die erwartete
Optimization-Schemaversion des föderierten M6-Requests erhält keinen Vergleich.

Die vier bedingten Grenzen betreffen unabhängige Replay-Reproduktion, Domain-/Corpus-Erhaltung
im Fixture-Bundle und die Candidate-Bindung im geschützten Output-Digest. Beim letzten Fall
ändern sich Candidate-Artefakt- und Trace-Digest, während der Output-Digest gleich bleibt.
Das ist eine Projektion unterschiedlicher Inhalte auf dieselben tatsächlich verwendeten
Digest-Eingaben, keine erzeugte SHA256-Kollision.

Die offenen Anforderungen betreffen vollständige Domain-Aggregation, verlangte Registry-
Dauerhaftigkeit, verpflichtenden externen Handoff und Behandlung unvollständig archivierter
Sessions. Vorhandene In-memory-, optionale Handoff- und Teilpersistenzverträge werden deshalb
nicht pauschal als Produktivfehler umgedeutet.

## Prüfgrenzen und Wiederholung

Eine bestandene Probe kann gerade die Reproduktion einer Lücke bestätigen. Sie besagt dann
nicht, dass die gewünschte Funktion erfüllt ist. Der bekannte synthetische Referenzpfad bleibt
synthetisch; spätere numerische Meta-Verarbeitung ist weder Forschungsqualitätsannahme noch
Produktivfreigabe. Der Gleichidentitäts-Gegenfall verwendet ausdrücklich temporär leere
Failure-/Gap-Kontexte bei vorhandenem temporärem Experiment-Memory; er beweist keinen
erfolgreichen ursprünglichen Forschungsversuch. Der injizierte Archivfehler verändert nur
temporäre Stores und erhält deren Originalrecords.

Die zusätzlichen Runner liegen inert als [korrigierte Fassung](probe_runner.py.txt) und
[erste Fassung](probe_runner_attempt1.py.txt) bei. Sie sind prüfbare Evidence, keine installierten
Tests oder Produktmodule. Für eine erneute Ausführung müssen Ausgabe und pytest-Temporärpfade
in einen eigenen externen Arbeitsordner zeigen; die bestehende kanonische Python-Umgebung
ist zu verwenden. Identische bereits gebundene Prüfungen werden nicht allein zum Versiegeln wiederholt.

[Alle Beobachtungen und Kriterien](results.json), [Testfallindex](test_execution_index.json),
[Prüfskriptkorrektur und Wiederverwendung](probe_harness_correction_and_reuse.json),
[Freeze-/Ledger-Verifikation](verification.json), [Manifest](manifest.json).
Keine Runtime-Services, Live-/Testnet-Orders, Zugangsdaten oder Kapitalbewegungen wurden verwendet.
Es gab keinen Push und keine Änderung der Scope-Berechnung.
