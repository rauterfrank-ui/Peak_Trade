# Dashboard-Workflow (Grafana) — Peak_Trade Observability (Watch-Only)

Diese Doku beschreibt den **Workflow der Grafana-Dashboards** in Peak_Trade: von **Metriken in der Web-App** über **Prometheus-Scraping** bis hin zu **Grafana Datasources** und **file-provisioned Dashboards** (JSON).

## Ziele & Scope

- **Ziel**: Minimaler, reproduzierbarer Observability-Workflow für die Watch-Only Web-App (HTTP-Layer / Service Health).
- **Scope**: Lokale Development-Setups und Docker-Compose-Betrieb von Grafana/Prometheus.
- **Nicht im Scope**: Live-Trading/Execution (explizit ausgeschlossen).

## Überblick: Datenfluss (End-to-End)

1) **Peak_Trade Web-App** exponiert `GET &#47;metrics` (Prometheus-Format).
2) **Prometheus** scrapt `http://host.docker.internal:8000/metrics` (Docker → Host Networking auf macOS).
3) **Grafana** nutzt eine oder mehrere **Prometheus Datasources**:
   - **`prometheus-local`** (Default): `http://host.docker.internal:9092` (Host-Prometheus-local)
   - optional: `prometheus-main`: `http://host.docker.internal:9090`
   - optional (mini-stack): `prometheus`: `http://prometheus:9090` (Docker-intern)
4) **Grafana Dashboards** werden via **file provisioning** aus JSON-Dateien geladen und in einem Folder angezeigt.
5) Optional (für Shadow-MVS Demo/Contract): ein lokaler **Mock-Exporter** liefert `peak_trade_pipeline_*` Serien auf dem Host (default `:9109`).

## Wo liegt was? (Repo-Struktur)

### Grafana Dashboards (JSON)

- **Pfad**: `docs/webui/observability/grafana/dashboards/`
- Beispiele:
  - `peaktrade-labeled-local.json`
  - `peaktrade-overview.json`

### Dashboard Provisioning (Provider YAML)

- **Pfad**: `docs/webui/observability/grafana/provisioning/dashboards/dashboards.yaml`
- **Wichtig**: Der Provider zeigt auf **`/etc/grafana/dashboards`** (Container-Pfad).

### Datasource Provisioning (YAML)

- **Pfad**: `docs/webui/observability/grafana/provisioning/datasources/`
- Relevante Files:
  - `datasources.yaml` (mini-stack: `prometheus` via `http://prometheus:9090`)
  - `datasources.prometheus-local.yaml` (Default: `prometheus-local` via `http://host.docker.internal:9092`)
  - `datasources.prometheus-main.yaml` (optional: `prometheus-main` via `http://host.docker.internal:9090`)

## Betriebsmodi

### Modus A: Grafana-only (empfohlen, wenn `pt-prometheus-local` bereits läuft)

**Compose**: `docs/webui/observability/DOCKER_COMPOSE_GRAFANA_ONLY.yml`

- Wenn `pt-prometheus-local` noch nicht läuft:
  - Start (Compose): `docs/webui/observability/DOCKER_COMPOSE_PROMETHEUS_LOCAL.yml` (Host-Port `:9092`)
  - Oder One-shot (Compose + Verify): `bash scripts/obs/shadow_mvs_local_up.sh` + `bash scripts/obs/shadow_mvs_local_verify.sh`

- **Hardening Notes (Compose/Verify/Panels)**:
  - Compose‑Projekt fix: `-p peaktrade-shadow-mvs` (verhindert Orphans)
  - `up`: `... up -d --renew-anon-volumes --remove-orphans` (keine Grafana‑DB/Passwort‑Drift)
  - `down`: `... down -v --remove-orphans` (sauberer Reset)
  - Verify: Warmup‑Retries ohne Traceback‑Spam; Grafana‑Auth‑Fail → klare 401‑Meldung
  - Verify: Stage‑Query Window **`[5m]`** (weniger flappy)
  - Panels: Error‑Rate Nenner via `clamp_min(..., 1e-9)` (stabil bei low traffic)

