# Legacy Order Intent Inventory SSOT v1

**Status:** BINDING inventory / pointer (docs + static contract only)  
**Date:** 2026-07-17  
**Plan item:** `P2_GOVERNANCE &#47; LEGACY_ORDER_INTENT`  
**Base SHA:** `19e4b1f26dcbbfeeef3b7138f15dfa5bc4181319`  
**Machine inventory:** [`config/governance/legacy_order_intent_inventory_ssot_v1.json`](../../config/governance/legacy_order_intent_inventory_ssot_v1.json)

```
LEGACY_ORDER_INTENT_INVENTORY_SSOT_V1=true
INVENTORY_ONLY=true
CONSOLIDATION_STATUS=NOT_STARTED
DECOMMISSION_STATUS=NOT_STARTED
LEGACY_ORDER_INTENT_CLAIMED_DECOMMISSIONED=false
LEGACY_ORDER_INTENT_CLAIMED_CONSOLIDATED=false
CANONICAL_ORDER_INTENT_OWNER=UNRESOLVED
CANONICAL_ORDER_INTENT_OWNER_MV2_SCOPE=src.governance.canonical_order_intent_v1
CANONICAL_EXECUTION_AUTHORITY_OWNER=UNRESOLVED
PRODUCTIVE_ORDER_INTENT_DECISION_OWNER_COUNT=3
PRODUCTIVE_BYPASS_PATH_COUNT=4
DIRECT_SUBMISSION_BYPASS_COUNT=5
DIRECT_SUBMISSION_SURFACE_CONTRACT_V1=true
DIRECT_SUBMISSION_SURFACE_CONTRACT_SEMANTICS=INVENTORY_ONLY_NOT_EXECUTION_PERMISSION
DIRECT_SUBMISSION_SURFACE_CONTRACT_IS_NOT_EXECUTION_ALLOWLIST=true
DECISION_OWNER_SURFACE_CONTRACT_V1=true
DECISION_OWNER_SURFACE_CONTRACT_SEMANTICS=INVENTORY_ONLY_NOT_AUTHORITY_ASSIGNMENT
DECISION_OWNER_SURFACE_CONTRACT_IS_NOT_AUTHORITY_ASSIGNMENT=true
DECISION_OWNER_SURFACE_CONTRACT_DOES_NOT_PROMOTE_REPO_WIDE_OWNER=true
AUTHORITY_LEAK_DETECTED=false
THIS_DOCUMENT_IS_INVENTORY_SSOT_NOT_RUNTIME_AUTHORITY=true
NO_RUNTIME_REWIRE_IN_THIS_SLICE=true
NO_TRADING_CORE_CHANGE=true
NO_EXECUTION_SEMANTICS_CHANGE=true
NO_RISK_SIZING_CHANGE=true
NO_RUNTIME_BRIDGE_ACTIVATION=true
ELIGIBLE_FOR_LIVE_DEFAULT=false
LIVE_AUTHORIZED=false
ORDERS_ENABLED=false
RUNTIME_BRIDGE_ACTIVATED=false
RUNTIME_BRIDGE_STATUS=BOUND_NOT_ACTIVATED
ECONOMIC_GATE_REMAINS_FAIL_CLOSED=true
AUTHORITY_EFFECT=NONE
```

**INVENTORY ONLY — CONSOLIDATION NOT STARTED — DECOMMISSION NOT STARTED.**  
This slice does **not** retire legacy paths, does not rewire producers, and does not change trading-core, execution semantics, risk/sizing, runtime bridge, live/order flags, economic gate, market dashboard, or GitHub settings.

## 1. Executive Summary

Repo-wide forensic inventory of order-intent producers, transformers, routers, adapters, dispatchers, and consumers.

| Field | Value |
|---|---|
| Repo-wide canonical order-intent owner | `UNRESOLVED` |
| MV2/offline-chain order-intent owner | `src.governance.canonical_order_intent_v1` |
| Canonical execution-authority owner | `UNRESOLVED` |
| Productive order-intent decision owners | `3` |
| Productive bypass paths | `4` |
| Direct submission bypasses | `5` |
| Authority leak detected | `false` |
| Consolidation / decommission | `NOT_STARTED` |

