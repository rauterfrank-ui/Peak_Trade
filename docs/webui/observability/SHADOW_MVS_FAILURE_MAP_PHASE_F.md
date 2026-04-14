# Shadow MVS Failure Map — Phase F (snapshot-only)
**Scope:** Shadow MVS local backbone (Mock Exporter → Prometheus-local → Grafana-only)  
**Mode:** Snapshot-only (kein Watch), governance-safe, **NO-LIVE**

> Referenz (SSOT Contract): `docs&#47;webui&#47;observability&#47;SHADOW_MVS_CONTRACT.md`

## Failure Map (Symptom → Check → Root Cause → Fix → Evidence)

| Symptom | Quick Check (Snapshot) | Root Cause (typisch) | Fix (Snapshot-only) | Evidence line expected |
|---|---|---|---|---|
| `up{job="shadow_mvs"} == 0` | `curl -fsS http:&#47;&#47;127.0.0.1:9092&#47;api&#47;v1&#47;query --data-urlencode 'query=up{job="shadow_mvs"}'` | Exporter down, falscher Target (`localhost` statt `host.docker.internal`), Port-Kollision 9109 | `bash scripts&#47;obs&#47;shadow_mvs_local_down.sh && bash scripts&#47;obs&#47;shadow_mvs_local_up.sh` + Scrape Target prüfen | `EVIDENCE&#124;prometheus=http:&#47;&#47;127.0.0.1:9092&#124;target=shadow_mvs:up` |
| `scrape_samples_scraped{job="shadow_mvs"} == 0` | `curl -fsS http:&#47;&#47;127.0.0.1:9092&#47;api&#47;v1&#47;query --data-urlencode 'query=scrape_samples_scraped{job="shadow_mvs"}'` | Prometheus scrapt zwar Target, aber Response leer/invalid; Exporter liefert leere Body | Exporter Logs prüfen (falls vorhanden) + Exporter neu starten via `..._up.sh` | `PASS&#124;exporter.metrics&#124;shadow_mvs_up + peak_trade_pipeline_events_total present` |
| Keine Series `shadow_mvs_up` | `curl -fsS http:&#47;&#47;127.0.0.1:9109&#47;metrics | head -n 60` | Falscher Exporter/Port, falscher Endpoint, Exporter nicht gestartet | `bash scripts&#47;obs&#47;shadow_mvs_local_up.sh` + Port 9109 freimachen | `EVIDENCE&#124;exporter=http:&#47;&#47;127.0.0.1:9109&#47;metrics&#124;series=shadow_mvs_up,peak_trade_pipeline_events_total` |
| Grafana DS mismatch (UID) | `curl -fsS -u "$GRAFANA_AUTH" http:&#47;&#47;127.0.0.1:3000&#47;api&#47;datasources | python3 -m json.tool | head -n 200` | Provisioning YAML nicht gemountet / alte Volumes / falscher UID | Deterministischer Reset: `bash scripts&#47;obs&#47;shadow_mvs_local_down.sh && bash scripts&#47;obs&#47;shadow_mvs_local_up.sh` | `EVIDENCE&#124;grafana=http:&#47;&#47;127.0.0.1:3000&#124;ds_uid=peaktrade-prometheus-local` |
| Dashboard UID mismatch / nicht provisioniert | `curl -fsS -u "$GRAFANA_AUTH" -G http:&#47;&#47;127.0.0.1:3000&#47;api&#47;search --data-urlencode type=dash-db | python3 -m json.tool | head -n 200` | Dashboard JSON nicht gemountet oder UID falsch | Grafana-only Compose Mounts prüfen + `..._down.sh`/`..._up.sh` (volumes reset) | `EVIDENCE&#124;dashboard_uid=peaktrade-shadow-pipeline-mvs` |
| Port-Kollision `:9109` | `lsof -nP -iTCP:9109 -sTCP:LISTEN || true` | Ein anderer Prozess bindet 9109 | Störprozess stoppen (Operator) oder Port wechseln (nur wenn Contract geändert wird) | Verify FAIL zeigt Exporter unreachable; danach PASS Evidence |
| Port-Kollision `:9092` | `lsof -nP -iTCP:9092 -sTCP:LISTEN || true` | Andere Prometheus-Instanz oder Service auf 9092 | Störprozess stoppen oder Compose/Mapping korrigieren (Contract bleibt 9092) | `PASS&#124;prometheus.ready&#124;http:&#47;&#47;127.0.0.1:9092&#47;-&#47;ready` |
| Port-Kollision `:3000` | `lsof -nP -iTCP:3000 -sTCP:LISTEN || true` | Andere Grafana/Service auf 3000 | Störprozess stoppen oder Port freimachen (Contract bleibt 3000) | `PASS&#124;grafana.health&#124;http:&#47;&#47;127.0.0.1:3000&#47;api&#47;health` |

