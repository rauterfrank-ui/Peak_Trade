# RUNBOOK — Peak_Trade Observability Dashboard (Grafana)
**Scope:** Shadow → Live symbiotischer Kern (Order/Execution Ledger + Metrics/Logs/Traces + Watch-Only UI)

**Zielgruppe:** Operator (du), Dev (Repo), CI/Gates, Incident Response

**Arbeitsmodus:** Cursor Multi‑Agent Chat (deterministisch, evidence-first, watch-only)

**Stand:** 2026‑01‑17 (Europe/Berlin)

> Hinweis (Repo-Kontext):
> - Dieses Runbook ergänzt die bestehende Watch-Only Observability Doku unter `docs/webui/observability/`.
> - Aktuell ist im Repo bereits ein Prometheus/Grafana Setup für **Service/HTTP-Layer** vorhanden (siehe `docs/webui/observability/README.md`).
> - Die hier beschriebenen **Pipeline-/Order-/Execution-Metriken** sind als v1-Contract/Spec dokumentiert, können aber je nach Code-Stand noch nicht vollständig instrumentiert sein.
> - NO-LIVE bleibt unverhandelbar (siehe `docs/webui/DASHBOARD_GOVERNANCE_NO_LIVE.md`).

---

## 0) TL;DR: Was du am Ende hast
- **Ein einheitliches Observability‑Backbone**, das *heute* Shadow‑Runs und *später* Kraken‑Live‑Runs identisch sichtbar macht.
- **Grafana** als *Ops/Monitoring* (Health, Latenz, Errors, Risk‑Blocks, Drift).
- **Peak_Trade Ledger** als *Source of Truth* (Events/Orders/Fills/Fees, replaybar).
- **Watch‑Only Web UI** als *Operator‑Konsole* (Run‑Snapshot, Blotter, Timeline) – optional, aber empfohlen.
- **Saubere Governance‑Schalter**: Live Execution nur via explicit enable + sanity checks + gates.

> Wichtig: Grafana ersetzt **nicht** “Trading‑UI”.  
> Grafana ist “Flugkontrolle/Telemetry”; Peak_Trade Ledger + Kraken sind “Buchhaltung/Wirklichkeit”.

---

## 1) Einstiegspunkte (Choose your own adventure)

### EP‑A: „Ich will sofort Nutzen“ (MVS: Minimum Viable Shadow Dashboard)
Du willst in 1–2 Sessions: **Shadow‑Events sehen**, Fehler/Latenzen erkennen, einfache Panels.
- Fokus: **Metrics + Labels** + 6 Panels + Basic Alerts (optional)
- Kein großes Refactor, keine Live‑Execution

### EP‑B: „Ich will es später 1:1 für Kraken übernehmen“
Du willst heute so bauen, dass Live später nur `mode=live` ist.
- Fokus: **Ledger Contract** + **Adapter‑Boundary** + **Cross‑Check Kraken↔Ledger**
- Grafana Panels identisch, nur Mode‑Filter

### EP‑C: „Ich hab schon Watch‑Only Web v0 – ich will symbiotisch“
Du willst Web‑Dashboard + Grafana sauber zusammenbringen.
- Fokus: **Run‑IDs**, **Snapshots**, **Correlation IDs**, **Deep Links** (Grafana ↔ Web)

### EP‑D: „Ich will zuerst Architektur & Contracts“
Du willst erst die Regeln, dann Code.
- Fokus: **Data Contract**, **Naming**, **Cardinality**, **SLOs**, **Runbook‑Ops**

**Empfehlung:** EP‑B + EP‑C (symbiotischer Kern), aber in Phasen mit MVS zuerst.

---

## 2) Symbiotischer Kern (unverhandelbar)

### 2.1 Source of Truth & Verantwortlichkeiten
| Ebene | System | Wahrheit für | Zweck |
|---|---|---|---|
| External Truth | **Kraken** | was wirklich gehandelt wurde | Broker Reality |
| Internal Truth | **Peak_Trade Ledger** | was Peak_Trade intendiert/gesendet/confirmed/filled hat | Replay, Audit, Debug, Determinismus |
| Observability | **Grafana** | “läuft’s gesund?” | Health, Incidents, Trends |
| Operator UX | **Watch‑Only Web UI** | “was passiert gerade?” | Run-Snapshot, Timeline, Blotter |

