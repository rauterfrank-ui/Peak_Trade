# RUNBOOK — Peak_Trade Observability Dashboard (Grafana)
**Scope:** Shadow → Live symbiotischer Kern (Order/Execution Ledger + Metrics/Logs/Traces + Watch-Only UI)

**Zielgruppe:** Operator (du), Dev (Repo), CI/Gates, Incident Response

**Arbeitsmodus:** Cursor Multi‑Agent Chat (deterministisch, evidence-first, watch-only)

**Stand:** 2026‑01‑17 (Europe/Berlin)

> **NO‑LIVE / WATCH‑ONLY (nicht verhandelbar)**  
> - Keine Trading‑Keys, keine Order‑Execution, keine Live‑Trades.  
> - Observability ist **read‑only** (Prometheus/Grafana), keine „Trading‑UI“.  
> - Deterministisch: keine Watch‑Loops; nur Snapshot‑Checks / Smoke.  
> - macOS Docker Desktop: Host‑Brücke via **`host.docker.internal`**.  

> Hinweis (Repo-Kontext):
> - Dieses Runbook ergänzt die bestehende Watch-Only Observability Doku unter `docs&#47;webui&#47;observability&#47;`.
> - Aktuell ist im Repo bereits ein Prometheus/Grafana Setup für **Service/HTTP-Layer** vorhanden (siehe `docs&#47;webui&#47;observability&#47;README.md`).
> - Die hier beschriebenen **Pipeline-/Order-/Execution-Metriken** sind als v1-Contract/Spec dokumentiert, können aber je nach Code-Stand noch nicht vollständig instrumentiert sein.
> - NO-LIVE bleibt unverhandelbar (siehe `docs&#47;webui&#47;DASHBOARD_GOVERNANCE_NO_LIVE.md`).

---

## 0) TL;DR: Was du am Ende hast
- **Ein einheitliches Observability‑Backbone**, das *heute* Shadow‑Runs und *später* Kraken‑Live‑Runs identisch sichtbar macht.
- **Grafana** als *Ops/Monitoring* (Health, Latenz, Errors, Risk‑Blocks, Drift).
- **Peak_Trade Ledger** als *Source of Truth* (Events/Orders/Fills/Fees, replaybar).
- **Watch‑Only Web UI** als *Operator‑Konsole* (Run‑Snapshot, Blotter, Timeline) – optional, aber empfohlen.
- **Saubere Governance‑Schalter**: Live Execution nur via explicit enable + sanity checks + gates.
- **Deterministisch (Operator‑tauglich)**: Shadow‑MVS Stack via `scripts&#47;obs&#47;shadow_mvs_local_{down,up,verify}.sh` (Snapshot‑Checks, keine Watch‑Loops).

### Operator Quickstart (lokal, <5 Minuten): Shadow MVS → Prometheus → Grafana → VERIFY PASS

Ziel: **ohne UI‑Klicks** ein reproduzierbares Shadow‑MVS Dashboard mit Daten sehen (watch‑only).

```bash
bash scripts/obs/shadow_mvs_local_down.sh
bash scripts/obs/shadow_mvs_local_up.sh
bash scripts/obs/shadow_mvs_local_verify.sh
```

> Projektname ist fix: `peaktrade-shadow-mvs` → verhindert Cross‑Orphans (Compose).

#### Hardening Notes (Compose/Verify/Panels)
- Compose‑Projekt fix: `-p peaktrade-shadow-mvs` (verhindert Orphans)
- `up`: `... up -d --renew-anon-volumes --remove-orphans` (keine Grafana‑DB/Passwort‑Drift)
- `down`: `... down -v --remove-orphans` (sauberer Reset)
- Verify: Warmup‑Retries ohne Traceback‑Spam; Grafana‑Auth‑Fail → klare 401‑Meldung
- Verify: Stage‑Query Window **`[5m]`** (weniger flappy)
- Panels: Error‑Rate Nenner via `clamp_min(..., 1e-9)` (stabil bei low traffic)

#### Contract (Single Source of Truth)
- `docs&#47;webui&#47;observability&#47;SHADOW_MVS_CONTRACT.md`
  - Ports/Endpoints
  - Prometheus Job `job="shadow_mvs"`
  - Grafana Datasource/Dashboard Provisioning (UIDs)
  - Golden Queries (Snapshot) + Failure Mapping → Phase F

