# Observability (Prometheus / Grafana) — Peak_Trade Watch-Only

Diese Assets sind **optional** und betreffen ausschließlich **Service Health / HTTP Layer** der Watch-Only Web-App.

## Quickstart (lokal, <10 Min): Shadow Pipeline MVS Dashboard (provisioned + verified)

Ziel: **Grafana-only UI** + **prometheus-local** (Host-Port `:9092`) + **automatisch provisioniertes** Dashboard
`Peak_Trade — Shadow Pipeline (MVS, Contract v1)` **ohne manuelles Grafana-Import/Klick-Orgie**.

> Hinweis: Der Shadow-MVS Quickstart startet zusätzlich einen kleinen **Mock-Exporter** (Host-Port `:9109`),
> lokal deterministisch Daten sehen (auch wenn du die Peak_Trade Web-App noch nicht laufen hast).

Start:

```bash
bash scripts/obs/shadow_mvs_local_up.sh
```

Verifikation (harte Checks: Targets UP, Datasource/Dashboard da, Kernqueries liefern Daten):

```bash
bash scripts/obs/shadow_mvs_local_verify.sh
```

Stop:

```bash
bash scripts/obs/shadow_mvs_local_down.sh
```

URLs:
- Grafana: http:&#47;&#47;127.0.0.1:3000 (admin/admin)
- Prometheus-local: http:&#47;&#47;127.0.0.1:9092
- Shadow-MVS Exporter: http:&#47;&#47;127.0.0.1:9109&#47;metrics

Relevante Compose-Files:
- docs/webui/observability/DOCKER_COMPOSE_GRAFANA_ONLY.yml
- docs/webui/observability/DOCKER_COMPOSE_PROMETHEUS_LOCAL.yml

## AI Live

## AI Live UX v2 (Dashboard)
This dashboard includes an expanded AI Live control + ops pack:
- Latency: p95/p99 (5m) from `peaktrade_ai_decision_latency_ms_bucket`
- Quality: parse errors and drops (5m) from `peaktrade_ai_events_parse_errors_total` and `peaktrade_ai_events_dropped_total`
- Freshness: worst-case event age (seconds) from `peaktrade_ai_last_event_timestamp_seconds` (and per run_id if enabled)
- Ops: active alert counts via Grafana `ALERTS` datasource query (no-data hardened)
 (Exporter + Dashboard Row)

Ziel: Eine kleine, **watch-only** AI-Event-Telemetrie, die in Grafana im Dashboard
„Execution Watch Overview“ als Row „AI Live“ sichtbar ist.

### AI Live

## AI Live UX v2 (Dashboard)
This dashboard includes an expanded AI Live control + ops pack:
- Latency: p95/p99 (5m) from `peaktrade_ai_decision_latency_ms_bucket`
- Quality: parse errors and drops (5m) from `peaktrade_ai_events_parse_errors_total` and `peaktrade_ai_events_dropped_total`
- Freshness: worst-case event age (seconds) from `peaktrade_ai_last_event_timestamp_seconds` (and per run_id if enabled)
- Ops: active alert counts via Grafana `ALERTS` datasource query (no-data hardened)
 Drilldown v1 (run_id)

 Ziel: **Maximale Operator-Visibility** für einen konkreten AI-Lauf über `run_id`, ohne `src&#47;**` anzufassen (watch-only).

- **Dashboard Variable**: `run_id` (Grafana Query Variable via `label_values(peaktrade_ai_decisions_total, run_id)`, Datasource **DS_LOCAL**)
- **Filter Contract**: Panels nutzen `run_id=~"$run_id"` (All → `.*`)
- **Freshness Drilldown**: Exporter emittiert zusätzlich (bounded):
  - `peaktrade_ai_last_event_timestamp_seconds_by_run_id{run_id,component,source}`

#### run_id Constraints (Cardinality Guardrail)