**Merke:**  
- Grafana zeigt **Aggregationen**.  
- Ledger/Web zeigen **konkrete Ereignisse** (Order X → Fill Y → Fee Z).

### 2.2 Der gemeinsame Event‑Strom (Shadow & Live identisch)
**Ein Event‑Contract**, der in beiden Modes gleich ist:

- `mode`: `shadow` | `live`
- `run_id`: stabile Session‑ID (low-cardinality im System, aber **nicht** als Prometheus‑Label, wenn es explodiert)
- `strategy_id`, `symbol` (sparsam!)
- `stage`: `signal | intent | submit | ack | fill | cancel | risk_block | error`
- IDs:
  - `intent_id` (intern)
  - `client_order_id` (intern, deterministisch)
  - `broker_order_id` (Kraken, live only)
  - `correlation_id` (optional: trace)
- State:
  - `status`, `qty`, `price`, `fee`, `reason`, `latency_ms`

**Regel:**  
- **Ledger/Logs** dürfen high-cardinality tragen (intent_id, order_id, run_id).  
- **Metrics** dürfen nur low-cardinality tragen (mode, stage, exchange, maybe symbol in limitierter Liste).

---

## 3) Cursor Multi‑Agent Chat Setup (symbiotisch)

### 3.1 Rollen (Minimum Set)
- **ORCHESTRATOR**: hält Scope, entscheidet Reihenfolge, blockt Scope‑Creep.
- **FACTS_COLLECTOR**: scannt Repo‑Iststand (Endpoints, existing metrics, logging, shadow runner).
- **CONTRACT_KEEPER**: definiert Data Contract (Ledger, metrics naming, labels, SLOs).
- **IMPLEMENTER**: setzt Code um (instrumentation, ledger, endpoints).
- **DASHBOARD_ENGINEER**: Grafana Panels, PromQL, Alerts.
- **CI_GUARDIAN**: Tests, docs gates, additive-only, token-policy.
- **EVIDENCE_SCRIBE**: legt Evidence/Run snapshots ab (nur wenn ihr das im Repo trackt).

### 3.2 Output‑Artefakte je Phase
- **Code**: Instrumentation + optional Ledger
- **Docs**: Dashboard Contract + Operator Runbook
- **Grafana**: Dashboard JSON export (optional) + Panel‑Liste + Queries
- **Evidence**: ein Snapshot der erwarteten Metrik‑Serien + Beispiel‑Run

---

## 4) Phasenplan (klar, symbiotisch, “absolut im Kern”)

### Phase 0 — Governance & Grenzen (NO‑LIVE)
**Ziel:** Sicherstellen, dass wir ein Watch‑Only/Shadow‑first Setup bauen.

**Definition of Done (DoD):**
- `LIVE_TRADING_ENABLED=false` default
- Explizites “Enable Gate” (Config + Sanity Check)
- Kein Weg, in Grafana/Web “Trades auszulösen”

**Deliverables:**
- `docs/webui/DASHBOARD_GOVERNANCE_NO_LIVE.md` (oder passende Stelle)
- Config‑Schalter dokumentiert

---

### Phase 1 — Iststand Inventur (Repo)
**Ziel:** Identifizieren, was schon existiert (Web API, Shadow runner, logging, metrics).

**Tasks:**
- Wo werden Runs/Shadow Daten erzeugt?
- Gibt es `/metrics` schon?
- Gibt es bereits `run_id` Registry / Session store?
- Welche Logger/Format (JSON?) existieren?

**DoD:**  
- 1 Seite „Iststand‑Notiz“ inkl. Pfadliste.

---

### Phase 2 — Contracts (Ledger + Metrics + Correlation)
**Ziel:** Ein Vertrag, den Shadow & Live gleichermaßen erfüllen.

#### 2.1 Ledger Contract (Minimum)
**Empfohlen**: JSONL (append-only) oder SQLite (append-only table).  
**Minimum fields:**
```json
{"ts":"...", "mode":"shadow", "run_id":"...", "stage":"intent", "strategy_id":"...", "symbol":"...", "intent_id":"...", "client_order_id":"...", "status":"created", "qty":1.0, "price":123.4, "fee":0.0, "reason":""}
```

