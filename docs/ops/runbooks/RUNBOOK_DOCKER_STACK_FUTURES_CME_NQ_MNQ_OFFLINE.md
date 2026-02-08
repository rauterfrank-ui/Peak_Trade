# RUNBOOK — Separater Docker-Stack für CME NQ/MNQ (Offline-First, NO-LIVE)

Stand: 2026-02-02 00:32 UTC

## 0) Zweck & Entscheidung
Dieses Runbook beschreibt, wie du **Peak_Trade Futures (CME NQ/MNQ)** als **separaten Docker/Compose-Stack** betreibst, um:
- **Vermischung** mit Daytrading/Crypto zu vermeiden (Daten/Configs/Secrets/Metrics)
- **Crash-Risiko** zu reduzieren (reproduzierbare Runtime, Preflight, Evidence)
- **NO-LIVE** technisch zu erzwingen (Hard-Gates, optional Network-Egress-Block)

> Scope: **Backtest / Replay / Paper**. **Kein Live-Trading.**  
> Out of scope: echte Broker-Integration (nur Stub/Paper), Holiday-Listen im Code.

---

## 1) Ausgangslage (bereits implementiert)
### 1.1 CME NQ/MNQ Implementierung (Offline)
- Contract Specs: `src/markets/cme/contracts.py`
  - NQ: 20 USD/Indexpunkt, Tick 0.25, Tick Value 5 USD
  - MNQ: 2 USD/Indexpunkt, Tick 0.25, Tick Value 0,50 USD
- Symbol-Format & Kalender: `src/markets/cme/symbols.py`, `calendar.py`
  - Canonical Format: `NQH2026`
  - Roll Policy: Montag vor dem 3. Freitag des Expirationsmonats
  - Session-Spec (Globex-ähnlich), keine Holiday-Liste im Code
- Continuous Contract Builder: `src/data/continuous/continuous_contract.py`
  - Stitch + BACK_ADJUST, deterministische OHLCV
- CLI:
  - `scripts/markets/build_continuous_contract.py`
  - `scripts/markets/validate_futures_dataset.py`
- Tests:
  - `tests/data/continuous/test_continuous_contract.py`
  - `tests/markets/cme/test_contract_specs.py`
- Doku/Runbook:
  - `docs/markets/cme/NQ_MNQ_SPEC.md`
  - `docs/markets/cme/ROLL_POLICY.md`
  - `docs/ops/runbooks/RUNBOOK_FUTURES_CME_NQ_MNQ_ENABLEMENT_FINISH.md`
  - Überblick: `docs/markets/UEBERBLICK_FUTURES_NASDAQ100_IMPLEMENTIERT.md`

### 1.2 Offene Punkte (laut Runbook)
- Futures-spezifische Risk-Config (max contracts, daily loss, fees, slippage)
- Observability (Roll Events, Risk Blocks)
- Broker-Adapter (Stub/Paper geplant)
- Evidence Pack

---

## 2) Entscheidungskriterien: „Neuer Stack ja/nein?“
### 2.1 Pro (warum separater Stack)
- **Hard Isolation**: eigene Volumes/Ports/Networks/Job-Namen
- **Repro Runtime**: pinned Dependencies, weniger Drift
- **Safety**: NO-LIVE technisch erzwingbar (Hard-Gates), Secrets nicht mounten
- **Debuggability**: Evidence Pack + logs getrennt

### 2.2 Contra (Kosten/Nachteile)
- zusätzlicher Ops-Overhead (Compose, Ports, Monitoring)
- doppelte Pflege (Images/Deps), wenn keine Base-Images genutzt werden
- zentrale Observability erfordert saubere Label/Target-Trennung

### 2.3 Empfehlung (Minimum)
Wenn dein Hauptproblem **Vermischen + Crash-Risiko** ist:
- ✅ **separates Compose-Projekt + eigene Volumes + Hard-Gates**  
Das ist die kleinste Trennung mit größtem Effekt.

---

## 3) Zielarchitektur (Minimal, safe)
### 3.1 Compose-Projekt
- Projektname: `peaktrade-futures-cme` (via `docker compose -p ...`)
- eigenes Network: `pt_futures_net`
- eigene Ports (Beispiel, kollisionsfrei):
  - Prometheus: `9096:9090` (optional)
  - Grafana: `3002:3000` (optional)
  - Exporter/Service: z.B. `9112` (nur falls nötig)

### 3.2 Volumes (keine Shares!)
- `pt_futures_data` — Futures Raw + Parquet (partitioniert)
- `pt_futures_registry` — Registry/Experiments
- `pt_futures_evidence` — Evidence Packs (pro Run)
- `pt_futures_logs` — NDJSON logs / artifacts

### 3.3 Hard-Gates (Env + Code Assertions)
**Im Compose hart setzen:**
- `PEAK_OFFLINE=1`
- `LIVE_TRADING=0`
- `BROKER_MODE=replay` (oder `paper`)
- `INSTRUMENT_ALLOWLIST=NQ,MNQ`
- `CME_FUTURES_ENABLED=1` (nur im Futures-Stack!)

**In Code/Init hart prüfen:**
- wenn `LIVE_TRADING != 0` → sofort abort
- wenn `BROKER_MODE` nicht in `{paper,replay}` → abort
- wenn Instrument nicht in Allowlist → block

### 3.4 Optional: Network-Egress-Block
- Kein outbound Netzwerk (maximal restriktiv)
- oder allowlist (z.B. nur interne endpoints)
Ziel: keine „versehentlichen“ externen Calls.

---

## 4) Verzeichnis-/Datei-Blueprint (Empfehlung)
Lege (oder plane) im Repo Folgendes an:

