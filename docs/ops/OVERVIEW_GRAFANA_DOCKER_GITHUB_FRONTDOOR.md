# Peak_Trade: Gesamtübersicht Grafana, Docker, GitHub & Frontdoor

**Zweck:** Eine zentrale Übersicht, wie das Grafana-Dashboard in Peak_Trade mit Docker, GitHub CI und der Dokumentations-Frontdoor zusammenspielt.

**Stand:** 2026-02-10

---

## 1. Kurzüberblick

| Komponente | Rolle |
|------------|--------|
| **Grafana** | Watch-only Observability-UI (Dashboards, Prometheus-Datasources), Port **3000** |
| **Docker** | Grafana + Prometheus + optionale Exporter als Container; Compose-Dateien im Repo |
| **GitHub** | CI erkennt Grafana/Docs-Änderungen (`docs_only`), reduziert Lauf (nur Fast-Lane); Dashboards versioniert in `docs/webui/observability/grafana/` |
| **Frontdoor** | Einstieg in die Doku: `docs/README.md` (Haupt-Frontdoor), `docs/WORKFLOW_FRONTDOOR.md` (Workflow/Runbooks); Ops-Hub `docs/ops/README.md` verlinkt Observability/Grafana-Kontext |

---

## 2. Grafana im Projekt

### 2.1 Speicherort im Repo

- **Dashboards (JSON):**  
  `docs/webui/observability/grafana/dashboards/`  
  - `overview/` — Operator Home, Unified, System Health, Contract Details, …  
  - `execution/` — Execution Watch Overview/Details  
  - `shadow/` — Shadow Pipeline MVS  
  - `compare/` — Main vs Shadow, Metrics Drift  
  - `http/` — HTTP/labeled local  

- **Provisioning:**  
  - **Datasources:** `docs/webui/observability/grafana/provisioning/datasources/`  
    - Aktiv: `multi_prom.yml` (Prometheus 9092/9093/9094/9095 via `host.docker.internal`)  
    - Legacy/disabled: `legacy_disabled/`  
  - **Dashboards:** `docs/webui/observability/grafana/provisioning/dashboards/dashboards.yaml`  
    - Provider „Peak_Trade“, Typ `file`, Pfad im Container: `/etc/grafana/dashboards`, Ordnerstruktur aus Dateien  

- **Default-Home-Dashboard:**  
  Im Compose per Umgebungsvariable gesetzt:  
  `GF_DASHBOARDS_DEFAULT_HOME_DASHBOARD_PATH: "/etc/grafana/dashboards/execution/peaktrade-execution-watch-overview.json"`

### 2.2 Datasources (Multi-Prometheus)

Aus `multi_prom.yml` werden u.a. bereitgestellt:

| Name | UID | Host-Port | Rolle |
|------|-----|-----------|--------|
| prom_local_9092 | prom_local_9092 | :9092 | Default, Prometheus-local |
| prom_shadow_9093 | prom_shadow_9093 | :9093 | Shadow |
| prom_ai_live_9094 | prom_ai_live_9094 | :9094 | AI Live |
| prom_observability_9095 | prom_observability_9095 | :9095 | Observability |

Alle URLs: `http://host.docker.internal:<port>` (Grafana im Container spricht Host-Prometheus an).

---

## 3. Docker-Integration

### 3.1 Relevante Compose-Dateien

| Datei | Verwendung |
|-------|------------|
| **Repo-Root** | |
| `DOCKER_COMPOSE_GRAFANA_ONLY.yml` | Nur Grafana (:3000), bindet `docs/webui/observability/grafana/` (provisioning + dashboards) |
| **Unter docs** | |
| `docs/webui/observability/DOCKER_COMPOSE_GRAFANA_ONLY.yml` | Grafana-only, relative Pfade zu `./grafana/...` (gleicher Inhalt wie Root-Variante, andere Basis) |
| `docs/webui/observability/DOCKER_COMPOSE_PROMETHEUS_LOCAL.yml` | Nur Prometheus-local (:9092), Scrape-Config + Rules |
| `docs/webui/observability/DOCKER_COMPOSE_PROM_GRAFANA.yml` | Stack: Shadow-MVS-Exporter + Prometheus + Grafana (Ports 9109, 9091, 3000) |

### 3.2 Typischer lokaler Start (Grafana + Prometheus-local)

- **Up (Prometheus-local + Grafana):**  
  `scripts/obs/grafana_local_up.sh`  
  - Nutzt:  
    - `docs/webui/observability/DOCKER_COMPOSE_PROMETHEUS_LOCAL.yml`  
    - `docs/webui/observability/DOCKER_COMPOSE_GRAFANA_ONLY.yml`  
  - Projektname: `peaktrade-grafana-local` (über `GRAFANA_LOCAL_COMPOSE_PROJECT` änderbar)  
  - Ports: Grafana **3000**, Prometheus **9092**