- **Max length**: 32 Zeichen (Exporter normalisiert/trunkiert)
- **Allowed chars**: `[A-Za-z0-9._-]` (alles andere wird zu `_`)
- **Empfehlung**: kurze, stabile IDs (z.B. `demo`, `mvs_20260124`, `shadow_smoke`)

### AI Live

## AI Live UX v2 (Dashboard)
This dashboard includes an expanded AI Live control + ops pack:
- Latency: p95/p99 (5m) from `peaktrade_ai_decision_latency_ms_bucket`
- Quality: parse errors and drops (5m) from `peaktrade_ai_events_parse_errors_total` and `peaktrade_ai_events_dropped_total`
- Freshness: worst-case event age (seconds) from `peaktrade_ai_last_event_timestamp_seconds` (and per run_id if enabled)
- Ops: active alert counts via Grafana `ALERTS` datasource query (no-data hardened)
 UX v2 — Reason/Action/SLO/Timeline

Ziel: Operator sieht pro Lauf (`run_id`) nicht nur „Up/Down“, sondern **warum** (Reasons), **was passiert** (Actions) und **wie gut** (SLO/Tail) – ohne Logs/Loki.

- **Reason breakdown**:
  - `Reject reasons (5m)` (Top-K, Timeseries, stacked)
  - `Noop reasons (5m)` (Top-K, Timeseries, stacked)
- **Action breakdown**:
  - `Actions (5m)` basiert auf `peaktrade_ai_actions_total{action,component,run_id}`
- **SLO/Tail**:
  - `Latency SLO > 500ms (5m) — breach %` nutzt das run-scoped Histogram `peaktrade_ai_decision_latency_seconds_*` (Threshold 0.5s)
  - `Latency breach % (>500ms) (5m)` als Timeseries
- **Timeline (lightweight)**:
  - `AI Activity State (per decision type, last 30m)` zeigt 0/1 Aktivität je Decision-Type (accept/reject/noop)

Hinweis (Label-Realität):
- `peaktrade_ai_events_*` (parse/drops) sind **source-scoped** (kein `run_id`); die Panels bleiben global.
- `peaktrade_ai_decision_latency_ms_*` ist **source+decision** (v2) und wird weiterhin als p95-Referenz genutzt; SLO ist run-scoped über `peaktrade_ai_decision_latency_seconds_*`.

### AI Live

## AI Live UX v2 (Dashboard)
This dashboard includes an expanded AI Live control + ops pack:
- Latency: p95/p99 (5m) from `peaktrade_ai_decision_latency_ms_bucket`
- Quality: parse errors and drops (5m) from `peaktrade_ai_events_parse_errors_total` and `peaktrade_ai_events_dropped_total`
- Freshness: worst-case event age (seconds) from `peaktrade_ai_last_event_timestamp_seconds` (and per run_id if enabled)
- Ops: active alert counts via Grafana `ALERTS` datasource query (no-data hardened)
 Port Contract v1 (lokal, deterministisch)

- **Port**: Der AI Live Exporter läuft lokal **immer auf `:9110`**.
- **Warum**: `prometheus-local` scrapt den Job **`ai_live`** fest auf `host.docker.internal:9110`.
- **Wichtig**: Die Smoke-/Verify-Skripte **fallen nicht** auf andere Ports zurück. Ein stiller Fallback würde zu
  „leeren“ Prometheus/Grafana Panels führen, obwohl der Exporter läuft.

Wenn `:9110` belegt ist:

```bash
lsof -nP -iTCP:9110 -sTCP:LISTEN
```

- Stoppe den Prozess, der `:9110` belegt (empfohlen) und starte dann den Exporter erneut.
- Nicht empfohlen: Exporter auf anderem Port laufen lassen **und** Prometheus-Scrape-Config explizit anpassen.

### Start (Exporter lokal)

**Python Env Contract (deterministisch):**
- Der AI Live Exporter benötigt `prometheus_client`.
- Die Ops-Skripte (`ai_live_smoke_test.sh`, `ai_live_verify.sh`, `ai_live_ops_verify.sh`) wählen standardmäßig:
  - `uv run python` (wenn `uv` verfügbar ist)
  - sonst `python3`
