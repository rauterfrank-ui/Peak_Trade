# Peak_Trade – Komplette Docker-Übersicht

**Stand:** Februar 2026  
**Zweck:** Zentrale Dokumentation aller Docker-Komponenten, Befehle und Workflows.

---

## 1. Übersicht der Docker-Komponenten

| Komponente | Pfad | Zweck |
|------------|------|-------|
| **MLflow** | `docker/compose.yml` | Lokaler MLflow Tracking Server (Experiment-Tracking, Port 5001) |
| **Ops Runner** | `docker/docker-compose.obs.yml` | Stage1 Monitoring (Snapshots, Trends) in isoliertem Container |
| **L3 Image** | `docker/l3/Dockerfile` | AIOps Layer-3 Dry-Run (netzwerkfrei, read-only mount) |
| **Prometheus (Docker)** | `.local/prometheus/prometheus.docker.yml` | Scrape-Config für Web-Metriken via `host.docker.internal` |

---

## 2. MLflow (Experiment-Tracking)

### 2.1 Dateien
- `docker/compose.yml` – Compose-Konfiguration
- `docker/mlflow/Dockerfile` – MLflow 2.15.1 Image
- `docker/.env.example` – Template für `docker/.env`
- `docker/README.md` – Detaillierte Anleitung

### 2.2 Befehle

```bash
# Start
make mlflow-up
# oder: docker compose -f docker/compose.yml --env-file docker/.env up -d --build

# Stop (Daten bleiben erhalten)
make mlflow-down

# Logs
make mlflow-logs

# Vollständiger Reset (löscht alle Daten!)
make mlflow-reset

# Smoke-Test
make mlflow-smoke
```

### 2.3 Konfiguration
- **Port:** 5001 (Standard), änderbar in `docker/.env` via `MLFLOW_PORT`
- **UI:** http://localhost:5001
- **Volumes:** `peak_trade_mlflow` (Experiments + Artifacts)

### 2.4 Hinweise
- Port 5000 oft von macOS AirPlay belegt → 5001 nutzen
- `docker/.env` aus `.env.example` erstellen: `cp docker/.env.example docker/.env`

---

## 3. Ops Runner (Stage1 Monitoring)

### 3.1 Dateien
- `docker/docker-compose.obs.yml` – Compose für Ops-Container
- `docker/obs/Dockerfile` – Python 3.11-slim, uv, frozen deps
- `docker/obs/entrypoint.sh` – Command-Dispatcher

### 3.2 Befehle

```bash
# Build
docker compose -f docker/docker-compose.obs.yml build

# Daily Snapshot
docker compose -f docker/docker-compose.obs.yml run --rm peaktrade-ops stage1-snapshot

# Weekly Trends (z.B. 21 Tage)
docker compose -f docker/docker-compose.obs.yml run --rm peaktrade-ops stage1-trends --days 21

# Help
docker compose -f docker/docker-compose.obs.yml run --rm peaktrade-ops --help
```

### 3.3 Convenience-Scripts
- `./scripts/obs/run_stage1_snapshot_docker.sh` – Baut Image, führt Snapshot aus
- `./scripts/obs/run_stage1_trends_docker.sh` – Baut Image, führt Trends aus

### 3.4 Umgebung
- `PEAK_REPORTS_DIR` – Reports-Verzeichnis (Default: `/reports`, Volume-Mount)
- Volume: `./reports:/reports`

### 3.5 Ausgabe
- `reports/obs/stage1/2025-12-20_snapshot.md`
- `reports/obs/stage1/2025-12-20_summary.json`
- `reports/obs/stage1/stage1_trend.json`

---

## 4. L3 Docker (AIOps Layer-3)

### 4.1 Dateien
- `docker/l3/Dockerfile` – Minimales Python-Image
- `scripts/docker/run_l3_no_net.sh` – Wrapper für netzwerkfreien Lauf

### 4.2 Befehle