- Start:

```bash
docker compose -p peaktrade-shadow-mvs -f docs/webui/observability/DOCKER_COMPOSE_GRAFANA_ONLY.yml up -d --force-recreate --renew-anon-volumes --remove-orphans
```

- Stop:

```bash
docker compose -p peaktrade-shadow-mvs -f docs/webui/observability/DOCKER_COMPOSE_GRAFANA_ONLY.yml down -v --remove-orphans
```

**Wichtiges Konzept**:
- Grafana läuft als UI „on-demand“.
- Prometheus kommt **nicht** aus diesem Compose, sondern ist bereits auf dem Host vorhanden (typisch Container `pt-prometheus-local` auf **`:9092`**).
 - Für das Shadow‑MVS Dashboard kann zusätzlich ein Host-Exporter laufen (via `bash scripts/obs/shadow_mvs_local_up.sh`), den Prometheus-local dann über `host.docker.internal:9109` scrapt.

### Modus B: Mini-Stack (Grafana + Prometheus im selben Compose)

**Compose**: `docs/webui/observability/DOCKER_COMPOSE_PROM_GRAFANA.yml`

- Start:

```bash
docker compose -f docs/webui/observability/DOCKER_COMPOSE_PROM_GRAFANA.yml up -d
```

- Stop:

```bash
docker compose -f docs/webui/observability/DOCKER_COMPOSE_PROM_GRAFANA.yml down
```

**Wichtiges Konzept**:
- Host-Port `9091` wird auf Container-Port `9090` gemappt (Konfliktvermeidung).
- Grafana muss Prometheus **docker-intern** über `http://prometheus:9090` erreichen (nicht über `:9091`).

## Dashboard-Workflow (Lifecycle)

### 1) Dashboard ändern / hinzufügen (JSON)

- Bearbeite oder füge eine Datei unter `docs/webui/observability/grafana/dashboards/` hinzu.
- Konvention:
  - sprechende Namen, z.B. `peaktrade-*.json`
  - UID stabil halten (wichtig für Links/Bookmarks)

### 2) Dashboard-Provider prüfen (Provisioning YAML)

In `docs/webui/observability/grafana/provisioning/dashboards/dashboards.yaml` muss der Provider auf den Container-Pfad zeigen, unter dem die JSONs gemountet sind:

- Provider `options.path`: **`/etc/grafana/dashboards`**

### 3) Compose-Mounts müssen zusammenpassen

Damit Grafana Dashboards automatisch findet, müssen diese 3 Dinge konsistent sein:

- **Dashboard-Provider YAML** ist im Container unter:
  - `/etc/grafana/provisioning/dashboards/dashboards.yaml`
- **Dashboard JSONs** sind im Container unter:
  - `/etc/grafana/dashboards/*.json`
- **Provider `options.path`** zeigt auf exakt denselben JSON-Pfad:
  - `/etc/grafana/dashboards`

Wenn eins davon nicht passt, bekommst du typischerweise:
- `api&#47;search?type=dash-db` → `[]` (keine Dashboards sichtbar)

### 4) Grafana neu laden

Für file-provisioned Dashboards ist der sichere Weg:

- Grafana (Container) neu erstellen:

```bash
docker compose -p peaktrade-shadow-mvs -f docs/webui/observability/DOCKER_COMPOSE_GRAFANA_ONLY.yml up -d --force-recreate --renew-anon-volumes --remove-orphans
```

## Verifikation (schnell & reproduzierbar)

### Grafana Health

```bash
curl -sS -u admin:admin http://127.0.0.1:3000/api/health
```

Erwartung: `"database": "ok"`.

### Dashboards sichtbar?

```bash
curl -sS -u admin:admin -G http://127.0.0.1:3000/api/search --data-urlencode type=dash-db | python3 -m json.tool | head -n 120
```

Erwartung: eine Liste mit z.B. `peaktrade-labeled-local` und `peaktrade-overview`.

### Default Datasource ist `prometheus-local`?

