# Online Readiness — Supervisor Health Gate v1 (P79)

## Purpose
Validate that the P78 supervisor (or P77 daemon) is healthy: ticks are recent, pidfile is valid (if present), and P76 artifacts exist per tick.

## Prerequisites
- `OUT_DIR` contains `tick_*` subdirs (from P78 supervisor)
- Each tick dir should have at least one of: `P76_RESULT.txt`, `ONLINE_READINESS_ENV.json`, `P71_GATE.log`, `P72_PACK.log`, `readiness_report.json`, `manifest.json`

## Invocation
```bash
MODE=shadow OUT_DIR=/path/to/supervisor/out MAX_AGE_SEC=300 \
  bash scripts/ops/p79_supervisor_health_gate_v1.sh
```

## Exit Codes
- `0` — gate OK
- `2` — usage/config error (missing MODE, OUT_DIR, invalid mode)
- `3` — gate failed (stale ticks, stale pidfile, missing artifacts)

## Evidence
- `OUT_DIR/p79_health_gate_v1.json` — JSON with mode, newest_tick, age_sec, etc.
