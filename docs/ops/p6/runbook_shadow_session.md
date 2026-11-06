# P6 — Shadow Session Runbook

Docs paths in prose use token-policy safe encoding (e.g. `out&#47;ops&#47;...`).
In the terminal examples below, paths use normal slashes.

## Goal
Run the Shadow Session pipeline (P4C → P5A) in **shadow/dry-run** mode, produce deterministic evidence, and collect ≥3 successful runs without regressions.

## Preconditions
- Branch: `main` (clean) or a dedicated feature branch
- `python3` available
- No live trading: this runner uses only subprocess and JSON I/O

## Inputs
- Shadow session spec: `tests/fixtures/p6/shadow_session_min_v0.json`
- P4C capsule fixture: `tests/fixtures/p4c/capsule_min_v0.json`
- P5A input fixture: `tests/fixtures/p5a/input_min_v0.json`

## Run (recommended)
Run with a deterministic id (repeatable evidence directory):

```bash
python3 scripts/aiops/run_shadow_session.py \
  --spec tests/fixtures/p6/shadow_session_min_v0.json \
  --run-id fixed \
  --evidence 1 \
  --dry-run
```

## Outputs
Session artifacts under `out&#47;ops&#47;p6&#47;shadow_&lt;run-id&gt;&#47;`:

- `shadow_session_summary.json` — schema version, steps, outputs, no_trade
- `p4c&#47;l2_market_outlook.json` — P4C output
- `p5a&#47;l3_trade_plan_advisory.json` — P5A output
- `evidence_manifest.json` — manifest of printed paths (when `--evidence 1`)

## Override output directory
Use `--outdir` for a custom path:

```bash
python3 scripts/aiops/run_shadow_session.py \
  --spec tests/fixtures/p6/shadow_session_min_v0.json \
  --outdir /tmp/shadow_run \
  --evidence 1 \
  --dry-run
```

## Stop
Single run. No daemon. Exit when finished.

## Monitor
- Check stdout: one path per line (summary, p4c out, p5a out, manifest)
- Inspect `shadow_session_summary.json` for `no_trade`, `steps`, `outputs`
- Run smoke test: `pytest tests&#47;aiops&#47;p6&#47;test_shadow_session_smoke.py -v`

## Troubleshooting
| Issue | Action |
|-------|--------|
| `FileNotFoundError` spec/capsule/p5a | Ensure fixtures exist and repo root is cwd |
| `subprocess` fails | Run P4C/P5A scripts individually to isolate |
| No evidence manifest | Pass `--evidence 1` (default) |

## ≥3 Shadow runs (Step 3 evidence)
To satisfy P6 gate: run ≥3 sessions over 1 week without regressions.

```bash
# Run 1
python3 scripts/aiops/run_shadow_session.py --spec tests/fixtures/p6/shadow_session_min_v0.json --run-id run1 --evidence 1 --dry-run
# Run 2
python3 scripts/aiops/run_shadow_session.py --spec tests/fixtures/p6/shadow_session_min_v0.json --run-id run2 --evidence 1 --dry-run
# Run 3
python3 scripts/aiops/run_shadow_session.py --spec tests/fixtures/p6/shadow_session_min_v0.json --run-id run3 --evidence 1 --dry-run
```

Compare outputs: `shadow_session_summary.json` schema_version and steps should match across runs.
