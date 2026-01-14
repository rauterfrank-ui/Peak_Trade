# Observability Stack Runbook (P2.3)

## What this is
A minimal local observability stack for Peak_Trade:
- **OpenTelemetry Collector** (OTLP ingest)
- **Tempo** (traces)
- **Loki** (logs)
- **Prometheus** (metrics)
- **Grafana** (UI)

## Quickstart

### Start
```bash
bash scripts/obs/up.sh
```

Access:
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090
- Tempo: http://localhost:3200
- Loki: http://localhost:3100
- OTLP gRPC: localhost:4317
- OTLP HTTP: http://localhost:4318

### Stop
```bash
bash scripts/obs/down.sh
```

### Send test span
```bash
# First ensure you have otel extras installed:
pip install -e '.[otel]'

# Then run smoke test:
bash scripts/obs/smoke.sh
```

This sends a single span to the collector, which forwards it to Tempo.
Open Grafana -> Explore -> Tempo and search for service: `peak_trade_smoke_sender`

## Architecture

```
Application (Python)
  |
  | OTLP gRPC/HTTP (localhost:4317 / localhost:4318)
  v
OpenTelemetry Collector
  |
  +---> Tempo (traces)
  +---> Loki (logs)
  +---> Prometheus (metrics via exporter)
        ^
        |
      Prometheus (scrapes collector:8889)
        |
        v
      Grafana (pre-configured datasources)
```

## Configuration Files

### Docker Compose
- `ops/observability/docker-compose.yml` - Main stack definition

### Service Configs
- `ops/observability/otel-collector-config.yaml` - Collector pipelines
- `ops/observability/tempo.yaml` - Tempo backend
- `ops/observability/prometheus.yml` - Prometheus scrape config
- `ops/observability/grafana/provisioning/datasources/datasources.yaml` - Auto-provisioned datasources

## Usage in Application Code

```python
from src.obs import init_otel, instrument_lake

# Initialize OpenTelemetry
init_otel(
    service_name="peak_trade_backtest",
    exporter="otlp",  # or "console" for stdout, "none" for no-op
    otlp_endpoint="http://localhost:4317"
)

# Instrument lake client (optional)
lake = LakeClient()
lake = instrument_lake(lake)

# Now all lake operations emit spans
lake.read(...)
```

## Viewing Traces in Grafana

1. Open http://localhost:3000
2. Login: admin/admin
3. Navigate to Explore (left sidebar)
4. Select "Tempo" datasource
5. Search by:
   - Service name: e.g., `peak_trade_smoke_sender`
   - Trace ID (if you have it)
   - Time range

## Troubleshooting

### Stack won't start
```bash
# Check Docker daemon is running
docker ps

# Clean up old containers
bash scripts/obs/down.sh
docker system prune -f

# Restart
bash scripts/obs/up.sh
```

### No traces in Tempo
```bash
# Verify collector is receiving spans
docker logs -f observability-otel-collector-1

# Send test span
bash scripts/obs/smoke.sh

# Check Tempo has received traces
curl http://localhost:3200/api/search?tags=service.name=peak_trade_smoke_sender
```

### Port conflicts
If ports 3000, 3100, 3200, 4317, 4318, 8889, or 9090 are already in use:
1. Stop conflicting services
2. Or modify port mappings in `ops/observability/docker-compose.yml`

## Non-Goals (P2.3)

- Production deployment (this is local dev only)
- Persistent storage (traces/logs/metrics are ephemeral)
- Authentication beyond basic Grafana login
- High availability or clustering
- Advanced trace sampling strategies

## Next Steps

For production observability:
- Use managed services (Grafana Cloud, Datadog, New Relic, etc.)
- Or deploy self-hosted stack with persistent storage
- Configure retention policies
- Set up alerting rules
- Implement distributed tracing across services

## Related

- P2.2: OpenTelemetry wiring (`src&#47;obs&#47;`)
- Evidence chain artifacts: `reports&#47;evidence&#47;`
- MLflow tracking: via `scripts&#47;runner&#47;backtest.py` with `--mlflow` (illustrative)
