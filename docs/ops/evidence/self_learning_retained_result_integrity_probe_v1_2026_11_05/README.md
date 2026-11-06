---
docs_token: DOCS_TOKEN_SELF_LEARNING_RETAINED_RESULT_INTEGRITY_PROBE_V1
status: executed_offline_counterexamples
runtime_authorization_effect: NONE
---

# GVEF: Integrität bereits gespeicherter Ergebnisse nach Wiederholung

Drei gezielte Folgetests ergänzen die [29 ausgeführten Funktionskriterien](../self_learning_offline_functional_execution_v1_2026_11_05/README.md).
Sie prüfen eine offene Voraussetzung der [Ergänzungskandidaten](../self_learning_offline_remediation_candidates_v1_2026_11_05/README.md):
Genügt es, lediglich den zweiten Candidate-Rückgabewert zu vergleichen?
Quellstand `732601aeacca7b87ff3df2e0373f180f8de50081`; Ausführungs-HEAD
`5ab28112440218fe0f6eb85aad299de38ae0da9d`. Implementierung und Konfiguration bleiben unverändert.
Das [Master-Runbook](../../../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) bleibt maßgeblich.

## Tatsächlich beobachtet

- Verändert der injizierte Evaluator beim ersten Candidate-Aufruf die gespeicherte Baseline,
  blockiert der vorhandene frühe Schutz mit INVARIANT_FAILURE.
- Verändert er erst beim zweiten Candidate-Aufruf die schon gespeicherte Baseline, bleibt
  der Run REGISTERED, obwohl ihr tatsächlicher Digest nicht mehr zum gespeicherten Snapshot passt.
- Verändert er beim zweiten Baseline-Aufruf den schon gespeicherten ersten Candidate, bleibt
  der Run ebenfalls REGISTERED, obwohl dieses Objekt nicht mehr seinem ursprünglichen Ergebnis entspricht.

In den beiden späten Fällen bleibt der geschützte Output-Digest identisch zum unveränderten
Kontrollfall. Der Evaluator verändert dafür verschachtelte Metriklisten; die äußerlich eingefrorene
Modellkonfiguration verhindert diese konkrete Listenoperation im ausgeführten Probe-Fall nicht.
Das ist ein kontrollierter Gegenfall an der injizierten Evaluator-Schnittstelle, kein Nachweis
von produktiv beschädigten Forschungsdaten und keine SHA256-Kollision.

## Konsequenz für die Ergänzung

Ein Vergleich des zweiten Rückgabewerts allein reicht nicht aus, wenn ein Evaluator gleichzeitig
bereits gespeicherte Objekte verändert. Baseline- und Candidate-Snapshots sind zusätzlich nach der
Wiederholung gegen die tatsächlich im Runrecord gehaltenen Ergebnisse zu prüfen, bevor Vergleich,
Post-Gate und Registrierung weiterlaufen. Frühere Schutzpfade müssen erhalten bleiben.
Dies präzisiert einen Vorschlag; es wurde kein Produktpatch angewendet oder als repariert getestet.

Alle drei Probes bestanden als Prüfung der genannten Beobachtungen. Zwei davon bestätigen gerade
noch bestehende Lücken. [Ergebnisse und exakte Quellenbindungen](results.json),
[inertes Prüfskript](probe_runner.py.txt), [Manifest](manifest.json).