#### 2.2 Metrics Contract (Prometheus)
**Names (Beispielkonvention):**
- `peak_trade_pipeline_events_total{mode,stage,exchange}`
- `peak_trade_pipeline_latency_seconds_bucket{mode,edge,exchange}` (edge z.B. `intent_to_ack`, `ack_to_fill`)
- `peak_trade_risk_blocks_total{mode,reason}`
- `peak_trade_feed_gaps_total{mode,feed}`
- `peak_trade_run_state{mode,state}` (gauge, niedrig kardinal)

**Cardinality Rules (hart):**
- Kein `run_id` als Label (außer ihr habt garantiert extrem wenige gleichzeitige Runs).
- Kein `intent_id`, kein `client_order_id`, kein `broker_order_id` als Label.
- `symbol` nur wenn begrenzt (whitelist oder top‑N), sonst in Logs/Ledger.

**DoD:**  
- Doc: `docs/webui/DASHBOARD_DATA_CONTRACT_OBS_v1.md` (oder analog)

---

### Phase 3 — Instrumentation (Code)
**Ziel:** Shadow produziert konsistent Events + Metrics, ohne Refactor‑Hölle.

**Must‑Have:**
- Pipeline stage counters
- Error counters
- Mindestens eine Latenz-Histogramm (intent→ack oder intent→fill)

**Nice‑to‑Have:**
- Trace correlation (OpenTelemetry) mit `correlation_id`

**DoD:**  
- Unit Test: “emits metrics on shadow run”  
- Local run: `curl &#47;metrics` zeigt Serien

---

### Phase 4 — Observability Stack lokal (Dev) & später Prod
**Ziel:** Grafana sieht Daten.

**Optionen:**
- **Local**: docker-compose (Grafana + Prometheus + Loki optional)
- **Prod**: Grafana Cloud oder self‑hosted Stack

**Minimum local setup (Prometheus + Grafana):**
- Prometheus scrapes Peak_Trade `/metrics`
- Grafana datasource Prometheus

**DoD:**  
- `sum(rate(peak_trade_pipeline_events_total{mode="shadow"}[1m])) > 0` im Explore

---

### Phase 5 — Grafana Dashboard (MVS)
**Ziel:** 6–10 Panels, die sofort Nutzen bringen.

#### MVS Panel‑Set (empfohlen)
1) **Event throughput** by `mode,stage`
```promql
sum by (mode, stage) (rate(peak_trade_pipeline_events_total[5m]))
```

2) **Error rate**
```promql
sum(rate(peak_trade_pipeline_events_total{stage="error"}[5m]))
/
sum(rate(peak_trade_pipeline_events_total[5m]))
```

3) **Risk blocks** by reason
```promql
sum by (mode, reason) (rate(peak_trade_risk_blocks_total[5m]))
```

4) **Latency P95** (intent→ack)
```promql
histogram_quantile(0.95, sum by (le, mode) (rate(peak_trade_pipeline_latency_seconds_bucket{edge="intent_to_ack"}[5m])))
```

5) **Feed gaps** (wenn vorhanden)
```promql
sum by (mode, feed) (rate(peak_trade_feed_gaps_total[15m]))
```

6) **Run state** (wenn gauge vorhanden)
```promql
sum by (mode, state) (peak_trade_run_state)
```

**DoD:**  
- Dashboard “Peak_Trade / Ops / Shadow” existiert
- Screenshot/Export (JSON) gespeichert (optional)

---

### Phase 6 — Shadow‑Session Runbook (Operator)
**Ziel:** Du kannst “zuschauen” – reproduzierbar.

**Operator Flow:**
1. Start Shadow run (Runner)
2. Öffne Watch‑Only Web (optional)
3. Öffne Grafana Dashboard
4. Verifiziere:
   - Events > 0
   - Error rate niedrig
   - Latency plausibel
   - Risk blocks erwartbar
5. Stop run & snapshot ledger

**DoD:**  
- 1 kompletter Shadow‑Durchlauf inkl. Evidence (Metrik‑Snapshot + ledger snippet)

---

### Phase 7 — Pre‑Live Hardening (SLOs, Alerts, Guardrails)
**Ziel:** Du erkennst früh, wenn etwas driftet oder brennt.

