# P79 — Supervisor Health + Drift Guard v1

## Goal
Detect operational drift in the **paper/shadow** online readiness stack:
- stale pidfiles
- no tick outputs
- stale tick outputs
- missing tick artifacts (best-effort)
- **hard block** any accidental mode escalation to live/record

## Safety
- MODE is restricted to `paper|shadow` (anything else => fail).
- No model calls, no networking.
- Evidence is written only to `OUT_DIR`.

## Artifacts
- `scripts/ops/p79_supervisor_health_gate_v1.sh` (exit 0 OK, exit 3 gate failed)
- Evidence JSON: `OUT_DIR&#47;p79_health_gate_v1.json`

## Usage
```bash
MODE=shadow OUT_DIR=out/ops/p78_supervisor_demo MAX_AGE_SEC=300 \
  bash scripts/ops/p79_supervisor_health_gate_v1.sh
```
