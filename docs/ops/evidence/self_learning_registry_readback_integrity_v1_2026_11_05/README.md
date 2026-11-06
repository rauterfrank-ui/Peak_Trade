---
docs_token: DOCS_TOKEN_SELF_LEARNING_REGISTRY_READBACK_INTEGRITY_V1
status: executed_offline_consumer_contract
runtime_authorization_effect: NONE
---

# GVEF-Registry: Register-Snapshot, Lesepfad und Handoff-Prüfung

Quellstand `732601aeacca7b87ff3df2e0373f180f8de50081`, Ausführungs-HEAD
`14a9620b731799148532a0c77d5d26b73273d4ad`. Drei neue gezielte Offline-Probes prüfen den
tatsächlichen kanonischen Registry-API, ergänzend zu den
[bereits ausgeführten Integritätsprobes](../self_learning_retained_result_integrity_probe_v1_2026_11_05/README.md).
Implementierung und Konfiguration bleiben eingefroren.
Das [Master-Runbook](../../../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) bleibt maßgeblich.

## Beobachtete Grenzen

- Register-Snapshot funktioniert: Eine nachträgliche Änderung des ursprünglichen Inputs
  verändert den gespeicherten Eintrag nicht. Sein Digest bleibt gültig und der konkrete
  Handoff-Adapter kann ein Evidence-Envelope erzeugen.
- Lesepfad gibt die interne Instanz zurück: Eine Änderung der verschachtelten Seed-Liste
  des aus `get()` erhaltenen Modells verändert den gespeicherten Registry-Inhalt.
  Ein erneutes Lesen liefert den veränderten Payload mit altem, dann ungültigem Digest.
  Das Mitgliedschaftsmanifest bleibt dabei unverändert.
- Der konkrete Handoff-Adapter schützt seine Grenze: Er berechnet den Digest erneut
  und weist den veränderten Readback ab. Es entsteht in diesem Probe-Fall kein Envelope.

Alle drei Probes bestanden als Prüfung dieser Beobachtungen; eine davon reproduziert eine
noch bestehende Lesepfad-Integritätslücke. Es wurden keine produktiv beschädigten Daten
beobachtet. Ein Manifest mit `append_only=true` belegt hier Mitgliedschaft und Reihenfolge,
nicht automatisch die Unveränderlichkeit aller ausgegebenen Inhalte.

## Bezug zum selbstlernenden Pfad

Corpus-Registry, Evidence-Registry und numerisches Forschungsarchiv haben unterschiedliche
Verträge. Der vorhandene Messreferenz-Test verwendet beim Evidence-Register eine andere
In-memory-Fixture. Dieser Befund wird deshalb nicht als beschädigter numerischer Meta-Rückweg
oder als Nachweis eines aktuellen produktiven Registry-Consumers ausgegeben.

## Konkreter Ergänzungskandidat

Wenn der Lesepfad unveränderte Evidence liefern soll, sind eine Integritätsprüfung vor dem
Return und eine unabhängige Modellkopie konkrete Ergänzungskandidaten. Der bereits vorhandene
Register-Snapshot und die Handoff-Rehashprüfung bleiben erhalten. Der API-Vertrag braucht
dafür keine neue Produktiv- oder Persistenzautorität. Es wurde kein Patch angewendet.

[Beobachtungen, exakte Quellenbindungen und Kriterien](results.json),
[inertes Prüfskript](probe_runner.py.txt), [Manifest](manifest.json).
Keine Netzwerk-, Live-/Testnet-, Order-, Credential- oder Kapitalaktion wurde ausgeführt.
