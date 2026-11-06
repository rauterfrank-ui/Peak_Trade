# Pilot Ready Snapshot

## Zweck
Dieses Runbook erzeugt ein reproduzierbares Snapshot-Evidence-Pack für Pilot-Readiness, Audit und Incident-Nachvollziehbarkeit.

## Outputs
Der Builder erstellt ein Verzeichnis unter:

```bash
out&#47;ops&#47;pilot_ready_snapshot_&lt;UTC_TS&gt;&#47;
```

### Generierte Dateien
- `manifest.json` — Auflistung aller Dateien und kopierter Inputs
- `SHA256SUMS.txt` — SHA256-Checksums zur Verifikation
- `snapshot_summary.json` — Maschinenlesbare Zusammenfassung
- `snapshot_summary.md` — Menschenlesbare Zusammenfassung
- `DONE_<UTC_TS>.txt` — Done-Token
- `DONE_<UTC_TS>.txt.sha256` — SHA256 des Done-Tokens
- `inputs&#47;` — Kopien der gefundenen Evidence-Inputs (prbi, prbg, prbe, prbj, live_pilot_caps)

## STRICT=0 vs STRICT=1
- **STRICT=0** (Default): Fehlende erwartete Inputs werden als `__MISSING__` im Summary vermerkt, der Build läuft weiter.
- **STRICT=1**: Fehlende erwartete Inputs führen zu Exit-Code 1 und Abbruch.

## Ausführung

```bash
STRICT=0 ./scripts/ops/build_pilot_ready_snapshot.sh
```

oder mit strenger Prüfung:

```bash
STRICT=1 ./scripts/ops/build_pilot_ready_snapshot.sh
```

## Verifikation

```bash
cd out&#47;ops&#47;pilot_ready_snapshot_&lt;UTC_TS&gt;
shasum -a 256 -c SHA256SUMS.txt
```

Alle geprüften Dateien sollten mit `OK` bestätigt werden.

## Pilot-Readiness / Incident-Audit
Das Snapshot-Pack dient als:
- Nachweis für Live-Pilot-Freigabe (Evidence-Trail)
- Anhang bei Incident-Postmortems
- Audit-Referenz für reproduzierbare Zustände

## Hinweis
Runtime-Evidence unter `out/ops/` wird nicht von Git getrackt. Snapshots sind lokale Artefakte und sollten bei Bedarf manuell archiviert oder exportiert werden.

## Truth-first reference
- Canonical AI layer truth: `docs&#47;governance&#47;ai&#47;AI_LAYER_CANONICAL_SPEC_V1.md`
- Latest truth model artifacts: `out&#47;ops&#47;peak_trade_truth_model_*`
- Latest AI layer matrix artifacts: `out&#47;ops&#47;ai_layer_model_matrix_v1_*`
