# P80 — Supervisor Stop + Idempotent Start v1

## Goal
Extend the P78 online readiness supervisor with:
- **Stop mode**: `STOP=1` or `ACTION=stop` to gracefully terminate an existing supervisor
- **Idempotent start**: refuse double-start if pidfile points to a live process
- **Stale pidfile handling**: if pidfile exists but process is dead, remove and proceed

## Safety
- MODE remains paper|shadow only (live/record blocked).
- Stop sends SIGTERM first, SIGKILL after 30s if needed.

## Usage
```bash
# Stop existing supervisor
STOP=1 bash scripts/ops/online_readiness_supervisor_v1.sh
# or
ACTION=stop bash scripts/ops/online_readiness_supervisor_v1.sh

# Start (refuses if already running)
MODE=shadow OUT_DIR=out/ops/p78_supervisor bash scripts/ops/online_readiness_supervisor_v1.sh
```
