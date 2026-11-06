# Post-#6828 architecture closure v1

`AUTHORITY_EFFECT=NONE` · `RUNTIME_AUTHORIZATION_EFFECT=NONE`

Machine contract: `config/governance/post_6828_architecture_closure_v1.json`

Owner-GO: **OWNER_GO_POST_6828_ARCHITECTURE_CLOSURE_V1** (CONSUMED)

Known proven baseline: `7cb1c5c57bfc486449cf4da361cb621a809e6075` (#6828 on `origin/main`).

## Scope

Ratifies WP-A (Universe/Ranking/Selection/Binding domain), WP-B (Companion C2
blocking boundary vs Full-Core), and WP-C (Portfolio reservation ↔ Treasury/Q0/Q1)
without changing ranking policy, MV2/DP logic, activation, or external effect.

## Child contracts

| WP | Contract | Doc |
|----|----------|-----|
| A | `universe_ranking_selection_binding_domain_ratification_v1.json` | `UNIVERSE_RANKING_SELECTION_BINDING_DOMAIN_RATIFICATION_V1.md` |
| B | `risk_sizing_c2_companion_blocking_boundary_ratification_v1.json` | `RISK_SIZING_C2_COMPANION_BLOCKING_BOUNDARY_RATIFICATION_V1.md` |
| C | `portfolio_reservation_treasury_equity_boundary_ratification_v1.json` | `PORTFOLIO_RESERVATION_TREASURY_EQUITY_BOUNDARY_RATIFICATION_V1.md` |

## Cross-domain authority matrix (CURRENT productive Full-Core)

| Domain | OWNS_DATA | OWNS_SELECTION | OWNS_TRADING_DECISION | OWNS_ACCOUNT_EQUITY | OWNS_PORTFOLIO_BUDGET | OWNS_POSITION_SIZING | OWNS_EXECUTION_PLAN | OWNS_EXTERNAL_EFFECT | CAN_MUTATE_DOWNSTREAM_AUTHORITY |
|--------|-----------|----------------|----------------------|---------------------|----------------------|---------------------|--------------------|--------------------|--------------------------------|
| Universe/Data ingress (EEA) | partial | no | no | no | no | no | no | no | no |
| Ranking (Cap-2.2) | context | no | no | no | no | no | no | no | no |
| Selection (Cap-2.3) | no | **yes** | no | no | no | no | no | no | no |
| Runtime binding (Cap-2.4) | validate | no | no | no | no | no | no | no | no |
| Full Autonomy orchestrator | no | no | no | no | no | no | no | no | no |
| MV2/DP replay | consume | no | **yes** | no | no | no | no | no | no |
| Treasury (enter-live) | observe | no | no | source handoff only | no | no | no | no | no |
| Portfolio reservation | no | no | no | no | **budget/concurrency** | no | no | no | no |
| Q1 CRS | no | no | no | no | no | **yes** (quantity) | no | no | no |
| Companion C2 | conversion inputs (unresolved) | no | no | no | no | no | no | no | no |
| Execution / egress | no | no | no | no | no | no | adapter | fail-closed | no |

## Invariants preserved

```text
POST_ALLOWED=false
EXTERNAL_EFFECT_AUTHORIZED=false
MULTI_FUTURE_RUNTIME_AUTHORIZED=false
MAX_POSITIONS_EFFECTIVE=1
CAP23_SOLE_PRODUCTIVE_SELECTION=true
CAP24_NO_RESELECT=true
MV2_SOLE_TRADING_DECISION=true
FULL_CORE_Q0_OWNER_COUNT=1
FULL_CORE_Q1_OWNER_COUNT=1
```
