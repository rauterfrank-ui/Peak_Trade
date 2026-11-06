# P7 — Paper Trading Validation

## Source
- Runbook: docs/ops/runbooks/RUNBOOK_AI_AUTONOMY_BIS_FINISH_2026.md
- Extract: out/ops/p7_kickoff_20260211_131930/P7_SECTION.txt

## Deliverables (from runbook)
- Paper Trading Simulator (tested, CI-green)
- Paper Trading Runbook (docs/ops/runbooks/)
- Consistent reconciliation logs (multiple sessions)

## Guardrails
- No live trading; simulator only
- Deterministic execution: explicit seeds where randomness exists
- Evidence artifacts under out&#47;ops&#47;p7&#47; (docs-encoded)

## Next steps
- [ ] Implement paper trading simulator core (fills + slippage + fees hooks)
- [x] Reconciliation checks (positions, cash, realized PnL invariants) — scripts/aiops/run_p7_reconcile.py
- [x] Paper trading runbook + operator CLI — runbook exists; scripts/ops/p7_ctl.py
- [x] Integrate into Shadow pipeline (P6 runner extension or separate P7 runner)
