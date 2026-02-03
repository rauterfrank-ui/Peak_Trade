## Scope
- Add `scripts/pipeline_cli.py` as a unified, offline-first entrypoint delegating to:
  - `scripts/research_cli.py`
  - `scripts/live_ops.py` (NO-LIVE)
  - `scripts/risk_cli.py`
- Provide consistent top-level flags:
  - `--run-id`
  - `--sandbox` (sets `PEAKTRADE_SANDBOX=1`)
  - `--artifacts-dir` (forwarded to `risk_cli` before subcommand parsing)

## Evidence
- CLI help:
  - `python3 scripts/pipeline_cli.py --help`
- Smoke test:
  - `PEAKTRADE_SANDBOX=1 python3 -m pytest -q tests/ops/test_pipeline_cli_smoke.py --maxfail=1`

## Notes
- Delegation is subprocess-based; no runtime execution path changes in existing CLIs.
- `pipeline_cli` passes `--run-id` through to all sub-CLIs; risk artifacts are written under `--artifacts-dir/<run-id>/...`.
- JSON parsing in the smoke test tolerates non-JSON prelude output (e.g., warnings) before the JSON payload.
