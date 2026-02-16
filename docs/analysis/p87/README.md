# P87 — online-readiness-supervisor-plus-ingest-v1

Supervisor nutzt standardmäßig den P86-Gate (Readiness + Ingest) statt nur P76 (Go/No-Go).

## Änderungen

- **scripts/ops/online_readiness_supervisor_v1.sh**: `CHECK_MODE=p76|p86` (default: p86)
  - `p86`: Ruft `p86_gate_v1.sh` pro Tick (P85 Live Ingest + P76 Go/No-Go)
  - `p76`: Legacy-Verhalten, nur `online_readiness_go_no_go_v1.sh`
- **src/ops/p78/online_readiness_supervisor_plan_v1.py**: Feld `gate_variant` ("p76"|"p86", default "p86")
- **Tests**: Supervisor-Tick schreibt P86-Artefakte (P86_GATE_RESULT.json, p86_result.json) in tick_* Verzeichnisse

## Nutzung

```bash
# Default: P86 Gate pro Tick
SUPERVISOR_ENABLE=YES OUT_DIR=out/ops/p87_demo MODE=shadow bash scripts/ops/online_readiness_supervisor_v1.sh

# Legacy: nur P76
CHECK_MODE=p76 SUPERVISOR_ENABLE=YES OUT_DIR=out/ops/p87_legacy MODE=shadow bash scripts/ops/online_readiness_supervisor_v1.sh
```
