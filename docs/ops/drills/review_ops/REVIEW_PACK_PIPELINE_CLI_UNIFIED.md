## Review order
1. `scripts/pipeline_cli.py`
2. `tests/ops/test_pipeline_cli_smoke.py`

## Quick verification
From repo root:
- `python3 scripts/pipeline_cli.py --help`
- `PEAKTRADE_SANDBOX=1 python3 -m pytest -q tests/ops/test_pipeline_cli_smoke.py --maxfail=1`

## What to look for
- `--artifacts-dir` is forwarded to `risk_cli` before the `var` subcommand so parsing works.
- `--run-id` is forwarded consistently to research/live_ops/risk.
- `--sandbox` only sets `PEAKTRADE_SANDBOX=1` (no other behavior changes).