**SLO‑Vorschläge:**
- Error rate < 1% (shadow), < 0.1% (live) – je nach Reife
- Intent→Ack P95 < X ms
- Feed gaps: 0 sustained

**Alerts (minimal):**
- No events for 5 min (shadow run läuft aber)
- Error rate > threshold
- Risk blocks spike

**DoD:**  
- 3 Alerts vorhanden (auch wenn disabled)

---

### Phase 8 — Live‑Integration (Kraken) ohne UI‑Trading
**Ziel:** Live‑Mode kann beobachtet werden, ohne dass UI etwas auslöst.

**Prinzip:**
- Live Execution nur durch **separaten** Operator‑Command/Process und nur wenn `LIVE_TRADING_ENABLED=true`.
- Web/Grafana bleiben read‑only.

**Must‑Have Cross‑Checks:**
- `client_order_id` ↔ Kraken Order
- Ledger vs Kraken fills/fees reconciliation (periodisch)

**DoD:**  
- Live‑Events erscheinen als `mode="live"` (nur in Test/Sim oder auf Sandbox)

---

### Phase 9 — Incident Runbooks (Ops)
**Ziel:** Wenn etwas schief läuft, weißt du exakt was zu tun ist.

**Runbooks (Minimum):**
- R‑1: “No Metrics / Prometheus down”
- R‑2: “Shadow Events stop / feed gap”
- R‑3: “Error spike / adapter failing”
- R‑4: “Risk blocks unexpected”
- R‑5: “Kraken mismatch / reconciliation failure”

---

## 5) Terminal‑Blöcke (Repo‑konform, Snapshot‑only)

> **Wichtig:** Wenn du diese Befehle *wirklich im Terminal* ausführst:  
> **ein Befehl pro Schritt** (und poste Snapshot), kein Watch, keine Loops.

### T‑0 Pre‑Flight (immer zuerst)
```bash
# Falls du in einer Continuation festhängst (>, dquote>, heredoc>): Ctrl-C
cd /Users/frnkhrz/Peak_Trade
pwd
git rev-parse --show-toplevel
git status -sb
```

### T‑1 Quick Inventory (Pfad‑Scan)
```bash
rg -n "metrics|/metrics|prometheus|opentelemetry|otel|grafana|loki|tempo" src scripts docs .github || true
```

### T‑2 Start local web (falls vorhanden, watch-only)
```bash
python3 -m scripts.live_web_server --help
```

### T‑3 Metrics probe (wenn server läuft)
```bash
curl -sS http://127.0.0.1:8000/metrics | head -n 50
```

---

## 6) Grafana/Prometheus Minimal Setup (lokal)

> Nur als **Option**, wenn ihr lokal schnell starten wollt.  
> Wenn du schon Grafana am Laufen hast: überspringen.

### 6.1 docker-compose (Beispiel)
```yaml
services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./observability/prometheus.yml:/etc/prometheus/prometheus.yml:ro
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    depends_on:
      - prometheus
```

### 6.2 prometheus.yml (Beispiel)
```yaml
global:
  scrape_interval: 5s

scrape_configs:
  - job_name: peak_trade
    metrics_path: /metrics
    static_configs:
      - targets: ["host.docker.internal:8000"]
```

---

## 7) Symbiose: Grafana ↔ Watch‑Only Web ↔ Ledger

### 7.1 Correlation / Deep Link Pattern
- Web UI zeigt `run_id` + “open in Grafana” Link (mit `mode=shadow&from=...`).
- Grafana Panel zeigt “open run snapshot” Link (falls Web Endpoint existiert).

**Regel:**  
Grafana bleibt aggregiert; Web zeigt Details; Ledger ist Audit.

### 7.2 Wo du später “siehst” was wirklich passiert ist
- **In Peak_Trade:** Ledger/Event‑Timeline (run_id filter)
- **In Kraken:** Orders/Trades (client_order_id match)
- **In Grafana:** health + lags + spikes

---

## 8) Cursor Multi‑Agent Prompt‑Blöcke (copy/paste)

