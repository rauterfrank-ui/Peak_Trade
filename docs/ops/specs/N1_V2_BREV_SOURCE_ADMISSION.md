---
docs_token: DOCS_TOKEN_N1_V2_BREV_SOURCE_ADMISSION
status: proposed
runtime_authorization_effect: NONE
---

# Quellprüfung für N1 V2 mit BREV auf LANE_1

Der Check `n1-v2-brev-admission` bindet die drei geprüften V2-Dateien an den
Offline-Wiederanlauf von `BREV-USDT-SWAP` auf `LANE_1`. Der Nachweis umfasst
zwei erfolgreiche Übernahmen mit derselben Store-Datei, derselben Reservierung
und demselben Cursor sowie acht vor den Kontoschnittstellen gesperrte Gegenproben.
Der portable Nachweis trägt den Hash des lokalen Originalreports und die Hashes
der geprüften Quellen. Die Abnahme war offline. Die Startfreigabe bleibt offen.
[Quellbindung](./N1_V2_BREV_SOURCE_ADMISSION.json), [Prüfnachweis](../evidence/N1_V2_BREV_OFFLINE_RECOVERY.json)

## Reihenfolge der Übernahme

1. Der Governance-PR führt Workflow, Checker, Quellbindung und Prüfbeleg ein.
   Der Bootstrap verlangt den geprüften Zielstand und einen Governance-Diff ohne
   V2-Laufzeitdateien. Beide V1-Siegelprüfungen bleiben bestehen.
2. Auf `main` registriert Ruleset 27494723 den Pflichtstatus aus GitHub Actions.
   PR #7315 hat das versionierte Inventar und den Ruleset-Nachweis nachgeführt.
   Im Workflow stammen Checker und Sollwerte für einen Implementierungskandidaten
   aus dem Ziel-Commit. Eine serverseitige Bindung an einen bestimmten Workflow
   geht über die Registrierung des Pflichtstatus hinaus.
3. Erst für den anschließenden Implementierungs-PR lädt der Check die Prüflogik
   und Sollwerte aus dem bereits übernommenen Ziel-Commit. Er akzeptiert genau
   die drei inhaltlich gebundenen V2-Dateien und die daraus folgenden Ergänzungen
   in Atlas und Law-Impact-Adjudikation. Sobald V2 im Zielbranch liegt, werden
   die gebundenen Dateiinhalte und die Prüfgrundlage weiter geprüft.

## Prüfgrundlage für `c358cd3c3`

Der Nachweis dieses Stands bindet die unveränderten V2-Quellbytes an
`c358cd3c3`. Der Test rekonstruiert die belegte Offline-Episode aus ihren
ursprünglichen Eingaben. Cap24 und der simulierte Laufzeitrequest verwenden
weiter die historische Revision `8557138f1`. Ein auf `c358cd3c3` gesetzter
Laufzeitrequest mit dem historischen Cap24-Beleg wurde wegen
`REPOSITORY_SHA_MISMATCH` abgewiesen. Der Nachweis gilt für den Prozesswiederanlauf
mit der ursprünglichen Bindung der Episode.

Das aktive Gate weist auf `c358cd3c3` einen direkten Implementierungs-PR mit
`REVIEWED_BASE_CHANGED` ab. Es weist auch Änderungen an seiner eigenen
Prüfgrundlage mit `TRUSTED_GOVERNANCE_FILES_CHANGED` ab. Die aktualisierte
Prüfgrundlage bildet deshalb einen eigenen Governance-Commit mit Prüfnachweis
und Sollwerten. Der Implementierungs-Commit kann geprüft werden, sobald die
aktualisierte Prüfgrundlage als eigenständig freigegebener Zielstand vorliegt.

Prüfgrundlage, Nachweis, Dateimodus, Paketinhalt und Quellbasis werden aus
Git-Objekten geprüft. Quelländerungen außerhalb der vorgesehenen Ergänzung
erfordern einen neu gebundenen Offline-Nachweis. Ein späterer Mac-Start hat
eine eigene Freigabe. [Workflow](../../../.github/workflows/n1-v2-brev-admission.yml), [Checker](../../../scripts/ci/check_n1_v2_brev_admission.py), [V1-Siegel](./N1_DOUBLE_PLAY_RUNTIME_SEAL_V1.md), [Ruleset-Vertrag](./BRANCH_RULESET_ENFORCEMENT_GOVERNANCE_V1.md)

## Lokale Prüfung der Git-Commits

```sh
./scripts/pt scripts/ci/check_n1_v2_brev_admission.py --bootstrap --base origin/main --candidate HEAD
```

Für einen lokalen Implementierungskandidaten zeigt `--base` auf den geprüften
Governance-Commit, `--candidate` auf den Implementierungs-Commit. Die Prüflogik
für diese Prüfung stammt aus dem Governance-Commit.