**Why order-intent is UNRESOLVED repo-wide:** MV2 offline chain uniquely uses `build_canonical_order_intent_v1`, but legacy `src.execution.pipeline.OrderIntent` and adapter `OrderIntentV1` still decide intent independently.

**Why execution authority is UNRESOLVED:** Submission unlocks are split across `go_no_go`, `SafetyGuard`, canary/transport gates, and executors. The canonical COI path never grants submission (`execution_eligible=false`, `submission_authorized=false`, plan-only boundary).

**Why `authority_leak_detected=false`:** Productive live entrypoints remain deauthorized (`BOUND_NOT_ACTIVATED`, legacy entrypoint guard, canary deny-all, live_order_execution locked). Latent library capability (`KrakenLiveClient`) without an open productive entrypoint is **not** counted as a leak.

## 2. Owner / Path Matrix

| Owner / Symbol | Path | Role | Reachability | Decides intent? | Can submit? |
|---|---|---|---|---|---|
| `build_canonical_order_intent_v1` | `src/governance/canonical_order_intent_v1.py` | CANONICAL_DECISION_OWNER | REACHABLE_PRODUCTIVE | Yes (MV2) | No |
| Offline / backtest COI adapters | `src&#47;trading&#47;master_v2&#47;canonical_order_intent_*_adapter_v0.py` | CANONICAL_ADAPTER | REACHABLE_PRODUCTIVE | No | No |
| Intent pipeline bridge | `src/trading/master_v2/canonical_core_runtime_integration_intent_pipeline_bridge_v0.py` | CANONICAL_ADAPTER | REACHABLE_PRODUCTIVE | No | No (`submission_blocked`) |
| Intent compatibility firewall | `src/governance/intent_compatibility_firewall_v1.py` | CANONICAL_ADAPTER | REACHABLE_PRODUCTIVE | No | No |
| Plan-only boundary | `src/execution_pipeline/plan_only_boundary_v0.py` | CANONICAL_ADAPTER | REACHABLE_PRODUCTIVE | No | No |
| Legacy `OrderIntent` / `ExecutionPipeline` | `src/execution/pipeline.py` | PRODUCTIVE_LEGACY_OWNER | REACHABLE_PRODUCTIVE | Yes | Yes (sim/gated) |
| `OrderIntentV1` | `src/execution/adapters/base_v1.py` | PRODUCTIVE_LEGACY_OWNER | REACHABLE_PRODUCTIVE | Yes | Via adapters |
| Paper executor | `src/orders/paper.py` | PRODUCTIVE_LEGACY_OWNER | REACHABLE_PRODUCTIVE | No | Sim only |
| `LiveOrderRequest` | `src/live/orders.py` | PRODUCTIVE_LEGACY_OWNER | REACHABLE_PRODUCTIVE | Partial | No |
| Router `OrderIntentV1` path | `src/execution/router/router_v1.py` | PRODUCTIVE_BYPASS | REACHABLE_PRODUCTIVE | Yes | Mocks |
| `ExchangeOrderExecutor` | `src/orders/exchange.py` | PRODUCTIVE_BYPASS | REACHABLE_PRODUCTIVE | No | Yes if client set |
| Unguarded shadow script | `scripts/run_shadow_execution.py` | PRODUCTIVE_BYPASS | REACHABLE_PRODUCTIVE | Yes | Shadow/paper |
| `KrakenLiveClient` | `src/exchange/kraken_live.py` | PRODUCTIVE_BYPASS | REACHABLE_PRODUCTIVE (library) | No | Yes (API) |
| `LiveSessionRunner` | `src/execution/live_session.py` | PRODUCTIVE_BYPASS | UNREACHABLE | Indirect | Guarded |
| `execution_simple` | `src/execution_simple/pipeline.py` | PRODUCTIVE_BYPASS | UNREACHABLE | Yes | Guarded |
| Legacy entrypoint guard | `src/trading/master_v2/legacy_runtime_entrypoint_guard_v0.py` | REPORTING_OR_OBSERVABILITY | REACHABLE_PRODUCTIVE | No | Blocks |
| Meta lifecycle / idempotency | `src&#47;meta&#47;learning_loop&#47;*order*` | REPORTING_OR_OBSERVABILITY | REACHABLE_PRODUCTIVE | No | No |
| `go_no_go` live map | `src/governance/go_no_go.py` | REPORTING_OR_OBSERVABILITY | REACHABLE_PRODUCTIVE | No | Unlock map only |
| COI tests | `tests/governance/test_canonical_order_intent_v1.py` | TEST_OR_FIXTURE | REACHABLE_TEST | No | No |
| Plan pointers in other SSOTs | docs | FALSE_POSITIVE | ARCHIVE | No | No |

