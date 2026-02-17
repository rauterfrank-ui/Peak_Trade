# P115 — Execution Session Runner v1 (mocks-only)

## Goal
Create a deterministic, reproducible execution-session evidence pack for the adapter+router stack (mock providers only).

## Safety / Guardrails
- mode: shadow|paper only
- dry_run: must be true (mocks-only)
- deny env vars (LIVE/TRADING/ARMED/etc.)
- secret env vars must not be set

## Run (example)
```bash
python3 -c "from src.execution.session.runner_v1 import ExecutionSessionContextV1, run_execution_session_v1; print(run_execution_session_v1(ExecutionSessionContextV1(mode='shadow', dry_run=True)))"
```

## Outputs
- out&#47;ops&#47;execution_sessions&#47;run_<TS>&#47; (report.json, manifest.json, SHA256SUMS.txt)
- bundle: out&#47;ops&#47;execution_sessions&#47;run_<TS>.bundle.tgz (+ .sha256)
- pin: out&#47;ops&#47;EXECUTION_SESSION_DONE_<TS>.txt (+ .sha256)
