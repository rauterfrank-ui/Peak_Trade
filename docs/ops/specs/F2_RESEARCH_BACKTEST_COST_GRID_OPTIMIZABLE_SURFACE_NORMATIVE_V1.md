---
docs_token: DOCS_TOKEN_F2_RESEARCH_BACKTEST_COST_GRID_OPTIMIZABLE_SURFACE_NORMATIVE_V1
status: active
scope: Owner-authorized F2 optimizable surface for research backtest fee/slippage grid only
capability: F2_RESEARCH_BACKTEST_COST_GRID_OPTIMIZABLE_SURFACE_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-19
---

# F2 — Research Backtest Cost Grid (Fee / Slippage) Optimizable Surface V1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
WORKPACKAGE_ID=F2_RESEARCH_BACKTEST_COST_GRID_END_TO_END_V1
BOUND_ORIGIN_MAIN_SHA=25b0518b93f91a9609d70c30fb8cd3bf96401a46
AUTHORIZED_SURFACE_ID=RESEARCH_BACKTEST_COST_GRID_FEE_SLIPPAGE_OPTIMIZATION_V1
RESEARCH_OPTIMIZATION_ONLY=true
PRODUCTIVE_TRADING_EFFECT=NONE
THRESHOLD_SELECTION_AUTHORIZED=false
ENFORCEMENT_AUTHORIZED=false
EXTERNAL_EFFECT_AUTHORIZED=false
```

Machine-readable decision:
`config/governance/f2_research_backtest_cost_grid_optimizable_surface_v1_decision_v1.json`

## Owner

- Registry bootstrap: `src/experiments/canonical_f2_research_backtest_cost_grid_optimizable_surface_v1.py`
- Research execution: `src/experiments/canonical_f2_research_backtest_cost_grid_research_execution_v1.py`
- Resolver: `src/experiments/canonical_optimizable_envelope_v1.py`

## Constraint artifacts

- Owner grant: `config/governance/f2_research_backtest_cost_grid_optimizable_surface_owner_grant_v1.json`
- Domain: `config/governance/optimizable_envelope/research_backtest_cost_grid_allowed_policy_domain_v1.json`
- Bounds: `config/governance/optimizable_envelope/research_backtest_cost_grid_discrete_bounds_v1.json`
- Change rate: `config/governance/optimizable_envelope/research_backtest_cost_grid_change_rate_v1.json`
- Risk: `config/governance/optimizable_envelope/research_backtest_cost_grid_risk_constraints_v1.json`
- Evidence: `config/governance/optimizable_envelope/research_backtest_cost_grid_evidence_requirements_v1.json`

## Non-goals

- Funding-rate optimization, strategy hyperparameters, risk sizing
- Promotion, productive apply, Master V2 / Double Play mutation
- Live/testnet config or execution authority