## 3. Call-Graph (simplified)

```
CRS (capital_risk_sizing_v1)
  └─ build_canonical_order_intent_v1   ← MV2 OWNER
       ├─ offline / backtest adapters
       └─ intent_pipeline_bridge_v0
            ├─ intent_compatibility_firewall
            └─ plan_only_boundary → submission_blocked, BOUND_NOT_ACTIVATED

LEGACY PARALLEL (no COI):
  signals → ExecutionPipeline.OrderIntent / execute_from_signals / submit_order
         → Paper|Shadow|Testnet|ExchangeOrderExecutor[(client)]
              → [bounded_pilot] KrakenLiveClient   ← entrypoint currently guarded

ADAPTER PARALLEL:
  OrderIntentV1 → Router/Adapters (mocks; shadow/paper modes)
```

## 4. Counts Detail

### Productive decision owners (3)

1. `src.governance.canonical_order_intent_v1`
2. `src.execution.pipeline.OrderIntent`
3. `src.execution.adapters.base_v1.OrderIntentV1`

### Decision-owner surface static contract (drift guard only)

```
DECISION_OWNER_SURFACE_CONTRACT_V1=true
DECISION_OWNER_SURFACE_CONTRACT_SEMANTICS=INVENTORY_ONLY_NOT_AUTHORITY_ASSIGNMENT
DECISION_OWNER_SURFACE_CONTRACT_IS_NOT_AUTHORITY_ASSIGNMENT=true
DECISION_OWNER_SURFACE_CONTRACT_DOES_NOT_PROMOTE_REPO_WIDE_OWNER=true
EXPECTED_OWNER_COUNT=3
DRIFT_POLICY=addition/removal/rename/duplicate/unresolved_symbol/role_or_reachability_drift/authority_escalation → FAIL
```

The three inventoried productive order-intent decision owners are **frozen as a static inventory/drift contract** so that addition of a fourth owner, removal, stable_id rename, source_path move, symbol rename, duplicate IDs, unresolved AST symbols, role/reachability drift, or authority escalation (`canonical=true` / `authorized=true` / `execution_authority=true` / resolving global authority owners) fail closed in tests.

Purpose: inventory / drift freeze only — **not** authority assignment and **not** promotion of any owner as repo-wide canonical.

This frozen set does not:
- assign `CANONICAL_ORDER_INTENT_OWNER` or `CANONICAL_EXECUTION_AUTHORITY_OWNER` (both remain `UNRESOLVED`)
- promote COI, legacy `OrderIntent`, or `OrderIntentV1` as sole repo-wide owner
- authorize, enable, or activate any surface
- start consolidation, decommission, rewire, or delegation
- change execution / trading-core / risk-sizing semantics
- activate runtime bridge, live, testnet, shadow, paper, or orders

`role=CANONICAL_DECISION_OWNER` for COI is **MV2-scope classification only**. Repo-wide `CANONICAL_ORDER_INTENT_OWNER` remains `UNRESOLVED`.

Per-owner freeze pins (inventory-backed IDs / paths / symbols only):

| stable_id | source_path | symbol_or_callable | role | reachability | canonical | authorized | execution_authority |
|---|---|---|---|---|---|---|---|
| `src.governance.canonical_order_intent_v1` | `src/governance/canonical_order_intent_v1.py` | `build_canonical_order_intent_v1` | CANONICAL_DECISION_OWNER | REACHABLE_PRODUCTIVE | false | false | false |
| `src.execution.pipeline.OrderIntent` | `src/execution/pipeline.py` | `OrderIntent` | PRODUCTIVE_LEGACY_OWNER | REACHABLE_PRODUCTIVE | false | false | false |
| `src.execution.adapters.base_v1.OrderIntentV1` | `src/execution/adapters/base_v1.py` | `OrderIntentV1` | PRODUCTIVE_LEGACY_OWNER | REACHABLE_PRODUCTIVE | false | false | false |