- Override (optional): `PY_CMD="uv run python"` oder `PY_CMD="python3"` (die Skripte loggen `PY_CMD=<...>`).

1) Events-Datei wählen (JSONL, append-only). Beispiel:

```bash
mkdir -p logs/ai
export PEAK_TRADE_AI_EVENTS_JSONL="logs/ai/ai_events.jsonl"
export PEAK_TRADE_AI_RUN_ID="demo"
export PEAK_TRADE_AI_COMPONENT="execution_watch"
export PEAK_TRADE_AI_EXPORTER_PORT="9110"
uv run python scripts&#47;obs&#47;ai_live_exporter.py
```

2) Beispiel-Events schreiben (separates Terminal):

```bash
uv run python scripts&#47;obs&#47;emit_ai_live_sample_events.py --out "logs/ai/ai_events.jsonl" --n 50 --interval-ms 200
```

### Prometheus (Scrape)

Wenn du den lokalen Observability-Stack nutzt, ist der Scrape-Target bereits in der
Prometheus-local Config enthalten (Host Target `host.docker.internal:9110`, Job `ai_live`).

### Unterstützte Event-Formate (Mapping → canonical metrics)

```text
v=1 JSONL (demo/emitter)  -> peaktrade_ai_* metrics
logs/execution/execution_events.jsonl (schema_version=BETA_EXEC_V1) -> peaktrade_ai_* metrics
logs/execution/execution_pipeline_events_v0.jsonl (schema=execution_event_v0) -> peaktrade_ai_* metrics
```

### Verify (Exporter + Prometheus)

```bash
chmod +x scripts/obs/ai_live_verify.sh
bash scripts/obs/ai_live_verify.sh
```

### Canonical Verify (Ops Pack v1, "one command" proof)

Der kanonische Snapshot-Only Proof ist:

```bash
chmod +x scripts/obs/ai_live_ops_verify.sh
bash scripts/obs/ai_live_ops_verify.sh
```

- **Evidence (file-backed):** schreibt ein OUT-Directory unter `.local_tmp/ai_live_ops_verify_<timestamp>` (oder `VERIFY_OUT_DIR`/`OUT_DIR` Override).
- **Summary:** `AI_LIVE_OPS_SUMMARY.txt`
- **Contract-TSV:** `PROM_REQUIRED_SERIES.tsv` (PromQL + result_count + scalar values)

### Smoke Test (Exporter + Emitter + Metrics Delta)

```bash
chmod +x scripts/obs/ai_live_smoke_test.sh
bash scripts/obs/ai_live_smoke_test.sh
```

### AI Live

## AI Live UX v2 (Dashboard)
This dashboard includes an expanded AI Live control + ops pack:
- Latency: p95/p99 (5m) from `peaktrade_ai_decision_latency_ms_bucket`
- Quality: parse errors and drops (5m) from `peaktrade_ai_events_parse_errors_total` and `peaktrade_ai_events_dropped_total`
- Freshness: worst-case event age (seconds) from `peaktrade_ai_last_event_timestamp_seconds` (and per run_id if enabled)
- Ops: active alert counts via Grafana `ALERTS` datasource query (no-data hardened)
 Ops Pack v1 (Alerts + Ops Summary)

Ziel: AI Live operabel machen (watch-only): **Alerts**, **SLO-Style Checks** und eine kompakte **Ops Summary** oben im
Dashboard `Peak_Trade — Execution Watch Overview`.

#### Grafana: „AI Live — Ops Summary“

- **AI Live Up**: `max(up{job="ai_live"})` (0/1)
- **AI Live Fresh (worst age s)**: Worst-case Event-Alter über alle `source`
- **Parse errors / 5m**: `increase(peaktrade_ai_events_parse_errors_total[5m])`
- **Drops / 5m**: `increase(peaktrade_ai_events_dropped_total[5m])`
- **Latency p95 (5m)**: `histogram_quantile(0.95, ...)`
- **Active alerts (firing)**: `count(ALERTS{alertstate="firing"})`

