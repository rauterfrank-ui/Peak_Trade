# Portfolio reservation treasury equity boundary ratification v1

See umbrella: `POST_6828_ARCHITECTURE_CLOSURE_V1.md`.

Machine contract: `config/governance/portfolio_reservation_treasury_equity_boundary_ratification_v1.json`

Code owner: `src/ops/portfolio_capital_reservation_budget_v1/contract_v1.py`

```text
PORTFOLIO_BUDGET_OWNER=portfolio_capital_reservation_budget_owner_v1
RESERVATION_OWNER=portfolio_capital_reservation_budget_owner_v1
Q0_OWNER=ops.governed_productive_account_equity_authority_producer_v1
Q1_OWNER=src.governance.capital_risk_sizing_v1
CAPITAL_AUTHORITY_OWNER_COUNT=1
DUPLICATE_CAPITAL_AUTHORITY_COUNT=0
CANONICAL_RESTART_RECONSTRUCTABLE=false
RESTART_CLASSIFICATION=N5_ACTIVATION_REQUIREMENT
```

Portfolio reservation is a **budget/concurrency owner** over already-produced 29P equity; it does not mint account equity or bypass Q0/Q1.
