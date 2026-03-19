# BOUNDED ACCEPTANCE OPERATOR CHEAT SHEET

## Purpose
Ultra-compact operator reference for bounded / acceptance runs.

## Canonical Path
- runbook: `docs&#47;ops&#47;runbooks&#47;ACCEPTANCE_ORIENTED_BOUNDED_RUN_OPERATOR_RUNBOOK.md`
- launcher: `scripts&#47;ops&#47;run_bounded_pilot_with_local_secrets.py`
- standard: `docs&#47;ops&#47;specs&#47;ACCEPTANCE_EVIDENCE_STANDARD.md`
- canonical example: `docs&#47;ops&#47;evidence&#47;CANONICAL_ACCEPTANCE_RUN_20260319_CLOSEOUT.md`

## Before Run
- `main` clean + synced
- no active bounded-pilot processes
- supervisor stopped
- Entry Contract confirmed
- Go/No-Go confirmed
- Dry Validation confirmed
- Ops Cockpit reviewed
- `.bounded_pilot.env` present
- `python3 scripts/ops/run_bounded_pilot_with_local_secrets.py --dry-check`

## Canonical Start
```bash
cd ~/Peak_Trade
python3 scripts/ops/run_bounded_pilot_with_local_secrets.py --dry-check
python3 scripts/ops/run_bounded_pilot_with_local_secrets.py --steps 25 --position-fraction 0.0005
```

## After Run
1. **Execution events** — `out/ops/execution_events/sessions/<session_id>/execution_events.jsonl`
2. **Live-session report** — `reports/experiments/live_sessions/<timestamp>_live_session_bounded_pilot_<session_id>.json`
3. **Closeout** — create under `docs/ops/evidence/` using `docs/ops/templates/ACCEPTED_AND_FILLED_CLOSEOUT_TEMPLATE.md` or `REJECTED_ORDER_CLOSEOUT_TEMPLATE.md`
4. **Handoff** — if evidence position changes, add under `docs/ops/reviews/`

## Allowed
- Bounded runs via local secret launcher
- Conservative sizing (e.g. `position_fraction` 0.0005)
- Evidence capture mandatory

## Not Allowed
- Blanket live authorization
- Weakening gates
- Live secrets in paper/shadow/testnet
- Skipping evidence capture

## References
- Go/No-Go: `docs/ops/reviews/bounded_acceptance_go_no_go_snapshot/GO_NO_GO_SNAPSHOT.md`
- Runbook: `docs/ops/runbooks/ACCEPTANCE_ORIENTED_BOUNDED_RUN_OPERATOR_RUNBOOK.md`
- Canonical: `docs/ops/evidence/CANONICAL_ACCEPTANCE_RUN_20260319_CLOSEOUT.md`