#### Prometheus Alerts (Regeln)

- Rules file:

```text
docs/webui/observability/prometheus/rules/ai_live_alerts_v1.yml
```

- Alert-Namen (stabil): `AI_LIVE_ExporterDown`, `AI_LIVE_StaleEvents`, `AI_LIVE_ParseErrorsSpike`, `AI_LIVE_DroppedEventsSpike`, `AI_LIVE_LatencyP95High`, `AI_LIVE_LatencyP99High`

### AI Live

## AI Live UX v2 (Dashboard)
This dashboard includes an expanded AI Live control + ops pack:
- Latency: p95/p99 (5m) from `peaktrade_ai_decision_latency_ms_bucket`
- Quality: parse errors and drops (5m) from `peaktrade_ai_events_parse_errors_total` and `peaktrade_ai_events_dropped_total`
- Freshness: worst-case event age (seconds) from `peaktrade_ai_last_event_timestamp_seconds` (and per run_id if enabled)
- Ops: active alert counts via Grafana `ALERTS` datasource query (no-data hardened)
 Ops Determinism v1 (no manual copy)

**Ziel:** Beim frischen Start des lokalen Observability-Stacks sind die AI Live Alert-Regeln **sofort geladen** (ohne manuelles Copy/Reload).

**Wie:** Das lokale Prometheus-Compose mountet die Rules aus dem Repo in einen festen Container-Pfad; die Prometheus-Config referenziert diese über `rule_files`.

```text
Compose: docs/webui/observability/DOCKER_COMPOSE_PROMETHEUS_LOCAL.yml
Host rules dir: docs/webui/observability/prometheus/rules
Container rules dir: &#47;etc&#47;prometheus&#47;rules
Prom config: docs/webui/observability/PROMETHEUS_LOCAL_SCRAPE.yml
rule_files:
  - &#47;etc&#47;prometheus&#47;rules&#47;*.yml
  - &#47;etc&#47;prometheus&#47;rules&#47;*.yaml
```

Start (fresh):

```bash
bash scripts/obs/grafana_local_down.sh
bash scripts/obs/grafana_local_up.sh
```

Verify (single-shot, ops-pack ready):

```bash
# Erwartung: targets ai_live UP, Ops Pack metrics contract PASS (run_id ready), file-backed evidence written
bash scripts/obs/ai_live_ops_verify.sh
```

#### Run-ID Variable (Quelle / Determinismus)

Grafana-Drilldowns nutzen `run_id` als Variable (typisch via `label_values(peaktrade_ai_decisions_total, run_id)`).

**Quelle:** `run_id` ist ein **Prometheus Label** auf den AI Live canonical metrics (z.B. `peaktrade_ai_decisions_total{...,run_id}`).
Der Exporter setzt `run_id` pro Event aus:
- Event-Feld `run_id` (falls vorhanden), sonst
- Default aus Env `PEAK_TRADE_AI_RUN_ID`

**Determinismus / Guardrail:** `run_id` wird kanonisiert (label-safe, bounded) und ist explizit als **low-cardinality** Operator-Drilldown gedacht.

#### Alert Meaning + Sofortmaßnahmen

- **AI_LIVE_ExporterDown**
  - Bedeutung: `up{job="ai_live"} == 0` → Exporter wird nicht gescrapt.
  - Sofort: Port Contract v1 prüfen (`:9110`), Exporter-Metrics direkt öffnen (`http://127.0.0.1:9110/metrics`), Port-Konflikt prüfen:

```bash
lsof -nP -iTCP:9110 -sTCP:LISTEN
```

- **AI_LIVE_StaleEvents**
  - Bedeutung: Event-Freshness pro `source` ist > 60s (über 2m).
  - Sofort: Event-Writer/Emitter läuft? JSONL-Pfad korrekt (`PEAK_TRADE_AI_EVENTS_JSONL`)? Werden Events noch appended?

