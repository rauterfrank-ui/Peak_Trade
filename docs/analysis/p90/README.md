# P90 — supervisor metrics v1

Goal: Produce a deterministic JSON summary of supervisor health KPIs per `run_*` directory (ticks, freshness, latest P76 status) and emit alerts based on simple thresholds.

## Script

- `scripts/ops/p90_supervisor_metrics_v1.sh`

### Usage

```bash
OUT_DIR=out/ops/online_readiness_supervisor/run_YYYYMMDDThhmmssZ \
MIN_TICKS=2 MAX_AGE_SEC=900 \
bash scripts/ops/p90_supervisor_metrics_v1.sh
```

Or with `--out-dir`:

```bash
bash scripts/ops/p90_supervisor_metrics_v1.sh --out-dir out/ops/online_readiness_supervisor/run_YYYYMMDDThhmmssZ
```

### Output

JSON to stdout with: `tick_count`, `latest_tick`, `age_sec`, `latest_p76_status`, `alerts`.