- **Down:**  
  `scripts/obs/grafana_local_down.sh` (falls vorhanden)

- **Verifikation:**  
  - Einfach: `scripts/obs/grafana_local_verify.sh`  
  - Operator-grade: `scripts/obs/grafana_verify_v2.sh` (Health, Auth, Datasources, Dashboards per API)

### 3.3 Shadow-MVS-Quickstart (mit Mock-Exporter)

- **Up:**  
  `scripts/obs/shadow_mvs_local_up.sh`  
- **Verify:**  
  `scripts/obs/shadow_mvs_local_verify.sh`  
- **Down:**  
  `scripts/obs/shadow_mvs_local_down.sh`  

Dokumentation: `docs/webui/observability/README.md` (Quickstart, URLs, Verhalten).

### 3.4 Weitere Docker-Bausteine

- **Ops-Runner:**  
  `docker/docker-compose.obs.yml` + `docker/obs/Dockerfile` — separater Ops-Container (z. B. Reports), kein Grafana.
- **Observability-Runbook:**  
  `docs/observability/Peak_Trade_Observability_Runbook_Grafana_Dashboard_Setup.md` — stabile Datenflüsse, Grafana-Betrieb ohne Compose-Änderungen.

---

## 4. GitHub-Integration

### 4.1 CI-Workflow (`.github/workflows/ci.yml`)

- **Change Detection (paths-filter):**  
  - **Code-Pfade** (→ volle Matrix): `src/**`, `tests/**`, `scripts/**`, `config/**`, `pyproject.toml`, `uv.lock`, `pytest.ini`, `Makefile`, …  
  - **Docs** (u.a.): `docs/**`, `**/grafana/dashboards/**`, `out/**`, `**/*.md`  
  - **Workflow:** `.github/workflows/**`  

- **Pragmatic Flow:**  
  - **docs_only = true**, wenn *nur* Docs/Grafana/out/md geändert → **keine** volle Python-Matrix, nur Fast-Lane + Smoke (+ PR Gate).  
  - **workflow_only = true**, wenn *nur* Workflows geändert → ebenfalls nur Fast-Lane (+ PR Gate).  
  - Ein **PR Gate** (ein Required Check) fasst die relevanten Jobs zusammen.

- **Konkrete Grafana-Relevanz:**  
  - Änderungen unter `docs/webui/observability/grafana/dashboards/**` zählen als Docs → `docs_only`-Pfad → schneller CI-Lauf ohne volle Test-Matrix.  
  - Referenz: `docs/ops/ci_pragmatic_flow_meta_gate.md`, `docs/ops/ci_pragmatic_flow_inventory.md`.

### 4.2 Weitere Workflows mit Docs/Observability-Bezug

