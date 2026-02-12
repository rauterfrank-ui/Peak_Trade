# P5A — L3 Trade Plan Advisory Kickoff

## Source
- Runbook: docs/ops/runbooks/RUNBOOK_AI_AUTONOMY_BIS_FINISH_2026.md
- Next phase after P4C (L2 Market Outlook)

## Deliverables (from runbook)
- [ ] L3 Runner script (scripts/aiops/run_l3_trade_plan_advisory.py) — exists
- [ ] Create L3 Evidence Pack fixtures
- [ ] Integrate L3 Capability Scope enforcement
- [ ] Add L3 unit tests (deterministic outputs, no execution triggers)
- [ ] L3 Operator Cheatsheet
- [ ] Document L3 → L5 (Risk Gate) handoff protocol

## Guardrails
- Safety-first, dry-run by default
- Deterministic evidence packs under out&#47;ops&#47;p5a&#47;
- NO execution triggers (no order placement logic)

## Next commands
- [ ] Identify inputs/outputs + schemas
- [ ] Implement minimal scaffolding + tests
- [ ] PR via scripts&#47;ops&#47;pr_safe_flow.sh