#### Verify Output (maschinenlesbar)
`bash scripts&#47;obs&#47;shadow_mvs_local_verify.sh` gibt **PASS/FAIL pro Check** aus, plus **EVIDENCE**-Zeilen und `RESULT=PASS|FAIL` (copy/paste für Merge-Log/PR).

#### Verify PASS Evidence (Deterministic, Snapshot-only)
Wenn du einen **reproduzierbaren PASS-Snapshot** (inkl. bounded retries + warmup) als Log brauchst:

```bash
LOG="/tmp/pt_shadow_mvs_verify.log"
rm -f "$LOG"
bash scripts/obs/shadow_mvs_local_down.sh 2>&1 | tee -a "$LOG"
bash scripts/obs/shadow_mvs_local_up.sh 2>&1 | tee -a "$LOG"
bash scripts/obs/shadow_mvs_local_verify.sh 2>&1 | tee -a "$LOG"
bash scripts/obs/shadow_mvs_local_down.sh 2>&1 | tee -a "$LOG"
rg -n "^(INFO\\|targets_retry=|EVIDENCE\\||RESULT=|INFO\\|See Contract:)" "$LOG" || true
echo "$LOG"
```

**PASS-Kriterien (Evidence Extract):**
- `INFO|targets_retry=...`
- `EVIDENCE|exporter=...`
- `EVIDENCE|prometheus=...`
- `EVIDENCE|grafana=...`
- `EVIDENCE|dashboard_uid=...`
- `RESULT=PASS`
- `INFO|See Contract: docs&#47;webui&#47;observability&#47;SHADOW_MVS_CONTRACT.md`

**Warum Retries/Warmup ok sind (ohne “ewig grün”):**
- Prometheus Targets können kurz leer sein direkt nach `up` → bounded `targets_retry`
- Grafana health kann kurz nicht ready sein → bounded health retries
- `rate(...[5m])`/`histogram_quantile(...)` kann in den ersten Scrapes leer/NaN sein → bounded warmup retries

#### Phase F — Troubleshooting (Decision Tree, kurz)
Wenn **irgendwas FAIL**: **sofort** auf den passenden Knoten springen (kein Scope-Creep).
- **F-1 Grafana Login/DS**: 401/403, Datasource/Dashboard fehlt → `bash scripts&#47;obs&#47;shadow_mvs_local_down.sh && bash scripts&#47;obs&#47;shadow_mvs_local_up.sh`
- **F-2 Prometheus Target DOWN**: `shadow_mvs` nicht UP → `http://127.0.0.1:9092/targets` + `docs&#47;webui&#47;observability&#47;PROMETHEUS_LOCAL_SCRAPE.yml`
- **F-3 /metrics leer/alt**: Contract-Serien fehlen → `bash scripts&#47;obs&#47;shadow_mvs_local_up.sh` (Exporter stdout) oder `bash scripts&#47;obs&#47;shadow_mvs_local_verify.sh`
- **F-4 Panels leer**: Targets UP, aber Queries leer → Time-Range (15m/1h), Filters (`mode`, `exchange`), Datasource

**Expected Outcomes (VERIFY PASS):**
- Exporter (Host): `http:&#47;&#47;127.0.0.1:9109&#47;metrics` ist erreichbar und enthält:
  - `shadow_mvs_up`
  - `peak_trade_pipeline_events_total`
- Prometheus-local (Host): `http://127.0.0.1:9092` zeigt unter `&#47;targets` **`job="shadow_mvs"` = UP**
- Grafana (Host): `http://127.0.0.1:3000` (Login: Credentials aus `.env` oder `GRAFANA_AUTH=user:pass`)
  - Datasource default: **`prometheus-local`** (UID `peaktrade-prometheus-local`, URL `http://host.docker.internal:9092`)
  - Dashboard sichtbar: UID **`peaktrade-shadow-pipeline-mvs`**

Details & Workflow: `docs&#47;webui&#47;observability&#47;README.md` und `docs&#47;webui&#47;observability&#47;DASHBOARD_WORKFLOW.md`.

> Wenn `shadow_mvs_local_verify.sh` fehlschlägt: springe zu **Phase F** (Decision Tree) und folge dem passenden Knoten.

> Wichtig: Grafana ersetzt **nicht** “Trading‑UI”.  
> Grafana ist “Flugkontrolle/Telemetry”; Peak_Trade Ledger + Kraken sind “Buchhaltung/Wirklichkeit”.