### Prompt P‑1 (Repo‑Inventur + Contracts)
**Einsatzort:** Cursor Multi‑Agent Chat  
```text
Rollen: ORCHESTRATOR, FACTS_COLLECTOR, CONTRACT_KEEPER.
Ziel: Repo‑Iststand erfassen (Metrics/Logging/Shadow‑Runner/Web) und daraus einen Observability Contract v1 ableiten.
Lieferung:
1) Pfadliste + kurze Befundpunkte (wo sind Runs, wo ist Web, gibt es /metrics?).
2) Data Contract v1: Ledger Event Schema + Metrics Names/Labels + Cardinality Rules.
3) Empfehlung EP‑A/B/C passend zu Iststand (ohne Inhalte zu recap-en, nur next actions).
Constraints: NO-LIVE default, additive-only, minimal invasive.
```

### Prompt P‑2 (Instrumentation MVS)
**Einsatzort:** Cursor Multi‑Agent Chat  
```text
Rollen: IMPLEMENTER, CI_GUARDIAN, CONTRACT_KEEPER.
Implementiere MVS Observability:
- Counter: peak_trade_pipeline_events_total{mode,stage,exchange}
- Histogram: peak_trade_pipeline_latency_seconds (edge label: intent_to_ack, intent_to_fill)
- Counter: peak_trade_risk_blocks_total{mode,reason}
- Exponiere /metrics (falls nicht vorhanden) in watch-only web app.
- Instrumentiere Shadow pipeline an den Stages: signal, intent, ack, fill, risk_block, error.
Tests:
- Unit test: shadow run emits at least 1 intent event & metrics endpoint returns series.
Docs:
- docs/webui/DASHBOARD_DATA_CONTRACT_OBS_v1.md mit PromQL für 6 Panels.
Constraints:
- Keine high-cardinality Labels (kein run_id/intent_id/order_id).
- NO-LIVE bleibt hard disabled.
```

### Prompt P‑3 (Grafana Dashboard Spec)
**Einsatzort:** Cursor Multi‑Agent Chat  
```text
Rollen: DASHBOARD_ENGINEER, CONTRACT_KEEPER.
Erstelle eine Grafana Dashboard Spezifikation (Markdown):
- Datasource: Prometheus
- Panels: MVS 6 Panels + optional 4 Advanced (feed gaps, reconciliation lag, risk exposure, drops)
- PromQL je Panel
- Variables: mode, exchange, (symbol optional begrenzt)
- Alert suggestions (disabled by default)
Output: docs/webui/GRAFANA_DASHBOARD_SPEC_PEAK_TRADE_OBS_v1.md
```

---

## 9) Acceptance Checklist (Phase‑by‑Phase)

### A‑Checklist (MVS Shadow)
- [ ] Shadow run erzeugt Events (`mode=shadow`)
- [ ] `/metrics` zeigt `peak_trade_pipeline_events_total`
- [ ] Grafana Panel “Shadow Events” > 0
- [ ] Error rate Panel zeigt plausible Werte
- [ ] Ledger/Eventlog vorhanden (optional aber empfohlen)

### B‑Checklist (Ready for Live later)
- [ ] Event Schema gilt für shadow & live
- [ ] Adapter boundary klar (Kraken connector)
- [ ] client_order_id ist deterministisch & matchbar
- [ ] Reconciliation Plan existiert (Ledger↔Kraken)

---

## 10) FAQ (kurz, aber praxisnah)

**„Ist Grafana später wichtig?“**  
Ja, als **Operations‑Nervensystem**. Ohne Grafana siehst du Incidents zu spät.

**„Wo sehe ich später die echten Trades?“**  
Primär: **Peak_Trade Ledger** + **Kraken UI/API**. Grafana zeigt nur aggregiert.

**„Wie handle ich später über Kraken?“**  
Über einen **Execution Adapter** (Kraken API), gesteuert durch Peak_Trade – aber nur wenn `LIVE_TRADING_ENABLED=true` und Governance Checks bestehen.

**„Kann ich meiner AI beim Arbeiten zuschauen?“**  
Ja: Shadow/Live erzeugen Telemetrie; du beobachtest in Grafana/Web. Das ist exakt die Idee.

---

## 11) Nächster Schritt (empfohlen)
Starte mit **Phase 1–3** (Inventur → Contract → Instrumentation MVS).  
Sobald `/metrics` live ist: baue **Phase 5 Dashboard MVS**.