- **docs_reference_targets_trend.yml** — prüft `docs/**`, Baseline in `docs/ops/`.  
- **docs-integrity-snapshot.yml** — wird bei Änderungen in `docs/**` getriggert.  
- **merge_logs / merge_log_hygiene** — Merge-Logs unter `docs/ops/merge_logs/`, inkl. Grafana/DS-Fixes (z. B. PR #999).  
- **mcp_smoke_preflight** — kann Runbooks wie `docs/ops/runbooks/RUNBOOK_MCP_TOOLING.md` (Playwright/Grafana MCP) referenzieren.

### 4.3 Tests im Repo

- **Grafana-Provisioning / Dashpack:**  
  - `tests/obs/test_grafana_provisioning_sanity.py`  
  - `tests/obs/test_grafana_dashpack_integrity_v1.py`  
  - Verweisen auf `docs/webui/observability/grafana/dashboards`.  
- **Shadow MVS / Grafana-Health:**  
  - `tests/obs/test_shadow_mvs_verify_retries.py` (Grafana Health, API).  
- **AI Live Ops:**  
  - `tests/obs/test_ai_live_ops_determinism_v1.py` (minimal Fake Prometheus + Grafana).

---

## 5. Frontdoor & Dokumentation

### 5.1 Was ist die „Frontdoor“?

Die **Frontdoor** ist der **zentrale Einstieg** in die Peak_Trade-Dokumentation:

- **Haupt-Frontdoor:**  
  **`docs/README.md`** — „Peak_Trade Documentation – Frontdoor“  
  - Start Here, By Audience (Research, Developer, Ops, Governance), Quick Start, Subdirectory Indexes.  
  - Verlinkt u.a. **Ops-Hub** `docs/ops/README.md`, **Monitoring** (z. B. `OBSERVABILITY_AND_MONITORING_PLAN.md`), Runbooks, Governance.

- **Workflow-Frontdoor:**  
  **`docs/WORKFLOW_FRONTDOOR.md`**  
  - Navigation zwischen autoritativer Operations-Referenz (2026) und historischem Workflow-Kontext.  
  - Verweist auf Runbook-Übersichten, Installation, Live Operational Runbooks.

- **Ops-Hub (Operator-Frontdoor):**  
  **`docs/ops/README.md`**  
  - Operator-Zentrum: Runbooks, Merge-Logs, Gates, Evidenz, CI-Policy.  
  - Enthält Verweise auf Grafana/Observability (z. B. PR #994 MCP/Playwright/Grafana, PR #964 AI Live Ops/Grafana, PR #999 DS_LOCAL Fix).

### 5.2 Einbindung von Grafana/Observability in die Frontdoor

- **Direkt:**  
  - Observability-Quickstart und Grafana-Betrieb stehen in **`docs/webui/observability/README.md`**.  
  - Von der Haupt-Frontdoor aus erreichbar über **Monitoring & Alerts** (z. B. `OBSERVABILITY_AND_MONITORING_PLAN.md`) und über den **Ops-Hub** (`docs/ops/README.md`), der Merge-Logs und Runbooks zu Grafana/Observability verlinkt.

- **Indirekt:**  
  - Runbooks unter `docs/ops/runbooks/` (z. B. MCP Tooling mit Grafana, Docker-Stack, Cursor Multi-Agent) und `docs/observability/Peak_Trade_Observability_Runbook_Grafana_Dashboard_Setup.md` sind Teil der ops-orientierten Navigation und über die Frontdoor-Struktur auffindbar.

### 5.3 Wichtige Docs-Pfade (Überblick)

| Pfad | Inhalt |
|------|--------|
| `docs/README.md` | Haupt-Frontdoor |
| `docs/WORKFLOW_FRONTDOOR.md` | Workflow-/Runbook-Navigation |
| `docs/ops/README.md` | Ops-Hub, inkl. Grafana/Observability-Kontext |
| `docs/webui/observability/README.md` | Grafana/Prometheus Quickstart, AI Live, Verify |
| `docs/webui/observability/grafana/` | Dashboards + Provisioning |
| `docs/observability/Peak_Trade_Observability_Runbook_*.md` | Runbook Grafana/Datenflüsse |
| `docs/ops/ci_pragmatic_flow_*.md` | CI-Logik (docs_only, PR Gate) |

---

## 6. Datenfluss (Grafana ↔ Prometheus)

- **Prometheus** (lokal typisch :9092) scrapt Targets z. B. über `host.docker.internal` (Exporter auf Host: z. B. :9109 Shadow-MVS, :9110 AI Live).  
- **Grafana** (Container :3000) liest über provisionierte Datasources (`multi_prom.yml`) von `http://host.docker.internal:9092` (und ggf. 9093/9094/9095).  
- **Dashboards** liegen als JSON im Repo und werden beim Start per File-Provisioning in den Container gemountet; kein manueller Import nötig.

---

## 7. Quick Reference

### URLs (lokal nach Start)

- Grafana: **http://127.0.0.1:3000** (Login: `.env` oder `GRAFANA_AUTH=user:pass`, siehe Runbook Grafana Auth Security)  
- Prometheus-local: **http://127.0.0.1:9092**  
- Shadow-MVS Exporter (wenn gestartet): **http://127.0.0.1:9109/metrics**

### Wichtige Befehle

```bash
# Grafana + Prometheus-local starten
bash scripts/obs/grafana_local_up.sh

# Verifizierung (einfach / operator-grade)
./scripts/obs/grafana_local_verify.sh
./scripts/obs/grafana_verify_v2.sh

# Shadow-MVS Stack (mit Mock-Exporter)
bash scripts/obs/shadow_mvs_local_up.sh
bash scripts/obs/shadow_mvs_local_verify.sh
bash scripts/obs/shadow_mvs_local_down.sh
```

### Wo was ändern?

- **Dashboard-JSON:** `docs/webui/observability/grafana/dashboards/` → wird von CI als Docs-Änderung erkannt (`docs_only`).  
- **Datasources:** `docs/webui/observability/grafana/provisioning/datasources/` (z. B. `multi_prom.yml`).  
- **Dashboard-Provider:** `docs/webui/observability/grafana/provisioning/dashboards/dashboards.yaml`.  
- **Compose (Grafana/Prom):** Root `DOCKER_COMPOSE_GRAFANA_ONLY.yml` bzw. `docs/webui/observability/*.yml`.

---

**Siehe auch:**  
- [Observability README](../webui/observability/README.md)  
- [CI Pragmatic Flow (PR Gate)](ci_pragmatic_flow_meta_gate.md)  
- [Ops README](README.md)  
- [Documentation Frontdoor](../README.md)
