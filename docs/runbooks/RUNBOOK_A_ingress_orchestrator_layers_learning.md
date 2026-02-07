# Runbook A — Incoming-Daten → Orchestrator → Layer-Vorselektion → Learning (inkl. Behavior/Process Critic)
Stand: 2026-02-07  
Scope: Peak_Trade (Kraken Spot REST), **kein** Futures/Derivatives.  
Ziel: **Alle** Incoming-Daten (von außen in Repo/Stack) sauber annehmen, etikettieren, lokal reproduzierbar ablegen, pro AI-Layer sinnvoll vorsortieren und **LearningCapsules** erzeugen – ohne Rohdaten-Leaks.

---

## 0) Grundprinzipien (bitte nicht überspringen)
- **Single Ingress**: Es gibt **eine** zentrale Inbox: Orchestrator/IngestionHub.
- **Single Egress**: Layer bekommen nur **Envelope** (kompakt, allowlisted, budgetiert).
- **Rohdaten bleiben lokal**: Rohpayload/Transkripte/Secrets nie direkt in Prompts/Envelopes; nur **Pointer + Hash**.
- **Deterministisch**: Vorselektion nach Regeln/Heuristiken (testbar), nicht "LLM entscheidet Wahrheit".
- **Learning getrennt von Serving**: LearningCapsules lokal (out/ops), optional später exportiert – nie "still".

---

## 1) Begriffsklärung in einfacher Sprache
- **Incoming-Daten**: alles, was "von außen" reinkommt (Market Data, Exchange Events, Logs, CI Output, manuelle Notizen, Dateien).
- **Event**: eine normalisierte "Postkarte" mit Metadaten (woher, wann, was, wie sensibel) + lokalem Rohinhalt.
- **FeatureView**: kompaktes "Was ist passiert?" (Metriken/Fakten/Tags) + Verweise auf Artefakte.
- **LayerEnvelope**: Paket pro Layer (L1/L2/L4) mit erlaubten Infos und Budgets.
- **LearningCapsule**: "Lernzettel" (Input/Output/Labels/Score), lokal gespeichert.

---

## 2) Layer-Map (heute)
- **L0** Orchestrator: Ingress + Routing + Tools
- **L1** DeepResearch ("Detektiv")
- **L2** Market Outlook ("Wetterbericht")
- **L3** Advisory (bei euch: Rolle/Map, kein eigener Runner)
- **L4** Critic/Policy ("Prüfer")
- **L5** Risk Gate (deterministisch, kein LLM)
- **L6** Execution (live gated / verboten für LLM)

Zusatz-Layer (neu, empfohlen):
- **LP0** Pre-Processor / Data Triage ("Aufräumer"): macht aus Rohdaten eine kurze, saubere Lage + Artefaktliste
- **LB1** Behavior & Process Critic ("Disziplin-Score"): bewertet **Prozessqualität** (Plan/Risk/Regeln), nicht mentale Gesundheit

---

## 3) Ergebnisartefakte & Speicherorte (konventionell)
> Wenn ihr schon andere Pfade nutzt, passt diese 3 Pfade als Konstante an.

- `out/ops/events/`  
  - `EVENTS_<run_id>_<ts>.jsonl` (+ `.sha256`)
- `out/ops/views/`  
  - `FEATURE_VIEW_<run_id>_<ts>.json` (+ `.sha256`)
- `out/ops/capsules/`  
  - `CAPSULES_<run_id>_<ts>.jsonl` (+ `.sha256`)
- `out/ops/audit/`  
  - `AUDIT_<run_id>.log` (append-only)

---

## 4) Phasenübersicht (A bis Z)
### Phase A1 — Inventar & Klassifizierung Incoming-Daten
**Ziel**: Liste + Kategorien + Sensitivity.  
**Einstieg**: du bist im Repo, Shadow läuft oder nicht.  
**Endpunkt**: "Incoming Taxonomy" ist dokumentiert.

**Schritte**
1. Alle Quellen sammeln (Docs + Code):
   - Data: `src/data/*` (Kraken OHLC, CCXT backend)
   - Exchange: `src/exchange/*` (KrakenTestnetClient, ccxt client)
   - Live/Shadow: `src/live/shadow_session.py`, `src/execution/live_session.py`
   - Scripts: `run_shadow_execution.py`, `run_testnet_session.py`, `check_live_readiness.py`, …
2. Tabelle erstellen:
   - Quelle → Event-Kind → Beispiel-Payload → Sensitivity → Retention

**Checkpoint**
- Für jede Quelle ist klar:
  - `source` (cli/runner/file/telemetry/market_data/exchange/system)
  - `kind` (ohlcv, ticker, order_intent, order_result, metrics, alert, config_change, transcript, …)
  - `sensitivity` (none / risk_strat_raw / pii / secrets / ops_internal)

**Troubleshoot**
- Wenn etwas "zu groß" ist: nicht direkt senden, sondern als Datei ablegen → nur pointer.

---

### Phase A2 — Single Ingress: NormalizedEvent-Contract + Writer
**Ziel**: alles geht zuerst in `NormalizedEvent` und wird lokal append-only gespeichert.  
**Einstieg**: Phase A1 fertig oder du hast bereits eine Event-Struktur.  
**Endpunkt**: `hub.ingest(...)` wird an allen Ingress-Stellen genutzt (oder parallel "tap").

**Schritte**
1. Contract festlegen (Minimalfelder):
   - `event_id`, `ts_ms`, `source`, `kind`, `scope`, `tags`, `sensitivity`, `payload`
2. Writer:
   - JSONL append + sha256 manifest
3. Policy:
   - Raw payload (z.B. Transcript Text) **nur** lokal, nicht in Envelope