- **AI_LIVE_ParseErrorsSpike**
  - Bedeutung: Parse-Errors treten auf (typisch: invalid JSON / Schema-Drift).
  - Sofort: Suche nach „bad lines“ im JSONL, reproduziere mit absichtlich kaputten Zeilen (z.B. Emitter/Hand-Append) und prüfe Drops/Reasons.

- **AI_LIVE_DroppedEventsSpike**
  - Bedeutung: Events werden verworfen; häufige Gründe: `bad_json`, `missing_fields`, `unknown_schema`.
  - Sofort: Breakdown in Grafana (Drops by reason) ansehen; bei `unknown_schema` ist das meist **Schema Drift**.

- **AI_LIVE_LatencyP95High** (optional **P99High**)
  - Bedeutung: Decision-Latenz (Histogram) ist über Threshold (p95 > 250ms / p99 > 500ms, 5m).
  - Sofort: Prüfe gleichzeitig Throughput (decisions/min) und Tail-Latency; bei low traffic kann p99 noisy sein → Thresholds nach Baseline tunen.

#### Prometheus API Quick Queries (robust, token-policy safe)

Nutze das repo-interne Helper-Script (Retries + Evidence), statt `curl | python json.load(sys.stdin)`:

```bash
PROM_BASE="http://127.0.0.1:9092"

bash scripts/obs/_prom_query_json.sh --base "$PROM_BASE" --query 'up{job="ai_live"}' --out /tmp/pt_ai_live_up.json --retries 3
bash scripts/obs/_prom_query_json.sh --base "$PROM_BASE" --query 'ALERTS{alertstate="firing"}' --out /tmp/pt_ai_live_alerts.json --retries 3
bash scripts/obs/_prom_query_json.sh --base "$PROM_BASE" --query 'max(clamp_min(time() - max by (source) (peaktrade_ai_last_event_timestamp_seconds), 0))' --out /tmp/pt_ai_live_age.json --retries 3
```

### Grafana Erwartung (Screenshot-Mental-Model)

Im Dashboard „Peak_Trade — Execution Watch Overview“ erscheint ganz oben:
- Row **„AI Live“** (Control Panel + Drilldown v1 via `run_id`)
- darunter Row **„AI Live — Ops Summary“** (Up/Freshness/Errors/Drops/Latency/Active Alerts)

## Quickstart (lokal): Grafana-only Provisioning Smoke (ohne Mock-Exporter)

Ziel: Nur Prometheus-local + Grafana-only starten und per Snapshot verifizieren, dass:
- Grafana health OK
- Datasources local/main/shadow provisioned
- Dashboards aus den Subfoldern provisioned (execution/overview/shadow/http)

Start:

```bash
bash scripts/obs/grafana_local_up.sh
```

Verify:

```bash
bash scripts/obs/grafana_local_verify.sh
```

## Operator Quick Path (3 Kommandos)

Ziel: Prometheus-local + Grafana starten, **operator-grade verify** laufen lassen, dann direkt in den Operator-Entry springen.

```bash
bash scripts/obs/grafana_local_up.sh
bash scripts/obs/grafana_verify_v2.sh
open "http://127.0.0.1:3000/d/peaktrade-operator-home"
```

Hinweis:
- Wenn `grafana_verify_v2.sh` bei **grafana.auth** scheitert, ist das typischerweise **Passwort-/Volume-Drift**. Fix (deterministisch): bash scripts&#47;obs&#47;grafana_local_down.sh und danach bash scripts&#47;obs&#47;grafana_local_up.sh (reset volumes).

## Grafana Verify v2 (operator-grade, evidenzfähig)

Script: `scripts&#47;obs&#47;grafana_verify_v2.sh`

- **Alternative (dashpack-only, hermetisch first)**: `scripts&#47;obs&#47;grafana_dashpack_local_verify_v2.sh`
  - Läuft **auch ohne** laufendes Grafana (JSON-only Integrity Checks), und macht API-Checks nur wenn Grafana erreichbar ist.

