# P7 Operator CLI (p7_ctl)

Entry point:
- `scripts/ops/p7_ctl.py`

Subcommands:
- `reconcile <outdir>`: run P7 reconciliation checks (python runner)
- `run-paper --spec <json> [--run-id <id>] [--outdir <dir>] [--evidence 0|1]`: run paper trading session
- `run-shadow --spec <shadow_spec_json> --outdir <dir> [--run-id <id>] [--p7-evidence 0|1]`: run shadow session (P6) with P7 enabled

Examples:

Reconcile a P7 outdir:
- `python3 scripts/ops/p7_ctl.py reconcile out/ops/p7_step6_smoke_20260211T144454Z`

Run paper trading (fixture):
- `python3 scripts/ops/p7_ctl.py run-paper --spec tests/fixtures/p7/paper_run_min_v0.json --run-id demo --outdir out/ops/p7_paper_demo --evidence 1`

Run shadow with P7 (fixture):
- `python3 scripts/ops/p7_ctl.py run-shadow --spec tests/fixtures/p6/shadow_session_min_v1_p7.json --run-id demo --outdir out/ops/p7_shadow_demo --p7-evidence 1`