```
deploy/
  futures_cme/
    docker-compose.yml
    .env.example
    README.md
    prometheus/            (optional)
      prometheus.yml
    grafana/               (optional)
      provisioning/
evidence/
  futures_cme/
    (auto-generated per run)
```

---

## 5) Compose-Konfiguration (Beispiel-Template)
> Hinweis: Das ist ein Template. Passe Service-Namen, Image und Entrypoints an deine Repo-Struktur an.

### 5.1 `.env.example`
- `PEAK_OFFLINE=1`
- `LIVE_TRADING=0`
- `BROKER_MODE=replay`
- `INSTRUMENT_ALLOWLIST=NQ,MNQ`
- `CME_FUTURES_ENABLED=1`
- `LOG_LEVEL=INFO`
- `EVIDENCE_DIR=/evidence`
- `DATA_DIR=/data`

### 5.2 `docker-compose.yml` (Skizze)
- `futures_runner` (Service der CLI/Jobs ausführt)
- optional `prometheus`, optional `grafana`

**Wichtig:**
- keine Secrets mounten (keine Broker/API Keys aus Daytrading)
- nur die Futures-Volumes

---

## 6) Preflight-Checks (Crash-Prevention)
### 6.1 System (Host)
- Disk frei: ausreichend Headroom (mind. 2–5× der erwarteten Parquet-Ausgabe)
- RAM frei: mindestens ~30% vor dem Build
- SSD empfohlen

### 6.2 Python/Deps im Container
- Python 3.9+
- `pandas`, `numpy`, `pyarrow` kompatibel/pinned
- `pytest` verfügbar

### 6.3 Daten-/Index-Guards (Builder)
- Zeitindex monotonic + keine doppelten Timestamps
- tz-awareness konsistent (tz-naive vs tz-aware vermeiden)
- Partitionierung Parquet nach `root/year/month` empfohlen

---

## 7) Smoke-Test (klein, deterministisch)
Ziel: die Crash-Pfade triggern, ohne große Datenmengen.

1. Tests:
   - `pytest -q tests/data/continuous/test_continuous_contract.py tests/markets/cme/test_contract_specs.py`

2. Mini Build (z.B. 2 Wochen, 1m Bars):
   - `python scripts/markets/build_continuous_contract.py --root NQ --from 2026-01-01 --to 2026-01-15 --method BACK_ADJUST --bar 1m`

3. Validate:
   - `python scripts/markets/validate_futures_dataset.py --root NQ --bar 1m`

**Abbruchkriterien:**
- RAM steigt ohne Plateau (Memory leak / giant concat)
- Laufzeit explodiert am Roll-Tag
- Warnungen: duplicate timestamps / non-monotonic index / tz mismatch

---

## 8) Observability (Minimal-Plan)
### 8.1 Structured Logs (NDJSON)
Emit pro Event:
- `roll_event`: root, from_symbol, to_symbol, roll_ts, roll_policy_version
- `continuous_stitch_event`: rows_in/out, gaps_detected, duplicates_removed
- `back_adjust_event`: adjustment_points, cumulative_adjustment
- `risk_block_event`: reason enum

### 8.2 Prometheus (optional, später)
- Counter: `roll_events_total`, `risk_blocks_total{reason=...}`
- Gauge: `open_contracts{symbol=...}`, `daily_pnl_usd`
- Histogram: `continuous_build_seconds`

---

## 9) Evidence Pack (Pflicht für Repro)
Pro Run ein neues Verzeichnis, z.B.:
- `env.json` (versions, platform, git sha)
- `config_resolved.yaml`
- `run_manifest.json` (dataset ids/hashes, time range)
- `metrics_snapshot.prom` (optional)
- `logs.ndjson`
- `artifacts/checksums.txt`

**DoD Evidence:**
- du kannst jeden Run 1:1 reproduzieren (gleiche inputs → gleiche outputs)

---

## 10) Operations: Start/Stop/Status (Konzept)
### 10.1 Start (Beispiel)
- `docker compose -p peaktrade-futures-cme -f deploy/futures_cme/docker-compose.yml up -d`

### 10.2 Logs
- `docker compose -p peaktrade-futures-cme -f ... logs -f --tail=200`

### 10.3 Stop
- `docker compose -p peaktrade-futures-cme -f ... down`

### 10.4 Cleanup (vorsichtig!)
- `docker compose ... down -v` löscht Volumes → nur wenn wirklich gewollt.

---

## 11) Sicherheits-Checkliste (No-Live Garantie)
- [ ] `LIVE_TRADING=0` im Compose fest verdrahtet
- [ ] keine Broker/API Secrets gemountet
- [ ] Broker Adapter erlaubt nur `{paper,replay}`
- [ ] Instrument Allowlist aktiv (`NQ,MNQ`)
- [ ] optional: outbound Netzwerk blockiert
- [ ] Evidence Pack schreibt Config+Env+Hashes
- [ ] Prometheus/Grafana Targets strikt getrennt (keine Job-Namen-Kollision)

---

## 12) Rollback-Plan (wenn du es doch nicht willst)
- Compose-Projekt stoppen: `docker compose -p peaktrade-futures-cme ... down`
- Volumes behalten (für spätere Entscheidung)
- Alternativ: Volumes exportieren (Parquet/Evidence sichern), dann löschen

---

## 13) Nächste Schritte (wenn du dich dafür entscheidest)
1. Compose-Projekt + Volumes + Hard-Gates anlegen (**Isolation zuerst**)
2. Smoke-Test im Container laufen lassen
3. Evidence Pack automatisieren
4. Risk Config + Preflight Validator implementieren
5. Observability events/metrics ergänzen
6. Broker Stub/Paper (replay only)
