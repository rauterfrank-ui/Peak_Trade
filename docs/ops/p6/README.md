# P6

Working notes for P6 (Shadow Mode Stability). See `docs/ops/p6/P6_TODO.md`.

## Shadow Session Runner (P6)

Docs paths are token-policy safe (e.g. `out&#47;ops&#47;...`). In your terminal, use `out/ops/...`.

Run (dry-run, deterministic):

```bash
python3 scripts/aiops/run_shadow_session.py \
  --spec tests/fixtures/p6/shadow_session_min_v0.json \
  --run-id fixed \
  --evidence 1 \
  --dry-run
```
