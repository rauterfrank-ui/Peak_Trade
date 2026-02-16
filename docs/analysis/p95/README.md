# P95 — Ops Health Meta Gate v1

Single-command health gate for the **shadow readiness ops loop** on macOS launchd:

- Supervisor present
- P93 status dashboard present
- P94 retention present
- Latest P93 pinned snapshot exists and is valid
- P79 gate OK and not stale (`MAX_AGE_SEC`)
- P90 metrics OK (no alerts, latest_p76_status = ready)

## Run

```bash
MAX_AGE_SEC=900 bash scripts&#47;ops&#47;p95_ops_health_meta_gate_v1.sh
```