**Separate, already-complete contract:** `direct_submission_surface_contract_v1` (PR #5301) remains the freeze for the five direct-submission surfaces and is **not** duplicated here.

**Out of scope / next candidate:** `risk_sizing_owner_and_bypass_surface_contract_v1` (exact freeze of five Risk/Sizing decision owners and five bypass paths) is **not** part of this slice.

### Productive bypass paths (4)

1. Legacy `ExecutionPipeline` intent path
2. `ExecutionRouterV1` / `OrderIntentV1` place path
3. `orders` + `ExchangeOrderExecutor` / `OrderRequest` path
4. Unguarded shadow/paper scripts

### Direct submission bypasses (5)

1. `ExecutionPipeline.submit_order`
2. `ExchangeOrderExecutor`
3. `KrakenLiveClient.place_order`
4. `ExecutionRouterV1.place_order` (mocks)
5. `execution_pipeline.ExecutionPipeline.execute` adapter submit

### Direct-submission surface static contract (drift guard only)

```
DIRECT_SUBMISSION_SURFACE_CONTRACT_V1=true
DIRECT_SUBMISSION_SURFACE_CONTRACT_SEMANTICS=INVENTORY_ONLY_NOT_EXECUTION_PERMISSION
DIRECT_SUBMISSION_SURFACE_CONTRACT_IS_NOT_EXECUTION_ALLOWLIST=true
EXPECTED_SURFACE_COUNT=5
DRIFT_POLICY=addition/removal/rename/duplicate/unresolved_symbol → FAIL
```

The five inventoried direct-submission surfaces are **frozen as a static inventory/drift contract** so that addition, removal, rename, duplicate IDs, or unresolved symbols fail closed in tests.

This frozen set is NOT an execution allowlist and does not:
- authorize, enable, or activate any surface
- make any surface canonical
- assign execution authority
- approve live / testnet / shadow / paper / orders
- start consolidation or decommission

`REACHABLE_PRODUCTIVE` and `can_submit_orders=true` describe **technical capability / reachability only**, never authorization.

`KrakenLiveClient.place_order` (`submission.kraken_live_client`) remains a **legacy direct-submission bypass** for governance visibility:
- `canonical=false`
- `authorized=false`
- `enabled=false`
- `execution_authority=false`
- `inventory_only=true`

`CANONICAL_EXECUTION_AUTHORITY_OWNER` remains `UNRESOLVED`. Consolidation and decommission remain `NOT_STARTED` and require a separate Operator decision.

## 5. Canonical Status

```
CANONICAL_ORDER_INTENT_OWNER=UNRESOLVED
CANONICAL_ORDER_INTENT_OWNER_MV2_SCOPE=src.governance.canonical_order_intent_v1
CANONICAL_EXECUTION_AUTHORITY_OWNER=UNRESOLVED
AUTHORITY_LEAK_DETECTED=false
CONSOLIDATION_STATUS=NOT_STARTED
DECOMMISSION_STATUS=NOT_STARTED
INVENTORY_ONLY=true
```

Do **not** delete or rewire legacy surfaces in this slice. Decommission requires a separate Operator-GO PR after review.

## 6. Safety invariants (unchanged)

- Runtime bridge remains `BOUND_NOT_ACTIVATED`
- `LIVE_AUTHORIZED=false`, `ORDERS_ENABLED=false`
- Economic gate remains fail-closed
- Market dashboard remains removed
- No GitHub settings mutation
- No trading-core / execution-semantics / risk-sizing change

## 7. Open governance decisions

1. Make COI the sole repo-wide order-intent owner?
2. Force all `OrderIntentV1` producers through COI transform only?
3. Hard-deauthorize unguarded scripts / exchange executor without semantic change?
4. Select a single execution-authority owner under Operator-GO
5. Keep `KrakenLiveClient` library-only until canonical submission exists

## 8. Next plan item

Decommission / consolidation of legacy order-intent paths requires **Operator-GO** and is **not** started by this inventory.

Semantikfreier Folgekandidat (nicht in diesem Slice): Risk/Sizing owner+bypass surface static contract (`RISK_SIZING_STATIC_GUARD`).
