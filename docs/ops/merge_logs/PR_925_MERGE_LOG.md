# PR #<NUM> — Merge Log

Summary
- ExecutionPipeline Slice 2: deterministic ledger/accounting + PnL from Slice‑1 events.

Why
- Provide audit‑friendly, deterministic accounting outputs (cash/positions/fees/PnL) with golden regression tests.

Changes
- Add a consumer‑only ledger package (double‑entry journal, balances, positions/WAC, valuation, stable exports).
- Enrich Slice‑1 BETA_EXEC_V1 events for deterministic accounting fields (additive fields only).
- Add invariant + golden + integration tests.
- Add Slice‑2 runbook + index/roadmap link updates.

Verification
- Tests → PASS

```bash
python3 -m pytest -q \
  tests/execution/test_ledger_double_entry.py \
  tests/execution/test_ledger_pnl_golden.py \
  tests/execution/test_execution_slice1_to_ledger_integration.py
```

- Docs gates (changed-scope) → PASS

```bash
bash scripts/ops/pt_docs_gates_snapshot.sh --changed
```

Risk
- LOW: consumer‑only ledger; no live unlocks; deterministic policy enforced.

Operator How‑To
- Run Slice‑2 runbook: [RUNBOOK_EXECUTION_SLICE2_LEDGER_PNL](../runbooks/RUNBOOK_EXECUTION_SLICE2_LEDGER_PNL.md)

References
- PR: <URL>
- Merge commit: <SHA>
- mergedAt: <UTC>