---

## Operator Entry (Shadow MVS Observability) — Standard-Startpunkt
**Ziel:** Du startest **immer hier**, wenn du Shadow MVS → Prometheus → Grafana reproduzierbar (watch‑only) laufen lassen willst.

> Hinweis zur Benennung: Die folgenden „Phasen E–H“ sind der **kanonische Operator‑Ablauf** (Snapshot → Up → Verify/Triage → Down).  
> Die inhaltlichen Runbook‑Abschnitte zu Persist/Provision/Smoke/Triage/Live‑Shape sind weiter unten dokumentiert.

### Phase E — Repo Snapshot (E‑1)
**Pre‑Flight (snapshot‑only):**

```bash
# Pre-Flight (Snapshot-only)
# Wenn du in einer Continuation festhängst (>, dquote>, heredoc>): Ctrl-C
cd /Users/frnkhrz/Peak_Trade
pwd
git rev-parse --show-toplevel
git status -sb
```

**Command:**

```bash
git status -sb
```

**Expected:** Branch ist clean oder bewusst staged; keine „Überraschungen“ außerhalb des erwarteten Diffs.

---

### Phase F — Bring-Up lokal (F‑1)
**Pre‑Flight (snapshot‑only):**

```bash
# Pre-Flight (Snapshot-only)
# Wenn du in einer Continuation festhängst (>, dquote>, heredoc>): Ctrl-C
cd /Users/frnkhrz/Peak_Trade
pwd
git rev-parse --show-toplevel
git status -sb
```

**Command:**

```bash
bash scripts/obs/shadow_mvs_local_up.sh
```

**Expected (Endpoints erreichbar):**
- Exporter: `http:&#47;&#47;127.0.0.1:9109&#47;metrics`
- Prometheus-local: `http://127.0.0.1:9092`
- Grafana: `http://127.0.0.1:3000`

---

### Phase G — Deterministic Verify + TRIAGE (G‑0…G‑8)
**Pre‑Flight (snapshot‑only):**

```bash
# Pre-Flight (Snapshot-only)
# Wenn du in einer Continuation festhängst (>, dquote>, heredoc>): Ctrl-C
cd /Users/frnkhrz/Peak_Trade
pwd
git rev-parse --show-toplevel
git status -sb
```

#### G‑0 Verify Command (kanonisch)

```bash
bash scripts/obs/shadow_mvs_local_verify.sh
```

**Expected (MUSS PASS):**
- Prometheus Targets: `job="shadow_mvs"` = UP
- PromQL Smoke (non‑empty):
  - `up{job="shadow_mvs"}`
  - Stage‑Query: `sum by (mode, stage) (rate(peak_trade_pipeline_events_total{mode="shadow"}[5m]))`
- Grafana:
  - Default Datasource: UID `peaktrade-prometheus-local`
  - URL enthält: `http://host.docker.internal:9092`
- Dashboard UID sichtbar: `peaktrade-shadow-pipeline-mvs`

**IF FAIL → TRIAGE ENTRY**
- Springe direkt zu **Phase G: Decision Tree (G‑1…G‑8)** (weiter unten im Runbook).
- Pro Knoten gilt: Symptom → Ursache → 1–2 Next Commands (snapshot‑only) → zurück zu **G‑0**.

---

### Phase H — Stop/Cleanup lokal (H‑1)
**Pre‑Flight (snapshot‑only):**

```bash
# Pre-Flight (Snapshot-only)
# Wenn du in einer Continuation festhängst (>, dquote>, heredoc>): Ctrl-C
cd /Users/frnkhrz/Peak_Trade
pwd
git rev-parse --show-toplevel
git status -sb
```

**Command:**

```bash
bash scripts/obs/shadow_mvs_local_down.sh
```

**Expected:** Exporter auf `http:&#47;&#47;127.0.0.1:9109&#47;metrics` ist nicht mehr erreichbar (lokal gestoppt).

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
- `docs&#47;webui&#47;DASHBOARD_GOVERNANCE_NO_LIVE.md` (oder passende Stelle)
- Config‑Schalter dokumentiert

---

### Phase 1 — Iststand Inventur (Repo)
**Ziel:** Identifizieren, was schon existiert (Web API, Shadow runner, logging, metrics).

