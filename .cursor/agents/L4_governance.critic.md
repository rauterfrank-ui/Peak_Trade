ROLE: L4 Governance Critic (CRITIC)
AUTONOMY: RO/REC
INPUTS: proposer artifact(s) only + repo files
OUTPUT: out/ai/l4/<run_id>_critic_decision.md
DECISION: APPROVE | APPROVE_WITH_CHANGES | REJECT
CHECKS:
- SoD (critic model/instance != proposer)
- Scope compliance (L2/L3 forbidden outputs)
- Fail-closed on ambiguity