```bash
curl -sS -u admin:admin http://127.0.0.1:3000/api/datasources | python3 -m json.tool | head -n 220
```

Erwartung: Datasource `prometheus-local` mit `"isDefault": true` und URL `http://host.docker.internal:9092`.

### Grafana Variable Queries vs PromQL

Grafana-Variablen-Queries (Prometheus Datasource) nutzen oft Helper wie `label_values(...)` — das ist **kein** PromQL.
PromQL nutzt du typischerweise in Panels oder in Explore.

- Grafana Variable Query (Prometheus datasource):

```promql
label_values(http_requests_total{job="peak_trade_web"}, route)
```

- **PromQL Alternative**:

```promql
count by (route) (http_requests_total{job="peak_trade_web"})
sum(http_requests_total{job="peak_trade_web"})
```

- **Shadow Label Checks**:

```promql
# (Grafana) Variable Query
label_values(http_requests_total{job="peak_trade_web"}, mode)

# (PromQL) Panel/Explore
count by (mode) (http_requests_total{job="peak_trade_web"})
```

- **Shadow Metric Discovery**:

```promql
count by (__name__) ({__name__=~".*shadow.*", job="peak_trade_web"})
```

#### Shadow Data Readiness (aktueller Stand)

- Im Dashboard sehen wir aktuell baseline: nur `GET &#47;health` und `GET &#47;metrics` (Service/HTTP-Layer).
- Prüfe, ob Labels `mode`/`pipeline`/`traffic` existieren: per Grafana Variable Queries (`label_values(...)`) und per PromQL (`count by (...)`).
- Wenn die Queries leer sind: Shadow-Instrumentation ist noch nicht implementiert (oder es wird noch nicht gescrapt).

## Troubleshooting (häufige Fehlerbilder)

### Problem: Dashboard-Suche liefert `[]`

**Symptom**
- `curl ... &#47;api&#47;search?type=dash-db` → `[]`

**Root Causes (typisch)**
- Dashboard-Provider YAML nicht gemountet (Grafana sieht `dashboards.yaml` nicht).
- JSON-Verzeichnis falsch gemountet (liegt z.B. unter `/etc/grafana/provisioning/dashboards`, Provider erwartet aber `/etc/grafana/dashboards`).
- Provider `options.path` zeigt auf falschen Container-Pfad.

**Debug (Container)**

```bash
docker compose -p peaktrade-shadow-mvs -f docs/webui/observability/DOCKER_COMPOSE_PROMETHEUS_LOCAL.yml -f docs/webui/observability/DOCKER_COMPOSE_GRAFANA_ONLY.yml exec grafana sh -lc '
  ls -la /etc/grafana/provisioning/dashboards || true
  echo
  ls -la /etc/grafana/dashboards || true
'
```

Erwartung:
- `/etc/grafana/provisioning/dashboards/dashboards.yaml` existiert
- `/etc/grafana/dashboards/*.json` existiert

### Problem: Datasource „prometheus“ ist da, aber Queries schlagen fehl

**Typischer Fehler im mini-stack**
- Grafana-Datasource zeigt auf `http://prometheus:9091` (Host-Port) statt `http://prometheus:9090` (Container-Port).

**Fix**
- In `grafana&#47;provisioning&#47;datasources&#47;datasources.yaml` ist korrekt: `url: http:&#47;&#47;prometheus:9090`

### Problem: Prometheus scrapt nicht `:8000` (Targets down)

**Typisch auf macOS Docker Desktop**
- `localhost:8000` im Container zeigt auf den Container selbst, nicht den Host.

**Fix**
- Scrape-Target: `host.docker.internal:8000`

## Praktische Hinweise (Operator-Style)

- **Ports** (üblich):
  - Grafana: `:3000`
  - Prometheus (mini-stack Host-Port): `:9091`
  - Prometheus-local (Host): `:9092`
- **Login** (lokal, default): `admin &#47; admin`
- **Safety/Governance**: Observability ist Watch-Only; keine Trading-/Execution-Pfade.