**Tasks:**
- Wo werden Runs/Shadow Daten erzeugt?
- Gibt es `&#47;metrics` schon?
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
- Doc: `docs&#47;webui&#47;DASHBOARD_DATA_CONTRACT_OBS_v1.md` (oder analog)

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
- Prometheus scrapes Peak_Trade `&#47;metrics`
- Grafana datasource Prometheus

**DoD:**  
- `sum(rate(peak_trade_pipeline_events_total{mode="shadow"}[5m])) > 0` im Explore

---

### Phase A–D — Shadow MVS Local Backbone (bereits abgeschlossen; nur Referenzen)
**Ziel:** Ein lokales, deterministisches „Known‑Good“ Backbone (Exporter → Prometheus → Grafana) als Ausgangspunkt für Persist/Operate/Live‑Shape.

**Inputs/Preconditions:**
- macOS Docker Desktop (Host‑Bridge via `host.docker.internal`)
- Repo‑lokal (keine Secrets)

**Operator Steps (kanonisch, snapshot‑only):**
1) Start: `bash scripts&#47;obs&#47;shadow_mvs_local_up.sh`
2) Verify/Smoke: `bash scripts&#47;obs&#47;shadow_mvs_local_verify.sh`
3) Stop: `bash scripts&#47;obs&#47;shadow_mvs_local_down.sh`

**Expected Outcomes (Known‑Good):**
- Exporter: `http:&#47;&#47;127.0.0.1:9109&#47;metrics`
- Prometheus-local: `http://127.0.0.1:9092` mit Target `job="shadow_mvs"` UP (Scrape: `docs&#47;webui&#47;observability&#47;PROMETHEUS_LOCAL_SCRAPE.yml`)
- Grafana: `http://127.0.0.1:3000` mit file‑provisioned Datasource + Dashboard (siehe Phase E)

---

### Phase E — Grafana „Persist & Provision“ (formalisiert; Default = Strategy A)
**Ziel:** Weg von „UI manuell gebaut“ → **reproduzierbar aus dem Repo** (Grafana startet mit Datasource + Dashboard ohne Klicks).

**Inputs/Preconditions:**
- Grafana läuft via Compose (empfohlen: Grafana‑only) und mountet Provisioning/JSONs read‑only.
- Prometheus‑Endpoint erreichbar (Default: `prometheus-local` via `host.docker.internal:9092`).

**Strategy A (Default): Auto‑Provision via Repo‑Assets**
- Datasource provisioning (YAML):  
  - `docs&#47;webui&#47;observability&#47;grafana&#47;provisioning&#47;datasources&#47;datasources.prometheus-local.yaml`
- Dashboard provider provisioning (YAML):  
  - `docs&#47;webui&#47;observability&#47;grafana&#47;provisioning&#47;dashboards&#47;dashboards.yaml` (Provider → `&#47;etc&#47;grafana&#47;dashboards`)
- Dashboard JSONs (file‑based):  
  - `docs&#47;webui&#47;observability&#47;grafana&#47;dashboards&#47;shadow&#47;peaktrade-shadow-pipeline-mvs.json` (UID: `peaktrade-shadow-pipeline-mvs`)

**Empfohlener lokaler Betrieb (Known‑Good Pairing):**
1) Prometheus-local starten: `docs&#47;webui&#47;observability&#47;DOCKER_COMPOSE_PROMETHEUS_LOCAL.yml` (Host `:9092`)
2) Grafana-only starten: `docs&#47;webui&#47;observability&#47;DOCKER_COMPOSE_GRAFANA_ONLY.yml` (Host `:3000`)

**Wiring Matrix (Compose → Mounts → Provisioning → Expectation):**
| Compose File | Mounts (Container) | Provisioning Files (Repo) | Expected Datasource | Expected Dashboard UID |
|---|---|---|---|---|
| `docs&#47;webui&#47;observability&#47;DOCKER_COMPOSE_GRAFANA_ONLY.yml` | `&#47;etc&#47;grafana&#47;provisioning&#47;datasources` (ro) | `grafana&#47;provisioning&#47;datasources&#47;datasources.prometheus-local.yaml` | Name `prometheus-local` (UID `peaktrade-prometheus-local`, Default, URL `http://host.docker.internal:9092`) | `peaktrade-shadow-pipeline-mvs` |
| `docs&#47;webui&#47;observability&#47;DOCKER_COMPOSE_GRAFANA_ONLY.yml` | `&#47;etc&#47;grafana&#47;provisioning&#47;dashboards` (ro) | `grafana&#47;provisioning&#47;dashboards&#47;dashboards.yaml` | (n/a) | Folder `"Peak_Trade"` lädt JSONs aus `&#47;etc&#47;grafana&#47;dashboards` |
| `docs&#47;webui&#47;observability&#47;DOCKER_COMPOSE_GRAFANA_ONLY.yml` | `&#47;etc&#47;grafana&#47;dashboards` (ro) | `grafana&#47;dashboards&#47;*.json` | (n/a) | JSON enthält UID `peaktrade-shadow-pipeline-mvs` |

