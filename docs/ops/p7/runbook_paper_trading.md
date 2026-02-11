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

## Smoke test
Run smoke test locally:

```bash
pytest tests/sim/paper/test_paper_runner_smoke.py -v
```
