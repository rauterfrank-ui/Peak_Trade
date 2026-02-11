# P7 — Paper Trading Runbook

Docs paths in prose use token-policy safe encoding (e.g. `out&#47;ops&#47;...`).
In the terminal examples below, paths use normal slashes.

## Goal
Validate the paper trading simulator end-to-end with deterministic runs and evidence manifests.

## Quickstart
Run a deterministic session:

```bash
python3 scripts/aiops/run_paper_trading_session.py \
  --spec tests/fixtures/p7/paper_run_min_v0.json \
  --run-id fixed \
  --evidence 1
```

## Outputs
Session artifacts under `out&#47;ops&#47;p7&#47;paper_&lt;run-id&gt;&#47;`:

- `fills.json` — fills (symbol, side, qty, price, fee)
- `account.json` — cash, positions
- `evidence_manifest.json` — manifest (when `--evidence 1`)

## Operator CLI (p7_ctl)

Full reference: [docs/ops/p7/operator_cli.md](operator_cli.md)

Reconcile, run-paper, run-shadow:

```bash
python3 scripts/ops/p7_ctl.py reconcile out/ops/<shadow_outdir> --spec tests/fixtures/p7/paper_run_min_v0.json
python3 scripts/ops/p7_ctl.py run-paper --spec tests/fixtures/p7/paper_run_min_v0.json
python3 scripts/ops/p7_ctl.py run-shadow --spec tests/fixtures/p6/shadow_session_min_v1_p7.json --outdir out/ops/p7_ctl_test
```

## Smoke test
Run smoke test locally:

```bash
pytest tests/sim/paper/test_paper_runner_smoke.py -v
pytest tests/aiops/p6/test_p7_reconcile_smoke.py -v
```
