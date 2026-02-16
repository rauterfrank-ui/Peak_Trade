# Online Readiness Go/No-Go v1 (P76)

## Goal
One canonical operator command that produces:
- deterministic **READY / NOT_READY** result
- evidence in a single OUT_DIR
- stable exit codes for CI / automation

## Safety
- **paper/shadow only** via existing gates
- **live/record remain blocked** upstream (P61/P62/P71, etc.)

## Command
Preferred (override vars):
```bash
OUT_DIR_OVERRIDE="out/ops/online_readiness_run_$(date -u +%Y%m%dT%H%M%SZ)" \
RUN_ID_OVERRIDE="p76_demo" \
MODE_OVERRIDE="shadow" \
ITERATIONS_OVERRIDE="1" \
INTERVAL_OVERRIDE="0" \
bash scripts/ops/online_readiness_go_no_go_v1.sh
```

Legacy vars also work: `OUT_DIR`, `RUN_ID`, `MODE`, `ITERATIONS`, `INTERVAL`.

## Exit codes
- **0** — READY (P71 gate passed, P72 pack completed)
- **2** — USAGE/ENV error (OUT_DIR or RUN_ID missing)
- **3** — NOT_READY (P71 health gate failed)
- **4** — NOT_READY (P72 pack failed)

## Evidence layout
- `ONLINE_READINESS_ENV.json` — pinned env snapshot
- `P71_GATE.log`, `P72_PACK.log` — step logs
- `P76_RESULT.txt` — final READY/NOT_READY
- P71/P72 evidence (reports, manifest, etc.)
