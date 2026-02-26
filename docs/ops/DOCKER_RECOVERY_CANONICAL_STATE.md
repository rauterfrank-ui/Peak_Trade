# Docker Recovery – Canonical State

## Ziel
Die aktuell gewollten Docker-Komponenten in Peak_Trade reproduzierbar betreiben und historische, gelöschte Observability-/Grafana-Pfade nicht mehr als Runtime-Quelle verwenden.

## Kanonische Runtime-Quellen

### MLflow
- Compose: `docker/compose.yml`
- Einstieg: `Makefile`
- Persistenz: Docker-Volumes

### Ops Runner / Stage1
- Compose: `docker/docker-compose.obs.yml`
- Entrypoints:
  - `scripts/obs/run_stage1_snapshot_docker.sh`
  - `scripts/obs/run_stage1_trends_docker.sh`

### Prometheus Local Scrape
- Config: `.local/prometheus/prometheus.docker.yml`

### L3 Docker
- Script: `scripts/docker/run_l3_no_net.sh`
- Image: `docker/l3/Dockerfile`
- Einstieg: `make l3-docker`

## Legacy / nicht mehr kanonisch
- `docs/webui/observability/DOCKER_COMPOSE_PROMETHEUS_LOCAL.yml`
- historische `DOCKER_COMPOSE_*.yml` im Grafana-/Dashboard-Kontext

## Recovery-Regel
Wenn alte Docs/Skripte/Testfälle auf entfernte `DOCKER_COMPOSE_*.yml` verweisen, müssen sie auf die aktuellen kanonischen Pfade umgestellt oder fail-fast bereinigt werden.

## Verify-Ziele
- `docker compose -f docker/compose.yml config`
- `docker compose -f docker/docker-compose.obs.yml config`
- `make mlflow-smoke`
- `bash scripts/obs/run_stage1_snapshot_docker.sh`
- `bash scripts/obs/run_stage1_trends_docker.sh`
- `make l3-docker`
