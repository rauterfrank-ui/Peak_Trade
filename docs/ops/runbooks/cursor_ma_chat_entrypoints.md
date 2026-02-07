# Cursor Multi-Agent Chat — Entry/Exit Points (Matrix-Gated)

## Entry points
- **L2 Proposer**: `.cursor/agents/L2_market_outlook.proposer.md`
- **L3 Proposer**: `.cursor/agents/L3_trade_plan_advisory.proposer.md`
- **L4 Critic**: `.cursor/agents/L4_governance.critic.md`

## Expected local artifacts (ignored by git)
- `out/ai/l2/<run_id>_market_outlook.md`
- `out/ai/l3/<run_id>_trade_plan.md`
- `out/ai/l4/<run_id>_critic_decision.md`

## Exit points
- L4 decision is **APPROVE / APPROVE_WITH_CHANGES / REJECT**
- Any ambiguity => **REJECT (fail-closed)**

## Gates (must be green)
- `python3 -m ruff check src/ tests/ scripts/`
- `python3 -m ruff format --check src/ tests/ scripts/`
- `python3 -m pytest -q tests/governance`
