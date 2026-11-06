# Shadow MVS Local Verify PASS — Evidence Snapshot

- timestamp_utc: 20260118T034113Z
- mode: snapshot-only
- stack: peaktrade-shadow-mvs (grafana-only + prometheus-local + mock exporter)

## Command
```bash
bash scripts/obs/shadow_mvs_local_verify.sh
```

## Output
```text
==> Shadow MVS verify (snapshot-only; max 1 retry per endpoint)
==> Check: Prometheus ready
PASS|prometheus.ready|http://127.0.0.1:9092/-/ready
==> Check: Exporter /metrics reachable + contract series present
PASS|exporter.metrics|shadow_mvs_up + peak_trade_pipeline_events_total present
==> Check: Grafana health
PASS|grafana.health|http://127.0.0.1:3000/api/health
==> Check: Grafana datasource + dashboard provisioned
PASS|grafana.datasource|peaktrade-prometheus-local default url=http://host.docker.internal:9092
PASS|grafana.dashboard|dashboard_uid=peaktrade-shadow-pipeline-mvs
==> Check: Prometheus targets contains shadow_mvs=up
INFO|targets_retry=max_attempts=8|sleep_s=1
INFO|targets_retry=attempts_used=1
PASS|prometheus.targets|shadow_mvs=up
==> Check: Golden PromQL returns data (Snapshot)
PASS|prometheus.query|up{job="shadow_mvs"} non-empty
PASS|prometheus.query|pipeline events (rate, job=shadow_mvs) non-empty
PASS|prometheus.query|risk blocks (rate, job=shadow_mvs) non-empty
PASS|prometheus.query|latency p95 intent_to_ack (rate, job=shadow_mvs) non-empty

EVIDENCE|exporter=http://127.0.0.1:9109/metrics|series=shadow_mvs_up,peak_trade_pipeline_events_total
EVIDENCE|prometheus=http://127.0.0.1:9092|target=shadow_mvs:up
EVIDENCE|grafana=http://127.0.0.1:3000|ds_uid=peaktrade-prometheus-local
EVIDENCE|dashboard_uid=peaktrade-shadow-pipeline-mvs
RESULT=PASS
INFO|See Contract: docs/webui/observability/SHADOW_MVS_CONTRACT.md
```
