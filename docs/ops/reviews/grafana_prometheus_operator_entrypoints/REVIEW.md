# GRAFANA / PROMETHEUS OPERATOR ENTRYPOINTS

## Purpose
Provide one compact docs-only operator entrypoint map for Grafana / Prometheus access.

## Scope
- exactly one PR
- docs only
- no runtime mutation
- no paper/shadow/testnet mutation

## Intended Content
- primary operator entrypoints
- likely local URLs / access points
- dashboard / UID discovery pointers
- Prometheus scrape / query entrypoints
- relationship to existing ops / cockpit documentation

## Desired Outcome
- one compact operator-facing map
- faster navigation to observability surfaces
- no behavioral changes


## Current operator entrypoints

### Valid operator-facing scripts
- `scripts/obs/ai_live_local_verify.sh`
- `scripts/obs/prom_9094_9095_restart.sh`
- `scripts/obs/prom_9094_9095_up_and_verify.sh`
- `scripts/obs/run_stage1_snapshot_docker.sh`
- `scripts/obs/run_stage1_trends_docker.sh`

### Relevant local ports
- Grafana: `3000`
- Prometheus local: `9092`
- Prometheus AI-live: `9094`
- Prometheus observability: `9095`

### Legacy / removed references
The following references appear in historical notes or merge logs but are not current operator entrypoints:
- `scripts/obs/grafana_local_up.sh`
- `docs/webui/observability/DOCKER_COMPOSE_GRAFANA_ONLY.yml`

Use the current scripts above instead of the legacy references.
