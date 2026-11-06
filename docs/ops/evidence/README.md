# Evidence Packs

## Purpose

Evidence Packs sind maschinen- und menschenlesbare Nachweise, die Doc-Claims absichern.

## Contract

- Schema: `EVIDENCE_SCHEMA_v1.json`
- Jeder Claim, der "wirksam" (`enforced`) behauptet, muss mindestens `E1` haben.
- Evidence Packs sind **append-only**: neue IDs statt Überschreiben.

## Structure

Empfohlen:

```
docs/ops/evidence/
  EVIDENCE_SCHEMA_v1.json
  README.md
  packs/
    PR-01/
      EV-2026-02-PR01-001.json
```

## Minimal Fields

Siehe `EVIDENCE_SCHEMA_v1.json` → `example`.

---

## Canary-Freigabe-Referenz (LB-APR-001)

Explizite **live-approved**-Freigabe für Canary-Live wird **primär außerhalb** des Repos geführt (Ticket, Formular, signiertes Dokument). Pflichtfelder und Abgrenzung (Merge/Repo ≠ Freigabe) stehen in [`CANARY_LIVE_ENTRY_CRITERIA.md`](../runbooks/CANARY_LIVE_ENTRY_CRITERIA.md#freigabe-artefakt-lb-apr-001).

Optional können unter diesem Verzeichnis **Kopien oder Links** als betriebliche Belege abgelegt werden — **Pointer-/Nachweischarakter** allein; **kein** Ersatz für das originale Freigabe-Artefakt und **kein** `live-approved` durch einen Docs-Merge.

## Obsidian und Repository: Wissensabgleich 06.11.2026

[Vollständige fachliche Dossiers, Werteursprünge, innere Ebenen und ursprüngliche Nachweise](obsidian_repo_alignment_2026_11_06/README.md). Gegenseitiger Abgleich der beiden aktiven Wissens-Vaults mit dem vollständigen Codecheckpoint und der anschließenden Consumerrekonstruktion; datierte Inhaltssicherung mit Einzeldateibindung, keine globale semantische Neuzertifizierung oder Betriebsfreigabe.

## Punkt 1: Eigenstaendige Marktbeobachtung und historischer Anschluss

[Ursprüngliche Git-/PR-Verträge, Messowner, optionale Forecastattribution und heutige Consumerproben](mi_independent_market_observation_history_2026_11_06/README.md). Historische Ursache der noch offenen unabhängigen Messkette; keine neue Produktimplementierung oder normative Ratifikation.

## Punkt 1: Implementierter unabhaengiger Offline-Marktpfad

[Marktidentität, Forecastfreeze, kanonische Messung und ursprünglicher Calibration-Readback](independent_market_observation_v1_2026_11_06/README.md). Funktionale Schließung des begrenzten entscheidungsfreien Returnpfads mit gemeinsamem Messowner und 787 gebundenen bestandenen Tests. Die historische Ursachenklärung darüber bleibt datiert; Modelllernen und Betriebsfreigaben bleiben getrennt.

## Obsidian: Cockpit, Systemkarten und 3D-Graph

[Aktualisierte Einstiegsansichten und aktivierte Galaxy View](obsidian_cockpit_graph_refresh_2026_11_06/README.md). Getrennte E6-/Market-only-Pfade, sichtbare Folgeconsumer-Lücken und echte Datei-Verbindungen im Dokumentgraph; Vorherbilder und begrenzte Ansichtsprüfung bleiben erhalten. Keine neue Produktimplementierung oder globale Neuzertifizierung.

## Punkt 2: Lernergebnis bis zum nächsten verwendeten Modell

[Historischer Label-Freeze, numerische Lernverfahren und tatsächliche Folgeconsumer](mi_next_model_causal_assessment_2026_11_06/README.md). Vier konkrete Anschlussverträge bis zum nächsten berechneten MI-Forecast, vollständiges Automatisierungsziel und bestätigte relative Instrumentwahl. Bestehende Tests ergeben 22 PASS, 3 umgebungsbedingte FAIL und 3 Archiv-SKIP; numerische Kontrollen und Originalstore-Readback sind getrennt dokumentiert. Keine Produktimplementierung oder Schließung von Punkt 2.

## Punkt 2: Numerischer Offline-Modellanschluss umgesetzt

[Originalmessungen, versionierter OLS-Modellkörper und tatsächlich berechneter Folgeforecast](independent_market_ols_next_forecast_v1_2026_11_06/README.md). 798 unterschiedliche verbundene Tests PASS, darunter elf neue Fälle; die 11.360 gebundenen Source-/Test-/Configdateien bleiben während des finalen Laufs unverändert. Die darüber erhaltene Ursachenanalyse ist der frühere Stand. Natural Enter mit fortgesetztem Double Play, fünf freigeschaltete Futures-Slots, Kandidatenrotation und natürliche Qualität bleiben Teil der späteren Gesamtsystemprüfung.