**Exit Criteria**
- Mindestens 1 Pipeline (Shadow oder Data) schreibt Events in `out/ops/events/`.

---

### Phase A3 — FeatureViews bauen (kompakt & deterministisch)
**Ziel**: Aus Events eine FeatureView erstellen, die für Routing/Layer reicht.  
**Endpunkt**: FeatureView ist reproduzierbar und klein.

**Schritte**
1. Regeln:
   - Aggregationen: counts, latenz, gaps, ohlcv summary, error counters
   - "Wichtige Fakten": symbol, timeframe, run_id, last candle ts, etc.
2. Artefakte:
   - Rohdaten/Reports als Datei ablegen
   - FeatureView enthält nur `path+sha256` Pointer

**Exit Criteria**
- FeatureView JSON existiert + sha256, und kann in Tests verifiziert werden.

---

### Phase A4 — LayerEnvelope Preselection (Allowlist + Budgets)
**Ziel**: L1/L2/L4 bekommen genau das richtige "Futter", kein Leak.  
**Endpunkt**: pro Layer Envelope erstellt und getestet.

**Budgets (Startwerte, später feinjustieren)**
- L1: viel Analyse, mehr Artefakte
- L2: weniger Details, mehr Aggregation
- L4: mehr Audit-Metadaten, aber trotzdem keine Rohpayload

**Schritte**
1. Per Layer definieren:
   - erlaubte Faktenfelder
   - erlaubte Artefakt-Typen
   - max chars / max artefacts
2. Tests:
   - "Raw darf nicht vorkommen"
   - "Pointer muss vorkommen"

**Exit Criteria**
- Testsuite "no raw leak" grün.

---

### Phase A5 — Tools: Artifact Resolver (controlled reveal)
**Ziel**: Layer kann "bitte Artefakt X laden" → Orchestrator liefert redacted snippet.  
**Endpunkt**: Toolcall existiert, mit Allowlist, Logging.

**Mindestregeln**
- Only read from `out/ops/` allowlist
- Snippet-Limits (z.B. max 2k chars)
- Redaction (secrets/keys) vor Ausgabe

---

### Phase A6 — LearningCapsules (lokal, signiert)
**Ziel**: Jede Layer-Interaktion erzeugt Lernzettel.  
**Endpunkt**: jsonl + sha256 manifest pro run.

**Capsule Inhalte (empfohlen)**
- Input: FeatureView hash + Envelope summary
- Output: Layer response (kompakt)
- Labels:
  - `process_score` (von Behavior layer)
  - `critic_flags` (von L4)
- Metrics: latency, cost, token counts, etc.

**Wichtig**
- Outcome (PnL) getrennt von ProcessScore.
- Kein Auto-Export nach außen.

---

### Phase A7 — Behavior & Process Critic (LB1) einführen
**Ziel**: "Belohnung" als **ProcessScore** (Plan/Risk/Regeln).  
**Endpunkt**: Scorecard pro Trade/Session, unabhängig von Gewinn/Verlust.

**Bewertungsbereiche (Start)**
- Plan-Compliance (0–100)
- Risk-Compliance (0–100)
- Execution-Quality (0–100)
- Overtrading/Churn (0–100)
- Regelverstöße (Liste)

**Inputs**
- Trade/Order Events (intent/result)
- Risk-Gate decisions
- Config changes (z.B. leverage, size)
- Timing/Latency metrics

**Outputs**
- `process_score_total`
- `violations[]` (konkret: "Stop missing", "size > limit", …)
- Capsule `kind="labels"`

---

### Phase A8 — Dokumentation + Entry/Exit Points (dieses Runbook)
**Ziel**: Wieder-Einstieg nach Pausen.  
**Endpunkt**: Jeder Phase hat klare Checkpoints und Artefakte.

---

## 5) Wieder-Einstiegspunkte (Quick Resume)
### Resume R1: "Ich will nur sehen, ob Events geschrieben werden"
- Prüfe: `out/ops/events/` neue JSONL?
- Prüfe: sha256 manifest ok?
- Prüfe: event_kinds counts

### Resume R2: "Envelopes testen"
- Run: unit tests (no raw leak)
- Erzeuge 1 Dummy-Event mit raw text → sicherstellen, dass raw nicht in Envelope landet

### Resume R3: "LearningCapsules erzeugen"
- Trigger 1 Shadow cycle
- Prüfe `out/ops/capsules/` neue jsonl + sha256

---

## 6) Definition of Done (Finish)
- [ ] Alle Incoming-Quellen schreiben `NormalizedEvent` (oder werden getappt)
- [ ] FeatureViews existieren deterministisch
- [ ] L1/L2/L4 Envelopes sind allowlisted + budgetiert
- [ ] Artifact Resolver Tool funktioniert, mit Redaction + logging
- [ ] LearningCapsules laufen automatisch, lokal signiert
- [ ] Behavior/Process Critic erzeugt ProcessScore + violations
- [ ] L4 Critic prüft Output + Flags (0 policy leaks)
- [ ] Dashboards/Prometheus zeigen Health (optional, aber empfohlen)

---

## 7) Anhang: Minimal Checklists
### A) "No-raw-leak"
- [ ] Kein Rohtext im Envelope
- [ ] Keine API Keys im Envelope
- [ ] Nur pointer+hash

### B) "Reproduzierbarkeit"
- [ ] run_id überall
- [ ] artifact sha256 überall
- [ ] append-only logs

### C) "Safety"
- [ ] single egress boundary
- [ ] budgets enforced
- [ ] kill switch vorhanden (siehe Runbook B)

---

## Appendix (Repo-derived drafts)

- docs/runbooks/appendix/A1_incoming_taxonomy.md
- docs/runbooks/appendix/A1_incoming_taxonomy_evidence.md