> Wiring‑Details (Dashboard Lifecycle, Provider path, Recreate‑Hinweis): siehe `docs&#47;webui&#47;observability&#47;DASHBOARD_WORKFLOW.md`.

**Failure Hook:** Wenn Datasource/Dashboard fehlt → **Phase G‑3 / G‑4**.

#### Appendix (kurz): Strategy B = 1‑Click Import (Fallback, wenn Provisioning nicht gemountet ist)
1) Grafana öffnen: `http://127.0.0.1:3000` (admin&#47;admin)  
2) Dashboard importieren aus Datei: `docs&#47;webui&#47;observability&#47;grafana&#47;dashboards&#47;shadow&#47;peaktrade-shadow-pipeline-mvs.json`  
3) Datasource wählen: `prometheus-local` (URL `http://host.docker.internal:9092`)  
4) Speichern im Folder `"Peak_Trade"`  

---

### Phase F — Operator Smoke (Snapshot‑only; kanonisch = `shadow_mvs_local_verify.sh`)
**Ziel:** In 30–60 Sekunden ein deterministischer PASS/FAIL‑Snapshot für Targets, Datasource, Dashboard und Kernqueries.

**Inputs/Preconditions:**
- `bash scripts&#47;obs&#47;shadow_mvs_local_up.sh` wurde ausgeführt (Exporter + Prometheus-local + Grafana laufen).

**Operator Steps (kanonisch):**
1) Smoke/Verify laufen lassen:

```bash
bash scripts/obs/shadow_mvs_local_verify.sh
```

2) (Optional) Manuelle Snapshot‑Checks (nur wenn du Debug brauchst):
- Exporter:
  - `curl -fsS http:&#47;&#47;127.0.0.1:9109&#47;metrics | head -n 50`
- Prometheus:
  - `curl -fsS "http:&#47;&#47;127.0.0.1:9092&#47;api&#47;v1&#47;query?query=up%7Bjob%3D%22shadow_mvs%22%7D"`
- Grafana:
  - `curl -fsS -u "$GRAFANA_AUTH" http:&#47;&#47;127.0.0.1:3000&#47;api&#47;health` (GRAFANA_AUTH aus .env oder export)

**Smoke Checklist (was das Script prüft):**
- Exporter erreichbar und enthält `shadow_mvs_up` + `peak_trade_pipeline_events_total`
- Grafana health ok
- Grafana Datasource: `prometheus-local` default (UID `peaktrade-prometheus-local`, URL enthält `host.docker.internal:9092`)
- Grafana Dashboard provisioned: UID `peaktrade-shadow-pipeline-mvs`
- Prometheus targets: `job="shadow_mvs"` UP
- PromQL liefert **non‑empty** Ergebnisse (Snapshot)

**Fixe PromQL‑Beispiele (Explore/Prometheus API):**
- Target up:
  - `up{job="shadow_mvs"}`
- Stage‑Events (non‑empty):
  - `sum by (mode, stage) (rate(peak_trade_pipeline_events_total{mode="shadow"}[5m]))`

**Verify Codes (Runbook‑Konvention, für Triage):**
- `F-OK`
- `F-FAIL-EXPORTER`
- `F-FAIL-GRAFANA`
- `F-FAIL-DATASOURCE`
- `F-FAIL-DASHBOARD`
- `F-FAIL-TARGETS`
- `F-FAIL-QUERIES`

**Failure Hook:** Bei Fail → Phase G (passender Knoten).

---

### Phase G — Failure Modes / Triage Decision Tree (≤ 9 Knoten, snapshot‑only)
**Ziel:** 90% der lokalen Fehler ohne Chat lösen: Symptom → Ursache → 1–2 Next Commands.

