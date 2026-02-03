# Phase B – live_ops Evidence-Chain (NO-LIVE)

Goal: `scripts/live_ops.py` produces a reproducible evidence pack per `run_id`:
- `artifacts&#47;live_ops&#47;<run_id>&#47;meta.json`
- `env&#47; logs&#47; reports&#47; plots&#47; results&#47;` subdirs
- meta contains git sha, python version, sandbox flag, and run parameters

Non-goal: This does **not** enable trading/execution. It only records evidence.
