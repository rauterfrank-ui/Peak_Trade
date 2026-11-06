# Sample-Size Ramp (Testnet Execution Evidence) — Runbook

Ziel
- PRBI (Live Pilot Scorecard) soll nicht mehr an `INSUFFICIENT_SAMPLE_SIZE` scheitern.
- Wir erhöhen die Execution Evidence Sample Size deterministisch über Testnet-Exec-Events.

Grundlagen
- PRBI liest Execution Evidence (PRBG) + Shadow/Testnet Scorecard (PRBE) + weitere Gates.
- Aktueller Blocker: `INSUFFICIENT_SAMPLE_SIZE` (Sample Size zu klein).
- PRBI Defaults (Stand Repo): `min_sample_size=100` (siehe `scripts/ci/live_pilot_scorecard.py`).

Konzept
- Wir erzeugen echte Testnet-Events (Orders/Fills/Rejects/RateLimit/Reconnect) via PR-BJ.
- PR-BG soll bevorzugt das PR-BJ Artifact konsumieren (Exec Events JSONL), nicht Repo-Samples.
- Danach PRBE + PRBI triggern und prüfen, ob `sample_size >= 100` und keine Fehler/Anomalien.

Vorbereitung (einmalig)
1) GitHub Secrets müssen gesetzt sein:
- `KRAKEN_TESTNET_API_KEY`
- `KRAKEN_TESTNET_API_SECRET`

2) Workflow vorhanden:
- PR-BJ: `.github/workflows/prbj-testnet-exec-events.yml`
- PR-BG: `.github/workflows/prbg-execution-evidence.yml`
- PR-BE: `.github/workflows/prbe-shadow-testnet-scorecard.yml`
- PR-BI: `.github/workflows/prbi-live-pilot-scorecard.yml`

Ramp-Strategie (empfohlen)
- Ziel: mindestens 100 Events in der JSONL (Sample Size).
- Vorgehen: mehrere PR-BJ Runs mit moderater Dauer statt 1 extrem langer Run.
  - Vorteil: weniger Risiko von Timeouts, stabilere Rate.
- Wenn ein Profil wenig Signale erzeugt: Profil wechseln.

Empfohlene Parameter
- Startprofil: `btc_momentum` oder anderes aktiveres Profil als `ma_crossover_small`
- `duration_min`: 30–60
- Wiederholungen: 2–4 Runs, bis `wc -l execution_events.jsonl >= 100`

Ablauf (Iteration)
1) PR-BJ dispatch (Testnet Exec Events Artifact erzeugen)
- Workflow: `prbj-testnet-exec-events.yml`
- Inputs:
  - `profile`: z. B. `btc_momentum`
  - `duration_min`: z. B. `60`

2) Artifact prüfen (Sample Size/Line Count)
- Download Artifact und `wc -l` auf `execution_events.jsonl`.
- Erwartung: > 2 Zeilen (nicht nur session_start/session_end).

3) PR-BG dispatch (Execution Evidence baut Evidence aus PR-BJ Artifact)
- Workflow: `prbg-execution-evidence.yml`
- Erwartung: `execution_evidence.json` mit `sample_size >= 100`.

4) PR-BE dispatch (Shadow/Testnet Scorecard)
- Workflow: `prbe-shadow-testnet-scorecard.yml`
- Erwartung: weiterhin `READY_FOR_TESTNET`.

5) PR-BI dispatch (Live Pilot Scorecard)
- Workflow: `prbi-live-pilot-scorecard.yml`
- Erwartung: Warning `INSUFFICIENT_SAMPLE_SIZE` verschwindet.
- Entscheidung bleibt nur dann nicht blockiert, wenn:
  - keine `EXECUTION_ERRORS_PRESENT`
  - keine Anomalien über Threshold
  - Shadow/Testnet bereit

Stop-Kriterien
- Stop, sobald `execution_evidence.sample_size >= 100` und PRBI ohne `INSUFFICIENT_SAMPLE_SIZE` läuft.
- Wenn `EXECUTION_ERRORS_PRESENT`: Profil/Dauer anpassen, Fehlerquelle im Testnet-Runner prüfen.

Troubleshooting
- PR-BJ erzeugt nur 2 Lines:
  - Secrets fehlen oder werden nicht gelesen
  - Profil generiert keine Orders/Fills in der Zeit
  - Dauer erhöhen / Profil wechseln
- PR-BG nutzt nicht PR-BJ Artifact:
  - prüfen, ob letzter erfolgreicher PR-BJ Run existiert
  - PR-BG Logs/Artifact-Source prüfen

Sicherheit
- Testnet only. Keine Live-Aktionen.
- Keys strikt getrennt: Bot-Key vs Treasury-Key (siehe separates Runbook).