```bash
# Image bauen (manuell)
docker build -f docker/l3/Dockerfile -t peaktrade-l3:latest .

# L3 Dry-Run ausführen
make l3-docker
# oder: ./scripts/docker/run_l3_no_net.sh
```

### 4.3 Umgebung
- `--network=none` – Kein Netzwerk
- `-v REPO:/work:ro` – Repo read-only
- `-v OUT_DIR:/out:rw` – Ausgabe
- `-v CACHE_DIR:/cache:rw` – Cache
- `IMAGE` (Default: `peaktrade-l3:latest`)
- `KEEP_CONTAINER=1` – Container nicht mit `--rm` entfernen

---

## 5. .dockerignore

Ausschlüsse beim Docker-Build (u.a.):
- `.git`, `.venv`, `__pycache__`
- `reports/`, `artifacts/`, `data/`
- `.env`, `secrets.toml`

---

## 6. Prometheus (Docker-Kontext)

`.local/prometheus/prometheus.docker.yml`:
- Scrape-Target: `host.docker.internal:8000` (Web-Metriken)
- Für Prometheus-Container, die Host-Services scrapen

---

## 7. Makefile-Targets (Docker)

| Target | Beschreibung |
|-------|--------------|
| `make mlflow-up` | MLflow starten |
| `make mlflow-down` | MLflow stoppen |
| `make mlflow-logs` | MLflow-Logs folgen |
| `make mlflow-reset` | MLflow + Volumes löschen |
| `make mlflow-smoke` | Smoke-Test (loggt Run) |
| `make l3-docker` | L3 Dry-Run in Docker |

---

## 8. Downloads-Ordner (Docker-Bezug)

In `/Users/frnkhrz/Downloads/`:
- `RUNBOOK_GRAFANA_MODULAR_HTTPS_ZERO_TRUST_20260211.md` – Enthält Docker Compose Setup für selbst-gehostetes Grafana (HTTPS, Zero-Trust). **Hinweis:** Grafana/Dashboard-Komponenten wurden aus dem Repo entfernt; dieses Runbook ist eine externe Referenz.

---

## 9. Weitere Dokumentation

- `docs/ops/PHASE_16L_DOCKER_OPS_RUNNER.md` – Detaillierte Phase-16L-Implementierung
- `docs/ops/UEBERSICHT_DATEN_GATES_DOCKER_GITHUB.md` – Docker-Stacks, Prometheus-Targets, GitHub-Workflows
- `docs/ops/runbooks/RUNBOOK_DOCKER_STACK_FUTURES_CME_NQ_MNQ_OFFLINE.md` – Separater Docker-Stack für CME NQ/MNQ (Offline-First, NO-LIVE)

---

## 10. CI/CD-Integration (Beispiel)

```yaml
# GitHub Actions: Stage1 Snapshot
- name: Run Stage1 Snapshot
  run: |
    docker compose -f docker/docker-compose.obs.yml run --rm peaktrade-ops stage1-snapshot

- name: Upload Reports
  uses: actions/upload-artifact@v3
  with:
    name: stage1-reports
    path: reports/obs/stage1/
```

---

## 11. Troubleshooting

### Port belegt
```bash
lsof -i :5001   # MLflow
lsof -i :3000   # Grafana (falls verwendet)
```

### Docker nicht gefunden
- Docker Desktop installieren: https://docs.docker.com/desktop/install/mac-install/

### Volume-Permissions
- Docker läuft als root; Schreibzugriff auf Host-Volumes funktioniert standardmäßig


## Canonical recovery note
Siehe: `docs/ops/DOCKER_RECOVERY_CANONICAL_STATE.md`

Kanonische Docker-/Prometheus-Pfade:
- `docker/compose.yml`
- `docker/docker-compose.obs.yml`
- `.local/prometheus/prometheus.docker.yml`
- `scripts/docker/run_l3_no_net.sh`

Historische Verweise auf entfernte `docs/webui/observability/DOCKER_COMPOSE_*.yml` sind Legacy.