## F-0X — Prometheus Targets API kurz leer nach `up`
**Symptom (Snapshot):**
- Direkt nach `bash scripts&#47;obs&#47;shadow_mvs_local_up.sh` ist `http:&#47;&#47;127.0.0.1:9092&#47;api&#47;v1&#47;targets` kurz **leer** (keine `activeTargets`), obwohl Prometheus bereits “ready” wirkt.

**Quick Check (Snapshot):**
- `curl -fsS http:&#47;&#47;127.0.0.1:9092&#47;api&#47;v1&#47;targets | jq -r ".data.activeTargets|length"`

**Likely Root Cause:**
- Prometheus ist gestartet, aber **Target Discovery/Refresh** hat noch nicht befüllt (kurzes Race nach `up`).

**Minimal Fix (repo-safe):**
- `scripts&#47;obs&#47;shadow_mvs_local_verify.sh`: **bounded retries** (kein watch) für den Targets-Check, bis `activeTargets` vorhanden sind oder Timeout erreicht ist.

**Expected Evidence:**
- `INFO|targets_retry=...` (falls implementiert)
- `EVIDENCE|prometheus=http:&#47;&#47;127.0.0.1:9092|target=shadow_mvs:up`

## F-0Y — Grafana health kurz nicht ready nach `up`
**Symptom (Snapshot):**
- Direkt nach `up` ist `http:&#47;&#47;127.0.0.1:3000&#47;api&#47;health` kurz nicht erreichbar/OK.

**Quick Check (Snapshot):**
- `curl -fsS http:&#47;&#47;127.0.0.1:3000&#47;api&#47;health || true`

**Likely Root Cause:**
- Grafana Container läuft, aber HTTP Server/DB-Migration/Provisioning ist noch nicht ready (kurzes Warmup).

**Minimal Fix (repo-safe):**
- `scripts&#47;obs&#47;shadow_mvs_local_verify.sh`: **bounded retries** für den Health-Check (snapshot-only).

**Expected Evidence:**
- Später: `EVIDENCE|grafana=http:&#47;&#47;127.0.0.1:3000|ds_uid=peaktrade-prometheus-local`

## F-0Z — Golden Query `rate()`/`histogram_quantile()` leer/NaN direkt nach `up`
**Symptom (Snapshot):**
- `up{job="shadow_mvs"}` ist non-empty, aber rate-basierte Golden Queries liefern kurz **empty** oder `NaN`.

**Quick Check (Snapshot):**
- `curl -fsS http:&#47;&#47;127.0.0.1:9092&#47;api&#47;v1&#47;query --data-urlencode 'query=sum by (mode, stage) (rate(peak_trade_pipeline_events_total{job="shadow_mvs"}[5m]))'`
- `curl -fsS http:&#47;&#47;127.0.0.1:9092&#47;api&#47;v1&#47;query --data-urlencode 'query=histogram_quantile(0.95, sum by (le) (rate(peak_trade_pipeline_latency_seconds_bucket{job="shadow_mvs",edge="intent_to_ack"}[5m])))'`

**Likely Root Cause:**
- Scrape/TSDB Window-Warmup: `rate(...[5m])` braucht eine minimale Historie; erste Samples sind noch nicht im Window.

**Minimal Fix (repo-safe):**
- `scripts&#47;obs&#47;shadow_mvs_local_verify.sh`: **bounded warmup retries** für Golden Queries; `NaN` wird als “not ready” behandelt (snapshot-only).

**Expected Evidence:**
- `RESULT=PASS` + Golden Query PASS-Lines im Verify Output

## Canonical TRIAGE entry (Phase F)
Wenn du „irgendwas FAIL“ siehst:
- Run the single source check: `bash scripts&#47;obs&#47;shadow_mvs_local_verify.sh`
- Mappe das erste rote Symptom auf die passende Zeile oben.