> Konvention: starte immer mit `bash scripts&#47;obs&#47;shadow_mvs_local_verify.sh` und mappe das erste rote Symptom auf einen Knoten.

#### G‑1: Exporter down / `:9109` nicht erreichbar
- **Symptom**: `curl http:&#47;&#47;127.0.0.1:9109&#47;metrics` schlägt fehl oder `shadow_mvs_local_verify.sh` meldet Exporter timeout
- **Wahrscheinlichste Ursache**: Exporter Prozess läuft nicht / Port belegt
- **Next Commands (snapshot)**:
  - `bash scripts&#47;obs&#47;shadow_mvs_local_up.sh`
  - `lsof -nP -iTCP:9109 -sTCP:LISTEN || true`

#### G‑2: Prometheus-local nicht ready / `:9092` down
- **Symptom**: `http:&#47;&#47;127.0.0.1:9092&#47;-&#47;ready` nicht OK
- **Wahrscheinlichste Ursache**: Compose nicht up / Docker nicht gestartet
- **Next Commands (snapshot)**:
  - `docker compose -p peaktrade-shadow-mvs -f docs&#47;webui&#47;observability&#47;DOCKER_COMPOSE_PROMETHEUS_LOCAL.yml ps`
  - `docker compose -p peaktrade-shadow-mvs -f docs&#47;webui&#47;observability&#47;DOCKER_COMPOSE_PROMETHEUS_LOCAL.yml up -d --force-recreate --renew-anon-volumes --remove-orphans`

#### G‑3: Prometheus Target `job="shadow_mvs"` DOWN
- **Symptom**: Prometheus `&#47;targets` zeigt `shadow_mvs` down
- **Wahrscheinlichste Ursache**: Host‑Bridge/Target falsch, Exporter down, oder falsche Scrape Config
- **Next Commands (snapshot)**:
  - `curl -fsS http:&#47;&#47;127.0.0.1:9109&#47;metrics | grep -n "^shadow_mvs_up" | head -n 5 || true`
  - `sed -n '1,120p' docs&#47;webui&#47;observability&#47;PROMETHEUS_LOCAL_SCRAPE.yml`
    - Erwartung: `targets: ["host.docker.internal:9109"]`

#### G‑4: Grafana down / health nicht OK
- **Symptom**: `curl -u "$GRAFANA_AUTH" http:&#47;&#47;127.0.0.1:3000&#47;api&#47;health` fail
- **Wahrscheinlichste Ursache**: Grafana container nicht läuft / Port `:3000` belegt
- **Next Commands (snapshot)**:
  - `docker compose -p peaktrade-shadow-mvs -f docs&#47;webui&#47;observability&#47;DOCKER_COMPOSE_GRAFANA_ONLY.yml ps`
  - `lsof -nP -iTCP:3000 -sTCP:LISTEN || true`

#### G‑5: Datasource falsch (nicht default / falsche URL)
- **Symptom**: Verify meldet fehlende Datasource UID oder URL nicht `host.docker.internal:9092`
- **Symptom (Auth)**: Verify meldet `Grafana auth failed ... (HTTP 401)` → Credentials/DB-Drift (alte Volumes) oder falsches Login
- **Wahrscheinlichste Ursache**: falsches Datasource‑YAML gemountet (oder altes Provisioning im Container)
- **Next Commands (snapshot)**:
  - `curl -fsS -u "$GRAFANA_AUTH" http:&#47;&#47;127.0.0.1:3000&#47;api&#47;datasources | python3 -m json.tool | head -n 220`
  - `docker compose -p peaktrade-shadow-mvs -f docs&#47;webui&#47;observability&#47;DOCKER_COMPOSE_GRAFANA_ONLY.yml up -d --force-recreate --renew-anon-volumes --remove-orphans`
  - (Reset, deterministisch) `bash scripts&#47;obs&#47;shadow_mvs_local_down.sh && bash scripts&#47;obs&#47;shadow_mvs_local_up.sh`

