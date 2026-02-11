# P6

Working notes for P6 (Shadow Mode Stability). See `docs/ops/p6/P6_TODO.md`.

## Shadow Session Runner (P6)

Docs paths in prose use token-policy safe encoding (e.g. `out&#47;ops&#47;...`). In the terminal examples below, paths use normal slashes.

- **Runbook:** `docs/ops/p6/runbook_shadow_session.md` (start/stop/monitor, ≥3 runs evidence)

Run (dry-run, deterministic):

```bash
python3 scripts/aiops/run_shadow_session.py \
  --spec tests/fixtures/p6/shadow_session_min_v0.json \
  --run-id fixed \
  --evidence 1 \
  --dry-run
```

Run with P7 paper trading (P4C + P5A + P7):

```bash
python3 scripts/aiops/run_shadow_session.py \
  --spec tests/fixtures/p6/shadow_session_min_v1_p7.json \
  --run-id fixed \
  --evidence 1 \
  --dry-run \
  --p7-enable 1 \
  --p7-evidence 1
```

Disable P7 (legacy P4C + P5A only):

```bash
python3 scripts/aiops/run_shadow_session.py \
  --spec tests/fixtures/p6/shadow_session_min_v0.json \
  --run-id fixed \
  --p7-enable 0
```
