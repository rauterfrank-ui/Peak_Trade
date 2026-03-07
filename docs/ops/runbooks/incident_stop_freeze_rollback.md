# Incident Stop Freeze Rollback

## Ziel
Operatives Runbook für Incident-Reaktion mit sicherem Fokus auf STOP NOW, FREEZE, ROLLBACK und POSTMORTEM. Standard bleibt NO_TRADE.

## Typische Incidents
- Exchange API Outage oder degradierter API-Betrieb
- Unexpected Order Placement
- Balance Drift oder Reconciliation Failure
- Evidence Pipeline Failure
- Export Failure oder Permission Regression

## STOP NOW
Ziel: sofortige lokale Betriebsbremse ohne neue Order-Platzierung.

```bash
INCIDENT_SLUG=exchange_api_outage ./scripts&#47;ops&#47;incident_stop_now.sh
```

Output unter `out&#47;ops&#47;incident_stop_&lt;UTC_TS&gt;_&lt;slug&gt;&#47;`:
- `incident_stop_state.env` — Gate-Zustände (PT_ENABLED=0, PT_ARMED=0, PT_FORCE_NO_TRADE=1)
- `incident_stop_summary.md` — Operative Zusammenfassung

Keine Order-Platzierung, keine Exchange-Mutation.

## FREEZE
Ziel: System in bekanntem Zustand halten, keine weiteren Aktionen.

1. STOP NOW ausführen (siehe oben).
2. Keine weiteren Bot-Runs starten.
3. Keine manuellen Orders platzieren.
4. Evidence-Snapshot erstellen (siehe Evidence Capture).

## ROLLBACK
Ziel: Rückkehr auf einen bekannten, verifizierten Zustand.

1. STOP NOW und FREEZE sicherstellen.
2. Evidence-Snapshot vor Rollback erstellen.
3. Rollback nur via PR und Review — keine Hot-Edits in main.
4. Nach Rollback: Verifikation gemäß Pilot-Ready-Snapshot oder Incident-Snapshot.

## POSTMORTEM
Ziel: Nachvollziehbare Dokumentation und Lessons Learned.

1. Evidence-Pack anhängen (Incident-Snapshot, Stop-State, Logs).
2. Kurze Beschreibung: Was sollte passieren? Was ist passiert?
3. Root-Cause-Hypothesen (max. 3) mit stützender/falsifizierender Evidenz.
4. Outcome: resolved / mitigated / open.
5. Lessons Learned: 3 Bullets.

## Evidence Capture
Incident-Snapshot für Audit und Postmortem:

```bash
INCIDENT_SLUG=exchange_api_outage STRICT=0 ./scripts&#47;ops&#47;build_incident_snapshot.sh
```

Output unter `out&#47;ops&#47;incident_&lt;UTC_TS&gt;_&lt;slug&gt;&#47;`:
- `manifest.json` — Auflistung der Dateien
- `SHA256SUMS.txt` — Checksums zur Verifikation
- `incident_summary.json` — Maschinenlesbare Zusammenfassung
- `incident_summary.md` — Menschenlesbare Zusammenfassung
- `DONE_&lt;UTC_TS&gt;.txt` — Done-Token
- `inputs&#47;` — Kopien verfügbarer Evidence-Inputs (prbi, prbg, prbe, prbj, live_pilot_caps)

STRICT=0: Fehlende Inputs als `__MISSING__` vermerkt, Build läuft weiter.
STRICT=1: Fehlende Inputs führen zu Exit 1.

## Verifikation
SHA256-Checksums prüfen:

```bash
cd out&#47;ops&#47;incident_&lt;UTC_TS&gt;_&lt;slug&gt;
shasum -a 256 -c SHA256SUMS.txt
```

Alle geprüften Dateien sollten mit `OK` bestätigt werden.

## Hinweis
Runtime-Evidence unter `out&#47;ops&#47;` wird nicht von Git getrackt. Incident-Snapshots sind lokale Artefakte und sollten bei Bedarf manuell archiviert oder exportiert werden.

## Truth-first reference
- Canonical AI layer truth: `docs&#47;governance&#47;ai&#47;AI_LAYER_CANONICAL_SPEC_V1.md`
- Latest truth model artifacts: `out&#47;ops&#47;peak_trade_truth_model_*`
- Latest AI layer matrix artifacts: `out&#47;ops&#47;ai_layer_model_matrix_v1_*`