#### G‑6: Dashboard fehlt (UID nicht sichtbar)
- **Symptom**: Grafana `&#47;api&#47;search?type=dash-db` enthält `peaktrade-shadow-pipeline-mvs` nicht
- **Wahrscheinlichste Ursache**: Dashboard provider path/mount mismatch oder JSON nicht gemountet
- **Next Commands (snapshot)**:
  - `curl -fsS -u "$GRAFANA_AUTH" -G http:&#47;&#47;127.0.0.1:3000&#47;api&#47;search --data-urlencode type=dash-db | python3 -m json.tool | head -n 120`
  - `docker compose -p peaktrade-shadow-mvs -f docs&#47;webui&#47;observability&#47;DOCKER_COMPOSE_PROMETHEUS_LOCAL.yml -f docs&#47;webui&#47;observability&#47;DOCKER_COMPOSE_GRAFANA_ONLY.yml exec grafana sh -lc 'ls -la &#47;etc&#47;grafana&#47;provisioning&#47;dashboards || true; echo; ls -la &#47;etc&#47;grafana&#47;dashboards || true'`

#### G‑7: Daten „empty“ obwohl Targets UP
- **Symptom**: `up{job="shadow_mvs"}` ist 1, aber Stage‑Query liefert leer
- **Wahrscheinlichste Ursache**: Exporter liefert nicht die erwarteten Serien / Zeitfenster zu kurz / falscher Mode‑Filter
- **Next Commands (snapshot)**:
  - `curl -fsS http:&#47;&#47;127.0.0.1:9109&#47;metrics | grep -n "^peak_trade_pipeline_events_total" | head -n 20`
  - `curl -fsS -G http:&#47;&#47;127.0.0.1:9092&#47;api&#47;v1&#47;query --data-urlencode 'query=count by (__name__) ({__name__=~"peak_trade_pipeline_.*"})' | python3 -m json.tool | head -n 120`

#### G‑8: „Mini‑Stack“ Verwechslung (Prometheus im Compose vs prom-local)
- **Symptom**: Grafana Datasource zeigt auf `http://prometheus:9090`, aber du nutzt `prometheus-local` auf `:9092` (oder umgekehrt)
- **Wahrscheinlichste Ursache**: falsche Compose‑Variante/Erwartung gemischt
- **Next Commands (snapshot)**:
  - Prüfe welche Compose‑Files laufen:  
    - `docker compose -p peaktrade-shadow-mvs -f docs&#47;webui&#47;observability&#47;DOCKER_COMPOSE_PROM_GRAFANA.yml ps`  
    - `docker compose -p peaktrade-shadow-mvs -f docs&#47;webui&#47;observability&#47;DOCKER_COMPOSE_PROMETHEUS_LOCAL.yml ps`
  - Nutze Known‑Good Pairing (Phase E) oder konsequent Mini‑Stack (siehe `docs&#47;webui&#47;observability&#47;DOCKER_COMPOSE_PROM_GRAFANA.yml`)

---

### Phase H — „Live‑Shape Bridge“ (nur Form/Mapping; Metrik‑Contract bleibt stabil)
**Ziel:** Shadow‑Metriken so formen/benennen, dass später Live‑Adapter/Exchange‑Feeds nur „Input“ austauschen — Observability bleibt gleich (watch‑only).

**Contract Shape (repo‑echte Serien aus dem Shadow‑MVS Exporter):**
- **Health**
  - `shadow_mvs_up{mode,exchange}`
- **Pipeline Events**
  - `peak_trade_pipeline_events_total{mode,stage,exchange}`
  - Stages (Set): `signal | intent | submit | ack | fill | cancel | risk_block | error`
- **Latency**
  - `peak_trade_pipeline_latency_seconds_bucket{mode,edge,exchange,le}`
  - `peak_trade_pipeline_latency_seconds_sum{mode,edge,exchange}`
  - `peak_trade_pipeline_latency_seconds_count{mode,edge,exchange}`
- **Risk**
  - `peak_trade_risk_blocks_total{mode,reason}`
- **Optional**
  - `peak_trade_feed_gaps_total{mode,feed}`
  - `peak_trade_run_state{mode,state}`

**Label‑Konventionen (Bridge‑fähig, cardinality‑safe):**
- **Stabil/low‑cardinality (ok in Metrics)**: `mode` (`shadow|live`), `stage`, `exchange` (später: venue), `edge`, `reason`, `feed`, `state`
- **High‑cardinality (NICHT als Prometheus‑Label)**: `run_id`, `intent_id`, `client_order_id`, `broker_order_id` → gehört in Ledger/Logs/Traces

