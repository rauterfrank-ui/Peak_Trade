---
docs_token: DOCS_TOKEN_FULL_CORE_CURRENT_PRODUCTIVE_HOST_ENTER_29P_INVALID_STOP_PRICE_REPAIR_V1
status: active
scope: Full-Core CURRENT_PRODUCTIVE host-ENTER 29P INVALID_STOP_PRICE root-cause and binding repair; offline confirmation/SideState → ARMED → ENTER → 29P PASS → 29Q PLAN_ONLY → Venue-Plan PASS → Envelope BOUND; no permit; no venue POST
capability: FULL_CORE_CURRENT_PRODUCTIVE_HOST_ENTER_29P_INVALID_STOP_PRICE_REPAIR_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-16
---

# Full Core Current Productive Host Enter 29P Invalid Stop Price Repair V1

Derived spec. Non-SSOT. Canonical persist is Master Runbook §11.2.1.DS.
Consumes Owner-GO
`OWNER_GO_CURRENT_PRODUCTIVE_HOST_ENTER_29P_INVALID_STOP_PRICE_ROOT_CAUSE_AND_REPAIR_V1`.
Atlas remains `NAVIGATION_ONLY` / `AUTHORITY=NONE`.

After §11.2.1.DR the one-shot host can reach ENTER with unchanged trading
logic. STEP-29P request construction still bound the offline fixture
`protective_stop_price=3400` while overriding `reference_price` to the
observed mark. Host ENTER mark `1630` made that fixture LONG-invalid
(`3400 >= 1630` → `INVALID_STOP_PRICE`). The separate ARMED replay kept
mark `3500`, so the same fixture remained LONG-valid.

This persist binds the already-current `adverse_exit_distance` producer
(host: `CANONICAL_ADVERSE_EXIT_DISTANCE`) to the 29P stop at the same
mark 29P uses as `reference_price`, using the existing LONG/SHORT
threshold orientation. It does not change 29P policy, Master-V2, Double
Play, confirmation thresholds, or the fixture constant used by unrelated
offline adapters that omit an explicit stop.

```text
OWNER_GO=OWNER_GO_CURRENT_PRODUCTIVE_HOST_ENTER_29P_INVALID_STOP_PRICE_ROOT_CAUSE_AND_REPAIR_V1
OWNER_GO_STATUS=CONSUMED
FAULT_LOCATION=29P_REQUEST_BINDING
29P_POLICY_CHANGED=false
TRADING_LOGIC_AUTHORITY_CHANGED=false
STOP_PRICE_AUTHORITY_SOURCE=inp.adverse_exit_distance+selected_side+mark_reference
VENUE_CAPITAL_CAUSAL=false
EXTERNAL_EFFECT_AUTHORIZED=false
REAL_EXTERNAL_EFFECT_AUTHORIZED=false
REAL_VENUE_POST_ALLOWED=false
POST_ALLOWED=false
STEP_29Q_STATUS=PLAN_ONLY
POST_COUNT=0
TRANSPORT_ATTEMPTED=false
VENUE_MUTATION_PERFORMED=false
PERMIT_CREATED=false
EXTERNAL_EFFECT_PERMIT_CREATED=false
MAX_POSITIONS_EFFECTIVE=1
RUNTIME_AUTHORIZATION_EFFECT=NONE
OFFLINE_ENTER_IS_NOT_LIVE_PROOF=true
```