- **Checks** (high level):
  - Grafana erreichbar (`api&#47;health`)
  - Login ok (`api&#47;user`)
  - Alle Dashboards im Dashpack per UID abrufbar (`api&#47;dashboards&#47;uid&#47;<uid>`) + JSON valid
  - DS_* Invariants: **DS_LOCAL/DS_MAIN/DS_SHADOW** vorhanden, **hidden** (hide=2), Defaults stabil
  - Alle internen Links `&#47;d&#47;<uid>` resolvable (UID existiert)
  - Optional: Prometheus-local Smoke „execution_watch metric present“ (via `_prom_query_json.sh`)
- **Artifacts**: schreibt Evidence in `docs&#47;ops&#47;evidence&#47;assets&#47;EV_GRAFANA_VERIFY_V2_<timestamp>` (oder per `VERIFY_OUT_DIR`).

Env Overrides:
- `GRAFANA_URL` (default `http:&#47;&#47;127.0.0.1:3000`)
- `GRAFANA_AUTH` (default `admin:admin`)
- `PROM_URL` (default `http:&#47;&#47;127.0.0.1:9092`)
- `VERIFY_OUT_DIR` (optional)

## Triage (DOWN / No data / MISSING / Wrong DS Scope)

- **DOWN / No data**:
  - Prüfe Port-Konflikt: du schaust wirklich auf `:3000` (nicht „anderes Grafana“).
  - Prüfe Prometheus-local: `http:&#47;&#47;127.0.0.1:9092&#47;-&#47;ready`
- **MISSING (Contract Panels)**:
  - Nutze `Peak_Trade — Contract Details (Debug)` (`&#47;d&#47;peaktrade-contract-details`) für Presence/Counts je DS_SHADOW/DS_LOCAL/DS_MAIN.
  - Guardrail: Execution Watch Contract Presence ist auf **DS_LOCAL** gescoped (vermeidet false MISSING auf DS_SHADOW).
- **Wrong DS Scope**:
  - DS_* Variablen sind standardmäßig **hidden**; Debug erfolgt über die Drilldown-Dashboards (Contract Details / Execution Watch Details).

Stop:

```bash
bash scripts/obs/grafana_local_down.sh
```

## Troubleshooting (minimal, deterministisch)

- Wenn Dashboards **DOWN / No data / MISSING** zeigen, liegt es lokal fast immer an einem der drei Punkte:
  - **Prometheus-local läuft nicht** (Datasource `prometheus-local` zeigt auf `http:&#47;&#47;host.docker.internal:9092`).
  - **Exporter läuft nicht** (für Shadow-MVS: `http:&#47;&#47;127.0.0.1:9109&#47;metrics`).
  - **Falscher Stack/Port-Konflikt** (ein anderer Grafana-Container belegt `:3000`).

- Schnellster „Beweis“-Pfad (liefert deterministische Evidence-Zeilen):

```bash
# Startet Prometheus-local + Grafana + Mock-Exporter (shadow_mvs) und vermeidet Passwort-/Volume-Drift.
bash scripts/obs/shadow_mvs_local_up.sh

# Harte Checks: Targets UP, DS/Dashboard provisioned, Golden Queries liefern Daten
bash scripts/obs/shadow_mvs_local_verify.sh
```

- Minimaler Snapshot (wenn du nur schauen willst, was genau DOWN ist):

```bash
curl -fsS http://127.0.0.1:9092/-/ready
curl -fsS http://127.0.0.1:9092/api/v1/targets | python3 -m json.tool | head -n 120
curl -fsS http://127.0.0.1:9109/metrics | head -n 40
curl -fsS -u admin:admin http://127.0.0.1:3000/api/health
```

- Golden Smoke Pattern (Prometheus Query deterministisch: `--out` + Parse aus Datei):