**Later Swap‑In Points (ohne Live‑Trading im Runbook):**
- Austauschbar: **Exporter/Adapter** (Shadow Demo Exporter ↔ Live Exchange Adapter)  
- Konstant: **Prometheus job + Grafana Dashboard Contract**
  - Job bleibt operatorisch „shadow_mvs“ (oder später zusätzlich „live_mvs“), Dashboard filtert über `mode`.

**Dashboard Layout Blueprint (Text‑Plan, Panels gruppiert):**
1) **Overview**
   - UP/Health (`shadow_mvs_up`)
   - Scrape/Contract‑Presence (absent‑Checks)
   - Pipeline Throughput nach `stage`
2) **Stage Values / Pipeline Health**
   - Stage‑Events Timeseries/Table (nach `stage`, `exchange`, `mode`)
   - Risk blocks nach `reason`
3) **Placeholders (Bridge‑ready, ggf. anfangs leer)**
   - Latency P95 (edge: `intent_to_ack`, später weitere edges)
   - Error‑Rate / Risk‑Block‑Rate
   - Slippage/Fill‑Quality (später live‑only Datenquelle; Panels bleiben)

**Failure Hook:** Wenn Label/Serie fehlt → Phase F (Smoke) und Phase G‑7.

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
- [ ] `&#47;metrics` zeigt `peak_trade_pipeline_events_total`
- [ ] Grafana Panel “Shadow Events” > 0
- [ ] Error rate Panel zeigt plausible Werte
- [ ] Ledger/Eventlog vorhanden (optional aber empfohlen)

### B‑Checklist (Ready for Live later)
- [ ] Event Schema gilt für shadow & live
- [ ] Adapter boundary klar (Kraken connector)
- [ ] client_order_id ist deterministisch & matchbar
- [ ] Reconciliation Plan existiert (Ledger↔Kraken)

### E‑Checklist (Persist & Provision)
- [ ] `docs&#47;webui&#47;observability&#47;grafana&#47;provisioning&#47;datasources&#47;datasources.prometheus-local.yaml` ist gemountet (Grafana-only Compose)
- [ ] Grafana Datasource default: `prometheus-local` (UID `peaktrade-prometheus-local`, URL `http://host.docker.internal:9092`)
- [ ] Dashboard provider aktiv: `grafana&#47;provisioning&#47;dashboards&#47;dashboards.yaml` (Path `&#47;etc&#47;grafana&#47;dashboards`)
- [ ] Dashboard UID `peaktrade-shadow-pipeline-mvs` ist sichtbar ohne UI‑Import

### F‑Checklist (Smoke / Snapshot)
- [ ] `bash scripts&#47;obs&#47;shadow_mvs_local_verify.sh` exit 0
- [ ] `up{job="shadow_mvs"}` liefert 1
- [ ] `sum by (mode, stage) (rate(peak_trade_pipeline_events_total{mode="shadow"}[5m]))` liefert non‑empty

### G‑Checklist (Triage Readiness)
- [ ] Decision Tree Knoten G‑1…G‑8 existieren und enthalten nur snapshot commands
- [ ] Jeder Smoke‑Fail ist mindestens einem Knoten zuordenbar (Exporter/Targets/Grafana/Datasource/Dashboard/Queries)

### H‑Checklist (Live‑Shape Bridge, nur Form)
- [ ] Metrik‑Familien und Label‑Konventionen sind dokumentiert (cardinality‑safe)
- [ ] Swap‑In Points sind klar (Adapter austauschbar, Dashboard contract stabil)
- [ ] Panel‑Gruppen Blueprint ist vorhanden (Overview / Stage / Placeholders)

---

## 9.1) Repo‑konforme Verification (CI/Gates, minimal)
> Ziel: PR‑sicher, keine Secrets, additive‑only, keine „watch loops“.

- [ ] Working tree sauber: `git status -sb`
- [ ] Quickstart smoke (lokal):  
  - `bash scripts&#47;obs&#47;shadow_mvs_local_up.sh`  
  - `bash scripts&#47;obs&#47;shadow_mvs_local_verify.sh`  
  - `bash scripts&#47;obs&#47;shadow_mvs_local_down.sh`
- [ ] Docs/Workflow Cross‑Check (nur lesen): `docs&#47;webui&#47;observability&#47;README.md` + `docs&#47;webui&#47;observability&#47;DASHBOARD_WORKFLOW.md`

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
Sobald `&#47;metrics` live ist: baue **Phase 5 Dashboard MVS**.
