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
2. Nach der Governance-Übernahme wird der Check serverseitig als Pflichtprüfung
   für `main` registriert. Die Durchsetzung muss die Workflow-Quelle aus einer
   vertrauenswürdigen Revision binden. Ein gleicher Jobname aus einem vom
   Kandidaten kontrollierten Workflow genügt dafür nicht. Danach werden der
   Required-Checks-Inventarstand und der verifizierte Ruleset-Nachweis zusammen
   nachgeführt. Die Registrierung und ein echter Ruleset-Nachweis stehen aus.
3. Erst für den anschließenden Implementierungs-PR lädt der Check die Prüflogik
   und Sollwerte aus dem bereits übernommenen Ziel-Commit. Er akzeptiert genau
   die drei inhaltlich gebundenen V2-Dateien und die daraus folgenden Ergänzungen
   in Atlas und Law-Impact-Adjudikation. Sobald V2 im Zielbranch liegt, werden
   die gebundenen Dateiinhalte und die Prüfgrundlage weiter geprüft.

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
