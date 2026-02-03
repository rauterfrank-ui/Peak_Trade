# Phase B – live_ops Evidence-Chain (NO-LIVE)

Goal: `scripts/live_ops.py` produces a reproducible evidence pack per `run_id`:
- `artifacts/live_ops/<run_id>/meta.json`
- `env/ logs/ reports/ plots/ results/` subdirs
- meta contains git sha, python version, sandbox flag, and run parameters

Non-goal: This does **not** enable trading/execution. It only records evidence.