```bash
PROM_BASE="http://127.0.0.1:9092"
QUERY='up{job="shadow_mvs"}'
OUT="/tmp/pt_prom_query.json"
ERR="/tmp/pt_prom_query.stderr"
rm -f "$OUT" "$ERR"

bash scripts/obs/_prom_query_json.sh --base "$PROM_BASE" --query "$QUERY" --out "$OUT" --retries 3 > /dev/null 2> "$ERR" || true
tail -n 40 "$ERR" || true
python3 -c 'import json; print(json.load(open("/tmp/pt_prom_query.json")).get("status"))'
```

- Wenn `grafana_local_up.sh` mit einer Docker-Daemon Meldung scheitert, starte Docker lokal und führe den Smoke erneut aus.
- Wenn `grafana_local_verify.sh` bei `prometheus.ready` scheitert, ist der Compose-Stack nicht gestartet oder Ports sind belegt.
- Wenn `grafana_local_verify.sh` bei `grafana.dashboards` scheitert, stimmt meist ein Mount oder die Provisioning-Config nicht.

Snapshot-Debug (keine Watch-Loops):

```bash
# Status
docker compose -p peaktrade-grafana-local -f docs/webui/observability/DOCKER_COMPOSE_PROMETHEUS_LOCAL.yml -f docs/webui/observability/DOCKER_COMPOSE_GRAFANA_ONLY.yml ps

# Grafana health
curl -fsS -u admin:admin http://127.0.0.1:3000/api/health

# Provisioning mounts (im Container)
docker compose -p peaktrade-grafana-local -f docs/webui/observability/DOCKER_COMPOSE_PROMETHEUS_LOCAL.yml -f docs/webui/observability/DOCKER_COMPOSE_GRAFANA_ONLY.yml exec grafana sh -lc 'ls -la /etc/grafana/provisioning/dashboards /etc/grafana/provisioning/datasources /etc/grafana/dashboards'
```

## Aktivierung (Peak_Trade Web-App)

- Env-Flag: `PEAK_TRADE_PROMETHEUS_ENABLED=1`
- Voraussetzung: `prometheus_client` ist im Python Environment verfügbar
- **Wichtig (tatsächliches Verhalten)**:
  - `&#47;metrics` ist **immer** erreichbar, aber:
    - Ohne `prometheus_client` liefert es im Default (fail-open) nur ein Fallback-Signal: `peak_trade_metrics_fallback 1` (HTTP 200).
    - Mit `REQUIRE_PROMETHEUS_CLIENT=1` wird es **strict** und liefert bei fehlendem `prometheus_client` HTTP **503** (Scrape soll rot werden, statt “grün fake”).
    - Peak_Trade HTTP-Metriken (z.B. `peak_trade_http_requests_total`) werden nur instrumentiert, wenn `PEAK_TRADE_PROMETHEUS_ENABLED=1` gesetzt ist **und** `prometheus_client` verfügbar ist.

## Quick Verify

- `curl http:&#47;&#47;127.0.0.1:8000&#47;metrics | head`
  - Erwartung (`prometheus_client` verfügbar, Flag **aus**): `python_*`, `process_*` (Default-Metriken), **keine** `peak_trade_http_*`
  - Erwartung (enabled + `prometheus_client`): `python_*`, `process_*`, plus `peak_trade_http_*`
  - Erwartung (kein `prometheus_client`, fail-open): `peak_trade_metrics_fallback 1`
  - Erwartung (strict): HTTP 503 + Text “prometheus_client required but unavailable”

## Step-by-step Log (Incident: `&#47;metrics` nur Fallback → echte Metriken)

**Status (jetzt grün):**
- Grafana Login: ✅
- Prometheus Data Source: ✅ (Prometheus API erfolgreich)
- Peak_Trade Live Dashboard liefert echte Prometheus-Metriken: ✅
  - `&#47;metrics`: `python_*`, `process_*`, `peak_trade_http_requests_total`
- Prometheus Targets: ✅ UP (auch im Observability-Stack)

**Root Cause:**
- Live-Web-App lief unter System-Python (`&#47;Library&#47;Developer&#47;CommandLineTools&#47;usr&#47;bin&#47;python3`)
- `prometheus_client` dort nicht vorhanden + `PEAK_TRADE_PROMETHEUS_ENABLED` nicht gesetzt
- Ergebnis: `&#47;metrics` lieferte nur `peak_trade_metrics_fallback 1`

