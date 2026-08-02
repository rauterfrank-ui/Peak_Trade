# CAPABILITY_3_1_PRODUCTIVE_FUTURES_ACCOUNTING_RUNTIME_BINDING_V1

---
docs_token: DOCS_TOKEN_CAPABILITY_3_1_PRODUCTIVE_FUTURES_ACCOUNTING_RUNTIME_BINDING_V1
STATUS: CAPABILITY_AVAILABLE
scope: Bind canonical futures_accounting kernel after simulated fill and before portfolio/risk persistence on Cap 2.4 productive host
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
RUNTIME_ACTIVATION_ALLOWED: false
MULTI_FUTURE_RUNTIME_AUTHORIZED: false
CORE_LOGIC_CHANGE: false
ACTIVATION_STATE: CODE_EXISTS_BOUND_RUNTIME_REACHABLE_NOT_ACTIVATED
HARD_STOP: true
---

```text
CAPABILITY_ID=CAPABILITY_3_1_PRODUCTIVE_FUTURES_ACCOUNTING_RUNTIME_BINDING_V1
TITLE=Productive Futures Accounting Runtime Binding (Capability 3.1)
OWNER_REQUIREMENT=Reuse src/execution/paper/futures_accounting.py as sole productive futures PnL/margin kernel after simulated fill; single-writer portfolio/risk projection; no second kernel; no live/order activation
CURRENT_STATE=CODE_EXISTS+BOUND+RUNTIME_REACHABLE; ACTIVATED=false; FUTURES_ACCOUNTING_RUNTIME_BOUND=true on Cap 2.4 wallclock host
TARGET_STATE=Productive analytical runtime consumes canonical futures accounting after fill and before portfolio/risk persistence with restart/idempotency proofs
OUT_OF_SCOPE=Master V2/Double Play/Bull-Bear/Selection/Ranking/Risk-Safety decision mutation/Exit mutation/Volatility Enforcement/Authorization Consumption/Session Lifecycle/Live/Testnet/Paper Activation/Rulesets/Notion/Dashboard Authority
AUTHORITY_OWNER=ops.productive_futures_accounting_runtime_binding_v1
CANONICAL_KERNEL_OWNER=src.execution.paper.futures_accounting
PRODUCTIVE_ENTRYPOINT=scripts/ops/run_single_selected_future_runtime_binding_v1.py → wallclock bridge host
CALL_GRAPH=
  Persisted Single Selected Future
  → Cap 2.4 binding + Cap 1.1 reconciliation
  → Public Market Data
  → Features / Regime
  → Master V2 / Double Play
  → Risk / Safety / Intent
  → Simulated Execution
  → Simulated Fill (fee/slippage)
  → Canonical Futures Accounting
  → Portfolio State
  → Risk State from Accounting
  → Evidence
CONFIG_KEYS=FUTURES_ACCOUNTING_RUNTIME_BOUND=true; POSITION_FLIP_ALLOWED=false; single accounting writer
SAFETY_INVARIANTS=ONE_CANONICAL_ACCOUNTING_KERNEL; FILL_THEN_ACCOUNTING_THEN_PORTFOLIO; RECONCILIATION_BEFORE_ALPHA; no flip; reduce-only/over-reduce fail-closed; LIVE/ORDERS false
TEST_PLAN=tests/ops/test_productive_futures_accounting_runtime_binding_v1.py
EVIDENCE_PLAN=docs/evidence/capability_3_1_productive_futures_accounting_runtime_binding_v1/
ACTIVATION_STATE=CODE_EXISTS_BOUND_RUNTIME_REACHABLE_NOT_ACTIVATED
ROLLBACK_PLAN=unbind Cap 3.1 bridge step only with FUTURES_ACCOUNTING_RUNTIME_BOUND=false; do not activate live paths
DOCS_UPDATE=Peak_Trade_Canonical_Capability_Closure_Runtime_Recovery_Trading_Path_Runbook_V1_2_Trading_First.md; PEAK_TRADE_CANONICAL_RUNTIME_TRUTH_MAP_V1.md
NOTION_UPDATE=false
```

## Capability closure markers

```text
CODE_EXISTS=true
BOUND=true
RUNTIME_REACHABLE=true
PRODUCTIVE_CALLER_ADDED=true
FUTURES_ACCOUNTING_RUNTIME_BOUND=true
CANONICAL_KERNEL_REUSED=true
ACCOUNTING_SINGLE_WRITER=true
RECONCILIATION_BEFORE_ALPHA=true
CORE_LOGIC_CHANGE=false
ACTIVATION_CHANGED=false
LIVE_PATH_CHANGED=false
ACTIVATED=false
CANONICAL_RUNTIME_ENTRYPOINT_STATUS=BOUND_NOT_ACTIVATED
```

## Explicit non-claims

- Runtime activation / live / testnet / paper orders are not authorized.
- Master V2 / Double Play / Risk / Safety decision semantics are unchanged.
- Cap 2.3 selection authority and Cap 2.4 instrument binding remain upstream authorities.
- Dashboard and allowlists are never accounting authority.
