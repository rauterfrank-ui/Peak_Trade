# Retention Strategy

## Ziel
Long-Run-Hygiene für Artefakte, Evidence-Packs und Export-Verifikation. Fokus: nachvollziehbare Retention, Integrität und reproduzierbare Verifikation bei langen Laufzeiten.

## Artefakt-Klassen

### Kurzlebige CI-Artefakte
Beispiele:
- Test-Logs
- temporäre Build-Artefakte
- PR-bezogene Download-Packs

Empfehlung:
- primär in GitHub Artifacts halten
- kurze Retention verwenden
- bei Bedarf gezielt rerunnen statt dauerhaft aufbewahren

### Operative Evidence-Artefakte
Beispiele:
- Snapshot-Ausgaben unter `out&#47;ops&#47;`
- Incident-Snapshots
- Pilot-Ready Snapshots
- Export-Verifikations-Ergebnisse

Empfehlung:
- lokal oder in Langzeit-Storage ablegen
- Integrität per SHA256 dokumentieren
- nur referenzierte, relevante Evidence langfristig behalten

### Langfristige Audit-Artefakte
Beispiele:
- freigaberelevante Evidence-Packs
- Incident-Postmortem-Bundles
- signifikante Governance-/Audit-Nachweise

Empfehlung:
- in langfristigem Storage halten, z. B. S3-kompatibler Bucket
- unveränderliche oder append-only Ablage bevorzugen
- Hashes und Manifest gemeinsam speichern

## Retention-Fenster (Retention Windows)

### GitHub Artifacts
Empfohlene Fenster:
- Routine-PR-Artefakte: 7 bis 14 Tage
- wichtige Release-/Pilot-Artefakte: 14 bis 30 Tage
- nicht als alleinige Langzeit-Ablage verwenden

### Lokale Runtime-Evidence
Empfohlene Fenster:
- operative Kurzfrist-Prüfung: 7 bis 30 Tage lokal
- danach gezielte Verschiebung oder Löschung nach Verifikation

### Long-Term Storage
Empfohlene Fenster:
- Pilot-/Incident-/Audit-relevante Artefakte: 90 Tage bis 1 Jahr oder nach Governance-Vorgabe
- kritische Freigabe-/Postmortem-Pakete: länger nach Audit-/Compliance-Bedarf

## GitHub Artifacts vs. Long-Term Storage

### GitHub Artifacts
Geeignet für:
- PR-nahe Prüfung
- schnelle Downloads
- kurzfristige CI-Verifikation

Nicht ausreichend für:
- alleinige Langzeitarchivierung
- Audit-relevante dauerhafte Ablage

### Long-Term Storage
Geeignet für:
- signifikante Evidence-Packs
- freigaberelevante Snapshots
- Incident-Bundles
- Export-Pakete mit Langzeitwert

Bevorzugte Eigenschaften:
- versioniert
- unveränderlich oder append-only
- objektbasierte Ablage
- Lifecycle-Rules
- getrennte Zugriffsrollen

## Integritäts-Erwartungen
Für langfristig relevante Pakete:
- Manifest-Datei beilegen
- SHA256SUMS beilegen
- Verifikation vor Upload und nach Download durchführen
- Hashes nicht getrennt vom Paket aufbewahren

Beispiel-Verifikation:

```bash
cd out&#47;ops&#47;&lt;artifact_dir&gt;
shasum -a 256 -c SHA256SUMS.txt
```

Alle geprüften Dateien sollten mit `OK` bestätigt werden.

## Rerun/Verify-Policy
- **Rerun:** Bei transienten CI-Fehlern (z. B. Concurrency-Cancel) gezielt den betroffenen Workflow rerunnen.
- **Verify:** Nach Download oder Restore stets `shasum -a 256 -c SHA256SUMS.txt` ausführen.
- **export-pack-verify:** Der Workflow `CI &#47; Export Pack Download + Verify` prüft Export-Pakete; bei Concurrency-Konflikten Rerun nutzen.
- **Reproduzierbarkeit:** Snapshot-Builder (Pilot-Ready, Incident) erzeugen deterministische Strukturen; bei Bedarf mit gleichen Inputs neu bauen.

## Operator-Hygiene für Long-Running Evidence
- Regelmäßig prüfen, ob lokale `out&#47;ops&#47;`-Artefakte noch benötigt werden.
- Vor Löschung: Verifikation durchführen und bei Relevanz in Long-Term Storage verschieben.
- Keine Secrets in Artefakten ablegen.
- Lifecycle-Rules für S3/Bucket definieren und dokumentieren.

## Minimaler Operativer Checklist
- [ ] Retention-Fenster für Artefakt-Klassen bekannt
- [ ] Integritäts-Verifikation vor Langzeit-Ablage durchgeführt
- [ ] GitHub Artifacts nicht als alleinige Langzeit-Ablage genutzt
- [ ] Bei export-pack-verify-Fehlern: Rerun prüfen
- [ ] Lokale Evidence nach Verifikation gezielt aufräumen oder archivieren