**Fix (repo-lokal, governance-safe):**
- System-Python Server auf `:8000` beendet (SIGINT), Port freigemacht
- Live-Web-App repo-lokal gestartet (Beispiel):
  - `PEAK_TRADE_PROMETHEUS_ENABLED=1`
  - `REQUIRE_PROMETHEUS_CLIENT=1`
  - `.venv&#47;bin&#47;python scripts&#47;live_web_server.py --host 127.0.0.1 --port 8000`

**Docker/Prometheus Networking Fix (macOS Docker Desktop):**
- Scrape Target im Container: `localhost:8000` → **falsch** (zeigt auf den Container)
- Korrekt: `host.docker.internal:8000`

**Prometheus Reload/Restart Outcome:**
- `POST &#47;-&#47;reload`: **403 Forbidden** (wenn Prometheus ohne `--web.enable-lifecycle` läuft)
- Workaround: Prometheus Container neu starten, damit Config neu geladen wird

## Dateien

- Prometheus Scrape Example: docs/webui/observability/PROMETHEUS_SCRAPE_EXAMPLE.yml
- Docker Compose (lokal): docs/webui/observability/DOCKER_COMPOSE_PROM_GRAFANA.yml
- Grafana Dashboard JSON: docs/webui/observability/GRAFANA_DASHBOARD_PEAK_TRADE_WATCH_ONLY.json
- Grafana Dashboards (provisioned, foldered):
  - docs/webui/observability/grafana/dashboards/execution/peaktrade-execution-watch-overview.json
  - docs/webui/observability/grafana/dashboards/overview/peaktrade-overview.json
  - docs/webui/observability/grafana/dashboards/shadow/peaktrade-shadow-pipeline-mvs.json
  - docs/webui/observability/grafana/dashboards/http/peaktrade-labeled-local.json
- Hinweis: Grafana `label_values(...)` (Variable Queries) vs PromQL ist in `DASHBOARD_WORKFLOW.md` im Abschnitt „Grafana Variable Queries vs PromQL“ erklärt.

## Ports & Networking (wichtig)

- **Grafana UI (Host)**: http:&#47;&#47;localhost:3000
- **Prometheus UI (Host)**: http:&#47;&#47;localhost:9091
  - In `DOCKER_COMPOSE_PROM_GRAFANA.yml` ist Prometheus bewusst auf **Host-Port 9091** gemappt (`"9091:9090"`), um Konflikte mit anderen Prometheus-Instanzen auf `9090` zu vermeiden.
- **Grafana → Prometheus (Docker-intern)**:
  - Grafana muss Prometheus über **http:&#47;&#47;prometheus:9090** (Service-Name + Container-Port) erreichen.
  - Nicht http:&#47;&#47;prometheus:9091 (das ist nur der Host-Port und führt im Container zu connection refused).

## Operator Runbook

- docs/ops/runbooks/RUNBOOK_DASHBOARD_WATCH_ONLY_START_TO_FINISH.md

## Shadow → Live Observability Runbook (Grafana)

Dieses Repo enthält zusätzlich ein Runbook für den **symbiotischen Kern** (Shadow → später Live) mit klarer Trennung:
- Grafana = Aggregationen/Health
- Ledger/Logs = konkrete Events (audit/replay)
- WebUI/Watch-Only = Operator-Detailsicht (read-only)

Startpunkt:
- docs/webui/observability/RUNBOOK_Peak_Trade_Grafana_Shadow_to_Live_Cursor_Multi_Agent.md

Begleitende Specs/Contracts:
- docs/webui/DASHBOARD_GOVERNANCE_NO_LIVE.md
- docs/webui/DASHBOARD_DATA_CONTRACT_OBS_v1.md
- docs/webui/GRAFANA_DASHBOARD_SPEC_PEAK_TRADE_OBS_v1.md
