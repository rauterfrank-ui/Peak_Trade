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

Local implementation addendum, 2026-11-03 (HEAD242b7974 plus uncommitted changes):
the existing owner now supports explicit optional durable storage and automatic
internal budget recovery. Its default memory mode and the global false restart
flag remain unchanged. The durable owner retains holds through process death,
requires the existing verified portfolio gate plus fresh account-scoped 29P
capital, and resumes internal admission automatically when the checks pass.
It never treats a fresh capital observation or flat position snapshot as a
release of an unknown reservation. No human capital approval is part of recovery.

Storage belongs to this budget owner: SQLite rollback journal (`DELETE`),
`synchronous=FULL`, `BEGIN IMMEDIATE`, a lifetime OS writer lock and a validated
sequence/hash history. SQLite was chosen for atomic multi-field reservation
state transitions, not as economic reconciliation evidence. The distinct DDO
custom-WAL owner and its restricted authority are unchanged. Transaction/rollback
behavior and durability assumptions follow the official
[SQLite transaction](https://www.sqlite.org/lang_transaction.html) and
[atomic commit](https://www.sqlite.org/atomiccommit.html) documentation; local
verification covers process death, not hardware/power failure.

The scoped process tests are
`tests/ops/test_durable_portfolio_budget_recovery_v1.py`. Current semantics,
proofs and remaining integration limits are recorded in the canonical master
runbook's durable internal reservation addendum. No default/productive host
binding or venue-order/fill reconciliation closure is claimed. N5 activation
requirements and machine-contract flags above remain in force.
