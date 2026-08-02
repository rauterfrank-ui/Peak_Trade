# CAPABILITY_2_4_SINGLE_SELECTED_FUTURE_RUNTIME_BINDING_V1

---
docs_token: DOCS_TOKEN_CAPABILITY_2_4_SINGLE_SELECTED_FUTURE_RUNTIME_BINDING_V1
STATUS: CAPABILITY_AVAILABLE
scope: Bind Cap 2.3 persisted single selected future into the productive analytical runtime host before reconciliation/alpha
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
RUNTIME_ACTIVATION_ALLOWED: false
MULTI_FUTURE_RUNTIME_AUTHORIZED: false
CORE_LOGIC_CHANGE: false
ACTIVATION_STATE: CODE_EXISTS_BOUND_RUNTIME_REACHABLE_NOT_ACTIVATED
HARD_STOP: true
---

```text
CAPABILITY_ID=CAPABILITY_2_4_SINGLE_SELECTED_FUTURE_RUNTIME_BINDING_V1
TITLE=Single Selected Future Runtime Binding (Capability 2.4)
OWNER_REQUIREMENT=Consume Cap 2.3 persisted selection as sole productive instrument authority; validate ranking/universe refs; bind venue-native instrument; run Cap 1.1 reconciliation before alpha; reject dashboard/allowlist/direct override authority
CURRENT_STATE=CODE_EXISTS+BOUND+RUNTIME_REACHABLE; ACTIVATED=false; no live/testnet/paper/order path
TARGET_STATE=Productive analytical runtime host consumes exactly one persisted selected future with fail-closed restart/recovery semantics
OUT_OF_SCOPE=Master V2/Double Play/Bull-Bear/Dynamic Scope/Composition/Confirmation/Risk/Safety mutation/Exit mutation/Volatility Enforcement/Authorization Consumption/Session Lifecycle/Live/Testnet/Paper Activation/Rulesets/Notion/Dashboard Authority/Top-N Active Set/Multi-Future
AUTHORITY_OWNER=ops.single_selected_future_runtime_binding_v1
SELECTION_AUTHORITY_OWNER=CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1
PRODUCTIVE_ENTRYPOINT=scripts/ops/run_single_selected_future_runtime_binding_v1.py → wallclock bridge host
CALL_GRAPH=
  Persisted Single Selected Future
  → Selection Integrity/Freshness Validation
  → Ranking Snapshot Reference Validation
  → Governed Universe Instrument Validation
  → Venue Native Instrument Binding
  → Productive Reconciliation Startup Gate (Cap 1.1)
  → Public Market Data
  → Features / Market State
  → Master V2 / Double Play
  → Risk / Safety / Intent
  → Simulated Economics (no-order)
  → Evidence
CONFIG_KEYS=selected_future_count=1; max_positions_effective=1; multi_future_runtime_authorized=false; dashboard_authority_effect=false; allowlist_selection_authority=false; direct_instrument_override_allowed=false
SELECTION_STATES=SELECTED_ACTIVE|SELECTED_DEGRADED|SELECTED_EXIT_ONLY|REPLACEMENT_PENDING|NO_SELECTION
SAFETY_INVARIANTS=SELECTION_AUTHORITY from Cap 2.3 only; dashboard READ_ONLY_CONSUMER; allowlist safety-only; productive direct override rejected; reconciliation before alpha; CORE_LOGIC_CHANGE=false
TEST_PLAN=tests/ops/test_single_selected_future_runtime_binding_v1.py
EVIDENCE_PLAN=docs/evidence/capability_2_4_single_selected_future_runtime_binding_v1/
ACTIVATION_STATE=CODE_EXISTS_BOUND_RUNTIME_REACHABLE_NOT_ACTIVATED
ROLLBACK_PLAN=set require_selection_binding=false on non-productive research callers only; do not activate live paths
DOCS_UPDATE=Peak_Trade_Canonical_Capability_Closure_Runtime_Recovery_Trading_Path_Runbook_V1_2_Trading_First.md
NOTION_UPDATE=false
```

## Capability closure markers

```text
CODE_EXISTS=true
BOUND=true
RUNTIME_REACHABLE=true
PRODUCTIVE_CALLER_ADDED=true
RECONCILIATION_BEFORE_ALPHA=true
SELECTED_FUTURE_COUNT=1
MAX_POSITIONS_EFFECTIVE=1
MULTI_FUTURE_RUNTIME_AUTHORIZED=false
DASHBOARD_AUTHORITY_EFFECT=false
ALLOWLIST_SELECTION_AUTHORITY=false
CORE_LOGIC_CHANGE=false
ACTIVATION_CHANGED=false
LIVE_PATH_CHANGED=false
ACTIVATED=false
CANONICAL_RUNTIME_ENTRYPOINT_STATUS=BOUND_NOT_ACTIVATED
```

## Selection-state semantics

| State | New Alpha | Exit/Risk/Safety |
|---|---|---|
| SELECTED_ACTIVE | allowed after remaining gates | preserved |
| SELECTED_DEGRADED | blocked | preserved |
| SELECTED_EXIT_ONLY | blocked | preserved (exit/reduce only) |
| REPLACEMENT_PENDING | blocked for replacement | current instrument remains bound for protection |
| NO_SELECTION | fully blocked | N/A |

## Explicit non-claims

- Runtime activation / live / testnet / paper orders are not authorized.
- Multi-Future runtime remains unauthorized.
- Master V2 / Double Play / Risk / Safety semantics are unchanged.
- Dashboard and allowlists are never selection authority.
